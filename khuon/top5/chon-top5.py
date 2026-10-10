# Chọn 5 game cho video "Top 5 bán chạy dưới X nghìn" từ dữ liệu ngày của repo kenh-game-du-lieu (cùng hàm web dùng).
#   python3 chon-top5.py [thu-muc-repo]  -> top5.json, cau-hinh.json, tai-san/bia1..5.png
# Luật (Hào chốt 10/10, LOI-SAI D7): X = mốc nhỏ nhất trong 100/200/300/400K mà CẢ 5 game đều nằm trong 100 hạng bán chạy
# (US+SG gộp); giá = rẻ nhất trong các vùng CÓ thẻ PSN (quy theo giá thẻ, làm tròn nghìn như web); 1 dòng game 1 suất
# (Mafia và Mafia III là 1 dòng); thứ hạng video = hạng bán chạy (bán chạy nhất = hạng 1).
import sys,json,re,pathlib,urllib.request,datetime
T=pathlib.Path(__file__).resolve().parent
REPO=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else T.parent/'kenh-game-du-lieu'
sys.path.insert(0,str(REPO)); import os; os.chdir(REPO)
import tin_tu_sinh as t
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
MOC=[100000,200000,300000,400000]; HANG_TOI_DA=100; HANG_DEM=300
d=t.nap_du_lieu(); th=t.thu_hang_theo_khoa(d['so'],d['giam_gia']); qd=d['qd']
gia=lambda h:int(t._dong(qd,h['vnd']).replace('.','').replace('đ',''))
def dong_game(ten):   # khoá DÒNG game (Mafia = Mafia III): tên gốc trước ':', bỏ ®™, bỏ số/số La Mã
    k=re.sub(r'[®™]','',ten).lower().split(':')[0]
    return re.sub(r'\s+',' ',re.sub(r'\b(ii|iii|iv|v|vi|\d+)\b','',k)).strip()
def cung_game(ten): return t._ten_goc(ten) or ten   # dùng để ĐẾM: chỉ gộp các bản của cùng 1 game
def chon(X,hmax):
    ung=[h for h in d['hangs'] if h['khoa'] in th and th[h['khoa']][0]+1<=hmax and h['giam']>0 and h['vnd'] is not None
         and not t._la_goi_nhieu_game(h) and gia(h)<=X]
    ung.sort(key=lambda h:(th[h['khoa']][0],-h['giam'])); thay=set(); ra=[]
    for h in ung:
        k=dong_game(h['ten'])
        if k in thay: continue
        thay.add(k); ra.append(h)
    return ra
for X in MOC:
    ds=chon(X,HANG_DEM)
    if len(ds)>=5 and all(th[h['khoa']][0]+1<=HANG_TOI_DA for h in ds[:5]): break
top=ds[:5]
# Đếm TỔNG game bán chạy (300 hạng) dưới X — gộp bản cùng game, KHÔNG gộp dòng game; lời đọc nói số CÒN LẠI = tổng − 5 (LOI-SAI D8)
tong=len({cung_game(h['ten']) for h in d['hangs'] if h['khoa'] in th and th[h['khoa']][0]+1<=HANG_DEM and h['giam']>0 and h['vnd'] is not None and not t._la_goi_nhieu_game(h) and gia(h)<=X})
us=json.load(open(REPO/'du-lieu/giam-gia-en-US.json'))['mon']; sg=json.load(open(REPO/'du-lieu/giam-gia-en-SG.json'))['mon']
(T/'tai-san').mkdir(exist_ok=True); out=[]
for i,h in enumerate(top,1):
    tid=h['khoa'].split('|')[0]; pid=next((k for k in list(us)+list(sg) if tid in k),None); loc='en-us' if pid in us else 'en-sg'
    html=urllib.request.urlopen(urllib.request.Request(f'https://store.playstation.com/{loc}/product/{pid}',headers={'User-Agent':UA}),timeout=30).read().decode('utf-8','ignore')
    vids=sorted(set(re.findall(r'"type":"VIDEO","url":"(https://vulcan\.dl\.playstation\.net[^"]+\.mp4)"',html)))
    ss=list(dict.fromkeys(re.findall(r'"role":"SCREENSHOT","type":"IMAGE","url":"([^"]+)"',html)))
    end=re.findall(r'"endTime":"(\d+)"',html)
    anh=t.url_anh_day_du(h['anh']) if h.get('anh') else None
    if anh: urllib.request.urlretrieve(anh+'?w=720',T/f'tai-san/bia{i}.png')
    out.append(dict(hang_ban_chay=th[h['khoa']][0]+1,ten=h['ten'],gia=t._dong(qd,h['vnd']),vung=h['vung'],giam=h['giam'],goc=t._dong(qd,h['goc']),
                    may=h['may_chuoi'],anh=anh,slug=h['slug'],pid=pid,loc=loc,trailer=vids,anh_chup=ss[:6],endTime=end[0] if end else None))
json.dump(out,open(T/'top5.json','w'),ensure_ascii=False,indent=1)
ng=str(d.get('cap_nhat') or datetime.date.today().isoformat()); mm=re.match(r'(\d{4})-(\d{2})-(\d{2})',ng)
ngay=f'{mm.group(3)}/{mm.group(2)}' if mm else ng[:5]
json.dump(dict(ngay=ngay,muc=X,tong=tong,con_lai=tong-5),open(T/'cau-hinh.json','w'),ensure_ascii=False)
print(f'muc {X//1000}K, tong {tong} game ban chay duoi muc (con lai {tong-5}); top 5:'); [print(f"  {i}. #{g['hang_ban_chay']} {g['ten']} {g['gia']} {g['vung']} -{g['giam']}% trailer:{len(g['trailer'])} anh:{len(g['anh_chup'])}") for i,g in enumerate(out,1)]
