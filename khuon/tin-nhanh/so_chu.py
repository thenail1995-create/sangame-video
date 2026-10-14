# Số / ngày / tên game -> chữ ĐỌC ĐƯỢC cho giọng (LOI-SAI N7: số viết bằng chữ, "Săn Game chấm com chấm vi en" có dấu).
# Dùng chung cho sinh-tin.py (lời đọc) và kiem/kiem-tat-ca.py (so lời Whisper nghe với dữ liệu).
import json,pathlib,re,unicodedata,datetime

T=pathlib.Path(__file__).resolve().parent
CH=['không','một','hai','ba','bốn','năm','sáu','bảy','tám','chín']

def _ba(n,day_du):
    """Đọc 0..999. day_du=True: có số 0 ở hàng trăm/chục thì đọc 'không trăm' / 'lẻ' (khi đứng sau nhóm lớn hơn)."""
    tram,chuc,dv=n//100,(n//10)%10,n%10; ra=[]
    if tram or day_du: ra.append(CH[tram]+' trăm')
    if chuc>1:
        ra.append(CH[chuc]+' mươi')
        if dv==1: ra.append('mốt')
        elif dv==5: ra.append('lăm')
        elif dv: ra.append(CH[dv])
    elif chuc==1:
        ra.append('mười')
        if dv==5: ra.append('lăm')
        elif dv: ra.append(CH[dv])
    else:
        if dv:
            if tram or day_du: ra.append('lẻ')
            ra.append(CH[dv])
    return ' '.join(ra)

def so_ra_chu(n):
    """Số nguyên không âm -> chữ tiếng Việt (288000 -> 'hai trăm tám mươi tám nghìn'; 1350000 -> 'một triệu ba trăm năm mươi nghìn')."""
    n=int(n)
    if n==0: return 'không'
    if n<0: return 'âm '+so_ra_chu(-n)
    nhom=[]; 
    while n: nhom.append(n%1000); n//=1000
    ten=['','nghìn','triệu','tỷ']; ra=[]
    for i in range(len(nhom)-1,-1,-1):
        g=nhom[i]
        if g==0: continue
        dau=(i==len(nhom)-1)
        ra.append(_ba(g,not dau and any(nhom[j] for j in range(i+1,len(nhom)))) + (' '+ten[i] if ten[i] else ''))
    return re.sub(r'\s+',' ',' '.join(ra)).strip()

def tung_chu_so(s):
    """Chuỗi chữ số -> đọc từng số ('25' -> 'hai lăm', '1896' -> 'một tám chín sáu'): dùng cho số TRONG TÊN GAME (F1 25, FIFA 27)."""
    ra=[]
    for i,c in enumerate(s):
        ra.append('lăm' if (c=='5' and i>0) else CH[int(c)])
    return ' '.join(ra)

THU=['Thứ Hai','Thứ Ba','Thứ Tư','Thứ Năm','Thứ Sáu','Thứ Bảy','Chủ Nhật']
def thu_cua(d): return THU[d.weekday()]
def thang_chu(m): return 'tư' if m==4 else so_ra_chu(m)
def ngay_doc(d):
    """date -> 'thứ Hai mười hai tháng mười' (đọc ngày ĐĂNG)."""
    t=thu_cua(d); t=('thứ'+t[3:]) if t.startswith('Thứ') else t
    return f'{t} {so_ra_chu(d.day)} tháng {thang_chu(d.month)}'
def ngay_ddmm(d): return f'{d.day:02d}/{d.month:02d}'

def nam_chu(y,ngay_dang):
    if y==ngay_dang.year+1: return 'năm sau'
    if y==ngay_dang.year: return 'năm nay'
    return 'năm '+so_ra_chu(y)

def _chu_so_dinh(m):
    return m.group(0) if (m.group(1).upper()=='F' and len(m.group(2))==1) else m.group(1)+' '+tung_chu_so(m.group(2))

