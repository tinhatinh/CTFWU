# Flappy Board — Misc (Intermediate)

**Flag:** `CSSCTF{birdddd}` · **Files:** `flappy_board` 43736 B sha256 `c07bd450...`

## Đề bài

Đề chỉ cho một binary `flappy_board` và nói phải qua ba khu vực relay trong 20 phút. Không có URL instance trên thẻ đề. Binary là client của một game flappy-bird chạy trong terminal; điểm được server duyệt lại, và cờ do server trả.

## Phân tích ban đầu

`file` báo ELF 64-bit PIE, stripped, động; entropy 4.700 nên không có khối payload nào giấu trong file. Imports cho thấy hai nửa: `XOpenDisplay`, `XDrawString`, `XNextEvent`, `XLoadQueryFont` (game cần X11, không chạy được trên máy không có display) và `curl_easy_*` (nói chuyện với server). `rabin2 -z` lộ toàn bộ giao thức:

```
Usage: %s [--server https://host] [--snapshot file.ppm]
http://34.116.80.78:8765        .rodata 0x8920, và .data 0xb060 (giá trị mặc định)
/api/attempt  /api/practice  /api/practice/check  /api/complete
Authorization: Bearer %s        round seed target wait_seconds remaining_seconds token flag
```

Help text của chính client gọi địa chỉ nan đó là "the configured event server", và `GET /` trả `error=Start+a+new+attempt+first.` nên endpoint còn sống: thẻ đề không thiếu dữ kiện.

Hai hàm quyết định mọi thứ: `FUN_00106c0f` khởi tạo trạng thái và `FUN_00106cfe` tiến một tick. Vật lý là số nguyên fixed-point đơn vị 1/256 px, tick 1/60 s, ống sinh bằng `xorshift32` (`FUN_00106b88`, `FUN_00106bc6`) với seed do server phát. Nghĩa là replay chỉ gồm các số nguyên "tick nào flap", và server mô phỏng lại được y hệt.

## Các hướng đã loại

Trước khi chốt đã kiểm tra và loại các kênh sau (log đầy đủ ở `notes.md`):

1. **Đi hỏi URL instance**: endpoint nan sẵn trong `.data`; probe `GET /` xác nhận server sống. Loại.
2. **Tìm cờ trong binary**: không có khối entropy cao, không có chuỗi `CSSCTF`; key `flag` chỉ được parse khi `round == 4` trong response của server. Loại.
3. **Parse response bằng JSON**: server trả `key=value` urlencoded; parser JSON cho `{}` nên request sau đó thiếu Bearer token và báo "Start a game session before practice". Loại.
4. **Nối danh sách flap bằng `&`**: `400 Malformed request`; xâu phân cách trong binary ở `0x874a` là `,`. Loại.
5. **Hiểu `ticks` là số phần tử flap**: `400 Invalid flap tick` khi gửi `flaps=0,2` với `ticks=2`; đúng ra `ticks` là số tick của chuyến bay. Loại.
6. **Gọi `/api/attempt` sau mỗi lần complete**: nó reset session về `round=1` với seed mới, khiến complete round 2 ăn `422 Virtual waiting timer has not completed` rồi `409 Round order mismatch`. Tham số round kế đã nằm trong response của `/api/complete`. Loại.
7. **Chờ cả departure timer lẫn thời gian bay**: 180+19.9 + 360+36.0 + 600+52.1 = 1248 s > 1200 s, round 3 nhận `410 The session deadline has expired, including practice time.` Loại.

## Chuỗi khai thác

**Bước 1 — Dựng lại một tick.** Dịch đúng thứ tự của `FUN_00106cfe`, vì mọi sai lệch một đơn vị cũng làm server tính ra điểm khác:

```python
if flap: self.v = FLAPV            # -1724
self.v = min(self.v + GRAV, VMAX)  # +67, clamp 2048
self.y += self.v
self.tick += 1
for p in w.pipes: p[0] -= SPEED    # 717
if out_of_bounds(self.y): self.dead = 1
for p in w.pipes:                  # va cham va tinh diem, cung mot vong
    if XLO < p[0] < XHI and collide(p, self.y): self.dead = 1
    if not p[2] and p[0] < XLO:
        p[2] = 1
        if not self.dead: w.score += 1
for p in w.pipes:                  # tam = max(x) + 69120, khe = xorshift32() % 231 + 125
    if p[0] < RECYCLE: ...
```

**Bước 2 — Tìm đường bằng beam search.** Vị trí ống hoàn tất do `seed` và số tick, không phụ thuộc vào người chơi, nên trạng thái chỉ còn cặp `(y, v)`. Beam 600 trạng thái, ưu tiên ứng viên gần tâm của ống gần nhất:

```python
flaps, msg = solve(seed, target)   # danh sach tick can flap
```

**Bước 3 — Kiểm chứng mô phỏng bằng practice oracle.** `POST /api/practice` trả `seed` miễn phí (chung đồng hồ session), và `/api/practice/check` trả `verified_score` do server tự tính. Đây là phép đối chiếu rẻ nhất:

```
target=5  715 ticks, 45 flaps  -> verified_score=5&complete=1&cheated=0
target=9  1100 ticks, 50 flaps -> verified_score=9&complete=1&cheated=0
```

**Bước 4 — Chơi ba round.** `wait_seconds` là 180, 360, 600; tổng đã 1140 s trên trần 1200 s, nên chỉ chờ đúng departure timer rồi gửi complete, không cộng thời gian bay. Thân gửi:

```python
body = "round=%d&wait_ms=%d&ticks=%d&score=%d&flaps=%s" % (
    rnd, wait * 1000, s.tick, s.score, ",".join(str(x) for x in flaps))
```

**Bước kiểm chứng.** Cả ba round trả HTTP 200 và response của round 3 chứa `round=4&...&flag=CSSCTF%7Bbirdddd%7D`; URL-decode ra `CSSCTF{birdddd}`. Chuỗi đến nguyên văn từ server, không phải suy luận.

## Flag

```bash
python exploit.py
```

```
[    0.5s] session: {'round': '1', 'seed': '125677873', 'remaining_seconds': '1200', 'limit_seconds': '1200', 'target': '10', 'wait_seconds': '180'}
[    3.2s] round 1 seed=125677873 target=10 wait=180s left=1200s | 1197 tick, 45 flap, score 10
[  181.6s] complete r1 -> 200 round=2&seed=2859321718&remaining_seconds=1019&target=20&wait_seconds=360
[  185.4s] round 2 seed=2859321718 target=20 wait=360s left=1019s | 2161 tick, 93 flap, score 20
[  542.7s] complete r2 -> 200 round=3&seed=2808984917&remaining_seconds=658&target=30&wait_seconds=600
[  548.1s] round 3 seed=2808984917 target=30 wait=600s left=658s | 3125 tick, 180 flap, score 30
[ 1143.9s] complete r3 -> 200 round=4&seed=870498010&remaining_seconds=57&target=0&wait_seconds=0&flag=CSSCTF%7Bbirdddd%7D
FLAG: CSSCTF{birdddd}
```

Cờ đến nguyên văn từ response của server; `CSSCTF%7Bbirdddd%7D` là dạng urlencoded của
`CSSCTF{birdddd}`. Lần chạy này dùng bộ seed khác hoàn toàn so với lần đầu
(`analysis/run3.log`), mỗi round server phát một `seed` mới.

## Reproduce

```bash
python exploit.py                 # ~19 phút, log từng round; --practice để chỉ đối chiếu vật lý
```

`analysis/` giữ `sim.py` (bản mô phỏng tách riêng), `bot.py` (lớp HTTP), `run.py`/`run2.py`/`run3.log` (hai lần chạy thất bại được mô tả ở mục Các hướng đã loại và lần thành công đầu tiên), `reproduce.log` (output của lệnh ở trên) và `decomp.c` (bản decompile Ghidra 12.1.4 của toàn binary). Token session trong các log đã được cắt còn 6 ký tự đầu.
