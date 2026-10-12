---
title: "Red Skull's Trail"
category: "OSINT"
tags: ["github-history", "git-rename-trail", "png-trailer", "base64", "username-enumeration"]
solve_date: "2026-10-09"
language: "vi"
---

# Red Skull's Trail

**Flag:** `OWASP{PhantomSoul}`
**Artifact:** `mr` — bản clone của `https://github.com/Vormir-616/Missing-Record` (21 commit, mọi commit một tác giả). Tệp chứa cờ: `RECORD6`, 1,917,594 B, sha256 `3ee355d92ebe3405dc0544aaf7ed9dc8e8375f81286939a50f1c826b288ce86f`. Tác giả bài: Suyog Jadhav.

## Đề bài

Easy, 100 điểm, 9 lượt solve, thẻ challenge tạo ngày 09/10/2026. Phần đính kèm của thẻ ghi `File Attachments: No attachments available.` — bài không phát tệp, toàn bộ dữ liệu nằm trên GitHub.

Văn bản câu đố của bài không được lưu lại trong workspace. Điều được ghi nhận là hướng đi mà câu đố mở ra: tài khoản GitHub `Vormir-616` và repository `Missing-Record`. Các số liệu về repo ở dưới lấy từ chính bản clone và các trang/bảng JSON GitHub đã lưu trong `r/`; riêng ngày tạo repo `2026-09-20T17:34:17.000Z` đọc từ bản `repo.html` lưu tại `repo.html`.

## Phân tích

### Kho lưu trữ

```console
$ git config --get remote.origin.url
https://github.com/Vormir-616/Missing-Record
$ git log --all --format='%an <%ae>' | sort -u
Vormir-616 <h3922457@gmail.com>
$ git log --all --oneline | wc -l
21
```

 Repo có 6 tệp nội dung: `README.md` và `RECORD1`…`RECORD6`. `README.md` mô tả vụ mất tích của Soul Stone trên Vormir và nói rằng "Only fragments remain".

`RECORD1`, `RECORD2`, `RECORD4`, `RECORD5` mỗi tệp nêu một tên người đã trả lại đá:

```text
RECORD1  -> soulkeeper
RECORD2  -> vormir_watcher
RECORD4  -> echoofvormir
RECORD5  -> soulbound
```

Bốn tệp này cùng một khuôn văn bản; `RECORD5` còn mang dòng tiêu đề `SOUL STONE — RECORD 04` dù là tệp số 5, dấu hiệu của nội dung ghép sẵn chứ không phải dữ liệu hiện trường.

`RECORD3` là tệp bị đánh dấu khác thường, nguyên văn 267 B ở HEAD:

```text
SOUL STONE — RECORD 03

Status: UNRECOVERED

The stone has not been returned.

This record appears to have been tampered with. Some information has been altered or removed from the original entry.
Find the user of the stone and prove your worthiness.

Record ends.
```

Câu "Some information has been altered or removed" đặt ra giả thuyết: tên của kẻ cầm đá từng nằm trong `RECORD3` và đã bị xoá, tức phải dò lại history.

### Kiểm chứng giả thuyết xoá nội dung

Toàn bộ history của `RECORD3` được lấy bằng `git log --all --name-status` kết hợp đọc blob trực tiếp:

```console
$ git log --all --oneline -- RECORD3
14ab6ee Update RECORD3
b442da8 Create RECORD3
$ git cat-file -s b442da8:RECORD3
160
$ git cat-file -s 14ab6ee:RECORD3
267
$ git show --name-status --format='%h %s' 4d71aab
4d71aab Update RECORD3
$ git diff-tree --no-commit-id --name-only -r 4d71aab | wc -l
0
```

Blob `RECORD3` tại commit sinh ra nó (`b442da8`, 160 B) là:

```text
SOUL STONE — RECORD 03

Status: RECOVERED

The stone has been returned.

The price was paid.

The details of the recovery
have been classified.

Record ends.
```

Ba điểm quyết định, đo lại trực tiếp trên bản clone tại thời điểm viết bài:

- `RECORD3` chưa từng có phiên bản nào chứa một tên người. Bản 160 B ban đầu đã không có tên — nó chỉ khác bản hiện tại ở dòng trạng thái `RECOVERED`. Vì vậy không có "thông tin bị xoá" nào để khôi phục; nói chính xác thì thứ bị thay đổi là trạng thái, không phải tên thủ phạm.
- Commit `4d71aab` có subject `Update RECORD3` nhưng đổi đúng 0 tệp. Commit `885dfc1` cùng subject cũng không in ra dòng đường dẫn nào trong `git log --all --name-status`.
- Số dòng tên người trong history của `RECORD3` là 0, nên hướng "tìm username trong diff" đóng lại.

Đây là quan sát chuyển hướng lời giải: `RECORD3` là dữ liệu gây nhiễu, và mồi nhử nằm ở chỗ khác trong history.

### Chuỗi đổi tên tệp

