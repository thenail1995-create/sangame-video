# Kiem TOAN BO mot video dung tu khuon tap chi v8 — chay sau moi lan dung (moi ngay).
#   uv run --with numpy --with faster-whisper --with pillow python kiem/kiem-tat-ca.py video-<nen_tang>.mp4 [nen_tang]
# Ra: kiem/bao-cao-<nen_tang>.md (bang DAT/LOI) + ma thoat 1 neu co LOI. Moi phep kiem gan voi mot loi THAT da gap (xem LOI-SAI.md cua khuon).
import json,re,subprocess,sys,pathlib,wave,difflib,datetime,os
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
ghi('Chu khong tran / bi cat / khong qua nho o moi moc (tit, ten game, gia)',not d['catChu'],f"{len(d['catChu'])} loi; co chu: {sorted(d['coChu'])[:8]}"+(f"; {d['catChu'][:3]}" if d['catChu'] else ''),'CHU-CAT')
nv=sum(len(v) for v in d['ngoaiVung'].values())
ghi(f'Chu/gia/logo trong vung an toan {NTS[NT]["ten"]} 120-888 x {TREN}-{DUOI}',nv==0,f"{nv} phan tu ngoai vung"+(f": {d['ngoaiVung']}" if nv else ''),'H6')

# 2b) do tren LOP CHU that (anh alpha) o luc dung yen cua 5 canh hang:
#   - khoi dau trang nam NGAY DUOI vung giao dien tren (N11/N12): 0..tren khong co giay; tren+20..tren+100 kin giay
#   - lop chu che <= 30% vung trailer net (tu mep duoi khoi dau trang toi y 1500) (N10)
from PIL import Image
CN=json.load(open(B/'canh.json')); MOC_H=[round(c['b']-0.3,2) for c in CN if re.match(r't\d$',c['k'])]
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
SO1={'0':'khong','1':'mot','2':'hai','3':'ba','4':'bon','5':'nam','6':'sau','7':'bay','8':'tam','9':'chin'}
def chu2(t):
    t=''.join(c for c in unicodedata.normalize('NFD',t.lower()) if unicodedata.category(c)!='Mn').replace('đ','d')
    return [SO1.get(w,w) for w in re.findall(r'\w+',t.replace('-',''))]
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
    # so sau khi BO DAU + doi so 1 chu so ra chu (K7/K13: Whisper dao dong 'Tim mot'/'Tim 1', 'chay'/'tray', 'nam sau'/'Nam Sao' du khong co tieng dong)
    rg=difflib.SequenceMatcher(None,chu2(kb),chu2(tg)).ratio(); rv=difflib.SequenceMatcher(None,chu2(kb),chu2(tv)).ratio()
    tong_g+=rg*n; tong_v+=rv*n; tong_chu+=n
    # cau bi coi la KEM chi khi: khop kich ban sut > 0.10 VA ban ghep khac ban chep giong goc (bo dau thanh, chuan hoa so "784 nghin"="784.000")
    # bo qua cau ngan < 1 s (Whisper doan bua ca 2 ban)
    if rv<rg-0.10 and (b-a)/16000>=1.0 and difflib.SequenceMatcher(None,chuan(tg),chuan(tv)).ratio()<0.80:
        xau.append(f"«{kb[:40]}» goc {rg:.2f} → ghep {rv:.2f} (goc: {tg[:40]} | ghep: {tv[:40]})")
rg,rv=tong_g/tong_chu,tong_v/tong_chu
ghi('Whisper tung cau: ban ghep nghe khong kem giong goc',rv>=rg-0.05 and not xau,f"{len(cau)} cau; khop kich ban: giong goc {rg:.2f}, ban ghep {rv:.2f}"+(f"; cau kem: {xau}" if xau else ''),'A2')

# 6) C3 — kiem tin TU DONG (chon-tin.py / sinh-tin.py). Moi phep gan voi mot loi that cua may tu dong: ten bia, ngay, so doc sai, loi dang.
sys.path.insert(0,str(B)); import so_chu as sc
TJ=json.load(open(B/'tin.json')); KB={x['k']:x['loi'] for x in json.load(open(B/'kich-ban.json'))}
ND=datetime.date.fromisoformat(TJ['ngay_dang'])
# 6a) ten game DOC trong loi phai co trong tin.json (khong de may bịa/ghi sai ten): moi tu viet hoa trong loi tung tin phai nam trong du lieu cua tin do
def bag(o,ra,bo=('loi','chi_so','kiem','anh','khoa','kieu')):
    if isinstance(o,dict):
        for kk,v in o.items():
            if kk not in bo: bag(v,ra)
    elif isinstance(o,list):
        for v in o: bag(v,ra)
    elif isinstance(o,str): ra.update(re.findall(r'[a-z0-9]+',sc.bo_dau(o)))
    return ra
