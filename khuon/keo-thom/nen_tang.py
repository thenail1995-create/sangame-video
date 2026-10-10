# Bố cục THEO NỀN TẢNG cho khuôn tạp chí (Hào 10/10: "vậy thay đổi cho phù hợp từng nền tảng"; LOI-SAI N12).
# nen-tang.json: tren = mép dưới vùng app che phía trên (TikTok 240 / Reels 269 / Shorts 288), duoi = mép trên vùng app phía dưới.
# Giấy đầu trang bắt đầu ở tren+6; dải gọn của khuôn Kèo thơm cao tới tren+158 -> trailer NÉT bắt đầu ở S = tren+146
# (giấy che mép nối 12 px). Phía trên S là chính trailer đó phóng to, làm mờ, tối 50%.
import json,pathlib
KHUON=pathlib.Path(__file__).resolve().parent
NT=json.load(open(KHUON/'nen-tang.json'))
DAI_GON=146   # S - tren cua khuon nay (Top 5 la 104 vi dai gon chi 1 hang)
GRADE="eq=saturation=0.78:contrast=1.06,curves=r='0/0.07 1/0.98':g='0/0.05 1/0.94':b='0/0.03 1/0.84',noise=alls=8:allf=t"
def chon(args):   # tach ten nen tang khoi tham so dong lenh; 'tat-ca' = ca 3
    du=[a for a in args if a in NT or a=='tat-ca']; con=[a for a in args if a not in NT and a!='tat-ca']
    return (list(NT) if (du and du[0]=='tat-ca') else (du or ['tiktok'])), con
def cao(nt): return (1920-(NT[nt]['tren']+DAI_GON))//2*2   # chieu cao mang trailer net (chan)
def loc_nen(nt):  # [0:v] = nen-<nt>.mp4 (1080 x cao) -> khung 1080x1920 da chinh mau, nhan [b]
    H=cao(nt); S=1920-H; WB=int(1080*1920/H)//2*2
    # setsar=1 sau moi scale doi ti le (LOI-SAI K11: SAR 14400:14381)
    return (f"[0:v]split[s][m];[m]scale={WB}:1920,setsar=1,crop=1080:1920,scale=270:480,boxblur=6:2,scale=1080:1920,setsar=1,"
            f"colorchannelmixer=rr=.5:gg=.5:bb=.5,eq=saturation=0.8[mo];[mo][s]overlay=0:{S},{GRADE},setsar=1[b]")
def nt_js(nt): return dict(ma=nt,ten=NT[nt]['ten'],tren=NT[nt]['tren'],duoi=NT[nt]['duoi'],S=1920-cao(nt))
