# D1 — Chon KEO THOM trong ngay: 1 game tu deal ban chay, uu tien CHENH GIA LON giua cac vung MUA DUOC BANG THE PSN.
#   python3 chon-keo.py --repo <kenh-game-du-lieu> [--ngay YYYY-MM-DD] [--ra keo.json] [--lich-su file.json | --bo-lich-su] [--toi-da 15]
# Luat (ke-hoach-tu-dong-video-11-10.md GD D1, Sol #16):
#  - Chi tinh vung mua duoc bang the: bo vung khong_co_the (An Do), khong_the, chi_hoi_vien; gia quy theo GIA THE PSN tung vung, lam tron nghin
#    (cung ham quy doi voi web). KHONG goi la "re nhat mua duoc" — chi so 3 vung RE NHAT trong cac vung co the; ghi chu tren bang: "gia tham khao".
#  - Vung re nhat (>= 40% giam) la vung noi tren bia; 2 vung re ke tiep la 2 vung so sanh. Chenh lech toi thieu de co chuyen ke (>= 20.000d & 4%).
#  - Diem = chenh (vung re thu 3 - vung re nhat, VND) x trong so hang ban chay (<=50: 1,0 · <=100: 0,8 · <=200: 0,6 · <=300: 0,45; ban dac biet `goi` x0,7). Game goi nhieu game bi loai.
#  - Khong lap 14 ngay: doc Release `v-*-keo-thom` cua sangame-video (manifest.json cua tung ban) qua `gh`; khong doc duoc -> DUNG (khong chon bua).
#  - Kiem LAI tren trang san pham DUNG vung (3 vung): gia tren trang ±2% so voi so; endTime >= 20:00 ngay dang + 1 ngay (vung noi tren bia);
#    CA 3 vung deu phai co endTime >= moc nay (may dang kiem lai ca 3 qua `kiem_lai`, thieu endTime = bo khung); gia/endTime ghi vao keo.json la GIA TRI DAU TIEN
#    tren trang = khoi gia mua dut cua DUNG pid (cong-cu/gia_trang.py, cung ham voi dang/gia.py kiem lai; khoi mo ho/khong co endTime -> loai); trailer + anh lay tu trang vung noi tren bia (khong gia dinh en-us).
#  - Xuat keo.json (+ kiem_lai + loi_dang cho manifest), loi-dang.json, ket-qua-chon.json (cung quy uoc voi Top 5: thoat 3 = BO KHUNG, workflow ntfy).
#  - LOAI game co nut UPSELL_PS_PLUS_GAME_CATALOG cua dung pid tren bat ky trang vung nao (dang trong PS Plus Game Catalog); ly do loai ghi vao ket-qua-chon.json[loai].
#    Ma thoat: 0 chon duoc · 3 bo khung (du lieu cu / khong ung vien dat) · 4 da co Release hom nay · 5 khong doc duoc lich su Release.
import argparse,datetime,hashlib,json,os,pathlib,re,subprocess,sys,urllib.request,zoneinfo
T=pathlib.Path(__file__).resolve().parent; sys.path.insert(0,str(T))
from loi_chu import VUNG,TEN_DAY_DU,gon_ten,ten_hien
ap=argparse.ArgumentParser()
ap.add_argument('--repo',default=os.environ.get('DATA_DIR') or str(T.parent.parent.parent/'kenh-game-du-lieu'))
ap.add_argument('--ngay'); ap.add_argument('--ra',default=str(T/'keo.json'))
ap.add_argument('--lich-su'); ap.add_argument('--bo-lich-su',action='store_true'); ap.add_argument('--repo-phat-hanh',default='thenail1995-create/sangame-video')
ap.add_argument('--toi-da',type=int,default=15); ap.add_argument('--khong-kiem-do-moi',action='store_true')
A=ap.parse_args()
VN=zoneinfo.ZoneInfo('Asia/Ho_Chi_Minh'); UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
HOM_NAY=datetime.datetime.now(VN).date(); NGAY=datetime.date.fromisoformat(A.ngay) if A.ngay else HOM_NAY
A.ra=str(pathlib.Path(A.ra).resolve()); A.lich_su=str(pathlib.Path(A.lich_su).resolve()) if A.lich_su else None   # duong dan tuong doi tinh TRUOC khi chdir vao repo du lieu
sys.path.insert(0,A.repo); os.chdir(A.repo)
import tin_tu_sinh as t, trang_game
import tempfile
import media_xau
import importlib.util
_sp=importlib.util.spec_from_file_location('sangame_gia_trang',str(T.parent.parent/'cong-cu'/'gia_trang.py')); GT=importlib.util.module_from_spec(_sp); _sp.loader.exec_module(GT)   # doc gia/han/media dung pid (dung chung voi Top 5 va dang/gia.py); nap theo duong dan de khong them cong-cu vao sys.path
GIAM_MIN=40; HANG_TOI_DA=300; SO_NGAY_LAP=14; CHENH_MIN=20000; CHENH_PCT=0.04; DUNG_SAI_GIA=0.02
GIO_DANG=datetime.datetime.combine(NGAY,datetime.time(20,0),VN); HAN_TOI_THIEU=GIO_DANG+datetime.timedelta(days=1)
LOC={ma:v[3] for ma,v in VUNG.items()}
KQ=pathlib.Path(A.ra).resolve().parent/'ket-qua-chon.json'
NHAT_KY=[]   # ung vien bi loai + ly do (ghi vao ket-qua-chon.json)
def thoat(ma,msg):
    print(msg,file=sys.stderr)
    json.dump(dict(du=False,ma=ma,ly_do=msg,ngay=NGAY.isoformat(),loai=NHAT_KY[-30:]),open(KQ,'w',encoding='utf-8'),ensure_ascii=False,indent=1); sys.exit(ma)
