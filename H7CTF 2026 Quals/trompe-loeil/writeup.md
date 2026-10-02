# Trompe-l'œil — Web3 (Hard)

**Flag:** `H7CTF{0bba5486-eebc-4ee8-a3de-a55e80c787f1}`
**File cung cấp:** Gồm `Setup.sol`, `Pool.sol`, `MirrorLend.sol`, `Token.sol`, `IERC20.sol` (Chạy trên nền Solidity 0.8.24)

## Đề bài

Hệ thống cho vay MirrorLend phát hành mã thông báo mUSD và yêu cầu thế chấp bằng mã thông báo LP (LP token) lấy từ một bể chứa (pool) có tên là Mirror. Tài liệu mô tả tính chính xác của hệ thống, đồng thời gợi ý: "Một bức tranh trompe-l'œil (ảo ảnh thị giác) chỉ trông có vẻ thật khi người ta vẫn còn đang chú ý vào chi tiết". 
Điều kiện hoàn thành được xác định trong hàm `Setup.isSolved()`:

```solidity
lend.totalDebt() > lend.totalCollateralLP() * pool.get_virtual_price() / 1e18
```

Môi trường chiến đấu là một node EVM độc lập: Truy vấn GET / tới URL sẽ nhận về rpc endpoint (yêu cầu gửi yêu cầu POST lại cùng URL), mã mạng chain id 31337, khoá riêng tư (private key) và địa chỉ bộ cài Setup. API không yêu cầu xác thực. Lấy cờ bằng lệnh `GET /flag`.

## Phân tích ban đầu

Điều kiện bất đẳng thức này có 2 con đường để thay đổi trạng thái: một là làm cho tổng nợ (`totalDebt`) tăng nhanh hơn khối tài sản thế chấp, hai là thay đổi hệ thống làm giảm giá ảo (`get_virtual_price()`) ngay SAU KHI đã vay tiền xong. 
Con đường thứ hai là không khả thi. Vì tài sản của Pool chỉ rút tài sản qua hàm `removeLiquidity`, hàm này chia đều tỷ lệ `lp/totalSupply` cho cả hai loại tài sản -> Dẫn tới giá ảo không thay đổi. Nếu đem tiền đi chuyển trực tiếp thì chỉ làm giá ảo tăng tỷ lệ vĩnh viễn chứ không hẹp lại.
Kết luận: Chỉ có thể thay đổi cho giá ảo tăng tạm thời trong quá trình lệnh vay `borrow()` đang chạy.

Hàm `MirrorLend.borrow` không lưu cache, nó gọi trực tiếp hàm `pool.get_virtual_price()`:

```solidity
uint256 maxDebt = collateralLP[msg.sender] * pool.get_virtual_price() / 1e18;
```

Khai thác: Chỉ cần thay đổi tỷ giá ảo trong quá trình này.

## Chuỗi khai thác

**Bước 1 - Phân tích lỗ hổng trong hàm `removeLiquidity`.** 
Lỗ hổng logic xuất hiện ở đây: Hệ thống tiến hành hủy (burn) LP và hoàn trả ETH trả trước, nhưng chuyển token sau.

```solidity
uint256 ethOut   = address(this).balance * lp / totalSupply;
uint256 tokenOut = token.balanceOf(address(this)) * lp / totalSupply;
balanceOf[msg.sender] -= lp;
totalSupply -= lp;                        // Lỗ hổng: Mẫu số đã giảm
(bool ok, ) = msg.sender.call{value: ethOut}("");   // <- Hàm callback kích hoạt
require(token.transfer(msg.sender, tokenOut));      // Lỗi logic: Tử số chưa được trừ đi phần token
```

Ngay tại nhịp chạy callback, lệnh `get_virtual_price()` sẽ thực hiện phép tính `(Lượng ETH đã giảm + Lượng token CHƯA HỀ bị giảm) / (Tổng cung supply đã giảm)`. 
Đối với những pool đang cân bằng 50/50, thì sai số giá vẫn rất nhỏ. Nhưng, nếu ta thay đổi tỷ lệ dự trữ của pool đó, thì lượng token chưa chuyển đi sẽ tính vào tổng cung, làm giá ảo tăng lên bất thường.

**Bước 2 - Làm lệch cán cân pool bằng gửi token không tỷ lệ.** 
Hàm `addLiquidity` cho phép gán `msg.value = 0` (không gửi ETH) nhưng tính toán tỷ lệ vẫn thực hiện:

```javascript
pool.addLiquidity(100n * 10n ** 18n)   // Không gửi kèm ETH
```

Lúc này, cái pool thay đổi thành: 10 ETH + 110 mUSD, tổng cung `totalSupply = 120`. Giá ảo thì vẫn giữ nguyên ở mức `1e18`. Quá trình này trả về 100 LP.

**Bước 3 - Chia lượng LP: Sử dụng một nửa để thế chấp, một nửa để rút thanh khoản.** 
Gửi `deposit(50)` vào kho MirrorLend, sau đó gọi lệnh `removeLiquidity(50)` từ một smart contract chứa hàm callback `receive()`. Ở khoảnh khắc callback diễn ra:

```text
ethOut  = tính ra 10 * 50/120 = 4.1667
tỷ giá ảo sau khi thay đổi = (10 - 4.1667 + 110) / (120 - 50) = 115.8333 / 70 = 1.6547619e18
```

Hàm `borrow()` tính toán với tỷ giá ảo hiện tại, cho phép vay lượng tài sản lớn `50 * 1.6547619 = 82.73809523809524` mUSD từ quỹ dự trữ 1000 mUSD. Sau khi callback hoàn tất, phần token được chuyển, tỷ giá ảo trở về mức `1e18`.

**Bước 4 - Kiểm chứng độc lập.** 
Kết quả tính toán trên được xác nhận qua thông số on-chain: Con số `82.73809523809524` tương đương với tính toán `50 * 115.8333.../70` xác định từ trạng thái on-chain (file `analysis/state.mjs` ghi nhận log `pool eth 10, pool tok 10, totalSupply 20, vprice 1`). Kết thúc giao dịch, kiểm tra thông số mạng:

```text
vprice 1  totalDebt 82.73809523809524  collateralValue 50  isSolved true
```

Kết luận: Tổng nợ đã lớn hơn 1.65 lần tài sản thế chấp, và khoản chênh lệch không thể được thu hồi do hệ thống thiếu hàm trả nợ (repay).

## Flag
```bash
CTF_PK=<thay thế bằng private key từ GET /> node exploit.mjs
```

Kết quả thực thi:
```text
deploying attack... (Triển khai mã khai thác)
attack 0xdD9751bB819BAcE6A3dDEA42a8438a23E4177ab4 tiêu thụ gas 490730n
funding 100 mUSD -> chuyển token vào 0xdD9751bB819BAcE6A3dDEA42a8438a23E4177ab4
running exploit... (Thực thi khai thác)
tx 0xbdeb34ea80abc37718a37da731d78cf8aa42d49a081fad044578b25ecc78bdf7 trả về status 1 tiêu thụ gas 272050n
vprice 1 totalDebt 82.73809523809524 collateralValue 50
isSolved true (Xác nhận điều kiện thắng)
```

```text
H7CTF{0bba5486-eebc-4ee8-a3de-a55e80c787f1}
```