def doc_van_ban(s,ngay_dang):
    """Văn bản tiếng Việt có số/ngày (tít, nhãn ngắn của bài) -> chữ đọc được. Không còn chữ số nào trong kết quả."""
    s=re.sub(r'[™®©]','',s)
    s=re.sub(r'\bTHÁNG\s+(\d{1,2})/(\d{4})\b',lambda m:f'tháng {thang_chu(int(m.group(1)))} {nam_chu(int(m.group(2)),ngay_dang)}',s,flags=re.I)
    s=re.sub(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',lambda m:f'{so_ra_chu(int(m.group(1)))} tháng {thang_chu(int(m.group(2)))} {nam_chu(int(m.group(3)),ngay_dang)}',s)
    s=re.sub(r'\b(\d{1,2})/(\d{4})\b',lambda m:f'tháng {thang_chu(int(m.group(1)))} {nam_chu(int(m.group(2)),ngay_dang)}',s)
    s=re.sub(r'\b(\d{1,2})/(\d{1,2})\b',lambda m:f'{so_ra_chu(int(m.group(1)))} tháng {thang_chu(int(m.group(2)))}',s)
    s=re.sub(r'\bNĂM\s+(\d{4})\b',lambda m:nam_chu(int(m.group(1)),ngay_dang),s,flags=re.I)
    s=re.sub(r'(\d+)\s*%',lambda m:so_ra_chu(int(m.group(1)))+' phần trăm',s)
    s=re.sub(r'\b(\d{1,3}(?:\.\d{3})+)\s*đ\b',lambda m:so_ra_chu(int(m.group(1).replace('.','')))+' đồng',s)
    s=re.sub(r'\b([A-Za-z]+)(\d+)\b',_chu_so_dinh,s)     # PS5 -> PS năm ; F1 giữ nguyên
    s=re.sub(r'\b(\d+)\b',lambda m:so_ra_chu(int(m.group(1))) if len(m.group(1))<=3 else tung_chu_so(m.group(1)),s)
    s=re.sub(r'[·|]',',',s)
    s=' '.join(w.lower() if (w.isupper() and (not w.isascii() or (len(w)>=4 and re.search('[AEIOUY]',w)))) else w for w in s.split())   # TỪ -> từ, DEMO -> demo ; DMZ, QSSR, PS (viết tắt, không nguyên âm / ngắn) giữ nguyên
    return re.sub(r'\s+,',',',re.sub(r'\s+',' ',s)).strip()

# ---------- tên game ----------
HAU_TO=r'(?:super deluxe|deluxe|premium|standard|gold|ultimate|complete|definitive|digital|launch|day one|legacy|anniversary)\s+edition|edition'
def _ngoai_le():
    f=T/'ten-ngoai-le.json'
    return json.load(open(f,encoding='utf-8')) if f.exists() else {}

def ten_hien_thi(ten,toi_da=30):
    """Tên game rút gọn để HIỆN trên hình: bỏ ™®, '(PS4 & PS5)', hậu tố 'Deluxe Edition'...; quá dài -> bỏ phần sau ':' / ' - ', rồi cắt theo từ.
    Có trong ten-ngoai-le.json thì lấy bản ghi tay (khoá = tên gốc)."""
    goc=ten
    ne=_ngoai_le().get(goc)
    if ne and ne.get('hien'): return ne['hien']
    t=re.sub(r'[™®©]','',ten)
    t=re.sub(r'\s*\((?:[^()]*(?:PS4|PS5|Chinese|English|Korean|Japanese|Thai|Ver)[^()]*)\)','',t)
    t=re.sub(r'\s+for\s+PlayStation\s*\d?\s*$','',t,flags=re.I)
    t=re.sub(r'\s+for\s+PS[45]\s*$','',t,flags=re.I)
    t=re.sub(r'\s*(?:PS4\s*&\s*PS5|PS5\s*&\s*PS4)\s*$','',t,flags=re.I)
    t=re.sub(r'\s+PS[45]\s*$','',t,flags=re.I)
    for _ in range(2):   # "X: Definitive Edition", "X - The Complete Edition", "X Deluxe Edition"
        t=re.sub(r'\s*[:–—-]?\s*(?:The\s+)?(?:'+HAU_TO+r')\s*$','',t,flags=re.I)
    t=re.sub(r'\s+',' ',t).strip(' -–—:')
    if len(t)>toi_da:
        for sep in (':',' – ',' — ',' - '):
            if sep in t:
                dau=t.split(sep)[0].strip()
                if len(dau)>=6: t=dau; break
    if len(t)>toi_da:
        tu=t.split(); t=''
        for w in tu:
            if len((t+' '+w).strip())>toi_da: break
            t=(t+' '+w).strip()
    return t

def ten_doc(ten_hien,goc=None):
    """Tên game -> cách ĐỌC cho giọng: bỏ dấu ':' ; số trong tên đọc từng chữ số; bỏ năm/phiên bản 4 chữ số đứng cuối ('Hunt: Showdown 1896' -> 'Hunt Showdown'). Ngoại lệ tay trong ten-ngoai-le.json."""
    ne=_ngoai_le().get(goc or ten_hien) or _ngoai_le().get(ten_hien)
    if ne and ne.get('doc'): return ne['doc']
    t=re.sub(r'[™®©:;"“”]','',ten_hien)
    t=re.sub(r'\s+\d{4}$','',t)
    t=re.sub(r'\s*[–—]\s*',' ',t)
    t=re.sub(r'\b(\d+)\b',lambda m:tung_chu_so(m.group(1)),t)
    t=re.sub(r'\b([A-Za-z]+)(\d+)\b',_chu_so_dinh,t)   # F1 giữ nguyên (đọc "ép một"), PS5 -> PS năm
    t=' '.join(w.capitalize() if (w.isalpha() and w.isascii() and w.isupper() and len(w)>=4 and re.search('[AEIOUY]',w)) else w for w in t.split())   # STAR WARS -> Star Wars (giong khong danh van chu hoa); DMZ, QSSR giu nguyen
    return re.sub(r'\s+',' ',t).strip()

def bo_dau(t):
    t=''.join(c for c in unicodedata.normalize('NFD',t.lower()) if unicodedata.category(c)!='Mn').replace('đ','d')
    return t

LA_MA={'II':2,'III':3,'IV':4,'VI':6,'VII':7,'VIII':8,'IX':9,'XI':11,'XII':12}

def chuan_so_sanh(t):
    """Chuẩn hoá để so lời Whisper nghe với dữ liệu: bỏ dấu, '288 nghìn'/'288.000' -> chữ, số lẻ -> chữ, bỏ ký tự lạ."""
    t=re.sub(r'\b(II|III|IV|VI|VII|VIII|IX|XI|XII)\b',lambda m:str(LA_MA[m.group(1)]),t)   # 15/10: «Spec IV» giong doc «bốn», Whisper viet «Specs 4» -> ca hai ve 'bon'; chi so La Ma VIET HOA >= 2 chu (I/V/X don co the la chu cai)
    t=t.lower()
    t=re.sub(r'(\d+)\s*(?:phần trăm|%)',lambda m:so_ra_chu(int(m.group(1)))+' phan tram',t)
    t=re.sub(r'(\d+)\s*k\b',lambda m:so_ra_chu(int(m.group(1))*1000),t)     # Whisper viet '335k'
    t=re.sub(r'(\d+)\s*nghìn',lambda m:so_ra_chu(int(m.group(1))*1000),t)
    t=re.sub(r'\b(\d{1,3}(?:[.,]\d{3})+)\b',lambda m:so_ra_chu(int(re.sub(r'[.,]','',m.group(1)))),t)
    t=re.sub(r'\b(\d+)\b',lambda m:so_ra_chu(int(m.group(1))),t)
    t=bo_dau(t)
    return re.findall(r'[a-z0-9]+',t)
