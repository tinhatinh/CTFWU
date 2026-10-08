# Genesis - Web3 (Medium)

**Flag:** `H7CTF{346df380-9ca8-41a7-8853-5a6f23c601ad}`
**Files cung cấp:** `GenesisVault.sol`, `Setup.sol`, `Token.sol`

## Đề bài

Hệ thống mô phỏng một kho lưu trữ tài sản (genesis vault) đã qua kiểm duyệt bảo mật. Một nhà đầu tư lớn (anchor investor) dự kiến nạp số vốn lớn vào hầm. Mục tiêu là thao túng hệ thống để rút sạch tài sản, làm cho số dư cổ phần (share) của nhà đầu tư lớn hoàn toàn bằng không.

Điều kiện chiến thắng được định nghĩa trong hàm `Setup.isSolved()`:

```solidity
victimDeposited && vault.balanceOf(victim) == 0 && token.balanceOf(address(vault)) < 1 ether
```

Đoạn mã yêu cầu 3 sự kiện đồng thời: Nhà đầu tư đã thực hiện giao dịch nạp tiền (`victimDeposited`), nhưng không nhận được cổ phần nào (`vault.balanceOf(victim) == 0`), và tổng lượng token trong hầm chứa đã được trích xuất (ít hơn 1 ether).

## Phân tích

Kiểm tra file `Setup.sol`, định danh nhà đầu tư lớn (victim) được cố định vào một địa chỉ:

```solidity
address public constant victim = address(0xC0FFEE);
```

Vì địa chỉ này không phải là Hợp đồng thông minh (smart contract), không có mã tự động giao dịch thay mặt nhà đầu tư. Hàm `victimDeposit()` trong `Setup` sử dụng chỉ thị `external` và không yêu cầu quyền `onlyOwner`, cho phép người chơi gọi trực tiếp hàm này. Hàm `deposit(assets, receiver)` cho phép chỉ định đối tượng nhận cổ phần (`receiver`), qua đó số lượng cổ phần của lần nạp này sẽ ghi nhận cho `victim`. Tính năng này được tác giả thiết kế như một quy trình chuẩn bị kịch bản (setup), không phải là lỗi.

Kiểm tra cơ chế của Vault, hàm `redeem` (rút tiền) tính toán cổ phần theo tỷ lệ lưu trữ, không cho phép rút tài sản trái phép:

```solidity
convertToAssets(shares) = shares * reserve / totalSupply
```

Tuy nhiên, hệ thống có hai lỗi nghiêm trọng trong các hàm cơ sở:

```solidity
function convertToShares(uint256 assets) public view returns (uint256) {
  uint256 supply = totalSupply;
  return supply == 0 ? assets : assets * supply / reserve;   // Lỗi nghiêm trọng: Thiếu cơ chế bù trừ ảo (virtual offset)
}

function sync() external { reserve = asset.balanceOf(address(this)); }   // Lỗi nghiêm trọng: Hàm mở, không kiểm soát quyền truy cập
```

Hàm `convertToShares` không áp dụng cơ chế cộng bù trừ ảo (virtual shares/virtual assets) thường được dùng để giảm rủi ro rounding/inflation trong các implementation ERC4626. Đồng thời, hàm đồng bộ tài sản `sync()` có thể được thực thi bởi bất kỳ người dùng nào. Sự kết hợp của hai lỗi này mở ra phương pháp tấn công lạm phát cổ phần (Inflation Attack): Nếu làm cho tổng cung (`totalSupply`) rất nhỏ trong khi tổng dự trữ (`reserve`) rất lớn, các giao dịch nạp tiền sau đó sẽ bị làm tròn thành 0 khi quy đổi ra cổ phần.

## Lời giải

Quy trình khai thác bao gồm 6 giao dịch, thực hiện tuần tự qua tài khoản EOA, không yêu cầu thiết lập contract trung gian.

1. **Giai đoạn 1: Thiết lập nguồn cung (Inflation).**
   Khi hầm chứa Vault chưa có dữ liệu (`supply == 0`), gửi một giao dịch nạp giá trị tối thiểu `deposit(1, player)`. Phép toán `supply == 0 ? assets : ...` cấp 1 wei cổ phần (share). Kết quả: `totalSupply = 1`, giá trị cung nhỏ nhất.
2. **Giai đoạn 2: Lạm phát dự trữ và đồng bộ hóa `sync()`.**
   Chuyển toàn bộ số token trong ví trực tiếp vào hầm chứa (chuyển qua giao dịch cơ bản), sau đó gọi hàm `sync()`. Hệ thống sẽ cập nhật biến `reserve` gánh thêm toàn bộ tài sản được gửi. Trên hệ thống thật, `reserve` tăng lên `200.000.000.000.000.000.000` trong khi `totalSupply` duy trì mức `1`.
   Lúc này, nếu một giao dịch 100 ether được nạp, số cổ phần quy đổi: `convertToShares(100e18) = 100e18 * 1 / 2e20 = 0`. Mọi khoản nạp tiếp theo đều trả về 0 share.
3. **Giai đoạn 3: Thực thi giao dịch đầu tư.**
   Gọi hàm `setup.victimDeposit()`. `reserve` của hệ thống tăng lên `3e20`. Giao dịch nạp khoản 100e18 bị hệ thống làm tròn và trả về 0 share cho nhà đầu tư.
   Kết quả: Điều kiện `vault.balanceOf(victim) == 0` được thỏa mãn, biến `victimDeposited == true` được cập nhật.
4. **Giai đoạn 4: Trích xuất toàn bộ hầm chứa.**
   Cuối cùng, thực hiện lệnh `redeem(1, player, player)` để thanh lý 1 wei cổ phần sở hữu ở bước 1. Phép tính `convertToAssets(1) = 1 * reserve / 1` trả về toàn bộ tài sản hiện có trong kho `reserve`. Các biến `reserve` và `totalSupply` giảm nhanh chóng về 0, hoàn tất điều kiện thứ ba `token.balanceOf(vault) < 1 ether`.

Cấu trúc tài sản (Trạng thái sau từng thao tác, trích xuất từ `solve.mjs`):

| Bước thực thi | Dự trữ (reserve) | Tổng cung (supply) | Share (Cá mập) | Token trong kho (vault) | Trạng thái (isSolved) |
| --- | --- | --- | --- | --- | --- |
| Khởi đầu | 0 | 0 | 0 | 0 | Sai (false) |
| Lệnh nạp `deposit(1)` | 1 | 1 | 0 | 1 wei | Sai (false) |
| Chuyển tiền + `sync()` | 200,000,000,000,000,000,000 | 1 | 0 | 200 | Sai (false) |
| Gọi `setup.victimDeposit()` | 300,000,000,000,000,000,000 | 1 | 0 | 300 | Sai (false) |
| Hút cạn `redeem(1, me, me)` | 0 | 0 | 0 | 0 | Đúng (true) |

## Kết quả
Kết quả thực thi tự động (sử dụng lệnh `CTF_PK=<private_key> node solve.mjs`):

```text
drained    tok(vault)= 0.0000 reserve= 0 supply= 0 share(victim)= 0 share(me)= 0 tok(me)= 300.0000 solved= true
```

Khi trạng thái `isSolved() = true` được cập nhật, đề cung cấp cờ qua API `GET /flag`:

```text
H7CTF{346df380-9ca8-41a7-8853-5a6f23c601ad}
```

## Tái hiện

```bash
node solve.mjs
```

Script này tự động sử dụng cấu hình node mạng (RPC), địa chỉ contract `SETUP` và private key từ phần khai báo hệ thống. Thay đổi 3 tham số này để thực thi trên các instance mới.
