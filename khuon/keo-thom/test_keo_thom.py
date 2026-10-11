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

class GioiThieuGame(unittest.TestCase):       # 11/10: cau giới thieu tu bang tu co dinh (loi_chu.gioi_thieu_tu_trang); thieu du lieu -> bo, khong doan
    DAI='Digital Deluxe Edition includes early access to in-game items which are otherwise obtainable via story progression:¹ <br/>- Electropylon Driver weapon.¹<br/>- Hollowseeker weapon.¹<br/>- One Reflex Stimulant.¹<br/>- One Adrenaline Booster.¹<br/>- One Pulsating Mass artefact.¹<br/>- PSN avatars for PS5™.<br/>- Digital soundtrack.<br/><br/>BREAK THE CYCLE<br/><br/>In this roguelike shooter, forced to restart her journey every time she dies. <br/><br/>Choose to go solo, or share your entire journey with another player in online Co-op Mode.²'
    def tt(self,**k):
        b=dict(the_loai=['Shooter'],diem=dict(tb=4.37,so_luot=27172),edition=dict(ten='Digital Deluxe Edition',loai='PREMIUM',tinh_nang=[]),mo_ta_dai=self.DAI,mo_ta_ngan='x'); b.update(k); return b
    def test_returnal_dung_loi_mau_da_duyet(self):
        g=lc.gioi_thieu_tu_trang(self.tt())
        self.assertEqual([x['vi'] for x in g['the_loai']],['bắn súng']); self.assertEqual([x['k'] for x in g['dac_diem']],['roguelike','co_op_online'])
        self.assertEqual((g['diem']['noi'],g['diem']['hien'],g['diem']['luot']),('bốn phẩy bốn','4,4','27K'))
        self.assertEqual((g['ban']['ten_noi'],[m['noi'] for m in g['ban']['them']]),('Deluxe',['hai vũ khí','vật phẩm dùng sớm','ảnh đại diện','nhạc phim']))
        self.assertEqual([m['hien'] for m in g['ban']['them']],['2 vũ khí','Vật phẩm dùng sớm','Ảnh đại diện','Nhạc phim'])
        self.assertEqual(lc.ghep_them(g['ban']['them']),[('','hai vũ khí',''),('với','vật phẩm dùng sớm',','),('','ảnh đại diện',''),('và','nhạc phim','.')])
    def test_it_luot_cham_thi_bo_diem(self):
        self.assertIsNone(lc.gioi_thieu_tu_trang(self.tt(diem=dict(tb=4.9,so_luot=199)))['diem']); self.assertIsNotNone(lc.gioi_thieu_tu_trang(self.tt(diem=dict(tb=4.9,so_luot=200)))['diem'])
        self.assertIsNone(lc.gioi_thieu_tu_trang(self.tt(diem=None))['diem'])
    def test_lam_tron_diem_nua_len_va_so_nguyen(self):
        for tb,r,noi,hien in ((4.37,4.4,'bốn phẩy bốn','4,4'),(4.25,4.3,'bốn phẩy ba','4,3'),(4.95,5.0,'năm','5'),(4.0,4.0,'bốn','4'),(3.04,3.0,'ba','3')):
            self.assertEqual(lc.lam_tron_diem(tb),r,tb); self.assertEqual((lc.noi_diem(r),lc.hien_diem(r)),(noi,hien),tb)
    def test_hien_luot(self):
        self.assertEqual([lc.hien_luot(n) for n in (200,999,1000,1234,9999,10000,27172,1500000)],['200','999','1K','1,2K','10K','10K','27K','1,5M'])
    def test_ban_thuong_khong_co_phan_them(self):
        for ed in (None,dict(ten='Cliff Rush 3D',loai='',tinh_nang=[]),dict(ten='Standard Edition',loai='PREMIUM',tinh_nang=[])):
            self.assertIsNone(lc.gioi_thieu_tu_trang(self.tt(edition=ed))['ban'],ed)
    def test_muc_la_bi_bo_khong_doan(self):
        d='Ultimate Edition includes:<br/>- Mystery Bonus Thing<br/>- Season Pass<br/>- 1000 in-game currency<br/>- Soundtrack<br/><br/>Story'
        g=lc.gioi_thieu_tu_trang(self.tt(edition=dict(ten='Ultimate Edition',loai='PREMIUM',tinh_nang=[]),mo_ta_dai=d))
        self.assertEqual([m['k'] for m in g['ban']['them']],['mo_rong','tien','nhac']); self.assertEqual(g['ban']['ten_noi'],'Ultimate'); self.assertFalse(g['ban']['dung_som'])
    def test_toan_muc_la_thi_khong_co_cau_ban(self):
        g=lc.gioi_thieu_tu_trang(self.tt(mo_ta_dai='Deluxe includes:<br/>- Something odd<br/>- Other odd<br/><br/>x'))
        self.assertIsNone(g['ban'])
    def test_toi_da_4_muc_va_dem_vu_khi(self):
        d='Deluxe Edition includes:<br/>- Two weapons<br/>- Cool outfit<br/>- Season pass<br/>- 500 credits<br/>- Booster<br/>- Soundtrack<br/><br/>x'
        g=lc.gioi_thieu_tu_trang(self.tt(mo_ta_dai=d)); self.assertEqual([m['noi'] for m in g['ban']['them']],['hai vũ khí','trang phục','gói mở rộng','tiền trong game'])
    def test_dac_diem_toi_da_2_theo_thu_tu_va_co_op_local(self):
        mo='A roguelike with open world and online co-op and souls-like combat'; g=lc.gioi_thieu_tu_trang(self.tt(mo_ta_dai=mo,edition=None))
        self.assertEqual([x['k'] for x in g['dac_diem']],['roguelike','the_gioi_mo'])
        g=lc.gioi_thieu_tu_trang(self.tt(mo_ta_dai='Great local co-op fun',edition=None)); self.assertEqual([x['noi'] for x in g['dac_diem']],['chơi chung trên một máy'])
        g=lc.gioi_thieu_tu_trang(self.tt(mo_ta_dai='local co-op and online co-op',edition=None)); self.assertEqual([x['noi'] for x in g['dac_diem']],['chơi chung online được'])
        g=lc.gioi_thieu_tu_trang(self.tt(mo_ta_dai='A story about cooperation',mo_ta_ngan='',edition=None)); self.assertEqual(g['dac_diem'],[])
    def test_the_loai_dich_khong_trung_va_bo_the_loai_la(self):
        g=lc.gioi_thieu_tu_trang(self.tt(the_loai=['Strategy','Strategy','Brain Training','Action','Puzzle'],edition=None)); self.assertEqual([x['vi'] for x in g['the_loai']],['chiến thuật','hành động'])
    def test_khong_co_gi_de_noi_thi_none(self):
        self.assertIsNone(lc.gioi_thieu_tu_trang(dict(the_loai=['Brain Training'],diem=None,edition=None,mo_ta_dai='plain',mo_ta_ngan='')))
    def test_dung_som_gan_vao_vat_pham_hoac_muc_dau(self):
        d='Deluxe includes early access to weapons obtainable via story progression:<br/>- Big weapon<br/>- Avatar<br/><br/>x'
        g=lc.gioi_thieu_tu_trang(self.tt(mo_ta_dai=d)); self.assertEqual([m['noi'] for m in g['ban']['them']],['một vũ khí dùng sớm','ảnh đại diện'])
    def test_du_phong_edition_features_khi_khong_co_dong_gach(self):
        g=lc.gioi_thieu_tu_trang(self.tt(mo_ta_dai='No bullets here.',edition=dict(ten='Gold Edition',loai='PREMIUM',tinh_nang=['Game™','Season Pass.¹','Digital artbook'])))
        self.assertEqual((g['ban']['ten_noi'],[m['noi'] for m in g['ban']['them']]),('Gold',['gói mở rộng','sách tranh']))

    # ---- Sol 11/10 (P1/P2): KHONG CHAC THI BO ----
    def test_p1_co_op_local_khong_thanh_online_va_co_op_mo_ho_bi_bo(self):
        k=lambda mo:[x['k'] for x in lc.gioi_thieu_tu_trang(self.tt(mo_ta_dai=mo,edition=None))['dac_diem']]
        self.assertEqual(k('Enjoy local co-op mode with friends'),['co_op_local']); self.assertEqual(k('couch co-op or split-screen co-op'),['co_op_local'])
        self.assertEqual(k('Play in co-op mode'),[]); self.assertEqual(k('A cooperative adventure'),[]); self.assertEqual(k('local co-op and online co-op'),['co_op_online'])
        self.assertEqual(k('Play local co-op or compete online'),['co_op_local'])
    def test_p1_weapon_skins_la_skin_khong_phai_vu_khi(self):
        g=lc.gioi_thieu_tu_trang(self.tt(mo_ta_dai='Gold Edition includes:<br/>- 2 exclusive Weapon Skins<br/>- Hero Skin<br/><br/>x',edition=dict(ten='Gold Edition',loai='PREMIUM',tinh_nang=[])))
        self.assertEqual([m['noi'] for m in g['ban']['them']],['skin vũ khí','trang phục'])
    def test_p1_bullet_gameplay_khong_phai_phan_them(self):
        for d in ('Game features:<br/>- Collect weapons and coins<br/><br/>x','Gold Edition<br/>- Collect weapons<br/><br/>x','Explore a world.<br/>- Collect weapons and coins<br/><br/>x'):
            self.assertIsNone(lc.gioi_thieu_tu_trang(self.tt(mo_ta_dai=d,edition=dict(ten='Gold Edition',loai='PREMIUM',tinh_nang=[])))['ban'],d)
    def test_p1_dung_som_chi_cho_vat_pham_vu_khi_khi_cau_dan_noi_in_game_items(self):
        ed=dict(ten='Deluxe Edition',loai='PREMIUM',tinh_nang=[])
        g=lc.gioi_thieu_tu_trang(self.tt(edition=ed,mo_ta_dai='Deluxe Edition includes early access to the game, obtainable via story progression unlock:<br/>- Digital soundtrack<br/>- Avatar<br/><br/>x'))
        self.assertEqual([m['noi'] for m in g['ban']['them']],['ảnh đại diện','nhạc phim']); self.assertFalse(g['ban']['dung_som'])    # early access vao GAME, khong co so ngay -> bo
        g=lc.gioi_thieu_tu_trang(self.tt(edition=ed,mo_ta_dai='Deluxe Edition includes 3 days early access to the game:<br/>- Digital soundtrack<br/><br/>x'))
        self.assertEqual([m['noi'] for m in g['ban']['them']],['nhạc phim','chơi sớm ba ngày']); self.assertFalse(any(m.get('dung_som') for m in g['ban']['them']))
        g=lc.gioi_thieu_tu_trang(self.tt(edition=ed,mo_ta_dai='Deluxe Edition includes early access to in-game items obtainable via progression:<br/>- One Booster<br/>- Digital soundtrack<br/><br/>x'))
        self.assertEqual([m['noi'] for m in g['ban']['them']],['vật phẩm dùng sớm','nhạc phim'])
    def test_p2_theme_chi_theo_loai_ghi_ro(self):
        ed=dict(ten='Deluxe Edition',loai='PREMIUM',tinh_nang=[])
        n=lambda b:[m['noi'] for m in (lc.gioi_thieu_tu_trang(self.tt(edition=ed,mo_ta_dai='Deluxe Edition includes:<br/>- '+b+'<br/><br/>x'))['ban'] or {'them':[]})['them']]
        self.assertEqual(n('Main Menu Theme'),['chủ đề menu game']); self.assertEqual(n('PS5 Dynamic Theme'),['hình nền PS5']); self.assertEqual(n('Cool Theme'),[])
    def test_p2_so_luong_vu_khi_chi_khi_ghi_ro(self):
        ed=dict(ten='Deluxe Edition',loai='PREMIUM',tinh_nang=[])
        n=lambda *b:[m['noi'] for m in lc.gioi_thieu_tu_trang(self.tt(edition=ed,mo_ta_dai='Deluxe Edition includes:<br/>'+'<br/>'.join('- '+x for x in b)+'<br/><br/>x'))['ban']['them']]
        self.assertEqual(n('Weapon Pack (5 weapons)'),['năm vũ khí']); self.assertEqual(n('Weapon Pack'),['gói vũ khí']); self.assertEqual(n('Sword and Axe weapons'),['vũ khí'])
        self.assertEqual(n('Big Sword weapon','Small Axe weapon'),['hai vũ khí'])
    def test_p2_edition_theo_ranh_gioi_tu(self):
        self.assertFalse(lc.la_ban_dac_biet(dict(ten='Golden Light',loai='STANDARD',tinh_nang=[]))); self.assertFalse(lc.la_ban_dac_biet(dict(ten='Golden Light',loai='',tinh_nang=[])))
        self.assertTrue(lc.la_ban_dac_biet(dict(ten='Gold Edition',loai='',tinh_nang=[]))); self.assertEqual(lc.ten_ban_noi(dict(ten='Golden Light Edition')),'này')
    def test_p2_full_html_ho_so_vao_theo_neo_cau_dau_va_moc_kiem_sau_khi_on_dinh(self):
        h=(T/'full.html').read_text(encoding='utf-8')
        self.assertIn('TA.g3=TA.dut+.30;',h); self.assertIn('t_ = TA.g3+.12',h)          # thể loại vào tại max(neo 'tl' - 0,04, g3+0,12): không tới sau lời đọc hơn ~0,4 s
        self.assertIn('Math.max(M.gioi.e+.02,gl+.5),TA.ra3-.05',h)                         # D1 lấy mẫu sau chữ cuối + 0,5 s, trước khi thẻ bay đi
if __name__=='__main__': unittest.main()
