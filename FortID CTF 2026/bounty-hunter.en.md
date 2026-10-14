---
title: "Bounty Hunter"
category: "Crypto"
tags: ["pcs", "polyfold", "commitment-binding", "degree-check", "argument-soundness"]
solve_date: "2026-10-10"
language: "en"
---

# Bounty Hunter

**Flag:** `FortID{BU6_B0UN7Y_H0un73r5_Sh0uld_B3_4B13_70_5p07_Un50Und_PR00fZz}`
**Instance:** `https://bounty-hunter-28fd9e43d86c.inst3.ctf.fortid.com` — the "BugLedger" researcher portal (Flask/gunicorn) with the pages `/reports`, `/transparency`, `/playground`, `/vault`. Author: ipaljak.

## Challenge

The service publishes its transparent-bounty proofs as a polyfold-style PCS ("TwinFold-PCS-v2") and ships the verifier so anyone can replay them:

```text
GET /api/replay/verifier.py                       -> 5076 B
GET /api/transparency/snapshots/latest/manifest.json -> 1811 B
GET /api/reports.json                             -> 1080 B
```

The manifest declares a public evaluation vector of 8192 elements over 13 fold rounds, one cell per column of a bug report:

```text
vector_length : 8192
variables     : 13
scheme        : TwinFold-PCS-v2
snapshot_id   : triage-2026-09-28
commitment    : d438f6d51d055de1555a4f6defacaf3a889b3700bedadd7edb4d513ba833c859
shards        : 8 x 1024 elements, served under /api/transparency/snapshots/triage-2026-09-28/shards/0NN.json
encoding      : little_endian_boolean_hypercube, report_id_bits 11, column_bits 2
columns       : duplicate 0, accepted 1, critical 2, payout_authorized 3
```

`vault_policy` asks for a valid proof of `payout_authorized = 1` on one of the six reports owned by the account:

```text
{"field":"payout_authorized","owned_report_ids":[271,604,918,1247,1569,1842],
 "required_claimed_value":"1","scope":"any_owned_report"}
```

All six reports read back as real value 0 in that column, matching the table in `/api/reports.json`:

```text
report 271   accepted 1 critical 0 duplicate 0 payout_authorized 0
report 604   accepted 1 critical 0 duplicate 0 payout_authorized 0
report 918   accepted 1 critical 0 duplicate 0 payout_authorized 0
report 1247  accepted 1 critical 1 duplicate 0 payout_authorized 0
report 1569  accepted 0 critical 0 duplicate 0 payout_authorized 0
report 1842  accepted 1 critical 1 duplicate 0 payout_authorized 0
```

The cell to hijack for report 604 follows from the bit decomposition: `bits_le(604, 11) + bits_le(3, 2)` = `[0,0,1,1,1,0,1,0,0,1,0,1,1]` → index 6748, real value 0. The goal is to make `/vault` accept a proof that asserts 1 at that cell.

## Analysis

`verify()` walks the 13 rounds like this (`verifier.py:122-145`):

```python
for i in range(n):
    if commit(coeffs) != (manifest["commitment"] if i == 0 else proof["fold_commitments"][i - 1]):
        return False, f"bad commitment in round {i}"

    r = proof["rounds"][i]
    a = eval_poly(coeffs, xs[i])
    b = eval_poly(coeffs, -xs[i])

    if a != F(r["a"]):
        return False, f"bad +x evaluation in round {i}"
    if b != F(r["b"]):
        return False, f"bad -x evaluation in round {i}"

    next_coeffs = [F(x) for x in r["next_coeffs"]]
    if len(next_coeffs) == 0:
        return False, f"empty next polynomial in round {i}"
    if commit(next_coeffs) != proof["fold_commitments"][i]:
        return False, f"bad next commitment in round {i}"

    next_value = claimed if i == n - 1 else F(proof["rounds"][i + 1]["a"])
    if fold_value(a, b, bits[i], xs[i]) != next_value:
        return False, f"fold equation failed in round {i}"

    coeffs = next_coeffs
```

