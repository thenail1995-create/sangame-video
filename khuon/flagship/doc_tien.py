# Hien thi + doc tien / the / ngay cho khuon FLAGSHIP (A1). Chi stdlib; so thanh CHU bang ten_rut_gon.so_chu (dung chung Top 5).
#   hien_tien(19.99,'USD') -> '$19,99' · hien_tien(74.75,'HKD') -> 'HK$74,75' · hien_the(10,'USD') -> '$10'
#   doc_tien(19.99,'USD') -> 'mười chín đô chín mươi chín' · doc_tien(74.75,'HKD') -> 'bảy mươi bốn đô Hồng Kông bảy mươi lăm'
#   doc_the([{'menh_gia':10,'so_luong':2}],'USD') -> 'Hai thẻ mười đô'
import datetime,pathlib,sys
T=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(T.parent/'top5'))
import ten_rut_gon as tr
so_chu=tr.so_chu
TIEN_TE_CUA_MA={'US':'USD','HK':'HKD','SG':'SGD'}      # vung Flagship duoc chon -> tien te cua trang store
LOC_CUA_MA={'US':'en-us','HK':'en-hk','SG':'en-sg'}
TEN_VUNG={'US':'Mỹ','HK':'Hồng Kông','SG':'Singapore'}  # ten doc/hien thi cua vung (Singapore doc day du, khong 'Sing')
TIEN_TO={'USD':'$','HKD':'HK$','SGD':'S$'}
HAU_DO={'USD':'đô','HKD':'đô Hồng Kông','SGD':'đô Singapore'}
VN=datetime.timezone(datetime.timedelta(hours=7))

def _xu(so):
    """So tien -> so xu nguyen (tranh loi so thuc: 19.99*100 = 1998.9999...)."""
    return int(round(float(so)*100))
def so_vn(x):
    """560000 -> '560.000' (nghin '.'). Chi so nguyen."""
    return f'{int(x):,}'.replace(',','.')
def hien_tien(so,tien_te):
    """Gia cuc bo: 19.99 -> '$19,99'; 20 -> '$20'; dau phay thap phan."""
    p=TIEN_TO[tien_te]; xu=_xu(so); d,c=divmod(xu,100)
    return f'{p}{d}' if c==0 else f'{p}{d},{c:02d}'
def hien_the(menh_gia,tien_te):
    """Menh gia the: 10 -> '$10', 80 HKD -> 'HK$80'."""
    return hien_tien(menh_gia,tien_te)
def hien_vnd(vnd):
    return f'{so_vn(vnd)}đ'
def doc_vnd(vnd):
    """560000 -> 'năm trăm sáu mươi nghìn'. Chi nhan boi cua 1000 va < 10 trieu (so_chu toi 9999 nghin)."""
    if vnd%1000 or not 0<vnd<10_000_000: raise ValueError(f'khong doc duoc {vnd} thanh «X nghìn»')
    return so_chu(vnd//1000)+' nghìn'
def doc_tien(so,tien_te):
    """'X đô Y' (USD) · 'X đô Hồng Kông Y' · 'X đô Singapore Y'; Y bo khi = 0; Y < 10 doc 'lẻ năm'."""
    xu=_xu(so); d,c=divmod(xu,100)
    if d>9999: raise ValueError(f'tien qua lon: {so}')
    ra=f'{so_chu(d)} {HAU_DO[tien_te]}'
    if c: ra+=' '+(('lẻ '+so_chu(c)) if c<10 else so_chu(c))
    return ra
_SL={1:'một',2:'hai',3:'ba',4:'bốn'}
def gom_the(the):
    """[{'menh_gia','so_luong',..}] (hoac tuple (menh_gia,so_luong,gia_vnd)) -> list dict menh_gia giam dan."""
    ra=[]
    for t in the:
        if isinstance(t,dict): mg,sl=t['menh_gia'],t['so_luong']; g=t.get('gia_vnd')
        else: mg,sl,g=t
        mg=int(mg) if float(mg)==int(mg) else float(mg)
        ra.append({'menh_gia':mg,'so_luong':int(sl),'gia_vnd':int(round(g)) if g is not None else None})
    return sorted(ra,key=lambda x:-x['menh_gia'])
def so_tam(the): return sum(t['so_luong'] for t in gom_the(the))
def the_hien(the,tien_te):
    """['$10','$10'] - moi tam mot phan tu."""
    return [hien_the(t['menh_gia'],tien_te) for t in gom_the(the) for _ in range(t['so_luong'])]
def doc_the(the,tien_te):
    """'Hai thẻ mười đô' / 'Một thẻ mười đô, một thẻ năm đô và một thẻ một đô' (HKD/SGD: them 'Hồng Kông'/'Singapore' sau 'đô')."""
    g=gom_the(the); phan=[]
    for t in g:
        sl=t['so_luong']
        if not 1<=sl<=4: raise ValueError(f'so tam {sl} ngoai 1..4')
        mg=t['menh_gia']
        mgc=so_chu(mg)+' '+HAU_DO[tien_te] if float(mg)==int(mg) else doc_tien(mg,tien_te)
        phan.append(f'{_SL[sl]} thẻ {mgc}')
    s=phan[0] if len(phan)==1 else ', '.join(phan[:-1])+' và '+phan[-1]
    return s[0].upper()+s[1:]
def han_vn(end_ms):
    """endTime (ms) -> (datetime VN, '5/11', 'ngày năm tháng mười một')."""
    dt=datetime.datetime.fromtimestamp(int(end_ms)/1000,VN)
    thang='tư' if dt.month==4 else so_chu(dt.month)
    return dt,f'{dt.day}/{dt.month}',f'ngày {so_chu(dt.day)} tháng {thang}'
def doc_phien_ban(x):
    """'2.5' -> 'hai chấm năm' · '1.12' -> 'một chấm mười hai' · '1.05' -> 'một chấm không năm' · '3' -> 'ba'."""
    d,_,le=str(x).partition('.')
    ra=so_chu(int(d))
    if le:
        ra+=' chấm '+(('không '+so_chu(int(le))) if le.startswith('0') and int(le)>0 else so_chu(int(le)))
    return ra
