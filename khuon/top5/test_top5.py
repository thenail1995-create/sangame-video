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
        for v in vung: json.dump({'so_mon':3,'mon':{'UP1':{'gia':1}},'cap_nhat':ngay},open(dl/f'giam-gia-en-{v}.json','w'))   # moc rieng tung feed (Sol bcd #19)
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
    def may(self,**kw): return unittest.mock.patch.object(gi.giong_may,'doc_may',**kw)   # KHONG chay VieNeu that trong test
    def test_vuot_tran_tu_choi(self):
        cong=CongGia(vuot=True); el=ElevenGia({'nghe_thu':'x'})
        with unittest.mock.patch.dict(os.environ,{'SG_GIONG_MAY':'0'}), self.may() as dm, self.assertRaises(SystemExit) as c: gi.cmd_giong(args(self.loi,self.d/'g.mp3'),cong,el)
        self.assertIn('vuot tran',str(c.exception)); self.assertEqual(el.goi_,[]); dm.assert_not_called()   # chua goi ElevenLabs, khong doc may
    def test_vuot_tran_doc_bang_may(self):
        cong=CongGia(vuot=True); el=ElevenGia({'nghe_thu':'x'})
        with self.may(return_value=('may',0)) as dm: kq=gi.cmd_giong(args(self.loi,self.d/'g.mp3'),cong,el)
        self.assertEqual(kq,('may',0)); self.assertEqual(el.goi_,[]); self.assertEqual(dm.call_args.kwargs['ly_do'],'vuot_tran')
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
            with unittest.mock.patch.dict(os.environ,{'SG_GIONG_MAY':'0'}), self.may() as dm, self.assertRaises(SystemExit): gi.cmd_giong(args(self.loi,self.d/'g.mp3'),cong,el)
            self.assertEqual([c[0] for c in cong.goi_],['tim_credit_khoa','giu_credit',viec]); dm.assert_not_called()
        cong=CongGia(); el=ElevenGia({'ok':False,'loi':'tts 401: quota_exceeded'})   # mac dinh: huy giu cho roi doc may
        with self.may(return_value=('may',0)) as dm: self.assertEqual(gi.cmd_giong(args(self.loi,self.d/'g2.mp3'),cong,el),('may',0))
        self.assertEqual([c[0] for c in cong.goi_],['tim_credit_khoa','giu_credit','huy_credit']); self.assertEqual(dm.call_args.kwargs['ly_do'],'quota_exceeded')
    def test_du_phong_huy_giu_cho(self):
        cong=CongGia(); el=ElevenGia({'nghe_thu':'x'},da_dung=(99900,))
        with unittest.mock.patch.dict(os.environ,{'SG_GIONG_MAY':'0'}), self.may() as dm, self.assertRaises(SystemExit) as c: gi.cmd_giong(args(self.loi,self.d/'g.mp3'),cong,el)
        self.assertIn('du phong',str(c.exception)); self.assertEqual([c[0] for c in cong.goi_],['tim_credit_khoa','giu_credit','huy_credit']); self.assertNotIn('tts',el.goi_); dm.assert_not_called()
        cong=CongGia(); el=ElevenGia({'nghe_thu':'x'},da_dung=(99900,))   # mac dinh: huy giu cho roi doc may
        with self.may(return_value=('may',0)) as dm: self.assertEqual(gi.cmd_giong(args(self.loi,self.d/'g3.mp3'),cong,el),('may',0))
        self.assertEqual([c[0] for c in cong.goi_],['tim_credit_khoa','giu_credit','huy_credit']); self.assertEqual(dm.call_args.kwargs['ly_do'],'du_phong_tai_khoan')
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

class KiemTatCaMaThoat(unittest.TestCase):   # vong 2 #6: kiem-video.py thoat != 0 => phep ky thuat TRUOT (khong chi doc chuoi "0 FAIL")
    def test_kiem_ma_thoat_kiem_video(self):
        for kh in ('top5','keo-thom'):
            s=(pathlib.Path(__file__).resolve().parents[1]/kh/'kiem'/'kiem-tat-ca.py').read_text(encoding='utf-8')
            self.assertIn("rv=subprocess.run([sys.executable,str(SK/'kiem-video.py')",s,kh)
            dong=[l for l in s.split('\n') if "'Ky thuat file (kiem-video.py)'" in l][0]
            self.assertIn('rv.returncode==0',dong,kh)

import datetime as _dt,re as _re,shutil as _sh
import nghe_so as _ns

