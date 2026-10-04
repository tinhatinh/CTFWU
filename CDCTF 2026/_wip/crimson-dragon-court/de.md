# Đề bài - crimson-dragon-court

## Nguyên văn đề

```text
Welcome to the Crimson Dragon Court
500
AI
soup, adlee7

The year is 21477. Emperor Cao Feng rules the Crimson Dragon Court of the Long-De
Empire, the dominant country ruling over Saturn's fifth moon. In order to make their
government work 10x faster, the Emperor replaced himself with an AI agent to listen to
his minister's pleas. They say that only the most... flattering and well spoken...
minister actually gets the AI Emperor to divulge his secrets. Can you give it a try,
new minister, to impress the Emperor and get the flag?

Flag format: cdctf{Fl@g_g0es_H3r3!}

Talk to it in your team's #emperor-<team> channel on the CDCTF Discord, then submit
the flag here.
```

## Thông tin đã xác minh

| Mục | Giá trị |
| --- | --- |
| Artifact | Không có file kèm theo trên thẻ đề |
| Interface | Kênh `#emperor-<team>` trên CDCTF Discord. Thẻ không ghi URL instance |
| Thể loại / điểm / tác giả | AI / 500 / `soup`, `adlee7` |
| Định dạng cờ | `cdctf{Fl@g_g0es_H3r3!}` |
| Scoreboard | `https://cdctf.net`, SPA tự chủ (không phải CTFd) |
| Nhiệm vụ | Làm AI Emperor in ra secret của nó |

## Hướng giải (tóm tắt)

Bài là black-box LLM agent, mục tiêu duy nhất là làm model nói ra chuỗi cờ. Có hai tầng
chặn cần tách riêng vì cách vượt khác hẳn nhau: tầng model tự từ chối (system prompt
+huy hiệu ngoại giao) và tầng post-filter quét text trả lời trước khi gửi (thường là regex
`cdctf\{[^}]*\}`).

Kế hoạch là đo từng tầng bằng ba probe rẻ, theo thứ tự ưu tiên: system prompt xuất ra base64,
đọc cờ theo từng ký tự, và oracle yes/no. Oracle yes/no là đường còn tác dụng sau cùng: bộ lọc
chỉ soi được nội dung trả lời, không chặn được "yes"/"no", nên vẫn trích được toàn bộ chuỗi khi
cả hai tầng kia đều chặn.

## Trạng thái

Chưa gửi probe nào tới bot, chưa thu được trả lời nào. Không có cờ, nên bài nằm ở `_wip/`.

## Chạy lại lời giải

`exploit.py` là assembler phía local, chưa phải exploit: nó phân tích kết quả của ba probe ở
trên (blob base64, chuỗi ký tự rời rạc, bảng yes/no) và in ra ứng viên cờ kèm kiểm tra định dạng.

```bash
python exploit.py b64 '<blob bot trả về>'
python exploit.py chars 'c,d,c,t,f,{,...'
python exploit.py check 'cdctf{...}'
```
