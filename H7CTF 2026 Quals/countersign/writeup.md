# Countersign — Rev (Insane)

**Flag:** `H7CTF{011c87d4-b5c8-405d-923a-33dbed3e5bf7}` 
**Files:** `countersign.zip` (Tệp ELF x86-64 PIE, bị tước bỏ nhãn (stripped), cỡ 22 KB) + `note.txt`
**Dịch vụ:** `nc pwn.h7tex.com 43708`

## Đề bài

> Countersign is the attestation core of a licensed firmware module. Slide a pass under the glass and the clerk stamps whatever you hand him, but the core itself only ever walks a route it can vouch for. Find the input that walks it all the way to the flag.

Tệp `note.txt` tiết lộ một giao thức mạng gồm 4 lệnh, mỗi lệnh chiếm một dòng:

```text
GET            Ép máy chủ nhả toàn bộ luồng nhị phân (image) của chương trình ra định dạng hex.
NONCE          Lấy mã nonce của luồng kết nối hiện tại.
MINT <hex>     Đóng dấu kiểm định (stamp) cho chuỗi đầu vào tối đa 16 byte.
RUN <hex>      Nạp một đầu vào dài 24 byte vào lõi (core) và in ra toàn bộ tiến trình xử lý của lõi.
```

Đồng thời, nó gợi ý rằng mã image và các tài nguyên chữ ký được sinh mới "cho mỗi instance". Về sau mới thấm thía thực sự ý nghĩa của câu nói này: chúng thay đổi ngẫu nhiên theo **từng kết nối mạng (connection)**, chứ không phải từng phiên bản chạy. Nhiệm vụ tối thượng là tìm ra đúng 24 byte dữ liệu đầu vào để dẫn dắt lõi đi hết trọn vẹn đồ thị và nôn ra cờ.

## Phân tích ban đầu

Môi trường phân tích cực kỳ ngặt nghèo: Không có pwntools, không có ghidra/r2. Mọi thông tin đều phải được đục đẽo hoàn toàn thủ công bằng công cụ `objdump -d`, `readelf` và các đoạn mã tự tự chế (như `fd.py` in khoảng địa chỉ ảo vma, `records.py` mổ xẻ file image). 
Tệp nhị phân rất nhỏ gọn chỉ với vài hàm, không hề chứa các trò mèo chống gỡ lỗi (anti-debug) hay mã tự giải nén (self-modifying code). Cái khó nhằn duy nhất là mã nguồn đã bị tước bỏ nhãn (stripped), buộc người giải phải tự vắt óc suy luận và đặt tên hàm dựa trên việc mổ xẻ mã máy.

Bản đồ hàm sau vài vòng lặp đúc kết (những đoạn từng bị gán nhãn sai lầm sẽ được đề cập ở mục "Các giả thuyết đã loại trừ"):

| Địa chỉ | Vai trò (Chức năng) |
|---|---|
| `0x1fa0` | boot: Khởi tạo, mở `/dev/urandom` rỉa 16 byte, nhào nặn ra một khoá 26 byte (`0x22e0`, dùng thuật toán splitmix64), nạp image vào bộ nhớ, và sinh ra chữ ký cho từng đường đi (edge). |
| `0x1810` | `exec_program`: Một Máy ảo (VM) chạy tuyến tính thẳng tắp (straight-line) hoạt động trên 8 thanh ghi u32. |
| `0x1d50` | `emit`: Hàm phát dữ liệu, nhận trọng trách chọn cạnh (edge) tiếp theo và xác thực chữ ký chéo (countersignature) của nó. |
| `0x1af0` | Hàm stamp (tạo khuôn chữ ký theo dáng dấp của SipHash): `stamp(domain, msg, len, out)`. Giá trị domain là `0x45` cho thuật toán edge, `0x4d` cho lệnh `MINT`. |
| `0x1eb0` | Trình giải mã hex (hex parser). |
| `0x1240` | Bộ đóng gói (serializer) của lệnh `GET` (Cỗ máy in tiền này giúp ta lấy được chính xác cấu trúc dữ liệu của một record). |
| `0x1410`/`0x1496` | Các hàm xử lý (handler) riêng biệt cho `MINT` và `RUN`. |

### Vòng lặp `RUN` (Trái tim của hệ thống)

