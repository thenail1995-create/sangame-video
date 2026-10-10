# Kiem TOAN BO mot video dung tu khuon tap chi v8 — chay sau moi lan dung (moi ngay).
#   uv run --with numpy --with faster-whisper --with pillow python kiem/kiem-tat-ca.py video-<nen_tang>.mp4 [nen_tang]
# Ra: kiem/bao-cao-<nen_tang>.md (bang DAT/LOI) + ma thoat 1 neu co LOI. Moi phep kiem gan voi mot loi THAT da gap (xem LOI-SAI.md cua khuon).
import json,re,subprocess,sys,pathlib,wave,difflib,datetime
import numpy as np
B=pathlib.Path(__file__).resolve().parent.parent; V=B/'dau-vao'
VID=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else B/'video-tiktok.mp4'
NTS=json.load(open(B/'nen-tang.json'))
NT=sys.argv[2] if len(sys.argv)>2 else next((k for k in NTS if VID.stem.endswith(k)),'tiktok'); TREN,DUOI=NTS[NT]['tren'],NTS[NT]['duoi']
print('nen tang:',NT,TREN,DUOI)
import os
SK=pathlib.Path(os.environ.get('MG_SCRIPTS') or pathlib.Path.home()/'.claude/skills/motion-graphics/scripts')   # A3: khong ghi cung duong dan Mac
sys.path.insert(0,str(B.parent.parent/'cong-cu')); import mo_hinh   # A4: Whisper ghim revision
import traceback
(B/f'kiem/kiem-{NT}.json').unlink(missing_ok=True); (B/f'kiem/bao-cao-{NT}.md').unlink(missing_ok=True)   # A5: khong de ket qua cu lam bao 'dat' oan
def _crash(t,v,tb):   # A5: crash = ma thoat != 0 + kiem.json ghi ro
    json.dump(dict(nt=NT,video=VID.name,dat=False,crash=''.join(traceback.format_exception(t,v,tb))[-3000:],phep=[dict(ten=a,dat=bool(b),so_do=c,loi=d) for a,b,c,d in KQ]),open(B/f'kiem/kiem-{NT}.json','w'),ensure_ascii=False,indent=1)
    sys.__excepthook__(t,v,tb)
sys.excepthook=_crash
KQ=[]   # (ten, dat?, so do, loi nao trong LOI-SAI)
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
o=subprocess.run([sys.executable,str(SK/'kiem-video.py'),str(VID)],capture_output=True,text=True).stdout
m=re.search(r'tong: (\d+) FAIL, (\d+) WARN',o); lu=re.search(r'loudness I = ([-\d.]+)',o); tp=re.search(r'true peak = ([-\d.]+)',o)
sar=subprocess.run(['ffprobe','-v','error','-select_streams','v','-show_entries','stream=width,height,sample_aspect_ratio','-of','csv=p=0',str(VID)],capture_output=True,text=True).stdout.strip()
ghi('Khung 1080x1920, diem anh vuong (SAR 1:1)',sar in ('1080,1920,1:1','1080,1920,N/A'),sar,'K11')
ghi('Ky thuat file (kiem-video.py)',bool(m) and m.group(1)=='0',f"{m.group(1) if m else '?'} FAIL, {m.group(2) if m else '?'} WARN; {lu.group(1) if lu else '?'} LUFS; dinh {tp.group(1) if tp else '?'} dBTP",'K1')

# 2) trang that: phu de tran + vung an toan
subprocess.run([sys.executable,str(B/'dung.py'),'build',NT],check=True)
d=json.loads(subprocess.run(['node',str(B/'kiem/kiem-dom.cjs'),NT],capture_output=True,text=True,check=True).stdout)
ghi('Khong trung ma phan tu (id)',not d.get('trungId'),f"{len(d.get('trungId',[]))} id trung"+(f": {d['trungId'][:5]}" if d.get('trungId') else ''),'H31')
ghi('Phu de khong tran khung (moi khung)',not d['tranPhuDe'],f"{len(d['tranPhuDe'])} khung tran"+(f": {d['tranPhuDe'][:3]}" if d['tranPhuDe'] else ''),'H5')
nv=sum(len(v) for v in d['ngoaiVung'].values())
ghi('Chu ten/gia/vung khong tran hop chua (the hang + trang ket, moi moc)',not d.get('tranChu'),f"{len(d.get('tranChu',[]))} cho tran"+(f": {d['tranChu'][:3]}" if d.get('tranChu') else ''),'K19')
ghi(f'Chu/gia/logo trong vung an toan {NTS[NT]["ten"]} 120-888 x {TREN}-{DUOI}',nv==0,f"{nv} phan tu ngoai vung"+(f": {d['ngoaiVung']}" if nv else ''),'H6')

