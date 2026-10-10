#!/usr/bin/env python3
"""Bo sung manifest.json cho khuon KHONG co sau-manifest.py rieng (Tin nhanh): loi_dang <- loi-dang.json, kiem_lai <- kiem-lai.json (neu co).
  python3 cong-cu/sau_manifest_chung.py <thu-muc-khuon> <out/manifest.json>
manifest.py chi biet top5.json; moi dang them du lieu rieng qua 2 tep nay. Co loi-dang.json -> kiem hop dong (tit <= 100, mo ta <= 2000, link Sang Game,
hashtag co #SănGame). Co kiem-lai.json -> moi muc phai du pid + loc + gia_cuc_bo + endTime (may dang fail-closed neu thieu)."""
import json,pathlib,sys
K=pathlib.Path(sys.argv[1]); M=pathlib.Path(sys.argv[2])
m=json.load(open(M,encoding='utf-8')); lam=[]
if (K/'loi-dang.json').exists():
    ld=json.load(open(K/'loi-dang.json',encoding='utf-8'))
    assert 0<len(ld['tieu_de'])<=100 and 0<len(ld['mo_ta'])<=2000 and ld['link'].startswith('https://sangame.com.vn') and '#SănGame' in ld['hashtag'],ld
    m['loi_dang']=ld; lam.append('loi_dang')
if (K/'kiem-lai.json').exists():
    kl=json.load(open(K/'kiem-lai.json',encoding='utf-8'))
    for x in kl: assert x.get('pid') and x.get('loc') and isinstance(x.get('gia_cuc_bo'),(int,float)) and x.get('endTime'),x
    m['kiem_lai']=kl; lam.append(f'kiem_lai({len(kl)})')
json.dump(m,open(M,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('sau_manifest_chung:',', '.join(lam) or 'khong co loi-dang.json / kiem-lai.json - giu mac dinh cua manifest.py')
