CTX = "xwxgu{zgyzhs1m_rg_fk_rm_s3iv}"
ALPHA = "abcdefghijklmnopqrstuvwxyz"


def caesar(s, k):
    return "".join(chr((ord(c) - 97 + k) % 26 + 97) if c in ALPHA else c for c in s)


def xor(s, k):
    return "".join(chr(ord(c) ^ k) for c in s)


def atbash(s):
    return "".join(chr(219 - ord(c)) if c in ALPHA else c for c in s)


print("[*] 25 Caesar shifts (letters only, braces and underscores untouched):")
for k in range(1, 26):
    print("    %+3d  %s" % (k, caesar(CTX, k)))

print("[*] 256 single-byte XOR keys, output fully printable:")
for k in range(256):
    p = xor(CTX, k)
    if all(32 <= ord(c) < 127 for c in p):
        print("    0x%02x  %s" % (k, p))

print("[*] Atbash: %s" % atbash(CTX))
print("[*] atbash(atbash(CTX)) == CTX ->", atbash(atbash(CTX)) == CTX)
