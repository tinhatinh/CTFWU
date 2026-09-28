import sys

def utf16_runs(d):
    out, i, seen = [], 0, []
    while i < len(d) - 1:
        if d[i + 1] == 0 and 0x20 <= d[i] < 0x7F:
            j = i
            while j + 1 < len(d) and d[j + 1] == 0 and 0x20 <= d[j] < 0x7F:
                j += 2
            s = d[i:j + 1:2].decode("latin-1")
            if s not in seen:
                seen.append(s)
            i = j + 2
        else:
            i += 1
    return seen

for fn in sys.argv[1:] or ["files/apk/AndroidManifest.xml"]:
    print("==== %s ====" % fn)
    for s in utf16_runs(open(fn, "rb").read()):
        if len(s) > 1:
            print(repr(s))
