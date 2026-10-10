# Chon 5 game cho video "Top 5 ban chay duoi X nghin" tu du lieu ngay cua repo rieng tu kenh-game-du-lieu (cung ham web dung). B1.
#   python3 chon-top5.py [thu-muc-repo-du-lieu] [--ngay YYYY-MM-DD]   (ngay = ngay DANG, gio VN; mac dinh env NGAY, roi ngay cap nhat du lieu)
#   Ra: top5.json, cau-hinh.json, loi-dang.json, tai-san/bia1..5.png, ket-qua-chon.json.  Thoat 3 = KHONG du 5 game -> bo khung (ntfy).
# Luat (Hao chot 10/10, LOI-SAI D7): X = moc nho nhat trong 100/200/300/400K ma CA 5 game deu nam trong 100 hang ban chay (US+SG gop);
# gia = re nhat trong cac vung CO the PSN (quy theo gia the, lam tron nghin nhu web); 1 dong game 1 suat; hang video = hang ban chay.
# Them o B1 (11/10): loai game da len Top 5 trong 3 ngay; loai deal het han truoc GIO_DANG + 2 gio; endTime + trailer + gia dia phuong lay tu
# DUNG product trang cua vung co gia duoc chon (Hong Kong -> en-hk, khong mac dinh en-us); ten doc/hien thi qua ten_rut_gon.
import sys,json,re,os,pathlib,time,urllib.request,urllib.error,datetime
T=pathlib.Path(__file__).resolve().parent; sys.path.insert(0,str(T))
import ten_rut_gon as tr, lich_su_top5 as ls
args=[a for a in sys.argv[1:] if not a.startswith('--')]
ngay_dang=next((sys.argv[i+1] for i,a in enumerate(sys.argv) if a=='--ngay'),None) or os.environ.get('NGAY') or ''
if ngay_dang in args: args.remove(ngay_dang)
def tim_repo():
    for p in [args[0] if args else None,os.environ.get('DU_LIEU_REPO'),T.parent.parent/'du-lieu',T.parent/'kenh-game-du-lieu',pathlib.Path.home()/'Kho-luu/kenh-game/dang-lam/kenh-game-du-lieu']:
        if p and (pathlib.Path(p)/'tin_tu_sinh.py').exists(): return pathlib.Path(p).resolve()
    sys.exit('LOI: khong thay thu muc kenh-game-du-lieu (tin_tu_sinh.py). Truyen duong dan hoac dat DU_LIEU_REPO.')
REPO=tim_repo(); sys.path.insert(0,str(REPO)); os.chdir(REPO)
import tin_tu_sinh as t
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
MOC=[100000,200000,300000,400000]; HANG_TOI_DA=100; HANG_DEM=300
VN=datetime.timezone(datetime.timedelta(hours=7))
d=t.nap_du_lieu(); th=t.thu_hang_theo_khoa(d['so'],d['giam_gia']); qd=d['qd']
if not ngay_dang: ngay_dang=str(d.get('cap_nhat') or datetime.datetime.now(VN).date().isoformat())[:10]
GIO_DANG=os.environ.get('GIO_DANG','12:00')
han_ms=int((datetime.datetime.fromisoformat(f'{ngay_dang}T{GIO_DANG}:00+07:00')+datetime.timedelta(hours=2)).timestamp()*1000)   # D2: con it nhat 2 gio sau gio dang
gia=lambda h:int(t._dong(qd,h['vnd']).replace('.','').replace('đ',''))
cung_game=lambda ten:t._ten_goc(ten) or ten   # dung de DEM: chi gop cac ban cua cung 1 game
dong_game=ls.ten_dong_game
da_len,ghi_chu_ls=ls.da_len(ngay_dang,3); print('lich su Top 5:',ghi_chu_ls,'| dong game da len:',sorted(da_len))
TIEN_TE={'US':'USD','HK':'HKD','SG':'SGD','ID':'IDR','TH':'THB','IN':'INR'}
def so_gia(s):   # 'HK$367.16' / 'Rp 756,430' / 'THB 1,601.00' / 'Rs 2,799' -> float
    n=re.sub(r'[^\d.,]','',s or '')
    if not n: return None
    if ',' in n and '.' in n: n=n.replace(',','')
    elif ',' in n: n=n.replace(',','') if re.fullmatch(r'\d{1,3}(,\d{3})+',n) else n.replace(',','.')
    return float(n)
