# Kintsugi Vault - notes

## K1. Handout
`handout.tar.gz` 347257 B, sha256 `4ce8375d99e0239992b6d2cb75a380cdf1c1747a94e9c06a1c81a9cc54e619c9`:
- 7 x `<32hex>.shard` (1211 B each)
- `vmrun` 776288 B, ELF x86-64 static, stripped, no PIE, sha256 `8b16608a78c81341dbf130007cd0a799c6e51633cdbd759d5274f6d622887d4f`
- `pubkey.bin` 32 B = `5a0239a82fba9d2d5c6c5418e237ed8a888baeced6f4c32aa71e7be3805775ee`
- `MANIFEST.txt`: team `team-local`, chain start `f6f11ad133cab21c96e0185e3411ddc4`, "shards are named by content id; order is not preserved on disk"
- `README.md`: usage `./vmrun <shard-file> <16-hex-key> [decode-table-file]`; `GET /attest` -> nonce, `POST /attest` form `nonce` + `sig` (hex) -> flag

## K2. Chay duoc vmrun?
Khong: may khong co docker/podman/qemu, WSL chua cai. Toan bo phai tai dung VM bang Python (xem K4).

## K3. Dinh dang shard (doc tu main cua vmrun)
```
0x00  4  'KSHD'
0x04  1  version (01)
0x05  1  flags: bit0 = 1 -> decode table nam trong file (0x32); bit0 = 0 -> BAT BUOC co file bang o ngoai
            (chu y: bit1 khong bao gio duoc kiem tra; flag 0x00 va 0x02 giong het nhau)
0x07  1  keylen = 08
0x08  2  u16 tablelen = 0x100
0x0a  2  u16 proglen  = 0x289 (649)
0x0e 16  content id  = ten file hex            <- KHONG duoc verify bao gio
0x1e  4  ? random                                <- khong duoc doc
0x22 16  'next' id, bi lam nan; = 0 o cfa1fa34   <- khong duoc doc
0x32 256 decode table (raw opcode -> so thu tu handler)
0x132 256 sbox (LUT), luan hoan, luon lon trong suot
0x232 649 chuong trinh
```
Check trong main: `size > 0x31`, `dword[0]=='KSHD'`, `size >= 0x132 + tablelen + proglen`
(`0x132 = 0x32 header + 0x100 sbox`). File bang ngoai: chi can `> 0xff` byte, **copy nguyen 0x100 byte
vao stack**, khong hoa tron voi bytes trong file, khong kiem tra noi dung (0x4030b2/0x4030cb).
Key: 16 ky tu hex, khong phan hoa hoa/thuong, SSE nibble decode, ghi 8 byte lien tiep tai rsp+0x58.
Header id/next **khong bao gio duoc kiem tra** -> day la manh/rei cho chung ta dung.

## K4. ISA (lay tu bang nhay 0x486ba8, da doi gia tri co dau)
`op = table[prog[pc]]`; 0 -> HALT (in "OK", exit 0); >13 -> "bad opcode" (exit 2);
`pc >= proglen` cung duoc coi la thanh cong. Sau moi lenh: `pc += width`.

| op | lenh | do dai | nghia |
|----|------|--------|-------|
| 0 | HALT | 1 | dung, OK |
| 1 | KEY  | 3 | `rA = (u32)mem8[0x58 + B]`  (B 0..7 = key; B>=8 doc sang ca table!) |
| 2 | MOVI | 6 | `rA = imm32` |
| 3 | MOV  | 3 | `rA = rB` (de diem = toan tu dau) |
| 4 | XOR  | 3 | `rA ^= rB` |
| 5 | ADD  | 3 | `rA = (rA + rB) mod 2^32` |
| 6 | MUL  | 3 | `rA = (rA * rB) mod 2^32` |
| 7 | AND  | 3 | `rA &= rB` |
| 8 | OR   | 3 | `rA |= rB` |
| 9 | ROL  | 3 | `rA = rol32(rA, B & 31)`  <- B la **imm8**, khong phai register |
| 10 | LUT | 3 | `rA = (u32)sbox[rB & 0xff]` (xoa 24 bit tren) |
| 11 | CMP | 6 | neu `rA != imm32` -> FAIL (exit 1) |
| 12 | ANDI| 6 | `rA &= imm32` |
| 13 | XORI| 6 | `rA ^= imm32` |

