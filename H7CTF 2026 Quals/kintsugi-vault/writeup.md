# Kintsugi Vault — Rev (Hard)

## 0. Tóm tắt

Hệ thống lõi `vmrun` là một máy ảo (VM) tự thiết kế, sở hữu vỏn vẹn 14 mã lệnh (opcode). Mỗi một vệ sĩ (`.shard` - mảnh vỡ) trong mạng lưới mang trong mình một bảng hoán vị opcode 256 byte (đóng vai trò như "chìa khóa biên dịch") và một cuộn mã chương trình dài 649 byte. Chương trình này có nhiệm vụ hút 8 byte khoá bí mật (key) từ dòng lệnh, ném chúng vào cối xay 3 tầng thuật toán `LUT` kết hợp cùng hỗn hợp trộn XOR tuyến tính, và cuối cùng đem 8 thanh ghi đối chiếu với 8 hằng số niêm phong. Hạt giống (seed) 32 byte để mở cái Két sắt (Vault) chính là kết quả của việc xâu chuỗi 8 byte khoá của 4 gã vệ sĩ đó lại với nhau. Nhiệm vụ phải làm:

1. Phẫu thuật và trích xuất định dạng shard cũng như tập lệnh ISA từ tệp `vmrun` (Đây là tệp nhị phân tĩnh (static binary), bị tước nhãn (stripped). Ác mộng là nó không thể chạy trực tiếp nếu máy chủ thiếu Docker/WSL, buộc ta phải viết lại bộ máy mô phỏng bằng Python).
2. Phục dựng lại bảng biên dịch (decode) cho những gã vệ sĩ không có bảng đi kèm ("chất keo đã mất" - theo ngữ cảnh Kintsugi).
3. Đảo ngược chiều thời gian, chạy lùi chương trình để mò ra khoá (key). Quá trình này đòi hỏi phải chấp nhận và vét cạn cả 2 nhánh phân kì (nhánh 0 và nhánh 1) sinh ra từ các bit đã bị lệnh `ANDI` nghiền nát.
4. Xoay vòng lắp ghép mọi thứ tự của 4 mảnh khoá, rọi đèn soi chiếu chúng qua lăng kính mã hoá Ed25519 với tệp `pubkey.bin`.
5. Đóng mộc chữ ký vào mã `nonce` và đem nộp lên cổng `POST /attest`.

Thành quả: Khối `seed = f860622f78adc147 0aba129efad830d8 1b091cc9cc9b71ee a4b10c57af5dd7af` (dành cho bộ tệp mẫu phát sẵn) và với bộ dữ liệu thật móc ra từ instance là `185087fcdd31641e 58f77177f104cded f29bb38be31bf782 8dd0b1fab65c4746`.

```text
H7CTF{9df8f215-6ef3-4ee2-a336-42d628680738}
```

Chi tiết chết người nằm ở mục 7: File tải về trên trang chủ chỉ là bản demo tĩnh của tác giả; máy chủ thật sự đang nhả một bản thiết kế sống (dynamic) riêng biệt qua cổng `GET /handout.tar.gz`.

## 1. Mổ xẻ định dạng Shard

```text
0x000  4 byte   Dấu ấn 'KSHD'
0x004  1 byte   Phiên bản = 01
0x005  1 byte   Cờ báo (flags); Nếu bit0 == 1 -> Bảng decode được nhúng thẳng vào ruột file (vệ sĩ đầu đàn).
                                Nếu bit0 == 0 -> BẮT BUỘC người dùng phải mớm file bảng từ bên ngoài thông qua tham số số 3.
0x007  1 byte   Độ dài khoá (keylen) = 08
0x008  2 byte   Kích thước bảng (u16 tablelen) = 0x100 (256 byte)
0x00a  2 byte   Độ dài mã lệnh (u16 proglen)  = 0x289 = 649 byte
0x00e 16 byte   ID định danh (chính là tên file)      <- Chú ý: vmrun KHÔNG BAO GIỜ xác thực trường này
0x01e  4 byte   (Đồ thừa, không dùng)                  <- vmrun KHÔNG BAO GIỜ đoái hoài
0x022 16 byte   ID "kẻ kế vị" (next) đã bị làm nhiễu   <- vmrun KHÔNG BAO GIỜ thèm check
0x032 256 byte  Bảng decode: Lọc mã lệnh thô (raw) chuyển thành số thứ tự của trạm xử lý (handler)
0x132 256 byte  Hộp thay thế sbox (LUT): Luôn luôn là một phép hoán vị (permutation), luôn phơi bày trong suốt
0x232 649 byte  Trái tim: Cuộn mã chương trình
```

