# You Cut Me Off - Forensics (Medium)

**Flag:** `sun{totallyoriginalchallengeidea}`
**Files:** `HEREYOUGO.PNG` (38759 B, ảnh Discord độ phân giải 492x382 RGBA)

## Đề bài

Phần mô tả của bài tập: "Here's a flag! It's uhhh ...... ............ ......................uhhhhhhhhhh..................... hmm....." kèm theo một file hình ảnh. Bức ảnh chụp lại một đoạn chat trên Discord, trong đó một nhân vật mang tên Ardian dõng dạc tuyên bố "today i will make a ctf challenge", thả vài bức ảnh chế meme, rồi kết thúc bằng câu nói "ill type it out just give me a second". Ngay sau câu nói này, bức ảnh bị cắt ngang một cách phũ phàng. Tiêu đề của thử thách, vô số dấu chấm lửng trong mô tả, và đường viền tin nhắn bị cắt gọt sắc lẹm ở mép dưới bức ảnh đều cùng hội tụ về một gợi ý rõ ràng: phần mấu chốt cuối cùng đã bị cố tình cắt xén.

## Phân tích

Điểm cần kiểm tra hiện rõ ngay từ đầu chính là sự bất hợp lý về kích thước nén. Đối với một tấm ảnh chụp màn hình chứa ít màu sắc và độ phân giải khiêm tốn 492x382 RGBA, việc chunk dữ liệu `IDAT` phình to tới 38652 byte là một điểm cần kiểm tra thêm.

## Lời giải

**Bước 1 - Đối chiếu kích thước thực tế so với kích thước khai báo.**
Đây là điểm sáng tạo giúp bài toán này khác biệt hoàn toàn so với các thử thách giấu tin trong ảnh (steganography) thông thường: người chơi không cần phải săm soi sửa đổi từng pixel, mà chỉ việc đọc header và đối chiếu thông số sau khi giải nén.

```python
import zlib
raw = zlib.decompress(IDAT)
print(len(raw), 382 * (1 + 492 * 4))     # Kết quả: 823042 so với 752158
```
Dữ liệu giải nén dài 823042 byte. Mỗi scanline RGBA dài `1969 = 1 + 492*4` byte, nên có `823042 / 1969 = 418` hàng, đều dùng filter type 0. `IHDR` chỉ khai báo 382 hàng; cần sửa chiều cao thành 418 và cập nhật CRC để hiển thị thêm 36 hàng.

**Bước 2 - Phục dựng bức ảnh với chiều cao nguyên bản.**
Bằng cách loại bỏ 1 byte màng lọc ở đầu mỗi dòng, ghép nối dữ liệu thô lại và dựng hình với chiều cao chính xác là 418 pixel, sự thật sẽ được phơi bày.

```python
from PIL import Image
rows = [raw[i*1969 + 1:(i+1)*1969] for i in range(418)]
Image.frombytes("RGBA", (492, 418), b"".join(rows)).save("analysis/full.png")
```

Ở phần ảnh bị giấu vừa được phục hồi ngay bên dưới dòng chữ "ill type it out just give me a second", ô soạn thảo tin nhắn quen thuộc của Discord hiện ra, mang theo một dòng chữ bí mật.

**Bước 3 - Đọc cờ.**
Phóng to tấm ảnh lên 4x và 6x (các file `analysis/hidden4x.png`, `analysis/mid.png`), sau đó soi kỹ càng 10x vào các cặp ký tự dễ gây nhầm lẫn để có được nội dung chính xác nhất (`analysis/glyphs.png`).

Chiều cao 418 khớp độ dài dữ liệu giải nén và các filter byte. Sau khi khôi phục ảnh, đọc trực tiếp dòng chữ trong ô chat. Đối chiếu nét chữ ở các vị trí dễ nhầm, như `i` và `l`, trên ảnh đầy đủ.

## Kết quả
```bash
python solve.py
```

```text
IHDR: 492x382  stride=1969  IDAT giải nén=823042 byte -> thực tế 418 dòng
số dòng bị ẩn: 36
đã ghi analysis/full.png và analysis/hidden.png
```

```text
sun{totallyoriginalchallengeidea}
```
