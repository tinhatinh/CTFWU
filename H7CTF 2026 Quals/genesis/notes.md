# notes.md - Genesis

Điều kiện thắng (`Setup.isSolved`):

```solidity
victimDeposited && vault.balanceOf(victim) == 0 && token.balanceOf(address(vault)) < 1 ether
```

Tức là: anchor đã deposit, họ không còn share nào, và vault gần như rỗng.

## H1 - gọi victim.victimDeposit()
cmd: đọc `Setup.sol:10`
evidence: `address public constant victim = address(0xC0FFEE)` chỉ là một địa chỉ hằng,
không phải contract. `victimDeposit()` nằm trên **Setup**, `external`, không có `onlyOwner`.
result: DEAD với tư cách một bug, nhưng là ý quan trọng: player tự gọi `setup.victimDeposit()`
để kích hoạt khoản deposit 100 gUSD bất cứ lúc nào.

## H2 - rút tiền bằng redeem thường
cmd: đọc `GenesisVault.redeem`
evidence: `convertToAssets(shares) = shares * reserve / totalSupply`, redeem bao nhiêu share
thì nhận đúng bấy nhiêu giá trị; không có cách rút nhiều hơn phần mình sở hữu.
result: DEAD nếu giá không đổi.

## H3 - làm giá đổi bằng donate + sync (ĐÚNG)
cmd: đọc `convertToShares` và `sync`
evidence:
```solidity
function convertToShares(uint256 assets) public view returns (uint256) {
  uint256 supply = totalSupply;
  return supply == 0 ? assets : assets * supply / reserve;   // không có virtual offset
}
function sync() external { reserve = asset.balanceOf(address(this)); }   // ai cũng gọi được
```
Hai chỗ này ghép lại thành bài toán làm tròn: nếu `totalSupply` cực nhỏ còn `reserve` cực lớn
thì một khoản deposit vừa phải nhận về **0 share**.
result: PENDING -> xác nhận ở H4.

## H4 - dựng chuỗi và chạy
cmd: `node solve.mjs`
evidence (in ra từ chính script, từng bước một):

| bước | reserve | supply | share(victim) | tok(vault) | isSolved |
| --- | --- | --- | --- | --- | --- |
| đầu | 0 | 0 | 0 | 0 | false |
| `deposit(1)` | 1 | 1 | 0 | 1 wei | false |
| donate 199999999999999999999 + `sync()` | 200000000000000000000 | 1 | 0 | 200 | false |
| `setup.victimDeposit()` | 300000000000000000000 | 1 | 0 | 300 | false |
| `redeem(1, me, me)` | 0 | 0 | 0 | 0 | **true** |

Trước khi deposit, script in luôn `victim's 100e18 would buy 0 shares` bằng cách gọi
`convertToShares(100e18)` on-chain - tức là dự đoán số share của anchor trước khi để họ vào.
result: OK - `GET /flag` -> `H7CTF{346df380-9ca8-41a7-8853-5a6f23c601ad}`

## Ghi chú
- Không cần contract trung gian: cả 6 transaction đều là EOA thường.
- `deposit(assets, receiver)` cho phép chỉ định receiver, nên anchor nhận share vào đúng
  địa chỉ `victim` mà Setup mong đợi.
- donate trực tiếp bằng `token.transfer(vault, ...)` không làm `reserve` đổi nếu không gọi
  `sync()`; chính `sync()` mới nhét khoản donate vào giá.
