import sys, re, wave, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Usage: python asr_whisper.py <audio> <model> <download_root> [--words]
AUDIO, MODEL, ROOT = sys.argv[1], sys.argv[2], sys.argv[3]
import whisper
m = whisper.load_model(MODEL, download_root=ROOT)

PROMPT = ("S/Key one-time passcodes: CODE 1 followed by six capitalized English words. CODE 2 ...")
opts = dict(fp16=False, temperature=0.0, initial_prompt=PROMPT)
if "--words" in sys.argv:
    opts["word_timestamps"] = True
r = m.transcribe(AUDIO, beam_size=5 if "--words" in sys.argv else 5, **opts)
for s in r["segments"]:
    print("[%.2f-%.2f] %s" % (s["start"], s["end"], s["text"].strip()))

# group the spoken payload into the eight six-word codes
toks = [t.upper() for t in re.findall(r"[A-Za-z0-9]+", " ".join(s["text"] for s in r["segments"]))]
codes, i = [], 0
while i < len(toks) - 6:
    if toks[i] == "CODE" and re.fullmatch(r"[1-8]", toks[i + 1]):
        codes.append(toks[i + 2:i + 8])
        i += 8
    else:
        i += 1
print("\n### parsed %d codes" % len(codes))
for n, c in enumerate(codes, 1):
    print("Code %d: %s" % (n, " ".join(c)))