Máy kiểm duyệt `main` (tại địa chỉ `0x402fd0`) chỉ ngó lơ qua vài chỉ số: file `size > 0x31`, đúng chữ ký magic, và file `size >= 0x132 + tablelen + proglen` (ngừa lỗi file lửng `truncated shard`). File bảng decode bên ngoài chỉ cần có độ dài `> 0xff` byte là sẽ được sao chép thẳng cẳng 256 byte nhét vào ngăn xếp stack (tại `0x4030cb`), không hề có sự pha trộn (mix) hay kiểm toán nội dung nào với file shard. 
Lỗ hổng từ trên trời rơi xuống: Chúng ta được trao quyền sinh sát tuyệt đối tự bịa ra một bảng decode, chỉ cần nó xúi giục chương trình chạy đúng hướng là xong.

Định dạng Key: 16 ký tự mã hex (không phân biệt hoa/thường), được hệ thống nghiền bằng lệnh SSE và khắc 8 byte liền tù tì vào vùng nhớ tại `rsp+0x58`.

## 2. Giải mã Tập Lệnh (ISA)

Cơ chế điều phối (Dispatch): `op = table[prog[pc]]`. Nếu `op == 0` -> Đạp thắng (HALT), in chữ `OK`, thoát với mã exit 0. Nếu `op > 13` -> Báo lỗi `bad opcode`, thoát mã 2. Việc chương trình chạy lố giới hạn `pc >= proglen` cũng được ưu ái phán là thành công. 
Mổ xẻ bảng nhảy (jump table) tại toạ độ `0x486ba8` (kiểu số nguyên 32-bit có dấu, ánh xạ tương đối), ta có từ điển tập lệnh sau:

| Mã lệnh (op) | Ký hiệu (mnemonic) | Kích thước | Chức năng (Ngữ nghĩa) |
|----|----------|--------|------------|
| 0 | HALT | 1 byte | Dừng chân, xưng vương (chấp nhận) |
| 1 | KEY | 3 byte | Gắn `rA = (u32)mem8[0x58 + B]` (B từ 0..7 trỏ vào key. Độc địa: Nếu B >= 8, nó sẽ đọc trộm luôn dữ liệu trong bảng decode!) |
| 2 | MOVI | 6 byte | Ép `rA = hằng số 32-bit (imm32)` |
| 3 | MOV | 3 byte | Sao chép `rA = rB` |
| 4 | XOR | 3 byte | Thực hiện `rA ^= rB` |
| 5 | ADD | 3 byte | Phép cộng `rA = (rA + rB) theo modulo 2^32` |
| 6 | MUL | 3 byte | Phép nhân `rA = (rA * rB) theo modulo 2^32` |
| 7 | AND | 3 byte | Phép và `rA &= rB` |
| 8 | OR | 3 byte | Phép hoặc `rA |= rB` |
| 9 | ROL | 3 byte | Xoay trái `rA = rol32(rA, B & 31)` - Lưu ý: B là hằng số imm8, không phải chỉ số thanh ghi |
| 10 | LUT | 3 byte | Tra hộp `rA = (u32)sbox[rB & 0xff]` (Quét sạch 24 bit cao đi) |
| 11 | CMP | 6 byte | Đối chiếu: Nếu `rA != imm32` -> Hét lên `FAIL`, tử ẹo exit 1 |
| 12 | ANDI | 6 byte | Phép và với hằng số `rA &= imm32` |
| 13 | XORI | 6 byte | Phép XOR với hằng số `rA ^= imm32` |

