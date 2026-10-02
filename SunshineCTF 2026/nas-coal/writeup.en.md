# NAS Coal - Forensics (Medium)

**Flag:** `sun{yup_issa_gem}` · Files: `gem_collection.pptm`, 2229848 bytes, sha256 `929726804037cc9b2e8779814aabf88361a6f4035ca1d93803662bdee543e855`

## Challenge

"someone put coal in my gem collection :'^(" - a single `.pptm` file, no service, no
instance. The task is to find the `sun{...}` flag hidden inside the "gem" collection.

The challenge description hints at finding a piece of "coal" inside a collection of valuable items (gems, memes).

## Initial Analysis

The file is a `Microsoft PowerPoint 2007+` (`.pptm`) file, structurally a ZIP archive containing XML and VBA code.

Notable anomalies:
1. `ppt/media/` holds 6 images for 5 slides: five `.png` files and one `.jpg` named
   `image1.jpg&w=1920&q=75`. The JPEG is the outlier "coal" mentioned in the description.
2. `docProps/app.xml` declares `Slides=5, Notes=0, HiddenSlides=0`, indicating no hidden slides.
3. Slide 5 has a textbox with the text `> mfw olevba oneshot chall`. This is a direct hint to use the `olevba` tool.

## Exploit Chain

**Step 1 - Extracting the macro with oletools.** Run `olevba` to inspect the `ppt/vbaProject.bin` OLE compound file and extract the `MediaCache` module:

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

The macro contains a long Base64 string and references a `.invalid` domain. It merely prints the command to the console without executing it, acting as a decoy. However, the encoded content holds the flag.

**Step 2 - Decoding `-EncodedCommand`.** PowerShell's `-EncodedCommand` payload is encoded in UTF-16LE, preventing simple plaintext searches from finding the `sun{` string. A script must decode the Base64 sequence:

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

**Step 3 - The decoding result.** The Base64 blob starts at offset 4117 of `vbaProject.bin`, is 584 bytes long, and decodes to:

```
$campaign = 'sun{yup_issa_gem}'
$source = 'https://gem-cache.example.invalid/coal.bin'
$destination = 'coal.bin'
[pscustomobject]@{Operation='download'; Campaign=$campaign; Source=$source; Destination=$destination}
```

A comprehensive sweep of the file (including LSB steganography and DCT analysis on the images) confirms that this is the only valid flag hidden within the archive.

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
