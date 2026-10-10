# Lời đọc Tin nhanh từ tin.json — số viết bằng CHỮ (LOI-SAI N7); tên khó đọc (EDF) chỉ hiện trên hình, không đọc.
#   python3 kich-ban.py  -> loi.txt (có thẻ cảm xúc eleven_v3) + kich-ban.json (lời từng đoạn để căn mốc chữ)
import json,re,pathlib
T=pathlib.Path(__file__).resolve().parent
D=json.load(open(T/'tin.json'))
doan=[('mo',f"[excited] Bản tin sáng Săn Game, {D['ngay_doc']}!")]
for i,g in enumerate(D['tin'],1): doan.append((f't{i}',g['loi']))
doan.append(('ket',"[excited] Chi tiết ở Săn Game chấm com chấm vi en!"))
loi=' '.join(c for _,c in doan)
(T/'loi.txt').write_text(loi,encoding='utf-8')
json.dump([dict(k=k,loi=re.sub(r'\[[^\]]*\]\s*','',c)) for k,c in doan],open(T/'kich-ban.json','w'),ensure_ascii=False,indent=1)
print(loi); print(len(loi),'ky tu')
