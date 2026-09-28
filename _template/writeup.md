# <Challenge Name> — <Category> (<Difficulty>)

**Flag:** `<PREFIX>{...}` · **Files:** `<artifact>`, <size>, sha256 `<hash>`

## Đề bài

<2-4 câu: mục tiêu phải đạt là gì, đề cho những gì, tương tác với cái nào.>

## Phân tích ban đầu

<Kết quả triage: loại file, mitigation/kích thước/entropy, những điểm bất thường đầu tiên.
Nêu rõ vì sao những điểm đó gợi hướng này.>

## Các hướng đã loại

Trước khi chốt đã kiểm tra và loại các kênh sau (log đầy đủ ở `notes.md`):

1. **<giả thuyết>**: <bằng chứng phản bác>. Loại.
2. **<giả thuyết>**: <bằng chứng phản bác>. Loại.

## Chuỗi khai thác

**Bước 1 — <việc làm>.** <kỹ thuật + vì sao làm bước này>

```bash
<lệnh>
```

**Bước 2 — <việc làm>.** <code hoặc lệnh, kèm output thật>

```python
<đoạn code quyết định>
```

**Bước N — Kiểm chứng.** <bằng chứng kết quả không phải trùng hợp:
độ dài chẵn, magic hợp lệ, toàn bộ dữ liệu khớp, v.v.>

## Flag

```bash
python solve.py files/<artifact>
```

```
<output thật của script, chứa cờ>
```

## Reproduce

```bash
python exploit.py files/<artifact>
```
