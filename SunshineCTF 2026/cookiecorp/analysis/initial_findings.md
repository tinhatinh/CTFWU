# Initial Findings - CookieCorp (SunshineCTF 2026)

## Architecture

**Backend:** Node.js + Express (confirmed via `X-Powered-By: Express`)
**Frontend:** Inline JavaScript handlers on `/` (no separate static assets served)
**Session/Auth:** Token-based or cookie-based after login

## Confirmed Endpoints

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/` | HTML page with inline JS, login/register forms |
| POST | `/register` | JSON payload `{"username":"...","password":"..."}` → user creation |
| POST | `/login` | JSON payload `{"username":"...","password":"..."}` → authentication |

## Response Patterns

### Register validation:
- Username: `[A-Za-z0-9_-]{3,32}`
- Password: minimum length (tested "x" = too short, "test123" = ok)
- Duplicate username: returns `409 {"error":"username taken"}`
- Success: `200 {"ok":true,"user":"...","role":"baker"}`

### Login:
- Success: `200 {"ok":true,"user":"...","role":"baker"}`
- Failure: `401 {"error":"bad credentials"}`

### All other routes:
- Return `404 <!DOCTYPE html><html><body><pre>Cannot GET /route</pre></body></html>`
- This is the **default Express error handler**, meaning those routes are not defined

## Suspicious Patterns

1. **No static files**: Despite CSS link in HTML (`/static/css/retro.css`), all static paths return 404
   - The app is likely serving everything through a single `GET /*` catch-all route
   - Static assets might be served by nginx directly but not present in the app directory

2. **Inline-only frontend**: Form submissions use inline `onclick="reg()"` handlers that call `post()` to `/register` and `/login`, but there's no visible UI for submitting batches

3. **Role-based architecture**: Response includes `"role":"baker"` - suggests:
   - Multiple roles (baker, chief, inspector?)
   - Different endpoints based on role
   - Golden Seal mechanism tied to Chief role

## Hypothesis

The **batch submission flow** might be:
- A hidden endpoint like `/api/batch` or `/quality/inspect` that only works with proper auth cookies
- Accessed after successful login (need to capture session cookie)
- Or it could be an AJAX path that requires a specific header/token from login response

## Next Steps

1. Capture session cookie from successful login
2. Retry POST to potential batch endpoints with cookie header
3. Check if login response contains JWT/token
4. Try to access `/dashboard` or similar authenticated paths
5. Look for any documentation strings or debug endpoints (`/routes`, `/debug`)