Register file: 12 o 32-bit tai rsp+0x30..0x57; `rep stos` chi xo **8 o dau** (rsp+0x30, ecx=8);
o 10/11 trung voi 8 byte key; index >= 12 ghi doc ngay vung table -> tu-modify duoc dispatch,
>= 0x4E cham canary/retaddr (khong shard nao dung den).

## K5. Phan loai shard
- Kieu A (3 vong LUT + tron XOR, CMP la 8 byte): `f6f11ad1` (start, flag 01), `080ec62d`, `3e3a0fc9`, `cfa1fa34` (flag 02, next=0)
- Kieu B (1 vong KEY->LUT->ADD->ROL->MUL->OR->XORI, CMP 32-bit): `3df10ef4`, `63bafd7f`, `f14ad4e2`
- 4 shard kieu A tu giai ma sach bang chinh table trong no (hoac chuyen template tu f6f1) -> 186/177 lenh, ket thuc HALT@648, dung 8 lenh CMP.
- 3 shard kieu B cung tu giai duoc nhung **ham kiem tra rat yeu**: da phan tich tay cho 3df1 thay co khoang 528 key duoc chap nhan -> chung la nai danh da (mesh), khong chieu mang seed.

## K6. "Chat keo" that su
 Voi shard khong co flag bit0, `vmrun` doi file bang 256 byte o ngoai. Ba shard `080ec62d`,`3e3a0fc9` co the
**phuc hoi bang** bang cach chuyen dung day (pc, op) cua `f6f11ad1` sang: moi raw byte tai cung vi tri
phai map cung op, va vi table that la hoan vi nen khong duoc xung dot. Ca hai khop sach (0 conflict).
`cfa1fa34` khong khop template (no dung 5 vong ANDI thay vi 4 nen vi tri lech); bang cua no doc truc tiep:
`f7=KEY 79=XORI 4e=ANDI d6=LUT 4c=XOR c1=MOV bc=CMP 44=HALT`,i chang = 175 lenh, HALT@648.

## K7. Dao nguoc key
Chuong trinh kieu A la mot khoi ma 64 bit: KEY (8 byte doc lap) -> (XORI/ANDI) -> LUT -> tron tuyen tinh GF(2) -> ... -> CMP.
Chay nguoc tu 8 CMP ve dau: XOR/XORI/LUT/MOV/KEY/ROL de dao; ANDI de lai bit bi anh huong (tu do).
-> moi shard cho 16..64 key hop le (vi cac bit ANDI huy). **Ban quan trong**: khi liet ke bien the
phai *ep ca 0 lan 1* cho bit tu do; chỉ "bật" bit se mat nua khong nghiem (day la loi lam minh
tim khong ra seed o lan chay dau tien).

## K8. Seed
Thu 24 thu tu x bien the key, doi chieu `pubkey.bin` (Ed25519, `cryptography` 50.0.1, da cross-check
bang `ed25519/ed.py` thuan Python khop 3 vector RFC 8032):

```
seed = f860622f78adc147 0aba129efad830d8 1b091cc9cc9b71ee a4b10c57af5dd7af
       f6f11ad1          3e3a0fc9           080ec62d            cfa1fa34
derive(seed).pubkey == pubkey.bin   -> True  (xac nhan noi tai, k can server)
```
Thu nguoc lai: gop 8 byte CMP-dich cua 4 shard, gop XORI/CMP immediates, moi cua so 32 byte trong
toan bo handout, cap 16-byte field... -> khong match. Chi co chu thuat toan tren la dung.

## K9. Server
- GET /attest: 24 byte ngau nhien, 48 ky tu hex + \n, 49 byte body, khong Set-Cookie, gunicorn.
- POST /attest (nonce + sig): **400 `attestation incomplete`** voi MOI bien the:
  sig tren 24 byte thô / chuoi hex 48 ky tu / +\n / sha256 / sha512 / nonce+pubkey / pubkey+nonce /
  nonce+seed / seed / JSON thay form / query-string thay body / base64 / hex hoa /
  them field `seed`,`chain`,`shards`,`pubkey`,`team`,`key`... (100+ cap net + 40 lan GET+POST lien tuc
  tren CUNG TCP connection de loai truri thuyet nonce nam o per-worker). Khong bao gio thay doi thong bao.
