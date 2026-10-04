# Đề bài - Troubled Translation

## Nguyên văn đề

```text
Troubled Translation
479
OSINT
adlee7, rei

A plain old Alabama college student, Bob Burke (username bubu77), was accidentally added to a random groupchat on the new messaging platform Chatterly. He was going to leave immediately but he could tell something weird was going on, so he took screenies before the users kicked him from the chat. Can you translate the text and figure out who the target of their next hack is?

The flag format is cdctf{Business_in_City}, for example if their next target is Woolworths in Blackwood, the flag would be cdctf{Woolworths_in_Blackwood}.
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/translation.zip`, copy từ `C:\Users\Administrator\Downloads\translation.zip` |
| Kích thước | 19609739 byte |
| SHA-256 | `b4e5df962599ce981bc05a8d1fd9e3d007f9f74a55b305f58537540eff51e10b` |
| Loại file | ZIP, chứa năm JPEG |
| Nhiệm vụ | Dịch chat, xác định doanh nghiệp và thành phố của mục tiêu |
| Định dạng cờ | `cdctf{Business_in_City}` |
| Độ khó | Đề không cung cấp |
| Trạng thái | Solved; người dùng xác nhận flag đúng |

## Hướng giải (tóm tắt)

Đọc năm ảnh theo thời gian. Hội thoại nhắc McDonald’s ở Chicago và sau đó quay lại lựa chọn McDonald’s. Flag được người dùng xác nhận là `cdctf{McDonald's_in_Chicago}`.

## Chạy lại lời giải

```powershell
python exploit.py files/translation.zip
```

Script giải nén để đọc trực tiếp, không in flag. Flag đúng đã lưu trong `flag.txt`, theo xác nhận của người dùng.
