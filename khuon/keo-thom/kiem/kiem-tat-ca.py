# Kiem TOAN BO mot video dung tu khuon tap chi v9 (Keo thom, du lieu theo ngay) — chay sau moi lan dung (moi ngay).
#   uv run --with numpy --with faster-whisper --with pillow python kiem/kiem-tat-ca.py video-<nen_tang>.mp4 [nen_tang]
# Ra: kiem/bao-cao-<nen_tang>.md (bang DAT/LOI) + ma thoat 1 neu co LOI. Moi phep kiem gan voi mot loi THAT da gap (xem ../LOI-SAI.md).
import json,re,subprocess,sys,pathlib,wave,difflib,datetime
import numpy as np
B=pathlib.Path(__file__).resolve().parent.parent; V=B/'dau-vao'
sys.path.insert(0,str(B))   # PHAI truoc moi import noi bo (loi_chu, media_xau...): CI that 11/10 sap ModuleNotFoundError vi import truoc khi them B
VID=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else B/'video-tiktok.mp4'
NTS=json.load(open(B/'nen-tang.json'))
NT=sys.argv[2] if len(sys.argv)>2 else next((k for k in NTS if VID.stem.endswith(k)),'tiktok'); TREN,DUOI=NTS[NT]['tren'],NTS[NT]['duoi']
print('nen tang:',NT,TREN,DUOI)
import os
SK=pathlib.Path(os.environ.get('MG_SCRIPTS') or pathlib.Path.home()/'.claude/skills/motion-graphics/scripts')   # A3: khong ghi cung duong dan Mac
SOM=os.environ.get('KIEM_SOM')=='1'   # KIEM SOM (GD=chung cua CI): chi cac phep KHONG can hinh da ve; ghi kiem/kiem-som-<nt>.json, KHONG ghi kiem-<nt>.json (manifest chi tin bao cao cuoi)
TT=('som-' if SOM else '')+NT
LK_KQ=None
sys.path.insert(0,str(B.parent.parent/'cong-cu')); import mo_hinh   # A4: Whisper ghim revision
import nghe_so as NS   # goi B: doc so/vung/han/ten theo GIA TRI
import lien_ket_giong as LK   # D3 doi thiet ke 11/10: noi dung nghe tren GIONG SACH + phep 'giong trong video = giong da kiem'
import traceback
(B/f'kiem/kiem-{TT}.json').unlink(missing_ok=True); (B/f'kiem/bao-cao-{TT}.md').unlink(missing_ok=True)   # A5: khong de ket qua cu lam bao 'dat' oan
def _crash(t,v,tb):   # A5: crash = ma thoat != 0 + kiem.json ghi ro
    json.dump(dict(nt=NT,video=VID.name,dat=False,crash=''.join(traceback.format_exception(t,v,tb))[-3000:],phep=[dict(ten=a,dat=bool(b),so_do=c,loi=d) for a,b,c,d in KQ]),open(B/f'kiem/kiem-{TT}.json','w'),ensure_ascii=False,indent=1)
    sys.__excepthook__(t,v,tb)
sys.excepthook=_crash
KQ=[]   # (ten, dat?, so do, loi nao trong LOI-SAI)
# v9: moc thoi gian + du lieu hien thi lay tu neo.json (do-khung.cjs ghi) va keo.json — khong con 25.12 / 3.7 / 8.4... ghi cung
def _cu(p,*deps): return (not p.exists()) or any(p.stat().st_mtime<d.stat().st_mtime for d in deps if d.exists())
if _cu(B/'neo.json',B/'full.html',V/'moc-chu.json',B/'keo.json'):
    subprocess.run([sys.executable,str(B/'dung.py'),'build','tiktok'],check=True); subprocess.run(['node',str(B/'do-khung.cjs'),'tiktok'],check=True)
NEO=json.load(open(B/'neo.json')); TA=NEO['TA']; DAI=TA['DAI']; KEO=json.load(open(B/'keo.json',encoding='utf-8'))
def ghi(ten,ok,so,ma): KQ.append((ten,ok,so,ma)); print(('DAT ' if ok else 'LOI ')+ten+' — '+so)

# 0) chu thich // NUOT LENH JS tren cung dong (H25 Top 5, H28 khuon v8.1, H30 Tin nhanh — 3 lan -> kiem may bat buoc)
_MAU=re.compile(r"(?<![:\w])//(?P<c>.*)$"); _LENH=re.compile(r"\b[a-zA-Z_$][\w$]*(\.[\w$]+)+\s*=[^=]|\b(tf|op|show|\$)\(\$?\(?['\"]|\bvar\s+\w+\s*=")
def _nuot(text):
    out=[]
    for i,l in enumerate(text.split('\n'),1):
        m=_MAU.search(l)
        if m and l[:m.start()].strip() and 'http' not in l[max(0,m.start()-6):m.start()] and _LENH.search(m.group('c')): out.append(f"dong {i}: {l.strip()[:70]}")
    return out
