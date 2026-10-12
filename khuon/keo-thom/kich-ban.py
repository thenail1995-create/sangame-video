# Loi doc Keo thom v9 tu keo.json — so viet bang CHU (may doc so de sai, LOI-SAI N7). Khuon cau co dinh, so/ten/vung/gio lay tu du lieu.
#   python3 kich-ban.py [keo.json]  -> loi.txt (co the cam xuc eleven_v3) + kich-ban.json
# kich-ban.json: {"doan":[{k, loi (khong the), neo:{ten_moc: chi so tu trong doan}}]} — can-chu.py can moc tung chu theo `loi.split()`
# (cung chi so), full.html lay moc theo KHOA doan + ten moc (`moc(k)`), am08.py/nen08.py dung chung. Khong con chi so tuyet doi W(n) (v9).
# 11/10 (Hao: "nen noi 1 chut ve game nay, hay do ra sao, ban deluxe la ban ntn; k can hoi them la mua o store khac co re hon khong"): bo doan hoi-dap `hoi`,
# them doan `gioi` (the loai + dac diem · diem sao · phan them cua ban dac biet) lay 100% tu keo.json.gioi_thieu (chon-keo.py ← trang PS Store); `dap` thanh cau so vung KHONG hoi-dap.
# v10 (12/10, Hao chot 01-quyet-dinh-va-ke-hoach-keo-v10.md): `mo` mo bang CAU TINH HUONG (loi_chu.cau_mo: so gia · so sao · giam sau; khong du dieu kien -> cum cam than cu); `gioi` them CAU KET LUAN cuoi
# (loi_chu.ket_luan); `ket` = «Theo doi Săn Game de khong lo keo nao nha!» (thay cau tra gia). Khoa doan mo/gia/gioi/dap/han/ket giu nguyen. kich-ban.json.doan[mo].kieu = kieu cau mo (D3 doc de biet so nao phai nghe).
import datetime,json,pathlib,sys
T=pathlib.Path(__file__).resolve().parent; sys.path.insert(0,str(T))
import os
from loi_chu import so_chu,nghin,noi_goc,noi_chenh,noi_han,ten_noi,VUNG,ghep_them,cau_mo,ket_luan
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
GT=KEO.get('gioi_thieu')
if not GT: raise SystemExit('keo.json THIEU gioi_thieu (chon-keo.py tu 11/10 ghi the loai / diem / phan them) — khong dung cau doan mo')
v=KEO['vung']; A,B,C=[VUNG[x['ma']][1] for x in v[:3]]
ten=ten_noi(KEO['game']['ten']); giam=so_chu(KEO['game']['giam']).upper()
tt,cum=noi_goc(KEO['goc_vnd'])
chB=noi_chenh(v[1]['vnd']-v[0]['vnd']); chC=noi_chenh(v[2]['vnd']-v[0]['vnd'])
het=datetime.datetime.fromtimestamp(int(KEO['han']['endTime'])/1000,VN)
han=noi_han(het,datetime.date.fromisoformat(KEO['ngay_dang']))
def doan_gioi(gt):
    """Doan GIOI THIEU: 1) 'Game <the loai> <dac diem 1>, <dac diem 2>.'  2) 'Nguoi choi cham <diem> tren nam sao.'  3) 'Ban <X> co them <A> voi <B>, <C> va <D>.'  Thieu du lieu nao -> bo CAU do (khong doan).
    Neo: game, tl (the loai), f1, f2 (dac diem), ng/cham/sc/sc_e (diem), ban, i1..i4 (phan them) — full.html hien tung hang dung luc giong doc toi."""
    d=Doan('gioi'); tl=gt.get('the_loai') or []; dd=gt.get('dac_diem') or []
    if tl or dd:
        d.noi('Game','game')
        if tl: d.noi(' và '.join(x['vi'] for x in tl),'tl')
        for i,x in enumerate(dd): d.noi(x['noi'],f'f{i+1}',sau=',' if i+1<len(dd) else '.')
        if not dd: d.toks[-1]+='.'; d.van[-1]+='.'
    dm=gt.get('diem')
    if dm:
        d.noi('Người','ng').noi('chơi').noi('chấm','cham')
        if dm['lam_tron']==int(dm['lam_tron']): d.noi(dm['noi'],'sc','sc_e').noi('sao.')
        else: d.noi(dm['noi'],'sc','sc_e').noi('trên năm sao.')
    ban=gt.get('ban')
    if ban:
        d.noi('Bản','ban').noi(ban['ten_noi']).noi('có thêm')
        for i,(truoc,cum,dau) in enumerate(ghep_them(ban['them'])):
            if truoc: d.noi(truoc)
            d.noi(cum,f'i{i+1}',sau=dau)
    d.noi(ket_luan(gt.get('diem')))    # v10 B: cau ket luan cuoi doan (khong so, khong khoa neo)
    return d
