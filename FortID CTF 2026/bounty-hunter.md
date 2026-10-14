---
title: "Bounty Hunter"
category: "Crypto"
tags: ["pcs", "polyfold", "commitment-binding", "degree-check", "argument-soundness"]
solve_date: "2026-10-10"
language: "vi"
---

# Bounty Hunter

**Flag:** `FortID{BU6_B0UN7Y_H0un73r5_Sh0uld_B3_4B13_70_5p07_Un50Und_PR00fZz}`
**Instance:** `https://bounty-hunter-28fd9e43d86c.inst3.ctf.fortid.com` — cổng thông tin nghiên cứu "BugLedger" chạy Flask/gunicorn, các trang `/reports`, `/transparency`, `/playground`, `/vault`. Tác giả: ipaljak.

## Đề bài

Dịch vụ công bố toàn bộ bằng chứng transparent-bounty dưới dạng một PCS kiểu polyfold ("TwinFold-PCS-v2") và phát kèm cả mã kiểm chứng để người chơi tự replay:

```text
GET /api/replay/verifier.py                       -> 5076 B
GET /api/transparency/snapshots/latest/manifest.json -> 1811 B
GET /api/reports.json                             -> 1080 B
```

Manifest khai báo một evaluation vector công khai gồm 8192 phần tử trên 13 vòng gấp (fold), mỗi ô là một cột của một báo cáo lỗi:

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

`vault_policy` đòi một bằng chứng hợp lệ cho `payout_authorized = 1` trên một trong sáu báo cáo thuộc tài khoản:

```text
{"field":"payout_authorized","owned_report_ids":[271,604,918,1247,1569,1842],
 "required_claimed_value":"1","scope":"any_owned_report"}
```

Cả sáu báo cáo đều đọc lại giá trị thật bằng 0 ở cột đó, khớp với bảng trong `/api/reports.json`:

```text
report 271   accepted 1 critical 0 duplicate 0 payout_authorized 0
report 604   accepted 1 critical 0 duplicate 0 payout_authorized 0
report 918   accepted 1 critical 0 duplicate 0 payout_authorized 0
report 1247  accepted 1 critical 1 duplicate 0 payout_authorized 0
report 1569  accepted 0 critical 0 duplicate 0 payout_authorized 0
report 1842  accepted 1 critical 1 duplicate 0 payout_authorized 0
```

Ô cần chiếm của report 604 có chỉ số suy ra từ bit: `bits_le(604, 11) + bits_le(3, 2)` = `[0,0,1,1,1,0,1,0,0,1,0,1,1]` → index 6748, giá trị thật 0. Mục tiêu là làm cho `/vault` chấp nhận một bằng chứng khẳng định ô đó bằng 1.

## Phân tích

`verify()` trong `verifier.py` đi qua 13 vòng với mỗi vòng như sau (`verifier.py:122-145`):

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

Ba ràng buộc làm nên tính đúng đắn của một polyfold: (1) đa thức vòng sau có bậc đúng bằng một nửa bậc vòng trước, (2) commitment ràng buộc đa thức đó, (3) phương trình fold nối `a`, `b` của vòng này với `a` của vòng sau. Kiểm (3) có đủ, và `a`, `b` ở vòng 0 được tính từ vector công khai nên không giả được. Kiểm (1) thì không: điều kiện ở `verifier.py:136` chỉ là `len(next_coeffs) != 0`. Không có chỗ nào so độ dài danh sách hệ số với bậc kỳ vọng `8192 / 2**(i+1) - 1`.

Kiểm (2) cũng không tạo thêm ràng buộc: `commit()` chỉ là SHA-256 trên danh sách hệ số do người nộp tự gửi (`verifier.py:74-80`), nên nó chỉ bắt người nộp phải trung thực với chính danh sách hệ số của mình, không ràng buộc danh sách đó với vector gốc.

Hệ quả: nếu vòng `i` trả về một đa thức bậc 1 thì người nộp tự do chọn cả `p(x_{i+1})` lẫn `p(-x_{i+1})`. Với hai điểm phân biệt luôn có đúng một đa thức bậc 1 đi qua, và verifier sẽ tự tính `a`, `b` từ đa thức ấy — tức là `a`, `b` của mọi vòng sau vòng 0 đều nằm trong tay người nộp, chỉ còn phải thoả phương trình fold với vòng trước.

Chuỗi fold vẫn phải khớp, nên cách dựng là đi ngược từ yêu cầu cuối:

- Vòng `i` (trừ vòng cuối): đã biết `A = fold_value(a, b, bits[i], xs[i])` từ `a`, `b` của vòng này. Chọn `p(-x_{i+1})` tuỳ ý, đặt `p(x_{i+1}) = A` rồi nội suy bậc 1. Khi đó `a` của vòng `i+1` đúng bằng `A`, phương trình fold của vòng `i` thoả.
- Vòng `n-2`: thay vì chọn `b` ngẫu nhiên, giải ngược phương trình fold để vòng cuối cho ra đúng `claimed`. Với `bit == 0`: `b = 2*claimed - a`; với `bit == 1`: `b = a - 2*x*claimed`.
- Vòng `n-1`: đặt `next_coeffs = [claimed]` (đa thức hằng), nên `eval_poly(coeffs, xs[-1]) == claimed` ở `verifier.py:147` luôn đúng.

Một dấu hiệu ngay trong dữ liệu công khai: sample proof ở `/playground` (`sample_proof.json`, 3000 B) cũng có 13 vòng với độ dài `next_coeffs` là `[2]*12 + [1]`. Không có prover trung thực nào trên vector 8192 phần tử lại sinh ra các đa thức bậc 1 như vậy; sample chỉ được chấp nhận vì chính verifier không kiểm bậc.

## Lời giải

`forge.py` (2328 B) dùng đúng `verifier.py` do dịch vụ phát hành làm mô-đun nội suy và lượng giá, dựng bằng chứng cho `payout_authorized(604) = 1`:

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

`assert V.commit(poly) == manifest["commitment"]` xác nhận 8 shard đọc về đúng là vector được cam kết trong manifest, nên `a`, `b` vòng 0 là lượng giá thật. Chạy trên instance đang sống:

```text
vector len 8192
sample verify: (True, 'accepted')
forged verify: (True, 'accepted')
```

Bản ghi giữ lại `sample verify` để đối chứng: cùng một harness, cùng một vector, một bằng chứng thật (cột `accepted` của report 604, giá trị thật bằng 1) và một bằng chứng giả (cột `payout_authorized`, giá trị thật bằng 0) đều cho kết luận `accepted`. Verifier không phân biệt được hai trường hợp.

`forged.json` (6258 B) có 13 vòng với độ dài `next_coeffs` `[2]*12 + [1]`, vòng cuối là hằng `[1]`. Nộp lên dịch vụ:

```text
POST /api/proof/verify
{"message":"accepted","ok":true, ...}
```

Bản ghi chỉ giữ hai trường `message` và `ok` của JSON phản hồi; các trường còn lại không được lưu. Bước cuối là dán đúng bằng chứng đó vào form `/vault` (`<textarea name="proof">`, `POST` chính nó) và nhận trang 9184 byte:

```html
    <div class="result ok">
      <strong>accepted</strong>
      <pre><code>FortID{BU6_B0UN7Y_H0un73r5_Sh0uld_B3_4B13_70_5p07_Un50Und_PR00fZz}</code></pre>
    </div>
```

Từ `accepted` trong khối này là kết luận của chính dịch vụ đề bài, không phải phản hồi submission từ nền tảng.

## Kết quả

```text
FortID{BU6_B0UN7Y_H0un73r5_Sh0uld_B3_4B13_70_5p07_Un50Und_PR00fZz}
```

Cờ đọc trực tiếp từ dịch vụ đề bài. Chưa lưu phản hồi submission.

## Tái hiện

Cần instance đang sống: `report_id`, `snapshot_id`, `commitment` và toàn bộ vector đều là dữ liệu theo instance, và manifest của mỗi instance một khác. Không có artifact offline nào đủ để chạy lại.

```console
$ mkdir bh && cd bh
$ curl -sS https://bounty-hunter-28fd9e43d86c.inst3.ctf.fortid.com/api/replay/verifier.py -o verifier.py
$ curl -sS https://bounty-hunter-28fd9e43d86c.inst3.ctf.fortid.com/api/transparency/snapshots/latest/manifest.json -o manifest.json
$ curl -sS https://bounty-hunter-28fd9e43d86c.inst3.ctf.fortid.com/api/reports.json -o reports.json
$ curl -sS https://bounty-hunter-28fd9e43d86c.inst3.ctf.fortid.com/playground -o playground.html
```

Lấy sample proof từ trang `/playground` và lưu thành `sample_proof.json` (dùng để đối chứng). Sửa hằng `BASE` trong `forge.py` ở mục Lời giải nếu tên instance khác, lưu script đó thành `bh/forge.py` rồi:

```console
$ python forge.py
```

`forge.py` tự tải 8 shard qua `V.load_vector(BASE, manifest)` và ghi `forged.json`. Nộp bằng chứng:

```console
$ curl -sS -X POST -H 'Content-Type: application/json' \
    --data @forged.json \
    https://bounty-hunter-28fd9e43d86c.inst3.ctf.fortid.com/api/proof/verify
$ curl -sS -X POST --data-urlencode "proof@forged.json" \
    https://bounty-hunter-28fd9e43d86c.inst3.ctf.fortid.com/vault
```

Response HTML của `/vault` chứa khối `<div class="result ok">` với cờ. Chỉ cần Python 3 stdlib; không có dependency ngoài.
