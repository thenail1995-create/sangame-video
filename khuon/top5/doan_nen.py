# Chon DOAN NEN trailer cho Top 5 (tach nguyen van tu nen-top5.py 22/11/2026): dung chung giua nen-top5.py (dung nen, job chung)
# va chon-top5.py (LOAI game co trailer Steam khong chon duoc doan o buoc CHON - 22/11 Mafia DE chi co video «Accolades - ESRB»
# toan chu -> job chung chet "KHONG video nao co doan sang du dai", mat Top 5 ca ngay; 14-15/11 game 4 cung vay).
# SUA LOGIC CHON DOAN O DAY (mot cho) - nen-top5.py va chon-top5.py cung goi.
import pathlib,re,subprocess,sys,tempfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import media_hop_le as MH   # K18
NGUONG_PHANG_CHON=0.70   # chon doan nen chat hon kiem cuoi K18 (0,75 trong media_hop_le.la_giu_cho) de chua bien sai so khi dung ban that
def chay(a,**k): return subprocess.run(a,capture_output=True,text=True,**k)
def thong(u):
    r=chay(['ffprobe','-v','error','-select_streams','v','-show_entries','stream=width,height:format=duration','-of','csv=p=0',u],timeout=60).stdout.split()
    # m3u8 master (Steam) co nhieu luong video (nhieu muc chat luong) -> ffprobe in nhieu dong 'w,h' roi dong thoi luong: lay luong CAO nhat
    lw=[tuple(map(int,x.split(',')[:2])) for x in r if ',' in x]; du=[float(x) for x in r if ',' not in x]
    w,h=max(lw,key=lambda x:x[1]); return w,h,du[-1]
def doc_crop(cr,w,h,H):   # cat dai den (cr) + lay dai doc rong 1080:H o giua, tron chieu cao
    cw,ch,cx,cy=cr if cr else (w,h,0,0)
    tw=min(cw,int(ch*1080/H))//2*2; return f'crop={tw}:{ch//2*2}:{cx+(cw-tw)//2}:{cy}'
def cat_vien(f):   # dai den dien anh: cropdetect tren 6 khung giua trailer
    o=chay(['ffmpeg','-v','info','-ss','20','-t','30','-i',f,'-vf','fps=0.2,cropdetect=24:2:0','-f','null','-'])
    c=re.findall(r'crop=(\d+):(\d+):(\d+):(\d+)',o.stderr)
    return list(map(int,c[-1])) if c else None
def sang_ca_doan(f,a,dl,cr=''):   # do sang TUNG KHUNG cua doan (5 diem van lot chop den ngan — LOI-SAI H23)
    y=chay(['ffmpeg','-v','error','-ss',f'{a:.2f}','-t',f'{dl:.2f}','-i',f,'-vf',(cr+',' if cr else '')+'fps=10,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-','-f','null','-']).stdout
    return [float(v) for v in re.findall(r'YAVG=([\d.]+)',y)] or [0.0]
def phang_doan(f,s0,dl,cr='',tmp=None):
    # 25/10 (run 40159369155, SOTTR Steam): doan du sang (YAVG) nhung khung GIUA doan la canh dem toi 77-78% 1 dai mau -> kiem cuoi K18 truot.
    # Soi DUNG phep cua kiem cuoi (MH.la_giu_cho) tren dai doc da cat, 3 diem quanh giua doan (kiem cuoi lay khung giua, lech khung nho)
    for fr in (0.1,0.35,0.5,0.65,0.9):   # 0,1/0,9: khung den/phang o dau-cuoi doan (25/10: 27,75-28,5 s den 12 luma lot)
        png=pathlib.Path(tmp or tempfile.gettempdir())/'_pd.png'; png.unlink(missing_ok=True)
        chay(['ffmpeg','-v','error','-y','-ss',f'{s0+dl*fr:.2f}','-i',f,'-frames:v','1','-vf',(cr+',' if cr else '')+'scale=960:-2',str(png)])
        if png.exists() and MH.la_giu_cho(png): return True
        # 30/10 (run 40811086734, 29/10): khung nguon do duoi nguong 75% nhung ban dung (scale lanczos + unsharp) do 76% -> kiem cuoi K18 truot ca bai.
        # Chon doan chua bien: bo doan khi 1 dai mau > 70% (kiem cuoi van 75%) -> thay doan/trailer khac thay vi truot.
        if png.exists() and MH.phang(png)[0]>NGUONG_PHANG_CHON: return True
        # 25/10 (run 40204868164, Risk of Rain 2 «1.0 Wide»): the logo hang HOPOO GAMES tren nen tron 1,7 s lot (phang chi 34%) -> mat do canh 1,3-2,2;
        # va SANG (luma 191-217). Canh game toi that (RE5, Lara dem) cung canh 1,1-2,5 nhung luma 12-64 -> chi bo khi canh < 2,5 VA luma > 120 (logo/the chu nen sang)
        if png.exists() and MH.phang(png)[1]<2.5:
            from PIL import Image
            if sum(Image.open(png).convert('L').resize((64,36)).getdata())/(64*36)>120: return True
    return False
def chon_doan(f,d,can,dl,cr='',cat_dau=0.0,cat_cuoi=0.0,long=False,tmp=None):
    # Doan dung phai NAM TRON trong 1 canh, du sang tung khung (Top 5 10/10: chi do diem giua -> lot doan chuyen den, YAVG 0-2; LOI-SAI H23),
    # tranh 10% dau (logo, xep hang tuoi) va 25% cuoi (man chu ket, title card)
    o=chay(['ffmpeg','-v','error','-i',f,'-vf','scdet=threshold=10,metadata=print:key=lavfi.scd.time:file=-','-an','-f','null','-'],timeout=600)
    cut=[0.0]+sorted(float(x) for x in re.findall(r'lavfi.scd.time=([\d.]+)',o.stdout))+[d]
    dau,cuoi=(0.04,0.92) if long else (0.10,0.75)   # long (24/10, Steam SOTTR 90 s khong co doan dat): noi cua so 4%-92%, van bo cat_dau/cat_cuoi
    shot=[(a,b) for a,b in zip(cut,cut[1:]) if b-a>=dl+0.15 and a>=max(d*dau,cat_dau) and b<=min(d*cuoi,d-cat_cuoi)]   # trailer Steam hay co logo/chu dau-cuoi: bo 3 s dau, 4 s cuoi
    tot=[]
    for a,b in shot:
        s0=a+min(0.1,(b-a-dl)/2); ys=sang_ca_doan(f,s0,dl,cr)
        if min(ys)>=28 and sum(ys)/len(ys)>=45 and not phang_doan(f,s0,dl,cr,tmp): tot.append((s0,s0+dl))
    if len(tot)<can:   # it doan dat: noi long nguong mot chut, van cam doan den
        for a,b in shot:
            s0=a+min(0.1,(b-a-dl)/2); ys=sang_ca_doan(f,s0,dl,cr)
            if min(ys)>=15 and (s0,s0+dl) not in tot and not phang_doan(f,s0,dl,cr,tmp): tot.append((s0,s0+dl))
    tot.sort()
    if not tot: raise SystemExit(f'KHONG co doan sang du dai trong {f} — dung anh thay trailer')
    return [tot[int(k*(len(tot)-1)/max(1,can-1))] if can>1 else tot[len(tot)//2] for k in range(can)]
