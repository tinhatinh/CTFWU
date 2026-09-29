# You Cut Me Off — Forensics (Medium)

**Flag:** `sun{totallyoriginalchallengeidea}` · **Files:** `HEREYOUGO.PNG`, 38759 B, a Discord image 492x382 RGBA

## Challenge

The challenge description is only: "Here's a flag! It's uhhh ...... ............ ......................uhhhhhhhhhh..................... hmm....." plus one image file. The image is a screenshot of a Discord chat: someone named Ardian announces "today i will make a ctf challenge", posts a few memes, then "ill type it out just give me a second" - and the image ends right there. The challenge name, the number of dots in the description and the message cut off at the bottom edge all point at one thing: the ending has been cropped.

## Initial Analysis

The stego route was followed first, because the description suggests "the flag is inside the image". All three directions died:

1. Appended data / hidden chunks. Every chunk walked: `IHDR sRGB gAMA pHYs IDAT IEND`, exactly 0 bytes after `IEND`, no `tEXt`/`iTXt`/`zTXt`.
2. LSB and the alpha channel. Alpha is 255 across the whole image. The blue channel's LSB has up to 96% odd values, which looks very suspicious, but the Discord background color is `(50,23,23)` - even/odd/odd - so that skew belongs to the palette, not to embedded data.
3. Text in a color close to the background (contrast stego). Counting the distance to the background color and amplifying it 24 times: no text layer shows up.

The only notable thing left is a disproportionate compressed size: an IDAT of 38652 bytes for a 492x382 RGBA image is rather large for a low-color screenshot.

## Exploit Chain

**Step 1 - Compare the decompressed size against the declared size.** This is where the challenge differs from every other image stego task: no need to touch pixels, just read the header and decompress.

```python
raw = zlib.decompress(IDAT)
print(len(raw), 382 * (1 + 492 * 4))     # 823042  752158
```

`823042 / 1969 = 418` divides evenly, with `1969 = 1 + 492*4` being the stride of one RGBA row. All 418 rows use filter type 0. That means the real scanline buffer is 418 rows long, while `IHDR` declares only 382: 36 rows missing, exactly one message.

**Step 2 - Rebuild the image at its true height.** Drop the 1 filter byte at the head of each row, concatenate them and render with height 418.

```python
rows = [raw[i*1969 + 1:(i+1)*1969] for i in range(418)]
Image.frombytes("RGBA", (492, 418), b"".join(rows)).save("analysis/full.png")
```

The image revealed just under the line "ill type it out just give me a second" is Discord's message input box, containing exactly one line of text.

**Step 3 - Read it character by character.** Zoomed to 4x and 6x (`analysis/hidden4x.png`, `analysis/mid.png`), then inspected at 10x just the easily confused character pair (`analysis/glyphs.png`).

**Step 4 - Verifying correctness.** This is not guesswork: `823042` divides evenly by `1969` and every row has a valid filter byte (0), so 418 is the only row count consistent with the data; had the header been correct, the surplus would have been 0 bytes. The character between "challenge" and "dea" has a dot above it, so it is `i`, not `l`; the string closes with `}` immediately after.

## Flag
```bash
python solve.py
```

```
IHDR: 492x382  stride=1969  IDAT giải nén=823042 byte -> thực tế 418 dòng
số dòng bị ẩn: 36
đã ghi analysis/full.png và analysis/hidden.png
```

```
sun{totallyoriginalchallengeidea}
```
