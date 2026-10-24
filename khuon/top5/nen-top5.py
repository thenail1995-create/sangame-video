# Nền Top 5 (tự động, không chọn tay): trailer nét nhất của từng game -> dò cắt cảnh -> chọn đoạn sáng ở giữa trailer
# -> cắt dải đen điện ảnh (LOI-SAI H20); game không có trailer -> ảnh chụp màn hình trượt chậm.
# Bố cục A · Đua giá (Hào chọn 24/10/2026): trailer SẠCH ở nửa trên, y 0..'trailer' trong nen-tang.json (960 px cho cả 3 nền tảng),
# không chữ/khối nào đè; nửa dưới là nền tối + 5 thanh giá do full.html vẽ. Mảng trailer cao 960 nên cắt vuông hơn 16:9 (lấy trọn chiều cao khung).
# Mốc cảnh lấy từ dau-vao/moc-chu.json (đổi cảnh ở GIỮA khoảng nghỉ thở giữa 2 đoạn — LOI-SAI A6).
#   python3 nen-top5.py [tiktok|reels|shorts|tat-ca]  -> canh.json, nen-doan.json (chọn đoạn 1 lần, dùng lại), nen-<nt>.mp4
import json,subprocess,re,pathlib,urllib.request,sys
import media_hop_le as MH   # K18: loai anh giu cho cua PS Store
T=pathlib.Path(__file__).resolve().parent; TS=T/'tai-san'; sys.path.insert(0,str(T))
NT=json.load(open(T/'nen-tang.json'))
def cao(nt): return int(NT[nt].get('trailer',960))//2*2   # chieu cao trailer SACH (y 0..cao); bo cuc A · Dua gia: phan duoi la nen toi + thanh gia (dung.py/full.html)
top=json.load(open(T/'top5.json')); moc=json.load(open(T/'dau-vao/moc-chu.json'))
GIU_CUOI=1.25
doan=[];
for w in moc:
    if not doan or doan[-1][0]!=w['doan']: doan.append([w['doan'],w['s'],w['e']])
    else: doan[-1][2]=w['e']
ranh=[0.0]+[round((doan[i][2]+doan[i+1][1])/2,2) for i in range(len(doan)-1)]+[round(moc[-1]['e']+GIU_CUOI,2)]
canh=[dict(k=doan[i][0],a=ranh[i],b=ranh[i+1]) for i in range(len(doan))]   # mo,h5,h4,h3,h2,h1,ket
json.dump(canh,open(T/'canh.json','w'),indent=1)
def chay(a,**k): return subprocess.run(a,capture_output=True,text=True,**k)
def thong(u):
    r=chay(['ffprobe','-v','error','-select_streams','v','-show_entries','stream=width,height:format=duration','-of','csv=p=0',u],timeout=60).stdout.split()
    w,h=map(int,r[0].split(',')); return w,h,float(r[1])
def doc_crop(cr,w,h,H):   # cat dai den (cr) + lay dai doc rong 1080:H o giua, tron chieu cao
    cw,ch,cx,cy=cr if cr else (w,h,0,0)
    tw=min(cw,int(ch*1080/H))//2*2; return f'crop={tw}:{ch//2*2}:{cx+(cw-tw)//2}:{cy}'
DOAN=T/'nen-doan.json'
cu=json.load(open(DOAN)) if DOAN.exists() else {}
if cu.get('canh')==canh and cu.get('top')==[g['slug'] for g in top]:
    SEG=cu['seg']; print('dung lai nen-doan.json')
    for s in SEG: s['src']=str(TS/pathlib.Path(s['src']).name)   # nen-doan.json fixture ghi duong dan may khac -> doi ve tai-san/ cua may nay
