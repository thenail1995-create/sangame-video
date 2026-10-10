# Dung khuon Keo thom v9 THEO NEN TANG: chen du lieu (keo.json), khoa doan (kich-ban.json), moc chu (moc-chu.json) + vung app vao full.html -> full-<nt>.build.html;
# chup anh tinh / lop alpha / anh bia. Ghep hinh: ghep08.py.
#   python3 dung.py build|stills|lop|bia [tiktok|reels|shorts|tat-ca] [moc giay]
#   vd: python3 dung.py stills reels 0.5,3.6   |   python3 dung.py lop tat-ca   |   python3 dung.py bia shorts   (moc mac dinh = moc bia trong neo.json)
import json,subprocess,sys,pathlib
from nen_tang import KHUON as B,chon,loc_nen,nt_js
V=B/'dau-vao'
import os
import keo_json,thoi_luong
# MG_SCRIPTS = thu muc co capture.mjs + node_modules/playwright (A3: Mac mac dinh la skill motion-graphics; GitHub dung cong-cu/ trong repo)
MG=pathlib.Path(os.environ.get('MG_SCRIPTS') or pathlib.Path.home()/'.claude/skills/motion-graphics/scripts')
CAP=str(MG/'capture.mjs')
WORKERS=os.environ.get('WORKERS','8')   # may 4 nhan GitHub: dat WORKERS theo nproc
DAI=thoi_luong.dai()   # = do dai giong + 1,23 s (v9: het 25.12 ghi cung)
m=[w for w in json.load(open(V/'moc-chu.json')) if w['w'].strip()]
if any('doan' not in w for w in m): raise SystemExit('LOI: moc-chu.json thieu khoa `doan` — chay can-chu.py (hoac hoi-quy/gan-doan.py voi mau cu)')
KB=json.load(open(B/'kich-ban.json')); KEO=keo_json.nap(B/'keo.json')
def moc_bia():   # moc mac dinh cho bia: moc 1 trong neo.json (= C1 - 0,16, nhu 3.7 cua ban v8.3); chua co neo.json -> 3.7
    try: return json.load(open(B/'neo.json'))['TA']['moc'][0]
    except Exception: return 3.7
def build(nt):
    s=(B/'full.html').read_text(encoding='utf-8').replace('__MOC__',json.dumps(m,ensure_ascii=False)).replace('__KB__',json.dumps(KB,ensure_ascii=False)).replace('__KEO__',json.dumps(KEO,ensure_ascii=False)).replace('__DAI__',str(DAI)).replace('__NT__',json.dumps(nt_js(nt),ensure_ascii=False))
    (B/f'full-{nt}.build.html').write_text(s,encoding='utf-8'); return s
def ghep_anh(nt,t,lop,ra,them=[]):
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(B/f'nen-{nt}.mp4'),'-i',str(lop),'-frames:v','1']+them+
                   ['-filter_complex',loc_nen(nt)+';[b][1:v]overlay=0:0',str(ra)],check=True)
viec=sys.argv[1] if len(sys.argv)>1 else 'build'
ds,thamso=chon(sys.argv[2:]); (B/'soi').mkdir(exist_ok=True)
for nt in ds:
    s=build(nt); trang=B/f'full-{nt}.build.html'
    if viec=='stills':
        ts=thamso[0] if thamso else ','.join(str(x) for x in json.load(open(B/'neo.json'))['TA']['moc'])
        subprocess.run(['node',CAP,str(trang),str(B/f'soi/lop-{nt}'),'30',str(DAI),'1080','1920','--alpha','--stills='+ts,'--quiet'],check=True)
        for t in ts.split(','):
            t=float(t); ghep_anh(nt,t,B/f'soi/lop-{nt}_{t:.2f}s.png',B/f'soi/ghep-{nt}_{t:.2f}.png')
        print('xong',nt,ts)
    elif viec=='bia':   # anh bia: khung bia tap chi day du (sao -60%, chip), AN phu de
        t=float(thamso[0]) if thamso else moc_bia()
        (B/f'bia-{nt}.build.html').write_text(s.replace('</style>','#subW{display:none!important}</style>',1),encoding='utf-8')
        subprocess.run(['node',CAP,str(B/f'bia-{nt}.build.html'),str(B/f'soi/bia-{nt}'),'30',str(DAI),'1080','1920','--alpha','--stills='+str(t),'--quiet'],check=True)
        ghep_anh(nt,t,B/f'soi/bia-{nt}_{t:.2f}s.png',B/f'bia-{nt}.jpg',['-q:v','2']); print('xong bia',nt)
    elif viec=='lop':
        subprocess.run(['node',CAP,str(trang),str(B/f'lop-{nt}.mov'),'30',str(DAI),'1080','1920','--alpha','--workers='+WORKERS,'--quiet'],check=True)
        print('xong lop',nt)
