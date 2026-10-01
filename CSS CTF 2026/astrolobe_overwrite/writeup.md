# Astrolobe Overwrite — PWN/Reverse (746pts)

**Flag:** `CSSCTF{0ur0b0r0s_g00d_j0b_b01s_heh3_67}` · **Files:** `ouroboros.7z`, 4121 bytes, sha256 `e7aecc224f6ead512639a33f42f9aa0464ce309ea758b180764ec8dd053e5f2e`

## Đề bài

Binary `nexus_core` chạy trên dịch vụ netcat tại `34.116.80.78:7654`, nhận payload hex tối đa 512 byte và thực thi trong cửa sổ thời gian <45s (alarm). Nhiệm vụ là gửi chuỗi mã đủ để thỏa mãn 6 cổng kiểm tra nội bộ (“harmonic resonance”), từ đó kích hoạt ghi đè khóa hệ thống và nhận flag.

Dịch vụ in beacon số thập lục phân khi kết nối, sau đó chờ input dưới dạng chuỗi hex đại diện cho chương trình máy. Không có tài liệu, chỉ có message lỗi “COHERENCE FAULT”, “THERMAL DETONATION”, “HARMONIC FAULT” khi thất bại.

## Phân tích ban đầu

```text
elf64 x86-64 PIE NX full-relro
interpreter: /lib64/ld-linux-x86-64.so.2
entry: 0x12f0
imports: printf,fgets,time,fopen,fclose,strlen,puts,exit,alarm,setvbuf,sscanf
strings: "flag.txt", "[!] COHERENCE FAULT: Quantum state cold", 
         "[!] THERMAL DETONATION: Core runaway", "[+] TELEMETRY STABILIZED"
```

Nhấn mạnh: binary gọi `time()` và `alarm(45)` → tương tác real-time với deadline; logic kiểm tra không đọc trực tiếp flag mà yêu cầu trạng thái nội bộ đúng điều kiện toán học phức tạp.

## Các hướng đã loại

Trước khi chốt đã kiểm tra và loại các kênh sau (log đầy đủ ở `notes.md`):

1. **Symbolic execution bằng angr**: DLL load fail (`rustylib`), cannot step into native block. Loại vì không thể emulate ELF Linux trên Windows box hiện tại.
2. **Ghidra headless decompile script**: Jython gone, log báo `ClassNotFoundException`; không sinh ra file C source. Loại vì toolchain bị cắt mất Python/Jython support, phải dùng trampoline native thay vào đó.
3. **Docker/WSL2 runtime**: Docker daemon không chạy (`//./pipe/dockerDesktopLinuxEngine unavailable`); WSL chỉ có docker-desktop stopped. Loại vì không thể chạy ELF Linux nguyên bản để quan sát hành vi thực.
4. **Brute-force toàn bộ không gian w_k ∈ F_M^4**: 65521⁴ ≈ 1.8×10¹⁹ > khả năng tính toán. Loại vì cần phát hiện ràng buộc suy biến trước khi liệt kê.

## Chuỗi khai thác

**Bước 1 — Trích khối kiểm tra sang bộ nhớ thực thi trên Windows.**  
Vì không chạy được ELF Linux, tôi trích nguyên block kiểm tra (từ 0x15AD đến 0x1966) sang `VirtualAlloc(..., PAGE_EXECUTE_READWRITE)` và gọi nó qua trampoline Assembly: push registers, lưu rsp vào r14, sub stack, jmp code; khi rơi vào stub trả lại tag (0/1/2/3/…). Kỹ thuật này xác nhận từng nhánh lỗi riêng biệt, tránh đoán mò.

```bash
gcc -O0 -o one.exe one.c
one.exe seg
seg 15AD-15B1 -> 50 want 50
seg 15AD-15C8 -> 51 want 51
...
```

**Bước 2 — Mô hình hóa 6 đồng nhất thức mod 65521.**  
Suy ngược từ assembly thấy ba nhóm:
- Gates 0–3: `(X·C + T_i) mod 2^64 ≤ K` với `C = 0x58862fdccdf01111`, `K = 2^64 // M`. Vì `C·M ≡ 1 mod 2^64`, đây chính là phép quy về residue nhỏ nhất trong F_M.
- Gate 4: `c₁² = c₀³ + 17c₀ + 43 mod M`
- Gate 5: `c₃² = c₂³ + 17c₂ + 43 mod M`

Viết hàm verify trong Python (`model.py`) và so sánh 200 mẫu ngẫu nhiên với oracle → match 100%.

**Bước 3 — Tìm nghiệm trong không gian suy biến.**  
Biểu diễn hệ phương trình bằng mô hình, dùng C enumerate với OpenMP (tối ưu `-fopenmp`) quét miền `t₀∈[0..300]`:

```bash
gcc -O3 -fopenmp -o search.exe search.c
./search.exe 0 300
SOLUTION t=(1,218,59611,783)  u=(37101,35947,43627,40060) c=(37319,30037,44410,40061)
done: qr=9892500 hits=1
```

Nghiệm `(1, 218, 59611, 783)` duy nhất trong lát cắt đầu tiên, xác nhận bởi oracle ở nhiều beacon.

**Bước 4 — Assembler VM và xây dựng payload.**  
VM có 8 opcode được đánh địa chỉ qua bảng `P` hoán vị tự tham chiếu; mỗi lệnh 4 bytes được giải mã bằng `opcode = P[(byte0 ^ z) & 7]`. Dùng simulator `vm.py::build(beacon, TVEC)` để tạo chương trình 420 byte (105 lệnh, pc=114) chứa chuỗi hex đủ để đặt `w[0..3] = (t_i + beacon) mod M`.

```python
blob, v = vm.build(beacon, TVEC)
hexstr = binascii.hexlify(blob).decode()
s.sendall(hexstr.encode() + b"\n")
```

**Bước N — Kiểm chứng.** Beacon từ dịch vụ `0x13D6`, payload generate → PC=114 ∈ [112,128] thỏa alarm window, service reply `[+] TELEMETRY STABILIZED` rồi hiển thị flag.

## Flag

```bash
python exploit.py files/ouroboros.7z
```

```
BEACON: 0x13D6
beacon=0x13D6  pc=114  w=[5079, 5296, 64689, 5861]  bytes=420
[+] TELEMETRY STABILIZED. OVERWRITING SYSTEM MASTER KEY...
CSSCTF{0ur0b0r0s_g00d_j0b_b01s_heh3_67}
FLAG: CSSCTF{0ur0b0r0s_g00d_j0b_b01s_heh3_67}
```

## Reproduce

```bash
cd Downloads/CTFWU/CSS\ CTF\ 2026/_wip/astrolobe_overwrite
python exploit.py
```

Hoặc copy `exploit.py, vm.py, model.py` sang môi trường khác và chạy với `HOST="34.116.80.78"` `PORT=7654`.
