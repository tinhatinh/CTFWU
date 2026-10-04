# notes.md - flag-knows-what-it-is

Input: `files/cipher.txt` (149 B, sha256 `23b75625f0b46c16e92de1844d77ece044918557cd472c0a398cb94da2afea75`)
Định dạng cờ đề yêu cầu: `cdctf{...}`

## H1 - Chuỗi hex là text thô
cmd: `bytes.fromhex(...)` rồi in
evidence: 74 byte đều >= `0x80`, `bytes.decode('ascii')` fail; không byte nào ở dải in được
result: DEAD - text thô không thể có toàn byte >= 0x80

## H2 - Dải byte là ảnh qua phép đảo bit
cmd: `min/max` của 74 byte
evidence: pham vi `0x82-0xdf`, đúng bang `~0x7d .. ~0x20` (ASCII in được dao động `0x20-0x7e`); 6 byte dau XOR `0xff` ra `cdctf{`
result: PENDING -> xác nhận ở H3

## H3 - Key duy nhất khi quet 256 gia tri XOR 1 byte
cmd: `python exploit.py files/cipher.txt`
evidence: `quet 256 key XOR 1 byte: 1 kha nang`, key = `0xff`
result: OK - cờ: `cdctf{it is sure where it isn't, within reason, and it knows where it was}`

## Bẫy ghi lại
Chép tay 74 byte ra câu sai: `where it is n't, with reason and it knows where it was` (tách nhầm chỗ có khoảng trắng, rơi một ký tự `n` và `s`). Bản chạy `exploit.py` cho `where it isn't, within reason, and it knows where it was`. Kết luận: với bài giải mã theo byte, chỉ tin output của script, không tin bản chép tay.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
