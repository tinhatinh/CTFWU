import base64, hashlib, hmac, json, re, struct, itertools, sys
from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

REF = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMDAxIiwiaWF0IjoxNzkwNDA1MDc3LCJleHAiOjE3OTA0OTE0Nzd9.gqT6WsJe13hA9L7M_viCPQxKiiKoDkNSMk2lc_8_iso"
h0, p0, s0 = REF.split(".")
SIGNING = (h0 + "." + p0).encode()
SIG = base64.urlsafe_b64decode(s0 + "=" * (-len(s0) % 4))

def b64u(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
def b64s(b): return base64.b64encode(b).decode()

def variants(d: bytes):
    """plausible textual renderings of a binary blob"""
    out = {d, d.hex().encode(), d.hex().upper().encode(), b64s(d).encode(), b64u(d).encode(),
           ":".join(f"{x:02X}" for x in d).encode(), d.hex().encode().upper()}
    # digests of the blob
    for alg in ("md5", "sha1", "sha256"):
        h = hashlib.new(alg, d).digest()
        out |= {h, h.hex().encode(), h.hex().upper().encode(), b64s(h).encode(), b64u(h).encode(),
                ":".join(f"{x:02X}" for x in h).encode(), h.hex().encode().replace(b"-", b""),
                h.hex()[:16].encode(), h.hex().upper()[:16].encode()}
    return out

cands = set()

# --- signing certificate material -------------------------------------------
der = open("apk/META-INF/ANDROIDD.RSA", "rb").read()
cands |= variants(der)
try:
    cert = x509.load_der_x509_certificate(der)
except Exception:
    # PKCS#7 wrapped: pull the embedded certificate
    from cryptography.hazmat.primitives.serialization import pkcs7
    cert = pkcs7.load_pem_pkcs7_certificates if False else None
    certs = None
    try:
        from cryptography.hazmat.primitives.serialization.pkcs7 import load_der_pkcs7_certificates
        certs = load_der_pkcs7_certificates(der)
    except Exception as e:
        print("pkcs7:", e)
    cert = certs[0] if certs else None
if cert:
    cder = cert.public_bytes(Encoding.DER)
    cands |= variants(cder)
    cands |= variants(cert.public_key().public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo))
    cands |= variants(cert.public_key().public_bytes(Encoding.OpenSSH, PublicFormat.OpenSSH)
                     if False else cert.public_key().public_numbers().n.to_bytes(
                        (cert.public_key().public_numbers().n.bit_length()+7)//8, "big"))
    cands |= variants(str(cert.serial_number).encode())
    cands |= variants(cert.subject.rfc4514_string().encode())
    cands |= variants(cert.issuer.rfc4514_string().encode())
    cands |= variants(cert.not_valid_before_utc.isoformat().encode())
    cands |= variants(cert.not_valid_after_utc.isoformat().encode())
    fp = hashlib.sha256(cder).digest(); f1 = hashlib.sha1(cder).digest()
    cands |= {b64u(fp).encode(), b64s(fp).encode(), fp.hex().encode(), f1.hex().encode(),
              fp.hex().upper().encode(), f1.hex().upper().encode()}
    print("cert subject:", cert.subject.rfc4514_string(), "serial:", cert.serial_number)

# --- every file in the package, plus declared digests ------------------------
import os, zipfile
for path in ["files/meridian-pay-3.2.1.apk", "apk/classes.dex", "apk/AndroidManifest.xml",
             "apk/resources.arsc", "apk/res/layout/activity_main.xml",
             "apk/META-INF/ANDROIDD.SF", "apk/META-INF/MANIFEST.MF",
             "C:/Users/Administrator/Downloads/meridian-pay-3.2.1.apk.zip"]:
    if os.path.exists(path):
        blob = open(path, "rb").read()
        cands |= variants(blob)
        cands |= variants(str(len(blob)).encode())
for name in zipfile.ZipFile("files/meridian-pay-3.2.1.apk").namelist():
    cands |= variants(zipfile.ZipFile("files/meridian-pay-3.2.1.apk").read(name))
for txt in [open("apk/META-INF/ANDROIDD.SF").read(), open("apk/META-INF/MANIFEST.MF").read()]:
    for dg in re.findall(r"([A-Za-z0-9+/=]{30,})", txt):
        cands |= {dg.encode(), dg.replace("=", "").encode(), base64.b64decode(dg + "="*(-len(dg)%4))}
    for hx in re.findall(rb"[\x20-\x7e]{6,}", txt.encode()):
        cands.add(hx)
# D8 embedded sha-1 + version strings
cands |= {b"084a89126ae0596c599143df57a654646af28313", b"9.2.4-dev", b"16885", b"12771"}

# --- keystore / debug-key passwords ------------------------------------------
for w in ["android", "androiddebugkey", "androiddebugstore", "debugkey", "ANDROIDD", "android1",
          "changeit", "meridian", "meridianpay", "MeridianPay", "password", "123456", "keystore",
          "alias", "alias1", "my-release-key", "release", "upload", "testkey", "secret"]:
    for s in {w, w.upper(), w.capitalize(), w+"!", w+"123", w+"1234", w+"@123", w+"2026"}:
        cands.add(s.encode())

print("candidates:", len(cands))
hit = None
for c in cands:
    try:
        if hmac.compare_digest(hmac.new(c, SIGNING, hashlib.sha256).digest(), SIG):
            hit = c; break
    except Exception:
        pass
print("SECRET BYTES:", hit)
if hit:
    open("jwt_secret.bin", "wb").write(hit)
