# Doc so / vung / han / ten game tu ban Whisper cho phep D3 cua 3 khuon (Top 5, Tin nhanh, Keo thom) — SO GIA TRI, KHONG SO CHU.
# Ly do (Sol soi 11/10, loi #7-#13, #17): D3 cu so do giong chu ("sau muoi bay" khop trong "mot tram sau muoi bay nghin", 64% giong 54%, "Resident Evil nam" giong
# "... bon") nen doc sai tien/phan tram/vung/ten van DAT. Moi ham o day tra GIA TRI da doc, nguoi goi so bang `==`.
#   doc_tien(van_ban)      -> [(gia_tri_vnd, tien_to, vi_tri)]   "mot tram sau muoi bay nghin" / "167.000" / "167k" / "1,3 trieu" / "sau tram ruoi" (=650.000)
#   doc_phan_tram(van_ban) -> [(so, vi_tri)]                     "54%" / "54 phan tram" / "chin muoi phan tram"
#   doc_vung(van_ban)      -> [(ma, vi_tri)]                     My/Hoa Ky->US, Hong Kong->HK, Sing->SG, Thai->TH, Indo->ID, An Do->IN
#   doc_han(van_ban)       -> [{gio24, buoi, ngay}]              "hai gio chieu ngay hai muoi hai thang muoi" / "muoi gio dem ngay mai"
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
            if h2=='don' or (h2=='nguyen' and v2<10): return tong+v2*100_000,j2     # 'mot trieu ba' = 1.300.000
            return tong+round(v2*1000),j2                                           # 'mot trieu ba tram' = 1.300.000 ; 'mot trieu nam muoi' = 1.050.000
        return tong,j
    if x in NGHIN or x=='k': return round(v*1000),j+1
    if x in DONG:
        j+=1
        return (v if hang=='nhom' or (hang=='nguyen' and v>=1000) else round(v*1000)),j
    if x in NON_TIEN_SAU: return None
    if i>0 and not T[i][2] and _w(T,i-1) in NON_TIEN_TRUOC: return None
    if hang=='nhom': return v,j
    if hang=='thap': return None
    if hang=='nguyen' and v>=1000: return v,j
    return round(v*1000),j       # khong co don vi trong ngu canh tien -> nghin (luat B1)
def doc_tien(van_ban):
    """-> [(gia_tri_vnd, tien_to, vi_tri)] theo thu tu xuat hien. Con so di kem 'phan tram' / '%' la PHAN TRAM, khong bao gio la tien."""
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
        kq.append((vnd,tt,T[i][3])); i=j
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
        elif x=='ngày':
            y=_w(T,j+1) if _lien(T,j+1) else None
            if y in ('mai','kia'): ngay=y
            else:
                r=_so(T,j+1) if _lien(T,j+1) else None
                if r and _w(T,r[2])=='tháng' and _lien(T,r[2]):
                    m=_so(T,r[2]+1)
                    mo=m[0] if m else (4 if _w(T,r[2]+1)=='tư' else None)
                    if mo: ngay=(int(r[0]),int(mo))
        kq.append(dict(gio24=gio24,buoi=buoi,ngay=ngay))
    return kq

# ---------------------------------------------------------------- ten game
VERSION={'deluxe':'deluxe','ultimate':'ultimate','definitive':'definitive','remastered':'remastered','remaster':'remastered','remake':'remake',
         'complete':'complete','goty':'goty'}
