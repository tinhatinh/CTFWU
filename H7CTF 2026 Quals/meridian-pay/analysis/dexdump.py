import logging, sys
logging.disable(logging.CRITICAL)
from androguard.misc import AnalyzeDex

path = sys.argv[1] if len(sys.argv) > 1 else "files/apk/classes.dex"
out = sys.argv[2] if len(sys.argv) > 2 else "de/dexdump.txt"
a, d, x = AnalyzeDex(path)
with open(out, "w", encoding="utf-8") as f:
    for cls in d.get_classes():
        f.write("\n######## CLASS %s access=%s\n" % (cls.get_name(), cls.get_access_flags()))
        for gf in cls.get_fields():
            f.write("  FIELD %s : %s\n" % (gf.get_name(), gf.get_descriptor()))
        for m in cls.get_methods():
            f.write("\n  == METHOD %s %s\n" % (m.get_name(), m.get_descriptor()))
            for ins in m.get_instructions():
                f.write("     %-16s %s\n" % (ins.get_name(), ins.get_output()))
print("wrote", out)