_trang={}
def lay_trang(loc,pid):
    k=(loc,pid)
    if k in _trang: return _trang[k]
    ket=None
    for lan in range(3):
        try:
            ket=urllib.request.urlopen(urllib.request.Request(f'https://store.playstation.com/{loc}/product/{pid}',headers={'User-Agent':UA}),timeout=40).read().decode('utf-8','ignore'); break
        except urllib.error.HTTPError as e:
            if e.code in (404,410): break
            time.sleep(2*(lan+1))
        except Exception: time.sleep(2*(lan+1))
    time.sleep(0.3); _trang[k]=ket; return ket
def gia_trang(html,con_du_lieu):
    """Khoi Price tren trang khop gia dang giam trong du lieu vung (chuoi y het, hoac lech <= 2%) -> dict hoac None."""
    cs=[]
    for m in re.finditer(r'"__typename":"Price","basePrice":"([^"]*)","discountedPrice":"([^"]*)"(.*?)"currencyCode":"(\w+)"',html,re.S):
        e=re.search(r'"endTime":(?:"(\d+)"|null)',m.group(3)); cs.append(dict(goc=m.group(1),con=m.group(2),end=e.group(1) if e else None,tien=m.group(4)))
    a=so_gia(con_du_lieu)
    for c in cs:
        if c['con'].replace('\xa0',' ')==(con_du_lieu or '').replace('\xa0',' '): return c
    for c in cs:
        b=so_gia(c['con'])
        if a and b and abs(a-b)/a<=0.02 and c['goc']!=c['con']: return c
    return None
bia_da=set()
def xet(h):
    """Ung vien -> dict hoac None (kem ly do). Goi trang PS Store DUNG vung cua gia duoc chon."""
    k=dong_game(h['ten'])
    if k in da_len: return None,'da len Top 5 trong 3 ngay'
    if not tr.doc_duoc(h['ten']): return None,f"ten may doc khong on dinh ({tr.hien_thi(h['ten'])})"
    if not h.get('anh'): return None,'khong co anh bia'
    ma=h['ma']; loc='en-'+ma.lower()
    rec=((d['so']['game'].get(h['khoa']) or {}).get('vung') or {}).get(ma)   # product id + gia CHINH vung co gia duoc chon (khong doan en-us)
    if not rec or not rec.get('id'): return None,f'so khong co product cua vung {ma}'
    if rec.get('giam')!=h['giam']: return None,f"so vung {ma} giam {rec.get('giam')}% khac hang {h['giam']}%"
    pid=rec['id']; con=rec.get('con')
    html=lay_trang(loc,pid)
    if not html: return None,f'khong mo duoc trang {loc}/{pid}'
    g=gia_trang(html,con)
    if not g: return None,f'gia tren trang {loc} khong khop du lieu ({con})'
    if not g['end']: return None,'khong co endTime (khong biet han giam)'
    if int(g['end'])<han_ms: return None,f"het han som ({datetime.datetime.fromtimestamp(int(g['end'])/1000,VN):%d/%m %H:%M} < gio dang + 2h)"
    vids=sorted(set(re.findall(r'"type":"VIDEO","url":"(https://vulcan\.dl\.playstation\.net[^"]+\.mp4)"',html)))
    ss=list(dict.fromkeys(re.findall(r'"role":"SCREENSHOT","type":"IMAGE","url":"([^"]+)"',html)))
    return dict(h=h,pid=pid,loc=loc,trailer=vids,anh_chup=ss[:6],endTime=g['end'],gia_cuc_bo=so_gia(g['con']),tien_te=g['tien'] or TIEN_TE.get(ma)),None
def ung_vien(X):
    u=[h for h in d['hangs'] if h['khoa'] in th and th[h['khoa']][0]+1<=HANG_DEM and h['giam']>0 and h['vnd'] is not None
       and not t._la_goi_nhieu_game(h) and gia(h)<=X]
    u.sort(key=lambda h:(th[h['khoa']][0],-h['giam'])); return u
_xet={}; ds=[]; X=None; nhat_ky=[]
for X in MOC:
    ds=[]; thay=set()
    for h in ung_vien(X):
        if th[h['khoa']][0]+1>HANG_TOI_DA: break
        k=dong_game(h['ten'])
        if k in thay: continue
        if h['khoa'] not in _xet:
            _xet[h['khoa']]=xet(h)
            r=_xet[h['khoa']]
            if r[0] is None: nhat_ky.append(f"  loai #{th[h['khoa']][0]+1} {h['ten'][:40]} ({gia(h)//1000}K {h['ma']}): {r[1]}"); print(nhat_ky[-1])
        r=_xet[h['khoa']]
        if r[0] is None: continue
        thay.add(k); ds.append(r[0])
        if len(ds)==5: break
    if len(ds)==5: break
