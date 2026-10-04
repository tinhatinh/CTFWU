# Doomscroll Hell - Forensics

**Flag:** `cdctf{doomscrolling_is_so_much_fun!}` · **Điểm:** 500 · **Tác giả:** soup
**Files:** `doomscroll.zip` (51.462.800 B, sha256 `5163b4d7...903f79`), 15 mp4 bên trong

## Đề bài

Đề cho một nhóm chat Instagram của đội đối thủ Crimson Offense, gồm 15 cái reel được cho là dùng để
exfiltrate dữ liệu. Nhiệm vụ là tìm cờ trong đống video đó. Thẻ đề báo định dạng
`cdctf{word_word_word_word_word}`.

## Phân tích ban đầu

15 file mp4, mỗi file 3,0-4,1 MB, H.264 + AAC, thời lượng 10-13 s. `ffprobe` và `exiftool` không cho
thấy gì đáng ngờ: nhãn chỉ có `encoder = Lavc libx264` và các `creation_time` ngày 2026-10-03, cho biết thời điểm và encoder ghi trong metadata; chưa xác định lịch sử tạo file chỉ từ các tag này. Khung hình là reel thông thường (con chó kéo quần ông chủ, watermark `@SNOPFEED`).

Khác biệt thật nằm ở mức container. Duyệt box MP4 cho thấy cả 15 file có cùng một chuỗi
`ftyp, moov, free, mdat, uuid`. Bốn box đầu là chuẩn ffmpeg; box cuối là `uuid` 92-93 byte, nằm
**sau** `mdat` nên ngoài vùng dữ liệu media, và 15 file dùng chung một UUID
`5f0a6c1e-7b3d-5a8e-9c4f-2d1b6a7e3c90`. Payload 68-69 byte của nó là text và byte trộn lẫn, trong
đó đọc được `%PDF-1.4`, `1 0 obj`, `/Type /Pages`, `xref`, `trailer`, `startxref`, `%%EOF` và một
đoạn mở đầu `x\xda`. Mỗi video đang giữ một lát cắt của cùng một file PDF.

## Các hướng đã loại

1. **Nhãn metadata**: `udta/meta` 53 byte chỉ chứa tag encoder, `free` đúng 8 byte rỗng,
   `creation_time` khác nhau nhưng không theo quy luật nào.
2. **Stego trong khung hình và âm thanh**: không khai thác. Sau khi 15 lát cắt PDF khép lại bằng
   ràng buộc `xref` thì kênh này không còn lý do; mới chỉ xem vài frame bằng mắt, chưa đo LSB hay phổ.

## Chuỗi khai thác

**Bước 1 - Carve lát cắt.** Box `uuid` có 4 byte size, 4 byte type rồi **16 byte extended_type**,
nên payload bắt đầu ở offset `o+24` (dùng `o+16` là lệch 8 byte và không khớp UUID nào). 15 payload
dài 13*68 + 2*69 = 1022 byte.

```python
size = struct.unpack(">I", buf[o:o + 4])[0]
kind = buf[o + 4:o + 8].decode("latin1")
if kind == "uuid" and buf[o + 8:o + 24] == UUID:
    chunks[name[:-4]] = buf[o + 24:o + size]
```

**Bước 2 - Định vị lát cắt bằng ràng buộc của chính PDF.** Không có thứ tự trong tên file, nhưng
file PDF tự kiểm chứng được bằng hai chỗ:

- Vùng stream: `/Length 450`, đúng một lát chứa `stream\n` (phải loại `endstream\n` bằng
  `(?<!end)stream\n`). Duyệt DFS các lát còn lại, mỗi bước giữ nguyên `zlib.decompressobj()` trên
  phần byte đã ghép; lát nào làm inflate lỗi là bị cắt ngay. Khi đủ 450 byte, điều kiện kết thúc là
  `zlib.decompress` chạy hết stream **và** byte kế tiếp phải mở đầu bằng `\nendstream`. Run duy nhất
  thoả: `Cks57_V-Hsy > CU4g7CDhW5q > CDx8NCxzTUA > CtJum68xxwr > CPZGeCCcZfB > Ct9t7nQO6KL >
  CYzUFRaPz5o > C1-sQVqsTIu`.
