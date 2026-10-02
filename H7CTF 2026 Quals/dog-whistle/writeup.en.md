# Dog Whistle — Hardware (Insane)

**Flag:** `H7CTF{3c48f268-6761-422b-9df0-e652f6b2c4d0}` · **Service:** `nc pwn.h7tex.com 40918` · **Files:** `dog_whistle.zip` (firmware `aria` r7.2)

## Challenge

A smart speaker takes commands over audio, firmware `aria` r7.2. The challenge says the only thing standing between us and the engineering command set is a "spectrum sweep" in the 300 - 3400 Hz band. Objective: take the flag the firmware holds.

## Initial Analysis

The defence is not a filter. It is a second decoder, running on the signal *before* the nonlinear
amplification stage, while the *real* decoder runs on the signal *after* it. Feed a command in as tones
on the difference of two 4 - 6 kHz carriers and the original signal carries nothing in the control band,
so the guard decodes garbage, whereas after the nonlinear stage the command frame appears. Literally
"audible to a dog, not to a human".

| File | Contents |
|---|---|
| `aria` | ELF x86-64, PIE, stripped, 18 KB, dynamic |
| `SPEC.md` | transport + modem + TLV description |
| `eq.cfg` | 8 band, all 0 dB (flat) |
| `reference_ping.wav` | 24-bit/96 kHz mono, 15168 frames, already decoded to `A5 5A 02 10 00 12` |

The processing chain for one capture (reversed from `analysis/aria.asm`, cross-checked against `frontend_notes.md`):

```
base64 → parse WAV → 0x1940 EQ → 0x2550 GUARD → 0x1f70 P(x)
       → 0x1e30 LPF 7 kHz + hạ mẫu /6 → 0x2070 Goertzel → 0x2790 dispatch
```

`0x1f70` is the amplifier + transducer response, and it is memoryless:

```
u = 4x;   y = 0.98u + 0.05u² + 0.005u³        (≈ 3.92x + 0.80x² + 0.32x³)
```

`0x2070` analyses with a 200-sample Goertzel at 16 kHz - exactly a 200-point DFT, bins 80 Hz apart,
and the 16 control tones `800+80k` are precisely bins 10…25.

### The guard never looks at the spectrum, only at the opcode

`0x2550` has no bins, no 300 - 3400 Hz window, no thresholds. It calls `0x1e30` + `0x2070` again,
then walks the whole decoded TLV chain and returns 1 if it sees a record of type `0x01` or `0x02`.

Live verification:

```
payload 01 01 0E, điều chế tone thường   -> SAFETY LOCKOUT: engineering tone signature...
payload 01 01 0E, điều chế carrier-hiệu  -> PROFILE SELECTED: region 0x0e
```

The problem reduces to a single question: make the guard decode something different from the real decoder.

## Exploit Chain

**Step 1 - Difference tones.** The guard reads `x`; the real decoder reads `P(x)`. The `0.05u²` term
generates `cos(2π(f_p−f_q)t)`. Pick two carriers per symbol at bins `p = 51+B` and `q = 51` (4080 Hz and
`(51+B)·80` Hz); then `p−q = B` is the control bin we need to emulate. For `B ∈ 10..25`:

- `x` has energy only at bins ≥ 26, and exactly at multiples of 80 Hz, so it is orthogonal to every bin
  10…25 → the guard measures an absolute zero, and its argmax has no energy threshold so it always returns
  nibble 0 → an all-`00` byte string → no `A5 5A` → decode fails → the guard returns 0, no lockout.
- `P(x)` has exactly one component inside bins 10…25: the difference `p−q`. Every other product falls
  outside: `2q−p = 51−B ∈ [26,41]`, `p+q ≥ 28`, `3p`, `3q` out of band (and partly blocked by the 7 kHz LPF). Because
  each frequency is an integer number of cycles within the 200-sample window, the window separates them
  completely.
- Choosing `q = 51` (rather than something lower) is what keeps `51−B ≥ 26` for every `B ≤ 25`.

