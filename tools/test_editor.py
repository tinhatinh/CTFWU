"""Data-integrity and request-boundary checks for the local writeup editor."""
import json
from pathlib import Path
import tempfile
import threading
import shutil
import datetime as dt
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from serve_site import EditorStore, EditError, handler_for
from fetch_ctftime import parse
from build_site import write_portfolio
import build_site
from unittest.mock import patch
from serve_site import verify_owner
import io


class OwnerTests(unittest.TestCase):
    def test_verified_user_must_be_repository_owner_even_if_collaborator(self):
        user = {"id": 1, "login": "collaborator"}
        repo = {"full_name": "tinhatinh/CTFWU", "owner": {"id": 2}, "permissions": {"admin": True, "push": True}}
        with patch("serve_site.urllib.request.urlopen", side_effect=[io.BytesIO(json.dumps(user).encode()),io.BytesIO(json.dumps(repo).encode())]):
            with self.assertRaises(EditError) as error: verify_owner("test-token")
            self.assertEqual(error.exception.status,403)

    def test_actual_owner_is_accepted(self):
        user = {"id": 2, "login": "tinhatinh"}
        repo = {"full_name": "tinhatinh/CTFWU", "owner": {"id": 2}}
        with patch("serve_site.urllib.request.urlopen", side_effect=[io.BytesIO(json.dumps(user).encode()),io.BytesIO(json.dumps(repo).encode())]):
            self.assertEqual(verify_owner("test-token"),"tinhatinh")

    def test_expired_session_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            store=EditorStore(root,lambda:None)
            cookie=store.login("tinhatinh")
            store.sessions[cookie]["expires"]=time.monotonic()-1
            with self.assertRaises(EditError):store.session(cookie)


class EditorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.path = self.root / "Example CTF 2026" / "sample" / "writeup.md"
        self.path.parent.mkdir(parents=True)
        self.path.write_bytes(b"# Sample - Web (Easy)\r\n\r\nOriginal.\r\n")
        self.english = self.path.with_name("writeup.en.md")
        self.english.write_text("# English\n", encoding="utf-8")
        self.store = EditorStore(self.root, lambda: None)
        self.key = "example-ctf-2026-sample"

    def tearDown(self):
        self.temp.cleanup()

    def test_save_updates_original_preserves_other_language_and_backup(self):
        before = self.path.read_bytes()
        english = self.english.read_bytes()
        current = self.store.read(self.key, "vi")
        result = self.store.save(self.key, "vi", "# Sample\n\nNội dung mới.\n", current["version"])
        for _ in range(100):
            if self.store.status["state"] != "running": break
            time.sleep(.01)
        self.assertEqual(self.store.status["state"], "done")
        self.assertEqual(self.path.read_bytes(), "# Sample\r\n\r\nNội dung mới.\r\n".encode())
        self.assertEqual((self.root / result["backup"]).read_bytes(), before)
        self.assertEqual(self.english.read_bytes(), english)

    def test_concurrent_external_change_is_not_overwritten(self):
        current = self.store.read(self.key, "vi")
        self.path.write_text("External edit\n", encoding="utf-8")
        with self.assertRaises(EditError) as error:
            self.store.save(self.key, "vi", "My edit", current["version"])
        self.assertEqual(error.exception.status, 409)
        self.assertEqual(self.path.read_text(), "External edit\n")

    def test_unknown_source_and_path_traversal_rejected(self):
        with self.assertRaises(EditError): self.store.read("../../Gemfile", "vi")
        with self.assertRaises(EditError): self.store.read(self.key, "../../Gemfile")

    def test_unchanged_save_does_not_rebuild_or_create_backup(self):
        current = self.store.read(self.key, "vi")
        result = self.store.save(self.key, "vi", current["content"], current["version"])
        self.assertFalse(result["saved"])
        self.assertFalse((self.root / "_build/editor-backups").exists())

    def test_http_requires_local_origin_and_owner_session(self):
        def authenticate(token):
            if token != 'test-owner-token': raise EditError(403, 'Not the owner')
            return 'tinhatinh'
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(self.store, 0))
        server.RequestHandlerClass = handler_for(self.store, server.server_port, authenticate)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        base = 'http://127.0.0.1:' + str(server.server_port)
        before = self.path.read_bytes()
        def post(route, body, headers=None):
            request = urllib.request.Request(base + route, data=json.dumps(body).encode(),
                headers={'Content-Type':'application/json', 'Origin':base, **(headers or {})})
            return urllib.request.urlopen(request)
        try:
            with urllib.request.urlopen(base + '/api/editor') as response:
                public = json.load(response)
                self.assertFalse(public['authenticated']); self.assertNotIn('token', public)
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(base + '/api/writeup?key=' + self.key + '&lang=vi')
            self.assertEqual(error.exception.code, 401)
            with self.assertRaises(urllib.error.HTTPError) as error:
                post('/api/login', {'token':'another-user-token'})
            self.assertEqual(error.exception.code, 403)
            with post('/api/login', {'token':'test-owner-token'}) as response:
                session = json.load(response); cookie = response.headers['Set-Cookie'].split(';')[0]
                self.assertIn('HttpOnly', response.headers['Set-Cookie'])
                self.assertIn('SameSite=Strict', response.headers['Set-Cookie'])
            for headers, expected in [({'Origin':'https://untrusted.example','Cookie':cookie,'X-Editor-Token':session['token']},403),
                                      ({'Cookie':cookie,'X-Editor-Token':'wrong'},403), ({'X-Editor-Token':session['token']},401)]:
                with self.assertRaises(urllib.error.HTTPError) as error: post('/api/writeup', {}, headers)
                self.assertEqual(error.exception.code, expected)
            current = self.store.read(self.key, 'vi')
            payload = {'key':self.key,'edits':[{'lang':'vi','content':current['content'],'version':current['version']}]}
            headers = {'Cookie':cookie,'X-Editor-Token':session['token']}
            with post('/api/writeup',payload,headers) as response: self.assertFalse(json.load(response)['saved'])
            with post('/api/logout',{},headers) as response: self.assertFalse(json.load(response)['authenticated'])
            with self.assertRaises(urllib.error.HTTPError) as error: post('/api/writeup',payload,headers)
            self.assertEqual(error.exception.code,401)
            self.assertEqual(self.path.read_bytes(),before)
        finally:
            server.shutdown();server.server_close();thread.join()

    def test_saving_both_checks_both_versions_before_writing(self):
        vi, en = self.store.read(self.key,'vi'),self.store.read(self.key,'en')
        self.english.write_text('External EN change',encoding='utf-8')
        before = self.path.read_bytes()
        with self.assertRaises(EditError):
            self.store.save_many(self.key,[{'lang':'vi','content':'New VN','version':vi['version']},
                                          {'lang':'en','content':'New EN','version':en['version']}])
        self.assertEqual(self.path.read_bytes(),before)
        self.assertEqual(self.english.read_text(),'External EN change')

    def test_saving_both_rebuilds_once_and_backups_both(self):
        from unittest.mock import Mock
        rebuild=Mock();self.store.rebuild=rebuild
        edits=[{'lang':lang,'content':'# New '+lang,'version':self.store.read(self.key,lang)['version']} for lang in ('vi','en')]
        result=self.store.save_many(self.key,edits)
        for _ in range(100):
            if self.store.status['state']!='running':break
            time.sleep(.01)
        self.assertEqual(len(result['backups']),2)
        self.assertEqual(self.path.read_text(),'# New vi')
        self.assertEqual(self.english.read_text(),'# New en')
        rebuild.assert_called_once()

    def test_partial_write_failure_rolls_back_both_files(self):
        import os
        original_replace=os.replace
        originals=(self.path.read_bytes(),self.english.read_bytes())
        edits=[{'lang':lang,'content':'# New '+lang,'version':self.store.read(self.key,lang)['version']} for lang in ('vi','en')]
        calls=0
        def replace(source,target):
            nonlocal calls
            calls+=1
            if calls==2:raise OSError('Simulated second-file failure')
            return original_replace(source,target)
        with patch('serve_site.os.replace',side_effect=replace):
            with self.assertRaises(OSError):self.store.save_many(self.key,edits)
        self.assertEqual((self.path.read_bytes(),self.english.read_bytes()),originals)
        self.assertEqual(self.store.status['state'],'idle')

    def test_failed_rebuild_keeps_saved_source_and_backup(self):
        def fail(): raise RuntimeError("Compiler unavailable")
        self.store.rebuild = fail
        current = self.store.read(self.key, "vi")
        result = self.store.save(self.key, "vi", "# Saved\n", current["version"])
        for _ in range(100):
            if self.store.status["state"] != "running": break
            time.sleep(.01)
        self.assertEqual(self.store.status["state"], "error")
        self.assertIn("# Saved", self.path.read_text())
        self.assertTrue((self.root / result["backup"]).exists())


