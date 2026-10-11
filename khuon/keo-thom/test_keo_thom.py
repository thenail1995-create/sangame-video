# Test GD C (Sol bcd #16 #20): loi_chu.noi_chenh tu 1 trieu; hoi-quy/so-hai-ban.py thoat 1 khi SSIM/cue sai.
import importlib.util,json,pathlib,re,shutil,subprocess,sys,tempfile,unittest
T=pathlib.Path(__file__).resolve().parent; sys.path.insert(0,str(T))
import loi_chu as lc
def doc_so_chu(w):
    """Doc nguoc 0..999 tu chu (toi gian, chi de test): 'ba trăm mười', 'hai mươi mốt', 'một trăm lẻ năm', 'một trăm hai mươi'."""
    tu={'không':0,'một':1,'hai':2,'ba':3,'bốn':4,'năm':5,'sáu':6,'bảy':7,'tám':8,'chín':9,'mốt':1,'tư':4,'lăm':5}; tram=chuc=dv=0; truoc=None
    for t in w.split():
        if t in tu: truoc=tu[t]; dv=tu[t]
        elif t=='trăm': tram=truoc; dv=0
        elif t=='mười': chuc=1; dv=0
        elif t=='mươi': chuc=truoc; dv=0
        elif t=='lẻ': pass
        else: raise ValueError(t)
    return tram*100+chuc*10+dv
def doc_chenh(c):
    """Cau noi_chenh -> VND (dang test): 'năm chục', 'một trăm hai', 'một trăm rưỡi', 'một triệu ba', 'một triệu rưỡi', 'một triệu ba trăm mười nghìn'."""
    w=c.split()
    if 'chục' in w: return doc_so_chu(' '.join(w[:-1]))*10000
    if 'triệu' in w:
        i=w.index('triệu'); tr=doc_so_chu(' '.join(w[:i])); phan=w[i+1:]
        if not phan: return tr*1000000
        if phan[-1]=='nghìn': return tr*1000000+doc_so_chu(' '.join(phan[:-1]))*1000
        return tr*1000000+(500000 if phan==['rưỡi'] else doc_so_chu(' '.join(phan))*100000)
    i=w.index('trăm'); h=doc_so_chu(' '.join(w[:i])); phan=w[i+1:]
    if not phan: return h*100000
    if phan==['rưỡi']: return h*100000+50000
    return h*100000+(10000 if phan==['mười'] else doc_so_chu(' '.join(phan))*10000)
class NoiChenh(unittest.TestCase):
    def test_tu_mot_trieu_phan_du_le_doc_day_du(self):   # code cu: 1.310.000 -> 'một triệu', 1.990.000 -> 'một triệu'
        self.assertEqual(lc.noi_chenh(1310000),'một triệu ba trăm mười nghìn')
        self.assertEqual(lc.noi_chenh(1990000),'một triệu chín trăm chín mươi nghìn')
        self.assertEqual(lc.noi_chenh(1050000),'một triệu năm mươi nghìn')
    def test_phan_du_chan_tram_nghin_van_noi_tat(self):
        for v,c in ((1000000,'một triệu'),(1300000,'một triệu ba'),(1500000,'một triệu rưỡi'),(2000000,'hai triệu'),(2900000,'hai triệu chín')): self.assertEqual(lc.noi_chenh(v),c)
    def test_duoi_mot_trieu_khong_doi(self):
        for v,c in ((50000,'năm chục'),(120000,'một trăm hai'),(150000,'một trăm rưỡi'),(300000,'ba trăm'),(110000,'một trăm mười')): self.assertEqual(lc.noi_chenh(v),c)
    def test_bang_10k_den_3_trieu_doc_nguoc_ra_dung_so(self):
        for v in range(10000,3000001,10000):
            c=lc.noi_chenh(v); self.assertEqual(doc_chenh(c),v,(v,c))
def nap(ten):
    sp=importlib.util.spec_from_file_location(ten,str(T/'hoi-quy'/'so-hai-ban.py')); m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
