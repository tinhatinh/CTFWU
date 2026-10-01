# Gateway — Notes

## Hypothesis log

1. **Gate nc is ethernaut-style instance factory** → verified: each action `launch/kill/get_flag` = separate TCP connection, server closes socket immediately after reply.

2. **Password in storage slot 1** → verified via `eth_getStorageAt(gate, 1)` == `keccak256("gateway to the flag")`.

3. **tx.origin trap requires intermediary contract** → Breaker.sol deploy + run() bypasses requirement.

4. **Ether payment triggers receive()** → confirmed: (bool ok, ) = address(gate).call{value: 1 ether}("") sets funded=true.

5. **Flag binding is ticket-based, not IP-based** → teammate can launch from different IP, other person exploits over RPC proxy, final `3 + ticket` works from anywhere.

## Commands executed

```bash
# Launch credentials retrieval
python gateway.py '["1","R3:TURИ"]'
# Output: uuid/rpc endpoint/private key/setup contract

# Deploy Breaker
export CSS_RPC=http://34.116.80.78:8545/47c4a887-8b71-4b92-aa4d-eea88f7669f2
export CSS_PK=d5c7492813f0829fc5534896e58179c3b618c6227b9c5df38f5d2b1aba6ba206
python exploit.py files/Gate.sol

# Get flag
python gateway.py '["3","R3:TURИ"]'
# Output: CSS{B451C_BL0CKCH41N_5K1LL5}
```

## Edge cases observed

- Server crashes on repeated `launch` within cooldown period → `JSONDecodeError` at launcher.py:99
- Instance already running prevents credential dump → must kill first
- Private key sent via env var only, never hardcoded
- Mainnet fork (chainId 1) vs usual testnets (chainId 31337)

## Timeline

- 2026-10-01: Instance launched, Breaker deployed, flag obtained
- Status: solved by R3:TURИ, instance auto-terminates after 30 minutes
