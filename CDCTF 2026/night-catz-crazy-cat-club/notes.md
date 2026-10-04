# notes.md - night-catz-crazy-cat-club

Input: `C:/Users/Administrator/Downloads/cat_club_authenticator.out` (861072 B, sha256 `4528f8454ae5c2db...606b0a04`)
Định dạng cờ đề yêu cầu: `cdctf{secret cat phrase}`

## H1 - Cờ xuất hiện plaintext trong .rodata
cmd: `strings -a -n 4 cat_club_authenticator.out | grep -i -E "cat|club|secret|phrase"`
evidence: chỉ ba xâu thuộc bài: prompt `When are you at your happiest?: ` (0x480010),
`Welcome to Night Catz Crazy Cat Club! Remember not to have tooo much fun!` (0x480038),
`INVALID. You are NOT a cat. You are NOT welcome in our club. Now SCRAM, HUMAN!` (0x480f00).
Không có xâu nào khớp `cdctf{`.
result: DEAD - binary không in cờ; dữ liệu so sánh nằm ở dạng khác.

## H2 - Có hàm checker riêng
cmd: `nm cat_club_authenticator.out | grep -w main` rồi `nm -n` liệt kê theo địa chỉ
evidence: symbol ứng dụng duy nhất là `main` tại 0x403035; hàm định nghĩa kế tiếp là `call_fini`
tại 0x4033e0, tức `main` dài 907 byte. Toàn bộ còn lại là glibc liên kết tĩnh.
result: OK - mọi logic so sánh nằm trong `main`, không có hàm con cần lần theo.

## H3 - `handle_zhaoxin` 0x403430 là một phần của lời giải
cmd: `objdump -d --start-address=0x4033e0 --stop-address=0x403560 -M intel cat_club_authenticator.out`
evidence: hàm lặp `cpuid` với `eax=4`, tách `eax>>5 & 7` và `eax & 0x1f`, chia cho 3 bằng hằng
`0xaaaaaaab`. `main` không gọi nó; đây là code khởi tạo CPU/cache của glibc.
result: DEAD - không liên quan, nhưng cần loại vì nằm ngay sau `main` và dễ bị đọc nhầm thành checker.

## H4 - Mảng dựng tĩnh trên stack là bản mã hoá XOR một byte
cmd: `objdump -d --start-address=0x403035 --stop-address=0x4033e0 -M intel ... > analysis/main.asm`
evidence: 46 lệnh `c7 85 <disp32> <imm32>` với `disp` từ -0x140 đến -0x8c, cộng các slot -0x144
(`imm=0x67`), -0x148 (biến đếm), -0x14c (cờ ok). Vòng kiểm so
`DWORD [rbp+i*4-0x140]` với `BYTE [rbp+i-0x80]` XOR `[rbp-0x144]`; trước đó là `cmp rax,0x2e`.
result: PENDING -> xác nhận ở H5.

## H5 - XOR ngược cả mảng với 0x67
cmd: `python exploit.py files/cat_club_authenticator.out`
evidence: `0x47` xuất hiện 10 lần và `0x47 ^ 0x67 = 0x20` là dấu cách; 36 giá trị còn lại nằm trong
0x00-0x1e nên sau khi XOR đều rơi vào dải ASCII in được. Chuỗi thu dài đúng 46, khớp `cmp rax,0x2e`.
result: OK - `with a glass in my paw and milk on my whiskers`, cờ
`cdctf{with a glass in my paw and milk on my whiskers}`.

## H6 - Chạy binary để đóng vòng lặp
cmd: `printf 'with a glass in my paw and milk on my whiskers\n' | wsl -d docker-desktop -- sh -c '/tmp/ccc.bin'`
evidence: in `Welcome to Night Catz Crazy Cat Club!` rồi ASCII art con mèo nằm cạnh dòng `GLASS OF MILK`
(46 dòng, 3803 byte, sha256 `3ce0ad080f5b8dd1...c11bafe8`, lưu ở `analysis/welcome_run.txt`).
Probe âm: cùng lệnh với input `wrong answer` in đúng nhánh `INVALID. You are NOT a cat ...`
(`analysis/rejected_run.txt`).
result: OK - hai nhánh hành xử đúng như disassembly dự đoán. Binary chỉ in ASCII art, không in cờ,
nên giá trị nộp là bản thân cụm từ.

## Ghi chú môi trường
Artifact là ELF Linux nên không chạy trực tiếp trên Windows. Distro WSL duy nhất có sẵn là
`docker-desktop` và không mount `/mnt/c`, vì vậy truyền binary qua stdin:
`cat files/cat_club_authenticator.out | wsl -d docker-desktop -- sh -c 'cat > /tmp/ccc.bin && chmod +x /tmp/ccc.bin'`.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