Đây chính là cạm bẫy dễ sập nhất. Hình hài thật sự của nó sau khi lột trần:

```asm
1519:  xor eax,eax ; mov ecx,8  ; lea rdi,[rsp+0x20]
1525:  movzx esi, WORD PTR [0x462d4]      ; Lấy thẻ (tag) của cửa vào (entry tag)
152c:  rep stos DWORD PTR [rdi],eax       ; Xoá sạch: regs = 0 (khởi tạo 8 thanh ghi u32)
152e:  lea rbp,[rsp+0x80] ; mov ecx,0x20 ; rep stos   ; Xoá sạch: buf = 0 (128 byte)
154f:  mov DWORD PTR [rsp+0x1c],0         ; printflag = 0
1553:  ...                                ; <- MỐC VÀO VÒNG LẶP, 3 lệnh khởi tạo biến nằm ở TRÊN vòng lặp
158e:  cmp si, WORD PTR [rdx]             ; Quét tìm record khớp với tag
15b6:  call 1810                          ; Gọi Máy ảo: exec_program(rec, regs, buf, input24, &printflag)
15bb:  cmp DWORD PTR [rsp+0x1c],0
15c5:  jne  1635                          ; Lỗ hổng: printflag != 0 -> in bộ đệm buf, DỪNG LẠI   <== ĐIỂM CHIẾN THẮNG
15c7:  test eax,eax
15c9:  jne  15ea                          ; Hàm trả về 1 -> Bắn thông báo "denied" (Tử ẹo)
15cb:  cmp BYTE PTR [rdi+0x208],0
15d2:  je   15ea                          ; Tuyệt tự (không còn edge nào đi tiếp) -> Bắn thông báo "denied"
15d4:  ... call 1d50                      ; Gọi hàm emit -> Sinh tag của trạm kế tiếp
15e0:  sub r13d,1 ; jne 1553              ; Khống chế vòng đời tối đa 0x30d40 = 200,000 bước
```

Ba phát hiện chí mạng định đoạt cuộc chơi:

1. Biến `printflag` được đem ra phán xét trước cả khi xem xét mã thoát của hàm `exec_program`. Suy ra, một đoạn record nếu chứa lệnh (opcode) in ra màn hình thì nó sẽ cướp được cờ NGAY LẬP TỨC, kể cả khi ngay sau lệnh in đó là một opcode từ chối.
2. Lệnh xoá bộ nhớ `rep stosd` nằm thảnh thơi bên ngoài vòng lặp (lệnh lùi `jne 1553` nhảy xuống bên dưới chúng). Điều này có nghĩa là các thanh ghi (registers) mang linh hồn bất tử, sống dai dẳng nối tiếp qua toàn bộ cuộc hành trình mà không hề bị làm sạch.
3. Tham số số 2 truyền vào hàm `emit` chính là con trỏ `rsp+0x20`, và đó chính xác là tập hợp file thanh ghi (register file), chứ không phải bất cứ vùng rác nào khác. Tập hợp này chỉ chứa duy nhất 8 biến u32.

### Trình Máy Ảo (VM) `exec_program`

Bảng nhảy (jump table) toạ lạc tại mốc `0x406c`, và được tính toán theo cơ chế nhảy tương đối (table-relative): 
`handler = 0x406c + (int32)*(uint32*)(0x406c + 4*op)`. Bất cứ sai số nào trong giải mã cũng sẽ dẫn tới một handler ma, kéo theo cả bảng mã sụp đổ.

Danh sách Opcode sau dịch ngược:
```text
0  NOP              1  MOVI  rD, imm32 (6B)  2  MOV   rD, rS
3  ADD rD,rS        4  XOR rD,rS             5  AND rD,rS      6  OR rD,rS
7  ROL rD, K        8  SHR rD, K   (K>31 -> 0)
9  ADDI rD,imm      10 XORI rD,imm           11 ANDI rD,imm
12 LBI  rD, in[k]   (Nếu k <= 0x17, ngược lại nhét 0)
13 strncpy(buf, getenv("FLAG") ?: "unavailable", 0x7f)
14 printflag = 1
15 return 1
```

