# Nen trailer ban 08: cat bo 10% duoi khung (dong chu phap ly "Not Actual Gameplay"/"Mix of gameplay..." cua Sony nam o ~93-98% chieu cao)
# + khung hinh dung den trang o chu "khoan..." (9,14 -> 9,80 s). Moc canh khop giong doc nhu ban 07.
# THEO NEN TANG (v8.3, LOI-SAI N12): moi nen tang 1 mang trailer net 1080 x cao(nt) (nen_tang.py), cat RONG hon 9:16
# de hien tron chieu cao khung trailer (van bo 10% day). python3 nen08.py [tiktok|reels|shorts|tat-ca]
import subprocess,sys,json
import pathlib
from nen_tang import KHUON,chon,cao
# Trailer + danh sach doan cat doc tu fixture/du lieu (A2: khong con duong dan tuyet doi cua Mac, khong chon tay trong code):
#   dau-vao/trailer/<ten>.mp4  va  dau-vao/nen-doan.json = [[ten_file, bat_dau_s, do_dai_s, dung_hinh(0/1), tam_cat_ngang(0-1)], ...]
# (nguon, bat dau, do dai, dung_hinh, tam cat ngang 0-1) — mau Spider-Man 2: doan hoi cat lech phai de thay mat Miles
TR=KHUON/'dau-vao'/'trailer'; ND=KHUON/'dau-vao'/'nen-doan.json'
if not ND.exists(): raise SystemExit(f'THIEU {ND} (danh sach doan trailer) — lay-tai-san.sh phai dat fixture vao khuon truoc')
S=[(str(TR/f),float(ss),float(dl),int(fz),float(xc)) for f,ss,dl,fz,xc in json.load(open(ND))]
def CROP(xc,H):
    w=f'trunc(ih*0.90*1080/{H}/2)*2'
    return f"crop={w}:trunc(ih*0.90/2)*2:min(max(iw*{xc}-{w}/2\\,0)\\,iw-{w}):0"
for nt in chon(sys.argv[1:])[0]:
    H=cao(nt); a=['ffmpeg','-v','error','-y']
    for f,s,d,fz,xc in S: a+=['-ss',str(s),'-t',str(max(d,0.1)),'-i',f]
    fc=''
    for i,(f,s,d,fz,xc) in enumerate(S):
        if fz: fc+=f'[{i}:v]{CROP(xc,H)},scale=1080:{H}:flags=lanczos,setsar=1,trim=end_frame=1,loop=loop={round(d*30)-1}:size=1,setpts=N/30/TB,hue=s=0,eq=contrast=1.15[v{i}];'
        else: fc+=f'[{i}:v]fps=30,{CROP(xc,H)},scale=1080:{H}:flags=lanczos,unsharp=5:5:0.7,setsar=1,trim=duration={d},setpts=PTS-STARTPTS[v{i}];'
    fc+=''.join(f'[v{i}]' for i in range(len(S)))+f'concat=n={len(S)}:v=1:a=0[o]'
    a+=['-filter_complex',fc,'-map','[o]','-an','-c:v','libx264','-crf','16','-pix_fmt','yuv420p',str(KHUON/f'nen-{nt}.mp4')]
    subprocess.run(a,check=True)
    print(f'nen-{nt}.mp4 1080x{H} (net tu y={1920-H}); tong', round(sum(d for _,_,d,_,_ in S),3))
