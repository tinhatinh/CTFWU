# Genesis — Web3 (Medium)

**Flag:** `H7CTF{346df380-9ca8-41a7-8853-5a6f23c601ad}`
**Files cung cấp:** `GenesisVault.sol`, `Setup.sol`, `Token.sol`

## Đề bài

Hệ thống đưa ra một kịch bản: "Một hầm chứa genesis (genesis vault) vừa được mở cửa sáng nay: một hầm chứa sinh lời hoàn toàn mới tinh, thuộc kiểu đã được các chuyên gia mổ xẻ kiểm toán (audit) tới hàng trăm lần. Một nhà đầu tư cá mập (anchor investor) sắp sửa đổ vào đây một lượng vốn khổng lồ. ... Trước khi dòng tiền của nhà đầu tư này yên vị trong hầm, nhiệm vụ của bạn là hãy chiếm đoạt toàn bộ hầm chứa, và biến số cổ phần của gã cá mập kia thành một con số 0 tròn trĩnh."

Điều kiện phân xử chiến thắng được lập trình cứng trong file `Setup.isSolved()`:

```solidity
victimDeposited && vault.balanceOf(victim) == 0 && token.balanceOf(address(vault)) < 1 ether
```

Đoạn mã này quy định 3 sự kiện phải xảy ra đồng thời: Cá mập (victim) đã thực sự nạp tiền (`victimDeposited`), nhưng gã không hề sở hữu một đồng cổ phần (share) nào (`vault.balanceOf(victim) == 0`), và toàn bộ lượng token nằm trong hầm chứa đã bị rút sạch bách (gần như rỗng, nhỏ hơn 1 ether).

## Phân tích ban đầu

Đào sâu vào `Setup.sol`, định danh của nhà đầu tư cá mập bị đóng chết vào một địa chỉ hằng số:

```solidity
address public constant victim = address(0xC0FFEE);
```

Vì địa chỉ ảo này không phải là một Hợp đồng thông minh (contract), nên chắc chắn không có chuyện một đoạn mã tự động nào đó đứng ra giao dịch với hầm chứa thay cho gã. Thật may, hàm `victimDeposit()` trong `Setup` lại mở toang cánh cửa `external` và không hề bị xích bởi bộ quyền `onlyOwner`. Nhờ thế, người chơi hoàn toàn có quyền vung tay bấm nút "nạp tiền" hộ gã cá mập. Khi hàm `deposit(assets, receiver)` được gọi, nó cho phép chỉ định đối tượng thụ hưởng (receiver), và toàn bộ số share của đợt nạp tiền đó sẽ được chuyển thẳng đứng tên `victim`. Phải hiểu rằng: Đây không phải là lỗ hổng để ta hack, mà đây là cái "công tắc" do tác giả cung cấp để ta điều khiển dòng thời gian diễn ra vụ cướp đúng như kịch bản.

Soi vào cơ chế của Vault, hàm `redeem` (rút tiền) tính toán cổ tức dựa theo tỷ giá hiện hành (spot price). Do đó, hoàn toàn không có khe hở nào để rút khống tài sản:

```solidity
convertToAssets(shares) = shares * reserve / totalSupply
```

Tuy nhiên, hai hàm cốt lõi dưới đây lại chính là bản án tử cho cả hệ thống:

```solidity
function convertToShares(uint256 assets) public view returns (uint256) {
  uint256 supply = totalSupply;
  return supply == 0 ? assets : assets * supply / reserve;   // Lỗi nghiêm trọng: Thiếu hụt virtual offset (bù trừ ảo)
}

function sync() external { reserve = asset.balanceOf(address(this)); }   // Lỗi nghiêm trọng: Hàm mở toang, không kiểm tra quyền (ai cũng gọi được)
```

Hàm `convertToShares` ngây thơ bỏ qua hoàn toàn cơ chế bảo vệ cộng bù trừ (virtual shares/virtual assets) của chuẩn ERC4626. Cùng lúc đó, hàm đồng bộ tài sản `sync()` lại hớ hênh phơi mình ra trước bàn dân thiên hạ. Ghép hai lỗ hổng này lại, ta có trong tay kịch bản hack kinh điển "Làm tròn về số 0" (Inflation Attack): Nếu ta thao túng để tổng cung (`totalSupply`) chỉ là một con số vi mô nhưng tổng dự trữ (`reserve`) lại phình to khổng lồ, thì mọi giao dịch nạp tiền to lớn sau đó khi quy đổi ra share đều sẽ bị chia làm tròn thành số 0 tròn trĩnh.

## Chuỗi khai thác

