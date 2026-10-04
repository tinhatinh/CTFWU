# notes.md - blakes-bride

Input: `C:\Users\Administrator\Downloads\blake.png` (139.894 B, sha256 `60cfcb420af6bd3b30b6fd0a9ee9abcb5584a2d47cb179dafc8448dac673178c`)
Định dạng cờ đề yêu cầu: `cdctf{password1-password2-password3}`

## H1 - Payload nằm trong ảnh (stego/append)
cmd: `python - <<'EOF'` (duyệt chunk) + `exiftool blake.png`
evidence: `IHDR 13, sRGB 1, gAMA 4, pHYs 9, iTXt 896, IDAT 64537, IDAT 65524, IDAT 8794, IEND 0`; số byte sau `IEND` = 0; `exiftool` chỉ ra thêm `UserComment` và `About: uuid:...`
result: DEAD cho phần pixel/stream - không có chunk lạ, không có byte nối đuôi. Nhưng `UserComment` chính là payload, nên hướng "metadata" đúng.

## H2 - Dữ liệu ẩn trong LSB của pixel
cmd: `python -` trích 1/2/3 bit thấp moi moi kenh, `np.packbits` voi `bitorder` ca `little` lan `big`
evidence: ti le byte in duoc 0,043 (1 bit), 0,019 (2 bit), 0,010 (3 bit); 48 byte dau cua moi xau la `00 00 00 00 00 00 f8 0f ...` theo nhiem xam anh, khong co header ASCII
result: DEAD - anh chi la van chuyen, khong phai chua co.

## H3 - ADS cua Windows (Zone.Identifier)
cmd: `Get-Item blake.png -Stream *`
evidence: hai stream, `Zone.Identifier` 240 B, ghi noi tai ve la endpoint file cua `cdctf.net` kem token truy xuat (khong ghi token vao writeup)
result: DEAD - chi la metadata tai cua trinh duyet, khong phai du lieu cua bai.

## H4 - Ba digest 64 byte la SHA-512
cmd: `python crack1.py` (wordlist dam cuoi thu cong x 000..999, ba ham blake2b/sha512/sha3_512, bon cach ghep tu va so)
evidence: `sha512` 0/3, `sha3_512` 0/3, `blake2b` 1/3 (chi co `honeymoon069`)
result: DEAD cho SHA-512/SHA3-512; PENDING -> xac nhan o H5. Ten file `blake.png` va cau "something wrong with Blake" chi BLAKE2b.

## H5 - Wordlist dam cuoi khong du
cmd: `python crack3.py` (tu dien `words_alpha.txt`, 369.778 muc tu, ghep `<tu> + %03d`, 16 tien trinh)
evidence: `HIT trousseau201`, `HIT epithalamium738`, `HIT honeymoon069`; hoan tat trong duoi 75 giay
result: OK - ca ba digest dong thoi khop, khong can rang buoc phu nao khac.

## H6 - Thu tu cua co
cmd: `python exploit.py files/blake.png`
evidence: digest thu nhat trong `UserComment` -> `epithalamium738`, thu hai -> `trousseau201`, thu ba -> `honeymoon069`
result: OK - co: `cdctf{epithalamium738-trousseau201-honeymoon069}`

## Bẫy công cụ đã gặp
- `multiprocessing.Pool` tren Windows dung `spawn`: script khong co `if __name__ == "__main__":` se de quy - moi tien trinh con import lai module va tao them Pool. Lan chay dau tien in ra 1,2 MB log truoc khi bi dung. Ban `exploit.py` nay da dat toan bo vao ham + guard.
- Git Bash bao chen `$_.Property` cua PowerShell thanh `extglob...`: nen ghi lenh PowerShell ra file `.ps1` roi goi bang `powershell -File`.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