Với tất cả các opcode từ 2..8 và lệnh 12, công thức định hình là: `rD = code[pc+1]`, tham số `rS/K/k = code[pc+2]`. Một điểm ngoại lệ là lệnh `ROL` và `SHR` sử dụng tham số phụ làm hằng số vật lý (constant) chứ không phải là con trỏ chỉ số thanh ghi. Các mã `op > 15` đều mặc định chỉ trượt đi 1 bước: `pc += 1`. Vòng lặp sẽ ngắt tự động khi `pc >= pay_len`, cho nên dù một dòng lệnh 6 byte bị chặt đứt làm đôi, chương trình vẫn chạy trơn tru mượt mà.

Cực kỳ quan trọng: VM không hề hỗ trợ bất cứ opcode nhảy (jump/branch) nào. Mỗi bản ghi (record) thực chất là một chuỗi mã nguồn phẳng lỳ không phân nhánh, nó nuốt thanh ghi, xử lý, rồi nôn thanh ghi mới ra.

### Hàm phát (emit)

```c
bpl = (rec->sel_reg == 0xff) ? 0xff
    : (regs[rec->sel_reg] >> (rec->sel_bit & 31)) & 1;   // Lệnh bt r32 lấy giá trị bit theo modulo 32
for (i = 0; i < rec->k; i++) {
    if (e[i].sel != bpl) continue;
    if (stamp6(tag || target || bpl || tweak) != (e[i].sig_lo, e[i].sig_hi)) continue;
    return e[i].target;                 // Điểm then chốt: lõi CHỈ chạy trên con đường CHỨNG MINH được bằng chữ ký
}
return rec->dflt;                       // Nếu thất bại, luôn tống thẳng vào hố đen từ chối (deny sink)
```

Ở mỗi mốc luân chuyển, trạng thái dữ liệu (input) hiện hành chỉ có quyền quyết định vào đúng MỘT bit đơn độc, và bit đó chịu trách nhiệm chọn con đường (cạnh - edge) để đi tiếp. Ác nghiệt thay, bất cứ con đường nào bám dính một chữ ký giả (forged signature) sẽ bị vứt xó không thương tiếc, cho dù chỉ số định tuyến `sel` có khớp đến đâu. Đó là lời giải mã sắc bén nhất cho câu nói trên đề bài: "the core only ever walks a route it can vouch for".

### Cấu trúc dữ liệu bản ghi (Layout Record)

Cấu trúc này được bóc lột sạch sẽ từ chính vòng lặp đóng gói (serialize) của lệnh `GET`:

```text
Dây mạng (wire):  tag u16 | sel_reg u8 | sel_bit u8 | dflt u16 | L u16 | mã code[L] byte | số lượng k u8 | k khối * 13 byte (của edge)
Cấu trúc Edge:  sel u8 | target u16 | tweak u32 | sig_lo u32 | sig_hi u16
Ánh xạ bộ nhớ:  bước nhảy stride là 0x30c byte, mã code chốt ở @ +8 (dài 512B), k chốt ở @ +0x208, mảng edge[j] cắm ở @ +0x20c + 16j
```

### Chân dung 4 giai cấp Record

Sau quá trình khởi động `entry=30137`, hệ thống nhả ra 40 bản ghi, đan xen 129 con đường (edge). Phân loại chúng theo độ dài của khối payload:

* **252 byte (Kẻ gác cổng - Record Entry):** Bắt đầu với lệnh dọn dẹp `MOVI r*,0`, tiếp nối bằng chuỗi điệp khúc 4 lần `LBI r6,in[k]; ROL r6,K; OR r*,r6`. Lệnh này đúc thành `r0..r5 = 6 khối từ (word) little-endian được lấy chính xác từ 24 byte đầu vào (input)`. Đây là phép ánh xạ song ánh 1-1 hoàn hảo giữa input và trạng thái thanh ghi ban đầu.
* **12 byte (Dân đen 1):** Thực thi `XORI r4,K; ADD r5,r4; ROL r5,s`. Cấu trúc này chỉ chọc ngoáy vào thanh ghi `r4` và `r5`.
* **30 byte (Dân đen 2):** Thực thi `ADD r0,r1; ROL r0,s1; XOR r2,r0; ADD r3,r2; ROL r3,s2; XOR r1,r3; ADDI r0,A; XORI r2,B`. Cấu trúc này chỉ nhào nặn nhóm `r0..r3`.
* **117 byte (Nếp gấp - "Fold" Record):** Thiết lập `r6 = (r0^C0) | (r1^C1) | ... | (r5^C5)` sau đó thi triển một nếp gấp liên hoàn `r6 |= r6>>16; r6 |= r6>>8; r6 |= r6>>4; r6 |= r6>>2; r6 |= r6>>1`. Chuỗi ma thuật này ép mọi bit dồn ép về bit 0. Nhờ đó: `bit0(r6) == 0 <=> r6 == 0 <=> toàn bộ r_i == C_i`. Nếu nhánh thoả mãn `sel=0`, con đường sẽ lao vút tới ngai vàng.
* **Ngai vàng (Record Thắng):** Mang payload `0d 0e 0f` (dịch ra: GETFLAG, PRINT, HALT). Vì cơ chế lỏng lẻo đi phán xét `printflag` trước cả hàm `ret`, việc gọi lệnh tử vong HALT sau đó là hoàn toàn vô hại.
* **Hố đen (Deny sink):** Payload vỏn vẹn `0f` (HALT). Ngoại trừ ngai vàng, toàn bộ các bản ghi khác đều chĩa đích đến mặc định (`dflt`) vào hố đen này.

## Chuỗi khai thác

**Bước 1 - Giết chết hướng đi xuôi (Forward Path).** 
Toàn bộ đường đi đều bị mã hoá cứng theo chuỗi input, lệnh `RUN` chỉ trả về thông báo cụt lủn `denied` (không đếm số bước chân, không một mảnh vụn dữ liệu nào để thực hiện thuật toán leo đồi - hill climbing). Đầu vào input thì dài tới 192 bit. Không hề tồn tại lỗ hổng oracle (tiên tri) để dò dẫm từng bit. Đánh thuận là vô vọng.

**Bước 2 - Lội ngược dòng từ nếp gấp (Backward tracing).** 
Trạng thái thanh ghi tại thời điểm chui vào cửa ải nếp gấp (fold record) bắt buộc phải mang giá trị đích `(C0..C5)`. Thật may mắn, 6 hằng số này có thể lột trần dễ dàng từ chính đoạn payload của record đó (gồm 6 lệnh `XORI r7, imm`). 
Toàn bộ các bản ghi chặn đường trước đó (loại 12 byte và 30 byte) đều là những cỗ máy nghịch đảo (invertible): Lệnh `ADD` hóa giải bằng trừ `-`, lệnh `XOR`/`XORI` thì đánh vào chính nó, `ROL` lật ngược thành `ROR`, và `ADDI` biến thành `-`. Do đó, nếu ta bắt đầu đi thụt lùi từ điểm nếp gấp về phía cổng vào (record entry), mỗi bước đi qua ta tính: `trạng_thái_trước = invert(mã_lệnh_bản_ghi, trạng_thái_sau)`. Khi lùi tới được cổng entry, đoạn mã sẽ ráp lại thành 24 byte đầu vào nguyên vẹn: `input = pack('<I', r0..r5)`.

Tại mỗi bước lùi, ta phải tung ra một phép thử thuận (forward constraint): `step(rec, trạng_thái_sau)` xem thử nó có thực sự chọn trúng cái đường (edge) mà ta đang thụt lùi hay không. Nhớ lại luật của hàm `emit`, nó chỉ vớt cái cạnh *khớp chữ ký đầu tiên (first match)*. Quy luật này hà khắc đến mức nó như một chiếc dao lam xén trụi gần như toàn bộ các nhánh rẽ sai lầm, tốc độ dò đường lùi tốn không tới 0.1 giây. Cột mốc khởi điểm của thuật toán lùi chính là nếp gấp (fold) - ta không thể lùi xuyên thấu qua nó vì nó sử dụng các hàm huỷ diệt thông tin (như `MOV`, `OR`, `SHR`).

