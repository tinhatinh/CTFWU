---
title: "The Last Protocol"
category: "Crypto"
tags: ["rsa", "wiener-attack", "finite-state-machine", "feistel", "sha256", "jpeg-metadata", "stream-cipher"]
solve_date: "2026-10-10T20:25:00+07:00"
language: "vi"
points: 983
---

# The Last Protocol

**Flag:** `kBxAc{cIPhEr_(h@in_ReCoNs7ru(tEd_31@90F84_FalS3_leAdS_De(iPheRed}`  
**Tác giả:** HydraRoot  
**Nguồn:** `thelastprotocol (1).zip` (100,632 bytes; SHA-256: `100d69e46e4d3da2f5ae35e1360e158dcf7ba5896e6285339e4a8bdb8be975ec`)

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `archive.bin` | 24 | `ff962ec3a8270f4d7139f37e66aea62cc86bf85093dd1d073586741ebf9da704` |
| `archive.jpg` | 148,887 | `48cd800f6abb7bb5dc1bf6c3fa0b54f4362e696a9cac26f7ef2d924fc8eb488d` |
| `final.dat` | 370 | `04027aa227262f995e121631988f027a15acb81a0d6878df8a5d4415dbda56b7` |
| `fragment_01.dat` | 1,024 | `e85a42edaeb5a98664942ab3162d1c9cf78ccb168ed702ea45d68fd143eb1713` |
| `fragment_02.dat` | 1,036 | `1360c29b0081e99fa5712fda2a9133aafd92acc4860e34f3b0aa9821ae698664` |
| `fragment_03.dat` | 1,045 | `b8efc49320401afc283488bc64c83f4b9d6ba58428f1aea2a9b82ea5db932207` |
| `fragment_04.dat` | 1,024 | `773545fb16801d19b04eb0ec6892704281b8464d3f0530cf999feb7042a04192` |
| `notebook.pdf` | 3,777 | `31c87a59deffe0dfc02887cc44d6090c0313a3645daab8884e6478da5945ad99` |
| `transmission.dat` | 495 | `a0401ce918e638b5e3f7cd7df964dcbd25245b32b9b7de0065d4f93e3e53bad9` |


## Đề bài

Một thông điệp được mã hóa ba lần. Bắt đầu với bản truyền RSA có tham số bất thường; dùng thông tin giải được để sắp thứ tự các calibration fragment có giá trị ở nhiều hệ cơ số. Các quan sát mô tả lịch sử một máy trạng thái. Dùng lịch sử đó làm vật liệu tạo khóa cho mạng Feistel, giải một archive ngắn, rồi đọc JPEG để lấy tham số giải lớp cuối. Định dạng lịch sử mà đề chỉ rõ: `THE_LAST_PROTOCOL|state0:state1:...`.

## Phân tích

### 1. RSA có số mũ bí mật nhỏ

`transmission.dat` chứa các số nguyên `n`, `e`, `c`. Thử **Wiener's attack** bằng continued fractions của `e/n` để khôi phục số mũ bí mật `d`. Kết quả:

```text
d = 109597755369341101
RSA plaintext = ORDER:03-01-04-02|NEXT:FRAGMENTS|CHECK:17
```

Vì vậy thứ tự đọc fragment **không phải 01→02→03→04**, mà là **03→01→04→02**. Chuỗi `CHECK:17` được giữ như dấu hiệu trong plaintext; không tự ý suy diễn đây là modulo cần áp dụng cho từng số đo.

### 2. Đọc fragment đa hệ cơ số và dựng đường đi

Mỗi dòng quan sát có dạng:

```text
<channel> | sample=<index> | fmt=<BIN|HEX|DEC> | value=<number>
```

Phải dùng đúng cơ số cho `value` (`BIN` = 2, `HEX` = 16, `DEC` = 10). Tám sample đầu của mỗi fragment có hai channel; sample 08–09 chỉ có một channel và không thuộc lịch sử 32 trạng thái dùng để tạo khóa. Chữ số trong tên sáu channel (`T9`, `K3`, `V8`, `R7`, `M2`, `Q4`) tạo ra chu kỳ trạng thái ứng viên:

```text
9 -> 3 -> 8 -> 7 -> 2 -> 4 -> 9
```

Trong mỗi sample 00–07, chọn số đo thuộc channel có chữ số là trạng thái tiếp theo trong chu kỳ. Mỗi fragment có **2 đường đi ứng viên**, do đó 4 fragment tạo **2^4 = 16** tổ hợp. Chỉ **một** tổ hợp dẫn xuất được khóa Feistel tái tạo đúng test vector trong notebook của ZIP. Điểm bắt đầu của bốn fragment theo thứ tự RSA là `9, 2, 3, 4`.

