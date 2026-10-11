# Test Sol soi cuoi 11/10 (phan may DUNG) - chay khoi D3 THAT cua khuon/tin-nhanh/kiem/kiem-tat-ca.py voi cau Whisper GIA DINH (khong mang, khong Whisper, khong ffmpeg):
#   - ten: diem + token phan biet tinh tren CUNG MOT candidate ("Resident Evil 5" + "Qzx 4 qzx" mong "Resident Evil 4" => TRUOT)
#   - tin DOT SALE: so GIA TRI ngay+thang het sale (mong 21/10, nghe "hai muoi hai thang muoi mot" => TRUOT) + sinh-tin.py luu kiem.han ISO
#   - the gia: truyen `ten` vao doi_chieu (khu so trong ten truoc khi doc tien)
#   uv run --frozen python -m pytest cong-cu/tests/test_soi_cuoi.py -q
import datetime,json,os,pathlib,re,difflib,shutil,subprocess,sys,tempfile,types,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'cong-cu')); sys.path.insert(0,str(ROOT/'khuon'/'tin-nhanh'))
import nghe_so as NS
import so_chu as sc
SRC=(ROOT/'khuon'/'tin-nhanh'/'kiem'/'kiem-tat-ca.py').read_text(encoding='utf-8')
I0=SRC.index("CHU_SO={'khong'"); I1=SRC.index("ghi('D3 giong sach: TEN"); I1=SRC.index('\n',I1)
KHOI=SRC[I0:I1]
def chay_khoi(tin,heard,heard_s=None,en=None):
    """Chay khoi D3 THAT cho `tin` (list the). heard = {'t1': cau turbo}; heard_s = {'t1': cau small}; en = cau Whisper nghe lai RIENG doan ten (moi lan goi transcribe tra mot cau, theo thu tu)."""
    kq=[]; heard_s=heard_s or {}; en=list(en or [])
    class Seg:
        def __init__(s,t): s.text=t
    class Mdl:
        def transcribe(s,*a,**k): return ([Seg(en.pop(0) if en else '')],None)
    moc=[w for i,_ in enumerate(tin,1) for w in (dict(w='x',s=1.0*i,e=1.0*i+0.2,doan=f't{i}'),dict(w='y',s=1.0*i+0.3,e=1.0*i+0.5,doan=f't{i}'),dict(w='z',s=1.0*i+0.6,e=1.0*i+0.8,doan=f't{i}'))]
    NS2=types.SimpleNamespace(**{k:getattr(NS,k) for k in dir(NS) if not k.startswith('__')})
    NS2.nghe_doan=lambda x16,cs,nghe,thu_muc,rev='':(({k:heard[k] for k in cs},dict(pcm_sha256='gia-dinh-000000',dung_lai=0,nghe_moi=len(cs))) if nghe is not None and getattr(nghe,'_la_turbo',True) else ({k:heard_s[k] for k in cs if k in heard_s},dict(pcm_sha256='s',dung_lai=0,nghe_moi=0)))
    tj=dict(tin=tin); m=Mdl()
    cap=[0]
    def nghe_kiem(x): return ''
    nghe_kiem._la_turbo=True
    def nghe_small(x): return ''
    nghe_small._la_turbo=False
    g=dict(json=json,os=os,sys=sys,re=re,difflib=difflib,datetime=datetime,sc=sc,NS=NS2,TJ=tj,moc=moc,G16=__import__('numpy').zeros(16000*30,dtype='float32'),B=pathlib.Path('.'),nghe=nghe_small,nghe_kiem=nghe_kiem,
           wt=lambda:m,wm=m,f_thieu_kiem=lambda i:False,THIEU_KIEM=[],HOI_QUY=False,ghi=lambda t,ok,so,ma:kq.append((t,bool(ok),so)),
           mo_hinh=types.SimpleNamespace(REV_GHIM='r',ten_nghe_kiem=lambda:'turbo'))
    exec(compile(KHOI,'d3-tin-nhanh','exec'),g)
    return kq

def the_do(ten='Resident Evil 4',gia='288.000đ',giam=60,vung='SG'):
    return dict(mau='do',kieu='giam-sau',ten_re=ten,gia=gia,giam=giam,chi_so=dict(ten=0,gia=3),kiem=dict(ten=[ten],so=[],vung=vung))
def the_sale(han='2026-10-21',ten='Player Choice'):
    return dict(mau='vang',kieu='sale',kiem=dict(ten=[ten],so=[],ngay=['hết ngày hai mươi mốt tháng mười'],**({'han':han} if han else {})))

class TenCungMotCandidate(unittest.TestCase):
    def test_hai_candidate_moi_cai_thieu_mot_dieu_kien_thi_truot(self):      # Sol: diem tu 'Resident Evil 5', token '4' tu 'Qzx 4 qzx'
        tin=[dict(mau='xanh',kieu='ps-plus-thang',loi='Tin một: Resident Evil bốn',chi_so=dict(ten=[0]),kiem=dict(ten=['Resident Evil 4'],so=[]))]
        kq=chay_khoi(tin,{'t1':'Resident Evil 5'},{'t1':'Resident Evil 5'},en=['Resident Evil 5','Qzx 4 qzx','Resident Evil 5','Qzx 4 qzx']*2)
        t=[x for x in kq if x[0].startswith('D3 giong sach')][0]; self.assertFalse(t[1],t[2])
    def test_dat_boi_chinh_mot_candidate(self):
        tin=[dict(mau='xanh',kieu='ps-plus-thang',loi='Tin một: Resident Evil bốn',chi_so=dict(ten=[0]),kiem=dict(ten=['Resident Evil 4'],so=[]))]
        kq=chay_khoi(tin,{'t1':'Resident Evil 5'},{'t1':'Resident Evil 5'},en=['Resident Evil 4']*8)
        t=[x for x in kq if x[0].startswith('D3 giong sach')][0]; self.assertTrue(t[1],t[2])

