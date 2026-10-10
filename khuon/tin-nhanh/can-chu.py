# Căn mốc từng chữ của lời đọc -> dau-vao/moc-chu.json [{w,s,e,doan}]
#   uv run --with faster-whisper --with numpy python can-chu.py
# 1) Whisper KHÔNG gợi ý -> in bản nghe để kiểm máy đọc đúng chưa (tên kênh, số).
# 2) Whisper CÓ gợi ý lời -> mốc từng từ; ghép vào lời gốc bằng difflib, từ không khớp thì nội suy;
# 3) bám mốc bắt đầu vào điểm năng lượng lên (sau khoảng im) gần nhất ±0,12 s (Whisper lệch ±0,1 s).
import json,re,subprocess,difflib,pathlib,unicodedata
import numpy as np
import sys,os; sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent.parent/'cong-cu')); import mo_hinh   # A4: Whisper ghim revision
T=pathlib.Path(__file__).resolve().parent
kb=json.load(open(T/'kich-ban.json'))
x=np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',str(T/'dau-vao/giong.mp3'),'-ac','1','-ar','16000','-f','f32le','-'],capture_output=True,check=True).stdout,dtype=np.float32)
wm=mo_hinh.nap_whisper('float32')   # K14: float32 on dinh hon int8 giua arm (Mac) va x86 (GitHub) - xem NHAT-KY
seg,_=wm.transcribe(x,language='vi',beam_size=5,temperature=0.0,condition_on_previous_text=False)
print('NGHE KHONG GOI Y:',' '.join(s.text.strip() for s in seg))
loi=' '.join(d['loi'] for d in kb)
seg,_=wm.transcribe(x,language='vi',beam_size=5,temperature=0.0,word_timestamps=True,initial_prompt=loi)
ws=[(w.word.strip(),w.start,w.end) for s in seg for w in s.words]
def chuan(t):
    t=''.join(c for c in unicodedata.normalize('NFD',t.lower()) if unicodedata.category(c)!='Mn').replace('đ','d')
    return re.sub(r'[^a-z0-9]','',t)
goc=[];
for d in kb:
    for w in d['loi'].split(): goc.append(dict(w=w,doan=d['k']))
a=[chuan(g['w']) for g in goc]; b=[chuan(w[0]) for w in ws]
sm=difflib.SequenceMatcher(None,a,b,autojunk=False); khop=0
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal':
        for k in range(i2-i1): goc[i1+k]['s'],goc[i1+k]['e']=ws[j1+k][1],ws[j1+k][2]; khop+=1
    elif tag=='replace' and (i2-i1)==(j2-j1):
        for k in range(i2-i1): goc[i1+k]['s'],goc[i1+k]['e']=ws[j1+k][1],ws[j1+k][2]
# noi suy tu chua co moc
for i,g in enumerate(goc):
    if 's' in g: continue
    l=next((j for j in range(i-1,-1,-1) if 's' in goc[j]),None); r=next((j for j in range(i+1,len(goc)) if 's' in goc[j]),None)
    t0=goc[l]['e'] if l is not None else 0.0; t1=goc[r]['s'] if r is not None else len(x)/16000
    n=(r if r is not None else len(goc))-(l if l is not None else -1)-1; k=i-(l if l is not None else -1)-1
    g['s']=t0+(t1-t0)*k/max(1,n); g['e']=t0+(t1-t0)*(k+1)/max(1,n)
# bam vao diem nang luong len
hop=160; n=len(x)//hop; db=20*np.log10(np.sqrt(np.mean(x[:n*hop].reshape(n,hop)**2,axis=1))+1e-9); nen=np.percentile(db,50)
for g in goc:
    a0=max(6,int((g['s']-0.12)*100)); b0=min(n-1,int((g['s']+0.12)*100))
    cand=[k for k in range(a0,b0) if db[k]>nen-8 and db[k-6:k].max()<nen-16]
    if cand: g['s']=min(cand,key=lambda k:abs(k*0.01-g['s']))*0.01
# chu DAU moi doan bam vao diem giong bat dau lai sau khoang lang >= 150 ms gan nhat (+-0,6 s) — 10/10: 'Còn' noi suy 24,14 nhung that 24,64
on=[];sil=0
for k in range(n):
    if db[k]<nen-16: sil+=1
    else:
        if sil>=15 and db[k:k+6].max()>nen-8: on.append(k*0.01)   # tieng len tu tu (lam mo dau) -> nhin truoc 60 ms
        sil=0
for i,g in enumerate(goc):
    if i and goc[i-1]['doan']!=g['doan']:
        c=[o for o in on if abs(o-g['s'])<=0.6]
        if c: g['s']=min(c,key=lambda o:abs(o-g['s']))
# bam vao KHOANG LANG that (>= 120 ms) — Tin nhanh 10/10: 'Tin' (doan t2) noi suy 6,74-7,64 vat qua 2 khoang lang, that 7,53;
# 'PS' noi suy 3,86 trong khi giong noi lai tu 3,61; 'ré' 10,48 nam truoc khoang lang 10,60-10,85
lang=[];s0=None
for k in range(n):
    if db[k]<nen-16:
        if s0 is None: s0=k
    else:
        if s0 is not None and k-s0>=12: lang.append((s0*0.01,k*0.01))
        s0=None
for i,g in enumerate(goc):
    trong=[(a,b) for a,b in lang if a>=g['s']-0.01 and b<=g['e']+0.01 and b-a>=0.25]   # tu dai bat thuong: khoang lang nam GIUA tu
    if trong:
        a,b=max(trong,key=lambda x:x[1]); a0=min(x[0] for x in trong)
        g['s']=b
        if i and goc[i-1]['e']<a0: goc[i-1]['e']=a0
        continue
    for a,b in lang:
        if a-0.05<=g['s']<b: g['s']=b; break                                      # bat dau nam TRONG khoang lang
        if i and goc[i-1]['e']<=b<g['s'] and g['s']-b>0.1: g['s']=b; break          # giong noi lai som hon moc noi suy
    if g['e']<g['s']: g['e']=g['s']
# 2 tu dinh cung moc (do dai ~0) -> chia doan theo so ky tu
for i in range(len(goc)-1):
    a,b=goc[i],goc[i+1]
    if b['s']-a['s']<0.06 and b['e']-a['s']>0.2:
        k=len(a['w'])/(len(a['w'])+len(b['w'])); m=a['s']+(b['e']-a['s'])*k; a['e']=b['s']=round(m,3)
for i in range(len(goc)-1):
    if goc[i]['e']>goc[i+1]['s']: goc[i]['e']=goc[i+1]['s']
    if goc[i]['e']<=goc[i]['s']: goc[i]['e']=min(goc[i+1]['s'],goc[i]['s']+0.15)
out=[dict(w=g['w'],s=round(g['s'],2),e=round(g['e'],2),doan=g['doan']) for g in goc]
json.dump(out,open(T/'dau-vao/moc-chu.json','w'),ensure_ascii=False,indent=0)
print(f'{khop}/{len(goc)} tu khop Whisper; ghi dau-vao/moc-chu.json')
for d in kb:
    ds=[g for g in out if g['doan']==d['k']]; print(f"  {d['k']:4s} {ds[0]['s']:5.2f}-{ds[-1]['e']:5.2f}  {' '.join(g['w'] for g in ds)[:70]}")
