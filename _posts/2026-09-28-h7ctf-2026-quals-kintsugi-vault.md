---
title: "Kintsugi Vault — Rev (Hard)"
date: 2026-09-28 16:53:17 +0700
lastmod_at: 2026-09-28 16:53:17 +0700
categories: [Rev]
tags: [h7ctf-quals, Rev]
---
{% raw %}
## 0. Tóm tắt

`vmrun` là một VM custom 14 opcode, mỗi guardian (`.shard`) chứa một bảng thế opcode
256 byte đóng vai trò "chìa khóa dịch mã" và một chương trình 649 byte. Chương trình đó đọc
8 byte key từ dòng lệnh, trộn chúng bằng 3 tầng `LUT` + trộn XOR tuyến tính, rồi so sánh 8
thanh ghi với 8 hằng số. Seed 32 byte của vault chính là 8 byte key của 4 guardian nối theo
thứ tự chuỗi. Việc phải làm:

1. đọc định dạng shard và ISA từ `vmrun` (binary static, stripped, không chạy được trên máy
   không có Docker/WSL nên bắt buộc tái dựng bằng Python),
2. phục hồi bảng decode của các guardian không có bảng trong suốt ("chất keo đã mất"),
3. chạy ngược chương trình để suy ra key, chấp nhận cả hai giá trị của các bit bị `ANDI` xóa,
4. thử mọi thứ tự ghép, đối chiếu với `pubkey.bin` bằng bài toán Ed25519,
5. ký nonce và nộp cho `POST /attest`.

Result: `seed = f860622f78adc147 0aba129efad830d8 1b091cc9cc9b71ee a4b10c57af5dd7af` (với bản
handout mẫu) và với handout thật của instance là
`185087fcdd31641e 58f77177f104cded f29bb38be31bf782 8dd0b1fab65c4746`,

```
H7CTF{9df8f215-6ef3-4ee2-a336-42d628680738}
```

Chi tiết quyết định nằm ở mục 7: handout trên trang challenge là bản mẫu của tác giả; instance
tự serve bản của nó tại `GET /handout.tar.gz`.

## 1. Định dạng shard

```
0x000  4   'KSHD'
0x004  1   version = 01
0x005  1   flags;  bit0 == 1  -> bảng decode nằm trong file (guardian khởi đầu)
                          == 0 -> BẮT BUỘC đưa file bảng ở tham số thứ 3
0x007  1   keylen = 08
0x008  2   u16 tablelen = 0x100
0x00a  2   u16 proglen  = 0x289 = 649
0x00e 16   content id (= tên file)      <- vmrun KHÔNG bao giờ kiểm tra
0x01e  4   (không dùng)                 <- vmrun KHÔNG bao giờ kiểm tra
0x022 16   "next" id đã bị làm nhiễu    <- vmrun KHÔNG bao giờ kiểm tra
0x032 256  decode table: raw opcode -> số thứ tự handler
0x132 256  sbox (LUT), luôn là hoán vị, luôn trong suốt
0x232 649  chương trình
```

Kiểm tra duy nhất trong `main` (0x402fd0): `size > 0x31`, magic, và
`size >= 0x132 + tablelen + proglen` (`truncated shard`). File bảng bên ngoài chỉ cần
`> 0xff` byte rồi được chép nguyên 256 byte vào stack (0x4030cb), không kết hợp với
bytes trong file, không kiểm tra nội dung. Kết luận quan trọng: chúng ta hoàn toàn tự do
tạo bảng decode, chỉ cần nó làm chương trình chạy đúng.

Key: 16 ký tự hex, không phân biệt hoa/thường, được giải mã bằng SSE và ghi 8 byte liên tiếp
tại `rsp+0x58`.

## 2. ISA

Dispatch: `op = table[prog[pc]]`. `op == 0` -> HALT, in `OK`, exit 0. `op > 13` -> `bad opcode`,
exit 2. `pc >= proglen` cũng được tính là thành công. Bảng nhảy tại `0x486ba8` (int32 tương đối,
có dấu) cho ra:

| op | mnemonic | độ dài | ngữ nghĩa |
|----|----------|--------|------------|
| 0 | HALT | 1 | dừng, chấp nhận |
| 1 | KEY | 3 | `rA = (u32)mem8[0x58 + B]` (B 0..7 là key, B >= 8 đọc luôn vào bảng decode!) |
| 2 | MOVI | 6 | `rA = imm32` |
| 3 | MOV | 3 | `rA = rB` |
| 4 | XOR | 3 | `rA ^= rB` |
| 5 | ADD | 3 | `rA = (rA + rB) mod 2^32` |
| 6 | MUL | 3 | `rA = (rA * rB) mod 2^32` |
| 7 | AND | 3 | `rA &= rB` |
| 8 | OR | 3 | `rA |= rB` |
| 9 | ROL | 3 | `rA = rol32(rA, B & 31)` - B là imm8, không phải thanh ghi |
| 10 | LUT | 3 | `rA = (u32)sbox[rB & 0xff]` (xóa 24 bit trên) |
| 11 | CMP | 6 | nếu `rA != imm32` -> in `FAIL`, exit 1 |
| 12 | ANDI | 6 | `rA &= imm32` |
| 13 | XORI | 6 | `rA ^= imm32` |

Ô thanh ghi là 12 cell 32-bit tại `rsp+0x30..0x57`; `rep stos` chỉ xóa 8 cell đầu, cell 10/11
trùng chính xác 8 byte key, cell >= 12 alias thẳng vào vùng bảng decode đang sống (chương trình
có thể tự sửa dispatch), cell >= 0x4e chạm canary/retaddr. Không guardian nào trong handout dùng
tới các chỉ số đó - chúng là bẫy tiềm tàng chứ không phải cơ chế.

Toàn bộ bảng opcode và các bẫy được kiểm chứng bằng cách tự viết lại VM (`vm.py`, `VM` class)
rồi đối chiếu với kết quả phân tích rã rời của hai hướng đọc độc lập.

## 3. Hai dòng guardian

Phân loại 7 shard theo cách chúng tự giải mã bằng chính bảng trong file:

- Dòng A (`f6f11ad1`, `080ec62d`, `3e3a0fc9`, `cfa1fa34`): 3 tầng `LUT` + trộn XOR,
  kết thúc bằng 8 lệnh `CMP` mà immediate vừa khít một byte. Đây là khối mã 64 bit thực thụ.
- Dòng B (`3df10ef4`, `63bafd7f`, `f14ad4e2`): một vòng `KEY -> LUT -> ADD -> ROL -> MUL -> OR ->
  XORI -> CMP` với immediate 32 bit. `MUL` và `OR` phá thông tin, nên phép kiểm rất yếu:
  phân tích tay cho `3df10ef4` ra khoảng 528 key được chấp nhận. Chúng là "đám vệ sĩ chết"
  trong mesh, không mang seed.

## 4. Phục hồi "chất keo" (bảng decode)

`vmrun` từ chối chạy shard dòng A không có flag bit0 nếu ta không đưa bảng. Bảng thật không tồn
tại trong file (region 0x32 của chúng chỉ có 158..163 giá trị phân biệt, tức là ngẫu nhiên).

Cách phục hồi, dùng chính tính chất của máy:

1. Mỗi chương trình chỉ dùng ~8 opcode khác nhau, và vì bảng thật là hoán vị nên mỗi raw byte
   phải ánh xạ tới một op khác nhau.
2. Vị trí các lệnh đã biết trước một phần: 8 lệnh `KEY` đầu tiên ở pc = 0,3,...,21 với operand
   `(i,i)`; đuôi 49 byte cuối chắc chắn là 8 lệnh `CMP` lên `r0..r7` với immediate một byte rồi
   tới một byte HALT. Vậy `KEY`, `CMP`, `HALT` bị ghim.
