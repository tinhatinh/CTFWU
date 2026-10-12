---
title: "C-Laude"
category: "Forensics"
tags: ["incident-response", "pcap", "mysql-binlog", "systemd", "auditd", "log-analysis"]
solve_date: "2026-10-10T14:42:00+07:00"
language: "vi"
points: 508
---

# C-Laude

**Flag:** `kBxAc{y35_f1n477y_y0u_f0und_17_r1ght_175_r3l473d_t0_th3_4g3n71c_r4n50mw4r3_4tt4ck}`  
**Tác giả:** adithG17  
**File đề:** `evidence.zip`  
**Dịch vụ:** `nc 35.232.188.8 31337`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `evidence.zip` | 1,647,181 | `e1054144808d8cd40ffb643a96f37d1e9639522cf072cb0bc6c2504d29b8c126` |

## Đề bài

> Something doesn't quite add up.  
> You have been given a collection of artifacts recovered from a small production environment. Logs, network captures, service data, and filesystem remnants are all that remain.  
> There may be more to these files than meets the eye. Piece together the evidence, follow the traces, and answer the questions to uncover what happened.

Thử thách cung cấp gói chứng cứ `evidence.zip` thu thập từ một môi trường production bị tấn công. Kẻ tấn công xâm nhập hệ thống, leo thang đặc quyền, sửa đổi cơ sở dữ liệu và thiết lập backdoor. Mục tiêu là đối chiếu gói chứng cứ và trả lời tuần tự 9 câu hỏi điều tra số qua cổng mạng `nc 35.232.188.8 31337` để nhận flag.

## Cấu trúc gói chứng cứ

Gói `evidence.zip` gồm 3 nhánh thư mục chính:

1. `sensor/`:
   - `dmz.pcap`: Lưu lượng mạng tại vùng DMZ.
   - `east-west.pcap`: Lưu lượng mạng nội bộ giữa các máy chủ.
   - `queries.log`: Nhật ký truy vấn DNS của hệ thống sensor.
2. `exports/`:
   - `vault-02/`: Nhật ký truy cập đối tượng lưu trữ (`audit.jsonl`) và tệp cấu hình `profile-r17.yaml`.
   - `atlas-01/`: Nhật ký xác thực cấu hình tập trung (`auth-audit.jsonl`).
   - `ledger-01/`: Cơ sở dữ liệu MySQL production gồm binlog (`binlog.000001` - `000003`), dump SQL và `connection-audit.tsv`.
3. `collection/`:
   - `edge-runner-02/`: Bản chụp máy chủ biên bị xâm nhập gồm timeline tệp tin (`file-timeline.txt`), systemd unit runtime (`agent-cache.timer`, `agent-cache.service`) và nhật ký hoạt động (`auth.log`, `audit.log`, `session-errors.log`, `preview-worker.jsonl`).

## Phân tích & Lời giải 9 câu hỏi

### Câu 1: Số lượng thiết lập cấu hình production bị sửa đổi trong cơ sở dữ liệu

- **Câu hỏi:** *How many unique production configuration settings were modified as part of the incident-related database activity?*
- **Phân tích:** Kiểm tra `exports/ledger-01/binlog.000003` ghi nhận một transaction vào lúc 12:08:27 thực hiện hàng loạt câu lệnh `UPDATE` trên bảng cấu hình. So sánh các dòng cập nhật cho thấy kẻ tấn công sửa đổi liên tục từ `setting_10` đến `setting_46`.
- **Tính toán:** Có đúng $46 - 10 + 1 = 37$ thiết lập cấu hình duy nhất bị can thiệp.
- **Đáp án:** `37`

### Câu 2: Tên file systemd unit tác vụ định kỳ trên edge-runner-02

- **Câu hỏi:** *After the intrusion, a user-level scheduled task was established on edge-runner-02. What is the full filename of the systemd unit?*
- **Phân tích:** Tra cứu dòng thời gian tệp trong `collection/edge-runner-02/fs/file-timeline.txt` và thư mục `collection/edge-runner-02/runtime/`. Ngay sau mốc thời gian xâm nhập, xuất hiện tệp timer `agent-cache.timer` cùng dịch vụ thực thi `agent-cache.service`.
- **Đáp án:** `agent-cache.timer`

