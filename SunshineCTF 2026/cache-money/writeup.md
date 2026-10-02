# Cache Money - Pwn (Hard)

**Flag:** `sun{s4fe_l1nk1ng_w0nt_s4ve_y0ur_tc4che}`

## 1. Bài toán

`cache_money` là một chương trình quản lý ví (wallet manager) hoạt động qua menu. Mỗi ví (wallet) là một struct có kích thước 0x30 byte được cấp phát bằng `calloc`, đi kèm với một "ledger" (sổ cái) được cấp phát bằng `malloc(size)`:

```text
+0x00 name[16]   +0x10 balance   +0x18 ledger*   +0x20 size   +0x28 active
```

Mảng `wallets[16]` nằm ở vùng nhớ `.bss` tại địa chỉ `0x4040c0` (binary không bật PIE nên địa chỉ này cố định). Chương trình có 3 primitive (hành động cơ bản), đúng như gợi ý của đề "the books haven't been audited" (sổ sách chưa được kiểm toán):

- `deposit(i)` = `read(0, wallets[i]->ledger, wallets[i]->size)` -> Ghi dữ liệu vào chunk.
- `withdraw(i)` = `write(1, wallets[i]->ledger, wallets[i]->size)` -> Đọc dữ liệu ra từ chunk.
- `open` = Gọi `calloc(0x30)` cho struct của ví, sau đó gọi `malloc(size)` cho ledger.

## 2. Lỗ hổng

Hàm `transfer(src, dst)` giải phóng (free) ledger của ví `src`, nhưng sau đó lại gán chính con trỏ vừa bị free đó cho ví `dst`:

```asm
401ac9: rdi = [src+0x18]      ; ledger cũ của src
401acd: call free
401ad2: rax = [src+0x18]
401ae8: [dst+0x18] = rax      ; dst nhận lại con trỏ đã bị free
401b1a: [src+0x28] = 0        ; src chỉ bị đánh dấu là inactive, vẫn nằm trong mảng wallets
```

Từ đây, ta có một lỗi Use-After-Free (UAF) trên heap: có thể đọc và ghi vào một chunk đang nằm trong tcache.

## 3. Hai đặc điểm của allocator quyết định hướng khai thác

**(a) `calloc` không lấy chunk từ tcache, trong khi `malloc` thì có.**
Trên hệ thống dùng glibc 2.39 của target, sau khi free ledger `X` và gọi `open` để tạo một ví mới, struct của ví mới sẽ được lấy từ top chunk, còn ledger của nó mới là chunk `X` vừa được pop ra từ tcache. Điều này có thể được kiểm chứng bằng chính chương trình: sau khi thực hiện `transfer(A->C)` rồi gọi `open B`, nếu ta gọi `withdraw(B)` thì nó vẫn in ra tên là `"B"` (struct vẫn còn nguyên vẹn) nhưng 48 byte đọc được lại chính là nội dung ta vừa ghi vào `C`, tức là `B->ledger == C->ledger`. Vì struct không bao giờ rơi vào chunk đã bị free, ta không thể dùng cách thông thường là "ghi đè ledger thành một struct giả".

**(b) Safe-linking.**
Chunk duy nhất nằm trong bin có con trỏ `fd = 0x2eea7`, trong khi base của heap là `0x2eea7xxx`. Điều này khớp với công thức `stored = ptr ^ (slot >> 12)`. Hệ quả rất thú vị ở đây là: khi bin đang rỗng (chưa trỏ đến chunk nào khác), giá trị `fd` đọc được chính là mask `heap_base >> 12`. Do đó, ta không cần phải leak riêng địa chỉ heap base nữa. Giá trị `key` là một số ngẫu nhiên theo từng thread nên không thể dùng để leak được.

## 4. Chuỗi tấn công

