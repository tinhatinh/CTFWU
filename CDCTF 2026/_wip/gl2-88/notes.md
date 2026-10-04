# notes.md - gl2-88

Input: `files/GL2-88.hs` (4013 B, sha256 `f1c7c3dfd5819a0b7257f03cc99f731fe8329d9acba723436fb5073fa606ccbc`)
Ciphertext: `files/ciphertext.txt` (44 B, sha256 `d83f904893e41d8cae69651272d17326026e340144ca187d695ae3a2e0c80c2f`)
Định dạng cờ đề yêu cầu: `cdctf{...}`

## H1 - Bug `det` là chìa khoá
cmd: đọc `GL2-88.hs:71` -> `det ((a, b), (c, d)) = a*d - c*d` (đúng ra là `a*d - b*c`)
evidence: mọi ma trận keystream đều có dạng `((k, a), (0, 1))` (dòng 2 là `(0,1)`).
Thế vào det lỗi: `a*d - c*d = k*1 - 0*1 = k`, trùng det thật `k*1 - a*0 = k`.
`minv` vì vậy trả về inverse đúng, và `decrypt(key, encrypt(key, pt)) == pt` (đã assert
trong `exploit.py::selftest`).
result: DEAD - đây là red herring, không phải lỗ hổng.

## H2 - Cấu trúc nhóm
cmd: `python -c "from exploit import GRP; print(len(GRP), GRP[1], GRP[12])"`
evidence: `_A *^* a` = shear `((1,a),(0,1))`, `_B *^* b` = `((9^b,0),(0,1))` (9 có cấp 11 mod 67).
`grp = [((9^b, a), (0,1))]` đúng 737 = 67*11 phần tử. Vì `md` (các ma trận sinh từ khoá)
thuộc `grp` nên `grp // md` chỉ là `grp` được sắp lại, không sinh phần tử mới.
result: OK - khung làm việc, không phải điểm yếu.

## H3 - Keystream tách làm hai phần
cmd: `python exploit.py` (ham `structure_report`)
evidence: thu `M_i = ((k_i, a_i), (0,1))` theo 11 ký tự khoá:
- `k_i` lap lai tren 5 khoa ngau nhien, gia tri dau `[14,14,14,14,14,14,14,14,14,14,62,64]`.
  14 = 9^2 mod 67 -> `k_i` chi do cuc ki truc tiep cua `concat (iterate go m0)` quyet dinh.
- `a_i` khop tuyen tinh: `a_i(k) = a_i(0) + sum_t k_t * (a_i(e_t) - a_i(0))` mod 67, sai khac 0
  tren ca 44 vi tri x 5 khoa ngau nhien.
=> `y_i = k_i * x_i - a_i (mod 67)` voi `k_i` cong khai. Toan bo cipher tro thanh affine theo khoa.
result: OK - day la diem yen cua he.

## H4 - Known plaintext + cuoc phieu 67^4
cmd: `python exploit.py` (ham `key_space` + `scan`, known = `cdctf{` 6 vi tri dau + `}` vi tri 43)
evidence: hang so hoa thu duoc `rank=7`, he nhat quan, `bac_tu_do = 4`,
`part = [51,37,10,4,45,10,23,0,0,0,0]`, 4 vector co so tu do nam o 4 ky tu cuoi cua khoa.
Quet toan bo 20.151.121 khoa: ung vien toan `[A-Za-z_]` = 3431, ung vien co >=35/37 vi tri
la chu cai = 197.046. Cham diem bang tu dien 370k tu (`words_alpha.txt`) + mo hinh bigram:
diem ph phu tu cao nhat chi 13/37 ky tu, vap nhat muc ngau nhien.
result: DEAD - khong co chuoi doc duoc trong khong gian.

