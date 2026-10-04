# Đề bài - crypto-cat-1

## Nguyên văn đề

```text
The Epic Adventures of Crypto Cat Caticus Catanius (1/5)
500
Crypto
alex

There is a far away place, scarcely heard of, but altogether splendid, known as
the village of Caterie. The residents are a peaceful folk; mostly farmers,
mouse-catchers, and artisans. A cat named Crypto Cat Caticus Catanius lives in a
quaint dwelling there, where he plays with his yarn and dines on fish.

One day, while Caticus was out fishing, the evil cat wizard Dericat the Unethicat
appeared, and abducted everyone in the village! He locked up the poor citizens of
Caterie in his terrifying cat dungeon!

Now, the fate of Caterie lies in the paws of Crypto Cat Caticus Catanius. In
order to save the villagers, you will need to role-play as a fantasy cyber cat.
Good luck!

Dericat the Unethicat has encrypted the master dungeon key with an enchantment
known as "xor with many keys." In order to access it, you will need to decrypt
the four minor keys of the dungeon. (Make sure to save flags as you go, as all of
them will be required for part 5).

The four minor encrypted keys seem to be accompanied by taunting messages written
by Daricat the Unethicat himself.

====================

Greetings, Crypto Cat Caticus Catanius! My invincible cat dungeon is pawrtected
by meowny keys. This is but the fish- coughs dryly -first one, and you will NEVER
break all of them!! Meowwrrrrrr!!!!

xwxgu{zgyzhs1m_rg_fk_rm_s3iv}
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/ciphertext.txt` (dòng cuối của đề, copy thủ công, không có file tải kèm theo) |
| Kích thước | 30 byte (29 ký tự ciphertext + 1 newline) |
| SHA-256 | `901d528d70490f20879dbbf29865c48c3440647a156e57ae261201f0db39cf99` |
| Loại file | ASCII text, một dòng, không có metadata |
| Nhiệm vụ | Giải mã minor key thứ nhất trong bốn key của ngục tối |
| Định dạng cờ | `cdctf{...}` |

## Hướng giải (tóm tắt)

Ten bài nói "xor with many keys" nhưng đó là cơ chế của khoá master ở phần 5; mỗi
phần 1-4 là một mật mã cổ điển độc lập. Ciphertext giữ nguyên `{`, `}` và bốn dấu
`_` đúng vị trí của một flag, nên phép biến đổi chỉ chạm vào chữ thường: dò hết
XOR một byte và 25 dịch chuyển Caesar đều không ra chuỗi đọc được, còn Atbash
(a<->z) biến `xwxgu` thành `cdctf` ngay lần thử đầu.

## Chạy lại lời giải

```bash
python exploit.py files/ciphertext.txt
```

Kết quả: `cdctf{atbash1n_it_up_in_h3re}` (đã lưu trong `flag.txt`).
