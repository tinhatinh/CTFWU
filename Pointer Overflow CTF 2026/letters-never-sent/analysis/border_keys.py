CT = "PXYWN{2.612.QNTOXCK6E7DKGMKC.WK4KK6MPPPRJGOFZZI66EISSED}"
L = [c for c in CT if c.isalpha()]
C = [ord(c) - 65 for c in L]
bf = lambda c, k: (k - c) % 26
dec = lambda key, start=0: "".join(chr(bf(C[i], ord(key[(i - start) % len(key)]) - 65) + 65) for i in range(start, len(C)))

# frame labels, clockwise from top-left
TOP = [("Rose", 0), ("Elder", 1), ("Fern", 0), ("Swan", 0), ("Lily", 1), ("Tulip", 0)]
RIGHT = [("Poppy", 0), ("Anchor", 1), ("Harp", 0), ("Willow", 0), ("Marigold", 0), ("Dove", 0)]
BOTTOM_L2R = [("Swan", 1), ("Carnation", 0), ("Yarrow", 0), ("Violet", 0), ("Poppy", 1), ("Oak", 0)]
LEFT_T2B = [("Tulip", 0), ("Elder", 1), ("Swan", 0), ("Fern", 0), ("Lily", 0), ("Rose", 0)]

clockwise = TOP + RIGHT + list(reversed(BOTTOM_L2R)) + list(reversed(LEFT_T2B))
starred = "".join(w[0][0] for w, s in clockwise if s)
unstarred = "".join(w[0][0] for w, s in clockwise if not s)
allinit = "".join(w[0][0] for w, s in clockwise)
print("clockwise order:", [w for w, s in clockwise])
print("starred  :", starred, len(starred))
print("unstarred:", unstarred, len(unstarred))
print("all      :", allinit, len(allinit))

for name, key in (("unstarred x2", unstarred + unstarred), ("unstarred", unstarred),
                  ("all24", allinit), ("ELAPSE", "ELAPSE")):
    if len(key) < 36:
        key = key * (36 // len(key) + 1)
    body = "".join(chr(bf(C[i + 5], ord(key[i % len(key)]) - 65) + 65) for i in range(36))
    print(f"{name:12s} body -> {body}")
