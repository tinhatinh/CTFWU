# Countersign - Rev (Insane)

**Flag:** `H7CTF{011c87d4-b5c8-405d-923a-33dbed3e5bf7}` 
**Files:** `countersign.zip` (File ELF x86-64 PIE, binary đã loại bỏ thông tin gỡ lỗi - stripped, kích thước 22 KB) + `note.txt`
**Dịch vụ:** `nc pwn.h7tex.com 43708`

## Đề bài

> Countersign is the attestation core of a licensed firmware module. Slide a pass under the glass and the clerk stamps whatever you hand him, but the core itself only ever walks a route it can vouch for. Find the input that walks it all the way to the flag.

File `note.txt` cung cấp mô tả giao thức mạng gồm 4 lệnh:

```text
GET            Yêu cầu máy chủ trả về toàn bộ luồng nhị phân (image) của chương trình dưới định dạng hex.
NONCE          Lấy mã nonce của kết nối hiện tại.
MINT <hex>     Đóng dấu kiểm định (stamp) cho chuỗi đầu vào (tối đa 16 byte).
RUN <hex>      Cung cấp đầu vào dài 24 byte cho lõi xử lý (core) và in ra log quá trình thực thi.
```

Đáng chú ý, tài nguyên chữ ký được khởi tạo ngẫu nhiên "cho mỗi instance" - tức là thay đổi theo **từng phiên kết nối (connection)**. Yêu cầu của bài toán là tìm 24 byte dữ liệu đầu vào chính xác để chương trình đi qua toàn bộ đồ thị kiểm tra và trả về cờ.

## Phân tích ban đầu

Quá trình phân tích thực hiện thông qua công cụ `objdump -d`, `readelf` và các script hỗ trợ (như `fd.py`, `records.py`). Binary có dung lượng nhỏ, không bao gồm mã cản trở (anti-debug) hoặc tự sửa đổi (self-modifying code). Thử thách chủ yếu đến từ việc mã nguồn đã bị loại bỏ thông tin gỡ lỗi, yêu cầu suy luận kiến trúc hệ thống từ mã assembly.

Sơ đồ chức năng các hàm được phân tách như sau:

| Địa chỉ | Vai trò (Chức năng) |
|---|---|
| `0x1fa0` | boot: Khởi tạo, mở `/dev/urandom` lấy 16 byte, tạo khóa 26 byte (thuật toán splitmix64), nạp image vào bộ nhớ, và sinh chữ ký cho các nhánh (edge). |
| `0x1810` | `exec_program`: Một Máy ảo (VM) hoạt động tuần tự trên 8 thanh ghi u32. |
| `0x1d50` | `emit`: Hàm điều hướng, chọn cạnh tiếp theo và xác thực chữ ký (countersignature). |
| `0x1af0` | Hàm stamp (thuật toán tương tự SipHash): `stamp(domain, msg, len, out)`. Giá trị domain là `0x45` cho thuật toán edge, `0x4d` cho lệnh `MINT`. |
| `0x1eb0` | Trình phân tích chuỗi hex (hex parser). |
| `0x1240` | Bộ xử lý lệnh `GET` (cung cấp cấu trúc dữ liệu của bản ghi). |
| `0x1410`/`0x1496` | Bộ xử lý (handler) cho lệnh `MINT` và `RUN`. |

### Vòng lặp `RUN` (Cơ chế xử lý chính)

Mô hình thực thi lệnh `RUN` sau dịch ngược:

```asm
1519:  xor eax,eax ; mov ecx,8  ; lea rdi,[rsp+0x20]
1525:  movzx esi, WORD PTR [0x462d4]      ; Lấy thẻ (tag) của mốc bắt đầu
152c:  rep stos DWORD PTR [rdi],eax       ; Khởi tạo 8 thanh ghi u32 (regs = 0)
152e:  lea rbp,[rsp+0x80] ; mov ecx,0x20 ; rep stos   ; Khởi tạo bộ đệm buf = 0 (128 byte)
154f:  mov DWORD PTR [rsp+0x1c],0         ; printflag = 0
1553:  ...                                ; <- ĐIỂM VÀO VÒNG LẶP
158e:  cmp si, WORD PTR [rdx]             ; Tìm bản ghi khớp với tag
15b6:  call 1810                          ; Gọi Máy ảo: exec_program(rec, regs, buf, input24, &printflag)
15bb:  cmp DWORD PTR [rsp+0x1c],0
15c5:  jne  1635                          ; Điều kiện thành công: printflag != 0 -> in bộ đệm buf, thoát vòng lặp
15c7:  test eax,eax
15c9:  jne  15ea                          ; Hàm trả về 1 -> Báo lỗi "denied"
15cb:  cmp BYTE PTR [rdi+0x208],0
15d2:  je   15ea                          ; Không còn nhánh khả dụng -> Báo lỗi "denied"
15d4:  ... call 1d50                      ; Gọi hàm emit -> Sinh tag của mốc tiếp theo
15e0:  sub r13d,1 ; jne 1553              ; Giới hạn tối đa 200,000 bước (0x30d40)
```

Ba đặc điểm quan trọng định hình phương pháp khai thác:

1. Biến `printflag` được kiểm tra trước giá trị trả về của `exec_program`. Điều này có nghĩa là nếu một bản ghi chứa lệnh in ra màn hình, cờ sẽ được trả về ngay lập tức, bất kể mã lệnh tiếp theo có báo lỗi hay không.
2. Các lệnh khởi tạo thanh ghi (`rep stosd`) nằm ngoài vòng lặp. Giá trị thanh ghi (registers) được bảo tồn qua các bước lặp.
3. Tham số truyền vào hàm `emit` là con trỏ `rsp+0x20`, chính là mảng 8 thanh ghi u32 của VM.

### Trình Máy Ảo (VM) `exec_program`

Bảng định tuyến (jump table) tại địa chỉ `0x406c`, sử dụng cơ chế nhảy tương đối: `handler = 0x406c + (int32)*(uint32*)(0x406c + 4*op)`.

Danh sách Opcode:
```text
0  NOP              1  MOVI  rD, imm32 (6B)  2  MOV   rD, rS
3  ADD rD,rS        4  XOR rD,rS             5  AND rD,rS      6  OR rD,rS
7  ROL rD, K        8  SHR rD, K   (K>31 -> 0)
9  ADDI rD,imm      10 XORI rD,imm           11 ANDI rD,imm
12 LBI  rD, in[k]   (Nếu k <= 0x17, ngược lại là 0)
13 strncpy(buf, getenv("FLAG") ?: "unavailable", 0x7f)
14 printflag = 1
15 return 1
```

Cấu trúc lệnh: lệnh từ 2-8 và 12 dùng công thức `rD = code[pc+1]`, tham số `rS/K/k = code[pc+2]`. Lệnh `ROL` và `SHR` sử dụng tham số phụ là hằng số vật lý. Các mã `op > 15` có độ dài 1 byte (`pc += 1`). VM không hỗ trợ lệnh nhảy nhánh (branching); mỗi bản ghi là một chuỗi mã thực thi tuyến tính.

### Hàm phát (emit)

```c
bpl = (rec->sel_reg == 0xff) ? 0xff
    : (regs[rec->sel_reg] >> (rec->sel_bit & 31)) & 1;   // Lấy giá trị bit
for (i = 0; i < rec->k; i++) {
    if (e[i].sel != bpl) continue;
    if (stamp6(tag || target || bpl || tweak) != (e[i].sig_lo, e[i].sig_hi)) continue;
    return e[i].target;                 // VM chỉ chọn nhánh có chữ ký hợp lệ
}
return rec->dflt;                       // Trả về mặc định nếu không khớp
```

Tại mỗi bước, trạng thái đầu vào xác định 1 bit quyết định chọn nhánh (edge). Bất kỳ nhánh nào mang chữ ký không hợp lệ (forged signature) sẽ bị loại bỏ, dù giá trị `sel` khớp. 

