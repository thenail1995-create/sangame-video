# Ham chu dung chung cua khuon Keo thom v9 (kich-ban.py, chon-keo.py): so -> chu, ten vung/ten game de DOC, gio het giam.
# So viet bang CHU (may doc so de sai - LOI-SAI N7). Ten thuong hieu luon co dau: "Săn Game".
import datetime,math,re
SO=['không','một','hai','ba','bốn','năm','sáu','bảy','tám','chín']
def so_chu(n):
    """0..999 -> chu: 112 'một trăm mười hai', 105 'một trăm lẻ năm', 75 'bảy mươi lăm', 21 'hai mươi mốt', 15 'mười lăm'."""
    n=int(n); tr,ch,dv=n//100,(n//10)%10,n%10; o=[]
    if tr: o.append(SO[tr]+' trăm')
    if ch==0:
        if dv: o.append(('lẻ ' if tr else '')+SO[dv])
    else:
        o.append('mười' if ch==1 else SO[ch]+' mươi')
        if dv==1 and ch>1: o.append('mốt')
        elif dv==5: o.append('lăm')
        elif dv==4 and ch>1: o.append('tư')
        elif dv: o.append(SO[dv])
    return ' '.join(o) if o else 'không'
def nghin(vnd):   # 784000 -> 'bảy trăm tám mươi tư nghìn' (tren 999 nghin: 'một triệu một trăm bốn mươi sáu nghìn')
    k=int(vnd/1000+0.5)
    if k<1000: return so_chu(k)+' nghìn'
    tr,r=divmod(k,1000)
    return so_chu(tr)+' triệu'+(' '+so_chu(r)+' nghìn' if r else '')
