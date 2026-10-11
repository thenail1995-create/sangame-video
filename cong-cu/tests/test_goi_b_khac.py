# Test goi B (phan khong phai doc so): B7 OCR fail-closed (#26), B5 kiem_lai moi the co gia (#13), B4 sinh-tin them vung/the_gia (#12).
#   uv run --frozen --with pytest python -m pytest cong-cu/tests -q
import json,os,pathlib,shutil,stat,subprocess,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
for p in ('cong-cu','khuon/top5','khuon/keo-thom','khuon/tin-nhanh'): sys.path.insert(0,str(ROOT/p))
from PIL import Image
import media_hop_le as MH, media_xau as MX, anh_gia as AG, sau_manifest_chung as SMC

class FakeTesseract:
    """PATH chi chua mot 'tesseract' gia: ma thoat + stdout tuy y."""
    def __init__(s,rc,out): s.rc=rc; s.out=out
    def __enter__(s):
        s.d=tempfile.mkdtemp(); f=pathlib.Path(s.d)/'tesseract'; f.write_text(f"#!/bin/sh\nprintf '%s' '{s.out}'\nexit {s.rc}\n"); f.chmod(0o755)
        s.old=os.environ['PATH']; os.environ['PATH']=s.d+':/bin:/usr/bin'; return s
    def __exit__(s,*a): os.environ['PATH']=s.old; shutil.rmtree(s.d,ignore_errors=True)
