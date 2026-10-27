# Bo sung manifest.json Flagship: loi_dang, noi_bat, kiem_lai (dang/gia.py doc), nhan.
#   python3 sau-manifest.py <out/manifest.json>
import json,pathlib,sys
M=pathlib.Path(sys.argv[1]); T=pathlib.Path(__file__).resolve().parent
L=T/'loi-dang.json'; F=T/'flagship.json'
if not L.exists() or not F.exists(): print('khong co loi-dang.json/flagship.json - giu manifest mac dinh'); sys.exit(0)
m=json.load(open(M,encoding='utf-8')); ld=json.load(open(L,encoding='utf-8')); f=json.load(open(F,encoding='utf-8')); cfg=json.load(open(T/'cau-hinh.json',encoding='utf-8'))
assert 0<len(ld['tieu_de'])<=100 and 0<len(ld['mo_ta'])<=2000 and ld['link'].startswith('https://sangame.com.vn') and ld['hashtag']==['#SănGame','#PlayStation','#PS5','#GiảmGiá'],ld
m['loi_dang']=ld
m['noi_bat']=[dict(ten=f['ten_goc'],pids=[f['pid']])]   # cong-cu/da_noi_bat.py
m['kiem_lai']=[dict(ten=f['ten'],pid=f['pid'],loc=f['loc'],gia_vnd=f['gia_vnd'],gia_cuc_bo=f['gia_cuc_bo'],tien_te=f['tien_te'],endTime=f['endTime'])]
moc=f.get('moc') or {}
nguon=f"keo:{(f.get('keo') or {}).get('hang')}"
if moc.get('loai') in ('tin','thap_nhat'): nguon+=f"+moc:{moc['loai']}"+(f":{moc['nguon']}" if moc.get('nguon') else '')
m['nhan']=dict(chu_de=f['ten_goc'],khuon='flagship',mo=f"k{cfg['kieu_mo']}",nguon=nguon)
json.dump(m,open(M,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('manifest <- flagship:',ld['tieu_de'])
