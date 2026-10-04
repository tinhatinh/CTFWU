# Night Catz Crazy Cat Club - RevE Crypto (500 điểm)

**Cờ:** `cdctf{with a glass in my paw and milk on my whiskers}`
**File đính kèm:** `cat_club_authenticator.out` (Kích thước: 861.072 B, SHA256: `4528f8454ae5c2db4b781f74a7e2be8ac1bb46d89218dd2d5b008d6f606b0a04`)
**Tác giả:** alex

## Đề bài

Dịch vụ xác thực dạng console hỏi `When are you at your happiest?: ` và chỉ cho qua khi nhận đúng
câu trả lời. Đề cho một binary duy nhất, không có địa chỉ mạng; cờ là chính câu trả lời, dạng
`cdctf{secret cat phrase}`.

## Phân tích ban đầu

`cat_club_authenticator.out` là ELF x86-64 liên kết tĩnh glibc, còn symbol. Symbol ứng dụng duy nhất
là `main` tại `0x403035`; hàm định nghĩa kế tiếp là `call_fini` tại `0x4033e0`, nên phần code của bài
chỉ dài 907 byte, toàn bộ dung lượng còn lại là thư viện. `strings` trên `.rodata` chỉ ra ba dòng chữ
của bài (prompt, dòng chúc mừng, dòng từ chối) và không có chuỗi nào khớp `cdctf{`, tức câu trả lời
đúng không tồn tại ở dạng rõ trong file.

Trong `main` có hai vùng dữ liệu đáng chú ý, tất cả đều là số nguyên 32 bit đặt trên stack bằng lệnh
`mov` trực tiếp:

| Vùng stack | Nội dung | Vai trò |
| --- | --- | --- |
| `[rbp-0x140] .. [rbp-0x8c]` | 46 giá trị, `disp` cách đều 4 byte | Mảng tham chiếu |
| `[rbp-0x144]` | `0x67` | Key |
| `[rbp-0x148]` | khởi tạo `0` | Biến đếm vòng |
| `[rbp-0x14c]` | khởi tạo `1` | Cờ hợp lệ |

Trước vòng lặp, code áp một ràng buộc độ dài:

```assembly
403303: call   4010a0 <strlen>
403308: cmp    rax,0x2e          ; strlen(input) must be 46
40330c: je     403318
40330e: mov    DWORD PTR [rbp-0x14c],0x0   ; wrong length -> valid flag = 0
```

## Các hướng đã loại

Trước khi chốt đã kiểm tra và loại các kênh sau (log đầy đủ ở `notes.md`):

1. **Tìm cờ dạng rõ trong file**: `strings` không trả về chuỗi nào khớp `cdctf{`; ba xâu của bài chỉ
   là prompt và hai thông báo.
2. **Tìm một hàm checker riêng**: `.symtab` không có hàm ứng dụng nào ngoài `main`, không có lời gọi
   nào tới hàm tự viết.
3. **`handle_zhaoxin` tại `0x403430`**: chạy `cpuid` lá 4 và duyệt cache descriptor theo modulo 3, là
   code khởi tạo CPU của glibc, `main` không gọi.

## Chuỗi khai thác

**Bước 1 - Đọc vòng so sánh.** Toàn bộ phép kiểm nằm ở đây; `A[i]` là slot `[rbp-0x140+4i]`,
`input` là buffer của `fgets` tại `[rbp-0x80]`:

```assembly
40332c: mov    edx,DWORD PTR [rbp+rax*4-0x140]   ; A[i]
40333b: movzx  eax,BYTE PTR [rbp+rax*1-0x80]     ; input[i]
403340: movsx  eax,al
403343: xor    eax,DWORD PTR [rbp-0x144]         ; input[i] ^ 0x67
403349: cmp    edx,eax
40334b: je     403359                            ; match -> i++
40334d: mov    DWORD PTR [rbp-0x14c],0x0         ; mismatch -> print INVALID
```

Quan hệ cần đảo là `A[i] == input[i] ^ 0x67`, tức `input[i] == A[i] ^ 0x67` vì XOR tự đảo.