1. Gọi `open A(48)`, `open C(48)`, `open F(48)` -> Tạo ra các ledger tương ứng là `X`, `Z`, `W`.
2. Gọi `transfer(A->C)` -> Chunk `X` bị đẩy vào tcache, `C->ledger = X`. Gọi `withdraw(C)` để đọc `fd` và thu được mask.
3. Gọi `transfer(F->C)` -> Chunk `W` bị đẩy lên đầu bin, `W->next = X ^ mask`. Gọi `withdraw(C)` để kiểm tra lại điều kiện `(W->next ^ mask) >> 12 == mask`, nhằm đảm bảo state của tcache diễn ra đúng như dự tính.
4. Gọi `deposit(C, p64(TARGET ^ mask) + ...)` -> Kỹ thuật tcache poisoning: ghi đè `W->next` thành `TARGET = 0x4040f0 = &wallets[6]`.
   Vùng nhớ này được chọn vì hàm `open_wallet` có gọi `__memset_chk(ledger, 0, size, size)` ngay sau khi `malloc`. Việc zero-out (làm sạch bằng số 0) 0x30 byte tại `&wallets[6]` sẽ chỉ xoá 6 slot đang trống trong mảng. Nếu chọn trỏ vào `.rodata` sẽ gây ra lỗi SIGSEGV, còn nếu trỏ vào bảng GOT sẽ vô tình xoá mất địa chỉ của `puts` hoặc `read`.
5. Gọi `open G1, G2, G3`: ledger của `G1` sẽ pop chunk `W`, ledger của `G2` sẽ pop `TARGET` -> Lúc này `G2->ledger` trỏ thẳng vào mảng `wallets`, còn `G3` giữ cho slot số 5 một giá trị khác NULL.
6. Gọi `deposit(G2, p64(0x4040c0))` -> Đồng nghĩa với việc ghi `wallets[6] = &wallets[0]`. Thao tác này biến chính mảng `wallets` thành một ví giả (fake wallet): `active` = 4 byte thấp của `wallets[5]`, `ledger` = `wallets[3]`, `size` = `wallets[4]` (đây là một con trỏ heap, có giá trị cực lớn, là độ dài khi gọi hàm `read()`, thực tế `read()` sẽ chỉ lấy đúng số byte mà ta gửi vào).
7. Gọi `deposit(6, fake_struct(GOT_FREE, 48))` -> Ghi đè lên struct của slot số 3, biến nó thành một primitive đọc/ghi tùy ý (arbitrary read/write).
8. Gọi `withdraw(3)`, đọc 48 byte từ `0x404000` -> Đây là vùng nhớ GOT. Các hàm `free` và `puts` đã được resolve sẵn (`transfer` có gọi `free`, banner có gọi `puts`), ta có thể tính được offset:
   `free - 0xadd20 == puts - 0x87bd0` -> Tính được `libc base` -> Tính được `system = base + 0x58740`.
9. Gọi `deposit(6, fake_struct(GOT_FREE, 8))` sau đó gọi `deposit(3, p64(system))` -> Ghi đè `GOT[free] := system` (đặt size = 8 để không ghi lẹm sang các slot bên cạnh).
10. Gọi `open CMD(256)`, rồi `deposit(CMD, "cat /ctf/flag.txt")`, sau đó `close(CMD)` -> Khi ví này bị đóng, lệnh `free(ledger)` sẽ thực thi thành `system("cat /ctf/flag.txt")`.

Bài này không cần dùng kỹ thuật ROP: dù không có hàm `system` trong PLT, nhưng do binary biên dịch với Partial RELRO nên ta có thể ghi đè GOT, và tham số `rdi` truyền vào cho `free()` cũng chính là con trỏ ledger mà ta hoàn toàn kiểm soát được nội dung.

## 5. Debug nhanh trên môi trường host Windows

Vì không cài sẵn `pwntools` hay `gdb` cho ELF Linux trên Windows, nên toàn bộ quá trình khai thác được thực hiện thông qua `objdump` và thao tác qua socket thô (raw socket). Có hai lỗi gây mất thời gian nhất và đều nằm ở phía client:

- `setvbuf(stdout, NULL, 2, 0)` với `2 == _IONBF`: `stdout` không được buffer, nhưng `stdin` thì có. Vì vậy, ta bắt buộc phải gửi từng dòng lệnh một và phải chờ đúng marker (dấu hiệu nhận biết) từ server, không gửi hàng loạt cùng lúc.
- Ban đầu script client dùng hàm `sleep 1s` cho mỗi lần nhận prompt, điều này làm kết nối bị ngắt (timeout) ở khoảng câu lệnh thứ 10. Khi chuyển sang kiểu recv hướng sự kiện (event-driven - trả lời ngay lập tức khi thấy marker xuất hiện), toàn bộ chuỗi khai thác chạy trong khoảng 2 giây.
