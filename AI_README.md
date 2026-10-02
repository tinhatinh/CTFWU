# Hướng dẫn cho AI thêm và cập nhật writeup

Đọc file này trước khi chỉnh kho. Đây là hướng dẫn trung lập cho mọi model/agent.

## Nguồn dữ liệu

- File thật: `<Tên cuộc thi>/<challenge-slug>/writeup.md` và `writeup.en.md`.
- `site/` chứa layout, CSS, JavaScript và bản dịch nhãn giao diện.
- `tools/build_site.py` dựng `_site_src/` (VI) và `_site_src_en/` (EN).
- Không chỉnh `_site_src/`, `_site_src_en/`, `_build/` hoặc `_site/`: đó là đầu ra sinh tự động.
- Không thay đổi artifact gốc hoặc file của challenge khác khi chỉ thêm một bài.

## Thêm cuộc thi / bài mới

1. Tạo thư mục cuộc thi ở root, ví dụ `Example CTF 2027/`, và thư mục challenge như `example-web/`.
   Không bắt đầu tên thư mục bằng `_` hoặc `.`. Không dùng tên trong `SKIP_TOP` của generator.
   Tên sau khi chuyển thành slug phải duy nhất (không tạo hai tên chỉ khác dấu/khoảng trắng).
2. Tạo `README.md` cho cuộc thi. Bảng metadata phải có cột **Category** và liên kết dạng
   `[example-web](example-web/writeup.md)`; parser lấy category từ bảng này. Ví dụ:

   ```markdown
   # Example CTF 2027

   | Challenge | Category | Difficulty | Flag |
   |-----------|----------|------------|------|
   | [example-web](example-web/writeup.md) | Web | Hard | Xem writeup |
   ```

3. Viết `writeup.md` dựa trên `_template/writeup.md`. Dòng đầu phải là heading:
   `# Example Web - Web (Hard)`. Phần sau gồm đề bài, phân tích, các hướng đã loại,
   chuỗi khai thác, kết quả và cách reproduce. Không thêm YAML front matter: generator tự sinh.
4. Viết `writeup.en.md` với cùng cấu trúc. Dịch phần văn xuôi; giữ nguyên code, lệnh, flag và output
   trong code fence. Nếu chưa dịch, generator có thể hiển thị bản VI ở cây EN với cảnh báo;
   không coi fallback là bản dịch hoàn chỉnh.
5. Giữ `notes.md`, `de.md`, script solve và artifact theo cấu trúc trong README gốc.
   Chỉ công bố flag/kết quả đã quan sát được; không bịa điểm, độ khó, thời gian hoặc thành tích.
6. Thêm thời điểm solve vào `tools/solve_times.json`, key chính xác `Tên cuộc thi/challenge-slug`:
   `"Example CTF 2027/example-web": "2027-01-02T14:30:00+07:00"`.
   Nếu chỉ có bằng chứng về ngày thì dùng `"2027-01-02"`; không tự chọn giờ.
   Thời điểm này dùng để sắp xếp bài mới, không thay bằng thời gian chỉnh bài.
7. Thêm ảnh bìa `site/assets/competitions/<event-slug>.png` khi có ảnh chính thức.
   Ảnh Markdown dùng đường dẫn tương đối trong thư mục challenge. Generator chỉ copy ảnh
   được tham chiếu và nhỏ hơn hoặc bằng 32 MiB; không đưa toàn bộ artifact lớn lên website.
8. Chạy generator và build hai ngôn ngữ như bên dưới. Trang chủ, thư viện, chuyên mục và cuộc thi
   tự cập nhật từ dữ liệu mới; không thêm card hoặc số đếm bằng tay vào layout.

## Kiểm tra trước khi bàn giao

```bash
python tools/build_site.py
python tools/test_editor.py
bundle install
JEKYLL_ENV=production bundle exec jekyll build -s _site_src -d _build/preview/CTFWU
JEKYLL_ENV=production bundle exec jekyll build -s _site_src_en -d _build/preview/CTFWU/en
bundle exec htmlproofer _build/preview --disable-external
python tools/serve_site.py --skip-build
```

Trong PowerShell, đặt `$env:JEKYLL_ENV='production'` trước lệnh Bundler thay cho tiền tố shell.
Build VI trước EN vì cây EN nằm trong thư mục đầu ra VI. Xem `/CTFWU/` và `/CTFWU/en/`,
đảm bảo bài mới có trong thư viện, bộ lọc, trang cuộc thi và liên kết source đúng file thật.
Kiểm tra Liquid payload (`{{...}}`, `{%...%}`) vẫn xuất hiện nguyên văn trong code, không bị thực thi.

Nếu dùng Docker, xem phần preview/editor trong README chính. Không tự cài runtime lên máy chủ
hoặc thay workflow chỉ để giải quyết thiếu công cụ local.

