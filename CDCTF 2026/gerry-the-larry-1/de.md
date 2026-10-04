# Đề bài - gerry-the-larry-1

## Nguyên văn đề

```text
Gerry the Larry (1/2)
500
Log Analysis
adlee7, reep236

The Meowjority's political machine and overfunded campaign has caused the great
baron Garry to consistently win the election for Chief Mouser against the best
interests of Cat County. A diligent civil servant, upset at his actions, has
leaked election info from polling places all across the county. Knowing that
this alone cannot save Cat County without action, an underground hackcatvist
(you) need to put this information to use.

Cat County is broken up into county blocks. Using the provided information, how
many of these blocks are currently controlled by the Meowjority? Make note of
which ones! You'll need that later.

The flag format is cdctf{##}. For example, cdctf{02} or cdctf{64}

Disclaimer: CDCTF and any of its parent organizations do NOT endorse
hacktivism. This is a fictional scenario created for illustrative purposes,
always obey laws and regulations regarding computer use.
```

File kèm theo: `catcounty_results.zip`, giải nén ra thư mục `gerry_final_files/`
gồm `info.csv`, `check_in.log`, `votes.log`.

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/catcounty_results.zip` (bản tải về từ thẻ bài, giữ nguyên, chưa sửa) |
| Kích thước | 37241 byte |
| SHA-256 | `462c4d84a16c96e062dba6d9830bf375e727d090318ac946d903e0826d5a9cb4` |
| Loại file | Zip archive data, made by v2.0 UNIX, CRC testzip OK, entry trong `gerry_final_files/` ghi ngày 2026-10-02 |
| `info.csv` | 38328 B, sha256 `85a55f5a91e2ab8a002d7c477727ab3affa6e06cf32f94508031d5668f2d1a19`, 1 dòng header + 1067 cử tri, cột `id,name,block`, 36 giá trị `block` |
| `check_in.log` | 45881 B, sha256 `d41fd97625a942036c01852f2dd5a520833201a894ba1d0bcd47c6d58103af0b`, 1067 dòng `YYYY-MM-DD HH:MM:SS receipt voter_id`, receipt 550408395..550409461 |
| `votes.log` | 49441 B, sha256 `2bcd81cb20278920c4d81f9e6ca38c5833e0d9590e70b9007cebdb565e715897`, 1067 dòng `YYYY-MM-DD HH:MM:SS:ballot:party`, ballot 381009204091..381009205157 |
| Bốn đảng trong `votes.log` | Domestic Loafs 293, Meowjority 286, Tuna Reform 254, Nap Rights 234 |
| Nhiệm vụ | Đếm số county block mà Meowjority đang kiểm soát, và ghi danh sách block đó để dùng cho phần 2 |
| Định dạng cờ | `cdctf{##}` (hai chữ số, theo ví dụ `cdctf{02}`, `cdctf{64}`) |

## Hướng giải (tóm tắt)

`votes.log` chỉ có số thứ tự ballot và tên đảng, không có danh tính cử tri; `check_in.log`
gắn số thứ tự receipt với `voter_id`, còn `info.csv` gắn `voter_id` với block. Hai log
không có khoá chung nào (receipt 9 chữ số và ballot 12 chữ số là hai không gian đánh số
độc lập, giao nhau rỗng), nên phải khôi phục quan hệ bằng cấu trúc chuỗi: cả hai đều đơn
điệu theo thời gian, đánh số liên tục, dài đúng 1067 dòng, mỗi cử tri check-in đúng một
lần, do đó phép gán 1-1 giữ thứ tự duy nhất là dòng i của log này với dòng i của log kia.
Gán xong thì cộng dồn phiếu theo block, đảng nhiều phiếu nhất trong block giành block
(không block nào hoà), Meowjority giành 12/36 block.

## Chạy lại lời giải

```bash
python exploit.py files/catcounty_results.zip
```

Kết quả: `cdctf{12}` (đã lưu trong `flag.txt`, output đầy đủ ở `analysis/exploit_output.txt`).
