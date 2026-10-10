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
    if n>=100:   # tu 1 trieu tro len
        tr,r=divmod(n,100); r=r//10 if r%10==0 else None
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