sai_ten=[]
for i,g in enumerate(TJ['tin'],1):
    loi=KB[f't{i}']; cho=bag(g,set())|{'tin','re'}
    for tk in re.findall(r"[^\W\d_][\w'’]*",loi):
        if tk[0].isupper() and re.sub(r"['’]",'',sc.bo_dau(tk)) not in {re.sub(r"['’]",'',x) for x in cho} and sc.bo_dau(tk) not in cho:
            sai_ten.append(f"tin {i}: «{tk}» khong co trong tin.json")
    for ten in g['kiem']['ten']:
        if ten not in loi: sai_ten.append(f"tin {i}: ten «{ten}» khong nam trong loi")
    if g['mau']=='xanh':
        hop={sc.ten_doc(x) for x in g['ten_game']}
        for ten in g['kiem']['ten']:
            if ten not in hop: sai_ten.append(f"tin {i}: ten doc «{ten}» khong suy ra duoc tu ten_game {g['ten_game']}")
    if g['mau']=='do' and g['kiem']['ten'][0]!=sc.ten_doc(g['ten_re']): sai_ten.append(f"tin {i}: ten doc «{g['kiem']['ten'][0]}» khac ten_re «{g['ten_re']}»")
    if re.search(r'\d',re.sub(r'\bF1\b','',loi)): sai_ten.append(f"tin {i}: loi con chu so")
ghi('Ten game doc trong loi co trong tin.json (khong chu so, khong tu la)',not sai_ten,f"{len(TJ['tin'])} tin"+(f"; {sai_ten[:4]}" if sai_ten else ''),'C3')

# 6b) ngay tren giay = ngay DANG (khong phai ngay dung): tin.json, chu tren trang that, loi dao dau
exp=ND
if os.environ.get('NGAY'): exp=datetime.date.fromisoformat(os.environ['NGAY'])
sai_ngay=[]
if TJ['ngay_dang']!=exp.isoformat(): sai_ngay.append(f"tin.json ngay_dang {TJ['ngay_dang']} != ngay dang {exp}")
if TJ['ngay']!=sc.ngay_ddmm(exp) or TJ['thu']!=sc.thu_cua(exp): sai_ngay.append(f"tin.json {TJ['thu']} {TJ['ngay']} != {sc.thu_cua(exp)} {sc.ngay_ddmm(exp)}")
n1,n6=d['ngay']['n1'].strip(),d['ngay']['n6'].strip()
if n1!=f"{sc.thu_cua(exp)} · {sc.ngay_ddmm(exp)}": sai_ngay.append(f"giay dau trang '{n1}'")
if n6!=f"Bản tin sáng · {sc.ngay_ddmm(exp)}": sai_ngay.append(f"giay cuoi '{n6}'")
if sc.ngay_doc(exp) not in KB['mo']: sai_ngay.append(f"loi mo dau khong doc ngay '{sc.ngay_doc(exp)}': {KB['mo']}")
ghi('Ngay tren giay = ngay DANG (hinh + loi)',not sai_ngay,f"ngay dang {exp}: giay '{n1}' / '{n6}'"+(f"; {sai_ngay}" if sai_ngay else ''),'C3')

# 6c) D3 — Whisper KHONG goi y phai nghe ra TEN + SO cua tung tin tren chinh video (co tieng dong). Truot = LOI (ma thoat != 0).
CHU_SO={'khong':'0','mot':'1','hai':'2','ba':'3','bon':'4','nam':'5','sau':'6','bay':'7','tam':'8','chin':'9'}
def chuan_ten(t):
    """Ten game de so voi Whisper: bo dau, so doc tung chu ('hai lam') va so Whisper viet ('25'/'125') cung ve DANG CHU SO LIEN (F1 hai lam -> f125)."""
    ra=[]
    for w in re.findall(r'[a-z0-9]+',sc.bo_dau(t)):
        if w in CHU_SO or (w=='lam' and ra and ra[-1].isdigit()): ra.append(CHU_SO.get(w,'5'))
        else: ra.append(w)
    gop=[]
    for w in ra:
        if gop and gop[-1].isdigit() and w.isdigit(): gop[-1]+=w
        else: gop.append(w)
    return gop
