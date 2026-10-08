# Astrolobe Overwrite - Pwn/Reverse (Expert, 746pts)

**Flag:** `CSSCTF{0ur0b0r0s_g00d_j0b_b01s_heh3_67}`
**File đính kèm:** `ouroboros.7z` (Kích thước: 4121 bytes, SHA256: `e7aecc224f6ead512639a33f42f9aa0464ce309ea758b180764ec8dd053e5f2e`)

## Đề bài

Đề cung cấp một binary `nexus_core` được triển khai dưới dạng dịch vụ qua giao thức netcat tại địa chỉ `34.116.80.78:7654`. Dịch vụ này tiếp nhận đầu vào (payload) dưới dạng chuỗi hexa, với dung lượng giới hạn tối đa 512 byte. Toàn bộ quá trình thực thi bị khống chế thời gian bởi một hàm alarm dưới 45 giây. Mục tiêu là gửi một chuỗi mã có khả năng thỏa mãn 6 cổng kiểm tra nội bộ (được gọi là "harmonic resonance"). Khi hệ thống vượt qua các vòng kiểm tra này, lệnh ghi đè khóa hệ thống sẽ được kích hoạt và trả về flag.

Khi kết nối, dịch vụ sẽ xuất ra một mã tín hiệu (beacon) dưới dạng hệ thập lục phân, sau đó chờ nhận dữ liệu đầu vào. Dữ liệu này phải là một chuỗi hexa đại diện cho một chương trình mã máy cấp thấp. Hệ thống không cung cấp tài liệu kỹ thuật đi kèm; nếu kiểm tra thất bại, nó chỉ phản hồi bằng các thông báo lỗi tĩnh như "COHERENCE FAULT", "THERMAL DETONATION", hoặc "HARMONIC FAULT".

## Phân tích

Đánh giá binary:
```text
elf64 x86-64 PIE NX full-relro
interpreter: /lib64/ld-linux-x86-64.so.2
entry: 0x12f0
imports: printf, fgets, time, fopen, fclose, strlen, puts, exit, alarm, setvbuf, sscanf
strings: "flag.txt", "[!] COHERENCE FAULT: Quantum state cold", 
         "[!] THERMAL DETONATION: Core runaway", "[+] TELEMETRY STABILIZED"
```

Điểm cốt lõi: Binary thực hiện gọi hàm `time()` và `alarm(45)`. Điều này áp đặt một yêu cầu tương tác theo thời gian thực (real-time) với một giới hạn khắt khe. Các khối logic kiểm tra không đọc trực tiếp file flag; thay vào đó, hệ thống yêu cầu các biến trạng thái nội bộ phải thỏa mãn các hệ điều kiện toán học phức tạp trước khi cho phép truy cập.

## Lời giải

**Bước 1 - Trích xuất khối kiểm tra và chạy độc lập qua Assembly Trampoline.**
Do không thể biên dịch mã phân tích ELF Linux trực tiếp cho môi trường giả lập, toàn bộ khối mã kiểm tra (từ địa chỉ `0x15AD` đến `0x1966`) được trích xuất thẳng vào vùng nhớ của một ứng dụng kiểm thử trên Windows thông qua lệnh `VirtualAlloc(..., PAGE_EXECUTE_READWRITE)`. Đoạn mã này được kích hoạt thông qua một trampoline Assembly: sao lưu các thanh ghi (`push registers`), lưu con trỏ stack `rsp` vào `r14`, cấp phát stack tạm, và `jmp` thẳng vào khối mã. Khi đoạn mã gặp nhánh trả về, nó sẽ thoát ra stub và xuất thẻ định danh lỗi (tag: 0, 1, 2, 3, v.v.). Kỹ thuật này giúp phân lập và xác nhận chính xác điều kiện của từng nhánh lỗi, để đối chiếu điều kiện của các nhánh đã thử.

```bash
gcc -O0 -o one.exe one.c
one.exe seg
seg 15AD-15B1 -> 50 want 50
seg 15AD-15C8 -> 51 want 51
...
```

