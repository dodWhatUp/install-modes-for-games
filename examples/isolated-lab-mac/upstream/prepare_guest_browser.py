"""Guest-side TLS-verified headless-shell download if the Node downloader fails.

Uses installed Playwright's exact registry version. Retains local SHA256 evidence;
that digest verifies storage/transfer, not a separately published vendor checksum.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import tempfile
import time
import urllib.request
import zipfile

import playwright


def main():
    os.umask(0o077)
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise RuntimeError("This browser preparation targets the Linux x86_64 guest only")
    registry = Path(playwright.__file__).parent / "driver/package/browsers.json"
    browser = next(b for b in json.loads(registry.read_text())["browsers"]
                   if b["name"] == "chromium-headless-shell")
    version, revision = browser["browserVersion"], browser["revision"]
    if not version.replace(".", "").isdigit() or not str(revision).isdigit():
        raise ValueError("Unexpected installed browser registry")
    url = "https://cdn.playwright.dev/builds/cft/" + version + "/linux64/chrome-headless-shell-linux64.zip"
    cache = Path.home() / ".cache/ms-playwright"
    target = cache / ("chromium_headless_shell-" + str(revision))
    if target.exists():
        raise FileExistsError("Existing browser cache preserved; inspect before replacement")
    artifacts = Path.home() / "artifacts"
    archive = artifacts / ("chrome-headless-shell-" + version + ".zip")
    if archive.exists():
        raise FileExistsError("Existing archive preserved; inspect before another download")
    digest = hashlib.sha256()
    started = time.monotonic()
    with urllib.request.urlopen(url, timeout=60) as response, archive.open("xb") as f:
        expected = int(response.headers["Content-Length"])
        size = 0
        while True:
            if time.monotonic() - started > 300:
                raise TimeoutError("Total browser download deadline exceeded")
            data = response.read(1024 * 1024)
            if not data:
                break
            f.write(data)
            digest.update(data)
            size += len(data)
    if size != expected:
        raise ValueError("Incomplete browser archive")
    cache.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="headless-staging-", dir=cache))
    with zipfile.ZipFile(archive) as z:
        for entry in z.infolist():
            destination = (staging / entry.filename).resolve()
            if staging.resolve() not in destination.parents:
                raise ValueError("Browser archive path escapes staging")
        z.extractall(staging)
    for path in staging.rglob("*"):
        if path.is_file():
            os.chmod(path, 0o755 if path.suffix in ("", ".so") else 0o644)
    executable = staging / "chrome-headless-shell-linux64/chrome-headless-shell"
    if not executable.is_file():
        raise ValueError("Expected browser executable missing")
    (staging / "INSTALLATION_COMPLETE").touch()
    os.replace(staging, target)
    receipt = {"url": url, "registry_version": version, "registry_revision": revision,
               "archive_bytes": size, "archive_sha256": digest.hexdigest(), "tls_verified": True,
               "checksum_scope": "local stored archive; no separate vendor checksum assertion",
               "installed": str(target)}
    (artifacts / ("browser-preparation-" + str(revision) + ".json")).write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
