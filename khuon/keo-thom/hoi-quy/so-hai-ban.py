# So video v9 voi video v8.3 DUNG TU CUNG FIXTURE: SSIM tai cac moc (135x240 va 270x480) + cac cu tieng (cue-am08.json) tung cu mot.
#   python3 so-hai-ban.py <video-moi.mp4> <video-cu.mp4> <nen-tang> <moc,moc,...> [cue-moi.json cue-cu.json]
import subprocess,sys,re,json,pathlib,tempfile
moi,cu,nt,mocs=sys.argv[1],sys.argv[2],sys.argv[3],[float(x) for x in sys.argv[4].split(',')]
tmp=pathlib.Path(tempfile.mkdtemp(prefix='so2ban-'))
def khung(v,t,rong,cao,ra): subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',v,'-frames:v','1','-vf',f'scale={rong}:{cao}:flags=area,setsar=1',str(ra)],check=True)
def ssim(a,b,rong,cao):
    r=subprocess.run(['ffmpeg','-hide_banner','-v','info','-i',str(a),'-i',str(b),'-lavfi',f'[0:v]scale={rong}:{cao}:flags=area[a];[1:v]scale={rong}:{cao}:flags=area[b];[a][b]ssim','-f','null','-'],capture_output=True,text=True).stderr
    return float(re.search(r'SSIM.*All:([\d.]+)',r).group(1))
kq=[]
for t in mocs:
    a=tmp/f'm{t}.png'; b=tmp/f'c{t}.png'; khung(moi,t,270,480,a); khung(cu,t,270,480,b); kq.append((t,ssim(a,b,135,240),ssim(a,b,270,480)))
print(f'SSIM {nt} (video moi vs video v8.3 cung fixture): '+'; '.join(f'{t:g}s 135x240={s1:.4f} 270x480={s2:.4f}' for t,s1,s2 in kq))
print(f'  min 135x240 = {min(x[1] for x in kq):.4f} | min 270x480 = {min(x[2] for x in kq):.4f}')
if len(sys.argv)>6:
    cm=sorted(json.load(open(sys.argv[5])),key=lambda c:c['t']); cc=sorted(json.load(open(sys.argv[6])),key=lambda c:c['t'])
    print(f'  cue tieng: moi {len(cm)} cu, cu {len(cc)} cu')
    if len(cm)==len(cc):
        d=[round((x['t']-y['t'])*1000) for x,y in zip(cm,cc)]; kk=sum(1 for x,y in zip(cm,cc) if x['k']!=y['k'])
        print(f'  lech cue moi - cu: min {min(d)} ms, max {max(d)} ms, |TB| {sum(map(abs,d))/len(d):.1f} ms; khac loai tieng: {kk}')
        xau=[(x['k'],round(x['t'],2),dd) for x,dd in zip(cm,d) if abs(dd)>34]
        print('  cue lech > 34 ms:',xau if xau else 'khong')
    else: print('  SO CUE KHAC NHAU')
