# So video v9 voi video v8.3 DUNG TU CUNG FIXTURE: SSIM tai cac moc (135x240 va 270x480) + cac cu tieng (cue-am08.json) tung cu mot.
#   python3 so-hai-ban.py <video-moi.mp4> <video-cu.mp4> <nen-tang> <moc,moc,...> [cue-moi.json cue-cu.json]
# THOAT 1 (Sol bcd #20) khi: min SSIM 135x240 < 0,985 · so cue khac nhau · loai tieng cua cue khac nhau · |lech cue| > 34 ms. Thoat 0 chi khi dat het.
import subprocess,sys,re,json,pathlib,tempfile
NGUONG_SSIM=0.985; NGUONG_CUE_MS=34
def danh_gia(kq,cm=None,cc=None):
    """kq = [(moc, ssim135x240, ssim270x480)]; cm/cc = danh sach cue moi/cu ({t,k}) hoac None (khong so cue). -> (dong in, danh sach LOI); LOI rong = DAT."""
    loi=[]; dong=[]
    mn=min(x[1] for x in kq) if kq else 0.0
    if not kq: loi.append('khong co moc nao de so SSIM')
    elif mn<NGUONG_SSIM: loi.append(f'SSIM 135x240 thap nhat {mn:.4f} < {NGUONG_SSIM} (moc {[f"{x[0]:g}s={x[1]:.4f}" for x in kq if x[1]<NGUONG_SSIM]})')
    if cm is not None and cc is not None:
        cm=sorted(cm,key=lambda c:c['t']); cc=sorted(cc,key=lambda c:c['t'])
        dong.append(f'  cue tieng: moi {len(cm)} cu, cu {len(cc)} cu')
        if len(cm)!=len(cc): loi.append(f'SO CUE KHAC NHAU: moi {len(cm)} · cu {len(cc)}')
        else:
            d=[round((x['t']-y['t'])*1000) for x,y in zip(cm,cc)]; kk=[(round(x['t'],2),x['k'],y['k']) for x,y in zip(cm,cc) if x['k']!=y['k']]
            if d: dong.append(f'  lech cue moi - cu: min {min(d)} ms, max {max(d)} ms, |TB| {sum(map(abs,d))/len(d):.1f} ms; khac loai tieng: {len(kk)}')
            xau=[(x['k'],round(x['t'],2),dd) for x,dd in zip(cm,d) if abs(dd)>NGUONG_CUE_MS]
            dong.append(f'  cue lech > {NGUONG_CUE_MS} ms: '+(str(xau) if xau else 'khong'))
            if kk: loi.append(f'{len(kk)} cue khac loai tieng (t, moi, cu): {kk}')
            if xau: loi.append(f'{len(xau)} cue lech > {NGUONG_CUE_MS} ms: {xau}')
    return dong,loi
def chay(moi,cu,nt,mocs,cue_moi=None,cue_cu=None):
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
    cm=json.load(open(cue_moi)) if cue_moi else None; cc=json.load(open(cue_cu)) if cue_cu else None
    dong,loi=danh_gia(kq,cm,cc)
    for x in dong: print(x)
    if loi:
        for x in loi: print('TRUOT:',x)
        return 1
    print(f'DAT: SSIM >= {NGUONG_SSIM}'+(f', cue khop (<= {NGUONG_CUE_MS} ms, cung loai)' if cm is not None else ''))
    return 0
if __name__=='__main__':
    moi,cu,nt,mocs=sys.argv[1],sys.argv[2],sys.argv[3],[float(x) for x in sys.argv[4].split(',')]
    sys.exit(chay(moi,cu,nt,mocs,*(sys.argv[5:7] if len(sys.argv)>6 else (None,None))))
