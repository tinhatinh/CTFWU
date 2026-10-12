---
title: "Safe Alone"
category: "AI"
tags: ["adapter-merge", "inverse-problem"]
solve_date: "2026-10-11T04:33:00+07:00"
language: "vi"
---

# Safe Alone

**Flag:** `isfcr{c076e5acfc0aac186add6491}`  
**Artifact:** `safe_alone.zip` (containing `data.json` and `unlock.py`)

| Artifact | SHA-256 |
|---|---|
| `safe_alone.zip` | `5d0f2d776c804b584198a45585c5522e71a08820684f8d77bc5ab91b3956e5c0` |
| `data.json` | `5a524d44cc2d03b51a65e49166f3138af253fa98ff894f64250ad0752ba89caa` |
| `unlock.py` | `3d61b5c450b4179a04abbbec7bd3b6ddfdec56bcdbc3d7663a9e06865974d520` |

## Đề bài

Khôi phục merge recipe của model từ adapter-gate telemetry. Đáp án là JSON array `adapter-id:coefficient`, chỉ gồm hệ số khác 0 và được sort ASCII.

## Phân tích

Có 120 adapter, input dimension 48, rank 2 và ba gate. Mỗi adapter đóng góp `scale*(B@A)`. Hệ số chỉ được là -1,0,1. 260 probe tạo 780 bit fired với threshold 7/9.

Tính trước contribution của mỗi adapter tại mỗi probe để lập design matrix 780×120. Đây là sparse inverse problem, không cần brute-force 3^120 cấu hình.

```text
W_i        = scale_i * (B_i @ A_i)          # shape: 3 x 48
F[t,j,i]   = W_i[j,:] @ x_t
score[t,j] = sum_i coefficient[i] * F[t,j,i]
```

## Lời giải

1. Parse rational entry bằng Fraction, tính B@A và giữ ID đi cùng từng cột feature.
2. Dùng sparse/regularized optimization cho constraint gate, có slack/tolerance. Khi đánh giá rule phải xét offset và threshold; telemetry không cung cấp implementation đầy đủ của production gate.
3. Candidate thu được có 54 hệ số khác 0: 22 dương, 32 âm. Proxy `score>7/9` bỏ offset khớp 773/780 bit. Bảy mismatch của proxy không chứng minh label lỗi hoặc recipe sai.
4. Định dạng hệ số dương là `1`, không phải `+1`; sort toàn bộ string ASCII. unlock.py serialize compact ASCII JSON rồi dùng scrypt để dựng AES-GCM key với AAD `safe-alone`.
5. Dùng authenticated checker để xác nhận candidate. Recipe dưới đây cho GCM authentication thành công, trong khi recipe sai bị `Rejected.`.

   ```python
   enc = json.dumps(answer, ensure_ascii=True, separators=(',', ':')).encode('ascii')
   key = hashlib.scrypt(
       b'isfcr-ml\0' + enc,
       salt=bytes.fromhex('0cc42cf2f78a7694ce467f5a69ceeab5'),
       n=131072, r=8, p=1, maxmem=2**28, dklen=32
   )
   ```

## Merge recipe đã khôi phục

JSON block dưới đây là toàn bộ 54 hệ số khác 0, đã sort ASCII. Giữ nguyên thứ tự và giá trị.

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

## Kết quả

Bản nguồn ghi recipe được kiểm tra local bằng unlock.py gốc và giải mã authenticated thành công.

`isfcr{c076e5acfc0aac186add6491}`

## Tái hiện

Giải nén `safe_alone.zip`, lưu JSON ở mục Recipe thành `recipe.json`, đặt cạnh unlock.py. Cần Python 3 và cryptography; chạy lệnh dưới đây để kiểm tra recipe. Bản nguồn nêu cách suy ra candidate nhưng không kèm script optimizer đầy đủ.

```bash
python3 unlock.py "$(python3 -c 'import json; print(json.dumps(json.load(open("recipe.json")), ensure_ascii=True, separators=(",", ":")))')"
```

```text
isfcr{c076e5acfc0aac186add6491}
```