def dau_hieu(heard,exp_toks,kieu):
    """kieu 'ten': phu >= 60% tu (gan dung) HOAC chuoi lien >= 75%; 'so': cua so truot khop thu tu (>= 0.85 o nguoi goi);
    'mem': moi tu >= 0.66 (ngay/moc ra mat: Whisper hay viet 'mot'->'mut', 'sau'->'sao')."""
    if not exp_toks: return 1.0
    if kieu=='so':
        n=len(exp_toks); best=0.0
        for w in range(max(1,n-1),n+2):
            for i in range(0,max(1,len(heard)-w+1)):
                best=max(best,difflib.SequenceMatcher(None,exp_toks,heard[i:i+w]).ratio())
        return best
    nguong=0.66 if kieu=='mem' else 0.75
    tu=sum(1 for e in exp_toks if any(difflib.SequenceMatcher(None,e,h).ratio()>=nguong for h in heard))/len(exp_toks)
    if kieu=='mem': return tu
    a=''.join(exp_toks); b=''.join(heard); m=difflib.SequenceMatcher(None,a,b).find_longest_match(0,len(a),0,len(b))
    return max(tu,m.size/len(a))
d3=[];d3_xau=[]
for i,g in enumerate(TJ['tin'],1):
    ws=[w for w in moc if w['doan']==f't{i}']
    if not ws: d3_xau.append(f'tin {i}: khong co chu trong moc-chu'); continue
    a=max(0,int((ws[0]['s']-0.15)*16000)); b=int((ws[-1]['e']+0.2)*16000)
    nghe_raw=nghe(X16[a:b]); heard_so=sc.chuan_so_sanh(nghe_raw); heard_ten=chuan_ten(nghe_raw)
    cs_=g.get('chi_so',{}).get('ten'); cs_=cs_ if isinstance(cs_,list) else ([cs_] if cs_ is not None else [])
    for jt,ten in enumerate(g['kiem']['ten']):
        r_=dau_hieu(heard_ten,chuan_ten(ten),'ten')
        if g['mau'] in ('xanh','do') and jt<len(cs_):   # ten game la tieng Anh: nghe RIENG doan ten (chi so tu trong loi) bang Whisper tieng Anh, khong goi y; lay diem cao hon
            sp=ws[cs_[jt]:cs_[jt]+len(ten.split())]
            if sp:
                en_all=[]
                for lg in ('en','vi'):
                    for pad in (0.12,0.3):
                        a2=max(0,int((sp[0]['s']-pad)*16000)); b2=int((sp[-1]['e']+0.15)*16000)
                        seg_,_=wm.transcribe(X16[a2:b2],language=lg,beam_size=5,temperature=0.0,condition_on_previous_text=False)
                        h_=' '.join(x.text.strip() for x in seg_); en_all.append(h_)
                        ht=chuan_ten(h_); r_=max(r_,dau_hieu(ht,chuan_ten(ten),'ten'),difflib.SequenceMatcher(None,''.join(chuan_ten(ten)),''.join(ht)).ratio())   # + ti le ca chuoi (Whisper nho nghe ten Anh: 'hustle down' ~ 'Hunt Showdown')
                if r_<0.6: nghe_raw=nghe_raw+' | doan ten: '+' / '.join(en_all)
        d3.append(r_)
        if r_<(0.6 if g['mau']!='vang' else 0.5): d3_xau.append(f"tin {i} ten «{ten}» {r_:.2f} nghe: «{nghe_raw[:60]}»")
    for so in g['kiem']['so']:
        r_=dau_hieu(heard_so,sc.chuan_so_sanh(so),'so'); d3.append(r_)
        if r_<0.85: d3_xau.append(f"tin {i} so «{so}» {r_:.2f} nghe: «{nghe_raw[:70]}»")
    for ng in g['kiem'].get('ngay',[]):
        r_=dau_hieu(heard_so,sc.chuan_so_sanh(ng),'mem'); d3.append(r_)
        if r_<0.75: d3_xau.append(f"tin {i} ngay/moc «{ng}» {r_:.2f} nghe: «{nghe_raw[:70]}»")
