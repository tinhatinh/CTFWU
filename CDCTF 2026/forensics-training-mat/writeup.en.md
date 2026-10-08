# Forensics Training Mat - Forensics (Training, 250 points)

**Flag:** `cdctf{A_Basic_Crimson_Disk_Exercise_in_Forensics}` · `cdctf{A_Little_XZtra_Tr3at!}` · `cdctf{d3l3te_w0_sync_h0l3y_C0W}` · `cdctf{f00rens!k_y!pP33}` (4/5, Part 2 still open)
**Files:** `suspicious.xz`, 109912 bytes, sha256 `9eed4778b09919b882670928dedcda98ac8962e95b1be338734076bdec9da9e5`

## Challenge

A CDCTF forensics training MAT: one `suspicious.xz` file plus a tutorial page split into 4 parts, with a quiz at the end. The card announces 5 flags and says all five must be submitted separately to CTFd. The tutorial page states that nothing can be skipped and that there is no shortcut hidden in its source.

## Analysis

`file` reports XZ and `xz -l` reports a 500.0 MiB uncompressed block. The decompressed artifact starts with a protective MBR followed by an "EFI PART" block, so this is a GPT disk image, not an archive. The partition table has four entries, labelled by the author, and each one holds a different filesystem:

| # | Label | Base (byte) | Size (byte) | Filesystem | Evidence |
| --- | --- | --- | --- | --- | --- |
| 0 | `billy` | 17408 | 4982784 | FAT32 | boot sector `"mkfs.fat"`, root cluster = 2 |
| 1 | `astrid` | 5242880 | 41943040 | ext2 | superblock `0xEF53`, compat has no `has_journal` bit |
| 2 | `hwk` | 48234496 | 130023424 | ext4 | incompat `extents+64bit+flex_bg`, ro_compat `metadata_csum` |
| 3 | `main` | 179306496 | 343932928 | btrfs | magic `_BHRfS_M` at offset 65536 |

Those four types match the answer key of quiz question q4 (vfat, ext2, ext4, btrfs), so the part-to-artifact mapping above is the one the challenge intends.

The filesystem parsers use Python `struct`. QR decoding uses `pyzbar`, with an OpenCV fallback.

## Approaches tried

1. **Sweep the whole image for `cdctf{` and take everything at once.** It yields exactly one string, `cdctf{d3l3te_w0_sync_h0l3y_C0W}`, six times inside partition `main`. The other three flags are not plaintext, and the quiz flag is not in the artifact at all. Ruled out as a general shortcut, but this is precisely the Part 4 solution.
2. **Recovering `flag1.png` from the deleted directory record.** Its LFN record carries the `0xE5` deletion marker, but cluster = 0 and size = 0, so there is nothing to recover. The live entry with the same name gives 405 bytes, the number the quiz asks for in the "Recovering Files" step.
3. **Treating the QR inside `flag2.jpg` as the flag.** The 610x610 image decodes to a taunt sentence, not a flag. The real core of Part 2 is the StegHide layer.
4. **Carving `flag2.jpg` from the offset where the JPEG magic was found.** That produces a JPEG without EOI. The actual cause was my block reader: blocks reached through the single indirect pointer were all assigned logical block number 0, which scrambles the order. Reading through the inode gives 82757 bytes ending with `FFD9`, and `exiftool` reports baseline DCT 610x610.

## Solution

**Step 1 - Part 1: FAT32, repair the PNG magic, read the QR.** The boot sector gives bytes/sector 512, sectors/cluster 1, 32 reserved sectors, a 75-sector FAT32 and root cluster 2. The `FLAG1 PNG` entry has size 405 and cluster 4. The first eight data bytes are `504e470d0a1a0a00`: the PNG signature lost its `0x89` byte, so the whole file is shifted one byte to the left and the leftover byte sits at the end. Repair = prepend `0x89`, drop the last byte. After the repair all six chunk CRCs validate and `IDAT` inflates to exactly `1665 = 111 * 15` bytes, so nothing else is broken.