- Chu tyr cua chunmg ta verify OK duoi `pubkey.bin` (tự kiem tra local).
=> Nghi ngor lon nhat: handout (`team: team-local`) khong gan voi instance `web-d6403eb95a65eea4`,
   tuc la instance dung cap khoa khac. Can tai lai handout tutrang instance hoac khoi dong lai instance.

## K11. Lop bot HTTP da thu (khong co oracle de tim)
- `OPTIONS /attest` -> `Allow: GET, POST, OPTIONS, HEAD`; PUT/PATCH/DELETE -> 405. Chi co `/attest`
  (`/attest/`, `/attest/submit`, `/flag`, `/unseal`, `/verify`, `/api`... -> 404 cua Flask).
- Body GET luon la 48 hex + `\n` (49 byte). Da thu gui nonce **co** va **khong** co `\n`, va ky
  tren ca hai dang.
- `multipart/form-data` (t boundary) vs `application/x-www-form-urlencoded` vs JSON vs
  query-string: tat ca 400 giong het nhau.
- Field bia: `sig`, `signature`, `seed`, `pubkey`, `chain`, `shards`, `ids`, `team`, `key`,
  `root`, `custody`, `vault`, `agent`, `shard`, `id`, `proof`, `token`, `answer` -> khong doi phan ung.
- Thong bao **giong het nhau** cho: `sig="zz"` (hex khong hop le), `sig` sai do dai, thieu `nonce`,
  thieu `sig`, POST rong, nonce khong bao gio duoc cap. => server khong co bat ky oracle nao de
  phan biet "nonce khong duoc biet" vs "chuu ky sai" vs "thieu field". Khong the tim kiem hop dong
  theo kieu brute-force.
- 40 cap GET+POST lien tiep tren CUNG ket noi TLS (http.client keep-alive) -> 40 lan that bai,
  loai bo (phan lon) gia thuyet nonce luu theo gunicorn worker.
- Ket luan: voi handout nay thi endpoint hien tai khong the thoa man. Hoac no dung cua instance
  khac (keypair khac), hoac state nonce cua no hong. Can instance moi.

## K13. bằng chứng định lượng rằng server không tới bước verify
- Handout tải lại sau khi instance khởi động: **sha256 giống hệt** (`4ce8375d...619c9`),
  `pubkey.bin` cũng giống hệt => artifact là tĩnh, cặp khóa dùng chung mọi team.
- 60 lần nộp **cùng một** (nonce, chữ ký hợp lệ) trên một kết nối: 60x400 như nhau
  => loại "nonce lưu theo worker/replica" (xác suất tuột cả 60 lần ~ 1e-8 với 4 replica).
- Độ trễ POST khi dùng nonce thật vs nonce bịa: median 117.82 ms vs 117.61 ms (độ lệch
  0.2 ms, stdev 1.77 ms) => không có đường nào chạm tới phép verify Ed25519 (~60-100 µs).
- Trình duyệt thật (same-origin, có đủ header, `credentials:'include'`, `document.cookie`
  rỗng cho `.h7tex.com`) cũng nhận y hệt => không phải cookie/UA/CORS.
- 23 cách dựng thông điệp x 3 vòng (raw/ascii/kèm \n/json/label/pub+nonce/nonce+pub/seed+nonce/
  sha256/sha512[:32]/upper/reversed + HMAC-SHA256(seed) + HMAC(pubkey) + sha256(seed||nonce)):
  tất cả trả cùng một xâu lỗi.
- `?debug=1`, `Accept: application/json`, `X-Requested-With` không đổi phản hồi.

Kết luận làm việc: phân tích bài toán đã đóng và được chứng minh bằng toán học
(`Ed25519_pubkey(seed) == pubkey.bin`), nhưng instance hiện tại không chấp nhận bất kỳ attestation
nào, kể cả nghiệp vụ đúng theo README. Đây là dấu hiệu instance/app hỏng (hoặc khóa của app không
phải khóa trong handout). 3 team đã solve => trước đó nó từng hoạt động.

## K15. NGUYÊN NHÂN THẬT: handout mẫu != handout của instance
Kết luận "instance hỏng" ở K13/K14 là **SAI**. Sự thật:

- `GET https://<instance>/handout.tar.gz` -> **200, 318172 byte**, sha256
  `6bbfc07a1d0066b84ce66be4a4250a61bc3f9930a90989b13b3a9667bc4063f5`
  - KHÁC bản tải từ trang challenge (347257 byte, `4ce8375d...`).
- Bản của instance có: `pubkey.bin` = `5b0a2f8195a3f59374f2cb71d1ba95ef5c5795645889f96d07563c6bcaa58a14`,
  7 shard với id hoàn toàn khác, chain start `35e266269ee507306702849122c57a71`, mtime 08:02 hôm nay.
- Chạy lại đúng pipeline trên artifact thật -> 4 guardian byte-target (1 shard start dùng bảng trong
  suốt của nó + 3 shard bảng nhiễu phục hồi bằng tìm kiếm gán raw->op) -> 4 mãnh 8 byte:
  `185087fcdd31641e` (35e26626), `58f77177f104cded` (80014ce5),
  `f29bb38be31bf782` (42b1de23), `8dd0b1fab65c4746` (aaae515b)
  -> `seed = 185087fcdd31641e58f77177f104cdedf29bb38be31bf7828dd0b1fab65c4746`
  -> `Ed25519_pubkey(seed) == pubkey.bin` của instance (khớp).
- `POST /attest` với `sig = ed25519_sign(seed, bytes.fromhex(nonce))` -> **200**
  `H7CTF{9df8f215-6ef3-4ee2-a336-42d628680738}` (mặc định là chữ ký trên 24 byte thô, KHÔNG phải
  trên chuỗi hex).

Bài học: khi một hosted instance từ chối credential đúng, **hỏi chính instance lấy artifact**
(`/handout.tar.gz`, `/pubkey`, ...). Tệp tĩnh trên trang challenge có thể là bản mẫu của tác giả
(`MANIFEST: team: team-local` là tín hiệu). Toàn bộ suy luận "server không parse sig / không tới
verify" đều đúng về mặt kỹ thuật nhưng dẫn tới kết luận sai vì nó mặc định khóa trong handout mẫu
là khóa của instance.
1. Báo BTC/WebVerse: `POST /attest` trên `web-d6403eb95a65eea4.web.h7tex.com` trả
   `attestation incomplete` cho mọi request, kể cả chữ ký Ed25519 hợp lệ trên nonce vừa cấp
   (kèm bằng chứng K13). Xin một instance mới hoặc xác nhận khóa mà app mong đợi.
2. Khi có instance chạy được: `python exploit.py` (đã tham số hóa URL) -> ghi `flag.txt`.
3. Cập nhật `writeup.md` mục 7 + `README.md` của CTFWU sau khi có cờ.

## K12. Tim cờ offline: khong co
`flag_sweep.py`: 53 blob (toan bo file + table/sbox/code/header cua tung shard + cac bang phuc hoi
+ seed) x ~30 cach ma hoa (raw, utf16le/be, rev, rot13, hex, b64/b64url/b32 voi 4 offset,
b64-of-utf16, zlib, nibswap, xor 1..7, add/sub 1..3) voi cac needle `H7CTF/FLAG/CTF{/WEBVERSE`.
15 "hit" deu la trung hop trong du lieu nhi phan (b32/b64 cua vmrun va shard). Quet chuoi trong
ngoac `{...}` chi ra cac chuoi nhi phan ngau nhien. => cờ chỉ có ở endpoint.

## K10. Cong cu trong thu muc nay
`vm.py` (ISA + emulator + disassembler), `isa.py` (doc bang nhay), `glue.py` (chuyen template -> phuc hoi bang),
`invert.py` (solver chay nguoc), `chain_solve.py` (ghe seed), `solve.py` (toan bo pipeline mot lenh:
tu do bang -> key -> seed, tai tao dung seed tren handout nay), `seed.hex`, `ed25519/` (oracle thuan
Python + tu kiem RFC 8032),
`hdr_probe.py` `table_probe.py` `table_struct.py` `link_probe.py` `big_hunt.py` `order_hunt.py` `seed_hunt.py` (cac gia thuyet da loai bo),
`attest_probe.py` `attest2.py` `msg_sweep.py` (thu hop dong HTTP), `vmrun.asm` (disasm day du).
