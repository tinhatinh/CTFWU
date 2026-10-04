# The Epic Adventures of Crypto Cat Caticus Catanius (1/5) - Crypto (Easy)

**Flag:** `cdctf{atbash1n_it_up_in_h3re}`
**Files:** `files/ciphertext.txt` (29 ký tự ciphertext, sha256 `901d528d70490f20879dbbf29865c48c3440647a156e57ae261201f0db39cf99`)

## Đề bài

Phần 1 của chuỗi năm phần về ngôi làng Caterie. Đề cho một tin nhắn chế giễu của
tên phù thuỷ mèo Dericat và đúng một dòng ciphertext:

```text
xwxgu{zgyzhs1m_rg_fk_rm_s3iv}
```

Chuỗi này là minor key thứ nhất trong bốn key của ngục tối. Tên bài ghi "xor with
many keys" nhưng mô tả nói rõ đó là bùa của khoá master, và toàn bộ bốn flag thành
phần sẽ được dùng lại ở phần 5, nên từng phần lẻ là một mật mã độc lập.

## Phân tích ban đầu

- Ciphertext dài 29 ký tự, chỉ gồm chữ thường, chữ số, `_`, `{`, `}`.
- Vị trí các ký tự đặc biệt: `{` ở chỉ số 5, bốn dấu `_` ở 14, 17, 20, 23, `}` ở
  chỉ số cuối. Đó chính là khung hình của một flag (`prefix{word_word_word_word}`),
  gợi ý phép biến đổi giữ nguyên các ký tự đặc biệt; XOR byte áp lên toàn chuỗi sẽ đổi luôn
  `{`, `}` và `_`.
- Đề không nói trước prefix cờ, nên mỗi hướng ứng viên được chấm bằng cách nhìn 5
  ký tự đầu (`xwxgu`) có biến thành một tag ra nghĩa không.

## Các hướng đã loại

1. **XOR một byte** (đúng cái tên của series): dò cả 256 khoá trên toàn chuỗi. 16
   khoá cho output nằm trọn trong dải ASCII in được, nhưng chỉ khoá `0x00` (tức
   không mã hoá) giữ được `{` ở chỉ số 5; các output còn lại là chuỗi không khớp định dạng, chẳng hạn
   `yvyftz{fx{ir0l^sf^gj^sl^r2hw|`.
2. **Caesar / dịch chuyển chữ cái**: in cả 25 dịch chuyển (`analysis/triage.py`),
   không dòng nào có prefix là một từ ra nghĩa, và `zgyzhs` không trở thành từ nào
   trong 25 khả năng.
3. **Vigenere/Beaufort với khoá lấy từ tên nhân vật** (`caticus`): ra
   `lmuoi{xuowpg1k_hd_tg_fc_a3et}` và `edvbh{svbtaj1f_im_wj_kn_p3lw}`, cả hai đều
   không có prefix cờ hợp lệ.

Hướng còn lại, Atbash (a<->z), cho `xwxgu` -> `cdctf` ngay lần thử đầu và là lời
giải bên dưới.

Log đầy đủ ở `notes.md`.

## Chuỗi khai thác

**Bước 1 - Xác định khung ciphertext.** Đếm vị trí `{`, `}`, `_` để nhận diện cấu trúc cờ, rồi chạy bảng 25 Caesar và 256 XOR một byte để loại hai hướng
đầu tiên:

```bash
python analysis/triage.py
```

**Bước 2 - Atbash.** Với ký tự thường, Atbash là `chr(219 - ord(c))` (vì
`ord('a') + ord('z') = 97 + 122 = 219`). Áp dụng cho toàn bộ chuỗi:

```python
ALPHABET = "abcdefghijklmnopqrstuvwxyz"


def atbash(s):
    return "".join(chr(219 - ord(c)) if c in ALPHABET else c for c in s)


print(atbash("xwxgu{zgyzhs1m_rg_fk_rm_s3iv}"))
```

```text
cdctf{atbash1n_it_up_in_h3re}
```

**Bước 3 - Kiểm chứng.** Atbash là involution: áp dụng lại lên plaintext phải trả
về đúng ciphertext gốc, và điều này đã được assert trong `exploit.py` (thoát lỗi
nếu không khớp). Prefix `cdctf` khớp định dạng cờ của giải, phần thân chỉ còn chữ
thường - số - gạch dưới, và nội dung tự đọc được (`atbash 1n it up 1n h3re`), phù hợp với kết quả giải mã.

## Flag

```bash
python exploit.py files/ciphertext.txt
```

```text
[*] ciphertext.txt: 29 ky tu
[*] vi tri cua ngoac va gach duoi: [5, 14, 17, 20, 23, 28]
[*] XOR 1 byte: 16/256 khoa cho output in duoc; cac khoa con giu duoc '{' o vi tri 5: ['0x0'] (k=0 la khong ma hoa)
[*] Atbash: xwxgu{zgyzhs1m_rg_fk_rm_s3iv} -> cdctf{atbash1n_it_up_in_h3re}
[+] kiem chung: atbash(atbash(ciphertext)) == ciphertext
[+] flag: cdctf{atbash1n_it_up_in_h3re}
[+] da luu flag.txt
```

## Reproduce

```bash
python exploit.py files/ciphertext.txt
```

## Ghi chú cho các phần sau

Flag phần 1 phải được giữ lại: đề ghi rõ bốn minor key đều cần cho phần 5, nơi
khoá master bị "xor with many keys" bảo vệ, Chưa xác định phép kết hợp các key trong phần này.
