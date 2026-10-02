# Server Juice - OSINT (Beginner)

**Flag:** `CSSCTF{premiumreserve}`
**Tài nguyên:** Không có tệp đính kèm phân tích, dữ liệu khảo sát dựa trên một nguồn mở công cộng. Tài liệu lưu trữ hỗ trợ bao gồm hai ảnh tĩnh trong thư mục `files/`.

## Đề bài

Hệ thống chỉ cung cấp một thông điệp văn bản duy nhất: "If you want to appease the algorithm (and maybe get a head start on future hints), consider keeping us on your radar by following." Đề bài không bao gồm bất kỳ tệp dữ liệu, máy chủ mô phỏng, hay địa chỉ URL nào. Gợi ý bổ sung định hướng người chơi tìm kiếm kênh Instagram của ban tổ chức sự kiện.
Mục tiêu là trích xuất cờ (flag) từ một bình luận công khai nằm bên dưới bài đăng có tựa đề "General Meeting 01!" thuộc tài khoản `@cybersecuritysydney`.

## Phân tích ban đầu

Tài khoản định hướng trong phần gợi ý tạo ra một cái bẫy thông tin (honeypot) gây nhiễu ngay từ bước đầu. Kênh `instagram.com/cybersecuritysociety` thực chất thuộc về một tổ chức an ninh mạng ngôn ngữ Ba Tư, toàn bộ 18 bài viết đều được đăng tải trong khoảng năm 2018 và hoàn toàn không liên quan đến phạm vi của giải đấu. Phân tích nguyên nhân sự cố này: trang cuối cùng của tài liệu trình chiếu (slide) lễ khai mạc giải ghi rõ thông điệp `Follow instagram.com/cybersecuritysociety :)`. Điều này xác nhận rằng lỗi xuất phát từ chính slide thuyết trình (ghi sai định danh handle), và phần gợi ý của đề bài chỉ đơn thuần sao chép lại lỗi đó. Tài khoản chính thức của ban tổ chức được xác nhận là `@cybersecuritysydney`.

Tiến hành rà soát chuyên sâu tài khoản `@cybersecuritysydney`, kết quả thu thập ban đầu không phát hiện dữ liệu bất thường:

- Khảo sát 27/27 nội dung mô tả (caption): Không có bài viết nào chứa định dạng tiền tố `CSSCTF{`.
- Khảo sát 19/19 bài viết tại thẻ Tagged: Toàn bộ là bài đăng từ các tổ chức liên kết khác gắn thẻ (tag) hướng tới, không chứa nội dung bất thường.
- Thẻ Reels không có dữ liệu. Ba thư mục lưu trữ (highlight) mang tên `EVENTS`, `FUN FRIDAYS!`, và `ARCHIVE` mỗi thư mục chỉ chứa một nội dung (story) nền nhạc, không đính kèm văn bản mã hóa.
- Hệ thống không có story hiển thị trực tiếp và không kích hoạt cơ chế tự động gửi tin nhắn (auto-DM) sau khi tài khoản được theo dõi (follow).
- Đường dẫn tiểu sử (Bio) chuyển hướng tới cấu trúc `linktr.ee/CybersecuritySocietySydney`. Cây liên kết này bao gồm 40 đường dẫn, trong đó 8 liên kết thuộc về tổ chức, phần còn lại là mã liên kết tiếp thị (affiliate) mặc định của nền tảng Linktree.
- Trích xuất và phân tích 25 ảnh thiết kế (áp phích) cùng 7 mã QR code. Toàn bộ mã QR giải nén đều trỏ về các liên kết đăng ký tham gia sự kiện thông thường (`ctf.cybersecurity.sydney`, biểu mẫu Google Forms, `forms.gle/...`, và chuỗi định tuyến `au.cglink.me/25W/r382007|r382336|r382696` sau đó chuyển hướng về `clubs.usu.edu.au/CSS/rsvp_boot?id=...`).

### Phân tích Áp phích và thông điệp giả lập (Định hướng tên bài)

Trên ấn phẩm áp phích "General Meeting 01!", hệ thống phát hiện một đoạn hội thoại mô phỏng (tin nhắn giả lập). Hai dòng hội thoại cuối cùng chính là bộ khóa khai thác:

```text
u seriously care more about a club than the premium reserve??
come for the server juiceeeee
```

Dòng hội thoại thứ hai ("server juice") trực tiếp giải mã danh xưng của thử thách. Dòng hội thoại thứ nhất ("premium reserve") mang nội dung của cờ.

*(Ảnh lưu trữ đoạn hội thoại tin nhắn trong áp phích được đính kèm tại `files/sms_bubble.png`)*

### Phân tích cấu trúc Bình luận chứa cờ

Sau quá trình quét cạn (exhaustive search) qua 27 bài đăng, hệ thống phát hiện một bình luận thuộc bài viết có định danh `DWL9S-wkyJT` phản hồi trực tiếp mã cờ:

```text
harrysalvesen  8h
CSSCTF{premiumreserve}
11 likes
Reply
```

Bình luận hiển thị mã văn bản thô (plaintext), không yêu cầu dịch thuật ngược, không sử dụng kỹ thuật giấu tin (steganography). Hình ảnh gốc của bình luận này được lưu trữ kỹ thuật số tại `files/comment_catch.png`.

## Chuỗi khai thác

