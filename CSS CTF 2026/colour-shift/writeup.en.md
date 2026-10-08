# Colour Shift - Forensics (Beginner)

**Flag:** `CSSCTF{SHINE ON}`
**Attached file:** `colorshiftctf.bmp` (Size: 1,083,738 B, SHA256: `689f33baf1acdef5c58b61a493977a44384694ef87f07a1f0606f1f34035ef92`)

## Challenge

The provided content includes a BMP format file and a text description related to Isaac Newton's law of light dispersion. The single attached file is `colorshiftctf.bmp`, and the description refers to the principle of splitting light into basic color spectrum components. The flag format is specified as `CSSCTF{...}`.

## Analysis

The BMP is 599×602 pixels, 24 bits per pixel, using `BI_RGB`. `bfOffBits=138` and `biSizeImage=1083600` sum to the file size, so there are no trailing bytes after the pixel array. It has a 124-byte `BITMAPV5HEADER`, bitmasks `ff/ff00/ff0000`, and `biClrUsed=0`; there is no palette.

The image uses *The Dark Side of the Moon* artwork and is dark and noisy. Mean R/G/B values are 15.4, 32.1 and 38.1. R spans 0–255, while G peaks at 240 and B at 215, so the analysis checks the channels separately.

## Solution

**Step 1 - Separate the color component structure.**
Increasing the contrast of the full image also amplifies noise. Instead, estimate the background with a median filter and subtract it from the image:

```python
def residual(chan):
    bg = np.asarray(Image.fromarray(chan).filter(ImageFilter.MedianFilter(41)))
    return chan.astype(np.float32) - bg.astype(np.float32)
```

The 41-pixel kernel is wider than the text strokes and is used to estimate the background. In this test, the median filter produced fewer halos around the strokes than the Gaussian filter.

**Step 2 - Comparative analysis on each channel.**
After median absolute deviation (MAD) normalization and upscaling, the text is visible in R and in `R - B`. G and B do not show the corresponding line in that region. Subtracting B from R reduces the shared background noise and improves readability.

*(Illustrative image of the three-channel analysis results: `analysis/channels.png`)*

**Step 3 - Decode the text content.**
The signal band containing the text is located on the y-axis (ordinate) from line 404 to line 436, extending across the entire x-axis (abscissa) of the image.

```text
C S S C T F { S H I N E   O N }
```

There is a space between `E` and `O`. The gap is about 47 pixels, compared with a mean character spacing of 33 pixels. A Gaussian-filtered version showed a stroke resembling `/`; that stroke is absent from the median-filtered result.

**Step 4 - Validate the process (Verification).**
Read the text directly from y=404–436 in the processed image. Compare the channel views and the difference image to check the characters, especially the space in `SHINE ON`.

## Result

Executing the script:

```bash
python exploit.py files/colorshiftctf.bmp -o analysis
```

```text
file      : files/colorshiftctf.bmp  599x602
  residual R  : min  -78.0 max +245.0  p99.9 +208.0
  residual G  : min  -86.0 max +214.0  p99.9 +172.0
  residual B  : min  -65.0 max +182.0  p99.9 +142.0

red channel = R - B (minus median 41 background, 2x2 binning)
orthogonalization: med 0.080  MAD-sd 1.186  z[min] -7.4
wrote analysis\flag_line.png

text stroke pixel count: 2774 (>=1500 to be considered a text line)
```

The content of the resulting output file `analysis/flag_line.png` displays the successfully recovered text line.

Result:
```text
CSSCTF{SHINE ON}
```