Three constraints give a polyfold its correctness: (1) each round's polynomial has exactly half the degree of the previous one, (2) the commitment binds that polynomial, (3) the fold equation links `a`, `b` of one round to `a` of the next. Constraint (3) is implemented, and `a`, `b` in round 0 are computed from the public vector so they cannot be faked. Constraint (1) is not: the only test at `verifier.py:136` is `len(next_coeffs) != 0`. Nothing compares the coefficient count with the expected degree `8192 / 2**(i+1) - 1`.

Constraint (2) adds no real binding either: `commit()` is just SHA-256 over the coefficient list the submitter sends (`verifier.py:74-80`), so it only forces the submitter to be consistent with their own list, not to stay tied to the original vector.

The consequence: if round `i` returns a degree-1 polynomial, the submitter freely controls both `p(x_{i+1})` and `p(-x_{i+1})`. Two distinct points always determine exactly one degree-1 polynomial, and the verifier then derives `a`, `b` from that polynomial — so `a`, `b` in every round after round 0 are in the attacker's hands, and only the fold equation with the previous round still has to hold.

The fold chain still has to be consistent, so the construction walks backwards from the final requirement:

- Round `i` (except the last): `A = fold_value(a, b, bits[i], xs[i])` is already fixed by this round's `a`, `b`. Pick `p(-x_{i+1})` arbitrarily, set `p(x_{i+1}) = A`, and interpolate degree 1. Then round `i+1`'s `a` equals `A`, so round `i`'s fold equation holds.
- Round `n-2`: instead of a random second value, solve the fold equation backwards so the last round lands on `claimed`. For `bit == 0`: `b = 2*claimed - a`; for `bit == 1`: `b = a - 2*x*claimed`.
- Round `n-1`: set `next_coeffs = [claimed]` (a constant polynomial), which makes `eval_poly(coeffs, xs[-1]) == claimed` at `verifier.py:147` hold automatically.

The public data already hints at this: the sample proof on `/playground` (`sample_proof.json`, 3000 B) also has 13 rounds with `next_coeffs` lengths `[2]*12 + [1]`. No honest prover over an 8192-element vector produces degree-1 polynomials like that; the sample is accepted precisely because the verifier never checks degrees.

## Solution

`forge.py` (2328 B) reuses the service's own `verifier.py` as the interpolation and evaluation library and builds a proof for `payout_authorized(604) = 1`:

```python
import json, random, sys
sys.path.insert(0, ".")
import verifier as V

BASE = "https://bounty-hunter-28fd9e43d86c.inst3.ctf.fortid.com"
manifest = json.load(open("manifest.json"))
vector = V.load_vector(BASE, manifest)
print("vector len", len(vector))
sample = json.load(open("sample_proof.json"))
print("sample verify:", V.verify(sample, manifest, vector))


def interp(x, fa, fb):
    # p(x)=fa, p(-x)=fb, degree 1
    c0 = V.F((V.F(fa) + V.F(fb)) * V.inv(2))
    c1 = V.F((V.F(fa) - V.F(fb)) * V.inv(2 * V.F(x)))
    return [c0, c1]

def last_b(a, x, bit, claimed):
    if bit == 0:
        return V.F(2 * V.F(claimed) - V.F(a))
    return V.F(V.F(a) - 2 * V.F(x) * V.F(claimed))

def forge(report_id, field, claimed_value):
    claimed = V.F(claimed_value)
    bits = V.point_bits(report_id, field, manifest)
    n = len(bits)
    rho = V.challenge(manifest["snapshot_id"], manifest["commitment"], report_id, field, claimed)
    xs = V.ladder(rho, n)
    poly = [V.F(x) for x in vector]
    assert V.commit(poly) == manifest["commitment"]
    rounds, fcs = [], []
    a = V.eval_poly(poly, xs[0])
    b = V.eval_poly(poly, -xs[0])
    for i in range(n):
        if i == n - 1:
            nxt = [claimed]
        else:
            A = V.fold_value(a, b, bits[i], xs[i])
            if i + 1 == n - 1:
                free = last_b(A, xs[i + 1], bits[i + 1], claimed)
            else:
                free = random.randrange(1, V.P)
            nxt = interp(xs[i + 1], A, free)
        rounds.append({"a": str(a), "b": str(b), "next_coeffs": [str(c) for c in nxt]})
        fcs.append(V.commit(nxt))
        a = V.eval_poly(nxt, xs[i + 1])
        b = V.eval_poly(nxt, -xs[i + 1])
    proof = {
        "claimed_value": str(claimed_value),
        "field": field,
        "fold_commitments": fcs,
        "report_id": report_id,
        "rounds": rounds,
        "scheme": manifest["scheme"],
        "snapshot_id": manifest["snapshot_id"],
    }
    return proof
reports = json.load(open("reports.json"))
policy = reports["vault_policy"]
rid = int(policy["owned_report_ids"][1])
proof = forge(rid, policy["field"], policy["required_claimed_value"])
json.dump(proof, open("forged.json", "w"), indent=2)
print("forged verify:", V.verify(proof, manifest, vector))
print("vault_policy ok:", V.vault_policy(proof, reports))
```

