# Test GD B (Top 5 tu dong): ten_rut_gon, lich_su_top5, cong-cu/kiem_do_moi.py, cong-cu/giong.py (luong credit), sau-manifest.py.
#   python3 khuon/top5/test_top5.py        (chi stdlib, khong mang, khong ton credit)
import contextlib,datetime,io,json,os,pathlib,subprocess,sys,tempfile,types,unittest,urllib.error
T=pathlib.Path(__file__).resolve().parent; ROOT=T.parent.parent
sys.path.insert(0,str(T)); sys.path.insert(0,str(ROOT/'cong-cu')); sys.path.insert(0,str(ROOT))
import ten_rut_gon as tr, lich_su_top5 as ls, kiem_do_moi as km, giong as gi

class TenRutGon(unittest.TestCase):
    def test_so_chu(self):
        for n,c in ((0,'không'),(5,'năm'),(15,'mười lăm'),(21,'hai mươi mốt'),(105,'một trăm lẻ năm'),(112,'một trăm mười hai'),(167,'một trăm sáu mươi bảy'),(2026,'hai nghìn không trăm hai mươi sáu'),(1000,'một nghìn')):
            self.assertEqual(tr.so_chu(n),c)
    def test_hien_thi_va_doc_ngoai_le(self):
        self.assertEqual(tr.doc('Mafia: Definitive Edition for PS5®'),'Mafia bản làm lại')
        self.assertEqual(tr.doc('Mortal Kombat 11'),'Mortal Kombat mười một')
        self.assertEqual(tr.doc('Outlast full game'),'Outlast')
        self.assertEqual(tr.hien_thi('NBA 2K27 (Simplified Chinese, English)'),'NBA 2K27')
        self.assertEqual(tr.hien_thi('Marvel’s Spider-Man 2 PS4 & PS5'),"Marvel's Spider-Man 2")
    def test_tu_dong(self):
        self.assertEqual(tr.doc('Resident Evil 4'),'Resident Evil bốn')
        self.assertEqual(tr.doc('The Witcher 3: Wild Hunt – Complete Edition'),'The Witcher ba, Wild Hunt')
        self.assertEqual(tr.doc('Hogwarts Legacy - Deluxe Edition'),'Hogwarts Legacy')
    def test_doc_duoc(self):
        self.assertTrue(tr.doc_duoc('Steelrising')); self.assertTrue(tr.doc_duoc('Resident Evil 4'))
        self.assertFalse(tr.doc_duoc('NBA 2K27')); self.assertFalse(tr.doc_duoc('FINAL FANTASY XVI')); self.assertFalse(tr.doc_duoc('F1 25'))
    def test_vung_va_gia(self):
        self.assertEqual(tr.vung_doc_cua({'vung':'Ấn Độ'}),'Ấn Độ'); self.assertEqual(tr.vung_doc_cua({'vung':'Indonesia'}),'Indo')
        self.assertEqual(tr.vung_doc_cua({'vung':'Vùng lạ'}),'Vùng lạ'); self.assertEqual(tr.nghin_so('167.000đ'),167)

class LichSu(unittest.TestCase):
    def test_da_len_3_ngay(self):
        with tempfile.TemporaryDirectory() as d:
            f=pathlib.Path(d)/'ls.json'; f.write_text(json.dumps({'2026-10-07':['Old Game'],'2026-10-09':['Mafia: Definitive Edition for PS5®'],'2026-10-10':['Mortal Kombat 11']}))
            with unittest.mock.patch.dict(os.environ,{'TOP5_LICH_SU':str(f)}):
                k,_=ls.da_len('2026-10-11',3)
        self.assertIn(ls.ten_dong_game('Mafia III: Definitive Edition'),k)   # Mafia = Mafia III = 1 dong
        self.assertIn(ls.ten_dong_game('Mortal Kombat'),k); self.assertNotIn(ls.ten_dong_game('Old Game'),k)   # 07/10 la 4 ngay truoc -> khong tinh