# Cum tieng Viet chi phien ban (Loi_chu: Definitive -> 'bản làm lại', Complete -> 'bản đầy đủ'). So bang bo dau, 'bản' di truoc la tuy chon. Bang alias theo game: Whisper small hay nghe
# 'làm lại' thanh 'nắm lại' va 'bản' thanh 'bán' (do tren video that Top 5 11/10) — alias nay KHONG phai noi nguong, chi liet ke cach nghe sai da biet cua DUNG cum nay.
VERSION_VN=[(('lam','lai'),'remake'),(('nam','lai'),'remake'),(('day','du'),'complete'),(('hoan','chinh'),'complete')]
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
def _tok_ten(text):
    """Ten game -> [('n',gia_tri)|('v',lop_phien_ban)|('w',tu_bo_dau)]. 4 = IV = 'bốn' ; 'mười một' = 11 ; 'hai lăm' = 25 (doc tung chu so)."""
    raw=re.findall(r"[^\W_]+",nfc(text)); low=[r.lower() for r in raw]; ra=[]; i=0
    while i<len(raw):
        r,l=raw[i],low[i]
        if l.isdigit(): ra.append(('n',int(l))); i+=1; continue
        rm=_la_ma_gt(r) if r.isupper() else None
        if rm: ra.append(('n',rm)); i+=1; continue
        hit=None; bd=[bo_dau(x) for x in low[i:i+3]]
        for ph,lop in VERSION_VN:
            if tuple(bd[:len(ph)])==ph: hit=(len(ph),lop); break
            if bd[:1]==['ban'] and tuple(bd[1:1+len(ph)])==ph: hit=(len(ph)+1,lop); break
        if hit: ra.append(('v',hit[1])); i+=hit[0]; continue
        if l in VERSION: ra.append(('v',VERSION[l])); i+=1; continue
        if l in CHU_SO or l=='mười':
            T=[('w',x,False,0) for x in low[i:i+8]]; r2=_ba(T,0)
            if r2:
                gt,_,j,hang=r2
                if hang=='don':
                    ds=[gt]; k=1
                    while k<len(T) and T[k][1] in _DAY_DON: ds.append(CHU_SO.get(T[k][1],DON_VI_SAU.get(T[k][1]))); k+=1
                    ra.append(('n',int(''.join(map(str,ds))))); i+=k
                else: ra.append(('n',gt)); i+=j
                continue
        ra.append(('w',bo_dau(l))); i+=1
    return ra
def _cs(t): return f'#{t[1]}' if t[0]=='n' else f'~{t[1]}' if t[0]=='v' else t[1]
def _cua_so_tot_nhat(M,H):
    """cua so [s:s+L) cua H (L = m-1 .. m+3 token) giong ten `M` nhat -> list token"""
    mj=''.join(_cs(t) for t in M); m=len(M); tot=(-1.0,[])
    for L in range(max(1,m-1),m+4):
        for s in range(0,max(1,len(H)-L+1)):
            w=H[s:s+L]
            if not w: continue
            sc=difflib.SequenceMatcher(None,mj,''.join(_cs(t) for t in w)).ratio()-0.001*abs(L-m)
            if sc>tot[0]: tot=(sc,w)
    return tot[1]
def so_phan_biet(mong,nghe):
    """Chi so token PHAN BIET (so phan/thu tu, so La Ma, so chu, Deluxe/Ultimate/Definitive/Remastered/Remake/Complete/'bản làm lại'/'bản đầy đủ') giua ten ky vong va cau nghe duoc.
    -> (dat, ly_do). Ten ky vong khong co token phan biet -> dat."""
    M=_tok_ten(mong); H=_tok_ten(nghe)
    can_n=Counter(t[1] for t in M if t[0]=='n'); can_v=Counter(t[1] for t in M if t[0]=='v')
    if not can_n and not can_v: return True,'khong co token phan biet'
    if not H: return False,'khong nghe duoc gi'
    W=_cua_so_tot_nhat(M,H); co_n=Counter(t[1] for t in W if t[0]=='n'); co_v=Counter(t[1] for t in W if t[0]=='v')
    chu_so_dinh=[t[1] for t in W if t[0]=='w' and re.fullmatch(r'[a-z]+\d+',t[1])]     # 'F125' = 'F1' + '25'
    thieu=[]
    for n,c in can_n.items():
        if co_n[n]<c and not any(s.endswith(str(n)) for s in chu_so_dinh): thieu.append(f'so {n}')
    for v,c in can_v.items():
        if co_v[v]<c: thieu.append(f'phien ban {v}')
    if thieu:
        return False,'thieu '+', '.join(thieu)+'; nghe duoc «'+' '.join(_cs(t) for t in W)+'»'
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
def cat_hang(nghe):
    """Bo tien to 'Hạng N' / 'Và hạng một' o dau cau Top 5 truoc khi so ten (Whisper hay nghe 'hạc bốn', 'h3', 'hang hai')."""
    tk=re.findall(r"[^\W_]+",nfc(nghe))
    for i in range(min(3,len(tk))):
        if re.fullmatch(r'h\d|một|hai|ba|bốn|năm|[1-5]|mot|bon|nam',tk[i].lower()):
            m=list(re.finditer(r"[^\W_]+",nfc(nghe)))[i]; return nfc(nghe)[m.end():].lstrip(' :,.;-')
    return nfc(nghe)