Trận đồ thanh ghi (Registers) gồm 12 ô 32-bit nằm dạt từ `rsp+0x30..0x57`. Mã huỷ `rep stos` lười biếng chỉ chịu xoá sạch 8 ô đầu tiên. Hệ quả: Ô số 10 và 11 trùng khít với vị trí cất giữ 8 byte key, trong khi các ô mang chỉ số >= 12 lại đâm chọc thẳng (alias) vào bộ ruột bảng decode đang sống lù lù trên đó (Nghĩa là chương trình có thể dùng nó để tự biến đổi não bộ của mình). Xa hơn, ô >= 0x4e sẽ kích nổ bom canary hoặc đạp lên địa chỉ trả về (retaddr). 
Rất tiếc (hoặc may mắn), không có bất kỳ vệ sĩ nào trong bộ file sử dụng tới các chỉ số hiểm ác đó - chúng chỉ là những cái bẫy tâm lý tác giả bày ra để rung cây dọa khỉ.

Toàn bộ bảng mã lệnh và hệ thống bẫy đã được chứng thực bằng việc tự code lại hoàn toàn Máy ảo (`vm.py`, lớp `VM`), đối sánh chéo với biên bản dịch ngược (disassembly) để không sót một hạt sạn.

## 3. Lưỡng phái Vệ Sĩ

Dựa vào cách tự chuyển hoá bản thân thông qua bảng mã nội trú, 7 shard được quy hoạch thành hai dòng dõi:

- Dòng A cao quý (gồm `f6f11ad1`, `080ec62d`, `3e3a0fc9`, `cfa1fa34`): Cày 3 lớp `LUT` quyện với ma trận trộn XOR, và chốt hạ bằng 8 đòn `CMP` mà phần hằng số (immediate) nằm trọn trong 1 byte. Đây đích thị là lõi mã 64-bit thứ thiệt.
- Dòng B lao động (gồm `3df10ef4`, `63bafd7f`, `f14ad4e2`): Chạy một chuỗi nông cạn `KEY -> LUT -> ADD -> ROL -> MUL -> OR -> XORI -> CMP` với hằng số phình to 32-bit. Kẻ thủ ác `MUL` và `OR` mang bản chất phá hủy thông tin, khiến tấm khiên phòng thủ (phép kiểm) trở nên rách nát: test chay mã `3df10ef4` nhả ra tới chừng 528 key cùng lọt. Chúng chỉ là "đám lính tốt thí mạng" lót đường cho mạng lưới mesh, hoàn toàn không giữ cờ.

## 4. Phục dựng "chất keo" (Bảng biên dịch)

Cỗ máy `vmrun` sẽ khước từ phục vụ (từ chối chạy) những shard dòng A mang cờ bit0 tắt ngúm nếu ta không tự móc bảng biên dịch đút cho nó. Và ác thay, bảng thật thì không hề tồn tại trong ruột file (khu vực 0x32 của chúng chỉ chứa một đống hổ lốn ngẫu nhiên gồm 158..163 giá trị dị biệt).

Phương pháp tái sinh bảng, dựa trên chính điểm yếu của cỗ máy:

