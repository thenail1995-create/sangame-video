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
    if n<10: return nghin(n*10000)   # 13/10 Keo 22:00 (run 38405501278): 'chín chục' -> Whisper nghe '9 trụng' -> D3 9.000đ truot; doc day du 'chín mươi nghìn' (ro hon cho nguoi xem)
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
# Ten giong AI (Minh Dang, eleven_v3) KHONG doc ro duoc -> chon-keo BO ung vien (12/10: 'Lies of P' -> Whisper turbo/small nghe 'Line Zoppy'/'live doc pi';
# da thu 'Lies of Pi', 'Lai-do op Pi' van truot D3). Khoa = chu thuong, khop neu nam trong ten goc (moi phien ban). Them khi gap ten moi.
TEN_KHO_DOC=('lies of p',)
# Luat noi dung cua Hao (CLAUDE.md du an: 'KHONG dung hinh meo'): game ma nhan vat chinh la meo -> bo ung vien (12/10: Hello Kitty Island Adventure).
TEN_BO_NOI_DUNG=('hello kitty',)
def kho_doc(ten):
    g=' '+re.sub(r'\s+',' ',(ten or '').lower())+' '
    return any(re.search(r'(?<![a-z0-9])'+re.escape(k)+r'(?![a-z0-9])',g) for k in TEN_KHO_DOC+TEN_BO_NOI_DUNG)
def ten_noi(t):
    """Ten de DOC: bo tien to so huu cach ('Marvel's Spider-Man 2' -> 'Spider-Man 2', nhu ban v8.3 da duyet), bo ':'."""
    g=gon_ten(t)
    if g in NGOAI_LE_NOI: return NGOAI_LE_NOI[g]
    g=ten_hien(g)[1]
    return re.sub(r'\s+',' ',g.replace(':',' ')).strip()
TIEN_TO_HANG=('Marvel’s','Tom Clancy’s','Sid Meier’s','Disney’s',)
def ten_hien(t):
    """(tien to, phan nhan manh) cho bia: "Marvel's Spider-Man 2" -> ('Marvel’s','Spider-Man 2'); khong co tien to so huu cach -> ('', ten)."""
    g=gon_ten(t).replace("'",'’'); w=g.split(' ',1)
    # 12/10: CHI tien to so huu cua HANG/TAC GIA (Marvel's...) moi tach; 'Assassin's Creed' la ten game -> giu nguyen (tung doc 'Creed Shadows')
    if len(w)==2 and w[0] in TIEN_TO_HANG and len(g.split())>=3: return w[0],w[1]
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
# dac diem (KHONG gom co-op: xu ly rieng, can bang chung online/local trong cung cum — Sol 11/10 P1): (khoa, mau regex tren mo ta tieng Anh chu thuong, cum NOI, nhan HIEN).
DAC_DIEM=[('roguelike',r"rogue[\s-]?(?:like|lite)",'roguelike, chết là chơi lại từ đầu','ROGUELIKE'),
          ('the_gioi_mo',r"open[\s-]world",'thế giới mở','THẾ GIỚI MỞ'),
          ('souls',r"souls[\s-]?like",'khó kiểu Souls','KHÓ KIỂU SOULS')]
CO_OP={'co_op_online':('chơi chung online được','CHƠI CHUNG ONLINE'),'co_op_local':('chơi chung trên một máy','CHƠI CHUNG 1 MÁY')}
THU_TU_DD=['roguelike','the_gioi_mo','co_op_online','co_op_local','souls']
def che_do_co_op(low):
    """Co-op: tach MENH DE (dau cau, ' and ', ' or ', ' but '); menh de nhac co-op ma co 'local/couch/split-screen/same screen' -> local; co 'online/internet/psn' -> online;
    co-op KHONG ro ('co-op mode' tron, 'cooperative') -> bo. Co online o BAT KY menh de nao -> online; khong thi local; khong thi None."""
    on=lo=False
    for c in re.split(r'[.!?;:\n,]|\band\b|\bor\b|\bbut\b',low):
        if not re.search(r"\bco-?op\b|\bco-?operative\b",c): continue
        if re.search(r"\blocal\b|\bcouch\b|split[\s-]?screen|same\s+(?:screen|console)|shared\s+screen",c): lo=True
        elif re.search(r"\bonline\b|\binternet\b|\bpsn\b",c): on=True
    return 'co_op_online' if on else 'co_op_local' if lo else None
