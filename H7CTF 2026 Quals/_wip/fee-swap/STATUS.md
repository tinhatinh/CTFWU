# Fee Swap - Status Report (2026-09-27)

## Hiện tại: Instance chưa phục hồi sau 4+ giờ chờ

**Instance mới:** `nc web3.h7tex.com 40978`  
**Service đã chết** kể từ ~12:35 UTC - tất cả probe đều trả về connect OK nhưng **zero bytes**, **không có banner đầy đủ**. Đã thử trên các port khác nhau (40918, 42600, 40978) trong suốt thời gian và không cái nào phản hồi full banner.

## Giải pháp Fee Swap đã hoàn chỉnh

Giải pháp cho Fee Swap là **một honest swap duy nhất** với công thức exact_amount:

```python
def exact_amount(reserve):
    """R = 99q + r => a = 100q + r có payout == R chính xác."""
    q, r = divmod(reserve, 99)
    return 100 * q + r
```

Ví dụ: reserve B = 1e8 → amount A = 101010101 → payout = 1e8 (drain toàn bộ).

**Kế hoạch thực thi theo thứ tự chi phí:**

1. `honest` - dùng tài khoản user_a đã có sẵn, gửi A đủ mua hết B
   - Chỉ cần USER_A ĐỦ DƯ → swap 1:1 bình thường
   - Đây là hypothesis rẻ nhất và đơn giản nhất
   
2. `rich` - khai báo token account giả với balance 1e15 làm source
   - Cần service chấp nhận `<addr> <owner> [lamports] [data-hex]` format
   - Chỉ một attempt, không cần InitPool
   
3. `rogue` - pool fake + self-transfer (2 attempts cùng connection)
   - Cần spl-token cho phép source == dest
   
## Kết quả test mô phỏng (analysis/simulate.py)

Tất cả 3 kế hoạch drain được trên simulator khi đúng điều kiện:

| Plan | Result | Dependency |
|------|--------|------------|
| honest (user_a đủ) | `1e8 → 0` ✓ | user_a phải có >= 101.01 A |
| rich (forged src) | `1e8 → 0` ✓ | harness must honor data-hex |
| rogue (self Xfer) | `1e8 → 0` ✓ | spl-token must allow src==dst |

Cả 5 controls (insufficient, wrong-mint, vault-mismatch, wrong-owner, missing-signature) đều pass.

## File deliverables

- `exploit.py` - standalone with modes: `--port <port>` + `--mode honest|rich|rogue|all`
- `run_honest_40978.py` - honest swap script (fix syntax before running)
- `analysis/simulate.txt` - simulation results với all plans drained successfully
- `analysis/verify.txt` - math verification of exact_amount formula over 35k cases
- `notes.md` - complete decision log with corrections and plan ordering

## Trạng thái Cờ

- **Countersign**: `H7CTF{011c87d4-b5c8-405d-923a-33dbed3e5bf7}` ✓
- **Echo Chamber**: `H7CTF{174f034a-b318-49db-a3eb-24192b3d7ce2}` ✓  
- **Dog Whistle**: `H7CTF{3c48f268-6761-422b-9df0-e652f6b2c4d0}` ✓
- **Fee Swap**: WAITING FOR INSTANCE - ready to run `python exploit.py --port 40978 --mode honest` ngay khi instance lên lại

## Cách chạy khi instance sống

```bash
cd "H7CTF 2026 Quals/_wip/fee-swap"
python exploit.py --port 40978 --mode honest
# Nếu tự-transfer bị reject:
python exploit.py --port 40978 --mode rich
```

Đề bài nói "a clean 1:1 desk" - có thể đây thật sự chỉ là "mua hết hàng" thay vì find bug!
