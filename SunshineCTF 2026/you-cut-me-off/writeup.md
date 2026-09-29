# You Cut Me Off — Forensics (Medium)

**Flag:** `sun{totallyoriginalchallengeidea}` · **Files:** `HEREYOUGO.PNG`, 38759 B, ảnh Discord 492x382 RGBA

## Đề bài

Mô tả bài chỉ có: "Here's a flag! It's uhhh ...... ............ ......................uhhhhhhhhhh..................... hmm....." kèm một file ảnh. Ảnh là ảnh chụp đoạn chat Discord: người tên Ardian tuyên bố "today i will make a ctf challenge", gửi vài cái meme, rồi "ill type it out just give me a second" - và hết ảnh đúng ở chỗ đó. Tên bài, số dấu chấm trong mô tả và viền tin nhắn cụt ở mép dưới đều chỉ vào một thứ: phần cuối bị cắt.

## Phân tích ban đầu

Đi theo đường stego trước, vì mô tả gợi "cờ nằm trong ảnh". Cả ba hướng đều chết:

1. Dữ liệu nối thêm / chunk ẩn. Duyệt hết chunk: `IHDR sRGB gAMA pHYs IDAT IEND`, sau `IEND` còn đúng 0 byte, không có `tEXt`/`iTXt`/`zTXt`.
2. LSB và kênh alpha. Alpha bằng 255 toàn ảnh. LSB kênh xanh dương có tới 96% giá trị lẻ, trông rất đáng ngờ, nhưng màu nền của ảnh Discord là `(50,23,23)` - chẵn/lẻ/lẻ - nên độ lệch đó là của bảng màu, không phải của dữ liệu nhúng.
3. Chữ màu gần nền (contrast stego). Đếm khoảng cách tới màu nền rồi khuếch đại 24 lần: không có lớp chữ nào hiện ra.

Điểm đáng chú ý duy nhất còn lại là kích thước nén không tương xứng: một ảnh 492x382 RGBA mà IDAT tới 38652 byte thì hơi lớn cho một screenshot ít màu.

## Chuỗi khai thác

**Bước 1 - So kích thước giải nén với kích thước khai báo.** Đây là chỗ bài này khác mọi bài stego ảnh khác: không cần đụng vào pixel, chỉ cần đọc header và giải nén.

```python
raw = zlib.decompress(IDAT)
print(len(raw), 382 * (1 + 492 * 4))     # 823042  752158
```

`823042 / 1969 = 418` chẵn, với `1969 = 1 + 492*4` là stride của một dòng RGBA. Toàn bộ 418 dòng đều dùng filter type 0. Nghĩa là buffer scanline thật dài 418 dòng, còn `IHDR` chỉ khai báo 382: thiếu 36 dòng, đúng bằng một tin nhắn.

**Bước 2 - Dựng lại ảnh theo chiều cao thật.** Bỏ 1 byte filter ở đầu mỗi dòng, ghép lại và vẽ bằng chiều cao 418.

```python
rows = [raw[i*1969 + 1:(i+1)*1969] for i in range(418)]
Image.frombytes("RGBA", (492, 418), b"".join(rows)).save("analysis/full.png")
```

Phần ảnh hiện ra ngay dưới dòng "ill type it out just give me a second" là ô soạn tin nhắn của Discord, chứa đúng một dòng chữ.

**Bước 3 - Đọc từng ký tự.** Phóng 4x và 6x (`analysis/hidden4x.png`, `analysis/mid.png`) rồi soi 10x riêng cặp ký tự dễ nhầm (`analysis/glyphs.png`).

**Bước 4 - Kiểm chứng tính đúng.** Đây không phải suy đoán: `823042` chia chẵn cho `1969` và mọi dòng đều có byte filter hợp lệ (0), nên 418 là số dòng duy nhất khớp với dữ liệu; nếu header đúng thì phần thừa phải là 0 byte. Ký tự giữa "challenge" và "dea" có dấu chấm phía trên nên là `i`, không phải `l`; chuỗi đóng ngoặc `}` ngay sau đó.

## Flag
```bash
python solve.py
```

```
IHDR: 492x382  stride=1969  IDAT giải nén=823042 byte -> thực tế 418 dòng
số dòng bị ẩn: 36
đã ghi analysis/full.png và analysis/hidden.png
```

```
sun{totallyoriginalchallengeidea}
```
