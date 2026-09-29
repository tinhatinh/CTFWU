---
title: "Where the Light Fails to Fall - OSINT"
date: 2026-09-29 23:31:27 +0700
lastmod_at: 2026-09-29 23:31:27 +0700
categories: [OSINT]
tags: [pointer-overflow, OSINT]
image:
  path: /CTFWU/Pointer%20Overflow%20CTF%202026/where-the-light-fails-to-fall/files/de.png
---
**Điểm:** 400 · **Wave:** 1 · **Cờ:** `POCTF{99.612.WTT7UHE5X3JIJMKQ.TO6LBQYYORFL6LLPF6Q22SRR2P}`

**Artifact:** `files/PXL_20260621_181159681.jpg` (3.940.516 B, sha256 `42b362b6…520a14a`) và bản
PNG đã giải mã `files/photo.png` (3000x4000, sha256 `2a25a576…a40339`). Ảnh là một con bồ câu
đứng trên nền đá khối, bóng đổ sang phải, kèm một nét đỏ chỉ hướng bắc thật.

## Đề bài

Tác giả kể rằng mùa hè năm đó đi du lịch và chụp con bồ câu ở "mọi thành phố lớn". Nhiệm vụ là
tìm ra thành phố nào, chỉ dựa vào ba manh mối: tấm ảnh, nét đỏ đánh dấu hướng bắc thật, và thời điểm
quan sát của team là `2026-06-20 · 19:55 · UTC+02:00`. Nộp tên thành phố vào `#city-input`; nếu
đúng thì server trả cờ về và tự đổ vào `#flag-input`.

## Phân tích ban đầu

Hai việc làm ngay và có kết quả thật:

**Lấy đúng file gốc.** Thẻ `<img>` trỏ `/challenges/where-light-falls/photo`. Request này cần
cookie phiên (curl trần nhận 401), nên đọc qua tab đang đăng nhập bằng `browser-use`. Phản hồi
mang `content-disposition: inline; filename=PXL_20260621_181159681.jpg`, tức là tên file gốc của
một chiếc Google Pixel, chụp 2026-06-21 lúc 18:11:59 giờ máy. Đây là dữ liệu tốt hơn nhiều so với
`photo.png` mà mình đang giữ, và nó là một sơ suất của server: file gốc vẫn được serve, chỉ là
không có link nào trỏ tới tên của nó.

**Đo nét đỏ.** Nét đỏ là đồ hoạ thuần nên tách được chính xác theo màu
(`R > 120 && R-G > 55 && R-B > 55`), rồi tách thành phần liên thông để loại mắt và hai bàn chân
màu hồng của con chim cũng rơi vào ngưỡng đỏ đó:

```text
nét north : (544, 3103) -> (2386, 3864)   dài 2029 px, dày ~15 px
hướng đơn vị (x phải, y lên): (-0.92429, +0.38169)   góc 157,561°
nhãn "N"  : thành phần tại (434, 3015) 84x110, nằm ở đầu trên-trái -> đầu mũi tên hướng lên-trái
mắt chim  : (1048, 1784)      chân đặt: bbox (1207,2559) 179x146 -> điểm thấp nhất y = 2705
```

Bóng của con chim tính từ điểm chân chạm đất tới chóp bóng là `(910, -925)` trong toạ độ y hướng
xuống, tức dài ~1.298 px và chếch 45,5° so với phương ngang. Chiều cao dựng của con chim (đỉnh đầu
y ≈ 1700 xuống bàn chân y = 2705) là ~1.005 px.

Con số 1.298 / 1.005 = 1,29 chính là chỗ khiến mọi hướng hình học sụp đổ, như phần dưới giải thích.

## Các hướng đã loại

Toàn bộ log nằm ở `notes.md`; đây là bốn nhánh chính và bằng chứng phản bác.

1. **Ảnh phẳng (coi mặt đất song song với mặt phẳng ảnh).** Khi đó góc giữa nét bắc và bóng đo
   ngay trong ảnh chính là phương vị mặt trời: 157,561° − 45,5° = 112,1° → mặt trời ở 292,1°, và
   cao độ = `atan(1005/1298)` = 37,8°. Nghịch đảo cặp (292°, 38°) cùng thời điểm 17:55 UT cho một
   điểm trên bờ đông bắc Brazil. Nhánh này dẫn tới đúng một cụm thành phố nên đã bị nộp thử và
   bị từ chối toàn bộ: Fortaleza, Recife, Natal, Maceió, João Pessoa, Olinda, Teresina, São Luís,
   Aracaju, Salvador, Campina Grande, Mossoró. Loại.
2. **Mô hình affine có hệ số nén `s` tự do.** Với nét bắc và bóng đã đo, `tan ψ = 2,4154 s` và
   `tan(B − ψ) = 1,2825 s`, nên `B ≤ 119,6°` và phương vị mặt trời bị chặn trên ở 299,6°. Muốn
   cao độ rơi vào khoảng 8-19° (đúng tầm buổi chiều mùa hạ ở châu Âu) thì phải có `s ≈ 0,2`, nhưng
   `s = 0,2` lại kéo phương vị xuống ~220°. Hai ràng buộc xung đột trực tiếp. Loại.
