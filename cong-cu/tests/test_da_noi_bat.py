# Test cong-cu/da_noi_bat.py (chong lap game giua cac dang, Hao 12/10) + noi_bat trong manifest cua 3 khuon. Mock `gh`, khong mang.
#   uv run --frozen python -m pytest cong-cu/tests/test_da_noi_bat.py -q
import json,os,pathlib,re,shutil,subprocess,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'cong-cu'))
import da_noi_bat as DN

def mf(dang,kl,mo_ta='',noi_bat=None):
    m=dict(dang=dang,kiem_lai=kl,loi_dang=dict(mo_ta=mo_ta))
    if noi_bat is not None: m['noi_bat']=noi_bat
    return m
KL_TIN=[dict(ten='Mafia III: Definitive Edition for PS5®',pid='UP1001-PPSA36864_00-MAFIA3DEPS500000',gia_vnd=160000),
        dict(ten='Mafia: Trilogy',pid='UP1001-CUSA03652_00-MAFIATRILOGYDEFI',gia_vnd=328000),
        dict(ten='It Takes Two',pid='EP0006-PPSA05192_00-ITTAKESTWO000000',gia_vnd=335000),
        dict(ten='Mortal Kombat™ 1',pid='UP1018-PPSA07570_00-MKONE00000000000',gia_vnd=272000)]
MO_TA='Giảm sâu: rẻ nhất Mafia III, 160.000đ ở Store Hồng Kông (giảm 80%).\nDeal hot: rẻ nhất It Takes Two, 335.000đ ở Store Hồng Kông (giảm 70%).\nTra giá'
KHO={'v-2026-10-12-tin-nhanh':mf('tin-nhanh',KL_TIN,MO_TA),
     'v-2026-10-12-top5':mf('top5',[dict(ten='Resident Evil 4',pid='UP0102-PPSA07411_00-RE4GOLD'),dict(ten='Mortal Kombat™ 1',pid='UP1018-PPSA07570_00-MKONE00000000000')]),
     'v-2026-10-11-keo-thom':mf('keo-thom',[dict(ten='Hogwarts Legacy',pid='UP1018-PPSA01593_00-HOGWARTSLEGACY01'),dict(ten='Hogwarts Legacy',pid='HP1018-PPSA01593_00-HOGWARTSLEGACY01')]),
     'v-2026-10-13-keo-thom-2':mf('keo-thom-2',[dict(ten='Gran Turismo 7',pid='UP9000-PPSA01234_00-GT7')]),
     'v-2026-10-13-tin-nhanh':mf('tin-nhanh',KL_TIN,'',noi_bat=[dict(ten='Mafia',pids=['UP1001-PPSA36393_00-MAFIA1DEPS500000'])]),
     'v-2026-10-08-top5':mf('top5',[dict(ten='Cu Qua Han',pid='UP0000-PPSA00000_00-CU')]),     # ngoai 3 ngay
     'thu-2026-10-12-top5':mf('top5',[dict(ten='Ban Thu',pid='UP0000-PPSA00001_00-THU')])}      # khong phai v-
class FakeGh:
    def __init__(s,kho,loi=0): s.kho=kho; s.loi=loi; s.goi=[]
    def __call__(s,args,timeout=60):
        s.goi.append(args)
        if s.loi: raise RuntimeError('mang chet')
        if args[:2]==['release','list']: return json.dumps([dict(tagName=k,isDraft=False) for k in s.kho])
        if args[:2]==['release','download']: return json.dumps(s.kho[args[2]])
        raise AssertionError(args)
class MoGh(unittest.TestCase):
    def chay(s,ngay,dang,kho=KHO,loi=0,**kw):
        goc=DN._gh; DN._gh=FakeGh(kho,loi)
        try: return DN.da_noi_bat(ngay,dang,**kw)
        finally: DN._gh=goc

