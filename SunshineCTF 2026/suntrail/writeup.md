# Suntrail - Misc (Medium)

**Flag:** `sun{qwerty_sucks}`
**Files:** `files/suntrail.klc` (419 byte ASCII, sha256 `abe7590751412fe5607bacd7bfc4a3131e5c108bf2eedbbe78d438e96dc8c6ff`)

## Đề bài

> `im lost, but you can find the way!`

Đề bài chỉ cung cấp duy nhất một file mồ côi, không kèm theo dịch vụ (instance) từ xa nào để kết nối, và cũng không có bất kỳ gợi ý (hint) nào cần phải mở khoá. Bài do tác giả `oatzs` biên soạn.

## Phân tích ban đầu

Đừng để cái đuôi mở rộng đánh lừa, `.klc` không phải là file bản quyền của phần mềm diệt virus Kaspersky như lầm tưởng. Nó thực chất là mã nguồn cấu hình của công cụ Microsoft Keyboard Layout Creator. Mở đầu file là dòng khai báo quen thuộc `KBD kbdusx "US"`, tiếp theo là khối định nghĩa `SHIFTSTATE` (trạng thái phím Shift), và chốt lại bằng từ khoá `ENDKBD`.

Tâm điểm của file nằm ở khối `LAYOUT` với 18 dòng dữ liệu được phân cách bằng tab, mỗi dòng đại diện cho cấu hình của một phím bấm. Ví dụ:

```text
10  Q  0  2192  0073  -1
```

Thứ tự các cột mang ý nghĩa lần lượt là: mã quét phần cứng (scan code), nhãn hiệu phím (key label), trạng thái shift, ký tự mã hoá unicode khi ở trạng thái bình thường (state 0), ký tự unicode khi nhấn cùng shift (state 1), và một mã kết thúc `-1`. Điểm dị thường là hai trạng thái (state) này được thiết kế không đối xứng nhau:

- **State 0 (không nhấn phím bổ trợ):** Chỉ xoay quanh bốn giá trị điều hướng: `U+2192` (mũi tên hướng sang phải, xuất hiện trên 4 phím), `U+2196` (mũi tên chéo lên trên, trên 4 phím), `U+2198` (mũi tên chéo xuống dưới, trên 6 phím), và cuối cùng là `U+25A0` (biểu tượng một ô vuông đen, chỉ xuất hiện duy nhất trên phím `H`).
- **State 1 (nhấn phím bổ trợ):** Cung cấp các chữ cái in thường cùng với ba ký tự đặc biệt là dấu `{`, dấu `}`, và dấu gạch dưới `_`. Đáng chú ý, dấu mở ngoặc `U+007B` nằm trên phím `X`, trong khi dấu đóng ngoặc `U+007D` lại cùng nằm với biểu tượng ô đen trên phím `H`.

Phím `H` chứa cả ô vuông đen và `}`, nên dùng làm điểm kết thúc. Với mỗi phím, state 0 cho hướng đi và state 1 cho ký tự cần lấy.

## Chuỗi khai thác

Parse 18 dòng `LAYOUT` và bỏ `SPACE` (`0x39`) vì hai state của phím này đều là dấu cách. Xếp 17 phím còn lại theo scan code:
- Hàng trên: `Q W E R T`
- Hàng giữa: `A S D F G H`
- Hàng dưới: `Z X C V B N`

**Bước 2 - Theo hướng trên các phím.**

Đọc mũi tên theo cách sắp ba hàng ở trên: sang phải một cột, lên một hàng hoặc xuống một hàng; ô vuông đen là điểm dừng. `analysis/search_geometry.py` ghi lại phép thử các ánh xạ khác trong `analysis/geometry_search_results.txt`, nhưng phép duyệt 8³ ánh xạ không phải điều kiện để đọc đường đi của bài này. Cách ánh xạ dùng để reproduce là:

Đọc mũi tên theo cách sắp ba hàng ở trên: sang phải một cột, lên một hàng hoặc xuống một hàng; ô vuông đen là điểm dừng. `analysis/search_geometry.py` ghi lại phép thử các ánh xạ khác trong `analysis/geometry_search_results.txt`, nhưng phép duyệt 8³ ánh xạ không phải điều kiện để đọc đường đi của bài này. Cách ánh xạ dùng để reproduce là:

Đọc mũi tên theo cách sắp ba hàng ở trên: sang phải một cột, lên một hàng hoặc xuống một hàng; ô vuông đen là điểm dừng. `analysis/search_geometry.py` ghi lại phép thử các ánh xạ khác trong `analysis/geometry_search_results.txt`, nhưng phép duyệt 8³ ánh xạ không phải điều kiện để đọc đường đi của bài này. Cách ánh xạ dùng để reproduce là:

Đọc mũi tên theo cách sắp ba hàng ở trên: sang phải một cột, lên một hàng hoặc xuống một hàng; ô vuông đen là điểm dừng. `analysis/search_geometry.py` ghi lại phép thử các ánh xạ khác trong `analysis/geometry_search_results.txt`, nhưng phép duyệt 8³ ánh xạ không phải điều kiện để đọc đường đi của bài này. Cách ánh xạ dùng để reproduce là:

```text
U+2192 -> Dịch sang phải một cột
U+2196 -> Lên một hàng
U+2198 -> Xuống một hàng
U+25A0 -> Dừng (Stop)
```
Với cách ánh xạ ở bước 2, chỉ `Q` có indegree 0. Đi từ `Q` theo mũi tên tới ô vuông đen đi qua 17/17 phím, mỗi phím một lần. Trong 21 ứng viên đã thử, đường này cho chuỗi đầy đủ.

```text
Q A Z X S W E D C V F R T G B N H
s u n { q w e r t y _ s u c k s }
```

## Flag
```bash
python exploit.py files/suntrail.klc
```

```text
keys with no incoming arrow (candidate starts): ['Q']
  start=Q path=QAZXSWEDCVFRTGBNH -> 'sun{qwerty_sucks}'
start key : Q
path      : QAZXSWEDCVFRTGBNH
keys used : 17/17
flag      : sun{qwerty_sucks}
```

## Tổ chức mã nguồn

`exploit.py` dùng thư viện chuẩn, nhận đường dẫn artifact từ `argv`, tìm đường tới ô đích và in flag. `analysis/search_geometry.py` thử các cách ánh xạ hướng; kết quả lưu ở `analysis/geometry_search_results.txt`.