d=t.nap_du_lieu()
if not d: thoat(3,'KHONG nap duoc du lieu (thieu trang-game.json)')
if not A.khong_kiem_do_moi:
    chinh,_=t.kiem_do_moi(HOM_NAY,d)
    if chinh: thoat(3,'DU LIEU CU, khong chon keo: '+'; '.join(chinh))
th=t.thu_hang_theo_khoa(d['so'],d['giam_gia']); qd=d['qd']
nghin_vnd=lambda x:int(re.sub(r'\D','',qd.dong(x)))
# ---------- lich su: game da len Keo thom trong 14 ngay + so ky
def lich_su():
    if A.bo_lich_su: return dict(so_ky=1,pid=set(),goc=set(),co_hom_nay=False)
    if A.lich_su:
        j=json.load(open(A.lich_su)); ds=[x for x in j.get('da_dang',[]) if 0<=(NGAY-datetime.date.fromisoformat(x['ngay'])).days<SO_NGAY_LAP]
        return dict(so_ky=int(j.get('so_ky',len(j.get('da_dang',[]))+1)),pid={p for x in ds for p in x.get('pid',[])},goc={t._ten_goc(x['ten']) for x in ds if x.get('ten')},
                    co_hom_nay=any(x['ngay']==NGAY.isoformat() for x in j.get('da_dang',[])))
    r=subprocess.run(['gh','release','list','-R',A.repo_phat_hanh,'--limit','200','--json','tagName'],capture_output=True,text=True)
    if r.returncode: thoat(5,'KHONG doc duoc lich su Release (gh): '+r.stderr.strip()[:200]+' — dung de khong chon lap')
    tags=[x['tagName'] for x in json.loads(r.stdout or '[]')]; ks=[]
    for tg in tags:
        m=re.fullmatch(r'v-(\d{4}-\d{2}-\d{2})-keo-thom',tg)
        if m: ks.append((m.group(1),tg))
    pid=set(); goc=set(); hom_nay=False
    for ng,tg in ks:
        if ng==NGAY.isoformat(): hom_nay=True
        if not (0<=(NGAY-datetime.date.fromisoformat(ng)).days<SO_NGAY_LAP): continue
        m=subprocess.run(['gh','release','download',tg,'-R',A.repo_phat_hanh,'-p','manifest.json','-O','-'],capture_output=True,text=True)
        if m.returncode: thoat(5,f'KHONG tai duoc manifest cua {tg}: {m.stderr.strip()[:200]}')
        for it in json.loads(m.stdout).get('kiem_lai',[]):
            if it.get('pid'): pid.add(it['pid'])
            if it.get('ten'): goc.add(t._ten_goc(it['ten']))
    return dict(so_ky=len(ks)+1,pid=pid,goc=goc,co_hom_nay=hom_nay)