_n=_nuot((B/'full.html').read_text(encoding='utf-8'))
ghi('Khong co chu thich // nuot lenh trong full.html',not _n,f"{len(_n)} dong"+(f": {_n[:2]}" if _n else ''),'H25/H28/H30')

# 1) ky thuat file (codec, mau BT.709, faststart, do to, khung den, dung hinh)
if not SOM:   # can video da dung - KIEM SOM bo qua (bo kiem cuoi van chay)
    rv=subprocess.run([sys.executable,str(SK/'kiem-video.py'),str(VID)],capture_output=True,text=True); o=rv.stdout   # ma thoat != 0 => TRUOT (vong 2 #6)
    m=re.search(r'tong: (\d+) FAIL, (\d+) WARN',o); lu=re.search(r'loudness I = ([-\d.]+)',o); tp=re.search(r'true peak = ([-\d.]+)',o)
    sar=subprocess.run(['ffprobe','-v','error','-select_streams','v','-show_entries','stream=width,height,sample_aspect_ratio','-of','csv=p=0',str(VID)],capture_output=True,text=True).stdout.strip()
    ghi('Khung 1080x1920, diem anh vuong (SAR 1:1)',sar in ('1080,1920,1:1','1080,1920,N/A'),sar,'K11')
    ghi('Ky thuat file (kiem-video.py)',bool(m) and m.group(1)=='0' and rv.returncode==0,f"ma thoat {rv.returncode}; {m.group(1) if m else '?'} FAIL, {m.group(2) if m else '?'} WARN; {lu.group(1) if lu else '?'} LUFS; dinh {tp.group(1) if tp else '?'} dBTP",'K1')

# 2) trang that: phu de tran + vung an toan
subprocess.run([sys.executable,str(B/'dung.py'),'build',NT],check=True)
d=json.loads(subprocess.run(['node',str(B/'kiem/kiem-dom.cjs'),NT,','.join(str(x) for x in TA['mocDom'])],capture_output=True,text=True,check=True).stdout)
ghi('Khong trung ma phan tu (id)',not d.get('trungId'),f"{len(d.get('trungId',[]))} id trung"+(f": {d['trungId'][:5]}" if d.get('trungId') else ''),'H31')
ghi('Phu de khong tran khung (moi khung)',not d['tranPhuDe'],f"{len(d['tranPhuDe'])} khung tran"+(f": {d['tranPhuDe'][:3]}" if d['tranPhuDe'] else ''),'H5')
nv=sum(len(v) for v in d['ngoaiVung'].values())
ghi(f'Chu/gia/logo trong vung an toan {NTS[NT]["ten"]} 120-888 x {TREN}-{DUOI}',nv==0,f"{nv} phan tu ngoai vung"+(f": {d['ngoaiVung']}" if nv else ''),'H6')

# 2a) NOI DUNG TREN HINH khop keo.json (D1: ten, giam %, gia goc/con/tiet kiem, 3 vung + chenh lech, so ky, gio het giam) — dinh dang tinh LAI doc lap tu keo.json tho
import datetime
VN=datetime.timezone(datetime.timedelta(hours=7))
def _k(g): return (f"{g//1000}.{g%1000:03d}" if g>=1000 else str(g))
def _d(vnd): return _k(int(round(vnd/1000)))+'.000đ'
HOI_QUY=os.environ.get('HOI_QUY')=='1'   # B6: ngoai le DUY NHAT
_ok_ng,_so_ng,_nd=NS.kiem_ngay(KEO.get('ngay_dang') or '',os.environ.get('NGAY',''),HOI_QUY)
_nd=_nd or datetime.date.fromisoformat(KEO['ngay_dang'])
_h=datetime.datetime.fromtimestamp(int(KEO['han']['endTime'])/1000,VN); _dl=datetime.date.fromisoformat(KEO.get('ngay_du_lieu') or KEO['ngay_dang'])
_V=KEO['vung']; _G=KEO['game']; _cs=lambda s:re.sub(r'\s+',' ',str(s or '')).strip()   # None (diem / ban / the loai thieu hop le) -> '' (Sol P1: D1 sap TypeError)
_VH={'US':'MỸ','HK':'HỒNG KÔNG','SG':'SINGAPORE','TH':'THÁI LAN','ID':'INDONESIA'}
_so=f"{int(KEO.get('so_ky',1)):03d}"
_ten=_G['ten'].replace('®','').replace('™','').replace("'",'’')
exp={'bia.issue':f"SỐ {_so} · THÁNG {_nd.month:02d} · {_nd.year}",'bia.sao':f"{_G['giam']}%",'bia.chip':(('PS STORE · ' if len(_VH[_V[0]['ma']])<=2 else '')+_VH[_V[0]['ma']]),   # 12/10: khop full.html chip1 (ten vung dai bo tien to, #56)
     
     'the.goc':_d(KEO['goc_vnd']),'the.con':_k(int(round(KEO['con_vnd']/1000)))+'.000đ','the.tk':_d(KEO['goc_vnd']-KEO['con_vnd']),'the.vung':f"CÒN LẠI · STORE {_VH[_V[0]['ma']]}",
     'bang.g':[_d(x['vnd']) for x in _V[:3]],'bang.n':[_VH[x['ma']] for x in _V[:3]],
     'bang.pill':['✓ RẺ NHẤT','+'+_d(_V[1]['vnd']-_V[0]['vnd']),'+'+_d(_V[2]['vnd']-_V[0]['vnd'])],'bang.tit':f"Giá ngày {_dl.day:02d}/{_dl.month:02d} · đổi ra đồng",
     'phieu.so':f"{_h.hour:02d}{_h.minute:02d}",'phieu.ngay':f"ngày {_h.day:02d}/{_h.month:02d} · giờ Việt Nam"}
