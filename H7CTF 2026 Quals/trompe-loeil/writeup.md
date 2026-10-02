# Trompe-l'œil — Web3 (Hard)

**Flag:** `H7CTF{0bba5486-eebc-4ee8-a3de-a55e80c787f1}`
**File cung cấp:** Gồm `Setup.sol`, `Pool.sol`, `MirrorLend.sol`, `Token.sol`, `IERC20.sol` (Chạy trên nền Solidity 0.8.24)

## Đề bài

Hệ thống cho vay MirrorLend bơm tiền mUSD và yêu cầu thế chấp bằng mã thông báo LP (LP token) lấy từ một bể chứa (pool) phong cách Curve có tên là Mirror. Tác giả tự tin vỗ ngực rằng "sổ sách khớp đến từng đồng", đồng thời buông lời ẩn ý: "Một bức tranh trompe-l'œil (ảo ảnh thị giác) chỉ trông có vẻ thật khi người ta vẫn còn đang trố mắt nhìn vào nó". 
Giấy chứng nhận chiến thắng bị trói vào hàm `Setup.isSolved()`:

```solidity
lend.totalDebt() > lend.totalCollateralLP() * pool.get_virtual_price() / 1e18
```

Môi trường chiến đấu là một node EVM độc lập: Quất lệnh `GET /` thẳng vào URL sẽ nhận về rpc endpoint (yêu cầu đâm POST lại cùng URL), mã mạng chain id 31337, khoá riêng tư (private key) của người chơi và địa chỉ bộ cài Setup. Cửa mở toang không đòi hỏi bất kỳ xác thực phiền nhiễu nào. Húp xong cờ thì vã lệnh `GET /flag`.

## Phân tích ban đầu

Bài toán bất đẳng thức sinh tử này chỉ có 2 con đường để lật ngược thế cờ: một là bóp méo cho tổng nợ (`totalDebt`) bành trướng nhanh hơn khối tài sản thế chấp, hai là đục thủng hệ thống làm sập giá ảo (`get_virtual_price()`) ngay SAU KHI đã vay tiền xong. 
Con đường thứ hai là bất khả thi (vô vọng). Vì tài sản của Pool chỉ chịu chui ra ngoài qua cái hố `removeLiquidity`, mà cái hố này lại cưa đều tỷ lệ `lp/totalSupply` cho cả hai loại tài sản -> Dẫn tới giá ảo đứng trơ như đá. Nếu đem tiền đi quyên góp (bơm trực tiếp) thì chỉ làm giá ảo phình to vĩnh viễn chứ không hẹp lại.
Kết luận đanh thép: Chỉ còn cách phù phép (thổi) cho giá ảo tăng khống TẠM THỜI vào ĐÚNG cái khoảnh khắc mà lệnh vay `borrow()` đang chạy.

Lệnh vay `MirrorLend.borrow` lại lười biếng không hề dùng bộ nhớ đệm (cache) nào cả, nó chạy sang gõ cửa thẳng mặt hàm `pool.get_virtual_price()`:

```solidity
uint256 maxDebt = collateralLP[msg.sender] * pool.get_virtual_price() / 1e18;
```

Cơ hội bằng vàng: Ta chỉ cần đúng một tích tắc để chọc cho giá ảo vút lên trời.

## Chuỗi khai thác

**Bước 1 - Tìm điểm nút sinh tử trong hang ổ `removeLiquidity`.** 
Lỗ hổng (lỗi) chí mạng lòi ra đây: Hệ thống tiến hành thiêu rụi (burn) LP và vãi tiền ETH trả trước, nhưng lại ngâm lại tiền token trả sau.

```solidity
uint256 ethOut   = address(this).balance * lp / totalSupply;
uint256 tokenOut = token.balanceOf(address(this)) * lp / totalSupply;
balanceOf[msg.sender] -= lp;
totalSupply -= lp;                        // Gót Achilles: Mẫu số đã bị bào mòn (giảm)
(bool ok, ) = msg.sender.call{value: ethOut}("");   // <- Hàm gọi ngược (callback) chui thẳng vào tay kẻ tấn công
require(token.transfer(msg.sender, tokenOut));      // Ngang trái: Tử số lại CHƯA kịp trừ phần token
```

