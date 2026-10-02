# Kintsugi Vault — Rev (Hard)

## 0. Tóm tắt

Hệ thống lõi `vmrun` là một máy ảo (VM) nội bộ sử dụng tập lệnh gồm 14 opcode. Mỗi điểm dữ liệu (node, file `.shard`) lưu trữ một bảng hoán vị opcode 256 byte (đóng vai trò "từ điển biên dịch") và một mã nhị phân dài 649 byte. Chương trình tiếp nhận 8 byte khóa (key), xử lý qua cấu trúc 3 tầng thuật toán `LUT` kết hợp trộn XOR tuyến tính, và đối chiếu 8 thanh ghi với 8 hằng số đích. Chuỗi 32 byte seed dùng để xác thực hệ thống là tổ hợp 8 byte khóa trích xuất từ 4 node. Quy trình thực hiện:

1. Phân tích cấu trúc tệp shard và tập lệnh ISA từ tệp `vmrun` (Đây là tệp nhị phân tĩnh, bị loại bỏ thông tin debug (stripped). Do yêu cầu nền tảng, hệ thống mô phỏng được phát triển lại bằng Python).
2. Tái tạo bảng biên dịch cho các node thiếu bảng mã (mô phỏng thuật ngữ "chất keo" của Kintsugi).
3. Thực hiện phân tích ngược quá trình tính toán để truy xuất khoá (key). Thao tác này đòi hỏi tính toán tất cả các nhánh nhị phân phát sinh từ các lệnh bị loại bỏ bit (`ANDI`).
4. Sắp xếp 4 mảnh khóa, đối chiếu (verify) với thuật toán Ed25519 sử dụng `pubkey.bin`.
5. Tạo chữ ký (signature) cho `nonce` và gửi yêu cầu đến `POST /attest`.

Kết quả: Chuỗi `seed = f860622f78adc147 0aba129efad830d8 1b091cc9cc9b71ee a4b10c57af5dd7af` (áp dụng cho bộ tải gốc) và `185087fcdd31641e 58f77177f104cded f29bb38be31bf782 8dd0b1fab65c4746` (đối với hệ thống live).

```text
H7CTF{9df8f215-6ef3-4ee2-a336-42d628680738}
```

Lưu ý quan trọng nằm ở mục 7: Tệp đính kèm trên trang chủ là phiên bản thử nghiệm tĩnh; hệ thống thực tế yêu cầu bộ dữ liệu tải qua `GET /handout.tar.gz`.

## 1. Phân tích định dạng Shard

```text
0x000  4 byte   Định danh 'KSHD'
0x004  1 byte   Phiên bản = 01
0x005  1 byte   Cờ cấu hình (flags); bit0 == 1 -> Bảng decode được tích hợp trong tệp.
                                 bit0 == 0 -> Yêu cầu chỉ định tệp bảng decode ngoài thông qua tham số số 3.
0x007  1 byte   Độ dài khoá (keylen) = 08
0x008  2 byte   Kích thước bảng (tablelen) = 0x100 (256 byte)
0x00a  2 byte   Kích thước mã (proglen)  = 0x289 = 649 byte
0x00e 16 byte   Định danh file (ID)      <- vmrun không kiểm tra
0x01e  4 byte   Padding                  <- vmrun không kiểm tra
0x022 16 byte   ID liên kết kế tiếp      <- vmrun không kiểm tra
0x032 256 byte  Bảng decode: Ánh xạ mã opcode thô thành lệnh thực thi
0x132 256 byte  Bảng S-box (LUT): Sử dụng hoán vị (permutation), dữ liệu công khai
0x232 649 byte  Khối mã thực thi
```

Hệ thống xử lý (`main` tại `0x402fd0`) chỉ xác nhận: kích thước tệp `size > 0x31`, đúng magic bytes, và `size >= 0x132 + tablelen + proglen`. Nếu bảng decode tải từ ngoài có `size > 0xff`, 256 byte sẽ được sao chép trực tiếp vào bộ nhớ stack (`0x4030cb`), không yêu cầu xác thực. 
Lỗ hổng nghiêm trọng: Người dùng có quyền kiểm soát nội dung bảng decode, quyết định trực tiếp hành vi thực thi lệnh của VM.