if len(ds)<5:
    ly_do=f'chi co {len(ds)} game du dieu kien trong top {HANG_TOI_DA} ban chay den moc {MOC[-1]//1000}K'
    json.dump(dict(trang_thai='thieu',ly_do=ly_do,loai=nhat_ky[-30:]),open(T/'ket-qua-chon.json','w'),ensure_ascii=False,indent=1)
    print('KHONG DU 5 GAME:',ly_do); sys.exit(3)
# Dem TONG game ban chay (300 hang) duoi X - gop ban cung game, KHONG gop dong game; loi doc noi so CON LAI = tong - 5 (LOI-SAI D8)
tong=len({cung_game(h['ten']) for h in ung_vien(X)})
(T/'tai-san').mkdir(exist_ok=True); out=[]
for i,c in enumerate(ds,1):
    h=c['h']; anh=t.url_anh_day_du(h['anh'])
    urllib.request.urlretrieve(anh+'?w=720',T/f'tai-san/bia{i}.png')
    out.append(dict(hang_ban_chay=th[h['khoa']][0]+1,ten=tr.hien_thi(h['ten']),ten_goc=h['ten'],ten_doc=tr.doc(h['ten']),gia=t._dong(qd,h['vnd']),vung=h['vung'],ma=h['ma'],giam=h['giam'],
                    goc=t._dong(qd,h['goc']),may=h['may_chuoi'],anh=anh,slug=h['slug'],pid=c['pid'],loc=c['loc'],trailer=c['trailer'],anh_chup=c['anh_chup'],
                    endTime=c['endTime'],gia_cuc_bo=c['gia_cuc_bo'],tien_te=c['tien_te']))
json.dump(out,open(T/'top5.json','w'),ensure_ascii=False,indent=1)
dd,mm=ngay_dang[8:10],ngay_dang[5:7]
json.dump(dict(ngay=f'{dd}/{mm}',ngay_iso=ngay_dang,muc=X,tong=tong,con_lai=tong-5),open(T/'cau-hinh.json','w'),ensure_ascii=False)
# Loi dang (tit <= 100 ky tu, mo ta <= 2000): moi so lay tu du lieu
cuoi=min(int(g['endTime']) for g in out); cuoi_s=datetime.datetime.fromtimestamp(cuoi/1000,VN).strftime('%d/%m %H:%M')
dong='\n'.join(f"{r}. {g['ten']} - {g['gia']} (-{g['giam']}%, store {g['vung']})" for r,g in enumerate(out,1))
mo_ta=(f"Top 5 game PS5 bán chạy đang giảm giá, dưới {X//1000}.000đ (ngày {dd}/{mm}):\n{dong}\n\n"
       f"Còn {tong-5} game bán chạy nữa dưới {X//1000}.000đ. Deal sớm nhất hết lúc {cuoi_s} (giờ VN).\n"
       f"Giá quy đổi theo giá thẻ PSN ở Việt Nam, có thể đổi theo tỷ giá. Tra giá 6 vùng PS Store: https://sangame.com.vn/")
tit=f"Top 5 game PS5 bán chạy dưới {X//1000}.000đ hôm nay ({dd}/{mm})"
json.dump(dict(tieu_de=tit[:100],mo_ta=mo_ta[:2000],hashtag=['#SănGame','#PlayStation','#PS5','#GiảmGiá'],link='https://sangame.com.vn/'),open(T/'loi-dang.json','w'),ensure_ascii=False,indent=1)
json.dump(dict(trang_thai='du',muc=X,tong=tong,ngay=ngay_dang,ghi_chu_lich_su=ghi_chu_ls,loai=nhat_ky[-30:]),open(T/'ket-qua-chon.json','w'),ensure_ascii=False,indent=1)
print(f'muc {X//1000}K, tong {tong} game ban chay duoi muc (con lai {tong-5}); top 5:')
for i,g in enumerate(out,1): print(f"  {i}. #{g['hang_ban_chay']} {g['ten']} [{g['ten_doc']}] {g['gia']} {g['vung']} -{g['giam']}% {g['gia_cuc_bo']} {g['tien_te']} het {datetime.datetime.fromtimestamp(int(g['endTime'])/1000,VN):%d/%m %H:%M} trailer:{len(g['trailer'])} anh:{len(g['anh_chup'])}")