LS=lich_su()
if LS['co_hom_nay']: thoat(4,f'Da co Release Keo thom ngay {NGAY} — khong chon lai')
# ---------- ung vien tu so (chua mo trang)
def ung_vien():
    ra=[]
    for h in d['hangs']:
        k=h['khoa']
        if k not in th or th[k][0]+1>HANG_TOI_DA or t._la_goi_nhieu_game(h): continue
        x=d['dls'].get(k)
        if not x: continue
        vs=[v for v in x['vung'] if not v.get('khong_co_the') and not v.get('khong_the') and not v.get('chi_hoi_vien') and v.get('vnd_con') and v['ma'] in VUNG]
        vs.sort(key=lambda v:v['vnd_con'])
        if len(vs)<3 or (vs[0].get('giam') or 0)<GIAM_MIN: continue
        v3=[dict(v,vnd=nghin_vnd(v['vnd_con']),goc_vnd=nghin_vnd(v['vnd_goc'])) for v in vs[:3]]
        c2=v3[1]['vnd']-v3[0]['vnd']; c3=v3[2]['vnd']-v3[0]['vnd']
        if c2<CHENH_MIN or c2/v3[0]['vnd']<CHENH_PCT or c3<2*CHENH_MIN: continue
        hang=th[k][0]+1; w=(1.0 if hang<=50 else .8 if hang<=100 else .6 if hang<=200 else .45)*(.7 if h.get("loai")=="goi" else 1)   # ban Deluxe/dac biet: ten dai, kem phan khi doc -> nhe diem
        pids={v['id'] for v in x['vung'] if v.get('id')}
        if pids&LS['pid'] or t._ten_goc(h['ten']) in LS['goc']: continue
        ra.append(dict(h=h,x=x,v3=v3,hang=hang,diem=c3*w,chenh=c3))
    ra.sort(key=lambda u:(-u['diem'],u['hang'],u['h']['slug']))
    return ra
UV=ung_vien()
print(f'{len(UV)} ung vien (chenh vung mua duoc bang the, giam >= {GIAM_MIN}%, hang <= {HANG_TOI_DA}, chua len 14 ngay); kiem tren trang san pham toi da {A.toi_da}:')
# ---------- trang san pham dung vung
def lay_trang(loc,pid):
    return urllib.request.urlopen(urllib.request.Request(f'https://store.playstation.com/{loc}/product/{pid}',headers={'User-Agent':UA}),timeout=40).read().decode('utf-8','ignore')
def doc_trang(html,pid):
    """-> dict(gia_cuc_bo, tien_te, endTime(ms str|None), video[], anh_chup[], anh, khoi) CHI tu KHOI GIA cua dung pid + Product:{pid} trong cache JSON
    (cong-cu/gia_trang.py; khong regex toan trang, khong 'gia dau tien': trang chua ca game goi y/ban khac). Khong co khoi ro rang -> gia_cuc_bo None.
    Luu y: dang/gia.py kiem lai cung bang gia_trang.khoi_gia nen gia/endTime ghi vao keo.json = gia/endTime may dang se doc."""
    k=GT.khoi_gia(html,pid); m=GT.media(html,pid)
    return dict(ps_plus=GT.ps_plus_catalog(html,pid),gia_cuc_bo=k['gia_cuc_bo'] if k else None,tien_te=k['tien_te'] if k else None,endTime=k['endTime'] if k else None,khoi=k,
                video=m['video'],anh_chup=m['anh_chup'],anh=m['anh'])
