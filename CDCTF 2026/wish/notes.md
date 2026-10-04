# notes.md - wish

Input: `files/client` (679.960 B, sha256 `ae308ff5a34c76e60455e5acbd69d7db993cd67fde038d854e114570424d0394`), `files/auth.hh`, `files/cmd_auth.hh`
Định dạng cờ đề yêu cầu: `cdctf{...}`
Giao diện: ttyd exec `env LD_PRELOAD=/opt/wish/shim.so /opt/wish/client /tmp/sat.sock`, chỉ có 7 lệnh của client, không có shell.

## H1 - Mật khẩu đúng là một chuỗi đoán được
cmd: `objdump -dM intel --start-address=0x404839 --stop-address=0x4048a1 files/client`
evidence: `check_password` mở `/flag.txt`, `getline(flag, 96)`, rồi `strlen(flag) == strlen(password) && !strncmp(password, flag, strlen(flag))`. Client chỉ in `authenticated` hoặc `authentication failed`, không có thông tin vị trí sai.
result: DEAD - không có oracle từng byte, cờ nằm trong file mà player không đọc trực tiếp được.

## H2 - Biến `dbg` thành RCE rồi `cat /flag.txt`
cmd: `readelf -hW files/client; readelf -lW files/client | grep -E 'GNU_STACK|GNU_RELRO'; readelf -dW files/client | grep -i BIND_NOW`
evidence: `Type: EXEC` nên text cố định ở `0x400000`, nhưng `GNU_STACK RW` (NX bật), RELRO chỉ tới `0x40d000` trong khi `.got.plt` chạy đến `0x40d258` (Partial RELRO) và không có `BIND_NOW`; libc/heap/stack vẫn ASLR vì binary link động, và không có lệnh nào in ra con trỏ.
result: DEAD - primitive là `call [chunk+0x18]` với đối số duy nhất là `&session`, không có kênh leak địa chỉ để chọn mục tiêu trong libc.

## H3 - Jump vào `popen@plt`
cmd: `nm -D files/client | grep -E ' U .*(popen|system|execl|execve|fork)'`
evidence: imports có `popen@GLIBC_2.2.5` và `pclose@GLIBC_2.2.5` (dùng cho gnuplot), không có `system`/`execl`. Nhưng tại `0x404810` lệnh gọi là `mov rdi,rbx; call rax` với `rbx = rsi = &session` (object trên stack của `main`), không phải con trỏ tới chunk payload.
result: DEAD - chuỗi lệnh shell phải nằm trong `session`, nơi dữ liệu người chơi không với tới (`session.hh` đề không cấp, nhưng không có input nào ghi vào nó).

## H4 - `shim_flush_class` chặn tái dùng chunk
cmd: `nm files/client | grep -i shim; objdump -dM intel --start-address=0x403fd4 --stop-address=0x40402a files/client`
evidence: binary chỉ có wrapper yếu `maybe_flush_shim_class` (0x403fd4) và hai biến guard/static ở `0x40d618`/`0x40d620`; tên hàm lấy qua `dlsym(RTLD_DEFAULT, "shim_flush_class")` (0x409502). Lời gọi ở `0x40489a` nằm cuối `check_password`, tức sau `free(password)` và sau khi `dbg` đã chạy.
result: OK nhưng không chặn - cửa sổ exploit đóng trước khi flush chạy.

## H5 - Double free có bị glibc bắt không
cmd: `nm -D files/client | grep GLIBC_2.34` rồi gửi thử một lần `AUTHENTICATE`
evidence: binary yêu cầu `__libc_start_main@GLIBC_2.34` và `dlsym@GLIBC_2.34`, tức glibc >= 2.34, nơi `_int_free` in `free(): double free detected in tcache 2`; banner cho thấy box chạy kèm `LD_PRELOAD=/opt/wish/shim.so`. Thực tế trên instance: một lệnh `AUTHENTICATE` đi hết `contrivance -> get_password -> check_password` mà không crash, và in `auth forced via dbg`.
result: OK - chunk A đúng thực được cấp hai lần trong cùng một lần gọi. Vì sao shim.so không để glibc abort chưa đo được (không lấy được `shim.so`, box không có shell).

## H6 - trọng lực có kéo vệ tinh không
cmd: `INFO Earth` / `INFO Satellite` cách nhau 2.5 s, không thrust
evidence: Earth `mass: 0` và `velocity: (0,0,0)`; Satellite giữ đúng `velocity: (-68.220297140345764, 0, 0)` qua nhiều lần gọi, vị trí dịch tuyến tính `1705.507` units mỗi 2.5 s thực.
result: OK - không có hấp dẫn, mọi chuyển động phải do thrust; nhịp sim gấp 10 lần thời gian thực.

## H7 - Burn toàn nhiên liệu trong một lần có đâm nổi không
cmd: `THRUST Satellite -1 0` rồi `INFO Satellite` liên tiếp
evidence: `mass` 1 -> 0.75 -> 0.5 và `velocity` 0 -> -28.293854944373365 -> -68.220297140345764; khớp `v = ve*ln(m0/m)` với `ve ~ 98.4` (`28.29/ln(4/3)=98.32`, `68.22/ln 2=98.44`), tức tổng delta-v đúng 68.22 và nhiên liệu cạn ở `mass = 0.5`. Vệ tinh đi từ `x=50` tới `-286` trong 2.5 s nên không quan sát được khoảnh khắc chạm.
result: OK - va chạm vẫn xảy ra, nhưng chứng minh bằng H8: thân bị nuốt là Earth.

## H8 - Body nào biến mất khi va chạm
cmd: `INFO Earth` trên cùng thế giới sau pha bay xuyên
evidence: `ERR no such body Earth`; `STATUS` chỉ còn một vòng tròn nhãn `Satellite`; `THRUST Earth ...` cũng `ERR no such body Earth`.
result: OK - server xoá body nhẹ hơn (Earth `mass 0`), nên điều kiện thắng của `vanished_alerts` là "một body không còn trong snapshot mới" chứ không phải "vệ tinh chết".

## H9 - Thế giới brick có tự hồi phục
cmd: mở 5 kết nối ttyd mới cách nhau vài phút, gọi `INFO Satellite`
evidence: vị trí tiếp tục tăng đơn điệu (`-39048`, `-45188`, `-52655`, `-197933`), `mass` kẹt ở `0.49999999999999994`, `THRUST` không đổi `velocity`; `ECHO` trả `unknown command`, bảng lệnh của `dispatch` (0x408d6b) chỉ có STATUS/AUTHENTICATE/THRUST/STOP/INFO/HELP/QUIT.
result: DEAD - không có đường reset từ phía player, phải xin instance mới (subdomain mới).

## H10 - Chuỗi chốt trên instance mới
cmd: `python exploit.py wss://sbrktohj.i.cdctf.net/ws`
evidence: cùng một kết nối gửi `AUTHENTICATE` + payload -> `auth forced via dbgauthenticated`; `STATUS` (snapshot nền, Earth còn); `THRUST Satellite -1 0` -> `OK`; poll `STATUS` mỗi 0.7 s -> `[ALERT] Earth is gone since the last STATUS; probable collision with Satellite (last seen gap 0.332567)` và `CONGRATULATIONS: cdctf{W!sh_Up0n_A_Sh0ot1ng_Star_81ab9a33}`.
result: OK - cờ: `cdctf{W!sh_Up0n_A_Sh0ot1ng_Star_81ab9a33}`

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
