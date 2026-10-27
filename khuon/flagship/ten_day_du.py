# Ten DAY DU cho Flagship (khong dung tr.hien_thi/tr.doc/tr.the vi chung rut gon va BO ten ban Deluxe/Definitive...).
#   tach('STAR WARS Jedi: Fallen Order Deluxe Edition') -> ('STAR WARS Jedi: Fallen Order','Deluxe')
#   hien('...Deluxe Edition') -> 'STAR WARS Jedi: Fallen Order Deluxe' · doc(...) -> 'STAR WARS Jedi, Fallen Order bản Deluxe'
#   'Tomb Raider: Definitive Edition' -> hien 'Tomb Raider Definitive' · doc 'Tomb Raider bản Definitive'
# Giu phu de sau ':'; so trong ten doc bang chu; bang ngoai le ten_ngoai_le.json (khoa = ten hien thi viet thuong) van dung cho cach doc tung tu.
import pathlib,re,sys
T=pathlib.Path(__file__).resolve().parent; sys.path.insert(0,str(T.parent/'top5'))
import ten_rut_gon as tr
def sach(ten):
    """Bo ®™©, (..), 'full game', hau to 'for PS5'/'PS4 & PS5'; giu phu de. KHONG rut gon do dai."""
    t=re.sub(r'[®™©]','',ten or ''); t=re.sub(r'\([^)]*\)','',t); t=re.sub(r'\s+full game\s*$','',t,flags=re.I)
    for _ in range(3): t=tr.HAU_TO.sub('',t)
    return re.sub(r'\s+',' ',t.replace('’',"'")).strip(' -–—|:')
def tach(ten):
    """-> (ten goc khong phien ban, nhan phien ban '' | 'Deluxe' | 'Digital Deluxe' | 'Game of the Year'...)."""
    t=sach(ten); m=tr.EDITION.search(t)
    if not m or m.start()==0: return t,''
    nhan=re.sub(r'^[\s\-–—:]+|[\s]*(edition|collection|cut|version)\s*$','',m.group(0),flags=re.I).strip(' -–—:')
    nhan=re.sub(r'^the\s+','',nhan,flags=re.I)
    return t[:m.start()].strip(' -–—:'),nhan
def hien(ten):
    b,n=tach(ten); return f'{b} {n}'.strip()
def _doc_goc(b):
    ra=[]; t=b.replace(':',',').replace('&',' và ').replace('+',' cộng ')
    for tok in t.split():
        c=tok.strip(',.!?')
        if re.fullmatch(r'\d{1,4}',c): ra.append(tok.replace(c,tr.so_chu(int(c))))
        elif c.lower() in tr.LA_MA and ra: ra.append(tok.replace(c,tr.SO[tr.LA_MA[c.lower()]]))
        else: ra.append(tok)
    return re.sub(r'\s+',' ',' '.join(ra)).strip()
def doc(ten):
    b,n=tach(ten)
    if hien(ten).lower() in tr.NGOAI_LE: return tr.NGOAI_LE[hien(ten).lower()]
    r=tr.NGOAI_LE.get(b.lower()) or _doc_goc(b)
    return f'{r} bản {n}' if n else r
def doc_duoc(ten):
    """Ten day du doc duoc on dinh: tr.doc_duoc cho phan goc (2K27, XVI...) VA ban doc day du khong con so/ky tu la, <= 60 ky tu."""
    b,_=tach(ten)
    if not tr.doc_duoc(b): return False
    d=doc(ten)
    return bool(d) and len(d)<=60 and re.fullmatch(r"[A-Za-zÀ-ỹ0-9 '’.,!\-]+",d) is not None and not re.search(r'\d',d)
