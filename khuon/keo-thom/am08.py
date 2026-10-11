# Tieng ban 08 (lam lai 10/10 sau khi Hao che "am thanh chua khop").
# Loi cu: file tieng dong ElevenLabs KHONG dap o dau file (dau-nhe dap o 0,60 s, giay-vut/lat-trang dinh ~0,46-0,5 s)
# ma cue dat DAU FILE vao luc hinh bat dau chuyen dong -> tieng tre ~0,5 s; do to cac file lech 36 dB.
# Cach moi: cat tung file DUNG CU DAP, chuan hoa do to, dat CU DAP trung KHUNG CHAM tinh tu cong thuc chuyen dong
# cua full.html (cung W(), cung hang so), giam tieng dong khi giong dang noi (ducking), chuan hoa -14 LUFS.
#   python3 am08.py            -> am08.wav + cue-am08.md + video-<nt>.mp4 (giu nguyen hinh, thay tieng)
# v9: moc thoi gian khong con ghi cung (W(n), 8.8, 9.92, 13.22...) — doc neo.json (do-khung.cjs ghi tu CHINH full.html: M = moc chu theo khoa doan, TA = moc chuyen canh).
import json,subprocess,numpy as np,pathlib,sys
B=pathlib.Path(__file__).resolve().parent; V=B/'dau-vao'
import pathlib
A=str(pathlib.Path(__file__).resolve().parent/'am-thanh')+'/'; MM=A   # thu vien tieng dong chep vao khuon (giay phep: am-thanh/NGUON.md)
import thoi_luong
SR=48000; DAI=thoi_luong.dai(); N=int(DAI*SR)
NEO=json.load(open(B/'neo.json')); M=NEO['M']; TA=NEO['TA']; C=TA['C']

def doc(f):
    return np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',f,'-ac','1','-ar',str(SR),'-f','f32le','-'],capture_output=True,check=True).stdout,dtype=np.float32).copy()
SRC={k:doc((MM if k=='record-scratch' else A)+k+'.mp3') for k in ['chuong-ket','danh-may','dau-nhe','dem-so','dong-dau','dong-ho','gach-but','giay-vut','ka-ching','lat-trang','to-mau','record-scratch']}

# KIT: ten -> (file, cat tu, cat den, cu dap trong doan cat, DINH so voi DINH GIONG dB). Moc cat/cu dap do bang song (cu.py, 10/10).
# Lan 1 can theo do to trung binh -> dinh tieng dong thap hon giong 15-35 dB (gan nhu khong nghe) -> doi sang can theo DINH 10 ms.
KIT={
 'dap':     ('dong-dau',0.000,0.32,0.006,-2),    # dong dau manh, dap ngay dau file
 'dau':     ('dau-nhe',0.596,0.80,0.006,-5),     # 1 cu dau nhe (cu to nhat trong 3 cu cua file, o 0,602 s)
 'vut':     ('giay-vut',0.05,0.76,0.445,-9),    # giay vut: dinh 0,495 s -> trung luc nhanh nhat
 'lat':     ('lat-trang',0.10,0.95,0.362,-6),
 'lat2':    ('lat-trang',0.20,0.62,0.262,-6),   # lat trang DUOI NGAN: tat truoc khi giong noi tiep (A6)    # lat trang: cu lat chinh 0,462 s
 'gach':    ('gach-but',0.0,0.55,0.0,-9),       # gach but 0,55 s (2 net gach)
 'to':      ('to-mau',0.0,0.55,0.0,-12),         # but da: 0,55 s = thoi gian thanh gia dai ra
 'dem':     ('dem-so',0.04,0.99,0.008,-10),      # may dem so 0,95 s = luc so dem
 'kaching': ('ka-ching',0.0,0.95,0.015,-6),
 'go':      ('danh-may',0.030,0.095,0.004,-8),  # 1 cu go phim (cu dau trong 4 cu)
 'go2':     ('danh-may',0.188,0.250,0.004,-8),  # cu go khac (tranh lap y het)
 'trang':   ('danh-may',0.0,0.38,0.034,-9),     # chuoi go 4 cu (bang lat so)
 'dongho':  ('dong-ho',0.0,0.80,0.066,-10),
 'chuong':  ('chuong-ket',0.0,1.48,0.0,-4),
 'rit':     ('record-scratch',0.175,0.535,0.0,-6),  # dia rit: doan dac nhat, het truoc chu "mua"
}
def dinh10(x,w=480):
    n=len(x)//w; return np.sqrt(np.mean(x[:n*w].reshape(n,w)**2,axis=1)).max()
