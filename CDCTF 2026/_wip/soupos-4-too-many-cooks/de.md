# Đề bài - soupos-4-too-many-cooks

## Nguyên văn đề

```text
soupOS 4: Too Many Cooks
489
Rev Eng pwn
soup

soupyc runs in ring 0. There is a routine nothing ever calls, and your symbol map has its address.

The flag format is cdctf{Ex4mP13_fL4g}

Your instance is running

https://elqgxtjy.i.cdctf.net
```

## Metadata đã xác minh

- Handout: `soupos-handout.tar.gz` (214.924 B, sha256 `c9fc07e2…92a1e7`) + `symbols.txt`
  (18.610 B, sha256 `1e1aad7e…04b7d9`) — giống hệt stage 0/1/2/3.
- `symbols.txt`: `00100990 T serve_the_special` → `1051024` ở hệ thập phân (giá trị phải gõ vào lệnh).
- **Trạng thái:** cơ chế đã chứng minh ở local bằng source thật; lệnh chưa được xác nhận bằng ảnh chụp
  màn hình trong phiên này, nên bài nằm trong `_wip` và không có `flag.txt`.