# GIOI THIEU game (11/10): tinh LAI tu so lieu tho trong keo.json.gioi_thieu (diem trung binh, so luot) bang loi_chu — khong doc chuoi da dinh dang san
from loi_chu import lam_tron_diem,hien_diem,hien_luot,the_biet_truoc
_GT=KEO.get('gioi_thieu') or {}; _gb=_GT.get('ban'); _gd=_GT.get('diem')
exp.update({'gioi.the_loai':' · '.join(x['vi'].upper() for x in _GT.get('the_loai',[])) or None,'gioi.chip':[x['hien'] for x in _GT.get('dac_diem',[])[:2]],
            'gioi.diem':(hien_diem(lam_tron_diem(_gd['tb']))+'/5') if _gd else None,'gioi.luot':(hien_luot(_gd['so_luot'])+' lượt chấm') if _gd else None,
            'gioi.ban':('BẢN '+_gb['ten_noi']+' CÓ THÊM').upper() if _gb else None,'gioi.them':[m['hien'] for m in (_gb or {}).get('them',[])[:4]],
            'gioi.the_bt':the_biet_truoc(KEO.get('biet_truoc'),next((x.get('bt') for x in json.load(open(B/'kich-ban.json'))['doan'] if x.get('k')=='gioi'),None))})   # G3: the biet truoc = dung cac cau da doc
nd=d.get('noiDung',{}); sai=[]
for k,v in exp.items():
    got=nd.get(k)
    if isinstance(v,list): okk=[ _cs(x) for x in (got or [])]==[_cs(x) for x in v]
    else: okk=_cs(got or '')==_cs(v)
    if not okk: sai.append(f"{k}: hinh «{got}» ≠ keo.json «{v}»")
_tg=_cs(nd.get('bia.title',''))
if _G['ten'] and not all(w.lower() in _tg.lower() for w in re.findall(r"[\wÀ-ỹ-]+",_ten.replace('’',''))[-2:] ): sai.append(f"bia.title: hinh «{_tg}» khong chua ten «{_ten}»")
_cat=d.get('catChu',[])
_chong=d.get('chongGT',[])
ghi('The biet truoc khong che / de len hang khac cua ho so game (ten the loai, chip, sao, ban, phan them) o moi moc (G3)',not _chong,f"{len(_chong)} cho de"+(f": {_chong[:3]}" if _chong else ''),'G3/Sol#14')
ghi('B6 ngay dang (keo.json) = NGAY dang cua luot chay',_ok_ng,_so_ng,'B6')
ghi('Chu (ten game, gia, vung, gio) khong tran / bi cat o moi moc dung yen (ten dai tu thu co)',not _cat,f"{len(_cat)} cho cat/tran"+(f": {_cat[:3]}" if _cat else ''),'H32')
ghi('Ten game / giam % / gia / 3 vung / chenh lech / gio het giam tren hinh khop keo.json (D1)',not sai,f"{len(exp)+1} muc doi chieu, {len(sai)} lech"+(f": {sai[:3]}" if sai else ''),'D1')
# D2: giay het giam (dung vung) con it nhat den GIO DANG CUA KHUNG ngay dang + 1 ngay (mau hoi quy v8.3: deal da het han tu truoc — bo qua, ghi ro)
#   12/10: 3 khung Keo (15:00 / 20:00 / 22:00): gio lay env GIO_DANG, thieu thi theo bang GIO_DANG_MAC_DINH cua DANG (mac dinh khung goc keo-thom 20:00)
_gio_d=os.environ.get('GIO_DANG') or NS.GIO_DANG_MAC_DINH.get(os.environ.get('DANG') or 'keo-thom',NS.GIO_DANG_MAC_DINH['keo-thom'])
_can=NS.han_toi_thieu(_nd,_gio_d,gio_them=24)   # NGAY dang + gio dang cua khung + 1 ngay
if HOI_QUY: ghi(f'Gio het giam >= {_gio_d} ngay dang + 1 ngay (D2)',True,f"BO QUA — HOI_QUY=1 (mau hoi quy v8.3), het giam {_h:%d/%m %H:%M} (khong dang)",'D2')
else: ghi(f'Gio het giam >= {_gio_d} ngay dang + 1 ngay (D2)',_h>=_can,f"het giam {_h:%d/%m %H:%M} VN (vung {KEO['han'].get('ma')}), can >= {_can:%d/%m %H:%M}",'D2')