SH=nap('so_hai_ban_test')
CUE=lambda *x:[{'t':t,'k':k} for t,k in x]
class DanhGia(unittest.TestCase):
    def test_dat(self):
        self.assertEqual(SH.danh_gia([(1,0.99,0.98)],CUE((1.0,'a'),(2.0,'b')),CUE((1.01,'a'),(2.0,'b')))[1],[])
    def test_ssim_thap(self): self.assertTrue(SH.danh_gia([(1,0.10,0.10)],CUE((1,'a')),CUE((1,'a')))[1])
    def test_ssim_sat_nguong(self): self.assertTrue(SH.danh_gia([(1,0.984,1.0)])[1]); self.assertFalse(SH.danh_gia([(1,0.985,1.0)])[1])
    def test_cue_lech_100ms(self): self.assertTrue(SH.danh_gia([(1,0.99,0.99)],CUE((1.1,'a')),CUE((1.0,'a')))[1])
    def test_cue_lech_34ms_van_dat(self): self.assertFalse(SH.danh_gia([(1,0.99,0.99)],CUE((1.034,'a')),CUE((1.0,'a')))[1])
    def test_khac_so_cue(self): self.assertTrue(SH.danh_gia([(1,0.99,0.99)],CUE((1,'a')),CUE((1,'a'),(2,'b')))[1])
    def test_khac_loai_cue(self): self.assertTrue(SH.danh_gia([(1,0.99,0.99)],CUE((1,'a')),CUE((1,'b')))[1])
    def test_khong_moc_thi_truot(self): self.assertTrue(SH.danh_gia([])[1])
@unittest.skipUnless(shutil.which('ffmpeg'),'can ffmpeg')
class ChayThat(unittest.TestCase):
    """Chay CHINH script (python3 so-hai-ban.py) tren video that tao bang ffmpeg: kiem ma thoat."""
    @classmethod
    def setUpClass(cls):
        cls.d=pathlib.Path(tempfile.mkdtemp(prefix='hoiquy-')); 
        mk=lambda ten,src:subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i',src,'-t','3','-r','10','-pix_fmt','yuv420p',str(cls.d/ten)],check=True)
        mk('a.mp4','testsrc2=size=270x480:rate=10'); mk('b.mp4','mandelbrot=size=270x480:rate=10')
    def chay(self,moi,cu,*cue):
        return subprocess.run([sys.executable,str(T/'hoi-quy'/'so-hai-ban.py'),str(self.d/moi),str(self.d/cu),'tiktok','0.5,1.5',*cue],capture_output=True,text=True)
    def cue(self,ten,*x): (self.d/ten).write_text(json.dumps(CUE(*x))); return str(self.d/ten)
    def test_video_giong_nhau_cue_khop_thoat_0(self):
        r=self.chay('a.mp4','a.mp4',self.cue('m.json',(1.0,'x')),self.cue('c.json',(1.01,'x'))); self.assertEqual(r.returncode,0,r.stdout+r.stderr)
    def test_ssim_thap_thoat_1(self):
        r=self.chay('a.mp4','b.mp4'); self.assertEqual(r.returncode,1,r.stdout+r.stderr); self.assertIn('TRUOT',r.stdout)
    def test_cue_lech_100ms_thoat_1(self):
        r=self.chay('a.mp4','a.mp4',self.cue('m2.json',(1.1,'x')),self.cue('c2.json',(1.0,'x'))); self.assertEqual(r.returncode,1,r.stdout+r.stderr)
    def test_khac_so_cue_thoat_1(self):
        r=self.chay('a.mp4','a.mp4',self.cue('m3.json',(1.0,'x')),self.cue('c3.json',(1.0,'x'),(2.0,'y'))); self.assertEqual(r.returncode,1,r.stdout+r.stderr)
class ScriptHoiQuy(unittest.TestCase):
    def test_chay_hoi_quy_dung_set_e_va_khong_nuot_ma_thoat(self):
        s=(T/'hoi-quy'/'chay-hoi-quy.sh').read_text()
        self.assertIn('set -euo pipefail',s); self.assertNotIn('|| RC=1',s)
        for l in s.splitlines():   # buoc so khong duoc bi nuot loi bang '|| true' / '; true'
            if 'so-hai-ban.py' in l or 'so-anh.py' in l: self.assertNotRegex(l,r'\|\|\s*(true|:)')
if __name__=='__main__': unittest.main()
