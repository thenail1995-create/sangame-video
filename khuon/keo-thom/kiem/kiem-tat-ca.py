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
sys.path.insert(0,str(B.parent.parent/'cong-cu')); import mo_hinh   # A4: Whisper ghim revision
import nghe_so as NS   # goi B: doc so/vung/han/ten theo GIA TRI
import traceback
(B/f'kiem/kiem-{NT}.json').unlink(missing_ok=True); (B/f'kiem/bao-cao-{NT}.md').unlink(missing_ok=True)   # A5: khong de ket qua cu lam bao 'dat' oan
def _crash(t,v,tb):   # A5: crash = ma thoat != 0 + kiem.json ghi ro
    json.dump(dict(nt=NT,video=VID.name,dat=False,crash=''.join(traceback.format_exception(t,v,tb))[-3000:],phep=[dict(ten=a,dat=bool(b),so_do=c,loi=d) for a,b,c,d in KQ]),open(B/f'kiem/kiem-{NT}.json','w'),ensure_ascii=False,indent=1)
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
_V=KEO['vung']; _G=KEO['game']; _cs=lambda s:re.sub(r'\s+',' ',s).strip()
_VH={'US':'MỸ','HK':'HỒNG KÔNG','SG':'SINGAPORE','TH':'THÁI LAN','ID':'INDONESIA'}
_so=f"{int(KEO.get('so_ky',1)):03d}"
_ten=_G['ten'].replace('®','').replace('™','').replace("'",'’')
exp={'bia.issue':f"SỐ {_so} · THÁNG {_nd.month:02d} · {_nd.year}",'bia.sao':f"{_G['giam']}%",'bia.chip':f"PS STORE · {_VH[_V[0]['ma']]}",
     'the.goc':_d(KEO['goc_vnd']),'the.con':_k(int(round(KEO['con_vnd']/1000)))+'.000đ','the.tk':_d(KEO['goc_vnd']-KEO['con_vnd']),'the.vung':f"CÒN LẠI · STORE {_VH[_V[0]['ma']]}",
     'thu.tem':[_VH[x['ma']] for x in _V[:3]],'bang.g':[_d(x['vnd']) for x in _V[:3]],'bang.n':[_VH[x['ma']] for x in _V[:3]],
     'bang.pill':['✓ RẺ NHẤT','+'+_d(_V[1]['vnd']-_V[0]['vnd']),'+'+_d(_V[2]['vnd']-_V[0]['vnd'])],'bang.tit':f"Giá ngày {_dl.day:02d}/{_dl.month:02d} · đổi ra đồng",
     'phieu.so':f"{_h.hour:02d}{_h.minute:02d}",'phieu.ngay':f"ngày {_h.day:02d}/{_h.month:02d} · giờ Việt Nam"}
nd=d.get('noiDung',{}); sai=[]
for k,v in exp.items():
    got=nd.get(k)
    if isinstance(v,list): okk=[ _cs(x) for x in (got or [])]==[_cs(x) for x in v]
    else: okk=_cs(got or '')==_cs(v)
    if not okk: sai.append(f"{k}: hinh «{got}» ≠ keo.json «{v}»")
_tg=_cs(nd.get('bia.title',''))
if _G['ten'] and not all(w.lower() in _tg.lower() for w in re.findall(r"[\wÀ-ỹ-]+",_ten.replace('’',''))[-2:] ): sai.append(f"bia.title: hinh «{_tg}» khong chua ten «{_ten}»")
_cat=d.get('catChu',[])
ghi('B6 ngay dang (keo.json) = NGAY dang cua luot chay',_ok_ng,_so_ng,'B6')
ghi('Chu (ten game, gia, vung, gio) khong tran / bi cat o moi moc dung yen (ten dai tu thu co)',not _cat,f"{len(_cat)} cho cat/tran"+(f": {_cat[:3]}" if _cat else ''),'H32')
ghi('Ten game / giam % / gia / 3 vung / chenh lech / gio het giam tren hinh khop keo.json (D1)',not sai,f"{len(exp)+1} muc doi chieu, {len(sai)} lech"+(f": {sai[:3]}" if sai else ''),'D1')
# D2: giay het giam (dung vung) con it nhat den 20:00 ngay dang + 1 ngay (mau hoi quy v8.3: deal da het han tu truoc — bo qua, ghi ro)
_can=NS.han_toi_thieu(_nd,os.environ.get('GIO_DANG') or NS.GIO_DANG_MAC_DINH['keo-thom'],gio_them=24)   # NGAY dang + gio dang (20:00) + 1 ngay
if HOI_QUY: ghi('Gio het giam >= 20:00 ngay dang + 1 ngay (D2)',True,f"BO QUA — HOI_QUY=1 (mau hoi quy v8.3), het giam {_h:%d/%m %H:%M} (khong dang)",'D2')
else: ghi('Gio het giam >= 20:00 ngay dang + 1 ngay (D2)',_h>=_can,f"het giam {_h:%d/%m %H:%M} VN (vung {KEO['han'].get('ma')}), can >= {_can:%d/%m %H:%M}",'D2')