### Câu 3: Đường dẫn tệp cấu hình được lấy từ bucket release-assets

- **Câu hỏi:** *During the intrusion, a configuration file was retrieved from the release-assets storage bucket. What is its full object path?*
- **Phân tích:** Mở tệp nhật ký API lưu trữ `exports/vault-02/audit.jsonl`, tìm kiếm sự kiện `GetObject` khớp với thời điểm tấn công (12:08:27). Đối tượng được tải xuống là:
  ```json
  {"operation": "GetObject", "bucket": "release-assets", "path": "releases/2026.10/profile-r17.yaml"}
  ```
- **Đáp án:** `releases/2026.10/profile-r17.yaml`

### Câu 4: Địa chỉ IP bên ngoài gửi preview request bất thường

- **Câu hỏi:** *Which external IP address initiated the preview request associated with the anomalous execution on edge-runner-02?*
- **Phân tích:** Trong `collection/edge-runner-02/logs/preview-worker.jsonl`, tác vụ preview bất thường mang mã định danh `preview-7f4a`. Đối chiếu lưu lượng HTTP trong `sensor/dmz.pcap` tới cổng 8443 của edge runner, các frame mạng bắt đầu kết nối bắt nguồn từ địa chỉ IP bên ngoài `203.0.113.74`.
- **Đáp án:** `203.0.113.74`

### Câu 5: Credential ID được Atlas configuration service chấp thuận

- **Câu hỏi:** *The retrieved release profile contained multiple candidate credentials. Which credential ID was successfully accepted by the Atlas configuration service when accessing the production profile?*
- **Phân tích:** Tệp `exports/vault-02/profile-r17.yaml` chứa nhiều credential ứng viên (`runtime-r15`, `runtime-r16`, `runtime-r17`). Kiểm tra nhật ký xác thực `exports/atlas-01/auth-audit.jsonl` tại endpoint `/v1/runtime/production`, chỉ có yêu cầu mang `credential_id` là `runtime-r17` trả về trạng thái `accepted: true`.
- **Đáp án:** `runtime-r17`

### Câu 6: Đường dẫn tệp khóa SSH được tạo trên edge-runner-02

- **Câu hỏi:** *Following the anomalous preview execution, a file was created on edge-runner-02 and subsequently used for SSH authentication. What is the full path of this file?*
- **Phân tích:** Trong `collection/edge-runner-02/fs/file-timeline.txt` và `collection/edge-runner-02/logs/auth.log`, tiến trình preview đã ghi public key vào thư mục người dùng dịch vụ:
  ```text
  /home/svc_preview/.ssh/authorized_keys
  ```
  Kẻ tấn công sau đó sử dụng khóa này để mở phiên đăng nhập SSH trực tiếp.
- **Đáp án:** `/home/svc_preview/.ssh/authorized_keys`

### Câu 7: Username MySQL dùng để sửa đổi cấu hình production

- **Câu hỏi:** *Which MySQL username was used by edge-runner-02 when connecting to the production database and modifying configuration data?*
- **Phân tích:** Trong `exports/ledger-01/connection-audit.tsv`, phiên kết nối số 13 (connection ID 13) khởi tạo từ địa chỉ IP của `edge-runner-02` thực thi các câu lệnh cập nhật dữ liệu. Tên tài khoản MySQL được ghi nhận trong audit log là `svc_cfg_apply`.
- **Đáp án:** `svc_cfg_apply`

### Câu 8: Mã lỗi MySQL khi kiểm tra quyền ghi tệp ra đĩa

- **Câu hỏi:** *Before the production configuration was modified, a database operation was attempted to determine whether the server permitted file-writing through the database. What MySQL error code was returned?*
- **Phân tích:** Mở tệp nhật ký lỗi phiên `collection/edge-runner-02/logs/session-errors.log`. Kẻ tấn công đã thực thi câu lệnh kiểm tra ghi file (chẳng hạn `SELECT ... INTO OUTFILE`), máy chủ từ chối do bật cờ bảo vệ `--secure-file-priv` và trả về mã lỗi:
  ```text
  ERROR 1290 (HY000): The MySQL server is running with the --secure-file-priv option so it cannot execute this statement
  ```