1. Mỗi cuốn mã chỉ triệu hồi lặp lại tầm 8 opcode. Vì bản thân bảng thật là một phép hoán vị (permutation) không có chỗ cho sự trùng lặp, nên mỗi một mã raw (raw byte) bắt buộc phải chĩa về một opcode độc nhất.
2. Bản đồ lệnh đã lộ sáng một góc: 8 lệnh mớm mồi `KEY` cắm cọc tại các toạ độ pc = 0, 3, ..., 21 đi kèm tham số đều chằn chặn `(i,i)`. Ở đuôi, khúc vĩ thanh 49 byte cuối bắt buộc phải là 8 phát `CMP` lên các thanh ghi `r0..r7` (so với hằng số 1 byte) và thắt cổ bằng 1 byte `HALT`. Vậy là bộ ba `KEY`, `CMP`, `HALT` đã bị trói chặt.
3. Kích thước mọi lệnh bị khoá ở 3 hoặc 6 byte, suy ra toạ độ mọi mã lệnh phải chia hết cho 3 (`pc % 3 == 0`). Ta bốc 5 raw byte có tần suất thét gào cao nhất tại các toạ độ này, và nhét chúng vào cái khuôn vét cạn (brute-force) của bộ `{MOV, XOR, LUT, ANDI, XORI}` (Đỉnh điểm là 6720 trường hợp). Lệnh duyệt chỉ chấp thuận phép gán khi nó thỏa mãn tiêu chí: cày mượt từ đầu tới cuối, đâm sầm vào HALT ngay byte cuối, đếm tròn 8 lệnh `CMP`, mọi chỉ số thanh ghi đều nằm ngoan trong giới hạn `<= 11`, và đặc biệt, phải chạy ngược chiều được mà không bị sặc (mâu thuẫn).

Riêng đối với `080ec62d` và `3e3a0fc9`, có một đường cao tốc trải sẵn: chỉ cần copy - paste nguyên xi ma trận `(pc, op)` của thằng đàn anh `f6f11ad1` sang, chúng ăn khớp 0 xung đột. Chứng tỏ bộ ba này được đúc ra từ cùng một cái khuôn. Kẻ dị biệt `cfa1fa34` bước hụt nhịp vì vòng xoáy `XORI/ANDI` mở màn của nó quăng tới 5 vòng thay vì 4, buộc ta phải cày bằng thuật toán tìm kiếm. Bảng decode mổ ra được của nó là:
`f7=KEY 79=XORI 4e=ANDI d6=LUT 4c=XOR c1=MOV bc=CMP 44=HALT`.

## 5. Dò ngược vết chân Khoá (Suy ngược key)

Với trong tay bảng dịch đúng, mã của dòng A phơi bày cấu trúc:

```text
Giai đoạn 1: r0..r7 = key[0..7]
Giai đoạn 2: Lặp vòng 1: Gieo (XORI r?, imm) xen (ANDI r?, mask) rải rác trên vài thanh ghi.
Giai đoạn 3: Lặp vòng xoáy x3 lần: Đẩy LUT r?,r? -> Hoà 16 đòn XOR trộn nhau -> Khóa (XORI r?, imm)
Giai đoạn 4: Chạy rà (padding) bằng MOV r0,r0 56 lần
Giai đoạn 5: Soi chốt (CMP r0..r7, byte đích) -> Chém (HALT)
```

Mọi đòn đánh đều có thể bị bẻ ngược (đảo), ngoại trừ tên khốn `ANDI`: Bất cứ bit nào bị cái rây (mask) của ANDI làm mờ (xoá) sẽ mang thân phận "bất tử" - nó chẳng bao giờ ảnh hưởng tới đích đến cuối cùng, biến nó thành một biến tự do (free bit). 
Quay ngược bánh xe thời gian từ 8 lệnh `CMP` bò về vạch xuất phát, ta moi ra được giá trị nguyên thủy của từng con chữ `key[i]` cùng với một rổ các bit tự do; hậu quả là mỗi tên vệ sĩ sẽ mở cửa với 16..64 key khác nhau thay vì chỉ trung thành với 1.

Cạm bẫy huỷ diệt khi cày vét cạn biến thể (variants): Bạn BẮT BUỘC phải ép các bit tự do tẻ ra thành cả 2 nhánh nhánh 0 và nhánh 1. Nếu chỉ lười biếng bật chúng lên 1 (`k[s] |= 1 << b`), bạn sẽ chém đứt chính xác một nửa vũ trụ khả năng. Và đó chính là vết xe đổ khiến lần mò ráp seed đầu tiên nhả về kết quả 0, dù lõi thuật toán vạch ra đã hoàn hảo.

## 6. Lắp ghép Seed Két Sắt

