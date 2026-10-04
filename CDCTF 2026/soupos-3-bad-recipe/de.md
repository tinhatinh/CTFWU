# Đề bài - soupos-3-bad-recipe

## Nguyên văn đề

```text
soupOS 3: Bad Recipe
498
Rev Eng pwn
soup

Somewhere in kernel memory is a string that is never written to disk. Build a binary that convinces the
loader to hand it to you.

There is no upload: /unhex.elf turns hex text into raw bytes and jot types it. Work in /prep, and give
cook absolute paths.

The flag format is cdctf{Ex4mP13_fL4g}

Your instance is running

https://enlpceyk.i.cdctf.net
```

## Metadata đã xác minh

- Handout: `soupos-handout.tar.gz` (214.924 B, sha256 `c9fc07e2…92a1e7`) + `symbols.txt`
  (18.610 B, sha256 `1e1aad7e…04b7d9`) — giống hệt stage 0/1/2.
- `challenge_init()` ghim cờ stage 3 trên heap và tự in địa chỉ ra log khởi động:
  `klog("[chal] stage3 flag pinned at %p\n", ...)` → trên máy là `[chal] stage3 flag pinned at 0x17600c`
  (heap_arena = `0x00176000` trong `symbols.txt`).
- Symbol map dùng chung cho cả 5 stage; các mốc cần nhớ: `heap_arena 0x176000`,
  `kernel_end 0x9c7000`, `serve_the_special 0x100990`, `sc_state 0x9a0c60`.
- Bài này **có** cờ verbatim (xem `flag.txt`), capture từ chính output của binary trên VM.
