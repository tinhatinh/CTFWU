# Tiep van cho objective v3

Cac buoc den day da dong. Con hai kha nang, va ca hai deu can thu the ma may nay khong co.

## Kha nang A: key HS256 la mat khau dan dien (can GPU)

**DA THUC HIEN, ket qua am.** hashcat 6.2.6 tren RTX 3050 dat 11,6 MH/s. Da chay: rockyou plain (14,3 trieu), best64 (1,10 ty), leetspeak (244 trieu), va vet can hoan toan moi key in duoc do dai <=5 (8,24 ty) - tat ca Exhausted, 0 recovered. Khoan trong `files/jwt.hashcat` va `analysis/hashcat_results.txt`.

Day la gia thuyet co xac suat cao nhat con lai, vi ho giai thich duoc con so: 5/51 team. D dan mobile bo qua JWT, dan web/crypto chay hashcat thi xong.

Target da luu san dang dang thuc hashcat mode 16500 (JWT HS256):

```
# file jwt.hashcat chua 1 dong <header>.<payload>.<signature>
hashcat -m 16500 jwt.hashcat rockyou.txt -r rules/best64.rule
hashcat -m 16500 jwt.hashcat rockyou.txt -r rules/d3ad0ne.rule      # neu can nhieu rule hon
hashcat -m 16500 jwt.hashcat rockyou.txt -r rules/leet.rule
```

Payload cua token la `{"sub":"1001","iat":...,"exp":...}`. Neu no no, gia mai:

```python
import base64, hmac, hashlib, json
def b64(x): return base64.urlsafe_b64encode(x).rstrip(b"=").decode()
def forge(key, sub):
    h = b64(json.dumps({"alg":"HS256","typ":"JWT"},separators=(",",":")).encode())
    p = b64(json.dumps({"sub":sub,"iat":1790405077,"exp":1790491477},separators=(",",":")).encode())
    return h+"."+p+"."+b64(hmac.new(key.encode(), (h+"."+p).encode(), hashlib.sha256).digest())
```

 Roi goi `GET /api/v1/accounts/me` va `GET /api/v1/internal/promo` voi `Authorization: Bearer <forge>`
va `X-Meridian-Client: MeridianPay-Android/3.2.1 (attested)`, thu `sub` = 1000, 1002, 1003, 9999, "admin", "corporate".

Da loai tru cho huong nay: key khong phai tu dien thuan, khong phai rockyou nhan 46 rule, khong phai rockyou nhan ~200 rule (`jwt_deep.py`), khong phai tu 2 tu ghep, khong phai chu sinh tu digest cua bat ky chuoi nao trong APK hoac gia tri co, khong phai gia tri co nay, khong phai 26 hang so nguon. Tong cong khoi da thu: ~2.5 ty candidate.

## Kha nang B: route thu 8 gate bang gia tri khong the doan

Neu A sai thi chi con B: mot route tra ve 404 that khi thieu dieu kien, nen moi cuoc fuzz duoi bat ky tu dien nao cung khong nhin thay no. Du da chung minh:

- 404 o moi nhanh la giong het nhau ( cung md5, 207 byte) => khong co error handler rieng de an route
- ~250 ngan path da thu, gom ca wordlist ten API that tu hien truong (`api-seen-in-wild`, `api-endpoints-res`, `objects`, `actions`, `mazen160`, `raft-medium`)
- da thu ca chu ky day du cua WebView (wv UA, Sec-Fetch navigate, Sec-CH-UA, X-Requested-With, Referer tu trang promo)
- da thu ca gia tri cua chinh 3 co lam gate

Nghia la muon tim tiep thi can source cua bai, khong can them thoi gian fuzz.

## Nhung gi da chac chan ve surface

```
GET  /                      khong can gi                -
POST /api/v1/auth/device    attestation                 -
GET  /api/v1/promo/public   khong can gi                -
GET  /api/v1/internal/promo bearer + attestation        v1
PATCH /api/v1/profile       bearer                      (mass assignment -> v2)
GET  /api/v1/admin/ledger   bearer + role=="admin"      v2
GET  /api/v1/accounts/me    bearer                      v4
```

Key JWT co dinh qua khoi dong lai (token cu van dung), con co thi xoay vong. Hai thu khong cung nguon sinh.
