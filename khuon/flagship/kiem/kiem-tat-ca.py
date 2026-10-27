# Kiem TOAN BO mot video FLAGSHIP — chay sau moi lan dung (moi ngay).
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
SOM=os.environ.get('KIEM_SOM')=='1'   # KIEM SOM (GD=chung cua CI): chi cac phep KHONG can hinh da ve; ghi kiem/kiem-som-<nt>.json, KHONG ghi kiem-<nt>.json (manifest chi tin bao cao cuoi)
TT=('som-' if SOM else '')+NT
LK_KQ=None
sys.path.insert(0,str(B.parent.parent/'cong-cu')); import mo_hinh   # A4: Whisper ghim revision
import traceback
(B/f'kiem/kiem-{TT}.json').unlink(missing_ok=True); (B/f'kiem/bao-cao-{TT}.md').unlink(missing_ok=True)   # A5: khong de ket qua cu lam bao 'dat' oan
def _crash(t,v,tb):   # A5: crash = ma thoat != 0 + kiem.json ghi ro
    json.dump(dict(nt=NT,video=VID.name,dat=False,crash=''.join(traceback.format_exception(t,v,tb))[-3000:],phep=[dict(ten=a,dat=bool(b),so_do=c,loi=d) for a,b,c,d in KQ]),open(B/f'kiem/kiem-{TT}.json','w'),ensure_ascii=False,indent=1)
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
if not SOM:   # can video da dung - KIEM SOM bo qua (bo kiem cuoi van chay)
    rv=subprocess.run([sys.executable,str(SK/'kiem-video.py'),str(VID)],capture_output=True,text=True); o=rv.stdout   # ma thoat != 0 => TRUOT (vong 2 #6)
    m=re.search(r'tong: (\d+) FAIL, (\d+) WARN',o); lu=re.search(r'loudness I = ([-\d.]+)',o); tp=re.search(r'true peak = ([-\d.]+)',o)
    sar=subprocess.run(['ffprobe','-v','error','-select_streams','v','-show_entries','stream=width,height,sample_aspect_ratio','-of','csv=p=0',str(VID)],capture_output=True,text=True).stdout.strip()
    ghi('Khung 1080x1920, diem anh vuong (SAR 1:1)',sar in ('1080,1920,1:1','1080,1920,N/A'),sar,'K11')
    ghi('Ky thuat file (kiem-video.py)',bool(m) and m.group(1)=='0' and rv.returncode==0,f"ma thoat {rv.returncode}; {m.group(1) if m else '?'} FAIL, {m.group(2) if m else '?'} WARN; {lu.group(1) if lu else '?'} LUFS; dinh {tp.group(1) if tp else '?'} dBTP",'K1')


# 2) trang that: vung an toan, D1 noi dung, D1-so (SAN #47), co chu toi thieu, khung 0
import sys as _s; _s.path.insert(0,str(B)); import flag_chung as FC
subprocess.run([sys.executable,str(B/'dung.py'),'build',NT],check=True)
d=json.loads(subprocess.run(['node',str(B/'kiem/kiem-dom.cjs'),NT],capture_output=True,text=True,check=True).stdout)
ghi('Khong trung ma phan tu (id)',not d.get('trungId'),f"{len(d.get('trungId',[]))} id trung"+(f": {d['trungId'][:5]}" if d.get('trungId') else ''),'H31')
nv=sum(len(v) for v in d['ngoaiVung'].values())
ghi('Chu/bia trong vung an toan x 70-890, y 1004-1480 (moc dung yen cuoi moi canh)',nv==0,f"{nv} phan tu ngoai vung"+(f": {d['ngoaiVung']}" if nv else ''),'H6/#49')
G=json.load(open(B/'flagship.json')); CFG=json.load(open(B/'cau-hinh.json')); ND=d['noiDung']
CN=json.load(open(B/'canh.json')); KEYS=[c['k'] for c in CN]
VUNG=G['vung'].upper(); sai=[]
def so_(ten,got,mong):
    if re.sub(r'\s+',' ',str(got)).strip()!=re.sub(r'\s+',' ',str(mong)).strip(): sai.append(f"{ten}: hinh '{got}' != du lieu '{mong}'")
