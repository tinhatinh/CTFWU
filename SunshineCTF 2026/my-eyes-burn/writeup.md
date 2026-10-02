# My Eyes Burn - Misc (Medium)

**Flag:** `sun{praisethesun}`
**Files:** `boardwriter.klc` (3562 B, UTF-16LE, CRLF)

## Đề bài

> "anon hasn't been outside in years, so he put the sun in his keyboard. find the flag he types to bring it out."

Đề bài cung cấp cho chúng ta một file `.klc` duy nhất. Đây là định dạng mã nguồn cấu hình bàn phím trên hệ điều hành Windows, thường được tạo ra bởi phần mềm Microsoft Keyboard Layout Creator (MSKLC). Mục tiêu của bài toán là tìm ra chuỗi phím bấm chính xác mà "anon" đã cấu hình để gõ ra biểu tượng mặt trời (chính là chuỗi cờ mà ta cần tìm).

## Phân tích định dạng KLC

Khi đọc file `.klc`, có hai quy tắc quan trọng về cơ chế hoạt động của bàn phím mà ta cần nắm bắt:

1. Trong phần định nghĩa phím (`KEYS`), bất kỳ phím nào được đánh dấu bằng hậu tố `@` đều đóng vai trò là một "dead key" (phím chết/phím kết hợp - loại phím không in ra ký tự ngay lập tức mà chờ phím tiếp theo để tạo thành một ký tự phức tạp). Khi phân tích file này, ta thấy chỉ tồn tại duy nhất một phím dead key: `29 OEM_3 0 0060@ 007e -1` (tương ứng với phím backtick `` ` ``).
2. Khi chương trình xử lý khối `DEADKEY <state>`, các dòng dữ liệu bên dưới có dạng `<src> <res>@` mang ý nghĩa: nếu người dùng gõ phím `<src>`, hệ thống sẽ tiếp tục chuyển sang trạng thái dead key `<res>` mới. Trong trường hợp `<res>` không đi kèm ký hiệu `@`, hệ thống sẽ hiểu rằng chuỗi kết hợp đã hoàn tất, in ký tự đó ra màn hình và thoát khỏi trạng thái dead key.

Cụ thể, file cấu hình này định nghĩa tổng cộng 17 trạng thái `DEADKEY` khác nhau. Quá trình theo vết bắt đầu từ trạng thái gốc là `0060`. Bằng cách phân tích toàn bộ các nhánh, ta phát hiện chỉ có duy nhất một kết quả đầu ra không phải là dead key:

```text
DEADKEY 02b0
007d    2600          <- Không có ký hiệu @  =>  Trả về mã U+2600 (BLACK SUN WITH RAYS = ☀)
```

Như vậy, toàn bộ cấu trúc bàn phím phức tạp này được thiết kế chỉ để in ra một biểu tượng mặt trời (☀) duy nhất thông qua một chuỗi phím kết hợp dài.

## Trích xuất cờ

Thay vì phải bruteforce, ta hoàn toàn có thể tìm ra chuỗi gõ phím bằng cách lần ngược (trace back) từ điểm đích `02b0` quay về điểm bắt đầu `0060`:

```text
0060 + s -> 02D0    02EF + p -> 02BA    02BD + e -> 02CD    02EE + s -> 02D4
02D0 + u -> 02ED    02BA + r -> 02C9    02CD + t -> 02E4    02D4 + u -> 02E1
02ED + n -> 02B4    02C9 + a -> 02D3    02E4 + h -> 02D8    02E1 + n -> 02B0
02B4 + { -> 02EF    02D3 + i -> 02E9    02D8 + e -> 02EE    02B0 + } -> U+2600 ☀
02E9 + s -> 02BD
```

Khi ghép nối các ký tự theo đúng trình tự từ đầu đến cuối, ta có được thứ tự gõ phím như sau: `` ` `` `s` `u` `n` `{` `p` `r` `a` `i` `s` `e` `t` `h` `e` `s` `u` `n` `}`.

Do phím backtick (`` ` ``) chỉ đóng vai trò kích hoạt trạng thái dead key ban đầu mà không in ra màn hình, phần văn bản thực sự hiện lên chính là chuỗi cờ của thử thách:

```text
sun{praisethesun}
```

## Flag
```bash
$ python solve_klc.py files/boardwriter.klc
[*] keystrokes: '`sun{praisethesun}'
[*] emits: ☀  (U+2600 BLACK SUN WITH RAYS)
[+] FLAG: sun{praisethesun}
```
