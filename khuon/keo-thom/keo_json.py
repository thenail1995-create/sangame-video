# Doc + chuan hoa keo.json cho full.html (dung.py) va nen08.py: them cac truong HIEN THI (so ky, thang, ngay dd/mm, co, ten vung, gio het giam...).
# Giong "du lieu thanh bien" cua Top 5; mot nguon duy nhat cho dinh dang hien thi. kiem/kiem-tat-ca.py tinh LAI doc lap tu keo.json tho de doi chieu.
import copy,datetime,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from loi_chu import VUNG,TEN_DAY_DU,ten_hien,gon_ten
VN=datetime.timezone(datetime.timedelta(hours=7))
def nap(duong=None):
    T=pathlib.Path(__file__).resolve().parent
    return chuan(json.load(open(duong or T/'keo.json',encoding='utf-8')))
def chuan(raw):
    k=copy.deepcopy(raw); g=k['game']
    g['tien'],g['chinh']=ten_hien(g['ten']); g['may']=g.get('may') or 'PS5'; g['giam']=int(g['giam'])
    nd=datetime.date.fromisoformat(k['ngay_dang']); dl=datetime.date.fromisoformat(k.get('ngay_du_lieu') or k['ngay_dang'])
    k['so_ky_s']=f"{int(k.get('so_ky',1)):03d}"; k['thang']=f'{nd.month:02d}'; k['nam']=str(nd.year)
    k['ngay_dm']=f'{dl.day:02d}/{dl.month:02d}'; k['ngay_dmy']=f'{dl.day:02d}.{dl.month:02d}.{dl.year%100:02d}'
    for v in k['vung']:
        h,_,co,_=VUNG[v['ma']]; v.setdefault('hien',h); v.setdefault('co',co); v.setdefault('dd',TEN_DAY_DU[v['ma']])
    het=datetime.datetime.fromtimestamp(int(k['han']['endTime'])/1000,VN)
    k['han'].update(dm=f'{het.day:02d}/{het.month:02d}',hhmm=f'{het.hour:02d}:{het.minute:02d}',gio=het.hour,phut=het.minute,iso=het.isoformat())
    k.setdefault('ghi_chu_bang','Quy theo giá thẻ PSN từng vùng · giá tham khảo')
    return k
