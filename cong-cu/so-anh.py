# So anh tinh (A6): 5 moc/ban cua video moi voi anh tham chieu cua ban Mac (SSIM). Anh Mac luu o 270x480 PNG; so o 270x480 (area) de hat nhieu phim (noise=alls=8) khong lam thap SSIM trong fixture (ref/).
#   python3 so-anh.py <video.mp4> <thu-muc-ref> <nen-tang> [nguong=0.97]   (ref/<nen-tang>_<t>.png, t = moc giay)
# In SSIM tung moc + min; exit 1 neu min < nguong. Dung ffmpeg filter ssim (lieu luma+chroma 'All').
import subprocess,sys,pathlib,re,json,os,shutil
vid,ref,nt=sys.argv[1],pathlib.Path(sys.argv[2]),sys.argv[3]; nguong=float(sys.argv[4]) if len(sys.argv)>4 else 0.97
fs=sorted(ref.glob(f'{nt}_*.png'),key=lambda p:float(p.stem.split('_')[1]))
if not fs: sys.exit(f'LOI: khong co anh tham chieu {ref}/{nt}_*.png')
kq=[]
for f in fs:
    t=float(f.stem.split('_')[1])
    # trich khung bang DUNG lenh da tao anh tham chieu (cung ma tran mau) roi so 2 anh PNG
    tmp=pathlib.Path(vid).parent/f'.ssim-{nt}-{t}.png'
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',vid,'-frames:v','1','-vf','scale=270:480:flags=area,setsar=1',str(tmp)],check=True)
    r=subprocess.run(['ffmpeg','-hide_banner','-v','info','-i',str(tmp),'-i',str(f),'-lavfi','ssim','-f','null','-'],capture_output=True,text=True)
    if os.environ.get('SSIM_GIU'): (pathlib.Path(os.environ['SSIM_GIU'])).mkdir(parents=True,exist_ok=True); shutil.copy(tmp,pathlib.Path(os.environ['SSIM_GIU'])/f'moi_{nt}_{t}.png')   # go loi: giu khung de nhin
    tmp.unlink()
    m=re.search(r'SSIM.*All:([\d.]+)',r.stderr)
    if not m: sys.exit(f'LOI: khong do duoc SSIM ({t}s): {r.stderr[-300:]}')
    kq.append((t,float(m.group(1))))
print(f"SSIM {nt}: "+', '.join(f'{t:g}s={s:.4f}' for t,s in kq)+f"; min {min(s for _,s in kq):.4f} (nguong {nguong})")
json.dump(dict(nt=nt,ssim=kq,min=min(s for _,s in kq),nguong=nguong),open(pathlib.Path(vid).parent/f'ssim-{nt}.json','w'))
sys.exit(0 if min(s for _,s in kq)>=nguong else 1)
