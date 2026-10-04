# Đề bài - soupos-2-salt-to-taste

## Nguyên văn đề

```text
soupOS 2: Salt to Taste
489
Rev Eng pwn
soup

Only the headchef knows today's special. The kitchen roster is world-readable.

The flag format is cdctf{Ex4mP13_fL4g}

Your instance is running

https://ctuwlvwa.i.cdctf.net
```

## Metadata đã xác minh

- Handout: `soupos-handout.tar.gz` (214.924 B, sha256 `c9fc07e2…92a1e7`) + `symbols.txt`
  (18.610 B, sha256 `1e1aad7e…04b7d9`) — giống hệt handout của stage 0 và 1 (`cmp` trực tiếp).
- Instance noVNC, đăng nhập `cook` / `soup`.
- Roster thật trên máy: `headchef:0:f63a9eb7`, `cook:1:e7d471fc` (đọc bằng `pour /etc/kitchen`).
- **Trạng thái cờ:** cơ chế đã nộp thành công để sang stage 3, nhưng chuỗi FLAG2 **không được ghi lại
  verbatim** trong phiên này nên thư mục này không có `flag.txt` (theo quy ước của repo).
