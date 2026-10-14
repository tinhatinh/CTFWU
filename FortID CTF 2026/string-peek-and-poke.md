---
title: "String Peek and Poke"
category: "Pwn"
tags: ["std-string","out-of-bounds-access","vtable-leak","rop"]
solve_date: "2026-10-10"
language: "vi"
---

# String Peek and Poke

**Flag:** `FortID{wh3n_7h3_0nly_t00l_15_4_h4mm3r_3v3ry_5tr1ng_15_4_n41l_c8a5687cdf}`  
**Dịch vụ:** `ncat --ssl string-peek-and-poke-2815b549b14a.inst17.ctf.fortid.com 1337` (instance lấy cờ; `d6ffdf3c7593` là instance đã kết nối ở lượt trước). Artifact: `handout.zip` 1.8 MB gồm `chall` 19512 B (ELF64 PIE, full RELRO, canary, NX), `chall.cpp` 804 B, `libc-2.39.so` 2129424 B, `libstdc++.so.6.0.33` 2592224 B.

## Đề bài

`chall.cpp` lưu ghi chú trong một mảng global `std::string notes[CAP=8]` và cung cấp hai thao tác `put` / `get` nhận chỉ mục kiểu `int` mà không kiểm tra biên. Dịch vụ chạy trên instance có TLS ở cổng 1337.

## Phân tích

Chỉ mục không bị kiểm tra biến mảng 8 phần tử thành một cặp primitive đọc/ghi ngoài biên hai chiều, tính từ địa chỉ của `notes`. Mỗi `std::string` của libstdc++ chiếm 32 byte (con trỏ dữ liệu, size, và union chứa capacity hoặc buffer SSO), và hiệu giữa các vùng dưới đây đúng bằng 9 chỉ mục:

| Object | Địa chỉ (theo base image) | Chỉ mục `put`/`get` tương ứng |
|---|---|---|
| `std::cout` | `exe + 0x203020` | -18 … -10 |
| `std::cin` | `exe + 0x203140` | -9 … -1 |
| `notes` | `exe + 0x203260` | 0 … 7 |

Tức là `put`/`get` với chỉ mục âm cho phép đọc và ghi từng khối 32 byte ngay bên trong hai object stream toàn cục.

Theo các attribute của binary trong handout, `chall` là ELF64 PIE, full RELRO, có stack canary và NX. Bộ này đóng các hướng quen thuộc: full RELRO chặn sửa GOT, NX chặn shellcode, canary chặn tràn stack trực tiếp, PIE buộc phải có leak trước khi nhắm địa chỉ. Chuỗi khai thác đi theo hướng còn lại: lấy leak từ chính vùng toàn cục, rồi dựng ROP.

Ba bước của chuỗi:

1. **Leak.** `get -67825` đọc một vùng chứa con trỏ của libstdc++. Trừ offset symbol đã đối chiếu với thư viện để tìm `lso`; solver sau đó dùng khoảng cách mapping của bản triển khai để suy ra libc và executable. Không suy ra heap base hay tính ổn định 20 bit thấp từ thuộc tính PIE.

## Lời giải

Toàn bộ chuỗi được chạy trên instance trực tiếp; `chall` chưa từng được thực thi ngoại tuyến (xem mục "Các hướng đã kiểm tra").

1. Kết nối TLS tới instance, dùng `get` với chỉ mục âm để lấy con trỏ vtable libstdc++ từ chỉ mục -67825, tính base libc và image. Log của phép thử remote đầu tiên ghi lại base thu được:

   ```text
   remote#0 lso=0x7f8aee782000
   ```

2. Dựng descriptor `std::string` giả trong facet `ctype<char>` để có cửa sổ đọc/ghi theo offset, rồi ghi chuỗi ROP xuống vùng đích. Dòng log xác nhận vị trí chuỗi và phần tử đầu tiên:

   ```text
   chain at 0x7ffc1562a318: libc+0x10c08e
   ```

3. Gọi `exit` để đưa quyền điều khiển vào chuỗi. Shell nhận được in marker `SHELL` và chạy các lệnh kiểm tra; `uid=10001(ctf)` là ngữ cảnh của process trên instance:

   ```text
   SHELL
   uid=10001(ctf)
   ```

4. Trong shell, `ls /home/ctf` xác định vị trí tệp cờ rồi `cat flag.txt`. Output của `cat flag.txt` xuất hiện hai lần và cả hai lần đều là cùng một chuỗi cờ.

Địa chỉ stack trong bước 2 (`0x7ffc1562a318`) thuộc range randomise theo từng lần chạy, nên nó là giá trị của phép thử tương ứng chứ không phải hằng số tái sử dụng được; offset `libc+0x10c08e` thì cố định với bản libc đi kèm.

## Kết quả

```text
FortID{wh3n_7h3_0nly_t00l_15_4_h4mm3r_3v3ry_5tr1ng_15_4_n41l_c8a5687cdf}
```

Cờ đọc trực tiếp từ dịch vụ đề bài. Chưa lưu phản hồi submission.

## Tái hiện

Cần một client TLS nói chuyện được với cổng 1337 và Python 3 để tự động hoá các vòng `put`/`get`. Ba offset của vùng toàn cục và các giá trị dẫn xuất từ libc là hằng số với bản handout; base image, base libc, base heap và địa chỉ stack phải lấy từ leak của chính lần chạy.

```text
ncat --ssl string-peek-and-poke-2815b549b14a.inst17.ctf.fortid.com 1337
```

| Dữ kiện | Giá trị | Nguồn |
|---|---|---|
| `std::cout` | `exe + 0x203020` | symbol của `chall` |
| `std::cin` | `exe + 0x203140` | symbol của `chall` |
| `notes` | `exe + 0x203260` | symbol của `chall` |
| stride mỗi chỉ mục | 32 byte | `sizeof(std::string)` |
| chỉ mục leak vtable | -67825 | vùng libstdc++ |
| phần tử đầu của chain | `libc + 0x10c08e` | `libc-2.39.so` trong handout |

Các gadget `ret`, `pop rdi`, `system` và chuỗi `"/bin/sh"` đều lấy từ `libc-2.39.so` đi kèm; việc xác định offset chúng làm trên file thư viện (objdump/readelf), không cần chạy `chall`. Script điều khiển instance không nằm trong handout nên không được chép lại ở đây.
