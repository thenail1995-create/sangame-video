# Nen trailer Keo thom v9: TU CHON doan trailer (khong chon tay, khong duong dan tuyet doi) theo moc canh trong neo.json — giong nen-top5.py.
# Giu nguyen luat da duyet: cat bo 10% duoi khung (dong chu phap ly "Not Actual Gameplay" cua Sony — H2), cat dai den dien anh (H20),
# chon trailer phan giai cao nhat roi dai nhat (H21), do sang TUNG KHUNG cua doan se dung tren dung dai 9:16 (H23), doan nam tron trong 1 canh
# (scdet), tranh 10% dau + 25% cuoi trailer, loai khung TINH (logo/man tieu de: YDIF~0 — Spider-Man 2: INSOMNIAC, MARVEL o giua trailer 29 s), dung hinh den trang o chu "khoan..." (H17, A6).
# THEO NEN TANG (v8.3, LOI-SAI N12): moi nen tang 1 mang trailer net 1080 x cao(nt) (nen_tang.py), cat RONG hon 9:16 de hien tron chieu cao khung trailer.
#   python3 nen08.py [tiktok|reels|shorts|tat-ca]   (can neo.json: node do-khung.cjs truoc)
# Nguon doan: dau-vao/nen-doan.json = [[ten_file, bat_dau_s, do_dai_s, dung_hinh(0/1), tam_cat_ngang(0-1)(, [cw,ch,cx,cy])], ...] neu CO SAN
# (mau hoi quy v8.3 / ban tay) — khong thi tu chon va ghi nen-ke-hoach.json. Trailer: dau-vao/trailer/*.mp4, khong co thi tai tu keo.json.
import subprocess,sys,json,re,pathlib,hashlib,urllib.request,tempfile,os
import media_xau
from nen_tang import KHUON,chon,cao
TR=KHUON/'dau-vao'/'trailer'; ND=KHUON/'dau-vao'/'nen-doan.json'; KH=KHUON/'nen-ke-hoach.json'
NEO=json.load(open(KHUON/'neo.json')); M=NEO['M']; TA=NEO['TA']; C=TA['C']; DAI=TA['DAI']
def chay(a,**k): return subprocess.run(a,capture_output=True,text=True,**k)
def CROP(xc,H,cr=None):
    """cat 10% duoi (H2) + lay dai rong 1080:H cua khung trailer. cr = dai den dien anh da do [cw,ch,cx,cy]; khong co -> cong thuc v8.3 goc."""
    if not cr:
        w=f'trunc(ih*0.90*1080/{H}/2)*2'
        return f"crop={w}:trunc(ih*0.90/2)*2:min(max(iw*{xc}-{w}/2\\,0)\\,iw-{w}):0"
    cw,ch,cx,cy=cr; h=int(ch*0.90/2)*2; w=min(cw//2*2,int(ch*0.90*1080/H/2)*2); x=cx+int(min(max(cw*xc-w/2,0),cw-w))
    return f"crop={w}:{h}:{x}:{cy}"
def thong(u):
    r=chay(['ffprobe','-v','error','-select_streams','v','-show_entries','stream=width,height:format=duration','-of','csv=p=0',str(u)],timeout=90).stdout.split()
    w,h=map(int,r[0].split(',')); return w,h,float(r[1])
def tai_trailer():
    fs=sorted(TR.glob('*.mp4')) if TR.exists() else []
    if not fs:   # tai tu keo.json: phan giai cao nhat roi dai nhat (H21), toi da 2 ban
        keo=json.load(open(KHUON/'keo.json')); us=keo['game'].get('trailer') or []
        if not us: raise SystemExit('KHONG co trailer cho game nay (keo.json game.trailer rong)')
        tt=sorted(((*thong(u),u) for u in us),key=lambda x:(-x[1],-x[2]))[:2]; TR.mkdir(parents=True,exist_ok=True)
        for w,h,d,u in tt:
            f=TR/(hashlib.sha1(u.encode()).hexdigest()[:16]+'.mp4')
            if not f.exists(): urllib.request.urlretrieve(u,f)
            fs.append(f)
    tt=sorted(((*thong(f),f) for f in fs),key=lambda x:(-x[1],-x[2]))   # cao nhat roi dai nhat
    return [(f,w,h,d) for w,h,d,f in tt]
def cat_vien(f,d):   # dai den dien anh: cropdetect tren 6 khung giua trailer
    o=chay(['ffmpeg','-v','info','-ss',f'{min(20,d*0.4):.1f}','-t','30','-i',str(f),'-vf','fps=0.2,cropdetect=24:2:0','-f','null','-'])
    c=re.findall(r'crop=(\d+):(\d+):(\d+):(\d+)',o.stderr)
    return list(map(int,c[-1])) if c else None
def phan_tich(f,w,h,d,H,chat=True):
    """-> cac doan sang lien tuc nam TRON trong 1 canh: [(src, bat_dau, do_dai, YAVG tb, cr)]"""
    cr=cat_vien(f,d); a0=d*0.10; b0=d*0.75
    o=chay(['ffmpeg','-v','error','-i',str(f),'-vf','scdet=threshold=10,metadata=print:key=lavfi.scd.time:file=-','-an','-f','null','-'],timeout=900)
    cut=[0.0]+sorted(float(x) for x in re.findall(r'lavfi.scd.time=([\d.]+)',o.stdout))+[d]
    y=chay(['ffmpeg','-v','error','-ss',f'{a0:.2f}','-t',f'{b0-a0:.2f}','-i',str(f),'-vf',CROP(0.5,H,cr)+',fps=10,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-,metadata=print:key=lavfi.signalstats.YDIF:file=-','-f','null','-'],timeout=900).stdout
    ys=[float(v) for v in re.findall(r'YAVG=([\d.]+)',y)]; yd=[float(v) for v in re.findall(r'YDIF=([\d.]+)',y)]
    if yd: yd[0]=99.0   # khung dau cua cua so do chua co khung truoc
    # TINH (the logo/man tieu de nhu 'INSOMNIAC', 'MARVEL': YDIF ~ 0 nhieu khung lien) bi loai nhu khung toi: chi nhan khung co chuyen dong (YDIF >= 0,8 giua 2 khung cach 0,1 s)
    ys=[(v if (i<len(yd) and yd[i]>=0.8) else 0.0) for i,v in enumerate(ys)]
    ymin,ytb,dmin=(28,45,0.8) if chat else (15,25,0.5)
    ra=[]
    for sa,sb in zip(cut,cut[1:]):
        sa=max(sa,a0)+0.12; sb=min(sb,b0)-0.12
        if sb-sa<dmin: continue
        i0=int(round((sa-a0)*10)); i1=int(round((sb-a0)*10)); i=i0
        while i<i1:
            if i>=len(ys) or ys[i]<ymin: i+=1; continue
            j=i
            while j<i1 and j<len(ys) and ys[j]>=ymin: j+=1
            seg=ys[i:j]
            if (j-i)/10>=dmin and sum(seg)/len(seg)>=ytb: ra.append((str(f),round(a0+i/10,2),round((j-i)/10,2),round(sum(seg)/len(seg),1),cr))
            i=j
    return ra
def lay(D,pool,tieu=0.6):
    """Lap day D giay bang cac doan trong pool (vua khit nhat; thieu thi noi nhieu doan). Mot doan da dung chi con phan sau, cach 0,3 s."""
    out=[]; con=D
    while con>0.04:
        c=[p for p in pool if p['len']>=con-1e-6]
        if c: p=min(c,key=lambda p:p['len']-con)
        else:
            c=[p for p in pool if p['len']>=tieu]
            if not c: raise SystemExit(f'KHONG du doan trailer sang de lap {D:.2f}s (con thieu {con:.2f}s) — trailer qua toi/qua ngan, can xem tay')
            p=max(c,key=lambda p:p['len'])
        d=min(con,p['len']); out.append((p['src'],round(p['s0'],3),round(d,3),0,0.5,p['cr']))
        rest=p['len']-d-0.3; pool.remove(p)
        if rest>=tieu: pool.append(dict(p,s0=p['s0']+d+0.3,len=rest))
        con=round(con-d,4)
    return out
def ke_hoach(H):
    """Tu dong: cac khe (theo moc canh trong neo.json) -> doan trailer. H = chieu cao mang net rong nhat (de do sang tren dung dai se dung)."""
    k=C; khoan_e=M['hoi']['khoan_e']; store=M['hoi']['store']; c3=C[3]; c4=C[4]+.25; c5=C[5]+.18
    cuts=[0,k[1]*.5436,k[1]*.79,k[1],k[2],khoan_e,store,store+.33,c3,c3+(c4-c3)*.207,c3+(c4-c3)*.69,c4,c5,c5+(DAI-c5)*.733,DAI]
    cuts=[round(x,2) for x in cuts]
    khe=[(a,b-a) for a,b in zip(cuts,cuts[1:])]
    FZ=5   # khe thu 6 (chi so 5) = dung hinh den trang o "khoan..."
    trs=tai_trailer(); pool=[]; cac=[]
    for chat in (True,False):
        pool=[]
        for f,w,h,d in trs[:3]:
            pool+=[dict(src=s,s0=a,len=l,y=y,cr=cr) for s,a,l,y,cr in phan_tich(f,w,h,d,H,chat)]
            if sum(p['len'] for p in pool)>=2.2*DAI: break
        if sum(p['len'] for p in pool)>=1.5*DAI: break
    if sum(p['len'] for p in pool)<DAI+1: raise SystemExit(f'Trailer chi co {sum(p["len"] for p in pool):.1f}s doan sang, can >= {DAI+1:.1f}s')
    # chan anh giu cho / man phang (media_xau): moi doan trong pool lay 1 khung giua doan -> OCR + mang mau phang; xau thi bo doan
    sach=[]
    with tempfile.TemporaryDirectory() as td:
        for p in pool:
            ly=media_xau.kiem_anh(media_xau.khung(p['src'],p['s0']+p['len']/2,os.path.join(td,'k.png')))
            if ly: print('  bo doan',pathlib.Path(p['src']).name,f"{p['s0']:.1f}s:",ly)
            else: sach.append(p)
    pool=sach
    if sum(p['len'] for p in pool)<DAI+1: raise SystemExit('Sau khi bo media xau (anh giu cho/man phang) trailer khong con du doan hop le — chon game khac')
    ds={}
    for i in sorted(range(len(khe)),key=lambda i:-khe[i][1]):
        a,D=khe[i]
        if i==FZ:
            p=max(pool,key=lambda p:p['y']); ds[i]=[(p['src'],round(p['s0']+min(.2,p['len']/2),3),round(D,3),1,0.5,p['cr'])]
        else: ds[i]=lay(D,pool)
    S=[x for i in range(len(khe)) for x in ds[i]]
    json.dump(dict(cuts=cuts,seg=[list(map(lambda v:v if not isinstance(v,pathlib.Path) else str(v),s)) for s in S]),open(KH,'w'),indent=1)
    return S
if ND.exists():
    S=[(str(TR/f) if not pathlib.Path(f).is_absolute() else f,float(ss),float(dl),int(fz),float(xc),(cr[0] if cr else None)) for f,ss,dl,fz,xc,*cr in json.load(open(ND))]
    print('nen-doan.json co san (mau/ban tay):',len(S),'doan')
elif os.environ.get('NEN_DUNG_LAI')=='1':   # job `ban` cua CI: dung lai ke hoach job chung da chon (3 ban cung doan nen); thieu = loi, KHONG chon lai
    if not KH.exists(): raise SystemExit('THIEU nen-ke-hoach.json - job ban KHONG duoc chon lai doan nen')
    S=[(str(TR/pathlib.Path(f).name),float(ss),float(dl),int(fz),float(xc),cr) for f,ss,dl,fz,xc,cr in json.load(open(KH))['seg']]   # trailer o dau-vao/trailer/ cua may nay
    print('nen-ke-hoach.json (job chung):',len(S),'doan')
else:
    S=None
CHI_CHON='chon' in sys.argv[1:]   # 'chon' = CHI chon doan (job chung cua CI), khong ma hoa nen
if CHI_CHON and S is None: S=ke_hoach(cao('tiktok')); print('TU CHON',len(S),'doan; ke hoach ->',KH.name)
for nt in ([] if CHI_CHON else chon(sys.argv[1:])[0]):
    H=cao(nt)
    if S is None: S=ke_hoach(cao('tiktok')); print('TU CHON',len(S),'doan; ke hoach ->',KH.name)
    a=['ffmpeg','-v','error','-y']
    for f,s,d,fz,xc,cr in S: a+=['-ss',str(s),'-t',str(max(d,0.1)),'-i',f]
    fc=''
    for i,(f,s,d,fz,xc,cr) in enumerate(S):
        if fz: fc+=f'[{i}:v]{CROP(xc,H,cr)},scale=1080:{H}:flags=lanczos,setsar=1,trim=end_frame=1,loop=loop={round(d*30)-1}:size=1,setpts=N/30/TB,hue=s=0,eq=contrast=1.15[v{i}];'
        else: fc+=f'[{i}:v]fps=30,{CROP(xc,H,cr)},scale=1080:{H}:flags=lanczos,unsharp=5:5:0.7,setsar=1,trim=duration={d},setpts=PTS-STARTPTS[v{i}];'
    fc+=''.join(f'[v{i}]' for i in range(len(S)))+f'concat=n={len(S)}:v=1:a=0[o]'
    a+=['-filter_complex',fc,'-map','[o]','-an','-c:v','libx264','-crf','16','-pix_fmt','yuv420p',str(KHUON/f'nen-{nt}.mp4')]
    subprocess.run(a,check=True)
    print(f'nen-{nt}.mp4 1080x{H} (net tu y={1920-H}); tong', round(sum(d for _,_,d,_,_,_ in S),3))