class CauMoXoay(unittest.TestCase):   # G2 (13/10, Sol #4/#18): `mo` xoay 3 kieu theo toordinal % 3; D3 `mo` ky vong theo kieu (kieu 1 = gia hang 1, khong phai muc)
    TOP=[dict(ten='Mafia',gia='167.000đ',giam=85,vung='Hồng Kông',ma='HK',goc='900.000đ',may='PS5'),dict(ten='Mortal Kombat 11',gia='136.000đ',giam=90,vung='Mỹ',ma='US',goc='900.000đ',may='PS5'),
         dict(ten='Little Nightmares',gia='130.000đ',giam=80,vung='Hồng Kông',ma='HK',goc='900.000đ',may='PS5'),dict(ten='Outlast',gia='133.000đ',giam=75,vung='Indonesia',ma='ID',goc='900.000đ',may='PS5'),
         dict(ten='Steelrising',gia='112.000đ',giam=90,vung='Hồng Kông',ma='HK',goc='900.000đ',may='PS5')]
    def kb(self,ngay_iso,muc=200000,top=None):
        with tempfile.TemporaryDirectory() as d:
            d=pathlib.Path(d)
            for f in ('kich-ban.py','ten_rut_gon.py','ten_ngoai_le.json'): _sh.copy(T/f,d/f)
            cfg=dict(muc=muc,con_lai=85,ngay='11/10'); 
            if ngay_iso: cfg['ngay_iso']=ngay_iso
            (d/'top5.json').write_text(json.dumps(top or self.TOP,ensure_ascii=False),encoding='utf-8'); (d/'cau-hinh.json').write_text(json.dumps(cfg),encoding='utf-8')
            r=subprocess.run([sys.executable,'-I',str(d/'kich-ban.py')],capture_output=True,text=True,cwd=d); self.assertEqual(r.returncode,0,r.stderr[-600:])
            return {x['k']:x['loi'] for x in json.load(open(d/'kich-ban.json',encoding='utf-8'))}
    def ngay_kieu(self,k):      # ngay ISO dau tien >= 2026-10-11 co toordinal % 3 == k
        d=_dt.date(2026,10,11)
        while d.toordinal()%3!=k: d+=_dt.timedelta(days=1)
        return d.isoformat()
    def test_ba_kieu_dung_cong_thuc(self):
        mong={0:'Top năm game bán chạy đang dưới hai trăm nghìn nè anh em!',
              1:'Mafia chỉ một trăm sáu mươi bảy nghìn, đứng đầu top năm hôm nay nè!',
              2:'Có hai trăm nghìn thì mua được game gì? Top năm hôm nay nè!'}
        for k,m in mong.items(): self.assertEqual(self.kb(self.ngay_kieu(k))['mo'],m,k)
    def test_hai_ngay_lien_khac_kieu_nhieu_ngay(self):
        d=_dt.date(2026,10,11); truoc=None; cac=set()
        for i in range(12):
            mo=self.kb((d+_dt.timedelta(days=i)).isoformat())['mo']; cac.add(mo)
            if truoc is not None: self.assertNotEqual(mo,truoc,(i,mo))
            truoc=mo
        self.assertEqual(len(cac),3)
    def test_thieu_ngay_iso_thi_kieu_cu(self):
        self.assertEqual(self.kb(None)['mo'],'Top năm game bán chạy đang dưới hai trăm nghìn nè anh em!')
    def test_ket_va_cac_hang_khong_doi(self):
        a,b=self.kb(self.ngay_kieu(0)),self.kb(self.ngay_kieu(1))
        for k in ('h1','h2','h3','h4','h5','ket'): self.assertEqual(a[k],b[k],k)
        self.assertEqual(a['ket'],'Còn tám mươi lăm game nữa dưới hai trăm nghìn, tra ở Săn Game chấm com chấm vi en!')
    def test_d3_mo_theo_kieu(self):                # chay DUNG khoi D3 `mo` that cua kiem-tat-ca.py (gia hang 1 167.000 != muc 200.000)
        import ten_rut_gon as TR
        src=(T/'kiem'/'kiem-tat-ca.py').read_text(encoding='utf-8'); a=src.index("_KMO="); b=src.index("sai+=[f'{k} {x}' for x in loi]",a)+len("sai+=[f'{k} {x}' for x in loi]")
        def chay(ngay_iso,mo,ket='Còn tám mươi lăm game nữa dưới hai trăm nghìn, tra ở Săn Game'):
            CFG=dict(muc=200000,con_lai=85); 
            if ngay_iso: CFG['ngay_iso']=ngay_iso
            g=dict(datetime=_dt,CFG=CFG,TOP=self.TOP,TR=TR,NS=_ns,heard=dict(mo=mo,ket=ket),heard_s={},TEN_BO={},sai=[]); exec(src[a:b],g); return g['sai']
        k1,k0=self.ngay_kieu(1),self.ngay_kieu(0)
        mo1='Mafia chỉ một trăm sáu mươi bảy nghìn, đứng đầu top năm hôm nay nè'; mo0='Top năm game bán chạy đang dưới hai trăm nghìn nè anh em'
        self.assertEqual(chay(k1,mo1),[]); self.assertEqual(chay(k0,mo0),[])
        self.assertTrue(chay(k1,mo0)); self.assertTrue(chay(k0,mo1))          # doi kieu: kieu 1 phai nghe gia hang 1; kieu 0 phai nghe muc
        self.assertTrue(chay(k1,'Mafia chỉ hai trăm nghìn, đứng đầu top năm hôm nay nè'))          # gia hang 1 sai (nghe muc) -> TRUOT
        self.assertTrue(chay(k1,'Outlast chỉ một trăm sáu mươi bảy nghìn, đứng đầu top năm hôm nay nè'))    # Sol soi diff G2: sai game -> TRUOT
        self.assertTrue(chay(k1,'Chỉ một trăm sáu mươi bảy nghìn, đứng đầu top năm hôm nay nè'))            # bo ten -> TRUOT
        self.assertTrue(chay(k0,mo0,ket='Còn tám mươi lăm game nữa dưới một trăm nghìn'))                     # ket van kiem muc
        self.assertEqual(chay(None,mo0),[])                                                                   # thieu ngay_iso -> kieu 0 (khop kich-ban.py)

