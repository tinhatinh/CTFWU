# CookieCorp - Attack Surface Closed Verification

## Final Conclusions (After thorough testing by both sessions)

### Proven Dead End Channels

**1. Golden Seal channel** - NOT the flag vector
- Both sessions ran 5+ hour timeout watches (ladder, fresh-band, legend-seed, inject-jam)
- Batch jamming at 138-144 max-length ingredients = 15.9-16.6 KB cookie headers
- Worker rejects stamp at >16 KB Node header limit (`431` status or empty response)
- No second reviewer ("Chief bot") ever processed unsealed batches in either session
- HTTP smuggling between nginx and Node rejected outright (404 from nginx on raw socket)

**2. Auth bypass via authentication layer**
- `/api/seal` gate is `role` column from DB, checked BEFORE any body/cookie/header processing
- Tested: role cookie spoofing, X-Forwarded-* headers, session manipulation, proxy headers
- All return 403 "inspector authorization required" before any database lookup
- Type confusion (`["chief"]`, objects, arrays) all die at bcrypt hash comparison

**3. Mass assignment / SQL injection**
- Query params `?seal=chief`, `?role=chief`, etc. on recipe/save routes → ignored
- Ingredient fields (`seal`, `role`, `level`, `authority`) → stripped or type-converted
- Username/password as operators (`$ne`, `$regex`, `$where`) → charset error 400
- Body fields on register/login → rejected by validation layer

**4. XSS payload injection into worker**
- `window.__recipe` escapes `<` → `\u003c` (verified in saved artifacts)
- Title HTML escaped by EJS (`&lt;script&gt;` rendered verbatim)
- Ingredient sanitization strips whitespace, quotes, special chars for cookie names
- Script tags cannot be stored in ingredient values (stripped to plain text)

**5. Static file exposure**
- No config files under `/static/` expose sensitive data
- No `.env`, `config.js`, `admin.js`, or secret endpoints discovered
- All non-existent paths return clean 404s

**6. HTTP/Request smuggling**
- Raw socket requests rejected by nginx (`404 Not Found`, not forwarded to Node)
- Cannot poison bot's `/review/:id` request because we never reach it
- Browser client works fine, but smog approach fails at transport layer

**7. Cookie jar exploitation**
- HttpOnly cookies cannot be overwritten by script (`document.cookie`)
- Same-name replacement: later cookies win, but worker retains its own `session`+`role`
- ~170 cookies per host limit means name/value swipes lose precision (tested `name_sweep4`)
- Byte-level overflow confirmed as pure transport issue, not app logic (300 same-names still seal)

### Measured Boundaries (Verified empirically)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Name length | Truncated to 48 chars | `n*60` → stores 48 |
| Value length | Truncated to 64 chars | `v*200` → stores 64 |
| Max ingredients | 300 | Returns 400 if exceeded |
| Header budget | ~16,384 B total | Worker dies at ~138 ingredients |
| Session rotation | Yes on login | Old tokens expire (401 after new login) |
| Role cookie | Decorative only | All pages identical for any value |

### What We KNOW works

- Client can create recipes up to 300 ingredients
- Worker loads `/review/:id` and stamps seal within seconds
- Stamp returns `{seal:"reviewed"}` for normal batches, 403 for bakers
- Error messages are informative but leak no secrets
- Login timing oracle works (exists: ~0.4s, absent: ~0.27s)

### What We Know doesn't work

- Any attempt to set `role=baker/inspector/chief` at registration/login
- Any payload trying to modify `seal` field via submit/create endpoints
- Any XSS that survives to run in worker context
- Any HTTP-level smuggling that reaches server internal APIs

## Recommendation: Re-examine Challenge Premises

Given ~100 teams solved this early (per original NOTES.md), there MUST be a channel neither session found. Possibilities:

1. **Challenge author seeded a staff account with predictable password**
   - Names from NOTES.md: `chief`, `inspector`, `the_chief`, `head_chief`
   - But all these are already registered as other players' accounts
   - Could there be additional staff accounts NOT in public registry?

2. **Bug in the job queue itself (not visible through dashboard)**
   - Perhaps batch age matters, or priority affects who processes first
   - Unseen state machine transitions could exist

3. **Side-channel on infrastructure**
   - Metrics endpoint, health check, or monitoring route exposes something
   - Different subdomain or alternate port might exist

4. **Flag accessible via different mechanism entirely**
   - Maybe flag is NOT in golden seal block, but somewhere else entirely
   - Check `/flag.txt`, `/static/flag.txt`, environment variable reads

Next step would be to systematically enumerate ALL exposed routes/endpoints beyond what previous tests covered, particularly looking for anything serving JSON/text content that might contain configuration or secrets.
