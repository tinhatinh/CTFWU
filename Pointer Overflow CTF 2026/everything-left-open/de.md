# Đề bài - Everything Left Open

Chưa có ảnh thẻ đề. Bản mô tả dưới đây chép nguyên văn từ phần text của thẻ.

## Nguyên văn đề

```text
FOR 100 · Wave 1
Everything Left Open

You've got no idea what you've gotten yourself into, Gumshoe. You think this is just a
quick little peak at some secrets, collect a payday, and move on with your life, huh?
Well, we'll just see about that. Could be this is just the first step. Better wise up,
flatfoot.

A hotel security officer bagged a laptop a guest walked away from - still unlocked,
browser open, data entered mid-form. It was zipped up by an outside IT consulting firm
the hotel retained, how it's in your hands. There a flag in that session, but you might
want to pay attention to the details, just in case.

Case artifact
-> left-open-profile.zip (generated for your team)
   faadae549b93f75ac371aecb62b97a778b8be80da07e66892ec9125137828a47
```

## Thông tin đã xác minh được

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/left-open-profile-team-612.zip`, 3.486 byte |
| SHA-256 | `faadae549b93f75ac371aecb62b97a778b8be80da07e66892ec9125137828a47` (khớp thẻ đề) |
| Nội dung zip | 6 file, không comment, không byte thừa sau EOCD |
| Định dạng | Firefox profile `k-vance-profile`: `places.sqlite`, `formhistory.sqlite`, `logins.json`, `prefs.js`, `sessionstore-backups/recovery.jsonlz4`, và `README.txt` |
| README trong zip | Docket MARCHETTI/2026-14, subject E. Marchetti (mất tích), analyst K. Vance, "Find what she was about to submit." |
| Cờ | `POCTF{109.612.I777LWHDFNCWRJ2S.JB6P5ZRASWPVYKKKHXKAPSQFWT}` |

## Hướng giải (tóm tắt)

Cờ nằm trong dữ liệu form chưa nộp của tab cuối, được Firefox ghi lại ở
`sessionstore-backups/recovery.jsonlz4`. Container đó là `mozLz40\0` + 4 byte size LE + một
LZ4 block, nên block bắt đầu ở offset 12. Chi tiết và các chi tiết lạc hướng khác trong
`writeup.md` và `notes.md`.

## Chạy lại

```bash
python exploit.py                       # dùng files/left-open-profile-team-612.zip
python exploit.py <duong-dan-zip-khac>  # bản của team khác
```