class SaleHanTheoGiaTri(unittest.TestCase):
    def test_nghe_ngay_22_thang_11_mong_21_10_truot(self):
        kq=chay_khoi([the_sale()],{'t1':'Player Choice đang chạy, hết ngày hai mươi hai tháng mười một.'})
        t=[x for x in kq if x[0].startswith('D3 giong sach')][0]; self.assertFalse(t[1],t[2])
    def test_nghe_dung_21_10_dat(self):
        kq=chay_khoi([the_sale()],{'t1':'Player Choice đang chạy, hết ngày hai mươi mốt tháng mười.'})
        t=[x for x in kq if x[0].startswith('D3 giong sach')][0]; self.assertTrue(t[1],t[2])
    def test_the_sale_thieu_kiem_han_truot(self):
        kq=chay_khoi([the_sale(han=None)],{'t1':'Player Choice đang chạy, hết ngày hai mươi mốt tháng mười.'})
        t=[x for x in kq if x[0].startswith('D3 giong sach')][0]; self.assertFalse(t[1],t[2])

class TheGiaKhuSoTrongTen(unittest.TestCase):
    def test_ten_mortal_kombat_11_gia_11k_nghe_12_nghin_truot(self):    # Sol: mong 11k, nghe "Mortal Kombat mười một ... chỉ mười hai nghìn" => phai bao loi tien
        g=the_do(ten='Mortal Kombat 11',gia='11.000đ',giam=60)
        kq=chay_khoi([g],{'t1':'Mortal Kombat mười một giảm sáu mươi phần trăm, chỉ mười hai nghìn ở store Mỹ.'})
        t=[x for x in kq if x[0].startswith('D3 giong sach')][0]; self.assertFalse(t[1],t[2]); self.assertIn('TIEN',t[2])
    def test_ten_co_so_gia_dung_van_dat(self):
        g=the_do(ten='Mortal Kombat 11',gia='11.000đ',giam=60,vung='US')
        kq=chay_khoi([g],{'t1':'Mortal Kombat mười một giảm sáu mươi phần trăm, chỉ mười một nghìn ở store Mỹ.'})
        t=[x for x in kq if x[0].startswith('D3 giong sach')][0]; self.assertTrue(t[1],t[2])

T=ROOT/'khuon'/'tin-nhanh'
class SinhTinSaleLuuHan(unittest.TestCase):
    def chay(self,sale):
        with tempfile.TemporaryDirectory() as d:
            d=pathlib.Path(d)
            for f in ('sinh-tin.py','so_chu.py','ten-ngoai-le.json'): shutil.copy(T/f,d/f)
            (d/'tin-chon.json').write_text(json.dumps(dict(ngay_dang='2026-10-12',ngay_dung='2026-10-11',sha_du_lieu='x',du_lieu_cap_nhat='2026-10-11',tin=[sale]),ensure_ascii=False),encoding='utf-8')
            r=subprocess.run([sys.executable,str(d/'sinh-tin.py'),str(d/'tin-chon.json')],capture_output=True,text=True,cwd=d)
            return r,(json.load(open(d/'tin.json',encoding='utf-8')) if (d/'tin.json').exists() else None)
    def sale(self,**kw):
        return dict(dict(kieu='sale',mau='vang',khoa='sale:Players Choice',loai='ĐỢT SALE',nguon='PS STORE · 12/10',tit="Player's Choice",moc='HẾT 21/10',anh_url=['u'],anh_tep=['tai-san/a.jpg'],bai=None,
                         tieu_de_bai="Player's Choice",nhan_dong='ĐANG GIẢM GIÁ',dong='sangame.com.vn · Cho sale',trailer=[],anh_chup=[]),**kw)
    def test_kiem_han_iso_tu_han_iso(self):
        r,j=self.chay(self.sale(han_iso='2026-10-21')); self.assertEqual(r.returncode,0,r.stdout+r.stderr); self.assertEqual(j['tin'][0]['kiem']['han'],'2026-10-21')
    def test_kiem_han_iso_suy_tu_moc_khi_thieu_han_iso(self):
        r,j=self.chay(self.sale()); self.assertEqual(r.returncode,0,r.stdout+r.stderr); self.assertEqual(j['tin'][0]['kiem']['han'],'2026-10-21')
    def test_sang_nam_sau(self):
        r,j=self.chay(self.sale(moc='HẾT 05/01')); self.assertEqual(r.returncode,0,r.stdout+r.stderr); self.assertEqual(j['tin'][0]['kiem']['han'],'2027-01-05')
if __name__=='__main__': unittest.main()