**Bước 2 - Trích mảng khỏi mã máy.** Không cần gõ tay 46 hằng số: trong thân `main`, mỗi phần tử
mảng được sinh bởi đúng một encoding `c7 85 <disp32> <imm32>`. `exploit.py` lọc các lệnh có `disp`
trong đoạn `[-0x144, -0x8c]`, tách `0x67` ở `disp=-0x144` làm key, rồi xếp phần còn lại theo `disp`
để khôi phục thứ tự ký tự:

```python
slots = {}
for i in range(len(body) - 10):
    if body[i:i + 2] == b"\xc7\x85":  # mov DWORD PTR [rbp+disp32], imm32
        disp, imm = struct.unpack_from("<ii", body, i + 2)
        if KEY_DISP <= disp <= ARRAY_HI:
            slots[disp] = imm

key = slots.pop(KEY_DISP)
array = [v for _, v in sorted(slots.items())]
phrase = bytes(v ^ key for v in array).decode()
```

**Bước 3 - Kiểm chứng.** Ba ràng buộc độc lập cùng thoả, dùng để đối chiếu key và phép đọc mảng:
mảng có đúng 46 phần tử bằng đúng ngưỡng `cmp rax,0x2e`; giá trị `0x47` lặp lại 10 lần và
`0x47 ^ 0x67 = 0x20` là dấu cách, khớp nhịp của một câu tiếng Anh; 36 giá trị còn lại nằm trong
0x00-0x1e nên sau khi XOR đều rơi vào dải ASCII in được. Chuỗi giải mã là
`with a glass in my paw and milk on my whiskers` (46 ký tự, không có chỗ nào phải đoán lại).

Chạy binary trên Linux để kiểm tra input đã khôi phục. Vì artifact là ELF, bản Windows phải truyền sang WSL
(distro `docker-desktop` không mount `/mnt/c`, nên copy qua stdin):

```bash
cat files/cat_club_authenticator.out | wsl -d docker-desktop \
  -- sh -c 'cat > /tmp/ccc.bin && chmod +x /tmp/ccc.bin'
printf 'with a glass in my paw and milk on my whiskers\n' | wsl -d docker-desktop -- sh -c '/tmp/ccc.bin'
```

```text
When are you at your happiest?: 
Welcome to Night Catz Crazy Cat Club! Remember not to have tooo much fun!

          @@@@@@@                                                               
         @@@@@@@@@@@                           @@@@@@@                          
...
```

Output đầy đủ 46 dòng lưu ở `analysis/welcome_run.txt` (sha256 `3ce0ad080f5b8dd135ceed10d1be9c9db3ac25d2720d718424e2c31dc11bafe8`);
ASCII art vẽ một con mèo nằm cạnh dòng `GLASS OF MILK`. Probe âm với input `wrong answer` in đúng
nhánh từ chối (`analysis/rejected_run.txt`), chứng tỏ phép thử phân biệt được hai nhánh:

```text
When are you at your happiest?: INVALID. You are NOT a cat. You are NOT welcome in our club. Now SCRAM, HUMAN!
```

Binary không in cờ; giá trị nộp là bản thân câu trả lời, đặt trong `cdctf{...}` theo định dạng đề yêu cầu.

## Cờ

```bash
python exploit.py files/cat_club_authenticator.out
```

```text
[*] main()            : 0x403035 - 0x4033e0
[*] array             : 46 ints, [rbp-0x140 .. rbp-0x8c]
[*] xor key           : 0x67  ([rbp-0x144])
[*] length gate       : strlen(input) == 0x2e (46)
[*] prompt            : When are you at your happiest?: 
[+] secret response   : with a glass in my paw and milk on my whiskers
[+] flag              : cdctf{with a glass in my paw and milk on my whiskers}
```

Kết quả:

```text
cdctf{with a glass in my paw and milk on my whiskers}
```

*Cờ tính bằng cách giải mã cục bộ, đã kiểm chứng bằng cách chạy binary với đúng input này (mục Chuỗi
khai thác); chưa đối chiếu bằng submission trên nền tảng.*

## Reproduce

```bash
python exploit.py files/cat_club_authenticator.out
```

Disassembly của `main` dùng để đối chiếu: `analysis/main.asm`.
