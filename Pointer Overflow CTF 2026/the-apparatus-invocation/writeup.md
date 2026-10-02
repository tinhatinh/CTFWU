# The Apparatus, Invocation - Misc

**Điểm:** 100 · **Wave:** 1
**Cờ:** `POCTF{3.612.H5VA2OHFE333SO62.EAIOF76YB2L4XMZTFSV4CPOEOX}`

**Artifact:** Thử thách này không cung cấp file để tải về. Thay vào đó, một bàn cờ trạng thái động được sinh ngẫu nhiên cho từng đội và hiển thị trực tiếp trên trang `/challenges/the-apparatus-invocation/`. Trạng thái khởi điểm của bàn cờ thuộc đội 612 được lưu giữ lại trong file `files/board.txt`.

## Đề bài

Hệ thống đưa ra một lưới toạ độ 7x7 chứa tổng cộng 49 ngọn nến. Lối chơi tuân theo quy luật muôn thuở của trò "Lights Out": Mỗi lần nhấn vào một ngọn nến, nó sẽ đảo trạng thái của chính nó (sáng thành tắt, tắt thành sáng), đồng thời kéo theo 4 ngọn nến láng giềng kề sát cạnh nó theo phương dọc và ngang cũng bị đảo trạng thái theo. 
Nhiệm vụ tối thượng để triệu hồi cỗ máy (apparatus) là phải làm tắt ngúm toàn bộ 49 ngọn nến trên bàn. Gợi ý trên trang web khẳng định: thứ tự bấm hoàn toàn vô nghĩa, điều duy nhất quan trọng là tập hợp các lần bấm. Đồng thời, một nút Reset được cung cấp để khôi phục bàn cờ về đúng mốc thời gian khởi thuỷ.

## Phân tích ban đầu

Đảo mắt qua cấu trúc DOM của trang để bóc tách hai yếu tố sống còn: trạng thái tĩnh của bàn cờ và cơ chế kiểm duyệt của máy chủ.

```html
<div id="board" class="board" role="grid" aria-label="Invocation board">
  <button type="button" class="cell" data-r="0" data-c="0" role="gridcell"
          aria-label="Candle at row 1 column 1" aria-pressed="false"></button>
  ...
```

Đào sâu vào đoạn script nội tuyến (inline script) nặng 4.3 KB, ta khai quật được ba yếu tố quyết định số phận ván đấu:

1. Lá cờ **không hề** bị giấu ngu ngốc trong mã HTML. Tác giả khai báo thẳng thừng `const presetFlag = ""` và `const alreadySolved = false`. Chỉ khi nào bạn dọn sạch bàn cờ, trang web mới kích hoạt lệnh gọi `fetch(window.location.pathname + 'complete', {body: JSON.stringify({clicks: presses})})` và cập nhật `$flagTxt.textContent = d.flag`. Điều này đập tan mọi ảo tưởng đi đường tắt: máy chủ sẽ tự tay thẩm định lại chuỗi hành động (presses) của đội chơi và tự mình sinh ra cờ; không có kẽ hở nào từ phía client để khai thác lỗ hổng.
2. Biến `presses` thực chất là một mảng lưu trữ cấu trúc toạ độ `{r, c}` (hàng, cột) được nạp vào (push) liên tục sau mỗi phát nhấn. Hệ quả là, ta chỉ việc kích hoạt chuẩn xác cơ chế lắng nghe sự kiện (handler) của trang là đủ để dắt mũi máy chủ, hoàn toàn miễn nhiễm với gánh nặng phải tự đồng bộ lại trạng thái hiển thị.
3. Việc vẽ lại giao diện (render) được giao phó cho lệnh `classList.toggle('lit', on)` chạy song hành cùng thuộc tính `aria-pressed`. Nhờ đó, bằng cách quét giá trị `aria-pressed` theo chiều dọc luồng DOM (quy tắc row-major), ta có thể ép xuất ra một ma trận 7x7 chân thực đến từng pixel.

Dưới đây là ma trận trạng thái khởi điểm trích xuất được (với `1` đại diện cho ngọn nến đang rực cháy):

```text
0000000
0000110
1100001
1001011
1000110
1111010
0110110
```

## Chuỗi khai thác