# 2b) do tren LOP CHU that (anh alpha) o luc dung yen cua tung canh (v8.3, N11/N12):
#   khoi dau trang nam NGAY DUOI vung app: 0..tren khong co giay; tren+20..tren+100 kin giay. Do che vung trailer net de theo doi (N10).
if not SOM:   # can video da dung - KIEM SOM bo qua (bo kiem cuoi van chay)
    from PIL import Image
    MOC_H=TA['moc']   # 6 moc dung yen cua 6 canh (= 3.7 8.4 12.2 17.8 20.8 24.8 o mau Spider-Man 2)
    CAP=str(SK/'capture.mjs'); (B/'soi').mkdir(exist_ok=True)
    subprocess.run(['node',CAP,str(B/f'full-{NT}.build.html'),str(B/'soi'/f'kiem-{NT}'),'30',str(DAI),'1080','1920','--alpha',
                    '--stills='+','.join(f'{t:.2f}' for t in MOC_H),'--quiet'],check=True)
    tren_ho=[];giay=[];che=[]
    for t in MOC_H:
        a=np.asarray(Image.open(B/'soi'/f'kiem-{NT}_{t:.2f}s.png').convert('RGBA'))[:,:,3]>=217   # alpha >= 0.85 = kin
        tren_ho.append(a[:TREN].mean()); giay.append(a[TREN+20:TREN+100].mean()); che.append(a[TREN+158:1500].mean())
    ghi(f'Khoi dau trang ngay duoi vung giao dien ({TREN} px)',max(tren_ho)<=0.01 and min(giay)>=0.95,f"giay trong vung app {max(tren_ho)*100:.1f}%; kin giay y {TREN+20}-{TREN+100}: {min(giay)*100:.0f}%",'N11/N12')
    ghi('Do che vung trailer net (theo doi, chua dat nguong cho Keo thom)',True,'che '+', '.join(f'{t}s {x*100:.0f}%' for t,x in zip(MOC_H,che)),'N10')

# 3) tieng khop khung cham (khung.json do tren trang that; sfx-bus.npy do am08.py ghi)
if (not (B/'khung.json').exists()) or (B/'khung.json').stat().st_mtime<(B/'full.html').stat().st_mtime:
    subprocess.run([sys.executable,str(B/'dung.py'),'build','tiktok'],check=True); subprocess.run(['node',str(B/'do-khung.cjs'),'tiktok'],check=True)
K=json.load(open(B/'khung.json')); F=len(K)
bus=np.load(B/'sfx-bus.npy').mean(axis=0); hop=96; n=len(bus)//hop
db=20*np.log10(np.sqrt(np.mean(bus[:n*hop].reshape(n,hop)**2,axis=1))+1e-9)
def onset(v,lo=0.025,hi=0.04):
    a=max(5,int((v-lo)/0.002)); b=min(n-1,int((v+hi)/0.002)); r=db[a:b]-db[a-5:b-5]; return (a+int(np.argmax(r))-3)*0.002
def sc(x):
    if isinstance(x,str):
        mm=re.search(r"scale\(([\d.]+)\)",x); return float(mm.group(1)) if mm else 0
    return x or 0
ev=[]
for k in ["ronde","sao","tk","gtG","gtScore","gtB","gtI1","gtI2","gtI3","gtI4","d1","d2","d3","logoW"]+[f"chip{i}" for i in range(6)]:
    for f in range(1,F):
        x=sc(K[f][k])
        if x and x<=1.03: ev.append((f/30,k)); break
for f in range(1,F):
    if K[f]["url"]>K[f-1]["url"]: ev.append((f/30,'go chu'))
    for i in range(3):
        if K[f]["b"][i]>0 and K[f-1]["b"][i]==0: ev.append((f/30,f'thanh {i+1}'))