Lịch sử 32 số thập phân khôi phục được:

```text
28476:44900:25841:59753:5171:4679:55113:51468:46083:31920:58185:21840:25453:39200:4872:56986:32349:57571:50713:11897:48565:18592:6165:12297:12273:53393:56625:49634:47558:55896:8129:10907
```

Ví dụ, fragment 03 có đường đi `9,3,8,7,2,4,9,3`, nên tám giá trị lấy ra lần lượt là `28476,44900,25841,59753,5171,4679,55113,51468`.

### 3. Tạo khóa SHA-256 và xác minh Feistel

Notebook mô tả tám vòng Feistel trên block 64 bit, chia hai nửa 32 bit, big-endian, **không đảo hai nửa lần cuối**. Gọi:

```python
serial = ':'.join(map(str, states)).encode('utf-8')
history = b'THE_LAST_PROTOCOL|' + serial
state_digest = SHA256(serial)
prev = SHA256(history)
for r in range(1, 9):
    prev = SHA256(prev + r.to_bytes(2, 'big') + state_digest)
    K_r = prev
```

Round function lấy **8 byte đầu của mỗi khóa 32 byte** thành hai từ 32-bit. Công thức thao tác tương đương:

```python
MASK = 0xffffffff
k = int.from_bytes(K_r[:8], 'big')
x = (R ^ (k & MASK) ^ ((k >> 32) & MASK)) & MASK
x = (x + r * 0x9E3779B9) & MASK
sh = (3 * r) % 32
x = ((x << sh) | (x >> (32 - sh))) & MASK
x ^= (x >> 13) | ((x << 19) & MASK)
x = (x * 0x045D9F3B) & MASK
F = (x ^ (x >> 16)) & MASK
```

Mỗi vòng áp dụng `(L, R) <- (R, L XOR F(R,K_r,r))`; giải mã bằng cách đảo thứ tự vòng. Test vector **thực tế trong `notebook.pdf` của ZIP**:

```text
Plaintext : 52 45 42 55 49 4C 44 3A  = "REBUILD:"
Ciphertext: BC BB AA 0C 38 91 AC B0
```

Đây cũng chính là 8 byte đầu của `archive.bin`. **Lưu ý:** bản PDF notebook đính kèm riêng trong quá trình phân tích ghi ciphertext khác (`FA D9 24 EE CF 4A DE AF`). Không dùng vector của bản PDF đó cho ZIP này; dùng vector `BCBBAA0C3891ACB0`, được kiểm chứng độc lập với ciphertext gốc.

### 4. Giải `archive.bin`

`archive.bin` dài 24 byte = 3 block × 8 byte. Sau khi giải ngược 8 vòng trên từng block, thu được:

```text
52454255494c443a54484548494444454e07070707070707
```

Bỏ bảy byte padding PKCS#7 `07` ở cuối:

```text
REBUILD:THEHIDDEN
```

Đây là bản ghi khôi phục đầu tiên; `THEHIDDEN` không phải flag cuối.

### 5. Lấy dữ liệu trong JPEG

`archive.jpg` là ảnh JPEG có sẵn trong ZIP, **không phải toàn bộ ảnh được mã hóa trong `archive.bin`**. Comment/metadata chứa:

```text
RECOVERED-BLOCK=d6d5da81f6bfffd0034b
VERIFY=49af4271c75288b0
```

`RECOVERED-BLOCK` là **10 byte** khi giải hex. Có thể đối chiếu metadata bằng cách lấy 16 ký tự đầu SHA-256 của **chuỗi ASCII hex**, không phải bytes đã giải hex:

```python
sha256(b'd6d5da81f6bfffd0034b').hexdigest()[:16]
# 49af4271c75288b0
```

### 6. Giải `final.dat` bằng keystream SHA-256

`final.dat` chứa 65 byte ciphertext viết dưới dạng hex, chia trên nhiều dòng. Đặt:

```python
root = SHA256(history)  # history có prefix THE_LAST_PROTOCOL|
block = bytes.fromhex('d6d5da81f6bfffd0034b')
stream_key = SHA256(root + block)
keystream = b''.join(
    SHA256(stream_key + i.to_bytes(4, 'big'))
    for i in range((len(ciphertext) + 31) // 32)
)
plaintext = bytes(a ^ b for a, b in zip(ciphertext, keystream))
```