3. **Hiệu chuẩn phối cảnh từ mặt lát đá.** Đây là chỗ đáng thất vọng nhất. Đá ở đây là đá khối
   đẽo tay, viên bo tròn, kích thước lệch nhau và mạch vữa uốn lượn, nên không có hai họ đường
   thẳng đủ dài và đủ đều để bắt vanishing point. Phổ Fourier 2D khoá vào hạt granite chu kỳ
   25-50 px chứ không khoá vào lưới đá; khi đã blur sigma 24 để diệt hạt thì phổ không còn đỉnh
   nào sắc (hai "chu kỳ" trả về đúng giá trị bin của cửa sổ ở mọi vị trí). Một đỉnh "coherence"
   trông rất đẹp ở (-4482, 193) hoá ra là gradient chiếu sáng toàn ảnh, không phải mạch đá: nó
   không nằm trên đường chân trời suy ra từ kích thước đá. Không có `f` và không có đường chân
   trời thì không có nghiệm duy nhất. Loại.
4. **Giải 3D nghiêm túc.** Với giả thiết phương ảnh nằm ngang, quét `f ∈ [2200, 5000]` và dòng
   chân trời `y_h ∈ [-4000, +200]`, dựng lại chóp bóng trên mặt đất rồi tìm cao độ sao cho tia
   máy ảnh qua đỉnh đầu cắt đúng tia nắng: kết quả trượt liên tục, `az 259..296` và `alt 17..56`
   tuỳ `(f, y_h)`, mỗi thành phố lớn đều có một bộ tham số khớp trong 2°. Nghĩa là mô hình này
   có khả năng biểu diễn mọi đáp án, tức là không có khả năng phân biệt. Loại.

Cũng đã loại bằng bằng chứng: reverse image search (Bing trả về đúng loài *Columba livia*, Google
Lens mục "Exact matches" báo không có kết quả, nên ảnh không nằm trên web), metadata (không
GPSInfo, không ExifIFD, một EOI duy nhất, 0 byte sau EOI), và stego giữa PNG với JPEG (pixel
giống hệt nhau).

## Chuỗi khai thác

**Bước 1 - Đọc lại hành vi của endpoint.** `POST /challenges/where-light-falls/answer` chỉ so
chuỗi. Probe bằng các giá trị đặc biệt cho thấy không có oracle nào:

```text
""  -> 400 {"correct": false, "message": "Enter a city name."}
"*" -> 200 {"correct": false, "message": "That's not the city the light points to."}
{"city": true}  -> 500            (server gọi .strip() trên bool)
{"city": []}, {"city": {}}, {}    -> 400
```

Không có phân biệt "tên không hợp lệ" với "sai thành phố", nên không dò được gần/xa. Nhưng cũng
có nghĩa điều kiện đúng là một phép so khớp chuỗi duy nhất, và nó **có thể liệt kê được**.

**Bước 2 - Xây danh sách theo thứ tự ưu tiên.** Tải `ne_10m_populated_places_simple.geojson`
(7.342 địa điểm có `pop_max`), tách tên `name` và `name_en`, thêm biến thể không dấu, sắp theo
dân số giảm dần và loại 25 tên đã nộp trước đó. Kết quả: 7.711 chuỗi, trong đó 1.100 chuỗi đầu
tương ứng các thành phố cỡ ~1 triệu dân trở lên, tức là đúng nghĩa "major city" mà đề dùng.

**Bước 3 - Worker chạy trong tab đang đăng nhập.** Giữ toàn bộ request trong `window.__bf` để
cookie phiên không rời khỏi trình duyệt, tự dừng ngay khi `correct`, và tự lùi nhịp khi server
 trả 429/5xx:

```js
while (b.q.length) {
  const c = b.q.shift();
  const r = await fetch('/challenges/where-light-falls/answer', {method:'POST',
      credentials:'same-origin', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({city:c})});
  const d = await r.json();
  if (d.correct) { b.found = c; b.flag = d.flag; return; }
  await new Promise(z => setTimeout(z, b.delay));   // delay khởi điểm 250 ms
}
```

Tốc độ thực tế ~1,7 req/s (250 ms chờ cộng với độ trễ server), không có request nào bị từ chối,
và hàng đợi bị bỏ ở tên thứ 480 khi tìm thấy đáp án.

**Bước 4 - Kết quả.** Tên thứ 480 trả về `correct: true` kèm cờ:

```text
found = Amsterdam
flag  = POCTF{99.612.WTT7UHE5X3JIJMKQ.TO6LBQYYORFL6LLPF6Q22SRR2P}
```

**Bước 5 - Kiểm chứng bằng chính endpoint cờ.** Cờ chưa phải của mình cho tới khi endpoint submit
nhận nó:

```text
POST /challenges/where-light-falls/submit {"flag":"POCTF{99.612.…}"}
-> 200 {"correct": true, "message": "Correct."}
```

Đáp án hợp lý về mặt nội dung: Amsterdam lúc 17:55 UT ngày 20-06-2026 có phương vị mặt trời
286,6° và cao độ 17,0°, tức là một buổi chiều mùa hạ đúng như bức ảnh mô tả. Sai số của mình nằm
ở chỗ đọc cao độ từ tỉ lệ bóng (37,8° thay vì 17°) do phối cảnh của mặt đất, đúng như đã phân tích
ở nhánh 2 và 4.

## Cờ

```text
POCTF{99.612.WTT7UHE5X3JIJMKQ.TO6LBQYYORFL6LLPF6Q22SRR2P}
```

Khớp khuôn `POCTF{<cid>.<team_id>.<nonce>.<sig26>}` với cid 99, team 612, nonce 16 ký tự.

## Chạy lại

```bash
cd where-the-light-fails-to-fall
python exploit.py                 # in đoạn JS worker + danh sách tên cần nạp
```

Toàn bộ số đo ảnh, danh sách thành phố và log các nhánh đã loại nằm trong `analysis/`. Nếu muốn
làm lại bằng hình học thay vì liệt kê, bắt đầu từ `analysis/rigorous.py` và `analysis/notes.md`
để không đi lại bốn nhánh đã bị phản bác.
