---
title: "OSINT Exam II"
category: "OSINT"
tags: ["multi-question", "exif", "race-results", "geolocation", "public-records", "remote-service"]
solve_date: "2026-10-10"
language: "vi"
---

# OSINT Exam II

**Flag:** `FortID{Y0u_H4v3_N0w_B3com3_4_C3rt1fi3d_0p3n_50urc3_1n73l1genc3_Gr4ndM45t3r_4_L1f3_af5a43ec69}`
**Bài:** `OSINT Exam II` (ipaljak). **Handout:** `data.zip` (7503579 B; thẻ đề ghi 7.2 MB) chứa `data/q1.png`, `data/q2.jpg`, `data/q3.jpeg`, `data/q5.jpg`, `data/q6.mp4`, `data/q6_1.jpeg`, `data/q6_2.jpeg`. **Dịch vụ:** `ncat --ssl osint-exam-ii-<hash>.inst12.ctf.fortid.com 1337`, chạy qua TLS bởi `osint_exam_ii/exam_client.py`. Instance đầu `d4372dc6d1ee` hết hạn giữa phiên và được thay bằng `70beb5f9e24d`.

## Đề bài

Đề là một "kỳ thi OSINT" sáu câu, phục vụ qua TLS: client nộp từng đáp án cho `exam_client.py`, và sau câu thứ sáu đúng thì dịch vụ in ra certificate (cờ). Mỗi câu tương ứng một media trong `data/` (q1→`q1.png`, q2→`q2.jpg`, q3→`q3.jpeg`, q5→`q5.jpg`, q6→`q6.mp4`/`q6_1.jpeg`/`q6_2.jpeg`). Sáu đáp án đã ghi nhận:

```text
q1 Edinburgh 14480 00:53:14
q2 From EU Digital Identity Architecture to Real-World Services
q3 Max Bruch Augusta Senoe 31a 23250 Pag Croatia
q4 Paljak Kiki Dino
q5 Docaposte Rennes Midnight Flag CTF
q6 Brant Fell
```

## Phân tích

- **q1** — biển số và thời gian của một runner nam ở giải chạy 10K: đọc số Bib trên ảnh cắt `q1_bib.png`, rồi tra bảng kết quả `mens10k.com/results?event=1070`. Cột ghép ra `Edinburgh 14480 00:53:14`.
- **q2** — tiêu đề một buổi thuyết trình về EU Digital Identity: `From EU Digital Identity Architecture to Real-World Services`.
- **q3** — địa chỉ khớp từ ảnh: `Max Bruch Augusta Senoe 31a 23250 Pag Croatia`.
- **q4** — bảng xếp hạng bóng đá bàn (foosball): `Paljak Kiki Dino`.
- **q5** — đáp án trong bản ghi là `Docaposte Rennes Midnight Flag CTF`. Mốc EXIF `2026-06-12` chỉ là đầu mối thời gian; chưa có nguồn lưu để xác nhận diễn giải về EUDIW Unfold #3.1.

## Lời giải

Với mỗi câu, đọc chữ trực tiếp trên media (số Bib, tên địa chỉ, bảng xếp hạng, tiêu đề slide) rồi đối chiếu một nguồn công khai khi cần (bảng kết quả 10K cho q1; lịch phiên EUDIW/Docaposte cho q5). q6 là câu duy nhất phải thử–sửa vì ảnh/video nhập nhằng giữa hai đỉnh; dịch vụ xác nhận bằng cách từ chối `Higger Tor` và chỉ nhận `Brant Fell`.

Nộp lần lượt sáu đáp án qua `exam_client.py`; sau câu 6, dịch vụ in certificate:

```text
After answer 6 : \r\nCongratulations!\r\nYou passed the exam, here is your certificate: FortID{Y0u_H4v3_N0w_B3com3_4_C3rt1fi3d_0p3n_50urc3_1n73l1genc3_Gr4ndM45t3r_4_L1f3_af5a43ec69}\r\n
```

## Kết quả

```text
FortID{Y0u_H4v3_N0w_B3com3_4_C3rt1fi3d_0p3n_50urc3_1n73l1genc3_Gr4ndM45t3r_4_L1f3_af5a43ec69}
```

Cờ vừa được đọc nguyên văn từ dịch vụ remote (dòng certificate ở trên, lưu vào `osint_exam_ii/flag.txt` 162 B), vừa được nền tảng chấp nhận khi nộp; phản hồi submission lưu nguyên văn:

```text
{'kind': 'goodFlag', 'message': 'The flag is correct.'}
```

## Tái hiện

Cần một instance đang sống: cờ dưới đây là giá trị đã nhận trong lần chạy được lưu. Chưa có source server để kết luận cách sinh hậu tố hoặc phạm vi chấp nhận giữa các instance.

```console
$ ncat --ssl osint-exam-ii-70beb5f9e24d.inst12.ctf.fortid.com 1337
```

`exam_client.py` nối tới instance và lần lượt gửi sáu đáp án: (1) đọc số Bib từ `q1_bib.png` rồi tra `mens10k.com/results?event=1070`; (2)-(4) đọc trực tiếp tiêu đề slide, dòng địa chỉ và bảng xếp hạng từ các media `q2.jpg`/`q3.jpeg` và bảng foosball; (5) dùng EXIF `2026-06-12` để chốt phiên EUDIW Unfold #3.1 của Docaposte và vòng chung kết Midnight Flag CTF; (6) nộp `Brant Fell` (sau khi `Higger Tor` bị từ chối). Sau câu 6, certificate in ra chính là cờ của instance đó.
