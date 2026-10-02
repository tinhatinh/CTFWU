# Prince Walk - Reverse (50 pts)

**Flag:** `CSSCTF{P12INC3_0R_P1NC3?}`
**File đính kèm:** `prince_walk` (Kích thước: 92.384 B, SHA256: `2d0c95f7...`)

## Đề bài

Hệ thống cung cấp một tệp nhị phân (binary) Linux có tên `prince_walk`. Mô tả ứng dụng cho biết đây là một bộ mô phỏng "khảo sát hành tinh". Nhân vật (avatar) khởi đầu tại tọa độ `(1, 1)` và tín hiệu đích (beacon) được đặt ở tọa độ `(999999, 999999)`. Cờ (flag) nằm tại đích đến. Tuy nhiên, không có môi trường máy ảo Linux nào được cung cấp để thực thi trực tiếp tệp nhị phân này (chương trình yêu cầu môi trường terminal tương tác, hàm `isatty` sẽ từ chối nếu luồng I/O bị điều hướng qua pipe).

## Phân tích ban đầu

Đánh giá định dạng tệp thông qua lệnh `file`: Tệp là ELF 64-bit, có cấu trúc mã vị trí độc lập (PIE), bị tước bỏ nhãn biểu tượng (stripped), liên kết động. Giá trị entropy tổng thể của tệp là 7.416. Lệnh `rabin2 -z` tiết lộ rằng phân đoạn chứa chuỗi ký tự kết thúc tại địa chỉ `0x8a12`. Liền kề sau đó, ở phân đoạn `.rodata`, xuất hiện một khối dữ liệu mờ (blob) kích thước 66.560 byte với entropy đạt mức rất cao là 7.98. Các thư viện phụ thuộc (Imports) như `tcgetattr`, `tcsetattr`, `ioctl`, `poll`, `isatty`, `prctl`, và `raise` cho thấy đây là một trò chơi dựa trên terminal được trang bị cơ chế chống gỡ lỗi (anti-debug).

Quá trình dịch ngược mã nguồn đem lại hai manh mối định hướng cốt lõi:

1. Cơ chế sinh địa hình: Hệ tọa độ bản đồ không được lưu trữ tĩnh mà tạo ra theo dạng sinh thủ tục. Hàm `FUN_00102c52` sử dụng phép quay bit `rol` và thao tác rút gọn 32-bit `lowbias32` (với các hằng số `0x7feb352d`, `0x846ca68b`) để khởi tạo 16 từ (word). Điều này chứng minh khối dữ liệu 66.560 byte kia không phải là dữ liệu bản đồ.
2. Cấu trúc số học: Kích thước 66.560 tương đương với công thức `8320 * 8`. Đây là một con số quá tròn trịa và bất thường để có thể là một tệp ảnh hay một khối dữ liệu nén tiêu chuẩn.

## Chuỗi khai thác

**Bước 1 - Định vị hàm xử lý khối dữ liệu.** 
Có hai lệnh `lea` (load effective address) trỏ đến khối dữ liệu này nằm trong hàm `FUN_00102c52`. Phần mở đầu của hàm này chứa điều kiện:

```c
if (param_1 == 999999 && param_2 == 999999) { ... }
```

Cấu trúc logic này xác nhận rằng toàn bộ chuỗi khối dữ liệu chỉ được giải mã khi nhân vật đứng ở chính xác tọa độ đích. Nhờ đó, việc di chuyển hàng triệu bước trong môi trường mô phỏng là không cần thiết. Thay vào đó, kịch bản khai thác sẽ giả lập việc gọi thẳng hàm giải mã với các tham số tọa độ mặc định `x = y = 999999`.

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

Một điểm thiết kế vô cùng chặt chẽ là mảng biến đổi trạng thái `A` liên tục thay đổi sau mỗi byte được sinh ra. Điều này vô hiệu hóa mọi nỗ lực chia nhỏ (tách rời) việc tính toán từng byte một cách đơn lẻ. Mọi quá trình sinh số phải tuân thủ nghiêm ngặt chuỗi tính toán nội vi.

**Bước 4 - Điều kiện nghiệm thu (Acceptance Criteria).** 
Hàm giải mã chỉ được chứng nhận hoàn tất và trả kết quả khi hệ thống ghi nhận đúng 128 byte phát ra mà không bị ghi đè trùng lặp ở bất kỳ vị trí nào. Tại đầu ra, byte đầu tiên `out[0]` giữ thông số chiều dài nội dung văn bản cờ (bắt buộc thuộc khoảng `1..123`). Chuỗi byte từ `out[1]` đến `out[len]` phải là các ký tự văn bản in được. Cuối cùng, cụm 4 byte từ `out[len+1]` đến `out[len+4]` là mã băm FNV-1a (sử dụng thông số khởi tạo init `0x811c9dc5`, số nguyên tố prime `0x1000193`) được tính từ chính chuỗi văn bản trên, hoạt động như một cơ chế toàn vẹn dữ liệu tự thân (self-checksum).

**Bước kiểm chứng.** Khi thực thi, tải trọng tự xác thực tính hợp lệ của chính nó. Mã băm FNV-1a đo được là `0x763cc96c`, trùng khớp hoàn toàn với 4 byte checksum được tác giả cố tình nhúng vào luồng mã. Sự đồng bộ này là bảo chứng toán học cho thấy chuỗi dữ liệu nhận được chính xác là chuỗi mà tệp nhị phân sẽ in ra trên hệ thống đích.

## Flag

Quá trình thực thi mã kịch bản:

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

Quá trình tự động tái thiết lập bằng công cụ (script):

```bash
python exploit.py files/prince_walk
```

Lưu ý: Môi trường yêu cầu cài đặt thư viện toán học `numpy`. Thư mục `analysis/` chứa các tệp `text.asm` và `main.asm` lưu trữ kết quả phân rã mã (disassembly) toàn bộ phân vùng `.text` và cấu trúc các hàm lõi (`main`/`FUN_00104c3`/`FUN_001051a2`). Những tài liệu này được sử dụng để đối chiếu tham chiếu cấu trúc trong quá trình thiết lập các hàm tính toán mô phỏng.
