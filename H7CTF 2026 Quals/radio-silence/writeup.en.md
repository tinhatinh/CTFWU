# Radio Silence - Hardware (Medium)

**Flag:** `H7CTF{6780856d-db42-4cfa-8b56-c62109d8417c}`
**Instance:** `https://web-0350e37b217a0cbc.web.h7tex.com`
**Files:** `capture.cf32` (393544 B, sha256 `167a70fa…`) - interleaved float32 LE I/Q, 1 Msps

## Challenge

A radio burst was transmitted next to a device nobody can name: no datasheet, no protocol notes, no label. The
challenge gives only a baseband file and says "Read it back", which means every parameter of the protocol has to be
measured from the signal itself.

## Analysis

```
$ curl -sS https://web-0350e37b217a0cbc.web.h7tex.com
file: capture.cf32 (complex baseband, interleaved float32 I/Q, little-endian: I0 Q0 I1 Q1 ...)
sample rate: 1000000 Hz
```

```python
raw = np.fromfile('files/capture.cf32', dtype='<f4')   # 49193 mẫu, 49.193 ms
iq  = raw[0::2] + 1j*raw[1::2]
```

The first thing is to decide amplitude modulation or frequency modulation. The histogram of `abs(iq)` is bimodal: one
cluster around 0 and one cluster around 1.0, which looks a lot like OOK (the previous challenge in the same event was
433 MHz OOK/Manchester). The run-lengths of the `abs > 0.35` gate reject that hypothesis right away:

```
total runs 5
   0  2909 0      im lặng đầu burst (noise floor)
2909 43200 1      continuous burst, unchanged envelope
46109   151 0
46260     1 1     blip đơn lẻ
46261  2932 0     im lặng cuối
```
The burst has a stable envelope over 43200 samples; zero-amplitude regions occur before and after it. The two tones in the FFT below support a 2-FSK decoder.

An FFT over the burst alone (Hanning, 23.1 Hz resolution) yields exactly two peaks:

```
+35.00 kHz   0.00 dB
+84.99 kHz  -2.68 dB
```

both sitting dead centre in their bins, so the real tones are 35 kHz and 85 kHz: a 60 kHz centre carrier, ±25 kHz deviation.

## Solution

### Step 1: symbol timing from the signal itself

Take the discriminators `diff(unwrap(angle(burst))) * fs / 2π`, smoothed over an 8 sample window. A histogram left with
only two clusters (around 35 and 85 kHz) proves 2 real frequency levels; the spread between the two clusters is the
level-transition samples.

Count the transition positions and examine them modulo each candidate period:

```
best symbol-period candidates:
   0.552  S=100  100.0 us  10000.0 baud
   0.552  S= 50   50.0 us  20000.0 baud      (harmonic of S=100)
   0.552  S= 25   25.0 us  40000.0 baud
   ...
top transition-train lines (Hz): [10001.9, 20003.7, ...]
```

S=100 is the fundamental period (50/25/10 are only harmonics of the same phase grid) and the transition pulse train has
a spectral line at exactly 10 kHz. 10 kBaud, so the 43200 sample burst carries `43200/100 = 432 symbol = 54 byte`, an
even number.

This is also where Manchester gets ruled out: Manchester with a 100 sample half-period would force a transition every
100 samples (≥431 of them), whereas the discriminators change level only 248 times over 431 symbol boundaries, i.e.
roughly the 50% transition density of random data at 10 kBaud.

### Step 2: deciding each symbol

Majority vote over the middle 80 samples of each 100 sample slot, tone 85 kHz = 1, packed MSB-first:

```python
states = (sm > 60e3).astype(np.int8)
slots  = [states[i*100+10:(i+1)*100-10] for i in range(432)]
bits   = np.array([s.mean() > 0.5 for s in slots], dtype=np.uint8)
frame  = np.packbits(bits).tobytes()
```

```
[*] decisions   min margin 0.500, 0/432 slots below 0.05 margin
[*] raw frame   aaaaaaaaaaaa2dd42b48374354467b36373830383536642d646234322d
                346366612d386235362d6336323130396438343137637d7a65
[*] as ascii    b'\xaa\xaa\xaa\xaa\xaa\xaa-\xd4+H7CTF{6780856d-db42-4cfa-8b56-c62109d8417c}ze'
[*] leftover    0 bits after the last whole byte
```
`min margin 0.500` shows that the samples used for each symbol all select the same tone. No symbol in this capture has a tied decision between the two tones.

### Step 3: eliminating the other 3 bit assignments

The four combinations (high/low tone = 1, MSB/LSB) give only one meaningful result:

```
t85=1 MSB   printable 46/54  b'\xaa\xaa...H7CTF{6780856d-db42-...'
t85=1 LSB   printable 25/54  rác
t35=1 MSB   printable  7/54  rác
t35=1 LSB   printable 18/54  rác
```

## Measured frame structure

| region | bytes | remarks |
| --- | --- | --- |
| preamble | `aa aa aa aa aa aa` | `0b10101010`, the alternation string used for bit sync |
| header | `2d d4 2b` | not identifiable, plausibly device id + command type |
| message | `48 37 43 54 46 7b … 7d` | `H7CTF{6780856d-db42-4cfa-8b56-c62109d8417c}` (43 B) |
| Trailer | `7a 65` | Meaning unknown. The recorded sum8, xor8 and CRC16 checks do not match; no specific field type is established. `sum8=0x9f` · `xor8=0xf7` · `0xdeea` · `0xd655` · `0x2d08` · `0x9657` · `0x7a65` |

Nothing is submitted over HTTP: the instance serves exactly one static file (`Server: SimpleHTTP/0.6`), with no `<pre>`
submission contract like the other web/hardware challenges of the same event, so the flag is pasted into the scoreboard.

## Result
```
$ python solve_rf.py files/capture.cf32
[+] FLAG: H7CTF{6780856d-db42-4cfa-8b56-c62109d8417c}
```
