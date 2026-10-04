# notes.md - crypto-cat-3

Input: `files/ciphertext.txt` (180 B, sha256 `742a5555bc13ed0d6336b29673baba2dca97ebfc77ad905989ca4015083233ed`), 179 ký tự, 151 chữ cái, 22 chữ phân biệt.
Định dạng cờ: `cdctf{...}` (đã xác nhận ở crypto-cat-1 và crypto-cat-2 cùng chuỗi).

## H1 - Phep the hoa don theo keyword (mono, but keyed alphabet)
cmd: `python analysis/triage_poly.py` (output `analysis/triage_poly.out`, phần A)
evidence: IC 0.0580 xac nhan mot bang chu cai, nhung doc `nv'llewergp` nhu `we'll...` thi khong co
tu tieng Anh nao khop voi ca `nv'll` va `nvk'n` cung luc (hai tu nay chia chung hai chu dau).
result: DEAD - mono thuan tuy khong doc duoc token co dau nhay, nen phai kiem tra da bang truoc.

## H2 - Vigenere/variant/Beaufort khoa tuan hoan theo chu cai
cmd: `python analysis/triage_poly.py` (phan B va C)
evidence: tu lap `wezmrf` cach 59 chu cai, `kr` cach 75, gcd = 1. Crib `cdctf` cho
`K[0..4]=u,z,u,w,g`, them cach doc `can't` (chu 22-25) va `we'll` (chu 83-86) thi chi L=13 song,
ma 13 khong chia 59.
result: DEAD - khong ton tai do dai khoa tuan hoan theo chu cai.

## H3 - Khoa chay theo moi ky tu (dem ca space, ngoac, nhay)
cmd: `python analysis/triage_poly.py` (phan B va C2)
evidence: khoang cach ky tu cua hai tu lap la 70 va 90, nen L phai chia 10. Chay crib trong chi so
tuyet doi nay: so L song trong 1..20 la danh sach rong cho ca ba phep.
result: DEAD.

## H4 - Autokey (primer + plaintext / primer + ciphertext)
cmd: `python analysis/triage_poly.py` (phan D)
evidence: m = 1..8, ba phep, hai loai keystream; bo dem tu pho thong khong ung vien nao >1. Rieng
m = 3, plaintext-autokey mo dau bang `cdctf{one` roi thoat thanh `eucdwswqybrqvt`.
result: DEAD - doan dau `one` la ngau nhien, doan sau khong ra tu.

## H5 - Phep the hoa don, crib tu dinh dang co
cmd: `python exploit.py files/ciphertext.txt` (output `analysis/solve.out`)
evidence: `wcwpl{` -> `cdctf{`; `pmr`->`the`, `ph`->`to`, `lhf`->`for`, `prdp`->`te?t`; tu lap
`wezmrf` -> `cipher` (e->i, z->p); `leovfrc`->`figured`, `wfqwyrc`->`cracked`, `pmfhvom`->`through`;
`sqpmrsqpewquuj`->`mathematically`, `shghquzmqkrpew`->`monoalphabetic`, `qgc`->`and`, `oetrg`->`given`,
`nvwm}`->`such`. 22 anh xa don anh, ban tho dung 22 chu (bang 22 chu cua ban ma), round-trip 179/179.
result: OK - co: `cdctf{any monoalphabetic sub'stitution cipher can be cracked through sta'tistical
analysis given su'fficient cipher text for the numbers to be figured out mathematically and such}`

## Ghi chu
- Ba dau nhay don la mồi chống wordlist: ba token chua dau nhay deu la mot tu bi cat giua
  (`sub'stitution`, `sta'tistical`, `su'fficient`), khong phai contraction. Vi vay cach doc
  `can't`/`we'll` trong H2/H3 la gia thiet co chu dich, va no dan toi ket luan sai ve Vigenère.
- `prdp` = `te?t`: `test` bi loai vi `s` da la anh cua `n`, nen `d->x` va tu la `text`.
- Ban the day du o `analysis/table.out` (script `analysis/table.py` doc dict truc tiep tu `exploit.py`).

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
