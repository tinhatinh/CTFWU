"""ASR bo tro (khong rang buoc tu dien) bang Vosk small-en, lay gia thuyet doc lap voi Whisper.

Chay:  python analysis/asr_vosk.py <duong-dan-model-vosk> <file-wav-16k>

Whisper va Vosk doc khac nhau o nhung tu dong nghia, nen loi cua moi ben lo ra khi
doi chieu chung: do la thu hieu de biet o nao can sua bang rang buoc chuoi hash.
Model Vosk (41 MB) khong commit trong repo.
"""

import json
import sys
import wave

from vosk import KaldiRecognizer, Model, SetLogLevel

SetLogLevel(-1)
model = Model(sys.argv[1])
wf = wave.open(sys.argv[2], "rb")
rec = KaldiRecognizer(model, wf.getframerate())
rec.SetWords(True)
words = []
while True:
    data = wf.readframes(4000)
    if not data:
        break
    if rec.AcceptWaveform(data):
        words += json.loads(rec.Result()).get("result", [])
words += json.loads(rec.FinalResult()).get("result", [])

line, start = [], None
for w in words:
    if start is None:
        start = w["start"]
    line.append(w["word"])
    if len(line) == 13:
        print("[%6.2f-%6.2f] %s" % (start, w["end"], " ".join(line)))
        line, start = [], None
if line:
    print("[%6.2f-%6.2f] %s" % (start, words[-1]["end"], " ".join(line)))