Trong tay có 4 mảnh khoá (mỗi mảnh 8 byte), 24 hoán vị thứ tự, nhân bung bét các cụm biến thể (16 x 32 x 32 x 64) - khối tính toán này bị nén chặt và dọn dẹp sạch sẽ chỉ trong vòng chưa đầy một phút:

```text
Mảnh khoá (seed) = f860622f78adc147 0aba129efad830d8 1b091cc9cc9b71ee a4b10c57af5dd7af
Dòng máu:          Thuộc vệ sĩ f6f11ad1 | Thuộc 3e3a0fc9 | Thuộc 080ec62d | Thuộc cfa1fa34
Dội qua Ed25519_pubkey(seed) nôn ra = 5a0239a82fba9d2d5c6c5418e237ed8a888baeced6f4c32aa71e7be3805775ee
Soi với tệp mẫu pubkey.bin           = 5a0239a82fba9d2d5c6c5418e237ed8a888baeced6f4c32aa71e7be3805775ee  -> Khớp hoàn hảo đến từng lỗ chân lông
```

Lời sấm truyền (Oracle) ở đây nằm ở toán học, không phải van xin máy chủ: Khóa công khai phái sinh từ seed trùng khít đồng nghĩa với việc 4 mảnh key và thứ tự đứng của chúng là đáp án độc tôn, khỏi cần đợi điểm truy cập (endpoint) gật đầu. Quá trình kiểm chứng chéo cặp (seed -> pubkey) được rèn bởi hai hệ thống độc lập: Thư viện `cryptography` bản 50.0.1 (chạy OpenSSL) và hàng thửa `ed25519/ed.py` (tự đúc bằng code thuần stdlib), cả hai đều vượt trót lọt 3 mốc vector kiểm định RFC 8032 mục 7.1.

Các thuyết âm mưu đã bị đập nát nhờ oracle này (toàn bộ cho ra kết quả trật chìa): 8 byte đích của lệnh `CMP` móc nối với nhau; lấy toàn bộ các hằng số `XORI`; quét mọi cửa sổ 32 byte dạt quanh mọi file; nhặt nhạnh các cặp data 16 byte ở phần mào đầu (`id`, `next`); hay lật ngược trật tự byte (endianness).

## 7. Cửa ải Xác thực (Attestation) - Trạng thái lật lọng

Y như sách giáo khoa README chỉ bảo, hợp đồng được triển khai: Quất `GET /attest` -> Hút về 24 byte nonce (chuỗi 48 ký tự hex), sau đó tọng vào `POST /attest` kẹp theo `nonce` và mã chữ ký `sig` (hex). Chữ ký ta tự luyện ra có thể tự tay bóc tem xác thực mượt mà bằng file `pubkey.bin` ngay trên ổ cứng (nhấn mạnh: đã test chéo bằng 2 công cụ độc lập). 
Thế mà, cỗ máy chủ khốn nạn lại trả về mặt lạnh te `400 attestation incomplete` cho *TOÀN BỘ* các biến thể được quăng lên - bạn có thể check độ tuyệt vọng tại bảng `notes.md` phần K9/K11: Đổi đủ kiểu đúc thông điệp, nhào nặn mọi thể loại format body, bóp méo (alias) mọi field, thử cả thảy 40 cặp GET+POST nhồi trong cùng một luồng duy trì (keep-alive), vọc luôn các thẻ `OPTIONS/PUT/PATCH/DELETE` (bất chấp việc mã nguồn chỉ mở cổng `GET, POST, OPTIONS, HEAD` và chỉ thông một đường duy nhất `/attest`).

Gót chân Achilles của sự vụ: Máy chủ phun ra một câu từ chối y chang nhau bất kể ta đưa `sig="zz"` (định dạng hex rác), `sig` thừa thiếu độ dài, hụt field thông tin, hay thậm chí ném vào một cái nonce chưa từng được đăng ký. Nghĩa là nó đập chết hy vọng mò mẫm (brute-force) vì ta không thể rạch ròi đâu là lỗi "nonce bay màu" đâu là lỗi "chữ ký phế".

