# Epic Rat Encoding - Reverse (498 points)

**Flag:** `cdctf{Tom_Bevill_Building_at_noon_next_week_Thursday}`
**Attached files:** `files/message_encoder.c`, 360 bytes, sha256 `738e4cbaa71cc9a48260ed6130718c04f66d910582a10d4760fc27466deb2734` · `files/nums.txt`, 160 bytes, sha256 `188ff63f2326345e495fffc6b2199384b87c021d92489a027354fe4d4f9085b5`
**Event:** CDCTF 2026 (Crimson Defense CTF) · **Author:** alex

## Challenge

The challenge ships `message_encoder.c` plus eight integers that supposedly describe a secret
meeting (where and when). The initialised string is gone from the C file
(`char* message = ""; // I think that Ratón deleted this part.`), so only the encoder body and its
numeric output remain. Required flag format: `cdctf{Place_Place_Place_at_time_time_time_Time}`.

## Analysis

- `nums[j] += message[i + 8 * j]` runs 8 times per `j`, and `nums[j] = nums[j] << 8` only runs when
  `i != 7`. With no shift after the last byte, the first byte of a chunk lands in the top 8 bits:
  `nums[j]` is `message[8j..8j+7]` packed big-endian into one `uint64_t`.
- 8 chunks × 8 bytes = 64 bytes. The flag format needs `Place_Place_Place` + `at` + four time
  tokens, i.e. roughly 47-64 bytes, so eight numbers are enough to hold the whole message.
- `uint64_t nums[8];` is uninitialised, so the C source has undefined behavior. Decode the supplied integers as big-endian bytes; initialise the array to zero in a reproduction of the encoder.

## Approaches tried

1. **`+=` as plain arithmetic** (each `nums[j]` being only the sum of 8 bytes, information lost):
   eight numbers would then carry about 8 bits each and could never rebuild 61 characters. The
   byte-packing reading produced clean ASCII on the first decode, so this is out.
2. **A self-built encoder printing wrong numbers**: on Windows, `printf("%lu")` with a `uint64_t`
   prints only the low 32 bits (LLP64, `long` is 4 bytes), which showed up as eight 10-digit tokens
   that decoded to interleaved dots and letters. Adding `-D__USE_MINGW_ANSI_STDIO=1` and printing
   with `%llu` restored the 19-20 digit values seen in the description. That is a build-environment
   trap, not part of the challenge.

## Solution

**Step 1 - Split each number into 8 big-endian bytes and concatenate.** There is no key and no
transform beyond that single packing step.

```python
nums = [int(t) for t in open("files/nums.txt").read().split()]
raw = b"".join(n.to_bytes(8, "big") for n in nums)
print("".join(chr(b) if 32 <= b < 127 else "." for b in raw))
```

```text
[*] 8 so -> 64 byte
[*] hex      : 4d656574206d652061742074686520546f6d20426576696c6c204275696c64696e67206174206e6f6f6e206e657874207765656b20546875727364617900256c
[*] printable: Meet me at the Tom Bevill Building at noon next week Thursday.%l
[*] byte sau NUL: 256c = %l (duoi cua chuoi format "%lu " trong binary)
[+] message (61 ky tu): Meet me at the Tom Bevill Building at noon next week Thursday
[+] flag      : cdctf{Tom_Bevill_Building_at_noon_next_week_Thursday}
[+] round-trip: re-encode bang vong lap C khop ca 8 so
```

**Step 2 - Fit the flag into the template.** `Meet me at the ` is the message introduction, excluded from the submitted value; `Place_Place_Place` maps
to `Tom_Bevill_Building`, `at` stays as is, and the last four tokens `time_time_time_Time` map to
`noon_next_week_Thursday` (final token capitalised, matching `Thursday`).

**Step 3 - Verify by re-running the encoder.** Feed the recovered string into the exact C loop and
compile it; the output must match all eight numbers from the description, not merely look readable.

```bash
gcc -O0 -D__USE_MINGW_ANSI_STDIO=1 -o analysis/encoder_reconstructed.exe analysis/encoder_reconstructed.c
./analysis/encoder_reconstructed.exe
```

```text
5576975263002879264 7022273403317198932 8029109180213651820 7791300427398276201 7955362869705469551 8029390844169057312 8603394173939509365 8247045712450168172
nums.txt          : [5576975263002879264, 7022273403317198932, 8029109180213651820, 7791300427398276201, 7955362869705469551, 8029390844169057312, 8603394173939509365, 8247045712450168172]
re-encode         : [5576975263002879264, 7022273403317198932, 8029109180213651820, 7791300427398276201, 7955362869705469551, 8029390844169057312, 8603394173939509365, 8247045712450168172]
identical         : True
```

The final two decoded bytes are `0x25 0x6c` = `%l`, matching the start of `"%lu "`. The loop reads 64 bytes from a 61-character message plus NUL, so it can read beyond the string. The supplied source and integers do not establish the memory placement of those trailing bytes.

## Result

```text
cdctf{Tom_Bevill_Building_at_noon_next_week_Thursday}
```

## Reproduce

```bash
python exploit.py files/nums.txt
```

Cross-check with the encoder itself:

```bash
gcc -O0 -D__USE_MINGW_ANSI_STDIO=1 -o analysis/encoder_reconstructed.exe analysis/encoder_reconstructed.c
./analysis/encoder_reconstructed.exe
```

No private keys or instance credentials appear in the script.