# 2b) do tren LOP CHU that (anh alpha) o luc dung yen cua tung canh (v8.3, N11/N12):
#   khoi dau trang nam NGAY DUOI vung app: 0..tren khong co giay; tren+20..tren+100 kin giay. Do che vung trailer net de theo doi (N10).
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
for k in ["ronde","sao","tk","tw1","tw2","tw3","buuC","khong","d1","d2","d3","logoW"]+[f"chip{i}" for i in range(6)]:
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
bien=sorted((r(g[int(w['s']*48000):int(w['e']*48000)])-r(bus[int(w['s']*48000):int(w['e']*48000)]),w['w'],w['s']) for w in moc)
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
cau=[];cur=[]
for k,w in enumerate(moc):
    cur.append(w)
    if re.search(r'[.!?…]$',w['w']) and (k+1==len(moc) or moc[k+1]['s']-w['e']>=0.3): cau.append(cur); cur=[]
if cur: cau.append(cur)
G16=doc(V/'giong.mp3',16000); X16=doc(VID,16000)
tong_g=tong_v=0; xau=[]; tong_chu=0; TVS=[]
for c in cau:
    a=max(0,int((c[0]['s']-0.15)*16000)); b=int((c[-1]['e']+0.2)*16000)
    kb=' '.join(w['w'] for w in c); tg=nghe(G16[a:b]); tv=nghe(X16[a:b]); n=len(chu(kb)); TVS.append((c[0]['s'],c[-1]['e'],tv))
    rg=difflib.SequenceMatcher(None,chu(kb),chu(tg)).ratio(); rv=difflib.SequenceMatcher(None,chu(kb),chu(tv)).ratio()
    tong_g+=rg*n; tong_v+=rv*n; tong_chu+=n
    # cau bi coi la KEM chi khi: khop kich ban sut > 0.10 VA ban ghep khac ban chep giong goc (bo dau thanh, chuan hoa so "784 nghin"="784.000")
    # bo qua cau ngan < 1 s (Whisper doan bua ca 2 ban)
    if rv<rg-0.10 and (b-a)/16000>=1.0 and difflib.SequenceMatcher(None,chuan(tg),chuan(tv)).ratio()<0.80:
        xau.append(f"«{kb[:40]}» goc {rg:.2f} → ghep {rv:.2f} (goc: {tg[:40]} | ghep: {tv[:40]})")
rg,rv=tong_g/tong_chu,tong_v/tong_chu
ghi('Whisper tung cau: ban ghep nghe khong kem giong goc',rv>=rg-0.05 and not xau,f"{len(cau)} cau; khop kich ban: giong goc {rg:.2f}, ban ghep {rv:.2f}"+(f"; cau kem: {xau}" if xau else ''),'A2')

# 5b) Whisper nghe TEN GAME trong ban ghep (D3: ten doc dung — vd 'Spider-Man 2', khong thanh 'Spider Men'): >= 60% tu cua ten (>= 3 chu) co mat trong cau chua ten
KBJ=json.load(open(B/'kich-ban.json'))['doan'][0]; _mo=[w for w in moc if w['doan']=='mo']; _i0=KBJ['neo']['ten']; _i1=next(i for i,w in enumerate(_mo) if w['w'].lower()=='đang')
_tok=[chuan(w['w']) for w in _mo[_i0:_i1]]; _tok=[t for t in _tok if len(t)>=3 or t.isdigit()]
_t0=_mo[_i0]['s']; _cau=next((tv for s,e,tv in TVS if s-0.05<=_t0<=e+0.05),'')
_tt=chuan(_cau); _co=[t for t in _tok if t in _tt]
ghi('Whisper nghe dung ten game trong ban ghep (D3)',len(_co)>=max(1,int(0.6*len(_tok)+0.5)),f"ten «{' '.join(w['w'] for w in _mo[_i0:_i1])}»: nghe duoc {len(_co)}/{len(_tok)} tu; «{_cau[:60]}»",'D3')

# 5d) D3 (B2) — nghe AM THANH MP4 CUOI tung doan, so GIA TRI theo VAI TRO: mo (ten, % giam, vung A) · gia (goc ROI con) · hoi (vung B, C) · dap (cap vung -> chenh lech) · han (gio + buoi + ngay).
#     Ky vong tinh lai tu keo.json (cung luat lam tron voi loi_chu.py). % / vung chi doi o doan ma LOI co doc. 3 ban chung luong tieng -> chung 1 lan Whisper (cache theo bam PCM).
from loi_chu import ten_noi
KBD={x['k']:x['loi'] for x in json.load(open(B/'kich-ban.json'))['doan']}
cs={}
for k in ('mo','gia','hoi','dap','han'):
    ws=[w for w in moc if w.get('doan')==k]
    if ws: cs[k]=(max(0,int((ws[0]['s']-0.15)*16000)),int((ws[-1]['e']+0.25)*16000))