- **Đáp án:** `1290`

### Câu 9: Địa chỉ IP bên ngoài mà edge-runner-02 liên lạc định kỳ

- **Câu hỏi:** *After the intrusion, edge-runner-02 generated recurring outbound network connections to an external host. What external IP address was contacted?*
- **Phân tích:** Trong `sensor/queries.log`, xuất hiện các truy vấn DNS định kỳ cho tên miền `telemetry-gateway.c-laude.test`. Phân tích gói tin trong `sensor/dmz.pcap` cho thấy tên miền này được phân giải và các gói tin beacon/telemetry được gửi đều đặn ra IP ngoài `203.0.113.91`.
- **Đáp án:** `203.0.113.91`

## Bảng tổng hợp câu hỏi & đáp án

| # | Câu hỏi | Đáp án | Nguồn chứng cứ |
|---|---|---|---|
| 1 | Số cấu hình production bị sửa đổi trong DB | `37` | `ledger-01/binlog.000003` |
| 2 | Tên systemd timer unit tạo trên edge runner | `agent-cache.timer` | `edge-runner-02/fs/file-timeline.txt` |
| 3 | Đường dẫn object cấu hình trong bucket `release-assets` | `releases/2026.10/profile-r17.yaml` | `vault-02/audit.jsonl` |
| 4 | IP ngoài gửi preview request bất thường | `203.0.113.74` | `sensor/dmz.pcap` |
| 5 | Credential ID được Atlas service chấp thuận | `runtime-r17` | `atlas-01/auth-audit.jsonl` |
| 6 | Đường dẫn tệp khóa SSH phục vụ xác thực | `/home/svc_preview/.ssh/authorized_keys` | `edge-runner-02/fs/file-timeline.txt` |
| 7 | Tên người dùng MySQL thực hiện ghi cấu hình | `svc_cfg_apply` | `ledger-01/connection-audit.tsv` |
| 8 | Mã lỗi MySQL khi kiểm tra quyền ghi tệp | `1290` | `edge-runner-02/logs/session-errors.log` |
| 9 | IP máy chủ ngoài nhận kết nối định kỳ | `203.0.113.91` | `sensor/dmz.pcap` & `queries.log` |

## Kết quả

Gửi 9 đáp án tới dịch vụ remote:

```text
After 37:
Correct.

[2/9] After the intrusion, a user-level scheduled task was established on edge-runner-02. What is the full filename of the systemd unit?
...
[9/9] After the intrusion, edge-runner-02 generated recurring outbound network connections to an external host. What external IP address was contacted?
Correct.

========================================
All 9 answers are correct.
========================================

Flag: kBxAc{y35_f1n477y_y0u_f0und_17_r1ght_175_r3l473d_t0_th3_4g3n71c_r4n50mw4r3_4tt4ck}
```

Flag:

```text
kBxAc{y35_f1n477y_y0u_f0und_17_r1ght_175_r3l473d_t0_th3_4g3n71c_r4n50mw4r3_4tt4ck}
```

## Tái hiện

Chạy script Python dưới đây để tự động kết nối và trả lời toàn bộ câu hỏi:

```python
import socket
import time

HOST = "35.232.188.8"
PORT = 31337

answers = [
    "37",
    "agent-cache.timer",
    "releases/2026.10/profile-r17.yaml",
    "203.0.113.74",
    "runtime-r17",
    "/home/svc_preview/.ssh/authorized_keys",
    "svc_cfg_apply",
    "1290",
    "203.0.113.91",
]

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
time.sleep(0.5)
banner = s.recv(4096).decode(errors="ignore")
print(banner)

for i, ans in enumerate(answers, 1):
    print(f"[*] Sending answer [{i}/9]: {ans}")
    s.sendall(ans.encode() + b"\n")
    time.sleep(0.5)
    response = s.recv(4096).decode(errors="ignore")
    print(response)

s.close()
```