class KiemDoMoi(unittest.TestCase):
    def dung(self,d,ngay,vung=('SG','HK','IN','ID','US','TH')):
        dl=pathlib.Path(d)/'du-lieu'; dl.mkdir(parents=True,exist_ok=True)
        json.dump({'cap_nhat':ngay,'so_mon_giu_lai':{v:5 for v in ('SG','HK','IN','ID','US','TH')}},open(dl/'bang-gia.json','w'))
        json.dump({'cap_nhat':ngay},open(dl/'trang-game.json','w')); json.dump({'ngay':ngay},open(dl/'gia-the.json','w'))
        for v in vung: json.dump({'so_mon':3,'cap_nhat':ngay},open(dl/f'giam-gia-en-{v}.json','w'))   # moc rieng tung feed (Sol bcd #19)
    def test_moi(self):
        with tempfile.TemporaryDirectory() as d:
            self.dung(d,'2026-10-12'); self.assertEqual(km.kiem(d,'2026-10-12'),(True,[]))
    def test_chua_moi_hom_qua(self):
        with tempfile.TemporaryDirectory() as d:
            self.dung(d,'2026-10-11'); moi,ly=km.kiem(d,'2026-10-12'); self.assertFalse(moi); self.assertEqual(len(ly),9)   # 3 file tong + 6 feed vung
    def test_thieu_an_do(self):
        with tempfile.TemporaryDirectory() as d:
            self.dung(d,'2026-10-12',vung=('SG','HK','ID','US','TH')); moi,ly=km.kiem(d,'2026-10-12'); self.assertFalse(moi); self.assertTrue(any('IN' in x for x in ly))

class CongGia:
    def __init__(self,vuot=False): self.vuot=vuot; self.goi_=[]
    def goi(self,viec,**kw):
        self.goi_.append((viec,kw))
        if viec=='giu_credit': return {'ok':True,'id':None if self.vuot else 7,'vuot_tran':self.vuot}
        return {'ok':True,'so_dong':1}
class ElevenGia:
    def __init__(self,tts=None,da_dung=(100,330)): self.tts=tts; self.dd=list(da_dung); self.goi_=[]
    def goi(self,body,timeout=0):
        self.goi_.append(body['action'])
        if body['action']=='goi': return {'gioi_han':100000,'da_dung':self.dd.pop(0) if len(self.dd)>1 else self.dd[0],'tier':'x'}
        if isinstance(self.tts,Exception): raise self.tts
        return self.tts
def args(loi_file,ra,**kw):
    d=dict(loi=None,loi_file=str(loi_file),voice=gi.VOICE_MAC_DINH,model='eleven_v3',on_dinh=0.0,toc_do=1.0,muoi='',ra=str(ra),du_an='san-game',dang='top5',tran=None,du_phong=10000,cho_vuot=False); d.update(kw)
    return types.SimpleNamespace(**d)
