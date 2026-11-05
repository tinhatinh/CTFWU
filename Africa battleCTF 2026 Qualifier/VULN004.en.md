---
title: "VULN#004"
category: "Vuln Research"
tags: ["giflib", "gif", "double-free", "reallocarray", "thumbnail-service", "crash-oracle"]
solve_date: "2026-10-27T06:25:05+07:00"
language: "en"
points: 148
---

# VULN#004 — giflib double-free when the image counter reaches zero

**Flag:** `CTF{2637c464bb603890315dd4f99714c6ea}`
**Service:** `169.58.126.107:7029`
**Flag format:** `CTF{}`

## Challenge

> VULN#004 — 148 points. A thumbnail service decodes whatever GIF file you send it. You are given the exact source tree the target binary is built from.

The service accepts a 4-byte big-endian length followed by that many raw bytes. It runs a small harness that opens the GIF, calls `DGifSlurp()`, and closes the file, then reports whether the process crashed. The target is the "Ghost-Pixel" thumbnail service. Source is giflib **5.2.2**.

## Analysis

### The bug

giflib 5.2.2's `DGifDecreaseImageCounter()` in `dgif_lib.c` is called on the error path when an image fails to decode. It decrements `ImageCount`, frees the failed image's raster, and then tries to shrink the `SavedImages` array:

```c
void DGifDecreaseImageCounter(GifFileType *GifFile) {
    GifFile->ImageCount--;
    if (GifFile->SavedImages[GifFile->ImageCount].RasterBits != NULL) {
        free(GifFile->SavedImages[GifFile->ImageCount].RasterBits);
    }

    // Realloc array according to the new image counter.
    SavedImage *correct_saved_images = (SavedImage *)reallocarray(
        GifFile->SavedImages, GifFile->ImageCount, sizeof(SavedImage));
    if (correct_saved_images != NULL) {
        GifFile->SavedImages = correct_saved_images;
    }
}
```

When the failing image is the first one, `ImageCount` becomes `0` and the call is `reallocarray(ptr, 0, sizeof(SavedImage))`. On glibc, `reallocarray(ptr, 0, size)` behaves like `realloc(ptr, 0)`: it frees `ptr` and returns `NULL`. Because the return value is `NULL`, the code leaves `GifFile->SavedImages` pointing at the freed allocation. `DGifCloseFile()` later frees `SavedImages` again — a double free.

The upstream fix is commit `c2585d0` (2026-04-11, *"Avoid a dodgy edge case in reallocarray()"*, SourceForge bug #193):

```c
if (GifFile->ImageCount <= 0) {
    free(GifFile->SavedImages);
    GifFile->SavedImages = NULL;
    GifFile->ImageCount = 0;
    return;
}
```

A detail that decides whether the box crashes: the bundled `openbsd_reallocarray()` returns `NULL` on a zero count *without* freeing, so a build using that implementation does not double-free. The target uses the system `reallocarray` (`HAVE_REALLOCARRAY`), which does free.

### The pre-validator

The service rejects structurally incomplete GIFs before they reach giflib:

- zero-width image descriptors,
- images with no data block,
- complete pixel data but no `0x00` block terminator or `0x3B` trailer.

All of those return `status: not valid`. The PoC therefore has to be a structurally valid GIF that still makes `DGifSlurp()` fail during raster decoding.

## PoC

The working file is an 86,906-byte GIF89a with:

| Property | Value |
|---|---|
| Logical screen / GCT | valid GIF89a header and global colour table |
| Image descriptor | `4096 × 57585` — 235,868,160 pixels |
| LZW data | a complete sub-block chain with 16 growth-chain cycles (~117,934,080 pixels) |
| Termination | proper `0x00` block terminator and `0x3B` trailer |

The LZW stream fills only about half of the declared raster. The validator sees a complete structure, but `DGifSlurp()` decodes ~118 M pixels, hits the terminator early (`Error=112`, `ImageCount` goes from 1 to 0), and calls `DGifDecreaseImageCounter()`.

PoC reference (reconstructed from the solve session):

```text
poc_slow_invalid.gif
86,906 bytes
sha256 163f02c485e0e1f2c5722e509dfae126bb6e94afb69707778c7af4223695f17c
```

Local confirmation against the vulnerable build (`-DHAVE_REALLOCARRAY`):

```text
DGifSlurp returned 0 ..., ImageCount=0, Error=112
free(): double free detected in tcache 2   (SIGABRT)
```

ASAN attributes the second free to `GifFreeSavedImages()` via `DGifCloseFile()`. The default Makefile build, which uses the bundled `openbsd_reallocarray`, does **not** crash — that is why the vulnerability initially looked absent.

### Sending it

```python
import socket, struct

data = open("poc_slow_invalid.gif", "rb").read()
s = socket.create_connection(("169.58.126.107", 7029), timeout=10)
s.sendall(struct.pack(">I", len(data)) + data)
print(s.recv(4096).decode())
```

```text
status: crash confirmed (double-free in giflib decode cleanup)
FLAG: CTF{2637c464bb603890315dd4f99714c6ea}
```

## Notes

- The target distinguishes the intended crash from other crashes. Earlier triggers (zero-width image, missing terminator, missing data block) were rejected by the structural validator with `not valid`, so they never exercised the giflib error path.
- The important distinction is **structurally complete but raster-incomplete**: enough structure to pass the validator, but a decoding failure on the first image so the counter reaches zero.
- The service is a crash oracle; the successful packet returned the target signature and the flag.

## References

- giflib 5.2.2 `dgif_lib.c`
- giflib commit `c2585d037fb619aa2df06dc8ba44bf894bcfdba2` — "Avoid a dodgy edge case in reallocarray()"
- SourceForge bug #193 — double free in `DGifDecreaseImageCounter` when `ImageCount` reaches zero