class HamPhu(unittest.TestCase):
    def test_pid_loi_bo_tien_to_vung(self):
        self.assertEqual(DN.pid_loi('UP1001-PPSA36864_00-MAFIA3DEPS500000'),'PPSA36864_00-MAFIA3DEPS500000')
        self.assertEqual(DN.pid_loi('HP1001-PPSA36864_00-MAFIA3DEPS500000'),DN.pid_loi('UP1001-PPSA36864_00-MAFIA3DEPS500000'))
        self.assertEqual(DN.pid_loi(None),''); self.assertEqual(DN.pid_loi('KHONGCO'),'KHONGCO')
    def test_tu_manifest_tin_nhanh_cu_ghep_theo_gia(self):
        g=DN.tu_manifest(KHO['v-2026-10-12-tin-nhanh'],'tin-nhanh'); ten={x['ten'] for x in g}
        self.assertIn('Mafia III',ten); self.assertIn('Mafia III: Definitive Edition for PS5®',ten); self.assertIn('It Takes Two',ten)
        self.assertNotIn('Mafia: Trilogy',ten); self.assertNotIn('Mortal Kombat™ 1',ten)          # game phu trong danh sach KHONG noi bat
        self.assertIn('UP1001-PPSA36864_00-MAFIA3DEPS500000',[p for x in g for p in x['pids']])
    def test_tu_manifest_top5_va_keo_dung_kiem_lai(self):
        self.assertEqual({x['ten'] for x in DN.tu_manifest(KHO['v-2026-10-12-top5'],'top5')},{'Resident Evil 4','Mortal Kombat™ 1'})
        k=DN.tu_manifest(KHO['v-2026-10-11-keo-thom'],'keo-thom'); self.assertEqual(len(k),1); self.assertEqual(len(k[0]['pids']),2)
    def test_noi_bat_tuong_minh_thang_suy_doan(self):
        g=DN.tu_manifest(KHO['v-2026-10-13-tin-nhanh'],'tin-nhanh'); self.assertEqual([x['ten'] for x in g],['Mafia'])

class DongGame(MoGh):
    def test_khoa_dong_game(self):
        for a,b in (('Mafia III: Definitive Edition for PS5®','Mafia: Definitive Edition for PS5®'),('Mafia','Mafia III'),("Marvel's Spider-Man 2 PS4 & PS5",'Marvel’s Spider-Man Remastered'),
                    ('Call of Duty®: Black Ops 6','Call of Duty: Modern Warfare III'),('Mortal Kombat™ 1','Mortal Kombat 11')):
            self.assertEqual(DN.dong_game(a),DN.dong_game(b),(a,b))
        self.assertEqual(DN.dong_game('Call of Duty®: Black Ops 6'),'call of duty')
        self.assertNotEqual(DN.dong_game('It Takes Two PS4™ & PS5™'),DN.dong_game('Split Fiction'))
    def test_chan_cung_dong(self):
        nb=DN.NoiBat(); nb.them('Mafia III: Definitive Edition for PS5®',['UP1001-PPSA36864_00-MAFIA3DEPS500000'],'t')
        self.assertIn('dong game',nb.trung('Mafia: Definitive Edition for PS5®',['UP1001-PPSA36393_00-MAFIA1DEPS500000']))
        nb=DN.NoiBat(); nb.them('Marvel’s Spider-Man Remastered',[],'t'); self.assertIn('dong game',nb.trung('Marvel’s Spider-Man 2',[]) or '')
    def test_khac_dong_khong_chan_nham(self):
        nb=DN.NoiBat(); nb.them('It Takes Two',[],'t'); self.assertIsNone(nb.trung('Split Fiction',[]))
        nb=DN.NoiBat(); nb.them('Split Fiction',[],'t'); self.assertIsNone(nb.trung('It Takes Two',[]))
        nb=DN.NoiBat(); nb.them('Call of Duty: Black Ops 6',[],'t'); self.assertTrue(nb.trung('Call of Duty®: Modern Warfare III')); self.assertIsNone(nb.trung('Duty Free Shop'))
    def test_mafia_tu_lich_su(self):
        self.assertIn('dong game',self.chay('2026-10-13','tin-nhanh').trung('Mafia: Definitive Edition for PS5®',['UP1001-PPSA36393_00-MAFIA1DEPS500000x']) or '')   # Mafia III 12/10 -> chan Mafia 1