lech=[(round((onset(v)-v)*1000),t,round(v,2)) for v,t in ev]
xau=[x for x in lech if abs(x[0])>34]
ghi('Tieng dap khop khung cham (<= 1 khung = 34 ms)',not xau,f"{len(lech)} cu; lech {min(x[0] for x in lech)}..{max(x[0] for x in lech)} ms"+(f"; qua 1 khung: {xau}" if xau else ''),'A1')

# 4) giong khong bi tieng dong che (tung chu)
def doc(f,sr=48000): return np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',str(f),'-ac','1','-ar',str(sr),'-f','f32le','-'],capture_output=True,check=True).stdout,dtype=np.float32)
g=doc(V/'giong.mp3'); g=np.pad(g,(0,max(0,len(bus)-len(g))))[:len(bus)]
moc=[w for w in json.load(open(V/'moc-chu.json')) if w['w'].strip()]
r=lambda x:20*np.log10(np.sqrt(np.mean(x**2))+1e-9)
# 13/10 (Top 5 run 38340819324): moc can chu doi khi bat dau trong quang lang truoc tieng noi ('Hạng' -46 dB, giong goc -84 dB o moc)
# -> chi do tren khung 10 ms CO GIONG (giong >= -45 dBFS); chu khong co khung nao co giong thi bo qua (khong co giong de bi che).
def _bien(w):
    a,b=int(w['s']*48000),int(w['e']*48000); k=480; n_=(b-a)//k
    if n_<1: return None
    gg=g[a:a+n_*k].reshape(n_,k); bb=bus[a:a+n_*k].reshape(n_,k)
    co=20*np.log10(np.sqrt(np.mean(gg**2,axis=1))+1e-9)>=-45
    if not co.any(): return None
    return r(gg[co].ravel())-r(bb[co].ravel())
