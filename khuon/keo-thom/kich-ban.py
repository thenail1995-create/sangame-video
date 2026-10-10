# Loi doc Keo thom v9 tu keo.json — so viet bang CHU (may doc so de sai, LOI-SAI N7). Khuon cau co dinh, so/ten/vung/gio lay tu du lieu.
#   python3 kich-ban.py [keo.json]  -> loi.txt (co the cam xuc eleven_v3) + kich-ban.json
# kich-ban.json: {"doan":[{k, loi (khong the), neo:{ten_moc: chi so tu trong doan}}]} — can-chu.py can moc tung chu theo `loi.split()`
# (cung chi so), full.html lay moc theo KHOA doan + ten moc (`moc(k)`), am08.py/nen08.py dung chung. Khong con chi so tuyet doi W(n) (v9).
import datetime,json,pathlib,sys
T=pathlib.Path(__file__).resolve().parent; sys.path.insert(0,str(T))
from loi_chu import so_chu,nghin,noi_goc,noi_chenh,noi_han,ten_noi,VUNG
KEO=json.load(open(sys.argv[1] if len(sys.argv)>1 else T/'keo.json'))
VN=datetime.timezone(datetime.timedelta(hours=7))
class Doan:
    def __init__(s,k): s.k=k; s.toks=[]; s.neo={}; s.van=[]
    def the(s,t): s.van.append(f'[{t}]'); return s
    def noi(s,txt,dau=None,cuoi=None,sau=''):   # txt nhieu tu; dau/cuoi = ten moc gan cho tu DAU/CUOI; sau = ky tu gan sau tu cuoi ('…')
        w=txt.split(); i0=len(s.toks)
        if dau: s.neo[dau]=i0
        if cuoi: s.neo[cuoi]=i0+len(w)-1
        if sau: w[-1]+=sau
        s.toks+=w; s.van.append(' '.join(w)); return s
v=KEO['vung']; A,B,C=[VUNG[x['ma']][1] for x in v[:3]]
ten=ten_noi(KEO['game']['ten']); giam=so_chu(KEO['game']['giam']).upper()
tt,cum=noi_goc(KEO['goc_vnd'])
chB=noi_chenh(v[1]['vnd']-v[0]['vnd']); chC=noi_chenh(v[2]['vnd']-v[0]['vnd'])
het=datetime.datetime.fromtimestamp(int(KEO['han']['endTime'])/1000,VN)
han=noi_han(het,datetime.date.fromisoformat(KEO['ngay_dang']))
DS=[Doan('mo').the('excited').noi('Ê anh').noi('em!!','em').noi(ten,'ten').noi('đang').noi('giảm','giam').noi(giam).noi('phần trăm trên').noi('PS','ps').noi('Store').noi(A,'vung').noi('nè!'),
    Doan('gia').the('gasps').noi('Từ '+tt).noi(cum,'g1','g2',sau='…').the('whispers').noi('giờ','gio').noi('còn có…').the('excited').noi(nghin(KEO['con_vnd'])+' thôi!','gia','thoi'),
    Doan('hoi').the('curious').noi('Ủa mà').noi('khoan…','khoan').noi('mua','mua').noi('store','store').noi(B,'b').noi('hay','hay').noi(C,'c').noi('có','co').noi('rẻ hơn').noi('không','khongq').noi('ta?'),
    Doan('dap').the('laughs').noi('Không','khong').noi('nha!').noi('Quy','quy').noi('ra tiền Việt,').noi(A,'a2').noi('vẫn').noi('rẻ','re1').noi('hơn').noi(B,'b2').noi(chB+',','chb').noi('rẻ','re2').noi('hơn').noi(C,'c2').noi('tới').noi(chC,'chc').noi('lận.'),
    Doan('han').the('serious').noi('Nhưng mà').noi('nhanh','nhanh').noi('tay','tay').noi('nha,','nha').noi('hết','het').noi('giảm','giam2').noi('trước','truoc').noi(han+'.'),
    Doan('ket').the('excited').noi('Tra','tra').noi('giá','gia').noi('mọi','moi').noi('game','game').noi('ở').noi('Săn','san').noi('Game').noi('chấm','cham1').noi('com').noi('chấm').noi('vi','vi').noi('en!','en')]
loi=' '.join(' '.join(d.van) for d in DS)
(T/'loi.txt').write_text(loi,encoding='utf-8')
json.dump(dict(doan=[dict(k=d.k,loi=' '.join(d.toks),neo=d.neo) for d in DS]),open(T/'kich-ban.json','w'),ensure_ascii=False,indent=1)
print(loi); print(len(loi),'ky tu;',sum(len(d.toks) for d in DS),'tu')