# phan them cua ban dac biet: (khoa, mau regex tren dong, cum NOI, nhan HIEN, co dem so?) — thu tu = thu tu doc / uu tien khi > 4 muc.
THEM=[('skin_vu_khi',r"weapon\s+(?:skins?|camos?|charms?)|(?:skins?|camos?)\s+for\s+(?:the\s+)?weapons?",'skin vũ khí','skin vũ khí',False),
      ('vu_khi',r"weapon",'vũ khí','vũ khí',True),('trang_phuc',r"\b(?:outfits?|skins?|costumes?|suits?)\b",'trang phục','trang phục',False),
      ('mo_rong',r"season\s+pass|expansion|\bdlc\b",'gói mở rộng','gói mở rộng',False),('tien',r"in-?game\s+currency|\bcredits\b|\bcoins\b|\bpoints\b",'tiền trong game','tiền trong game',False),
      ('vat_pham',r"booster|stimulant|consumable|\bitems?\b|artefact|artifact",'vật phẩm','vật phẩm',False),
      ('chu_de_menu',r"(?:main\s+)?menu\s+theme|game\s+theme",'chủ đề menu game','chủ đề menu game',False),
      ('hinh_nen',r"ps5\W+(?:dynamic\s+)?theme|dynamic\s+theme|theme\W+for\s+ps5|ps5.{0,30}\btheme",'hình nền PS5','hình nền PS5',False),
      ('sach_tranh',r"art\s?book",'sách tranh','sách tranh',False),('avatar',r"avatars?",'ảnh đại diện','ảnh đại diện',False),('nhac',r"soundtrack",'nhạc phim','nhạc phim',False),
      ('choi_som',r"$^",'chơi sớm','chơi sớm',False)]    # choi_som: tao rieng tu cau dan (N ngay choi som game)
# MOI DONG chi thuoc 1 loai, xet theo thu tu nay (skin vu khi / hinh nen PS5 / chu de menu truoc loai chung; "in-game currency" truoc "item")
_THU_TU_DONG=['skin_vu_khi','vu_khi','nhac','sach_tranh','avatar','mo_rong','tien','hinh_nen','chu_de_menu','trang_phuc','vat_pham']
TEN_BAN={'deluxe':'Deluxe','ultimate':'Ultimate','gold':'Gold','premium':'Premium','collector':'Collector','definitive':'Definitive','complete':'đầy đủ','special':'đặc biệt',
         'legendary':'Legendary','founder':'Founder','anniversary':'kỷ niệm'}
