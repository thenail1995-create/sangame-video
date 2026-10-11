# Can moc tung chu cua loi doc Top 5 -> dau-vao/moc-chu.json [{w,s,e,doan}]  (doan = khoa doan trong kich-ban.json)
#   uv run --frozen python can-chu.py [ra.json]
# 1) Whisper KHONG goi y -> in ban nghe de kiem may doc dung chua (ten game, so, ten kenh).
# 2) CACH CHINH ("cum cau", Top 5 11/10): loi doc co dau cau (. ! ? … , :) ma giong eleven_v3 nghi o dau cau (co khi nghi them cho khac). Ranh gioi cum = khoang LANG
#    chon bang QUY HOACH DONG theo SO AM TIET (khong dung moc Whisper: voi loi "300.000", "Away Out" Whisper nghe khac -> 63/114 tu khong khop, noi suy deu 0,26 s/tu,
#    moc lech tien giay -> phu de tran khung + tieng dong de len chu). Moi cum vao/ra dung diem tieng noi; chu trong cum chia theo SO AM TIET. Whisper chi con de NGHE kiem.
# 3) Neu khong tach duoc cum (khoang lang dau cau ngan/khong ro) -> CACH DU PHONG: Whisper co goi y + bam nang luong len/khoang lang (K9, K12).
import json,re,subprocess,difflib,pathlib,unicodedata,sys
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent.parent/'cong-cu')); import mo_hinh   # A4: Whisper ghim revision
T=pathlib.Path(__file__).resolve().parent
kb=json.load(open(T/'kich-ban.json'))   # Top 5: danh sach [{k,loi}] (Keo thom: {'doan':[...]})
x=np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',str(T/'dau-vao/giong.mp3'),'-ac','1','-ar','16000','-f','f32le','-'],capture_output=True,check=True).stdout,dtype=np.float32)
wm=mo_hinh.nap_whisper('float32')   # K14: float32 on dinh hon int8 giua arm (Mac) va x86 (GitHub) - xem NHAT-KY
seg,_=wm.transcribe(x,language='vi',beam_size=5,temperature=0.0,condition_on_previous_text=False,word_timestamps=True)
seg=list(seg); WS0=[(w.word.strip(),w.start,w.end) for s in seg for w in s.words]
print('NGHE KHONG GOI Y:',' '.join(s.text.strip() for s in seg))
goc=[]
for d in kb:
    for w in d['loi'].split(): goc.append(dict(w=w,doan=d['k']))
hop=160; n=len(x)//hop; db=20*np.log10(np.sqrt(np.mean(x[:n*hop].reshape(n,hop)**2,axis=1))+1e-9); nen=np.percentile(db,50)

# ===================== CACH CHINH: cum cau =====================
VOWEL=r'[aeiouyàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ]+'
def am_tiet(w):   # so am tiet (uoc luong): moi nhom nguyen am = 1; so = 1; "Spider-Man" = 3
    k=0
    for p in re.sub(r'[^\wÀ-ỹ]+','|',w.lower().replace('-','|')).split('|'):
        if p: k+=1 if re.fullmatch(r'\d+',p) else max(1,len(re.findall(VOWEL,p)))
    return k
def lang_giua(thr=12,blip=6):
    """-> (khoang lang [(a,b) khung 10 ms] nam GIUA tieng noi, v0, v1). Cum tieng < blip khung (nhieu/tho) coi la lang; lang = db < nen-thr."""
    v=db>=nen-thr; idx=np.where(v)[0]; v0,v1=idx[0],idx[-1]
    k=v0
    while k<=v1:
        if v[k]:
            j=k
            while j<=v1 and v[j]: j+=1
            if j-k<blip: v[k:j]=False
            k=j
        else: k+=1
    lang=[];s0=None
    for k in range(v0,v1+1):
        if not v[k]:
            if s0 is None: s0=k
        else:
            if s0 is not None: lang.append((s0,k)); s0=None
    return lang,v0,v1+1
