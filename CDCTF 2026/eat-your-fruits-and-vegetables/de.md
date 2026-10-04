# Đề bài - eat-your-fruits-and-vegetables

**Sự kiện:** CDCTF 2026 · **Thể loại:** Crypto · **Điểm:** 500 · **Tác giả đề:** alex

## Nguyên văn đề

```text
Eat your fruits and vegetables!
500
Crypto
alex

We did an epic hack on big data and stole this database containing information about 30000 people. Unfortunately, they have implemented epic security practices and have encrypted their database! However, they used AES ECB 128, and we believe that it may still be possible to discern some much needed information. I have a friend named Bob, and I'd like to buy him some fresh produce for his birthday, but I need to know what kind of produce item he likes. I once heard that all people named Bob have the same favorite produce item, so if we can figure out what every Bob likes, we will know what my Bob likes.

About this data that we stole. We hear that when it's decrypted, it is structured as follows: Every person is listed in sequence (in no particular order) with no header or footer or metadata stuff. Every person takes up 32 bytes. The first 8 bytes is their name, followed by null bytes. The next 8 bytes is what brand of car they drive, followed by nulls. The next 8 bytes is their favorite produce item, followed by nulls. The final 8 bytes is their favorite operating system, followed by nulls.

We hear that the data distributions for the entire population are as follows:

Name: Bob - 5% Sally - 5% Mike - 5% Jeffrey - 5% Jeffrica - 5% Joe - 5% Sherry - 5% Perry - 5% Terry - 5% Carrie - 5% Lary - 5% Mary - 5%

Cars: Toyota - 33.33% Chevy - 33.33% Mercedes - 33.33%

Favorite Produce Item: Apple - 10% Orange - 12% Banana - 15% Carrot - 18% Onion - 21% Potato - 24%

Favorite Operating System: Arch - 33.33% Fedora - 33.33% NixOS - 33.33%

In my research, I discovered this article, which may be helpful: https://www.linkedin.com/pulse/ecb-mode-how-works-why-fails-still-exists-yashraj-singh-tomar-rf7ae/

I am leaving the fate of Bob's birthday in YOUR hands, please do not disappoint me.

flag format is 'cdctf{Produce_Item}' (capitalization doesn't matter)

You only get TWO submissions for this challenge, so make sure to get it right!
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/data.db.enc` (copy từ: `C:/Users/Administrator/Downloads/data.db.enc`) |
| Kích thước | 960000 byte |
| SHA-256 | `ea8bfa7cfc6f9f319ccf4f5efa12377beb84087ffb5885bd975656cc628e0374` |
| Loại file | data (khong phai nen, khong co magic header) |
| Entropy | 5.64 bit / 16-byte block (0.35 bit/byte); 60000 block chi co 54 gia tri khac nhau |
| Nhiệm vụ | Suy ra `favorite produce item` cua cac record co `name == "Bob"` |
| Định dạng cờ | `cdctf{Produce_Item}`, khong phan biet hoa thuong |
| Số lần nộp | 2 |

## Hướng giải (tóm tắt)

Không có key và không có oracle, nên mọi hướng tấn công vào AES đều đóng. ECB bảo toàn bằng chứng khối: hai plaintext 16 byte giống nhau cho ra cùng một ciphertext, do đó cấu trúc bản rõ hiện ra nguyên vẹn trong ciphertext. 30000 record chỉ tạo ra 36 ciphertext khác nhau ở nửa đầu và 18 ở nửa sau, tức là toàn bộ không gian trường đã bị lộ.

Nhóm 3 block "tên + xe" mà đề nói bị ràng buộc (Bob có một loại hoa quả cố định) chỉ xuất hiện cùng 3 block "hoa quả + OS", trong khi mọi tên khác xuất hiện cùng cả 18 block. Tổng tần suất của đúng 3 block đó trên toàn cơ sở dữ liệu bằng 5400/30000 = 18%, đối chiếu bảng phân bố của đề cho ra Carrot.

## Chạy lại lời giải

```bash
python exploit.py files/data.db.enc
```

Kết quả: `cdctf{Carrot}` (đã lưu trong `flag.txt`).