if not (GT.get('the_loai') or GT.get('dac_diem') or GT.get('diem') or GT.get('ban')): raise SystemExit('gioi_thieu rong — khong dung cau doan mo')
def mo_dau(d):
    """Cau mo doan `mo` (loi_chu.cau_mo, theo ngay + khung env DANG + du lieu keo.json). KHONG chua `đang`. Khoa `em` (full.html giat nhe o do): cum cam than cu giu o tu `em`;
    cau tinh huong v10 khong co tu `em` nen gan khoa `em` cho TU THU HAI (cung nhip ~0,3-0,5 s sau tu dau nhu cum cu)."""
    cm=cau_mo(KEO.get('ngay_dang'),os.environ.get('DANG'),KEO['con_vnd'],KEO['game']['giam'],GT.get('diem'))
    ws=cm['loi'].split(); d.kieu=cm['kieu']
    for i,w in enumerate(ws):
        em=(w.lower().strip('!?.,…')=='em') if cm['kieu']=='cum' else (i==min(1,len(ws)-1))
        d.noi(w,'em' if em else None)
    return d
DS=[mo_dau(Doan('mo').the('excited')).noi(ten,'ten').noi('đang').noi('giảm','giam').noi(giam).noi('phần trăm trên').noi('PS','ps').noi('Store').noi(A,'vung').noi('nè!'),
    Doan('gia').the('gasps').noi('Từ '+tt).noi(cum,'g1','g2',sau='…').the('whispers').noi('giờ','gio').noi('còn có…').the('excited').noi(nghin(KEO['con_vnd'])+' thôi!','gia','thoi'),
    doan_gioi(GT),
    Doan('dap').noi('Store').noi(A,'a2').noi('đang').noi('rẻ','re1').noi('nhất,').noi('rẻ','rb').noi('hơn').noi(B,'b2').noi(chB+',','chb').noi('rẻ','re2').noi('hơn').noi(C,'c2').noi(chC+'.','chc'),
    Doan('han').the('serious').noi('Nhưng mà').noi('nhanh','nhanh').noi('tay','tay').noi('nha,','nha').noi('hết','het').noi('giảm','giam2').noi('trước','truoc').noi(han+'.'),
    Doan('ket').the('excited').noi('Theo','theo').noi('dõi','doi').noi('Săn','san').noi('Game','game').noi('để','de').noi('không').noi('lỡ').noi('kèo').noi('nào').noi('nha!','nha')]
loi=' '.join(' '.join(d.van) for d in DS)
(T/'loi.txt').write_text(loi,encoding='utf-8')
json.dump(dict(doan=[dict(k=d.k,loi=' '.join(d.toks),neo=d.neo,**({'kieu':d.kieu} if hasattr(d,'kieu') else {})) for d in DS]),open(T/'kich-ban.json','w'),ensure_ascii=False,indent=1)
print(loi); print(len(loi),'ky tu;',sum(len(d.toks) for d in DS),'tu')
