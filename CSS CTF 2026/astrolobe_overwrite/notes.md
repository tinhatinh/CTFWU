# Astrolobe Overwrite — analysis log

## Hypothesis tree (dạng bảng để đọc nhanh)

| STT | Giả thuyết | Kiểm tra | Kết quả | Ghi chú |
| --- | --- | --- | --- | --- |
| 1 | VM tự tham chiếu, bảng P hoán vị tại chỗ | Extract block 0x15AD–0x1966 sang Windows + trampoline, mỗi `jcc` → tag riêng | PASS 6 cổng: (1,218,59611,783) với beacon=0 | Trampoline dùng `mov r14,rsp`=49 89 e6 / `mov rsp,r14`=4c 89 f4; cần save/restore đúng |
| 2 | 4 cổng đầu là đồng nhất thức mod 65521 với `inv(65521)=C` | `C*65521 ≡ 1 (mod 2^64)`; ngưỡng K = floor(2^64/M); `r_i` nhỏ nhất trong `[LSB(T_i), LSB(T_i)+K]` | PASS oracle vs model 200 trạng thái, sau đó validate từng cổng riêng biệt | Oracle ở `one.exe`, mô hình trong `model.py` |
| 3 | 2 cổng cuối là đường cong Edwards `y² = x³+17x+43` | So sánh `s²` với `RT(c)` cho mọi c ∈ F_M | PASS trên 200 mẫu | Hàm `O(t)`: `pow(x,17,M)` rồi `rol(x,7)^0x1337` |
| 4 | Nghiệm suy biến có thực trong không gian 4 ẩn? | Liệt kê bằng C `-fopenmp` từ t_lo=0 đến t_hi=300 | Found `(1,218,59611,783)` ngay lát cắt đầu | Beacons khác nhau dịch nghiệm: `w_k = t_k + beacon mod M` |

## Command log (tóm tắt)

- Extract & list:  
  `7z l ouroboros.7z`, `7z x -y -oouroboros`
- Disassemble:  
  `objdump -d -M intel orig/ouroboros/nexus_core > nexus_core.asm`
- Build trampoline harness (Strawberry gcc):  
  `gcc -O0 -o one.exe one.c` (mỗi nhánh lỗi → tag 0/1/2/3)
- Validate gate logic (oracle vs model):  
  `one.exe seg`, `one.exe gran rnd 200 5 > gran.txt` → Python diff trong `model.py`
- Enumerate solutions:  
  `gcc -O3 -fopenmp -o search.exe search.c`, `./search.exe 0 300`
- Payload assembler:  
  `vm.py::build(beacon, TVEC)` tạo 420 byte hex (105 lệnh, pc=114)
- Exploit:  
  `python exploit.py` chạy socket tới `34.116.80.78:7654`, parse beacon, send hex blob

## Notes về trap khi chạy ELF Linux trên Windows

- `unicorn`/`pwn.ELF()` crash (access violation); `angr` fail load DLL
- WSL2/Docker không chạy được (`docker-desktop` stopped; npipe unavailable)
- Ghidra headless script Jython gone, log báo `ClassNotFoundException`; không sinh ra decompiled.c
- **Giải pháp:** copy đoạn bytecode trực tiếp vào `VirtualAlloc(..., PAGE_EXECUTE_READWRITE)` và gọi qua `__asm__` trampoline; trả lại stack bằng register còn sống (r14) tránh xung đột với opcode hoán vị tại chỗ

## Files in writeup

- `exploit.py` — socket client: connect → banner → beacon → payload (hex) → recv flag
- `vm.py` — VM simulator + assembler: `VM.beacon`, `VM.step()`, `encode()`, `build()`
- `model.py` — gate verifier: `gates(w,beacon)`, `gatevals()`, `Ofunc()`, residue targets
- `one.c` — oracle (native): trích khối check sang Windows, redirect mỗi nhánh tới stub tag
- `search.c` — C enumerator (OMP) liệt kê nghiệm trong F_65521^4
- `flag.txt` — `CSSCTF{0ur0b0r0s_g00d_j0b_b01s_heh3_67}`

## Time budget

- Banner read + beacon parse: ~5ms
- Hex generation + socket send: ~30ms
- Service reply (stabilized): immediate (within 1s)
- Tổng thời gian giải (local + remote): <5 phút cho final pass (chưa tính debug trampoline ~1h)
