# CookieCorp Investigation Log (2026-09-27)

## Successfully Tested Workflow

1. **Registration**: `POST /register {username, password}` → `{ok:true,user:"...",role:"baker"}`
2. **Login**: `POST /login` → session cookie + role cookie
3. **Save Recipe**: `POST /api/recipe {title, ingredients:[{name,value}]}` → `{ok:true,id:"...",ingredients:N}`
4. **Submit**: `POST /api/recipe/{id}/submit` → `{ok:true,status:"queued"}`

## Key Findings

### Endpoints Confirmed Working

| Method | Path | Auth Required | Description |
| --- | --- | --- | --- |
| GET | `/dashboard` | Yes | User console showing queue depth |
| GET | `/builder` | Yes | Cookie designer UI |
| POST | `/api/recipe` | Yes | Save batch to database |
| POST | `/api/recipe/{id}/submit` | Yes | Queue for inspection |
| POST | `/logout` | Yes | Destroy session |

### Routes That Don't Exist (404)

All of these returned HTML error pages (Express default):
- `/admin`, `/chief`, `/quality`, `/inspect`
- `/api/admin`, `/api/chief`, `/api/quality`, `/api/inspect`
- `/api/golden`
- `/api/recipes/:id/inspect`

### Golden Seal Mystery

The description says "Only the Chief can award that seal." Two possibilities:

1. **Hidden endpoint only accessible to Chief role**
   - Need to somehow get "chief" role
   - Could be stored procedurally or from a special user
   
2. **Ingredient-based unlocking**
   - Specific ingredients trigger special behavior
   - Like `"secret_ingredient": "golden_seal"` or similar
   - Or specific ingredient counts/names

3. **Role switching mechanism**
   - Maybe there's an admin panel somewhere
   - Or a way to create users with "chief" role

## Next Investigation Paths

### Path A: Role Discovery
- Check if there's a `/api/users` endpoint that lists all users
- Try creating user with role param in registration
- Look for privilege escalation via SQL injection or other vulns

### Path B: Ingredient Patterns  
- Try special ingredient names: `chef_secret`, `golden`, `chief`, `flag`
- Try exact strings mentioned in description: "Chief's Golden Seal"
- Look for patterns in successful inspections

### Path C: Route Enumeration
- Systematically sweep common paths: `/admin/*`, `/api/admin/*`
- Check if Express has any debug endpoints exposed
- Look for unhandled routes that might reveal something

### Path D: Session Analysis
- Decode cookies to see if they encode role information
- Check JWT signatures or session structure
- See if role can be modified client-side

## Immediate Action Items

1. Try ingredients with suspicious names (`chief`, `golden`, `secret`)
2. Test `/api/recipes` GET (list all batches?)
3. Check if login with existing username but wrong password reveals anything
4. Look for rate limiting or brute-force protections on routes

