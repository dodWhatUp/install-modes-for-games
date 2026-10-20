"""Destination-local Windows account verification. No passwords or exportable proof.

Uses the documented desktop UserConsentVerifier interop ABI, not the UWP-only
RequestVerificationAsync route. Availability is headless; verify opens an owned
window and the Windows verification prompt only when explicitly requested.
"""
from contextlib import contextmanager
import ctypes as c
import os
import sys
import time
import uuid

from GameToolAIContracts import stable_revision
from .contracts import ContextError, require
from .workspace_state import principal

PROVIDER = "windows_hello"
STATICS = "af4f3f91-564c-4ddc-b8b5-973447627c65"
INTEROP = "39e050c3-4e74-441a-8dc0-b81104df949c"
ASYNC_INFO = "00000036-0000-0000-c000-000000000046"
ASYNC_RESULT = "fd596ffd-2318-558f-9dbe-d21df43764a5"
AVAILABILITY = ("available", "device_not_present", "disabled_by_policy", "not_configured_for_user", "device_busy")
RESULTS = ("verified", "device_not_present", "not_configured_for_user", "disabled_by_policy", "device_busy", "retries_exhausted", "canceled")


class WindowsAccountDenied(ContextError):
    def __init__(self, outcome):
        self.outcome = outcome if type(outcome) is str and outcome in RESULTS else "unavailable"
        super().__init__("Windows account verification: " + self.outcome + "; no operation accepted.")


def _hr(value):
    require(value >= 0, "Windows account API failed (HRESULT 0x%08X); no sign-in accepted." % (value & 0xffffffff))


