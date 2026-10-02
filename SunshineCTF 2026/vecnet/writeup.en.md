# VecNet — Web (Hard)

**Flag:** `sun{k33p_your_emb3ddings_secur3!}`

## Challenge

"VecNet makes use of AI embedding technologies to speed up your database needs. Get started
today!" - `https://vec.web.2026.sunshinectf.games/`, no files provided.

The challenge goes through four layers, each one opening a key of the next: the public `/.git` hands
back a reverted `config.php`, `config.php` gives the credentials to read MailHog, MailHog gives the
vec2text parameters and the path to `specs.7z`, and Chroma on port 8000 holds three records, one of
which is left with nothing but a 768-dimensional vector. vec2text returns the sentence describing the
archive's password structure, and the password is found by brute-forcing against a hash already
present in the database.

The rest of the attack surface (SQLi, SSRF, XSS) has no way in; the hypotheses that were checked and
ruled out are listed at the end.

## Initial Analysis

```
443   Apache/2.4.68 + PHP/8.2.33   docroot = repo Git, /.git public
8025  MailHog web UI               chặn sau nginx Basic auth
8000  GET /api/v2 -> {"nanosecond heartbeat": ...}   = Chroma
```

Port 8000 was found by scanning the host's public ports. `paths.py` tried calling `/api/v2` on
443/8025/8000 alike; only 8000 returns the heartbeat JSON.

## Exploit Chain

### Step 1 - `/.git`: a reverted file still has its object

The reflog (`/.git/logs/HEAD`) lists all 5 SHAs, so nothing has to be guessed. `githist.py` is a
minimal loose-object reader (zlib, `<type> <len>\0<content>`; tree entry `<mode> <name>\0<20-byte sha>`),
walking each commit in turn and printing its tree:

```
3e02a92  initial site deploy
517ac72  add embed preview endpoint
c3cd120  add internal service config          <- config.php
130e195  REVERT: do not commit secrets        <- xoá file, thêm .gitignore
e6a0074  add htaccess                         <- HEAD
```

`git rm` only removes it from the tree; the old blob still lives in `.git/objects/c3/...` and Apache
serves that directory as static files:

```php
define('MAIL_ADMIN_URL',  'http://127.0.0.1:8025');
define('MAIL_ADMIN_USER', 'vecadmin');
define('MAIL_ADMIN_PASS', 'Emb3dPass2026!');
define('INTERNAL_API_KEY', 'vsk_live_aX92kLmNpQrStUvWxYz');
```

`INTERNAL_API_KEY` is no use at all. The Chroma here authenticates with HTTP Basic, and this key does
not change the response of any route among the 626 shapes that were swept.

### Step 2 - MailHog gives the parameters, not the flag

`GET http://...:8025/api/v2/messages` with Basic auth `vecadmin:Emb3dPass2026!` returns the whole
mailbox. Three messages, no flag, but two details:

* Greg to Mike: "Here are the vec2text specifications you were asking for earlier:
  num_steps=4, sequence_beam_width=5", with the link `http://...:8025/files/specs.7z`.
* Greg to Steve: "our ChromaDB database is not exposed to the open Internet, and is only
  accessible on our local servers, served with proper authentication to our web interface". That
  sentence is true in the literal sense, Chroma is not exposed to the Internet; it sits on port 8000
  of the same host.

### Step 3 - `fetch.php` and `specs.7z`

```php
const ALLOWED_URL = 'http://localhost/files/specs.7z';
if (!isset($_GET['url']) || !hash_equals(ALLOWED_URL, $_GET['url'])) fail_request(403, ...);
readfile('/var/www/html/files/specs.7z');
```

GET only, only one accepted `url` value, and no outbound request is ever made. What you get is the
archive:

```
Method = LZMA2:12 7zAES     1 member: flag.txt, 34 byte
```

The file listing inside the archive is not encrypted, so `7z l -slt` reveals the flag length in
advance. Every credential in hand (`Emb3dPass2026!`, `vsk_live_...`, `sunshinectf8_`, the available
sha256) returns "Wrong password".

### Step 4 - Chroma: reconstructing the route path

`GET /api/v2/collections` returns

```json
{"error":"route not allowed"}
```

exactly like the 625 other meaningless routes, so it is easy to misread as "special authentication
needed". Chroma 1.x has no such route; `/api/v2/collections` is the v1 shape, while the 1.x release is
organized per tenant. The route table came from the wheel (`chromadb/server/fastapi/__init__.py`,
fetched with `pip download chromadb==1.0.0 --no-deps` purely to read it):

```
/api/v2/auth/identity
/api/v2/tenants/{tenant}/databases/{database}/collections
/api/v2/tenants/{tenant}/databases/{database}/collections/{uuid}/get     POST
```

