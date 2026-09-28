# Cache Money — Pwn (Hard)

**Flag:** `sun{s4fe_l1nk1ng_w0nt_s4ve_y0ur_tc4che}`

## 1. Bài toán

`cache_money` là một wallet manager chạy theo menu, mỗi wallet là một struct 0x30 byte cấp bằng
`calloc`, kèm một "ledger" cấp bằng `malloc(size)`:

```
+0x00 name[16]   +0x10 balance   +0x18 ledger*   +0x20 size   +0x28 active
```

Mảng `wallets[16]` nằm ở `.bss` tại `0x4040c0` (binary no PIE nên địa chỉ cố định).
Ba primitive đúng như đề gợi ý "the books haven't been audited":

- `deposit(i)` = `read(0, wallets[i]->ledger, wallets[i]->size)`  -> ghi vào chunk
- `withdraw(i)` = `write(1, wallets[i]->ledger, wallets[i]->size)` -> đọc khỏi chunk
- `open` = `calloc(0x30)` cho struct rồi `malloc(size)` cho ledger

## 2. Lỗ hổng

`transfer(src, dst)` giải phóng ledger của src rồi gán chính con trỏ đã free cho dst:

```asm
401ac9: rdi = [src+0x18]      ; ledger cũ của src
401acd: call free
401ad2: rax = [src+0x18]
401ae8: [dst+0x18] = rax      ; dst nhận con trỏ đã free
401b1a: [src+0x28] = 0        ; src chỉ bị đánh dấu inactive, vẫn nằm trong mảng
```

Từ đây có use-after-free trên heap: đọc và ghi vào một chunk đang nằm trong tcache.

## 3. Hai chi tiết của allocator quyết định hướng đi

**(a) `calloc` không lấy chunk từ tcache, `malloc` thì có.**
Trên glibc 2.39 của target, sau khi free ledger X rồi `open` một wallet mới thì struct của wallet
mới lấy từ top chunk, còn ledger của nó mới là chunk X pop ra từ tcache. Kiểm chứng bằng
chính chương trình: sau `transfer(A->C)` rồi `open B`, `withdraw(B)` in ra tên `"B"` (struct còn
nguyên) nhưng 48 byte đọc được lại là nội dung mình vừa ghi vào C, tức `B->ledger == C->ledger`.
Vì struct không rơi vào chunk đã free nên không thể "đè ledger thành struct" như cách thông thường.

(b) Safe-linking. Chunk độc nhất trong bin có `fd = 0x2eea7` trong khi heap ở `0x2eea7xxx`,
đúng dạng `stored = ptr ^ (slot >> 12)`. Hệ quả hay: khi bin đang rỗng, giá trị `fd` đọc được
chính là mask `heap_base >> 12`, không cần leak heap base riêng. `key` là số ngẫu nhiên theo
thread nên không dùng để leak được.

## 4. Chuỗi tấn công

1. `open A(48)`, `open C(48)`, `open F(48)` -> ledger X, Z, W.
2. `transfer(A->C)` -> X vào tcache, `C->ledger = X`. `withdraw(C)` đọc `fd` => mask.
3. `transfer(F->C)` -> W vào đầu bin, `W->next = X ^ mask`. `withdraw(C)` kiểm tra lại
   `(W->next ^ mask) >> 12 == mask` để chắc model đúng.
4. `deposit(C, p64(TARGET ^ mask) + ...)` -> poison `W->next` thành
   `TARGET = 0x4040f0 = &wallets[6]`.
   Chọn vùng này vì `open_wallet` có `__memset_chk(ledger, 0, size, size)` ngay sau malloc:
   zero 0x30 byte tại `&wallets[6]` chỉ xoá sáu slot đang trống, còn `.rodata` sẽ SIGSEGV và
   GOT sẽ bị xoá luôn `puts`/`read`.
5. `open G1, G2, G3`: ledger của G1 pop W, ledger của G2 pop TARGET -> G2->ledger trỏ thẳng vào
   mảng wallets, G3 giữ slot 5 khác NULL.
6. `deposit(G2, p64(0x4040c0))` -> `wallets[6] = &wallets[0]`, biến chính mảng thành một wallet giả:
   `active` = 4 byte thấp của `wallets[5]`, `ledger` = `wallets[3]`, `size` = `wallets[4]`
   (một con trỏ heap, tức độ dài `read()` khổng lồ, thực tế chỉ lấy đúng số byte mình gửi).
7. `deposit(6, fake_struct(GOT_FREE, 48))` -> đè struct slot 3, biến nó thành đọc/ghi tuỳ ý.
8. `withdraw(3)` đọc 48 byte từ `0x404000` -> GOT. `free` và `puts` đã resolve sẵn
   (`transfer` gọi free, banner gọi puts), hiệu số khớp:
   `free-0xadd20 == puts-0x87bd0` -> libc base -> `system = base + 0x58740`.
9. `deposit(6, fake_struct(GOT_FREE, 8))` rồi `deposit(3, p64(system))` -> `GOT[free] := system`
   (size = 8 để không chạm slot kế bên).
10. `open CMD(256)`, `deposit(CMD, "cat /ctf/flag.txt")`, `close(CMD)` ->
    `free(ledger)` gọi `system("cat /ctf/flag.txt")`.

Không cần ROP: không có `system` trong PLT nhưng Partial RELRO cho phép ghi GOT, và đối số `rdi`
của `free()` chính là con trỏ ledger mà ta kiểm soát nội dung.

## 5. Debug nhanh trên host Windows

Không có pwntools, không có gdb cho ELF Linux, nên toàn bộ là `objdump` + socket thô.
Hai lỗi làm mất nhiều thời gian nhất, đều ở phía client:

- `setvbuf(stdout, NULL, 2, 0)` với `2 == _IONBF`: stdout không buffer, nhưng stdin thì có, nên
  phải gửi từng dòng và chờ đúng marker, không được gửi cả cụm.
- Client chờ kiểu `sleep 1s` cho mỗi prompt bị cắt kết nối ở khoảng lệnh thứ 10. Đổi sang recv
  event-driven (trả lời ngay khi marker xuất hiện) thì cả chuỗi chạy trong ~2 giây.
