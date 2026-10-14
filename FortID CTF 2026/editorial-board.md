---
title: "Editorial Board"
category: "Pwn"
tags: ["charset-shellcode","ret-overwrite","language-tool-oracle","self-modifying"]
solve_date: "2026-10-10"
language: "vi"
---

# Editorial Board

**Flag:** `FortID{Sh3llc0d1n6_L1k3_Sh4k3sp34r3_G3ts_7h3_Fl4G!_31475ec574}`  
**Dịch vụ:** `ncat --ssl editorial-board-ad8e57922c7a.inst2.ctf.fortid.com 1337` (instance giải flag; instance `a20043e92cc9` dùng ở lượt trước đó). Artifact: `handout.zip` 5.7 KB chứa `editorial_board` 13936 B (ELF 32-bit, base `0x08048000`) và `validate.py` 5623 B.

## Đề bài

Dịch vụ nhận một đoạn văn bản và chỉ chạy phần xử lý nội bộ khi văn bản đó "sạch". Hai điều kiện phải thỏa đồng thời:

- Vượt bàn "anti-slop desk": 640–900 ký tự, tối thiểu 90 từ, tối thiểu 4 câu, không có lỗi chính tả. Bàn này hỏi một oracle LanguageTool (instance công khai `languagetool.org`, trả về `matches: 0` với software `6.9-SNAPSHOT`).
- Sau khi được duyệt, văn bản đi qua một typesetter pipeline có overflow `leave; ret` cho phép ghi đè return address.

## Phân tích

`validate.py` trong handout chính là bàn kiểm chống-slop: nó dựng ràng buộc về số ký tự / số từ / số câu rồi chuyển tiếp phần kiểm tra chính tả sang LanguageTool. Văn bản nộp vào vì vậy phải là tiếng Anh thật.

Phía sau bàn kiểm là pipeline typesetter. Khi văn bản được duyệt, một function kết thúc bằng cặp instruction `leave; ret`: `leave` khôi phục stack pointer từ frame pointer, còn `ret` lấy địa chỉ return tại đó. EIP vì thế nhận giá trị do input kiểm soát. Địa chỉ đích là trang `mmap` RWX tại `0x656c6000`, được memset `0xff` trước khi chép payload. Ghi đè return address thành `0x656c6261` (base + `0x261`) chuyển control flow vào byte của văn bản.

Ràng buộc khó nhất là charset payload chỉ cho phép `[A-Za-z .,;:'-?!]` — toàn ký tự in được của văn bản tiếng Anh. Không có byte `\x00`, không có dấu ngoặc nhọn, không có nhóm ký tự điều khiển. Shellcode x86 thông thường không vừa tập ký tự này, kể cả cặp `int 0x80` (`0xcd 0x80`) cần cho `execve("/bin/sh")` trên 32-bit.

Lối thoát là self-modifying code dựng từ các từ tiếng Anh có thật: chọn những từ mà mã ASCII của chúng tình cờ là một dãy chỉ thị hợp lệ trên 32-bit, đủ để tự ghi hai byte `0xcd 0x80` vào vùng nhớ có quyền thực thi, rồi nhảy vào stub `execve("/bin/sh")`. Cùng đoạn văn bản đó vừa là tiếng Anh "sạch" theo LanguageTool, vừa là shellcode khi thực thi.

## Lời giải

Payload chỉ được thực thi trên instance trực tiếp; phía local dừng ở bước mô phỏng payload bằng Unicorn (xem mục "Các hướng đã kiểm tra").

1. Xây payload tiếng-Anh-thành-shellcode bằng `build.py`, xuất ra `ms.bin` 694 B. 693 byte văn bản trước newline nằm trong `[A-Za-z .,;:'-?!]`, đủ dài để phủ buffer dẫn nhập và ghi đè return address về `0x656c6261`.
2. Kiểm payload ngoại tuyến bằng `emu.py` (dựa trên Unicorn): mô phỏng `leave; ret` rơi vào `0x656c6261` đã memset `0xff`, chạy `ms.bin` và xác nhận nó tự ghi `0xcd 0x80` rồi gọi `execve("/bin/sh")` mà không chạm byte ngoài charset hay gây fault. Bước này chỉ mô phỏng, không gửi đi.
3. Mở TLS tới instance. Dịch vụ in chính checksum validator của nó, trùng với `validate.py` trong handout:

   ```text
   57d0eb4d48604a922583646dea18594e41958b0ad8ef3dccfc66e930b0542610 /challenge/validate.py
   validator checksum MATCH
   ```

4. Gửi `ms.bin` qua TLS. Văn bản đi qua bàn anti-slop, rồi return address bị ghi đè vào trang RWX, shellcode tự sửa và exec `sh`:

   ```text
   [+28.3s] Accepted by the anti-slop desk
   [+40.9s] uid=1000(ctf)
   ```

5. Trong shell đã có RCE, `cat` file flag trên instance để đọc flag trực tiếp.

## Kết quả

```text
FortID{Sh3llc0d1n6_L1k3_Sh4k3sp34r3_G3ts_7h3_Fl4G!_31475ec574}
```

Flag đọc trực tiếp từ dịch vụ đề bài. Chưa lưu phản hồi submission.

## Tái hiện

Cần Python 3, Unicorn (`pip install unicorn`) và một client TLS (nmap-ncat hoặc tương đương). Ba dòng đầu của bảng dưới lấy từ handout và từ checksum mà dịch vụ tự in ra; dòng cuối là sản phẩm dựng tại local:

```text
handout.zip      5.7 KB
editorial_board  13936 B   ELF 32-bit, base 0x08048000
validate.py       5623 B   57d0eb4d48604a922583646dea18594e41958b0ad8ef3dccfc66e930b0542610
ms.bin             694 B   payload, charset [A-Za-z .,;:'-?!]
```

`build.py` sinh `ms.bin`: dựng văn bản tiếng Anh thỏa 640–900 ký tự, tối thiểu 90 từ, tối thiểu 4 câu, đồng thời bảo đảm dãy byte nằm trong charset và đủ dài để phủ buffer dẫn nhập tới return address `0x656c6000`. `emu.py` nạp `ms.bin` vào mô hình Unicorn của vùng `0x656c6000` (memset `0xff`) để kiểm charset và luồng tự ghi `0xcd 0x80` trước khi gửi. Hai script này là công cụ hỗ trợ ở local, không nằm trong handout, nên không được chép lại trong bài; mô tả cơ chế ở trên là toàn bộ thông tin cần để dựng lại.

Kết nối tới instance:

```text
ncat --ssl editorial-board-ad8e57922c7a.inst2.ctf.fortid.com 1337
```

Sau khi `execve("/bin/sh")` cho shell, đọc flag bằng `cat` trên file flag của instance.
