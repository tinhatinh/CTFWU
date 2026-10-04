# Đề bài - soupos-0-welcome-to-the-kitchen

## Nguyên văn đề

```text
soupOS 0: Welcome to the Kitchen
431
Rev Eng pwn
soup

soupOS is a 32-bit OS vibe-coded from scratch (yes, I told Claude to just make a
32-bit OS with no human intervention. Smart? No.). It is complete with a Kitchen
theme, no mitigations, and four places where it trusts the wrong thing.

Click Start Instance, open the URL, and log in:

cook:   cook
secret: soup
One instance serves all five challenges. The handout is the redacted source plus
a symbol map of the kernel you are connected to.

Free flag, so you can check your submission works: cdctf{soupOS_is_better_than_arch}

If something is genuinely broken, tell Jeffery Barrett on the CDCTF admin team and
pray. If you get bored, type doom.

Your instance is running

https://dqrgwcfv.i.cdctf.net
```

## Metadata đã xác minh

- File đính kèm: `soupos-handout.tar.gz` (214.924 B, sha256 `c9fc07e2c9d189bd51fc7db1206b4766dcfc921908e9ed2055116d55f992a1e7`,
  121 mục, thư mục gốc `soupos/`) và `symbols.txt` (18.610 B, sha256 `1e1aad7ec719a97f774f382bd4c228b70c6a87a112384a0c7cec711f5f04b7d9`).
- **Cả bốn thẻ soupOS dùng đúng một handout và một symbol map** (đã `cmp` từng cặp: giống hệt), nên một lần
  đọc source là đủ cho cả chain 5 bài.
- Instance là noVNC/QEMU, đăng nhập `cook` / `soup`.
- Cờ của bài này nằm ngay trên thẻ đề (bài free flag, dùng để kiểm tra kênh nộp bài).
