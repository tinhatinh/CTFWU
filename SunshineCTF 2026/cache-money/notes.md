# Decision log - Cache Money

## H1 - overflow trong deposit?
evidence: `deposit` làm `read(0, wallet->ledger, wallet->size)` với size được chặn `[0x20, 0x100]`
ở `open_wallet` (`rax = size-0x20; cmp rax,0xe0; ja -> default 0x80`), chunk cấp đúng bằng size.
result: DEAD - không thừa byte nào để tràn.

## H2 - format string qua `__printf_chk`?
evidence: mọi lời gọi đều `__printf_chk(2, fmt_const, ...)`, có FORTIFY. Tên in bằng `"%s"`.
result: DEAD - không có format do người dùng quyết định.

## H3 - UAF trong `transfer` (ĐÚNG)
evidence: `401ac9: rdi=[src+0x18]; call free` rồi `401ae8: [dst+0x18]=rax` -> dst giữ con trỏ
đã free; src chỉ bị gán 0 và `active=0` chứ không bị xoát khỏi mảng.
primitive: `deposit` = ghi vào chunk đã free, `withdraw` = đọc từ chunk đã free.
result: PENDING -> xác nhận ở H4.

## H4 - calloc có lấy chunk từ tcache không?
evidence (debug1, debug2): sau `transfer(A->C)` thì `open B` cho ra struct B **không phải** X,
mà ledger của B mới là X. Bê nguyên văn: in ra `Ledger contents for "B"` (tên vẫn là "B")
nhưng 48 byte đọc được lại chính là fake struct mình vừa ghi vào C.
result: PENDING -> trên glibc 2.39 target này: `calloc` (wallet struct) bỏ qua tcache,
`malloc` (ledger) mới pop tcache. Đây là mắt xích để đổi hướng tấn công.

## H5 - safe-linking
evidence: chunk độc nhất trong bin có `fd = 0x2eea7` trong khi heap ở `0x2eea7xxx`
=> `stored = NULL ^ (slot>>12)`, đúng dạng XOR đơn giản của glibc 2.33+.
`key = 0x84ca...` ngẫu nhiên, không phải con trỏ -> không dùng để leak heap được.
check chéo: `fd_W ^ mask = X` và `X>>12 == mask` -> model khớp, chạy lại nhiều lần đều đúng.
result: PENDING -> mask lấy trực tiếp từ fd của chunk free đầu tiên, không cần leak heap base.

## H6 - chọn mục tiêu ghi
evidence: `open_wallet` gọi `__memset_chk(ledger, 0, size, size)` NGAY sau khi malloc, nên đích
phải là vùng ghi được và 0x30 byte quanh nó phải vô hại.
`.rodata` (0x402008) -> SIGSEGV. GOT (0x404000) -> memset sẽ xoá luôn puts/read/fgets.
`wallets[]` ở 0x4040c0: chọn `TARGET = 0x4040f0` = `&wallets[6]` -> memset chỉ xoá 6 slot trống.
result: PENDING -> dùng wallets array làm struct giả.

## H7 - struct giả tự tham chiếu
evidence: đặt `wallets[6] = 0x4040c0` thì khi truy cập slot 6, program đọc "ledger" tại
`0x4040c0+0x18 = &wallets[3]` và "size" tại `&wallets[4]` (một con trỏ heap -> độ dài read khổng lồ,
read() chỉ lấy đúng số byte mình gửi). `active` = 4 byte thấp của `wallets[5]` nên phải mở thêm
G3 để khác NULL.
=> `deposit(6)` = ghi Tuỳ Ý vào struct của slot 3. `withdraw(3)` = đọc Tuỳ Ý.
result: PENDING -> khớp, leak được GOT.

## H8 - leak libc và kết liễu
evidence: GOT[free] và GOT[puts] đã resolve (transfer gọi free, banner gọi puts),
`free-0xadd20 == puts-0x87bd0` -> base nhất quán. `system = base+0x58740`.
Ghi 8 byte `system` lên `GOT[free]` (size=8 để không chạm slot khác), rồi `close` một wallet
thường có ledger là chuỗi lệnh -> `free(ledger)` thành `system(ledger)`.
result: OK - `id` chạy được, `find / -iname '*flag*'` ra `/ctf/flag.txt`, cat ra cờ.

## Ghi chú vận hành
- Client phải recv theo event. Bản dùng `pump(1.0)` mỗi prompt bị server/proxy cắt kết nối ở
  lệnh thứ ~10; bản event-driven chạy toàn bộ chuỗi trong ~2 giây.
- Cờ nằm ở `/ctf/flag.txt`, không phải `/flag`.
