import sys
d=open(sys.argv[1],'rb').read()
BR=[0,32,40,48,56,64,80,96,112,128,160,192,224,256,320,0]  # v2 layer3 index? actually MPEG2 L3 bitrate table
# MPEG2 Layer III bitrate idx table
L3=[0,8,16,24,32,40,48,56,64,80,96,112,128,144,160]
SR={0:22050,1:24000,2:16000,3:0}
def isf(b,o):
    if b[o]!=0xFF: return False
    if (b[o+1]&0xE0)!=0xE0: return False
    ver=(b[o+1]>>3)&3      # 0=MPEG2.5,1=reserved,2=MPEG2,3=MPEG1
    lay=(b[o+1]>>1)&3      # 0=reserved,1=L3,2=L2,3=L1
    if lay!=1: return False
    bi=(b[o+2]>>4)&15; si=(b[o+2]>>2)&3; pad=(b[o+2]>>1)&1
    if bi==0 or bi==15 or si==3: return False
    ver2 = 2 if ver in (2,0) else 1
    sr=SR[si] if ver2==2 else [44100,48000,16000,0][si]
    br=L3[bi] if ver2==2 else [0,32,40,48,56,64,80,96,112,128,160,192,224,256,320][bi]
    if br==0: return False
    fl=(144*1000*br//sr)+(pad) if ver2==2 else (72*1000*br//sr)+pad
    return fl if fl>24 else False
o=10 if d[:3]==b'ID3' else 0
# skip id3v2 sized
if d[:3]==b'ID3':
    sz=(d[6]<<21)|(d[7]<<14)|(d[8]<<7)|d[9]
    o=10+sz
print("id3 size bytes:", o-10, "frame start at", o, repr(d[10:o]))
frames=0; gaps=[]; last=None; sizes={}
while o+4<=len(d):
    fl=isf(d,o)
    if fl and o+fl<=len(d):
        if last is not None and o>last: gaps.append((last,o-last))
        sizes[fl]=sizes.get(fl,0)+1
        frames+=1; last=o+fl; o=last
    else: o+=1
print("frames:",frames,"covered:",last,"of",len(d),"tail:",len(d)-(last or 0))
print("distinct frame sizes:",sorted(sizes.items(),key=lambda x:-x[1])[:8])
print("gaps (non-frame byte runs):",len(gaps), "total gap bytes:", sum(g for _,g in gaps))
print("first gaps:",gaps[:12])