class CTFTimeTests(unittest.TestCase):
    def test_zero_rating_with_explanation_link_is_preserved(self):
        fixture = '<title>CTFtime.org / R3:TURИ</title><a href="#rating_2026">2026</a><div id="rating_2026"><td class="place">8</td><td><a href="/event/1">CSS CTF</a></td><td>2066.0000</td><td>0.000<a href="/faq">*</a></td></div>'
        result = parse(fixture)
        self.assertEqual(result["years"]["2026"][0]["rating_points"], "0.000")
        self.assertTrue(result["years"]["2026"][0]["rating_pending"])
        final = parse(fixture.replace('<a href="/faq">*</a>', ''))
        self.assertFalse(final["years"]["2026"][0]["rating_pending"])

    def test_empty_or_changed_response_cannot_replace_cache(self):
        with self.assertRaises(SystemExit): parse("<title>CTFtime.org / R3:TURИ</title>")

    def test_new_competition_without_cover_gets_a_valid_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "_data").mkdir()
            source = Path(__file__).resolve().parent.parent / "site"
            for relative in ["assets/css/campus.css", "assets/js/site.js", "assets/js/editor.js", "assets/js/github-editor.js"]:
                target = stage / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source / relative, target)
            event = {"name": "Another & New CTF 2027", "slug": "another-new-ctf-2027",
                     "posts": [{"date": dt.datetime(2027, 1, 2), "cat": "Web"}]}
            write_portfolio(str(stage), [event], "vi")
            record = json.loads((stage / "_data/portfolio.json").read_text(encoding="utf-8"))["events"][0]
            self.assertEqual(record["count"], 1)
            self.assertTrue((stage / record["cover"].lstrip("/")).is_file())


class ImageTests(unittest.TestCase):
    def test_statement_and_inline_images_keep_paths_and_do_not_collide(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = root / "Example CTF" / "sample case"
            for relative, content in [("files/de.png", b"statement"), ("files/second.png", b"second"),
                                      ("analysis/de.png", b"inline"), ("analysis/proof.png", b"proof"),
                                      ("analysis/unreferenced.png", b"private")]:
                path = case / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(content)
            (case / "de.md").write_text('![de](files/de.png)\n![Second view](files/second.png)', encoding="utf-8")
            source = case / "writeup.md"
            text = '# Sample - Web\n\n![Inline](analysis/de.png)\n\nResult: `analysis/proof.png`\n'
            source.write_text(text, encoding="utf-8")
            date = dt.datetime(2026, 1, 2, tzinfo=dt.timezone.utc)
            post = {"text": text, "path": str(source), "case": "sample case", "title": "Sample - Web",
                    "date": date, "mod": date, "exact": True, "key": "example-ctf-sample-case", "cat": "Web"}
            stage = root / "stage"; stage.mkdir()
            event = {"name": "Example CTF", "slug": "example-ctf"}
            with patch.object(build_site, "ROOT", str(root)):
                generated = build_site.write_post(str(stage), event, post, "vi", "/CTFWU")
            rendered = Path(generated).read_text(encoding="utf-8")
            self.assertIn('/sample%20case/analysis/de.png', rendered)
            self.assertIn('/sample%20case/files/de.png', rendered)
            self.assertIn('/sample%20case/files/second.png', rendered)
            self.assertIn('/sample%20case/analysis/proof.png', rendered)
            target = stage / "assets/writeups/example-ctf/sample case"
            self.assertEqual((target / "files/de.png").read_bytes(), b"statement")
            self.assertEqual((target / "analysis/de.png").read_bytes(), b"inline")
            self.assertFalse((target / "analysis/unreferenced.png").exists())


if __name__ == "__main__":
    unittest.main()
