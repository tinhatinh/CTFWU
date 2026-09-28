# Kintsugi Vault

The Kintsugi Vault was a key-custody appliance. Instead of keeping its root
custody seed in one place, it broke the seed into a mesh of small guardian
agents and threw away the tooling that put them back together. The appliance is
retired, but its re-attestation endpoint is still answering.

You are handed the raw shard dump and the ground-truth agent runtime. Put the
seed back together and re-attest to unseal.

## Files

- `vmrun` - the guardian agent runtime as a static executable. Given a shard and
  a candidate 8 byte key it reports whether the shard accepts that key. Shards
  that are not the chain start need their decode table supplied as a third file
  argument.
- `*.shard` - the guardian dump. Each file is one agent. File names are content
  ids, not positions. Order on disk means nothing.
- `pubkey.bin` - the vault's public attestation key for your instance.
- `MANIFEST.txt` - names the one agent that is the start of the chain.

## Re-attestation

The live endpoint for your instance:

- `GET /attest` returns a fresh challenge nonce.
- `POST /attest` with form fields `nonce` and `sig` (hex) returns the flag when
  `sig` is a valid attestation over that nonce under your instance public key.

Each nonce is single use.

## Usage

```
./vmrun <shard-file> <16-hex-key> [decode-table-file]
```
