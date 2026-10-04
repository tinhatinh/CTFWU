# notes.md - eat-your-fruits-and-vegetables

Input: `files/data.db.enc` (960000 B, sha256 `ea8bfa7cfc6f9f319ccf4f5efa12377beb84087ffb5885bd975656cc628e0374`)
Định dạng cờ đề yêu cầu: `cdctf{Produce_Item}`, không phân biệt hoa thường, chỉ được nộp 2 lần.

## H1 - Tấn công bản thân AES (khôi phục key, brute-force, meet-in-the-middle)
cmd: `python -c "len(open('data.db.enc','rb').read())"`
evidence: 960000 byte, chia hết cho 16 và cho 32; không có header/IV/magic.
result: DEAD - AES-128 không khôi phục được key từ ciphertext-only, và bài không cho oracle giải mã. Hướng này chỉ tổ tốn thời gian; đề đã nói rõ điểm yếu nằm ở chế độ ECB.

## H2 - Nhận diện Bob qua tần suất của từng block nửa đầu
cmd: `python an.py` (đếm block ở offset 0 và 16 của mỗi record)
evidence: 36 block A phân biệt, tần suất trải từ 786 đến 872; 18 block B phân biệt.
result: DEAD - 36 block A phân bố đều nên không có block nào "nổi bật" để gán cho Bob. Số học: 30000/36 = 833, đúng bằng dải quan sát, tức tên và xe độc lập và đồng nhất.

## H3 - Dựa vào con số "Bob - 5%" trong đề để định danh nhóm
cmd: `python an3.py` (đếm số dòng của nhóm bị ràng buộc)
evidence: nhóm bị ràng buộc có đúng 2500 dòng = 30000/12, không phải 1500 = 30000*5%.
result: DEAD - bảng Name trong đề chỉ là minh hoạ; dữ liệu thật chia đều 12 tên. Không được dùng số dòng của tên để suy ra loại hoa quả. Bảng Produce thì khớp chính xác (10/12/15/18/21/24%), nên phép đối chiếu phải làm trên Produce.

## H4 - So 8 byte đầu của các block B với nhau
evidence: với ECB mỗi block 16 byte được mã hoá trọn vẹn, hai plaintext chỉ khác nhau ở 8 byte cuối vẫn cho ra 16 byte ciphertext khác hoàn toàn. Ba block B của cùng một loại hoa quả (483a10eb..., 7ad7bda1..., 30cbb1d2...) không có chung byte nào.
result: DEAD - không đọc được tính bằng nhau của nửa đầu block từ ciphertext. Phải suy ra qua cấu trúc liên kết A-B và tần suất.

## H5 - Gom block A theo tập hợp block B đứng ngay sau nó
cmd: `python an2.py`
evidence: 33/36 block A có cùng một tập B gồm đủ 18 block (tên không ràng buộc hoa quả). Chỉ còn đúng 1 nhóm gồm 3 block A với tập B chỉ có 3 block, phủ đúng 2500 dòng.
result: PENDING -> 3 block A = 3 hãng xe của cùng một tên, 3 block B = 3 hệ điều hành của cùng một loại hoa quả. Đây chính là nhóm Bob mà đề mô tả; độ lớn 3x3 là duy nhất trong toàn bộ dữ liệu.

## H6 - Đọc loại hoa quả từ tổng tần suất của 3 block B
cmd: `python exploit.py files/data.db.enc`
evidence: tổng = 1852 + 1780 + 1768 = 5400 dòng = 18,00% của 30000. Trong nhóm, mỗi block chiếm 885/805/810 dòng xấp xỉ 2500/3, xác nhận OS phân bố đều và cả 3 block thuộc cùng một loại hoa quả. Kiểm chứng độc lập: 18 block B tách thành đúng 6 cụm theo khoảng cách tần suất, tổng các cụm là 3000/3600/4500/5400/6300/7200 = 10/12/15/18/21/24%, khớp từng dòng với bảng của đề.
result: OK - 18% chỉ ánh xạ vào duy nhất một giá trị là Carrot. Cờ: `cdctf{Carrot}`

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.

Ghi chú thêm:
- Lý do phải dùng tổng tần suất toàn cục thay vì tần suất trong nhóm: nội bộ nhóm Bob, ba block gần như bằng nhau nên không mang thông tin; thông tin nằm ở chỗ loại hoa quả đó chiếm bao nhiêu phần trăm của cả cơ sở dữ liệu.
- Bài này cho phép suy ra mà không cần phân biệt tên nào là Bob: chỉ một tên bị ràng buộc hoa quả, và đề đã nói tên đó là Bob.
- Lời giải là suy diễn tất định từ dữ liệu, không có tham số tự do, nên đáp số chỉ phụ thuộc vào bảng phân bố mà đề cho.
