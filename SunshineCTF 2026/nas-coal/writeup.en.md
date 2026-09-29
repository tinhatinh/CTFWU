# NAS Coal — Forensics (Medium)

**Flag:** `sun{yup_issa_gem}` · Files: `gem_collection.pptm`, 2229848 bytes, sha256 `929726804037cc9b2e8779814aabf88361a6f4035ca1d93803662bdee543e855`

## Challenge

"someone put coal in my gem collection :'^(" - a single `.pptm` file, no service, no
instance. The task is to find the `sun{...}` flag hidden inside the "gem" collection.

The author describes the challenge by its exact mechanism: in a pile full of valuable things
(gemstone pictures, Pepe memes) there is one piece of "coal" that looks worthless - and that
piece is the solution.

## Initial Analysis

`file` reports `Microsoft PowerPoint 2007+`; the `.pptm` extension means ZIP + VBA. Three
anomalies are visible straight away:

1. `ppt/media/` holds 6 images for 5 slides: five `.png` files and one `.jpg` named
   `image1.jpg&w=1920&q=75`, the kind of name produced when saving an image from the URL of an
   image optimizer. The only JPEG in a deck that is otherwise all PNG, literally the "coal"
   from the challenge text.
2. `docProps/app.xml` declares `Slides=5, Notes=0, HiddenSlides=0`, so there are no hidden slides.
3. Slide 5 has an accent-colored textbox with the text `> mfw olevba oneshot chall`.

Point 3 is the author stating the answer outright. The wording ("mfw" = my fucking reaction)
makes it read like a joke, which is why it is easy to walk past.

## Approaches Ruled Out

The full log is in `notes.md`. These channels were checked and dropped:

1. ZIP appended data / orphan entries: 63 entries, CRC and `compress_size` agree in both
   local↔central directions, 0 bytes left uncovered, no `extra` or `comment` fields.
2. One "image" actually being a different file (`coal.bin`): the magic of all 6 media files and
   of the thumbnail matches what is declared.
3. OOXML traps (`customXml`, `changesInfo`, rels, `[Content_Types]`): just a standard
   SharePoint template.
4. Hidden text in the slides (white text, off-canvas, zero-width, notes): scanning `<a:t>` over
   all slides plus the 11 layouts, masters and theme leaves only the meme content itself.
5. PNG LSB / bit-plane / alpha / filter-type: planes 1 and 2 scanned in both bit orders, per
   channel and across all three channels. Every touch of a `78 9C`/`1F 8B` header is noise,
   `zlib` errors out on decompression.
6. JPEG progressive DCT stego: 5 scans following the standard libjpeg pattern, no extra
   segments, no data after EOI.

## Exploit Chain

**Step 1 - Reading the macro with oletools.** `olevba` opens `ppt/vbaProject.bin` (the OLE
compound file living inside the ZIP) and extracts the `MediaCache` module:

```bash
pip install --index-url https://pypi.org/simple oletools
olevba gem_collection.pptm
```

```vba
Public Sub RefreshCache()
    Dim encoded As String
    Dim commandLine As String
    encoded = "JABjAGEAbQBwAGEAaQBnAG4AIAA9ACAAJwBzAHUAbgB7AHkAdQBwAF8AaQBzAHMAYQBfAGcAZQBtAH0AJwANAAoA..."
    commandLine = "powershell.exe -NoProfile -EncodedCommand " & encoded
    Debug.Print commandLine
End Sub
```

It looks like a decoy: the URL `https://gem-cache.example.invalid/coal.bin` uses the `.invalid`
TLD (which does not exist per RFC 2606) and the macro only calls `Debug.Print`, executing
nothing.

**Step 2 - Decoding `-EncodedCommand` anyway.** `sun{` never appears in plaintext anywhere in
the file, so this base64 string is the only place that could hold the flag. This challenge uses
its own flag format `sun{...}` (different from the `H7CTF{...}` of every other challenge in the
same event), so the whole file has to be re-searched for exactly that prefix:

```python
B64_RUN = re.compile(rb"[A-Za-z0-9+/=]{80,}")
FLAG    = re.compile(rb"sun\{[^}\n]{1,120}\}")

for m in B64_RUN.finditer(vba_bin):
    s = m.group(); s = s[: len(s) // 4 * 4]
    for skip in range(4):
        raw = base64.b64decode(s[skip:])
        text = raw.decode("utf-16-le", errors="ignore").encode("latin-1", "ignore")
        if FLAG.search(text):
            yield text
```

PowerShell's `-EncodedCommand` is always UTF-16LE, which is why `sun{` cannot show up under a
raw grep.

**Step 3 - The decoding result.** The base64 sits at offset 4117 of `vbaProject.bin`, is 584
bytes long in encoded form, and decodes to exactly 4 lines:

```
$campaign = 'sun{yup_issa_gem}'
$source = 'https://gem-cache.example.invalid/coal.bin'
$destination = 'coal.bin'
[pscustomobject]@{Operation='download'; Campaign=$campaign; Source=$source; Destination=$destination}
```

**Step 4 - Proving there is no other flag.** Every encoding variant (raw, UTF-16LE/BE,
reversed, ROT13, hex, base64 at 4 different offsets, base64-of-UTF-16, hex-in-file) was
generated over the 63 decompressed ZIP entries, over filter-reversed pixels, over the LSB
bit-planes, and over each individual OLE stream. There is only one `sun{...}` string in the
whole archive, the one from Step 3. So it is the flag, and the real decoys were the five stego
channels ruled out above.

## Flag
```bash
python exploit.py files/gem_collection.pptm
```

```
[*] files/gem_collection.pptm -> ppt/vbaProject.bin = 13312 byte
[+] PowerShell -EncodedCommand giai ma duoc:
    $campaign = 'sun{yup_issa_gem}'
    $source = 'https://gem-cache.example.invalid/coal.bin'
    $destination = 'coal.bin'
    [pscustomobject]@{Operation='download'; Campaign=$campaign; Source=$source; Destination=$destination}
[+] CO: sun{yup_issa_gem}
```
