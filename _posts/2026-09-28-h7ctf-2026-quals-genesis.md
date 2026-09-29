---
title: "Genesis — Web3 (Medium)"
date: 2026-09-28 18:32:57 +0700
lastmod_at: 2026-09-28 18:32:57 +0700
categories: [Web3]
tags: [h7ctf-quals, Web3]
image:
  path: /CTFWU/H7CTF%202026%20Quals/genesis/files/de.png
---
**Flag:** `H7CTF{346df380-9ca8-41a7-8853-5a6f23c601ad}`
**Files:** `GenesisVault.sol`, `Setup.sol`, `Token.sol`

## Đề bài

"genesis vault opened this morning: a fresh yield vault, the sort that's been audited a hundred
times over. a big anchor investor is about to move in with a very large stake. ... by the time the
anchor's deposit settles, own the vault outright and leave their stake worth exactly nothing."

Điều kiện thắng trong `Setup.isSolved()`:

```solidity
victimDeposited && vault.balanceOf(victim) == 0 && token.balanceOf(address(vault)) < 1 ether
```

Tức là ba thứ phải xảy ra cùng lúc: anchor đã deposit, họ không giữ share nào, và vault gần như
rỗng.

## Phân tích ban đầu

`Setup.sol` định nghĩa anchor bằng một địa chỉ hằng:

```solidity
address public constant victim = address(0xC0FFEE);
```

Địa chỉ này không phải contract, nên không có code nào tự tương tác với vault thay anchor. Nhưng
`Setup` lại expose `victimDeposit()` là `external`, không kèm `onlyOwner`, nghĩa là người chơi tự
gọi hộ anchor được, và `deposit(assets, receiver)` cho phép chỉ định receiver, nên số share của
đợt deposit đó ghi thẳng vào `victim`. Đây không phải lỗi cần khai thác, mà là công tắc để kích
hoạt đúng nhịp thời gian mà đề bài mô tả.

Về phía vault, `redeem` chia theo giá hiện hành nên không có đường rút non phần:

```solidity
convertToAssets(shares) = shares * reserve / totalSupply
```

Hai hàm còn lại mới là lời giải:

```solidity
function convertToShares(uint256 assets) public view returns (uint256) {
  uint256 supply = totalSupply;
  return supply == 0 ? assets : assets * supply / reserve;   // không có virtual offset
}

function sync() external { reserve = asset.balanceOf(address(this)); }   // ai cũng gọi được
```

`convertToShares` không cộng virtual shares/virtual assets như ERC4626 tham chiếu, và `sync()` để
ngoài quyền chủ sở hữu. Ghép lại thành một bài làm tròn: giữ `totalSupply` cực nhỏ trong khi
`reserve` cực lớn thì một khoản deposit rất to quy về 0 share.

## Các hướng đã loại

1. Rút bằng `redeem` thường khi giá chưa đổi: mỗi share nhận đúng `reserve/totalSupply` của nó,
   không lấy được phần của người khác.
2. Chặn anchor bằng cách gọi `victimDeposit()` trước: vô nghĩa, vì điều kiện thắng đòi
   `victimDeposited == true`.
3. donate trực tiếp bằng `token.transfer(vault, amount)`: số dư ví tăng nhưng `reserve` không đổi
   nếu thiếu `sync()`, nên giá share đứng nguyên.

## Chuỗi khai thác

Bốn nhịp, cả sáu transaction đều gửi từ EOA thường, không cần contract trung gian.

1. **Gửi hạt giống.** Vault còn trống (`supply == 0`), nên `deposit(1, player)` cho ra đúng 1 wei
   share: `supply == 0 ? assets : ...`. Kết quả là `totalSupply = 1`, nhỏ nhất có thể.
2. **Bơm dự trữ rồi gọi `sync()`.** Chuyển toàn bộ số token còn lại của mình vào vault và gọi
   `sync()` để `reserve` nhận phần donate. Với instance này `reserve = 200000000000000000000`
   trong khi `totalSupply = 1`, nên `convertToShares(100e18)` = `100e18 * 1 / 2e20` = 0. Script in
   câu dự đoán đó ra trước khi để anchor vào, và con số in ra là 0.
3. **Mời anchor.** Gọi `setup.victimDeposit()`. `reserve` lên `3e20` nhưng 100e18 của anchor vẫn
   đổi lấy 0 share, nên `vault.balanceOf(victim) == 0` thỏa ngay từ đầu, và
   `victimDeposited == true`.
4. **Thu gọn vault.** `redeem(1, player, player)` đốt 1 share duy nhất, nhận về toàn bộ `reserve`,
   vì `convertToAssets(1) = 1 * reserve / 1`. `reserve` và `totalSupply` về 0, điều kiện
   `token.balanceOf(vault) < 1 ether` cũng đúng.

Trạng thái sau từng bước, lấy từ output của `solve.mjs`:

| bước | reserve | supply | share(victim) | tok(vault) | isSolved |
| --- | --- | --- | --- | --- | --- |
| đầu | 0 | 0 | 0 | 0 | false |
| `deposit(1)` | 1 | 1 | 0 | 1 wei | false |
| donate + `sync()` | 200000000000000000000 | 1 | 0 | 200 | false |
| `setup.victimDeposit()` | 300000000000000000000 | 1 | 0 | 300 | false |
| `redeem(1, me, me)` | 0 | 0 | 0 | 0 | true |

## Flag
Dòng cuối của `CTF_PK=<private key trong GET /> node solve.mjs` (hàm `show()` in trạng thái sau mỗi transaction):

```
drained    tok(vault)= 0.0000 reserve= 0 supply= 0 share(victim)= 0 share(me)= 0 tok(me)= 300.0000 solved= true
```

`isSolved()` đã true nên instance trả cờ qua `GET /flag`:

```
H7CTF{346df380-9ca8-41a7-8853-5a6f23c601ad}
```

## Reproduce

```
node solve.mjs
```

Script đọc RPC, `SETUP` và private key của instance từ ba hằng ở đầu file; đổi ba giá trị đó là
chạy được trên instance mới.