The carriers are generated directly at 96 kHz with `1200 sample/symbol`, i.e. exactly `m` cycles per
symbol, so the orthogonality still holds after downsampling.

```
DEBUG_PING đặt trên carrier-hiệu  -> PONG     (lần đầu tiên)
SELECT_PROFILE(0x0E) trên carrier -> PROFILE SELECTED + CAL ECHO
```

**Step 2 - Heap overflow in `SET_CAL_VECTOR`.**

```c
g_cal       = malloc(0x20);   /* 32 byte */
g_cal_desc  = malloc(0x30);   /* chunk ngay sau */
/* 0x2790, case 2 */
memcpy(g_cal, value + 1, 2 * value[0]);   /* value[0] do ta chọn, chỉ bị chặn bởi độ dài frame */
```

`count` is one byte ⇒ up to ~70 bytes can be written over a 32-byte region. The next chunk sits at
`g_cal+0x20` (prev_size), `g_cal+0x28` (size, `0x41`), `g_cal+0x30` (`desc.fn`).

`0x2970` runs after every accepted capture:

```c
if (g_cal_desc->fn == &inc32) g_hits += 2;
else { rdi = &g_hits; jmp g_cal_desc->fn; }     /* jumps, does not call */
```

Patching `desc.fn` alone buys a function call with an argument we do not have to care about.

**Step 3 - `CAL ECHO` leaks the function address on its own.** `SELECT_PROFILE(0x0E)` prints the first 16 bytes of `g_cal`.
The first 8 bytes are exactly the address of the show_flag function pointer:

```
CAL ECHO: 80 25 53 df bc 55 00 00 | d0 62 53 df bc 55 00 00
           ^ base+0x2580            ^ base+0x62d0 = g_cal+0x30 (which is the desc)
```

**Step 4 - three shots on the socket.** `exploit.py` (stdlib only + `analysis/enc.py`):

1. connect, send `SELECT_PROFILE(0x0E)` modulated on the carrier difference, parse `CAL ECHO` → `fn`;
2. send `SET_CAL_VECTOR(count=28)` - a 56-byte payload: `0..39 = 0`,
   `g_cal+0x28 = 0x41` (keeping the size intact so the heap is not corrupted), `g_cal+0x30 = fn`;
3. `0x2970` jumps into `show_flag`, which prints the flag; read the socket in a way that tolerates EOF/RST.

**Step 5 - Verifying the frame length.** The total frame length
`A5 5A 3E 01 01 0E 02 39 1C … CK` = 66 bytes = 132 symbols = 1.65 s, within the WAV's 2-second ceiling.

## Flag
```bash
python -u exploit.py
```

```
$ python -u exploit.py
[1] ===
[*] leak show_flag = 0x5619a36fa580
[*] 106 byte cuoi: CAL VECTOR WRITTEN: count=28 | FACTORY DIAG UNLOCKED |
    FLAG: H7CTF{3c48f268-6761-422b-9df0-e652f6b2c4d0} | ---- |
[+] FLAG: H7CTF{3c48f268-6761-422b-9df0-e652f6b2c4d0}
```

## Files

```
de.md  notes.md  writeup.md  flag.txt  exploit.py
analysis/
  unpacked/            dog_whistle.zip giải ra: aria, SPEC.md, eq.cfg, reference_ping.wav
  aria.asm             objdump -D -M intel .text
  frontend_notes.md    0x1940 / 0x1e30 / 0x1f70 / 0x2550 viết lại thành công thức
  enc.py               khung MFSK + generator carrier-hiệu (96 kHz, 1200 sample/symbol)
  client.py            socket event-driven, đọc tới dấu '----'
  exploit.py           the 3 steps above, prints flag or exits non-zero
  wav_ref.py           decode + kiểm chứng reference_ping.wav
  probe1-3.py sweep.py dẫn dò layout heap; tries/ phản hồi đầy đủ từng biến thể
  live1-8.txt          nhật ký phiên đích
files/dog_whistle.zip
```
