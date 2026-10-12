---
title: "The Deletion Echo"
category: "AI"
tags: ["model-inversion", "machine-unlearning"]
solve_date: "2026-10-10T20:36:00+07:00"
language: "en"
---

# The Deletion Echo

**Flag:** `isfcr{763c8479fac095a9e471ad3d}`  
**Artifacts:** `data.json`, `unlock.py` (distributed in `the_deletion_echo.zip`)

| Artifact | SHA-256 |
|---|---|
| `the_deletion_echo.zip` | `c487973cd06cad6bf487d7fd483d4ebe03c7690a36e9f37ce32b13313fa3b535` |
| `data.json` | `4afb0ff16febdbd9aec0f11b901a423376b018e2d257468141de35ce62f808d9` |
| `unlock.py` | `ab008f286c2164f302a0f10d8e9d5d5036c842cd80e9d6870bf3aa2f21f884e3` |

## Challenge

A regression service claims that a deletion request was honored through exact retraining. Recover the deleted records **and their private labels**. Submit one `record-id:label` string per deleted record, sorted lexicographically as ASCII strings, as a JSON list to `unlock.py`.

The supplied dataset contains observations from a series of regression-model snapshots, candidate records that might have been deleted, and several unlabeled ingestion batches. Neither snapshot chronology nor the number of deleted records is supplied. One snapshot may represent a stale redeployment rather than another state transition.

## Initial Analysis

`data.json` contains:

- A 12-dimensional feature-transform and model contract.
- Five unordered snapshots, with 240 prediction queries per snapshot (1,200 total).
- 140 possible deleted records (`candidates`), each with an ID and a known raw feature vector, but no label.
- Three unlabeled ingestion batches: `ingest-5798d74d` (12 records), `ingest-e0449f2a` (10 records), and `ingest-578b7698` (9 records).
- For each query, a raw vector, a noisy prediction mean, and a noisy predictive variance.

The feature transform is public:

```python
x[j] = (raw[permutation[j]] - center[j]) / scale[j]
```

The model is ridge regression **without an intercept**:

\[
H = \sum_i x_i x_i^\mathsf{T} + \lambda I,
\qquad
b = \sum_i x_i y_i,
\qquad
\theta = H^{-1}b.
\]

An oracle response at transformed query vector \(q\) has the form:

\[
\operatorname{mean}(q) = q^\mathsf{T}\theta + e_m,
\]

\[
\operatorname{variance}(q) = \sigma^2
  (1+q^\mathsf{T}H^{-1}q)(1+e_v).
\]

Both noise terms are extremely small. Crucially, **the predictive variance leaks the inverse of the training Gram matrix**. This makes exact deletion observable even though the deleted samples and their labels are not provided.

`unlock.py` does not contain a plaintext flag. It converts the answer list to compact ASCII JSON, derives an AES-256 key with scrypt using the prefix `b'isfcr-ml\0'`, and authenticates/decrypts a sealed ciphertext with AES-GCM. An incorrect record or label changes the derived key and is rejected.

## Exploitation Chain

1. **Reconstruct the model state in each snapshot.** Transform every query vector using the public `permutation`, `center`, and `scale`. Ordinary least squares on prediction means estimates the 12 entries of \(\theta\). Independently, fit predictive variance against a constant and the 78 distinct quadratic monomials \(q_iq_j\). The constant estimates \(\sigma^2\), and the remaining coefficients estimate \(\sigma^2 H^{-1}\) (accounting for the factor of two on off-diagonal terms). Invert this symmetric matrix to estimate \(H\), then compute \(b=H\theta\). Using `q / 100` when constructing the quadratic design matrix improves numerical conditioning. The observed standard deviations of the variance-fit residuals are roughly \(2\times10^{-9}\) to \(4\times10^{-9}\).