# 2a) NOI DUNG (B4). D1: ten/gia/giam/goc/vung/may tren hinh (DOM luc dung yen) khop top5.json. D2: endTime >= gio dang + 2 gio.
sys.path.insert(0,str(B)); import ten_rut_gon as TR
TOP=json.load(open(B/'top5.json')); CFG=json.load(open(B/'cau-hinh.json')); ND=d['noiDung']
def ten_gon(t): return re.sub(r'\s+',' ',re.sub(r' PS4 & PS5','',re.sub(r' for PS5| full game','',re.sub(r'[®™]','',t),flags=re.I),flags=re.I)).strip()   # = tenGon() trong full.html
sai=[]
for r in range(1,6):
    g=TOP[r-1]; h=ND['hang'][str(r)]
    mong=dict(ten=ten_gon(g.get('ten_the') or g['ten']),gia=g['gia'],giam=f"−{g['giam']}%",goc=g['goc'],vung=g['vung'].upper(),may=g['may'])
    for k,v in mong.items():
        if h.get(k)!=v: sai.append(f"hang {r} {k}: hinh '{h.get(k)}' != du lieu '{v}'")
    if not (h['hienTen'] and h['hienGia']): sai.append(f'hang {r}: ten/gia khong hien luc dung yen')
for i in range(5):
    g=TOP[i]; k=ND['ket'][i]
    if k.get('ten') in (ten_gon(g['ten']),ten_gon(g.get('ten_the') or g['ten'])): k=dict(k,ten=ten_gon(g['ten']))   # trang ket: ten day du, hoac ten the khi day du khong vua >= 26 px
    for kk,v in (('ten',ten_gon(g['ten'])),('phu',f"−{g['giam']}% · {g['vung']}"),('gia',g['gia'].replace('.000đ','K'))):
        if k.get(kk)!=v: sai.append(f"bang ket {i+1} {kk}: '{k.get(kk)}' != '{v}'")
X=CFG['muc']//1000
for kk,got,v in (('tit',ND['tit'],f'Top 5 bán chạy dưới {X}K'),('con',ND['con'],f"Còn {CFG['con_lai']} game nữa dưới {X}K:"),('ngay1',ND['ngay1'],f"Ngày {CFG['ngay']}"),('ngay6',ND['ngay6'],f"Bảng xếp hạng · Ngày {CFG['ngay']}")):
    if got!=v: sai.append(f"{kk}: hinh '{got}' != du lieu '{v}'")
ghi('D1 gia/ten/vung/giam tren hinh khop top5.json (DOM that, 5 hang + bang ket + tit + ngay)',not sai,f"{5*6+15+4} gia tri doi chieu; {len(sai)} lech"+(f": {sai[:4]}" if sai else ''),'D1')
if CFG.get('ngay_iso'):
    gio=os.environ.get('GIO_DANG','12:00'); han=datetime.datetime.fromisoformat(f"{CFG['ngay_iso']}T{gio}:00+07:00")+datetime.timedelta(hours=2)
    vn=datetime.timezone(datetime.timedelta(hours=7)); ket=[(g['ten_goc'] if g.get('ten_goc') else g['ten'],g.get('endTime')) for g in TOP]
    som=[(t[:30],datetime.datetime.fromtimestamp(int(e)/1000,vn).strftime('%d/%m %H:%M') if e else 'thieu') for t,e in ket if not e or datetime.datetime.fromtimestamp(int(e)/1000,vn)<han]
    ghi('D2 deal con it nhat 2 gio sau gio dang (endTime)',not som,f"han toi thieu {han:%d/%m %H:%M}; endTime som nhat {min(datetime.datetime.fromtimestamp(int(e)/1000,vn) for _,e in ket if e):%d/%m %H:%M}"+(f"; HET HAN SOM: {som}" if som else ''),'D2')
