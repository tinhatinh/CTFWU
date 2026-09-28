import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from androguard.core.dex import DEX

d = DEX(bytearray(open("apk/classes.dex", "rb").read()))
for c in d.get_classes():
    print("=== CLASS", c.name)
    for m in c.get_methods():
        print("  --", m.get_access_flags_string(), m.get_name(), getattr(m, "signature", ""))
        code = m.get_code()
        if not code or not code.get_bc():
            continue
        for ins in code.get_bc().get_instructions():
            try:
                out = ins.get_output()
            except Exception:
                out = ""
            print("     ", ins.get_name(), out)