def noi_goc(vnd):
    """Gia goc noi mieng, lam tron 100 nghin: 1.960.000 -> 'gần hai triệu'; 1.640.000 -> 'hơn một triệu sáu'; 840.000 -> 'gần tám trăm nghìn'... Tra (tien_to, cum)."""
    t=max(1,int(vnd/100000+0.5)); d=vnd-t*100000
    if t%10==0: cum=so_chu(t//10)+' triệu'
    elif t<10: cum=so_chu(t)+' trăm nghìn'
    else: cum=so_chu(t//10)+' triệu '+so_chu(t%10)
    if abs(d)<=0.06*t*100000: tt='gần' if d<0 else 'hơn' if d>0 else 'đúng'
    else: tt='khoảng'
    return tt,cum
def noi_chenh(vnd):
    """Chenh lech tien noi mieng, lam tron CHUC nghin: 51.000 -> 'năm chục'; 120.000 -> 'một trăm hai'; 150.000 -> 'một trăm rưỡi'; 300.000 -> 'ba trăm'."""
    n=max(1,int(vnd/10000+0.5))
    if n<10: return so_chu(n)+' chục'
    if n>=100:   # tu 1 trieu tro len: phan du CHAN tram nghin noi tat ("mot trieu ba", "mot trieu ruoi"); phan du le -> doc DAY DU bang nghin() (Sol bcd #16)
        tr,r=divmod(n,100)
        if r%10: return nghin(n*10000)   # 1.310.000 -> 'một triệu ba trăm mười nghìn' (truoc day bi doc hut thanh 'một triệu')
        r=r//10
        return so_chu(tr)+' triệu'+('' if not r else ' rưỡi' if r==5 else ' '+SO[r])
    h,r=divmod(n,10); ten=so_chu(h)+' trăm'
    return ten+('' if r==0 else ' rưỡi' if r==5 else ' mười' if r==1 else ' '+SO[r])
# ten vung: ma -> (hien thi tren hinh, noi mieng, co, ma chip, ma store)
VUNG={'US':('MỸ','Mỹ','us.svg','en-us'),'HK':('HỒNG KÔNG','Hồng Kông','hk.svg','en-hk'),'SG':('SINGAPORE','Sing','sg.svg','en-sg'),
      'TH':('THÁI LAN','Thái','th.svg','en-th'),'ID':('INDONESIA','Indo','id.svg','en-id')}
TEN_DAY_DU={'US':'Mỹ','HK':'Hồng Kông','SG':'Singapore','TH':'Thái Lan','ID':'Indonesia'}
def gon_ten(t):
    """Ten game de hien/noi: bo ®™, hau to nen tang/phien ban thuong gap."""
    t=re.sub(r'[®™]','',t or '')
    t=re.sub(r'\s*\((?:[^()]*(?:Chinese|English|Korean|Japanese|Thai|Ver\.?)[^()]*)\)','',t)
    t=re.sub(r'\s*\((?:Game|PS4|PS5)\)','',t)
    t=re.sub(r'\s+(?:for|cho)\s+PS[45]\b.*$','',t,flags=re.I)
    t=re.sub(r'\s*[-–:]\s*(?:PS4\s*&\s*PS5|PS5\s*&\s*PS4)\s*$','',t,flags=re.I)
    t=re.sub(r'\s*(?:PS4\s*&\s*PS5|PS5\s*&\s*PS4)\s*$','',t,flags=re.I)
    t=re.sub(r'\s+(?:full game|digital|standard edition)\s*$','',t,flags=re.I)
    return re.sub(r'\s+',' ',t).strip(' -–')
NGOAI_LE_NOI={'Mortal Kombat 11':'Mortal Kombat mười một','Mafia: Definitive Edition':'Mafia bản làm lại'}   # them khi gap ten doc sai
def ten_noi(t):
    """Ten de DOC: bo tien to so huu cach ('Marvel's Spider-Man 2' -> 'Spider-Man 2', nhu ban v8.3 da duyet), bo ':'."""
    g=gon_ten(t)
    if g in NGOAI_LE_NOI: return NGOAI_LE_NOI[g]
    g=ten_hien(g)[1]
    return re.sub(r'\s+',' ',g.replace(':',' ')).strip()
def ten_hien(t):
    """(tien to, phan nhan manh) cho bia: "Marvel's Spider-Man 2" -> ('Marvel’s','Spider-Man 2'); khong co tien to so huu cach -> ('', ten)."""
    g=gon_ten(t).replace("'",'’'); w=g.split(' ',1)
    if len(w)==2 and w[0].endswith('’s') and len(g.split())>=3: return w[0],w[1]
    return '',g
def buoi(gio24):
    """gio (1..23) -> (so doc 1..12, buoi): 14 -> ('hai','chiều')."""
    if gio24<=10: return so_chu(gio24),'sáng'
    if gio24<=12: return so_chu(gio24),'trưa'
    if gio24<=17: return so_chu(gio24-12),'chiều'
    if gio24<=21: return so_chu(gio24-12),'tối'
    return so_chu(gio24-12),'đêm'
def noi_han(het,ngay_dang):
    """het = datetime co mui gio VN luc het giam; ngay_dang = date. -> 'hai giờ chiều nay' / 'mười giờ đêm ngày mai' / 'hai giờ chiều ngày hai mươi hai tháng mười'.
    Doc 'truoc X gio' voi X = gio tron KE TIEP (13:59 -> hai giờ chiều): dung vi het giam 13:59 < 14:00."""
    gio=het.hour+(1 if (het.minute or het.second) else 0); ngay=het.date()
    if gio==0: ngay-=datetime.timedelta(days=1); gio=24   # 00:00 chinh xac = het ngay hom truoc
    if gio>=24: b='nửa đêm'
    else:
        so,bu=buoi(gio); b=f'{so} giờ {bu}'
    d=(ngay-ngay_dang).days
    n='nay' if d==0 else 'ngày mai' if d==1 else 'ngày kia' if d==2 else f'ngày {so_chu(ngay.day)} tháng {so_chu(ngay.month)}'
    return f'{b} {n}'

# ================= GIOI THIEU GAME (Hao 11/10: "nen noi 1 chut ve game nay, hay do ra sao, ban deluxe la ban ntn") =================
# 100% tu du lieu trang PS Store (cong-cu/gia_trang.thong_tin_game): the loai, diem sao + so luot, phan them cua ban dac biet, vai dac diem tu mo ta.
# BANG TU CO DINH, KHONG AI viet; thieu / khong khop chac chan => BO cau do (khong doan). Ket qua nam trong keo.json["gioi_thieu"].
import html as _html
from decimal import Decimal,ROUND_HALF_UP
THE_LOAI={'Action':'hành động','Adventure':'phiêu lưu','Arcade':'arcade','Casual':'giải trí nhẹ nhàng','Educational':'giáo dục','Family':'gia đình','Fighting':'đối kháng',
          'Horror':'kinh dị','Music/Rhythm':'âm nhạc','Party':'tiệc tùng','Platformer':'đi cảnh','Puzzle':'giải đố','Quiz':'đố vui','Racing':'đua xe','Role Playing Games':'nhập vai',
          'Shooter':'bắn súng','Simulation':'mô phỏng','Sport':'thể thao','Strategy':'chiến thuật'}
# dac diem: (khoa, mau regex tren mo ta tieng Anh chu thuong, cum NOI, nhan HIEN). Thu tu = thu tu uu tien khi chon toi da 2.
DAC_DIEM=[('roguelike',r"rogue[\s-]?(?:like|lite)",'roguelike, chết là chơi lại từ đầu','ROGUELIKE'),
          ('the_gioi_mo',r"open[\s-]world",'thế giới mở','THẾ GIỚI MỞ'),
          ('co_op_online',r"online\s+co-?op|co-?op(?:erative)?\s+mode|co-?operative",'chơi chung online được','CHƠI CHUNG ONLINE'),
          ('co_op_local',r"local\s+co-?op|couch\s+co-?op|split[\s-]?screen",'chơi chung trên một máy','CHƠI CHUNG 1 MÁY'),
          ('souls',r"souls[\s-]?like",'khó kiểu Souls','KHÓ KIỂU SOULS')]
# phan them cua ban dac biet: (khoa, mau regex tren dong, cum NOI, nhan HIEN, co dem so?) — thu tu = thu tu doc / uu tien khi > 4 muc.
THEM=[('vu_khi',r"weapon",'vũ khí','vũ khí',True),('trang_phuc',r"\b(?:outfits?|skins?|costumes?|suits?)\b",'trang phục','trang phục',False),
      ('mo_rong',r"season\s+pass|expansion|\bdlc\b",'gói mở rộng','gói mở rộng',False),('tien',r"in-?game\s+currency|\bcredits\b|\bcoins\b|\bpoints\b",'tiền trong game','tiền trong game',False),
      ('vat_pham',r"booster|stimulant|consumable|\bitems?\b|artefact|artifact",'vật phẩm','vật phẩm',False),('hinh_nen',r"\bthemes?\b",'hình nền PS5','hình nền PS5',False),
      ('sach_tranh',r"art\s?book",'sách tranh','sách tranh',False),('avatar',r"avatars?",'ảnh đại diện','ảnh đại diện',False),('nhac',r"soundtrack",'nhạc phim','nhạc phim',False)]
# MOI DONG chi thuoc 1 loai, xet theo thu tu nay (vu khi truoc vat pham; "in-game currency" thuoc tien truoc khi xet "item")
_THU_TU_DONG=['vu_khi','nhac','sach_tranh','avatar','mo_rong','tien','hinh_nen','trang_phuc','vat_pham']
TEN_BAN={'deluxe':'Deluxe','ultimate':'Ultimate','gold':'Gold','premium':'Premium','collector':'Collector','definitive':'Definitive','complete':'đầy đủ','special':'đặc biệt',
         'legendary':'Legendary','founder':'Founder','anniversary':'kỷ niệm'}
_SO_EN={'one':1,'two':2,'three':3,'four':4,'five':5}
MIN_LUOT=200
def _dong(mo_ta):
    t=re.sub(r'<br\s*/?>','\n',mo_ta or '',flags=re.I); t=_html.unescape(re.sub(r'<[^>]+>','',t))
    return [l.strip() for l in t.split('\n')]
def _lam_sach(l):
    l=re.sub(r'^[\s\-–•*·]+','',l); l=re.sub(r'[¹²³⁴⁵⁶⁷⁸⁹⁰†‡™®]','',l)
    return re.sub(r'\s+',' ',l).strip(' .;:')
def la_ban_dac_biet(ed):
    """edition khac ban thuong: ten co tu khoa ban dac biet (Deluxe/Ultimate/...) hoac loai PREMIUM, va khong ghi 'standard'. 'Cliff Rush 3D' (ten edition = ten game) -> khong."""
    if not ed or not ed.get('ten'): return False
    t=ed['ten'].lower()
    if 'standard' in t: return False
    return ed.get('loai')=='PREMIUM' or any(re.search(r'\b'+k,t) for k in TEN_BAN)
def ten_ban_noi(ed):
    t=(ed or {}).get('ten','').lower()
    return next((v for k,v in TEN_BAN.items() if re.search(r'\b'+k,t)),'này')
def phan_them(mo_ta_dai,tinh_nang=()):
    """-> (muc[], dong_goc[], dung_som). Doc khoi DAU cua mo ta dai (tieu de + cac dong '- ...' truoc dong trong dau tien); khong co dong '- ' nao -> edition.features. Muc ngoai bang -> bo (khong doan)."""
    ds=_dong(mo_ta_dai); i=0
    while i<len(ds) and not ds[i]: i+=1
    khoi=[]
    while i<len(ds) and ds[i]: khoi.append(ds[i]); i+=1
    bullets=[l for l in khoi if re.match(r'^[-–•*·]\s*\S',l)]
    dung_som=bool(bullets) and bool(re.search(r'early\s+access.{0,200}?(?:obtainable|unlock|story\s+progression)',' '.join(khoi),re.I|re.S))
    goc=[_lam_sach(l) for l in (bullets or list(tinh_nang))]; goc=[g for g in goc if g]
    dem={}
    for g in goc:
        low=g.lower()
        for k in _THU_TU_DONG:
            if re.search(next(m for kk,m,_,_,_ in THEM if kk==k),low):
                n=1
                if k=='vu_khi':
                    q=re.match(r'(\d+|one|two|three|four|five)\b',low)
                    if q: n=int(q.group(1)) if q.group(1).isdigit() else _SO_EN[q.group(1)]
                dem[k]=dem.get(k,0)+n; break
    muc=[]
    for kk,_,noi,hien,dem_so in THEM:
        if kk not in dem: continue
        if dem_so and 0<dem[kk]<100: muc.append(dict(k=kk,so=dem[kk],noi=f'{so_chu(dem[kk])} {noi}',hien=f'{dem[kk]} {hien}'))
        else: muc.append(dict(k=kk,so=1,noi=noi,hien=hien[0].upper()+hien[1:]))
    muc=muc[:4]
    if dung_som and muc:   # "dung som": gan vao vat pham neu co, khong thi muc dau (loi mau: "vat pham dung som")
        m=next((x for x in muc if x['k']=='vat_pham'),muc[0]); m['noi']+=' dùng sớm'; m['hien']+=' dùng sớm'; m['dung_som']=True
    return muc,goc,dung_som
def lam_tron_diem(tb): return float(Decimal(str(tb)).quantize(Decimal('0.1'),rounding=ROUND_HALF_UP))
def noi_diem(r):
    """4.4 -> 'bốn phẩy bốn'; 4.0 -> 'bốn' (kem 'sao' o cau)."""
    n=int(r); f=int(round((r-n)*10))
    return so_chu(n) if not f else f'{so_chu(n)} phẩy {SO[f]}'
def hien_diem(r): return str(int(r)) if r==int(r) else f'{r:.1f}'.replace('.',',')
def hien_luot(n):
    if n>=1_000_000: return f'{n/1e6:.1f}M'.replace('.',',').replace(',0M','M')
    if n>=10_000: return f'{int(n/1000+.5)}K'
    if n>=1000: return f'{n/1000:.1f}K'.replace('.',',').replace(',0K','K')
    return str(n)
def gioi_thieu_tu_trang(tt):
    """tt = gia_trang.thong_tin_game / hop_nhat_thong_tin. -> dict(gioi_thieu) hoac None neu khong co GI de noi (khong the loai, khong dac diem, khong diem, khong phan them)."""
    gen=[]
    for g in tt.get('the_loai') or []:
        v=THE_LOAI.get(g)
        if v and v not in [x['vi'] for x in gen]: gen.append(dict(goc=g,vi=v))
    gen=gen[:2]
    mo=(tt.get('mo_ta_dai') or '')+' '+(tt.get('mo_ta_ngan') or ''); low=_html.unescape(re.sub(r'<[^>]+>',' ',mo)).lower().replace('’',"'")
    dd=[dict(k=k,noi=noi,hien=hien) for k,mau,noi,hien in DAC_DIEM if re.search(mau,low)]
    if any(x['k']=='co_op_online' for x in dd): dd=[x for x in dd if x['k']!='co_op_local']
    dd=dd[:2]
    d=tt.get('diem'); diem=None
    if d and d.get('so_luot',0)>=MIN_LUOT:
        r=lam_tron_diem(d['tb']); diem=dict(tb=d['tb'],lam_tron=r,so_luot=d['so_luot'],noi=noi_diem(r),hien=hien_diem(r),luot=hien_luot(d['so_luot']))
    ban=None; ed=tt.get('edition')
    if la_ban_dac_biet(ed):
        muc,goc,ds=phan_them(tt.get('mo_ta_dai'),(ed or {}).get('tinh_nang') or [])
        if muc: ban=dict(ten=ed['ten'],ten_noi=ten_ban_noi(ed),them=muc,dung_som=ds,them_goc=goc)
    if not (gen or dd or diem or ban): return None
    return dict(the_loai=gen,dac_diem=dd,diem=diem,ban=ban)
def ghep_them(muc):
    """Danh sach phan them -> [(tu_noi_truoc, cum_noi, dau_sau)]: 1 'A.' · 2 'A và B.' · 3 'A, B và C.' · 4 'A với B, C và D.' (4 muc = dung loi mau da duyet 11/10)."""
    t=[m['noi'] for m in muc]; n=len(t)
    if n==1: return [('',t[0],'.')]
    if n==2: return [('',t[0],''),('và',t[1],'.')]
    if n==3: return [('',t[0],','),('',t[1],''),('và',t[2],'.')]
    return [('',t[0],''),('với',t[1],','),('',t[2],''),('và',t[3],'.')]
