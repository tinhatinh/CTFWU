#!/usr/bin/env python3
"""Loopback-only site preview with an editor that saves original writeup files."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from urllib.parse import parse_qs, urlsplit
import urllib.request
import urllib.error

from build_site import SKIP_TOP, slugify

ROOT = Path(__file__).resolve().parent.parent
MAX_CONTENT = 2 * 1024 * 1024
REPOSITORY = "tinhatinh/CTFWU"
SESSION_SECONDS = 8 * 60 * 60


def verify_owner(token):
    if not isinstance(token, str) or not token.strip() or len(token) > 512:
        raise EditError(401, "Enter a valid GitHub personal access token.")
    token = token.strip()
    if not token.isascii() or any(character.isspace() for character in token):
        raise EditError(401, "Enter a valid GitHub personal access token.")
    def get(path):
        request = urllib.request.Request("https://api.github.com/" + path, headers={
            "Authorization": "Bearer " + token.strip(), "Accept": "application/vnd.github+json",
            "User-Agent": "CTFWU-owner-editor", "X-GitHub-Api-Version": "2026-03-10"})
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return json.load(response)
        except urllib.error.HTTPError:
            raise EditError(401, "GitHub could not verify this token.") from None
        except (OSError, ValueError):
            raise EditError(503, "GitHub verification is unavailable. Try again later.") from None
    user = get("user")
    repository = get("repos/" + REPOSITORY)
    if repository.get("full_name", "").casefold() != REPOSITORY.casefold() or not user.get("id") or user["id"] != repository.get("owner", {}).get("id"):
        raise EditError(403, "Only the GitHub repository owner may edit these writeups.")
    return user["login"]


class EditError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


class EditorStore:
    def __init__(self, root, rebuild):
        self.root = Path(root).resolve()
        self.rebuild = rebuild
        self.sessions = {}
        self.lock = threading.RLock()
        self.status = {"state": "idle"}
        self.files = {}
        for event in self.root.iterdir():
            if not event.is_dir() or event.name in SKIP_TOP or event.name.startswith((".", "_")):
                continue
            for case in event.iterdir():
                if not case.is_dir() or case.name.startswith((".", "_")):
                    continue
                for lang, name in [("vi", "writeup.md"), ("en", "writeup.en.md")]:
                    path = case / name
                    if path.is_file() and path.resolve().is_relative_to(self.root):
                        key = (slugify(event.name) + "-" + slugify(case.name), lang)
                        if key in self.files:
                            raise ValueError("Duplicate challenge key: " + key[0])
                        self.files[key] = path

    def path(self, key, lang):
        path = self.files.get((key, lang))
        if not path or not path.resolve().is_relative_to(self.root) or not path.is_file():
            raise EditError(404, "Writeup source not found for this language.")
        return path

    def read(self, key, lang):
        with self.lock:
            path = self.path(key, lang)
            raw = path.read_bytes()
            return {"content": raw.decode("utf-8"), "version": hashlib.sha256(raw).hexdigest(),
                    "path": path.relative_to(self.root).as_posix()}

    def login(self, login):
        session = secrets.token_urlsafe(32)
        with self.lock:
            self.sessions = {key: value for key, value in self.sessions.items() if value["expires"] > time.monotonic()}
            self.sessions[session] = {"owner": login, "csrf": secrets.token_urlsafe(32), "expires": time.monotonic() + SESSION_SECONDS}
        return session

    def session(self, cookie):
        with self.lock:
            value = self.sessions.get(cookie)
            if not value or value["expires"] <= time.monotonic():
                self.sessions.pop(cookie, None)
                raise EditError(401, "Owner authentication required.")
            return value

    def save(self, key, lang, content, version):
        return self.save_many(key, [{"lang": lang, "content": content, "version": version}])

    def save_many(self, key, edits):
        if not isinstance(key, str) or not isinstance(edits, list) or not 1 <= len(edits) <= 2:
            raise EditError(400, "Choose Vietnamese, English, or both.")
        langs = [edit.get("lang") if isinstance(edit, dict) else None for edit in edits]
        if any(lang not in ("vi", "en") for lang in langs) or len(set(langs)) != len(langs):
            raise EditError(400, "Invalid or duplicated language.")
        with self.lock:
            if self.status["state"] == "running":
                raise EditError(409, "A rebuild is running. Please wait before saving again.")
            changes = []
            for edit in edits:
                content, version = edit.get("content"), edit.get("version")
                if not isinstance(content, str) or not content.strip() or "\0" in content:
                    raise EditError(400, "Writeup content must be non-empty UTF-8 text.")
                if len(content.encode("utf-8")) > MAX_CONTENT:
                    raise EditError(413, "Writeup is too large.")
                path = self.path(key, edit["lang"])
                original = path.read_bytes()
                if not isinstance(version, str) or not secrets.compare_digest(hashlib.sha256(original).hexdigest(), version):
                    raise EditError(409, "The source changed since you opened it. Reload the source before saving.")
                normalized = content.replace("\r\n", "\n").replace("\r", "\n")
                original_text = original.decode("utf-8")
                if normalized == original_text.replace("\r\n", "\n").replace("\r", "\n"):
                    updated = original
                else:
                    first_line = original.split(b"\n", 1)[0]
                    if first_line.endswith(b"\r"):
                        normalized = normalized.replace("\n", "\r\n")
                    updated = normalized.encode("utf-8")
                if updated != original:
                    changes.append((path, original, updated))
            if not changes:
                return {"saved": False, "state": "unchanged"}
            backups, prepared, replaced = [], [], []
            def prepare(path, data):
                fd, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
                try:
                    with os.fdopen(fd, "wb") as stream:
                        stream.write(data); stream.flush(); os.fsync(stream.fileno())
                    os.chmod(temporary, path.stat().st_mode)
                    return temporary
                except Exception:
                    if os.path.exists(temporary): os.unlink(temporary)
                    raise
            try:
                for path, original, updated in changes:
                    backup = self.root / "_build" / "editor-backups" / path.relative_to(self.root).parent
                    backup.mkdir(parents=True, exist_ok=True)
                    backup = backup / (path.name + "." + time.strftime("%Y%m%d-%H%M%S") + "." + secrets.token_hex(4))
                    backup.write_bytes(original); backups.append(backup.relative_to(self.root).as_posix())
                    prepared.append((path, original, prepare(path, updated)))
                for path, original, temporary in prepared:
                    if path.read_bytes() != original:
                        raise EditError(409, "The source changed during saving. Reload before retrying.")
                for path, original, temporary in prepared:
                    os.replace(temporary, path); replaced.append((path, original))
            except Exception:
                for path, original in reversed(replaced):
                    rollback = prepare(path, original)
                    try: os.replace(rollback, path)
                    finally:
                        if os.path.exists(rollback): os.unlink(rollback)
                raise
            finally:
                for _, _, temporary in prepared:
                    if os.path.exists(temporary): os.unlink(temporary)
            self.status = {"state": "running"}
            threading.Thread(target=self.run_build, daemon=True).start()
            return {"saved": True, "backup": backups[0], "backups": backups, "state": "running"}

    def run_build(self):
        try:
            self.rebuild()
            status = {"state": "done"}
        except Exception:
            status = {"state": "error", "message": "Source saved, but rebuild failed. See _build/editor-build.log."}
        with self.lock:
            self.status = status


def build(root=ROOT):
    root = Path(root)
    (root / "_build").mkdir(exist_ok=True)
    with (root / "_build" / "editor-build.log").open("w", encoding="utf-8") as log:
        subprocess.run([sys.executable, "tools/build_site.py"], cwd=root, stdout=log, stderr=log, check=True)
        args = ["jekyll", "build", "-s", "_site_src", "-d", "_build/preview/CTFWU"]
        en_args = ["jekyll", "build", "-s", "_site_src_en", "-d", "_build/preview/CTFWU/en"]
        env = dict(os.environ, JEKYLL_ENV="production")
        if shutil.which("bundle"):
            for command in [args, en_args]:
                subprocess.run(["bundle", "exec", *command], cwd=root, env=env, stdout=log, stderr=log, check=True)
        elif shutil.which("docker"):
            # Uses the cached Ruby image and gem volume; no credentials or repo publishing.
            subprocess.run(["docker", "run", "--rm", "-e", "JEKYLL_ENV=production",
                            "-v", str(root) + ":/work", "-v", "ctfwu-bundle:/usr/local/bundle",
                            "-w", "/work", "ruby:3.4-slim", "sh", "-c",
                            "bundle exec " + " ".join(args) + " && bundle exec " + " ".join(en_args)],
                           cwd=root, stdout=log, stderr=log, check=True)
        else:
            raise RuntimeError("Install Ruby/Bundler or use the documented Docker setup.")


def handler_for(store, port, authenticate=verify_owner):
    origins = {"http://127.0.0.1:" + str(port), "http://localhost:" + str(port)}
    cookie_name = "ctfwu_owner_" + str(port)

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(store.root / "_build" / "preview"), **kwargs)

        def trusted(self):
            # Reject DNS rebinding and cross-origin access, including GET session requests.
            host = self.headers.get("Host", "")
            origin = self.headers.get("Origin")
            site = self.headers.get("Sec-Fetch-Site")
            if "http://" + host not in origins or (origin and origin not in origins) or site == "cross-site":
                raise EditError(403, "Use the local editor from the preview origin.")

        def cookie(self):
            cookie = SimpleCookie()
            try: cookie.load(self.headers.get("Cookie", ""))
            except Exception: raise EditError(401, "Owner authentication required.")
            return cookie[cookie_name].value if cookie_name in cookie else ""

        def reply(self, code, data, cookie=None):
            raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(raw)))
            if cookie is not None:
                self.send_header("Set-Cookie", cookie_name + "=" + cookie + "; HttpOnly; SameSite=Strict; Path=/; Max-Age=" + str(SESSION_SECONDS if cookie else 0))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            url = urlsplit(self.path)
            if not url.path.startswith("/api/"):
                return super().do_GET()
            try:
                self.trusted()
                if url.path == "/api/editor":
                    try:
                        session = store.session(self.cookie())
                        return self.reply(200, {"enabled": True, "authenticated": True, "token": session["csrf"], "owner": session["owner"]})
                    except EditError:
                        return self.reply(200, {"enabled": True, "authenticated": False, "owner": REPOSITORY.split("/")[0]})
                store.session(self.cookie())
                if url.path == "/api/build":
                    with store.lock:
                        return self.reply(200, store.status.copy())
                if url.path == "/api/writeup":
                    params = parse_qs(url.query)
                    key = params.get("key", [""])[0]
                    if "lang" in params:
                        return self.reply(200, store.read(key, params["lang"][0]))
                    variants = {}
                    for lang in ("vi", "en"):
                        try: variants[lang] = store.read(key, lang)
                        except EditError as error:
                            if error.status != 404: raise
                    if not variants: raise EditError(404, "Writeup source not found.")
                    return self.reply(200, {"variants": variants})
                raise EditError(404, "Unknown API route.")
            except EditError as error:
                self.reply(error.status, {"error": error.message})

        def do_POST(self):
            try:
                self.trusted()
                if self.headers.get("Origin") not in origins:
                    raise EditError(403, "Invalid editor session. Reload the page.")
                if self.path not in ("/api/writeup", "/api/login", "/api/logout"):
                    raise EditError(404, "Unknown API route.")
                if self.path != "/api/login":
                    session = store.session(self.cookie())
                    if not secrets.compare_digest(self.headers.get("X-Editor-Token", ""), session["csrf"]):
                        raise EditError(403, "Invalid editor session. Reload the page.")
                if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                    raise EditError(415, "Expected JSON content.")
                size = int(self.headers.get("Content-Length", "0"))
                limit = 4096 if self.path == "/api/login" else 2 * MAX_CONTENT + 131072
                if not 0 < size <= limit:
                    raise EditError(413, "Request is too large.")
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise EditError(400, "Expected an object.")
                if self.path == "/api/login":
                    login = authenticate(data.get("token"))
                    cookie = store.login(login)
                    return self.reply(200, {"authenticated": True, "owner": login, "token": store.session(cookie)["csrf"]}, cookie)
                if self.path == "/api/logout":
                    with store.lock: store.sessions.pop(self.cookie(), None)
                    return self.reply(200, {"authenticated": False}, "")
                self.reply(200, store.save_many(data.get("key"), data.get("edits")))
            except EditError as error:
                self.reply(error.status, {"error": error.message})
            except (ValueError, TypeError):
                self.reply(400, {"error": "Invalid request."})
            except OSError:
                self.reply(500, {"error": "Could not save the source. Check file permissions."})

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=4173)
    parser.add_argument("--skip-build", action="store_true", help="Serve an already built preview")
    args = parser.parse_args()
    if not args.skip_build:
        build()
    store = EditorStore(ROOT, build)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(store, args.port))
    print(f"Preview + editor: http://127.0.0.1:{args.port}/CTFWU/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