## H5 - Alphabet thuc su cua cipher
cmd: `python -c "print([ (c, (ord(c)-60)%67, chr((ord(c)-60)%67+60)) for c in '0123456789!@#.-_ ' ])"`
evidence: `s2c` luon tra ky tu trong `[<, ~]`, nen giai ma khong the sinh chu so.
`'0'..'7'` (ma 55..62) hien ra thanh `'s'..'z'`, `'8'/'9'/':'/';'` (ma 63..66) hien ra thanh
`'{' '|' '}' '~'`. Vi vay mot co leetspeak van xuat hien nhu chu cai, nen bo loc `[A-Za-z_]`
dan la du rong cho co that, tr cu co chua `8`, `9`, `:` hoac `;`.
result: OK - giaiii thich vi sao bo loc charset khong phai la nan nhan.

## H6 - Bang gia thuyet ve dau vao
cmd: `python gen.py` (5 gia thuyet A-E trong `gen.py::__main__`)
evidence: A `cdctf{` + `}`@43; B `}`@42 va `'\n'`@43; C prefix hoa `CDCTF{`;
D dao nguoc chieu ma hoa (`x_i = k_i*y_i - a_i`, tuc CT sinh boi lenh `decrypt`);
E nhu A nhung chap nhan toi da 2 ky tu ngoai chu cai.
Ca 5 chieu: dim=4, so ung vien 3357..197046, diem tu thap nhat 8..13/37, khong co ket qua doc duoc.
result: DEAD - moi bien the cua gia dinh dinh dang deu loai duoc.

## H7 - Known-answer test cua chinh solver
cmd: `python solve.py` (ma hoa 3 co gia `cdctf{...}` voi khoa ngau nhien, roi chay toan bo pipeline)
evidence: ca 3/3 co that nam trong tap ung vien loc `[A-Za-z_]` (3390, 3391, 3437 ung vien),
tuc solver + bo loc charset phat hien dung dap an khi dau vao do minh sinh ra.
result: OK - chung minh machine attack dung, van de nam o dau vao.

## H8 - Doi chieu port Python voi GHC that
cmd: `curl -s -H 'Content-Type: application/json' --data @payload.json https://wandbox.org/api/compile.json`
        (source go = `GL2-88.hs` bo shebang, chi thay `main`, trinh GHC 9.10.1 bien dich)
evidence: GHC that in ra `pNW@JXxoFGI`, `Qux\`OtZS\NfEotCec>>G}eRxrJD[XXsMftQy<qmkYsog`,
`737`, va 6 ma trận dau cua `getKeyStream "eOnBEHjC|W@"` =
`[((14,56),(0,1)),((14,34),(0,1)),((14,17),(0,1)),((14,11),(0,1)),((14,33),(0,1)),((14,22),(0,1))]`.
Port Python trung khop byte-by-byte ca 4 vector (da ghi thanh `GHC_VECTORS` + assert trong `exploit.py`).
result: OK - port trung thuc, khong con kha nang "Haskell semantics toi hieu".

## H9 - Khoa la tu dien / cum tu
cmd: `python kdict.py` (254.905 khoa dai 11: tu 11 chu trong tu dien + hoa/thuong + 1 bien the leet + cum tu goi y)
evidence: kiem tra thoa 6 phuong trinh `cdctf{` (xac suat trung hop ~ 67^-6 cho mot khoa ngau nhien,
nen kiem nay gan nhu tuyet doi): 0 khop. Voi 7 phuong trinh cung: 0 khop.
result: DEAD - khoa khong phai tu dien, huong nay dong.

## H10 - Bo gia dinh `}` cuoi chuoi (dim 5)
cmd: `python scanF.py`
evidence: DANG CHAY. Dung `cdctf{` thoi -> rank 6, bac tu do 5 = 1.35 ty khoa, chap nhan ung vien
co >=36/38 vi tri la chu cai. Neu ciphertext bi cat khi paste thi prefix van lo ra co that, nen
phuong trinh nay tra loi duoc kha nang "CT thieu ky tu".
result: PENDING

## Lenh can de tranh thu lai
- `python exploit.py` : tu kiem chung + do khong gian khoa ( chay ~40 giay).
- `python solve.py`   : known-answer test 3/3.
- `python kdict.py`   : kiem khoa tu dien.
- `python scanF.py`   : dim 5 khong gia dinh `}`.

---
Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