Đây là một keystream tạo từ SHA-256, **không phải AES-GCM**. Kết quả ASCII bắt đầu bằng `kBxAc{` và kết thúc bằng `}`, khôi phục đủ 65 byte:

```text
kBxAc{cIPhEr_(h@in_ReCoNs7ru(tEd_31@90F84_FalS3_leAdS_De(iPheRed}
```

## Các hướng sai / bẫy đã kiểm tra

| Hướng | Vì sao không đúng |
|---|---|
| Ghép mọi số đo theo thứ tự xuất hiện | Không tái tạo test vector Feistel; lịch sử phải theo đường đi state machine. |
| Dùng sample 08–09 vào lịch sử | Không khớp 32 trạng thái và khóa đúng. |
| Coi chuỗi `CHECK:17` là phép modulo bắt buộc | Không cần cho nghiệm được xác minh bằng test vector. |
| Dùng vector `FAD924EECF4ADEAF` từ notebook rời | Khác với vector trong ZIP và 8 byte đầu `archive.bin`. |
| Giải trực tiếp `final.dat` bằng AES/nonce tự đoán | Thuật toán thực tế là XOR với keystream dẫn xuất SHA-256. |

## Kết quả

Cả ba tầng đều được kiểm tra độc lập: plaintext RSA xác định thứ tự fragment, Feistel mã hóa lại `REBUILD:` đúng vector, PKCS#7 padding hợp lệ, metadata JPEG có hash kiểm tra, và bước cuối giải toàn bộ ciphertext thành flag định dạng chuẩn.

```text
kBxAc{cIPhEr_(h@in_ReCoNs7ru(tEd_31@90F84_FalS3_leAdS_De(iPheRed}
```

## Tái hiện

**Yêu cầu:** Python 3.9+ (chỉ dùng standard library). Lưu code Python dưới đây thành `solve_the_last_protocol.py`; đặt ZIP tại cùng thư mục hoặc truyền đường dẫn tuyệt đối.

```powershell
python solve_the_last_protocol.py "thelastprotocol (1).zip"
```

**Solver:**