GIONG=doc(str(V/'giong.mp3'))
VP=np.percentile(np.sqrt(np.mean(GIONG[:len(GIONG)//480*480].reshape(-1,480)**2,axis=1)),99)   # dinh giong (10 ms, phan vi 99)
def chuan(x):
    return x*(VP/dinh10(x))
# Loc thong cao cho tieng SOT SOAT (gach but, lat trang, giay vut, to but): bo dai tan cua loi noi (~300-2500 Hz) de khong che chu.
# Do 10/10: gach but de len 'hai trieu' -> Whisper nghe 'thai chieu' (LOI-SAI A6).
HP={'gach':2800,'lat':1800,'lat2':1800,'vut':1800,'to':2800}
def hp(x,f):
    return np.frombuffer(subprocess.run(['ffmpeg','-v','error','-f','f32le','-ar',str(SR),'-ac','1','-i','-','-af',f'highpass=f={f},highpass=f={f}','-f','f32le','-'],input=x.astype(np.float32).tobytes(),capture_output=True,check=True).stdout,dtype=np.float32).copy()
CUT={}
for k,(f,a,b,hit,g) in KIT.items():
    x=SRC[f][int(a*SR):int(b*SR)].copy()
    if k in HP: x=hp(x,HP[k])
    fi=int(0.003*SR); x[:fi]*=np.linspace(0,1,fi)               # chong click dau doan
    fo=int(min(0.06,(b-a)/4)*SR); x[-fo:]*=np.linspace(1,0,fo)**2
    CUT[k]=(chuan(x)*10**(g/20),hit)

# ===== KHUNG CHAM DO TREN TRANG THAT (do-khung.cjs -> khung.json) =====
import re
K=json.load(open(B/'khung.json')); F=len(K); FPS=30
SOM=0.010                                    # tieng dap som 10 ms so voi khung hien (mat nghe tieng truoc thay hinh thi ok, tre thi lech)
def sc(x):
    if isinstance(x,str):
        mm=re.search(r"scale\(([\d.]+)\)",x); return float(mm.group(1)) if mm else 0
    return x
def cham(key):                               # khung dau tien vat hien va co <= 1.03 (dau/tem da cham giay)
    for f in range(1,F):
        x=sc(K[f][key])
        if x and x<=1.03: return f/FPS
def doi(key,dk):                             # cac khung ma gia tri doi theo dieu kien
    return [f/FPS for f in range(1,F) if dk(K[f-1][key],K[f][key])]
def keo():
    out=[]
    ang=lambda r:abs(float(re.search(r"rotate\(([-\d.e]+)",r['keo']).group(1))) if r['keo'] and r['keoOn'] else 99
    for f in range(1,F-1):
        a=ang(K[f])
        if K[f]['keoOn'] and a<=ang(K[f-1]) and a<ang(K[f+1]) and a<6: out.append(f/FPS)
    return out
def chot(i,fin=TA['so']):                     # khung o so i CHOT hang (tu do tro di luon dung chu cuoi; so ngau nhien trung chu cuoi truoc do khong tinh)
    for f in range(1,F):
        if K[f-1]['lat'][i]!=fin[i] and all(K[g]['lat'][i]==fin[i] for g in range(f,F)): return f/FPS
def nhanh_nhat(lo,hi):                       # khung bang dau doi chieu cao nhanh nhat (gap / phu trang)
    fs=[f for f in range(1,F) if lo<=f/FPS<=hi]; return max(fs,key=lambda f:abs(K[f]['H']-K[f-1]['H']))/FPS

E=[]
def cu(t,k,db=0,x=540,ghi=''): E.append((round(t,3),k,db,x,ghi))
def dap(key,k,db,x,ghi): cu(cham(key)-SOM,k,db,x,ghi+' (khung cham do duoc)')
# bia
dap('ronde','dau',-2,230,'dau tron KEO THOM')
cu(M['mo']['ten']-0.05,'to',-2,700,'but da quet duoi ten game (bat dau quet)')
dap('sao','dap',-2,690,'sao GIAM 60%')
cu(M['mo']['ps']-0.07,'vut',-3,300,'chip PS STORE MY truot vao (eo5, nhanh nhat ~+0.05)')
# trang 01
cu(nhanh_nhat(C[1]-0.06,C[1]+0.54),'lat2',-1,540,'bia gap lai thanh dau trang (khung gap nhanh nhat)')
cu(next(f/FPS for f in range(1,F) if K[f]['saoNho'] and not K[f-1]['saoNho'])-SOM,'dau',-7,235,'sao 60% dan len goc the gia')
cu(doi('g1',lambda a,b:a>=519 and b<519)[0]-SOM,'gach',-3,420,'gach but do gia goc (khung net bat dau)')
cu(doi('so',lambda a,b:a==TA['goc'] and b!=a and b!='???')[0]-SOM,'dem',0,520,'so dem gia goc -> gia con (khung so bat dau doi)')
dap('tk','dap',-1,670,'dau DA TIET KIEM')
cu(cham('tk')-SOM+0.01,'kaching',0,670,'')
cu(TA['dut']+0.12,'vut',-8,540,'day dut, the roi (dy2 = 4500 t^2)')
# trang 02: HO SO GAME (11/10, thay canh hoi-dap): ho so truot vao khi the gia da roi; moi hang hien theo chu (khung cham do tren trang that); hang khong co du lieu thi khong co cue
def dapk(key,k,db,x,ghi):
    t=cham(key)
    if t: cu(t-SOM,k,db,x,ghi+' (khung cham do duoc)')
cu(TA['g3']+0.04,'vut',-7,300,'ho so game truot vao tu trai (eo5, nhanh nhat dau)')
dapk('gtG','dau',-6,230,'con dau the loai')
dapk('gtScore','dau',-8,520,'so diem sao dong dau')
dapk('gtB','dau',-7,300,'dai BAN ... CO THEM')
for i in range(1,5): dapk(f'gtI{i}','go' if i%2 else 'go2',-9,220+80*i,f'phan them {i} hien')
cu(TA['ra3']+0.05,'lat2',0,540,'lat trang: ho so game bay trai (khoang nghi truoc "Store")')
# bang so
for i in range(3):
    cu(doi('b',lambda a,b,i=i:a[i]==0 and b[i]>0)[0]-SOM,'to',0,300,f'thanh gia hang {i+1} bat dau dai ra (0,55 s)')
for key,ghi in [('d1','nhan RE NHAT'),('d2','nhan +51.000d'),('d3','nhan +120.000d')]: dap(key,'dau',-5,800,ghi)
cu(TA['r4']+0.14,'lat2',-2,540,'bang so bay trai + phieu vao tu phai (khoang nghi truoc "Nhung")')
# trang 03
cu(M['han']['nhanh']-0.06+0.1,'dau',-7,300,'chu "Nhanh" roi cham')
cu(M['han']['nha']-0.02+0.1,'dau',-5,300,'chu "keo lo!" roi cham')
for j,t in enumerate(keo()): cu(t-SOM,'go' if j%2 else 'go2',-6,80+75*j,'keo khep luoi (khung do duoc)')
cu(TA['dq'],'dongho',0,256,'kim dong ho quay (0,8 s)')
cu(TA['bd'],'trang',0,620,'bang lat so xao')
cu(TA['bd']+0.30,'trang',-4,620,'bang lat so xao (tiep)')
for i in range(4): cu(chot(i)-SOM,'go',-6,400+110*i+(30 if i>1 else 0),f'o so {i+1} chot (khung do duoc)')
# bia sau
cu(nhanh_nhat(C[5]-0.07,C[5]+0.58),'lat2',+1,540,'trang bia sau phu xuong (khung phu nhanh nhat)')
for i in range(6): dap(f'chip{i}','dau',-5,182+126*i,f'o vung {i+1}')
go=doi('url',lambda a,b:b>a)
for j,t in enumerate(go): cu(t-SOM,'go' if j%2 else 'go2',-7,420,f'go chu thu {j+1} sangame.com.vn (khung chu hien)')
dap('logoW','dap',-6,240,'logo dan len')
cu(max(go[-1]+0.03,M['ket']['en_e']+0.02),'chuong',0,700,'chuong may chu khi go xong .vn — sau chu "en" de khong de len giong')

# Thi nghiem (doi chung): BO="lat:4.0-4.6,gach:4.5-4.8" -> bo cac cu trong cua so do (khong dung khi dung that)
import os
for mau in [x for x in os.environ.get('BO','').split(',') if x]:
    kk,kt=mau.split(':'); t0,t1=map(float,kt.split('-')); E=[e for e in E if not (e[1]==kk and t0<=e[0]<=t1)]
# ===== DAT VAO BUS =====
LIEN={'to','dem','dongho','trang','gach','vut','lat','lat2'}   # tieng keo dai: ha manh khi giong noi; tieng dap ngan: ha nhe
L=np.zeros((2,N),np.float32); R=np.zeros((2,N),np.float32)
for t,k,db,x,_ in E:
    q=1 if k in LIEN else 0
    s,hit=CUT[k]; st=int(round((t-hit)*SR)); s=s*10**(db/20)
    pan=(x/1080-0.5)*0.7; gl,gr=np.cos((pan+1)*np.pi/4),np.sin((pan+1)*np.pi/4)
    a0=max(0,st); b0=min(N,st+len(s))
    if b0>a0: L[q,a0:b0]+=s[a0-st:b0-st]*gl*1.414; R[q,a0:b0]+=s[a0-st:b0-st]*gr*1.414
# ===== GIAM TIENG DONG KHI GIONG NOI (ducking) =====
g=GIONG.copy(); g=np.pad(g,(0,max(0,N-len(g))))[:N]
hop=480; nh=N//hop; env=np.sqrt(np.mean(g[:nh*hop].reshape(nh,hop)**2,axis=1)); vdb=20*np.log10(env+1e-9)
def duck(sau):                                          # giong >= -28 dBFS -> giam 'sau' dB; tan cong 20 ms, nha 160 ms
    d=-sau*np.clip((vdb+42)/14,0,1); sm=np.zeros_like(d); cur=0
    for i,x in enumerate(d):
        a=0.4 if x<cur else 0.06; cur=cur+(x-cur)*a; sm[i]=cur
    gn=np.repeat(10**(sm/20),hop); return np.pad(gn,(0,N-len(gn)),constant_values=1.0)
g0,g1=duck(2),duck(8)
L=L[0]*g0+L[1]*g1; R=R[0]*g0+R[1]*g1
np.save(B/'sfx-bus.npy',np.stack([L,R]))
mix=np.stack([g+L,g+R],axis=1).astype(np.float32)
raw=B/'am08-tho.wav'
subprocess.run(['ffmpeg','-v','error','-y','-f','f32le','-ar',str(SR),'-ac','2','-i','-','-c:a','pcm_f32le',str(raw)],input=mix.tobytes(),check=True)
# chuan hoa -14 LUFS 2 luot (tuyen tinh, khong bom)
o=subprocess.run(['ffmpeg','-v','info','-i',str(raw),'-af','loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True).stderr
js=json.loads(o[o.rindex('{'):o.rindex('}')+1])
af=f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true,aresample=48000"
subprocess.run(['ffmpeg','-v','error','-y','-i',str(raw),'-af',af,'-c:a','pcm_s24le',str(B/'am08.wav')],check=True)
# ghep: moi nen tang 1 ban hinh (hinh-<nt>.mp4 tu ghep08.py), CHUNG 1 tieng (moc thoi gian giong nhau o 3 ban — v8.3)
sys.path.insert(0,str(B.parent.parent/'cong-cu')); import ghep_am   # dung chung 3 khuon; env BAN = chi ghep ban do (CI chay 3 ban song song)
RA=ghep_am.ghep(B,B/'am08.wav',DAI)
with open(B/'cue-am08.md','w') as f:
    f.write('# Bang tieng dong ban 08 (thoi diem = khung cham tren hinh)\n\n| giay | tieng | dB | viec tren hinh |\n|---|---|---|---|\n')
    for t,k,db,x,gh in sorted(E): f.write(f'| {t:.2f} | {k} | {db:+d} | {gh} |\n')
json.dump([dict(t=t,k=k,hit=CUT[k][1]) for t,k,db,x,_ in E],open(B/'cue-am08.json','w'))
print(len(E),'cu tieng ->',RA,'| do lan 1:',js['input_i'],'LUFS')
