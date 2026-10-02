# The Apparatus, Invocation - Misc

**Điểm:** 100 · **Wave:** 1
**Cờ:** `POCTF{3.612.H5VA2OHFE333SO62.EAIOF76YB2L4XMZTFSV4CPOEOX}`

**Artifact:** Thử thách này không cung cấp file tải về. Hệ thống tạo một bàn cờ trạng thái ngẫu nhiên cho từng đội, hiển thị trực tiếp trên trang `/challenges/the-apparatus-invocation/`. Trạng thái khởi tạo của bàn cờ thuộc đội 612 được lưu trữ trong file `files/board.txt`.

## Đề bài

Hệ thống hiển thị một lưới toạ độ 7x7 gồm 49 bóng đèn (ngọn nến). Cách chơi tương tự trò "Lights Out": Nhấn vào một bóng đèn sẽ thay đổi trạng thái của nó (sáng thành tắt, tắt thành sáng), và đồng thời thay đổi trạng thái của 4 bóng đèn liền kề (trên, dưới, trái, phải). 
Mục tiêu là phải tắt hoàn toàn 49 bóng đèn trên bàn cờ. Gợi ý cho biết thứ tự thực hiện không quan trọng, chỉ tập hợp các ô được chọn mới quyết định kết quả. Hệ thống cũng cung cấp nút Reset để khôi phục trạng thái ban đầu.

## Phân tích ban đầu

Kiểm tra cấu trúc DOM của trang để xác định trạng thái bàn cờ và cơ chế giao tiếp với máy chủ.

```html
<div id="board" class="board" role="grid" aria-label="Invocation board">
  <button type="button" class="cell" data-r="0" data-c="0" role="gridcell"
          aria-label="Candle at row 1 column 1" aria-pressed="false"></button>
  ...
```

Phân tích đoạn mã script nội tuyến (inline script) dung lượng 4.3 KB tiết lộ các yếu tố quan trọng:

1. Mã cờ không được nhúng sẵn trong HTML. Script khởi tạo `const presetFlag = ""` và `const alreadySolved = false`. Khi trạng thái bàn cờ đạt yêu cầu, trang web gọi API `fetch(window.location.pathname + 'complete', {body: JSON.stringify({clicks: presses})})` và nhận mã cờ. Do đó, người chơi bắt buộc phải tìm ra chuỗi hành động (presses) chính xác và gửi về máy chủ để xác thực.
2. Biến `presses` là mảng lưu trữ toạ độ `{r, c}` (hàng, cột) của mỗi lần nhấn. Việc kích hoạt sự kiện click trên giao diện sẽ tự động cập nhật mảng này và duy trì đồng bộ trạng thái.
3. Việc cập nhật giao diện được thực hiện thông qua lệnh `classList.toggle('lit', on)` kết hợp thuộc tính `aria-pressed`. Trạng thái toàn bộ bàn cờ có thể được trích xuất bằng cách quét giá trị `aria-pressed` theo từng hàng (row-major).

Ma trận trạng thái khởi điểm trích xuất được (giá trị `1` tương ứng với bóng đèn đang sáng):

```text
0000000
0000110
1100001
1001011
1000110
1111010
0110110
```

## Quá trình phân tích

**Bước 1 - Mô hình hoá toán học (Mathematical Modeling).** 
Trò chơi "Lights Out" có thể được biểu diễn thông qua đại số tuyến tính trên trường GF(2) (nơi phép cộng và trừ tương đương với phép XOR). Bài toán đưa về hệ phương trình ma trận: `A * x = b`. 
Trong đó: Hàng `i` đại diện cho ô thứ `i`; Hệ số `A[i][j] = 1` nếu việc nhấn ô `j` làm thay đổi trạng thái của ô `i` (nghĩa là `j` trùng với `i` hoặc `j` kề cạnh `i`); Vector `b[i]` biểu diễn trạng thái ban đầu của ô `i` (xác định ô đó cần thay đổi trạng thái số lẻ lần hay không).

**Bước 2 - Giải hệ phương trình.** 
Sử dụng thuật toán khử Gauss (Gaussian elimination) trên ma trận kích thước 49x50. Phân tích cho thấy hạng (rank) của ma trận `A` là 49, nghĩa là không có biến tự do (free variable). Do đó, hệ phương trình luôn có một nghiệm duy nhất, đảm bảo tính xác định cho mọi cấu hình trạng thái ban đầu. 
Nghiệm thu được cho ma trận của đội 612 gồm 14 toạ độ (chỉ số tính từ 0):

```text
(2,4) (2,5) (3,0) (3,1) (3,3) (4,0) (4,6) (5,0) (5,3) (5,4) (5,6) (6,0) (6,3) (6,5)
```

**Bước 3 - Kiểm tra nghiệm (Local Verification).** 
Trước khi gửi kết quả, hệ thống tiến hành kiểm tra trên mô phỏng cục bộ bằng cách mô phỏng 14 thao tác click trên ma trận ban đầu (áp dụng hàm `neighbors()` lấy từ mã nguồn). Mọi ô đèn đều chuyển sang trạng thái 0, xác nhận nghiệm hoàn toàn chính xác.

**Bước 4 - Thực thi.** 
Sử dụng đoạn mã tự động để gọi sự kiện click trên 14 toạ độ tương ứng trên giao diện trang web. Trình xử lý sự kiện sẽ cập nhật mảng `presses` và tự động gọi API:

```javascript
() => { 
  const P = [[2,4],[2,5],[3,0],[3,1],[3,3],[4,0],[4,6],[5,0],[5,3],[5,4],[5,6],[6,0],[6,3],[6,5]];
  for (const [r,c] of P) {
    document.querySelector(`#board .cell[data-r="${r}"][data-c="${c}"]`).click(); 
  }
}
```

Bộ đếm thao tác đạt 14, thẻ `#flag-box` xuất hiện và `#flag-text` hiển thị mã cờ do máy chủ trả về.

## Flag

```text
POCTF{3.612.H5VA2OHFE333SO62.EAIOF76YB2L4XMZTFSV4CPOEOX}
```

Chuỗi cờ tuân thủ định dạng chuẩn `POCTF{<cid>.<team_id>.<nonce>.<sig26>}`: ứng với cid 3, mã đội 612, theo sau là 16 ký tự nonce ngẫu nhiên và 26 ký tự mã băm (sig) ở hệ base32.

## Reproduce

```bash
cd the-apparatus-invocation
python exploit.py
```

Công cụ giải mã (script) tự động phân tích dữ liệu lưới từ `files/board.txt` và trả về danh sách 14 toạ độ cần thao tác, kèm theo đoạn mã JavaScript để chạy trực tiếp trong console của trình duyệt. 
Để giải mã bảng của đội khác, thay thế nội dung `files/board.txt` bằng mẫu ma trận lấy từ cấu trúc DOM (hướng dẫn chi tiết trong tệp `de.md`).
