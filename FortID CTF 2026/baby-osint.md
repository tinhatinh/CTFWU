---
title: "Baby OSINT"
category: "OSINT"
tags: [ "exif", "event-matching", "public-dashboard", "replay-chart"]
solve_date: "2026-10-10"
language: "vi"
---

# Baby OSINT

**Flag:** `FortID{hodaj_za_liku_hodaj_za_hrvatsku:zegevege:wednesday:909}`
**Bài:** `Baby OSINT` (laragrr, ipaljak), challenge UUID `90b48aac-8c30-40a9-b922-0c9f45534de9`. **Handout:** `handout.jpeg` (thẻ đề ghi 5.8 MB; bản local đã bị xoá nên không còn mở lại ảnh để xem được). Định dạng đáp án: `FortID{q1:q2:q3:q4}`. Thẻ đề xếp bài vào nhóm "intro".

## Đề bài

Một ảnh JPEG duy nhất và bốn câu hỏi, nộp dưới dạng `FortID{q1:q2:q3:q4}`. Ảnh chứa metadata EXIF định thời một khoảnh khắc cụ thể; các đáp án được suy từ những sự kiện và nguồn data công khai trùng thời điểm đó.

```text
FortID{q1:q2:q3:q4}
q1 = hodaj_za_liku_hodaj_za_hrvatsku
q2 = zegevege
q3 = wednesday
q4 = 909
```

## Phân tích

Bản `handout.jpeg` không còn trên máy, nên phần dưới đây dựa trên các giá trị đã ghi nhận trong phiên giải (trước hết là mốc EXIF) chứ không phải ảnh còn xem lại được.

Mốc EXIF `2026-09-05 12:03` là anchor để lần ra từng đáp án:

- **q1** — trùng với một buổi biểu tình ở Zagreb, "Hodaj za Liku, hodaj za Hrvatsku" (đăng trên ursh.hr). Token chấp nhận: `hodaj_za_liku_hodaj_za_hrvatsku`.
- **q2** — lễ hội ẩm thực cùng cuối tuần đó: ZeGeVege. Token chấp nhận là `zegevege` (không phải `zegevege_festival`).
- **q3** — thứ trong ngày đạt đỉnh sử dụng xe đạp. Nguồn: dashboard công khai của hệ thống bike-share Zagreb `bajs.informacija.hr`, kèm biểu đồ phát lại (replay chart) ở `mkranj.github.io/BajsBoard`. Thứ đạt đỉnh: `wednesday`.
- **q4** — số người đi đạp đỉnh điểm tại sự kiện INmusic, lấy từ bài đưa tin về INmusic. Giá trị chấp nhận: `909`.

Bước phân biệt nằm ở đáp án cuối. Dashboard ghi nhận `911` lượt trong mẫu năm phút, còn bài báo "više od 900 ljudi na Inmusic doslo bajsom" (index.hr/fit/2805907) nêu `909`. Các biến thể `thursday` chỉ thắng khi tính data đến hết ngày 2026-09-11, ngoài date range của sự kiện; trong event window, `wednesday` mới là ngày có đỉnh.

## Lời giải

Chuỗi suy luận là ghép mốc EXIF sang các nguồn công khai trùng thời điểm:

```text
EXIF 2026-09-05 12:03 -> demonstration "Hodaj za Liku, hodaj za Hrvatsku" (ursh.hr)            -> q1
same weekend -> food festival ZeGeVege                                                          -> q2
bike-share peak weekday -> bajs.informacija.hr, replay chart mkranj.github.io/BajsBoard         -> q3 (wednesday)
INmusic peak riders -> index.hr/fit/2805907 ("više od 900 ljudi ... doslo bajsom")              -> q4 (909)
```

Ba đáp án đầu khớp với nguồn tương ứng. Ở câu cuối, chọn `909` theo bài báo và giới hạn data trong event window; mở rộng đến 2026-09-11 sẽ làm `thursday` thành ngày có đỉnh.

## Các hướng đã kiểm tra

Các ứng viên sau đã nộp và nhận `badFlag` (38 dòng `badFlag` trong `submission_results.jsonl`):

- q2 = `zegevege_festival` → `badFlag` (token đúng là `zegevege`); q2 = `bas_nas_bbq` → `badFlag`.
- q3 theo bảy cách viết thứ trong tuần, gồm cả tiếng Croatia `srijeda`, `utorak`, `cetvrtak` → `badFlag`; `wednesday` mới đúng. `thursday` chỉ thắng khi tính data ngoài event window, đến 2026-09-11.
- q4 ∈ {`911`, `269`, `111`, `235`} → `badFlag`; `909` (theo bài báo) được chấp nhận.

Dòng chấp nhận lưu nguyên văn:

```text
FortID{hodaj_za_liku_hodaj_za_hrvatsku:zegevege_festival:wednesday:909} badFlag\r\nFortID{hodaj_za_liku_hodaj_za_hrvatsku:zegevege:wednesday:909} goodFlag\r\nACCEPTED
```

Bằng chứng bền: `accepted_flag.txt` (62 B) và dòng `goodFlag` kèm `"The flag is correct."`.

## Kết quả

```text
FortID{hodaj_za_liku_hodaj_za_hrvatsku:zegevege:wednesday:909}
```

Flag đã được nền tảng chấp nhận (dòng `goodFlag ... ACCEPTED` ở trên). Không có instance FortID nào tham gia; phản hồi chấp nhận đến từ `/submit`.

## Tái hiện

Bản `handout.jpeg` đã bị xoá nên không mở lại ảnh để xem được; tái hiện dựa trên mốc EXIF đã ghi (`2026-09-05 12:03`) và các tra cứu công khai sau (nguồn có thể đã đổi chỗ sau sự kiện, nên cần xác minh lại path):

- đối chiếu mốc EXIF với listing sự kiện trên ursh.hr → tên buổi biểu tình (q1);
- lịch lễ hội cuối tuần đó → xác định ZeGeVege và token `zegevege` (q2);
- dashboard `bajs.informacija.hr` cùng biểu đồ phát lại `mkranj.github.io/BajsBoard` → ngày đạt đỉnh trong tuần (q3);
- bài đưa tin INmusic `index.hr/fit/2805907` → số người đạp đỉnh điểm `909` (q4); giới hạn data đến cuối tuần sự kiện để `wednesday` là ngày có đỉnh.

Ghép bốn token theo định dạng `FortID{q1:q2:q3:q4}` là ra flag.
