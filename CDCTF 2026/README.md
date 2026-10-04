# CDCTF 2026

Writeups cho các bài solved trên [cdctf.net](https://cdctf.net/), nền tảng của CDCTF Team.
Cards của bài training ghi thẳng tên tác giả là `CDCTF Team` và hạng `Training <Category>`.

Flag format: `cdctf{...}` (xác nhận từ thẻ bài, ví dụ `cdctf{fL@g!}`).

## Thông tin đã kiểm

- Trang tutorial của từng MAT nằm ở `https://cdctf.net/training/<mat>.html`, nội dung render phía client nên đọc trực tiếp HTML thì lấy được cả đáp án quiz lẫn cờ của phần quiz nếu tác giả không tách sang API.
- Các MAT training có nhiều cờ trên một thẻ bài. Với Forensics Training Mat, thẻ ghi rõ `ALL FIVE (5) flags need to submitted`, tức mỗi cờ phải nộp riêng.
- Đường dẫn vào tài nguyên tải về (artifact) là link trên CTFd, không phải URL công khai ổn định; artifact nào tải được đều copy vào `<ten-bai>/files/`.

## Cấu trúc và Quy ước mỗi bài

Tạo bằng script có sẵn, thêm `--wip` khi chưa ra cờ:

```bash
bash _template/new_case.sh "CDCTF 2026" <ten-bai> "<duong-dan-file-de>" --wip
```

**Cấu trúc thư mục chuẩn:**

```
<ten-bai>/
  de.md        đề nguyên văn + metadata đã xác minh (kind file, size, sha256, format cờ)
  writeup.md   lời giải: Phân tích ban đầu / Các hướng đã loại / Chuỗi khai thác / Cờ
  writeup.en.md bản tiếng Anh, fenced block giữ nguyên từng byte
  notes.md     log từng bước, gồm cả nhánh sai và lý do loại
  flag.txt     đúng chuỗi cờ đã capture
  exploit.py   script tái chạy được, đọc artifact từ argv
  analysis/    script khám phá từng giai đoạn + output đã chạy
  files/       bản sao artifact của đề, không sửa
```

**Quy ước:**

- Cờ chỉ được ghi khi nó xuất hiện verbatim trong output của lệnh đã chạy. Không đoán, không viết trước.
- Số liệu trong `writeup.md` phải truy vết được về một lệnh trong `notes.md`.
- Giữ lại các giả thuyết sai; phần "Các hướng đã loại" là phần đáng đọc nhất khi quay lại sau vài tháng.
- Artifact lớn không commit. Ảnh đĩa 500 MiB của bài forensics chỉ tồn tại tạm thời trong `%TEMP%`, do `exploit.py` sinh ra và xoá.

## Solved Challenges

| Challenge | Category | Difficulty | Flag |
|-----------|----------|------------|------|
| [forensics-training-mat](forensics-training-mat/writeup.md) | Forensics | Training, 250 | 4/5 cờ: `cdctf{A_Basic_Crimson_Disk_Exercise_in_Forensics}`, `cdctf{A_Little_XZtra_Tr3at!}`, `cdctf{d3l3te_w0_sync_h0l3y_C0W}`, `cdctf{f00rens!k_y!pP33}` |
| [corporate-rat](corporate-rat/writeup.md) | Log Analysis | 500 | `cdctf{Lamar Hackson}` |
| [gerry-the-larry-1](gerry-the-larry-1/writeup.md) | Log Analysis | 500 | `cdctf{12}` (số block Meowjority kiểm soát, tính cục bộ từ 1067 phiếu, chưa đối chiếu bằng submission) |
| [best-of-friends](best-of-friends/writeup.md) | Cryptography | 500 | `cdctf{friendshipisalotlikecheese}` (bang chu cai Tom-Tom, tinh cuc bo tu file de, chua doi chieu bang submission) |
| [doomscroll-hell](doomscroll-hell/writeup.md) | Forensics | 500 | `cdctf{doomscrolling_is_so_much_fun!}` (the de ghi `word_word_word_word_word`, co `!` o tu cuoi) |
| [vat-1-going-ham](vat-1-going-ham/writeup.md) | OSINT + Crypto | 500 | `cdctf{N4T0_comms}` (bảng NATO đọc chính tả hex, phát sóng tự sửa bằng từ `Correction`) |
| [vat-4-what-the-helly](vat-4-what-the-helly/writeup.md) | OSINT + Crypto + Password Cracking | 500 | `cdctf{idontcare1}` (S/Key six-word RFC 2289, nhưng chuỗi đi `fold(MD5(hex))` chứ không phải `fold(MD5(8 byte thô))`; mask 53-64 bit quet 14.3M tu rockyou) |
| [vat-5-you-get-all-that](vat-5-you-get-all-that/writeup.md) | OSINT + Crypto | 500 | `cdctf{8u88l3_848813_fl4g_pa55ing}` (BubbleBabble của OpenSSH, đảo theo chuỗi seed; đối chiếu round-trip 85/85 ký tự) |
| [crypto-cat-2](crypto-cat-2/writeup.md) | Cryptography | 496 | `cdctf{exclus1ve_x0r1n_these_byt3s_and_5tuff}` (XOR mot byte, k = 0x8f) |
| [crypto-cat-3](crypto-cat-3/writeup.md) | Cryptography | 498 | `cdctf{any monoalphabetic sub'stitution cipher can be cracked through sta'tistical analysis given su'fficient cipher text for the numbers to be figured out mathematically and such}` (phep the hoa don, ba dau nhay don la mồi chống wordlist) |

\* Forensics Training Mat còn thiếu cờ Part 2 (StegHide trong `flag2.jpg`): máy làm bài không có binary `steghide`/`stegseek`, winget và pip đều không cung cấp. Bài vẫn được đưa vào bảng vì 4/5 cờ đã nộp và toàn bộ phần còn lại đã tái lập bằng `exploit.py`; phần đang mở ghi rõ ở cuối `writeup.md`.

## Chưa có writeup

Các bài CDCTF khác đã làm trong cùng giải nhưng chưa được đóng gói vào thư mục này (GitLash, soupOS,
Catty Malware, Tattle Tale, Cosmic Call, Crimson Clinic, CommuniCATe, Polyglot, Gerry the
Larry (2/2)) đang nằm trong memory của các phiên chơi, chưa có folder. Thêm bằng `new_case.sh` rồi cập
nhật bảng ở trên. Phần 1 của Gerry the Larry đã đóng gói ở `gerry-the-larry-1/`, trong đó có danh sách
12 block cần cho phần 2. Series VAT của `b0b` đã đóng gói 1/5, 4/5 (`vat-4-what-the-helly/`, S/Key)
và 5/5; còn 2/5 (LARP) và 3/5 (Pretty Good Passphrase) chưa có folder. Key PGP `VAT_key` (userid
"Crimson Offense b0b (baller) <b0b@crimson.offense>") tải về cùng đợt với audio của 4/5, nhiều khả
năng là artifact của 3/5; 4/5 đã dùng nó làm đối chứng mật khẩu.
