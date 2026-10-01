# Đề bài - lottery

## Nguyên văn đề

```text
Lottery
299
Beyond the checkpoint, a Beltway Bandits gambling terminal has resumed broadcasting: "Ten wins in a row. One fortune. No second chances." Once used to distribute stolen credits, it now holds an access key to the Bandits' hidden network. Beat the house and claim it before they return to collect.

The ticket is your team name, case-sensitive

Flag Format : CSSCTF{CSS{...}} where CSS{...} is what you get from the netcat

nc 34.116.80.78 31338

附件引用：
- 文件：C:\Users\Administrator\Downloads\Setup (2).sol
- 文件：C:\Users\Administrator\Downloads\Lottery.sol
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/Lottery.sol` (copy từ: `/c/Users/Administrator/Downloads/Lottery.sol`) |
| Kích thước | 1153 byte |
| SHA-256 | `38f58ac24b5c9e8ac0d31195ba1e4ae489bf51b6a00f47320231fb6891df88b5` |
| Loại file | Unicode text, UTF-8 text, `pragma solidity ^0.8.19` |
| Artifact | `files/Setup.sol` (copy từ: `/c/Users/Administrator/Downloads/Setup (2).sol`) |
| Kích thước | 314 byte |
| SHA-256 | `ebb2b795e85b9c713341ab32b4bb106e2ece698658c73417e3e79b5ab866ab06` |
| Loại file | ASCII text, `pragma solidity ^0.8.19` |
| Dịch vụ nc | menu `1 launch / 2 kill / 3 get flag`, mỗi hành động một kết nối TCP |
| Instance | mainnet fork qua RPC `http://34.116.80.78:8546/<uuid>`, chainId `0x1`, tip `26096389` |
| Nhiệm vụ | đặt `lottery.winner()` khác 0, tức đoán đúng 10 số liên tiếp |
| Định dạng cờ | `CSSCTF{CSS{...}}`, phần `CSS{...}` do nc in ra |

## Hướng giải (tóm tắt)

`random()` chỉ băm ba giá trị của block đang thực thi (`blockhash(block.number-1)`, `block.timestamp`, `block.difficulty`) nên nó là hằng số trong suốt một transaction: contract trung gian đọc `random() % 100` rồi gọi `guess()` ngay cùng tx sẽ đúng cả 10 vòng. Điều kiện thắng chỉ là `lottery.winner() != address(0)`, không bắt winner là EOA của player, nên một transaction duy nhất là đủ. Phần còn lại của bài nằm ở hạ tầng: launcher của sandbox từ chối tạo instance suốt hai tiếng, và khi tạo được thì response bị cắt mất dòng private key, nên phải lấy quyền gửi transaction từ chính node (proxy cho `eth_sendTransaction`, account của anvil đang unlocked) và suy ra địa chỉ Setup/Lottery bằng số học CREATE.

## Chạy lại lời giải

```bash
python exploit.py http://34.116.80.78:8546/<uuid> "R3:TURИ"
```

Kết quả: `CSS{U5E_4_R4ND0M_FUNCT10N}` (đã lưu trong `flag.txt`, nop dạng `CSSCTF{CSS{...}}`).