### Cấu trúc dữ liệu bản ghi (Record Layout)

Cấu trúc trích xuất từ lệnh `GET`:

```text
Chuỗi truyền tải:  tag u16 | sel_reg u8 | sel_bit u8 | dflt u16 | L u16 | mã code[L] byte | số lượng k u8 | k khối * 13 byte (của edge)
Cấu trúc Edge:  sel u8 | target u16 | tweak u32 | sig_lo u32 | sig_hi u16
Ánh xạ bộ nhớ:  kích thước (stride) là 0x30c byte, mã code tại offset +8 (dài tối đa 512B), k tại +0x208, mảng edge[j] tại +0x20c + 16j
```

### Các dạng bản ghi

Sau quá trình khởi động, hệ thống tạo ra 40 bản ghi với 129 nhánh (edge). Dựa theo độ dài tải trọng (payload), có thể phân loại:

* **252 byte (Điểm vào - Entry Record):** Bắt đầu bằng `MOVI r*,0`, tiếp tục lặp 4 lần chuỗi lệnh `LBI r6,in[k]; ROL r6,K; OR r*,r6`. Quá trình này nạp 24 byte dữ liệu đầu vào thành 6 biến word (little-endian) vào `r0..r5`.
* **12 byte (Bản ghi trung gian 1):** Thực thi `XORI r4,K; ADD r5,r4; ROL r5,s`. Xử lý trên thanh ghi `r4` và `r5`.
* **30 byte (Bản ghi trung gian 2):** Thực thi `ADD r0,r1; ROL r0,s1; XOR r2,r0; ADD r3,r2; ROL r3,s2; XOR r1,r3; ADDI r0,A; XORI r2,B`. Xử lý trên `r0..r3`.
* **117 byte (Bản ghi gom nhóm - "Fold"):** Khởi tạo `r6 = (r0^C0) | (r1^C1) | ... | (r5^C5)` và nén dữ liệu `r6 |= r6>>16; r6 |= r6>>8; ...; r6 |= r6>>1`. Cơ chế này kiểm tra xem toàn bộ thanh ghi `r_i` có bằng hằng số `C_i` hay không. Nếu bằng (nhánh `sel=0`), tiến trình sẽ dẫn tới cờ.
* **Bản ghi đích (Win Record):** Payload `0d 0e 0f` (GETFLAG, PRINT, HALT). Lệnh PRINT cập nhật `printflag`, kích hoạt việc trả về cờ trước khi lệnh HALT được xử lý.
* **Bản ghi loại bỏ (Deny sink):** Payload `0f` (HALT). Trừ bản ghi đích, các đường dẫn mặc định (`dflt`) khác đều trỏ tới bản ghi này.

## Quá trình khai thác

**Bước 1 - Phân tích hạn chế tiếp cận tuần tự (Forward Path).** 
Các nhánh phụ thuộc vào đầu vào 192 bit. Lệnh `RUN` chỉ thông báo "denied" khi thất bại mà không cung cấp dữ liệu trung gian, do đó không thể dò tìm tuyến tính.

**Bước 2 - Phân tích luồng ngược (Backward tracing).** 
Trạng thái thanh ghi tại bản ghi Fold cần đạt giá trị đích `(C0..C5)`. Các hằng số này có thể trích xuất từ tải trọng của bản ghi (các lệnh `XORI r7, imm`). 
Các bản ghi trung gian (12 byte, 30 byte) có khả năng đảo ngược chức năng (invertible): Lệnh `ADD` đảo thành `-`, `XOR`/`XORI` tự đảo, `ROL` đảo thành `ROR`, `ADDI` đảo thành `-`. Bằng cách tính ngược từ bản ghi Fold qua các mốc trung gian về điểm khởi đầu (Entry Record), ta sẽ thu được chuỗi 24 byte đầu vào gốc: `input = pack('<I', r0..r5)`.

