# RoboCall - Pwn (Hard)

**Flag:** `sun{you_must_be_some_sort_of_nimble_space_navigator}`

## Phân tích

Binary được bảo vệ bằng hàng loạt cơ chế bảo mật: PIE, NX, Partial RELRO và vẫn còn giữ nguyên bảng symbol. Đặc biệt, file không chứa bất kỳ gadget dạng `pop reg; ret` nào (`5f c3`, `5e c3`, `5a c3`), bảng PLT cũng hoàn toàn vắng bóng các hàm thực thi shell như `system` hay `execve`. Không những thế, mọi bộ đệm tiếp nhận dữ liệu đầu vào đều được kiểm soát kích thước.

Cụ thể, hàm `raw_readline(buf, len)` giới hạn khắt khe số lượng byte được đọc và luôn tự động chốt hạ bằng ký tự null `\0` tại vị trí `buf[len-1]`. Áp dụng với cấu trúc `buf = rbp-0x100, len = 0x100`, byte cuối cùng ghi được sẽ dừng lại ở `rbp-0x01`. Vì con trỏ rbp lưu trữ (Saved RBP) nằm ngay tại vị trí `[rbp]`, cách vùng ghi tối đa đúng 1 byte, lỗ hổng buffer overflow hay khai thác ROP truyền thống là hoàn toàn vô vọng.

## Lỗ hổng đọc bộ nhớ

Mấu chốt của bài toán lại nằm ở một lỗi sơ đẳng: sử dụng biến trên stack mà không khởi tạo giá trị ban đầu.

```asm
raw_parse_int(rdi=str, rsi=out):
  14c6:  cmp    al,0x2f          ; kiểm tra nếu ký tự đầu tiên không phải là chữ số
  14c8:  jle    14de
  14de:  mov    eax,0x0
  14e3:  jmp    156a             ; trả về 0 -> KHÔNG hề ghi giá trị vào biến con trỏ *out
```

Nhánh thoát sớm này đã vô tình bỏ qua việc gán giá trị cho con trỏ `*out`. Khi các hàm gọi tới nó truyền vào địa chỉ của một biến cục bộ chưa được khởi tạo, biến đó sẽ giữ nguyên giá trị rác sẵn có trên stack. Cụ thể, trong hàm `cancel_plan`, giá trị rác này sau đó lại được in thẳng ra màn hình:

```asm
2f34:  print "You've entered \""
2f4b:  raw_print_int([rbp-0x204])      ; in ra ô nhớ chưa hề được ghi
2f50:  print "\", are you sure?"
```
Khi input không phải số nguyên, chương trình in bốn byte đang có trên stack dưới dạng số nguyên có dấu. Dùng kết quả này làm memory leak cho bước sau.

## Lời giải

**Bước 1 - Truy tìm vị trí cờ trên stack.**
Cờ không nằm một chỗ mà đã bị xé lẻ trên stack bởi hàm `place_flag()` (hàm này được thực thi trước khi hiển thị menu):

```asm
18f8:  open("flag.txt", 0)
1938:  read(fd, rbp-0x2060, 0x3c)          ; đọc 60 byte
loop i = 0..12:
  d    = CHUNK_DEPTH[i]                   ; tham chiếu từ bảng số nguyên u32 tại 0x4020
  dest = rbp-0x2020 + (0x19dc - d)        ; công thức: rbp - 0x644 - d
  sao chép 4 byte flag[i*4 .. i*4+3] vào địa chỉ dest
```

Hàm sử dụng một khung stack (frame) khổng lồ lên tới 0x2060 byte, sau đó giải phóng và return. Dựa vào vị trí con trỏ `rbp` của hàm `main`, 13 mảnh cờ 4-byte được rải rác tại các vị trí:
`rbp_main - {0xb64,0xbe4,0xc84,0xcd4,0xd04,0xda4,0xdf4,0xe24,0xec4,0xf14,0xf44,0xf64,0xfe4}`. Điều đáng nói là toàn bộ các mảnh này đều nằm chìm sâu trong vùng stack cũ – nơi mà các menu gọi tiếp theo sẽ sử dụng và ghi đè lên.

**Bước 2 - Điều hướng ngăn xếp (Stack Navigation).**
Độ sâu của ô nhớ bị rò rỉ (`rbp_cancel_plan - 0x204`) hoàn toàn phụ thuộc vào đường đi (path) của người dùng xuyên qua cấu trúc cây menu. Nguyên lý là `rbp_callee = rbp_caller - (frame_size + 16)` và kích thước của mọi frame luôn là bội số của 0x10.

Khảo sát bảng kích thước frame:
```
start_position 0x110  initial_call 0x170  report_outage 0x150
technical_support 0x160  other_inquiries 0x190  cancel_plan 0x430
```

Mỗi lần di chuyển sâu xuống một cấp menu, ô nhớ bị rò rỉ sẽ bị đẩy lùi xuống tương ứng với kích thước frame. Giao thức khai thác sẽ triển khai thuật toán Duyệt theo chiều rộng (BFS) để dò tìm những tổ hợp đường đi cụ thể có khả năng quét trúng 13 vị trí cờ.

Ví dụ:
| Số thứ tự mảnh | Tổ hợp đường đi |
|---|---|
| Mảnh 0 (`sun{`) | Nhấn `1 -> 6 -> 2` (gọi điện -> vấn đề khác -> huỷ), rò rỉ tại `rbp_main - 0x764` |
| Mảnh 12 (`tor}`) | Nhấn `1 -> 6 -> 2`, sau đó kích hoạt đệ quy gọi `cancel_plan` 2 lần liên tiếp (bằng cách chọn lý do huỷ = 4) |

**Bước 3 - Quá trình trích xuất.**
Kịch bản thực thi một lượt gọi `cancel_plan` diễn ra như sau:
- Menu `start_position` sẽ xoá cờ tại `userData+4`, sau đó gọi `login_roleplay` (trình bày 3 câu hỏi liên tiếp).
- Ở Câu hỏi 1: Nhập vào một ký tự chữ cái (không phải số nguyên) -> nội dung biến trên stack không bị thay đổi.
- Ở Câu hỏi 2: Chương trình ngây thơ in ra giá trị biến -> qua đó làm rò rỉ thành công 4 byte cờ.
- Để đào sâu hơn vào stack: Ta chọn đáp án theo thứ tự Câu 1 = `0`, Câu 2 = `1`, Câu 3 = `4` (nhằm kích hoạt gọi đệ quy).

Mở tổng cộng 13 luồng kết nối tương ứng với 13 đường đi đã tính toán, lần lượt trích xuất và ghép mí 13 mảnh 4-byte lại với nhau để khôi phục trọn vẹn flag.

Lưu ý khi chạy: Nhập `42` ngay tại dòng nhắc lệnh "Press enter to start." để vô hiệu hoá chế độ `nanosleep`, giúp cắt giảm đáng kể khoảng thời gian chờ chết của hàm `speak_with_an_operator`. Ngoài ra, mặc dù menu gợi ý "press 3 to speak with an operator", tuỳ chọn chính xác để rẽ sang mục khác trên thực tế lại là phím 2. Để tự động hoá, script sẽ đánh dấu đồng bộ (sync) dựa trên văn bản câu hỏi độc nhất (Ví dụ: `Press 8 for yes.`).
