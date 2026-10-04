import numpy as np
from scipy.signal import stft, welch
x=np.load('x.npy'); sr=24000
# 1) DTMF check
dt_lo=[697,770,850,941]; dt_hi=[1209,1336,1477,1850]
f,t,Z=stft(x,fs=sr,nperseg=2048,noverlap=1024)
def mag(fr):
    j=np.argmin(abs(f-fr)); return Z[j]
print("== DTMF band energies (mean |X|) ==")
for lo in dt_lo:
    print(f"  {lo}: {np.mean(np.abs(mag(lo))):.5f}", end='')
    for hi in dt_hi: print(f"  {hi}:{np.mean(np.abs(mag(hi))):.5f}", end='')
    print()
print("  broadband ref 500Hz:", round(float(np.mean(np.abs(mag(500)))),5), " 2000Hz:", round(float(np.mean(np.abs(mag(2000)))),5))
# 2) pitch track via autocorrelation on 40ms frames
print("== pitch (Hz) per 60ms, voiced frames ==")
pitches=[]
for i in range(0,len(x)-1440,1440):
    s=x[i:i+1440]-x[i:i+1440].mean()
    if np.sqrt((s**2).mean())<0.01: pitches.append(0); continue
    a=np.correlate(s,s,'full')[len(s)-1:]
    a[0:int(sr/1000)]=0
    lag=np.argmax(a[int(sr/500):int(sr/70)]+int(sr/500))
    pitches.append(sr/(lag+sr/500) if a.max()>0.2*a[0] else 0)
p=np.array(pitches,float); v=p[p>0]
print("  voiced frames:",len(v),"/",len(p))
print("  pitch median %.1f  p10 %.1f p90 %.1f"%(np.median(v),np.percentile(v,10),np.percentile(v,90)))
h=np.histogram(v,bins=np.arange(40,400,10))[0]
print("  pitch histogram:", " ".join(f"{int(b/10-4)}:{c}" for b,c in zip(np.arange(40,400,10),h) if c>0))
