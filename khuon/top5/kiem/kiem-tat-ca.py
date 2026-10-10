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
ghi(f'Chu/gia/logo trong vung an toan {NTS[NT]["ten"]} 120-888 x {TREN}-{DUOI}',nv==0,f"{nv} phan tu ngoai vung"+(f": {d['ngoaiVung']}" if nv else ''),'H6')

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

dat=sum(1 for x in KQ if x[1]); tong=len(KQ)
with open(B/f'kiem/bao-cao-{NT}.md','w',encoding='utf-8') as f:
    f.write(f"# Bao cao kiem — {VID.name} ({NTS[NT]['ten']}) — {datetime.datetime.now():%d/%m/%Y %H:%M}\n\n**{dat}/{tong} DAT**\n\n| Phep kiem | Ket qua | So do | Loi da tung gap |\n|---|---|---|---|\n")
    for t,ok,so,ma in KQ: f.write(f"| {t} | {'DAT' if ok else '**LOI**'} | {so.replace('|','/')} | {ma} |\n")
json.dump(dict(nt=NT,video=VID.name,dat=(dat==tong),so_dat=dat,tong=tong,luc=datetime.datetime.now().isoformat(timespec='seconds'),phien_ban=mo_hinh.in_phien_ban(),
     phep=[dict(ten=a,dat=bool(b),so_do=c,loi=d) for a,b,c,d in KQ]),open(B/f'kiem/kiem-{NT}.json','w'),ensure_ascii=False,indent=1)
print(f"\n{dat}/{tong} DAT -> {B/f'kiem/bao-cao-{NT}.md'}")
sys.exit(0 if dat==tong else 1)