```python
fixed = b'\x89' + data[:-1]          # data = 405 byte đọc từ cluster 4
w, h, bd, ct = struct.unpack('>IIBB', fixed[16:26])   # 111 x 111, bit depth 1, palette
```

The image is a QR version 17: 85 modules, one pixel per module, plus a 13 px quiet zone. Upscaled 6x and handed to `pyzbar`:

```
    QR -> 'cdctf{A_Basic_Crimson_Disk_Exercise_in_Forensics}'
```

**Step 2 - Part 3: ext4, split PNG/XZ, unxz.** `hwk` uses extents, so `ext4_extent_header` has to be parsed field by field (magic `0xF30A`; the `eh_max` field is easy to miss and then `eh_depth` reads from the wrong offset). Inode 13 is named `flag3.png`, size 1405 bytes. binwalk and the CyberChef Extract Files block only ever do one thing: cut at the magic `FD377A585A00`.

```
    carrier=1405 byte = PNG 917 byte + XZ 488 byte (ngat ngay sau IEND)
    XZ -> 559 byte, dong cuoi: b'cdctf{A_Little_XZtra_Tr3at!}'
```

The 559-byte payload is three charset lines, one lorem ipsum paragraph and the flag on the last line, so the 917-byte PNG is only the wrapper.

**Step 3 - Part 4: btrfs, `strings` on the partition.** `main` is the last partition and the one the quiz asks about snapshots: a deleted file whose data survives in the copy-on-write tree, plus extra copies in the metadata. Scanning the partition for plaintext is enough, with no mount and no `btrfs-progs`:

```
    cdctf{d3l3te_w0_sync_h0l3y_C0W} xuat hien 6 lan, offset dau [42122663, 42155821, 42270047]
```

Those six positions are why q14 asks which sub-command would have forced the deletion to commit before the drive was pulled (`sync`), and why q15 answers `strings`: the flag still reads straight off the partition.

**Step 4 - The quiz flag.** The tutorial page claims there is no shortcut in its source, yet the quiz flag sits in the JavaScript at the bottom of the page, gated only on answering all 15 questions:

```javascript
      // Sorry buddy, there's only one free flag here. You gotta get the rest the old-fashioned way -> Solvin' the challenges!
      if (score === total) {
        resultEl.textContent = 'Congratulations! You completed the CDCTF Digital Forensics Training MAT! Here is your flag to enter on the CTFd platform: cdctf{f00rens!k_y!pP33}';
```

The answer key below was parsed from the `questions` array in the same HTML (full dump in `analysis/quiz_answers.txt`): q1 `unxz`, q2 `Disk Image`, q3 `Autopsy + Volatility + losetup`, q4 `vfat + ext2 + ext4 + btrfs`, q5 `flag1.png`, q6 `405`, q7 wrong magic bytes, q8 `A JPEG of a QR Code`, q9 `StegHide`, q10 `1405`, q11 `CyberChef (Extract Files) + binwalk`, q12 `XZ`, q13 `A snapshot`, q14 `sync`, q15 `strings`.

**Step 5 - Verification.** Every measurement in the solution lines up with an independent quiz question: 405 (q6) is the size of `flag1.png` in FAT32, 1405 (q10) is the size of `flag3.png` in ext4, the four filesystem types (q4) are exactly the partition table, and the Part 4 flag appears many times inside `main` rather than in one live file. All four flags are strings copied from command output, none of them assembled by hand.

## Part 2 still open

`astrid` is ext2, inode 12 is `flag2.jpg`, 82757 bytes, a baseline grayscale JPEG 610x610 ending in `FFD9`; SHA-256 of the extracted copy: `c798f09c73a6195fb1db2aa46a7d696e08224cd59bf57cbaae5e058bf5be1f30`. The image is saved as `analysis/flag2.jpg`. The visible QR is only a taunt, the flag is in the StegHide payload (quiz q9 names exactly that technique).

