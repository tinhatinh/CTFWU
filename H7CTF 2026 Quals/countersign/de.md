# Countersign — Rev (Insane)

```
Countersign
insane
Docker
Rev
930 Points

Countersign is the attestation core of a licensed firmware module. Slide a pass under
the glass and the clerk stamps whatever you hand him, but the core itself only ever
walks a route it can vouch for.

Find the input that walks it all the way to the flag.

Objectives 0/1
1  flag  19  100%
Files countersign.zip 9 KB
Instance Running
nc pwn.h7tex.com 43708
Time to submit 19h 59m 9s
Submit Flag H7CTF{...}
```

## File

```
countersign   22768 B  ELF x86-64 PIE, stripped, động  sha256 39a30cf4c52896d3
note.txt        616 B
```

## note.txt (nguyên văn)

```
Countersign attestation core

The shipped binary is the attestation core exactly as it runs on the box.
Your instance runs the same core behind a plain TCP line protocol.

Commands (one per line):
  GET            stream this instance's program image as hex
  NONCE          this instance's nonce
  MINT <hex>     debug stamp for up to 16 bytes
  RUN <hex>      drive the core with a 24 byte input, print what it emits

The program image and the signing material are generated fresh for every
instance, so nothing about one box carries over to another.

Recover the 24 byte input that makes the core emit your flag.
```

## Định dạng flag

`H7CTF{...}` theo thẻ đề.

## Artefact đã bắt từ instance (2026-09-27)

- NONCE = `81c7ad957a5c8aa9`
- `GET` = 3037 byte, lưu `analysis/image.txt` (hex). Mở đầu `4353474e 0200 2800 0b48 | a98a5c7a95adc781 (= nonce đảo) | 0b48 ff 00 660d ...`
- `MINT 414243` = `a5125e08daf0` (6 byte cho 3 byte vào)
- `RUN 00*24` = `denied`