2. **Recover the history and identify the stale redeployment.** Compare every pair of reconstructed Gram matrices with the known update \(G_B=\sum_{i\in B}x_ix_i^\mathsf{T}\) for each ingestion batch. The consistent history is:

   ```text
   snapshot-2ee90f53b5c2
       + ingest-5798d74d (12 records)
          -> snapshot-d1f54facd170
       + ingest-e0449f2a (10 records)
       - deleted records (unknown subset)
          -> snapshot-e385b6f3720a
       + ingest-578b7698 (9 records)
          -> snapshot-9ccbadef83c2
   ```

   `snapshot-80794d4ee21c` is a stale redeployment of the `snapshot-d1f54facd170` training state, **not** an additional ingestion or deletion. Its inferred Gram matrix and mean parameters agree up to oracle noise, despite a different noise-variance parameter. For the two pure-ingestion transitions, the differences in \(H\) closely match the corresponding batches' Gram matrices (Frobenius residuals around 10.2 and 15.0 in the reconstructed units).

3. **Isolate the deleted records.** Let \(H_{\rm before}\) be the Gram matrix for `snapshot-d1f54facd170`, let \(H_{\rm after}\) be that for `snapshot-e385b6f3720a`, and let \(G_{\rm ingest}\) be the Gram matrix of `ingest-e0449f2a`. Because an ingestion and an exact deletion occurred together,

   \[
   H_{\rm after} = H_{\rm before}+G_{\rm ingest}-G_{\rm deleted},
   \]

   so

   \[
   \boxed{G_{\rm deleted}=H_{\rm before}
           +G_{\rm ingest}-H_{\rm after}}.
   \]

   The unknown ridge penalty cancels between the snapshots. For every one of the 140 candidate records, construct its outer product \(x_ix_i^\mathsf{T}\) and vectorize the 78 unique entries. Solve the nonnegative least-squares problem

   \[
   \min_{w\geq0}\left\|\sum_i w_i\operatorname{vech}(x_ix_i^\mathsf{T})
                    -\operatorname{vech}(G_{\rm deleted})\right\|_2.
   \]

   **Exactly 26 coefficients are greater than 0.5 and all are extremely close to 1** (approximately 0.99978 to 1.00005); the other coefficients are negligible. Since each deleted record occurs at most once, these 26 IDs form the deletion set. Rebuilding their Gram matrix gives a full-matrix Frobenius discrepancy of approximately 16.4 from the oracle-derived deletion matrix, consistent with the extremely small variance noise magnified by matrix inversion.

4. **Recover the private integer labels.** The prediction means reveal \(\theta\), so the reconstructed sufficient statistics \(b=H\theta\) can also be differenced. Across the deletion release,

   \[
   b_{\rm after}-b_{\rm before}
      = \sum_{i\in\mathrm{ingest}} x_i y_i
        -\sum_{j\in\mathrm{deleted}}x_j y_j.
   \]

   The ten ingested labels and the 26 deleted labels are all unknown integers in \(\{0,1,2,3\}\). After moving the terms to one side, this is a 12-equation bounded-integer system over 36 unknown labels. All feature coordinates have denominators dividing four; consequently, multiplying the equations by four produces an **integer coefficient matrix**, and rounding the high-precision inferred right-hand side recovers the exact integer equations. Solve this bounded small-integer lattice problem (for example, using an LLL-based short-vector/closest-vector construction followed by a bounds check) to recover the labels. Verify the assignment using the original floating-point \(H\theta\) differences. As an additional consistency test, once the deleted labels are known, ordinary least squares recovers the ten ingestion labels as `[2, 0, 1, 3, 0, 2, 2, 2, 2, 2]`; rounding them yields a residual norm of approximately 0.0065 in the sufficient-statistic equations. The other two ingestions independently yield integer labels and similarly small residuals.

5. **Sort, serialize, and decrypt.** Format all 26 deleted records as `record-id:label`, sort by ASCII, and serialize as compact JSON. Pass this exact JSON array to `unlock.py`. AES-GCM authentication succeeds, producing the flag.