`auth/identity` is inside the allowed route group and returns the tenant and database names right
away:

```json
{"user_id":"","tenant":"default_tenant","databases":["default_database"]}
```

Putting it together:

```
GET  /api/v2/tenants/default_tenant/databases/default_database/collections
 -> [{"id":"455b419b-...","name":"VecNetDB","dimension":768,
      "configuration_json":{...,"embedding_function":null}, ...}]

POST /api/v2/tenants/default_tenant/databases/default_database
     /collections/455b419b-.../get
     {"include":["metadatas","documents","embeddings","uris"]}
```

Two things have to be correct: the path uses the UUID (putting the name `VecNetDB` there still gives
`route not allowed`), and `include` accepts only those five keys; calling it wrongly makes the server
answer 422 and list the valid values right away (`distances, documents, embeddings, metadatas, uris`).

Collection contents:

| id | type | document |
| --- | --- | --- |
| `magic_string` | plaintext | `sunshinectf8_` |
| `user_hash_sha256` | plaintext | `d8dd241199d2617765d7613fdd1df5358297b55f258647fe463de586bbfe3ebf` |
| `user_password_requirements` | embedding_only | `null`, 768-dimensional vector |

The two plaintext records do not open the archive. The record whose text is hidden has an
`embedding_fn` of `jxm/gtr__nq__32`, exactly the checkpoint vec2text loads for the `gtr-base` path, so
the parameters in Greg's email can be used as they are.

### Step 5 - vec2text

`pip install vec2text sentence-transformers` on Windows needs two patches, both caused by version
drift:

* `vec2text/__init__.py` imports `experiments`, and that file does `import resource` (POSIX only).
  Stub `sys.modules["resource"]` before importing.
* vec2text pins `low_cpu_mem_usage=True`; transformers 5 initializes the model inside
  `init_empty_weights()` so the default device becomes `meta`, then `InversionModel.__init__` loads a
  real T5 from within that context and `check_and_set_device_map()` raises. Rolling back to
  `transformers==4.53.2` + `sentence-transformers<4`.

The control run on a vector whose answer is known:

```
inversion(vec(magic_string)) -> '   suncf8_ '      cos 0.85
```

Off in exactly the way vec2text usually is (losing `shin`, `t`), meaning the harness works. For
`user_password_requirements`:

```
The user's first and last initials, three special characters followed by the magic string.
```

There is one more check that does not depend on the quality of the answer: use the frozen GTR inside
the corrector to re-embed the hypothesis and compare the cosine with the stored vector. cos = 0.9956,
clearly higher than the control, so the sentence above was recovered verbatim.

### Step 6 - The password: brute-forcing the sha256 instead of the 7z

That sentence gives the structure, not the letters:

```
<initials><3 special characters>sunshinectf8_
```

The space is `26*26` letter pairs × 4 case forms × `32^3` special characters = 88.6M combinations.
Trying them directly against the archive costs about 0.2 s each, i.e. more than 200 hours. But the
collection already hands over `user_hash_sha256`, and one sha256 takes about 1µs: the entire space runs
in about 35 seconds with 8 processes (`crack2.py`), and only candidates matching the digest are passed
on to 7z.

```
[+] GR$*#sunshinectf8_
```

`GR` are the initials of Greg Roberts, the three special characters are `$*#`.

### Step 7 - Opening the archive

```
$ python -c "subprocess.run(['7z','x','-y','-pGR$*#sunshinectf8_','-oanalysis/unpacked','files/specs.7z'])"
Everything is Ok
Size: 34

$ cat analysis/unpacked/flag.txt
sun{k33p_your_emb3ddings_secur3!}
```

## Flag
```
sun{k33p_your_emb3ddings_secur3!}
```

## Approaches Ruled Out

| Direction | Evidence for ruling it out |
| --- | --- |
| SSRF through `fetch.php` | `hash_equals` against one fixed string, GET-only, only `readfile` of a local file |
| IMAP/SMTP mailstore | mentioned in `index.html` but the port is not open to the outside |
| Token auth for Chroma | `INTERNAL_API_KEY` does not change the response of any route among the 626 shapes swept |
| The `/api/v2/collections` path | a v1 route; 1.x answers `route not allowed` because the route does not exist |
| The flag being in MailHog | all 3 messages read, no `sun{` string |
| The password being one of the known credentials | 7z answers "Wrong password" for every candidate |
| sentence-transformers to produce a comparison vector | `jxm/gtr__nq__32` on HF is a vec2text checkpoint, not an ST model; that path is dead, but the corrector already ships an embedder so a cosine oracle still exists |

## Reproduce

```
python exploit.py            # ~40s, no torch needed
python exploit.py --invert   # runs vec2text too, ~3 mins (cached model)
```

Both paths were re-run against the live instance after capturing the flag and produced exactly the
flag above.
