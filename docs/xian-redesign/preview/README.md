# Preview giao diện "Mực & Kim"

Mock tĩnh của giai đoạn 2, **chưa nối vào Jekyll**. Dùng để duyệt hướng mỹ thuật trước khi
động vào `site/`.

## Xem

Mở trực tiếp bằng trình duyệt:

```
home.html      trang chủ
archive.html   thư viện writeups
post.html      một bài dài (OT#007)
```

Hoặc chạy server tĩnh nếu muốn kiểm trên điện thoại cùng mạng LAN:

```bash
cd docs/xian-redesign/preview
python3 -m http.server 8799
```

## Ảnh hero

`assets/hero-desktop.jpg` và `assets/hero-mobile.jpg` **không nằm trong git** — đây là tranh
promotional lấy từ trang tham chiếu, có bản quyền của nhà phát hành. Chạy lại khi cần:

```bash
bash fetch-assets.sh
```

Script tải tranh gốc rồi cắt hai kích thước (1600×900 và 1080×1350), đúng ngân sách
600 KB / 300 KB.

Trước khi đưa lên production phải thay bằng tranh bạn có quyền dùng, hoặc dựng nền SVG.
Bố cục đã tính theo tỉ lệ 16:9 và 4:5 nên đổi ảnh không phải sửa CSS.

## Ảnh chụp

`shots/` chứa ảnh chụp desktop 1440px và mobile 390px của ba trang. Cũng không nằm trong git
vì chứa tranh có bản quyền.
