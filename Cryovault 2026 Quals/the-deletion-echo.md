---
title: "The Deletion Echo"
category: "AI"
tags: ["model-inversion", "machine-unlearning"]
solve_date: "2026-10-10T20:36:00+07:00"
language: "vi"
---

# The Deletion Echo

**Flag:** `isfcr{763c8479fac095a9e471ad3d}`  
**Artifact:** `data.json`, `unlock.py` (distributed in `the_deletion_echo.zip`)
| Artifact | SHA-256 |
|---|---|
| `the_deletion_echo.zip` | `c487973cd06cad6bf487d7fd483d4ebe03c7690a36e9f37ce32b13313fa3b535` |
| `data.json` | `4afb0ff16febdbd9aec0f11b901a423376b018e2d257468141de35ce62f808d9` |
| `unlock.py` | `ab008f286c2164f302a0f10d8e9d5d5036c842cd80e9d6870bf3aa2f21f884e3` |

## Đề bài

Khôi phục các record bị xóa và private label của chúng từ regression-model snapshot. Đáp án là JSON array `record-id:label` được sort ASCII và kiểm tra bằng unlock.py.

## Phân tích

Có feature dimension 12, năm snapshot không theo thứ tự, 240 query mỗi snapshot, 140 deletion candidate và ba ingestion batch. Model là ridge regression không intercept: H là tổng outer product cộng lambda I, b là tổng x*y và theta=H^-1*b.

Prediction mean cho thông tin về theta; predictive variance dạng `sigma²*(1+qᵀH^-1q)*(1+noise)` làm lộ inverse Gram matrix. Noise nhỏ nhưng phải xử lý conditioning. unlock.py dùng compact JSON, prefix `isfcr-ml` với NUL, scrypt và AES-GCM; output đúng cả record lẫn label mới xác thực được.

```python
x[j] = (raw[permutation[j]] - center[j]) / scale[j]
```

## Lời giải

1. Transform query theo permutation/center/scale. Least squares trên mean ước lượng theta. Fit variance theo constant và 78 quadratic monomial, chú ý factor 2 của off-diagonal. Dùng q/100 để conditioning tốt hơn, khôi phục H và b=H*theta.
2. So các H với Gram matrix của ingestion batch để xác định chronology. `snapshot-80794d4ee21c` là redeploy stale của `snapshot-d1f54facd170`, không phải một transition mới, dù sigma² khác.
3. Qua release vừa ingest vừa delete, tính `G_deleted=H_before+G_ingest-H_after`; ridge penalty triệt tiêu. Dùng NNLS với outer product của 140 candidate. Có 26 weight vượt 0,5 và gần 1; các weight còn lại gần 0.
4. Difference b tạo 12 phương trình cho 36 integer label: 10 ingested và 26 deleted, mỗi label thuộc 0…3. Nhân 4 vì denominator feature chia hết 4, làm tròn RHS đã ước lượng để có integer system. Dùng lattice/LLL rồi kiểm tra bounds và residual theo sufficient statistic gốc.
5. Các ingestion label suy ra có thể dùng làm đối chứng; residual của batch liên quan khoảng 0,0065. Sort 26 string record-id:label và đưa chính JSON đó vào unlock.py để xác thực.

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

## Các record đã khôi phục

Block JSON dưới đây chứa toàn bộ 26 record và label đã khôi phục, ở thứ tự ASCII. Giữ nguyên các ID, dấu phân cách và label.

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

## Kết quả

unlock.py gốc đã giải mã authenticated với answer này và in flag ở local.

`isfcr{763c8479fac095a9e471ad3d}`

## Tái hiện

Cần Python, NumPy và SciPy cho bước nhận diện record. Python block dưới đây tái hiện reconstruction/NNLS. Phần giải integer label được mô tả ở Lời giải nhưng chưa có code đầy đủ trong bản nguồn; JSON Answer chứa kết quả đã tìm. Lưu block đó thành answer.json cạnh unlock.py rồi chạy lệnh kiểm tra để xác nhận cả ID và label.

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

```bash
python3 unlock.py "$(cat answer.json)"
```

```text
isfcr{763c8479fac095a9e471ad3d}
```
