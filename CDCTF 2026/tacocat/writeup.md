# Tacocat - Misc

**Flag:** `cdctf{I_really_rea11y_1ik3_th3_tac0b311_classic_crunchy_taco3}` · **Điểm:** 500 · **Tác giả:** alex
**Files:** `fat_tacocat.png` (578053 B, sha256 `11fe22d62e5f8a1fee9cb0d9cdc04efd6d66b20ea860aeb58351bf5b69e1f07f`)

## Đề bài

Đề cho một ảnh mèo cam cầm hai cái taco, kèm câu gợi ý "what you could ever want that's extra or say,
in addition to the classic crunchy tacobell taco". Từ khóa là `extra` và `in addition to`: dữ liệu cần tìm
nằm thêm ra ngoài phần ảnh mà trình xem hiển thị.

## Phân tích

`file` báo PNG 1244x700 RGBA non-interlaced, 578053 byte. Duyệt các chunk thì ảnh kết thúc ở `IEND`
offset 459177, còn lại 118876 byte nối đuôi. Ngay trước `IEND` có một chunk private 4 byte tên `deBG`,
payload 16 ký tự hex `0E0EE52B90EDBA88`.

Hai điểm bất thường định hướng luôn: `deBG` là chunk không có trong đặc tả PNG, và 118876 byte phía sau
chiếm 20% dung lượng file. Phần đuôi mở đầu bằng `0A 00 00 00 0D 49 48 44 52`, tức là một byte newline rồi chunk `IHDR` dài 13 byte ( chiều rộng `0x04ED` = 1261) nhưng thiếu 8 byte chữ ký PNG. Thiếu chữ ký nên công cụ
quét magic bytes không thấy gì.

## Hướng đã thử

1. **Ảnh hiển thị:** 56 chunk `IDAT` có CRC hợp lệ và giải mã được ảnh mèo. Lời giải tập trung vào PNG nối sau `IEND`; CRC hợp lệ không loại trừ stego trong pixel.
2. **Bọc archive hoặc file khác định dạng**: quét `PK\x03\x04`, `\x1f\x8b`, `7zXZ`, `Rar!`, `\xff\xd8\xff`
   trong 118916 byte đuôi, chỉ ra 6 vị trí `\x1f\x8b` và tất cả nằm giữa dòng nén `IDAT`, là trùng hợp ngẫu
   nhiên.
3. **`deBG` là khóa hoặc checksum**: hai payload `0E0EE52B90EDBA88` và `2E1D19437C4E9802` XOR ra
   `2013FC68ECA1228A`, không phải ASCII. Không có khối mật nào cần giải. Loại, vai trò của chunk này chưa được xác định và không cần cho bước khôi phục PNG.
4. **Chuỗi "Extra data is no fun!!" cuối file**: 80 byte ASCII thuận, tự nó nói "extra data is no fun",
   trái ngược hẳn với gợi ý của đề. Loại, đây là mồi.

## Lời giải

**Bước 1 - Tách PNG thứ hai.** Duyệt chunk từ đầu, lấy offset ngay sau `IEND` của ảnh đầu, tìm `IHDR`
đầu tiên trong phần đuôi rồi ghép lại 8 byte chữ ký. File dựng lại có 19 chunk, tất cả CRC hợp lệ,
kích thước 1261x1403 depth 8 colortype 6.

```python
appended = data[end:]                      # end = offset ket thuc IEND cua anh dau
i = appended.find(b"\x00\x00\x00\rIHDR")
hidden = b"\x89PNG\r\n\x1a\n" + appended[i:]
```

**Bước 2 - Đọc kênh alpha.** Giải `IDAT`, unfilter 5 kiểu, thấy mọi pixel không trong suốt đều có
RGB = `0,0,0`: ảnh chỉ là mặt nạ. Nét chữ nằm trọn trong byte alpha, nên đổi thành grayscale đảo là đọc được.

```python
idat = b"".join(hidden[o + 8:o + 8 + l] for o, t, l in inner if t == "IDAT")
px = unfilter(zlib.decompress(idat), w, h)
alpha = bytes(px[i * 4 + 3] for i in range(w * h))
write_gray("analysis/alpha_read.png", w, h, bytes(255 - v for v in alpha))
```

Ảnh kết quả: một nét vẽ cái taco ở trên và 4 dòng chữ viết tay bên dưới, vùng nét trải từ y=28 đến y=1056.

**Bước 3 - Phân biệt `l` và `1`.** Bốn dòng ghép lại thành một câu leetspeak, nhưng font tay này làm
chữ `l` và số `1` gần giống nhau, và đo độ rộng nét ở 12% dưới mỗi glyph thì hai ký tự tách rõ:

```text
  dong 0 're[l][l]y'       base=19   -> chu l (mong deu)
  dong 1 're[a][1][1]y'    base=39   -> so 1 (co chan ngang)
  dong 1 're[a][1][1]y'    base=41   -> so 1 (co chan ngang)
  dong 1 '[1]ik3'          base=93   -> so 1 (co chan ngang)
  dong 2 'tac0b3[1][1]'    base=56   -> so 1 (co chan ngang)
  dong 2 'tac0b3[1][1]'    base=60   -> so 1 (co chan ngang)
  dong 2 'c[l]assic'       base=19   -> chu l (mong deu)
  glyph sau '{'            top=71 stem=19 base=71  -> 'I' HOA
```

`l` là que mỏng rộng 19-23px đều từ trên xuống. `1` có móc chéo ở đỉnh và thanh ngang làm chân, nên độ
rộng hàng dưới bằng cả glyph. Glyph sau `{` có serif cả đỉnh lẫn đáy (71px) trong khi thân chỉ 19px, đó
là `I` hoa chứ không phải `l`. Chữ `0` trong `tac0b3` bị gạch chéo, xác nhận là số không.

Bốn dòng, đọc trái phải trên dưới:

```text
cdctf{I_really_re
a11y_1ik3_th3_tac0b3
11_classic_crunchy_
taco3}
```

**Bước 4 - Kiểm chứng.** Ghép dòng không thừa ký tự nào: `re` + `a11y` = `rea11y`, `tac0b3` + `11` =
`tac0b311`. Toàn bộ ký tự nằm trong bảng chữ cái cờ (`A-Za-z0-9_{}`), cặp ngoặc `{}` đóng đúng một lần
ở cuối, và mỗi glyph đều nằm trong hai dải y liên tục không có dòng nào bị bỏ sót.

## Kết quả

```bash
python exploit.py files/fat_tacocat.png
```

```text
== noi dung doc tu alpha_read.png ==
  dong 0: cdctf{I_really_re
  dong 1: a11y_1ik3_th3_tac0b3
  dong 2: 11_classic_crunchy_
  dong 3: taco3}

FLAG: cdctf{I_really_rea11y_1ik3_th3_tac0b311_classic_crunchy_taco3}
```

## Tái hiện

```bash
python exploit.py files/fat_tacocat.png
```

Script dựng `analysis/hidden.png` và `analysis/alpha_read.png`, in bảng đo nét và ghi `flag.txt`.
Phần chữ vẫn phải đọc từ `analysis/alpha_read.png`; script chỉ in sẵn bảng phân loại `l`/`1` để khỏi đoán.