else:
    ghi('D2 deal con it nhat 2 gio sau gio dang (endTime)',True,'bo qua: du lieu fixture (cau-hinh.json khong co ngay_iso)','D2')

# 2b) do tren LOP CHU that (anh alpha) o luc dung yen cua 5 canh hang:
#   - khoi dau trang nam NGAY DUOI vung giao dien tren (N11/N12): 0..tren khong co giay; tren+20..tren+100 kin giay
#   - lop chu che <= 30% vung trailer net (tu mep duoi khoi dau trang toi y 1500) (N10)
from PIL import Image
CN=json.load(open(B/'canh.json')); MOC_H=[round(c['b']-0.3,2) for c in CN if c['k'].startswith('h')]
CAP=str(SK/'capture.mjs'); (B/'soi').mkdir(exist_ok=True)
subprocess.run(['node',CAP,str(B/f'full-{NT}.build.html'),str(B/'soi'/f'kiem-{NT}'),'30',str(CN[-1]['b']),'1080','1920','--alpha',
                '--stills='+','.join(f'{t:.2f}' for t in MOC_H),'--quiet','--root='+str(B)],check=True)
tren_ho=[];giay=[];che=[]
for t in MOC_H:
    a=np.asarray(Image.open(B/'soi'/f'kiem-{NT}_{t:.2f}s.png').convert('RGBA'))[:,:,3]>=217   # alpha >= 0.85 = kin
    tren_ho.append(a[:TREN].mean()); giay.append(a[TREN+20:TREN+100].mean()); che.append(a[TREN+116:1500].mean())
ok_k=max(tren_ho)<=0.01 and min(giay)>=0.95
ghi(f'Khoi dau trang ngay duoi vung giao dien ({TREN} px)',ok_k,f"giay trong vung giao dien {max(tren_ho)*100:.1f}%; kin giay y {TREN+20}-{TREN+100}: {min(giay)*100:.0f}%",'N11/N12')
ghi('Lop chu che <= 30% vung trailer net (5 canh hang)',max(che)<=0.30,'che '+', '.join(f'{x*100:.0f}%' for x in che),'N10')

# 3) tieng khop khung cham: moi cu co 'hinh' (khung cham do tren trang) -> tim suon len that trong bus quanh do
bus=np.load(B/'sfx-bus.npy').mean(axis=0); hop=96; n=len(bus)//hop
db=20*np.log10(np.sqrt(np.mean(bus[:n*hop].reshape(n,hop)**2,axis=1))+1e-9)
def onset(v,lo=0.025,hi=0.04):
    a=max(5,int((v-lo)/0.002)); b=min(n-1,int((v+hi)/0.002)); r=db[a:b]-db[a-5:b-5]; return (a+int(np.argmax(r))-3)*0.002
cue=[c for c in json.load(open(B/'cue-am.json')) if c.get('hinh') is not None and c['k'] not in ('kaching',)]
lech=[(round((onset(c['hinh'])-c['hinh'])*1000),c['k'],round(c['hinh'],2)) for c in cue]
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
tong_g=tong_v=0; xau=[]; tong_chu=0
for c in cau:
    a=max(0,int((c[0]['s']-0.15)*16000)); b=int((c[-1]['e']+0.2)*16000)
    kb=' '.join(w['w'] for w in c); tg=nghe(G16[a:b]); tv=nghe(X16[a:b]); n=len(chu(kb))
    rg=difflib.SequenceMatcher(None,chu(kb),chu(tg)).ratio(); rv=difflib.SequenceMatcher(None,chu(kb),chu(tv)).ratio()
    tong_g+=rg*n; tong_v+=rv*n; tong_chu+=n
    # cau bi coi la KEM chi khi: khop kich ban sut > 0.10 VA ban ghep khac ban chep giong goc (bo dau thanh, chuan hoa so "784 nghin"="784.000")
    # bo qua cau ngan < 1 s (Whisper doan bua ca 2 ban)
    if rv<rg-0.10 and (b-a)/16000>=1.0 and difflib.SequenceMatcher(None,chuan(tg),chuan(tv)).ratio()<0.80:
        xau.append(f"«{kb[:40]}» goc {rg:.2f} → ghep {rv:.2f} (goc: {tg[:40]} | ghep: {tv[:40]})")