Cấu trúc Key: 16 ký tự hex, xử lý qua lệnh SSE và phân bổ 8 byte vào bộ nhớ tại `rsp+0x58`.

## 2. Giải mã Tập lệnh (ISA)

Hệ thống điều phối: `op = table[prog[pc]]`. Nếu `op == 0` -> Dừng thực thi (HALT), ghi nhận `OK` (mã 0). Nếu `op > 13` -> Lỗi `bad opcode` (mã 2). Hành vi vượt giới hạn `pc >= proglen` được đánh giá là thực thi thành công. 
Bảng nhảy (jump table) tại `0x486ba8` (chỉ mục số nguyên 32-bit tương đối) xác định tập lệnh:

| Mã lệnh (op) | Ký hiệu (mnemonic) | Kích thước | Chức năng |
|----|----------|--------|------------|
| 0 | HALT | 1 byte | Dừng thực thi, xác nhận |
| 1 | KEY | 3 byte | Gán `rA = (u32)mem8[0x58 + B]` (B từ 0..7 trỏ vào cấu trúc key. Lưu ý: B >= 8 sẽ truy cập dữ liệu bảng decode) |
| 2 | MOVI | 6 byte | Gán hằng số 32-bit `rA = imm32` |
| 3 | MOV | 3 byte | Gán giá trị thanh ghi `rA = rB` |
| 4 | XOR | 3 byte | Thực hiện `rA ^= rB` |
| 5 | ADD | 3 byte | Tính tổng module `rA = (rA + rB) % 2^32` |
| 6 | MUL | 3 byte | Tính tích module `rA = (rA * rB) % 2^32` |
| 7 | AND | 3 byte | Toán tử AND `rA &= rB` |
| 8 | OR | 3 byte | Toán tử OR `rA |= rB` |
| 9 | ROL | 3 byte | Dịch trái `rA = rol32(rA, B & 31)` (B là hằng số) |
| 10 | LUT | 3 byte | Hoán vị bảng `rA = (u32)sbox[rB & 0xff]` |
| 11 | CMP | 6 byte | Kiểm tra điều kiện: Nếu `rA != imm32` -> Lỗi `FAIL` (mã 1) |
| 12 | ANDI | 6 byte | Toán tử AND với hằng số `rA &= imm32` |
| 13 | XORI | 6 byte | Toán tử XOR với hằng số `rA ^= imm32` |

Kiến trúc thanh ghi gồm 12 block 32-bit cấp phát tại `rsp+0x30..0x57`. Mã khởi tạo chỉ xóa 8 khối đầu tiên. Do đó, thanh ghi số 10 và 11 trùng khớp địa chỉ của key. Các thanh ghi có chỉ số >= 12 sẽ ảnh hưởng bộ nhớ bảng decode hoặc con trỏ trả về (retaddr). Các đặc tính này không được khai thác thực tế trong mẫu bài nhưng được thiết lập nhằm gây hiểu nhầm phân tích.

Mã máy ảo được mô phỏng hoàn thiện tại script `vm.py`, đảm bảo khả năng tính toán chéo.

## 3. Phân loại cấu trúc xử lý Node

Phân tích mã vận hành 7 tệp shard cho thấy có 2 phương pháp tổ chức cấu trúc lệnh:

- Nhóm A (chứa ID `f6f11ad1`, `080ec62d`, `3e3a0fc9`, `cfa1fa34`): Thực thi 3 lớp `LUT` lồng ghép ma trận XOR, chốt bằng 8 lệnh `CMP` với hằng số thuộc chuẩn 1 byte. Cấu trúc mã là hệ thuật toán 64-bit chắc chắn.
- Nhóm B (chứa ID `3df10ef4`, `63bafd7f`, `f14ad4e2`): Vận hành theo chu trình đơn giản `KEY -> LUT -> ADD -> ROL -> MUL -> OR -> XORI -> CMP` với hằng số 32-bit. Lệnh `MUL` và `OR` là các hàm phân rã dữ liệu, dẫn đến tỷ lệ lỗi phân tích cao (mã `3df10ef4` có thể chấp nhận hơn 500 key). Chúng là các node trung gian cho cấu trúc mạng mesh, không lưu cờ đích.

