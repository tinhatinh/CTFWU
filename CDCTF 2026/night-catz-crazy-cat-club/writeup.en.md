# Night Catz Crazy Cat Club - RevE Crypto (500 points)

**Flag:** `cdctf{with a glass in my paw and milk on my whiskers}`
**Attachment:** `cat_club_authenticator.out` (Size: 861072 B, SHA256: `4528f8454ae5c2db4b781f74a7e2be8ac1bb46d89218dd2d5b008d6f606b0a04`)
**Author:** alex

## Challenge

A console authenticator asks `When are you at your happiest?: ` and only lets you through when the
answer is exact. The challenge ships a single binary and no network address; the flag is the answer
itself, in the form `cdctf{secret cat phrase}`.

## Initial analysis

`cat_club_authenticator.out` is an x86-64 ELF statically linked against glibc, symbols intact. The
only application symbol is `main` at `0x403035`, and the next defined function is `call_fini` at
`0x4033e0`, so the challenge code is 907 bytes long and the rest of the file is library code.
`strings` over `.rodata` yields three lines belonging to the challenge (the prompt, the success
message, the rejection message) and nothing matching `cdctf{`, so the expected answer is not stored
in clear form anywhere in the file.

Inside `main` there are two interesting data regions, all 32-bit integers materialised on the stack
with direct `mov` instructions:

| Stack slot | Content | Role |
| --- | --- | --- |
| `[rbp-0x140] .. [rbp-0x8c]` | 46 values, `disp` spaced 4 bytes apart | Reference array |
| `[rbp-0x144]` | `0x67` | Key |
| `[rbp-0x148]` | initialised to `0` | Loop counter |
| `[rbp-0x14c]` | initialised to `1` | Valid flag |

Before the loop, the code applies a length constraint:

```assembly
403303: call   4010a0 <strlen>
403308: cmp    rax,0x2e          ; strlen(input) must be 46
40330c: je     403318
40330e: mov    DWORD PTR [rbp-0x14c],0x0   ; wrong length -> valid flag = 0
```

## Ruled out

Before settling on this reading, the following channels were tested and dropped (full log in `notes.md`):

1. **Looking for a clear-text flag in the file**: `strings` returns nothing matching `cdctf{`; the three
   challenge strings are only the prompt and the two messages. Dropped.
2. **Looking for a separate checker function**: `.symtab` has no application function other than `main`,
   and `main` contains no call to any hand-written routine. Dropped.
3. **`handle_zhaoxin` at `0x403430`**: it runs `cpuid` leaf 4 and walks cache descriptors with a modulo
   3 division. It is glibc CPU init code and `main` never calls it. Dropped.

## Exploit chain

**Step 1 - Read the comparison loop.** The whole check lives here; `A[i]` is slot `[rbp-0x140+4i]` and
`input` is the `fgets` buffer at `[rbp-0x80]`:

```assembly
40332c: mov    edx,DWORD PTR [rbp+rax*4-0x140]   ; A[i]
40333b: movzx  eax,BYTE PTR [rbp+rax*1-0x80]     ; input[i]
403340: movsx  eax,al
403343: xor    eax,DWORD PTR [rbp-0x144]         ; input[i] ^ 0x67
403349: cmp    edx,eax
40334b: je     403359                            ; match -> i++
40334d: mov    DWORD PTR [rbp-0x14c],0x0         ; mismatch -> print INVALID
```

The relation to invert is `A[i] == input[i] ^ 0x67`, which gives `input[i] == A[i] ^ 0x67` because XOR
is its own inverse.

**Step 2 - Extract the array from machine code.** The 46 immediates do not have to be transcribed by
hand: inside `main` each array element is produced by exactly one encoding `c7 85 <disp32> <imm32>`.
`exploit.py` keeps the instructions whose `disp` falls in `[-0x144, -0x8c]`, separates `0x67` at
`disp=-0x144` as the key, and sorts the remaining slots by `disp` to recover character order:

```python
slots = {}
for i in range(len(body) - 10):
    if body[i:i + 2] == b"\xc7\x85":  # mov DWORD PTR [rbp+disp32], imm32
        disp, imm = struct.unpack_from("<ii", body, i + 2)
        if KEY_DISP <= disp <= ARRAY_HI:
            slots[disp] = imm

key = slots.pop(KEY_DISP)
array = [v for _, v in sorted(slots.items())]
phrase = bytes(v ^ key for v in array).decode()
```

**Step 3 - Verification.** The decoded array satisfies these checks: the array has exactly 46 elements, matching the `cmp rax,0x2e` gate;
the value `0x47` repeats 10 times and `0x47 ^ 0x67 = 0x20` is a space, which matches the rhythm of an
English sentence; the other 36 values sit in 0x00-0x1e, so after the XOR they all land in the printable
ASCII range. The decoded string is `with a glass in my paw and milk on my whiskers` (46 characters,
nothing left to guess).

The binary was then run on Linux to check the recovered input. Because the artifact is an ELF, the Windows host
has to hand it to WSL (the `docker-desktop` distro does not mount `/mnt/c`, so it is copied over stdin):

```bash
cat files/cat_club_authenticator.out | wsl -d docker-desktop \
  -- sh -c 'cat > /tmp/ccc.bin && chmod +x /tmp/ccc.bin'
printf 'with a glass in my paw and milk on my whiskers\n' | wsl -d docker-desktop -- sh -c '/tmp/ccc.bin'
```

```text
When are you at your happiest?: 
Welcome to Night Catz Crazy Cat Club! Remember not to have tooo much fun!

          @@@@@@@                                                               
         @@@@@@@@@@@                           @@@@@@@                          
...
```

The full 46-line output is stored in `analysis/welcome_run.txt` (sha256
`3ce0ad080f5b8dd135ceed10d1be9c9db3ac25d2720d718424e2c31dc11bafe8`); the ASCII art shows a cat lying
next to a `GLASS OF MILK` label. The negative probe with input `wrong answer` prints exactly the
rejection branch (`analysis/rejected_run.txt`), which proves the test distinguishes the two branches:

```text
When are you at your happiest?: INVALID. You are NOT a cat. You are NOT welcome in our club. Now SCRAM, HUMAN!
```

The binary never prints a flag; the submitted value is the answer itself, wrapped in `cdctf{...}` as
the challenge statement requires.

## Flag

```bash
python exploit.py files/cat_club_authenticator.out
```

```text
[*] main()            : 0x403035 - 0x4033e0
[*] array             : 46 ints, [rbp-0x140 .. rbp-0x8c]
[*] xor key           : 0x67  ([rbp-0x144])
[*] length gate       : strlen(input) == 0x2e (46)
[*] prompt            : When are you at your happiest?: 
[+] secret response   : with a glass in my paw and milk on my whiskers
[+] flag              : cdctf{with a glass in my paw and milk on my whiskers}
```

Result:

```text
cdctf{with a glass in my paw and milk on my whiskers}
```

*The flag was produced by local decoding and verified by running the binary with this exact input
(see Exploit chain); it has not been cross-checked with a submission on the platform.*

## Reproduce

```bash
python exploit.py files/cat_club_authenticator.out
```

The `main` disassembly used for cross-checking: `analysis/main.asm`.
