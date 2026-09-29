# Đề bài - Read Me My Fortune

Không có ảnh thẻ đề: trang `/challenges/read-me-my-fortune/` đã trả 404 sau khi wave 1 đóng, nên không chụp lại được. Bản dưới chép nguyên văn từ text của thẻ khi trang còn mở.

## Nguyên văn đề

```text
EXP 200 · Wave 1
Read Me My Fortune

Welcome to Madam Elara's Personalized Fortune Reading Service. Take a seat and allow me
to gaze into your future...

Oh... The veil is parting... My format call is working! I see it! A flag is in your future!

Connect
Madame Elara's parlour speaks netcat:

nc read-my-fortune.pointeroverflowctf.com 9000

She will ask for your session token before beginning.

Downloads
Recommended: bring the service down to your workstation to test your exploit before you
burn tokens against the live server.

service.py                 a1421668d2270d5db45c35755b5b64942e2ec781af7746b034cc872a9f83c2ae
Dockerfile                 23a92701a5c893948a8b500d5c4be5b80dc2fe1c4ad51375acb789827437f664
runner.sh                  8290974899e127c690f4624000d3d518ae369ae171649a0b80c2b2b8a460e05f
entrypoint.sh              acda6269034dd96deea61bd67d2a8fbba12f288f5f1676f2bbad26ad9b962b5f
read_my_fortune.xinetd     fe2583b382b4fd2f9cf9c14614dec683747b5247f8f6638fc2a6f0b69fc267e3

For a quick local run without Docker: POCTF_DEV_MODE=1 python3 service.py. Dev mode skips
the token step and uses a placeholder flag so you can develop and iterate.
```

## Thông tin đã xác minh được

| Mục | Giá trị |
| --- | --- |
| Service | `read-my-fortune.pointeroverflowctf.com:9000`, TCP, one process per xinetd connection |
| Artifact | `files/service.py` 242 dòng, sha256 `a1421668d2270d5d...` khớp thẻ đề |
| Artifact | `files/Dockerfile`, `files/runner.sh`, `files/entrypoint.sh`, `files/read_my_fortune.xinetd`, cả 4 khớp sha256 trên thẻ |
| Session token | 6 phần `EXP1.<team_id>.<cid>.<nonce>.<expires_unix>.<sig26>`, đổi mỗi lần reload trang, hạn 15 phút |
| Cờ | `POCTF{<cid>.<team_id>.<nonce>.<sig26>}`, sig là base32 không dấu `=` cắt còn 26 ký tự của HMAC-SHA256 |
| Timeout | `CONNECTION_TIMEOUT_SEC = 120` qua `signal.alarm` |
| Chế độ dev | `POCTF_DEV_MODE=1` bỏ qua bước token, `FLAG = "POCTF{dev.flag.local.testing.only}"` |

## Hướng giải (tóm tắt)

`service.py` render template của người chơi bằng `template.format(name=..., sign=..., date=..., elara=_greet)`.
`elara` là một function object nên phép đi thuộc tính của format string chạm được
`__globals__` của nó, tức là namespace module, nơi `FLAG` được ghi rõ là global. Một field duy nhất
`{elara.__globals__[FLAG]}` in ra cờ. Chi tiết và các nhánh đã loại trừ trong `writeup.md` và `notes.md`.

## Chạy lại

```bash
python exploit.py --local                                            # proof trên service dev-mode
python exploit.py read-my-fortune.pointeroverflowctf.com 9000 "<token>"
```

Kết quả: `POCTF{127.612.IB2GGFAM2XGX6RDT.TEENFQ3KNWVEA3MCHJNFWFODQI}` (đã lưu trong `flag.txt`).
Token là của team và chỉ có hạn 15 phút, nên muốn chạy lại phải lấy token mới từ trang challenge.
