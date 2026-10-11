#!/usr/bin/env python3
"""Bo sung manifest.json cho khuon KHONG co sau-manifest.py rieng (Tin nhanh): loi_dang <- loi-dang.json, kiem_lai <- kiem-lai.json (neu co).
  python3 cong-cu/sau_manifest_chung.py <thu-muc-khuon> <out/manifest.json>
manifest.py chi biet top5.json; moi dang them du lieu rieng qua 2 tep nay. Co loi-dang.json -> kiem hop dong (tit <= 100, mo ta <= 2000, link Sang Game,
hashtag co #SănGame). Co kiem-lai.json -> moi muc phai du pid + loc + gia_cuc_bo + endTime (may dang fail-closed neu thieu).
Co tin.json (Tin nhanh) -> MOI THE CO GIA tren hinh phai co DUNG 1 ban ghi kiem_lai (khop pid + loc + gia_vnd), du truong; thieu / rong / trung -> loi (Sol #13)."""
import json,pathlib,sys
TRUONG_SO=('gia_cuc_bo',)
VUNG_LOC={'SG':'en-sg','HK':'en-hk','US':'en-us','ID':'en-id','TH':'en-th','IN':'en-in'}
TRUONG_DONG_NHAT=('gia_vnd','gia_cuc_bo','tien_te','endTime')
def khu_trung(kl):
    """Nhieu the co the chia chung game => kiem-lai co ban ghi trung (pid,loc). Dong nhat moi truong (TRUONG_DONG_NHAT) thi gop con 1; khac nhau => loi. -> (list da khu, list loi)"""
    ra=[]; loi=[]; thay={}
    for x in kl:
        k=(x.get('pid'),x.get('loc'))
        if k not in thay: thay[k]=x; ra.append(x); continue
        y=thay[k]; kh=[f for f in TRUONG_DONG_NHAT if str(x.get(f))!=str(y.get(f))]
        if kh: loi.append(f'kiem_lai {k[0]}/{k[1]}: ban ghi trung khac nhau o {", ".join(kh)}')
    return ra,loi
def loi_kiem_lai(tin,kl):
    """tin = tin.json (dict), kl = kiem-lai.json (list). -> list loi (rong = hop le). The co gia = tin mau 'do'."""
    kl,loi=khu_trung(kl)
    for i,g in enumerate(tin.get('tin',[]),1):
        if g.get('mau')!='do': continue
        tg=(g.get('kiem') or {}).get('the_gia')
        if not tg or not tg.get('pid') or not tg.get('loc'): loi.append(f'the {i} ({g.get("ten_re")}): tin.json thieu kiem.the_gia (pid/loc)'); continue
        vz=(g.get('kiem') or {}).get('vung')
        if VUNG_LOC.get(vz)!=tg['loc']: loi.append(f'the {i} ({g.get("ten_re")}): the_gia.loc {tg["loc"]} khong khop vung {vz} (can {VUNG_LOC.get(vz)})'); continue
        kh=[x for x in kl if x.get('pid')==tg['pid'] and x.get('loc')==tg['loc']]
        if len(kh)!=1: loi.append(f'the {i} ({g.get("ten_re")}): {len(kh)} ban ghi kiem_lai cho {tg["pid"]}/{tg["loc"]} (can DUNG 1)'); continue
        x=kh[0]
        if not isinstance(x.get('gia_vnd'),int) or x['gia_vnd']<=0 or x['gia_vnd']!=tg.get('gia_vnd'): loi.append(f'the {i}: kiem_lai.gia_vnd {x.get("gia_vnd")} != the {tg.get("gia_vnd")}')
        gia_tren_hinh=int(''.join(c for c in str(g.get('gia','')) if c.isdigit()) or 0)
        if abs(gia_tren_hinh-(tg.get('gia_vnd') or 0))>1000: loi.append(f'the {i}: gia tren hinh {g.get("gia")} lech gia_vnd the_gia {tg.get("gia_vnd")}')
        if not isinstance(x.get('gia_cuc_bo'),(int,float)) or x['gia_cuc_bo']<=0: loi.append(f'the {i}: kiem_lai thieu gia_cuc_bo')
        if not x.get('tien_te'): loi.append(f'the {i}: kiem_lai thieu tien_te')
        if not str(x.get('endTime') or '').isdigit(): loi.append(f'the {i}: kiem_lai thieu/sai endTime')
        gc=tg.get('gia_cuc_bo')
        if not isinstance(gc,(int,float)) or gc<=0 or not isinstance(x.get('gia_cuc_bo'),(int,float)) or abs(x['gia_cuc_bo']-gc)>0.005*gc: loi.append(f'the {i}: kiem_lai.gia_cuc_bo {x.get("gia_cuc_bo")} lech the_gia {gc} (>0,5%)')
        if x.get('tien_te')!=tg.get('tien_te'): loi.append(f'the {i}: kiem_lai.tien_te {x.get("tien_te")} != the_gia {tg.get("tien_te")}')
        if str(x.get('endTime'))!=str(tg.get('endTime')): loi.append(f'the {i}: kiem_lai.endTime {x.get("endTime")} != the_gia {tg.get("endTime")}')
    return loi
def main():
    K=pathlib.Path(sys.argv[1]); M=pathlib.Path(sys.argv[2])
    m=json.load(open(M,encoding='utf-8')); lam=[]
    if (K/'loi-dang.json').exists():
        ld=json.load(open(K/'loi-dang.json',encoding='utf-8'))
        assert 0<len(ld['tieu_de'])<=100 and 0<len(ld['mo_ta'])<=2000 and ld['link'].startswith('https://sangame.com.vn') and '#SănGame' in ld['hashtag'],ld
        m['loi_dang']=ld; lam.append('loi_dang')
    if (K/'kiem-lai.json').exists():
        kl=json.load(open(K/'kiem-lai.json',encoding='utf-8'))
        for x in kl: assert x.get('pid') and x.get('loc') and isinstance(x.get('gia_cuc_bo'),(int,float)) and x.get('endTime'),x
        kl,loi_trung=khu_trung(kl); assert not loi_trung,'kiem_lai trung khong dong nhat: '+'; '.join(loi_trung)
        if (K/'tin.json').exists():
            loi=loi_kiem_lai(json.load(open(K/'tin.json',encoding='utf-8')),kl)
            assert not loi,'kiem_lai khong du cho cac the co gia: '+'; '.join(loi)
        m['kiem_lai']=kl; lam.append(f'kiem_lai({len(kl)})')
    elif (K/'tin.json').exists():
        loi=loi_kiem_lai(json.load(open(K/'tin.json',encoding='utf-8')),[])
        assert not loi,'kiem_lai khong du cho cac the co gia: '+'; '.join(loi)
    json.dump(m,open(M,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    print('sau_manifest_chung:',', '.join(lam) or 'khong co loi-dang.json / kiem-lai.json - giu mac dinh cua manifest.py')
if __name__=='__main__': main()
