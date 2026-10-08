# Genesis - Web3 (Medium)

**Flag:** `H7CTF{346df380-9ca8-41a7-8853-5a6f23c601ad}`
**Files:** `GenesisVault.sol`, `Setup.sol`, `Token.sol`

## Challenge

"genesis vault opened this morning: a fresh yield vault, the sort that's been audited a hundred
times over. a big anchor investor is about to move in with a very large stake.... by the time the
anchor's deposit settles, own the vault outright and leave their stake worth exactly nothing."

The win condition in `Setup.isSolved()`:

```solidity
victimDeposited && vault.balanceOf(victim) == 0 && token.balanceOf(address(vault)) < 1 ether
```

That is, three things must happen at once: the anchor has deposited, they hold no shares, and the vault is nearly
empty.

## Analysis

`Setup.sol` defines the anchor with a constant address:

```solidity
address public constant victim = address(0xC0FFEE);
```

The source uses this fixed address to identify the anchor. Yet `Setup` exposes
`victimDeposit()` as `external`, with no `onlyOwner`, meaning the player can call it on the anchor's behalf, and
`deposit(assets, receiver)` lets you name the receiver, so the shares of that deposit are credited straight to
`victim`. This is not a bug to exploit, but the switch that triggers exactly the timing sequence the challenge
describes.

On the vault side, `redeem` divides at the current price, so there is no way to withdraw more than your share:

```solidity
convertToAssets(shares) = shares * reserve / totalSupply
```

The remaining two functions are the solution:

```solidity
function convertToShares(uint256 assets) public view returns (uint256) {
  uint256 supply = totalSupply;
  return supply == 0 ? assets : assets * supply / reserve;   // no virtual offset
}

function sync() external { reserve = asset.balanceOf(address(this)); }   // anyone can call it
```

`convertToShares` adds no virtual shares/virtual assets as some ERC4626 implementations do to mitigate rounding/inflation risk, and `sync()` sits outside
owner control. Together they make a rounding puzzle: keep `totalSupply` extremely small while `reserve` is extremely
large, and a very large deposit converts to 0 shares.

## Solution

Four beats, and all six transactions are sent from a plain EOA, no intermediary contract needed.

1. **Plant the seed.** The vault is still empty (`supply == 0`), so `deposit(1, player)` yields exactly 1 wei of
   share: `supply == 0 ? assets : ...`. The result is `totalSupply = 1`, the smallest possible.
2. **Flood the reserve, then call `sync()`.** Transfer all the tokens you have left into the vault and call
   `sync()` so `reserve` picks up the donation. On this instance `reserve = 200000000000000000000` while
   `totalSupply = 1`, so `convertToShares(100e18)` = `100e18 * 1 / 2e20` = 0. The script prints that prediction before
   letting the anchor in, and the number printed is 0.
3. **Invite the anchor.** Call `setup.victimDeposit()`. `reserve` rises to `3e20`, but the anchor's 100e18 still
   buys 0 shares, so `vault.balanceOf(victim) == 0` is satisfied from the start, and
   `victimDeposited == true`.
4. **Collapse the vault.** `redeem(1, player, player)` burns the single share and takes back the whole `reserve`,
   because `convertToAssets(1) = 1 * reserve / 1`. `reserve` and `totalSupply` go to 0, and the condition
   `token.balanceOf(vault) < 1 ether` holds too.

State after each step, taken from the output of `solve.mjs`:

| step | reserve | supply | share(victim) | tok(vault) | isSolved |
| --- | --- | --- | --- | --- | --- |
| start | 0 | 0 | 0 | 0 | false |
| `deposit(1)` | 1 | 1 | 0 | 1 wei | false |
| donate + `sync()` | 200000000000000000000 | 1 | 0 | 200 | false |
| `setup.victimDeposit()` | 300000000000000000000 | 1 | 0 | 300 | false |
| `redeem(1, me, me)` | 0 | 0 | 0 | 0 | true |

## Result
The last line of `CTF_PK=<private key from GET /> node solve.mjs` (the `show()` function prints the state after each transaction):

```
drained    tok(vault)= 0.0000 reserve= 0 supply= 0 share(victim)= 0 share(me)= 0 tok(me)= 300.0000 solved= true
```

`isSolved()` is true by now, so the instance hands the flag back through `GET /flag`:

```
H7CTF{346df380-9ca8-41a7-8853-5a6f23c601ad}
```

## Reproduce

```
node solve.mjs
```

The script reads the RPC, `SETUP` and the instance's private key from three constants at the top of the file; change
those three values and it runs against a fresh instance.