def kiem_ung_vien(u):
    """-> (keo|None, ly do loai)"""
    v3=u['v3']; tr=[]
    for i,v in enumerate(v3):
        try: p=doc_trang(lay_trang(LOC[v['ma']],v['id']),v['id'])
        except Exception as e: return None,f"khong mo duoc trang {LOC[v['ma']]} {v['id']}: {str(e)[:80]}"
        # Opus 11/10: game nam trong PS Plus Game Catalog (nut UPSELL_PS_PLUS_GAME_CATALOG cua DUNG pid) -> nguoi co Extra choi duoc, khong phai "keo" dang mua -> LOAI
        if p['ps_plus']: return None,f"{LOC[v['ma']]}: game co trong PS Plus Game Catalog (nut UPSELL_PS_PLUS_GAME_CATALOG cua dung pid) — nguoi co Extra choi duoc, khong phai keo dang mua"
        if p['gia_cuc_bo'] is None: return None,f"trang {LOC[v['ma']]} khong co khoi gia mua dut ro rang cua dung pid (het ban / nhieu khoi gia khac nhau / doi cau truc)"
        if abs(p['gia_cuc_bo']-v['con_so'])>DUNG_SAI_GIA*v['con_so']: return None,f"gia trang {LOC[v['ma']]} {p['gia_cuc_bo']:.2f} lech so {v['con_so']:.2f} > 2%"
        # may dang kiem lai CA 3 vung (kiem_lai) va coi thieu endTime la loi -> vung nao cung phai co endTime >= moc
        if not p['endTime']: return None,f"vung {LOC[v['ma']]} khong co endTime (may dang se bo khung)"
        het=datetime.datetime.fromtimestamp(int(p['endTime'])/1000,VN)
        if het<HAN_TOI_THIEU: return None,f"{LOC[v['ma']]} het giam {het:%d/%m %H:%M} < {HAN_TOI_THIEU:%d/%m %H:%M}"
        tr.append(p)
    if not tr[0]['video']: return None,f"trang {LOC[v3[0]['ma']]} khong co trailer"
    # chan media xau (anh giu cho 'PLACEHOLDER SCREENSHOTS', man phang): 3 khung trailer (25/50/75%) + toi da 2 anh chup + anh bia
    with tempfile.TemporaryDirectory() as td:
        f=os.path.join(td,'tr.mp4')
        try: urllib.request.urlretrieve(tr[0]['video'][0],f)
        except Exception as e: return None,f'khong tai duoc trailer: {str(e)[:60]}'
        dai=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f],capture_output=True,text=True).stdout.strip() or 0)
        for k in (.25,.5,.75):
            ly=media_xau.kiem_anh(media_xau.khung(f,dai*k,os.path.join(td,'k.png')))
            if ly: return None,f'khung trailer {int(k*100)}% {ly}'
        for j,u in enumerate(([tr[0]['anh']] if tr[0]['anh'] else [])+tr[0]['anh_chup'][:2]):
            g=os.path.join(td,f'a{j}.jpg')
            try: urllib.request.urlretrieve(u,g)
            except Exception: continue
            ly=media_xau.kiem_anh(g)
            if ly: return None,f'anh {u.rsplit("/",1)[-1][:20]} {ly}'
    return tr,None
chon=None
for i,u in enumerate(UV[:A.toi_da],1):
    h=u['h']; v3=u['v3']
    tr,ly=kiem_ung_vien(u)
    if not tr: NHAT_KY.append(f"#{u['hang']} {h['ten'][:50]}: {ly}")
    print(f"  {i:2d}. #{u['hang']} {h['ten'][:44]:44s} {v3[0]['ma']} {v3[0]['vnd']:,}d -{v3[0]['giam']}% | {v3[1]['ma']} +{v3[1]['vnd']-v3[0]['vnd']:,} | {v3[2]['ma']} +{v3[2]['vnd']-v3[0]['vnd']:,} -> "+('DAT' if tr else 'loai: '+ly))
    if tr: chon=(u,tr); break
