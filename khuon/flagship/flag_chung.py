"""Ham THUAN dung chung cua khuon flagship (kiem + test): tap so duoc phep hien tren hinh."""
import re
def vnd_k(g):
    return f"{g['gia_vnd']//1000}K" if g['gia_vnd']%1000==0 else g['gia_vnd_hien']
def tap_so(g):
    """Moi chuoi so (regex \\d+([.,]\\d+)*) duoc phep xuat hien tren DOM — suy ra tu flagship.json. So la -> D1-so LOI."""
    ok=set()
    def them(t):
        for k in re.findall(r'\d+(?:[.,]\d+)*',str(t or '')): ok.add(k)
    for f in ('ten','ten_the','ten_goc','gia_hien','goc_hien','gia_vnd_hien','han_hien'): them(g.get(f))
    them(g.get('moc',{}).get('chu') if g.get('moc',{}).get('loai') not in (None,'khong') else '')
    ok.add(str(g['giam'])); ok.add(str(g['gia_vnd']//1000))
    for t in g.get('the_hien',[]): them(t)
    if g.get('han_con_ngay') is not None: ok.add(str(g['han_con_ngay']))
    ok.update(re.findall(r'\d+',g.get('han_hien','')))
    return ok
