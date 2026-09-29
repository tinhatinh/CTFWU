# Countersign — Rev (Insane)

**Flag:** `H7CTF{011c87d4-b5c8-405d-923a-33dbed3e5bf7}` · **Files:** `countersign.zip` (ELF x86-64 PIE, stripped, 22 KB) + `note.txt` · Service: `nc pwn.h7tex.com 43708`

## Đề bài

> Countersign is the attestation core of a licensed firmware module. Slide a pass under
> the glass and the clerk stamps whatever you hand him, but the core itself only ever
> walks a route it can vouch for. Find the input that walks it all the way to the flag.

`note.txt` mô tả protocol 4 lệnh, một lệnh mỗi dòng:

```
GET            stream image chương trình của instance này ra hex
NONCE          nonce của instance
MINT <hex>     stamp debug cho tối đa 16 byte
RUN <hex>      đưa vào core 24 byte input, in ra những gì core nhả ra
```

và ghi rằng image và material ký được sinh mới cho mỗi instance. Về sau mới hiểu hết câu
đó: nó đổi theo từng kết nối, chứ không phải từng instance. Việc là tìm 24 byte input khiến
core đi hết đồ thị và nhả cờ.

## Phân tích ban đầu

Máy không có pwntools, không có ghidra/r2, nên toàn bộ đi bằng `objdump -d` + `readelf` và
tự viết tool (`fd.py` in khoảng vma, `records.py` parse image). Binary chỉ có vài hàm,
không anti-debug, không tự giải mã; cái khó là stripped, phải tự đặt tên hàm bằng cách đọc
body.

Bản đồ hàm (đọc lại vài vòng; những chỗ tôi từng gán sai nằm ở mục
"Các giả thuyết đã loại trừ"):

| Địa chỉ | Vai trò |
|---|---|
| `0x1fa0` | boot: mở `/dev/urandom`, đọc 16 byte, sinh key 26 byte (`0x22e0`, splitmix64), nạp image, sinh chữ ký cho từng edge |
| `0x1810` | `exec_program`: VM straight-line trên 8 thanh ghi u32 |
| `0x1d50` | `emit`: chọn cạnh tiếp theo và verify countersignature của nó |
| `0x1af0` | hàm stamp (hình dạng SipHash): `stamp(domain, msg, len, out)`, domain `0x45` cho edge, `0x4d` cho `MINT` |
| `0x1eb0` | hex parser |
| `0x1240` | serializer của `GET` (cho ta layout record chính xác) |
| `0x1410`/`0x1496` | handler `MINT` / `RUN` |

### Vòng lặp `RUN`

Đây là chỗ tôi đọc sai lâu nhất. Hình dạng thật của nó:

```asm
1519:  xor eax,eax ; mov ecx,8  ; lea rdi,[rsp+0x20]
1525:  movzx esi, WORD PTR [0x462d4]      ; entry tag
152c:  rep stos DWORD PTR [rdi],eax       ; regs = 0   (8 u32)
152e:  lea rbp,[rsp+0x80] ; mov ecx,0x20 ; rep stos   ; buf = 0 (128 byte)
154f:  mov DWORD PTR [rsp+0x1c],0         ; printflag = 0
1553:  ...                                ; <- đầu vòng lặp, ba lệnh xóa ở TRÊN vòng
158e:  cmp si, WORD PTR [rdx]             ; tìm record theo tag
15b6:  call 1810                          ; exec_program(rec, regs, buf, input24, &printflag)
15bb:  cmp DWORD PTR [rsp+0x1c],0
15c5:  jne  1635                          ; printflag != 0 -> in buf, DUNG   <== THẮNG
15c7:  test eax,eax
15c9:  jne  15ea                          ; ret == 1 -> "denied"
15cb:  cmp BYTE PTR [rdi+0x208],0
15d2:  je   15ea                          ; không edge nào -> "denied"
15d4:  ... call 1d50                      ; emit -> tag kế tiếp
15e0:  sub r13d,1 ; jne 1553              ; tối đa 0x30d40 = 200000 bước
```

Ba điểm quyết định:

1. `printflag` được kiểm tra trước cả giá trị trả về của `exec_program`. Một record có opcode
   in sẽ thắng ngay cả khi nó kết thúc bằng opcode từ chối.
2. `rep stosd` nằm ngoài vòng lặp (`jne 1553` nhảy về sau chúng). Registers sống xuyên suốt
   cả cuốc đi, không bị xóa mỗi bước.
3. Tham số 2 của `emit` là `rsp+0x20`, tức chính là register file, không phải vùng nào khác.
   Register file chỉ có 8 u32.

### VM `exec_program`

Jump table tại `0x406c`, tính theo kiểu table-relative:
`handler = 0x406c + (int32)*(uint32*)(0x406c + 4*op)`. Sai một chữ số là ra handler giả và
sai luôn cả bảng.

