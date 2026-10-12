# Test D3 doi thiet ke 11/10/2026 (Sol #10): noi dung nghe tren GIONG SACH + phep "giong trong video = giong da kiem" + tu phien ban lech chinh ta <= 1 ky tu.
#   uv run --frozen python -m pytest cong-cu/tests/test_d3_giong_sach.py -q       (khong mang, khong Whisper, khong ffmpeg; tin hieu tong hop)
import pathlib,re,sys,tempfile,unittest
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'cong-cu'))
import lien_ket_giong as LK
import nghe_so as NS
KHUON=('top5','keo-thom','tin-nhanh')
SR=16000

def giong_gia(seed,giay=24.0):
    """'Giong noi' tong hop: chuoi am tiet (nhieu bang rong) co do to/do dai ngau nhien + khoang nghi — duong bao nang luong nhu loi noi that."""
    r=np.random.default_rng(seed); out=[]; t=0.0
    while t<giay:
        d=r.uniform(0.10,0.32); a=r.uniform(0.15,0.8); n=int(d*SR)
        env=np.hanning(n)**0.7*a; out.append(r.standard_normal(n)*env*0.5); t+=d
        p=r.uniform(0.02,0.22); out.append(np.zeros(int(p*SR))); t+=p
    return np.concatenate(out).astype(np.float32)
def nhac(seed,n):
    r=np.random.default_rng(seed); k=np.arange(n)/SR
    return (0.06*r.standard_normal(n)+0.1*np.sin(2*np.pi*220*k)*(0.6+0.4*np.sin(2*np.pi*0.5*k))+0.05*np.sin(2*np.pi*660*k)).astype(np.float32)
def ghep(g,tre_s=0.0,ben=0.4,seed=99,them=1.5):
    """Video = giong (tre `tre_s`) + nhac ben `ben` + gain khac (loudnorm), dai hon giong `them` giay (outro)."""
    n=len(g)+int(them*SR); x=np.zeros(n,np.float32); o=int(tre_s*SR); x[o:o+len(g)]+=g[:n-o]
    return (x+ben*nhac(seed,n))*1.7

class TenGiongSach(unittest.TestCase):
    def test_chon_dung_tep_giong_sach(self):
        with tempfile.TemporaryDirectory() as d:
            d=pathlib.Path(d); (d/'giong.mp3').write_bytes(b'x'); (d/'khac.mp3').write_bytes(b'y')
            self.assertEqual(LK.ten_giong_sach(d),d/'giong.mp3')
    def test_thieu_giong_sach_thi_loi_khong_am_tham(self):
        with tempfile.TemporaryDirectory() as d: self.assertRaises(FileNotFoundError,LK.ten_giong_sach,d)
    def test_ba_kiem_tat_ca_nghe_noi_dung_tren_giong_sach(self):
        # cac khuon PHAI: lay tep bang ten_giong_sach, nghe_doan tren G16 (giong sach), goi lien_ket(G16,X16) va ghi phep; KHONG con nghe_doan tren X16 (ban ghep)
        for k in KHUON:
            src=(ROOT/'khuon'/k/'kiem'/'kiem-tat-ca.py').read_text(encoding='utf-8')
            self.assertIn('GS=LK.ten_giong_sach(V)',src,k); self.assertIn('G16=doc(GS,16000)',src,k)
            self.assertEqual(len(re.findall(r'nghe_doan\(G16,cs,nghe_kiem,',src)),1,k); self.assertIn('ten_nghe_kiem()',src,k); self.assertNotIn('nghe_doan(X16',src,k)
            self.assertIn('LK.lien_ket(G16,X16,cua_so=LK.cua_so_moc_chu(moc))',src,k); self.assertIn('LK.dat_lien_ket(LK_KQ)',src,k)
            self.assertIn('lien_ket_giong=LK_KQ',src,k)                     # bang chung vao kiem-<nt>.json
            self.assertNotIn("wm.transcribe(X16",src,k)                      # tin-nhanh: nghe lai doan ten tieng Anh cung phai tren giong sach
    def test_keo_thom_ten_game_5b_nghe_tren_giong_sach(self):
        src=(ROOT/'khuon'/'keo-thom'/'kiem'/'kiem-tat-ca.py').read_text(encoding='utf-8')
        self.assertIn("TVS.append((c[0]['s'],c[-1]['e'],tg))",src); self.assertNotIn("TVS.append((c[0]['s'],c[-1]['e'],tv))",src)

