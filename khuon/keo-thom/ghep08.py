# Ghep hinh khuon Keo thom v9 (v8.3) THEO NEN TANG: trailer net (nen-<nt>.mp4) tu y=S + trailer mo toi phia tren + chinh mau bao in
# + lop do hoa alpha (lop-<nt>.mov) -> hinh-<nt>.mp4 (CHI hinh; tieng do am08.py tao va ghep).
#   python3 ghep08.py [tiktok|reels|shorts|tat-ca]
import subprocess,sys
from nen_tang import KHUON as B,chon,loc_nen
import thoi_luong
DAI=thoi_luong.dai()
for nt in chon(sys.argv[1:])[0]:
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(B/f'nen-{nt}.mp4'),'-i',str(B/f'lop-{nt}.mov'),'-filter_complex',
        loc_nen(nt)+";[b][1:v]overlay=0:0:format=auto,format=yuv420p,setparams=colorspace=bt709:color_trc=bt709:color_primaries=bt709:range=tv[v]",
        '-map','[v]','-t',str(DAI),'-c:v','libx264','-crf','19','-maxrate','14M','-bufsize','28M','-preset','medium','-profile:v','high','-pix_fmt','yuv420p',
        '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-movflags','+faststart',str(B/f'hinh-{nt}.mp4')],check=True)
    print('xong hinh',nt)
