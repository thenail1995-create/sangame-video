"""Game "da noi bat" trong N ngay gan nhat o BAT KY dang nao (Hao 12/10: "tin co the bi trung").
Nguon: manifest.json cua cac Release `v-<ngay>-<dang>` (tin-nhanh, top5, keo-thom, keo-thom-2, keo-thom-3) cua sangame-video.
  - Keo = game cua keo; Top 5 = 5 game; Tin nhanh = game "re nhat" cua tung tin gia (KHONG tinh cac game phu trong danh sach).
  - Release moi co truong manifest `noi_bat` = [{"ten":..., "pids":[...]}] (sinh luc dung). Release cu khong co -> suy:
      top5 / keo : kiem_lai (5 game / game cua keo);
      tin-nhanh  : cau "rẻ nhất <ten rut gon>, <gia>đ" trong loi_dang.mo_ta, ghep voi kiem_lai theo GIA (gia_vnd) + ten; khong ghep duoc -> chi giu ten rut gon.
  Khoang ngay: [ngay - so_ngay, ngay], tru chinh khung (ngay, dang) dang dung (cac khung KHAC cung ngay van tinh).
  Khop theo PID (bo tien to vung UP/HP/EP.. truoc dau '-') HOAC ten goc chuan hoa HOAC khoa DONG game (dong_game: Mafia = Mafia III = Mafia: Definitive Edition).
  Loi mang: thu 3 lan; van loi -> tap RONG kem ghi chu 'CANH BAO' (khong chan khung, nhu lich_su_top5).
  da_noi_bat(ngay, dang, so_ngay=3, ten_goc=None) -> NoiBat ; ten_goc = tin_tu_sinh._ten_goc neu co (mac dinh: chuan hoa don gian).
  Thu tren Mac khong co mang: env NOI_BAT_LICH_SU = duong dan json {"v-2026-10-12-top5": <manifest>, ...}."""
import datetime,json,os,re,subprocess,time
DANG_HOP_LE=('tin-nhanh','top5','keo-thom','keo-thom-2','keo-thom-3')
REPO_MAC_DINH='thenail1995-create/sangame-video'
_RE_TAG=re.compile(r'v-(\d{4}-\d{2}-\d{2})-(tin-nhanh|top5|keo-thom(?:-[23])?)')
_RE_RE_NHAT=re.compile(r'rẻ nhất\s+(.+?),\s*([\d.]+)\s*đ')

def pid_loi(pid):
    """Bo tien to vung (UP1001-PPSA36864_00-MAFIA3.. -> PPSA36864_00-MAFIA3..). Khong co '-' thi giu nguyen."""
    return pid.split('-',1)[1] if pid and '-' in pid else (pid or '')
def ten_don_gian(ten):
    k=re.sub(r'[®™©]','',ten or '').lower().replace('’',"'")
    k=re.sub(r'\(.*?\)','',k); k=re.sub(r'[^\w\s]',' ',k)
    tu=k.split()
    while tu and tu[-1] in ('edition','standard','deluxe','definitive','remastered','ps4','ps5','version','for','and'): tu.pop()
    return ' '.join(tu)
_LA_MA=frozenset('i ii iii iv v vi vii viii ix x xi xii'.split())
_BO=frozenset('edition standard deluxe definitive remastered remaster remake ultimate complete collection bundle gold premium digital super game of the year goty director cut version for ps4 ps5 and pack'.split())
_TIEN_TO=('marvel s','tom clancy s','sid meier s','disney s')
def dong_game(ten):
    """Khoa DONG game (Hao 12/10: Mafia III hom truoc, Mafia phan 1 hom sau): cat sau ':' / ' - ', bo (..), tien to hang (Marvel's), so phan, so La Ma, hau to edition/nen tang.
    'Mafia', 'Mafia III', 'Mafia: Definitive Edition' -> 'mafia'; 'Marvel's Spider-Man 2' / 'Spider-Man Remastered' -> 'spider man'; 'Call of Duty: X' -> 'call of duty'."""
    k=re.sub(r'[®™©]','',ten or '').lower().replace('’',"'")
    k=re.sub(r'\(.*?\)','',k); k=re.split(r':|\s[-–—]\s',k)[0]
    k=' '.join(re.sub(r'[^\w\s]',' ',k).split())
    for tt in _TIEN_TO:
        if k.startswith(tt+' '): k=k[len(tt)+1:]
    # 'of'/'the' o GIUA ten ('Call of Duty') phai giu: chi bo chung o dau/cuoi
    gh=[w for w in k.split() if not w.isdigit() and w not in _LA_MA and w not in (_BO-{'of','the','for','and'})]
    while gh and gh[-1] in ('of','the','for','and'): gh.pop()
    while gh and gh[0]=='the': gh.pop(0)
    return ' '.join(gh) or k