`assert V.commit(poly) == manifest["commitment"]` confirms the 8 shards fetched are exactly the vector committed in the manifest, so round 0's `a`, `b` are genuine evaluations. Run against the live instance:

```text
vector len 8192
sample verify: (True, 'accepted')
forged verify: (True, 'accepted')
```

The `sample verify` line is kept deliberately: with one harness and one vector, a real proof (column `accepted` of report 604, real value 1) and a forged proof (column `payout_authorized`, real value 0) both come out `accepted`. The verifier cannot tell the two apart.

`forged.json` (6258 B) holds 13 rounds with `next_coeffs` lengths `[2]*12 + [1]`, the last round being the constant `[1]`. Submitting it:

```text
POST /api/proof/verify
{"message":"accepted","ok":true, ...}
```

The saved record keeps only the `message` and `ok` fields of the JSON response; the remaining fields were not recorded. The last step is to paste the same proof into the `/vault` form (`<textarea name="proof">`, `POST` to itself) and read back the 9184-byte page:

```html
    <div class="result ok">
      <strong>accepted</strong>
      <pre><code>FortID{BU6_B0UN7Y_H0un73r5_Sh0uld_B3_4B13_70_5p07_Un50Und_PR00fZz}</code></pre>
    </div>
```

The word `accepted` in that block is the challenge service's own verdict, not a submission response from the platform.

## Result

```text
FortID{BU6_B0UN7Y_H0un73r5_Sh0uld_B3_4B13_70_5p07_Un50Und_PR00fZz}
```

The flag was read directly from the challenge service. No submission response recorded.

## Reproduce

A live instance is required: `report_id`, `snapshot_id`, `commitment` and the whole vector are per-instance data, and each instance publishes a different manifest. No offline artifact is sufficient to replay this.

```console
$ mkdir bh && cd bh
$ curl -sS https://bounty-hunter-28fd9e43d86c.inst3.ctf.fortid.com/api/replay/verifier.py -o verifier.py
$ curl -sS https://bounty-hunter-28fd9e43d86c.inst3.ctf.fortid.com/api/transparency/snapshots/latest/manifest.json -o manifest.json
$ curl -sS https://bounty-hunter-28fd9e43d86c.inst3.ctf.fortid.com/api/reports.json -o reports.json
$ curl -sS https://bounty-hunter-28fd9e43d86c.inst3.ctf.fortid.com/playground -o playground.html
```

Take the sample proof from the `/playground` page and save it as `sample_proof.json` (used as the control). Update the `BASE` constant in the `forge.py` listing above if the instance name differs, save that listing as `bh/forge.py`, then:

```console
$ python forge.py
```

`forge.py` fetches the 8 shards through `V.load_vector(BASE, manifest)` and writes `forged.json`. Submit the proof:

```console
$ curl -sS -X POST -H 'Content-Type: application/json' \
    --data @forged.json \
    https://bounty-hunter-28fd9e43d86c.inst3.ctf.fortid.com/api/proof/verify
$ curl -sS -X POST --data-urlencode "proof@forged.json" \
    https://bounty-hunter-28fd9e43d86c.inst3.ctf.fortid.com/vault
```

The `/vault` HTML response contains the `<div class="result ok">` block with the flag. Python 3 standard library only; no external dependencies.
