# Low on function names - Reverse Engineering (500 points)

**Flag:** `cdctf{Y_m4ny_functi0s_wh3n_f3w_d0_trick}` · **Files:** `low_on_fun.py`, 8690 B, sha256 `cb043a7dc96d316c7e46825268511bf5b0c2da38599ede991af237ccb7edff5f`

## Problem Description

The challenge ships a single Python file and asks what the author did to declare functions "more efficiently". The program is a flag checker: it reads input, validates the format, then prints a verdict. The goal is the input string the checker accepts, in the form `cdctf{...}`.

## Initial Analysis

Every function body is missing. Only an empty `changing()` and a 3069-byte blob on line 3 remain:

```python
def replacer(obj):new_fun = marshal.loads(obj);changing.__code__ = new_fun;return
def changing():return
def main():
    funs = functions.split(b'DELIM');replacer(funs[0]);flag = changing();replacer(funs[1]);
    if not changing(flag): return
    replacer(funs[2]);print(changing(flag.encode()).decode());return
```

The blob splits on the string `DELIM` into 3 `marshal` code objects of 326 / 497 / 2236 bytes, named `get_flag`, `init_checks`, `checker`. That is the answer to the "efficient declaration" question: the author never declared three functions. One anonymous function object has its `__code__` swapped through three stages, reusing the function object across the three stages.

The real obstacle is the interpreter version. A `marshal` code object carries no `.pyc` magic number, so nothing states which bytecode it belongs to. The machine has 3.9, 3.11, 3.12 and 3.14:

```text
===== py -3.9 =====
ValueError: bad marshal data (unknown type code)
===== py -3.11 =====
Segmentation fault   (exit=139)
===== py -3.12 =====
Segmentation fault   (exit=139)
===== py -3.14 =====
...
>Checking input...
That's the wrong length!
```

`dis` under 3.12 and 3.11 also returns nonsense (the first instruction is `POP_JUMP_IF_NOT_NONE`, and a function that only calls `input()` contains `LIST_TO_TUPLE` and `BEFORE_ASYNC_WITH`), because the inline cache width differs and the opcode framing shifts. Only CPython 3.14 runs the artifact, so all analysis below uses `py -3.14`.

## Routes Ruled Out

Before settling on this path, the following channels were tested and rejected (full log in `notes.md`):

1. **Disassembly with system Python 3.12 / 3.11**: opcodes decoded wrongly throughout, `IndexError: tuple index out of range`, and the very first instruction is already a conditional jump. Rejected as the wrong version.
2. **Trusting that `marshal.loads` succeeds and executing under 3.11 / 3.12**: both segfault (exit 139), since `marshal.loads` does not validate the cache layout and the interpreter runs mixed-version bytecode. Rejected.
3. **Brute-forcing input through the checker as an oracle**: the checker compares all 40 bytes once and returns one of two strings, `b"That's it!"` or `b'heck nah'`, with no per-character comparison and no recorded per-position oracle. Rejected as unnecessary, see Step 3.

## Exploit Chain

**Step 1 - Pin the version and split the three functions.** Use `py -3.14` as the decoder and dump each code object into `analysis/`:

```bash
bash analysis/run_triage.sh
py -3.14 analysis/dump_dis.py 2
```

**Step 2 - Read the constraints from `init_checks`.** `str(inp).startswith('cdctf')` and `len(inp) == 40`; `inp` is overwritten by `str(inp)`, so the length applies to the character string.

**Step 3 - Recognize that `checker` is RC4 and the keystream does not depend on the plaintext.** The 229 disassembly lines reduce to:

```python
def checker(data):
    key = bytes.fromhex('98e2...d92c')          # 128 byte, nhúng sẵn
    enc = ['61','2e','ba','33','6f','91','33', ...]  # LIST_APPEND 40 lan, tu 36 hang so
    check = bytes.fromhex(''.join(enc))         # 40 byte: dung chuoi phai tim
    S = list(range(256)); j = 0
    for i in range(256):                        # KSA
        j = (S[i] + j + key[i % key_length]) % 256
        S[j], S[i] = S[i], S[j]
    out = bytearray(); k = l = 0
    for byte in data:                           # PRSA
        k = (k + 1) % 256; l = (S[k] + l) % 256
        S[k], S[l] = S[l], S[k]
        out.append(byte ^ S[(S[k] + S[l]) % 256])
    if bytes(out) == check: return b"That's it!"
    return b'heck nah'
```

Two bytecode details: the parameter of `checker` is named `data` (varname 0) rather than `inp`, so one name serves both the input and the loop, and the `enc` list holds 40 elements while `co_consts` carries only 36 hex strings because indices 5 (`33`), 11 (`4c`) and 14 (`03`) are reused. Since `out = data ^ keystream(key)` and the keystream comes only from `key`, the condition `out == check` is equivalent to `data == check ^ keystream`, so decryption is direct and the oracle is never needed.

**Step 4 - Reverse the cipher.** The script does not need `marshal.loads`: the key and the hex pairs are present verbatim in the blob, so regex extraction makes it run on any Python 3.8+.

```python
check = bytes.fromhex(b"".join(pairs[i - 2] for i in ENC_ORDER).decode())
keystream = rc4_keystream(key, len(check))
flag = bytes(a ^ b for a, b in zip(check, keystream))
```

**Step 5 - Verification.** Length 40 matches the `init_checks` constraint and the prefix matches `cdctf`. Re-running the challenge's own checker under Python 3.14 prints `That's it!` for the full string while changing only the last character from `k` to `l` prints `heck nah`, confirming the checker distinguishes the recovered input from the tested incorrect input.

## Flag

```bash
python exploit.py files/low_on_fun.py
```

```text
[*] low_on_fun.py: 3069 bytes blob, 3 phan tu code (DELIM-split)
[*] ten ham trong 3 code object: get_flag, init_checks, checker
[*] khoa RC4: 128 byte, hex bat dau bang 98e29c5194c02970
[*] hang so 2-ky-tu tim thay: 36 (khop 36 muc co_consts cua checker)
[+] check = bytes.fromhex(''.join(enc)) -> 40 byte: 612eba336f913337b3de4c3b1e03f199014c12084a93e3f847d4bea54c03517f1bdc2718cc2d6cfb
[+] rc4_keystream(key, len(check)) -> XOR voi check
[+] flag = cdctf{Y_m4ny_functi0s_wh3n_f3w_d0_trick}
[+] khop rang buoc cua init_checks: prefix 'cdctf', do dai 40
[+] da luu flag.txt
```

```text
cdctf{Y_m4ny_functi0s_wh3n_f3w_d0_trick}
```

## Reproduce

```bash
py -3.14 analysis/dump_dis.py 1   # rang buoc dinh dang
py -3.14 analysis/dump_dis.py 2   # toan bo disassembly cua checker
python exploit.py files/low_on_fun.py
echo 'cdctf{Y_m4ny_functi0s_wh3n_f3w_d0_trick}' | py -3.14 files/low_on_fun.py
```

*The flag is derived from the artifact and confirmed by the challenge's own checker; this record has no scoreboard submission confirmation.*
