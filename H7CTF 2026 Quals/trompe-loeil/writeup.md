# Trompe-l'œil — Web3 (Hard)

**Flag:** `H7CTF{0bba5486-eebc-4ee8-a3de-a55e80c787f1}` · Files: `Setup.sol`, `Pool.sol`, `MirrorLend.sol`, `Token.sol`, `IERC20.sol` (Solidity 0.8.24)

## Đề bài

MirrorLend cho vay mUSD thế chấp bằng LP token của một pool Curve-style tên Mirror. Đề khẳng định "sổ sách khớp hết" và gợi ý: một bức tranh trompe-l'œil chỉ cần thật chừng nào người ta còn nhìn vào nó. Điều kiện thắng là `Setup.isSolved()`:

```solidity
lend.totalDebt() > lend.totalCollateralLP() * pool.get_virtual_price() / 1e18
```

Instance là một node EVM: `GET /` trên chính URL bài trả về rpc endpoint (POST cùng URL), chain id 31337, private key của player và địa chỉ Setup, không cần xác thực gì thêm. Solve xong thì `GET /flag`.

## Phân tích ban đầu

Bất đẳng thức thắng chỉ đổi dấu theo hai cách: làm `totalDebt` tăng nhanh hơn giá trị thế chấp, hoặc làm `get_virtual_price()` tụt sau khi đã vay. Vế thứ hai vô vọng vì tài sản của Pool chỉ ra khỏi nó qua `removeLiquidity`, và hàm đó chia đúng tỷ lệ `lp/totalSupply` cho cả hai loại tài sản nên giá không đổi; quyên góp trực tiếp thì chỉ làm giá tăng vĩnh viễn. Vậy phải khiến giá cao giả tạm thời đúng lúc `borrow()` chạy.

`MirrorLend.borrow` không dùng cache nào, nó gọi thẳng `pool.get_virtual_price()`:

```solidity
uint256 maxDebt = collateralLP[msg.sender] * pool.get_virtual_price() / 1e18;
```

Nên chỉ cần một khoảnh khắc mà giá ảo bị thổi lên.

## Chuỗi khai thác

**Bước 1 - Tìm khoảnh khắc đó trong `removeLiquidity`.** Đây là lỗi: burn LP và trả ETH trước, trả token sau.

```solidity
uint256 ethOut   = address(this).balance * lp / totalSupply;
uint256 tokenOut = token.balanceOf(address(this)) * lp / totalSupply;
balanceOf[msg.sender] -= lp;
totalSupply -= lp;                        // mẫu số đã giảm
(bool ok, ) = msg.sender.call{value: ethOut}("");   // <- callback của đối tượng tấn công
require(token.transfer(msg.sender, tokenOut));      // tử số chưa trừ phần token
```

Trong callback, `get_virtual_price()` lấy `(ETH đã giảm + token CHƯA giảm) / (supply đã giảm)`._pool nào cân bằng 50/50 thì giá vẫn đúng xấp xỉ, nhưng pool lệch về phía token sẽ phóng to phần bị đếm hai lần.

**Bước 2 - Làm pool lệch bằng cách nạp chỉ-token.** `addLiquidity` cho phép `msg.value = 0` và vẫn tính giá công bằng, nên không lỗ gì:

```js
pool.addLiquidity(100n * 10n ** 18n)   // không kèm ETH
```

Pool thành 10 ETH + 110 mUSD, `totalSupply = 120`, giá vẫn đúng `1e18`. Ta giữ 100 LP.

**Bước 3 - Chia LP: một nửa thế chấp, một nửa đem đốt.** `deposit(50)` vào MirrorLend, rồi `removeLiquidity(50)` từ một contract có `receive()`. Trong callback:

```
ethOut  = 10 * 50/120 = 4.1667
giá ảo  = (10 - 4.1667 + 110) / (120 - 50) = 115.8333 / 70 = 1.6547619e18
```

`borrow()` thấy giá đó nên cho phép vay `50 * 1.6547619 = 82.73809523809524` mUSD từ reserve 1000 mUSD. Callback trả về, phần token được chuyển đi, giá về đúng `1e18`.

**Bước 4 - Kiểm chứng tính đúng.** Các con số không phải suy luận sau khi chạy: `82.73809523809524` đúng bằng `50 * 115.8333.../70` tính tay từ trạng thái on-chain đọc trước đó (`analysis/state.mjs` in ra `pool eth 10, pool tok 10, totalSupply 20, vprice 1`). Sau transaction, đọc lại từ chain:

```
vprice 1  totalDebt 82.73809523809524  collateralValue 50  isSolved true
```

Nợ gấp 1.65 lần giá trị thế chấp, và phần chênh không thể bị đòi lại vì MirrorLend không có hàm repay nào trong đề bài.

## Flag
```bash
CTF_PK=<private key trong GET /> node exploit.mjs
```

```
deploying attack...
attack 0xdD9751bB819BAcE6A3dDEA42a8438a23E4177ab4 gas 490730n
funding 100 mUSD -> 0xdD9751bB819BAcE6A3dDEA42a8438a23E4177ab4
running exploit...
tx 0xbdeb34ea80abc37718a37da731d78cf8aa42d49a081fad044578b25ecc78bdf7 status 1 gas 272050n
vprice 1 totalDebt 82.73809523809524 collateralValue 50
isSolved true
```

```
H7CTF{0bba5486-eebc-4ee8-a3de-a55e80c787f1}
```
