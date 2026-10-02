# Suntrail — Misc (Medium)

**Flag:** `sun{qwerty_sucks}`
**Files:** `files/suntrail.klc` (419 byte ASCII, sha256 `abe7590751412fe5607bacd7bfc4a3131e5c108bf2eedbbe78d438e96dc8c6ff`)

## Đề bài

> `im lost, but you can find the way!`

Đề bài chỉ cung cấp duy nhất một file mồ côi, không kèm theo dịch vụ (instance) từ xa nào để kết nối, và cũng không có bất kỳ gợi ý (hint) nào cần phải mở khoá. Bài do tác giả `oatzs` biên soạn.

## Phân tích ban đầu

Đừng để cái đuôi mở rộng đánh lừa, `.klc` không phải là tập tin bản quyền của phần mềm diệt virus Kaspersky như lầm tưởng. Nó thực chất là mã nguồn cấu hình của công cụ Microsoft Keyboard Layout Creator. Mở đầu tệp tin là dòng khai báo quen thuộc `KBD kbdusx "US"`, tiếp theo là khối định nghĩa `SHIFTSTATE` (trạng thái phím Shift), và chốt lại bằng từ khoá `ENDKBD`.

Tâm điểm của file nằm ở khối `LAYOUT` với 18 dòng dữ liệu được phân cách bằng tab, mỗi dòng đại diện cho cấu hình của một phím bấm. Ví dụ:

```text
10  Q  0  2192  0073  -1
```

Thứ tự các cột mang ý nghĩa lần lượt là: mã quét phần cứng (scan code), nhãn hiệu phím (key label), trạng thái shift, ký tự mã hoá unicode khi ở trạng thái bình thường (state 0), ký tự unicode khi nhấn cùng shift (state 1), và một mã kết thúc `-1`. Điểm dị thường là hai trạng thái (state) này được thiết kế không hề đối xứng nhau:

- **State 0 (không nhấn phím bổ trợ):** Chỉ xoay quanh vỏn vẹn bốn giá trị điều hướng: `U+2192` (mũi tên hướng sang phải, xuất hiện trên 4 phím), `U+2196` (mũi tên chéo lên trên, trên 4 phím), `U+2198` (mũi tên chéo xuống dưới, trên 6 phím), và cuối cùng là `U+25A0` (biểu tượng một ô vuông đen huyền bí, chỉ cắm chốt duy nhất trên phím `H`).
- **State 1 (nhấn phím bổ trợ):** Cung cấp các chữ cái in thường cùng với ba ký tự đặc biệt là dấu `{`, dấu `}`, và dấu gạch dưới `_`. Đáng chú ý, dấu mở ngoặc `U+007B` nằm gọn trên phím `X`, trong khi dấu đóng ngoặc `U+007D` lại chung nhà với biểu tượng ô đen trên phím `H`.

Vì ô vuông đen và dấu đóng ngoặc `}` cùng đóng đô trên phím `H`, logic chỉ ra rằng `H` chính là đích đến cuối cùng của mê cung. Cấu trúc này biến mỗi phím bấm thành một điểm nút chứa hai lớp thông tin xếp chồng: lớp thứ nhất là kim chỉ nam (hướng đi tiếp theo), và lớp thứ hai là viên gạch dữ liệu (ký tự thu thập được dọc đường).

## Chuỗi khai thác

**Bước 1 - Lọc và cấu trúc dữ liệu.** 
Việc đầu tiên là phân tích (parse) 18 dòng dữ liệu trong khối `LAYOUT`. Phím `SPACE` (mã quét `0x39`) bị loại bỏ không thương tiếc vì cả hai trạng thái của nó đều chỉ trả về dấu cách vô nghĩa. 17 phím còn lại được xếp ngay ngắn thành ba hàng vật lý theo đúng vị trí của chúng trên bàn phím QWERTY thông qua hệ thống mã quét: 
- Hàng trên cùng (top): `Q W E R T`
- Hàng giữa (home): `A S D F G H`
- Hàng dưới (bottom): `Z X C V B N`

**Bước 2 - Vẽ lại hình học không gian bằng sức mạnh cày cuốc (brute-force).** 
Trên thực tế, các hàng phím cơ học được xếp sole với nhau chứ không thẳng hàng, khiến ta không thể đoán mò được "mũi tên chéo" sẽ chỉ chính xác vào phím nào. Để giải quyết, đoạn script `analysis/search_geometry.py` được tung vào cuộc. Nó quét cạn toàn bộ không gian tổ hợp 8³ (tương đương với các cách gán ba loại mũi tên hướng vào 8 ô liền kề xung quanh một phím). Với mỗi cách gán (bản đồ hình học), script sẽ xuất phát thử từ mọi phím, đi dọc theo các mũi tên chỉ dẫn, và ghi nhận lại những lộ trình sinh ra được một chuỗi ký tự chứa đủ cả dấu `{` lẫn dấu `}`. Tuy nhiên, hệ thống lưới toạ độ này không nhả ra một đáp án duy nhất: tệp `analysis/geometry_search_results.txt` hứng được tới 21 đường đi khác nhau, nhưng phần lớn đều là những chuỗi bị cụt ngủn hoặc rụng mất các ký tự mở đầu quan trọng. Bộ quy tắc ánh xạ toạ độ hợp lý nhất còn trụ lại sau vòng tinh tuyển này là:

```text
U+2192 -> Dịch sang phải một cột
U+2196 -> Trườn lên trên một hàng
U+2198 -> Trượt xuống dưới một hàng
U+25A0 -> Điểm dừng chân tuyệt đối (Stop)
```

**Bước 3 - Truy vết điểm khởi nguồn từ đồ thị.** 
Áp dụng bộ hình học không gian vừa chốt được ở bước 2, ta đếm ngược số lượng phím KHÔNG BỊ bất kỳ mũi tên nào trỏ tới. Kết quả thật hoàn hảo: chỉ còn sót lại duy nhất phím `Q`. Bắt đầu hành trình từ `Q` và đi xuôi theo các mũi tên cho đến khi đụng phải ô vuông đen, lộ trình này càn quét qua chính xác 17/17 phím, không bỏ sót hay giẫm chân lên bất kỳ phím nào hai lần. Hơn thế nữa, đây là con đường duy nhất trong số 21 ứng viên nhả ra được một chuỗi văn bản có nghĩa trọn vẹn.

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

Kịch bản khai thác `exploit.py` được thiết kế tối giản, chỉ vận dụng thư viện chuẩn của Python (stdlib). Nó tiếp nhận đường dẫn của tệp cấu hình (artifact) từ tham số dòng lệnh `argv`, tự động dò tìm đường đi. Khi phát hiện được một lộ trình trọn vẹn không tì vết tiến thẳng tới ô đích, script sẽ thoát với mã trạng thái 0 và rực rỡ in ra chuỗi cờ. Tập tin `analysis/search_geometry.py` là bộ công cụ cày cuốc thô bạo dùng ở khâu dò tìm hình học, mọi kết quả trung gian của nó được lưu trữ vĩnh viễn trong `analysis/geometry_search_results.txt`.
