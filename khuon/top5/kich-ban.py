# Lời đọc Top 5 từ top5.json — số viết bằng CHỮ (máy đọc số dễ sai, LOI-SAI N7/skill reel-giong-doc).
#   python3 kich-ban.py  -> loi.txt (có thẻ cảm xúc eleven_v3) + kich-ban.json (lời từng đoạn để căn mốc chữ)
import json,re,pathlib
T=pathlib.Path(__file__).resolve().parent
top=json.load(open(T/'top5.json'))
SO=['không','một','hai','ba','bốn','năm','sáu','bảy','tám','chín']
def so_chu(n):
    """0..999 -> chữ: 112 'một trăm mười hai', 105 'một trăm lẻ năm', 75 'bảy mươi lăm', 21 'hai mươi mốt', 15 'mười lăm'."""
    tr,ch,dv=n//100,(n//10)%10,n%10; o=[]
    if tr: o.append(SO[tr]+' trăm')
    if ch==0:
        if dv: o.append(('lẻ ' if tr else '')+SO[dv])
    else:
        o.append('mười' if ch==1 else SO[ch]+' mươi')
        if dv==1 and ch>1: o.append('mốt')
        elif dv==5: o.append('lăm')
        elif dv==4 and ch>1: o.append('tư')
        elif dv: o.append(SO[dv])
    return ' '.join(o) if o else 'không'
def nghin(gia):   # '167.000đ' -> 'một trăm sáu mươi bảy nghìn'
    return so_chu(int(gia.replace('.','').replace('đ',''))//1000)+' nghìn'
TEN={'Mafia: Definitive Edition for PS5®':'Mafia bản làm lại','Mortal Kombat 11':'Mortal Kombat mười một',
     'Little Nightmares Complete Edition':'Little Nightmares bản đầy đủ','Outlast full game':'Outlast','Steelrising':'Steelrising'}
VUNG={'Hồng Kông':'Hồng Kông','Indonesia':'Indo','Mỹ':'Mỹ','Singapore':'Sing','Thái Lan':'Thái'}
HANG=['một','hai','ba','bốn','năm']
doan=[('mo','[excited] Top năm game bán chạy đang dưới hai trăm nghìn nè anh em!')]
for i in range(4,-1,-1):
    g=top[i]; ten=TEN.get(g['ten'],g['ten']); gia=nghin(g['gia']); giam=so_chu(g['giam'])+' phần trăm'
    if i==4: c=f"Hạng năm: {ten}, giảm {giam}, còn {gia}."
    elif i==3: c=f"Hạng bốn: {ten}, giảm {giam}, {gia} ở store {VUNG[g['vung']]}."
    elif i==2: c=f"Hạng ba: {ten}, {gia}."
    elif i==1: c=f"Hạng hai: {ten}, giảm {giam}, chỉ {gia}!"
    else: c=f"[excited] Và hạng một: {ten}, {gia} ở {VUNG[g['vung']]}!"
    doan.append((f'h{i+1}',c))
CFG=json.load(open(T/'cau-hinh.json'))   # con_lai = tong - 5 (LOI-SAI D8: 'con ... nua' phai TRU 5 game da noi)
doan.append(('ket',f"Còn {so_chu(CFG['con_lai'])} game nữa dưới {so_chu(CFG['muc']//1000)} nghìn, tra ở Săn Game chấm com chấm vi en!"))
loi=' '.join(c for _,c in doan)
(T/'loi.txt').write_text(loi,encoding='utf-8')
json.dump([dict(k=k,loi=re.sub(r'\[[^\]]*\]\s*','',c)) for k,c in doan],open(T/'kich-ban.json','w'),ensure_ascii=False,indent=1)
print(loi); print(len(loi),'ky tu')
