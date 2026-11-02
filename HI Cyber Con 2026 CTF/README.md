# HI Cyber Con 2026 CTF

![HI Cyber Con 2026](../site/assets/competitions/hi-cyber-con-2026-ctf.png)

18 writeup thuộc **HI Cyber Con 2026 (HI CON CTF)**. Mỗi bài gồm một file `.md` tiếng Việt và một file `.en.md` tiếng Anh theo template hiện tại của repo. Đề bài, phân tích, lời giải, code và kết quả được trình bày trong từng file.

Flag format: `hiCTF{...}`. Ngày solve lấy từ ngày ghi trong tài liệu gốc (31/10 hoặc 01/11/2026); không suy ra giờ solve từ thời điểm chỉnh sửa file.

## Danh sách writeup

| Challenge | Category | VN | EN | Solve |
|---|---|---|---|---|
| Apex Engine | Pwn | [VN](apex-engine.md) | [EN](apex-engine.en.md) | 2026-10-31 |
| ChronoGrind | Crypto | [VN](chronogrind.md) | [EN](chronogrind.en.md) | 2026-10-31 |
| Cipher | Mobile | [VN](cipher.md) | [EN](cipher.en.md) | 2026-10-31 |
| Cold Chain | Hardware | [VN](cold-chain.md) | [EN](cold-chain.en.md) | 2026-10-31 |
| Cold Circuit | Reverse | [VN](cold-circuit.md) | [EN](cold-circuit.en.md) | 2026-10-31 |
| File Viewer | Web | [VN](file-viewer.md) | [EN](file-viewer.en.md) | 2026-10-31 |
| Ground Station | Hardware | [VN](ground-station.md) | [EN](ground-station.en.md) | 2026-10-31 |
| Labyrinth | Misc | [VN](labyrinth.md) | [EN](labyrinth.en.md) | 2026-10-31 |
| Overgrowth | Web | [VN](overgrowth.md) | [EN](overgrowth.en.md) | 2026-10-31 |
| Quiet Upgrade | Web3 | [VN](quiet-upgrade.md) | [EN](quiet-upgrade.en.md) | 2026-10-31 |
| Rocinate | Crypto | [VN](rocinate.md) | [EN](rocinate.en.md) | 2026-10-31 |
| Standing Order | Web3 | [VN](standing-order.md) | [EN](standing-order.en.md) | 2026-10-31 |
| Stillwell Estates | Web | [VN](stillwell-estates.md) | [EN](stillwell-estates.en.md) | 2026-11-01 |
| The Coffee Shop | Web | [VN](the-coffee-shop.md) | [EN](the-coffee-shop.en.md) | 2026-11-01 |
| The Miner That Mined The Victim | Forensics | [VN](the-miner-that-mined-the-victim.md) | [EN](the-miner-that-mined-the-victim.en.md) | 2026-11-01 |
| The Quiet Divide | NTA | [VN](the-quiet-divide.md) | [EN](the-quiet-divide.en.md) | 2026-10-31 |
| Titan Relay | Pwn | [VN](titan-relay.md) | [EN](titan-relay.en.md) | 2026-10-31 |
| No Bit Sings Alone | Steg | [VN](no-bit-sings-alone.md) | [EN](no-bit-sings-alone.en.md) | 2026-11-01 |

## Tác giả đề

Theo danh sách nguồn, các đề của Hidden Investigations ngoại trừ: **Apex Engine** (otolk1), **File Viewer** (0x0Sayan), **Overgrowth** (Oxnoobsec), **Rocinate** (Tsumiiiiiiii), **Titan Relay** (0xblackfox).

## Đọc và tái hiện

- Hai bản của mỗi bài dùng cùng category, ngày solve, code, output và flag. Các nhãn được chuẩn hóa theo site: Android → Mobile, Blockchain → Web3, Network → NTA, Cryptography → Crypto.
- The Coffee Shop và Stillwell Estates có flag riêng theo instance của đội. Flag Stillwell có đúng một khoảng trắng đầu; phản hồi `goodFlag` được giữ trong bài. Chuỗi `local_development_only_do_not_submit` của Coffee Shop là một phần giá trị ledger, không tự ý bỏ nó hoặc hậu tố instance.
- No Bit Sings Alone có hai ảnh spectrogram và [script giải độc lập](assets/no-bit-sings-alone/solve.py); toàn bộ code cũng được nhúng trong cả hai bản Markdown. Bài ghi rõ SHA-256 của WAV và kiểm tra authentication tag AES-GCM.
- Một số tài liệu gốc chỉ giữ tóm tắt, công thức hoặc hash rút gọn. Từng bài nêu phần dữ liệu/script còn thiếu; không coi các địa chỉ instance cũ hoặc prefix `...` là input tái hiện đầy đủ. Bộ writeup không kèm toàn bộ artifact đề.

## Các bài chưa có lời giải hoàn chỉnh

Blind Index, Unremarkable, Paper Trail, Ouroboros, The Collector's Trail, Rocinate Revenge, Low Tide Ledger và Ghost in RAM chưa có writeup hoàn chỉnh trong bộ nguồn này. Tyco không được đưa vào danh sách vì không có bằng chứng submission được chấp nhận.
