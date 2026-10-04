# Đề bài - polyglot

## Nguyên văn đề

```text
Polyglot
500
Reverse Engineering
reep236

BigBadOrganizationTM is serious on security, so all members are verified through multiple Q&A sessions.
We've recovered a set of protocols, questions, and answers, but each one is missing some key information
we need to match their dialect. Can you harness your knowledge of languages to get us the information we
need?

We believe this protocol originates from the far depths of Glasgow, Scotland

The flag format for this round is cdctf{ABunchOfTitleCaseWords}
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/Polyglot1.zip` (copy từ: `/c/Users/Administrator/Downloads/Polyglot1.zip`) |
| Kích thước | 2313 byte |
| SHA-256 | `f96c6082004222a2c8356d24e0edfb92f8256c5f9986a7d099b5b11089d88555` |
| Loại file | Zip archive data, made by v3.0 UNIX, last modified Aug 08 2026 21:34:26 |
| Nội dung zip | `Polyglot1/Program1.hs` (4482 B), `Polyglot1/Questions1.txt` (548 B, 32 dòng), `Polyglot1/Answers1.txt` (660 B, 32 dòng) |
| Nhiệm vụ | Recover `KEY` (module `Secrets` mà `Program1.hs` import thiếu). `KEY` chính là xâu cờ |
| Định dạng cờ | `cdctf{ABunchOfTitleCaseWords}`, chỉ dùng ký tự trong `'A'..'}`, nên không có digit, khoảng trắng, apostrophe |

## Hướng giải (tóm tắt)

`Program1.hs` là automaton ở tầng type: 6 chuỗi `Locale` (person/place/thing/time/method/reason) duyệt
ký tự của `KEY`, mỗi bước phát ra một biến thể Glasgow theo `(n * ord c) mod 6` và chuyển state theo
`(n * ord c) mod 7`. Mỗi dòng answer chỉ lộ 3 trong 6 cột, nên bài quy về một CSP trên state mod 7:
duyệt forward cộng backward để lấy tập ký tự khả dụng từng vị trí. Vị trí 1-18 bị siết lại thành
`cdctf{SecretOfComp`, nhưng ký tự 18 buộc thuộc `{F, p}` và `p ≡ 0 (mod 7)` làm state về 0, từ vị trí 19
mọi ký tự đều hợp lệ. Tác giả sau đó xác nhận checker đã đổi thành regex tính từ vùng mơ hồ đó.

## Chạy lại lời giải

```bash
python exploit.py files/Polyglot1.zip                     # bang ung vien tung vi tri + canh bao vung mo ho
python exploit.py files/Polyglot1.zip --selftest           # cai KEY da biet, kiem bo loc khong tim chan
python exploit.py files/Polyglot1.zip "cdctf{SecretOfCompartmentalized}"   # verify mot KEY
```

Kết quả: prefix đã chứng minh `cdctf{SecretOfComp`; chưa có xác nhận nộp thành công nên bài nằm ở `_wip`.
