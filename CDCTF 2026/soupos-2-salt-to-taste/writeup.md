# soupOS 2: Salt to Taste - Rev Eng pwn (489 điểm)

**Cờ:** FLAG2, in ra bởi `chef special` (chuỗi không được ghi lại verbatim trong bản ghi đã lưu)
· **Điểm:** 489 · **Tác giả:** soup (CDCTF)
**Handout:** `soupos-handout.tar.gz` + `symbols.txt` (dùng chung với stage 0 và 1)

## Đề bài

"Only the headchef knows today's special. The kitchen roster is world-readable."

## Phân tích

Roster là một file FAT đọc được bằng chính lệnh của shell (`/etc/kitchen` world-readable):

```text
cook@soupOS:/> pour /etc/kitchen
headchef:0:f63a9eb7
cook:1:e7d471fc
```

Định dạng `name:uid:hexhash`, so sánh trong `users.c`:

```c
int users_check(const char *name, const char *secret) {
        if (roster[i].hash == hash_secret(secret)) return (int)roster[i].uid;   /* so HASH */
```

Hai hệ quả ngay từ source:

1. **Không salt, không key** ⇒ không thể loại trừ brute-force; nhưng
2. **cổng chỉ so giá trị hash** ⇒ ta **không cần mật khẩu thật**, chỉ cần một tiền ảnh bất kỳ của
   `0xf63a9eb7`.

`alphasoup("soup") = e7d471fc` khớp dòng `cook`, dùng làm test vector cho implementation của hàm hash.

## Hướng đã thử

1. **Gõ mật khẩu redact `xxxxxxxx`.** Handout có `roster[0].hash = hash_secret("xxxxxxxx")` nhưng
   `alphasoup("xxxxxxxx") = 0e4273c9` ≠ `f63a9eb7` ⇒ ảnh gốc đã được build lại với secret khác.
2. **Đưa `chef special` vào ngay màn hình đăng nhập.** Cổng đăng nhập đọc **tên tài khoản** trước, nên
   chuỗi đó bị hiểu là tên user. `chef` là lệnh của shell, chỉ chạy được sau khi đã vào `cook`.
3. **Dùng `src/solve/crack.c` của chính tác giả** (vét cạn 36^7 ≈ 783 triệu với OpenMP). Chạy được, nhưng
   không cần: AlphaSOUP-32 là **lọc theo từng byte và mỗi bước đều khả nghịch** (`^b`, `rotl 13`,
   `* NOODLE` với NOODLE lẻ, `^ h>>17`), nên chia chuỗi 7 ký tự thành 3 + 4 và gặp nhau ở giữa rẻ hơn
   ~450 lần. Giữ lại như phương án dự phòng.

## Lời giải

**Bước 1 - Đảo hàm băm để làm meet-in-the-middle.** Với mỗi byte, phép trộn là song ánh trên 32 bit state,
nên viết được chiều ngược: `rotr 13`, nhân nghịch đảo modulo 2^32, và `x = z ^ (x >> s)` giải bằng 4 vòng
lặp. `analysis/collide.c` dùng đúng `alphasoup_hash()` của kernel cho chiều tới và bản đảo của nó cho chiều
lùi, bảng băm 1.679.616 trạng thái lùi so với 46.656 trạng thái tới:

```bash
gcc -O2 -w -idirafter "../soupos/src" -o collide.exe collide.c ../soupos/src/alphasoup.c
./collide.exe -selftest          # 7/7: băm rồi đảo phải ra đúng chuỗi ban đầu
./collide.exe 0xf63a9eb7
```

```text
target      : 0xf63a9eb7
preimage    : saohjea
verify      : alphasoup("saohjea") = f63a9eb7
```

**Bước 2 - Kiểm tra với code xác thực của handout.** `analysis/gate_test.c` link thẳng
`users.c` + `alphasoup.c` của handout, dựng roster y hệt máy (`headchef:0:f63a9eb7`), rồi gọi
`users_check()`:

```bash
gcc -O2 -w -idirafter "../soupos/src" -o gate.exe gate_test.c \
     ../soupos/src/users.c ../soupos/src/alphasoup.c
./gate.exe 0xf63a9eb7 saohjea      # -> uid 0 (chấp nhận)
./gate.exe 0xf63a9eb7 zzzzzzz      # -> -1  (từ chối)
```

Có cả nhánh dương và nhánh âm nên bước này chứng minh được tiền ảnh thật sự mở được cổng, chứ không chỉ
trùng một hàm tự viết lại.

**Bước 3 - Lên uid 0 và gọi món đặc biệt.** `chef <command>` dispatch với uid 0, và
`challenge_special()` chỉ in cờ khi `users_is_headchef()`:

```text
cook@soupOS:/> chef special
headchef's secret: saohjea
  Today's special: cdctf{...}
```

## Kết quả

`chef special` in cờ stage 2 trên VM. Đội đã báo cáo dùng cách này để mở stage 3, nhưng giá trị cờ chưa được lưu trong bản ghi. Kết quả local xác nhận `saohjea` cho hash `f63a9eb7` và `users_check()` trả uid 0 với roster thử nghiệm.

## Tái hiện

```bash
# local: sinh tiền ảnh và kiểm chứng bằng chính source của đề
gcc -O2 -w -idirafter "../soupos/src" -o collide.exe analysis/collide.c ../soupos/src/alphasoup.c
./collide.exe 0xf63a9eb7
gcc -O2 -w -idirafter "../soupos/src" -o gate.exe analysis/gate_test.c \
     ../soupos/src/users.c ../soupos/src/alphasoup.c
./gate.exe 0xf63a9eb7 saohjea

# trên máy:
pour /etc/kitchen
chef special            # nhập: saohjea
```
