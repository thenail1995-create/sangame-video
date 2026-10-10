# Nền Tin nhanh (chép từ nen-top5.py 10/10): trailer nét nhất của game từng tin -> dò cắt cảnh -> chọn đoạn sáng ở giữa trailer
# -> cắt dải đen điện ảnh (LOI-SAI H20); game không có trailer -> ảnh chụp màn hình trượt chậm.
# Bố cục THEO NỀN TẢNG (Hào 10/10: "thay đổi cho phù hợp từng nền tảng", LOI-SAI N12): khối đầu trang nằm ngay dưới vùng
# giao diện của nền tảng (nen-tang.json: TikTok 240 / Reels 269 / Shorts 288), trailer NÉT liền một mảng từ mép dưới khối
# tới đáy khung. Mảng nét cao 1920 - S nên cắt RỘNG hơn 9:16 (lấy trọn chiều cao khung trailer, không cắt đầu/chân);
# phần trên khối là trailer mờ tối do dung.py ghép.
# Mốc cảnh lấy từ dau-vao/moc-chu.json (đổi cảnh ở GIỮA khoảng nghỉ thở giữa 2 đoạn — LOI-SAI A6).
#   python3 nen-tin.py [tiktok|reels|shorts|tat-ca]  -> canh.json, nen-doan.json (chọn đoạn 1 lần, dùng lại), nen-<nt>.mp4
# Nguồn nền từng cảnh: nen-nguon.json (sinh-tin.py; trailer lấy từ tai-san/trailer.json = trang PS Store ĐÚNG vùng của game; không có trailer -> ảnh chụp màn hình/bìa trượt chậm).
import json,subprocess,re,pathlib,urllib.request,sys,hashlib
T=pathlib.Path(__file__).resolve().parent; TS=T/'tai-san'
NT=json.load(open(T/'nen-tang.json'))
def cao(nt): return (1920-(NT[nt]['tren']+104))//2*2   # chieu cao mang trailer net; S = 1920 - cao = mep tren mang net
moc=json.load(open(T/'dau-vao/moc-chu.json'))
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
# canh -> [(kieu, ten, so doan)]: 'v' = trailer trong tai-san/trailer.json (khoa t1..t3), 'a' = anh trong tai-san/. Nguon do sinh-tin.py ghi vao nen-nguon.json (C2) —
# khong ghi cung ten game nua (truoc: hunt/jedi/rockbeasts.png).
NGUON={k:[(x[0],x[1],int(x[2])) for x in v] for k,v in json.load(open(T/'nen-nguon.json')).items()}
NGUON_KHOA=json.loads(json.dumps(NGUON))
DOAN=T/'nen-doan.json'
cu=json.load(open(DOAN)) if DOAN.exists() else {}
TSHA=hashlib.sha1(((TS/'trailer.json').read_bytes() if (TS/'trailer.json').exists() else b'')+b'|'+json.dumps(NGUON_KHOA,sort_keys=True).encode()).hexdigest()   # nen-doan.json cua ngay khac (trailer khac) khong duoc dung lai
if cu.get('canh')==canh and cu.get('nguon')==NGUON_KHOA and cu.get('tsha',TSHA)==TSHA:   # khong co tsha = fixture (A2)
    SEG=cu['seg']; print('dung lai nen-doan.json')
    for s in SEG: s['src']=str(TS/pathlib.Path(s['src']).name)   # nen-doan.json fixture ghi duong dan may khac -> doi ve tai-san/ cua may nay
else:
    TRJ=json.load(open(TS/'trailer.json'))
    def tai_trailer(ten,k=0):   # cao nhat roi dai nhat (H21) — trailer.json da xep san
        x=TRJ[ten][k]; f=TS/f'tr-{ten}-{k}.mp4'
        if not f.exists(): urllib.request.urlretrieve(x['u'],f)
        return str(f),x['w'],x['h'],x['d']
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
    for c in canh:
        dd=c['b']-c['a']; ds=NGUON[c['k']]; phan=dd/len(ds)
        for kieu,ten,can in ds:
            if kieu=='v':   # trailer dau toi/cat qua nhanh -> thu trailer ke tiep cua trang PS Store (Tin nhanh 10/10: Hunt trailer 1 khong co doan sang)
                for k in range(len(TRJ[ten])):
                    try: them_trailer(tai_trailer(ten,k),phan,can); break
                    except SystemExit as e: print('bo qua',ten,k,e)
                else: raise SystemExit(f'het trailer sang cho {ten}')
            else: them_anh([TS/ten],phan)
    json.dump(dict(canh=canh,nguon=NGUON_KHOA,tsha=TSHA,seg=SEG),open(DOAN,'w'),indent=1)

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
    print(f'{ra.name}: 1080x{H}, mang net tu y={1920-H}')
ds=list(NT) if len(sys.argv)<2 or sys.argv[1]=='tat-ca' else [sys.argv[1]]
for nt in ds: dung(nt)
print(len(SEG),'doan;',[(c['k'],c['a'],c['b']) for c in canh])
for s in SEG: print(f"  {s['kieu']} {pathlib.Path(s['src']).name:18s} tu {s['ss']:6.2f}s dai {s['dl']:.2f}s")
