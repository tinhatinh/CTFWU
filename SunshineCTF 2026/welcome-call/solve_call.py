#!/usr/bin/env python
"""Welcome Call (Bsides Orlando, oatzs) -- recover the spoken flag from welcomecall.pcap.

Chain:
  1. SIP INVITE/200-OK between 192.0.2.10 and 192.0.2.20 negotiates RTP audio:
     m=audio, payload type 0 = PCMU (mu-law) at 8 kHz, 20 ms ptime.
  2. Concatenate the 778 RTP payloads in stream order (sequence numbers are
     contiguous, timestamps step by exactly 160, single SSRC -> no reordering,
     no loss).
  3. Expand mu-law with the STANDARD LIBRARY (audioop.ulaw2lin). A hand-written
     G.711 table here produced values ~4x out of range and made the whole
     pipeline lie: the spectrogram looked like speech, STT hallucinated, and the
     first conclusion was "it's just a voice call".
  4. The audio is time-reversed speech. Reverse the sample array and transcribe.

Whisper is only needed for step 4; the script prints the reversed WAV either way.

usage: python solve_call.py [--no-transcribe]
"""
import os
import subprocess
import sys
import wave

import numpy as np
from scapy.all import IP, UDP, Raw, rdpcap

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PCAP = "files/welcomecall.pcap"
OUT = "analysis"
DO_TRANSCRIBE = "--no-transcribe" not in sys.argv


def rtp_payloads(path):
    """RTP payloads of the mu-law stream, in capture order, plus stream stats."""
    chunks, seqs, tss = [], [], []
    for p in rdpcap(path):
        if UDP not in p or Raw not in p:
            continue
        b = bytes(p[Raw].load)
        if len(b) < 13 or (b[0] >> 6) != 2 or (b[1] & 0x7F) != 0:
            continue
        chunks.append(b[12:])
        seqs.append(int.from_bytes(b[2:4], "big"))
        tss.append(int.from_bytes(b[4:8], "big"))
    gaps = sum(1 for i in range(1, len(seqs)) if (seqs[i] - seqs[i - 1]) % 65536 != 1)
    bad_ts = sum(1 for i in range(1, len(tss)) if (tss[i] - tss[i - 1]) % 2**32 != 160)
    return b"".join(chunks), len(chunks), gaps, bad_ts


def write_wav(path, pcm16, rate=8000):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm16)


def main():
    os.makedirs(OUT, exist_ok=True)
    for p in (PCAP,):
        if not os.path.exists(p):
            sys.exit("[-] missing %s" % p)

    print("[1] SIP negotiation:")
    for p in rdpcap(PCAP):
        if UDP in p and Raw in p:
            t = bytes(p[Raw].load).decode("latin-1", "replace")
            for line in t.split("\r\n"):
                if line.startswith(("m=audio", "a=rtpmap", "a=ptime", "s=")):
                    print("    %-14s %s" % (p[IP].src, line))

    payload, n, gaps, bad_ts = rtp_payloads(PCAP)
    print("\n[2] RTP: %d packets, %d payload bytes, %d sequence gaps, %d bad timestamps"
          % (n, len(payload), gaps, bad_ts))
    if gaps or bad_ts:
        print("    [!] stream is not contiguous - reorder before decoding")

    print("\n[3] mu-law expansion via stdlib audioop")
    try:
        import audioop
        pcm = audioop.ulaw2lin(payload, 2)
    except Exception as exc:                                # noqa: BLE001
        print("    audioop unavailable (%s); falling back to ffmpeg" % exc)
        open(OUT + "/payload.raw", "wb").write(payload)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "mulaw", "-ar", "8000",
                        "-ac", "1", "-i", OUT + "/payload.raw", "-c:a", "pcm_s16le",
                        OUT + "/call_decoded.wav"], check=True)
        pcm = None
    if pcm is not None:
        write_wav(OUT + "/call_decoded.wav", pcm)
        # independent cross-check of the decoder
        open(OUT + "/payload.raw", "wb").write(payload)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "mulaw", "-ar", "8000",
                        "-ac", "1", "-i", OUT + "/payload.raw", "-c:a", "pcm_s16le",
                        OUT + "/call_ffmpeg.wav"], check=True)
        a = np.frombuffer(pcm, dtype="<i2").astype(float)
        w = wave.open(OUT + "/call_ffmpeg.wav", "rb")
        b = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(float)
        k = min(len(a), len(b))
        print("    %.2f s of audio; corr(audioop, ffmpeg) = %.4f"
              % (len(a) / 8000, np.corrcoef(a[:k], b[:k])[0, 1]))

    x = np.frombuffer(pcm if pcm is not None else open(OUT + "/call_decoded.wav", "rb").read()[44:],
                      dtype="<i2")
    write_wav(OUT + "/call_reversed.wav", x[::-1].copy())
    print("\n[4] wrote %s/call_reversed.wav  (time-reversed: the call is backwards speech)" % OUT)

    if not DO_TRANSCRIBE:
        print("    transcribe it yourself or re-run without --no-transcribe")
        return
    import whisper
    m = whisper.load_model("small")
    r = m.transcribe(OUT + "/call_reversed.wav", language="en", fp16=False, beam_size=5,
                     condition_on_previous_text=False, temperature=0.0)
    msg = r["text"].strip()
    print("\n[5] transcription:\n    %s" % msg)

    import re
    body = msg.lower()
    # the speaker *names* the brackets: "... is <prefix> with a left curly bracket
    # <body> right curly bracket. All lowercase, no spaces."
    m2 = re.search(r"([a-z]+)(?: with a)? left curly bracket[., ]+(.*?)[., ]+right curly bracket",
                   body, re.S)
    if m2:
        prefix = m2.group(1)
        inner = re.sub(r"[^a-z0-9_]", "", m2.group(2))     # "all lowercase, no spaces"
        flag = "%s{%s}" % (prefix, inner)
        print("\n[+] FLAG: %s" % flag)
        open("flag.txt", "w").write(flag)
    else:
        print("\n[!] could not assemble the flag mechanically; read the sentence above")


if __name__ == "__main__":
    main()