- 7 lát ASCII còn lại: thử 7! hoán vị x 8 vị trí chèn, nghiệm đúng là nghiệm mà mọi offset trong
  bảng `xref` trỏ trúng header `N 0 obj` của nó và `startxref` trỏ trúng chữ `xref`.

**Bước 3 - Kiểm chứng.** File dựng lại đúng 1022 byte, kết thúc bằng `%%EOF`, và bảng `xref` khớp
tuyệt đối với vị trí thật:

```text
xref rows   15 64 121 247 317   ->  offset thật của `1 0 obj` .. `5 0 obj`: 15 64 121 247 317
startxref   839                 ->  offset thật của `xref`: 839
```

Các lát cắt được ghép đủ và các offset nội bộ khớp cấu trúc PDF. `fitz` render ra một trang duy nhất,
content stream dài 946 byte chứa một "internal memo" về chỉ số retention, dòng áp chót là cờ.

## Flag

```bash
python exploit.py files/chunks
```

```text
[*] 15 uuid slices, 1022 byte total
[+] order: CWBRyIGYAOd > CFH95xUXh5X > C_pn-Ww2wKg > C4cE45r8ICF > CyzAgQA4oVO > Cks57_V-Hsy > CU4g7CDhW5q > CDx8NCxzTUA > CtJum68xxwr > CPZGeCCcZfB > Ct9t7nQO6KL > CYzUFRaPz5o > C1-sQVqsTIu > CdWtouUG4Bu > C9nruRG2aNs
[+] pdf 1022 B, xref offsets verified: True, stream inflated to 946 B
BT
/F1 24 Tf 1 0 0 1 60 740 Tm (INTERNAL MEMO: Engagement Retention Initiative) Tj
/F1 11 Tf 1 0 0 1 60 704 Tm (Classification: DO NOT SCROLL PAST) Tj
/F1 11 Tf 1 0 0 1 60 681 Tm () Tj
/F1 11 Tf 1 0 0 1 60 658 Tm (Team,) Tj
/F1 11 Tf 1 0 0 1 60 635 Tm (Average session length is up 41% since we removed the end of the feed.) Tj
/F1 11 Tf 1 0 0 1 60 612 Tm (Users report they 'only meant to watch one'. This is working as intended.) Tj
/F1 11 Tf 1 0 0 1 60 589 Tm (Autoplay stays on. The refresh gesture stays satisfying. Nobody gets bored.) Tj
/F1 11 Tf 1 0 0 1 60 566 Tm () Tj
/F1 11 Tf 1 0 0 1 60 543 Tm (If you have read this far, you watched every single reel. Congratulations.) Tj
/F1 11 Tf 1 0 0 1 60 520 Tm () Tj
/F1 14 Tf 1 0 0 1 60 497 Tm (Retention key:) Tj
/F1 16 Tf 1 0 0 1 60 471 Tm (cdctf{doomscrolling_is_so_much_fun!}) Tj
/F1 11 Tf 1 0 0 1 60 443 Tm () Tj
/F1 11 Tf 1 0 0 1 60 420 Tm (Now put the phone down and go outside.) Tj
ET
[+] flag: cdctf{doomscrolling_is_so_much_fun!}
```

Thẻ đề hứa năm từ, cờ thật là năm từ kèm một dấu `!` dính vào từ cuối.

## Reproduce

```bash
python exploit.py files/chunks           # 15 lát cắt đã carve, không cần video
python exploit.py /path/to/doomscroll    # carve lại trực tiếp từ 15 file mp4
```

Hai đường cho ra cùng một `recovered.pdf` (đã đối chiếu byte). PDF dựng lại lưu ở
`files/recovered.pdf`, 15 lát cắt ở `files/chunks/*.bin`.