3. Vì mọi opcode đều dài 3 hoặc 6 byte, mọi vị trí opcode đều thỏa `pc % 3 == 0`; chọn 5 raw byte
   xuất hiện nhiều nhất ở các vị trí đó và thử mọi phép gán cho `{MOV, XOR, LUT, ANDI, XORI}`
   (tối đa 6720 khả năng), chấp nhận phép gán mà: đi bộ phủ kín chương trình, dừng ở HALT đúng
   byte cuối, có đúng 8 lệnh `CMP`, mọi operand thanh ghi <= 11, và chạy ngược không mâu thuẫn.

Với `080ec62d` và `3e3a0fc9` còn có con đường tắt: chuyển nguyên dãy `(pc, op)` của `f6f11ad1`
sang từng vị trí của chúng cho kết quả 0 xung đột - tức ba shard này chung một hình dạng
chương trình. `cfa1fa34` lệch pha vì vòng `XORI/ANDI` đầu của nó chạy 5 lượt chứ không phải 4,
nên phải dùng cách tìm kiếm ở trên; bảng của nó là
`f7=KEY 79=XORI 4e=ANDI d6=LUT 4c=XOR c1=MOV bc=CMP 44=HALT`.

## 5. Suy ngược key

Với bảng đúng, chương trình dòng A có dạng

```
r0..r7 = key[0..7]
vòng 1: (XORI r?, imm) (ANDI r?, mask) xen kẽ trên một vài thanh ghi
lặp 3 lần: LUT r?,r?  ->  16 lệnh XOR trộn  ->  XORI r?, imm
MOV r0,r0 x56          (padding)
CMP r0..r7, byte đích  -> HALT
```

Mọi bước đều đảo được trừ `ANDI`: bit mà mask xóa sẽ không bao giờ ảnh hưởng tới kết quả, nên
nó là bbit tự do. Chạy ngược từ 8 `CMP` về đầu cho ra giá trị của từng `key[i]` cùng danh sách
bit tự do; mỗi guardian vì thế có 16..64 key được chấp nhận chứ không phải 1.

Bẫy chí mạng khi liệt kê biến thể: phải ép bit tự do về cả 0 lẫn 1. Một vòng lặp chỉ *bật*
bit (`k[s] |= 1 << b`) sẽ bỏ sót chính xác một nửa không gian nghiệm, và đó là lý do lần ghép seed
đầu tiên trả về 0 kết quả dù thuật toán đã đúng.

## 6. Ghép seed

4 mảnh 8 byte, 24 thứ tự, tích các biến thể (16 x 32 x 32 x 64) - vừa gọn trong một phút tính:

```
seed = f860622f78adc147 0aba129efad830d8 1b091cc9cc9b71ee a4b10c57af5dd7af
       f6f11ad1           3e3a0fc9           080ec62d           cfa1fa34
Ed25519_pubkey(seed) = 5a0239a82fba9d2d5c6c5418e237ed8a888baeced6f4c32aa71e7be3805775ee
pubkey.bin           = 5a0239a82fba9d2d5c6c5418e237ed8a888baeced6f4c32aa71e7be3805775ee  -> khớp
```

Oracle ở đây là toán học, không phải server: khóa public dẫn xuất từ seed trùng khớp chứng tỏ
4 key và thứ tự của chúng là nghiệm đúng duy nhất, không cần chờ endpoint hồi đáp. Đã kiểm chứng
cặp (seed -> pubkey) bằng hai cài đặt độc lập: `cryptography` 50.0.1 (OpenSSL) và `ed25519/ed.py`
thuần stdlib tự viết, cả hai khớp 3 vector RFC 8032 mục 7.1.

Những giả thuyết đã loại bỏ bằng oracle này (không khớp): 8 byte `CMP` đích nối nhau; toàn bộ
immediate `XORI`; mọi cửa sổ 32 byte của mọi file trong handout; các cặp field 16 byte trong
header (`id`, `next`); thứ tự byte đảo ngược.

