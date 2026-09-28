# CookieCorp Solution Notes (2026-09-27)

## Key Findings

**Architecture:** Single-page app with Express backend
**Endpoints discovered:**
- `POST /register` - Create user
- `POST /login` - Authenticate, returns session + role cookies  
- `POST /api/recipe` - Save cookie batch, returns ID
- `POST /api/recipe/{id}/submit` - Queue for inspection
- `GET /recipe/{id}` - View saved batch page
- `GET /review/{id}` - Inspector's-eye view page
- `POST /api/seal` - Quality inspector endpoint that stamps seals

**The Golden Seal Mechanism:**
From `/static/js/mixer.js`:
1. Page loads with `window.__recipe = {...ingredients...}`
2. JavaScript "dispenses" each ingredient as a cookie: `document.cookie = ing.name + '=' + ing.value`
3. Calls `POST /api/seal {recipeId: id}` with `credentials: 'same-origin'`
4. Server checks ingredients in cookies and returns:
   - `{seal: 'chief'}` → GOLDEN SEAL
   - `{seal: 'reviewed'}` → standard seal
   - `{error: ...}` → rejected

**Critical Insight:** The **ingredient values** are what matter, not just names! The mixer sets cookies where both name AND value from each ingredient.

## Testing Strategy

Need to test combinations like:
- Ingredient `name="flag"`, `value="sunshinectf"`
- Cookie header: `session=X; role=baker; flag=sunshinectf`

**Current blocker:** Rate limiting (429 Too Many Requests) on rapid /api/recipe or /api/seal calls.

## Next Steps When Unblocked

1. Create fresh account
2. Save batch with specific ingredients
3. Immediately call /api/seal with matching cookies
4. Check for golden seal response containing flag

## Hypothesis

Likely flag format: `sunshinectf{...}` based on other challenges and typical CTF patterns.

Possible secret ingredients:
- `flag=sunshinectf_flag`
- `secret_ingredient=FLAG`
- Multiple ingredients forming a key

EOF
echo "Notes saved"; cat solution_notes.md