rg,rv=tong_g/tong_chu,tong_v/tong_chu
ghi('Whisper tung cau: ban ghep nghe khong kem giong goc',rv>=rg-0.05 and not xau,f"{len(cau)} cau; khop kich ban: giong goc {rg:.2f}, ban ghep {rv:.2f}"+(f"; cau kem: {xau}" if xau else ''),'A2')


# 7) K18: nen trailer/anh KHONG phai anh giu cho cua PS Store ("PLACEHOLDER SCREENSHOTS"). OCR 1 khung GIUA moi doan nen (nen-<nt>.mp4 = lop nen
# thuan, chua co lop chu) -> thay PLACEHOLDER / SCREENSHOT / COMING SOON / TBA = LOI. Khong co tesseract = LOI (fail-closed).
sys.path.insert(0,str(B)); import media_hop_le as MH
if not __import__('shutil').which('tesseract'): ghi('Nen khong phai anh giu cho (OCR)',False,'may khong co tesseract (apt install tesseract-ocr / brew install tesseract)','K18')
else:
    SEG=json.load(open(B/'nen-doan.json'))['seg']; t0=0.0; xau=[]; (B/'soi').mkdir(exist_ok=True)
    for k,sg in enumerate(SEG):
        tg=t0+sg['dl']/2; t0+=sg['dl']; png=B/'soi'/f'ocr-{NT}-{k}.png'
        subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{tg:.2f}','-i',str(B/f'nen-{NT}.mp4'),'-frames:v','1','-vf','scale=960:-2',str(png)],check=True)
        ly=MH.la_giu_cho(png)
        if ly: xau.append(f'doan {k} (~{tg:.1f}s): {ly}')
    ghi('Nen khong phai anh giu cho PS Store (OCR + mang mau phang, moi doan nen)',not xau,f'{len(SEG)} doan; '+('; '.join(xau) if xau else 'khong thay chu giu cho'),'K18')

# 6) D3 (B4): Whisper KHONG goi y nghe ra TEN RUT GON + SO TIEN + TEN VUNG cua tung hang (nghe tung doan cua giong goc). Sai = TRUOT.
def bo_dau(t):
    t=''.join(c for c in unicodedata.normalize('NFD',t.lower()) if unicodedata.category(c)!='Mn').replace('đ','d')
    return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9 ]',' ',t)).strip()
def ten_nghe_duoc(h,m):   # cac tu ngay SAU tien to 'Hang N' (Whisper co luc viet 'h3'), dai m+2 tu: phan ten game ban nghe
    tk=h.split(); st=0
    for i in range(min(4,len(tk))):
        if tk[i] in ('hang','han'): st=i+2; break
        if re.fullmatch(r'h\d',tk[i]): st=i+1; break
    return ' '.join(tk[st:st+m+2])