Chuỗi lập luận rối rắm lúc bấy giờ đã dắt mũi tới một kết luận hoang tưởng: "Bộ dữ liệu mẫu ăn khớp, chữ ký đúng chuẩn, nhưng máy chủ kiên quyết lắc đầu => Cái container đang chạy chả dính dáng mẹ gì tới cái mớ file ta đang giữ". Sự thật phũ phàng là: Kết luận này đúng một nửa. Đúng là cái artifact ta cầm chả liên quan, nhưng không phải do máy chủ bị điên.

Khoá giải mã thực sự nằm ở một đường hầm mà không ai chịu chui vào: Bắn request `GET /handout.tar.gz` ngay trên chính máy chủ mục tiêu đang sống (instance). Nó nôn về mã 200, kèm theo một cục dữ liệu 318.172 byte (sha256 `6bbfc07a...`) - một giống loài biến dị hoàn toàn so với cái cục xác thối tĩnh 347.257 byte (`4ce8375d...`) gắn trên trang đề bài. 
Bản ngự trị trên máy chủ đẻ ra một cái `pubkey.bin` lạ hoắc (`5b0a2f81...`), 7 thằng vệ sĩ mang ID nội tạng hoàn toàn khác, nút thắt chuỗi khai mào biến thành `35e266269ee5...`, và đồng hồ sinh học (timestamp) điểm đúng lúc máy chủ bật dậy. Tóm gọn: File đính kèm tải từ trang chủ chỉ là bản nháp đồ chơi của tác giả vứt lại (chi tiết chết người trong `MANIFEST.txt` ghi `team: team-local` - tín hiệu cảnh báo đã hiện diện nhưng đội săn lùng đã lờ đi quá lâu).

Kích hoạt lại đường ống tiêu diệt (`analysis/live_solve.py <thu_muc>`) cắm thẳng vào bộ artifact xương máu thật:

| Tên vệ sĩ | Phương pháp bóc bảng | Khoá key (8 byte) moi được |
|----------|----------------|--------------|
| `35e266269ee5` (Nút khởi đầu, ôm cờ 0x01) | Rút bảng trong suốt từ chính nó | `185087fcdd31641e` |
| `80014ce50564` | Cày vét thuật toán gán mã raw->op | `58f77177f104cded` |
| `42b1de232bfc` | Cày vét thuật toán gán mã raw->op | `f29bb38be31bf782` |
| `aaae515b295d` (Nút chốt sổ, ôm cờ 0x02) | Cày vét thuật toán gán mã raw->op | `8dd0b1fab65c4746` |

```text
Mảnh ghép seed cuối = 185087fcdd31641e58f77177f104cdedf29bb38be31bf7828dd0b1fab65c4746
Chữ ký sig          = Ed25519_sign(seed, bytes.fromhex(nonce))        # Bắn ra chuỗi 24 byte nguyên thủy (thô), KHÔNG PHẢI chuỗi hex định dạng
Nã pháo POST /attest kèm nonce=...&sig=...  ->  Phản hồi 200 OK
H7CTF{9df8f215-6ef3-4ee2-a336-42d628680738}
```

Nhìn lại, cuộc vật lộn đẫm máu test endpoint ở dải K9-K14 không hề thừa thãi: Nó là minh chứng thép cho việc máy chủ đã "đứt gánh" *trước khi* thèm ngó qua mớ chữ ký. Nghĩa là chìa khoá verify trong bụng nó đã không còn là cái `pubkey.bin` rởm trong bộ handout nữa - đây là chỉ điểm cực mạnh dẫn dắt tới manh mối tệp động (dynamic artifact). 
(Chi tiết bên lề: Công cụ vét cạn cờ offline `analysis/flag_sweep.py` từng cày 53 khối byte trộn với ~30 phép biến đổi mã hoá, và kết luận rạch ròi: KHÔNG ĐÀO ĐÂU RA cờ ẩn trong cái bộ handout mồi nhử kia cả).
