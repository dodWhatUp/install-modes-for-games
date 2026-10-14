"""Bounded official-source downloads. No browser scraping, retries, or credential export."""
from __future__ import annotations
import hashlib
import json
import os
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from . import __version__
from .safety import ModError, require, no_links, slug, copy_new

@dataclass
class Budget:
    max_bytes: int = 128 * 1024 * 1024
    max_requests: int = 40
    seconds: int = 300
    used_bytes: int = 0
    requests: int = 0
    started: float = 0
    def __post_init__(self):
        self.started = time.monotonic()
    def check(self, cancel: Event | None = None):
        require(not cancel or not cancel.is_set(), "CANCELLED", "Operation cancelled; completed downloads are retained.")
        require(time.monotonic() - self.started < self.seconds, "TIME_LIMIT", "This operation reached its time budget.")
    def request(self, cancel=None):
        self.check(cancel)
        self.requests += 1
        require(self.requests <= self.max_requests, "REQUEST_LIMIT", "The request budget is exhausted.")
    def consume(self, size: int, cancel=None):
        self.check(cancel)
        self.used_bytes += size
        require(self.used_bytes <= self.max_bytes, "BUDGET_EXCEEDED", "The transfer budget is exhausted; partial bytes are not retried.")


def https_url(url: str, family: str) -> str:
    try:
        u = urllib.parse.urlsplit(url)
        port = u.port
    except (ValueError, TypeError) as e:
        raise ModError("UNSAFE_URL", "Invalid download URL.") from e
    require(u.scheme == "https" and not u.username and not u.password and port in (None, 443)
            and not u.fragment and not any(ord(c) < 33 for c in url),
            "UNSAFE_URL", "Only HTTPS URLs without credentials, fragments, or control characters are accepted.")
    host = (u.hostname or "").lower()
    allowed = {
        "github": {"api.github.com", "github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"},
        "dropbox": {"www.dropbox.com", "dl.dropboxusercontent.com"},
        "nexus-api": {"api.nexusmods.com"},
        "nexus-cdn": {"download.nexusmods.com", "cdn.nexusmods.com"},
    }
    ok = host in allowed.get(family, set())
    if family == "nexus-cdn":
        ok = ok or host.endswith(".nexus-cdn.com") or host.endswith(".nexusmods.com")
    if family == "dropbox":
        ok = ok or host.endswith(".dropboxusercontent.com")
    require(ok, "HOST_BLOCKED", "The destination is not an approved host for this provider.")
    return host


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, family: str, budget: Budget, cancel: Event | None):
        self.family, self.budget, self.cancel = family, budget, cancel
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        require(self.family != "nexus-api", "AUTH_REDIRECT_BLOCKED", "Authenticated API requests may not redirect.")
        https_url(newurl, self.family)
        self.budget.request(self.cancel)
        # Construct a new request, deliberately dropping all original credentials/headers.
        return urllib.request.Request(newurl, headers={"User-Agent": "GameToolHub-ModWorkflows/" + __version__})


