# The Apparatus, Invocation - log phân tích

Quy ước: mỗi giả thuyết một mục, nhánh sai ghi `result: DEAD - <lý do>`.

## H1 - Cờ có sẵn trong HTML hay không
`const presetFlag = ""` và `alreadySolved = false`; cờ chỉ xuất hiện sau
`fetch(pathname + 'complete', {body: JSON.stringify({clicks: presses})})` và được gán vào
`#flag-text` từ `d.flag`. Quét `document.body.innerHTML` trước khi thắng không có `POCTF{`.
`result: DEAD cho việc đọc tắt - bắt buộc thắng bàn rồi để server trả cờ.`

## H2 - Có cần bấm đúng thứ tự không
Trang ghi rõ thứ tự không quan trọng; handler chỉ push `{r,c}` rồi toggle. Nghiệm GF(2) là tập
hợp ô, nên bấm theo thứ tự nào server cũng mô phỏng ra cùng trạng thái cuối.
`result: OK - bấm theo thứ tự danh sách in ra từ solver.`

## H3 - Bài có vô nghiệm hoặc nhiều nghiệm không
Hạng của ma trận 49x49 là 49, số biến tự do = 0. Với lưới 7x7 luật plus-neighbours, mọi bàn đều
giải được và nghiệm duy nhất. Không cần tìm nghiệm tối thiểu.
`result: OK - 14 phép bấm, duy nhất.`

## H4 - Đọc trạng thái bàn bằng class `lit` thay vì `aria-pressed`
Lần đọc đầu dùng `aria-pressed === 'true' || /lit|on\b/i.test(className)`. Regex `on\b` không
khớp với class nào (các cell chỉ có class `cell`, khi bật mới thêm `lit`), nên kết quả trùng với
đọc thuần `aria-pressed`. Đã đối chiếu lại bằng cách đếm theo `cells[r*7+c]` (thứ tự DOM) và
theo `data-r`/`data-c`: hai cách cho cùng ma trận.
`result: OK sau khi đối chiếu - nhưng nên đọc thẳng aria-pressed, đừng dùng regex.`

## H5 - Bấm bằng cách đổi state nội bộ
Không có handle nào trên `presses` hay `grid` được phơi ra ngoài (toàn bộ nằm trong closure
IIFE), nên không thể ghi đè biến. Chỉ còn cách kích `click()` thật.
`result: DEAD cho đường tắt - click thật là đường duy nhất, và cũng đủ.`

## Ghi chú
- Endpoint hoàn thành là `POST /challenges/the-apparatus-invocation/complete`, body
  `{"clicks":[{"r":..,"c":..},..]}`. Trả về JSON có khoá `flag`.
- Cờ nhận được khớp khuôn `POCTF{<cid>.<team_id>.<nonce>.<sig26>}`, cid của bài này là 3.
- Nếu lỡ bấm sai, nút Reset đưa bàn về đúng trạng thái đầu và xoá `presses`, không tốn lượt.