class LienKetGiong(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.g=giong_gia(1); cls.khac=giong_gia(2)
    CS=[(i*2.0,i*2.0+2.0) for i in range(12)]   # cua so 2 s phu 24 s giong tong hop (thay cho moc-chu)
    def lk(self,g,x): return LK.lien_ket(g,x,cua_so=self.CS)
    def test_giong_dung_cong_nhac_dat(self):
        kq=self.lk(self.g,ghep(self.g)); ok,_=LK.dat_lien_ket(kq)
        self.assertTrue(ok,kq); self.assertGreater(kq['r'],0.95); self.assertEqual(kq['lech_ms'],0)
    def test_giong_dung_nhac_to_hon_van_dat(self):
        kq=self.lk(self.g,ghep(self.g,ben=0.8)); self.assertTrue(LK.dat_lien_ket(kq)[0],kq)
    def test_giong_dung_lech_100ms_dat_va_bao_dung_do_lech(self):
        kq=self.lk(self.g,ghep(self.g,tre_s=0.1)); self.assertTrue(LK.dat_lien_ket(kq)[0],kq); self.assertEqual(kq['lech_ms'],100)
    def test_giong_khac_cong_cung_nhac_truot(self):
        kq=self.lk(self.g,ghep(self.khac)); ok,_=LK.dat_lien_ket(kq)
        self.assertFalse(ok,kq); self.assertLess(kq['r'],0.6)
    def test_giong_dung_nhung_lech_1_giay_truot(self):            # ngoai +-300 ms
        kq=self.lk(self.g,ghep(self.g,tre_s=1.0)); self.assertFalse(LK.dat_lien_ket(kq)[0],kq)
    def test_chi_nhac_khong_giong_truot(self):
        self.assertFalse(LK.dat_lien_ket(self.lk(self.g,ghep(np.zeros(len(self.g),np.float32))))[0])
    def test_thay_mot_phan_giong_truot_nho_nguong_doan(self):     # 1/3 cuoi bai la giong khac -> doan thap nhat rot, du toan bai con cao
        x=self.g.copy(); c=len(x)*2//3; kh=np.pad(self.khac,(0,max(0,len(x)-len(self.khac))))[:len(x)]; x[c:]=kh[c:]
        kq=self.lk(self.g,ghep(x)); self.assertFalse(LK.dat_lien_ket(kq)[0],kq); self.assertLess(kq['r_doan_min'],LK.NGUONG_TQ_DOAN)
    def test_nguong_nam_giua_cap_dung_va_cap_sai_do_that(self):  # so do that 11/10: dung >= 0,96 (doan >= 0,93) ; sai cao nhat 0,87 (doan 0,70)
        self.assertTrue(0.87<LK.NGUONG_TQ<0.96); self.assertTrue(0.70<LK.NGUONG_TQ_DOAN<0.93)
    # --- Sol soi cuoi 11/10: RMS khong chung minh cung giong; cat / them giong; thay doan ngan
    def test_cat_con_nua_giong_truot_vi_phu(self):                # TRUOC: r=1 du chi con nua bai
        x=self.g.copy(); x[len(x)//2:]=0; kq=self.lk(self.g,ghep(x)); ok,_=LK.dat_lien_ket(kq)
        self.assertFalse(ok,kq); self.assertLess(kq['phu'],LK.NGUONG_PHU)
    def test_noi_them_giong_khac_sau_bai_truot(self):             # TRUOC: chi xet phan giao nen van dat
        x=np.concatenate([self.g,self.khac[:int(3*SR)]]); kq=self.lk(self.g,ghep(x,them=0.0)); ok,_=LK.dat_lien_ket(kq)
        self.assertFalse(ok,kq); self.assertGreater(kq['ngoai_s'],LK.NGUONG_NGOAI_S)
    def test_thay_200ms_trong_mot_cua_so_truot_theo_cua_so(self):  # TRUOC: r toan bai ~0,99 va 3 phan van dat
        x=self.g.copy(); a=int(9.2*SR); b=a+int(0.4*SR); x[a:b]=self.khac[a:b]   # thay 0,4 s bang giong khac, cua so 1 s (nhu cum ten/gia/han that)
        kq=LK.lien_ket(self.g,ghep(x),cua_so=[(i*1.0,i*1.0+1.0) for i in range(24)]); ok,_=LK.dat_lien_ket(kq)
        self.assertFalse(ok,kq); self.assertLess(kq['r_cua_so_min'],LK.NGUONG_TQ_CUA_SO); self.assertGreater(kq['r'],LK.NGUONG_TQ)
    def test_thieu_cua_so_khong_dat(self):                        # cua so moc-chu BAT BUOC
        kq=LK.lien_ket(self.g,ghep(self.g)); self.assertFalse(LK.dat_lien_ket(kq)[0],kq)
    def test_cua_so_moc_chu_phu_loi_noi_va_khong_vuot_doan(self):
        moc=[{'w':'a','s':0.0,'e':0.5,'doan':'x'},{'w':'b','s':0.55,'e':1.2,'doan':'x'},{'w':'c','s':1.25,'e':2.0,'doan':'x'},{'w':'d','s':2.1,'e':3.9,'doan':'x'},{'w':'e','s':4.0,'e':4.5,'doan':'y'}]
        cs=LK.cua_so_moc_chu(moc); self.assertEqual(cs[0][0],0.0); self.assertEqual(cs[-1],(4.0,4.5)); self.assertTrue(all(e-s<=4.0 for s,e in cs))
    def test_tin_hieu_qua_ngan_khong_dat(self):
        kq=self.lk(self.g[:SR//4],self.g[:SR//4]); self.assertFalse(LK.dat_lien_ket(kq)[0])

class TuPhienBanLechChinhTa(unittest.TestCase):
    def test_delux_bang_deluxe(self):
        ok,ly=NS.so_phan_biet('Returnal Digital Deluxe Edition','Anm Returnal Digital Delux Edition'); self.assertTrue(ok,ly)
        self.assertEqual(NS.tu_phien_ban('delux'),'deluxe'); self.assertEqual(NS.tu_phien_ban('deluxe'),'deluxe')
    def test_ca_loi_ca_nghe_deu_chap_nhan(self):
        self.assertEqual(NS.so_ten('Returnal Digital Deluxe Edition','Returnal Digital Delux Edition')[0],True)
    def test_lech_2_ky_tu_hoac_tu_ngan_khong_chap_nhan(self):
        self.assertIsNone(NS.tu_phien_ban('delx')); self.assertIsNone(NS.tu_phien_ban('lux')); self.assertIsNone(NS.tu_phien_ban('comple'))
        self.assertFalse(NS.so_phan_biet('X Goty','X Got')[0])           # 'goty' < 5 ky tu: chinh xac
    def test_thieu_hoac_thua_phien_ban_van_truot(self):
        self.assertFalse(NS.so_phan_biet('Resident Evil 4 Deluxe','Resident Evil 4')[0]); self.assertFalse(NS.so_phan_biet('Resident Evil 4','Resident Evil 4 Delux')[0])
    def test_so_phan_van_khop_tuyet_doi(self):
        self.assertFalse(NS.so_phan_biet('Resident Evil 4','Resident Evil 5')[0]); self.assertFalse(NS.so_ten('Resident Evil 4','Resident Evil 5')[0])
        self.assertTrue(NS.so_phan_biet('Resident Evil 4','Resident Evil bốn')[0]); self.assertFalse(NS.so_phan_biet('Mortal Kombat XI','Mortal Kombat X')[0])
    def test_lech_chinh_ta_khong_ap_dung_cho_so_la_ma_hay_chu_thuong(self):
        self.assertFalse(NS.so_phan_biet('Final Fantasy VII','Final Fantasy VIII')[0])
    def test_remaster_remastered(self):
        self.assertEqual(NS.tu_phien_ban('remaster'),'remastered'); self.assertTrue(NS.so_phan_biet('Game Remastered','Game Remaster')[0])

class BiDanhThang(unittest.TestCase):
    def test_khang_chi_trong_mau_ngay_so_thang_so(self):
        self.assertEqual(NS.doc_ngay('hết giảm ngày 22 kháng 10'),[(22,10)]); self.assertEqual(NS.doc_ngay('ngày hai mươi hai kháng mười'),[(22,10)])
        self.assertEqual(NS.doc_han('hết giảm trước 2 giờ chiều ngày 22 kháng 10')[0]['ngay'],(22,10))
        self.assertEqual(NS.doc_ngay('kháng 10'),[]); self.assertEqual(NS.doc_ngay('ngày kháng 10'),[])
    def test_van_so_gia_tri(self):
        self.assertNotIn((23,10),NS.doc_ngay('ngày 22 kháng 10')); self.assertNotIn((22,11),NS.doc_ngay('ngày 22 kháng 10'))

class BiDanhNgayNay(unittest.TestCase):   # 12/10 run 38210460267: turbo nghe 'đêm ngày 21 tháng 10' thanh 'đêm này 21 tháng 10'
    KY=dict(gio24=22,buoi='đêm',ngay=(21,10))
    def test_nay_truoc_so_thang_so_la_ngay(self):
        self.assertEqual(NS.doc_han('Nhưng mà nhanh tay nha, hết giảm trước 10 giờ đêm này 21 tháng 10')[0]['ngay'],(21,10))
        self.assertEqual(NS.doi_chieu('hết giảm trước 10 giờ đêm này 21 tháng 10',han=self.KY),[])
    def test_van_truot_khi_sai_ngay_hoac_gio(self):
        self.assertTrue(NS.doi_chieu('hết giảm trước 10 giờ đêm này 22 tháng 10',han=self.KY))
        self.assertTrue(NS.doi_chieu('hết giảm trước 9 giờ đêm này 21 tháng 10',han=self.KY))
    def test_nay_mai_khong_nhan_va_nay_khong_doi(self):
        self.assertIsNone(NS.doc_han('hết giảm trước 10 giờ đêm này mai')[0]['ngay'])
        self.assertEqual(NS.doc_han('hết giảm trước 10 giờ đêm nay')[0]['ngay'],'nay')

class TenHaiBo(unittest.TestCase):        # Opus 11/10: TEN dat neu small HOAC turbo dat 0,40 + token phan biet khop trong chinh ban do; tien/%/vung chi turbo
    M='Returnal Digital Deluxe Edition'
    def test_turbo_sai_small_dat_thi_dat(self):
        ok,bo,ly=NS.ten_hai_bo(self.M,{'turbo':'Ê anh em Rê tơ nan đi chi tồ','small':'Returnal Digital Deluxe Edition đang giảm'}); self.assertTrue(ok,ly); self.assertEqual(bo,'small')
    def test_turbo_dat_thi_dat_boi_turbo(self):
        ok,bo,_=NS.ten_hai_bo(self.M,{'turbo':'Returnal Digital Deluxe Edition','small':'xxx'}); self.assertTrue(ok); self.assertEqual(bo,'turbo')
    def test_ca_hai_truot_thi_truot(self):
        ok,bo,ly=NS.ten_hai_bo(self.M,{'turbo':'Tôi đi ăn cơm','small':'Hôm nay trời đẹp quá'}); self.assertFalse(ok); self.assertIsNone(bo); self.assertIn('turbo',ly); self.assertIn('small',ly)
    def test_small_dat_nguong_nhung_sai_so_phan_thi_truot(self):
        ok,bo,ly=NS.ten_hai_bo('Resident Evil 4',{'turbo':'xxx yyy','small':'Resident Evil 5'}); self.assertFalse(ok,ly)
        ok,bo,ly=NS.ten_hai_bo('Resident Evil 4',{'turbo':'Resident Evil','small':'Resident Evil 4 Deluxe'}); self.assertFalse(ok,ly)
    def test_so_phan_phai_khop_trong_chinh_ban_dat(self):             # turbo dung chu nhung thieu so, small dung so nhung sai chu -> khong ghep hai ban
        ok,_,_=NS.ten_hai_bo('Resident Evil 4',{'turbo':'Resident Evil','small':'Hôm qua tôi mua 4 cái bánh'}); self.assertFalse(ok)
    def test_hang_cat_tien_to(self):
        self.assertTrue(NS.ten_hai_bo('Outlast',{'turbo':'Hạng 4 Outlast giảm'},hang=True)[0])
    def test_doi_chieu_kiem_ten_false_van_che_so_trong_ten_va_khong_cham_ten(self):
        l=NS.doi_chieu('Mortal Kombat 11 giảm 90% chỉ 136.000',ten=['Mortal Kombat mười một'],tien=[136000],kiem_ten=False); self.assertEqual(l,[])
        self.assertEqual(NS.doi_chieu('xxx 136.000',ten=['Mortal Kombat mười một'],tien=[136000],kiem_ten=False),[])
        self.assertTrue(NS.doi_chieu('xxx 136.000',ten=['Mortal Kombat mười một'],tien=[136000]))
    def test_ba_kiem_tat_ca_ghi_bo_nghe_dat_va_tien_chi_turbo(self):
        for k in KHUON:
            src=(ROOT/'khuon'/k/'kiem'/'kiem-tat-ca.py').read_text(encoding='utf-8')
            self.assertIn('ten_dat_boi=TEN_BO',src,k); self.assertRegex(src,r"NS\.nghe_doan\(G16,cs,nghe,",k)          # small chay cho TEN
            self.assertEqual(len(re.findall(r'nghe_doan\(G16,cs,nghe_kiem,',src)),1,k)                                      # tien/%/vung: chi turbo
        for k in ('top5','keo-thom'): self.assertIn('kiem_ten=False',(ROOT/'khuon'/k/'kiem'/'kiem-tat-ca.py').read_text(encoding='utf-8'))

if __name__=='__main__': unittest.main()