Ngay tại nhịp chạy callback, lệnh `get_virtual_price()` sẽ ngây thơ hốt phép tính `(Lượng ETH đã giảm + Lượng token CHƯA HỀ bị giảm) / (Tổng cung supply đã giảm)`. 
Đối với những cái pool đang nằm im ở thế cân bằng 50/50, thì sai số giá vẫn chỉ xấp xỉ nhỏ xíu. Nhưng, nếu ta ép cái pool đó nghiêng hẳn (lệch) về phía token, thì cục token đang chờ kia sẽ biến thành một khối bướu bị đếm khống (đếm 2 lần), làm giá ảo phình to điên rồ.

**Bước 2 - Làm lệch cán cân pool bằng trò nạp chay token.** 
Cửa nạp `addLiquidity` lỏng lẻo cho phép ta cắm `msg.value = 0` (không nhồi ETH) mà vẫn ngoan ngoãn chia tỷ lệ giá trị công bằng, nên chả mất đồng nào:

```javascript
pool.addLiquidity(100n * 10n ** 18n)   // Bơm chay không kèm một cắc ETH nào
```

Lúc này, cái pool bị biến dạng thành: 10 ETH + 110 mUSD, tổng cung `totalSupply = 120`. Giá ảo thì vẫn khư khư ở mốc đúng `1e18`. Cú lướt này mang về cho ta 100 LP.

**Bước 3 - Cưa đôi LP: Xẻ một nửa đem đi thế chấp, nửa còn lại tống vào lò đốt.** 
Rót `deposit(50)` vào kho MirrorLend, sau đó bồi lệnh `removeLiquidity(50)` từ một cái contract có trang bị hàm hứng đạn `receive()`. Ở khoảnh khắc callback diễn ra:

```text
ethOut  = tính ra 10 * 50/120 = 4.1667
giá ảo  bị thổi = (10 - 4.1667 + 110) / (120 - 50) = 115.8333 / 70 = 1.6547619e18
```

Hàm `borrow()` mù loà nhìn thấy cái giá ốp-la đó, nên hào phóng mở kho cho phép ta húp nợ `50 * 1.6547619 = 82.73809523809524` mUSD từ cục dự trữ (reserve) khổng lồ 1000 mUSD. Sau khi sóng gió callback qua đi, phần token mới được chuyển rốt ráo, giá ảo lại xẹp về cái mốc đúng `1e18`.

**Bước 4 - Khâu tự vấn (Kiểm chứng tính đúng đắn).** 
Những con số điên rồ ở trên hoàn toàn không phải là đống suy luận suông sau khi nhắm mắt chạy bừa: Con số `82.73809523809524` ăn khớp 100% với phép nhẩm tay `50 * 115.8333.../70` tính từ cái trạng thái on-chain thô lôi ra trước đó (Bằng chứng: file `analysis/state.mjs` hắt ra dòng log `pool eth 10, pool tok 10, totalSupply 20, vprice 1`). Kết thúc giao dịch, soi ngược lại từ chain:

```text
vprice 1  totalDebt 82.73809523809524  collateralValue 50  isSolved true
```

Tàn cuộc: Nợ đã phình to gấp 1.65 lần tài sản thế chấp, và khoản chênh lệch thâm hụt đó trở thành hố đen không thể đòi lại vì trong thiết kế của bài, cái hệ thống MirrorLend khốn khổ này chả hề được trang bị hàm trả nợ (repay) nào cả.

## Flag
```bash
CTF_PK=<nhét private key bốc từ GET / vào đây> node exploit.mjs
```

Khói súng:
```text
deploying attack... (Thả mã độc)
attack 0xdD9751bB819BAcE6A3dDEA42a8438a23E4177ab4 cắn gas 490730n
funding 100 mUSD -> bơm vào 0xdD9751bB819BAcE6A3dDEA42a8438a23E4177ab4
running exploit... (Đục khoét)
tx 0xbdeb34ea80abc37718a37da731d78cf8aa42d49a081fad044578b25ecc78bdf7 nhả status 1 cắn gas 272050n
vprice 1 totalDebt 82.73809523809524 collateralValue 50
isSolved true (Điều kiện thắng: MỞ)
```

```text
H7CTF{0bba5486-eebc-4ee8-a3de-a55e80c787f1}
```