```
0  NOP              1  MOVI  rD, imm32 (6B)  2  MOV   rD, rS
3  ADD rD,rS        4  XOR rD,rS             5  AND rD,rS      6  OR rD,rS
7  ROL rD, K        8  SHR rD, K   (K>31 -> 0)
9  ADDI rD,imm      10 XORI rD,imm           11 ANDI rD,imm
12 LBI  rD, in[k]   (k <= 0x17, ngược lại lấy 0)
13 strncpy(buf, getenv("FLAG") ?: "unavailable", 0x7f)
14 printflag = 1
15 return 1
```

Với mọi opcode 2..8 và 12: `rD = code[pc+1]`, `rS/K/k = code[pc+2]`. Riêng `ROL` và `SHR`
operand thứ hai là hằng số, không phải chỉ số thanh ghi. `op > 15` chỉ `pc += 1`. Vòng lặp
dừng khi `pc >= pay_len`, nên code bị cắt giữa một lệnh 6 byte vẫn chạy bình thường.

Không có opcode nhảy. Mỗi record là một hàm không nhánh, nhận registers, trả về registers.

### `emit`

```c
bpl = (rec->sel_reg == 0xff) ? 0xff
    : (regs[rec->sel_reg] >> (rec->sel_bit & 31)) & 1;   // bt r32 lấy bit modulo 32
for (i = 0; i < rec->k; i++) {
    if (e[i].sel != bpl) continue;
    if (stamp6(tag || target || bpl || tweak) != (e[i].sig_lo, e[i].sig_hi)) continue;
    return e[i].target;                 // chỉ đi trên đường CHỨNG MINH được
}
return rec->dflt;                       // luôn trỏ về "deny sink"
```

Mỗi bước input chỉ điều khiển đúng một bit, và bit đó chọn cạnh. Cạnh nào có chữ ký giả thì
bị bỏ qua kể cả khi `sel` khớp. Đó là nội dung câu "the core only ever walks a route it can
vouch for".

### Layout record

Suy ra từ chính vòng lặp serialize trong `GET`:

```
wire:  tag u16 | sel_reg u8 | sel_bit u8 | dflt u16 | L u16 | code[L] | k u8 | k * 13B
edge:  sel u8 | target u16 | tweak u32 | sig_lo u32 | sig_hi u16
mem:   stride 0x30c, code @ +8 (512B), k @ +0x208, edge[j] @ +0x20c + 16j
```

### Bốn loại record

Boot `entry=30137`, 40 record, 129 edge. Phân loại theo độ dài payload:

* 252 byte, record entry: `MOVI r*,0` rồi 4 lần `LBI r6,in[k]; ROL r6,K; OR r*,r6`.
  Nghĩa là `r0..r5 = 6 word little-endian của 24 byte input`. Song ảnh 1-1 giữa input và
  trạng thái khởi đầu.
* 12 byte: `XORI r4,K; ADD r5,r4; ROL r5,s`. Chỉ động `r4, r5`.
* 30 byte: `ADD r0,r1; ROL r0,s1; XOR r2,r0; ADD r3,r2; ROL r3,s2; XOR r1,r3;
  ADDI r0,A; XORI r2,B`. Chỉ động `r0..r3`.
* 117 byte, "fold": `r6 = (r0^C0) | (r1^C1) | ... | (r5^C5)` rồi
  `r6 |= r6>>16; r6 |= r6>>8; r6 |= r6>>4; r6 |= r6>>2; r6 |= r6>>1`.
  Gấp mọi bit về bit 0, nên `bit0(r6) == 0 <=> r6 == 0 <=> r_i == C_i với mọi i`.
  Cạnh `sel=0` của nó dẫn thẳng tới record thắng.
* Record thắng: payload `0d 0e 0f` = GETFLAG, PRINT, HALT. Vì `printflag` được kiểm trước
  `ret`, HALT không sao cả.
* Deny sink: payload `0f` = HALT. Mọi record khác đều có `dflt` trỏ về nó.

## Các hướng đã loại

Trước khi chốt đã kiểm tra và loại các kênh sau (log đầy đủ ở `notes.md`). Đây là những chỗ
tôi đọc sai, và lần nào kết luận sai cũng trông rất chắc chắn:

1. `emit` in cờ khi `next == 0`, mà không edge nào có `nx == 0`, nên bài vô nghiệm.
   `emit` không in gì cả; điều kiện in là opcode 14 trong payload. Toàn bộ kết luận "vô
   nghiệm" được dựng từ chỗ đọc sai này.
2. Ops 3/4/5 lấy `rD = code[pc+2]`. `rD = code[pc+1]` với mọi op 2..8.
3. `ROL`/`SHR` dùng chỉ số thanh ghi làm số dịch. Operand thứ hai là hằng số.
4. Register file 32 u32 và bị xóa mỗi bước. 8 u32, xóa một lần trước vòng lặp
   (`rep stosd` nằm ngoài).
