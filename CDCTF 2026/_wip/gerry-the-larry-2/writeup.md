# Gerry the Larry (2/2) - Web Exploitation (500 điểm) — ĐANG MỞ

**Cờ:** chưa có · **Điểm:** 500 · **Tác giả:** reep236, adlee7 (CDCTF)
**Artifact:** web app trên instance, không có file đề

## Đề bài

Giúp Larry (phe Domestic Loafs) thắng cử với "hệ thống khu vực mới". Định dạng cờ `cdctf{Fl4gGo3sH3re!}`.

## Những gì đã đo được

### 1. Client là PureScript→JS, backend là FastAPI

`index.html` chỉ nạp `/assets/index.501b4b7d.js` (152 KB). Trong bundle có chuỗi lỗi
`Failed pattern match at Control.Applicative`/`Data.Map.Internal` → PureScript compiled.
Phản hồi 422 của `/vote` có dạng `{"detail":[{"type":"bool_type","loc":["body","votes",0],...}]}` → pydantic.
`/openapi.json`, `/docs`, `/redoc` đều 404 (nginx), nên không truy cập được schema qua các đường dẫn này.

### 2. "Chữ ký" không có khoá bí mật — mint được UVIN tuỳ ý

```javascript
ES = function(n){ return tS(((n.number + (2*n.lon_block)) + (4*n.lat_block)) + (8*n.year)) }
SS = function(n){ return lu(4)(n.year) + lu(2)(n.lat_block) + lu(2)(n.lon_block) + lu(4)(n.number) }
```

tức `signature = 8·year + 4·lat_block + 2·lon_block + number` và
`uvin = "%04d%02d%02d%04d"`. Ô nhập trên UI đòi dạng có gạch `YYYY-LL-LL-NNNN`
(`_S` split `'-'` và bắt buộc đúng 4 nhóm), nhưng `/vote` nhận chuỗi 12 chữ số.

Đã xác nhận phía server: gửi `signature:"1"` → `flag = "Error: Invalid UVIN!"`, còn
`signature:"16215"` (= 8·2026+4·1+2·1+1) thì **không** bị báo lỗi UVIN.

### 3. Lá phiếu là 121 boolean, `result` chỉ là echo

```text
POST /vote {"uvin":"202601010001","signature":"16215","votes":[true, ... ]}
-> 200 {"result":[<đúng danh sách phiếu đã gửi>], "flag":"<kết luận hoặc lỗi>"}
```

pydantic báo `"Input should be a valid boolean"` khi `votes[i]` là object ⇒ **không có**
`{address,payload}` như cách `CS(n)` dựng state trong client; danh sách phẳng, thứ tự theo
`Ys(5)` = `lat` ngoài `1..11`, `lon` trong `1..11` ⇒ chỉ số `i = (lat-1)*11 + (lon-1)`.
Độ dài không bị chặn: 100, 121, 122 và rỗng đều được chấp nhận (`result` trả về đúng độ dài đó).

Lưới 11×11 khớp client: `kS(5)` duyệt `1..(2·5+1)`; các ô có `lat` lẻ **và** `lon` lẻ là ô **nhãn**
(tên precinct, bảng `OS` 6×6 = 36 tên), 85 ô còn lại là checkbox.

### 4. Chưa xác định phạm vi khóa "already voted"

10 UVIN khác nhau (`number` 1..10, cùng `lat_block=1, lon_block=1`) đều trả `Error: You have already voted!`. Chưa xác định khóa theo block, IP, phiên hay trạng thái đã lưu của từng UVIN. Cần thêm phép thử để phân biệt.

## Hướng chưa kiểm chứng

1. Thử UVIN ở các block khác nhau để thu thập phản hồi. Cần kiểm soát IP, phiên và trạng thái trước đó; hình dạng lưới phản hồi chỉ là gợi ý, chưa chứng minh phạm vi khóa.
2. Với mỗi phiếu hợp lệ còn lại, `flag` sẽ lộ điều kiện thắng (dạng `Error: ...` khác, hoặc cờ).
   Khi biết cách server tính ghế, dùng solver ở `analysis/solver.py` để chọn tập block:
   mô hình = lưới precinct 2 phiếu/đảng, chia `K` khu liền kề bằng nhau, tối đa số khu ta thắng.
3. Solver đã kiểm chứng ở local trên 4 bộ dữ liệu thử nghiệm:

| bản kiểm chứng | ta giữ | trần lý thuyết | solver đạt |
|---|---|---|---|
| 6×6, K=4 | 18/36 | 3 | **3** ✓ |
| 10×10 hai khối, K=10 | 40/100 | 6 | **6** ✓ |
| 10×10 phân tán 50/50, K=10 | 40/100 | 6 | **6** ✓ |
| 10×10 ta chỉ 10% | 10/100 | – | **0** (đối chứng âm) ✓ |

```bash
python analysis/solver.py        # chạy 4 bản điều khiển ở trên
```

## Việc còn lại

- Chưa biết server tính "thắng" từ gì: chỉ nhìn `votes` của một phiếu, hay tổng hợp nhiều phiếu của nhiều
  UVIN, hay so với số cử tri dựng sẵn (1067 cử tri của bài 1/2 là ứng viên số 1 cho con số đó).
- Chưa có message nào khác ngoài `Invalid UVIN!` / `You have already voted!` ⇒ cần kết quả của phép quét
  block để mở khoá nhánh tiếp theo.
- Khi đã có luật: đưa ra đúng một lệnh `POST /vote` (hoặc một chuỗi rất ngắn) để người chơi tự dán.
