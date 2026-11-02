---
title: "Quiet Upgrade"
category: "Web3"
tags: []
solve_date: "2026-10-31"
language: "en"
---

# Quiet Upgrade

## Challenge

An upgradeable settlement proxy stores its admin and implementation at storage slots 0 and 1. The settlement logic behind the proxy uses the same slots for `branchOperator` and `branchRegistrar`, so registering a branch overwrites the proxy admin. Once the attacker controls the admin slot, they can upgrade to a malicious implementation and drain the treasury. The win condition is the treasury holding less than 1% of its starting reserve, at which point `Setup.isSolved()` returns true and the checker releases the flag.

## Solution

### Step 1: Map the storage collision

- `SettlementProxy` keeps `admin` at slot 0 and `implementation` at slot 1.
- `SettlementV1` is executed by `delegatecall`; its `branchOperator` and `branchRegistrar` variables also live at slots 0 and 1.
- Calling `registerBranch()` writes the attacker-controlled operator address into slot 0, replacing the proxy admin.

### Step 2: Become admin and upgrade

With the admin slot overwritten, call `upgradeTo()` with an attacker implementation that returns:

```
proxiableSlot() = keccak256(QU_TAG, proxy)
```

The proxy accepts the implementation. The malicious implementation calls `treasury.release()` in the proxy's context.

### Step 3: Drain and submit

Drain the treasury until it holds less than 1% of the starting reserve. `Setup.isSolved()` then returns true; submit the flag through the checker.



## Result

```
hiCTF{sl0t0_c0llision_then_a_qu1et_upgrade_0545bd77a4}
```

## Reproduction notes

Reproduction requires the original contract source and instance addresses, including QU_TAG construction, the registerBranch ABI, and treasury setup. The summary does not include a complete deployment script or transaction log.