def cum_cau():
    cum=[];cur=[]
    for g in goc:
        cur.append(g)
        if re.search(r'[.!?…,:]$',g['w']): cum.append(cur); cur=[]   # ':' ("Hang nam:") giong cung nghi
    if cur: cum.append(cur)
    P=len(cum); lang,v0,v1=lang_giua()
    lang=[g for g in lang if g[1]-g[0]>=8]
    # CHON RANH GIOI BANG QUY HOACH DONG THEO SO AM TIET (Top 5 11/10: Whisper nghe "300.000"/"Away Out" khac loi goc -> 63/114 tu khong khop, noi suy deu 0,26 s/tu,
    # moc chu lech tien giay: phu de tran khung + tieng dong de len chu). Cum i ket thuc sau S_i am tiet => ranh gioi i du kien o v0 + S_i*r + (i-0,5)*nghi; chon P-1
    # khoang lang (theo thu tu) sao cho tong binh phuong lech nho nhat, thuong khoang lang dai. Khong phu thuoc Whisper.
    if len(lang)<P-1: return None,f'chi co {len(lang)} khoang lang >= 80 ms cho {P-1} ranh gioi cum'
    syl=[sum(am_tiet(g['w']) for g in p) for p in cum]; tot=sum(syl); NGHI=0.25
    r=((v1-v0)*.01-(P-1)*NGHI)/tot
    S=0; E=[]
    for i in range(P-1): S+=syl[i]; E.append(v0*.01+S*r+(i+0.5)*NGHI)
    tam=[(g[0]+g[1])*.005 for g in lang]; dai=[(g[1]-g[0])*.01 for g in lang]
    cost=lambda i,j:((tam[j]-E[i])/0.35)**2-3.0*min(dai[j],0.8)
    M=len(lang); INF=1e18; f=[[INF]*M for _ in range(P-1)]; tr=[[-1]*M for _ in range(P-1)]
    for j in range(M): f[0][j]=cost(0,j)
    for i in range(1,P-1):
        for j in range(i,M):
            for q in range(i-1,j):
                if f[i-1][q]<INF and f[i-1][q]+cost(i,j)<f[i][j]: f[i][j]=f[i-1][q]+cost(i,j); tr[i][j]=q
    j=min(range(M),key=lambda j:f[P-2][j]) if P>1 else None
    if j is None or f[P-2][j]>=INF: return None,'khong chon duoc ranh gioi cum'
    ids=[j]
    for i in range(P-2,0,-1): j=tr[i][j]; ids.append(j)
    chon=[lang[k] for k in reversed(ids)]
    lech=max(abs(tam[k]-E[i]) for i,k in enumerate(reversed(ids)))
    nho=min((g[1]-g[0])*.01 for g in chon)
    if nho<0.10: return None,f'khoang lang dau cau ngan nhat chi {nho:.2f}s'
    ranh=[];a=v0
    for s0,s1 in chon: ranh.append((a,s0)); a=s1
    ranh.append((a,v1))
    for p,(cs,ce) in zip(cum,ranh):
        wgt=[am_tiet(g['w']) for g in p]; tot=sum(wgt); t=cs*.01; D=(ce-cs)*.01
        for g,wi in zip(p,wgt):
            g['s']=t; t+=D*wi/tot; g['e']=t
    return [(cs*.01,ce*.01) for cs,ce in ranh],f'{P} cum, {P-1} ranh gioi chon theo so am tiet + khoang lang (ngan nhat {nho:.2f}s, lech du kien toi da {lech:.2f}s)'
ranh,ghi_chu=cum_cau()
if ranh:
    print('CAN CHU: cach cum cau —',ghi_chu); khop=len(goc)
