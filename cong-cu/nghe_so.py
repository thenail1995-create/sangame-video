# Doc so / vung / han / ten game tu ban Whisper cho phep D3 cua 3 khuon (Top 5, Tin nhanh, Keo thom) — SO GIA TRI, KHONG SO CHU.
# Ly do (Sol soi 11/10, loi #7-#13, #17): D3 cu so do giong chu ("sau muoi bay" khop trong "mot tram sau muoi bay nghin", 64% giong 54%, "Resident Evil nam" giong
# "... bon") nen doc sai tien/phan tram/vung/ten van DAT. Moi ham o day tra GIA TRI da doc, nguoi goi so bang `==`.
#   doc_tien(van_ban)      -> [(gia_tri_vnd, tien_to, vi_tri)]   "mot tram sau muoi bay nghin" / "167.000" / "167k" / "1,3 trieu" / "sau tram ruoi" (=650.000)
#   doc_phan_tram(van_ban) -> [(so, vi_tri)]                     "54%" / "54 phan tram" / "chin muoi phan tram"
#   doc_vung(van_ban)      -> [(ma, vi_tri)]                     My/Hoa Ky->US, Hong Kong->HK, Sing->SG, Thai->TH, Indo->ID, An Do->IN
#   doc_han(van_ban)       -> [{gio24, buoi, ngay}]              "hai gio chieu ngay hai muoi hai thang muoi" / "muoi gio dem ngay mai"
#   doc_ngay(van_ban)      -> [(ngay, thang)]                    "het giam ngay hai muoi mot thang muoi" (khong can gio)
#   so_ten(mong, nghe)     -> (dat, ly_do)                       token phan biet (so phan, so La Ma, so chu, Deluxe/Remake/...) phai KHOP CHINH XAC; phan con lai theo nguong 0,40
# `doi_chieu` gom cac phep tren cho mot doan; `nghe_doan` nghe tren am thanh MP4 cuoi (+ cache theo bam PCM de 3 ban chung mot lan Whisper).
# Chu thich file nay khong dau theo phong cach repo; chuoi tieng Viet trong ma giu day du dau (Whisper tra chu co dau; "sáu" != "sau").
import datetime,difflib,hashlib,json,pathlib,re,unicodedata
from collections import Counter

def nfc(t): return unicodedata.normalize('NFC',t or '')
def bo_dau(t):
    """Bo dau, 'đ'->'d', chu thuong; GIU nguyen do dai chuoi (vi_tri van dung cho van ban goc)."""
    ra=[]
    for c in nfc(t):
        c=c.lower()
        if c=='đ': ra.append('d'); continue
        d=unicodedata.normalize('NFD',c)
        ra.append(d[0] if d else c)
    return ''.join(ra)

# ---------------------------------------------------------------- tach token
CHU_SO={'không':0,'một':1,'hai':2,'ba':3,'bốn':4,'năm':5,'sáu':6,'bảy':7,'bẩy':7,'tám':8,'chín':9}
DON_VI_SAU={'mốt':1,'tư':4,'lăm':5,'nhăm':5}      # chi hop le sau mươi / mười / trăm
NGHIN={'nghìn','ngàn','nghin','ngan'}; TRIEU={'triệu','trieu'}; RUOI={'rưỡi','rưởi','rưỡi'}
LE={'lẻ','linh','lẽ'}; DONG={'đồng','đ','vnd','vnđ','dong'}
TIEN_TO_TU={'gần','hơn','khoảng','đúng','tầm','chừng','xấp','xỉ'}
NON_TIEN_SAU={'game','giờ','tháng','ngày','phút','giây','hạng','lần','người','tin','vùng','store','bản','tuổi','điểm','giải','phần','cái','món'}
NON_TIEN_TRUOC={'hạng','top','tháng','ngày','tin','thứ','phần','chương','số'}
_TOK=re.compile(r"\d+(?:[.,]\d+)*|[^\W\d_]+|%")
_NGAT=re.compile(r"[.,;:!?…\n]")
def _tach(van_ban):
    """-> [(loai, gia_tri, brk, vi_tri)]: loai 's' (so viet bang chu so) | 'w' (tu, da thuong + NFC; '%' cung la 'w'); brk = co dau cau ngan voi token truoc."""
    t=nfc(van_ban); ra=[]; fin=0
    for m in _TOK.finditer(t):
        s=m.group()
        ra.append(('s' if s[0].isdigit() else 'w', s if s[0].isdigit() else s.lower(), (not ra) or bool(_NGAT.search(t[fin:m.start()])), m.start())); fin=m.end()
    return ra
def _w(T,k): return T[k][1] if 0<=k<len(T) and T[k][0]=='w' else None
def _lien(T,k): return 0<k<len(T) and not T[k][2]
def _dg(s):
    """token chu so -> (gia_tri, loai): 'nhom' 167.000 | 'thap' 1,3 | 'nguyen' 167"""
    if re.fullmatch(r'\d{1,3}(?:[.,]\d{3})+',s): return int(re.sub(r'[.,]','',s)),'nhom'
    if re.fullmatch(r'\d+[.,]\d+',s): return float(s.replace(',','.')),'thap'
    if re.fullmatch(r'\d+',s): return int(s),'nguyen'
    return None,None

# ---------------------------------------------------------------- doc so bang chu 0..999
def _ba(T,i):
    """Doc so 0..999 bang chu bat dau o T[i] -> (gia_tri, tat, j, hang) | None.
    tat=True: dang noi tat ('mot tram hai' = 120, 'sau tram ruoi' = 650: don vi lap ngam la chuc nghin). hang: 'don' (1 chu so) | 'chuc' | 'tram'."""
    w=_w(T,i)
    if w is None: return None
    def nho(k):
        x=_w(T,k) if _lien(T,k) else None
        if x is None: return None
        if x in CHU_SO and x!='không': return CHU_SO[x]
        return DON_VI_SAU.get(x)
    if w in CHU_SO and (w!='không' or (_w(T,i+1)=='trăm' and _lien(T,i+1))):
        d=CHU_SO[w]; k=i+1; x=_w(T,k) if _lien(T,k) else None
        if x=='trăm':
            h=d; k+=1; x2=_w(T,k) if _lien(T,k) else None
            if x2 in LE:
                u=nho(k+1)
                return (h*100+u,False,k+2,'tram') if u is not None else (h*100,False,k,'tram')
            if x2=='mười':
                u=nho(k+1); return h*100+10+(u or 0),False,k+1+(u is not None),'tram'
            if x2 is not None and (x2 in CHU_SO or x2 in DON_VI_SAU) and x2!='không':
                dd=CHU_SO.get(x2) or DON_VI_SAU[x2]
                if dd>=2 and _w(T,k+1)=='mươi' and _lien(T,k+1):
                    u=nho(k+2); return h*100+dd*10+(u or 0),False,k+2+(u is not None),'tram'
                return h*100+dd*10,True,k+1,'tram'
            if x2 in RUOI: return h*100+50,True,k+1,'tram'
            return h*100,False,k,'tram'
        if x=='mươi' and d>=2:
            u=nho(k+1); return d*10+(u or 0),False,k+1+(u is not None),'chuc'
        if x=='chục': return d*10,False,k+1,'chuc'
        return d,False,i+1,'don'
    if w=='mười':
        u=nho(i+1); return 10+(u or 0),False,i+1+(u is not None),'chuc'
    return None
