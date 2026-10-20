"""Local revision records over the existing file, lock and journal owners.

Not a distributed lock, identity provider, credential store or task database.
Interrupted writes/locks require inspection; they are never silently repaired.
"""
from copy import deepcopy
import os
from pathlib import Path

from GameToolUserData import _canonical, _decode, _read, _write_new, local_path, digest
from GameToolJournal import Journal, inspect_journal
from game_mod_ops.safety import local_lock
from .contracts import require, identifier

VERSION = "0.1.0-preview.1"
MAX_REVISIONS = 256


def principal():
    """Fresh local OS identity, not an OpenAI/cloud account authentication."""
    if os.name == "nt":
        import ctypes as c
        from ctypes import wintypes as w
        kernel = c.WinDLL("kernel32", use_last_error=True)
        advapi = c.WinDLL("advapi32", use_last_error=True)
        kernel.GetCurrentProcess.restype = w.HANDLE
        advapi.OpenProcessToken.argtypes = [w.HANDLE, w.DWORD, c.POINTER(w.HANDLE)]
        advapi.GetTokenInformation.argtypes = [w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.POINTER(w.DWORD)]
        advapi.ConvertSidToStringSidW.argtypes = [c.c_void_p, c.POINTER(w.LPWSTR)]
        kernel.CloseHandle.argtypes = [w.HANDLE]
        kernel.LocalFree.argtypes = [c.c_void_p]
        token = w.HANDLE()
        require(advapi.OpenProcessToken(kernel.GetCurrentProcess(), 8, c.byref(token)), "Local OS identity unavailable.")
        try:
            size = w.DWORD()
            advapi.GetTokenInformation(token, 1, None, 0, c.byref(size))
            require(0 < size.value <= 65536, "Local OS identity unavailable.")
            buffer = c.create_string_buffer(size.value)
            require(advapi.GetTokenInformation(token, 1, buffer, size, c.byref(size)), "Local OS identity unavailable.")
            sid = c.cast(buffer, c.POINTER(c.c_void_p))[0]
            text = w.LPWSTR()
            require(advapi.ConvertSidToStringSidW(sid, c.byref(text)), "Local OS identity unavailable.")
            try:
                subject = text.value
            finally:
                kernel.LocalFree(c.cast(text, c.c_void_p))
        finally:
            kernel.CloseHandle(token)
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            machine = winreg.QueryValueEx(key, "MachineGuid")[0]
        require(type(machine) is str and 0 < len(machine) <= 256, "Machine-local OS identity unavailable.")
    else:
        subject = str(os.geteuid())
        with Path("/etc/machine-id").open("rb") as stream:
            raw = stream.read(257)
        require(0 < len(raw) <= 256, "Machine-local OS identity unavailable.")
        machine = raw.decode("ascii").strip()
    return digest((os.name + ":local-os:" + subject + ":" + machine).encode())


def private_root(path):
    path = local_path(path)
    require(not any(p.casefold() in {".codex", "onedrive"} for p in path.parts), "Local state must stay outside Codex and OneDrive.")
    return path


class LocalState:
    """Append-only compare-and-swap revisions; one local OS owner."""
    def __init__(self, root, kind):
        self.root = private_root(root)
        self.kind = identifier(kind)

    @classmethod
    def create(cls, root, kind, body):
        store = cls(root, kind)
        require(store.root.parent.is_dir(), "Select an existing local parent.")
        require(not store.root.exists(), "A new local state directory is required.")
        value = store._record(body, 0, None, principal())
        store.root.mkdir(mode=0o700)
        (store.root/"audit").mkdir(mode=0o700)
        _write_new(store.root/"00000000.json", _canonical(value))
        return store

    def _record(self, body, generation, parent, owner):
        require(type(body) is dict, "Local state body must be an object.")
        value = {"schema_version": 1, "kind": self.kind, "generation": generation,
                 "parent": parent, "owner_principal": owner, "body": deepcopy(body)}
        _decode(_canonical(value))
        require(len(_canonical(value)) <= 127 * 1024, "Local state record exceeds its readback bound.")
        return {**value, "revision": digest(_canonical(value))}

    def history(self):
        require(self.root.is_dir(), "Selected local state is absent; no fallback was used.")
        paths = sorted(p for p in self.root.glob("*.json") if p.name != "LOCAL-STOP.json")
        require(0 < len(paths) <= MAX_REVISIONS, "Local revision count is outside its bound.")
        rows, parent, owner = [], None, principal()
        for i, path in enumerate(paths):
            require(path.name == f"{i:08}.json", "Local revision history has a gap or unknown file.")
            value = _decode(_read(path, 128 * 1024)[0])
            require(type(value) is dict and set(value) == {"schema_version", "kind", "generation", "parent", "owner_principal", "body", "revision"}, "Invalid local revision record.")
            require(value == self._record(value["body"], i, parent, owner), "Local state changed, belongs to another OS user or has unsupported schema.")
            if i:
                audit = inspect_journal(self.root/"audit"/f"{i:08}.jsonl")
                results = [r for r in audit["verified_records"] if r["kind"] == "operation_result"]
                require(audit["valid"] and audit["clean_end"] and len(results) == 1 and results[0]["data"].get("revision") == value["revision"],
                        "Local revision has incomplete or mismatched audit evidence; reconcile without replay.")
            rows.append(value); parent = value["revision"]
        return rows

    def snapshot(self):
        return self.history()[-1]

    def propose(self, body, expected_revision=None):
        current = self.snapshot()
        require(expected_revision is None or current["revision"] == expected_revision, "State changed while preparing this edit; rebuild it from the current revision.")
        proposal = {"kind": self.kind, "expected_revision": current["revision"], "body": deepcopy(body)}
        return {**proposal, "preview_sha256": digest(_canonical(proposal))}

    def commit(self, proposal, accepted_sha256):
        require(type(proposal) is dict and set(proposal) == {"kind", "expected_revision", "body", "preview_sha256"}, "Invalid local proposal.")
        core = {k: proposal[k] for k in ("kind", "expected_revision", "body")}
        require(proposal["kind"] == self.kind and accepted_sha256 == proposal["preview_sha256"] == digest(_canonical(core)), "Review and accept the exact proposal digest.")
        with local_lock(self.root, ".workspace-state.lock"):
            current = self.snapshot()
            require(current["revision"] == proposal["expected_revision"], "Local revision drift; review again.")
            generation = current["generation"] + 1
            require(generation < MAX_REVISIONS, "Local revision bound reached; archive/reconcile before more writes.")
            value = self._record(proposal["body"], generation, current["revision"], principal())
            with Journal.create(self.root/"audit"/f"{generation:08}.jsonl", {"owner": "managed-workspace", "kind": self.kind, "parent": current["revision"]}) as journal:
                journal.append("operation_intent", {"preview_sha256": accepted_sha256})
                _write_new(self.root/f"{generation:08}.json", _canonical(value))
                journal.append("operation_result", {"revision": value["revision"]})
                journal.append("session_closed", {"reason": "local_revision_published"})
            return self.snapshot()
