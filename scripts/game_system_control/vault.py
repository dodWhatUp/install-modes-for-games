"""MCI-07: explicit managed roots, volume binding and new-copy placement."""
from copy import deepcopy
import os
from pathlib import Path
import unicodedata
import uuid

from GameToolUserData import _canonical, _decode, _read, _write_new, _relative, digest, local_path
from .contracts import require, identifier, replica_binding_status
from .workspace_state import LocalState, private_root
from game_mod_ops.safety import no_links

CLASSES = {"project_source": "source", "selected_assets": "assets", "selected_results": "outputs", "continuation_packet": "continuation"}
EXCLUDED = {"credentials", "browser_profiles", "os_credential_store", "local_permissions", "live_runtime_databases", "schedules", "action_approvals"}
SENSITIVE = {"auth.json", "credentials", "sessions", "archived_sessions", "browser", "cookies", "tokens", ".git", ".codex"}


def volume_identity(root):
    """Observe a Windows volume GUID; unknown OS adapters fail closed."""
    candidate = Path(root)
    root = no_links(candidate) if candidate.is_absolute() and candidate == Path(candidate.anchor) else local_path(candidate)
    require(root.exists(), "Selected volume path is absent.")
    require(os.name == "nt", "Native volume adapter is currently Windows-only; no drive-letter fallback.")
    import ctypes as c
    from ctypes import wintypes as w
    kernel = c.WinDLL("kernel32", use_last_error=True)
    kernel.GetVolumePathNameW.argtypes = [w.LPCWSTR, w.LPWSTR, w.DWORD]
    kernel.GetVolumeNameForVolumeMountPointW.argtypes = [w.LPCWSTR, w.LPWSTR, w.DWORD]
    kernel.GetWindowsDirectoryW.argtypes = [w.LPWSTR, w.UINT]
    def guid(path):
        mount, name = c.create_unicode_buffer(32768), c.create_unicode_buffer(128)
        require(kernel.GetVolumePathNameW(str(path), mount, len(mount)), "Volume mount identity unavailable.")
        require(kernel.GetVolumeNameForVolumeMountPointW(mount.value, name, len(name)), "Volume GUID unavailable.")
        return name.value.casefold()
    windows = c.create_unicode_buffer(32768)
    require(kernel.GetWindowsDirectoryW(windows, len(windows)), "System volume identity unavailable.")
    selected, system = guid(root), guid(windows.value)
    return {"volume_id": digest(selected.encode()), "system_volume": selected == system, "adapter": "windows-volume-guid"}


def _relative_managed(value):
    value = _relative(value)
    require(unicodedata.normalize("NFC", value) == value, "Use NFC-normalized portable paths.")
    require(not any(p.casefold() in SENSITIVE or p.casefold().startswith(".env") for p in value.split("/")) and
            not value.casefold().endswith((".db", ".sqlite", ".sqlite3", ".pem", ".key")), "Credential/native/runtime paths are excluded from managed placement.")
    return value


