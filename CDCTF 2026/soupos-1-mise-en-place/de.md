# Đề bài - soupos-1-mise-en-place

## Nguyên văn đề

```text
soupOS 1: Mise en Place
479
Rev Eng pwn
soup

There is a flag file in the root bowl and you cannot read it. serve / will tell you why.

The flag format is cdctf{Ex4mP13_fL4g}

Your instance is running

https://bldtbfjt.i.cdctf.net
```

## Metadata đã xác minh

- Handout: `soupos-handout.tar.gz` (214.924 B, sha256 `c9fc07e2…92a1e7`) + `symbols.txt`
  (18.610 B, sha256 `1e1aad7e…04b7d9`) — **giống hệt** handout của soupOS 0.
- Instance noVNC, đăng nhập `cook` / `soup`.
- Cờ của bài này được capture verbatim ở giai đoạn quét bộ nhớ của stage 3 (xem `notes.md`), vì nó nằm
  sẵn trong `.rodata` của kernel.
