# Crypto Cat Caticus Catanius (3/5) - Crypto (498 điểm)

**Flag:** `cdctf{any monoalphabetic sub'stitution cipher can be cracked through sta'tistical analysis given su'fficient cipher text for the numbers to be figured out mathematically and such}` · **Files:** `files/ciphertext.txt`, 180 byte, sha256 `742a5555bc13ed0d6336b29673baba2dca97ebfc77ad905989ca4015083233ed`
**Event:** CDCTF 2026 (Crimson Defense CTF) · **Tác giả:** alex

## Đề bài

Phần 3/5 của chuỗi Crypto Cat, chỉ gồm 179 ký tự bản mã in trong thẻ, không file tải về, không
instance. Bản mã giữ nguyên dấu cách, cặp ngoặc `{}` và ba dấu nháy đơn, nên phần word hình (độ dài
token, vị trí ngoặc) đọc được trực tiếp từ đề.

## Phân tích ban đầu

- 151 chữ cái, 22 chữ phân biệt, Index of Coincidence = 0.0580. Văn bản tiếng Anh một bảng chữ cái
  đo khoảng 0.066, Vigenère nhiều bảng rơi về 0.045; 0.0580 gợi ý thử một bảng chữ cái, nhưng mẫu ngắn không đủ để kết luận riêng từ IC.
- Hai token lặp lại nguyên vẹn: `wezmrf` (6 chữ) xuất hiện ở token 4 và token 13, `kr` (2 chữ) ở token
  6 và token 19. Khoảng cách giữa hai lần lặp là 59 và 75 chữ cái, gcd = 1.
- Nếu các từ lặp tương ứng cùng plaintext và cùng pha khóa, chu kỳ Vigenère phải chia 59 và 75, tức L = 1. Đây là giả định để ưu tiên monoalphabetic substitution, không phải chứng minh loại trừ mọi cipher đa bảng.
- Ba dấu nháy đơn (`nvk'n...`, `npq'p...`, `nv'll...`) ban đầu gợi ý các dạng rút gọn. Sau khi giải mã, chúng nằm trong `sub'stitution`, `sta'tistical`, `su'fficient`; cần giữ nguyên dấu nháy khi chép plaintext.

## Các hướng đã loại

Toàn bộ số liệu ở `analysis/triage_poly.py` (`analysis/triage_poly.out`).

1. **Vigenère / variant Beaufort / Beaufort, khóa tuần hoàn theo chữ cái.** Crib `cdctf` ở 5 chữ cái
   đầu cho `K[0..4] = u,z,u,w,g`; thêm cách đọc `can't` và `we'll` vào các vị trí chữ cái 22-25 và
   83-86 thì cả ba phép chỉ còn đúng L = 13 sống. Nhưng L = 13 không chia 59, trái với phép đo từ lặp.

2. **Khóa chạy theo mọi ký tự** (đếm cả dấu cách, ngoặc, nháy). Từ lặp cho khoảng cách 70 và 90 ký
   tự, nên nếu giả định từ lặp có cùng pha khóa, L phải chia 10, tức L ∈ {2, 5, 10}. Chạy lại crib `cdctf` + `can't` + `we'll` trong chỉ số
   này: không L nào từ 1 đến 20 thỏa, danh sách rỗng ở cả ba phép.
3. **Autokey** (primer + plaintext và primer + ciphertext, m = 1..8, cả ba phép). Bộ đếm từ tiếng Anh
   phổ thông không ứng viên nào vượt 1, nên không có kết quả nào đáng đọc tiếp.
4. **IC theo độ dài khóa** không có đỉnh duy nhất: L = 9 và L = 18 cho 0.0767 và 0.0776 nhưng 18
   không chia 59, còn L = 8 và 16 cũng nằm trong vùng nhiễu của mẫu 151 chữ cái. Không đủ cơ sở,
   và đã bị (1) và (2) phủ.

## Chuỗi khai thác

**Bước 1 - Crib định dạng cờ.** Token đầu `wcwpl{qgj` có dạng `ABACD{`, khớp `cdctf{`, cho bốn ánh xạ
đầu tiên `w→c, c→d, p→t, l→f`.

**Bước 2 - Mở rộng qua các token ngắn.** Bốn ánh xạ đó dịch các từ 2-4 chữ cái thành khuôn gần hoàn
chỉnh: `pmr` = `t?e` → `the` (m→h, r→e), `ph` = `t?` → `to` (h→o), `lhf` = `f?r`... chỉ `for` (f→r),
`prdp` = `te?t` (còn d→s hoặc x).

