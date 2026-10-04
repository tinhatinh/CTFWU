# notes.md - soupos-2-salt-to-taste

Handout: `files/soupos-handout.tar.gz` (sha256 `c9fc07e2…92a1e7`) — giống hệt stage 0/1.
Instance noVNC `cook`/`soup`.

## H1 - Đọc roster
cmd: `pour /etc/kitchen`
evidence: `headchef:0:f63a9eb7` và `cook:1:e7d471fc`
result: OK - định dạng `name:uid:hexhash`, world-readable đúng như đề

## H2 - Cổng đăng nhập so cái gì
cmd: `grep -n -A4 'int users_check' soupos/src/users.c`
evidence: `if (roster[i].hash == hash_secret(secret)) return roster[i].uid;` → so **hash**
result: OK - không cần mật khẩu thật, chỉ cần một tiền ảnh của `0xf63a9eb7`

## H3 - Positive control cho hàm băm
cmd: `python exploit.py f63a9eb7 selftest` (dùng bản cài Python của `src/alphasoup.c`)
evidence: `soup -> e7d471fc` (khớp đúng dòng `cook`), `xxxxxxxx -> 0e4273c9`, round-trip 4/4 OK
result: OK - mô hình hash đúng; đồng thời loại giả thuyết "secret là chuỗi redact `xxxxxxxx`"

## H4 - Có brute force được không, và rẻ hơn bằng cách nào
cmd: xem `soupos/src/solve/crack.c` (solver của tác giả, vét cạn 36^7 với OpenMP)
evidence: mỗi byte trộn bằng `^b → rotl 13 → * NOODLE (lẻ) → ^h>>17`, tất cả đều khả nghịch
result: OK - thay 36^7 bằng meet-in-the-middle 3+4: 36^3 = 46.656 trạng thái tới gặp
36^4 = 1.679.616 trạng thái lùi; `exploit.py f63a9eb7` chạy ~2.4 s ra `7q2gtka`
(trên máy đã gõ `saohjea` — cùng một target, mọi tiền ảnh đều hợp lệ)

## H5 - Kiểm chứng qua cổng THẬT, không phải bản Python tự viết
cmd: `gcc -O2 -w -idirafter ../soupos/src -o gate.exe analysis/gate_test.c ../soupos/src/users.c ../soupos/src/alphasoup.c && ./gate.exe 0xf63a9eb7 saohjea`
evidence: `saohjea` → uid 0; `zzzzzzz` → -1
result: OK - có cả nhánh dương và nhánh âm trên đúng `users.c` của đề

## H6 - Sai chỗ đặt lệnh
cmd: gõ `chef special` ở màn hình đăng nhập
evidence: cổng đăng nhập đọc **tên tài khoản** trước nên chuỗi bị hiểu là username
result: DEAD - `chef` là lệnh shell, chỉ chạy sau khi đã vào `cook`

## Kết quả

`chef special` với `saohjea` in `Today's special: <FLAG2>` trên màn hình VM và mở khoá stage 3.
Chuỗi FLAG2 không được dán lại trong phiên nên không có `flag.txt` (quy ước của repo).
