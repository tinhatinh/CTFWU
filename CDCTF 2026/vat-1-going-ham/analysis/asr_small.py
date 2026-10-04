import whisper, json
m=whisper.load_model("small", download_root="./wm")
P="NATO phonetic alphabet radio spelling: alpha bravo charlie delta echo foxtrot golf hotel india juliett kilo lima mike november oscar papa quebec romeo sierra tango uniform victor whiskey xray yankee zulu. Digits: zero one two three four five six seven eight nine niner fife tree."
for tag,(a,b),prompt in [("full",(0,97),P),("flagpart",(45,83),P)]:
    r=m.transcribe(f"audio.wav" if tag=="full" else f"part_{a}_{b}.wav", language="en",
                   beam_size=10, temperature=0.0, word_timestamps=True,
                   condition_on_previous_text=False, initial_prompt=prompt)
    print("=== %s ==="%tag); print(r["text"].strip())
    json.dump(r["segments"], open("segs_%s.json"%tag,"w"), indent=1, default=str)
    for s in r["segments"]:
        print(f"[{s['start']:6.2f}-{s['end']:6.2f}] {s['text']}")
        for w in s.get('words',[]): print(f"     {w['start']:6.2f}-{w['end']:6.2f} {w['word']!r} p={w.get('probability'):.2f}")
