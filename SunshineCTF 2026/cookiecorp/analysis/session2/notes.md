# CookieCorp Notes (SunshineCTF 2026, web 479đ)

## Architecture Confirmed

**Frontend:** Single-page app with inline JS
**Backend:** Express + session cookies
**Key Endpoints:**
- `GET /` - login/register page
- `POST /register` - create user (req: username, password; res: {"ok":true,"user":"...","role":"baker"})
- `POST /login` - authenticate
- `GET /dashboard` - baker console (protected by session)
- `GET /builder` - cookie designer (protected by session)
- `POST /api/recipe` - save batch (req: {title, ingredients:[{name,value}]}, res: {"id":"...","ingredients":N})
- `POST /api/recipe/{id}/submit` - submit for Quality Inspector review

## Workflow

1. Register/Login → gets `session` cookie + `role:baker` cookie
2. Access `/builder` with session
3. Fill ingredients → "Save Batch" calls `/api/recipe`
4. Get back `{id: "...", ingredients: N}`
5. "Submit for Review" calls `/api/recipe/{id}/submit`
6. Queue shows in dashboard: "Inspector queue depth: 0 batch(es)"

## Investigation Goals

### Quality Inspector Logic

The description says "loads your recipe into the fabrication mixer and stamps a verdict." Need to find:
- What makes a recipe "approved"?
- What triggers "disapproved"?
- Is there a pattern or rule set?

### Golden Seal of the Chief

Description: "Only the Chief can award that seal." This suggests:
- There's a `/quality/inspect` or similar endpoint that inspects batches
- Regular inspectors give standard approval
- **Chief** role has special privileges
- Need to find if there's a `/admin` route or Chief-specific logic

### Route Discovery Strategy

From HTML extraction, routes are:
- `/dashboard`, `/builder` (user pages)
- `/recipe/{id}` - view saved batch
- `/logout` - destroy session
- `/api/recipe` - POST save, possibly GET list
- `/api/recipe/{id}/submit` - POST submit
- Potentially `/quality/inspect`, `/admin/chief`, etc.

## Next Steps

1. Test `/api/recipe` POST with a simple batch
2. Explore `/recipe/{id}` GET
3. Look for `/quality` or `/inspect` routes
4. Check if there are multiple roles (baker vs chief)
5. Try to find the Golden Seal award mechanism