ghi('Whisper KHONG goi y nghe ra TEN + SO tung tin (D3)',not d3_xau,f"{len(d3)} muc, thap nhat {min(d3) if d3 else 1:.2f}"+(f"; {d3_xau}" if d3_xau else ''),'D3')

# 6e) khung GIUA moi canh khong co anh giu cho / chu cam (PLACEHOLDER SCREENSHOTS...) — OCR tesseract + mang mau phang (lỗi thật Top 5 11/10)
import anh_gia
if not anh_gia.co_ocr(): ghi('OCR khung giua moi canh (anh giu cho)',False,'THIEU tesseract (apt install tesseract-ocr) — khong the kiem','PLACEHOLDER')
else:
    xau_gc=[]
    for c in CN:
        tm=(c['a']+c['b'])/2; ld=anh_gia.ly_do_video(VID,tm)
        if ld: xau_gc.append(f"canh {c['k']} {tm:.1f}s: {ld}")
    ghi('Khung giua moi canh khong co anh giu cho / chu cam (OCR)',not xau_gc,f"{len(CN)} canh"+(f"; {xau_gc}" if xau_gc else ''),'PLACEHOLDER')

# 6d) loi dang cho manifest: tit <= 100, mo ta tu du lieu, hashtag, link; kiem_lai con han >= 2 ngay tu 07:30 ngay dang
LD=json.load(open(B/'loi-dang.json')); sai_ld=[]
if not 0<len(LD['tieu_de'])<=100: sai_ld.append(f"tieu_de {len(LD['tieu_de'])} ky tu")
if len(LD['mo_ta'])>2000: sai_ld.append('mo_ta > 2000')
if LD['hashtag']!=['#SănGame','#PlayStation','#PS5']: sai_ld.append(f"hashtag {LD['hashtag']}")
if LD['link']!='https://sangame.com.vn/' or 'https://sangame.com.vn/' not in LD['mo_ta']: sai_ld.append('link')
nguon_so=set(re.findall(r'\d[\d.,]*',json.dumps(TJ,ensure_ascii=False)))|set(re.findall(r'\d+',sc.ngay_ddmm(ND)))
for so in re.findall(r'\d[\d.,]*\d|\d',LD['mo_ta']):
    if so not in nguon_so and not any(so in x for x in nguon_so): sai_ld.append(f"so «{so}» trong mo ta khong co trong tin.json")
KL=json.load(open(B/'kiem-lai.json')); han=int((datetime.datetime.combine(ND,datetime.time(7,30),datetime.timezone(datetime.timedelta(hours=7)))+datetime.timedelta(days=2)).timestamp()*1000)
het=[x['ten'] for x in KL if not x.get('endTime') or int(x['endTime'])<han]
if het: sai_ld.append(f"deal het han < 2 ngay: {het[:3]}")
ghi('Loi dang (tit <= 100, mo ta tu du lieu, hashtag, link) + deal con han >= 2 ngay',not sai_ld,f"tit {len(LD['tieu_de'])} ky tu; {len(KL)} deal kiem lai"+(f"; {sai_ld[:3]}" if sai_ld else ''),'C3')

dat=sum(1 for x in KQ if x[1]); tong=len(KQ)
with open(B/f'kiem/bao-cao-{NT}.md','w',encoding='utf-8') as f:
    f.write(f"# Bao cao kiem — {VID.name} ({NTS[NT]['ten']}) — {datetime.datetime.now():%d/%m/%Y %H:%M}\n\n**{dat}/{tong} DAT**\n\n| Phep kiem | Ket qua | So do | Loi da tung gap |\n|---|---|---|---|\n")
    for t,ok,so,ma in KQ: f.write(f"| {t} | {'DAT' if ok else '**LOI**'} | {so.replace('|','/')} | {ma} |\n")
json.dump(dict(nt=NT,video=VID.name,dat=(dat==tong),so_dat=dat,tong=tong,luc=datetime.datetime.now().isoformat(timespec='seconds'),phien_ban=mo_hinh.in_phien_ban(),
     phep=[dict(ten=a,dat=bool(b),so_do=c,loi=d) for a,b,c,d in KQ]),open(B/f'kiem/kiem-{NT}.json','w'),ensure_ascii=False,indent=1)
print(f"\n{dat}/{tong} DAT -> {B/f'kiem/bao-cao-{NT}.md'}")
sys.exit(0 if dat==tong else 1)
