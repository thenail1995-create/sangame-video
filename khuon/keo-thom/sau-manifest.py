# Bo sung manifest.json cua Keo thom (che do tu dong): loi_dang + kiem_lai lay tu keo.json (manifest.py chi biet top5.json). Tu choi mau hoi quy.
#   python3 sau-manifest.py <out/manifest.json>
import json,pathlib,sys
M=pathlib.Path(sys.argv[1]); K=pathlib.Path(__file__).resolve().parent/'keo.json'
if not K.exists(): sys.exit('THIEU keo.json — khong bo sung duoc manifest')
k=json.load(open(K,encoding='utf-8'))
if k.get('che_do_hoi_quy'): sys.exit('keo.json la MAU HOI QUY (Spider-Man 2, deal da het) — KHONG tao manifest de dang')
ld=k['loi_dang']; kl=k['kiem_lai']
assert 0<len(ld['tieu_de'])<=100 and 0<len(ld['mo_ta'])<=2000 and ld['link'].startswith('https://sangame.com.vn') and ld['hashtag']==['#SănGame','#PlayStation','#PS5','#GiảmGiá'],ld
assert len(kl)==3 and all(x.get('pid') and x.get('loc') and isinstance(x.get('gia_cuc_bo'),(int,float)) and x.get('endTime') for x in kl),kl
m=json.load(open(M,encoding='utf-8')); m['loi_dang']=ld; m['kiem_lai']=kl
m['noi_bat']=[dict(ten=k['game']['ten'],pids=[x['pid'] for x in kl if x.get('pid')])]   # cong-cu/da_noi_bat.py
json.dump(m,open(M,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('manifest.loi_dang + kiem_lai (3 vung) <- keo.json:',ld['tieu_de'])