**Bước 1 - Trừu tượng hoá toán học (Mathematical Modeling).** 
Bản chất của mọi thao tác nhấn chuột trên lưới "Lights Out" đều được quy về một phép cộng tuyến tính tĩnh trên trường hữu hạn GF(2) (nơi phép cộng và trừ đồng nhất với phép XOR) và có tính chất giao hoán tuyệt đối. Bài toán được thu gọn thành một hệ phương trình ma trận kinh điển: `A * x = b`. 
Trong đó: Hàng `i` đại diện cho ô thứ `i`; Hệ số `A[i][j] = 1` nếu việc nhấn ô `j` có sức sát thương lan tới ô `i` (nghĩa là `j` trùng `i` hoặc `j` kề cạnh `i`); Và vector `b[i]` lưu trữ giá trị trạng thái ban đầu của ô `i` (chỉ ra liệu ô đó có cần bị đảo ngược trạng thái số lẻ lần hay không).

**Bước 2 - Phá giải hệ phương trình.** 
Vận hành thuật toán khử Gauss (Gaussian elimination) trên không gian ma trận 49x50. Phân tích toán học chỉ ra hạng (rank) của ma trận `A` đạt mốc tối đa 49, nghĩa là không hề tồn tại bất kỳ biến tự do (free variable) nào. Lời giải (nghiệm) sinh ra là **duy nhất** — bất kể hệ thống tung ra ván cờ nào cũng đều bị giải mã dễ dàng và không bao giờ xảy ra rủi ro chọn nhầm nghiệm. 
Toạ độ sinh ra dành riêng cho đội 612 gồm 14 phát bắn (đánh chỉ số từ 0):

```text
(2,4) (2,5) (3,0) (3,1) (3,3) (4,0) (4,6) (5,0) (5,3) (5,4) (5,6) (6,0) (6,3) (6,5)
```

**Bước 3 - Diễn tập cục bộ (Local Verification).** 
Trước khi tung đòn trên môi trường live, hệ thống được cho diễn tập mô phỏng lại 14 phát bắn trực tiếp trên ma trận ban đầu thông qua chính lõi hàm `neighbors()` trộm từ script của tác giả. Mọi ô đèn đều ngoan ngoãn tắt lịm về 0, xác nhận đường đạn hoàn mỹ.

**Bước 4 - Bóp cò.** 
Bắn một đợt sóng sự kiện click tự động ngắm chuẩn xác vào 14 toạ độ (button) tương ứng trên giao diện. Trình xử lý sự kiện (handler) của trang web sẽ tự động ghi chép vào mảng `presses` và kính cẩn gọi API lên máy chủ:

```javascript
() => { 
  const P = [[2,4],[2,5],[3,0],[3,1],[3,3],[4,0],[4,6],[5,0],[5,3],[5,4],[5,6],[6,0],[6,3],[6,5]];
  for (const [r,c] of P) {
    document.querySelector(`#board .cell[data-r="${r}"][data-c="${c}"]`).click(); 
  }
}
```

Đồng hồ đếm `press-count` nảy lên con số 14, thẻ `#flag-box` trồi lên khỏi mặt nước và thẻ `#flag-text` rực rỡ hiện ra chuỗi cờ do máy chủ nôn về.

## Flag

```text
POCTF{3.612.H5VA2OHFE333SO62.EAIOF76YB2L4XMZTFSV4CPOEOX}
```

Chuỗi cờ tuân thủ nghiêm ngặt định dạng chuẩn `POCTF{<cid>.<team_id>.<nonce>.<sig26>}`: ứng với cid 3, mã đội 612, theo sau là 16 ký tự nonce ngẫu nhiên và chốt chặn bằng 26 ký tự mã băm (sig) ở hệ base32.

## Phục dựng (Reproduce)

```bash
cd the-apparatus-invocation
python exploit.py
```

Công cụ giải mã (script) sẽ tự động in ra 14 toạ độ chết chóc cần nhắm bắn dựa trên dữ liệu lưới lấy từ `files/board.txt`, đi kèm với đoạn mã JavaScript để người chơi nã trực tiếp vào giao diện (console) của trình duyệt. 
Nếu bạn muốn san bằng bàn cờ của đội khác, chỉ cần vứt bỏ `files/board.txt` và nạp mẫu ma trận rút từ cấu trúc DOM bằng mệnh lệnh ghi trong tài liệu `de.md`.