class Http:
    def __init__(self, budget: Budget | None = None, cancel: Event | None = None):
        self.budget, self.cancel = budget or Budget(), cancel
    def _open(self, url: str, family: str, key: str | None = None):
        host = https_url(url, family)
        require(not key or (family == "nexus-api" and host == "api.nexusmods.com"),
                "AUTH_HOST_BLOCKED", "An API key can only be sent to the Nexus API.")
        self.budget.request(self.cancel)
        headers = {"User-Agent": "GameToolHub-ModWorkflows/" + __version__,
                   "Application-Name": "GameToolHub-ModWorkflows", "Application-Version": __version__,
                   "Accept": "application/json" if family == "nexus-api" or host == "api.github.com" else "application/octet-stream"}
        if key:
            require(not any(ord(c) < 33 for c in key), "INVALID_KEY", "The API key contains whitespace or control characters.")
            headers["apikey"] = key
        opener = urllib.request.build_opener(SafeRedirect(family, self.budget, self.cancel))
        try:
            return opener.open(urllib.request.Request(url, headers=headers), timeout=12)
        except urllib.error.HTTPError as e:
            code = {401: "ACCESS_DENIED", 403: "ACCESS_DENIED", 404: "NOT_FOUND", 429: "RATE_LIMITED"}.get(e.code, "HTTP_FAILED")
            # No raw URL, body, key, signed link, cookie, or user identity is retained.
            raise ModError(code, "Provider returned HTTP %s. No automatic retry or alternate-source attempt was made." % e.code) from None
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError):
            raise ModError("NETWORK_UNCERTAIN", "Network request failed. Inspect this job before any new attempt.") from None
    def json(self, url: str, family: str, key: str | None = None):
        with self._open(url, family, key) as r:
            chunks, size = [], 0
            while True:
                self.budget.check(self.cancel)
                chunk = (r.read1 if hasattr(r, "read1") else r.read)(64 * 1024)
                if not chunk: break
                size += len(chunk)
                self.budget.consume(len(chunk), self.cancel)
                require(size <= 2 * 1024 * 1024, "SIZE_LIMIT", "API response exceeds the bounded metadata limit.")
                chunks.append(chunk)
            buf = b"".join(chunks)
        try:
            return json.loads(buf)
        except (ValueError, UnicodeError):
            raise ModError("BAD_RESPONSE", "Provider did not return valid JSON.") from None
    def download(self, url: str, family: str, dest: Path, max_bytes: int, expected: str | None):
        dest = no_links(dest)
        require(not dest.exists(), "EXISTS", "Download destination already exists; inspect it instead of overwriting.")
        dest.parent.mkdir(parents=True, exist_ok=True)
        partial = dest.with_name(dest.name + ".part")
        require(not partial.exists(), "PARTIAL_REVIEW_REQUIRED", "A partial download is present; it is not automatically resumed or overwritten.")
        h, count = hashlib.sha256(), 0
        with self._open(url, family) as r:
            length = r.headers.get("Content-Length")
            if length and length.isdigit():
                require(int(length) <= max_bytes, "SIZE_LIMIT", "Download is larger than the approved item budget.")
            host = https_url(r.geturl(), family)
            with partial.open("xb") as f:
                while True:
                    self.budget.check(self.cancel)
                    chunk = (r.read1 if hasattr(r, "read1") else r.read)(256 * 1024)
                    if not chunk:
                        break
                    count += len(chunk)
                    self.budget.consume(len(chunk), self.cancel)
                    require(count <= max_bytes, "SIZE_LIMIT", "Download exceeded its item budget.")
                    f.write(chunk)
                    h.update(chunk)
                f.flush()
                os.fsync(f.fileno())
        require(count > 0, "EMPTY_DOWNLOAD", "Provider returned an empty download.")
        require(not length or not length.isdigit() or int(length) == count,
                "INCOMPLETE_DOWNLOAD", "Download size does not match Content-Length.")
        sha = h.hexdigest()
        require(not expected or sha == expected, "HASH_MISMATCH", "Downloaded bytes do not match the pinned digest. Partial evidence was retained.")
        # Destination is inside the currently locked job. No overwrite is allowed.
        require(not dest.exists(), "CONCURRENT_CHANGE", "Download destination changed during transfer.")
        # Exclusive creation avoids POSIX rename silently replacing an external writer.
        copy_new(partial, dest, sha)
        partial.unlink()
        return {"sha256": sha, "bytes": count, "source_host": host,
                "integrity": "upstream_digest_matched" if expected else "locally_hashed_only"}


def nxm_parameters(text: str, game: str, mod_id: int, file_id: int) -> dict:
    try:
        u = urllib.parse.urlsplit(text.strip())
        q = urllib.parse.parse_qs(u.query, strict_parsing=True)
    except ValueError:
        raise ModError("INVALID_NXM", "Invalid NXM link.") from None
    require(u.scheme == "nxm" and u.netloc == game and u.path == f"/mods/{mod_id}/files/{file_id}",
            "NXM_MISMATCH", "The NXM link does not match this exact game, mod and file.")
    require(not u.fragment and all(len(v) == 1 for v in q.values()), "INVALID_NXM", "Ambiguous NXM parameters.")
    require(bool(q.get("key")) and bool(q.get("expires")), "WAITING_USER_DOWNLOAD", "Use a fresh website-issued Mod Manager Download link.")
    require(q["expires"][0].isdigit() and int(q["expires"][0]) > time.time(),
            "EXPIRED_NXM", "The website-issued download authorization has expired.")
    return {"key": q["key"][0], "expires": q["expires"][0]}