if not chon: thoat(3,f'KHONG ung vien nao qua kiem tren trang san pham ({len(UV)} ung vien so bo, da thu {min(len(UV),A.toi_da)})')
u,tr=chon; h=u['h']; v3=u['v3']
het=datetime.datetime.fromtimestamp(int(tr[0]['endTime'])/1000,VN)
vung=[]
for v,p in zip(v3,tr):
    vung.append(dict(ma=v['ma'],hien=VUNG[v['ma']][0],dd=TEN_DAY_DU[v['ma']],co=VUNG[v['ma']][2],vnd=v['vnd'],goc_vnd=v['goc_vnd'],giam=v.get('giam'),pid=v['id'],loc=LOC[v['ma']],
                     gia_cuc_bo=p['gia_cuc_bo'],tien_te=p['tien_te'],endTime=p['endTime']))
may=' · '.join(u['x'].get('may') or []) or 'PS5'
tien,chinh=ten_hien(h['ten'])
a=vung[0]; con_goc=lambda n:f"{n:,}".replace(',','.')+'đ'
mo_ta=(f"{chinh} đang giảm {a['giam']}% ở PS Store {a['dd']}: còn {con_goc(a['vnd'])} (giá gốc {con_goc(a['goc_vnd'])}) khi quy theo giá thẻ PSN. "
       f"So với {vung[1]['dd']}: +{con_goc(vung[1]['vnd']-a['vnd'])}; {vung[2]['dd']}: +{con_goc(vung[2]['vnd']-a['vnd'])}. "
       f"Hết giảm {het:%H:%M ngày %d/%m} giờ Việt Nam. Giá quy đổi chỉ để tham khảo.\n\nXem giá ở 6 vùng PS Store: https://sangame.com.vn/{trang_game.ten_file_trang(h['slug'])}")
keo=dict(phien_ban=1,che_do_hoi_quy=False,ngay_dang=NGAY.isoformat(),gio_dang=GIO_DANG.isoformat(),ngay_du_lieu=str(d['cap_nhat'])[:10],gia_the_ngay=d.get('gia_the_ngay'),so_ky=LS['so_ky'],
    game=dict(ten=h['ten'],giam=a['giam'],may=may,hang_ban_chay=u['hang'],slug=h['slug'],khoa=h['khoa'],anh=tr[0]['anh'] or h.get('anh'),anh_chup=tr[0]['anh_chup'][:8],trailer=tr[0]['video']),
    goc_vnd=a['goc_vnd'],con_vnd=a['vnd'],vung=vung,han=dict(ma=a['ma'],endTime=a['endTime'],iso=het.isoformat()),
    ghi_chu_bang='Quy theo giá thẻ PSN từng vùng · giá tham khảo',
    kiem_lai=[dict(ten=h['ten'],pid=v['pid'],loc=v['loc'],gia_vnd=v['vnd'],gia_cuc_bo=v['gia_cuc_bo'],tien_te=v['tien_te'],endTime=v['endTime']) for v in vung],
    loi_dang=dict(tieu_de=f"{chinh} giảm {a['giam']}% ở PS Store {a['dd']}: còn {con_goc(a['vnd'])}"[:100],mo_ta=mo_ta[:2000],hashtag=['#SănGame','#PlayStation','#PS5','#GiảmGiá'],link='https://sangame.com.vn/'))
json.dump(keo,open(A.ra,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
json.dump(keo['loi_dang'],open(pathlib.Path(A.ra).resolve().parent/'loi-dang.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
json.dump(dict(du=True,ngay=NGAY.isoformat(),game=h['ten'],hang=u['hang'],vung=[x['ma'] for x in vung],thu=i,ung_vien=len(UV),loai=NHAT_KY[-30:]),open(KQ,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(f"CHON: #{u['hang']} {h['ten']} — {a['dd']} {con_goc(a['vnd'])} (-{a['giam']}%), so voi {vung[1]['dd']} +{con_goc(vung[1]['vnd']-a['vnd'])}, {vung[2]['dd']} +{con_goc(vung[2]['vnd']-a['vnd'])}; het giam {het:%d/%m %H:%M}; ky so {LS['so_ky']:03d} -> {A.ra}")
