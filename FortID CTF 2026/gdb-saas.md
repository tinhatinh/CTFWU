---
title: "GDB SaaS"
category: "Pwn"
tags: ["gdb","dwarf-line-table","argument-injection","filter-bypass"]
solve_date: "2026-10-10"
language: "vi"
---

# GDB SaaS

**Flag:** `FortID{N0_5h3ll_n33d3D_jU57_m41N_ce0eaeff26}`  
**Dịch vụ:** `ncat --ssl gdb-saas-53b083dc24af.inst19.ctf.fortid.com 1337` (TLS trên cổng 1337, banner từ xa `GNU gdb (Ubuntu 17.1…)`). Artifact: `server.py` 1.4 KB. Các lượt thử được ghi nhận trên instance `gdb-saas-7e15a5b0c61e`, output lời giải lấy từ instance `gdb-saas-53b083dc24af`.

## Đề bài

Dịch vụ tự giới thiệu "Get your mains disassembled for free…": nhận ELF dạng base64 cùng tên function, dùng GDB disassemble function đó rồi trả kết quả cho client. Mục tiêu là lấy flag mà không có shell.

## Phân tích

Lời giải dựa trên ba mảnh ghép.

Bộ lọc. `server.py` chặn ký tự qua `BAD_CHARS`, nhưng bộ lọc này chỉ được áp lên argument tên hàm, và trong danh sách bị chặn không có `/` lẫn `s`. Chuỗi `/s main` vì vậy đi qua nguyên vẹn và được nối thẳng vào lệnh GDB: dịch vụ chạy `disassemble /s main` thay vì `disassemble main`. Đây là injection tham số vào command line của GDB, không phải khai thác bộ nhớ.

Bảng dòng DWARF. ELF nộp lên do `mkdwarf.py` dựng tại local: một binary có `main` bình thường, kèm DWARF-4 line table mà source file #1 mang tên `flag.txt`. Bản thân file ELF không chứa flag; tên file chỉ là một chuỗi trong line table, path ở dạng basename, không có comp_dir tuyệt đối.

Cách GDB in nguồn. Với `/s`, GDB duyệt từng entry của line table và in kèm "source line" tương ứng. Vì basename không có directory đi kèm, GDB giải nó theo directory làm việc hiện tại của chính quá trình dịch vụ — nơi `server.py` đã chép file flag thật vào. Kết quả là nội dung file flag của dịch vụ được in ra như thể là dòng đầu tiên của `flag.txt`.

Toàn bộ data đi ra theo output chuẩn của GDB trong phiên đã được phép, nên không cần thực thi lệnh nào trong process dịch vụ.

## Lời giải

1. Dựng ELF local bằng `mkdwarf.py`: có hàm `main`, DWARF-4 line table khai báo source file #1 tên `flag.txt`. Bước này không phụ thuộc instance.
2. Base64 file ELF và upload lên instance qua TLS.
3. Ở bước hỏi tên hàm, truyền argument `/s main`. Hai ký tự `/` và `s` không bị `BAD_CHARS` chặn, nên lệnh thực thi phía server trở thành `disassemble /s main`.
4. Đọc phản hồi. Dòng cảnh báo cho thấy GDB đã mở thật một file trong CWD của dịch vụ và file đó chỉ có một dòng; phần disassembly đi kèm in luôn nội dung của nó. Nguyên văn theo phản hồi đã ghi nhận (dòng thứ hai giữ dạng một dòng):

   ```text
   Line number 2 out of range; flag.txt has 1 lines.
   Dump of assembler code for function main: | flag.txt: | 1	FortID{N0_5h3ll_n33d3D_jU57_m41N_ce0eaeff26}
   ```

## Kết quả

```text
FortID{N0_5h3ll_n33d3D_jU57_m41N_ce0eaeff26}
```

Flag đọc trực tiếp từ dịch vụ đề bài. Chưa lưu phản hồi submission.

## Tái hiện

Cần Python 3 để base64 và mở socket TLS, một bộ GDB để kiểm cơ chế tại local (bài này dùng gdb 14.2 cục bộ; dịch vụ chạy `GNU gdb (Ubuntu 17.1…)`), và một instance đang chạy vì file flag nằm trong CWD của dịch vụ. Chi tiết quyết định của ELF nộp lên chỉ là một entry trong bảng dòng:

```text
file_names[1] = "flag.txt"     # basename only, no absolute comp_dir
```

Bản `mkdwarf.py` đã dùng là script hỗ trợ tại local, không nằm trong handout nên không được chép nguyên văn ở đây; khung client tương đương về mặt kết nối:

```python
import base64, socket, ssl

HOST = "gdb-saas-53b083dc24af.inst19.ctf.fortid.com"
ELF_PATH = "out.elf"           # built locally by mkdwarf.py
blob = base64.b64encode(open(ELF_PATH, "rb").read())

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
s = ctx.wrap_socket(socket.socket(), server_hostname=HOST)
s.connect((HOST, 1337))
# upload the base64 blob, then answer the function-name prompt with: /s main
```

Hoặc trên hệ thống có redirect ổn định:

```text
ncat --ssl gdb-saas-53b083dc24af.inst19.ctf.fortid.com 1337
```
