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
| [troubled-translation](troubled-translation/writeup.md) | OSINT | 479 điểm; độ khó không cung cấp | `cdctf{McDonald's_in_Chicago}` (người dùng xác nhận) |
| [calcurator-1](calcurator-1/writeup.md) | Forensics + Rev Eng | 491 | `cdctf{wpad}` (suy ra cục bộ, chưa đối chiếu submission) |
| [calcurator-2](calcurator-2/writeup.md) | Forensics + Rev Eng | 500 | `cdctf{ICMP ECHO REQUEST}` (suy ra cục bộ, chưa đối chiếu submission) |
| [calcurator-3](calcurator-3/writeup.md) | Forensics + Rev Eng | 500 | `cdctf{1CMP_TR1GG3R$}` (suy ra cục bộ, chưa đối chiếu submission) |
| [calcurator-4](calcurator-4/writeup.md) | Forensics + Rev Eng + OSINT | 500 | `cdctf{libqalculate/prism}` (suy ra cục bộ, chưa đối chiếu submission) |
| [forensics-training-mat](forensics-training-mat/writeup.md) | Forensics | Training, 250 | 4/5 cờ: `cdctf{A_Basic_Crimson_Disk_Exercise_in_Forensics}`, `cdctf{A_Little_XZtra_Tr3at!}`, `cdctf{d3l3te_w0_sync_h0l3y_C0W}`, `cdctf{f00rens!k_y!pP33}` |
| [corporate-rat](corporate-rat/writeup.md) | Log Analysis | 500 | `cdctf{Lamar Hackson}` |
| [gerry-the-larry-1](gerry-the-larry-1/writeup.md) | Log Analysis | 500 | `cdctf{12}` (số block Meowjority kiểm soát, tính cục bộ từ 1067 phiếu, chưa đối chiếu bằng submission) |
| [best-of-friends](best-of-friends/writeup.md) | Cryptography | 500 | `cdctf{friendshipisalotlikecheese}` (bang chu cai Tom-Tom, tinh cuc bo tu file de, chua doi chieu bang submission) |
| [doomscroll-hell](doomscroll-hell/writeup.md) | Forensics | 500 | `cdctf{doomscrolling_is_so_much_fun!}` (the de ghi `word_word_word_word_word`, co `!` o tu cuoi) |
| [vat-1-going-ham](vat-1-going-ham/writeup.md) | OSINT + Crypto | 500 | `cdctf{N4T0_comms}` (bảng NATO đọc chính tả hex, phát sóng tự sửa bằng từ `Correction`) |
| [vat-3-pretty-good-passphrase](vat-3-pretty-good-passphrase/writeup.md) | OSINT + Crypto | 500 | `cdctf{pr3t7y_g00d_piv4cy_fl4G}` (PGP Word List: mỗi từ là một byte của cả khối ASCII armor, chẵn = từ 2 âm tiết, lẻ = từ 3 âm tiết; hợp nhất 3 bản nghe whisper để sửa 8 ô lệch) |
| [vat-4-what-the-helly](vat-4-what-the-helly/writeup.md) | OSINT + Crypto + Password Cracking | 500 | `cdctf{idontcare1}` (S/Key six-word RFC 2289, nhưng chuỗi đi `fold(MD5(hex))` chứ không phải `fold(MD5(8 byte thô))`; mask 53-64 bit quet 14.3M tu rockyou) |
| [vat-5-you-get-all-that](vat-5-you-get-all-that/writeup.md) | OSINT + Crypto | 500 | `cdctf{8u88l3_848813_fl4g_pa55ing}` (BubbleBabble của OpenSSH, đảo theo chuỗi seed; đối chiếu round-trip 85/85 ký tự) |
| [crypto-cat-2](crypto-cat-2/writeup.md) | Cryptography | 496 | `cdctf{exclus1ve_x0r1n_these_byt3s_and_5tuff}` (XOR mot byte, k = 0x8f) |
| [crypto-cat-3](crypto-cat-3/writeup.md) | Cryptography | 498 | `cdctf{any monoalphabetic sub'stitution cipher can be cracked through sta'tistical analysis given su'fficient cipher text for the numbers to be figured out mathematically and such}` (phep the hoa don, ba dau nhay don la mồi chống wordlist) |
| [yummy-rat-toast](yummy-rat-toast/writeup.md) | Password Cracking | 500 | `cdctf{Alfredo Linguini01}` (md5 tên dàn cast Ratatouille ghép thành tên đầy đủ; wordlist chuẩn và rule mở rộng đều trượt vì không sinh dạng "Title Title" + số; cờ có dấu cách, chưa đối chiếu bằng submission) |
| [diggity-network](diggity-network/writeup.md) | Forensics | 500 | `cdctf{file_over_http}` (đọc trực tiếp từ ảnh PNG trong TCP stream 0) |
| [soupos-0-welcome-to-the-kitchen](soupos-0-welcome-to-the-kitchen/writeup.md) | Rev Eng pwn | 431 | `cdctf{soupOS_is_better_than_arch}` (free flag trên thẻ đề; bài này còn dựng bản đồ 4 chỗ "trust the wrong thing" của cả chain) |
| [soupos-1-mise-en-place](soupos-1-mise-en-place/writeup.md) | Rev Eng pwn | 479 | `cdctf{mise_en_place_two_paths_one_check}` (`soup -c pour read(open("/FLAG1.TXT"),47)` - soupyc gọi thẳng VFS, bỏ qua `may()` của shell) |
| [soupos-2-salt-to-taste](soupos-2-salt-to-taste/writeup.md) | Rev Eng pwn | 489 | chưa capture verbatim (AlphaSOUP-32 không salt: tiền ảnh `saohjea` của `f63a9eb7` tìm bằng meet-in-the-middle 3+4, rồi `chef special`) |
| [soupos-3-bad-recipe](soupos-3-bad-recipe/writeup.md) | Rev Eng pwn | 498 | `cdctf{bad_recipe_the_loader_reads_wide}` (ELF 174 B, `p_offset=0xFFF00000` wrap cửa sổ đọc xuống dưới buffer 1 MB; payload 90 byte quét "cdct") |
| [cosmic-call](cosmic-call/writeup.md) | Scanning NTA Crypto | 797 | `cdctf{W3_@rE_n0T_AL0n3_OuT_h3r3?_5d68a0e7}` (keystream 8 byte dùng lại; lệnh `downlinkflag`; độ hoa/thường không phục hồi được từ một mẫu nhiễu) |
| [wish](wish/writeup.md) | pwn | 800 | `cdctf{W!sh_Up0n_A_Sh0ot1ng_Star_81ab9a33}` (double free trong `contrivance` lam `password` va `auth_sess` trung chunk, ghi `dbg` = `auth_bypass_dbg` o `0x403ac9`; co do `vanished_alerts` in ra khi mot body bien mat giua hai lan `STATUS`) |