def _so(T,i):
    if i>=len(T): return None
    if T[i][0]=='s':
        g,loai=_dg(T[i][1])
        if g is None: return None
        if loai=='nguyen' and 100<=g<=900 and g%100==0 and _w(T,i+1) in RUOI and _lien(T,i+1): return g+50,True,i+2,'tram'     # Whisper viet 'sáu trăm rưỡi' = '600 rưỡi'
        return g,False,i+1,loai
    return _ba(T,i)
def _pt_het(T,j):
    """neu T[j:] la 'phan tram' / '%' -> chi so sau cum, nguoc lai None"""
    if _w(T,j)=='%' : return j+1
    if _w(T,j)=='phần' and _lien(T,j) and _w(T,j+1)=='trăm' and _lien(T,j+1): return j+2
    return None

# ---------------------------------------------------------------- tien
def _tien_tu(T,i,r):
    """Doc mot khoi tien bat dau o T[i] (r = ket qua _so) -> (vnd, j) | None."""
    v,tat,j,hang=r
    x=_w(T,j) if _lien(T,j) else None
    if x in TRIEU:
        tong=round(v*1_000_000); j+=1
        if _w(T,j) in RUOI and _lien(T,j): return tong+500_000,j+1
        r2=_so(T,j) if _lien(T,j) else None
        if r2:
            v2,t2,j2,h2=r2; y=_w(T,j2) if _lien(T,j2) else None
            if y in NGHIN or y=='k': return tong+round(v2*1000),j2+1
            if _pt_het(T,j2) is not None or h2=='thap': return tong,j       # (khong chan theo 'giờ': 'hai triệu hai… giờ còn có' Whisper nghe '2 triệu 2 giờ còn có')
            if h2=='nhom' and v2<1_000_000: return tong+v2,j2                      # '1 triệu 48.000' = 1.048.000 (CI that 11/10: Whisper viet 'một triệu không trăm bốn mươi tám nghìn' nhu vay)
            if h2=='don' or (h2=='nguyen' and v2<10): return tong+v2*100_000,j2     # 'mot trieu ba' = 1.300.000
            return tong+round(v2*1000),j2                                           # 'mot trieu ba tram' = 1.300.000 ; 'mot trieu nam muoi' = 1.050.000
        return tong,j
    if x in NGHIN or x=='k': return round(v*1000),j+1
    if x in DONG:
        j+=1
        return int(round(v)),j        # 'đồng/đ' GIỮ NGUYÊN giá trị (167 đồng = 167 đ, không phải 167.000; Sol vòng 2b #4)
    if x in NON_TIEN_SAU: return None
    if i>0 and not T[i][2] and _w(T,i-1) in NON_TIEN_TRUOC: return None
    if hang=='nhom': return v,j
    if hang=='thap': return None
    if hang=='nguyen' and v>=1000: return v,j
    return round(v*1000),j       # khong co don vi trong ngu canh tien -> nghin (luat B1)
def doc_tien(van_ban):
    """-> [(gia_tri_vnd, tien_to, vi_tri)] theo thu tu xuat hien. Con so di kem 'phan tram' / '%' la PHAN TRAM, khong bao gio la tien."""
    return [(v,tt,p) for v,tt,p,_ in doc_tien_ct(van_ban)]
def doc_tien_ct(van_ban):
    """Nhu doc_tien nhung them nguon: 'b' = so TRAN 3 chu so khong nhom nghin, khong don vi ("706", khong phai "706.000" / "706 dong" / "706 nghin" / "706k") - DUY NHAT dang nay duoc
    bi danh «noi tat» (xem noi_tat_literal); 's' = cac khoi tien bat dau bang chu so con lai ("706.000 dong", "167k"); 'c' = viet bang chu ("bay tram le sau nghin")."""
    T=_tach(van_ban); kq=[]; i=0
    while i<len(T):
        r=_so(T,i)
        if not r: i+=1; continue
        pj=_pt_het(T,r[2])
        if pj is not None: i=pj; continue
        t=_tien_tu(T,i,r)
        if t is None: i=max(i+1,r[2]); continue
        vnd,j=t
        if _w(T,j) in DONG and _lien(T,j): j+=1
        tt=_w(T,i-1) if i>0 and not T[i][2] and _w(T,i-1) in TIEN_TO_TU else ''
        ng='c'
        if T[i][0]=='s':
            ng='s'; nx=_w(T,i+1) if _lien(T,i+1) else None
            if re.fullmatch(r'[1-9]\d\d',T[i][1]) and nx not in NGHIN and nx not in TRIEU and nx not in DONG and nx not in RUOI and nx!='k' and vnd==int(T[i][1])*1000: ng='b'
        kq.append((vnd,tt,T[i][3],ng)); i=j
    return kq
def doc_phan_tram(van_ban):
    """-> [(so, vi_tri)]"""
    T=_tach(van_ban); kq=[]; i=0
    while i<len(T):
        r=_so(T,i)
        if not r: i+=1; continue
        pj=_pt_het(T,r[2])
        if pj is None: i=max(i+1,r[2]); continue
        v=r[0]; kq.append((int(v) if float(v).is_integer() else v,T[i][3])); i=pj
    return kq

# ---------------------------------------------------------------- vung
# 'sinh'/'xinh' (SG): Whisper small nghe 'Sing' thanh 'sinh' tren video that thu-d; bi danh CHI dung o doc_vung
VUNG_MAU=[('US',r'my|hoa ky|usa'),('HK',r'hong ?kong|hong kon|hongkong|honkong'),('SG',r'singapore|singapo|xin[ -]ga[ -]po|sin[ -]ga[ -]po|sing|sinh|xinh'),
          ('TH',r'thai lan|thai'),('ID',r'indonesia|indo|in do'),('IN',r'an do|ando|india')]
VUNG_HIEN={'US':'MỸ','HK':'HỒNG KÔNG','SG':'SINGAPORE','TH':'THÁI LAN','ID':'INDONESIA','IN':'ẤN ĐỘ'}   # chu hoa tren hinh (dung chung khi so DOM)
def doc_vung(van_ban):
    """-> [(ma, vi_tri)] ; ma trong US/HK/SG/TH/ID/IN."""
    t=bo_dau(van_ban); kq=[]
    for ma,mau in VUNG_MAU:
        for m in re.finditer(r'(?<![a-z0-9])(?:'+mau+r')(?![a-z0-9])',t): kq.append((ma,m.start()))
    return sorted(kq,key=lambda x:x[1])

# ---------------------------------------------------------------- han (Keo thom)
# 'kháng' = bi danh CO CHU DICH cua 'tháng' (Whisper nghe 'ngày 22 tháng 10' thanh 'ngày 22 kháng 10' tren giong CI 11/10, ca small lan large-v3-turbo); CHI trong mau 'ngày <số> (tháng|kháng) <số>', van so GIA TRI ngay+thang.
THANG_NGAY=('tháng','kháng')
BUOI=('sáng','trưa','chiều','tối','đêm')
def buoi_cua(gio24):
    """Giong loi_chu.buoi: gio 1..23 -> (so doc 1..12, buoi)"""
    if gio24<=10: return gio24,'sáng'
    if gio24<=12: return gio24,'trưa'
    if gio24<=17: return gio24-12,'chiều'
    if gio24<=21: return gio24-12,'tối'
    return gio24-12,'đêm'