TTS_OK={'ok':True,'bytes':6000,'path':'giong/1791000000000-123456.mp3','nghe_thu':'https://x/y.mp3'}   # dang tra ve that cua doc-giong
class Giong(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.d=pathlib.Path(self.tmp.name); self.loi=self.d/'loi.txt'; self.loi.write_text('Top năm game bán chạy. '*20,encoding='utf-8')
        self.env=unittest.mock.patch.dict(os.environ,{'GIONG_KHO':str(self.d/'kho'),'SUPABASE_ANON_THENAIL':'anon-gia-khong-that-0123456789','SG_CONG_KHOA':'khoa-cong-gia-0123456789'}); self.env.start()
    def tearDown(self): self.env.stop(); self.tmp.cleanup()
    def mp3(self): return unittest.mock.patch.object(gi,'lay_mp3',lambda url,dich,lan=3,**kw:pathlib.Path(dich).write_bytes(b'x'*6000))
    def test_khoa_giong_el_py(self):
        import hashlib; l='xin chao'; self.assertEqual(gi.khoa_kho(l,'v','m',0.0,1.0),hashlib.sha256(json.dumps([l,'v','m',0.0,1.0]).encode()).hexdigest()[:20])
    def test_muoi_doi_khoa(self):
        a=gi.khoa_kho('x','v','m',0.0,1.0); self.assertNotEqual(a,gi.khoa_kho('x','v','m',0.0,1.0,'lan2')); self.assertEqual(a,gi.khoa_kho('x','v','m',0.0,1.0,''))
    def test_thanh_cong_ghi_so_va_kho(self):
        cong=CongGia(); el=ElevenGia(TTS_OK); ra=self.d/'o'/'giong.mp3'
        with self.mp3(): kq=gi.cmd_giong(args(self.loi,ra),cong,el)
        self.assertEqual(kq[0],'goi'); self.assertEqual(kq[1],230.0)   # chenh da_dung 330-100 (<= 3 x uoc) la credit that
        self.assertEqual([c[0] for c in cong.goi_],['tim_credit_khoa','giu_credit','ghi_tep_credit','xong_credit']); self.assertEqual(cong.goi_[1][1]['tran'],20000); self.assertEqual(cong.goi_[3][1]['credit_that'],230.0)
        self.assertTrue(ra.exists())
        # lan 2 cung loi: kho -> 0 credit, khong goi mang/so
        cong2=CongGia(); el2=ElevenGia({'nghe_thu':'x'}); ra2=self.d/'giong2.mp3'
        self.assertEqual(gi.cmd_giong(args(self.loi,ra2),cong2,el2),('kho',0)); self.assertEqual(cong2.goi_,[]); self.assertEqual(el2.goi_,[])
    def test_vuot_tran_tu_choi(self):
        cong=CongGia(vuot=True); el=ElevenGia({'nghe_thu':'x'})
        with self.assertRaises(SystemExit) as c: gi.cmd_giong(args(self.loi,self.d/'g.mp3'),cong,el)
        self.assertIn('vuot tran',str(c.exception)); self.assertEqual(el.goi_,[])   # chua goi ElevenLabs
    def test_tts_5xx_khong_ro_4xx_huy(self):
        for ma,viec in ((502,'khong_ro_credit'),(400,'huy_credit')):
            cong=CongGia(); el=ElevenGia(urllib.error.HTTPError('u',ma,'e',{},None))
            with self.assertRaises(SystemExit): gi.cmd_giong(args(self.loi,self.d/f'g{ma}.mp3'),cong,el)
            self.assertEqual([c[0] for c in cong.goi_],['tim_credit_khoa','giu_credit',viec])
    def test_mat_ket_noi_khong_ro(self):
        cong=CongGia(); el=ElevenGia(TimeoutError('het gio'))
        with self.assertRaises(SystemExit): gi.cmd_giong(args(self.loi,self.d/'g.mp3'),cong,el)
        self.assertEqual([c[0] for c in cong.goi_],['tim_credit_khoa','giu_credit','khong_ro_credit'])
    def test_khong_nghe_thu_huy(self):
        # doc-giong tra HTTP 200 kem {"ok":false,"loi":"tts 4xx: ..."} khi ElevenLabs tu choi => huy; loi khong ro dang => khong_ro (Sol bcd #6)
        for tts,viec in (({'ok':False,'loi':'tts 401: quota_exceeded'},'huy_credit'),({'loi':'quota'},'khong_ro_credit')):
            cong=CongGia(); el=ElevenGia(tts)
            with self.assertRaises(SystemExit): gi.cmd_giong(args(self.loi,self.d/'g.mp3'),cong,el)
            self.assertEqual([c[0] for c in cong.goi_],['tim_credit_khoa','giu_credit',viec])
    def test_du_phong_huy_giu_cho(self):
        cong=CongGia(); el=ElevenGia({'nghe_thu':'x'},da_dung=(99900,))
        with self.assertRaises(SystemExit) as c: gi.cmd_giong(args(self.loi,self.d/'g.mp3'),cong,el)
        self.assertIn('du phong',str(c.exception)); self.assertEqual([c[0] for c in cong.goi_],['tim_credit_khoa','giu_credit','huy_credit']); self.assertNotIn('tts',el.goi_)
    def test_bo_cai_dat_chua_thu_ngan_tu_choi(self):
        cong=CongGia(); el=ElevenGia({'nghe_thu':'x'})
        with self.assertRaises(SystemExit) as c: gi.cmd_giong(args(self.loi,self.d/'g.mp3',on_dinh=0.5),cong,el)
        self.assertIn('cau ngan',str(c.exception)); self.assertEqual([c[0] for c in cong.goi_],['tim_credit_khoa']); self.assertEqual(el.goi_,[])   # chi tra kho rieng (0 credit), khong giu/khong goi ElevenLabs
    def test_khong_in_khoa(self):
        out=io.StringIO(); cong=CongGia(); el=ElevenGia(RuntimeError('loi co anon-gia-khong-that-0123456789 trong thong bao'))
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as c: gi.cmd_giong(args(self.loi,self.d/'g.mp3'),cong,el)
        self.assertNotIn('anon-gia-khong-that',str(c.exception)+out.getvalue()+json.dumps(cong.goi_))

class SauManifest(unittest.TestCase):
    def test_ghi_loi_dang(self):
        with tempfile.TemporaryDirectory() as d:
            m=pathlib.Path(d)/'manifest.json'; m.write_text(json.dumps({'loi_dang':{'tieu_de':'cu'}}))
            ld=T/'loi-dang.json'; co=ld.exists(); cu=ld.read_text(encoding='utf-8') if co else None
            try:
                ld.write_text(json.dumps({'tieu_de':'Top 5','mo_ta':'a','hashtag':['#SănGame','#PlayStation','#PS5','#GiảmGiá'],'link':'https://sangame.com.vn/'},ensure_ascii=False),encoding='utf-8')
                subprocess.run([sys.executable,str(T/'sau-manifest.py'),str(m)],check=True,capture_output=True)
                self.assertEqual(json.load(open(m,encoding='utf-8'))['loi_dang']['tieu_de'],'Top 5')
            finally:
                ld.unlink(missing_ok=True)
                if co: ld.write_text(cu,encoding='utf-8')
import unittest.mock
if __name__=='__main__': unittest.main(verbosity=1)
