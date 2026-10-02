# Prince Walk - Reverse (50 pts)

**Flag:** `CSSCTF{P12INC3_0R_P1NC3?}`
**File đính kèm:** `prince_walk` (Kích thước: 92.384 B, SHA256: `2d0c95f7...`)

## Đề bài

Đề cung cấp một binary Linux có tên `prince_walk`. Mô tả ứng dụng cho biết đây là một bộ mô phỏng "khảo sát hành tinh". Nhân vật (avatar) khởi đầu tại tọa độ `(1, 1)` và tín hiệu đích (beacon) được đặt ở tọa độ `(999999, 999999)`. Cờ (flag) nằm tại đích đến. Tuy nhiên, không có môi trường máy ảo Linux nào được cung cấp để thực thi trực tiếp binary này (chương trình yêu cầu môi trường terminal tương tác, hàm `isatty` sẽ từ chối nếu luồng I/O bị điều hướng qua pipe).

## Phân tích ban đầu

Đánh giá định dạng file thông qua lệnh `file`: File là ELF 64-bit, có cấu trúc mã vị trí độc lập (PIE), bị tước bỏ nhãn biểu tượng (stripped), liên kết động. Giá trị entropy tổng thể của file là 7.416. Lệnh `rabin2 -z` tiết lộ rằng phân đoạn chứa chuỗi ký tự kết thúc tại địa chỉ `0x8a12`. Liền kề sau đó, ở phân đoạn `.rodata`, xuất hiện một khối dữ liệu mờ (blob) kích thước 66.560 byte với entropy đạt mức rất cao là 7.98. Các thư viện phụ thuộc (Imports) như `tcgetattr`, `tcsetattr`, `ioctl`, `poll`, `isatty`, `prctl`, và `raise` cho thấy đây là một trò chơi dựa trên terminal được trang bị cơ chế chống gỡ lỗi (anti-debug).

Quá trình dịch ngược mã nguồn đem lại hai manh mối định hướng cốt lõi:

1. `FUN_00102c52` sinh dữ liệu địa hình từ tọa độ bằng `rol` và `lowbias32`, với hằng số `0x7feb352d`, `0x846ca68b`, tạo 16 word.
2. Khối 66.560 byte có kích thước `8320 * 8`. Kích thước này gợi cách đọc theo word 8 byte, nhưng không tự xác định định dạng. Phần phân tích tiếp theo dựa vào các lệnh mà binary dùng để đọc và xử lý khối đó.

## Chuỗi khai thác

**Bước 1 - Định vị hàm xử lý khối dữ liệu.** 
Có hai lệnh `lea` (load effective address) trỏ đến khối dữ liệu này nằm trong hàm `FUN_00102c52`. Phần mở đầu của hàm này chứa điều kiện:

```c
if (param_1 == 999999 && param_2 == 999999) { ... }
```

Cấu trúc logic này xác nhận rằng toàn bộ chuỗi khối dữ liệu chỉ được giải mã khi nhân vật đứng ở chính xác tọa độ đích. Nhờ đó, việc di chuyển hàng triệu bước trong môi trường mô phỏng là không cần thiết. Thay vào đó, exploit script sẽ giả lập việc gọi thẳng hàm giải mã với các tham số tọa độ mặc định `x = y = 999999`.

**Bước 2 - Trích xuất thuật toán khởi tạo khóa từ tọa độ.** 
Toán hạng giải mã được thiết kế dựa trên tọa độ đầu vào:

```c
for (i = 0; i < 16; i++)
    A[i] = lowbias32(((i+1) * 0x9e3779b9) ^ rol(999999, i+1) ^ 999999);
key  = lowbias32((rol(999999, 19) + 999999) ^ 0xa4093822);
```

**Bước 3 - Kiến trúc vòng lặp giải mã máy ảo (VM Decoder Loop).** 
Với chu kỳ biến `j` chạy từ 0 đến 8319, hệ thống xác định chỉ số mảng bản ghi thông qua phép hoán vị `idx = (217*j + 3286) mod 8320` (hệ số 217 và 8320 là hai số nguyên tố cùng nhau, đảm bảo quét toàn bộ không gian). Quá trình giải mã trích xuất từng cặp tham số:

```python
v1 = blob[2*idx]     ^ lowbias32((j * 0x9e3779b9) ^ key)
v2 = blob[2*idx + 1] ^ lowbias32(key + j + 0x6a09e667)
```

Tham số `v1` được chia thành bốn phân đoạn 4-bit (nibble) dùng làm chỉ số (index) truy xuất các ô của mảng `A`: `s = (v1>>8)&0xf`, `a = (v1>>12)&0xf`, `b = (v1>>16)&0xf`, và `r = (v1>>20)&0x1f`. Phần 8-bit thấp `v1 & 0xff` đóng vai trò là mã lệnh (opcode). Tập lệnh bao gồm `{0xff, 0xb3, 0x8b, 0x83, 0x71, 0x48, 0x12, 0x31}`. Bảy opcode đầu tiên có nhiệm vụ cập nhật mảng trạng thái `A[s]`. Opcode `0x83` đóng vai trò lệnh xuất dữ liệu (emit):

```python
pos = v2 >> 25
val = (v2 ^ A[a] ^ rol(A[b], r)) & 0xff
out[pos] = val; used[pos] = 1
A[s] ^= ((pos + val) * 0x45d9f3b) & 0xffffffff
key = (j * 0x3c6ef372 + v2 + rol(A[s] ^ A[a] ^ key ^ v1, 9)) & 0xffffffff
```
Mảng trạng thái `A` thay đổi sau mỗi byte được sinh. Do đó, mô phỏng các bước theo đúng thứ tự và giữ trạng thái giữa các byte.

**Bước 4 - Điều kiện nghiệm thu (Acceptance Criteria).** 
Hàm giải mã chỉ được cho thấy hoàn tất và trả kết quả khi hệ thống ghi nhận đúng 128 byte phát ra mà không bị ghi đè trùng lặp ở bất kỳ vị trí nào. Tại đầu ra, byte đầu tiên `out[0]` giữ thông số chiều dài nội dung văn bản cờ (bắt buộc thuộc khoảng `1..123`). Chuỗi byte từ `out[1]` đến `out[len]` phải là các ký tự văn bản in được. Cuối cùng, cụm 4 byte từ `out[len+1]` đến `out[len+4]` là mã băm FNV-1a (sử dụng thông số khởi tạo init `0x811c9dc5`, số nguyên tố prime `0x1000193`) được tính từ chính chuỗi văn bản trên, hoạt động như một cơ chế toàn vẹn dữ liệu tự thân (self-checksum).

**Kiểm chứng.** Output có FNV-1a checksum `0x763cc96c`, khớp bốn byte checksum lưu trong bytecode. Đây là phép đối chiếu output của interpreter với giá trị có trong binary.

## Flag

Chạy script:

```bash
python exploit.py files/prince_walk
```

```text
result: ok  (Xác minh chữ ký FNV 763cc96c hoàn tất, sinh thành công 128 byte, độ dài len=72)
FLAG: Developer:
"No you didn't."

MISSION COMPLETE

CSSCTF{P12INC3_0R_P1NC3?}
```

Kết quả:
```text
CSSCTF{P12INC3_0R_P1NC3?}
```

## Reproduce

Chạy script để reproduce:

```bash
python exploit.py files/prince_walk
```

Lưu ý: Môi trường yêu cầu cài đặt thư viện toán học `numpy`. Thư mục `analysis/` chứa các file `text.asm` và `main.asm` lưu trữ kết quả phân rã mã (disassembly) toàn bộ phân vùng `.text` và cấu trúc các hàm lõi (`main`/`FUN_00104c3`/`FUN_001051a2`). Những tài liệu này được sử dụng để đối chiếu tham chiếu cấu trúc trong quá trình thiết lập các hàm tính toán mô phỏng.
