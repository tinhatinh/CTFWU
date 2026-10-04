# Đề bài - diggity-network

## Nguyên văn đề

```text
Diggity Network
500
I told my friend to send me a flag over the internet, so he catted it into netcat.
Dạng flag: cdctf{....
}
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/network_traffic_with_a_flag_in_there.pcapng` (copy từ: `C:\Users\Administrator\Downloads\network_traffic_with_a_flag_in_there.pcapng`) |
| Kích thước | 104320 byte |
| SHA-256 | `2b77a67c14d61cbabd48ca338cbe86188f5bd5c5ff700e00546fe9b6bbd67fa3` |
| Loại file | PCAPNG, Ethernet/IP/TCP |
| Nhiệm vụ | Khôi phục file gửi qua netcat và đọc cờ |
| Định dạng cờ | `cdctf{...}` |
| Điểm | 500, theo đề trong chat |
| Thể loại | Forensics, suy ra từ artifact |
| Tác giả / độ khó | Không được cung cấp trong chat |

## Hướng giải (tóm tắt)

TCP stream 0 truyền một PNG từ 172.21.0.3:34012 đến 172.21.0.2:8080. Ghép payload theo sequence number và đọc cờ viết tay trong ảnh. Không cần HTTP hay giải mã.

## Chạy lại lời giải

```powershell
python exploit.py files/network_traffic_with_a_flag_in_there.pcapng --open-image
```

Nhập cờ đọc từ ảnh: `cdctf{file_over_http}` (đã lưu trong `flag.txt`). Script nhận bản chép bằng tay sau khi khôi phục ảnh.
