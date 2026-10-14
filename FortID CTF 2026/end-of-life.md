---
title: "End of Life"
category: "Pwn"
tags: ["text-binary-mode-mismatch", "stack-overwrite", "16-bit-rop", "dos-int21h"]
solve_date: "2026-10-10"
language: "vi"
---

# End of Life

**Flag:** `FortID{3oF_15_JU57_4_5u993571On_829c948e61}`  
**Dịch vụ:** `ncat --ssl end-of-life-ee7d2f4fa278.inst20.ctf.fortid.com 1337` (TLS trên cổng 1337; flag lấy trên instance `ee7d2f4fa278`, lượt kết nối đầu tiên là `a36309e460e2`). Handout: `handout.zip` 10 KB. Tác giả: ante.

## Đề bài

Target của bài là một chương trình DOS dạng `.COM` theo kiểu CP/M: dịch vụ nhận input, chạy chương trình bên trong một dosbox riêng của nó, rồi in ra file mà chương trình tạo ra (`OUTPUT.TXT`) dưới dạng base64. Bên trong môi trường đó có `flag.txt`; mục tiêu là khiến chương trình đọc file này và đẩy nội dung ra output mà dịch vụ in lại.

## Phân tích

**Lỗ hổng: hai chế độ mở file không khớp nhau.** `check_input()` mở file input ở chế độ text, nên byte `0x1A` được coi là EOF; `process_input()` mở cùng file input đó ở chế độ binary và đọc toàn bộ byte. Hệ quả là phần input sau một `0x1A` không được bộ kiểm tra nhìn thấy nhưng vẫn tới được bước xử lý. Ở bước xử lý, `fscanf("%[^ ]")` nạp chuỗi vào `char name[17]` đặt tại `[bp-0x12]` mà không chặn theo length buffer, nên input dài hơn 17 byte sẽ ghi tiếp qua vùng đó.

**Bố trí stack 16 bit.** `name` bắt đầu ở `bp-0x12`, tức `bp-18`; địa chỉ IP đã lưu (near return của một `call` trong real mode, với BP được push trước đó) nằm ở `name+20`, tức `[bp+2]`. Vì vậy 20 byte đầu của payload là data đệm và 2 byte IP overwrite nằm ngay sau đó; trong chế độ 16 bit của một `.COM`, giá trị ghi đè chỉ là offset IP bên trong segment code của chính chương trình.

**Chuỗi khai thác: ROP 16 bit trên `int 21h`.** Vì quyền điều khiển chỉ có thể nhảy tới các offset trong đúng segment của chương trình, chuỗi được dựng từ các vị trí đã có sẵn trong file:

| Syscall | Offset trong chương trình |
|---|---|
| `_open` | `0x1cf3` |
| `_read` | `0x05ed` |
| `_write` | `0x2366` |
| `_exit` | `0x0197` |

Chuỗi dùng buffer tại offset `0xFFE0` trong data segment và hai handle 5/6 của lần chạy đã lưu. Các handle này phụ thuộc state bảng file của process. `_exit` kết thúc chương trình để dịch vụ trả nội dung `OUTPUT.TXT`.

**Giới hạn byte.** Hai site `0x0d97` và `0x0d96` bị loại khỏi chuỗi vì byte cao của chúng là `0x0d`, nghĩa là khi ghi theo thứ tự byte của một IP thực thì payload chứa byte CR; phần xử lý input nhạy cảm với CR/LF. Bốn offset được chọn (`0x1cf3`, `0x05ed`, `0x2366`, `0x0197`) không chứa byte `0x0d` hay `0x0a`.

## Lời giải

1. Dựng input cho chương trình `.COM`: 20 byte đệm tới vị trí IP đã lưu, rồi tới chuỗi offset ở trên, chèn `0x1A` ở vị trí khiến `check_input()` dừng đọc còn `process_input()` thì không.
2. Gửi payload xuống instance; chương trình chạy trong dosbox của dịch vụ, mở `flag.txt`, đọc vào `DGROUP 0xFFE0`, ghi vùng đệm đó ra `OUTPUT.TXT` rồi `_exit`.
3. Dịch vụ in nội dung file mà chương trình vừa tạo:

   ```text
   Your OUTPUT.TXT: Rm9ydElEezNvRl8xNV9KVTU3XzRfNXU5OTM1NzFPbl84MjljOTQ4ZTYxfQoA…
   ```

4. Giải mã base64 thu được chuỗi flag:

   ```text
   FortID{3oF_15_JU57_4_5u993571On_829c948e61}
   ```

Phần base64 được lưu dài 60 ký tự, là bội số của 4 và giải mã trọn vẹn thành 45 byte: chuỗi flag 43 byte, một byte `0x0A` và một byte `0x00` ở cuối. Byte `0x00` đó là nội dung do chính output của dịch vụ mang lại (vùng đệm được ghi ra file), không phải ký tự thêm vào khi giải mã. Dấu `…` cuối dòng là ký hiệu cắt của bản ghi, không thuộc bảng chữ cái base64, và nằm sau lượng data đã đủ để giải mã toàn bộ chuỗi flag.

## Kết quả

```text
FortID{3oF_15_JU57_4_5u993571On_829c948e61}
```

Flag đọc trực tiếp từ dịch vụ đề bài, qua dòng `Your OUTPUT.TXT:` mà dịch vụ in ra (nội dung base64 của `flag.txt` phía remote). Chưa lưu phản hồi submission.

## Tái hiện

Cần một client TLS nói chuyện được với cổng 1337 (nmap-ncat hoặc tương đương) và một instance đang chạy, vì chuỗi chỉ được thực thi trong dosbox của dịch vụ:

```text
ncat --ssl end-of-life-ee7d2f4fa278.inst20.ctf.fortid.com 1337
```

Bản ghi chưa đủ để dựng payload đầy đủ; không coi mô tả này là solver có thể chạy ngay.