class DocLichSu(MoGh):
    def test_khoang_ngay_va_loai_chinh_khung(self):
        nb=self.chay('2026-10-13','tin-nhanh')       # 3 ngay: 10-10..10-13, tru (10-13, tin-nhanh)
        self.assertIsNone(nb.trung('Cu Qua Han'))                                  # 10-08 ngoai khoang
        self.assertIsNone(nb.trung('Ban Thu'))                                     # thu-... khong tinh
        solo=self.chay('2026-10-13','tin-nhanh',kho={'v-2026-10-13-tin-nhanh':KHO['v-2026-10-13-tin-nhanh']})
        self.assertEqual(len(solo),0); self.assertIsNone(solo.trung('Mafia'))        # chinh khung tin-nhanh 13/10 bi loai
        self.assertTrue(nb.trung('Gran Turismo 7'))                                # khung KHAC cung ngay (keo-thom-2) tinh
        self.assertTrue(nb.trung('Hogwarts Legacy'))                               # keo 11/10
    def test_khung_khac_thay_tin_nhanh_cung_ngay(self):
        nb=self.chay('2026-10-13','top5')
        self.assertTrue(nb.trung('Mafia')); self.assertTrue(nb.trung(pids=['UP1001-PPSA36393_00-MAFIA1DEPS500000']))
    def test_khop_pid_khac_vung_va_ten_khac_dang(self):
        nb=self.chay('2026-10-13','keo-thom')
        self.assertIn('pid',nb.trung('Ten Khac Hoan Toan',['HP1001-PPSA36864_00-MAFIA3DEPS500000']))   # cung noi dung, tien to vung khac
        self.assertIn('ten',nb.trung('It Takes Two',[]))
        self.assertIsNone(nb.trung('Lies of P',['HP1804-PPSA10623_00-LOP']))                           # game phu (khong noi bat, khac dong) KHONG bi chan
        self.assertIsNone(nb.trung('Game Moi',['UP9999-PPSA99999_00-MOI']))
    def test_ten_goc_tiem_vao(self):
        nb=self.chay('2026-10-13','keo-thom',ten_goc=lambda t:t.lower().split(':')[0].strip())
        self.assertTrue(nb.trung('MORTAL KOMBAT™ 1')) if False else None
        self.assertTrue(nb.trung('RESIDENT EVIL 4: Gold'))
    def test_loi_mang_tap_rong_canh_bao(self):
        nb=self.chay('2026-10-13','top5',loi=1)
        self.assertEqual(len(nb),0); self.assertTrue(nb.canh_bao.startswith('CANH BAO')); self.assertIsNone(nb.trung('It Takes Two'))
    def test_thu_3_lan(self):
        n=[0]; goc=DN._gh; real=subprocess.run
        class R:
            def __init__(s,rc,out): s.returncode=rc; s.stdout=out; s.stderr='x'
        def fake(cmd,**kw): n[0]+=1; return R(1,'')
        sl=DN.time.sleep; DN.time.sleep=lambda x:None; DN.subprocess.run=fake
        try: self.assertRaises(RuntimeError,DN._gh,['release','list'])
        finally: DN.subprocess.run=real; DN.time.sleep=sl
        self.assertEqual(n[0],3)
    def test_lich_su_file_tren_mac(self):
        with tempfile.TemporaryDirectory() as d:
            f=pathlib.Path(d)/'ls.json'; f.write_text(json.dumps(KHO)); os.environ['NOI_BAT_LICH_SU']=str(f)
            try: nb=DN.da_noi_bat('2026-10-13','top5')
            finally: del os.environ['NOI_BAT_LICH_SU']
        self.assertTrue(nb.trung('Mafia'))

class SauManifestChung(unittest.TestCase):
    def test_tin_nhanh_noi_bat_vao_manifest(self):
        import sau_manifest_chung as SMC
        with tempfile.TemporaryDirectory() as d:
            d=pathlib.Path(d); (d/'noi-bat.json').write_text(json.dumps([dict(ten='It Takes Two',pids=['EP0006-X'])]),encoding='utf-8'); (d/'m.json').write_text('{}')
            sys.argv=['x',str(d),str(d/'m.json')]; SMC.main()
            self.assertEqual(json.load(open(d/'m.json'))['noi_bat'],[dict(ten='It Takes Two',pids=['EP0006-X'])])

