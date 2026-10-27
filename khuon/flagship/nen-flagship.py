# Nền FLAGSHIP (tự động): MỘT game, mỗi cảnh một đoạn trailer KHÁC NHAU (dò cắt cảnh scdet), trailer SẠCH 1080x1000 (y 0..'trailer' trong nen-tang.json).
# Bỏ 6% đầu + 12% cuối trailer (logo / end card), bỏ đoạn: có chữ (OCR), logo/thẻ chữ nền sáng, tối (YAVG), ảnh giữ chỗ (media_hop_le), MÁU ME (điểm ảnh đỏ bão hòa > 6%).
# Cắt dải đen, cắt 10% đáy (chữ pháp lý, H2), setsar=1 (K11). Thiếu đoạn hợp lệ -> thử trailer kế (PS rồi Steam); vẫn thiếu -> thoát lỗi (không dùng ảnh tĩnh).
# Mốc cảnh từ dau-vao/moc-chu.json (đổi cảnh ở GIỮA khoảng nghỉ thở — LOI-SAI A6).
#   python3 nen-flagship.py [chon|tiktok|reels|shorts|tat-ca]  -> canh.json, nen-doan.json (chọn 1 lần, 3 bản dùng chung), nen-<nt>.mp4
import json,subprocess,re,pathlib,urllib.request,sys,os
import media_hop_le as MH
import importlib.util
_sp=importlib.util.spec_from_file_location('sangame_video_steam',str(pathlib.Path(__file__).resolve().parent.parent.parent/'cong-cu'/'video_steam.py')); VS=importlib.util.module_from_spec(_sp); _sp.loader.exec_module(VS)
T=pathlib.Path(__file__).resolve().parent; TS=T/'tai-san'; sys.path.insert(0,str(T)); TS.mkdir(exist_ok=True)
NT=json.load(open(T/'nen-tang.json'))
def cao(nt): return int(NT[nt].get('trailer',1000))//2*2
G=json.load(open(T/'flagship.json')); moc=json.load(open(T/'dau-vao/moc-chu.json'))
GIU_CUOI=0.6          # khoá cuối <= 0,8 s sau chữ cuối (lặp liền)
CAT_DAU,CAT_CUOI=0.06,0.12
doan=[]
for w in moc:
    if not doan or doan[-1][0]!=w['doan']: doan.append([w['doan'],w['s'],w['e']])
    else: doan[-1][2]=w['e']
ranh=[0.0]+[round((doan[i][2]+doan[i+1][1])/2,2) for i in range(len(doan)-1)]+[round(moc[-1]['e']+GIU_CUOI,2)]
canh=[dict(k=doan[i][0],a=ranh[i],b=ranh[i+1]) for i in range(len(doan))]
json.dump(canh,open(T/'canh.json','w'),indent=1)
def chay(a,**k): return subprocess.run(a,capture_output=True,text=True,**k)
def la_m3u8(u): return '.m3u8' in u.split('?')[0]
def thong(u):
    r=chay(['ffprobe','-v','error','-select_streams','v','-show_entries','stream=width,height:format=duration','-of','csv=p=0',u],timeout=60).stdout.split()
    lw=[tuple(map(int,x.split(',')[:2])) for x in r if ',' in x]; du=[float(x) for x in r if ',' not in x]
    w,h=max(lw,key=lambda x:x[1]); return w,h,du[-1]
def khung_cat(cr,w,h,H):
    """Hộp cắt (tw,th,x,y): bỏ dải đen (cr), bỏ 10% đáy (chữ pháp lý), lấy tỉ lệ 1080:H ở giữa chiều ngang, giữ phần TRÊN."""
    cw,ch,cx,cy=cr if cr else (w,h,0,0)
    ch2=int(ch*0.9)//2*2; asp=1080/H
    tw=min(cw,int(ch2*asp)); th=min(ch2,int(tw/asp)); tw=int(th*asp)
    tw,th=tw//2*2,th//2*2
    return tw,th,cx+(cw-tw)//2,cy