class VaultRegistry:
    def __init__(self, state_root, observer=volume_identity):
        self.state = LocalState(state_root, "workspace-vault-bindings")
        self.observer = observer

    @classmethod
    def create(cls, state_root, observer=volume_identity):
        LocalState.create(state_root, "workspace-vault-bindings", {"vaults": []})
        return cls(state_root, observer)

    def enroll(self, root, workspace_id, expected_revision):
        root = private_root(root); identifier(workspace_id)
        require(root.parent.is_dir() and not root.exists(), "Select a new vault directory under an existing parent.")
        current = self.state.snapshot()
        require(current["revision"] == expected_revision, "Binding registry changed; inspect again.")
        require(len(current["body"]["vaults"]) < 64, "Vault count bound reached.")
        observed = self.observer(root.parent)
        require(observed["system_volume"] is False, "Managed vault enrollment requires an observed non-system volume.")
        marker = {"schema_version": 1, "kind": "GameToolsManagedVault", "workspace_id": workspace_id,
                  "vault_id": str(uuid.uuid4()), "replica_id": str(uuid.uuid4()), "storage_instance_id": str(uuid.uuid4()), "roots": CLASSES}
        root.mkdir(mode=0o700)
        (root/"projects").mkdir(); (root/"recovery").mkdir()
        _write_new(root/"vault.json", _canonical(marker))
        binding = {"marker": marker, "root": str(root), "volume": observed, "directory_identity": root.stat().st_ino}
        body = deepcopy(current["body"]); body["vaults"].append(binding)
        proposal = self.state.propose(body, current["revision"])
        return self.state.commit(proposal, proposal["preview_sha256"])

    def attach(self, root, expected_revision):
        """Accept an existing selected vault on this OS without copying bindings."""
        root = private_root(root)
        current = self.state.snapshot()
        require(current["revision"] == expected_revision, "Binding registry changed; inspect again.")
        require(root.is_dir() and len(current["body"]["vaults"]) < 64, "Existing vault or registry capacity unavailable.")
        observed = self.observer(root)
        require(observed["system_volume"] is False, "Attach requires a non-system volume.")
        marker = _decode(_read(root/"vault.json", 128 * 1024)[0])
        require(type(marker) is dict and marker.get("schema_version") == 1 and marker.get("kind") == "GameToolsManagedVault" and marker.get("roots") == CLASSES,
                "Unknown vault format/root map; preserve it for a reviewed adapter.")
        for key in ("workspace_id", "vault_id", "replica_id", "storage_instance_id"): identifier(marker.get(key))
        require(not any(r["marker"]["vault_id"] == marker["vault_id"] or
                        (r["marker"]["workspace_id"], r["marker"]["replica_id"]) == (marker["workspace_id"], marker["replica_id"]) for r in current["body"]["vaults"]),
                "Vault/replica identity is already bound; inspect clone or relocation instead of attaching another copy.")
        body = deepcopy(current["body"])
        body["vaults"].append({"marker": marker, "root": str(root), "volume": observed, "directory_identity": root.stat().st_ino})
        proposal = self.state.propose(body, current["revision"])
        return self.state.commit(proposal, proposal["preview_sha256"])

    def _binding(self, vault_id):
        rows = [r for r in self.state.snapshot()["body"]["vaults"] if r["marker"]["vault_id"] == vault_id]
        require(len(rows) == 1, "Select one enrolled vault identity.")
        return rows[0]

    def _verify(self, binding, root):
        root = private_root(root)
        require(root.is_dir(), "Vault is absent; no OS-drive fallback was used.")
        require(self.observer(root) == binding["volume"], "Volume identity changed; explicit new-replica enrollment is required.")
        require(root.stat().st_ino == binding["directory_identity"], "Vault directory identity changed; possible clone/replacement.")
        marker = _decode(_read(root/"vault.json", 128 * 1024)[0])
        require(marker == binding["marker"], "Vault marker changed; inspect the selected replica.")
        return root

    def inspect(self, vault_id):
        binding = self._binding(vault_id)
        self._verify(binding, binding["root"])
        return {**binding["marker"], "available": True, "volume_verified": True, "roots_relative": True,
                "unsupported_outputs": ["Native Codex runtime/chat databases", "Tool outputs without an explicit managed destination"],
                "tool_output_coverage": [{"owner": "GameToolManagedWorkspace", "status": "explicit_managed_routes_supported", "classes": sorted(CLASSES)},
                    {"owner": "Codex", "status": "native_state_not_redirected", "project_source": "explicit_working_directory_only"},
                    {"owner": "existing_Hub_and_external_tools", "status": "host_local_or_unknown_until_adapter_selected"}],
                "fallback": "refuse", "codex_configuration_changed": False}

    def rebind(self, vault_id, root, expected_revision):
        current = self.state.snapshot()
        require(current["revision"] == expected_revision, "Binding registry drift.")
        binding = self._binding(vault_id)
        self._verify(binding, root)
        old = Path(binding["root"])
        if old.exists():
            require(os.path.samefile(old, root), "Two attached copies are ambiguous; preserve both and enroll a distinct replica.")
        body = deepcopy(current["body"])
        next(r for r in body["vaults"] if r["marker"]["vault_id"] == vault_id)["root"] = str(private_root(root))
        proposal = self.state.propose(body, current["revision"])
        return self.state.commit(proposal, proposal["preview_sha256"])

    def route(self, vault_id, project_id, content_class, relative):
        identifier(project_id); _relative(project_id)
        require(content_class in CLASSES and content_class not in EXCLUDED, "Unsupported managed content class; no fallback.")
        relative = _relative_managed(relative)
        root = self._verify(self._binding(vault_id), self._binding(vault_id)["root"])
        target = local_path(root/"projects"/project_id/CLASSES[content_class]/relative)
        require(root in target.parents, "Managed path escaped its vault.")
        part = root
        for segment in target.relative_to(root).parts:
            if part.is_dir():
                require(not any(p.name.casefold() == segment.casefold() and p.name != segment for p in part.iterdir()), "Managed path has a case alias; select its existing spelling.")
            part = part/segment
        return target

    def place(self, vault_id, project_id, content_class, relative, source, expected_sha256, *, before_publish=None):
        """Write one reviewed new managed copy; original bytes/settings unchanged."""
        _relative_managed(Path(source).name)
        require(not any(p.casefold() in SENSITIVE for p in Path(source).parts), "Native/profile source roots cannot enter generic managed storage.")
        raw = _read(local_path(source))[0]
        require(digest(raw) == expected_sha256, "Selected source changed; review before placement.")
        target = self.route(vault_id, project_id, content_class, relative)
        parent = target.parent
        # Refuse Windows case aliases even on a case-sensitive source filesystem.
        if parent.exists():
            require(not any(p.name.casefold() == target.name.casefold() for p in parent.iterdir()), "Managed name/case collision; keep the existing copy.")
        parent.mkdir(parents=True, exist_ok=True)
        self.route(vault_id, project_id, content_class, relative)
        if before_publish is not None: before_publish()
        _write_new(target, raw)
        require(_read(target)[0] == raw, "Managed output readback failed; preserve the partial result.")
        return {"state": "PLACED_NEW_COPY", "vault_id": vault_id, "project_id": project_id, "content_class": content_class,
                "relative": relative, "sha256": digest(raw), "bytes": len(raw), "originals_changed": False}

    def selected_collisions(self, roots):
        require(type(roots) is list and len(roots) <= 64, "Selected vault scan exceeds its bound.")
        rows, selected_roots = [], []
        for selected in roots:
            root = private_root(selected)
            physical = (self.observer(root)["volume_id"], root.stat().st_dev, root.stat().st_ino)
            if any(os.path.samefile(root, seen) for seen in selected_roots):
                continue
            selected_roots.append(root)
            marker = _decode(_read(root/"vault.json", 128 * 1024)[0])
            rows.append({"workspace_id": marker["workspace_id"], "replica_id": marker["replica_id"], "storage_instance_id": digest(_canonical([*physical, len(selected_roots)]))})
        return replica_binding_status(rows)
