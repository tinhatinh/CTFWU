import numpy as np
from scipy.signal import spectrogram as sgram
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
x=np.load('x.npy'); sr=24000
for fmax,nper,h in [(12000,1024,5),(1200,8192,4),(6000,4096,4)]:
    fr,t,S=sgram(x,fs=sr,nperseg=nper,noverlap=nper//2)
    m=fr<=fmax
    db=10*np.log10(S[m]+1e-14)
    lo,hi=np.percentile(db,25),np.percentile(db,99.7)
    fig=plt.figure(figsize=(22,h)); ax=fig.add_axes([0,0,1,1])
    ax.imshow(db,aspect='auto',origin='lower',extent=[0,t[-1],fr[0],fr[m][-1]],
              cmap='magma',vmin=lo,vmax=hi); ax.set_ylabel('Hz'); fig.savefig('sg_%d_%d.png'%(fmax,nper),dpi=110); plt.close(fig)
    print('ok sg_%d_%d.png'% (fmax,nper), db.shape)