# ---------------------------------------------------------------- doi chieu mot doan
def cap_vung_tien(nghe):
    """-> [(ma_vung_gan_nhat_dung_truoc, vnd)] : moi khoan tien ghep voi vung nhac TRUOC no (vai tro 'vung -> chenh lech')."""
    vs=doc_vung(nghe); ra=[]
    for v,_,pos in doc_tien(nghe):
        truoc=[m for m,p in vs if p<pos]
        ra.append((truoc[-1] if truoc else None,v))
    return ra
def noi_tat_literal(vnd):
    """Cum KY VONG dang noi tat 'X tram Y' (loi_chu.noi_chenh: 760.000 = 'bảy trăm sáu') -> gia tri Whisper co the viet THEO CHU SO LITERAL ('706' = 706.000). Khong phai dung sai:
    chi tra gia tri khi ky vong that su la dang noi tat (Y = 2..9, tru 5 'rưỡi' va 1 'mười'; < 1 trieu); khong thi None."""
    n=int(vnd/10000+0.5)
    if vnd<1_000_000 and 10<n<100 and n%10 not in (0,1,5): return ((n//10)*100+n%10)*1000
    return None
def _la_day_con(can,co):
    it=iter(co); return all(any(x==y for y in it) for x in can)
def doi_chieu(nghe,tien=(),phan_tram=(),vung=(),ten=(),han=None,tien_thu_tu=(),cap=(),tien_tat=()):
    """So cau Whisper nghe duoc (`nghe`) voi gia tri KY VONG tinh tu du lieu. -> list loi (rong = dat).
    tien_tat: [vnd] ky vong dang noi tat 'X tram Y' (cho phep viet literal '706') · tien_thu_tu: [vnd] phai xuat hien DUNG THU TU · cap: [(ma_vung, vnd)] tien di sau vung tuong ung
    tien: [vnd] moi gia tri phai co mat DUNG (doc_tien) · phan_tram: [so] · vung: [ma] · ten: [ten mong (chu doc)] · han: han_ky_vong()."""
    loi=[]
    gt=[v for v,_,_ in doc_tien(nghe)]
    alt=lambda v:noi_tat_literal(v) if v in tien_tat else None      # tien_tat: ky vong la dang noi tat -> chap nhan dung phien am literal cua CHINH cum do
    for v in tien:
        if v not in gt and alt(v) not in gt: loi.append(f'TIEN: mong {v:,} nghe duoc {sorted(set(gt))} («{nghe[:70]}»)'.replace(',','.'))
    if tien_thu_tu and not _la_day_con(list(tien_thu_tu),gt): loi.append(f'TIEN THEO THU TU (vd goc roi con): mong {list(tien_thu_tu)} nghe duoc {gt} («{nghe[:70]}»)')
    cv=cap_vung_tien(nghe)
    for c in cap:
        if tuple(c) not in cv and (c[0],alt(c[1])) not in cv: loi.append(f'CAP vung-tien: mong {tuple(c)} nghe duoc {cv} («{nghe[:70]}»)')
    pt=[p for p,_ in doc_phan_tram(nghe)]
    for p in phan_tram:
        if p not in pt: loi.append(f'PHAN TRAM: mong {p}% nghe duoc {pt} («{nghe[:70]}»)')
    vg=[m for m,_ in doc_vung(nghe)]
    for m in vung:
        if m not in vg: loi.append(f'VUNG: mong {m} nghe duoc {vg or "khong co"} («{nghe[:70]}»)')
    for t in ten:
        ok,ly=so_ten(t,cat_hang(nghe))
        if not ok: loi.append(f'TEN «{t}»: {ly} («{nghe[:70]}»)')
    if han is not None:
        hs=doc_han(nghe)
        if not any(h['gio24']==han['gio24'] and h['buoi']==han['buoi'] and h['ngay']==han['ngay'] for h in hs):
            loi.append(f'HAN: mong {han} nghe duoc {hs or "khong co"} («{nghe[:70]}»)')
    return loi

# ---------------------------------------------------------------- nghe tren am thanh MP4 cuoi + cache theo bam PCM
def sha_pcm(x16):
    """Bam sha256 cua PCM da giai ma (16 kHz mono float32)."""
    return hashlib.sha256(x16.tobytes()).hexdigest()
def nghe_doan(x16,cua_so,nghe,thu_muc_cache,rev=''):
    """Nghe tung doan tren AM THANH TRICH TU MP4 CUOI (`x16`, khong phai giong goc). cua_so = {khoa: (a, b)} chi so mau 16 kHz.
    3 ban nen tang cung luong tieng -> cung bam PCM -> doan da nghe o ban truoc duoc dung lai (Whisper 1 lan). -> (heard {khoa: van_ban}, bang_chung)."""
    sha=sha_pcm(x16); f=pathlib.Path(thu_muc_cache)/f'kiem-nghe-{sha[:16]}.json'
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
GIO_DANG_MAC_DINH={'top5':'12:00','tin-nhanh':'07:30','keo-thom':'20:00'}
def kiem_ngay(ngay_du_lieu,ngay_env,hoi_quy=False):
    """Ngay trong cau hinh/du lieu (ISO) PHAI bang env NGAY (ngay dang cua luot chay). Thieu NGAY -> TRUOT. Ngoai le DUY NHAT: HOI_QUY=1.
    -> (dat, so_do, ngay_dung)  ; ngay_dung = datetime.date dung de tinh han (NGAY neu co)."""
    if hoi_quy:
        try: nd=datetime.date.fromisoformat(ngay_env or ngay_du_lieu)
        except Exception: nd=None
        return True,f'HOI_QUY=1: bo qua doi chieu ngay (du lieu {ngay_du_lieu}, NGAY {ngay_env or "khong"})',nd
    if not ngay_env: return False,'THIEU env NGAY (ngay dang cua luot chay): khong the doi chieu ngay du lieu '+str(ngay_du_lieu),None
    try: nd=datetime.date.fromisoformat(ngay_env)
    except Exception: return False,f'NGAY khong hop le: {ngay_env}',None
    if str(ngay_du_lieu)!=nd.isoformat(): return False,f'ngay du lieu {ngay_du_lieu} != NGAY {nd.isoformat()} (du lieu cu / sai ngay)',nd
    return True,f'ngay du lieu = NGAY {nd.isoformat()}',nd
def han_toi_thieu(nd,gio_dang,gio_them=2):
    """Moc toi thieu cua endTime = NGAY + gio dang cua dang + gio_them (gio VN)."""
    return datetime.datetime.fromisoformat(f'{nd.isoformat()}T{gio_dang}:00+07:00')+datetime.timedelta(hours=gio_them)
