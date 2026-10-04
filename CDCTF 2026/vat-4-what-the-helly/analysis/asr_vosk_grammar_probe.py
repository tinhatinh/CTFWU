"""Thu nhan dang bi rang buoc dung 2048 tu dien S/Key bang Vosk (huong that bai).

Chay:  python analysis/asr_vosk_grammar_probe.py <model-vosk> <wav-16k> [so-lan-thu]

KaldiRecognizer ho tro grammar JSON list, ve ly thuyet ep dau ra chi la tu dien S/Key.
Thu tren tung lan cat 1.1 s (mot tu) va in ra so ket qua nhan duoc.
"""

import json
import os
import re
import sys
import wave

from vosk import KaldiRecognizer, Model, SetLogLevel

SetLogLevel(-1)
model = Model(sys.argv[1])
WAV = sys.argv[2]
MODE = sys.argv[3] if len(sys.argv) > 3 else "6"
DICT = [w.strip().lower() for w in open("files/skey_dictionary.txt", encoding="utf-8") if w.strip()]
print("grammar: %d tu" % len(DICT))

if MODE == "all":
    # moi dong "[a-b] Word ..." trong log Whisper small la mot tu OTP
    SLICES = []
    for line in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "asr_small_run.log"),
                     encoding="utf-8"):
        m = re.match(r"^\[(\d+\.\d+)-(\d+\.\d+)\]\s+([A-Za-z]+)\s*\.\.\.\s*$", line.strip())
        if m and len(m.group(3)) <= 6:
            SLICES.append((float(m.group(1)), float(m.group(2)), m.group(3).title()))
else:
    # thoi diat cua nam tu dau va "Knoll", lay truc tiep tu asr_small_run.log
    SLICES = [(6.00, 7.04, "Bait"), (7.04, 8.24, "Gower"), (9.56, 10.64, "Tacked"),
              (14.16, 15.28, "Glyn"), (31.68, 32.84, "Cuts"), (48.32, 49.48, "Knoll")]
wf = wave.open(WAV, "rb")
rate = wf.getframerate()
empty = 0
for a, b, heard in SLICES:
    wf.setpos(int((a - 0.05) * rate))
    data = wf.readframes(int((b - a + 0.1) * rate))
    rec = KaldiRecognizer(model, rate, json.dumps(DICT))
    rec.SetMaxAlternatives(5)
    out = []
    if rec.AcceptWaveform(data):
        out = json.loads(rec.Result()).get("alternatives", [])
    out += json.loads(rec.FinalResult()).get("alternatives", [])
    cands = [o["word"] for o in out if o.get("word")]
    empty += not cands
    print("[%5.2f-%5.2f] nghe=%-8s candidates=%s" % (a, b, heard, " ".join(cands) or "(rong)"))
print("ket luan: %d/%d lan cat tra ve rong -> nhan dang rang buoc tu dien khong dung duoc voi lat ngan"
      % (empty, len(SLICES)))
