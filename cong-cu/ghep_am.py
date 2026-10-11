#!/usr/bin/env python3
"""Ghep hinh-<nt>.mp4 + tieng (am.wav / am08.wav) -> video-<nt>.mp4 (copy hinh, AAC 192k). Dung chung 3 khuon.
  - import: ghep_am.ghep(B, wav, dai)  — am-top5.py / am-tin.py / am08.py goi ngay sau khi tron tieng (bo qua ban nao chua co hinh-<nt>.mp4)
  - dong lenh (CI job `ban`, mot ban): BAN=reels python3 cong-cu/ghep_am.py khuon/top5 am.wav   -> THIEU hinh = loi (khong bo qua)
Env BAN (tiktok|reels|shorts) = chi ghep ban do; khong dat = ca 3 (Mac)."""
import json,os,pathlib,subprocess,sys
def danh_sach_ban(B):
    tat_ca=list(json.load(open(B/'nen-tang.json')))
    ban=os.environ.get('BAN','')
    if not ban: return tat_ca
    if ban not in tat_ca: raise SystemExit(f'BAN khong hop le: {ban}')
    return [ban]
def ghep(B,wav,dai,nts=None,bat_buoc=False):
    B=pathlib.Path(B); wav=pathlib.Path(wav); ra_ds=[]
    for nt in (nts or danh_sach_ban(B)):
        hinh=B/f'hinh-{nt}.mp4'
        if not hinh.exists():
            if bat_buoc: raise SystemExit(f'THIEU {hinh.name} - khong ghep duoc ban {nt}')
            continue
        ra=str(B/f'video-{nt}.mp4'); ra_ds.append(ra)
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(hinh),'-i',str(wav),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-t',str(dai),'-movflags','+faststart',ra],check=True)
    return ra_ds
def dai_cua_khuon(B):
    sys.path.insert(0,str(B))
    try:
        import thoi_luong; return thoi_luong.dai()   # Keo thom: do dai giong + 1,23 s
    except ImportError:
        return json.load(open(B/'canh.json'))[-1]['b']    # Top 5 / Tin nhanh
if __name__=='__main__':
    B=pathlib.Path(sys.argv[1]).resolve(); wav=B/(sys.argv[2] if len(sys.argv)>2 else 'am.wav')
    ra=ghep(B,wav,dai_cua_khuon(B),bat_buoc=True); print('ghep',ra)