else:
    print('CAN CHU: KHONG tach duoc cum cau ->',ghi_chu,'-> dung cach du phong Whisper')
    # ===================== CACH DU PHONG: Whisper + bam nang luong =====================
    loi=' '.join(d['loi'] for d in kb)
    seg,_=wm.transcribe(x,language='vi',beam_size=5,temperature=0.0,word_timestamps=True,initial_prompt=loi)
    ws=[(w.word.strip(),w.start,w.end) for s in seg for w in s.words]
    def chuan(t):
        t=''.join(c for c in unicodedata.normalize('NFD',t.lower()) if unicodedata.category(c)!='Mn').replace('đ','d')
        return re.sub(r'[^a-z0-9]','',t)
    a=[chuan(g['w']) for g in goc]; b=[chuan(w[0]) for w in ws]
    sm=difflib.SequenceMatcher(None,a,b,autojunk=False); khop=0
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if tag=='equal':
            for k in range(i2-i1): goc[i1+k]['s'],goc[i1+k]['e']=ws[j1+k][1],ws[j1+k][2]; khop+=1
        elif tag=='replace' and (i2-i1)==(j2-j1):
            for k in range(i2-i1): goc[i1+k]['s'],goc[i1+k]['e']=ws[j1+k][1],ws[j1+k][2]
    for i,g in enumerate(goc):   # noi suy tu chua co moc
        if 's' in g: continue
        l=next((j for j in range(i-1,-1,-1) if 's' in goc[j]),None); r=next((j for j in range(i+1,len(goc)) if 's' in goc[j]),None)
        t0=goc[l]['e'] if l is not None else 0.0; t1=goc[r]['s'] if r is not None else len(x)/16000
        nn=(r if r is not None else len(goc))-(l if l is not None else -1)-1; k=i-(l if l is not None else -1)-1
        g['s']=t0+(t1-t0)*k/max(1,nn); g['e']=t0+(t1-t0)*(k+1)/max(1,nn)
    for g in goc:   # bam vao diem nang luong len (sau khoang im) +-0,12 s
        a0=max(6,int((g['s']-0.12)*100)); b0=min(n-1,int((g['s']+0.12)*100))
        cand=[k for k in range(a0,b0) if db[k]>nen-8 and db[k-6:k].max()<nen-16]
        if cand: g['s']=min(cand,key=lambda k:abs(k*0.01-g['s']))*0.01
    on=[];sil=0
    for k in range(n):   # chu DAU moi doan bam vao diem giong bat dau lai sau khoang lang >= 150 ms (+-0,6 s) (K9)
        if db[k]<nen-16: sil+=1
        else:
            if sil>=15 and db[k:k+6].max()>nen-8: on.append(k*0.01)
            sil=0
    for i,g in enumerate(goc):
        if i and goc[i-1]['doan']!=g['doan']:
            c=[o for o in on if abs(o-g['s'])<=0.6]
            if c: g['s']=min(c,key=lambda o:abs(o-g['s']))
    lang=[];s0=None   # bam vao KHOANG LANG that >= 120 ms (K12)
    for k in range(n):
        if db[k]<nen-16:
            if s0 is None: s0=k
        else:
            if s0 is not None and k-s0>=12: lang.append((s0*0.01,k*0.01))
            s0=None
    for i,g in enumerate(goc):
        trong=[(a,b) for a,b in lang if a>=g['s']-0.01 and b<=g['e']+0.01 and b-a>=0.25]
        if trong:
            a,b=max(trong,key=lambda x:x[1]); a0=min(x[0] for x in trong)
            if a-g['s']>=0.12: g['e']=min(g['e'],a); continue          # tieng noi TRUOC khoang lang ('khoan…'): khoang lang la DUOI tu -> cat duoi, giu dau
            g['s']=b                                                    # khoang lang o DAU tu (Tin nhanh 'Tin'): doi dau ra sau khoang lang
            if i and goc[i-1]['e']<a0: goc[i-1]['e']=a0
            continue
        for a,b in lang:
            if a-0.05<=g['s']<b: g['s']=b; break
            if i and goc[i-1]['e']<=b<g['s'] and g['s']-b>0.1: g['s']=b; break
        if g['e']<g['s']: g['e']=g['s']
    for i in range(len(goc)-1):   # 2 tu dinh cung moc -> chia theo so ky tu
        a,b=goc[i],goc[i+1]
        if b['s']-a['s']<0.06 and b['e']-a['s']>0.2:
            k=len(a['w'])/(len(a['w'])+len(b['w'])); m=a['s']+(b['e']-a['s'])*k; a['e']=b['s']=round(m,3)
    for g in goc:   # cat duoi tu o khoang lang >= 120 ms ngay sau tieng noi (e cua 'khoan…' 9,36 chu khong phai 9,76)
        for a,b in lang:
            if g['s']+0.1<=a<g['e']: g['e']=a; break
for i in range(len(goc)-1):
    if goc[i]['e']>goc[i+1]['s']: goc[i]['e']=goc[i+1]['s']
    if goc[i]['e']<=goc[i]['s']: goc[i]['e']=min(goc[i+1]['s'],goc[i]['s']+0.15)
out=[dict(w=g['w'],s=round(g['s'],2),e=round(g['e'],2),doan=g['doan']) for g in goc]
RA=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else T/'dau-vao/moc-chu.json'   # tham so tuy chon: ghi ra file khac (hoi quy so voi moc cu)
json.dump(out,open(RA,'w'),ensure_ascii=False,indent=0)
print(f'{khop}/{len(goc)} tu co moc; ghi {RA}')
for d in kb:
    ds=[g for g in out if g['doan']==d['k']]; print(f"  {d['k']:4s} {ds[0]['s']:5.2f}-{ds[-1]['e']:5.2f}  {' '.join(g['w'] for g in ds)[:70]}")
