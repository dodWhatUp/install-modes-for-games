"""Shared wire, path and publication guards; no VM or desktop side effects."""
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import uuid

LIMIT = 262144
VERSION = "0.1.0-candidate"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", value):
        raise ValueError("Invalid bounded identifier")
    return value


def vm_id(value):
    return str(uuid.UUID(value.strip("{}")))


def relative(value):
    if not isinstance(value, str) or not value or len(value) > 2048:
        raise ValueError("Expected a bounded relative path")
    if "\\" in value or "\0" in value or ":" in value:
        raise ValueError("Invalid path")
    p = PurePosixPath(value)
    if p.is_absolute() or str(p) != value or any(x in ("", ".", "..") for x in value.split("/")):
        raise ValueError("Path is not a normalized workspace-relative path")
    return p.parts


def sign(body, key):
    if len(key) != 32:
        raise ValueError("Expected a fresh 256-bit local key")
    return {"body": body, "mac": hmac.new(key, canonical(body), hashlib.sha256).hexdigest()}


def authenticate(envelope, key):
    if not isinstance(envelope, dict) or set(envelope) != {"body", "mac"}:
        raise ValueError("Invalid authenticated envelope")
    expected = sign(envelope["body"], key)["mac"]
    if not isinstance(envelope["mac"], str) or not hmac.compare_digest(envelope["mac"], expected):
        raise ValueError("Authentication failed")
    return envelope["body"]


def read_private(path):
    path = Path(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
            raise ValueError("Private file must be owned by this user and have mode 600")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            data = stream.read(LIMIT + 1)
            if len(data) > LIMIT:
                raise ValueError("Private file exceeds limit")
            return data
    finally:
        os.close(fd)


def parent_fd(root, path, create=False):
    parts = relative(path)
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for name in parts[:-1]:
            if create:
                try:
                    os.mkdir(name, 0o700, dir_fd=fd)
                except FileExistsError:
                    pass
            nxt = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = nxt
        return fd, parts[-1]
    except BaseException:
        os.close(fd)
        raise


def publish(root, path, data, expected):
    """Link a fully flushed verified temporary file without replacing a target."""
    if digest(data) != expected:
        raise ValueError("Selected-file hash mismatch")
    fd, name = parent_fd(root, path, create=True)
    temp = ".isolatedlab-" + uuid.uuid4().hex
    try:
        out = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
        with os.fdopen(out, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temp, name, src_dir_fd=fd, dst_dir_fd=fd, follow_symlinks=False)
        os.fsync(fd)
    finally:
        try:
            os.unlink(temp, dir_fd=fd)
        except FileNotFoundError:
            pass
        os.close(fd)
    return {"path": path, "bytes": len(data), "sha256": expected, "published": True}


def selected(root, path):
    fd, name = parent_fd(root, path)
    try:
        f = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(f, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ValueError("Selected input must be a regular file")
            data = stream.read(65537)
    finally:
        os.close(fd)
    if len(data) > 65536:
        raise ValueError("Select files of at most 64 KiB per request")
    return {"path": path, "bytes": len(data), "sha256": digest(data),
            "base64": base64.b64encode(data).decode()}


def validate(request):
    if not isinstance(request, dict) or request.get("schema") != 1:
        raise ValueError("Expected schema 1")
    identifier(request.get("id"))
    identifier(request.get("owner"))
    vm_id(request.get("vm_uuid", ""))
    if not isinstance(request.get("args", {}), dict):
        raise ValueError("args must be an object")
    timeout = request.get("timeout_ms", 15000)
    if type(timeout) is not int or not 500 <= timeout <= 60000:
        raise ValueError("Deadline must be 500..60000 ms")
    if len(canonical(request)) > LIMIT:
        raise ValueError("Request exceeds limit")
    return request