else:
    if __import__('os').environ.get('NEN_DUNG_LAI')=='1': raise SystemExit('nen-doan.json khong khop canh/nguon - job ban KHONG duoc chon lai doan nen (3 ban phai cung doan)')
    def tai_trailer(i,g):
        if not g.get('trailer'): return None
        tt=sorted(((*thong(u),u) for u in g['trailer']),key=lambda x:(-x[1],-x[2]))   # cao nhat roi dai nhat (H21)
        w,h,d,u=tt[0]; f=TS/f'tr{i}.mp4'
        if not f.exists(): urllib.request.urlretrieve(u,f)
        for fr in (0.3,0.5,0.7):   # K18: khung trailer la anh giu cho -> bo ca trailer (dung anh chup / bia)
            png=TS/f'_kt{i}.png'; chay(['ffmpeg','-v','error','-y','-ss',f'{d*fr:.2f}','-i',str(f),'-frames:v','1','-vf','scale=960:-2',str(png)])
            if png.exists() and (ly:=MH.la_giu_cho(png)): print(f'trailer game {i} bo: {ly}'); return None
        return str(f),w,h,d
    def cat_vien(f):   # dai den dien anh: cropdetect tren 6 khung giua trailer
        o=chay(['ffmpeg','-v','info','-ss','20','-t','30','-i',f,'-vf','fps=0.2,cropdetect=24:2:0','-f','null','-'])
        c=re.findall(r'crop=(\d+):(\d+):(\d+):(\d+)',o.stderr)
        return list(map(int,c[-1])) if c else None
    def sang_ca_doan(f,a,dl,cr=''):   # do sang TUNG KHUNG cua doan (5 diem van lot chop den ngan — LOI-SAI H23)
        y=chay(['ffmpeg','-v','error','-ss',f'{a:.2f}','-t',f'{dl:.2f}','-i',f,'-vf',(cr+',' if cr else '')+'fps=10,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-','-f','null','-']).stdout
        return [float(v) for v in re.findall(r'YAVG=([\d.]+)',y)] or [0.0]
    def chon_doan(f,d,can,dl,cr=''):
        # Doan dung phai NAM TRON trong 1 canh, du sang tung khung (Top 5 10/10: chi do diem giua -> lot doan chuyen den, YAVG 0-2; LOI-SAI H23),
        # tranh 10% dau (logo, xep hang tuoi) va 25% cuoi (man chu ket, title card)
        o=chay(['ffmpeg','-v','error','-i',f,'-vf','scdet=threshold=10,metadata=print:key=lavfi.scd.time:file=-','-an','-f','null','-'],timeout=600)
        cut=[0.0]+sorted(float(x) for x in re.findall(r'lavfi.scd.time=([\d.]+)',o.stdout))+[d]
        shot=[(a,b) for a,b in zip(cut,cut[1:]) if b-a>=dl+0.15 and a>=d*0.10 and b<=d*0.75]
        tot=[]
        for a,b in shot:
            s0=a+min(0.1,(b-a-dl)/2); ys=sang_ca_doan(f,s0,dl,cr)
            if min(ys)>=28 and sum(ys)/len(ys)>=45: tot.append((s0,s0+dl))
        if len(tot)<can:   # it doan dat: noi long nguong mot chut, van cam doan den
            for a,b in shot:
                s0=a+min(0.1,(b-a-dl)/2); ys=sang_ca_doan(f,s0,dl,cr)
                if min(ys)>=15 and (s0,s0+dl) not in tot: tot.append((s0,s0+dl))
        tot.sort()
        if not tot: raise SystemExit(f'KHONG co doan sang du dai trong {f} — dung anh thay trailer')
        return [tot[int(k*(len(tot)-1)/max(1,can-1))] if can>1 else tot[len(tot)//2] for k in range(can)]
    SEG=[]
    def them_trailer(info,dd,can):
        f,w,h,d=info; cr=cat_vien(f); dl=dd/can
        ds=chon_doan(f,d,can,dl,doc_crop(cr,w,h,cao('tiktok')))   # do sang tren DUNG dai se dung (mang rong nhat)
        for a,b in ds: SEG.append(dict(kieu='v',src=f,ss=a,dl=dl,cr=cr,w=w,h=h))
    def them_anh(paths,dd):
        dl=dd/len(paths)
        for k,p in enumerate(paths): SEG.append(dict(kieu='a',src=str(p),ss=0,dl=dl,ben='trai' if k%2 else 'phai'))
    TR={i:tai_trailer(i,g) for i,g in enumerate(top,1)}
    ANH={}
    for i,g in enumerate(top,1):
        if TR[i]: continue
        ps=[]
        for k,u in enumerate(g.get('anh_chup',[])[:2]):
            p=TS/f'chup{i}_{k}.jpg'
            if not p.exists(): urllib.request.urlretrieve(u+'?w=1920',p)
            ly=MH.la_giu_cho(p)
            if ly: print(f'anh chup game {i} bo: {ly}'); continue   # K18
            ps.append(p)
        if not ps and (TS/'o_pic0.png').exists() and i==4: ps=[TS/'o_pic0.png',TS/'bia4-goc.png']   # Outlast: anh nen goi game (pic0) + bia goc; KHONG dung anh hub (la bia DLC Whistleblower)
        ANH[i]=ps or [TS/f'bia{i}.png']
    for c in canh:
        dd=c['b']-c['a']
        if c['k']=='mo':      # mo dau: 5 canh nhanh, hang 5 -> 1
            for i in (5,4,3,2,1):
                if TR[i]: them_trailer(TR[i],dd/5,1)
                else: them_anh(ANH[i][:1],dd/5)
        elif c['k']=='ket':   # ket: doan sang cua game hang 1
            them_trailer(TR[1],dd,2) if TR[1] else them_anh(ANH[1][:1],dd)   # 2 canh ngan: trailer hiem canh sang lien 5,7 s
        else:
            i=int(c['k'][1])
            them_trailer(TR[i],dd,2) if TR[i] else them_anh(ANH[i][:2],dd)
    json.dump(dict(canh=canh,top=[g['slug'] for g in top],seg=SEG),open(DOAN,'w'),indent=1)

def dung(nt):
    H=cao(nt); HH=int(H*1.1)//2*2; a=['ffmpeg','-v','error','-y']; fc=''
    for k,s in enumerate(SEG):
        dl=s['dl']
        if s['kieu']=='v':
            a+=['-ss',f"{s['ss']:.3f}",'-t',f'{dl+0.1:.3f}','-i',s['src']]
            fc+=f"[{k}:v]fps=30,{doc_crop(s['cr'],s['w'],s['h'],H)},scale=1080:{H}:flags=lanczos,unsharp=5:5:0.6,setsar=1,trim=duration={dl:.4f},setpts=PTS-STARTPTS[v{k}];"
        else:
            from PIL import Image
            ys=sum(Image.open(s['src']).convert('L').resize((64,36)).getdata())/(64*36)
            nang=',eq=gamma=1.35:brightness=0.03' if ys<55 else ''   # anh toi (YAVG<55) nang sang nhe
            a+=['-loop','1','-t',f'{dl+0.1:.3f}','-i',s['src']]
            x0,x1=(0.15,0.45) if s['ben']=='phai' else (0.55,0.25)
            fc+=(f"[{k}:v]fps=30,scale=w='trunc(max(1188,iw*{HH}/ih)/2)*2':h='trunc(max({HH},ih*1188/iw)/2)*2',"
                 f"crop=1188:{HH}:'(iw-ow)*({x0}+({x1}-{x0})*t/{dl:.3f})':'(ih-oh)/2',scale=1080:{H}:flags=lanczos{nang},setsar=1,"
                 f"trim=duration={dl:.4f},setpts=PTS-STARTPTS[v{k}];")
    fc+=''.join(f'[v{k}]' for k in range(len(SEG)))+f'concat=n={len(SEG)}:v=1:a=0[o]'
    ra=T/f'nen-{nt}.mp4'
    a+=['-filter_complex',fc,'-map','[o]','-an','-c:v','libx264','-crf','16','-pix_fmt','yuv420p',str(ra)]
    r=subprocess.run(a); assert r.returncode==0
    print(f'{ra.name}: 1080x{H}, trailer sach y 0..{H}')
# 'chon' = CHI chon doan + tai trailer/anh (canh.json, nen-doan.json, tai-san/): job chung cua CI; job tung ban sau do `python3 nen-... <nt>` dung lai nen-doan.json va chi ma hoa nen cua ban do
ds=[] if len(sys.argv)>1 and sys.argv[1]=='chon' else list(NT) if len(sys.argv)<2 or sys.argv[1]=='tat-ca' else [sys.argv[1]]
for nt in ds: dung(nt)
print(len(SEG),'doan;',[(c['k'],c['a'],c['b']) for c in canh])
for s in SEG: print(f"  {s['kieu']} {pathlib.Path(s['src']).name:18s} tu {s['ss']:6.2f}s dai {s['dl']:.2f}s")
