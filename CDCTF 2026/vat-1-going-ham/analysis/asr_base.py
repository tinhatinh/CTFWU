import whisper, json, sys
m=whisper.load_model("base", download_root="./wm")
r=m.transcribe("audio.wav", language="en", task="transcribe", beam_size=5,
               word_timestamps=True, condition_on_previous_text=False,
               initial_prompt="Radio transmission. Words may be spelled using the NATO phonetic alphabet.")
print("TEXT:", r["text"].strip())
json.dump([{k:v for k,v in s.items() if k!="no_speech_prob"} for s in r["segments"]], open("segs.json","w"), indent=1)
for s in r["segments"]: print(f"[{s['start']:6.2f}-{s['end']:6.2f}] {s['text']}")
