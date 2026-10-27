# Loi doc Flagship tu flagship.json + cau-hinh.json -> loi.txt (co the [excited] o 'mo') + kich-ban.json (7 doan, bo the).
#   python3 kich-ban.py
import json,pathlib,sys
T=pathlib.Path(__file__).resolve().parent; sys.path.insert(0,str(T))
import loi_flagship as lf
f=json.load(open(T/'flagship.json',encoding='utf-8')); cfg=json.load(open(T/'cau-hinh.json',encoding='utf-8'))
ds=lf.doan(f,cfg['ngay_iso'])   # f['moc'].loai='khong' (da bo o buoc chon) -> khong co doan moc
assert lf.kieu_mo(cfg['ngay_iso'])==cfg['kieu_mo'],'kieu_mo trong cau-hinh lech ngay_iso'
loi=' '.join(('[excited] '+c if k=='mo' else c) for k,c in ds)
(T/'loi.txt').write_text(loi,encoding='utf-8')
json.dump([dict(k=k,loi=c) for k,c in ds],open(T/'kich-ban.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(loi); print(len(loi),'ky tu | uoc luong',round(lf.uoc_giay(ds),1),'giay')