def resolve(item: dict, http: Http, nexus_key: str | None = None, nxm: str | None = None) -> tuple:
    s = item["source"]
    kind = s["kind"]
    if kind == "manual":
        raise ModError("WAITING_MANUAL_DOWNLOAD", "Download this item through its official page, then import the original archive.")
    if kind == "github_release":
        repo = s["repository"]
        require(bool(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo)) and ".." not in repo,
                "INVALID_SOURCE", "Invalid repository identity.")
        tag = urllib.parse.quote(s["tag"], safe="")
        data = http.json(f"https://api.github.com/repos/{repo}/releases/tags/{tag}", "github")
        require(data.get("tag_name") == s["tag"], "UPSTREAM_CHANGED", "The returned release tag differs from the selected tag.")
        require(not data.get("draft") and not data.get("prerelease"), "UNREVIEWED_RELEASE", "Draft or prerelease assets are not accepted by this recipe.")
        assets = [a for a in data.get("assets", []) if a.get("name") == s["asset"]]
        require(len(assets) == 1, "AMBIGUOUS_ASSET", "The exact pinned release asset was not found uniquely.")
        a = assets[0]
        reported = a.get("digest") or ""
        expected = item.get("sha256")
        if reported.startswith("sha256:"):
            reported = reported[7:]
            require(not expected or reported == expected, "UPSTREAM_CHANGED", "Release digest differs from the reviewed recipe.")
            expected = reported
        return a["browser_download_url"], "github", expected, {"release_tag": s["tag"], "asset_id": a["id"], "file_name": a["name"]}
    if kind == "author_https":
        require(s["url"] == "https://www.dropbox.com/s/wz8x8e4onjdfdbm/UnityModManager.zip?dl=1",
                "SOURCE_NOT_REVIEWED", "This preview supports only the recorded author-linked UMM mirror.")
        return s["url"], "dropbox", item.get("sha256"), {"file_name": "UnityModManager.zip", "version_pin": "verify_after_download"}
    require(kind == "nexus", "PROVIDER_UNSUPPORTED", "No download adapter exists for this provider.")
    require(nexus_key is not None and bool(nexus_key.strip()), "WAITING_NEXUS_AUTH", "Set a personal Nexus API key locally or import a manual download; do not send the key to chat.")
    game = slug(s["game"])
    mod_id = s["mod_id"]
    require(type(mod_id) is int and mod_id > 0, "INVALID_SOURCE", "Invalid Nexus mod ID.")
    user = http.json("https://api.nexusmods.com/v1/users/validate.json", "nexus-api", nexus_key)
    file_id = s.get("file_id")
    if not file_id:
        require(bool(s.get("file_name")) and bool(s.get("version")), "FILE_PIN_REQUIRED", "This Nexus recipe needs a reviewed file ID or exact file name and version before automatic download.")
        data = http.json(f"https://api.nexusmods.com/v1/games/{game}/mods/{mod_id}/files.json", "nexus-api", nexus_key)
        matches = [f for f in data.get("files", []) if f.get("file_name") == s["file_name"] and f.get("version") == s["version"] and f.get("category_name", "").lower() not in {"archived", "deleted"}]
        require(len(matches) == 1, "AMBIGUOUS_FILE", "The requested Nexus file was not found uniquely; no latest-file guess was made.")
        file_id = matches[0]["file_id"]
    require(type(file_id) is int and file_id > 0, "FILE_PIN_REQUIRED", "Invalid Nexus file ID.")
    query = ""
    if not user.get("is_premium", False):
        require(bool(nxm), "WAITING_USER_DOWNLOAD", "Free-account downloads need a website-issued NXM authorization or manual archive import.")
        query = "?" + urllib.parse.urlencode(nxm_parameters(nxm, game, mod_id, file_id))
    data = http.json(f"https://api.nexusmods.com/v1/games/{game}/mods/{mod_id}/files/{file_id}/download_link.json" + query,
                     "nexus-api", nexus_key)
    require(isinstance(data, list) and bool(data) and isinstance(data[0].get("URI"), str), "BAD_RESPONSE", "No authorized download link was returned.")
    return data[0]["URI"], "nexus-cdn", item.get("sha256"), {"game": game, "mod_id": mod_id, "file_id": file_id}
