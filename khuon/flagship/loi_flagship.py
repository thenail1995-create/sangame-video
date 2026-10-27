# Loi doc Flagship: 7 doan (mo,gia,the,[moc],han,vung,ket), so viet bang CHU; 7 kieu cau mo xoay theo toordinal()%7; uoc luong do dai.
import datetime,pathlib,sys
T=pathlib.Path(__file__).resolve().parent; sys.path.insert(0,str(T))
import doc_tien as dt
SAN_GIAY=16   # < 16 s bo game (brief 15-27 s, muc tieu 17-25 s)
SLOGAN='Săn Game: săn đúng kèo, chơi đỡ nghèo!'
MAU_MO=['{V} đồng là có {G}.','{V} đồng, đủ mua đứt {G}.','Chỉ {V} đồng là có {G} rồi.','{V} đồng cho {G}, rẻ chưa?','{V} đồng là chơi được {G}.','{V} đồng mua được {G}, thật đó.','{V} đồng thôi, {G} về tay.']
def kieu_mo(ngay_iso): return datetime.date.fromisoformat(ngay_iso).toordinal()%7
def cau_mo(f,k):
    c=MAU_MO[k].format(V=f['vnd_doc'],G=f['ten_doc']); return c[0].upper()+c[1:]
def doan(f,ngay_iso,co_moc=True):
    """-> [(k, loi)] (loi CHUA co the cam xuc)."""
    k=kieu_mo(ngay_iso); v=dt.TEN_VUNG[f['ma']]
    ra=[('mo',cau_mo(f,k)),
        ('gia',f"Game đang giảm {dt.so_chu(f['giam'])} phần trăm trên PS Store {v}, từ {f['goc_doc']} còn {f['gia_doc']}."),
        ('the',f"{f['the_doc']} là vừa khít, đúng {f['vnd_doc']}.")]
    if co_moc and (f.get('moc') or {}).get('loai') in ('tin','thap_nhat'): ra.append(('moc',f['moc']['cau']))
    ra+= [('han',f"Giảm giá tới {f['han_doc']}"+(f", còn {dt.so_chu(f['han_con_ngay'])} ngày nữa." if (f.get('han_con_ngay') or 0)>=2 else '.')),('vung',f'Nhớ là cần tài khoản PSN {v}.'),('ket',SLOGAN)]
    return ra
def _am_tiet(tu):
    t=tu.strip('.,!?:;')
    if t.isascii() and len(t)>=6 and t.isalpha(): return -(-len(t)//3)   # ten tieng Anh dai ~ 1 am tiet / 3 chu
    return 1
def uoc_giay(ds):
    """(am tiet / 5,2 giay) + 0,35 s moi doan. Am tiet: moi tu 1, tu ASCII chu cai dai >= 6 tinh len(tu)/3 lam tron len."""
    n=sum(_am_tiet(t) for _,c in ds for t in c.split())
    return n/5.2+0.35*len(ds)
def lap_loi(f,ngay_iso):
    """Ap quy tac do dai: > 25 s -> bo moc; van > 26 s -> None (bo game). Tra (doan, giay, da_bo_moc)."""
    ds=doan(f,ngay_iso); g=uoc_giay(ds); bo=False
    if g>25 and any(k=='moc' for k,_ in ds):
        ds=doan(f,ngay_iso,co_moc=False); g=uoc_giay(ds); bo=True
    return (None if g>26 or g<SAN_GIAY else ds),g,bo