5. Có một "node 31762" và một `alt_id` ẩn ở `rec+0x20a` không bao giờ ra wire. Trường
   đó chính là `dflt`, nằm trên wire ở offset 4.
6. Image luôn 3076 byte. Độ dài thay đổi theo instance: 2998 / 3063 / 3076 / 3089.
7. Instance khởi động lại làm mất trạng thái. Không có restart. State đổi theo từng
   kết nối, và đó là chủ ý của đề.
8. Cần Unicorn để lấy ground truth. Đã đổ hơn một tiếng vào PLT trampoline, stack
   canary, `FS_BASE`; sau đó đọc lại disassembly kỹ hơn thì đủ.
9. Service trả lời `route N step M bad stampslot`, `ok <hex>`, `no route`, image 145 KB
   (báo cáo của một agent phụ). Không chuỗi nào trong số đó tồn tại trong binary, `grep` xâu
   là loại được ngay.

## Chuỗi khai thác

**Bước 1 - Loại hướng đi thuận.** Cuốc đi tất định theo input, `RUN` chỉ trả về `denied`
(không số bước, không gì để leo đồi), và input có 192 bit. Không có oracle để dò từng bit.

**Bước 2 - Đi ngược từ record fold.** Trạng thái khi bước vào record fold bắt buộc là
`(C0..C5)`, và sáu hằng số đó đọc trực tiếp từ payload của nó (sáu lệnh `XORI r7, imm`).
Mọi record trên đường (12 byte và 30 byte) đều nghịch đảo được: `ADD` thành `-`,
`XOR`/`XORI` thành chính nó, `ROL` thành `ROR`, `ADDI` thành `-`. Vậy lùi từ record fold về
record entry, mỗi bước `pre = invert(rec.program, post)`; tới record entry thì
`input = pack('<I', r0..r5)`.

Ở mỗi bước phải kiểm điều kiện thuận: `step(rec, post)` có thật sự chọn đúng cạnh ta đang lùi
không. Vì `emit` lấy cạnh *khớp đầu tiên*, điều kiện này cực kỳ mạnh và cắt gần hết nhánh. Tìm
đường mất chưa tới 0.1 giây. Gốc của phép tìm đường là chính record fold - không lùi qua nó
được vì nó dùng `MOV`/`OR`/`SHR`, mất thông tin.

**Bước 3 - Phân loại edge bằng `MINT`.** Muốn kiểm ràng buộc thuận phải biết cạnh nào có chữ
ký hợp lệ, vì `first_match` phụ thuộc vào đó. Key ký là per-connection nên không tính offline
được, nhưng `MINT` là một oracle ký tuyệt đối: nhận tối đa 16 byte, trả 6 byte stamp, tức đúng
bằng `(sig_lo, sig_hi)`. Message của edge là

```
MINT( tag(u16) || target(u16) || sel(u8) || tweak(u32) )[:6] == edge.sig
```

Trên boot của tôi: 51/129 edge hợp lệ, 78 edge mang chữ ký giả. Mấy edge giả đó không phải
nhiễu - chính việc `emit` bỏ qua chúng mới mở ra đường thắng. Ví dụ record fold nằm ngay sau
các record 12 byte có `sel_reg=0xff`, mà edge đầu của chúng (luôn khớp về `sel`) lại là edge
giả, nên lõi nhảy sang edge thứ hai.

**Bước 4 - Gộp vào một kết nối.** Vì image, key ký và lời giải chỉ cùng đúng trên một phiên:

```
connect -> GET (image) -> 129 x MINT (phân loại edge) -> solve (ngược) -> RUN
```

~13.5 giây cho 129 lệnh `MINT`, ~0.42 s/lệnh nói chung, tổng dưới 20 s một lần nộp.

**Bước 5 - Kiểm chứng.** Mô hình Python (`analysis/core.py`, dựng lại VM + `emit` + vòng
`RUN`) chạy thuận trên input vừa tìm cho ra `(win, 52312, 26)`, trùng với `RUN` thật, và ba
lần `RUN` liên tiếp trên cùng socket cùng trả lời một chuỗi cờ. Cuốc đi thực tế dài 26 record.

## Flag
```bash
python solve_live.py
```

```
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

## Files

```
exploit.py            standalone: connect, GET, probe MINT, solve, RUN
flag.txt
analysis/core.py      mô hình VM + emit + run (đã đối chiếu tung lenh)
analysis/back.py      tim duong nguoc
analysis/records.py   parse image
analysis/session.py   client mot ket noi
analysis/solve_live.py
analysis/diag.py      luu image + bang chu ky ve file
analysis/img_live.bin, analysis/valid_live.json
analysis/cs.asm       objdump -d
analysis/unpacked/    binary goc (khong bao gio sua)
```
