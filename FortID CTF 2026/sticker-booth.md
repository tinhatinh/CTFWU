---
title: "Sticker Booth"
category: "Pwn"
tags: ["use-after-free", "out-of-bounds-read", "arbitrary-file-read"]
solve_date: "2026-10-10"
language: "vi"
---

# Sticker Booth

**Flag:** `FortID{I_h0p3_Y0u_W1ll_Pu7_Th15_5t1ck3r_0n_Y0ur_L4p70p_4f42043742}`  
**Dịch vụ:** `ncat --ssl sticker-booth-51680d7b0aa2.inst18.ctf.fortid.com 1337` (TLS trên port 1337) — handout `handout.zip` 338 KB, gồm `chall` (790416 byte ELF), `recipe_docs.md`, `sample.recipe`

## Đề bài

Dịch vụ là một `Sticker Booth recipe runner`: nhận data theo định dạng recipe được mô tả trong `recipe_docs.md` (kèm một `sample.recipe` hợp lệ trong handout) rồi in ra các sticker mà recipe đó mô tả. Mục tiêu là đọc `flag.txt` trên instance.

```text
Sticker Booth recipe runner
```

## Phân tích

Chuỗi khai thác dùng hai primitive:

1. **Use-after-free → out-of-bounds read.** Sau khi một entry bị giải phóng, bản in recipe vẫn còn tham chiếu tới vùng heap đó, nên phần đọc chạy ra ngoài ranh giới object và in lại nội dung còn sót. Trong các giá trị lộ ra có ticket nội bộ của booth:

   ```text
   [+] booth_ticket = 0xe57de37aa7603634
   ```

2. **Header sticker được tin cậy.** Header của một sticker được dùng làm tham số cho thao tác in mà không đối chiếu với length và nội dung thật của entry. Một header dựng lại (forged) khiến runner gọi `open()` rồi `read()` rồi `write()` theo path do input chọn: nội dung file được đẩy vào slot `b:` của sticker đang hiển thị. Primitive này là đọc file tuỳ ý theo quyền của process `chall`, không phải thực thi mã.

## Lời giải

Trình tự gửi lên instance, đi từ leak tới đọc flag.

1. Đặt booth vào state UAF theo đúng vòng đời recipe (tạo entry rồi xoá entry), sau đó yêu cầu in recipe để phần đọc vượt ranh giới lấy ra `booth_ticket`. Đây là data chạy của process trên instance, phải đọc qua bước leak chứ không dựng lại được từ handout.
2. Dựng header sticker với path trỏ tới `flag.txt`, giữ các trường khác khớp với những gì runner kiểm tra.
3. Gửi recipe chứa header đã dựng. Runner in dòng state cho file rồi đẩy nội dung vào slot `b:`:

   ```text
   --- flag.txt (133 bytes) ---
   ```

   ```text
   b: FortID{I_h0p3_Y0u_W1ll_Pu7_Th15_5t1ck3r_0n_Y0ur_L4p70p_4f42043742}
   ```

   `flag.txt` được runner báo 133 byte, lớn hơn 66 byte của chuỗi flag; chỉ dòng slot `b:` mang chuỗi flag được lưu lại ở đây, toàn bộ thân file không được ghi lại.
4. Vì bước 3 dùng path tương đối, cần xác nhận vị trí làm việc của process trước khi kết luận. Cùng primitive đọc file được dùng với `/proc/self/cmdline`:

   ```text
   /home/ctf/chall
   ```

   `/proc/self/cmdline` chỉ xác nhận argv là `/home/ctf/chall`; nó không cho biết CWD. Phản hồi đã lưu cho thấy lần đọc `flag.txt` thành công, nhưng chưa xác định được vì sao path tương đối phân giải được. Cần đọc `/proc/self/cwd` hoặc kiểm launcher để tái hiện phần này.

Hai block trong bước 3 là các dòng được trích từ cùng một phản hồi của instance, không liên tiếp nhau trong output.

## Kết quả

```text
FortID{I_h0p3_Y0u_W1ll_Pu7_Th15_5t1ck3r_0n_Y0ur_L4p70p_4f42043742}
```

Flag đọc trực tiếp từ dịch vụ đề bài. Chưa lưu phản hồi submission.

## Tái hiện

Cần một client TLS nói chuyện được với port 1337 (nmap-ncat hoặc tương đương) và recipe dựng theo `recipe_docs.md`:

```text
ncat --ssl sticker-booth-51680d7b0aa2.inst18.ctf.fortid.com 1337
```

Bản ghi chưa đủ để dựng payload đầy đủ; không coi mô tả này là solver có thể chạy ngay.
