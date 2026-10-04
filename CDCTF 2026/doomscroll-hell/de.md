# Đề bài - doomscroll-hell

## Nguyên văn đề

```text
Doomscroll Hell
500
Forensics
soup

We intercepted Crimson Offense's Instagram group chat where we believe they were
exfiltrating data by sending these awesome reels! Can you help us find the flag?

Flag format: cdctf{word_word_word_word_word}
```

File kèm theo: `doomscroll.zip`, bên trong là thư mục `doomscroll/` với 15 file `.mp4`
tên dạng shortcode Instagram (`C1-sQVqsTIu.mp4`, `CWBRyIGYAOd.mp4`, ...).

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact gốc | `doomscroll.zip`, 51.462.800 B, sha256 `5163b4d7ac3210f8e9e01024c8981f8ed71858665b003955af56cdd123903f79` |
| Nội dung zip | 15 mp4, tổng 51.460.858 B uncompressed, hash từng file ở `files/mp4-sha256.txt` |
| Video | H.264 + AAC 44,1 kHz stereo, 540x960 (11 file), 540x540 (2), 480x854 (2), 540x588 (1); 10,1-13,5 s; encoder `Lavc libx264`; `creation_time` 2026-10-03 |
| Cấu trúc box | cả 15 file có đúng `ftyp, moov, free, mdat, uuid`; `free` 8 B rỗng |
| Box ẩn | `uuid` 92-93 B nằm SAU `mdat`, 15 file dùng chung UUID `5f0a6c1e-7b3d-5a8e-9c4f-2d1b6a7e3c90`, payload 68-69 B |
| Payload | 15 lát cắt của một PDF 1022 B (`%PDF-1.4`, `N 0 obj`, `xref`, `trailer`, `startxref`, `%%EOF`, một stream FlateDecode `/Length 450`) |
| Artifact đã lưu | `files/chunks/*.bin` (15 lát cắt, tên theo shortcode), `files/recovered.pdf` (PDF dựng lại) |
| Nhiệm vụ | ghép 15 lát cắt theo đúng thứ tự byte, giải nén content stream để đọc cờ |
| Định dạng cờ | thẻ đề ghi `cdctf{word_word_word_word_word}`; cờ thật có thêm `!` ở cuối từ cuối cùng |

51 MB video không đưa vào repo. `exploit.py` chạy trực tiếp trên thư mục mp4 hoặc trên
`files/chunks/` đã carve sẵn, hai đường cho ra cùng một file PDF.

## Hướng giải (tóm tắt)

Dữ liệu không nằm trong khung hình hay âm thanh mà nằm ở box `uuid` thừa sau `mdat` của mỗi
file. 15 box chứa 15 lát cắt liên tiếp của một PDF; thứ tự ghép phục hồi bằng hai ràng buộc
của chính file PDF: vùng stream phải inflate hợp lệ tới đúng `/Length 450` byte và mọi offset
trong bảng `xref` phải trỏ đúng vào header `N 0 obj` tương ứng. PDF dựng lại chứa một "internal
memo", dòng `Retention key:` là cờ.

## Chạy lại lời giải

```bash
python exploit.py files/chunks          # không cần video
python exploit.py /path/to/doomscroll   # carve lại từ mp4
```

Kết quả: `cdctf{doomscrolling_is_so_much_fun!}` (đã lưu trong `flag.txt`).
