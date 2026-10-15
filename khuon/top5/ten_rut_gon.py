# Ten game cho video Top 5: ten HIEN THI tren hinh, ten DOC trong loi, so thanh chu (B1/B4).
# - hien_thi(ten_goc): bo (R)/(TM), ngoac don ( ... ), hau to "for PS5", "PS4 & PS5", "full game"; rut gon ten qua dai.
# - doc(ten_goc): ten may DOC (so thanh chu, bo ten ban "Definitive/Complete Edition"...); bang ngoai le trong ten_ngoai_le.json thang.
# - doc_duoc(ten_goc): False neu ten co chu+so lien nhau (2K27, F1...) ma KHONG co trong bang ngoai le - may doc khong on dinh -> chon-top5 bo ung vien.
# Bang ngoai le: khoa = ten HIEN THI viet thuong (da bo (R)(TM)); gia tri = chuoi may doc.
import json,pathlib,re
T=pathlib.Path(__file__).resolve().parent
NGOAI_LE={k.lower():v for k,v in json.load(open(T/'ten_ngoai_le.json',encoding='utf-8')).items() if not k.startswith('_')}
SO=['không','một','hai','ba','bốn','năm','sáu','bảy','tám','chín']
def so_chu(n):
    """0..9999 -> chu: 112 'một trăm mười hai', 105 'một trăm lẻ năm', 75 'bảy mươi lăm', 21 'hai mươi mốt', 2026 'hai nghìn không trăm hai mươi sáu'."""
    if n>=1000:
        ng,du=divmod(n,1000); r=so_chu(ng)+' nghìn'
        if du==0: return r
        return r+(' không trăm '+so_chu(du) if du<100 else ' '+so_chu(du))
    tr,ch,dv=n//100,(n//10)%10,n%10; o=[]
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
LA_MA={'ii':2,'iii':3,'iv':4,'v':5,'vi':6,'vii':7,'viii':8,'ix':9}
HAU_TO=re.compile(r"\s*(?:[-–—|:]\s*)?(?:for\s+)?(?:PlayStation\s*®?\s*)?(?:PS\s*4\s*(?:&|and|\+|/)\s*PS\s*5|PS\s*5\s*(?:&|and|\+|/)\s*PS\s*4|PS\s*5|PS\s*4)\s*$",re.I)
EDITION=re.compile(r"\s*(?:[-–—:]\s*)?(?:(?:the\s+)?(?:definitive|complete|deluxe|ultimate|premium|standard|digital|gold|legendary|collector'?s?|anniversary|special|enhanced|director'?s\s+cut|game\s+of\s+the\s+year|goty|remastered|remaster)\s+)+(?:edition|collection|cut|version)?\s*$",re.I)
def hien_thi(ten):
    t=re.sub(r'[®™©]','',ten); t=re.sub(r'\([^)]*\)','',t)
    t=re.sub(r'\s+full game\s*$','',t,flags=re.I)
    for _ in range(3): t=HAU_TO.sub('',t)
    t=re.sub(r'\s+',' ',t).strip(' -–—|:')
    t=t.replace('’',"'")
    if len(t)>34:   # qua dai: bo ten ban (Deluxe/Complete Edition...), roi moi bo phu de neu phan dau con du dai (>= 14 ky tu)
        t=EDITION.sub('',t).strip(' -–—:') or t
    if len(t)>34:
        d=re.split(r'\s*(?::|\s[-–—]\s)\s*',t,maxsplit=1)[0]
        if len(d)>=14: t=d
    return t
def the(ten):
    """Ten NGAN cho the hang (K19): ten hien thi bo ten ban (Complete/Definitive Edition...) va phu de sau ':'/' - ' neu phan dau con >= 10 ky tu; trang ket giu ten day du."""
    h=hien_thi(ten); t=EDITION.sub('',h).strip(' -–—:') or h
    d=re.split(r'\s*(?::|\s[-–—]\s)\s*',t,maxsplit=1)[0]
    return d if len(d)>=10 else t
def _doc_tu_dong(hien):
    t=EDITION.sub('',hien).strip(' -–—:')
    t=re.split(r'\s*(?::|\s[-–—]\s)\s*',t,maxsplit=1)[0] if len(t)>26 else t   # phu de dai khong doc
    t=t.replace(':',',').replace('&',' và ').replace('+',' cộng ')
    ra=[]
    for tok in t.split():
        c=tok.strip(',.!?')
        if re.fullmatch(r'\d{1,4}',c): ra.append(tok.replace(c,so_chu(int(c))))
        elif c.lower() in LA_MA and ra: ra.append(tok.replace(c,SO[LA_MA[c.lower()]]))
        else: ra.append(tok)
    return re.sub(r'\s+',' ',' '.join(ra)).strip()
def doc(ten):
    h=hien_thi(ten)
    if h.lower() in NGOAI_LE: return NGOAI_LE[h.lower()]
    return _doc_tu_dong(h)
def doc_duoc(ten):
    """May doc ten nay on dinh khong: co trong bang ngoai le, hoac sau khi doi so/La Ma chi con chu cai Latin (co dau), dau cach, ' - . , !"""
    h=hien_thi(ten)
    if h.lower() in NGOAI_LE: return True
    d=doc(ten)
    if not d or len(d)>42: return False
    if re.search(r'[A-Za-zÀ-ỹ]\d|\d[A-Za-zÀ-ỹ]',h): return False          # 2K27, F1, GTA5...
    if any(re.fullmatch(r'[IVXLCDM]{2,}',w) and w.lower() not in LA_MA for w in d.split()): return False   # XVI, XIV: may doc tung chu cai
    return re.fullmatch(r"[A-Za-zÀ-ỹ0-9 '’.,!\-]+",d) is not None and not re.search(r'\d',d)
# --- dung chung voi kich-ban.py va kiem/kiem-tat-ca.py (D3) ---
VUNG={'Hồng Kông':'Hồng Kông','Indonesia':'Indo','Mỹ':'Mỹ','Singapore':'Sing','Thái Lan':'Thái','Ấn Độ':'Ấn Độ','Ukraine':'Ukraine'}   # 6 vung + Ukraine (tham khao, khong duoc chon); vung la -> ten day du
LOC_CUA_MA={'SG':'en-sg','HK':'en-hk','US':'en-us','ID':'en-id','TH':'en-th','IN':'en-in','UA':'uk-ua'}   # ma vung -> locale store (UA = uk-ua, KHONG ghep 'en-'+ma)
VUNG_THAM_KHAO=('IN','UA')   # gia tham khao, khong the o VN: khong bao gio la vung re nhat mua duoc
def ten_doc_cua(g): return g.get('ten_doc') or doc(g.get('ten_goc') or g['ten'])   # top5.json cu (fixture) chua co ten_doc -> tinh bang ham
def vung_doc_cua(g): return VUNG.get(g['vung'],g['vung'])
def nghin_so(gia): return int(gia.replace('.','').replace('đ',''))//1000   # '167.000đ' -> 167