class _Runtime:
    """Small ctypes projection of the published WinRT/COM ABI; owns its pointers."""
    def __init__(self):
        require(os.name == "nt" and sys.getwindowsversion().build >= 22000, "Windows account verification requires Windows build 22000 or later.")
        self.api = c.WinDLL("combase", use_last_error=True)
        self.api.RoInitialize.argtypes = [c.c_uint32]; self.api.RoInitialize.restype = c.c_int32
        self.api.RoUninitialize.argtypes = []; self.api.RoUninitialize.restype = None
        self.api.WindowsCreateString.argtypes = [c.c_wchar_p, c.c_uint32, c.POINTER(c.c_void_p)]
        self.api.WindowsCreateString.restype = c.c_int32
        self.api.WindowsDeleteString.argtypes = [c.c_void_p]; self.api.WindowsDeleteString.restype = c.c_int32
        self.api.RoGetActivationFactory.argtypes = [c.c_void_p, c.c_void_p, c.POINTER(c.c_void_p)]
        self.api.RoGetActivationFactory.restype = c.c_int32
        # STA is needed for the owned desktop window. Do not change another
        # caller's incompatible COM apartment (RPC_E_CHANGED_MODE fails closed).
        _hr(self.api.RoInitialize(0)); self.initialized = True

    def close(self):
        if self.initialized:
            self.api.RoUninitialize(); self.initialized = False

    @staticmethod
    def guid(value): return c.create_string_buffer(uuid.UUID(value).bytes_le, 16)

    @staticmethod
    def call(pointer, slot, *types):
        require(bool(pointer), "Windows account API returned no interface.")
        table = c.cast(pointer, c.POINTER(c.POINTER(c.c_void_p))).contents
        return c.WINFUNCTYPE(c.c_int32, c.c_void_p, *types)(table[slot])

    def release(self, pointer):
        if pointer: self.call(pointer, 2)(pointer)

    @contextmanager
    def string(self, value):
        handle = c.c_void_p()
        _hr(self.api.WindowsCreateString(value, len(value.encode("utf-16-le")) // 2, c.byref(handle)))
        try: yield handle
        finally: self.api.WindowsDeleteString(handle)

    def factory(self, iid):
        pointer = c.c_void_p()
        with self.string("Windows.Security.Credentials.UI.UserConsentVerifier") as name:
            _hr(self.api.RoGetActivationFactory(name, self.guid(iid), c.byref(pointer)))
        return pointer

    def wait(self, operation, *, timeout, pump=lambda: True):
        info = c.c_void_p()
        try:
            _hr(self.call(operation, 0, c.c_void_p, c.POINTER(c.c_void_p))(operation, self.guid(ASYNC_INFO), c.byref(info)))
            deadline = time.monotonic() + timeout
            while True:
                if time.monotonic() >= deadline or not pump():
                    _hr(self.call(info, 9)(info))  # IAsyncInfo.Cancel
                    require(False, "Windows account verification canceled or timed out; no sign-in accepted.")
                status = c.c_int32()
                _hr(self.call(info, 7, c.POINTER(c.c_int32))(info, c.byref(status)))
                if status.value == 1:
                    result = c.c_int32()
                    _hr(self.call(operation, 8, c.POINTER(c.c_int32))(operation, c.byref(result)))
                    return result.value
                if status.value != 0:
                    require(False, "Windows account verification was canceled or failed; no sign-in accepted.")
                time.sleep(0.025)
        finally:
            if info:
                self.call(info, 10)(info)  # IAsyncInfo.Close, including cancellation
                self.release(info)
            self.release(operation)

    def availability(self):
        factory, operation = self.factory(STATICS), c.c_void_p()
        try:
            _hr(self.call(factory, 6, c.POINTER(c.c_void_p))(factory, c.byref(operation)))
            value = self.wait(operation, timeout=10)
            return AVAILABILITY[value] if 0 <= value < len(AVAILABILITY) else "unavailable"
        finally: self.release(factory)

    def verify(self, hwnd, message, pump):
        factory, operation = self.factory(INTEROP), c.c_void_p()
        try:
            with self.string(message) as text:
                _hr(self.call(factory, 6, c.c_void_p, c.c_void_p, c.c_void_p, c.POINTER(c.c_void_p))(
                    factory, hwnd, text, self.guid(ASYNC_RESULT), c.byref(operation)))
            value = self.wait(operation, timeout=60, pump=pump)
            return RESULTS[value] if 0 <= value < len(RESULTS) else "unavailable"
        finally: self.release(factory)


def availability():
    if os.name != "nt": return {"provider": PROVIDER, "status": "unsupported_platform", "interactive": False}
    runtime = _Runtime()
    try:
        interop = runtime.factory(INTEROP); runtime.release(interop)
        return {"provider": PROVIDER, "status": runtime.availability(), "interactive": False}
    finally: runtime.close()


def _native_verify(scope):
    runtime = _Runtime()
    root = None
    try:
        require(runtime.availability() == "available", "Windows verification is unavailable or not configured; configure it locally in Windows. No fallback sign-in was accepted.")
        import tkinter as tk
        try: root = tk.Tk()
        except tk.TclError: require(False, "An interactive local Windows desktop is required for account verification.")
        root.title("Verify Windows account")
        root.geometry("520x150"); root.resizable(False, False)
        tk.Label(root, text="Verify this Windows account to apply the selected workspace operation.", wraplength=470, justify="left").pack(padx=20, pady=(18, 8))
        tk.Label(root, text="Operation: " + scope[:16] + "\nEnter your PIN or biometric only in the Windows prompt.", justify="left").pack(padx=20, anchor="w")
        root.update()
        # winfo_id can name Tk's child window. GetAncestor(GA_ROOT) selects the
        # owned top-level HWND required by the desktop interop contract.
        user = c.WinDLL("user32", use_last_error=True)
        user.GetAncestor.argtypes = [c.c_void_p, c.c_uint32]; user.GetAncestor.restype = c.c_void_p
        user.GetWindowThreadProcessId.argtypes = [c.c_void_p, c.POINTER(c.c_uint32)]
        user.GetWindowThreadProcessId.restype = c.c_uint32
        hwnd = user.GetAncestor(root.winfo_id(), 2); owner = c.c_uint32()
        require(hwnd and user.GetWindowThreadProcessId(hwnd, c.byref(owner)) and owner.value == os.getpid(), "Verification requires this process's own window.")
        def pump():
            try: root.update(); return bool(root.winfo_exists())
            except tk.TclError: return False
        return runtime.verify(hwnd, "GameTools workspace operation " + scope[:16], pump)
    finally:
        if root is not None:
            try: root.destroy()
            except Exception: pass
        runtime.close()


class _Verified:
    """One process, one exact operation, at most 60 seconds; never a JSON token."""
    def __init__(self, scope, subject, issued):
        self.scope, self.subject, self.issued, self.used = scope, subject, issued, False

    def consume(self, scope):
        require(not self.used and self.scope == scope and self.subject == principal() and 0 <= time.monotonic() - self.issued <= 60,
                "Fresh local Windows verification is required for this exact operation.")
        self.used = True


def operation_scope(root, purpose, content):
    return stable_revision({"provider": PROVIDER, "local_root": str(root.resolve()), "purpose": purpose, "content": content})


def verify(scope):
    subject = principal()
    outcome = _native_verify(scope)
    if outcome != "verified": raise WindowsAccountDenied(outcome)
    require(principal() == subject, "The local Windows account changed during verification.")
    return _Verified(scope, subject, time.monotonic())
