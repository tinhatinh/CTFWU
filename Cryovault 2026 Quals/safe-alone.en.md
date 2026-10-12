---
title: "Safe Alone"
category: "AI"
tags: ["adapter-merge", "inverse-problem"]
solve_date: "2026-10-11T04:33:00+07:00"
language: "en"
---

# Safe Alone

**Flag:** `isfcr{c076e5acfc0aac186add6491}`  
**Artifacts:** `safe_alone.zip` (containing `data.json` and `unlock.py`)

| Artifact | SHA-256 |
|---|---|
| `safe_alone.zip` | `5d0f2d776c804b584198a45585c5522e71a08820684f8d77bc5ab91b3956e5c0` |
| `data.json` | `5a524d44cc2d03b51a65e49166f3138af253fa98ff894f64250ad0752ba89caa` |
| `unlock.py` | `3d61b5c450b4179a04abbbec7bd3b6ddfdec56bcdbc3d7663a9e06865974d520` |

## Challenge

Recover the production model's merge recipe from adapter-gate telemetry. The answer must be a JSON array of strings in the exact form `adapter-id:coefficient`, containing only nonzero coefficients, **sorted lexicographically in ASCII order**. The checker `unlock.py` decrypts the flag only when the submitted recipe matches the one used to seal it.

## Initial Analysis

The JSON describes a low-rank adapter merge rather than a conventional hidden password:

- **120 candidate adapters**, each with a unique `adapter-...` identifier.
- Model dimension **48**, adapter rank **2**, and **3 gate outputs**.
- Each adapter has a 2-by-48 matrix `A`, a 3-by-2 matrix `B`, and a rational-valued `scale`.
- The possible merge coefficients are explicitly restricted to **`-1`, `0`, or `1`**.
- **260 probes**, each containing a 48-dimensional input vector `x`, an `offset`, and a three-bit `fired` observation, supply **780 binary observations** in total.
- The model metadata specifies a gate threshold of **`7/9`**.

The low-rank adapter representation is the key structural clue. For adapter `i`, its contribution to gate output `j` on probe `t` can be precomputed as

```text
W_i        = scale_i * (B_i @ A_i)          # shape: 3 x 48
F[t,j,i]   = W_i[j,:] @ x_t
score[t,j] = sum_i coefficient[i] * F[t,j,i]
```

Here `F` is an observation-by-adapter design matrix with shape **780 x 120**, and each unknown `coefficient[i]` is in `{-1,0,1}`. As a result, the telemetry provides a constrained sparse inverse problem over the adapter coefficients, rather than requiring brute force over all `3^120` assignments.

## Exploitation Chain