heard,NGHE_BC=NS.nghe_doan(X16,cs,nghe,B/'kiem',rev=os.environ.get('WHISPER_REV') or mo_hinh.REV_GHIM)
_ma=[x['ma'] for x in _V[:3]]; _round=lambda v,q:max(1,int(v/q+0.5))*q
_ky={'mo':dict(ten=[ten_noi(_G['ten'])],phan_tram=[_G['giam']],vung=[_ma[0]]),
     'gia':dict(tien=[_round(KEO['goc_vnd'],100000),_round(KEO['con_vnd'],1000)],tien_thu_tu=[_round(KEO['goc_vnd'],100000),_round(KEO['con_vnd'],1000)]),
     'hoi':dict(vung=[_ma[1],_ma[2]]),
     'dap':dict(tien_tat=[_round(_V[1]['vnd']-_V[0]['vnd'],10000),_round(_V[2]['vnd']-_V[0]['vnd'],10000)],vung=_ma,cap=[(_ma[1],_round(_V[1]['vnd']-_V[0]['vnd'],10000)),(_ma[2],_round(_V[2]['vnd']-_V[0]['vnd'],10000))],chu_the=_ma[0],tien=[_round(_V[1]['vnd']-_V[0]['vnd'],10000),_round(_V[2]['vnd']-_V[0]['vnd'],10000)]),
     'han':dict(han=NS.han_ky_vong(_h,_nd))}
_sai=[]
for k,ky in _ky.items():
    if k not in heard: _sai.append(f'doan {k}: khong co chu trong moc-chu'); continue
    # Sol vong 2b #11: % / vung BAT BUOC theo LUAT khuon (nghe_so.KEO_*, = kich-ban.py) — KHONG con bo phep khi `loi` thieu cau; test_kiem_tat_ca.py doi chieu luat voi kich-ban.py that
    if k not in NS.KEO_PHAN_TRAM: ky.pop('phan_tram',None)
    if k not in NS.KEO_VUNG: ky.pop('vung',None); ky.pop('cap',None)
    _sai+=[f'{k} {x}' for x in NS.doi_chieu(heard[k],**ky)]
ghi('D3 am thanh MP4 cuoi: ten + % + vung + goc roi con + cap vung-chenh + han khop keo.json (theo vai tro)',not _sai,f"{len(cs)} doan; pcm {NGHE_BC['pcm_sha256'][:12]} (nghe moi {NGHE_BC['nghe_moi']}, dung lai {NGHE_BC['dung_lai']})"+(f"; SAI: {_sai}" if _sai else ''),'D3')

# 5c) NEN trailer khong co anh giu cho / man phang: OCR + mang mau phang tren khung nen (khong co chu cua khuon) o 6 moc dung yen
sys.path.insert(0,str(B))
import media_xau
_xau=media_xau.kiem_video_o(B/f'nen-{NT}.mp4',TA['moc'])
ghi('Nen khong co anh giu cho (PLACEHOLDER/SCREENSHOT/COMING SOON/TBA) hoac man mau phang (OCR + do phang)',not _xau,f"{len(TA['moc'])} khung nen"+(f": {_xau}" if _xau else ' sach'),'D12')

dat=sum(1 for x in KQ if x[1]); tong=len(KQ)
with open(B/f'kiem/bao-cao-{NT}.md','w',encoding='utf-8') as f:
    f.write(f"# Bao cao kiem — {VID.name} ({NTS[NT]['ten']}) — {datetime.datetime.now():%d/%m/%Y %H:%M}\n\n**{dat}/{tong} DAT**\n\n| Phep kiem | Ket qua | So do | Loi da tung gap |\n|---|---|---|---|\n")
    for t,ok,so,ma in KQ: f.write(f"| {t} | {'DAT' if ok else '**LOI**'} | {so.replace('|','/')} | {ma} |\n")
json.dump(dict(nt=NT,video=VID.name,dat=(dat==tong),so_dat=dat,tong=tong,nghe_d3=NGHE_BC,luc=datetime.datetime.now().isoformat(timespec='seconds'),phien_ban=mo_hinh.in_phien_ban(),
     phep=[dict(ten=a,dat=bool(b),so_do=c,loi=d) for a,b,c,d in KQ]),open(B/f'kiem/kiem-{NT}.json','w'),ensure_ascii=False,indent=1)
print(f"\n{dat}/{tong} DAT -> {B/f'kiem/bao-cao-{NT}.md'}")
sys.exit(0 if dat==tong else 1)