The StegHide payload has not been extracted. Try extraction with an empty passphrase, then test the QR strings or a wordlist if needed. These steps have not yet produced a verified result.

1. Start Docker Desktop, run a Debian/Ubuntu container with `steghide` installed and try the empty passphrase first (`steghide extract -sf flag2.jpg -p '' -w out`).
2. If the empty passphrase fails, use `stegseek` with a wordlist; the most natural candidates are the QR strings the MAT itself hands out (the taunt in `flag2.jpg`, the text inside `flag3.png`).
3. Aperi'Solve runs every technique at once, but it means uploading the challenge artifact to a third party.

## Result

```bash
python exploit.py files/suspicious.xz
```

```
[0] files/suspicious.xz : 109912 byte, magic fd377a585a00 (XZ) -> unxz
    -> 524288000 byte, 512 byte dau la DOS/MBR boot sector: day la DISK IMAGE, khong phai archive
[1] GPT co 4 partition
    #0 billy   base=17408       size=4982784    loai=vfat
    #1 astrid  base=5242880     size=41943040   loai=ext
    #2 hwk     base=48234496    size=130023424  loai=ext
    #3 main    base=179306496   size=343932928  loai=?

[2] Part 1 - "billy" = FAT32
    'flag1.png' : 405 byte, 8 byte dau = 504e470d0a1a0a00 (thieu 0x89 -> PNG khong mo duoc)
    them 0x89 va bo byte duoi -> PNG 111x111 1-bit, CRC hop le cho moi chunk: True
    QR -> 'cdctf{A_Basic_Crimson_Disk_Exercise_in_Forensics}'

[3] Part 2 - "astrid" = ext2 (compat bit has_journal = False)
    ino=12 size=82757 -> analysis/flag2.jpg, JPEG 610x610, co EOI: True
    QR trong anh giai ra: "Don't worry, as lasy as it might feel lite challenge makers tene to ge, we hould never give you the same ihallenge twice in a row dith no meaningful differences. Ee put a lot of heart and soul into these things."
    -> day la chu thach thuc, khong phai co; co Part 2 nam trong payload StegHide

[4] Part 3 - "hwk" = ext4 (extents + 64bit + metadata_csum)
    root dir: [(11, 'lost+found'), (13, 'flag3.png')]
    carrier=1405 byte = PNG 917 byte + XZ 488 byte (ngat ngay sau IEND)
    XZ -> 559 byte, dong cuoi: b'cdctf{A_Little_XZtra_Tr3at!}'

[5] Part 4 - "main" = btrfs (superblock magic _BHRfS_M @65536)
    magic = b'_BHRfS_M'
    cdctf{d3l3te_w0_sync_h0l3y_C0W} xuat hien 6 lan, offset dau [42122663, 42155821, 42270047] (san pham cua snapshot, khong phai file song)

=== Cac co thu duoc tu artifact ===
  Part 1 (QR trong flag1.png)        cdctf{A_Basic_Crimson_Disk_Exercise_in_Forensics}
  Part 3 (XZ noi them sau PNG)       cdctf{A_Little_XZtra_Tr3at!}
  Part 4 (btrfs snapshot + strings)  cdctf{d3l3te_w0_sync_h0l3y_C0W}
  Quiz (doc tu JS cua trang tutorial) cdctf{f00rens!k_y!pP33}
  Part 2 (StegHide trong flag2.jpg)  con mo: can binary steghide + passphrase
[xoa] C:\Users\ADMINI~1\AppData\Local\Temp\cdctf_forensics_disk.img
```

## Reproduce

```bash
python exploit.py files/suspicious.xz
```

Needs `numpy`, `Pillow` and `pyzbar` for the QR step (the script falls back to `cv2.QRCodeDetector` when `pyzbar` is missing). The 500 MiB disk image is decompressed into `%TEMP%` and deleted when the run finishes.