def ham_tu_script(duong_dan,ten,ns):
    """Lay NGUYEN van mot ham cap module trong script chay thang (chon-top5.py khong import duoc) roi exec trong khong gian ns -> test dung code that."""
    import ast
    src=pathlib.Path(duong_dan).read_text(encoding='utf-8')
    for n in ast.parse(src).body:
        if isinstance(n,ast.FunctionDef) and n.name==ten:
            exec(compile(ast.Module(body=[n],type_ignores=[]),str(duong_dan),'exec'),ns); return ns[ten]
    raise AssertionError(f'khong thay ham {ten} trong {duong_dan}')

class VungUkraine(unittest.TestCase):      # 15/10: UA = vung THAM KHAO; du lieu co UA khong gay KeyError va KHONG bao gio duoc chon
    def test_bang_vung(self):
        self.assertEqual(tr.LOC_CUA_MA['UA'],'uk-ua'); self.assertEqual(tr.LOC_CUA_MA['IN'],'en-in')
        for ma,loc in tr.LOC_CUA_MA.items():
            if ma!='UA': self.assertEqual(loc,'en-'+ma.lower())
        self.assertNotEqual(tr.LOC_CUA_MA['UA'],'en-ua')
        self.assertEqual(set(tr.VUNG_THAM_KHAO),{'IN','UA'}); self.assertEqual(tr.vung_doc_cua({'vung':'Ukraine'}),'Ukraine')
    def test_bang_tien_te_chon_top5(self):
        import ast
        src=(T/'chon-top5.py').read_text(encoding='utf-8'); tt=None
        for n in ast.parse(src).body:
            if isinstance(n,ast.Assign) and getattr(n.targets[0],'id','')=='TIEN_TE': tt=ast.literal_eval(n.value)
        self.assertEqual(tt['UA'],'UAH'); self.assertEqual(set(tt),set(tr.LOC_CUA_MA))
    def test_ung_vien_khong_chon_ua_du_re_nhat(self):
        ung_vien=ham_tu_script(T/'chon-top5.py','ung_vien',dict(d=dict(hangs=[
            dict(khoa='ua',ma='UA',giam=70,vnd=40000,ten='Rẻ nhất theo tỷ giá ngân hàng'),dict(khoa='in',ma='IN',giam=70,vnd=45000,ten='Ấn'),
            dict(khoa='sg',ma='SG',giam=50,vnd=90000,ten='Mua được'),dict(khoa='th',ma='TH',giam=50,vnd=95000,ten='Thái')]),
            th={k:(i,) for i,k in enumerate(('ua','in','sg','th'))},HANG_DEM=300,tr=tr,t=types.SimpleNamespace(_la_goi_nhieu_game=lambda h:False),gia=lambda h:h['vnd']))
        self.assertEqual([h['ma'] for h in ung_vien(100000)],['SG','TH'])
    def test_xet_chan_ua_truoc_khi_goi_mang(self):
        def mang(*a): raise AssertionError('khong duoc goi mang cho vung tham khao')
        ns=dict(dong_game=lambda t:t,da_len=set(),NB=types.SimpleNamespace(trung=lambda *a:None),tr=tr,d=dict(so=dict(game={'ua':dict(vung=dict(UA=dict(id='P',giam=70,con='UAH 100')))})),lay_trang=mang,GT=None,han_ms=0,TIEN_TE={})
        xet=ham_tu_script(T/'chon-top5.py','xet',ns)
        for ma in ('UA','IN'):
            r,ly=xet(dict(ten='Steelrising',khoa='ua',anh='x',ma=ma,giam=70)); self.assertIsNone(r); self.assertIn('tham khao',ly)
        r,ly=xet(dict(ten='Steelrising',khoa='ua',anh='x',ma='SG',giam=70)); self.assertIsNone(r); self.assertIn('so khong co product cua vung SG',ly)   # vung mua duoc van di tiep qua cua chan

if __name__=='__main__': unittest.main(verbosity=1)