def vf_cat(box): return f'crop={box[0]}:{box[1]}:{box[2]}:{box[3]}'
H0=cao('tiktok')
def cat_vien(f,d=None):
    """Dải đen: cropdetect rải khắp giữa trailer, lấy HỢP (union) các hộp -> không cắt nhầm nội dung tối (end card đen)."""
    d=d or 60; a=max(0,d*0.15); L=max(5,d*0.7)
    o=chay(['ffmpeg','-v','info','-ss',f'{a:.1f}','-t',f'{L:.1f}','-i',f,'-vf','fps=0.5,cropdetect=24:2:0','-f','null','-'])
    c=[list(map(int,x)) for x in re.findall(r'crop=(\d+):(\d+):(\d+):(\d+)',o.stderr)]
    if not c: return None
    x0=min(b[2] for b in c); y0=min(b[3] for b in c); x1=max(b[2]+b[0] for b in c); y1=max(b[3]+b[1] for b in c)
    return [x1-x0,y1-y0,x0,y0]
def tai(i,u,steam):
    f=TS/f'fl{i}{"s" if steam else ""}.mp4'
    if not f.exists():
        if la_m3u8(u):
            r=chay(['ffmpeg','-v','error','-y','-i',u,'-t','150','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-an',str(f)],timeout=900)
            if r.returncode!=0 or not f.exists(): f.unlink(missing_ok=True); print('trailer Steam tai loi:',r.stderr[-200:]); return None
        else:
            try: urllib.request.urlretrieve(u,f)
            except Exception as e: f.unlink(missing_ok=True); print('trailer tai loi:',e); return None
    w,h,d=thong(str(f)); return str(f),w,h,d
def ung_vien():
    """Sinh lần lượt các trailer dùng được: PS (trailer) rồi Steam (video_steam / tìm theo tên)."""
    urls=G.get('trailer') or []; steam0=G.get('nguon_video')=='steam'
    for k,u in enumerate(urls[:4]):
        r=tai(f'a{k}',u,steam0)
        if r: yield r+(steam0,u)
    vs=[{'url':u} for u in (G.get('video_steam') or [])]
    if not vs:
        for ten in dict.fromkeys([x for t0 in (G.get('ten'),G.get('ten_goc')) if t0 for x in (t0,re.sub(r'\s+(Deluxe|Ultimate|Definitive|Digital|Standard|Complete|Gold|Premium|Game of the Year|GOTY)\b.*$','',t0,flags=re.I).strip())]):
            vs=VS.tim_video(ten) if ten else []
            if vs: break
    for k,v in enumerate(vs[:4]):
        r=tai(f'b{k}',v['url'],True)
        if r: yield r+(True,v['url'])
def sang(f,a,dl,vf):
    y=chay(['ffmpeg','-v','error','-ss',f'{a:.2f}','-t',f'{dl:.2f}','-i',f,'-vf',vf+',fps=10,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-','-f','null','-']).stdout
    return [float(v) for v in re.findall(r'YAVG=([\d.]+)',y)] or [0.0]
def mau_me(png):
    import numpy as np
    from PIL import Image
    a=np.asarray(Image.open(png).convert('RGB')).astype(int); R,Gc,Bc=a[:,:,0],a[:,:,1],a[:,:,2]
    return ((R>110)&(R>1.6*Gc)&(R>1.6*Bc)).mean()
def co_chu(png):
    """OCR tesseract TSV: có từ >= 3 chữ cái độ tin cậy >= 60 -> đoạn có chữ."""
    r=chay(['tesseract',str(png),'stdout','--psm','11','-l','eng','tsv'],timeout=90)
    if r.returncode!=0: raise SystemExit('tesseract loi: '+r.stderr[:100])
    for ln in r.stdout.splitlines()[1:]:
        c=ln.split('\t')
        if len(c)>=12:
            try: cf=float(c[10])
            except: continue
            if cf>=60 and len(re.sub(r'[^A-Za-z]','',c[11]))>=3: return c[11]
    return None