_SO_EN={'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9}
MIN_LUOT=200
def _dong(mo_ta):
    t=re.sub(r'<br\s*/?>','\n',mo_ta or '',flags=re.I); t=_html.unescape(re.sub(r'<[^>]+>','',t))
    return [l.strip() for l in t.split('\n')]
def _lam_sach(l):
    l=re.sub(r'^[\s\-–•*·]+','',l); l=re.sub(r'[¹²³⁴⁵⁶⁷⁸⁹⁰†‡™®]','',l)
    return re.sub(r'\s+',' ',l).strip(' .;:')
def _tu_edition(t):
    """Tu khoa ban dac biet theo RANH GIOI TU DAY DU ('Golden Light' KHONG phai Gold)."""
    t=(t or '').lower(); return next((k for k in TEN_BAN if re.search(r'\b'+k+r'\b',t)),None)
def la_ban_dac_biet(ed):
    """edition khac ban thuong: loai PREMIUM, hoac TEN EDITION co tu khoa ban dac biet nguyen tu (Deluxe/Ultimate/...); loai STANDARD / ten ghi 'standard' -> khong. Khong suy tu ten game."""
    if not ed or not ed.get('ten'): return False
    if 'standard' in ed['ten'].lower() or (ed.get('loai') or '').upper()=='STANDARD': return False
    return (ed.get('loai') or '').upper()=='PREMIUM' or _tu_edition(ed['ten']) is not None
def ten_ban_noi(ed):
    return TEN_BAN.get(_tu_edition((ed or {}).get('ten','')),'này')
def _so_luong_vu_khi(low):
    """So vu khi CHI khi ghi ro: '(5 weapons)', 'two weapons', 'weapon x2'; 'weapon' so it khong so -> 1; 'weapons' so nhieu khong so -> None (khong ro). Tra (so|None)."""
    m=re.search(r'\b(\d+|one|two|three|four|five|six|seven|eight|nine)\s+(?:[\w\'-]+\s+){0,2}weapons?\b',low) or re.search(r'\bweapons?\s*[x×]\s*(\d+)',low)
    if m: g=m.group(1); return int(g) if g.isdigit() else _SO_EN[g]
    if re.search(r'weapons\b|\bpack\b|\bbundle\b|\bset\b',low): return None
    return 1
def _dan_edition(khoi,ten_edition):
    """Khoi dau mo ta dai -> (bullets, dung_som, ngay_choi_som). Bullet chi tinh khi DONG DAN ngay truoc la tieu de noi dung edition: '<Edition> includes/contains/comes with:' (nhac ten edition / 'edition' / 'bundle' / 'pack'),
    khong phai 'Game features:' hay mo ta gameplay."""
    i=next((k for k,l in enumerate(khoi) if re.match(r'^[-–•*·]\s*\S',l)),None)
    if i is None or i==0: return [],False,None
    dan=' '.join(khoi[:i])
    if not re.search(r'\b(?:includes?|contains?|comes\s+with)\b',dan,re.I): return [],False,None
    ten=re.sub(r'\b(?:edition|digital|bundle|pack)\b','',(ten_edition or ''),flags=re.I).strip().lower()
    if not (re.search(r'\b(?:edition|bundle|pack)\b',dan,re.I) or (ten and ten in dan.lower())): return [],False,None
    if re.match(r'\s*(?:game|key)\s+features',dan,re.I): return [],False,None
    bullets=[l for l in khoi[i:] if re.match(r'^[-–•*·]\s*\S',l)]
    som=bool(re.search(r'early\s+access\s+to\s+(?:the\s+following\s+)?(?:in-?game\s+)?(?:items|content|weapons|gear|outfits)',dan,re.I)) and bool(re.search(r'obtainable|unlock|story\s+progression|progression',dan,re.I))
    m=re.search(r'(\d+)[\s-]*days?\s+(?:of\s+)?early\s+access|early\s+access.{0,40}?(\d+)\s*days?',dan,re.I|re.S)
    ngay=int(next(g for g in m.groups() if g)) if m and not som else None
    return bullets,som,ngay
def phan_them(mo_ta_dai,tinh_nang=(),ten_edition=''):
    """-> (muc[], dong_goc[], dung_som). Chi lay tu khoi noi dung edition RO RANG (xem _dan_edition) hoac edition.features (cau truc). Muc ngoai bang -> bo (khong doan)."""
    ds=_dong(mo_ta_dai); i=0
    while i<len(ds) and not ds[i]: i+=1
    khoi=[]
    while i<len(ds) and ds[i]: khoi.append(ds[i]); i+=1
    bullets,som,ngay=_dan_edition(khoi,ten_edition)
    goc=[_lam_sach(l) for l in (bullets or list(tinh_nang))]; goc=[g for g in goc if g]
    dem={}
    for g in goc:
        low=g.lower()
        for k in _THU_TU_DONG:
            if re.search(next(m for kk,m,_,_,_ in THEM if kk==k),low):
                if k=='vu_khi':
                    n=_so_luong_vu_khi(low); a=dem.setdefault(k,[0,False,False]); a[2]=a[2] or ('pack' in low)
                    if n is None: a[1]=True
                    else: a[0]+=n
                else: dem.setdefault(k,[1,False,False])
                break
    muc=[]
    for kk,_,noi,hien,dem_so in THEM:
        if kk not in dem: continue
        n,mo,goi=dem[kk]
        if kk=='vu_khi':
            if mo or not 0<n<100: txt='gói vũ khí' if goi else 'vũ khí'; muc.append(dict(k=kk,so=0,noi=txt,hien=txt[0].upper()+txt[1:]))
            else: muc.append(dict(k=kk,so=n,noi=f'{so_chu(n)} {noi}',hien=f'{n} {hien}'))
        else: muc.append(dict(k=kk,so=1,noi=noi,hien=hien[0].upper()+hien[1:]))
    if ngay and 0<ngay<100 and bullets: muc.append(dict(k='choi_som',so=ngay,noi=f'chơi sớm {so_chu(ngay)} ngày',hien=f'Chơi sớm {ngay} ngày'))
    muc=muc[:4]
    if som and muc:   # "dung som" CHI cho vat pham / vu khi (cau dan noi early access toi in-game items); khong gan cho nhac / avatar / ...
        m=next((x for x in muc if x['k']=='vat_pham'),None) or next((x for x in muc if x['k']=='vu_khi'),None)
        if m: m['noi']+=' dùng sớm'; m['hien']+=' dùng sớm'; m['dung_som']=True
    return muc,goc,bool(som and muc and any(x.get('dung_som') for x in muc))
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
    co=che_do_co_op(low)
    if co: dd.append(dict(k=co,noi=CO_OP[co][0],hien=CO_OP[co][1]))
    dd.sort(key=lambda x:THU_TU_DD.index(x['k'])); dd=dd[:2]
    d=tt.get('diem'); diem=None
    if d and d.get('so_luot',0)>=MIN_LUOT:
        r=lam_tron_diem(d['tb']); diem=dict(tb=d['tb'],lam_tron=r,so_luot=d['so_luot'],noi=noi_diem(r),hien=hien_diem(r),luot=hien_luot(d['so_luot']))
    ban=None; ed=tt.get('edition')
    if la_ban_dac_biet(ed):
        muc,goc,ds=phan_them(tt.get('mo_ta_dai'),(ed or {}).get('tinh_nang') or [],(ed or {}).get('ten',''))
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

# ---------- CUM MO (12/10): cum cam than DUNG TRUOC ten game cua doan `mo`; 3 khung Keo trong ngay khong doc cung 1 cum.
# Cau mo van la «<cum> <ten> đang giảm <x> phần trăm trên PS Store <vung> nè!» — kiem-tat-ca.py (D3) tim chu `đang` DAU TIEN cua doan `mo` de cat ten game
# => cum mo KHONG DUOC chua tu `đang`. Moi cum co dung 1 tu `em` (full.html giat nhe o khoa `em`: M.mo.em) -> kich-ban.py gan khoa `em` cho tu do.
CUM_MO=['Ê anh em!!','Anh em ơi!!','Khoan lướt đã anh em!!','Tin vui nè anh em!!','Hàng ngon nè anh em!!','Chú ý nè anh em!!','Nghe này anh em!!','Dừng tay chút anh em!!']
KHUNG_KEO={'keo-thom-2':0,'keo-thom':1,'keo-thom-3':2}   # thu tu theo gio dang trong ngay (15:00 · 20:00 · 22:00)
def cum_mo(ngay_dang,dang):
    """Chon cum mo theo (ngay, khung): chi so = (3*so_ngay + thu_tu_khung) % len(CUM_MO). len=8 va buoc 3 nguyen to cung nhau =>
    (a) 3 khung cung ngay ra 3 cum KHAC nhau; (b) moi khung KHAC cum cua chinh khung do hom truoc (chi so lech 3 mod 8); (c) khong khung nao lap cum trong 2 ngay lien tiep.
    Khong biet khung (thieu DANG / khung la) hoac khong co ngay -> 'Ê anh em!!' (hanh vi cu)."""
    if dang not in KHUNG_KEO or not ngay_dang: return CUM_MO[0]
    n=datetime.date.fromisoformat(str(ngay_dang)[:10]).toordinal()
    return CUM_MO[(3*n+KHUNG_KEO[dang])%len(CUM_MO)]

# ================= KHUON KEO v10 (Hao chot 12/10/2026, ke-hoach-noi-dung/01-quyet-dinh-va-ke-hoach-keo-v10.md) =================
# Quyet dinh nen tang: moi video phai TRA LOI cau nguoi xem hoi (mua o dau re nhat / co dang mua khong / ban nao) va MO bang cau TINH HUONG
# (Facebook goc: "them thong tin moi hoac phan tich"; YouTube YPP "inauthentic"). Hai thay doi chu trong khung doan co dinh mo · gia · gioi · dap · han · ket:
#   A. CAU MO TINH HUONG (thay cum cam than): 3 kieu xoay theo (ngay, khung) — so gia voi mon quen · so sao · giam sau; khong du dieu kien -> cum cam than cu (CUM_MO).
#   B. CAU KET LUAN cuoi doan `gioi` (khong so moi), nhanh theo diem + so luot.
#   C. doan `ket` doi thanh «Theo doi Săn Game de khong lo keo nao nha!» (kich-ban.py).
# KHONG goi AI: moi cau la khuon co dinh + so lay tu keo.json. Moi so trong cau mo phai qua D3 (kiem-tat-ca.py 5d: tien / sao / phan tram, so theo GIA TRI).
# Bang nguong so gia (con_vnd, DONG TIEN CON LAI): <= moc dau tien khop. > moc cuoi cung (600.000) -> khong dung kieu nay.
# (v10, Opus duyet 12/10: cau mo KHONG doc so tien — gia con da nam o doan `gia`; chi giu cum so sanh, chon theo con_vnd.)
BANG_SO_GIA=((45000,'Rẻ hơn một ly trà sữa'),(110000,'Chưa bằng một vé xem phim'),(600000,'Chưa bằng một bữa lẩu cho bốn người'))
SAO_TOI_THIEU_SO_GIA=4.0      # kieu 1 chi nhac "mot game X sao" khi diem >= 4,0 (diem da lam tron 1 chu so, cung so voi cau gioi thieu)
SAO_KIEU_SAO=4.5; LUOT_KIEU_SAO=200       # kieu 2: diem >= 4,5 va >= 200 luot
GIAM_KIEU_GIAM_SAU=50                     # kieu 3: giam >= 50%
KIEU_MO=('so_gia','so_sao','giam_sau')    # thu tu xoay; fallback: kieu uu tien -> 2 kieu con lai (thu tu XOAY theo khung) -> cum cam than (CUM_MO)
def kieu_uu_tien(ngay_dang,dang):
    """Kieu uu tien theo (ngay, khung) = (so_ngay + thu_tu_khung) % 3: 3 khung CUNG NGAY ra 3 kieu KHAC nhau; CUNG KHUNG hom sau sang kieu ke tiep (khac hom truoc).
    Khong biet khung / khong co ngay -> None (hanh vi cu: cum cam than)."""
    if dang not in KHUNG_KEO or not ngay_dang: return None
    return (datetime.date.fromisoformat(str(ngay_dang)[:10]).toordinal()+KHUNG_KEO[dang])%3
def _diem_lam_tron(diem):
    """diem = gioi_thieu['diem'] (tb, so_luot) hoac None -> (r lam tron 1 chu so, so_luot) | (None,0)."""
    if not diem or diem.get('tb') is None: return None,0
    return lam_tron_diem(diem['tb']),int(diem.get('so_luot') or 0)
def _hop_le_kieu(k,con_vnd,giam,diem):
    r,luot=_diem_lam_tron(diem)
    if k=='so_gia': return con_vnd is not None and 1000<=con_vnd<=BANG_SO_GIA[-1][0]
    if k=='so_sao': return r is not None and r>=SAO_KIEU_SAO and luot>=LUOT_KIEU_SAO
    if k=='giam_sau': return giam is not None and giam>=GIAM_KIEU_GIAM_SAU
    return False
def cau_mo(ngay_dang,dang,con_vnd,giam,diem):
    """CAU MO doan `mo`, dung TRUOC ten game, KHONG chua tu `đang` (D3 5b cat ten game tai `đang` dau tien). -> dict(kieu, loi, ky_vong).
    kieu: 'so_gia' (so sanh gia con voi mon quen, KHONG doc so tien) | 'so_gia_sao' (nhu tren + «mot game X sao») | 'so_sao' | 'giam_sau' | 'cum' (cum cam than CUM_MO, giu khoa `em`).
    ky_vong = {'tien':[] (v10: cau mo khong doc tien), 'sao':[diem], 'phan_tram':[giam]} — cac so xuat hien trong cau mo (D3 doc theo GIA TRI)."""
    r,_=_diem_lam_tron(diem); p=kieu_uu_tien(ngay_dang,dang)
    if p is not None:
        # kieu uu tien truoc; du phong XOAY THEO KHUNG (Sol P2): khung thu tu chan (keo-thom-2, keo-thom-3) thu p+1 roi p+2, khung le (keo-thom) thu p+2 roi p+1
        nho=(1,2) if KHUNG_KEO[dang]%2==0 else (2,1)
        for k in [KIEU_MO[p]]+[KIEU_MO[(p+i)%3] for i in nho]:
            if not _hop_le_kieu(k,con_vnd,giam,diem): continue
            if k=='so_gia':
                ss=next(c for m,c in BANG_SO_GIA if con_vnd<=m); co_sao=r is not None and r>=SAO_TOI_THIEU_SO_GIA
                cau=f"{ss}, mà mua được "+(f"một game {noi_diem(r)} sao" if co_sao else 'game này')+" nè."
                kv={'tien':[],'sao':[r] if co_sao else [],'phan_tram':[]}
                return dict(kieu='so_gia_sao' if co_sao else 'so_gia',loi=cau,ky_vong=kv)
            if k=='so_sao': return dict(kieu='so_sao',loi=f"Game {noi_diem(r)} sao mà giờ giảm sâu nè.",ky_vong={'tien':[],'sao':[r],'phan_tram':[]})
            return dict(kieu='giam_sau',loi=f"Giảm {so_chu(giam)} phần trăm, kèo này hiếm nha.",ky_vong={'tien':[],'sao':[],'phan_tram':[int(giam)]})
    return dict(kieu='cum',loi=cum_mo(ngay_dang,dang),ky_vong={'tien':[],'sao':[],'phan_tram':[]})

# ---------- CAU KET LUAN cuoi doan `gioi` (B). Tham so theo DIEM DA LAM TRON (nhu video noi) + so luot. Khong so moi.
KET_LUAN_DANG_MUA='Với giá này thì đáng mua.'
KET_LUAN_HOP='Hợp với ai thích thể loại này.'
KET_LUAN_CAN_NHAC='Chỉ nên mua nếu bạn thật sự thích game này.'
KET_LUAN_ALL=(KET_LUAN_DANG_MUA,KET_LUAN_HOP,KET_LUAN_CAN_NHAC)
def ket_luan(diem):
    """diem = gioi_thieu['diem'] hoac None. r>=4,5 va luot>=200 -> dang mua · 4,0<=r<4,5 va luot>=50 -> hop voi ai thich · con lai (r<4,0, luot<50, khong co diem) -> chi nen mua neu thich.
    LUU Y: gioi_thieu_tu_trang bo `diem` khi luot < MIN_LUOT (200) nen nhanh luot 50..199 chi chay khi chon-keo ghi diem voi luot thap (hien chua)."""
    r,luot=_diem_lam_tron(diem)
    if r is None: return KET_LUAN_CAN_NHAC
    if r>=4.5 and luot>=200: return KET_LUAN_DANG_MUA
    if 4.0<=r<4.5 and luot>=50: return KET_LUAN_HOP
    return KET_LUAN_CAN_NHAC

# ================= BIET TRUOC KHI MUA (G3, 13/10/2026; 22-dac-ta-dot-1.md) =================
# 1-2 cau chen CUOI doan `gioi`, TRUOC cau ket luan (6 khoa doan va moi neo cu giu nguyen). Du lieu = keo.json.biet_truoc (chon-keo.py ← cong-cu/gia_trang.biet_truoc cua DUNG vung re nhat).
# Cau chi phat khi DU BANG CHUNG (Sol #13): thieu truong -> khong cau. Khuon cau co dinh, khong goi AI.
#   phu_de   : screenLanguages co 'vi' -> «Game có phụ đề tiếng Việt.» · khong co 'vi' nhung co 'en' -> «Game chưa có phụ đề tiếng Việt, có tiếng Anh.» · con lai: khong cau
#   online   : online='tuy_chon' va can_plus_online=True -> «Chơi một mình không cần PS Plus, chơi online cần gói.» · online='bat_buoc' va can_plus_online=True -> «Game cần mạng và gói PS Plus để chơi online.»
#   so_nguoi : chi khi online la tuy_chon/bat_buoc va so_nguoi_online >= 2 -> «Chơi online được tối đa <so chu> người.»
# Toi da 2 cau; thu tu/cap chon xoay theo (ngay, khung) nhu cum_mo. D3 (kiem-tat-ca.py) tinh LAI gia tri tu keo.json qua biet_truoc_ky_vong().
CAU_PHU_DE_CO='Game có phụ đề tiếng Việt.'
CAU_PHU_DE_CHUA='Game chưa có phụ đề tiếng Việt, có tiếng Anh.'
CAU_ONLINE_TUY_CHON='Chơi một mình không cần PS Plus, chơi online cần gói.'
CAU_ONLINE_BAT_BUOC='Game cần mạng và gói PS Plus để chơi online.'
KIEU_BIET_TRUOC=('phu_de','online','so_nguoi')
def _co_ngon_ngu(ds,ma): return any(isinstance(x,str) and x.lower().replace('-','_').split('_')[0]==ma for x in (ds or []))
def phu_de_viet(bt):
    """-> 'co' | 'chua' | None (thieu bang chung). 'co' khi screenLanguages co vi; 'chua' CHI khi co danh sach ngon ngu, khong co vi, va co en (de nói «có tiếng Anh»)."""
    sl=(bt or {}).get('screenLanguages')
    if not sl: return None
    if _co_ngon_ngu(sl,'vi'): return 'co'
    return 'chua' if _co_ngon_ngu(sl,'en') else None
def che_do_online(bt):
    """-> 'tuy_chon' | 'bat_buoc' | None: CHI khi trang ghi ro online + 'PS Plus required' (can_plus_online True)."""
    bt=bt or {}
    return bt['online'] if bt.get('online') in ('tuy_chon','bat_buoc') and bt.get('can_plus_online') is True else None
def so_nguoi_online(bt):
    bt=bt or {}; n=bt.get('so_nguoi_online')
    return n if che_do_online(bt) and isinstance(n,int) and not isinstance(n,bool) and 2<=n<=99 else None
def cac_cau_biet_truoc(bt):
    """Moi cau ung vien du bang chung, theo thu tu co dinh phu_de · online · so_nguoi -> [dict(kieu, loi)]."""
    ra=[]; pd=phu_de_viet(bt)
    if pd: ra.append(dict(kieu='phu_de',loi=CAU_PHU_DE_CO if pd=='co' else CAU_PHU_DE_CHUA))
    on=che_do_online(bt)
    if on: ra.append(dict(kieu='online',loi=CAU_ONLINE_TUY_CHON if on=='tuy_chon' else CAU_ONLINE_BAT_BUOC))
    n=so_nguoi_online(bt)
    if n: ra.append(dict(kieu='so_nguoi',loi=f'Chơi online được tối đa {so_chu(n)} người.'))
    return ra
def cau_biet_truoc(bt,ngay_dang,dang,toi_da=2):
    """Chon <= toi_da cau tu cac cau du bang chung, XOAY theo (ngay, khung): bat dau tu vi tri (3*so_ngay + thu_tu_khung) % so_cau, lay lien tiep vong tron. -> [dict(kieu, loi)] ([] neu khong co bang chung).
    Khong biet khung / khong co ngay -> bat dau o vi tri 0."""
    ds=cac_cau_biet_truoc(bt)
    if not ds: return []
    s=0
    if dang in KHUNG_KEO and ngay_dang: s=(3*datetime.date.fromisoformat(str(ngay_dang)[:10]).toordinal()+KHUNG_KEO[dang])%len(ds)
    return [ds[(s+i)%len(ds)] for i in range(min(toi_da,len(ds)))]
def biet_truoc_ky_vong(bt,cac_kieu):
    """Gia tri KY VONG cho D3 tu keo.json.biet_truoc va danh sach kieu da doc (kich-ban.json.doan[gioi].bt) -> [(kieu_menh_de, gia_tri)] cho nghe_so.doi_chieu(biet_truoc=...).
    Gia tri None khi keo.json KHONG du bang chung ma kich-ban van doc cau do -> D3 TRUOT (khong tu tin kich-ban.json)."""
    ra=[]
    for k in cac_kieu or []:
        if k=='phu_de': ra.append(('phu_de',phu_de_viet(bt)))
        elif k=='online': ra.append(('ps_plus',che_do_online(bt)))
        elif k=='so_nguoi': ra.append(('so_nguoi',so_nguoi_online(bt)))
        else: ra.append((k,None))
    return ra
def the_biet_truoc(bt,cac_kieu):
    """Chu tren cac THE nho cuoi ho so game (full.html theBT() lam y het; kiem-tat-ca.py D1 tinh LAI o day, doc lap voi JS) cho dung cac kieu cau da doc. Thieu bang chung -> '?<kieu>' (khong the nao khop hinh)."""
    ra=[]
    for k in cac_kieu or []:
        pd=phu_de_viet(bt); on=che_do_online(bt); n=so_nguoi_online(bt)
        if k=='phu_de': ra.append('PHỤ ĐỀ VIỆT '+('✓' if pd=='co' else '✗') if pd else '?phu_de')
        elif k=='online': ra.append(('PHẢI ONLINE + PS PLUS' if on=='bat_buoc' else 'ONLINE CẦN PS PLUS') if on else '?online')
        elif k=='so_nguoi': ra.append(f'TỐI ĐA {n} NGƯỜI ONLINE' if n else '?so_nguoi')
        else: ra.append('?'+str(k))
    return ra[:3]
