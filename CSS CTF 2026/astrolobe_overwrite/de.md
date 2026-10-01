# Đề bài - Astrolobe Overwrite

## Nguyên văn đề

```text
The Astrolobe Overwrite
746
Expert PWN Reverse Engineering
When "The Severance" hit in 2100, the Kuiper Relay wasn't abandoned. Instead, it was locked into a loop governed by the Council. To prevent manual takeover, the council's instruction consumes and rewrites its own memory.

To force an administrative override, your payload must achieve harmonic resonance across the three rings of the Astrolabe:

Unravel the permutation field of the first gate.
Stabilize the coupled wave recurrence across the lattice.
Lock onto the projective coordinates of the orbital horizon.

The telemetry receiver requires exact synchronization with the beacon and will purge the core if total execution falls outside the quantum decay window.

Flag Format: CSSCTF{...}

nc 34.116.80.78 7654
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/ouroboros.7z` (copy từ: `C:\Users\Administrator\Downloads\ouroboros.7z`) |
| Kích thước | 4121 byte |
| SHA-256 | `e7aecc224f6ead512639a33f42f9aa0464ce309ea758b180764ec8dd053e5f2e` |
| Loại file | 7-zip archive data, version 0.4 |
| Nhiệm vụ | Ném payload lên dịch vụ netcat `34.116.80.78:7654` để nhận flag |
| Định dạng cờ | `CSSCTF{...}` |

## Hướng giải (tóm tắt)

Binary `nexus_core` là một VM tự tham chiếu: mỗi lệnh 4 bytes được giải mã bằng biến `z` và tra bảng `P` (được hoán vị tại chỗ sau mỗi bước), với cổng kiểm tra gồm 6 đồng nhất thức mod 65521 – ba cổng đầu dựa trên phép nhân ngược với hằng `0x58862fdccdf01111`, hai cổng tiếp theo là đường cong Edwards `y² = x³+17x+43`. Trích khối check (0x15AD–0x1966) sang bộ nhớ thực thi trên Windows và chạy trực tiếp làm oracle, vá từng nhánh lỗi thành tag riêng để xác nhận mô hình; liệt kê toàn bộ nghiệm trong không gian suy biến 4 ẩn → `(t₀,t₁,t₂,t₃)=(1,218,59611,783)`; xây dựng chương trình 420 byte (105 lệnh, 840 ký tự hex) qua assembler mô phỏng chính xác trạng thái ban đầu của VM.

## Chạy lại lời giải

```bash
python exploit.py files/ouroboros.7z
```

Kết quả: `CSSCTF{0ur0b0r0s_g00d_j0b_b01s_heh3_67}` (đã lưu trong `flag.txt`).