def so_trong_van_ban(t):   # tap cac so (don vi: nghin dong) ma van ban noi toi: chu so ("167.000", "167 nghin") + so viet bang chu
    kq=set()
    for m in re.finditer(r'\d[\d.,]*',t):
        n=int(re.sub(r'\D','',m.group())); kq.add(n//1000 if n>=1000 else n)
    return kq
def bien_the_chu(n):   # cach doc so nghin 'n' bang chu (da bo dau) + bien the thuong gap (linh/le, tu/bon, lam/nam)
    c=bo_dau(TR.so_chu(n)); return {c,c.replace(' le ',' linh '),c.replace(' tu',' bon'),c.replace(' lam',' nam')}
RAW=json.load(open(B/'kich-ban.json')); sai=[]; thu=[]
NGUONG_TEN=0.40   # Whisper tieng Viet (khong goi y) nghe ten Anh rat sai chinh ta ('Outlast' -> 'aulas', 'Mortal Kombat' -> 'mo thuat combox'): fixture Top 5 01 dat 0,42-0,85 (so thu tu ten khac 0,08-0,59). Phep NAY CHI BAT thieu/loi ro; SO TIEN va VUNG moi la phep chat (xem NHAT-KY GD B)
for r in range(1,6):
    g=TOP[r-1]; k=f'h{r}'; ws=[w for w in moc if w.get('doan')==k]
    if not ws: sai.append(f'hang {r}: khong co chu nao trong moc-chu'); continue
    a0=max(0,int((ws[0]['s']-0.15)*16000)); b0=int((ws[-1]['e']+0.25)*16000)
    tho=nghe(G16[a0:b0]); nghe_ra=bo_dau(tho); loi_dong=next(x['loi'] for x in RAW if x['k']==k)
    nghe_ten=re.sub(r'\b\d{1,3}\b',lambda m:bo_dau(TR.so_chu(int(m.group()))),nghe_ra)   # 'Mortal Kombat 11' -> '...muoi mot' de so voi ten doc bang chu
    ten_mong=bo_dau(TR.ten_doc_cua(g)); ti=difflib.SequenceMatcher(None,ten_mong.replace(' ',''),ten_nghe_duoc(nghe_ten,len(ten_mong.split())).replace(' ','')).ratio()
    n_gia=TR.nghin_so(g['gia']); co_gia=(n_gia in so_trong_van_ban(tho)) or any(f' {v} ' in f' {nghe_ra} ' for v in bien_the_chu(n_gia))
    vd=TR.vung_doc_cua(g); co_vung_noi=bo_dau(vd) in bo_dau(loi_dong)   # vung chi duoc kiem o hang kich ban co noi ten vung
    bt={'indo':['indo','indonesia','in do'],'sing':['sing','singapore','xin ga'],'thai':['thai'],'my':['my','mi'],'hong kong':['hong kong','hongkong','hong kon'],'an do':['an do','ando','india']}.get(bo_dau(vd),[bo_dau(vd)])
    co_vung=(not co_vung_noi) or any(f' {v} ' in f' {nghe_ra} ' or f' {v}' in f' {nghe_ra}' and len(v)>3 for v in bt)
    thu.append(f"h{r} ten {ti:.2f}")
    if ti<NGUONG_TEN: sai.append(f"hang {r} TEN: mong '{ten_mong}' nghe ra '{nghe_ra[:50]}' (giong {ti:.2f})")
    if not co_gia: sai.append(f"hang {r} SO TIEN: mong {n_gia} nghin ('{bo_dau(TR.so_chu(n_gia))}') nghe ra '{nghe_ra[:50]}'")
    if not co_vung: sai.append(f"hang {r} VUNG: mong '{vd}' nghe ra '{nghe_ra[:50]}'")
ghi('D3 Whisper khong goi y nghe ra ten rut gon + so tien + ten vung tung hang',not sai,f"5 hang; "+', '.join(thu)+(f"; SAI: {sai}" if sai else ''),'D3')

dat=sum(1 for x in KQ if x[1]); tong=len(KQ)
with open(B/f'kiem/bao-cao-{NT}.md','w',encoding='utf-8') as f:
    f.write(f"# Bao cao kiem — {VID.name} ({NTS[NT]['ten']}) — {datetime.datetime.now():%d/%m/%Y %H:%M}\n\n**{dat}/{tong} DAT**\n\n| Phep kiem | Ket qua | So do | Loi da tung gap |\n|---|---|---|---|\n")
    for t,ok,so,ma in KQ: f.write(f"| {t} | {'DAT' if ok else '**LOI**'} | {so.replace('|','/')} | {ma} |\n")
json.dump(dict(nt=NT,video=VID.name,dat=(dat==tong),so_dat=dat,tong=tong,luc=datetime.datetime.now().isoformat(timespec='seconds'),phien_ban=mo_hinh.in_phien_ban(),
     phep=[dict(ten=a,dat=bool(b),so_do=c,loi=d) for a,b,c,d in KQ]),open(B/f'kiem/kiem-{NT}.json','w'),ensure_ascii=False,indent=1)
print(f"\n{dat}/{tong} DAT -> {B/f'kiem/bao-cao-{NT}.md'}")
sys.exit(0 if dat==tong else 1)
