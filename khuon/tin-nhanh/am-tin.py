# Tieng Tin nhanh (chep tu am-top5.py, khuon tieng ban 08 — lam lai 10/10 sau khi Hao che "am thanh chua khop").
# Loi cu: file tieng dong ElevenLabs KHONG dap o dau file (dau-nhe dap o 0,60 s, giay-vut/lat-trang dinh ~0,46-0,5 s)
# ma cue dat DAU FILE vao luc hinh bat dau chuyen dong -> tieng tre ~0,5 s; do to cac file lech 36 dB.
# Cach moi: cat tung file DUNG CU DAP, chuan hoa do to, dat CU DAP trung KHUNG CHAM tinh tu cong thuc chuyen dong
# cua full.html (cung W(), cung hang so), giam tieng dong khi giong dang noi (ducking), chuan hoa -14 LUFS.
#   python3 am08.py            -> am08.wav + cue-am08.md + san-game-mau-08.mp4 (giu nguyen hinh, thay tieng)
import json,subprocess,numpy as np,pathlib,sys
B=pathlib.Path(__file__).resolve().parent; V=B/'dau-vao'
import pathlib
A=str(pathlib.Path(__file__).resolve().parent/'am-thanh')+'/'; MM=A   # thu vien tieng dong chep vao khuon (giay phep: am-thanh/NGUON.md)
SR=48000; DAI=json.load(open(pathlib.Path(__file__).resolve().parent/'canh.json'))[-1]['b']; N=int(DAI*SR)
m=[w for w in json.load(open(V/'moc-chu.json')) if w['w'].strip()]; W=lambda i:m[i]['s']

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
K=json.load(open(B/'khung.json')); F=len(K); FPS=30; SOM=0.010
CANH={c['k']:c for c in json.load(open(B/'canh.json'))}
def cham(key):      # khung dau tien vat hien va co <= 1.03 (dau, so hang, gia...)
    for f in range(1,F):
        x=K[f][key]
        if x and x[0]<=1.03: return f/FPS
def dap_xuong(key): # the/bia bay vao: khung dau tien da dung yen (dich chuyen < 4 px)
    for f in range(1,F):
        x=K[f][key]
        if x and abs(x[1])<4 and abs(x[2])<4: return f/FPS
def nhanh_nhat(lo,hi):
    fs=[f for f in range(1,F) if lo<=f/FPS<=hi]; return max(fs,key=lambda f:abs(K[f]['H']-K[f-1]['H']))/FPS
E=[]
def cu(t,k,db=0,x=540,ghi='',hinh=None): E.append((round(t,3),k,db,x,ghi,hinh))
def dap(t,k,db,x,ghi):
    if t is not None: cu(t-SOM,k,db,x,ghi+' (khung cham do duoc)',t)
# mo dau: 3 manh muc luc dap xuong, bia gap thanh dai dau trang
for i in range(3): dap(cham(f'm{i}'),'dau',-10,540,f'muc luc tin {i+1} dap xuong')
cu(nhanh_nhat(CANH['t1']['a']-0.45,CANH['t1']['a']+0.3),'lat2',-1,540,'bia gap thanh dai dau trang (khoang nghi)')
for r in (1,2,3):
    c=CANH[f't{r}']
    if r!=1: cu(c['a']-0.2,'lat2',-2,540,f'lat sang tin {r} (khoang nghi tho)')
    dap(cham(f'dau{r}'),'dap',0,540,f'con dau loai tin {r} dap giua khung (truoc chu Tin)')
    ve=dap_xuong(f'dauW{r}')   # con dau bay ve goc manh bao: tieng vut nhe, dinh truoc luc cham 0,12 s
    if ve: cu(ve-0.12,'vut',-8,760,f'con dau tin {r} ve goc manh bao')
    # bia game hien: KHONG tieng (lan 1: cu dau -7 dB dap dung chu 'F1', 'Hunt' -> Whisper nghe 'app 125', 'handshow' — LOI-SAI A8)
    if r==2:
        dap(cham('gm2'),'dau',-12,800,'nhan -85% (nho: roi vao giua ten game)')
        g=cham('g2'); dap(g,'dap',-3,800,'gia re nhat dong dau (khoang nghi truoc chu hai)')   # bo ka-ching: ngan 0,9 s de len 'hai tram...'
    if r==3: dap(cham('g3'),'dap',-3,800,'moc ra mat 01/2027')