Tại mỗi bước tính ngược, cần xác nhận bằng một phép thử tuần tự để đảm bảo nhánh xử lý hiện tại tuân theo thuật toán của `emit`. Cơ chế ưu tiên `first_match` của hàm này giúp nhanh chóng loại bỏ các giả thuyết không hợp lệ. Quá trình tính ngược bắt đầu từ vị trí Fold, không tính toán xuyên qua nó do Fold sử dụng các hàm loại bỏ dữ liệu.

**Bước 3 - Xác thực nhánh bằng lệnh `MINT`.** 
Mã khóa để xác thực nhánh thay đổi theo kết nối. Do đó, cần kiểm tra tính hợp lệ của từng chữ ký trên nhánh bằng lệnh `MINT`. Cấu trúc gói tin MINT xác thực:

```text
MINT( tag(u16) || target(u16) || sel(u8) || tweak(u32) ) cắt lấy 6 byte đầu == edge.sig
```

Trong 129 nhánh, chỉ có 51 nhánh là hợp lệ. Việc `emit` từ chối các nhánh chữ ký lỗi (forged) là yếu tố quyết định. Tại mốc Fold, nhánh thông thường (luôn khớp điều kiện) có chữ ký lỗi sẽ bị loại, buộc tiến trình chọn nhánh thứ hai, dẫn trực tiếp đến cờ.

**Bước 4 - Khai thác tổng hợp (Single-Connection Stream).** 
Toàn bộ chuỗi lệnh khai thác phải chạy trên một kết nối duy nhất để bảo toàn mã khóa:

```text
Kết_nối -> Gửi lệnh GET -> Chạy 129 lệnh MINT (dán nhãn đường đi) -> Tính ngược -> Gửi lệnh RUN
```

Với độ trễ ~13.5 giây để gửi 129 lệnh MINT, tổng thời gian khai thác dưới 20 giây.

**Bước 5 - Trích xuất cờ.** 
Sử dụng công cụ Python mô phỏng máy ảo VM (`analysis/core.py`) để chạy bộ dữ liệu input, kết quả `(win, 52312, 26)` phản ánh chính xác hành vi máy chủ. Quá trình khai thác trả về cờ thành công.

## Flag
```bash
python solve_live.py
```

```text
$ python solve_live.py
[*] nonce: a02b52f22ef6817d
[*] image 3076 byte entry=43250
[*] 129 link, 51 hop le (13.5s)
[?] fold 24915 seed={'0x0': '0xe53bf802', ... '0x5': '0xf1551421'} -> emit idx=3 (can 3)
[+] duoi dai 26
[*] solve 0.0s -> a8a5d7f6053e442d785c81c2e7f137825c6181553d2a6d52
[*] model forward: ('win', 52312, 26)
[!] RUN a8a5d7f6053e442d785c81c2e7f137825c6181553d2a6d52 -> H7CTF{011c87d4-b5c8-405d-923a-33dbed3e5bf7}
[*] thu them 2 lan nua:
       H7CTF{011c87d4-b5c8-405d-923a-33dbed3e5bf7}
       H7CTF{011c87d4-b5c8-405d-923a-33dbed3e5bf7}
```

## Các file liên quan

```text
exploit.py            Công cụ tự động khai thác: kết nối, phân tích GET, xác thực MINT, nội suy ngược và kích hoạt RUN.
flag.txt              Cờ thu thập được.
analysis/core.py      Máy ảo mô phỏng (tích hợp VM, emit và run) đồng bộ cấu trúc bytecode.
analysis/back.py      Thuật toán tính ngược đồ thị.
analysis/records.py   Bộ phân giải (parser) cho định dạng image.
analysis/session.py   Quản lý phiên kết nối mạng.
analysis/solve_live.py Tệp thực thi trên môi trường live.
analysis/diag.py      Bộ phân tích lưu dữ liệu chẩn đoán (image, chữ ký).
analysis/img_live.bin, analysis/valid_live.json Dữ liệu đệm.
analysis/cs.asm       Mã Assembly dịch ngược bằng objdump.
analysis/unpacked/    Tệp tin nhị phân gốc.
```
