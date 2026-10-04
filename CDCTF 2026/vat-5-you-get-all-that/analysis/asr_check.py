"""ASR toan bo file de xem phan doc code word co lay ra chu cai nao khong.
Chay: python analysis/asr_check.py     (can model Whisper 'small', weights tai lan dau)
"""
import subprocess
import sys
from pathlib import Path

import whisper

WAV = Path("analysis/_asr.wav")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "files/captured_cred_call.mp3",
                "-acodec", "pcm_s16le", "-ar", "16000", str(WAV)], check=True)

model = whisper.load_model("small", device="cpu")
res = model.transcribe(str(WAV), word_timestamps=True, fp16=False, language="en")
toks = []
for s in res["segments"]:
    print(f"[{s['start']:6.2f} {s['end']:6.2f}] {s['text']}")
    for w in s.get("words", []):
        toks.append((w["start"], w["word"].strip()))
print(f"tokens = {len(toks)}")
print("token tu 9 s tro di:", [t for st, t in toks if st >= 9.0])
WAV.unlink()