**Bước 1 - Khai phá ngữ nghĩa qua ấn phẩm hình ảnh.** 
Xây dựng lưới hình ảnh (contact sheet) kết hợp toàn bộ 25 ấn phẩm đã trích xuất và thực hiện rà soát trực quan. Trên áp phích mã định danh `DWL9S-wkyJT` (sự kiện "General Meeting 01!"), cấu trúc tin nhắn giả lập phơi bày hai dòng dữ liệu cốt lõi:

```text
u seriously care more about a club than the premium reserve??
come for the server juiceeeee
```

Nhận định: Cụm từ "premium reserve" là thành phần lõi tạo nên cờ. Cụm từ "server juice" định danh mối liên kết mật thiết với tiêu đề của thử thách.

*(Minh họa chi tiết vị trí thông điệp trên áp phích: `analysis/sms_bubbles.jpg`)*

**Bước 2 - Quét mạng lưới bình luận công cộng.** 
Trong chu kỳ kiểm tra trước đó, do chỉ tập trung vào luồng bình luận của bài viết được ghim (pinned post) với kết quả 0 bình luận, hệ thống đã tạm thời bỏ qua không gian dữ liệu này. Tuy nhiên, việc rà soát luồng bình luận của bài viết `DWL9S-wkyJT` đem lại kết quả hiển thị nguyên bản:

```text
harrysalvesen  8h
CSSCTF{premiumreserve}
11 likes  Reply
```

Dữ liệu cờ được đặt lộ thiên, không trải qua quá trình mã hóa hay kỹ thuật che giấu. Đáng chú ý, nội dung mô tả (caption) của bài viết này mang trạng thái chỉnh sửa ("Edited"). Sự thay đổi được thực hiện nhằm bổ sung thông điệp chốt: "We hope to see you there; BYO water. 💧". Chi tiết bổ sung này cấu thành chuỗi logic thống nhất với khái niệm "nước làm mát server" (server juice) được ngụ ý trong bức ảnh áp phích.

**Bước 3 - Xác thực định danh tài khoản.** 
Tài khoản phát tán bình luận thuộc về `harrysalvesen`. Qua đối chiếu hệ thống, danh tính này trùng khớp với tài khoản `hsalvesen` / `vesen.app` xuất hiện trong các manh mối từ giai đoạn tiền trinh sát. Đường dẫn tiểu sử (Bio) Instagram của tài khoản cá nhân này trỏ thẳng về `vesen.app`, giải thích hoàn chỉnh nguồn gốc của thông số đánh dấu UTM `link_in_bio` mà hệ thống lưu vết được.

**Bước 4 - Khâu tự kiểm chứng (Verification).** 
Chuỗi dữ liệu thu thập được hoàn toàn tuân thủ định dạng chuẩn `CSSCTF{...}` theo đặc tả kỹ thuật. Dữ liệu này tồn tại dưới dạng nguyên văn trong mã nguồn nội dung bài viết, được xác thực đăng tải bởi tài khoản có liên quan tới tác giả sự kiện, và đã được cộng đồng ghi nhận với 11 lượt thích. Quy định số 6 trong tài liệu khai mạc áp đặt cơ chế phân biệt chữ hoa, chữ thường đối với cờ; cấu trúc chuỗi thu được (`premiumreserve`) tuân thủ tuyệt đối định dạng chữ in thường toàn phần.

## Flag

Quá trình thực thi truy xuất bằng lệnh tự động:

```bash
$ python exploit.py
```

Kết xuất bằng chứng được trích xuất trực tiếp từ khối dữ liệu JSON lưu trữ (Bao gồm dữ liệu mô tả, nội dung bình luận, các đường dẫn URL đã được lược bỏ để bảo mật):

```text
Nguồn dữ liệu: analysis/evidence.json  (Mã định dạng bài viết DWL9S-wkyJT)

--- Trích xuất liên hợp caption và comment (Đã được làm sạch) ---
...
We hope to see you there; BYO water. 💧
See translation
harrysalvesen
8h
CSSCTF{premiumreserve}
11 likes
Reply

Cờ phân tích được: ['CSSCTF{premiumreserve}']

=== CỜ ===
CSSCTF{premiumreserve}
```

Kết quả:
```text
CSSCTF{premiumreserve}
```

## Reproduce

Do kiến trúc bảo mật của nền tảng Instagram yêu cầu phiên đăng nhập hợp lệ để hiển thị các luồng bình luận, quá trình thu thập thông tin được cấu hình thực thi trực tiếp thông qua công cụ Console của trình duyệt trong phiên hoạt động (logged-in session). Đoạn mã thực thi (script) được tích hợp trong biến `BROWSER` thuộc tệp `exploit.py`. Kịch bản tự động thực hiện thao tác cuộn tải dữ liệu (scroll) qua 27 bài viết, sử dụng hàm `fetch` để nạp mã nguồn từng trang, và áp dụng bộ lọc `grep CSSCTF\{...\}` để rà quét. Quá trình quét được tối ưu hóa bằng các khoảng trễ (`sleep`) để tránh cơ chế chặn thao tác tự động của nền tảng.

```bash
python exploit.py
```

Khối dữ liệu bằng chứng thu thập được bảo lưu tại `analysis/evidence.json`. Dữ liệu này đã được thanh lọc, chỉ giữ lại các trường văn bản mô tả và bình luận, toàn bộ các liên kết URL chứa chữ ký xác thực CDN được lược bỏ nhằm ngăn chặn hành vi truy ngược danh tính và bảo vệ thông tin liên quan tới tài khoản cá nhân.