**Bước 2 - Mô hình hóa hệ thống 6 phương trình đồng dư modulo 65521.**
Quá trình dịch ngược assembly phân mảnh logic thành ba nhóm phương trình chính:
- Nhóm Gates 0–3: Có dạng `(X·C + T_i) mod 2^64 ≤ K`, trong đó `C = 0x58862fdccdf01111` và `K = 2^64 // M`. Dựa trên tính chất đại số `C·M ≡ 1 mod 2^64`, phương trình này thực chất là thao tác quy đổi về thặng dư nhỏ nhất (least residue) trên trường hữu hạn `F_M`.
- Nhóm Gate 4: Có dạng `c₁² = c₀³ + 17c₀ + 43 mod M`.
- Nhóm Gate 5: Có dạng `c₃² = c₂³ + 17c₂ + 43 mod M`.

Viết mô hình Python trong `model.py` và đối chiếu với oracle trên 200 mẫu ngẫu nhiên. Cả 200 mẫu đã thử cho kết quả khớp; đây là kiểm tra trên tập mẫu đó, không phải chứng minh cho mọi input.

**Bước 3 - Giải hệ phương trình thông qua không gian suy biến.**
Dựa trên mô hình toán học đã thiết lập, một mã nguồn bằng ngôn ngữ C được tối ưu hóa đa luồng (sử dụng OpenMP qua cờ `-fopenmp`) được sử dụng để quét không gian biến `t₀∈[0..300]`:

```bash
gcc -O3 -fopenmp -o search.exe search.c
./search.exe 0 300
SOLUTION t=(1,218,59611,783)  u=(37101,35947,43627,40060) c=(37319,30037,44410,40061)
done: qr=9892500 hits=1
```

Hệ thống ghi nhận ứng viên `(1, 218, 59611, 783)` trong dải quét đầu tiên. Nghiệm này sau đó được chứng minh tính chính xác thông qua đối chiếu với thông số beacon trên máy chủ.

**Bước 4 - Mô phỏng máy ảo Assembly (Assembler VM) và thiết lập Payload.**
Dịch vụ sở hữu một máy ảo (VM) thực thi 8 mã lệnh (opcode). Các opcode này được đánh địa chỉ thông qua bảng hoán vị tự tham chiếu `P`. Cụ thể, mỗi khối lệnh 4 byte được giải mã theo công thức `opcode = P[(byte0 ^ z) & 7]`. Sử dụng bộ mô phỏng `vm.py::build(beacon, TVEC)` để sinh ra một mã máy cấp thấp dung lượng 420 byte (bao gồm 105 lệnh, giá trị Program Counter pc=114). Mã máy này đảm bảo khởi tạo đúng dải biến `w[0..3] = (t_i + beacon) mod M`.

```python
blob, v = vm.build(beacon, TVEC)
hexstr = binascii.hexlify(blob).decode()
s.sendall(hexstr.encode() + b"\n")
```

**Bước 5 - Triển khai và Kiểm chứng.**
Dịch vụ trả về mã beacon `0x13D6`. Hệ thống khởi tạo payload tương ứng với mức `PC=114`, nằm trong khoảng an toàn `[112,128]` để tránh kích hoạt alarm. Gửi dữ liệu tới dịch vụ, nhận phản hồi `[+] TELEMETRY STABILIZED` và thu hồi flag.

## Kết quả

Quá trình thực thi trên máy trạm:

```bash
python exploit.py files/ouroboros.7z
```

```text
BEACON: 0x13D6
beacon=0x13D6  pc=114  w=[5079, 5296, 64689, 5861]  bytes=420
[+] TELEMETRY STABILIZED. OVERWRITING SYSTEM MASTER KEY...
CSSCTF{0ur0b0r0s_g00d_j0b_b01s_heh3_67}
FLAG: CSSCTF{0ur0b0r0s_g00d_j0b_b01s_heh3_67}
```

Kết quả:
```text
CSSCTF{0ur0b0r0s_g00d_j0b_b01s_heh3_67}
```
