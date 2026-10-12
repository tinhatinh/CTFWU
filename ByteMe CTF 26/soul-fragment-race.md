---
title: "Soul Fragment Race"
category: "Web"
tags: ["flask", "session-cookie", "business-logic", "state-accumulation", "options-oracle"]
solve_date: "2026-10-09"
language: "vi"
---

# Soul Fragment Race

**Flag:** `OWASP{byteme_soul_fragment_race}`
**Dịch vụ:** `https://byteme-soul-fragment-race.onrender.com` (Flask chạy sau gunicorn, fronts bởi Cloudflare).

## Đề bài

Soul Fragment Race (Web, Hard, 300 điểm, 2 lời giải). Cookie phiên giải mã ra `{"uid": N}`. Cần làm `claim` chấp nhận để trả cờ.

## Phân tích

Các route bổ sung định vị bằng oracle OPTIONS:

```text
POST /vault/recover
POST /vault/verify
POST /vault/claim
GET /api/events
```

Một lần `claim` với đúng một proof trả về:

```text
403 {"error":"the final fragment resists a single proof","hint":"the keeper expects contradictory proof"}
```

Luồng thành công là hai lần `recover` tuần tự cách nhau hơn ba giây. Trạng thái ledger quan sát được giữ proof `verified` của attempt đã hết hạn; `claim` chấp nhận sau khi tài khoản có hai proof trái ngược. Kết quả này cho thấy lỗi quản lý trạng thái trong luồng đã thử, không loại trừ mọi race condition khác.

## Lời giải

Dùng một tài khoản mới (state ledger là theo tài khoản), thực hiện `recover` → đợi hết cửa sổ 3 giây → `recover` lần hai để tài khoản tích luỹ hai proof trái ngược, rồi `claim`. Kết quả ghi từ `soul/mech2.py` / `soul/race.py`:

```text
claim#2 (0.2301, 200, '{"flag":"OWASP{byteme_soul_fragment_race}","status":"awakened"}')
```

`claim` trả `200` kèm cờ; trạng thái chuyển `fragments 6 → 7`, `awakened: true`, và có một mục `events` tên `vault_awakened`.

## Kết quả

```text
OWASP{byteme_soul_fragment_race}
```

Cờ đọc trực tiếp từ dịch vụ qua `POST /vault/claim`. Chưa lưu phản hồi submission.

## Tái hiện

Cần instance còn hoạt động và một tài khoản mới. Dùng cùng session cho luồng `recover` → chờ quá 3 giây → `recover` → `claim`. Bản ghi hiện có không kèm đầy đủ request body hay solver nên chưa đủ để tự động tái hiện toàn bộ luồng.
