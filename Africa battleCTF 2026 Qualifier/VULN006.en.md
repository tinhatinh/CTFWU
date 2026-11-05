---
title: "VULN#006"
category: "Vuln Research"
tags: ["freetype", "ttbdf", "bdf", "sfnt", "out-of-bounds-read", "font-parser", "asan"]
solve_date: "2026-11-03T09:50:38+07:00"
language: "en"
points: 94
---

# VULN#006 — FreeType embedded BDF property lookup OOB read

**Flag:** `CTF{88315c14eccce5613b6913b8b89f53c7}`
**Service:** `169.58.126.107:7030`
**Flag format:** `CTF{}`

## Challenge

> VULN#006 — 94 points. A font-inspection service loads whatever font file you send it and reads one piece of metadata off it.

The service takes a 4-byte big-endian length followed by the raw font bytes. The handout is a FreeType **2.14.1** source tree plus a small harness. The target is a crash oracle: only the intended memory-safety bug returns the flag.

## Analysis

### Harness and target path

`harness/harness.c` performs exactly three FreeType calls:

```c
FT_New_Memory_Face(library, buf, len, 0, &face);
FT_Set_Pixel_Sizes(face, 0, 16);
FT_Get_BDF_Property(face, "FOO", &prop);
```

The last call reads the embedded `BDF ` table of an SFNT font — the path through `src/sfnt/ttbdf.c`, not the standalone BDF driver. The source tree is byte-identical to upstream 2.14.1 (only `harness/` was added).

### The bug

`tt_face_find_bdf_prop()` validates the property's string offset against `strings_size` but then gives `ft_memchr()` the *full* string-table size instead of the remaining size:

```c
if ( value < bdf->strings_size &&
     ft_memchr( bdf->strings + value, 0, bdf->strings_size ) )
```

The scan starts at `strings + value`, so it can read up to `value` bytes past the end of the string table. With `value = strings_size - 1` and no NUL byte after the last offset, the `memchr` walks off the allocation.

The bug dates back to 2005. It was fixed by FreeType commit `b6c6934` (2026-07-19, *"src/sfnt/ttbdf.c (tt_face_find_bdf_prop): Fix OOB read"*) and shipped in **2.15.0** (2026-10-12). The 2.15.0 security fixes are tracked as CVE-2026-50811 / CVE-2026-95512; the challenge uses the 2.14.1 parent.

### PoC construction

The PoC is a minimal SFNT built with FontTools containing a `BDF ` table that ends exactly at the end of the file:

| Element | Value |
|---|---|
| Strikes | 1 strike at 16 ppem |
| Property atoms | 1 — name `FOO` |
| String table | 1022 bytes: `FOO\0` followed by `A` bytes with no NUL |
| Property `value` | 1021 (`strings_size - 1`) |
| BDF table size | 1044 bytes, placed at EOF |
| Whole font | 1936 bytes |

`ft_memchr(strings + 1021, 0, 1022)` reads one byte from the final table byte and then continues past the allocation. ASAN confirms:

```text
ERROR: AddressSanitizer: heap-buffer-overflow ... memchr
  #1 tt_face_find_bdf_prop   src/sfnt/ttbdf.c:216
  #2 FT_Get_BDF_Property     src/base/ftbdf.c:82
  #3 main                    harness/harness.c:67
0 bytes to the right of 1936-byte region
```

PoC:

```text
foo.ttf
1,936 bytes
sha256 d88f2cb9f9cdf46370ce05ba55ae58b17ac0d337407f141eecfb92a550517921
```

### Remote

```python
import socket, struct

data = open("foo.ttf", "rb").read()
s = socket.create_connection(("169.58.126.107", 7030), timeout=10)
s.sendall(struct.pack(">I", len(data)) + data)
print(s.recv(4096).decode())
```

```text
status: crash confirmed (heap-buffer-overflow in embedded BDF property lookup)
FLAG: CTF{88315c14eccce5613b6913b8b89f53c7}
```

## Notes

- The service only reads one property (`FOO`), so the PoC only needs one property atom and one strike. No glyph loading or rendering is involved.
- The table must end at the end of the allocation for the over-read to leave the buffer; placing the `BDF ` table at EOF is the reliable way to do that.
- The fix for this class is to pass `strings_size - value` to `memchr`, not the full table size.

## References

- FreeType 2.14.1 `src/sfnt/ttbdf.c`
- FreeType commit `b6c6934a76fae579fce081b03e2e74aca17e7eeb` — "Fix OOB read"
- FreeType 2.15.0 release (2026-10-12)
- FreeType issue #1446 — heap-buffer-over-read in embedded BDF property lookup: <https://gitlab.freedesktop.org/freetype/freetype/-/work_items/1446>