## 4. Tái tạo Bảng biên dịch (Decode Table)

`vmrun` từ chối thực thi các shard nhóm A nếu cờ bit0 bị tắt và bảng decode không được cung cấp. Bảng tích hợp của chúng bị làm rối (random 158..163 byte độc nhất).

Quy trình tái thiết lập bảng decode:

1. Mỗi khối mã thực thi sử dụng 8 opcode. Vì bảng decode là ma trận hoán vị, mỗi raw byte yêu cầu một lệnh opcode duy nhất.
2. Dữ liệu tập lệnh: Lệnh `KEY` đặt tại chỉ số pc = 0, 3, ..., 21 kết hợp đối số `(i,i)`. Ở phần kết, 49 byte cuối yêu cầu 8 cấu trúc `CMP` cho thanh ghi `r0..r7` (so sánh hằng số 1 byte) và kết thúc bằng `HALT`.
3. Mọi lệnh có quy ước kích thước 3 hoặc 6 byte (`pc % 3 == 0`). Thực hiện ánh xạ (brute-force) 5 raw byte có tần suất cao tại các khoảng pc cho 5 opcode `{MOV, XOR, LUT, ANDI, XORI}`. Tiêu chí xác nhận: luồng điều khiển kết thúc bằng HALT, có đủ 8 lệnh CMP, thanh ghi `<= 11`, và tương thích khi tính toán đảo chiều (reverse).

Hai ID `080ec62d` và `3e3a0fc9` có cấu trúc tương đồng, có thể sao chép ánh xạ `(pc, op)` từ tệp `f6f11ad1`. ID `cfa1fa34` có vòng lặp biến đổi khác nên phải xử lý bằng thuật toán tự động. Bảng decode thu được:
`f7=KEY 79=XORI 4e=ANDI d6=LUT 4c=XOR c1=MOV bc=CMP 44=HALT`.

## 5. Phân tích ngược tính toán khóa

Cấu trúc lệnh Nhóm A:

```text
Giai đoạn 1: r0..r7 = key[0..7]
Giai đoạn 2: Lặp 1: Phân bổ (XORI r?, imm) xen kẽ (ANDI r?, mask)
Giai đoạn 3: Lặp 3: Biến đổi LUT r?,r? -> Trộn XOR 16 lần -> (XORI r?, imm)
Giai đoạn 4: Vùng đệm bằng MOV r0,r0 56 lần
Giai đoạn 5: So sánh (CMP r0..r7, byte chuẩn) -> HALT
```

Phần lớn phép toán có thể nghịch đảo, ngoại trừ `ANDI`: Các bit bị lọc bởi mask của ANDI (reset về 0) không có ảnh hưởng tới phép toán tiếp theo, tạo thành các bit tự do (free bit). 
Quá trình tính toán ngược bắt đầu từ 8 lệnh `CMP`, cho kết quả từng byte `key[i]` và các tổ hợp bit tự do, dẫn đến mỗi node có khoảng 16 đến 64 key hợp lệ.

Lỗi trong quá trình tính toán các biến thể (variants): Yêu cầu tất cả nhánh bit tự do phải được xử lý ở 2 trạng thái 0 và 1. Khởi tạo chúng về 1 sẽ loại bỏ 50% khả năng chính xác. Đây là nguyên nhân khiến quá trình xác nhận seed không thành công ở giai đoạn thử nghiệm đầu tiên.

## 6. Tổng hợp hệ Seed Xác thực

Kết hợp 4 khối khóa (mỗi khối 8 byte), 24 hoán vị kết hợp, số lượng biến thể ước tính (16 x 32 x 32 x 64). Tính toán được xử lý nhanh chóng:

```text
Chuỗi Seed = f860622f78adc147 0aba129efad830d8 1b091cc9cc9b71ee a4b10c57af5dd7af
ID quản lý:          Thuộc f6f11ad1 | Thuộc 3e3a0fc9 | Thuộc 080ec62d | Thuộc cfa1fa34
Xử lý Ed25519_pubkey(seed) = 5a0239a82fba9d2d5c6c5418e237ed8a888baeced6f4c32aa71e7be3805775ee
Đối chiếu pubkey.bin       = 5a0239a82fba9d2d5c6c5418e237ed8a888baeced6f4c32aa71e7be3805775ee  -> Khớp hoàn toàn
```

Cơ sở xác thực (oracle) ở đây là hệ mã hóa nội tại: Khi khóa công khai xuất từ seed khớp với bảng `pubkey`, thông tin seed và hoán vị tương ứng là chính xác 100%, không yêu cầu gửi xác thực về máy chủ. Việc thử nghiệm với thư viện `cryptography` bản 50.0.1 (OpenSSL) và thuật toán tự biên dịch `ed25519/ed.py` xác minh độ tin cậy.

Các phỏng đoán trước đó bao gồm lấy 8 byte mục tiêu CMP, sử dụng thông số XORI, hoặc sửa định dạng endian đều cho kết quả sai.

## 7. Xác thực API (Attestation) - Sự khác biệt phiên bản

Thực hiện lệnh `GET /attest` -> Lấy 24 byte `nonce` (chuỗi hex), gửi yêu cầu `POST /attest` với `nonce` và `sig` (chữ ký). 
Dù kết quả mã chữ ký chính xác dựa trên `pubkey.bin` (đã chứng minh bằng hai thuật toán độc lập), máy chủ liên tục trả về lỗi `400 attestation incomplete`. Nhiều phương án thay đổi cấu trúc truy vấn, thẻ HTTP và định dạng payload đều không khả thi.

Nguyên nhân lỗi: Máy chủ trả về cùng một mã thông báo lỗi cho các trường hợp chữ ký sai định dạng, thiếu độ dài, hay `nonce` không hợp lệ. Hành vi này ngăn cản phương pháp thử tự động (brute-force).

Phân tích trạng thái dẫn đến suy luận sai lầm: Phiên bản file đính kèm trên trang chủ không đồng bộ với máy chủ cấu hình.

Xác thực phiên bản qua lệnh `GET /handout.tar.gz` trên instance live. Phản hồi trả về tệp nén dung lượng 318.172 byte (khác biệt với tệp tĩnh 347.257 byte trên trang chủ). Phiên bản này chứa tệp `pubkey.bin` mới, ID của 7 node được cập nhật, với định danh node mốc là `35e266269ee5...`. Tệp đính kèm gốc là phiên bản thử nghiệm cục bộ (tham chiếu nội dung `MANIFEST.txt` ghi `team: team-local`).

Vận hành mã kiểm tra `analysis/live_solve.py` cho hệ thống live:

| Tên node | Phương pháp decode | Khóa thu hồi (8 byte) |
|----------|----------------|--------------|
| `35e266269ee5` (Nút khởi đầu, cờ 0x01) | Tái tạo bảng trực tiếp | `185087fcdd31641e` |
| `80014ce50564` | Ánh xạ opcode tự động | `58f77177f104cded` |
| `42b1de232bfc` | Ánh xạ opcode tự động | `f29bb38be31bf782` |
| `aaae515b295d` (Nút cuối, cờ 0x02) | Ánh xạ opcode tự động | `8dd0b1fab65c4746` |

```text
Mảnh ghép seed cuối = 185087fcdd31641e58f77177f104cdedf29bb38be31bf7828dd0b1fab65c4746
Chữ ký sig          = Ed25519_sign(seed, bytes.fromhex(nonce))        # Chữ ký dạng byte thô, không xuất hex
Gửi POST /attest nonce=...&sig=...  ->  200 OK
H7CTF{9df8f215-6ef3-4ee2-a336-42d628680738}
```