**Bước 3 - Cấp bách phân loại đường đi bằng `MINT`.** 
Để phép kiểm chứng thuận ở bước 2 vận hành được, bắt buộc ta phải điểm mặt chỉ tên được cạnh (edge) nào đang mang một chữ ký hợp lệ, bởi vì cơ chế `first_match` lệ thuộc hoàn toàn vào đó. Đau đớn thay, mã khoá ký lại nhảy cóc theo từng kết nối mạng, phá hỏng mọi ảo mộng tính toán offline.
Nhưng hệ thống lại tạo ra lỗ hổng từ trên trời rơi xuống: Lệnh `MINT` hoạt động như một cỗ máy đóng dấu tuyệt đối. Nếu nhét vào tối đa 16 byte, nó sẽ cắn trả 6 byte chữ ký stamp, vừa vặn bằng đúng cái mảng `(sig_lo, sig_hi)`. Cấu trúc của khối thông điệp (message) đi qua cạnh là:

```text
MINT( tag(u16) || target(u16) || sel(u8) || tweak(u32) ) cắt lấy 6 byte đầu == edge.sig
```

Khi chạy quét ở giai đoạn boot: chỉ có 51 trên tổng số 129 con đường là hợp pháp, 78 đường đi mang chữ ký giả mạo. Đám chữ ký rác rưởi này không phải là nhiễu ngẫu nhiên - chính nhờ sự kiện hàm `emit` từ chối bọn chúng đã mở toang cánh cổng chiến thắng. Đơn cử: cửa ải nếp gấp (fold record) toạ lạc ngay sau cụm bản ghi loại 12 byte (với thông số `sel_reg=0xff`). Lẽ ra lõi sẽ lao vào con đường đầu tiên (vốn luôn khớp điều kiện `sel`), nhưng vì đường đó mang chữ ký giả, lõi buộc lòng nhảy sang con đường thứ hai, một đường cao tốc dẫn thẳng tới cờ.

**Bước 4 - Gom cả giang sơn vào một gói (Single-Connection Stream).** 
Bởi lẽ mã image, khoá ký và lời giải chỉ tồn tại chớp nhoáng trên cùng một nhịp đập phiên mạng, vòng lặp khai thác phải liền mạch như nước chảy:

```text
Kết_nối -> Gửi lệnh GET (lấy image) -> Bắn 129 lần MINT (để dán nhãn các con đường) -> Chạy code lùi (solve) -> Gửi lệnh RUN
```

Với tốc độ ~13.5 giây để bắn tàn bạo 129 lệnh `MINT` (tương đương ~0.42 s/lệnh), toàn bộ quá trình hack chưa tốn đến 20 giây cho mỗi đợt.

**Bước 5 - Đóng dấu bảo chứng.** 
Khởi tạo một môi trường máy ảo giả lập bằng Python (`analysis/core.py`, nhái trọn vẹn tập lệnh VM, hàm `emit` và vòng xoáy `RUN`), cấp cho nó đoạn input vừa tìm được để chạy xuôi. Máy ảo nội bộ này nhả ra `(win, 52312, 26)`, đồng điệu hoàn hảo với log của hàm `RUN` trên máy chủ thực. Cực đoan hơn, nếu ta spam 3 lần lệnh `RUN` rực lửa liên tiếp trên cùng một socket, máy chủ sẽ ngoan ngoãn nôn ra 3 dòng cờ giống nhau. Đường đi xương máu để giành chiến thắng này dài đúng 26 chặng record.

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

## Hệ sinh thái File nguồn

```text
exploit.py            Vũ khí vạn năng (standalone): tự động hoá toàn bộ chuỗi connect, GET, bắn probe MINT, giải ngược, và nã RUN.
flag.txt              Cờ thu thập được.
analysis/core.py      Máy ảo mô phỏng (tích hợp VM + emit + run), đã được đối chiếu độ chuẩn xác tới từng bytecode.
analysis/back.py      Thuật toán nội suy đường đi ngược.
analysis/records.py   Động cơ phân rã (parser) file image.
analysis/session.py   Xử lý client giao tiếp mạng trên một kết nối dai dẳng.
analysis/solve_live.py Script chốt hạ thực chiến.
analysis/diag.py      Bộ phân tích lưu vết image và bảng chữ ký ra ổ cứng.
analysis/img_live.bin, analysis/valid_live.json (File đệm chẩn đoán)
analysis/cs.asm       Mã Assembly thô đúc bằng objdump -d.
analysis/unpacked/    Tệp tin nhị phân gốc (cấm sửa).
```