## 7. Attestation - trạng thái

Đúng như README, contract là `GET /attest` -> nonce 24 byte (48 ký tự hex), rồi
`POST /attest` với `nonce` và `sig` (hex). Chữ ký của chúng ta tự verify được dưới
`pubkey.bin` (đã kiểm tại địa phương, bằng hai cài đặt độc lập). Thế nhưng endpoint trả
`400 attestation incomplete` cho *mọi* biến thể đã thử - danh sách đầy đủ ở `notes.md` K9/K11:
nhiều cách dựng thông điệp, mọi cách mã hoá body, mọi alias field, 40 cặp GET+POST trên cùng một
kết nối, và cả `OPTIONS/PUT/PATCH/DELETE` (app chỉ nhận `GET, POST, OPTIONS, HEAD`, duy nhất
đường dẫn `/attest`).

Điểm then chốt: server trả cùng một thông báo cho cả `sig="zz"` (hex không hợp lệ), `sig` sai
độ dài, thiếu field, và nonce chưa từng được cấp. Nghĩa là nó không cho bất kỳ oracle nào để phân
biệt "không tìm thấy nonce" với "chữ ký sai" - nên không thể dò hợp đồng bằng brute-force.

Chuỗi suy luận lúc đó dẫn tới một kết luận sai: "handout nội tại nhất quán, chữ ký hợp lệ,
server một mực từ chối => container này không gắn với artifact ta có". Đúng một nửa: artifact ta
có thật sự không gắn với instance - nhưng không phải vì instance hỏng.

Chìa khoá là một request chưa ai gọi: `GET /handout.tar.gz` trên chính instance trả về 200 với
318172 byte, sha256 `6bbfc07a...`, tức là một bộ artifact khác hoàn toàn với tệp tĩnh
347257 byte (`4ce8375d...`) tải từ trang challenge. Bản của instance có `pubkey.bin` khác
(`5b0a2f81...`), 7 shard với content id khác, chain start `35e266269ee5...`, timestamp cùng giờ
khởi động instance. Nói cách khác: tệp trên trang challenge là bản dump mẫu của tác giả
(`MANIFEST.txt` ghi `team: team-local` - tín hiệu đã nhìn thấy nhưng không bị nghi ngờ đủ sớm).

Chạy lại đúng pipeline (`analysis/live_solve.py <thu_muc>`) trên artifact thật:

| guardian | cách lấy bảng | key (8 byte) |
|----------|----------------|--------------|
| `35e266269ee5` (start, flag 0x01) | bảng trong suốt của chính nó | `185087fcdd31641e` |
| `80014ce50564` | tìm kiếm gán raw->op | `58f77177f104cded` |
| `42b1de232bfc` | tìm kiếm gán raw->op | `f29bb38be31bf782` |
| `aaae515b295d` (flag 0x02) | tìm kiếm gán raw->op | `8dd0b1fab65c4746` |

```
seed  = 185087fcdd31641e58f77177f104cdedf29bb38be31bf7828dd0b1fab65c4746
sig   = Ed25519_sign(seed, bytes.fromhex(nonce))        # 24 byte thô, KHÔNG phải chuỗi hex
POST /attest  nonce=...&sig=...  ->  200
H7CTF{9df8f215-6ef3-4ee2-a336-42d628680738}
```

Toàn bộ phần điều tra endpoint ở K9-K14 không phải vô ích: nó chứng minh server fail *trước khi*
parse chữ ký, tức là khóa verify của nó khác `pubkey.bin` trong handout mẫu - chính là manh mối
dẫn tới tệp artifact động. Đã kiểm tra thêm khả năng lấy cờ ngoại tuyến
(`analysis/flag_sweep.py`, 53 mảng byte x ~30 phép mã hoá): không có cờ nào trong handout.

{% endraw %}