## Recovered Deleted Records

The final answer, already sorted as ASCII strings, is:

```json
[
  "record-0730706150:0",
  "record-28c0bbf813:2",
  "record-2e6662ecc6:3",
  "record-3de105d25d:3",
  "record-3ee76f33c8:2",
  "record-46126dd779:0",
  "record-473e486afd:0",
  "record-49aa7c51a4:2",
  "record-507645d5d9:2",
  "record-58fad90382:2",
  "record-5bc7d8554c:1",
  "record-66f65f5026:0",
  "record-71fb3e266c:2",
  "record-7796490f27:1",
  "record-77a4509144:1",
  "record-8f4b4073f9:1",
  "record-90769aad7a:1",
  "record-978b124800:1",
  "record-9cddf7a4fb:0",
  "record-9cfdc74744:3",
  "record-b9e67b6811:2",
  "record-cf44aec78a:2",
  "record-cf4fee237a:0",
  "record-d32fd7d5d5:1",
  "record-ebfb2ad09e:0",
  "record-ee9e7ec4d8:1"
]
```

## Flag

`isfcr{763c8479fac095a9e471ad3d}`

The recovered answer was verified **locally with the original `unlock.py`** from the challenge archive. It successfully decrypted the sealed payload and printed the flag. Acceptance by the remote CTF scoreboard was not independently checked.

## Reproduce

Extract `the_deletion_echo.zip` to obtain `data.json` and `unlock.py`. Use Python, NumPy, and SciPy to reproduce the main deletion-identification step:

```python
import json
import numpy as np
from scipy.optimize import nnls

D = json.load(open('data.json', encoding='utf-8'))
C = D['contract']

def features(raw):
    a = np.asarray(raw, dtype=float)
    return (a[..., C['permutation']] - C['center']) / C['scale']

H = {}
for snap in D['snapshots']:
    sid = snap['id']
    rows = [q for q in D['queries'] if q['snapshot_id'] == sid]
    X = features([q['raw'] for q in rows])
    Z = X / 100.0
    pairs = [(i, j) for i in range(12) for j in range(i, 12)]
    design = np.column_stack(
        [np.ones(len(rows))] + [Z[:, i] * Z[:, j] for i, j in pairs]
    )
    v = np.array([float(q['predictive_variance']) for q in rows])
    c = np.linalg.lstsq(design, v, rcond=None)[0]
    invH = np.zeros((12, 12))
    for k, (i, j) in enumerate(pairs):
        invH[i, j] = invH[j, i] = c[k + 1] / (
            c[0] * 10000.0 * (2 if i != j else 1)
        )
    H[sid] = np.linalg.inv(invH)

batch = next(b for b in D['ingest'] if b['batch_id'] == 'ingest-e0449f2a')
Xb = features([r['raw'] for r in batch['records']])
G_deleted = (H['snapshot-d1f54facd170']
             + Xb.T @ Xb - H['snapshot-e385b6f3720a'])

pairs = np.triu_indices(12)
Xc = features([r['raw'] for r in D['candidates']])
A = np.column_stack([np.outer(x, x)[pairs] for x in Xc])
w, _ = nnls(A, G_deleted[pairs])
ids = sorted(D['candidates'][i]['id'] for i in np.flatnonzero(w > 0.5))
print(len(ids), ids)
# Expected: exactly 26 IDs, matching the IDs in the answer list above.
```

Recover the labels using the integer system in Step 4. Save the recovered, ASCII-sorted JSON list shown above as `answer.json`, in the same directory as `unlock.py`, and run:

```bash
python3 unlock.py "$(cat answer.json)"
```

Expected output:

```text
isfcr{763c8479fac095a9e471ad3d}
```

This final step checks **both** the recovered record identities and their labels: the answer is part of the scrypt key derivation, and the AES-GCM tag verifies only with the correct key.