```python
#!/usr/bin/env python3
"""Reproducible solver for HydraRoot's The Last Protocol (stdlib only).

Usage: python solve_the_last_protocol.py '/path/to/thelastprotocol (1).zip'
"""
import hashlib
import itertools
import math
import re
import sys
import zipfile
from collections import defaultdict

SHA = lambda data: hashlib.sha256(data).digest()
M32 = 0xFFFFFFFF
CYCLE = (9, 3, 8, 7, 2, 4)


def wiener_attack(n, e):
    # Continued-fraction convergents of e/n.
    num, den = e, n
    p0, p1, q0, q1 = 0, 1, 1, 0
    while den:
        a, num, den = num // den, den, num % den
        p0, p1 = p1, a * p1 + p0
        q0, q1 = q1, a * q1 + q0
        k, d = p1, q1
        if k and (e * d - 1) % k == 0:
            phi = (e * d - 1) // k
            t = n - phi + 1
            discriminant = t * t - 4 * n
            if discriminant >= 0 and math.isqrt(discriminant) ** 2 == discriminant:
                return d
    raise ValueError('Wiener attack failed')


def read_observations(content):
    obs = defaultdict(dict)
    pattern = r'(\w+) \| sample=(\d+) \| fmt=(\w+) \| value=(\w+)'
    for channel, sample, fmt, val in re.findall(pattern, content.decode()):
        obs[int(sample)][channel] = int(val, {'BIN': 2, 'HEX': 16, 'DEC': 10}[fmt])
    return obs


def candidate_paths(obs):
    solutions = []
    for first in obs[0]:
        path = [int(first[1])]
        for s in range(1, 8):
            following = CYCLE[(CYCLE.index(path[-1]) + 1) % 6]
            if not any(int(ch[1]) == following for ch in obs[s]):
                break
            path.append(following)
        if len(path) == 8:
            solutions.append(path)
    return solutions


def f_round(v, key, r):
    k = int.from_bytes(key[:8], 'big')
    x = (v ^ (k & M32) ^ ((k >> 32) & M32)) & M32
    x = (x + r * 0x9E3779B9) & M32
    sh = (3 * r) % 32
    x = ((x << sh) | (x >> (32 - sh))) & M32
    x ^= (x >> 13) | ((x << 19) & M32)
    x = (x * 0x045D9F3B) & M32
    return (x ^ (x >> 16)) & M32


def feistel(block, keys, reverse=False):
    L = int.from_bytes(block[:4], 'big')
    R = int.from_bytes(block[4:], 'big')
    if not reverse:
        for r, key in enumerate(keys, 1):
            L, R = R, (L ^ f_round(R, key, r)) & M32
    else:
        for r in range(8, 0, -1):
            L, R = (R ^ f_round(L, keys[r - 1], r)) & M32, L
    return L.to_bytes(4, 'big') + R.to_bytes(4, 'big')


def derive_keys(states):
    serialized = ':'.join(map(str, states)).encode()
    full_history = b'THE_LAST_PROTOCOL|' + serialized
    digest = SHA(serialized)
    keys, prev = [], SHA(full_history)
    for r in range(1, 9):
        prev = SHA(prev + r.to_bytes(2, 'big') + digest)
        keys.append(prev)
    return keys, full_history


def main(path):
    with zipfile.ZipFile(path) as z:
        n, e, c = [int(re.search(rb'\b' + name + rb' = (\d+)',
                                 z.read('transmission.dat')).group(1))
                   for name in (b'n', b'e', b'c')]
        d = wiener_attack(n, e)
        rsa_plain = pow(c, d, n).to_bytes((n.bit_length() + 7) // 8, 'big').lstrip(b'\0')
        print('RSA:', rsa_plain.decode())
        assert b'CHECK:17' in rsa_plain
        names = re.search(rb'ORDER:([0-9-]+)\|NEXT:', rsa_plain).group(1).split(b'-')
        order = [int(x) for x in names]
        observations = {f: read_observations(z.read(f'fragment_{f:02}.dat')) for f in order}
        paths = [candidate_paths(observations[f]) for f in order]
        encrypted_archive = z.read('archive.bin')
        solution = None
        for choice in itertools.product(*paths):
            states = []
            for file_no, path_values in zip(order, choice):
                for sample, digit in enumerate(path_values):
                    states.append(next(v for channel, v in observations[file_no][sample].items()
                                       if int(channel[1]) == digit))
            keys, history = derive_keys(states)
            if feistel(b'REBUILD:', keys) == encrypted_archive[:8]:
                solution = states, keys, history
                break
        if solution is None:
            raise ValueError('Unable to verify recovered state history with Feistel vector')
        states, keys, full_history = solution
        print('States:', ':'.join(map(str, states)))
        decoded = b''.join(feistel(encrypted_archive[i:i+8], keys, reverse=True)
                           for i in range(0, len(encrypted_archive), 8))
        padding = decoded[-1]
        assert 1 <= padding <= 8 and decoded.endswith(bytes([padding]) * padding)
        archive_message = decoded[:-padding]
        print('Archive:', archive_message.decode())
        assert archive_message == b'REBUILD:THEHIDDEN'

        jpeg = z.read('archive.jpg')
        recovered_hex = re.search(rb'RECOVERED-BLOCK=([0-9a-f]+)', jpeg).group(1)
        verifier = re.search(rb'VERIFY=([0-9a-f]+)', jpeg).group(1)
        assert SHA(recovered_hex).hex()[:16].encode() == verifier
        recovered_block = bytes.fromhex(recovered_hex.decode())
        print('JPEG recovered block:', recovered_block.hex())

        final_note = z.read('final.dat').decode()
        part = final_note.split('The archive yielded this record:', 1)[1].split(
            "The operator's final note:", 1)[0]
        ciphertext = bytes.fromhex(''.join(re.findall(r'\b[0-9a-f]{10,}\b', part)))
        stream_key = SHA(SHA(full_history) + recovered_block)
        stream = b''.join(SHA(stream_key + i.to_bytes(4, 'big'))
                          for i in range((len(ciphertext) + 31) // 32))
        plaintext = bytes(a ^ b for a, b in zip(ciphertext, stream))
        assert plaintext.startswith(b'kBxAc{') and plaintext.endswith(b'}')
        print('FLAG:', plaintext.decode('ascii'))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'thelastprotocol.zip')
```

**Output kiểm chứng:**

```text
RSA: ORDER:03-01-04-02|NEXT:FRAGMENTS|CHECK:17
States: 28476:44900:25841:59753:5171:4679:55113:51468:46083:31920:58185:21840:25453:39200:4872:56986:32349:57571:50713:11897:48565:18592:6165:12297:12273:53393:56625:49634:47558:55896:8129:10907
Archive: REBUILD:THEHIDDEN
JPEG recovered block: d6d5da81f6bfffd0034b
FLAG: kBxAc{cIPhEr_(h@in_ReCoNs7ru(tEd_31@90F84_FalS3_leAdS_De(iPheRed}
```
