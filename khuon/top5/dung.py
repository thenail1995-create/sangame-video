# Dựng Top 5 THEO NỀN TẢNG (Hào 10/10: "thay đổi cho phù hợp từng nền tảng"; vùng giao diện ở nen-tang.json):
# chèn dữ liệu + vùng giao diện vào full.html -> full-<nt>.build.html; chụp ảnh tĩnh / lớp alpha / ghép hình / ảnh bìa.
# Ghép hình: trailer NÉT (nen-<nt>.mp4, cao 1920-S) đặt từ y=S tới đáy; phía trên là chính trailer đó phóng to, làm mờ, tối đi.
#   python3 dung.py build|stills|lop|hinh|bia [tiktok|reels|shorts|tat-ca] [moc giay]
#   vd: python3 dung.py stills reels 3.6,9.0   |   python3 dung.py lop tat-ca   |   python3 dung.py bia shorts 2.2
import json,subprocess,sys,pathlib
B=pathlib.Path(__file__).resolve().parent; V=B/'dau-vao'
import os
# MG_SCRIPTS = thu muc co capture.mjs + node_modules/playwright (A3: Mac mac dinh la skill motion-graphics; GitHub dung cong-cu/ trong repo)
MG=pathlib.Path(os.environ.get('MG_SCRIPTS') or pathlib.Path.home()/'.claude/skills/motion-graphics/scripts')
CAP=str(MG/'capture.mjs')
WORKERS=os.environ.get('WORKERS','8')   # may 4 nhan GitHub: dat WORKERS theo nproc
NT=json.load(open(B/'nen-tang.json'))
canh=json.load(open(B/'canh.json')); DAI=canh[-1]['b']
CFG=json.load(open(B/'cau-hinh.json'))   # {"ngay":"10/10","muc":200000,"tong":90,"con_lai":85}
GRADE="eq=saturation=0.78:contrast=1.06,curves=r='0/0.07 1/0.98':g='0/0.05 1/0.94':b='0/0.03 1/0.84',noise=alls=8:allf=t"
def cao(nt): return (1920-(NT[nt]['tren']+104))//2*2   # giong nen-top5.py
def loc_nen(nt):   # [0:v] = nen-<nt>.mp4 -> khung 1080x1920 da chinh mau, nhan [b]
    H=cao(nt); S=1920-H; WB=int(1080*1920/H)//2*2
    # setsar=1: scale WB:1920 khong dung ti le lam ffmpeg chinh SAR (14400:14381) -> app hien lech 1 px (LOI-SAI K11)
    return (f"[0:v]split[s][m];[m]scale={WB}:1920,setsar=1,crop=1080:1920,scale=270:480,boxblur=6:2,scale=1080:1920,setsar=1,"
            f"colorchannelmixer=rr=.5:gg=.5:bb=.5,eq=saturation=0.8[mo];[mo][s]overlay=0:{S},{GRADE},setsar=1[b]")
def build(nt):
    m=json.load(open(V/'moc-chu.json')); s=(B/'full.html').read_text(encoding='utf-8')
    nt_js=dict(ma=nt,ten=NT[nt]['ten'],tren=NT[nt]['tren'],duoi=NT[nt]['duoi'],S=1920-cao(nt))
    for k,v in [('__MOC__',m),('__CANH__',canh),('__TOP__',json.load(open(B/'top5.json'))),('__DAI__',DAI),('__NGAY__',CFG['ngay']),
                ('__MUC__',CFG['muc']),('__DEM__',CFG['con_lai']),('__NT__',nt_js)]:
        s=s.replace(k,json.dumps(v,ensure_ascii=False))
    (B/f'full-{nt}.build.html').write_text(s,encoding='utf-8'); return s
def chup(trang,ts,ten):
    (B/'soi').mkdir(exist_ok=True)
    subprocess.run(['node',CAP,str(trang),str(B/'soi'/ten),'30',str(DAI),'1080','1920','--alpha','--stills='+ts,'--quiet','--root='+str(B)],check=True)
def ghep_anh(nt,t,lop,ra,them=[]):
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(B/f'nen-{nt}.mp4'),'-i',str(lop),'-frames:v','1']+them+
                   ['-filter_complex',loc_nen(nt)+';[b][1:v]overlay=0:0',str(ra)],check=True)
viec=sys.argv[1] if len(sys.argv)>1 else 'build'
du=[a for a in sys.argv[2:] if a in NT or a=='tat-ca']; thamso=[a for a in sys.argv[2:] if a not in NT and a!='tat-ca']
ds=list(NT) if (du and du[0]=='tat-ca') else (du or ['tiktok'])
for nt in ds:
    s=build(nt); trang=B/f'full-{nt}.build.html'
    if viec=='stills':
        ts=thamso[0]; chup(trang,ts,f'lop-{nt}')
        for t in ts.split(','):
            t=float(t); ghep_anh(nt,t,B/f'soi/lop-{nt}_{t:.2f}s.png',B/f'soi/ghep-{nt}_{t:.2f}.png')
        print('xong',nt,ts)
    elif viec=='lop':
        subprocess.run(['node',CAP,str(trang),str(B/f'lop-{nt}.mov'),'30',str(DAI),'1080','1920','--alpha','--workers='+WORKERS,'--quiet','--root='+str(B)],check=True); print('xong lop',nt)
    elif viec=='hinh':
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(B/f'nen-{nt}.mp4'),'-i',str(B/f'lop-{nt}.mov'),'-filter_complex',
            loc_nen(nt)+";[b][1:v]overlay=0:0:format=auto,format=yuv420p,setparams=colorspace=bt709:color_trc=bt709:color_primaries=bt709:range=tv[v]",
            '-map','[v]','-t',str(DAI),'-c:v','libx264','-crf','19','-maxrate','14M','-bufsize','28M','-preset','medium','-profile:v','high','-pix_fmt','yuv420p',
            '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',str(B/f'hinh-{nt}.mp4')],check=True); print('xong hinh',nt)
    elif viec=='bia':   # anh bia: an phu de, chup khung dep nhat (mac dinh 2,2 s = bia TOP 5 du 5 bia + tem)
        t=float(thamso[0]) if thamso else 2.2
        (B/f'bia-{nt}.build.html').write_text(s.replace('</style>','#subW{display:none!important}</style>',1),encoding='utf-8')
        chup(B/f'bia-{nt}.build.html',str(t),f'bia-{nt}')
        ghep_anh(nt,t,B/f'soi/bia-{nt}_{t:.2f}s.png',B/f'bia-{nt}.jpg',['-q:v','2']); print('xong bia',nt)
