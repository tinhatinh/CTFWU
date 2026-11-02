---
title: "Standing Order"
category: "Web3"
tags: []
solve_date: "2026-10-31"
language: "en"
---

# Standing Order

## Challenge

A grant program pays out against committee-signed vouchers. Two redemption paths share the same `(amount, nonce)` signature check: `redeem` (onboarding) and `disburse` (committee path). The onboarding voucher is 1 ETH with nonce 0, and `disburse` makes the external call before marking the voucher used, so the voucher can be replayed through `disburse` in a reentrancy loop. Draining the program below 1% of its reserve makes `isSolved()` true and releases the flag.

## Solution

### Step 1: Inspect the deployed contracts

The setup contract and the `GrantProgram` were recovered from the instance:

- Setup: `0x66977ca8d525A4B51a851Cbda5d1fb44Bfb322aC`
- GrantProgram: `0x40676c7618d9F9F62e02e6E67cD0c18b47EeE086`
- Voucher: `amount = 1 ether`, `nonce = 0`, signed by the committee.
- Digest: `keccak256(abi.encode(1 ether, 0))`, signed under the standard Ethereum signed-message prefix.

### Step 2: Identify the order-of-operations bug

The two selectors have the same ABI `(address to, uint256 amount, uint256 nonce, bytes sig)`:

- `0x31d1299d` (onboarding): checks the signature, sets `voucherUsed[digest] = true`, then transfers. Safe.
- `0x7c05469e` (`disburse`): performs the ETH `CALL` at pc `0x477` and only afterwards writes `voucherUsed[digest] = true` at pc `0x503`. Reentrant.

The digest binds only `(amount, nonce)`, not the recipient or the execution path, so the onboarding voucher can be used with `disburse` and an attacker-controlled `to`.

### Step 3: Reenter and drain

`StandingOrderExploit` calls `disburse(address(this), 1 ether, 0, sig)`. Its `receive()` reenters while the program still holds at least 1 ETH; 20 recursive withdrawals empty the 20 ETH reserve. `isSolved()` requires the program balance to fall below `RESERVE/100 = 0.2 ETH`, which is satisfied (balance 0).

- Deploy tx: `0xd4f2f26cb3c91efeeef62bd190fc44de3758112a986d1663117b380a2d6021d0`
- Attack tx: `0x7c316486601a2b272de36e97fe352c4bf33a34af1625fdf9f6a7864b23fc3867` (374,966 gas)
- Result: `GrantProgram.balance = 0`, `isSolved() = true`.



## Result

```
hiCTF{one_sig_two_paths_then_the_l00p_a0f353c92e}
```

## Reproduction notes

The addresses and signature belong to the recorded instance; obtain fresh instance values for reproduction.