Toàn bộ vở kịch gồm 4 hồi, triển khai qua 6 giao dịch, tất cả đều được gửi mượt mà từ một tài khoản EOA bình thường, không cần phải đẻ ra bất kỳ contract trung gian nào.

1. **Hồi 1: Gieo hạt giống (Inflation).** 
   Khi hầm chứa Vault vẫn còn hoang vu (`supply == 0`), ta gửi một giao dịch nạp cực nhỏ `deposit(1, player)`. Phép toán `supply == 0 ? assets : ...` lập tức trả về cho ta chính xác 1 wei cổ phần (share). Kết cục: `totalSupply = 1`, con số nhỏ nhất có thể tồn tại trong hệ thống.
2. **Hồi 2: Bơm thổi dự trữ và chốt hạ `sync()`.** 
   Ta ném tàn bạo toàn bộ số token còn lại trong ví thẳng vào hầm chứa (donate), rồi gọi hàm `sync()` để hệ thống cập nhật biến `reserve` gánh trọn phần tài sản hiến tặng đó. Trên môi trường live, `reserve` vọt lên mức `200.000.000.000.000.000.000` trong khi `totalSupply` vẫn kiên cường ở mức `1`. 
   Lúc này, nếu ai đó nạp vào 100 ether, số share quy đổi sẽ là: `convertToShares(100e18) = 100e18 * 1 / 2e20 = 0`. Kịch bản hack đã hiển thị rõ ràng thông báo: "Nếu nạp vào bây giờ, cá mập sẽ nhận được 0 share."
3. **Hồi 3: Trải thảm đón cá mập.** 
   Ta kích hoạt công tắc `setup.victimDeposit()`. Lượng tiền `reserve` của hệ thống dâng lên tới `3e20`. Tuy nhiên, vì bị làm tròn, khoản 100e18 mà gã cá mập vừa ném vào chỉ mang về cho gã đúng 0 share. 
   Thế là xong: Điều kiện `vault.balanceOf(victim) == 0` đã thoả mãn ngay lập tức, và cờ báo `victimDeposited == true` cũng bật sáng.
4. **Hồi 4: Hút cạn hầm chứa.** 
   Cuối cùng, ta gọi lệnh rút tiền `redeem(1, player, player)` để thiêu rụi 1 wei share duy nhất mà ta sở hữu từ bước 1. Phép tính chia `convertToAssets(1) = 1 * reserve / 1` sẽ nôn về toàn bộ tài sản đang có trong kho `reserve`. Biến `reserve` và `totalSupply` lao dốc không phanh về 0, giúp điều kiện thứ ba `token.balanceOf(vault) < 1 ether` cũng được đáp ứng hoàn hảo.

Cấu trúc tài sản (Trạng thái sau mỗi nhịp, được trích xuất từ bảng log của `solve.mjs`):

| Bước thực thi | Dự trữ (reserve) | Tổng cung (supply) | Share (Cá mập) | Token trong kho (vault) | Trạng thái (isSolved) |
| --- | --- | --- | --- | --- | --- |
| Khởi đầu | 0 | 0 | 0 | 0 | Sai (false) |
| Lệnh nạp `deposit(1)` | 1 | 1 | 0 | 1 wei | Sai (false) |
| Bơm tiền + `sync()` | 200,000,000,000,000,000,000 | 1 | 0 | 200 | Sai (false) |
| Bật `setup.victimDeposit()` | 300,000,000,000,000,000,000 | 1 | 0 | 300 | Sai (false) |
| Hút cạn `redeem(1, me, me)` | 0 | 0 | 0 | 0 | Đúng (true) |

## Flag
Kết quả bắn ra từ dòng log cuối của công cụ tấn công (Kích hoạt lệnh `CTF_PK=<private_key_trên_web> node solve.mjs`):

```text
drained    tok(vault)= 0.0000 reserve= 0 supply= 0 share(victim)= 0 share(me)= 0 tok(me)= 300.0000 solved= true
```

Chốt báo cáo `isSolved() = true`, máy chủ ngoan ngoãn dâng cờ thông qua cổng API `GET /flag`:

```text
H7CTF{346df380-9ca8-41a7-8853-5a6f23c601ad}
```

## Phục dựng (Reproduce)

```bash
node solve.mjs
```

Đoạn script này tự động đọc địa chỉ nút mạng (RPC), địa chỉ contract `SETUP` và khoá riêng tư (private key) từ 3 hằng số khai báo ở đầu file. Chỉ cần thay đổi 3 tham số đó là bạn có thể đánh sập bất kỳ instance mục tiêu mới nào.
