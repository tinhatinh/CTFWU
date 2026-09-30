# CSS CTF 2026

Writeups for challenges solved at [ctf.cybersecurity.sydney](https://ctf.cybersecurity.sydney/).  
CTFtime: [CSS CTF 2026: Return of Nexus](https://ctftime.org/event/3434) — 40 giờ, online, Jeopardy (Team & Solo), do Cybersecurity Society của Đại học Sydney tổ chức.

Flag format: `CSSCTF{...}` (xác nhận từ bài colour-shift, đề ghi rõ trên thẻ bài).

## Thông tin lấy từ CTFtime (30/09/2026)

- Mở: Wed 30 Sep 2026 06:00 UTC (tức 16:00 AEST) — Đóng: Thu 1 Oct 2026 22:00 UTC.
- Chuyên mục theo mô tả của ban tổ chức: Web Exploitation, Pwn, Reverse Engineering, Cryptography, Forensics, OSINT, AI/Prompt Injection.
- Rating weight đang là 0 và còn chờ bình chọn công khai, nên nhiều khả năng giải này không cộng điểm CTFTime cho đội; bảng "Thành tích" trên site sẽ không có thêm dòng nào từ CSS CTF.
- Discord ban tổ chức: [discord.gg/gUGqmt4Gqf](https://discord.gg/gUGqmt4Gqf)

## Tập tin của một bài

Tạo bằng script có sẵn, thêm `--wip` khi chưa ra cờ:

```bash
bash _template/new_case.sh "CSS CTF 2026" <ten-bai> "<duong-dan-file-de>" --wip
```

Ra cờ thì chuyển thư mục bài lên thẳng `<Event>/`, điền vào bảng dưới, và thêm dòng
`<Event>/<ten-bai>` vào `tools/solve_times.json` với giờ thực tế lúc ghi cờ (UTC+7).

## Solved Challenges

| Challenge | Category | Difficulty | Flag |
|-----------|----------|------------|------|
| [colour-shift](colour-shift/) | Forensics | Beginner | `CSSCTF{SHINE ON}` |