ten_hien=re.sub(r'[®™]','',G['ten']).strip()
so_('mo.so tien VND',ND['mo']['so'],FC.vnd_k(G)); so_('mo.ten game',ND['mo']['ten'],ten_hien)
if not (ND['mo']['hienSo'] and ND['mo']['hienTen']): sai.append('mo: so tien / ten khong hien luc dung yen')
so_('gia.-% to',ND['pct']['pct'],f"−{G['giam']}%")
if not ND['pct']['hien']: sai.append('gia: -% to khong hien o moc doc no')
so_('gia.chip -%',ND['gia']['chip'],f"−{G['giam']}%"); so_('gia.gia cuc bo',ND['gia']['gia'],G['gia_hien']); so_('gia.gia goc',ND['gia']['goc'],G['goc_hien']); so_('gia.nhan vung',ND['gia']['lbl'],'PS STORE '+VUNG)
if not all(ND['gia']['hien']): sai.append(f"gia: khoi khong hien luc dung yen {ND['gia']['hien']}")
so_('the.menh gia + so the',ND['the']['tiles'],G['the_hien']); so_('the.= VND','='.join(ND['the']['vnd'].split('=')),'='.join(('= '+G['gia_vnd_hien']).split('=')))
if not ND['the']['hien']: sai.append('the: dong VND khong hien')
mc=G.get('moc') or {}; co_moc=mc.get('loai') not in (None,'khong') and bool(mc.get('chu'))
if co_moc!=('moc' in KEYS): sai.append(f"moc: du lieu {'co' if co_moc else 'khong co'} moc nhung canh.json {'co' if 'moc' in KEYS else 'khong co'} doan moc")
if co_moc and 'moc' in ND: so_('moc.chu',(ND['moc']['l1']+' '+ND['moc']['l2']).strip(),mc['chu'])
so_('han.nhan','GIẢM TỚI' if ND['han']['lab']=='GIẢM TỚI' else ND['han']['lab'],'GIẢM TỚI'); so_('han.ngay',ND['han']['ngay'],G['han_hien'])
if G.get('han_con_ngay') is not None: so_('han.CON N NGAY',ND['han']['con'],f"CÒN {G['han_con_ngay']} NGÀY")
elif ND['han']['con']: sai.append('han: hien CON N NGAY nhung du lieu khong co han_con_ngay')
so_('vung.dieu kien',ND['vung']['can'],'CẦN TÀI KHOẢN'); so_('vung.PSN',ND['vung']['psn'],'PSN '+VUNG)
so_('ket.thuong hieu',ND['ket']['brand'],'SĂN GAME'); so_('ket.khau hieu 1',ND['ket']['k1'],'SĂN ĐÚNG KÈO,'); so_('ket.khau hieu 2',ND['ket']['k2'],'CHƠI ĐỠ NGHÈO!')
ghi('D1 tien VND, -%, gia cuc bo, gia goc, the, ngay han, vung, ten game, moc, khau hieu tren hinh = flagship.json (DOM that)',not sai,f"{len(ND)} canh doi chieu; {len(sai)} lech"+(f": {sai[:4]}" if sai else ''),'D1')
la=[k for k in d['soHien'] if k not in FC.tap_so(G)]
ghi('D1-so: moi chuoi SO dang hien (10 khung/s) thuoc tap so trong flagship.json (khong xao/dem so la)',not la,f"{len(d['soHien'])} chuoi so khac nhau: {sorted(d['soHien'])}"+(f"; SO LA: {la}" if la else ''),'D1-so/#47')
ghi('Khong khoi chu nao bi CAT NET (khung bao ink that cua chu dang hien nam tron trong vung nhin thay cua dai: y >= 1004, khong bi overflow/clip cua cha cat; moc 0, 0,1, 0,15, 0,3, 1,0 s va dau moi canh)',not d['catNet'],f"{len(d['catNet'])} cho bi cat"+(f": {d['catNet'][:4]}" if d['catNet'] else ''),'t0-cat-so/#48')
k0=d['khung0']; ghi('Khung n=0 co so tien tren hinh (DOM t=0)',bool(k0['hien']) and k0['so']==FC.vnd_k(G) and k0['opa']>=.5,f"t=0: «{k0['so']}» hien={k0['hien']}",'#48')
K_=d['kich']; MIN={'tien_mo':139,'pct':139,'gia':139,'han_ngay':139,'ten':56,'vnd':71,'goc':48,'nhan_vung':48,'chip':48,'han_lab':48,'han_con':48,'vung_can':48,'vung_psn':48,'slogan1':64,'slogan2':64}
nho=[f"{k} {K_[k]}px < {v}" for k,v in MIN.items() if k in K_ and K_[k]<v]
ghi('Co chu toi thieu (so tien/gia >= 139, ten >= 56, dong the >= 71, chu phu >= 48, khau hieu >= 64)',not nho,f"co do: {K_}"+(f"; NHO HON: {nho}" if nho else ''),'#49')