```text
pmr -> the    ph -> to    lhf -> for    prdp -> te?t
```

**Bước 3 - Từ lặp chốt cả bảng.** `wezmrf` = `c?pher` với `r→e, m→h` nên bắt buộc là `cipher`, cho
`e→i` và `z→p`. Từ đó `leovfrc` = `f?gur?d` → `figured` (o→g, v→u), `wfqwyrc` = `cr?ck?d` → `cracked`
(q→a, y→k), `pmfhvom` = `through` xác nhận lại toàn bộ.

**Bước 4 - Điền chữ còn lại bằng khuôn từ.** Tám chữ chưa ánh xạ (`g,n,u,k,s,t,d,j`) được chốt qua các
còn thiếu: `sqpmrsqpewquuj` = `?athe?atic???` chỉ `mathematically` (s→m, u→l, j→y),
`shghquzmqkrpew` = `?o?oa?pha?etic` chỉ `monoalphabetic` (g→n, k→b), `qgc` = `a.d` → `and` (xác nhận
g→n), `oetrg` = `gi.e?` → `given` (t→v), `nvwm}` = `?uch` → `such`, `prdp` = `te?t` → `text` (d→x,
loại `test` vì `s` đã thuộc về `n`).

**Bước 5 - Kiểm chứng.** Bảng có 22 ánh xạ đơn ánh, và đó chính là ràng buộc của một song ánh trên
bảng chữ cái: bản mã thiếu đúng 4 chữ `a,b,i,x` thì plaintext cũng phải thiếu đúng 4 chữ, thực đo là
`j,q,w,z`. Mã hóa lại plaintext bằng bảng ngược tái tạo đủ 179 ký tự của đề, 24/24 token là từ tiếng
Anh, không còn ký tự nào chưa giải.

```text
[*] ban tho dung 22 chu cai phan biet, bang so chu cua ban ma (22): True
[+] round-trip: ma hoa lai ban tho bang bang the nguoc tai tao dung 179 ky tu cua de -> True
```

Bảng ánh xạ cuối (`analysis/table.out`, in từ chính dict trong `exploit.py`). Dòng trên là chữ cái
trong bản mã, dòng dưới là chữ cái tương ứng trong plaintext:

```text
ma : . . d x i r n o . y b f h s g t a e m v l u c . k p
co : a b c d e f g h i j k l m n o p q r s t u v w x y z
```

Chiều ngược lại, plaintext → bản mã:

```text
co : q k w c r l o m e . y u s g h z . f n p v t . d j .
ma : a b c d e f g h i j k l m n o p q r s t u v w x y z
```

## Flag

```bash
python exploit.py files/ciphertext.txt
```

```text
[*] ciphertext.txt: 151 chu cai, 22 chu phan biet, IC = 0.0580
    tan suat top 6: p:17 q:13 r:13 e:13 w:12 g:9
[*] tu lap lai 'wezmrf': cach 59 chu cai, 70 ky tu
[*] tu lap lai 'kr': cach 75 chu cai, 90 ky tu
[*] bang the 22 anh xa, don anh, 22 chu cai trong ban ma duoc phan anh het
    chu vang trong ban ma: abix | chu vang trong ban tho: jqwz
[*] ban tho dung 22 chu cai phan biet, bang so chu cua ban ma (22): True
[+] round-trip: ma hoa lai ban tho bang bang the nguoc tai tao dung 179 ky tu cua de -> True
[+] plaintext: cdctf{any monoalphabetic sub'stitution cipher can be cracked through sta'tistical analysis given su'fficient cipher text for the numbers to be figured out mathematically and such}
[+] da luu flag.txt
```

## Reproduce

```bash
python exploit.py files/ciphertext.txt
```

`analysis/triage_poly.py` là phần loại các giả thuyết đa bảng (IC theo độ dài khóa, khoảng cách từ lặp,
crib theo hai cách đếm chỉ số, quét autokey), output lưu ở `analysis/triage_poly.out`. Bài này không có
artifact tải về, `files/ciphertext.txt` là bản chép lại đúng bản mã in trên thẻ đề, kể cả ba dấu nháy
đơn; nếu server không nhận chuỗi có dấu nháy, bản bỏ dấu nháy là
`cdctf{any monoalphabetic substitution cipher can be cracked through statistical analysis given sufficient cipher text for the numbers to be figured out mathematically and such}`.