bien=sorted((x,w['w'],w['s']) for w in moc if (x:=_bien(w)) is not None)
duoi6=[(round(a,1),b,c) for a,b,c in bien if a<6]
ghi('Giong to hon tieng dong >= 6 dB (>= 95% chu)',len(duoi6)<=max(1,len(bien)//20),f"duoi 6 dB: {len(duoi6)}/{len(bien)} {duoi6[:4]}",'A3')

# 5) Whisper: nghe TUNG CAU (cat theo moc chu) tren giong goc va ban ghep, so voi kich ban.
# Nghe ca bai mot luot khong on dinh (co luc bo cau cuoi — LOI-SAI A4; "Ê anh em"/"Em em" dao dong), nen cat cau + temperature 0.
wm=mo_hinh.nap_whisper()
chu=lambda s:re.findall(r'\w+',s.lower().replace('-',''))
import unicodedata
def chuan(t):
    t=re.sub(r'(\d+)\s*nghìn',r'\g<1>000',t.lower()); t=re.sub(r'(?<=\d)[.,](?=\d)','',t)
    t=''.join(c for c in unicodedata.normalize('NFD',t) if unicodedata.category(c)!='Mn').replace('đ','d')
    return re.sub(r'[^a-z0-9]','',t)
def nghe(x16):
    seg,_=wm.transcribe(x16,language='vi',beam_size=5,temperature=0.0,condition_on_previous_text=False,vad_filter=False)
    return ' '.join(x.text.strip() for x in seg)
_WT=[]
def wt():
    """Mo hinh NGHE KIEM D3 noi dung (large-v3-turbo, ghim revision) — nap lan dau khi can (cache nghe_doan trung thi khong nap)."""
    if not _WT: _WT.append(mo_hinh.nap_whisper_nghe_kiem())
    return _WT[0]
def nghe_kiem(x16):
    seg,_=wt().transcribe(x16,language='vi',beam_size=5,temperature=0.0,condition_on_previous_text=False,vad_filter=False)
    return ' '.join(x.text.strip() for x in seg)
cau=[];cur=[]
for k,w in enumerate(moc):
    cur.append(w)
    if re.search(r'[.!?…]$',w['w']) and (k+1==len(moc) or moc[k+1]['s']-w['e']>=0.3): cau.append(cur); cur=[]
if cur: cau.append(cur)
GS=LK.ten_giong_sach(V); G16=doc(GS,16000); X16=None if SOM else doc(VID,16000)   # GS = tep giong SACH dung de tron video; D3 noi dung nghe tren G16, KHONG nghe tren ban ghep (CI 11/10)
if not SOM:   # can video da dung - KIEM SOM bo qua (bo kiem cuoi van chay)
    tong_g=tong_v=0; xau=[]; tong_chu=0; TVS=[]
    for c in cau:
        a=max(0,int((c[0]['s']-0.15)*16000)); b=int((c[-1]['e']+0.2)*16000)
        kb=' '.join(w['w'] for w in c); tg=nghe(G16[a:b]); tv=nghe(X16[a:b]); n=len(chu(kb)); TVS.append((c[0]['s'],c[-1]['e'],tg))
        rg=difflib.SequenceMatcher(None,chu(kb),chu(tg)).ratio(); rv=difflib.SequenceMatcher(None,chu(kb),chu(tv)).ratio()
        tong_g+=rg*n; tong_v+=rv*n; tong_chu+=n
        # cau bi coi la KEM chi khi: khop kich ban sut > 0.10 VA ban ghep khac ban chep giong goc (bo dau thanh, chuan hoa so "784 nghin"="784.000")
        # bo qua cau ngan < 1 s (Whisper doan bua ca 2 ban)
        if rv<rg-0.10 and (b-a)/16000>=1.0 and difflib.SequenceMatcher(None,chuan(tg),chuan(tv)).ratio()<0.80:
            xau.append(f"«{kb[:40]}» goc {rg:.2f} → ghep {rv:.2f} (goc: {tg[:40]} | ghep: {tv[:40]})")
    rg,rv=tong_g/tong_chu,tong_v/tong_chu
    ghi('Whisper tung cau: ban ghep nghe khong kem giong goc',rv>=rg-0.05 and not xau,f"{len(cau)} cau; khop kich ban: giong goc {rg:.2f}, ban ghep {rv:.2f}"+(f"; cau kem: {xau}" if xau else ''),'A2')


# (Keo v10: mo con doc SAO cua cau mo tinh huong; gioi con doc CAU KET LUAN)
# 5d) D3 (B2) — nghe GIONG SACH (G16, khong phai ban ghep: CI 11/10 Whisper nghe nhac+tieng dong thanh «ANM RETURNAL DIGITAL DELUX…») tung doan, so GIA TRI theo VAI TRO: mo (ten, % giam, vung A) · gia (goc ROI con) · gioi (DIEM SAO dung gia tri + tu khoa the loai/dac diem/phan them) · dap (cap vung -> chenh lech) · han (gio + buoi + ngay).
#     Ky vong tinh lai tu keo.json (cung luat lam tron voi loi_chu.py). % / vung chi doi o doan ma LOI co doc. 3 ban chung luong tieng -> chung 1 lan Whisper (cache theo bam PCM).
from loi_chu import ten_noi,lam_tron_diem,ket_luan,KET_LUAN_ALL,biet_truoc_ky_vong
_GT=KEO.get('gioi_thieu') or {}; _gd=_GT.get('diem')    # (D3 tu chua du: tinh lai o day de khoi nay chay doc lap trong test)
KBD={x['k']:x['loi'] for x in json.load(open(B/'kich-ban.json'))['doan']}
cs={}
for k in ('mo','gia','gioi','dap','han'):
    ws=[w for w in moc if w.get('doan')==k]
    if ws: cs[k]=(max(0,int((ws[0]['s']-0.15)*16000)),int((ws[-1]['e']+0.25)*16000))
heard,NGHE_BC=NS.nghe_doan(G16,cs,nghe_kiem,B/'kiem',rev=(os.environ.get('WHISPER_REV') or mo_hinh.REV_GHIM)+'|'+mo_hinh.ten_nghe_kiem())
heard_s,_bc_s=NS.nghe_doan(G16,cs,nghe,B/'kiem',rev=os.environ.get('WHISPER_REV') or mo_hinh.REV_GHIM)   # small: CHI cho TEN game (Opus 11/10)
_ma=[x['ma'] for x in _V[:3]]; _round=lambda v,q:max(1,int(v/q+0.5))*q
# Keo v10 A: cau mo tinh huong — kieu do kich-ban.py ghi (kich-ban.json.doan[mo].kieu); MOI SO trong cau mo (diem sao · % giam; v10 Opus 12/10: cau mo KHONG doc tien nen khong kiem tien) tinh LAI tu keo.json va so theo GIA TRI. Khong co `kieu` (kich-ban cu / cum cam than) -> chi ten + % + vung.
_kieu_mo=next((x.get('kieu') for x in json.load(open(B/'kich-ban.json'))['doan'] if x.get('k')=='mo'),None)
_ky_mo=dict(ten=[ten_noi(_G['ten'])],phan_tram=[_G['giam']],vung=[_ma[0]])
if _kieu_mo in ('so_gia_sao','so_sao') and _gd: _ky_mo['sao']=[lam_tron_diem(_gd['tb'])]
elif _kieu_mo in ('so_gia_sao','so_sao'): _ky_mo['sao']=[-1]    # kieu nhac sao ma keo.json khong co diem -> chac chan sai: ep TRUOT
# G3 (13/10) BIET TRUOC KHI MUA: kich-ban.json.doan[gioi].bt = cac kieu cau da doc ('phu_de' · 'online' · 'so_nguoi'); gia tri ky vong tinh LAI tu keo.json.biet_truoc (khong tin kich-ban.json): cau trai nghia (co/chua phu de VI, can/khong can PS Plus, sai so nguoi) -> TRUOT
_bt_kieu=next((x.get('bt') for x in json.load(open(B/'kich-ban.json'))['doan'] if x.get('k')=='gioi'),None) or []
_KL=ket_luan(_gd)     # Keo v10 B: cau ket luan cuoi doan gioi (tu khoa BAT BUOC; hai cau con lai CAM)
_ky={'mo':_ky_mo,
     'gia':dict(tien=[_round(KEO['goc_vnd'],100000),_round(KEO['con_vnd'],1000)],tien_thu_tu=[_round(KEO['goc_vnd'],100000),_round(KEO['con_vnd'],1000)]),
     'gioi':dict(diem=[lam_tron_diem(_gd['tb'])] if _gd else [],tu_khoa=NS.tu_khoa_gioi(_GT,ket_luan=(_KL,[x for x in KET_LUAN_ALL if x!=_KL])),biet_truoc=biet_truoc_ky_vong(KEO.get('biet_truoc'),_bt_kieu)),
     'dap':dict(tien_tat=[_round(_V[1]['vnd']-_V[0]['vnd'],10000),_round(_V[2]['vnd']-_V[0]['vnd'],10000)],vung=_ma,cap=[(_ma[1],_round(_V[1]['vnd']-_V[0]['vnd'],10000)),(_ma[2],_round(_V[2]['vnd']-_V[0]['vnd'],10000))],chu_the=_ma[0],tien=[_round(_V[1]['vnd']-_V[0]['vnd'],10000),_round(_V[2]['vnd']-_V[0]['vnd'],10000)]),
     'han':dict(han=NS.han_ky_vong(_h,_nd))}
_sai=[]; TEN_BO=None
for k,ky in _ky.items():
    if k not in heard: _sai.append(f'doan {k}: khong co chu trong moc-chu'); continue
    # Sol vong 2b #11: % / vung BAT BUOC theo LUAT khuon (nghe_so.KEO_*, = kich-ban.py) — KHONG con bo phep khi `loi` thieu cau; test_kiem_tat_ca.py doi chieu luat voi kich-ban.py that
    if k not in NS.KEO_PHAN_TRAM: ky.pop('phan_tram',None)
    if k not in NS.KEO_VUNG: ky.pop('vung',None); ky.pop('cap',None)
    _sai+=[f'{k} {x}' for x in NS.doi_chieu(heard[k],kiem_ten=False,**ky)]
    if k=='mo' and _kieu_mo=='giam_sau':    # Keo v10 (Sol P1): cau mo kieu 3 doc phan tram -> MOI lan nghe phan tram trong doan mo phai = giam (75% ma cau mo doc 60% -> TRUOT)
        _pt_sai=sorted({p for p,_ in NS.doc_phan_tram(heard[k]) if p!=_G['giam']})
        if _pt_sai: _sai.append(f"mo PHAN TRAM LAN KHAC: nghe duoc {_pt_sai} ≠ giam {_G['giam']}% («{heard[k][:70]}»)")
    if k=='mo':
        _ok,TEN_BO,_ly=NS.ten_hai_bo(ky['ten'][0],{'turbo':heard[k],'small':heard_s.get(k)})
        if not _ok: _sai.append(f"mo TEN «{ky['ten'][0]}»: {_ly}")
ghi('D3 giong sach: ten + % + vung + goc roi con + diem sao & tu khoa gioi thieu & menh de biet truoc (phu de VI / can PS Plus / so nguoi) + cap vung-chenh + han khop keo.json (theo vai tro)',not _sai,f"{len(cs)} doan; ten dat boi {TEN_BO}; pcm {NGHE_BC['pcm_sha256'][:12]} (nghe moi {NGHE_BC['nghe_moi']}, dung lai {NGHE_BC['dung_lai']})"+(f"; SAI: {_sai}" if _sai else ''),'D3')


# 5c) NEN trailer khong co anh giu cho / man phang: OCR + mang mau phang tren khung nen (khong co chu cua khuon) o 6 moc dung yen
sys.path.insert(0,str(B))
if not SOM:   # can video da dung - KIEM SOM bo qua (bo kiem cuoi van chay)
    import media_xau
    _xau=media_xau.kiem_video_o(B/f'nen-{NT}.mp4',TA['moc'])
    ghi('Nen khong co anh giu cho (PLACEHOLDER/SCREENSHOT/COMING SOON/TBA) hoac man mau phang (OCR + do phang)',not _xau,f"{len(TA['moc'])} khung nen"+(f": {_xau}" if _xau else ' sach'),'D12')

# 5b) Whisper nghe TEN GAME trong GIONG SACH (D3; Opus 11/10): DAT neu small (cau A2, TVS) HOAC turbo (doan 'mo') phu >= 60% tu cua ten (>= 3 chu) VA token phan biet khop tuyet doi trong chinh ban nghe do
if not SOM:   # can video da dung - KIEM SOM bo qua (bo kiem cuoi van chay)
    KBJ=json.load(open(B/'kich-ban.json'))['doan'][0]; _mo=[w for w in moc if w['doan']=='mo']; _i0=KBJ['neo']['ten']; _i1=next(i for i,w in enumerate(_mo) if w['w'].lower()=='đang')
    _tok=[chuan(w['w']) for w in _mo[_i0:_i1]]; _tok=[t for t in _tok if len(t)>=3 or t.isdigit()]
    _t0=_mo[_i0]['s']; _cau=next((tv for s,e,tv in TVS if s-0.05<=_t0<=e+0.05),''); _ten5b=ten_noi(_G['ten'])
    _kq5b={}
    for _bo,_van in (('turbo',heard.get('mo','')),('small',_cau)):
        _tt=chuan(_van); _co=[t for t in _tok if t in _tt]; _pb=NS.so_phan_biet(_ten5b,_van)
        _kq5b[_bo]=(len(_co)>=max(1,int(0.6*len(_tok)+0.5)) and _pb[0],len(_co),_pb[1],_van)
    _bo5b=next((b for b in ('turbo','small') if _kq5b[b][0]),None)
    ghi('Whisper nghe dung ten game trong giong sach (D3)',_bo5b is not None,f"ten «{' '.join(w['w'] for w in _mo[_i0:_i1])}»: dat boi {_bo5b}; "+'; '.join(f"{b}: {v[1]}/{len(_tok)} tu, {v[2]}, «{v[3][:50]}»" for b,v in _kq5b.items()),'D3')
# 5e) D3 (doi thiet ke 11/10, Sol #10) — "giong trong video = giong da kiem": am thanh 16 kHz trich tu MP4 nay phai TUONG QUAN duong bao nang luong (RMS 20 ms, khung co giong, lech +-300 ms) voi
#     GIONG SACH `dau-vao/giong.mp3` (dung tep da kiem noi dung o D3). Giong khac / lan thu khac => truot. Nguong hieu chinh bang so that: xem cong-cu/lien_ket_giong.py.
if not SOM:   # can video da dung - KIEM SOM bo qua (bo kiem cuoi van chay)
    LK_KQ=LK.lien_ket(G16,X16,cua_so=LK.cua_so_moc_chu(moc)); _ok_lk,_so_lk=LK.dat_lien_ket(LK_KQ)
    ghi('D3 giong trong video = giong sach da kiem noi dung (tuong quan duong bao nang luong + phu + cua so moc-chu, lech +-300 ms)',_ok_lk,_so_lk,'D3/Sol#10')

dat=sum(1 for x in KQ if x[1]); tong=len(KQ)
with open(B/f'kiem/bao-cao-{TT}.md','w',encoding='utf-8') as f:
    f.write(f"# Bao cao kiem — {VID.name} ({NTS[NT]['ten']}) — {datetime.datetime.now():%d/%m/%Y %H:%M}\n\n**{dat}/{tong} DAT**\n\n| Phep kiem | Ket qua | So do | Loi da tung gap |\n|---|---|---|---|\n")
    for t,ok,so,ma in KQ: f.write(f"| {t} | {'DAT' if ok else '**LOI**'} | {so.replace('|','/')} | {ma} |\n")
json.dump(dict(nt=NT,video=VID.name,dat=(dat==tong),so_dat=dat,tong=tong,nghe_d3=NGHE_BC,ten_dat_boi=TEN_BO,lien_ket_giong=LK_KQ,giong_sach=GS.name,luc=datetime.datetime.now().isoformat(timespec='seconds'),phien_ban=mo_hinh.in_phien_ban(),
     phep=[dict(ten=a,dat=bool(b),so_do=c,loi=d) for a,b,c,d in KQ]),open(B/f'kiem/kiem-{TT}.json','w'),ensure_ascii=False,indent=1)
print(f"\n{dat}/{tong} DAT -> {B/f'kiem/bao-cao-{TT}.md'}")
sys.exit(0 if dat==tong else 1)
