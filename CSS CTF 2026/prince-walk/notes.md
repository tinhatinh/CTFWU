# notes.md - prince-walk

Input: `files/prince_walk` (92384 B, sha256 `2d0c95f718b84f07d94173def6753a105260a8d1a46e92cac9d8352e84ee5812`)
Định dạng cờ đề yêu cầu: `CSSCTF{...}`

## H1 - Cờ là một chuỗi ký tự trong .rodata
cmd: `rabin2 -z files/prince_walk | grep -i cssctf`
evidence: 0 kết quả; toàn bộ chuỗi đọc được dừng ở `0x8a12` ("Cannot load an X11 font."), sau đó là khối 66560 byte entropy 7.98.
result: DEAD - không có plaintext.

## H2 - Khối entropy cao là dữ liệu nén
cmd: `python -c "so 8 byte dau moi block 4KB"`
evidence: entropy mỗi block 4 KB đều 7.97-7.98, không có magic zlib (`78 9c`) hay zstd; khối có độ dài chính xác `8320 * 8` byte.
result: DEAD - là payload đã bị làm trắng theo từng cặp từ 32 bit.

## H3 - Không có code nào tham chiếu khối đó
cmd: `r2 -c "aaa; pd 8600 @ 0x1340" | grep "; 0x"`
evidence: chỉ thấy các annotation trỏ vào `0x4000..0x4999` và `.data.rel.ro`; kết luận sai là khối không dùng tới.
result: DEAD - annotation của r2 bỏ sót; liệt kê mọi toán hạng RIP-relative bằng capstone thì thấy `lea` tại `0x2e6a` và `0x2ea3` trỏ đúng `0x4a80`/`0x4a84`.

## H4 - Hai lea đó nằm trong hàm nào và được guard bằng gì
cmd: `r2 -c "aaa; s fcn.00102c52; pdf"` (Ghidra: `FUN_00102c52`)
evidence: đầu hàm là `cmp dword [x], 0xf423f; cmp dword [y], 0xf423f`, tức chỉ chạy khi toạ độ là `(999999, 999999)`; ngay trước vòng lặp có bảng 16 từ `A[i] = lowbias32(((i+1)*0x9e3779b9) ^ rol(999999, i+1) ^ 999999)` và khoá `key = lowbias32((rol(999999,19)+999999) ^ 0xa4093822)`.
result: PENDING -> xác nhận ở H5.

## H5 - Viết lại hàm đó bằng Python
cmd: `python exploit.py files/prince_walk`
evidence: vòng `j = 0..8319` với `idx = (217*j + 3286) mod 8320`, `v1 = blob[2*idx] ^ lowbias32(j*0x9e3779b9 ^ key)`, `v2 = blob[2*idx+1] ^ lowbias32(key + j + 0x6a09e667)`; opcode `v1 & 0xff` thuộc `{0xff, 0xb3, 0x8b, 0x83, 0x71, 0x48, 0x12, 0x31}`, trong đó `0x83` phát một byte tại `v2 >> 25`; khoá tiến hoá `key = j*0x3c6ef372 + v2 + rol(A[s]^A[a]^key^v1, 9)`.
result: OK - đúng 128 byte được phát ra, không va chạm vị trí.

## H6 - Kết quả có phải chuỗi hợp lệ không
cmd: xem `result:` mà exploit in ra
evidence: byte 0 của payload là độ dài 72, bốn byte tại `payload[73:77]` là `763cc96c` và FNV-1a trên `payload[1:73]` tính ra đúng `0x763cc96c`; mọi byte trong khoảng in được.
result: OK - cờ: `CSSCTF{P12INC3_0R_P1NC3?}`

## Ghi chú thêm
- Bảng landmark trong `.data.rel.ro` (`0x16be0`, stride 32) cho các mốc `(69,420)`, `(404,404)`, `(1337,1337)`, `(0,0)`, `(-1,-1)`, `(999999,999998)`, `(9999999,9999999)` và 10 achievement; `FUN_001029ca` còn phân biệt "đi bộ thật" (`inputs > 2000000`) với tới đích theo cách khác. Không cần tới chúng để lấy cờ, nhưng chúng là thứ chứng minh khối kia là payload chứ không phải ảnh hay map.
- Địa hình sinh thủ tục bằng `rol` + `lowbias32` (hằng `0x7feb352d`, `0x846ca68b`), nên không có map nào được lưu trong file.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
