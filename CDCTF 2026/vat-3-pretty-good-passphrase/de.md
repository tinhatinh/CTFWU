# Đề bài - vat-3-pretty-good-passphrase

## Nguyên văn đề

```text
Verbal Authentication Transmissions 3/5: Pretty Good Passphrase
500
OSINT Crypto
b0b

One of my friends said he was going to send me a message encrypted with PGP, but then he left
me an automated voicemail?!? How am I supposed to decrypt this message? Heres by PGP private
key, you give it a try. Passphrase for the key is 'Password123!'

Flag Format: cdctf{3x4Mpl3_F14g}
```

File đính kèm: `voicemail.mp3`, `VAT_key`.

Thẻ bài không được lưu ảnh trong phiên này nên case không có `files/de.png`; văn bản trên là
nguyên văn phần đề người dùng dán vào chat.

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact 1 | `files/voicemail.mp3` (copy từ: `C:/Users/Administrator/Downloads/voicemail.mp3`) |
| Kích thước 1 | 3964752 byte |
| SHA-256 1 | `437d7631ee3ee3aaf15ddb54383609b3f550c4feb5bbd08814c87ccd0b4e613a` |
| Loại file 1 | MPEG ADTS, layer III, v2, 48 kbps, 24 kHz, mono, `duration=660.792` s |
| Artifact 2 | `files/VAT_key` (copy từ: `C:/Users/Administrator/Downloads/VAT_key`) |
| Kích thước 2 | 2096 byte |
| SHA-256 2 | `28715250c107ef4a3b2bbe611df4a457256c865c091087a0eaf3a6e0875fd03a` |
| Loại file 2 | PGP private key block |
| khoá | RSA-1024, primary `CCD2 6E0B 97CB F289 9D97 9B1B 9BAAC44EC4B7766A`, keyID `9BAAC44EC4B7766A`, subkey encrypt `C87AFF55F4097C91`, uid `Crimson Offense b0b (baller) <b0b@crimson.offense>`, created 1790985684 |
| Bảo vệ key | S2K iter+salt, CAST5 (algo 7), SHA1, salt `AB08DCAE9DAAD9CD`, protect count 65011712 |
| Nhiệm vụ | Suy ra thông điệp PGP đã được đọc thành tiếng trong audio, rồi giải mã bằng key đã cho |
| Định dạng cờ | `cdctf{...}` |

## Hướng giải (tóm tắt)

Audio là lời đọc từng byte của **toàn bộ khối ASCII armor** theo **PGP Word List**: byte ở vị trí
từ chẵn phát âm bằng từ hai âm tiết, vị trí lẻ bằng từ ba âm tiết, và chỉ số trong danh sách
chính là giá trị byte. Đọc 417 từ thành 417 ký tự ASCII, ghép lại được `-----BEGIN PGP MESSAGE-----`
cho tới dòng CRC. Passphrase `Password123!` đề cho là đúng, nên chỉ cần dựng lại armor là giải mã
được; phần khó duy nhất là sửa vài từ mà bộ nhận dạng giọng nói nghe lệch.

## Chạy lại lời giải

```bash
python exploit.py files/voicemail.mp3
```

Kết quả: `cdctf{pr3t7y_g00d_piv4cy_fl4G}` (đã lưu trong `flag.txt`).