1. **Convert the adapters into a numerical design matrix.** Parse the rational matrix entries and scales exactly (for example, with Python's `fractions.Fraction`), multiply `B @ A` for every adapter, and evaluate its three gate contributions on every telemetry input. Keep an explicit association between each feature column and its original adapter ID.

2. **Infer sparse signed coefficients from the gate observations.** Encode each `fired` bit as a positive or negative gate-sign constraint, with a tolerance or slack variable rather than requiring every observation to be perfectly consistent with a simplified linear threshold rule. Fit the coefficient vector using sparse/regularized optimization, restrict candidate values to `{-1,0,1}`, and refine ambiguous coefficients by checking the remaining gate disagreements. The recorded `offset` and threshold must be considered when choosing a proxy gate rule; the telemetry alone does not provide a complete reference implementation of the production gate.

3. **Do not treat imperfect telemetry agreement as proof of a wrong recipe.** The recovered solution has **54 nonzero coefficients**, comprising **22 positive** and **32 negative** coefficients. A simple diagnostic based on the signed linear score (`score > 7/9`, without applying the per-probe offset) reproduces **773 of the 780** recorded gate bits. Seven disagreements therefore remain under *this simplified proxy*, but an exact fit to it is not a necessary acceptance condition. In particular, this count is a diagnostic, not a claim that the seven labels are definitely corrupt.

4. **Use the authenticated checker to identify the exact recipe.** Convert the surviving candidate into strings `adapter-id:+/-1` (using `1`, not `+1`), discard zero coefficients, and sort the complete strings in ASCII order. The checker serializes the JSON with `ensure_ascii=True` and compact separators before deriving a key using `hashlib.scrypt`:

   ```python
   enc = json.dumps(answer, ensure_ascii=True, separators=(',', ':')).encode('ascii')
   key = hashlib.scrypt(
       b'isfcr-ml\0' + enc,
       salt=bytes.fromhex('0cc42cf2f78a7694ce467f5a69ceeab5'),
       n=131072, r=8, p=1, maxmem=2**28, dklen=32
   )
   ```

   The derived AES-256-GCM key is used with the hard-coded nonce and the AAD `safe-alone`. An incorrect recipe produces an authentication failure (`Rejected.`). The recovered recipe below passes authentication and returns the flag.

## Recovered Merge Recipe

The following is the **complete submission** (54 nonzero coefficients), already sorted as ASCII strings:

```json
[
  "adapter-09027b78fe:-1",
  "adapter-0a32cb3b12:1",
  "adapter-141f02a7fc:-1",
  "adapter-17f16c1958:-1",
  "adapter-2946a20178:-1",
  "adapter-2ad5ac7e79:-1",
  "adapter-2df01da8f4:-1",
  "adapter-2ef7951ee5:-1",
  "adapter-2f6946d4df:-1",
  "adapter-364a65c4ec:-1",
  "adapter-3fce23bf8b:1",
  "adapter-423cf163fd:-1",
  "adapter-5200d01820:-1",
  "adapter-52cc220e59:-1",
  "adapter-531190460f:1",
  "adapter-5312b875b7:1",
  "adapter-53ff0e2cb4:1",
  "adapter-598659ff1c:1",
  "adapter-5daffe0354:-1",
  "adapter-6835e6a755:-1",
  "adapter-684fff23e9:-1",
  "adapter-6b512202d8:1",
  "adapter-705a5b2c1d:1",
  "adapter-7e4ea991af:-1",
  "adapter-85686b6549:-1",
  "adapter-86a2ed2376:-1",
  "adapter-871006528f:1",
  "adapter-89cbd1782d:-1",
  "adapter-9028a83cc0:1",
  "adapter-938bb6157b:-1",
  "adapter-93de68b078:1",
  "adapter-9931209431:-1",
  "adapter-9999da443a:1",
  "adapter-9d70196f50:1",
  "adapter-a3df0cf01d:1",
  "adapter-ab1af0c73d:1",
  "adapter-abd08a3dc7:-1",
  "adapter-ac48a7a78a:1",
  "adapter-b56d849e15:-1",
  "adapter-b65166624b:-1",
  "adapter-bb55fc6722:-1",
  "adapter-bc1c8c938a:-1",
  "adapter-bced3514ff:-1",
  "adapter-be328a55cb:1",
  "adapter-c0b42e8201:-1",
  "adapter-cc449a31f0:-1",
  "adapter-cf46f32219:1",
  "adapter-d03361f462:-1",
  "adapter-e375a915ab:1",
  "adapter-e44aadc5a7:1",
  "adapter-eb6d3e723f:1",
  "adapter-ef5a0cf455:-1",
  "adapter-f86c34eeb4:1",
  "adapter-f86cc06675:-1"
]
```

## Flag

`isfcr{c076e5acfc0aac186add6491}`

This flag was **verified locally with the challenge's original `unlock.py`**. It is an authenticated decryption result, not a guess based solely on agreement with the telemetry. Submission to the competition server was not independently checked.

## Reproduce

1. Extract `safe_alone.zip` to obtain `data.json` and `unlock.py`.
2. Copy the JSON array in **Recovered Merge Recipe** into a file named `recipe.json`, without changing entry order or values.
3. In a shell with Python 3 and the `cryptography` package installed, run:

```bash
python3 unlock.py "$(python3 -c 'import json; print(json.dumps(json.load(open("recipe.json")), ensure_ascii=True, separators=(",", ":")))')"
```

Expected output (observed from the provided checker):

```text
isfcr{c076e5acfc0aac186add6491}
```

The crucial final validation is the successful AES-GCM authentication of the JSON-encoded recipe; high agreement with gate telemetry alone would not validate the exact submission.
