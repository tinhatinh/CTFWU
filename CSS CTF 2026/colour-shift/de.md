# Đề bài - colour-shift

## Nguyên văn đề

```text
Colour Shift
124
Beginner
In 1666 Issac Newton split light into their compositve wavelengths. Can you?

Flag format: CSSCTF{...}
```

File đính kèm: `colorshiftctf.bmp`.

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/colorshiftctf.bmp` (copy từ: `C:\Users\Administrator\Downloads\colorshiftctf.bmp`) |
| Kích thước | 1083738 byte |
| SHA-256 | `689f33baf1acdef5c58b61a493977a44384694ef87f07a1f0606f1f34035ef92` |
| Loại file | PC bitmap, Windows 98/2000 and newer format, 599 x 602 x 24, cbSize 1083738, bits offset 138 |
| Cấu trúc | BITMAPV5HEADER (124 byte), BI_RGB, 24 bpp, `biSizeImage` = 1083600 = 1800 x 602, `bfOffBits + biSizeImage` khớp chính xác 1083738 |
| Nội dung ảnh | Bìa album The Dark Side of the Moon, nền tối, mean kênh R/G/B = 15.4 / 32.1 / 38.1 |
| Nhiệm vụ | Tìm dòng chữ bị giấu trong ảnh |
| Định dạng cờ | `CSSCTF{...}` |

## Hướng giải (tóm tắt)

Chữ được vẽ đè lên ảnh nhưng chỉ làm thay đổi kênh đỏ, biên độ nhỏ hơn hẳn nhiễu hạt của nền nên mắt thường và các phép thử thông dụng (nối byte, LSB, bảng màu) đều không thấy. Tách ảnh thành ba thành phần màu rồi trừ nền cục bộ bằng median filter 41 px, phần chữ còn lại ở kênh R và rõ nhất ở hiệu R - B; kênh G và B phẳng lì, chứng tỏ lớp đè chỉ động vào đỏ.

## Chạy lại lời giải

```bash
python exploit.py files/colorshiftctf.bmp -o analysis
```

Kết quả: `CSSCTF{SHINE ON}` (đã lưu trong `flag.txt`), kèm `analysis/flag_line.png` phóng to dòng chữ vừa khôi phục.