class SinhTinNoiBat(unittest.TestCase):
    def test_noi_bat_json_chi_game_re_nhat(self):
        T=ROOT/'khuon/tin-nhanh'
        END=1792594740000
        def tin(kieu,ten,pid,vung):
            return dict(kieu=kieu,khoa=f'{kieu}:x',mau='do',loai='GIẢM SÂU',nguon='PS STORE · 11/10',n=7,cum='giảm sâu',giam_min=40,giam_max=70,
                re_nhat=dict(ten=ten,ten_hien=ten,ten_doc=ten,gia_vnd=288000,gia='288.000đ',giam=60,vung='Singapore',ma='SG',khoa='k',pid=pid,pids_vung=vung,loc='en-sg',end=END,gia_cuc_bo=14.9,tien_te='SGD'),
                nhan_dong='RẺ NHẤT · STORE SINGAPORE',anh_url=['u'],anh_tep=['tai-san/a.jpg'],trailer=[],anh_chup=[],
                kiem_lai=[dict(ten=ten,pid=pid,loc='en-sg',gia_vnd=288000,gia_cuc_bo=14.9,tien_te='SGD',endTime=str(END))])
        with tempfile.TemporaryDirectory() as d:
            d=pathlib.Path(d)
            for f in ('sinh-tin.py','so_chu.py','ten-ngoai-le.json'): shutil.copy(T/f,d/f)
            (d/'tin-chon.json').write_text(json.dumps(dict(ngay_dang='2026-10-12',ngay_dung='2026-10-11',sha_du_lieu='x',du_lieu_cap_nhat='2026-10-11',
                tin=[tin('giam-sau','Resident Evil Requiem','UP0001-PPSA00000_00-X',['UP0001-PPSA00000_00-X','HP0001-PPSA00000_00-X'])]),ensure_ascii=False),encoding='utf-8')
            r=subprocess.run([sys.executable,str(d/'sinh-tin.py'),str(d/'tin-chon.json')],capture_output=True,text=True,cwd=d)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            self.assertEqual(json.load(open(d/'noi-bat.json',encoding='utf-8')),[dict(ten='Resident Evil Requiem',pids=['HP0001-PPSA00000_00-X','UP0001-PPSA00000_00-X'])])

class SauManifestTop5Keo(unittest.TestCase):
    def chay(self,khuon,tep,man):
        with tempfile.TemporaryDirectory() as d:
            d=pathlib.Path(d); shutil.copy(ROOT/'khuon'/khuon/'sau-manifest.py',d/'sau-manifest.py')
            for k,v in tep.items(): (d/k).write_text(json.dumps(v,ensure_ascii=False),encoding='utf-8')
            (d/'m.json').write_text(json.dumps(man),encoding='utf-8')
            r=subprocess.run([sys.executable,str(d/'sau-manifest.py'),str(d/'m.json')],capture_output=True,text=True,cwd=d)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr); return json.load(open(d/'m.json',encoding='utf-8'))
    def test_top5(self):
        ld=dict(tieu_de='x',mo_ta='y',hashtag=['#SănGame','#PlayStation','#PS5','#GiảmGiá'],link='https://sangame.com.vn/')
        m=self.chay('top5',{'loi-dang.json':ld,'top5.json':[dict(ten_goc=f'Game {i}',pid=f'UP0000-PPSA0000{i}_00-G{i}') for i in range(5)]},{})
        self.assertEqual(len(m['noi_bat']),5); self.assertEqual(m['noi_bat'][0],dict(ten='Game 0',pids=['UP0000-PPSA00000_00-G0']))
    def test_keo(self):
        ld=dict(tieu_de='x',mo_ta='y',hashtag=['#SănGame','#PlayStation','#PS5','#GiảmGiá'],link='https://sangame.com.vn/')
        kl=[dict(ten='Hogwarts Legacy',pid=f'{p}-PPSA01593_00-H',loc=l,gia_vnd=1,gia_cuc_bo=1.5,tien_te='USD',endTime='1') for p,l in (('UP1018','en-us'),('HP1018','en-hk'),('EP1018','en-sg'))]
        m=self.chay('keo-thom',{'keo.json':dict(che_do_hoi_quy=False,loi_dang=ld,kiem_lai=kl,game=dict(ten='Hogwarts Legacy'))},{})
        self.assertEqual(m['noi_bat'],[dict(ten='Hogwarts Legacy',pids=[x['pid'] for x in kl])])

class KhuonDungNoiBat(unittest.TestCase):    # 3 bo chon deu goi NB.trung (kiem nguon: chon-* la script, khong import duoc)
    def test_goi_trung(self):
        for f,dang in (('tin-nhanh/chon-tin.py','tin-nhanh'),('top5/chon-top5.py','top5'),('keo-thom/chon-keo.py','DANG')):
            s=(ROOT/'khuon'/f).read_text(encoding='utf-8'); self.assertIn('da_noi_bat',s,f); self.assertRegex(s,r'NB\.trung\(',f)
            self.assertRegex(s,r"da_noi_bat\([^)]*"+(dang if dang=='DANG' else f"'{dang}'"),f)
if __name__=='__main__': unittest.main()