def mau_quet(f,s0,dl,box):
    """Quet ca doan 4 khung/s (CUNG cach kiem/kiem-tat-ca.py kiem nen): -> (YAVG nho nhat thang limited 16-235, ty le do bao hoa lon nhat)."""
    import numpy as np
    H=cao('tiktok'); wv,hv=480,int(480*H/1080)//2*2
    raw=chay_b(['ffmpeg','-v','error','-ss',f'{s0:.2f}','-t',f'{dl:.2f}','-i',f,'-vf',vf_cat(box)+f',fps=4,scale={wv}:{hv}','-f','rawvideo','-pix_fmt','rgb24','-'])
    fr=np.frombuffer(raw,dtype=np.uint8).reshape(-1,hv,wv,3).astype(np.int16)
    if not len(fr): return 0.0,1.0
    ya=(0.299*fr[...,0]+0.587*fr[...,1]+0.114*fr[...,2]).mean(axis=(1,2))*219/255+16
    me=[float(((x[...,0]>110)&(x[...,0]>1.6*x[...,1])&(x[...,0]>1.6*x[...,2])).mean()) for x in fr]
    return float(ya.min()),max(me)
def chay_b(a): return subprocess.run(a,capture_output=True,check=True).stdout
def hop_le(f,s0,dl,box):
    """Doan [s0,s0+dl) hop le? -> (ok, ly do). Soi tren DUNG khung da cat: quet 4 khung/s (toi, mau me) + OCR / giu cho / logo o 3 khung."""
    vf=vf_cat(box)
    ymin,me=mau_quet(f,s0,dl,box)
    if ymin<30: return False,f'toi (YAVG min {ymin:.0f})'
    if me>0.05: return False,f'mau me {me*100:.1f}%'
    from PIL import Image
    for fr in (0.08,0.5,0.92):
        png=TS/'_fl.png'; png.unlink(missing_ok=True)
        chay(['ffmpeg','-v','error','-y','-ss',f'{s0+dl*fr:.2f}','-i',f,'-frames:v','1','-vf',vf+',scale=1080:-2',str(png)])
        if not png.exists(): return False,'khong chup duoc khung'
        ly=MH.la_giu_cho(png)
        if ly: return False,'giu cho: '+ly
        if MH.phang(png)[1]<2.5 and sum(Image.open(png).convert('L').resize((64,36)).getdata())/(64*36)>120: return False,'logo/the chu nen sang'
        c=co_chu(png)
        if c: return False,f'co chu «{c}»'
    return True,''
DOAN=T/'nen-doan.json'
cu=json.load(open(DOAN)) if DOAN.exists() else {}
if cu.get('canh')==canh and cu.get('pid')==G.get('pid'):
    SEG=cu['seg']; print('dung lai nen-doan.json')
    for s in SEG: s['src']=str(TS/pathlib.Path(s['src']).name)