\* Forensics Training Mat còn thiếu cờ Part 2 (StegHide trong `flag2.jpg`): máy làm bài không có binary `steghide`/`stegseek`, winget và pip đều không cung cấp. Bài vẫn được đưa vào bảng vì 4/5 cờ đã nộp và toàn bộ phần còn lại đã tái lập bằng `exploit.py`; phần đang mở ghi rõ ở cuối `writeup.md`.

## Chưa có writeup

Các bài CDCTF khác đã làm trong cùng giải nhưng chưa được đóng gói vào thư mục này (GitLash, Catty Malware,
Tattle Tale, Crimson Clinic, CommuniCATe, Polyglot) đang nằm trong memory của các phiên chơi. Thêm bằng
`new_case.sh` rồi cập nhật bảng ở trên.

Đang mở, đã có folder trong `_wip/`:

- `_wip/soupos-4-too-many-cooks/` - primitive và lệnh `soup -c let a=[1] a[-1]=1051024` đã chứng minh ở local
  bằng `soupyc.c` thật, còn thiếu một lần xác nhận trên màn hình VM.
- `_wip/gerry-the-larry-2/` - đã bóc client (signature = `8·year+4·lat+2·lon+number`, mint UVIN tuỳ ý),
  đã đo schema `/vote` qua lỗi 422 (`votes` là danh sách boolean phẳng, 121 ô theo `lat` ngoài `lon` trong),
  còn đang mở ở câu "khoá `already voted` tính theo cấp nào"; solver chia khu đã kiểm chứng ở
  `analysis/solver.py`.

Phần 1 của Gerry the Larry đã đóng gói ở `gerry-the-larry-1/`, trong đó có danh sách 12 block cần cho phần 2.
Series VAT của `b0b` đã đóng gói 1/5, 3/5 (`vat-3-pretty-good-passphrase/`, PGP Word List),
4/5 (`vat-4-what-the-helly/`, S/Key) và 5/5; còn 2/5 (LARP) chưa có folder. Key PGP `VAT_key`
(userid "Crimson Offense b0b (baller) <b0b@crimson.offense>") đúng là artifact của 3/5, đã kiểm chứng:
keyID subkey `C87AFF55F4097C91` xuất hiện ngay trong PKESK giải ra từ audio.
