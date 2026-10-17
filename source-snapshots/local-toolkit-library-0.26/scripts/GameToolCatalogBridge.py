"""Read-only in-process adapter for the exact sibling game-tool catalog backend.

Loading and planning do not authorize or execute any declared action. A source
change invalidates the cached snapshot until an explicit successful reload.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.abc
import importlib.util
import json
from pathlib import Path
import sys
from threading import RLock


SUPPORTED_VERSION = "0.1.1"
MAX_SOURCE_BYTES = 1024 * 1024
MAX_VALIDATION_WORK = 4_000_000
_BACKEND_PATH = Path(__file__).resolve().with_name("Game-Tool-Catalog.py")
_COLLECTIONS = ("components", "games", "features", "relationships", "actions")
_FILTERS = {"kind", "category", "game", "status", "relationship", "search", "installation", "sort"}
_FG_PATHS = {name: _BACKEND_PATH.with_name(name + ".py")
             for name in ("GameFgInspector", "GameFgPreflight")}
_FG_LOCK = RLock()


def _fg_unavailable(scope, game, code):
    return {"schema_version": 1, "status": "BLOCKED", "can_compare": False,
            "scope": scope, "game_id": game, "execution": "none",
            "reason_codes": [code], "reasons": [
                "Effective FG/Dynamic MFG could not be verified. No comparison is permitted."],
            "provenance": {"trusted": False}, "source_revisions": {}}


def _run_fg_preflight(scope, game, executable=None, native_settings_path=None):
    """Explicit read only. No cached receipt, imported proof, or settings action."""
    if scope == "process-idle":
        return {"schema_version": 1, "status": "NOT_APPLICABLE", "can_compare": True,
                "scope": scope, "game_id": game, "execution": "none",
                "reason_codes": ["NO_RENDERING_WORKLOAD"],
                "reasons": ["Manager-idle scope has no game-rendering workload; no FG source was read."],
                "source_revisions": {}}
    with _FG_LOCK:
        absent = object()
        previous = {name: sys.modules.get(name, absent) for name in _FG_PATHS}
        try:
            captured = {name: _read_source(path, name) for name, path in _FG_PATHS.items()}
            modules = {}
            for name, path in _FG_PATHS.items():
                spec = importlib.util.spec_from_file_location(name, path,
                    loader=_SnapshotLoader(captured[name][0], path))
                module = importlib.util.module_from_spec(spec)
                # One exact inspector identity for its in-process evidence seal.
                sys.modules[name] = module
                try:
                    spec.loader.exec_module(module)
                except Exception:
                    sys.modules.pop(name, None)
                    raise
                if getattr(module, "VERSION", None) != "0.1.0":
                    raise ValueError("Unsupported FG adapter version")
                modules[name] = module
            observation = modules["GameFgInspector"].inspect_fg(
                game, executable=executable, native_settings_path=native_settings_path)
            receipt = modules["GameFgPreflight"].assess_fg(scope, game, observation)
            if any(_read_source(path, name)[1] != captured[name][1]
                   for name, path in _FG_PATHS.items()):
                return _fg_unavailable(scope, game, "FG_SOURCE_CHANGED")
            if not isinstance(receipt, dict) or receipt.get("schema_version") != 1 or \
                    receipt.get("status") not in {"PASS", "BLOCKED"} or \
                    receipt.get("can_compare") is not (receipt.get("status") == "PASS") or \
                    receipt.get("scope") != scope or receipt.get("game_id") != game or \
                    receipt.get("execution") != "none" or \
                    not isinstance(receipt.get("reasons"), list) or \
                    not all(isinstance(reason, str) for reason in receipt["reasons"]) or \
                    not isinstance(receipt.get("reason_codes"), list) or \
                    not all(isinstance(code, str) for code in receipt["reason_codes"]) or \
                    receipt.get("policy", {}).get("version") != "0.1.0" or \
                    (receipt["status"] == "PASS" and receipt.get("provenance", {}).get("trusted") is not True):
                return _fg_unavailable(scope, game, "FG_POLICY_INVALID")
            receipt["source_revisions"] = {name: item[1] for name, item in captured.items()}
            return receipt
        except Exception:
            # Never export an exception containing a private path or driver dump.
            # Adapter failure must not break browsing, idle plans, or original tabs.
            return _fg_unavailable(scope, game, "FG_ADAPTER_UNAVAILABLE")
        finally:
            for name, module in previous.items():
                if module is absent:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module


class CatalogBridgeError(ValueError):
    """A catalog request failed; no execution or automatic recovery occurred."""


def _read_source(path, label):
    """Read one bounded, stable source without writing a bytecode/cache file."""
    try:
        before = path.stat()
        if not path.is_file() or before.st_size > MAX_SOURCE_BYTES:
            raise CatalogBridgeError(f"{label} must be a file no larger than 1 MiB")
        with path.open("rb") as stream:
            raw = stream.read(MAX_SOURCE_BYTES + 1)
        after = path.stat()
    except OSError as error:
        raise CatalogBridgeError(f"{label} is unavailable; explicit reload is required") from error
    signature = lambda stat: (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
    if len(raw) > MAX_SOURCE_BYTES or len(raw) != before.st_size or signature(before) != signature(after):
        raise CatalogBridgeError(f"{label} changed during its bounded read; explicit reload is required")
    return raw, hashlib.sha256(raw).hexdigest()


class _SnapshotLoader(importlib.abc.Loader):
    """Import only captured sibling source; never read or write .pyc files."""

    def __init__(self, raw, path):
        self.raw, self.path = raw, path

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        exec(compile(self.raw, str(self.path), "exec", dont_inherit=True), module.__dict__)


def _load_backend(raw):
    spec = importlib.util.spec_from_file_location(
        "_game_tool_catalog_backend", _BACKEND_PATH, loader=_SnapshotLoader(raw, _BACKEND_PATH)
    )
    if spec is None or spec.loader is None:
        raise CatalogBridgeError("Exact sibling catalog backend could not be loaded")
    backend = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(backend)
    if getattr(backend, "VERSION", None) != SUPPORTED_VERSION:
        raise CatalogBridgeError("Catalog backend version is unsupported")
    for name in ("validate", "no_duplicate_keys", "filtered_nodes", "show_node", "plan_overhead"):
        if not callable(getattr(backend, name, None)):
            raise CatalogBridgeError("Catalog backend API is unsupported")
    return backend


def _require_validation_budget(snapshot):
    """Conservative scan-work estimate, not a runtime deadline or a validator."""
    fields = ("components", "games", "features", "relationships")
    if not isinstance(snapshot, dict) or not all(isinstance(snapshot.get(field), list) for field in fields):
        return  # Let the backend reject malformed shapes with its normal errors.
    node_count = sum(len(snapshot[field]) for field in fields[:3])
    estimated_work = max(1, len(snapshot["games"])) * node_count * max(1, len(snapshot["relationships"]))
    if estimated_work > MAX_VALIDATION_WORK:
        raise CatalogBridgeError("Catalog exceeds integration validation work budget")


class CatalogService:
    """Validated, detached data access and nonexecuting plans for a local catalog.

    ``path`` is an absolute Path for the host UI. Exported metadata contains only
    its filename. ``revision`` hashes the exact catalog bytes, not live PC state.
    All source-dependent methods fail closed after drift or a failed reload.
    """

    def __init__(self, catalog_path=None):
        default = _BACKEND_PATH.parent.parent / "examples/game-tool-hub/catalog.example.json"
        self.path = Path(default if catalog_path is None else catalog_path).resolve()
        self.revision = None
        self.catalog_version = None
        self._lock = RLock()
        self._current = False
        self._snapshot = None
        self._backend = None
        self._backend_revision = None
        self.reload()

    def _invalidate(self, message):
        self._current = False
        raise CatalogBridgeError(message)

    def _require_current(self):
        if not self._current:
            raise CatalogBridgeError("Catalog snapshot is noncurrent; explicit successful reload is required")
        try:
            _, revision = _read_source(self.path, "Catalog source")
            _, backend_revision = _read_source(_BACKEND_PATH, "Catalog backend")
        except CatalogBridgeError:
            self._current = False
            raise
        if revision != self.revision or backend_revision != self._backend_revision:
            self._invalidate("Catalog source or backend changed; explicit successful reload is required")

    def reload(self):
        """Explicitly load and validate one fresh snapshot; failed loads invalidate it."""
        with self._lock:
            self._current = False
            try:
                backend_raw, backend_revision = _read_source(_BACKEND_PATH, "Catalog backend")
                backend = _load_backend(backend_raw)
                raw, revision = _read_source(self.path, "Catalog source")

                def reject_constant(value):
                    raise CatalogBridgeError("Nonfinite JSON constants are prohibited")

                snapshot = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=backend.no_duplicate_keys,
                                      parse_constant=reject_constant)
                _require_validation_budget(snapshot)
                backend.validate(snapshot)
                # Do not publish a snapshot if either source moved while validating.
                if _read_source(self.path, "Catalog source")[1] != revision or \
                        _read_source(_BACKEND_PATH, "Catalog backend")[1] != backend_revision:
                    raise CatalogBridgeError("Catalog sources changed while loading; reload is required")
            except (OSError, ValueError, TypeError, RecursionError, SyntaxError, ImportError) as error:
                if isinstance(error, CatalogBridgeError):
                    raise
                raise CatalogBridgeError(f"Catalog reload failed: {error}") from error
            self._snapshot = snapshot
            self._backend = backend
            self.revision = revision
            self.catalog_version = backend.VERSION
            self._backend_revision = backend_revision
            self._current = True
            return {"version": self.catalog_version, "revision": self.revision,
                    "counts": {field: len(snapshot[field]) for field in _COLLECTIONS}, "execution": "none"}

    def _request(self, callback):
        with self._lock:
            self._require_current()
            try:
                result = callback()
            except (ValueError, TypeError, RecursionError) as error:
                raise CatalogBridgeError(str(error)) from error
            self._require_current()
            return deepcopy(result)

    def _source(self):
        return {"revision": self.revision, "version": self.catalog_version,
                "planning_only": True, "locator": self.path.name}

    def options(self):
        """Available data filters, not claims of live installation or connection."""
        def collect():
            nodes = self._backend.filtered_nodes(self._snapshot)
            return {"kinds": sorted({node["entity"] for node in nodes} |
                                    {node["kind"] for node in nodes if "kind" in node}),
                    "categories": sorted({category for node in nodes for category in node.get("categories", [])}),
                    "games": [{"id": node["id"], "name": node["name"]}
                              for node in nodes if node["entity"] == "game"],
                    "statuses": sorted(self._backend.STATUSES),
                    "installations": sorted(self._backend.INSTALLATION),
                    "relationships": sorted(self._backend.RELATIONS),
                    "sorts": ["id", "name", "kind", "status"]}
        return self._request(collect)

    def list_nodes(self, **filters):
        """Backend filters/defaults; detached plain node list (default ID order)."""
        def collect():
            if set(filters) - _FILTERS:
                raise CatalogBridgeError("Unsupported catalog filter")
            return self._backend.filtered_nodes(self._snapshot, **filters)
        return self._request(collect)

    def details(self, identifier):
        """Backend detail plus portable source provenance; actions remain declarations."""
        def collect():
            return {**self._backend.show_node(self._snapshot, identifier), "catalog_source": self._source()}
        return self._request(collect)

    def fg_preflight(self, scope, game=None, executable=None, native_settings_path=None):
        """Observe explicitly; no game, collector, registry or settings mutation."""
        def collect():
            if scope not in {"process-idle", "in-game"}:
                raise CatalogBridgeError("Unknown overhead scope")
            if scope == "in-game" and game not in {g["id"] for g in self._snapshot["games"]}:
                return _fg_unavailable(scope, game, "EXACT_GAME_REQUIRED")
            if scope == "process-idle" and game is not None:
                raise CatalogBridgeError("Idle scope cannot select a game")
            return _run_fg_preflight(scope, game, executable, native_settings_path)
        return self._request(collect)

    def prepare_plan(self, scope, game=None, factors=None, executable=None, native_settings_path=None):
        """Dependency proposal plus mandatory fresh FG gate; never run a test."""
        def collect():
            plan = self._backend.plan_overhead(self._snapshot, scope, game, deepcopy(factors))
            gate = (_fg_unavailable(scope, game, "INVALID_IDLE_GAME_SELECTION")
                    if scope == "process-idle" and game is not None else
                    self.fg_preflight(scope, game, executable, native_settings_path))
            plan["fg_preflight"] = gate
            plan["comparison_ready"] = gate["can_compare"] and plan["status"] != "blocked"
            if not gate["can_compare"]:
                plan["status"] = "blocked"
                plan["blockers"].append("FG preflight BLOCKED: " + "; ".join(gate["reasons"]))
                plan["suppressed_case_count"] = len(plan["cases"])
                plan["cases"] = []
            return {**plan, "catalog_source": self._source()}
        return self._request(collect)