else:
    if os.environ.get('NEN_DUNG_LAI')=='1': raise SystemExit('nen-doan.json khong khop canh/game - job ban KHONG duoc chon lai doan nen')
    SEG=[]; dl_canh=[round(c['b']-c['a'],3) for c in canh]
    # gom CA shot cua cac trailer (chua kiem hop le), kiem LUOI khi can
    POOL=[]   # dict(src,w,h,box,a,b,steam)
    gen=ung_vien(); het=False
    def them_trailer():
        global het
        try: f,w,h,d,steam,u=next(gen)
        except StopIteration: het=True; return False
        cr=cat_vien(f,d); box=khung_cat(cr,w,h,H0)
        o=chay(['ffmpeg','-v','error','-i',f,'-vf','scdet=threshold=10,metadata=print:key=lavfi.scd.time:file=-','-an','-f','null','-'],timeout=900)
        cut=[0.0]+sorted(float(x) for x in re.findall(r'lavfi.scd.time=([\d.]+)',o.stdout))+[d]
        lo,hi=d*CAT_DAU,d*(1-CAT_CUOI)
        if steam: lo,hi=max(lo,3.0),min(hi,d-4.0)
        n0=len(POOL)
        for a,b in zip(cut,cut[1:]):
            a2,b2=max(a,lo),min(b,hi)
            if b2-a2>=1.2: POOL.append(dict(src=f,w=w,h=h,box=box,a=a2,b=b2,steam=steam,id=len(POOL),ok=None))
        print(f'trailer {pathlib.Path(f).name} {d:.0f}s {w}x{h} box={box}: {len(POOL)-n0} shot dung duoc',[(round(x["a"],1),round(x["b"],1)) for x in POOL[n0:]],flush=True); return True
    them_trailer()
    while sum(1 for s_ in POOL if s_['b']-s_['a']>=3.6)<8 and them_trailer(): pass   # nap them trailer cho toi khi du shot DAI (it cat giua canh)
    n=len(canh); DUNG=set(); CHE={}
    def kiem(sh,s0,dl):
        k=(sh['id'],round(s0,2),round(dl,2))
        if k not in CHE:
            CHE[k]=hop_le(sh['src'],s0,dl,sh['box']); print(f"  shot {sh['id']} {pathlib.Path(sh['src']).name} {s0:.1f}+{dl:.1f}s:",'DAT' if CHE[k][0] else 'LOAI '+CHE[k][1],flush=True)
        return CHE[k]
    def chon_canh(i,dl):
        """Một đoạn liền nếu có shot đủ dài; không thì ghép vài shot ngắn (mỗi shot một đoạn con)."""
        while True:
            m=max(len(POOL),1); target=(i+.5)/n
            ds=sorted(POOL,key=lambda s:abs((POOL.index(s)+.5)/m-target))
            for sh in ds:
                if sh['id'] in DUNG or sh['b']-sh['a']<dl+0.15: continue
                sl=sh['b']-sh['a']-dl-0.1
                for off in sorted({min(0.1,sl/2),max(0.1,sl/2),max(0.1,sl-0.05)}):   # shot dai: thu 3 vi tri cua so (dau / giua / cuoi)
                    s0=sh['a']+off; ok,ly=kiem(sh,s0,dl)
                    if ok: DUNG.add(sh['id']); return [(sh,s0,dl)]
            # ghep: toi da 3 shot >= 1,2 s
            parts=[];con=dl
            for sh in sorted(ds,key=lambda s_:-(s_['b']-s_['a'])):   # ghep: shot DAI truoc (it cat nhat)
                if sh['id'] in DUNG or con<=0.01: continue
                d1=min(con,sh['b']-sh['a']-0.15)
                if d1<0.9 and con-d1>0.3: continue
                if d1<=0.3: continue
                s0=sh['a']+0.075; ok,ly=kiem(sh,s0,d1)
                if ok: parts.append((sh,s0,d1)); con-=d1
                if len(parts)>=5: break
            if con<=0.02:
                for p_ in parts: DUNG.add(p_[0]['id'])
                return parts
            if not them_trailer(): raise SystemExit(f'canh {canh[i]["k"]}: KHONG du doan hop le (het trailer) — dung anh thay trailer bi cam')
    for i,c in enumerate(canh):
        for sh,s0,d1 in chon_canh(i,round(c['b']-c['a'],3)):
            SEG.append(dict(kieu='v',src=sh['src'],ss=round(s0,3),dl=round(d1,3),box=sh['box'],w=sh['w'],h=sh['h'],canh=c['k']))
    json.dump(dict(canh=canh,pid=G.get('pid'),seg=SEG),open(DOAN,'w'),indent=1)
def dung(nt):
    H=cao(nt); a=['ffmpeg','-v','error','-y']; fc=''
    for k,s in enumerate(SEG):
        dl=s['dl']; box=s['box']
        a+=['-ss',f"{s['ss']:.3f}",'-t',f'{dl+0.1:.3f}','-i',s['src']]
        fc+=f"[{k}:v]fps=30,{vf_cat(box)},scale=1080:{H}:flags=lanczos,unsharp=5:5:0.6,setsar=1,trim=duration={dl:.4f},setpts=PTS-STARTPTS[v{k}];"
    fc+=''.join(f'[v{k}]' for k in range(len(SEG)))+f'concat=n={len(SEG)}:v=1:a=0[o]'
    ra=T/f'nen-{nt}.mp4'
    a+=['-filter_complex',fc,'-map','[o]','-an','-c:v','libx264','-crf','16','-pix_fmt','yuv420p',str(ra)]
    assert subprocess.run(a).returncode==0
    print(f'{ra.name}: 1080x{H}, trailer sach y 0..{H}')
ds=[] if len(sys.argv)>1 and sys.argv[1]=='chon' else list(NT) if len(sys.argv)<2 or sys.argv[1]=='tat-ca' else [sys.argv[1]]
for nt in ds: dung(nt)
print(len(SEG),'doan;',[(c['k'],c['a'],c['b']) for c in canh])
for s in SEG: print(f"  {s['canh']:5s} {pathlib.Path(s['src']).name:14s} tu {s['ss']:6.2f}s dai {s['dl']:.2f}s")
