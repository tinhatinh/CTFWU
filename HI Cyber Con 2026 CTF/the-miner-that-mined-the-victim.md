---
title: "The Miner That Mined The Victim"
category: "Forensics"
tags: []
solve_date: "2026-11-01"
language: "vi"
---

# The Miner That Mined The Victim

## Đề bài

Bộ chứng cứ Windows ghi lại một ca lây nhiễm từ công cụ giả “free mining optimizer”. Instance TLS đặt 14 câu hỏi theo thứ tự; ba đáp án sai liên tiếp sẽ reset tiến độ. Cần phân tích chứng cứ trước, sau đó gửi đủ đáp án trong một phiên để lấy flag cuối.

## Phân tích

Timeline dựng được từ artifact:

- User `milon1` truy cập trang Telegraph `CoinBoost-Pro-v32--Free-Mining-Optimizer-05-12`, rồi tải `miner.zip` 77.944 byte từ LimeWire.
- Tải xong lúc `2026-05-13 14:25:36 UTC`. `miner.exe` chạy lần đầu lúc `14:26:55 UTC`, được đối chiếu bằng Prefetch run count 1 và `PcaAppLaunchDic`.
- Lúc `14:26:58 UTC`, payload nạp `System.Security.Cryptography.dll` từ thư mục .NET `9.0.16`.
- Payload đặt policy `DisableAntiSpyware` rồi mã hóa 34 file thành đuôi `.vibed`.
- Thư mục `C:\Users\milon1\Downloads\miner` bị đưa vào Recycle Bin lúc `14:27:47 UTC`, kích thước 179.623 byte.

## Lời giải

### 1. Khôi phục nội dung đã bị xóa

Kho lưu Sysmon ở `C:\Sysmon` giữ bản plaintext của các file được theo dõi. Từ đó khôi phục được `bar.txt`:

```
I will always be there for you bro!
```

File `Microsoft-Windows-Sysmon%4Operational.evtx` chỉ hiển thị 58 record còn sống nhưng vẫn chứa chunk cũ. Carve 126 chunk thu 7.460 event, trong đó có việc xóa `C:\Users\milon1\Documents\noting.txt` với mẫu ghi đè `0x706c6568`.

Trên x86 little-endian, giá trị đó có thứ tự byte `68 65 6c 70`, đọc thành `help`.

### 2. Gửi bộ đáp án

| # | Đáp án |
|---|---|
| 1 | `Microsoft Windows NT 10.0.26200.0` |
| 2 | `UTC-7, 420` |
| 3 | `https://limewire.com/d/Ak55K#Yrx3FgK3du` |
| 4 | `42d377fe-8948-4a32-809f-69a51e6dbcfa` |
| 5 | `2026-05-13 14:25:36 UTC` |
| 6 | `2026-05-13 14:26:55 UTC, 1` |
| 7 | `C:\Program Files\dotnet\shared\Microsoft.NETCore.App\9.0.16\System.Security.Cryptography.dll, 2026-05-13 14:26:58 UTC` |
| 8 | `HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\DisableAntiSpyware` |
| 9 | `T1685` |
| 10 | `hiCTF{finally_u_proved_ur_worthiness}` |
| 11 | `C:\Users\milon1\Downloads\miner, 2026-05-13 14:27:47 UTC` |
| 12 | `179623` |
| 13 | `I will always be there for you bro!` |
| 14 | `help` |

`T1685` ở câu 9 được giữ nguyên như đáp án của instance đã ghi lại, không dùng nó làm kết luận độc lập về phân loại kỹ thuật ATT&CK.

### 3. Phân biệt đáp án trung gian và flag

Chuỗi ở câu 10 là nội dung file “important text”, không phải flag cuối. Instance chỉ in flag thật sau khi cả 14 câu đã được chấp nhận trong cùng lượt.

## Kết quả

```
hiCTF{c4r3ful_4b0ut_cr4ck3d_t001s_34aa866011}
```

Bản writeup giữ bộ đáp án và phương pháp khôi phục chứng cứ; không kèm bộ ảnh đĩa/bộ nhớ hay client TLS tự động. URL LimeWire trong bảng là chứng cứ của tình huống, không phải tài nguyên cần tải để đọc bài.
