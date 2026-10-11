# Gom ket qua dung thanh out/ (DUNG 7 tai san cua HOP-DONG.md muc 1) + manifest.json (phien_ban 1, HOP-DONG muc 2).
# THAT BAI (exit 1) neu thieu file / thieu bao cao kiem / bat ky phep nao truot / crash (A5).
#   python3 manifest.py --khuon khuon/top5 --ra out --dang top5 --ngay 2026-10-12 --che-do thu|that
# --ngay = ngay DANG (gio VN). Bien moi truong: CODE_SHA (mac dinh git HEAD), DATA_SHA (commit repo rieng tu).
import argparse,hashlib,json,os,pathlib,re,shutil,subprocess,sys,datetime
ap=argparse.ArgumentParser(); ap.add_argument('--khuon',required=True); ap.add_argument('--ra',required=True); ap.add_argument('--dang',required=True)
ap.add_argument('--ngay',required=True); ap.add_argument('--che-do',default='thu'); a=ap.parse_args()
K=pathlib.Path(a.khuon); R=pathlib.Path(a.ra); R.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
GIO={'tin-nhanh':'07:30','top5':'12:00','keo-thom':'20:00'}
loi=[]; nts=json.load(open(K/'nen-tang.json')); files={}
for nt in nts:
    v=K/f'video-{nt}.mp4'; b=K/f'bia-{nt}.jpg'; j=K/'kiem'/f'kiem-{nt}.json'
    if not v.exists() or v.stat().st_size<1_000_000: loi.append(f'thieu/hong {v.name}'); continue
    if not b.exists(): loi.append(f'thieu {b.name}'); continue
    if not j.exists(): loi.append(f'THIEU bao cao kiem {j.name} (kiem khong chay/crash)'); continue
    kj=json.load(open(j))
    if not kj.get('dat') or kj.get('crash'):
        loi.append(f'{nt}: kiem TRUOT ({kj.get("so_dat")}/{kj.get("tong")}) '+', '.join(p['ten'] for p in kj.get('phep',[]) if not p['dat'])[:300]+(' CRASH' if kj.get('crash') else ''))
    files[nt]=(v,b,kj)
if not loi and len(files)!=len(nts): loi.append('khong du 3 ban')
if loi:
    print('MANIFEST THAT BAI -> KHONG phat hanh:\n - '+'\n - '.join(loi)); sys.exit(1)
dur=lambda p:round(float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(p)],capture_output=True,text=True).stdout.strip()),2)
ban={}
for nt,(v,b,kj) in files.items():
    shutil.copy2(v,R/f'video-{nt}.mp4'); shutil.copy2(b,R/f'bia-{nt}.jpg')
    ban[nt]=dict(video=f'video-{nt}.mp4',sha256=sha(R/f'video-{nt}.mp4'),bia=f'bia-{nt}.jpg',bia_sha256=sha(R/f'bia-{nt}.jpg'),giay=dur(v),
                 kiem=dict(dat=True,phep=[dict(ten=p['ten'],dat=bool(p['dat']),so_do=p['so_do']) for p in kj['phep']]))
# loi dang tam: tu kich ban (B/C/D se thay bang tieu de + mo ta tu du lieu ngay)
TD={'tin-nhanh':'Bản tin game PlayStation sáng nay: 3 tin nóng','top5':'Top 5 game PlayStation bán chạy giá rẻ hôm nay','keo-thom':'Kèo thơm hôm nay: game PlayStation đang giảm sâu'}
loi_txt=(K/'loi.txt').read_text(encoding='utf-8').strip() if (K/'loi.txt').exists() else ''
loi_txt=re.sub(r'\[[^\]]*\]\s*','',loi_txt)
loi_dang=dict(tieu_de=TD[a.dang][:100],mo_ta=(loi_txt+'\n\nTra giá mọi game ở 6 vùng PS Store: https://sangame.com.vn/')[:2000],
              hashtag=['#SănGame','#PlayStation','#PS5','#GiảmGiá'],link='https://sangame.com.vn/')
kiem_lai=[]
if (K/'top5.json').exists():
    for g in json.load(open(K/'top5.json')):
        d=re.sub(r'\D','',g.get('gia',''))
        it=dict(ten=g['ten'],pid=g.get('pid'),loc=g.get('loc'),gia_vnd=int(d) if d else None)
        if g.get('gia_cuc_bo') is not None: it.update(gia_cuc_bo=g['gia_cuc_bo'],tien_te=g.get('tien_te'))   # gia tren trang PS Store vung do (khi du lieu co)
        it['endTime']=g.get('endTime'); kiem_lai.append(it)
vn=datetime.timezone(datetime.timedelta(hours=7))
m=dict(phien_ban=1,ngay_dang=a.ngay,dang=a.dang,gio_dang=f'{a.ngay}T{GIO[a.dang]}:00+07:00',che_do=a.che_do,
       sha_code=os.environ.get('CODE_SHA') or subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True).stdout.strip(),
       sha_du_lieu=os.environ.get('DATA_SHA',''),tao_luc=datetime.datetime.now(vn).isoformat(timespec='seconds'),ban=ban,loi_dang=loi_dang,kiem_lai=kiem_lai)
json.dump(m,open(R/'manifest.json','w'),ensure_ascii=False,indent=1)
print('MANIFEST DAT:',a.dang,a.ngay,{nt:(x['giay'],len(x['kiem']['phep'])) for nt,x in ban.items()},'kiem_lai',len(kiem_lai))