cu(nhanh_nhat(CANH['ket']['a'],CANH['ket']['a']+0.6),'lat2',+1,540,'trang bang xep hang phu xuong')
for i in range(3): dap(cham(f'dk{i}'),'dau',-10,300,f'dong {i+1} trang ket')
go=[f/FPS for f in range(1,F) if K[f]['url']>K[f-1]['url']]
for j,t in enumerate(go): cu(t-SOM,'go' if j%2 else 'go2',-7,420,f'go chu {j+1}',t)
dap(cham('logo3'),'dap',-6,780,'logo dan len')
cu(m[-1]['e']+0.02,'chuong',0,700,'chuong sau chu cuoi')

# Thi nghiem (doi chung): BO="lat:4.0-4.6,gach:4.5-4.8" -> bo cac cu trong cua so do (khong dung khi dung that)
import os
for mau in [x for x in os.environ.get('BO','').split(',') if x]:
    kk,kt=mau.split(':'); t0,t1=map(float,kt.split('-')); E=[e for e in E if not (e[1]==kk and t0<=e[0]<=t1)]
# ===== DAT VAO BUS =====
LIEN={'to','dem','dongho','trang','gach','vut','lat','lat2'}   # tieng keo dai: ha manh khi giong noi; tieng dap ngan: ha nhe
L=np.zeros((2,N),np.float32); R=np.zeros((2,N),np.float32)
for t,k,db,x,_,_h in E:
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
raw=B/'am-tho.wav'
subprocess.run(['ffmpeg','-v','error','-y','-f','f32le','-ar',str(SR),'-ac','2','-i','-','-c:a','pcm_f32le',str(raw)],input=mix.tobytes(),check=True)
# chuan hoa -14 LUFS 2 luot (tuyen tinh, khong bom)
o=subprocess.run(['ffmpeg','-v','info','-i',str(raw),'-af','loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True).stderr
js=json.loads(o[o.rindex('{'):o.rindex('}')+1])
af=f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true,aresample=48000"
subprocess.run(['ffmpeg','-v','error','-y','-i',str(raw),'-af',af,'-c:a','pcm_s24le',str(B/'am.wav')],check=True)
# ghep: moi nen tang 1 ban hinh (hinh-<nt>.mp4 tu dung.py hinh), CHUNG 1 tieng (moc thoi gian giong nhau o 3 ban)
RA=[]
for nt in json.load(open(B/'nen-tang.json')):
    HINH=B/f'hinh-{nt}.mp4'
    if not HINH.exists(): continue
    ra=str(B/f'video-{nt}.mp4'); RA.append(ra)
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(HINH),'-i',str(B/'am.wav'),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-t',str(DAI),'-movflags','+faststart',ra],check=True)
with open(B/'cue-am.md','w') as f:
    f.write('# Bang tieng dong Tin nhanh (thoi diem = khung cham tren hinh; chung cho TikTok/Reels/Shorts)\n\n| giay | tieng | dB | viec tren hinh |\n|---|---|---|---|\n')
    for t,k,db,x,gh,_h in sorted(E): f.write(f'| {t:.2f} | {k} | {db:+d} | {gh} |\n')
json.dump([dict(t=t,k=k,hit=CUT[k][1],hinh=h) for t,k,db,x,_,h in E],open(B/'cue-am.json','w'))
print(len(E),'cu tieng ->',RA,'| do lan 1:',js['input_i'],'LUFS')
