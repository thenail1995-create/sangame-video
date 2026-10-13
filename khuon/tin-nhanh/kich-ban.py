# Lời đọc Tin nhanh từ tin.json — số viết bằng CHỮ (LOI-SAI N7); tên khó đọc (EDF) chỉ hiện trên hình, không đọc.
#   python3 kich-ban.py  -> loi.txt (có thẻ cảm xúc eleven_v3) + kich-ban.json (lời từng đoạn để căn mốc chữ)
# 13/10 (Sol soi #1-#3): `mo` mở bằng DEAL THẬT (tin.json.mo_du_lieu = deal rẻ nhất mục giảm sâu), không còn «Bản tin sáng Săn Game, <ngày>!» (tên kênh + ngày ở 3 giây đầu);
#   `ket` = «Theo dõi Săn Game để không lỡ kèo nào nha!» (hình cuối hiện @sangamecomvn). Ngày vẫn nằm trên hình/giấy/tin.json.
import json,re,pathlib,sys
T=pathlib.Path(__file__).resolve().parent; sys.path.insert(0,str(T))
import so_chu as sc
D=json.load(open(T/'tin.json'))
MO_CHUNG="[excited] Sáng nay PS Store có deal mới nè anh em!"
KET="[excited] Theo dõi Săn Game để không lỡ kèo nào nha!"
def cau_mo(md):
    """md = tin.json.mo_du_lieu {ten_doc, gia_vnd, giam}; thiếu / sai kiểu -> câu mở chung (không đoán)."""
    try:
        if not isinstance(md,dict): return MO_CHUNG
        ten=md.get('ten_doc'); gia=md['gia_vnd']; giam=md['giam']
        if not (isinstance(ten,str) and ten.strip() and isinstance(gia,int) and gia>0 and isinstance(giam,int) and 0<giam<=100): return MO_CHUNG
        return f"[excited] {ten.strip()} còn {sc.so_ra_chu(gia)}, giảm {sc.so_ra_chu(giam)} phần trăm, sáng nay PS Store có deal mới nè!"
    except (TypeError,KeyError): return MO_CHUNG
doan=[('mo',cau_mo(D.get('mo_du_lieu')))]
for i,g in enumerate(D['tin'],1): doan.append((f't{i}',g['loi']))
doan.append(('ket',KET))
loi=' '.join(c for _,c in doan)
(T/'loi.txt').write_text(loi,encoding='utf-8')
json.dump([dict(k=k,loi=re.sub(r'\[[^\]]*\]\s*','',c)) for k,c in doan],open(T/'kich-ban.json','w'),ensure_ascii=False,indent=1)
print(loi); print(len(loi),'ky tu')
