# Đề bài - severed-symmetry

## Nguyên văn đề

```text
Severed Symmetry
357
Expert
As the Kuiper Belt Relay reboots, your terminal intercepts an encrypted archive belonging to the Ætheric Order. Its contents survived The Severance, but the private key did not; only the encryption program, public equations, and ciphertext remain. The Order is already moving to reclaim it; recover the access key hidden inside before their secrets disappear into the Nexus again.

Flag Format: CSSCTF{...}

附件引用:
- 文件: C:\Users\Administrator\Downloads\out.txt
- 文件: C:\Users\Administrator\Downloads\source.py
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/source.py` (copy từ: `/c/Users/Administrator/Downloads/source.py`) |
| Kích thước | 10103 byte |
| SHA-256 | `b1945c904bc5d729ba4e6be6439259b331ab5dc7cbd31b876600fe44fcc8b90a` |
| Loại file | Python script, ASCII text executable |
| Artifact | `files/out.txt` (copy từ: `/c/Users/Administrator/Downloads/out.txt`) |
| Kích thước | 31778814 byte |
| SHA-256 | `5bd759a0593a39277157f8025784296d5c4684c75a4bc3823bceef2c5d76c0bf` |
| Loại file | ASCII text, một dòng JSON: `public_key` (34 polynomial) + `ciphertext` (3 block) |
| Tham số | `p=17, n=32, m=34, t=16, s=4`; mỗi polynomial có tới 55470 số hạng, bậc tối đa 4 |
| Block cuối | 3 block x 32 chữ số base-17 = 96 chữ số = 48 byte, nên độ dài cờ từ 29 đến 43 ký tự |
| Nhiệm vụ | Tìm preimage của cả 3 block rồi ghép lại thành frame có header độ dài |
| Định dạng cờ | `CSSCTF{...}` |

## Hướng giải (tóm tắt)

Bảng mã là một biến thể VLG: `F = A1 . (w, U(w, v)) . A2` với `w_a = u_a - q_a(v)` và `U` dạng vinegar-oil chỉ có 4 biến vinegar nằm trong `v`. Không cần khoá bí mật: không gian các tổ hợp tuyến tính bậc ≤2 của 34 polynomial chính là `span{w_a}`, và từ đó suy ra toàn bộ khung toạ độ `(u, v)` bằng đại số tuyến tính thuần tuý. Thế `u_a = t_a + q_a(v)` làm bậc hệ tụt từ 4 xuống 2, các `t_a` lấy được vì mỗi phần tử của `W` là một polynomial hiện theo `x` nên giá trị của nó là cùng tổ hợp trên ciphertext. Phần còn lại là bài toán tìm không gian oil (12 chiều) qua không gian ảnh vinegar 4 chiều, rồi duyệt 17^4 giá trị vinegar như bên giải mã hợp lệ.

## Chạy lại lời giải

```bash
python exploit.py files/out.txt
```

Kết quả: `CSSCTF{P35T0_5CH3M3_4TT4CK2026}` (đã lưu trong `flag.txt`).