Cùng một lần `git log --all --name-status` cho thấy một chuỗi đổi tên nối tiếp nhau, mỗi lần `R100` nghĩa là nội dung không đổi một byte nào:

```console
$ git log --all --follow --oneline -- RECORD6
16af270 Rename Nothing_suspicious to RECORD6
617ed85 Rename Nothing_suspicious.md to Nothing_suspicious
7ad8f4c Rename Nothing_suspicious.png to Nothing_suspicious.md
2f85701 Rename soul_stone.png to Nothing_suspicious.png
a28755b Add files via upload
```

Chuỗi `soul_stone.png → Nothing_suspicious.png → Nothing_suspicious.md → Nothing_suspicious → RECORD6` cho thấy `RECORD6` ở HEAD chính là ảnh `soul_stone.png` được upload ở `a28755b`, không qua bất kỳ sửa đổi nào. Tác giả đổi tên để tệp trông như một bức ảnh vô hại, và tên tệp cuối bị trùng khuôn với các `RECORD*` văn bản nên nó dễ bị bỏ qua khi chỉ đọc `README`/`RECORD1..5`.

## Lời giải

### Đọc phần đuôi của RECORD6

```console
$ file RECORD6
RECORD6: PNG image data, 1254 x 1254, ...
$ stat -c%s RECORD6
1917594
$ tail -c 40 RECORD6 | xxd
00000000: 28fe 1f12 2b12 3bfa f3e5 1e00 0000 0049  (...+.;........I
00000010: 454e 44ae 4260 8255 4768 6862 6e52 7662  END.B`.UGhhbnRvb
00000020: 564e 7664 5777 3d0a                      VNvdWw=.
```

`IEND` là chunk kết thúc của PNG; 8 byte của nó là `49 45 4E 44 AE 42 60 82`. Trong ảnh hợp lệ, sau 8 byte đó không còn gì. Ở đây `IEND` nằm ở offset 1917569, và `1917569 + 8 = 1917577`, tức còn đúng `1917594 - 1917577 = 17` byte nối sau: `b'UGhhbnRvbVNvdWw=\n'`.

17 byte đó là một chuỗi base64:

```console
$ tail -c 17 RECORD6
UGhhbnRvbVNvdWw=
$ tail -c 17 RECORD6 | base64 -d
PhantomSoul
```

Cùng phép kiểm bằng Python, để nguyên dạng byte của phần đuôi:

```python
import base64, pathlib

d = pathlib.Path("RECORD6").read_bytes()
i = d.rfind(b"IEND")
print("IEND at", i, "| size", len(d), "| trailing bytes", len(d) - (i + 8))
tail = d[i + 8:]
print(repr(tail))
print(base64.b64decode(tail.strip()))
```

```text
IEND at 1917569 | size 1917594 | trailing bytes 17
b'UGhhbnRvbVNvdWw=\n'
b'PhantomSoul'
```

`PhantomSoul` là dữ liệu giải mã trực tiếp từ artifact, không phải kết quả suy luận.

### Từ chuỗi đã giải mã tới cờ

Định dạng cờ của giải là `OWASP{...}` (theo thẻ challenge). Chuỗi giải mã được không có dấu ngoặc, nên việc bọc nó thành `OWASP{PhantomSoul}` là một bước suy luận, không phải dữ liệu đọc ra từ tệp.

Cần nói rõ phạm vi của suy luận này: bản ghi của người chơi liệt kê ba biến thể — `OWASP{PhantomSoul}`, `OWASP{phantomsoul}` và `OWASP{phantom_soul}` — và không có dòng phản hồi submission nào được lưu lại. Vì vậy tài liệu này không khẳng định được biến thể hoa/thường nào nền tảng chấp nhận; bảng các bài đã solve của sự kiện chỉ ghi nhận bài này đã solve.

## Kết quả

```text
OWASP{PhantomSoul}
```

`PhantomSoul` là 11 byte chuỗi base64 nối sau IEND của `RECORD6`, giải mã được trực tiếp. Phần `OWASP{}` là cách bọc theo định dạng giải, và vì không có phản hồi submission nào được lưu, biến thể hoa/thường chính xác mà nền tảng chấp nhận không có trong hồ sơ người chơi.

## Tái hiện

Cần `git`, `xxd`, `base64` (coreutils) và Python 3 stdlib. Repo phải còn công khai tại thời điểm chạy.

```console
$ git clone https://github.com/Vormir-616/Missing-Record mr
$ cd mr
$ git log --all --name-status
$ git cat-file -p b442da8:RECORD3
$ tail -c 17 RECORD6
UGhhbnRvbVNvdWw=
$ tail -c 17 RECORD6 | base64 -d
PhantomSoul
```

`git log --all --name-status` là bước định hình lời giải: nó vừa cho thấy `RECORD3` không từng chứa tên nào, vừa lộ chuỗi đổi tên `R100` dẫn tới `RECORD6`. Nếu repo bị chuyển thành private hoặc bị xoá, bản clone trong workspace vẫn giữ đủ history để chạy lại toàn bộ phép kiểm.
