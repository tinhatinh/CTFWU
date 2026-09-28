# notes.md - afterglow

Input: `<đường dẫn artifact>` (<size> B, sha256 `<hash>`)
Định dạng cờ đề yêu cầu: `<PREFIX>{...}`

## H1 - <giả thuyết đầu tiên>
cmd: `<lệnh đã chạy>`
evidence: `<đọc thấy gì, số liệu cụ thể>`
result: DEAD - <lý do loại, nói rõ bằng chứng phản bác>

## H2 - <giả thuyết tiếp theo>
cmd: `<lệnh>`
evidence: `<số liệu>`
result: DEAD - <lý do>

## H3 - <giả thuyết đúng>
cmd: `<lệnh>`
evidence: `<số liệu + vì sao nó buộc hướng này đúng>`
result: PENDING -> <xác nhận ở H4>

## H4 - <bước chốt>
cmd: `python solve.py <artifact>`
evidence: `<đầu ra trung gian>` -> `<kết quả cuối>`
result: OK - cờ: `<PREFIX>{...}`

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
