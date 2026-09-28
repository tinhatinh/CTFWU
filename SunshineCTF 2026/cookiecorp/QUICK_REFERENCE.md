# CookieCorp - Quick Reference (TL;DR)

## Key facts:
- **Flag location**: Only in `<div class="seal gold">...<div class="flag">sun{...}</div></div>` of Golden Seal
- **Gatekeeper**: `/api/seal` requires staff DB role (baker→403 always)
- **Worker**: Real browser loads `/review/:id`, writes ingredients as cookies, POSTs seal
- **Header limit**: Worker dies at ~16KB total headers → batch stays `reviewed` + NONE seal forever

## What's proven dead:
1. Role cookie spoofing (all variations 403)
2. Session token prediction/sharing (random per login, rotates on refresh)
3. Mass assignment via body/query params (always rejected or ignored)
4. XSS into worker context (escaped in `window.__recipe`)
5. Queue backlog triggering Chief (no evidence after 20h+ total watch)
6. HTTP smuggling (nginx rejects raw requests)

## Measurements:
- Ingredient clamp: name 48 bytes, value 64 bytes (truncated silently)
- Jam boundary: n≥138 max-length ingredients = header overflow = unsealed
- Login timing oracle exists (exists vs absent), but no credential attack found

## Next steps if continuing:
- Re-read challenge statement very carefully (maybe I'm missing something obvious)
- Check seeded accounts list from groundhog day notes (`chief`, `inspector`, etc.) - maybe one has simple password?
- Consider flag might come from different channel entirely

---

*Files in `analysis/` and `files/` are all available for inspection*