def anh(d,kieu):
    im=Image.new('RGB',(640,360))
    px=im.load()
    for x in range(640):
        for y in range(360): px[x,y]=((x*255//639),(y*255//359),(x*y)%256) if kieu=='nhieu' else (x*255//639,)*3
    f=pathlib.Path(d)/f'{kieu}.png'; im.save(f); return f

class OcrFailClosed(unittest.TestCase):
    def setUp(s): s.d=tempfile.mkdtemp()
    def tearDown(s): shutil.rmtree(s.d,ignore_errors=True)
    def cac(s,f):
        return [('top5',lambda: MH.la_giu_cho(f)),('keo',lambda: MX.kiem_anh(f)),('tin',lambda: AG.ly_do(f,toi=False))]
    def test_ma_thoat_khac_0_la_khong_kiem_duoc(self):        # Sol #26: ma thoat bi bo qua -> anh bi coi la sach
        f=anh(self.d,'nhieu')
        with FakeTesseract(1,''):
            for ten,h in self.cac(f): self.assertIn('khong kiem duoc OCR',h() or '',ten)
    def test_khong_co_tesseract(self):
        f=anh(self.d,'nhieu'); old=os.environ['PATH']; os.environ['PATH']=self.d      # thu muc rong
        try:
            for ten,h in self.cac(f): self.assertIn('khong kiem duoc OCR',h() or '',ten)
        finally: os.environ['PATH']=old
    def test_gradient_stdout_rong_ma_0_la_hop_le(self):        # dieu phoi vien: tesseract thoat 0 + stdout rong = khong thay chu = DAT
        f=anh(self.d,'gradient')
        with FakeTesseract(0,''):
            for ten,h in self.cac(f): 
                r=h()
                self.assertFalse(r and 'OCR' in r,(ten,r))
    def test_thay_chu_cam_van_bat(self):
        f=anh(self.d,'nhieu')
        with FakeTesseract(0,'PLACEHOLDER SCREENSHOTS'):
            for ten,h in self.cac(f): self.assertTrue(h(),ten)

def tin(n_do=2):
    ts=[]
    for i in range(n_do):
        ts.append(dict(mau='do',ten_re=f'Game{i}',gia=f'{100+i}.000đ',kiem=dict(vung='HK',the_gia=dict(pid=f'UP{i}',loc='en-hk',gia_vnd=(100+i)*1000,gia_cuc_bo=30.5,tien_te='HKD',endTime='1792594740000'))))
    return dict(tin=[dict(mau='xanh')]+ts)
def kl(i): return dict(ten=f'G{i}',pid=f'UP{i}',loc='en-hk',gia_vnd=(100+i)*1000,gia_cuc_bo=30.5,tien_te='HKD',endTime='1792594740000')
class KiemLaiMoiThe(unittest.TestCase):                       # Sol #13: kiem-lai.json=[] van dat
    def test_day_du(self): self.assertEqual(SMC.loi_kiem_lai(tin(),[kl(0),kl(1),dict(kl(9))]),[])
    def test_rong(self): self.assertEqual(len(SMC.loi_kiem_lai(tin(),[])),2)
    def test_thieu_mot_the(self): self.assertEqual(len(SMC.loi_kiem_lai(tin(),[kl(0)])),1)
    def test_trung_ban_ghi(self): self.assertTrue(SMC.loi_kiem_lai(tin(),[kl(0),kl(0),kl(1)]))
    def test_thieu_truong(self):
        x=kl(0); x['endTime']=''; self.assertTrue(SMC.loi_kiem_lai(tin(),[x,kl(1)]))
        x=kl(0); x['gia_cuc_bo']=0; self.assertTrue(SMC.loi_kiem_lai(tin(),[x,kl(1)]))
        x=kl(0); x['tien_te']=''; self.assertTrue(SMC.loi_kiem_lai(tin(),[x,kl(1)]))
        x=kl(0); x['gia_vnd']=999; self.assertTrue(SMC.loi_kiem_lai(tin(),[x,kl(1)]))
    def test_the_khong_gan_pid(self):
        t=tin(1); del t['tin'][1]['kiem']['the_gia']; self.assertTrue(SMC.loi_kiem_lai(t,[kl(0)]))
    def test_khong_the_gia_thi_khong_doi_kiem_lai(self): self.assertEqual(SMC.loi_kiem_lai(tin(0),[]),[])
    def test_main_that_bai_khi_thieu(self):
        with tempfile.TemporaryDirectory() as d:
            d=pathlib.Path(d); (d/'tin.json').write_text(json.dumps(tin()),encoding='utf-8'); (d/'kiem-lai.json').write_text('[]'); (d/'m.json').write_text('{}')
            r=subprocess.run([sys.executable,str(ROOT/'cong-cu'/'sau_manifest_chung.py'),str(d),str(d/'m.json')],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0); self.assertIn('kiem_lai khong du',r.stderr)

class SinhTinVungVaTheGia(unittest.TestCase):                 # Sol #12: kiem cua tin co gia thieu ma vung
    def test_kiem_co_vung_va_the_gia(self):
        with tempfile.TemporaryDirectory() as d:
            d=pathlib.Path(d)
            for f in ('sinh-tin.py','so_chu.py'): shutil.copy(ROOT/'khuon'/'tin-nhanh'/f,d/f)
            x=dict(ten='Mafia: Definitive Edition',ten_hien='Mafia',ten_doc='Mafia',gia_vnd=167000,gia='167.000đ',giam=85,vung='Hồng Kông',ma='HK',khoa='k',pid='UP1001-X',loc='en-hk',end=1792594740000,gia_cuc_bo=47.7,tien_te='HKD')
            C=dict(ngay_dang='2026-10-12',ngay_dung='2026-10-11',sha_du_lieu='x',tin=[dict(kieu='giam-sau',mau='do',loai='GIẢM SÂU',nguon='PS STORE · 10/10',n=8,cum='giảm sâu',giam_min=50,giam_max=85,re_nhat=x,
                  nhan_dong='RẺ NHẤT · STORE HỒNG KÔNG',anh_tep=['tai-san/a.jpg'],khoa='giam-sau:1',kiem_lai=[dict(ten='Mafia',pid='UP1001-X',loc='en-hk',gia_vnd=167000,gia_cuc_bo=47.7,tien_te='HKD',endTime='1792594740000')])])
            (d/'tin-chon.json').write_text(json.dumps(C),encoding='utf-8')
            r=subprocess.run([sys.executable,str(d/'sinh-tin.py'),str(d/'tin-chon.json')],capture_output=True,text=True); self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            t=json.load(open(d/'tin.json',encoding='utf-8'))['tin'][0]['kiem']
            self.assertEqual(t['vung'],'HK'); self.assertEqual(t['the_gia'],dict(pid='UP1001-X',loc='en-hk',gia_vnd=167000,gia_cuc_bo=47.7,tien_te='HKD',endTime='1792594740000'))
if __name__=='__main__': unittest.main()