def han_ky_vong(het,ngay_dang):
    """Han ky vong theo DUNG luat noi_han() cua loi_chu: het = datetime (VN) luc het giam, ngay_dang = date.
    -> dict(gio24, buoi, ngay): ngay = 'nay' | 'mai' | 'kia' | (ngay, thang). Gio le (13:59) doc la gio tron KE TIEP; 00:00 = nua dem cua ngay truoc."""
    gio=het.hour+(1 if (het.minute or het.second) else 0); ngay=het.date()
    if gio==0: ngay-=datetime.timedelta(days=1); gio=24
    buoi='nửa đêm' if gio>=24 else buoi_cua(gio)[1]
    d=(ngay-ngay_dang).days
    return dict(gio24=gio,buoi=buoi,ngay='nay' if d==0 else 'mai' if d==1 else 'kia' if d==2 else (ngay.day,ngay.month))
def _gio_24(so,buoi):
    if buoi in ('chiều','tối','đêm') and so<12: return so+12
    return so
def doc_han(van_ban):
    """-> [dict(gio24, buoi, ngay)] ; buoi/ngay co the None neu khong nghe duoc."""
    t=re.sub(r'(?<=\d)\s*/\s*(?=\d)',' tháng ',nfc(van_ban)); T=_tach(t); kq=[]
    for i,(lo,gt,_,_) in enumerate(T):
        gio24=buoi=None; j=None
        if lo=='w' and gt=='nửa' and _w(T,i+1)=='đêm' and _lien(T,i+1): gio24,buoi,j=24,'nửa đêm',i+2
        elif lo=='w' and gt in ('giờ','h') and i>0:
            # lui lai tim so dung ngay truoc 'giờ'
            for b in range(max(0,i-6),i):
                r=_so(T,b)
                if r and r[2]==i and r[0]==int(r[0]) and 0<=r[0]<=24: gio=int(r[0]); break
            else: continue
            j=i+1; x=_w(T,j) if _lien(T,j) else None
            buoi=x if x in BUOI else None
            if buoi: j+=1; gio24=_gio_24(gio,buoi)
            elif gio>12: gio24=gio; buoi=buoi_cua(gio)[1]
            else: gio24=-gio     # co gio, khong nghe buoi -> khong the khop (gio24 am)
        else: continue
        ngay=None; x=_w(T,j) if _lien(T,j) else None
        if x=='nay': ngay='nay'
        elif x in ('ngày','này'):
            # 'này' = bi danh CO CHU DICH cua 'ngày' CHI trong mau '<giờ> <buổi> này <số> (tháng|kháng) <số>' (12/10: turbo nghe giong
            # 'mười giờ đêm ngày 21 tháng 10' thanh 'đêm này 21 tháng 10' - run 38210460267). 'này mai/kia' KHONG nhan; van so GIA TRI ngay+thang.
            y=_w(T,j+1) if _lien(T,j+1) else None
            if y in ('mai','kia') and x=='ngày': ngay=y
            else:
                r=_so(T,j+1) if _lien(T,j+1) else None
                if r and _w(T,r[2]) in THANG_NGAY and _lien(T,r[2]):
                    m=_so(T,r[2]+1)
                    mo=m[0] if m else (4 if _w(T,r[2]+1)=='tư' else None)
                    if mo: ngay=(int(r[0]),int(mo))
        kq.append(dict(gio24=gio24,buoi=buoi,ngay=ngay))
    return kq

def doc_ngay(van_ban):
    """-> [(ngay, thang)] cho cum 'ngày X tháng Y' (khong can gio): 'hết giảm ngày hai mươi mốt tháng mười' -> [(21,10)]; Whisper viet '14 tháng 10' / '14/10' cung nhan."""
    t=re.sub(r'(?<=\d)\s*/\s*(?=\d)',' tháng ',nfc(van_ban)); T=_tach(t); kq=[]
    for i in range(len(T)):
        if _w(T,i)!='ngày': continue
        r=_so(T,i+1) if _lien(T,i+1) else None
        if r and _w(T,r[2]) in THANG_NGAY and _lien(T,r[2]):
            m=_so(T,r[2]+1) if _lien(T,r[2]+1) else None
            mo=m[0] if m else (4 if _w(T,r[2]+1)=='tư' and _lien(T,r[2]+1) else None)
            if mo and r[0]==int(r[0]) and mo==int(mo): kq.append((int(r[0]),int(mo)))
    return kq

# ---------------------------------------------------------------- ten game
VERSION={'deluxe':'deluxe','ultimate':'ultimate','definitive':'definitive','remastered':'remastered','remaster':'remastered','remake':'remake',
         'complete':'complete','goty':'goty'}
# Cum tieng Viet chi phien ban (Loi_chu: Definitive -> 'bản làm lại', Complete -> 'bản đầy đủ'). So bang bo dau, 'bản' di truoc la tuy chon. Bang alias theo game: Whisper small hay nghe
# 'làm lại' thanh 'nắm lại' va 'bản' thanh 'bán' (do tren video that Top 5 11/10) — alias nay KHONG phai noi nguong, chi liet ke cach nghe sai da biet cua DUNG cum nay.
VERSION_VN=[(('lam','lai'),'remake'),(('nam','lai'),'remake'),(('day','du'),'complete'),(('hoan','chinh'),'complete')]
def _lech_1(a,b):
    """Hai chuoi ASCII lech DUNG <= 1 ky tu (thay / chen / bo 1 ky tu)."""
    if a==b: return True
    if abs(len(a)-len(b))>1: return False
    if len(a)==len(b): return sum(x!=y for x,y in zip(a,b))==1
    s,l=(a,b) if len(a)<len(b) else (b,a)
    return any(l[:i]+l[i+1:]==s for i in range(len(l)))
def tu_phien_ban(l):
    """Tu chi phien ban (Deluxe, Ultimate, ...): khop CHINH XAC, hoac lech chinh ta <= 1 ky tu VOI tu >= 5 ky tu ('delux' = 'deluxe', 'remaster' = 'remastered'; Whisper nghe thieu/thua 1 chu cai).
    Tu < 5 ky tu ('goty') phai khop chinh xac; so phan / so La Ma KHONG qua cua nay. -> lop phien ban hoac None."""
    if l in VERSION: return VERSION[l]
    d=bo_dau(l)
    if len(d)>=5 and d.isascii() and d.isalpha():
        for k,v in VERSION.items():
            if len(k)>=5 and _lech_1(d,k): return v
    return None