class NoiBat:
    def __init__(self,ten_goc=None):
        self.ten_goc=ten_goc or ten_don_gian; self.pids=set(); self.ten=set(); self.dong=set(); self.nguon={}; self.canh_bao=None
    def them(self,ten=None,pids=(),nguon=''):
        if ten:
            k=self._k(ten)
            if k: self.ten.add(k); self.nguon.setdefault(('ten',k),nguon)
            dg=dong_game(ten)
            if dg: self.dong.add(dg); self.nguon.setdefault(('dong',dg),nguon)
        for p in pids or ():
            q=pid_loi(p)
            if q: self.pids.add(q); self.nguon.setdefault(('pid',q),nguon)
    def _k(self,ten):
        try: return self.ten_goc(ten) or ''
        except Exception: return ten_don_gian(ten)
    def trung(self,ten=None,pids=()):
        """-> chuoi ly do (khop pid hoac ten) hoac None."""
        for p in pids or ():
            q=pid_loi(p)
            if q and q in self.pids: return f'pid {q} ({self.nguon.get(("pid",q),"")})'
        if ten:
            k=self._k(ten)
            if k and k in self.ten: return f'ten "{k}" ({self.nguon.get(("ten",k),"")})'
            dg=dong_game(ten)
            if dg and dg in self.dong: return f'dong game "{dg}" ({self.nguon.get(("dong",dg),"")})'
        return None
    def __len__(self): return len(self.ten)+len(self.pids)+len(self.dong)

def _gh(args,timeout=60):
    """Chay `gh`, thu 3 lan. Tra stdout; loi cuoi -> raise RuntimeError."""
    err=''
    for lan in range(3):
        try:
            r=subprocess.run(['gh']+args,capture_output=True,text=True,timeout=timeout)
            if r.returncode==0: return r.stdout
            err=r.stderr.strip()[:200]
        except Exception as e: err=f'{type(e).__name__}: {str(e)[:120]}'
        time.sleep(2*(lan+1))
    raise RuntimeError(err or 'gh loi')

def tu_manifest(m,dang):
    """manifest (dict) -> list dict(ten, pids) cac game noi bat. Uu tien truong `noi_bat`; thieu -> suy tu kiem_lai / mo ta (Release cu)."""
    nb=m.get('noi_bat')
    if isinstance(nb,list):
        return [dict(ten=x.get('ten'),pids=list(x.get('pids') or [])) for x in nb if isinstance(x,dict) and (x.get('ten') or x.get('pids'))]
    kl=[x for x in (m.get('kiem_lai') or []) if isinstance(x,dict)]
    if dang!='tin-nhanh':   # top5: 5 game; keo: 1 game (3 vung cung ten)
        gop={}
        for x in kl:
            if x.get('ten'): gop.setdefault(x['ten'],[]).append(x.get('pid'))
        return [dict(ten=t,pids=[p for p in ps if p]) for t,ps in gop.items()]
    ra=[]
    for ten,gia in _RE_RE_NHAT.findall(((m.get('loi_dang') or {}).get('mo_ta')) or ''):
        gia_vnd=int(gia.replace('.',''))
        # ghep: gia khop + ten kiem_lai bat dau bang ten rut gon (token dau); khong ghep duoc -> chi ten rut gon
        tk=ten_don_gian(ten).split()
        kh=[x for x in kl if x.get('gia_vnd')==gia_vnd and tk and ten_don_gian(x.get('ten','')).split()[:len(tk)]==tk]
        if len(kh)>1: kh=[x for x in kh if x.get('pid')]
        ra.append(dict(ten=ten,pids=[x['pid'] for x in kh if x.get('pid')]))
        for x in kh:
            if x.get('ten'): ra.append(dict(ten=x['ten'],pids=[x['pid']] if x.get('pid') else []))
    return ra

def da_noi_bat(ngay,dang,so_ngay=3,ten_goc=None,repo=None):
    """ngay = ngay DANG ('YYYY-MM-DD' hoac date); dang = khung dang dung (bi loai khoi lich su). -> NoiBat."""
    d0=ngay if isinstance(ngay,datetime.date) else datetime.date.fromisoformat(str(ngay)); tu=d0-datetime.timedelta(days=so_ngay)
    nb=NoiBat(ten_goc); dem=0
    try:
        f=os.environ.get('NOI_BAT_LICH_SU')
        if f:
            with open(f,encoding='utf-8') as fh: kho=json.load(fh)
            ds=[(tg,lambda tg=tg:kho[tg]) for tg in kho]
        else:
            repo=repo or os.environ.get('GITHUB_REPOSITORY') or REPO_MAC_DINH
            j=json.loads(_gh(['release','list','-R',repo,'--limit','200','--json','tagName,isDraft']) or '[]')
            ds=[(x['tagName'],(lambda tg=x['tagName']:json.loads(_gh(['release','download',tg,'-R',repo,'-p','manifest.json','-O','-'])))) for x in j if not x.get('isDraft')]
        for tg,tai in ds:
            m=_RE_TAG.fullmatch(tg)
            if not m: continue
            ng=datetime.date.fromisoformat(m.group(1)); d_=m.group(2)
            if not (tu<=ng<=d0) or (ng==d0 and d_==dang): continue
            for g in tu_manifest(tai(),d_): nb.them(g.get('ten'),g.get('pids'),f'{tg}');
            dem+=1
        nb.ghi_chu=f'{dem} Release trong {so_ngay} ngay den {d0} (tru {d0}/{dang}): {len(nb.ten)} ten, {len(nb.pids)} pid'
    except Exception as e:
        nb=NoiBat(ten_goc); nb.canh_bao=f'CANH BAO: khong doc duoc lich su noi bat ({type(e).__name__}: {str(e)[:120]}) - khong loc game da noi bat'
        nb.ghi_chu=nb.canh_bao; print(nb.canh_bao)
    return nb
