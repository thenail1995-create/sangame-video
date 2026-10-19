# Do DOAN SANG cua trailer (tach tu nen08.py 19/10): dung chung giua nen08.py (dung nen) va chon-keo.py (LOAI game trailer toi o buoc CHON,
# 18/10 Keo 22:00 run 39131831379: Triangle Strategy chi co 18,0 s doan sang < 21 s -> chet o job `chung`). KHONG doc neo.json khi import.
import subprocess,re,time,hashlib,urllib.request,pathlib
NGUONG_SANG=21.0   # giay: ~60% cua ~35 s Kèo (du_canh() cua nen08 chi cuu trailer >= 60% can; duoi do thoat)
DAI_UOC=35.0       # DAI uoc luong cua Keo (neo.json TA.DAI) — chon-keo khong co neo.json
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
def _dai(d): return d['len'] if isinstance(d,dict) else d[2]
def quyet_dinh(doan,nguong=NGUONG_SANG):
    """Ham thuan: doan = danh sach doan sang (tuple cua phan_tich: do dai o vi tri 2, hoac dict co 'len'). -> (dat: bool, ly do|None, tong giay)."""
    tong=sum(_dai(d) for d in doan)
    if tong<nguong: return False,f'trailer chi co {tong:.1f}s doan sang < {nguong:g}s',tong
    return True,None,tong
def do_trailer(urls,H,td,san=None,ngan_sach=100.0,dai=DAI_UOC):
    """Do tong doan sang cua toi da 4 trailer (phan giai cao nhat roi dai nhat — giong tai_trailer cua nen08), thu thu tu chat=True roi chat=False
    (giong ke_hoach). san = {url: file da tai} de khong tai lai. Quá ngan_sach giay thi dung them (khong cat ngang mot lan ffmpeg).
    -> (danh sach doan, so_giay_do)"""
    t0=time.time(); san=san or {}
    tt=sorted(((*thong(u),u) for u in urls),key=lambda x:(-x[1],-x[2]))[:4]
    fs=[]
    for w,h,d,u in tt:
        f=san.get(u) or str(pathlib.Path(td)/(hashlib.sha1(u.encode()).hexdigest()[:16]+'.mp4'))
        if not pathlib.Path(f).exists():
            if time.time()-t0>ngan_sach: break
            urllib.request.urlretrieve(u,f)
        fs.append((f,w,h,d))
    pool=[]
    for chat in (True,False):
        pool=[]
        for f,w,h,d in fs:
            pool+=phan_tich(f,w,h,d,H,chat)
            if sum(_dai(p) for p in pool)>=2.2*dai or time.time()-t0>ngan_sach: break
        if sum(_dai(p) for p in pool)>=1.5*dai or time.time()-t0>ngan_sach: break
    return pool,time.time()-t0
