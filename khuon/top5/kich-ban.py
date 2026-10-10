# Lời đọc Top 5 từ top5.json — số viết bằng CHỮ (máy đọc số dễ sai, LOI-SAI N7/skill reel-giong-doc).
#   python3 kich-ban.py  -> loi.txt (có thẻ cảm xúc eleven_v3) + kich-ban.json (lời từng đoạn để căn mốc chữ)
import json,re,pathlib
T=pathlib.Path(__file__).resolve().parent
top=json.load(open(T/'top5.json'))
import sys; sys.path.insert(0,str(T)); import ten_rut_gon as tr
so_chu=tr.so_chu   # B1: dung chung voi ten_rut_gon (toi 9999)
def nghin(gia):   # '167.000đ' -> 'một trăm sáu mươi bảy nghìn'
    return so_chu(int(gia.replace('.','').replace('đ',''))//1000)+' nghìn'
ten_doc=tr.ten_doc_cua; vung_doc=tr.vung_doc_cua
HANG=['một','hai','ba','bốn','năm']
CFG=json.load(open(T/'cau-hinh.json'))   # muc, con_lai = tong - 5 (LOI-SAI D8: 'con ... nua' phai TRU 5 game da noi)
doan=[('mo',f"[excited] Top năm game bán chạy đang dưới {so_chu(CFG['muc']//1000)} nghìn nè anh em!")]
for i in range(4,-1,-1):
    g=top[i]; ten=ten_doc(g); gia=nghin(g['gia']); giam=so_chu(g['giam'])+' phần trăm'
    if i==4: c=f"Hạng năm: {ten}, giảm {giam}, còn {gia}."
    elif i==3: c=f"Hạng bốn: {ten}, giảm {giam}, {gia} ở store {vung_doc(g)}."
    elif i==2: c=f"Hạng ba: {ten}, {gia}."
    elif i==1: c=f"Hạng hai: {ten}, giảm {giam}, chỉ {gia}!"
    else: c=f"[excited] Và hạng một: {ten}, {gia} ở {vung_doc(g)}!"
    doan.append((f'h{i+1}',c))
doan.append(('ket',f"Còn {so_chu(CFG['con_lai'])} game nữa dưới {so_chu(CFG['muc']//1000)} nghìn, tra ở Săn Game chấm com chấm vi en!"))
loi=' '.join(c for _,c in doan)
(T/'loi.txt').write_text(loi,encoding='utf-8')
json.dump([dict(k=k,loi=re.sub(r'\[[^\]]*\]\s*','',c)) for k,c in doan],open(T/'kich-ban.json','w'),ensure_ascii=False,indent=1)
print(loi); print(len(loi),'ky tu')
