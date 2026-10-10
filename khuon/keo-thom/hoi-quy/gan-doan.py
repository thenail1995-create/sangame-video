# Mau hoi quy v8.3: moc-chu.json cu KHONG co khoa doan (va co phan tu khoang trang). Gan khoa doan theo kich-ban.json (cung chu, cung thu tu) de v9 chay duoc
# voi GIONG + MOC CU. Loi neu chu khong khop (nghia la kich-ban.py khong tai tao dung loi cu).
#   python3 gan-doan.py <moc-chu-cu.json> <kich-ban.json> <ra moc-chu.json>
import json,sys,unicodedata,re
cu=[w for w in json.load(open(sys.argv[1])) if w['w'].strip()]; kb=json.load(open(sys.argv[2]))['doan']
def ch(t): return re.sub(r'[^a-z0-9]','',''.join(c for c in unicodedata.normalize('NFD',t.lower()) if unicodedata.category(c)!='Mn').replace('đ','d'))
goc=[(d['k'],w) for d in kb for w in d['loi'].split()]
if len(goc)!=len(cu): sys.exit(f'LOI: {len(goc)} chu kich ban != {len(cu)} chu moc cu')
sai=[(k,w,c['w']) for (k,w),c in zip(goc,cu) if ch(w)!=ch(c['w'])]
if sai: sys.exit(f'LOI: chu khong khop: {sai[:5]}')
json.dump([dict(w=c['w'],s=c['s'],e=c['e'],doan=k) for (k,_),c in zip(goc,cu)],open(sys.argv[3],'w'),ensure_ascii=False,indent=0)
print('gan doan:',len(cu),'chu ->',sys.argv[3])