import nghe_so as NS
import lien_ket_giong as LK
HOI_QUY=os.environ.get('HOI_QUY')=='1'
ok_ng,so_ng,ND_=NS.kiem_ngay(CFG.get('ngay_iso') or '',os.environ.get('NGAY',''),HOI_QUY)
ghi('B6 ngay du lieu (cau-hinh.json) = NGAY dang cua luot chay',ok_ng,so_ng,'B6')
if ND_ is None and CFG.get('ngay_iso'): ND_=datetime.date.fromisoformat(CFG['ngay_iso'])
if ND_ is not None and G.get('endTime'):
    gio=os.environ.get('GIO_DANG') or NS.GIO_DANG_MAC_DINH['flagship']; han=NS.han_toi_thieu(ND_,gio,6)
    vn=datetime.timezone(datetime.timedelta(hours=7)); et=datetime.datetime.fromtimestamp(int(G['endTime'])/1000,vn)
    ghi('D2 deal con it nhat 6 gio sau gio dang (endTime)',et>=han,f"han toi thieu {han:%d/%m %H:%M}; endTime {et:%d/%m %H:%M}",'D2')
else: ghi('D2 deal con it nhat 6 gio sau gio dang (endTime)',False,'khong tinh duoc: thieu ngay dang hop le hoac thieu endTime','D2')
DAIV=CN[-1]['b']; ghi('Do dai 15-27 s',15<=DAIV<=27,f"{DAIV:.2f} s",'#48')

# 2b) TRAILER SACH (bo cuc A, SAN-CHAT-LUONG #49): do tren LOP CHU that (anh alpha) — vung trailer y 0..'trailer' (nen-tang.json) KHONG co diem anh do hoa nao
#   (alpha >= 5%) o cac moc mo / dung yen / cuoi; dai y trailer..1480 phai la nen toi (alpha >= 0.85); y > 1480 la trailer mo toi (khong co do hoa).
if not SOM:   # can video da dung - KIEM SOM bo qua (bo kiem cuoi van chay)
    from PIL import Image
    MOC_H=[round(c['b']-0.3,2) for c in CN]+[round((c['a']+c['b'])/2,2) for c in CN]
    YP=NTS[NT]['trailer']; MOC_S=sorted(set([0.0,0.1,0.3,1.0]+MOC_H+[round(CN[-1]['b']-0.4,2)]))
    CAP=str(SK/'capture.mjs'); (B/'soi').mkdir(exist_ok=True)
    subprocess.run(['node',CAP,str(B/f'full-{NT}.build.html'),str(B/'soi'/f'kiem-{NT}'),'30',str(CN[-1]['b']),'1080','1920','--alpha',
                    '--stills='+','.join(f'{t:.2f}' for t in MOC_S),'--quiet','--root='+str(B)],check=True)
    tren_ho=[];duoi_kin=[]
    for t in MOC_S:
        al=np.asarray(Image.open(B/'soi'/f'kiem-{NT}_{t:.2f}s.png').convert('RGBA'))[:,:,3]
        tren_ho.append((al[:YP]>=13).mean()); duoi_kin.append((al[YP:1480,:]>=217).mean())
    ghi(f'Trailer sach: vung y 0-{YP} khong co diem anh do hoa nao (alpha >= 5%) o moc mo/giua/cuoi tung canh, {len(MOC_S)} moc',max(tren_ho)<=0.0005,f"do hoa de len trailer toi da {max(tren_ho)*100:.3f}%",'N10/#49')
    ghi('Dai thong tin phu nen toi (y trailer-1480, alpha >= 0.85; duoi 1480 chi con trailer mo, khong chu)',min(duoi_kin)>=0.995,f"kin toi thieu {min(duoi_kin)*100:.2f}%",'#49')

