# Bo sung manifest.json cua Top 5 che do tu dong: loi_dang (tit/mo ta/hashtag/link) lay tu loi-dang.json do chon-top5.py sinh (moi so tu du lieu).
#   python3 sau-manifest.py <out/manifest.json>
import json,pathlib,sys
M=pathlib.Path(sys.argv[1]); L=pathlib.Path(__file__).resolve().parent/'loi-dang.json'
if not L.exists(): print('khong co loi-dang.json - giu loi_dang mac dinh cua manifest.py'); sys.exit(0)
m=json.load(open(M,encoding='utf-8')); ld=json.load(open(L,encoding='utf-8'))
assert 0<len(ld['tieu_de'])<=100 and 0<len(ld['mo_ta'])<=2000 and ld['link'].startswith('https://sangame.com.vn') and ld['hashtag']==['#SănGame','#PlayStation','#PS5','#GiảmGiá'],ld
m['loi_dang']=ld
json.dump(m,open(M,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('manifest.loi_dang <- loi-dang.json:',ld['tieu_de'])