def _la_ma_gt(s):
    """so La Ma hop le (chu hoa, 2..39) -> int, khong thi None"""
    if not re.fullmatch(r'[IVX]{2,}',s): return None
    v={'I':1,'V':5,'X':10}; tong=0
    for a,b in zip(s,s[1:]+' '): tong+=-v[a] if b!=' ' and v[b]>v[a] else v[a]
    ra=''; n=tong
    for k,s2 in ((10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')):
        while n>=k: ra+=s2; n-=k
    return tong if ra==s and tong<40 else None
_DAY_DON=set(CHU_SO)|set(DON_VI_SAU)
VER_CHU={'remake':'banlamlai','complete':'bandaydu'}
_LA_MA_1={'I':1,'V':5,'X':10}
def _tok_ten(text):
    """Ten game -> [(loai,gia_tri,bat_dau,ket_thuc)] voi loai 'n' (so) | 'v' (lop phien ban) | 'w' (tu bo dau); bat_dau/ket_thuc = vi tri trong nfc(text).
    4 = IV = 'bốn' ; 'mười một' = 11 ; 'hai lăm' = 25 (doc tung chu so) ; 'GTA V' = 'GTA năm' = 'GTA 5' = 'GTA5' (La Ma 1 ky tu V/X/I chi tu vi tri thu 2 tro di: 'V Rising' giu la chu) ;
    'F1 hai lăm' = 'F1 25' = 'F125' (chu+so dinh nhau tach thanh chu + so, so dung ngay sau noi vao: 1 + 25 = 125, KHONG so theo hau to)."""
    t=nfc(text); ms=list(re.finditer(r"[^\W_]+",t)); raw=[m.group() for m in ms]; low=[r.lower() for r in raw]; ra=[]; i=0
    sp=lambda a,b:(ms[a].start(),ms[b-1].end())
    while i<len(raw):
        r,l=raw[i],low[i]
        if l.isdigit(): ra.append(('n',int(l))+sp(i,i+1)); i+=1; continue
        rm=_la_ma_gt(r) if r.isupper() else None
        if rm: ra.append(('n',rm)+sp(i,i+1)); i+=1; continue
        if i>0 and r in _LA_MA_1: ra.append(('n',_LA_MA_1[r])+sp(i,i+1)); i+=1; continue
        hit=None; bd=[bo_dau(x) for x in low[i:i+3]]
        for ph,lop in VERSION_VN:
            if tuple(bd[:len(ph)])==ph: hit=(len(ph),lop); break
            if bd[:1]==['ban'] and tuple(bd[1:1+len(ph)])==ph: hit=(len(ph)+1,lop); break
        if hit: ra.append(('v',hit[1])+sp(i,i+hit[0])); i+=hit[0]; continue
        pb_=tu_phien_ban(l)
        if pb_: ra.append(('v',pb_)+sp(i,i+1)); i+=1; continue
        if l in CHU_SO or l=='mười':
            T=[('w',x,False,0) for x in low[i:i+8]]; r2=_ba(T,0)
            if r2:
                gt,_,j,hang=r2
                if hang=='don':
                    ds=[gt]; k=1
                    while k<len(T) and T[k][1] in _DAY_DON: ds.append(CHU_SO.get(T[k][1],DON_VI_SAU.get(T[k][1]))); k+=1
                    ra.append(('n',int(''.join(map(str,ds)))))
                    ra[-1]+=sp(i,i+k); i+=k
                else: ra.append(('n',gt)+sp(i,i+j)); i+=j
                continue
        m2=re.fullmatch(r'([^\W\d_]+)(\d+)',l)
        if m2: ra.append(('w',bo_dau(m2.group(1)))+sp(i,i+1)); ra.append(('n',int(m2.group(2)),ms[i].start(),ms[i].end(),'dinh')); i+=1; continue
        ra.append(('w',bo_dau(l))+sp(i,i+1)); i+=1
    ket=[]; k=0
    while k<len(ra):                      # 'F1' + '25' -> chu F + so 125 (so dinh lien chu noi tiep so ke ngay sau)
        x=ra[k]
        if len(x)==5 and k+1<len(ra) and ra[k+1][0]=='n' and len(ra[k+1])==4:
            y=ra[k+1]; ket.append(('n',int(str(x[1])+str(y[1])),x[2],y[3])); k+=2; continue
        ket.append(x[:4]); k+=1
    return ket
def _cs(t): return f'#{t[1]}' if t[0]=='n' else f'~{t[1]}' if t[0]=='v' else t[1]
def _cua_so(M,H):
    """cua so (s,L) cua H (L = m-1 .. m+3 token) giong ten `M` nhat"""
    mj=''.join(_cs(t) for t in M); m=len(M); tot=(-1.0,0,0)
    for L in range(max(1,m-1),m+4):
        for s in range(0,max(1,len(H)-L+1)):
            w=H[s:s+L]
            if not w: continue
            sc=difflib.SequenceMatcher(None,mj,''.join(_cs(t) for t in w)).ratio()-0.001*abs(L-m)
            if sc>tot[0]: tot=(sc,s,len(w))
    return tot[1],tot[2]
def _cua_so_tot_nhat(M,H):
    s,L=_cua_so(M,H); return H[s:s+L]
_DON_VI_GIA=NGHIN|TRIEU|DONG|{'k','phần','giờ','phút','giây','tháng','ngày','phan','gio'}
def _la_them_vao_ten(text,H,k):
    """Token H[k] ngay sau cua so ten co phai MOT PHAN CUA TEN (so phan, phien ban) khong: noi lien (khong dau cau), khong phai tien/phan tram/gio/ngay."""
    tk=H[k]
    if tk[0] not in ('n','v') or k==0: return False
    giua=text[H[k-1][3]:tk[2]]
    if re.search(r'\S',giua):
        # dau cau Whisper chen vao ('Resident Evil 4, Deluxe Edition') KHONG phai ranh gioi ten: chi voi tu PHIEN BAN ('v') va chi dau , . ; : - (so thi van chan nhu cu: '4, 12 game')
        if tk[0]!='v' or re.search(r'[^\s,.;:\-–—]',giua): return False
    if tk[0]=='n' and not (tk[1]<100 or 1980<=tk[1]<=2100): return False
    rest=text[tk[3]:]
    if re.match(r'\s*%',rest) or re.match(r'[.,]\d',rest): return False
    m=re.match(r'\s*([^\W_]+)',rest)
    return not (tk[0]=='n' and m and m.group(1).lower() in _DON_VI_GIA)
def so_phan_biet(mong,nghe):
    """So DU TAP token PHAN BIET (so phan/thu tu, so La Ma, so chu, Deluxe/Ultimate/Definitive/Remastered/Remake/Complete/'bản làm lại'/'bản đầy đủ') giua ten ky vong va cua so TEN trong cau nghe duoc:
    THIEU hoac THUA deu TRUOT ('Resident Evil' nghe 'Resident Evil hai' -> truot; 'Resident Evil 4' nghe '... 4 Deluxe' -> truot). Cua so ten = cum giong ten nhat + cac token phan biet NOI LIEN ngay sau
    (khong lay so cua cum gia/hang phia sau). -> (dat, ly_do)."""
    t=nfc(nghe); M=_tok_ten(mong); H=_tok_ten(t)
    if not H: return False,'khong nghe duoc gi'
    s,L=_cua_so(M,H); e=s+L
    while e<len(H) and _la_them_vao_ten(t,H,e): e+=1
    W=H[s:e]
    can_n=Counter(x[1] for x in M if x[0]=='n'); can_v=Counter(x[1] for x in M if x[0]=='v')
    co_n=Counter(x[1] for x in W if x[0]=='n'); co_v=Counter(x[1] for x in W if x[0]=='v')
    sai=[f'thieu so {n}' for n in (can_n-co_n)]+[f'thieu phien ban {v}' for v in (can_v-co_v)]+[f'thua so {n}' for n in (co_n-can_n)]+[f'thua phien ban {v}' for v in (co_v-can_v)]
    if sai: return False,', '.join(sai)+'; nghe duoc «'+' '.join(_cs(x) for x in W)+'»'
    return True,'khop token phan biet'
def so_ten(mong,nghe,nguong=0.40):
    """Ten game: token phan biet khop CHINH XAC (so_phan_biet) + phan chu con lai giong >= nguong (0,40: Whisper tieng Viet nghe ten Anh rat sai chinh ta). -> (dat, ly_do)"""
    ok,ly=so_phan_biet(mong,nghe)
    if not ok: return False,ly
    M=_tok_ten(mong); H=_tok_ten(nghe)
    chu=lambda ts:''.join((t[1] if t[0]=='w' else VER_CHU.get(t[1],t[1])) for t in ts if t[0]!='n')     # cum phien ban tinh nhu chu (giong cach do cu: ca 'bản đầy đủ')
    a=chu(M)
    if not a: return True,ly
    W=_cua_so_tot_nhat(M,H); b=chu(W)
    r=difflib.SequenceMatcher(None,a,b).ratio()
    return (r>=nguong),(f'ten giong {r:.2f}' if r>=nguong else f'ten giong {r:.2f} < {nguong}: mong «{a}» nghe «{b}»')
_HANG_TU={'hang','hac','han','hanh'}; _SO_HANG={'mot','hai','ba','bon','tu','nam','1','2','3','4','5'}
def cat_hang(nghe):
    """Bo tien to hang CHI KHI nhan dang duoc dung dang tien to Top 5: [Và] + (hạng|hãng|hạc|hẳn…) + so 1..5 ('Hạng năm:', 'Và hạng một,', 'Hẳn 3.', 'hang hai', 'h3').
    Khong nhan dang duoc -> giu nguyen ('Resident Evil bốn đang giảm' khong bi cat mat 'bốn')."""
    t=nfc(nghe); ms=list(re.finditer(r"[^\W_]+",t)); k=0
    if k<len(ms) and bo_dau(ms[k].group())=='va': k+=1
    if k<len(ms) and re.fullmatch(r'h[1-5]',ms[k].group().lower()): return t[ms[k].end():].lstrip(' :,.;-')
    if k+1<len(ms) and bo_dau(ms[k].group()) in _HANG_TU and bo_dau(ms[k+1].group()) in _SO_HANG: return t[ms[k+1].end():].lstrip(' :,.;-')
    return t
def che_so_trong_ten(nghe,ten):
    """Thay (bang khoang trang, giu do dai) cac SO nam trong cua so TEN game ky vong ('Mortal Kombat mười một' -> '11') de doc_tien khong coi so phan cua ten la tien."""
    ra=nfc(nghe)
    for tn in ten:
        M=_tok_ten(tn); can={x[1] for x in M if x[0]=='n'}; H=_tok_ten(ra)
        if not can or not H: continue
        s,L=_cua_so(M,H)
        for x in H[s:s+L]:
            if x[0]=='n' and x[1] in can: ra=ra[:x[2]]+' '*(x[3]-x[2])+ra[x[3]:]
    return ra

# ---------------------------------------------------------------- doi chieu mot doan
def cap_vung_tien_ct(nghe):
    """-> [(ma_vung_gan_nhat_dung_truoc, vnd, nguon)] : moi khoan tien ghep voi vung nhac TRUOC no (vai tro 'vung -> chenh lech')."""
    vs=doc_vung(nghe); ra=[]
    for v,_,pos,ng in doc_tien_ct(nghe):
        truoc=[m for m,p in vs if p<pos]
        ra.append((truoc[-1] if truoc else None,v,ng))
    return ra
def cap_vung_tien(nghe): return [(m,v) for m,v,_ in cap_vung_tien_ct(nghe)]
def noi_tat_literal(vnd):
    """Cum KY VONG dang noi tat 'X tram Y' (loi_chu.noi_chenh: 760.000 = 'bảy trăm sáu') -> gia tri Whisper co the viet THEO CHU SO LITERAL ('706' = 706.000). Khong phai dung sai:
    chi tra gia tri khi ky vong that su la dang noi tat (Y = 2..9, tru 5 'rưỡi' va 1 'mười'; < 1 trieu); khong thi None. Ap dung CHI cho khoan tien Whisper viet bang CHU SO (xem doi_chieu)."""
    n=int(vnd/10000+0.5)
    if vnd<1_000_000 and 10<n<100 and n%10 not in (0,1,5): return ((n//10)*100+n%10)*1000
    return None
def _la_day_con(can,co):
    it=iter(co); return all(any(x==y for y in it) for x in can)
def chieu_so_sanh(nghe,chu_the,ma_kia):
    """Cau 'chu_the RE HON kia ...': chu the (vung re nhat) phai la vung nhac DAU TIEN; doan van giua vung truoc va vung `kia` phai con cau truc so sanh ('hơn') va KHONG co 'dat/mac' (đắt/mắc hơn = nguoc chieu).
    KHONG bat buoc nghe ra dung chu 'rẻ': Whisper small hay nghe 'rẻ hơn' thanh 'dạy hơn'/'dẻ hơn' (video that thu-d) — chieu sai that su la 'đắt/mắc hơn', loi nghe thi khong phai chieu sai. -> list loi (rong = dung chieu)."""
    t=bo_dau(nfc(nghe)); vs=doc_vung(nfc(nghe)); loi=[]
    if not vs or vs[0][0]!=chu_the: return [f'CHIEU SO SANH: chu the phai la {chu_the} (nhac dau tien) nghe duoc {vs[0][0] if vs else "khong co vung"} («{nghe[:70]}»)']
    for k in range(1,len(vs)):
        if vs[k][0]!=ma_kia: continue
        seg=t[vs[k-1][1]:vs[k][1]]
        if re.search(r'(?<![a-z])(?:dat|mac)(?![a-z])',seg): loi.append(f'CHIEU SO SANH: {chu_the} khong the DAT hon {ma_kia} («{nghe[:70]}»)')
        elif re.search(r'(?<![a-z])(?:khong|chang|chua|ko)(?![a-z])',seg): loi.append(f'CHIEU SO SANH: cau PHU DINH giua {chu_the} va {ma_kia} ("khong/chang re hon" = nguoc nghia) («{nghe[:70]}»)')
        elif not re.search(r'(?<![a-z])hon(?![a-z])',seg): loi.append(f'CHIEU SO SANH: thieu cau truc "{chu_the} rẻ hơn {ma_kia}" (khong co "hơn" giua hai vung) («{nghe[:70]}»)')
        return loi
    return [f'CHIEU SO SANH: khong thay vung {ma_kia} sau chu the {chu_the} («{nghe[:70]}»)']
# ---------------------------------------------------------------- diem sao + tu khoa (doan GIOI THIEU cua Keo thom, 11/10)
_SO_CHU_BD={'khong':0,'mot':1,'hai':2,'ba':3,'bon':4,'tu':4,'nam':5,'lam':5,'sau':6,'bay':7,'tam':8,'chin':9}
def doc_diem(van_ban):
    """Diem sao nghe duoc (so thap phan 1 chu so) -> [float]: '4,4' / '4.4' / '4 phay 4' / 'bon phay bon' / 'bon phay bon tren nam sao'; so nguyen chi khi di kem 'sao' ('cham bon sao', 'bon tren nam sao').
    Whisper doc '4.4' / '4,4' / 'bon phay bon' deu ve cung gia tri 4.4 (khong phai tien / % / ngay)."""
    t=bo_dau(nfc(van_ban)); ra=[]
    def so(x): return int(x) if x.isdigit() else _SO_CHU_BD.get(x)
    for m in re.finditer(r'(?<![\d.,])(\d)\s*[.,]\s*(\d)(?![\d])',t): ra.append(int(m.group(1))+int(m.group(2))/10)
    tok=_tach_bd(t)
    for i in range(len(tok)-2):
        if tok[i+1] in ('phay','phai') and so(tok[i]) is not None and so(tok[i+2]) is not None and so(tok[i+2])<10 and so(tok[i])<10: ra.append(so(tok[i])+so(tok[i+2])/10)
    for m in re.finditer(r'cham\s+(\d|[a-z]+)\s+(?:tren\s+(?:5|nam)\s+)?sao',t):
        v=so(m.group(1))
        if v is not None and 1<=v<=5: ra.append(float(v))
    return ra
def _tach_bd(t): return re.findall(r'[a-z0-9]+',t)
def doc_sao(van_ban):
    """Diem sao nghe duoc TRONG CAU MO (Keo v10: 'mot game bon phay tam sao' / 'Game 4,8 sao' / 'game bon sao') -> [float]: gom doc_diem (so thap phan, 'cham N sao') va so nguyen 1-5 NGAY TRUOC chu 'sao'
    ('bon sao', '5 sao'). Dung cho phep 'sao' cua doi_chieu (so theo GIA TRI, chua kem 'cham ... tren 5 sao' nhu doan gioi)."""
    ra=list(doc_diem(van_ban)); t=bo_dau(nfc(van_ban))
    for m in re.finditer(r'(?<![a-z0-9.,])(?<!phay )(\d|khong|mot|hai|ba|bon|nam|sau|bay|tam|chin)\s+sao(?![a-z0-9])',t):
        g=m.group(1); v=int(g) if g.isdigit() else _SO_CHU_BD.get(g)
        if v is not None and 1<=v<=5: ra.append(float(v))
    return ra
def co_tu_khoa(nghe,alts,nguong=0.78):
    """Mot nhom tu khoa (cac cach viet khong dau, 1-4 tu): co mat trong ban nghe neu la chuoi con, hoac cua so tu cung do dai giong >= nguong (Whisper hay nghe sai chinh ta: 'delux', 'vu khi' -> 'vu khi')."""
    tk=_tach_bd(bo_dau(nfc(nghe))); chuoi=' '.join(tk)
    for a in alts:
        a=' '.join(_tach_bd(bo_dau(a)))
        if not a: continue
        if a in chuoi: return True
        n=len(a.split())
        for k in {max(1,n-1),n,n+1}:
            for i in range(len(tk)-k+1):
                if difflib.SequenceMatcher(None,a,' '.join(tk[i:i+k])).ratio()>=nguong: return True
    return False
def doc_diem_cham(van_ban):
    """Diem sao nghe duoc TRONG MENH DE DANH GIA: 'cham <diem> tren 5 sao' / 'cham <diem> sao' / 'cham <diem>/5' (<diem> = 4,4 · 4.4 · 4 phay 4 · bon phay bon · bon). Thang khac ('tren 10 sao'), so khong di
    kem 'cham' ('phien ban 4.4') -> KHONG tinh; rieng '<diem> tren 5 sao' tinh ca khi Whisper nghe sai/mat chu 'cham'. -> [float]."""
    t=bo_dau(nfc(van_ban)); ra=[]
    def so(x): return int(x) if x.isdigit() else _SO_CHU_BD.get(x)
    D=r'(\d\s*[.,]\s*\d|[a-z0-9]+\s+phay\s+[a-z0-9]+|[a-z0-9]+)'
    # '<diem> tren 5 sao' tu no da la menh de danh gia (thang 5 sao) -> khong can 'cham' (CI that 11/10: Whisper nghe 'người chơi chấm 4,5' thanh 'người chơi trên 4,5 trên 5 sao')
    # 12/10 (Keo 20:00, run 38242333660): Whisper turbo nghe 'chấm 4,5 trên năm sao' thanh 'châm 4,5 chiến năm sau' -> chap nhan bien the nghe sai cua 'trên' / 'sao'
    TREN=r'(?:tren|chien|chen|trien)'; SAO=r'(?:sao|sau|xao)'
    ms=list(re.finditer(r'(?<![a-z0-9])cham\s+(?:duoc\s+)?'+D+r'(?:\s*/\s*5|\s+'+TREN+r'\s+(?:5|nam)\s+'+SAO+r'|\s+sao)(?![a-z0-9])',t))
    ms+=list(re.finditer(r'(?<![a-z0-9.,])'+D+r'\s+'+TREN+r'\s+(?:5|nam)\s+'+SAO+r'(?![a-z0-9])',t))
    for m in ms:
        g=m.group(1); d=re.fullmatch(r'(\d)\s*[.,]\s*(\d)',g)
        if d: ra.append(int(d.group(1))+int(d.group(2))/10); continue
        w=re.fullmatch(r'([a-z0-9]+)\s+phay\s+([a-z0-9]+)',g)
        if w:
            a_,b_=so(w.group(1)),so(w.group(2))
            if a_ is not None and b_ is not None and a_<10 and b_<10: ra.append(a_+b_/10)
        else:
            v=so(g)
            if v is not None and 1<=v<=5: ra.append(float(v))
    return ra
def _co_chinh_xac(nghe,alts):
    chuoi=' '.join(_tach_bd(bo_dau(nfc(nghe))))
    return any(re.search(r'(?<![a-z0-9])'+re.escape(' '.join(_tach_bd(bo_dau(a))))+r'(?![a-z0-9])',chuoi) for a in alts if a)
_SO_TEN=['khong','mot','hai','ba','bon','nam','sau','bay','tam','chin']
def co_so_luong(nghe,so,tu):
    """'<so> [1 tu] <tu>' (so = chu so hoac chu): 'hai vu khi' / '2 vu khi'."""
    t=' '.join(_tach_bd(bo_dau(nfc(nghe)))); n=_SO_TEN[so] if 0<=so<10 else str(so)
    return bool(re.search(r'(?<![a-z0-9])(?:%d|%s)\s+(?:[a-z]+\s+)?%s'%(so,n,re.escape(tu)),t))
def tu_khoa_gioi(gt,ket_luan=None):
    """Kiem doan gioi thieu (tinh tu keo.json.gioi_thieu). (Keo v10: `ket_luan=(cau_dung,[cau_khac])` them cau ket luan cuoi doan: cau dung BAT BUOC, cau khac CAM.) BAT BUOC: tung phan them cua ban dac biet (kem SO vu khi + 'dung som' dung muc), TEN edition, che do co-op dung chu ('choi chung online' / 'tren mot may', khong
    alias 'choi chung'). MEM (>= 60%): the loai, dac diem khac. CAM: ten edition khac / 'standard', che do co-op nguoc, 'dung som' khi khong co, phu dinh ('khong co them'). -> dict."""
    gt=gt or {}; BB=[]; MEM=[]; CAM=[]; SL=[]; SOM=False
    if ket_luan:    # Keo v10 B: (cau dung, [cac cau con lai]) — cau dung BAT BUOC (mem theo chinh ta), cau khac CAM (khop nguyen cum)
        BB.append([bo_dau(ket_luan[0]).strip(' .')]); CAM+=[[bo_dau(x).strip(' .')] for x in ket_luan[1]]
    DIEN={'skin_vu_khi':['skin vu khi'],'vu_khi':['vu khi'],'trang_phuc':['trang phuc'],'mo_rong':['goi mo rong','mo rong'],'tien':['tien trong game'],'vat_pham':['vat pham'],'hinh_nen':['hinh nen'],'chu_de_menu':['chu de menu','chu de'],'sach_tranh':['sach tranh'],'avatar':['anh dai dien','dai dien'],'nhac':['nhac phim'],'choi_som':['choi som']}
    ban=gt.get('ban')
    if ban:
        for m in ban.get('them',[]):
            BB.append(DIEN.get(m['k'],[bo_dau(m['noi'])]))
            if m['k']=='vu_khi' and m.get('so',0)>0: SL.append((m['so'],'vu khi'))
            if m.get('dung_som'): SOM=True
        nm=bo_dau(ban['ten_noi']); BB.append([nm])
        CAM+=[[bo_dau(v)] for v in ('Standard','Ultimate','Gold','Premium','Deluxe','Collector','Definitive') if bo_dau(v)!=nm]
    if not SOM: CAM.append(['dung som'])
    for g in gt.get('the_loai',[]): MEM.append([bo_dau(g['vi'])])
    DD={'roguelike':['roguelike','rogue like','choi lai tu dau'],'the_gioi_mo':['the gioi mo'],'souls':['kho kieu souls','souls']}
    keys=[x['k'] for x in gt.get('dac_diem',[])]
    for x in gt.get('dac_diem',[]):
        if x['k']=='co_op_online': BB.append(['choi chung online'])
        elif x['k']=='co_op_local': BB.append(['choi chung tren mot may'])
        else: MEM.append(DD.get(x['k'],[bo_dau(x['noi'])]))
    if 'co_op_online' in keys: CAM.append(['choi chung tren mot may'])
    if 'co_op_local' in keys: CAM.append(['choi chung online'])
    return dict(bat_buoc=BB,mem=MEM,cam=CAM,so_luong=SL,dung_som=SOM)
def doi_chieu(nghe,tien=(),phan_tram=(),vung=(),ten=(),han=None,tien_thu_tu=(),cap=(),tien_tat=(),ngay=(),hang=False,chu_the=None,kiem_ten=True,diem=(),tu_khoa=None,sao=()):
    """So cau Whisper nghe duoc (`nghe`) voi gia tri KY VONG tinh tu du lieu. -> list loi (rong = dat).
    tien_tat: [vnd] ky vong dang noi tat 'X tram Y' (cho phep Whisper viet CHU SO literal '706' = 706.000; nghe CHU DAY DU 'bay tram le sau nghin' van so DUNG gia tri) · tien_thu_tu: [vnd] phai xuat hien DUNG THU TU ·
    cap: [(ma_vung, vnd)] tien di sau vung tuong ung · chu_the: ma vung re nhat -> kiem chieu 'chu_the RE HON kia' voi moi vung trong `cap` · hang=True (Top 5): cat tien to 'Hạng N' truoc khi so TEN ·
    tien: [vnd] moi gia tri phai co mat DUNG (doc_tien; SO TRONG TEN GAME khong tinh la tien) · phan_tram: [so] · vung: [ma] · ten: [ten mong (chu doc)] · han: han_ky_vong()."""
    loi=[]
    nt=che_so_trong_ten(nghe,ten) if ten else nfc(nghe)       # so phan cua ten game ('Mortal Kombat mười một') khong phai tien
    ct=doc_tien_ct(nt); gt=[v for v,_,_,_ in ct]; gt_so={v for v,_,_,ng in ct if ng=='b'}
    alt=lambda v:noi_tat_literal(v) if v in tien_tat else None      # tien_tat: ky vong la dang noi tat -> chap nhan phien am literal CHU SO cua CHINH cum do
    for v in tien:
        if v not in gt and alt(v) not in gt_so: loi.append(f'TIEN: mong {v:,} nghe duoc {sorted(set(gt))} («{nghe[:70]}»)'.replace(',','.'))
    if tien_thu_tu and not _la_day_con(list(tien_thu_tu),gt): loi.append(f'TIEN THEO THU TU (vd goc roi con): mong {list(tien_thu_tu)} nghe duoc {gt} («{nghe[:70]}»)')
    cv=cap_vung_tien_ct(nt); cv2={(m,v) for m,v,_ in cv}; cv_so={(m,v) for m,v,ng in cv if ng=='b'}
    for c in cap:
        if tuple(c) not in cv2 and (c[0],alt(c[1])) not in cv_so: loi.append(f'CAP vung-tien: mong {tuple(c)} nghe duoc {[(m,v) for m,v,_ in cv]} («{nghe[:70]}»)')
    if chu_the:
        for c in cap: loi+=chieu_so_sanh(nghe,chu_the,c[0])
    pt=[p for p,_ in doc_phan_tram(nghe)]
    for p in phan_tram:
        if p not in pt: loi.append(f'PHAN TRAM: mong {p}% nghe duoc {pt} («{nghe[:70]}»)')
    vg=[m for m,_ in doc_vung(nghe)]
    for m in vung:
        if m not in vg: loi.append(f'VUNG: mong {m} nghe duoc {vg or "khong co"} («{nghe[:70]}»)')
    for t in (ten if kiem_ten else ()):      # kiem_ten=False: chi dung `ten` de che so trong ten game; ten duoc cham rieng bang ten_hai_bo
        ok,ly=so_ten(t,cat_hang(nghe) if hang else nghe)
        if not ok: loi.append(f'TEN «{t}»: {ly} («{nghe[:70]}»)')
    if ngay:
        ng=doc_ngay(nghe)
        for n in ngay:
            if tuple(n) not in ng: loi.append(f'NGAY: mong {tuple(n)} (ngay, thang) nghe duoc {ng or "khong co"} («{nghe[:70]}»)')
    if sao:      # Keo v10: diem sao nhac TRONG CAU MO ('mot game bon phay tam sao'); khong yeu cau 'cham ... tren 5 sao'
        ss=doc_sao(nghe)
        for d_ in sao:
            if not any(abs(x-d_)<0.05 for x in ss): loi.append(f'SAO (cau mo): mong {d_} nghe duoc {ss or "khong co"} («{nghe[:70]}»)')
    if diem:
        ds=doc_diem_cham(nghe)
        for d_ in diem:
            if not any(abs(x-d_)<0.05 for x in ds): loi.append(f'DIEM SAO: mong {d_} (trong menh de "cham ... tren 5 sao") nghe duoc {ds or "khong co"} («{nghe[:70]}»)')
    if tu_khoa:
        thieu=[a[0] for a in tu_khoa.get('bat_buoc',[]) if not co_tu_khoa(nghe,a)]
        if thieu: loi.append(f'TU KHOA phan them / edition / che do choi: thieu {thieu} («{nghe[:90]}»)')
        for so_,tu_ in tu_khoa.get('so_luong',[]):
            if not co_so_luong(nghe,so_,tu_): loi.append(f'SO LUONG: mong "{so_} {tu_}" («{nghe[:90]}»)')
        if tu_khoa.get('dung_som') and not co_tu_khoa(nghe,['dung som']): loi.append(f'DUNG SOM: thieu "dung som" («{nghe[:90]}»)')
        co=[a[0] for a in tu_khoa.get('cam',[]) if _co_chinh_xac(nghe,a)]
        if co: loi.append(f'TU CAM (sai edition / che do choi / dung som): {co} («{nghe[:90]}»)')
        if re.search(r'(?<![a-z])(?:khong|chang|chua|ko)\s+(?:co\s+)?(?:them|bao\s+gom|kem)',bo_dau(nfc(nghe))): loi.append(f'PHU DINH phan them ("khong co them"): («{nghe[:90]}»)')
        mem=tu_khoa.get('mem',[]); tr=[a[0] for a in mem if not co_tu_khoa(nghe,a)]
        if mem and (len(mem)-len(tr))<-(-0.6*len(mem)//1): loi.append(f'TU KHOA the loai/dac diem: chi nghe duoc {len(mem)-len(tr)}/{len(mem)}, thieu {tr} («{nghe[:90]}»)')
    if han is not None:
        hs=doc_han(nghe)
        if not any(h['gio24']==han['gio24'] and h['buoi']==han['buoi'] and h['ngay']==han['ngay'] for h in hs):
            loi.append(f'HAN: mong {han} nghe duoc {hs or "khong co"} («{nghe[:70]}»)')
    return loi

def ten_hai_bo(mong,bo,hang=False):
    """TEN game (Opus chot 11/10): DAT neu MOT trong cac bo nghe (`bo` = {ten_bo: van_ban}; thu tu = thu tu thu, turbo truoc small) dat so_ten (nguong 0,40) VA token phan biet (so phan / La Ma / phien ban)
    khop tuyet doi TRONG CHINH ban nghe dat do. Tien / % / vung / han KHONG qua cua nay (chi turbo). -> (dat, ten_bo_dat | None, ly_do)."""
    sai=[]
    for ten_bo,van in bo.items():
        if van is None: continue
        ok,ly=so_ten(mong,cat_hang(van) if hang else van)
        if ok: return True,ten_bo,f'{ten_bo}: {ly}'
        sai.append(f'{ten_bo}: {ly}')
    return False,None,' | '.join(sai) or 'khong co ban nghe'
# ---------------------------------------------------------------- NHIEM VU doc theo LUAT KHUON (khong suy tu chinh loi dang kiem)
# Sol vong 2b #11: kiem-tat-ca.py cu hoi chinh `loi` xem co cau giam gia / ten vung khong roi moi doi chieu -> loi bo cau do thi phep kiem TU TAT. Nay % / vung bat buoc theo LUAT cua kich-ban.py
# (Top 5: hang 5/4/2 doc phan tram, hang 4/1 doc vung; Keo thom: doan mo = ten+%+vung A, dap = vung A+B+C; gioi = diem sao + tu khoa). test_kiem_tat_ca.py chay kich-ban.py that va doi chieu voi bang nay.
TOP5_PHAN_TRAM=frozenset({5,4,2}); TOP5_VUNG=frozenset({4,1})
def nhiem_vu_top5(hang): return hang in TOP5_PHAN_TRAM, hang in TOP5_VUNG       # -> (doc_phan_tram, doc_vung)
KEO_PHAN_TRAM=frozenset({'mo'}); KEO_VUNG={'mo':('A',),'dap':('A','B','C')}   # 11/10: bo doan `hoi` (hoi-dap); `gioi` doc DIEM SAO + tu khoa (doi_chieu: diem=, tu_khoa=)

# ---------------------------------------------------------------- nghe tren am thanh MP4 cuoi + cache theo bam PCM
def sha_pcm(x16):
    """Bam sha256 cua PCM da giai ma (16 kHz mono float32)."""
    return hashlib.sha256(x16.tobytes()).hexdigest()
def _khoa_mo_hinh(rev):
    """Khoa ten file cache tu chuoi mo hinh+revision (`rev`): slug doc duoc + bam sha1 (chuoi khac nhau => ten file khac nhau)."""
    rev=str(rev or ''); return re.sub(r'[^A-Za-z0-9]+','_',rev)[:24].strip('_')+'-'+hashlib.sha1(rev.encode('utf-8')).hexdigest()[:10]
def nghe_doan(x16,cua_so,nghe,thu_muc_cache,rev=''):
    """Nghe tung doan tren AM THANH TRICH TU MP4 CUOI (`x16`, khong phai giong goc). cua_so = {khoa: (a, b)} chi so mau 16 kHz.
    3 ban nen tang cung luong tieng -> cung bam PCM -> doan da nghe o ban truoc duoc dung lai (Whisper 1 lan). -> (heard {khoa: van_ban}, bang_chung)."""
    sha=sha_pcm(x16); f=pathlib.Path(thu_muc_cache)/f'kiem-nghe-{sha[:16]}-{_khoa_mo_hinh(rev)}.json'    # TEN FILE theo mo hinh+revision: turbo / small khong ghi de nhau (Sol soi cuoi: chuoi turbo->small lap tren 3 ban cung PCM nghe du 6 lan)
    try: cache=json.load(open(f,encoding='utf-8'))
    except Exception: cache={}
    heard={}; dung_lai=0
    for k,(a,b) in cua_so.items():
        c=cache.get(k)
        if c and c.get('a')==a and c.get('b')==b and c.get('rev')==rev: heard[k]=c['text']; dung_lai+=1
        else:
            heard[k]=nghe(x16[a:b]); cache[k]=dict(a=a,b=b,rev=rev,text=heard[k])
    try: json.dump(cache,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    except Exception: pass
    return heard,dict(pcm_sha256=sha,dung_lai=dung_lai,nghe_moi=len(cua_so)-dung_lai)

# ---------------------------------------------------------------- ngay du lieu = ngay DANG cua luot chay (B6)
GIO_DANG_MAC_DINH={'top5':'12:00','tin-nhanh':'07:30','keo-thom-2':'15:00','keo-thom':'20:00','keo-thom-3':'22:00'}
THU_VN=['Thứ Hai','Thứ Ba','Thứ Tư','Thứ Năm','Thứ Sáu','Thứ Bảy','Chủ Nhật']
def ngay_tu_ddmm(ddmm,thu=None,moc=None):
    """'10/10' (+ 'Thứ Bảy') -> date gan `moc` nhat (nam moc +-1) khop thu; khong suy ra duoc -> None. Dung cho du lieu cu (fixture) khong co ngay_dang khi HOI_QUY=1."""
    m=re.fullmatch(r'\s*(\d{1,2})/(\d{1,2})\s*',ddmm or '')
    if not m: return None
    moc=moc or datetime.date.today(); ds=[]
    for y in (moc.year,moc.year-1,moc.year+1):
        try: d=datetime.date(y,int(m.group(2)),int(m.group(1)))
        except ValueError: continue
        if thu is None or THU_VN[d.weekday()]==thu: ds.append(d)
    return min(ds,key=lambda d:abs((d-moc).days)) if ds else None
def kiem_ngay(ngay_du_lieu,ngay_env,hoi_quy=False):
    """Ngay trong cau hinh/du lieu (ISO) PHAI bang env NGAY (ngay dang cua luot chay). Thieu NGAY -> TRUOT. Du lieu THIEU ngay (fixture cu khong co khoa ngay_dang) -> TRUOT co ly do (khong crash).
    Ngoai le DUY NHAT: HOI_QUY=1 (bo qua phep ngay, ghi 'hoi quy'; cac phep khac van chay).
    -> (dat, so_do, ngay_dung)  ; ngay_dung = datetime.date dung de tinh han (NGAY neu co)."""
    if hoi_quy:
        try: nd=datetime.date.fromisoformat(ngay_env or ngay_du_lieu)
        except Exception: nd=None
        return True,f'HOI_QUY=1 (hoi quy): bo qua doi chieu ngay (du lieu {ngay_du_lieu or "khong co ngay_dang"}, NGAY {ngay_env or "khong"})',nd
    try: nd=datetime.date.fromisoformat(ngay_env) if ngay_env else None
    except Exception: return False,f'NGAY khong hop le: {ngay_env}',None
    if not ngay_du_lieu: return False,'du lieu THIEU ngay_dang: khong the doi chieu voi NGAY '+(ngay_env or '(khong co)'),nd
    if not ngay_env: return False,'THIEU env NGAY (ngay dang cua luot chay): khong the doi chieu ngay du lieu '+str(ngay_du_lieu),None
    if str(ngay_du_lieu)!=nd.isoformat(): return False,f'ngay du lieu {ngay_du_lieu} != NGAY {nd.isoformat()} (du lieu cu / sai ngay)',nd
    return True,f'ngay du lieu = NGAY {nd.isoformat()}',nd
def han_toi_thieu(nd,gio_dang,gio_them=2):
    """Moc toi thieu cua endTime = NGAY + gio dang cua dang + gio_them (gio VN)."""
    return datetime.datetime.fromisoformat(f'{nd.isoformat()}T{gio_dang}:00+07:00')+datetime.timedelta(hours=gio_them)