## Chỉnh bài đã có

- Chỉnh file gốc, giữ key/permalink và thời điểm solve.
- Bản VI và EN là hai file độc lập. Nếu sửa nội dung kỹ thuật, kiểm tra và cập nhật cả hai
  nếu phạm vi yêu cầu bao gồm bản dịch; không âm thầm ghi đè ngôn ngữ kia.
- Local editor đọc/lưu đúng các file này, sao lưu vào `_build/editor-backups/`, rồi rebuild.
  Nếu file đổi sau khi editor mở thì reload/đối chiếu; không bỏ qua kiểm tra version.
- Editor local chỉ cấp quyền sau khi xác minh tài khoản GitHub là chủ sở hữu repo bằng user ID.
  Không thay bằng tên Git/email, cờ trên frontend, hoặc quyền collaborator. Không thêm chế độ bypass.
  Có thể chọn VN, EN hoặc cả hai; kiểm tra version của mọi file trước khi ghi, sao lưu từng file
  và rollback nếu việc lưu một file thất bại. Không tự dịch nội dung của bản còn lại.
- Editor trên GitHub Pages dùng GitHub API: token chủ repo cần Contents: Read and write;
  kiểm tra owner, blob version, tạo một commit cho các bản đã chọn và update ref không force.
  GitHub kiểm tra quyền ghi repo. Không đưa token vào localStorage, HTML, log hoặc URL.
  Phiên public chỉ nằm trong bộ nhớ tab, tối đa 8 giờ, kết thúc khi reload/đóng tab.
  GitHub Actions dựng lại website sau commit; máy local cần git pull để nhận thay đổi đó.

## CTFTime và triển khai

- Nguồn kết quả đội: `https://ctftime.org/team/449538`, cache: `tools/ctftime_team.json`.
- Workflow cập nhật mỗi 12 giờ và khi chạy build. Không sửa số liệu theo suy đoán.
- Fetch lỗi hoặc cấu trúc trang đổi phải giữ snapshot cũ, không ghi dữ liệu trống.
- Chỉ commit/push/deploy khi yêu cầu hiện tại cho phép; kiểm tra `git status` và tránh đưa
  file công việc không liên quan hoặc log/credential vào commit.

## Giao diện và giọng văn

Overview chỉ có giới thiệu ngắn, số liệu kho và writeup mới nhất. Không thêm slogan, phần
tự quảng bá hay diễn giải phương pháp làm việc. Giữ nhãn VI/EN đồng bộ trong
`site/_data/interface.json`. Tái sử dụng layout và token CSS hiện có, tránh thay framework.

Writeup dùng giọng văn kỹ thuật, nghiêm túc và trực tiếp. Tránh cường điệu hoặc cách dịch gượng
như “đệ trình mật khẩu”, “khai phá không gian”, “mã kịch bản hệ thống”, “chứng thực tuyệt đối”.
Giữ các thuật ngữ quen thuộc như payload, stack, return address, contract, storage slot,
RPC, instance và script bằng tiếng Anh khi rõ nghĩa hơn. Phân biệt quan sát với suy luận;
không mô tả tính duy nhất, hiệu quả hoặc mức độ bảo mật như một bảo đảm khi chưa có bằng chứng.
Chỉnh văn xuôi không được làm đổi code fence, lệnh, flag hoặc output đã ghi nhận.

Ưu tiên thao tác trực tiếp, đơn giản khi artifact cho phép: đọc chữ rõ trên ảnh, nghe lời nói
đã giải mã, đọc bảng chân lý hoặc lần theo mũi tên. Không thêm OCR/ASR hay brute-force để tạo
một quy trình phức tạp nếu không cần. Script có thể dùng để reproduce nhưng không nên được
mô tả như điều kiện bắt buộc cho thao tác người đọc làm trực tiếp được. Những phép thử phụ và
nhánh đã loại chỉ cần tóm tắt trong writeup; giữ nhật ký chi tiết trong `notes.md`.

Giới hạn kết luận theo bằng chứng: cosine similarity cao không chứng minh khôi phục nguyên văn;
padding đúng không tự chứng minh key duy nhất; N/N test pass chỉ mô tả tập N mẫu đã kiểm tra.
Không suy đoán ý đồ tác giả, tính an toàn tuyệt đối hoặc chất lượng của model từ một vài quan sát.

Ảnh đề bài lấy từ các tham chiếu ảnh trong `de.md`; ảnh phân tích phải được tham chiếu trong
writeup bằng Markdown hoặc đường dẫn file. Không copy tất cả ảnh trong thư mục artifact lên
website. Generator giữ cấu trúc thư mục con và kiểm tra kích thước ảnh khi copy.