# 2c) NEN: khong khung toi (YAVG<20 keo >= 0,3 s), khong khung dung yen >= 1 s, khong mau me (ty le do bao hoa > 6%) — mau moi 0,25 s tren nen-<nt>.mp4
if not SOM:
    NEN=B/f'nen-{NT}.mp4'; wv,hv=480,int(480*YP/1080)//2*2
    raw=subprocess.run(['ffmpeg','-v','error','-i',str(NEN),'-vf',f'fps=4,scale={wv}:{hv}','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True).stdout
    fr=np.frombuffer(raw,dtype=np.uint8).reshape(-1,hv,wv,3).astype(np.int16)
    ya=(0.299*fr[...,0]+0.587*fr[...,1]+0.114*fr[...,2]).mean(axis=(1,2))*219/255+16   # thang YAVG cua signalstats (16-235)
    toi=[]; run=0
    for i,y in enumerate(ya):
        run=run+1 if y<20 else 0
        if run>=2: toi.append(round(i/4,2))
    me=[(round(i/4,2),round(float(((f[...,0]>110)&(f[...,0]>1.6*f[...,1])&(f[...,0]>1.6*f[...,2])).mean()),3)) for i,f in enumerate(fr)]; me=[x for x in me if x[1]>0.06]
    dung=[]; run=0
    for i in range(1,len(fr)):
        dd=np.abs(fr[i]-fr[i-1]).mean(); run=run+1 if dd<0.4 else 0
        if run>=4: dung.append(round(i/4,2))
    ghi('Nen: khong khung toi (YAVG < 20 keo >= 0,3 s), khong mau me (> 6% do bao hoa), khong dung yen >= 1 s',not toi and not me and not dung,f"{len(fr)} mau 0,25 s; YAVG min {ya.min():.0f}; toi {toi[:3]}; mau me {me[:3]}; dung yen {dung[:3]}",'K18/#cong9')

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
# 13/10 (run 38340819324): moc can chu doi khi bat dau trong quang lang truoc tieng noi ('Hạng' -46 dB) -> chi do tren khung 10 ms
# CO GIONG (giong >= -45 dBFS); chu khong co khung nao co giong thi bo qua (khong co giong de bi che). Giong goc da nghe lai: du chu 'Hạng'.
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
    # 14/10 (Keo run 38550032936): Whisper viet «3,2 trên 5» thanh «3,256» -> bo 'trên' / '/' giua hai so truoc khi so
    t=re.sub(r'(?<=\d)\s*(?:trên|/)\s*(?=\d)','',t.lower())
    t=re.sub(r'(\d+)\s*nghìn',r'\g<1>000',t); t=re.sub(r'(?<=\d)[.,](?=\d)','',t)
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
    tong_g=tong_v=0; xau=[]; tong_chu=0
    for c in cau:
        a=max(0,int((c[0]['s']-0.15)*16000)); b=int((c[-1]['e']+0.2)*16000)
        kb=' '.join(w['w'] for w in c); tg=nghe(G16[a:b]); tv=nghe(X16[a:b]); n=len(chu(kb))
        rg=difflib.SequenceMatcher(None,chu(kb),chu(tg)).ratio(); rv=difflib.SequenceMatcher(None,chu(kb),chu(tv)).ratio()
        tong_g+=rg*n; tong_v+=rv*n; tong_chu+=n
        # cau bi coi la KEM chi khi: khop kich ban sut > 0.10 VA ban ghep khac ban chep giong goc (bo dau thanh, chuan hoa so "784 nghin"="784.000")
        # bo qua cau ngan < 1 s (Whisper doan bua ca 2 ban)
        # 14/10 (Keo run 38550032936): Whisper small doc SO lech kieu viet giua 2 ban (goc «3,2 trên 5» / ghep «3,256») -> cau bi bat
        # thi nghe LAI bang turbo (mo hinh nghe kiem D3) tren ca 2 ban; chi KEM khi turbo cung thay ban ghep sut > 0.10 va khac ban goc.
        if rv<rg-0.10 and (b-a)/16000>=1.0 and difflib.SequenceMatcher(None,chuan(tg),chuan(tv)).ratio()<0.80 \
           and (lambda tg2,tv2:difflib.SequenceMatcher(None,chu(kb),chu(tv2)).ratio()<difflib.SequenceMatcher(None,chu(kb),chu(tg2)).ratio()-0.10
                and difflib.SequenceMatcher(None,chuan(tg2),chuan(tv2)).ratio()<0.80)(nghe_kiem(G16[a:b]),nghe_kiem(X16[a:b])):
            xau.append(f"«{kb[:40]}» goc {rg:.2f} → ghep {rv:.2f} (goc: {tg[:40]} | ghep: {tv[:40]})")
    rg,rv=tong_g/tong_chu,tong_v/tong_chu
    ghi('Whisper tung cau: ban ghep nghe khong kem giong goc',rv>=rg-0.05 and not xau,f"{len(cau)} cau; khop kich ban: giong goc {rg:.2f}, ban ghep {rv:.2f}"+(f"; cau kem: {xau}" if xau else ''),'A2')


# 7a) Hao 24/10/2026 ("clip dang dung hinh thay video, toi muon thay bang video cua game do"): MOI doan nen phai la VIDEO (kieu='v'), 0 doan anh (kieu='a').
#     Doc nen-doan.json (chon 1 lan, 3 ban dung chung). Thieu file / thieu khoa 'kieu' = LOI (fail-closed).
try:
    _sg=json.load(open(B/'nen-doan.json'))['seg']; _anh_nen=[f"doan {k} ({pathlib.Path(x.get('src','?')).name})" for k,x in enumerate(_sg) if x.get('kieu')!='v']
    ghi('Moi doan nen la VIDEO cua game, 0 doan anh tinh (nen-doan.json)',bool(_sg) and not _anh_nen,f"{len(_sg)} doan; {len(_anh_nen)} doan khong phai video"+(f": {_anh_nen[:4]}" if _anh_nen else ''),'V1')
except Exception as e: ghi('Moi doan nen la VIDEO cua game, 0 doan anh tinh (nen-doan.json)',False,f'khong doc duoc nen-doan.json: {e}','V1')

# 7) K18: nen trailer/anh KHONG phai anh giu cho cua PS Store ("PLACEHOLDER SCREENSHOTS"). OCR 1 khung GIUA moi doan nen (nen-<nt>.mp4 = lop nen
# thuan, chua co lop chu) -> thay PLACEHOLDER / SCREENSHOT / COMING SOON / TBA = LOI. Khong co tesseract = LOI (fail-closed).
if not SOM:   # can video da dung - KIEM SOM bo qua (bo kiem cuoi van chay)
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

# 6) D3 (nghe GIONG SACH G16): tien VND, %, vung, ngay han, ten game, gia USD (nghe so/chu), khau hieu — tung doan
cs={}
for c in CN:
    ws=[w for w in moc if w.get('doan')==c['k']]
    if ws: cs[c['k']]=(max(0,int((ws[0]['s']-0.15)*16000)),int((ws[-1]['e']+0.25)*16000))
heard,bc=NS.nghe_doan(G16,cs,nghe_kiem,B/'kiem',rev=(mo_hinh.REV_GHIM if hasattr(mo_hinh,'REV_GHIM') else '')+'|'+mo_hinh.ten_nghe_kiem())
heard_s,bc_s=NS.nghe_doan(G16,cs,nghe,B/'kiem',rev=mo_hinh.REV_GHIM if hasattr(mo_hinh,'REV_GHIM') else '')
TEN_BO={}; sai=[]; thu=[]; ma=G.get('ma') or (NS.doc_vung(G['vung']) or [(None,0)])[0][0]
def gia_usd_nghe(h,gia_doc,gia_hien):
    num=re.sub(r'[^\d.,]','',gia_hien).replace(',','.'); a,b=(num.split('.')+['0'])[:2]
    return NS.co_tu_khoa(h,[NS.bo_dau(gia_doc)]) or bool(re.search(r'(?<!\d)'+re.escape(a)+r'\s*(?:đô|do|\$)?\s*[.,]?\s*'+re.escape(b)+r'(?!\d)',h))
for k,h in heard.items():
    loi=[]
    if k=='mo':
        loi=NS.doi_chieu(h,tien=[G['gia_vnd']],ten=[G['ten_doc']],kiem_ten=False)
        _ok,_bo,_ly=NS.ten_hai_bo(G['ten_doc'],{'turbo':h,'small':heard_s.get(k)}); TEN_BO[k]=_bo
        if not _ok: loi.append(f"TEN «{G['ten_doc']}»: {_ly}")
    elif k=='gia':
        loi=NS.doi_chieu(h,phan_tram=[G['giam']],vung=[ma])
        if not gia_usd_nghe(h,G['gia_doc'],G['gia_hien']): loi.append(f"GIA {G['gia_hien']}: nghe «{h[:70]}»")
        if G.get('goc_doc') and not gia_usd_nghe(h,G['goc_doc'],G['goc_hien']): loi.append(f"GIA GOC {G['goc_hien']}: nghe «{h[:70]}»")
    elif k=='the': loi=NS.doi_chieu(h,tien=[G['gia_vnd']])
    elif k=='moc': thu.append('moc (khong kiem duoc doc theo loi tin — doc bang mat)')
    elif k=='han':
        dm=re.fullmatch(r'(\d+)/(\d+)',G['han_hien']); loi=NS.doi_chieu(h,ngay=[(int(dm.group(1)),int(dm.group(2)))])
        n_=G.get('han_con_ngay')
        if n_ is not None and 0<=n_<10 and not (NS.co_tu_khoa(h,['con '+NS._SO_TEN[n_]+' ngay']) or re.search(r'còn\s*'+str(n_)+r'\s*ngày',h,re.I)): loi.append(f'CON N NGAY: mong «con {n_} ngay» («{h[:60]}»)')
    elif k=='vung': loi=NS.doi_chieu(h,vung=[ma])
    elif k=='ket':
        for alts in (['dung keo'],['do ngheo']):
            if not NS.co_tu_khoa(h,alts): loi.append(f'KHAU HIEU: thieu «{alts[0]}» («{h[:60]}»)')
    thu.append(f"{k} «{h[:36]}»"); sai+=[f'{k} {x}' for x in loi]
ghi('D3 giong sach, tung doan: ten game, tien VND, %, vung, gia USD (so/chu), ngay han, khau hieu khop du lieu',not sai,f"{len(heard)} doan; ten dat boi {TEN_BO}; pcm {bc['pcm_sha256'][:12]} (nghe moi {bc['nghe_moi']}, dung lai {bc['dung_lai']}); "+' | '.join(thu)+(f"; SAI: {sai}" if sai else ''),'D3')
NGHE_BC=bc

# 6b) D3 (doi thiet ke 11/10, Sol #10) — "giong trong video = giong da kiem": am thanh 16 kHz trich tu MP4 nay phai TUONG QUAN duong bao nang luong (RMS 20 ms, khung co giong, lech +-300 ms) voi
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
