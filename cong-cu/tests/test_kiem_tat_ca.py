# Test 3 file khuon/{top5,keo-thom,tin-nhanh}/kiem/kiem-tat-ca.py (Sol/Opus vong 2b, CI that 11/10 run 38103818379 + 38104157707):
#   - KHOI DONG: moi `import` noi bo o cap module phai chay duoc voi dung thu tu sys.path (loi that: keo-thom `from loi_chu import ten_noi` chay TRUOC sys.path.insert -> ModuleNotFoundError)
#   - py_compile ca 3 file
#   - luat khuon (% / vung bat buoc) khop kich-ban.py that · khoi B6 cua tin-nhanh khong sap khi tin.json thieu ngay_dang
#   uv run --frozen python -m pytest cong-cu/tests/test_kiem_tat_ca.py -q       (khong mang, khong Whisper, khong ffmpeg)
import re,datetime,json,os,pathlib,py_compile,shutil,subprocess,sys,tempfile,types,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'cong-cu'))
import nghe_so as ns
KHUON=('top5','keo-thom','tin-nhanh')
KIEM=lambda k:ROOT/'khuon'/k/'kiem'/'kiem-tat-ca.py'
# Chay RIENG (python -I: khong thua huong cwd/PYTHONPATH/thu muc script) chuoi lenh o cap module: import + gan B + sys.path.insert, DUNG THU TU nhu file that.
DRIVER=r'''
import ast,sys
p=sys.argv[1]; tree=ast.parse(open(p,encoding='utf-8').read(),p); keep=[]
for n in tree.body:
    if isinstance(n,(ast.Import,ast.ImportFrom)): keep.append(n)
    elif isinstance(n,ast.Assign) and all(isinstance(t,ast.Name) and t.id=='B' for t in n.targets): keep.append(n)
    elif isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='sys.path.insert': keep.append(n)
mod=ast.Module(body=keep,type_ignores=[]); ast.fix_missing_locations(mod)
exec(compile(mod,p,'exec'),{'__file__':p,'__name__':'kiem_khoi_dong'})
print('OK',len(keep))
'''
def chay_khoi_dong(path):
    with tempfile.TemporaryDirectory() as d:
        return subprocess.run([sys.executable,'-I','-c',DRIVER,str(path)],cwd=d,capture_output=True,text=True,timeout=120)

class KhoiDong(unittest.TestCase):
    def test_py_compile(self):
        for k in KHUON:
            with tempfile.TemporaryDirectory() as d: py_compile.compile(str(KIEM(k)),cfile=str(pathlib.Path(d)/'x.pyc'),doraise=True)
    def test_import_noi_bo_chay_duoc_dung_thu_tu(self):
        for k in KHUON:
            r=chay_khoi_dong(KIEM(k)); self.assertEqual(r.returncode,0,f'{k}: {r.stderr[-800:]}'); self.assertIn('OK',r.stdout)
    def test_bat_duoc_loi_thu_tu_sys_path(self):        # doi chung: file import loi_chu TRUOC khi them thu muc khuon -> driver PHAI do
        with tempfile.TemporaryDirectory() as d:
            f=pathlib.Path(d)/'x'/'kiem'; f.mkdir(parents=True); (pathlib.Path(d)/'x'/'loi_chu.py').write_text('X=1\n'); p=f/'kiem-tat-ca.py'
            p.write_text("import sys,pathlib\nB=pathlib.Path(__file__).resolve().parent.parent\nfrom loi_chu import X\nsys.path.insert(0,str(B))\n")
            r=chay_khoi_dong(p); self.assertNotEqual(r.returncode,0); self.assertIn('loi_chu',r.stderr)
            p.write_text("import sys,pathlib\nB=pathlib.Path(__file__).resolve().parent.parent\nsys.path.insert(0,str(B))\nfrom loi_chu import X\n")
            self.assertEqual(chay_khoi_dong(p).returncode,0)
    def test_keo_thom_them_sys_path_truoc_import_noi_bo(self):      # kiem tinh them: khong con import noi bo nao nam TRUOC sys.path.insert(0,str(B)) dau tien
        src=KIEM('keo-thom').read_text(encoding='utf-8'); i=src.index("sys.path.insert(0,str(B))")
        self.assertLess(i,src.index('from loi_chu import ten_noi')); self.assertLess(i,src.index('import media_xau'))

# thong tin trang PS Store cua Returnal Digital Deluxe (11/10, cong-cu/gia_trang.thong_tin_game) -> keo.json.gioi_thieu cho test kich-ban / D3 (khong mang)
TT_RETURNAL=dict(the_loai=['Shooter'],diem=dict(tb=4.37,so_luot=27172),edition=dict(ten='Digital Deluxe Edition',loai='PREMIUM',tinh_nang=[]),mo_ta_ngan='Fight to break the cycle of chaos on a hostile, alien planet.',
    mo_ta_dai='Digital Deluxe Edition includes early access to in-game items which are otherwise obtainable via story progression:¹ <br/>- Electropylon Driver weapon.¹<br/>- Hollowseeker weapon.¹<br/>- One Reflex Stimulant.¹<br/>- One Adrenaline Booster.¹<br/>- One Pulsating Mass artefact.¹<br/>- PSN avatars for PS5™.<br/>- Digital soundtrack.<br/><br/>BREAK THE CYCLE<br/><br/>In this roguelike shooter, both the planet and your equipment change with every cycle. <br/><br/>Choose to go solo, or share your entire journey with another player in online Co-op Mode.²')
def gioi_mau(tt=None):
    sys.path.insert(0,str(ROOT/'khuon'/'keo-thom'))
    try:
        import loi_chu as lc; return lc.gioi_thieu_tu_trang(tt or TT_RETURNAL)
    finally: sys.path.remove(str(ROOT/'khuon'/'keo-thom'))
def chay_kich_ban(thu_muc_khuon,tep,du_lieu):
    with tempfile.TemporaryDirectory() as d:
        d=pathlib.Path(d)
        for t in tep: shutil.copy(ROOT/'khuon'/thu_muc_khuon/t,d/t)
        for t,v in du_lieu.items(): (d/t).write_text(json.dumps(v,ensure_ascii=False),encoding='utf-8')
        r=subprocess.run([sys.executable,'-I',str(d/'kich-ban.py')],cwd=d,capture_output=True,text=True,timeout=60); assert r.returncode==0,r.stderr[-600:]
        return json.load(open(d/'kich-ban.json',encoding='utf-8'))

class LuatKhuonKhopKichBan(unittest.TestCase):       # nghe_so.nhiem_vu_top5 / KEO_* phai khop cau kich-ban.py THAT sinh ra (doi kich-ban.py ma quen doi luat -> do)
    def test_top5(self):
        top=[dict(ten=f'Game {x}',ten_goc=f'Game {x}',gia=f'{100+i*10}.000đ',giam=50+i,vung=v,ma=m,goc='500.000đ',may='PS5') for i,(x,v,m) in enumerate((('Mot','Hồng Kông','HK'),('Hai','Mỹ','US'),('Ba','Indonesia','ID'),('Bon','Indonesia','ID'),('Nam','Singapore','SG')))]
        kb=chay_kich_ban('top5',['kich-ban.py','ten_rut_gon.py','ten_ngoai_le.json'],dict(**{'top5.json':top,'cau-hinh.json':dict(muc=200000,con_lai=85,ngay='11/10',ngay_iso='2026-10-11')}))
        loi={x['k']:x['loi'] for x in kb}
        for r in range(1,6):
            pt,vg=ns.nhiem_vu_top5(r); self.assertEqual(bool(ns.doc_phan_tram(loi[f'h{r}'])),pt,(r,loi[f'h{r}'])); self.assertEqual(bool(ns.doc_vung(loi[f'h{r}'])),vg,(r,loi[f'h{r}']))
    def test_keo_thom(self):
        het=int(datetime.datetime(2026,10,22,13,59,tzinfo=datetime.timezone(datetime.timedelta(hours=7))).timestamp()*1000)
        keo=dict(ngay_dang='2026-10-11',game=dict(ten='Returnal Digital Deluxe Edition',giam=75),goc_vnd=2240000,con_vnd=560000,han=dict(endTime=het,ma='US'),gioi_thieu=gioi_mau(),
                 vung=[dict(ma='US',vnd=560000),dict(ma='HK',vnd=1210000),dict(ma='SG',vnd=1320000)])
        kb=chay_kich_ban('keo-thom',['kich-ban.py','loi_chu.py'],{'keo.json':keo}); loi={x['k']:x['loi'] for x in kb['doan']}
        ma=lambda s:[m for m,_ in ns.doc_vung(s)]
        for k,t in loi.items():
            self.assertEqual(bool(ns.doc_phan_tram(t)),k in ns.KEO_PHAN_TRAM,(k,t))
            mong=[keo['vung']['ABC'.index(x)]['ma'] for x in ns.KEO_VUNG.get(k,())]
            self.assertEqual(sorted(set(ma(t))),sorted(set(mong)),(k,t))
        self.assertEqual(ma(loi['dap']),['US','HK','SG']); self.assertIn('rẻ hơn',loi['dap'])      # chieu so sanh 'A rẻ hơn B' (phep chu_the trong doi_chieu)
        self.assertNotIn('hoi',loi); self.assertNotIn('Không nha',' '.join(loi.values())); self.assertNotIn('rẻ hơn không',' '.join(loi.values()))   # 11/10: bo doan hoi-dap
        self.assertIn('bốn phẩy bốn trên năm sao',loi['gioi']); self.assertEqual(list(loi),['mo','gia','gioi','dap','han','ket'])
    def test_keo_thom_thieu_gioi_thieu_thi_dung(self):
        with tempfile.TemporaryDirectory() as d:
            d=pathlib.Path(d)
            for t in ('kich-ban.py','loi_chu.py'): shutil.copy(ROOT/'khuon'/'keo-thom'/t,d/t)
            het=int(datetime.datetime(2026,10,22,13,59,tzinfo=datetime.timezone(datetime.timedelta(hours=7))).timestamp()*1000)
            (d/'keo.json').write_text(json.dumps(dict(ngay_dang='2026-10-11',game=dict(ten='X',giam=75),goc_vnd=2240000,con_vnd=560000,han=dict(endTime=het,ma='US'),vung=[dict(ma='US',vnd=560000),dict(ma='HK',vnd=1210000),dict(ma='SG',vnd=1320000)])),encoding='utf-8')
            r=subprocess.run([sys.executable,'-I',str(d/'kich-ban.py')],cwd=d,capture_output=True,text=True,timeout=60); self.assertNotEqual(r.returncode,0); self.assertIn('gioi_thieu',r.stderr+r.stdout)

class TinNhanhB6(unittest.TestCase):         # khoi B6 THAT trong kiem-tat-ca.py (tin-nhanh) chay voi tin.json thieu ngay_dang (fixture tin-nhanh-01): khong KeyError
    def chay(self,TJ,env):
        src=KIEM('tin-nhanh').read_text(encoding='utf-8'); a=src.index("HOI_QUY=os.environ.get('HOI_QUY')=='1'\nok_ng"); k="ND=ND_DL or exp\n"; b=src.index(k)+len(k)
        NS=types.SimpleNamespace(kiem_ngay=ns.kiem_ngay,ngay_tu_ddmm=lambda a,t:ns.ngay_tu_ddmm(a,t,datetime.date(2026,10,12)))
        g=dict(os=types.SimpleNamespace(environ=env),datetime=datetime,NS=NS,TJ=TJ); exec(compile(src[a:b],'khoi-b6','exec'),g); return g
    def test_thieu_ngay_dang_thuc_te_truot_co_ly_do(self):
        g=self.chay({'ngay':'10/10','thu':'Thứ Bảy','tin':[]},{'NGAY':'2026-10-10'}); self.assertFalse(g['ok_ng']); self.assertIn('THIEU ngay_dang',g['so_ng']); self.assertEqual(g['ND'],datetime.date(2026,10,10))
        g=self.chay({'ngay':'10/10','thu':'Thứ Bảy'},{}); self.assertFalse(g['ok_ng']); self.assertEqual(g['exp'],datetime.date(2026,10,10))
    def test_hoi_quy_bo_qua_phep_ngay_cac_phep_khac_van_co_ngay(self):
        g=self.chay({'ngay':'10/10','thu':'Thứ Bảy'},{'HOI_QUY':'1'}); self.assertTrue(g['ok_ng']); self.assertIn('hoi quy',g['so_ng']); self.assertEqual(g['exp'],datetime.date(2026,10,10)); self.assertEqual(g['ND'],datetime.date(2026,10,10))
    def test_co_ngay_dang_nhu_cu(self):
        g=self.chay({'ngay_dang':'2026-10-12','ngay':'12/10','thu':'Thứ Hai'},{'NGAY':'2026-10-12'}); self.assertTrue(g['ok_ng']); self.assertEqual(g['ND'],datetime.date(2026,10,12))
        g=self.chay({'ngay_dang':'2026-10-11','ngay':'11/10','thu':'Chủ Nhật'},{'NGAY':'2026-10-12'}); self.assertFalse(g['ok_ng']); self.assertEqual(g['exp'],datetime.date(2026,10,12))
    def test_khong_con_chi_muc_cung_ngay_dang(self):
        src=KIEM('tin-nhanh').read_text(encoding='utf-8'); self.assertNotIn("TJ['ngay_dang']",src.replace("TJ['ngay_dang']!=exp","").replace("{TJ['ngay_dang']}",""))

class TinNhanhThieuKiem(unittest.TestCase):     # fixture tin-nhanh-01 dinh dang CU: tin khong co `kiem` -> hoi quy bo qua co ly do, thuc te TRUOT; khong KeyError
    SRC=KIEM('tin-nhanh').read_text(encoding='utf-8')
    def test_khong_con_truy_cap_kiem_tran_khong_bao_ve(self):
        for m in re.finditer(r"g\['kiem'\]",self.SRC):
            dong=self.SRC[:m.start()].count('\n')+1; dd=self.SRC.split('\n')[:dong]
            j=max(k for k,l in enumerate(dd) if l.startswith("for i,g in enumerate(TJ['tin'],1):")); ctx='\n'.join(dd[j:])     # tu dau vong lap tin den dong dung `kiem`
            self.assertIn('f_thieu_kiem(i)',ctx,f'dong {dong}: g[\'kiem\'] khong duoc bao ve boi f_thieu_kiem')
    def test_khoi_dau_thieu_kiem_nhan_ra_tin_cu(self):
        a=self.SRC.index("THIEU_KIEM=["); b=self.SRC.index("\n",a); g=dict(TJ=dict(tin=[{'mau':'do'},{'kiem':{'ten':['x']}},{'kiem':None}])); exec(self.SRC[a:b],g); self.assertEqual(g['THIEU_KIEM'],[1,3])
    def test_b3_b5_cung_bo_qua_o_hoi_quy_va_truot_o_thuc_te(self):
        self.assertIn("if f_thieu_kiem(r) and HOI_QUY: pass",self.SRC); self.assertIn("_lk=[] if (THIEU_KIEM and HOI_QUY) else SMC.loi_kiem_lai(TJ,_KL)",self.SRC)
    def test_hoi_quy_bo_qua_va_thuc_te_truot_co_ly_do(self):
        self.assertIn("if THIEU_KIEM and not HOI_QUY: sai_ten.append",self.SRC); self.assertIn("if not HOI_QUY: d3_xau.append(f'tin {i}: tin.json thieu `kiem`",self.SRC)
        self.assertIn("BO QUA {len(THIEU_KIEM)} tin thieu `kiem` — fixture dinh dang cu (hoi quy)",self.SRC)

def chay_d3(khuon,a,b,ns_extra,heard,cs_keys):
    """Chay khoi D3 THAT cua kiem-tat-ca.py (giua 2 moc `a`..`b`) voi cau Whisper nghe duoc GIA DINH `heard`. -> list (ten,dat,so_do)."""
    src=KIEM(khuon).read_text(encoding='utf-8'); i=src.index(a); j=src.index(b,i)+(len(b) if b.startswith('NGHE') else 0); kq=[]
    moc=[w for k in cs_keys for w in (dict(w='x',s=1.0,e=1.2,doan=k),dict(w='y',s=1.3,e=1.5,doan=k))]
    sys.path.insert(0,str(ROOT/'khuon'/khuon))
    try:
        with tempfile.TemporaryDirectory() as d:
            NS=types.SimpleNamespace(**{k:getattr(ns,k) for k in dir(ns) if not k.startswith('__')}); NS.nghe_doan=lambda x16,cs,nghe,thu_muc,rev='':({k:heard[k] for k in cs},dict(pcm_sha256='gia-dinh-000000',dung_lai=0,nghe_moi=len(cs)))
            g=dict(json=json,os=os,sys=sys,re=__import__('re'),datetime=datetime,B=pathlib.Path(d),moc=moc,X16=None,G16=None,nghe=None,nghe_kiem=None,NS=NS,mo_hinh=types.SimpleNamespace(REV_GHIM='r',ten_nghe_kiem=lambda:'turbo',in_phien_ban=lambda:''),ghi=lambda t,ok,so,ma:kq.append((t,bool(ok),so)),**ns_extra)
            (pathlib.Path(d)/'kich-ban.json').write_text(json.dumps(ns_extra.pop('_kb',[])),encoding='utf-8')
            exec(compile(src[i:j],'d3-'+khuon,'exec'),g)
    finally: sys.path.remove(str(ROOT/'khuon'/khuon))
    return kq

class D3TheoLuatKhuon(unittest.TestCase):      # Sol vong 2b #11/#12 o CAP SCRIPT: loi bo cau giam gia / vung / dao chieu so sanh -> D3 TRUOT (truoc day phep kiem tu tat)
    def top5(self,heard):
        sys.path.insert(0,str(ROOT/'khuon'/'top5')); import ten_rut_gon as TR
        TOP=[dict(ten='Mafia',ten_doc='Mafia bản làm lại',gia='167.000đ',giam=85,vung='Hồng Kông',ma='HK'),dict(ten='Mortal Kombat 11',ten_doc='Mortal Kombat mười một',gia='136.000đ',giam=90,vung='Mỹ',ma='US'),
             dict(ten='Little Nightmares',ten_doc='Little Nightmares bản đầy đủ',gia='130.000đ',giam=80,vung='Hồng Kông',ma='HK'),dict(ten='Outlast',ten_doc='Outlast',gia='133.000đ',giam=75,vung='Indonesia',ma='ID'),
             dict(ten='Steelrising',ten_doc='Steelrising',gia='112.000đ',giam=90,vung='Hồng Kông',ma='HK')]
        return chay_d3('top5','# 6) D3 (B2)','NGHE_BC=bc',dict(TR=TR,TOP=TOP,CFG=dict(muc=200000,con_lai=85),_kb=[dict(k=k,loi=v) for k,v in heard.items()]),heard,['h1','h2','h3','h4','h5','mo','ket'])[0]
    H5={'h1':'Và hãng 1, Mafia bản nắm lại 167.000 ở Hong Kong.','h2':'Hạn 2, mô tù con bát 11 giảm 90% chỉ 136.000.','h3':'Hẳn 3. Lý đồ NaiMask bán đầy đủ 130.000.','h4':'Hạng 4, ao last giảm 75% 133.000 ở Stò Indo.',
        'h5':'Hạng năm, still rising giảm 90% còn 112.000.','mo':'Top 5 game bán chạy đang dưới 200k nơi nèm.','ket':'Còn 85 game nữa dưới 200k, cha ở sanggame.com.vn'}
    def test_top5_cau_that_dat(self):
        r=self.top5(self.H5); self.assertTrue(r[1],r)
    def test_top5_bo_cau_giam_gia_hoac_vung_thi_truot(self):
        for k,moi,dau in (('h2','Hạn 2, mô tù con bát 11 chỉ 136.000.','PHAN TRAM'),('h5','Hạng năm, still rising còn 112.000.','PHAN TRAM'),('h4','Hạng 4, ao last giảm 75% 133.000.','VUNG'),('h1','Và hãng 1, Mafia bản nắm lại 167.000.','VUNG')):
            r=self.top5(dict(self.H5,**{k:moi})); self.assertFalse(r[1],(k,r)); self.assertIn(dau,r[2],(k,r[2]))
    def keo(self,heard,kieu=None):
        VN=datetime.timezone(datetime.timedelta(hours=7)); het=datetime.datetime(2026,10,22,13,59,tzinfo=VN)
        V=[dict(ma='US',vnd=560000),dict(ma='HK',vnd=1209000),dict(ma='SG',vnd=1319000)]
        KEO=dict(game=dict(ten='Returnal™ Digital Deluxe Edition',giam=75),goc_vnd=2240000,con_vnd=560000,vung=V,gioi_thieu=gioi_mau())
        sys.path.insert(0,str(ROOT/'khuon'/'keo-thom'))
        try: return chay_d3('keo-thom','# 5d) D3 (B2)','# 5c) NEN',dict(KEO=KEO,_G=KEO['game'],_V=V,_h=het,_nd=datetime.date(2026,10,11),_kb=dict(doan=[dict(k=k,loi=v,**({'kieu':kieu} if (k=='mo' and kieu) else {})) for k,v in heard.items()])),heard,['mo','gia','gioi','dap','han'])[0]
        finally: sys.path.remove(str(ROOT/'khuon'/'keo-thom'))
    KL='Hợp với ai thích thể loại này.'      # Keo v10 B: gioi_mau diem 4,4 / 27.172 luot -> nhanh «hop voi ai thich»
    HK={'mo':'Returno Digital Deluxe Edition đang giảm 75% trên PS to Mỹ nè.','gia':'Từ hơn 2 triệu 2 giờ còn có 560.000 thôi','gioi':'Game bắn súng roguelike, chết là chơi lại từ đầu, chơi chung online được, người chơi chấm 4.4 trên 5 sao. Bản Deluxe có thêm 2 vũ khí với vật phẩm dùng sớm, ảnh đại diện và nhạc phim. '+KL,
        'dap':'Store Mỹ đáng rẻ nhất, rẻ hơn Hồng Kông 650, rẻ hơn Sinh 706.','han':'Nhưng mà nhanh tay nha, hết giảm trước 2h chiều ngày 22 tháng 10, cha dám!'}
    def test_keo_cau_that_dat(self):
        r=self.keo(self.HK); self.assertTrue(r[1],r)
    def test_keo_delux_thieu_chu_e_van_dat_nhung_thieu_phien_ban_van_truot(self):      # CI that 11/10: Whisper nghe 'Delux' thay 'Deluxe'
        r=self.keo(dict(self.HK,mo='Returnal Digital Delux Edition đang giảm 75% trên PS to Mỹ nè.')); self.assertTrue(r[1],r)
        r=self.keo(dict(self.HK,mo='Returnal Digital Edition đang giảm 75% trên PS to Mỹ nè.')); self.assertFalse(r[1],r); self.assertIn('thieu phien ban deluxe',r[2])
    def test_keo_bo_cau_phan_tram_vung_hoac_dao_chieu_thi_truot(self):
        for k,moi,dau in (('mo','Returno Digital Deluxe Edition đang giảm trên PS Store nè.','VUNG'),('mo','Returno Digital Deluxe Edition đang giảm trên PS to Mỹ nè.','PHAN TRAM'),
                          ('dap','Store Mỹ đang đắt hơn Hồng Kông 650, rẻ hơn Sinh 706.','CHIEU SO SANH')):
            r=self.keo(dict(self.HK,**{k:moi})); self.assertFalse(r[1],(k,r)); self.assertIn(dau,r[2],(k,r[2]))
    def test_keo_gioi_diem_sai_hoac_thieu_phan_them_thi_truot(self):      # doan `gioi` (11/10): diem sao phai nghe DUNG 4,4 ('4.4' / '4,4' / 'bốn phẩy bốn' deu duoc); thieu phan them bat buoc -> truot
        for ok in ('Game bắn súng roguelike, chơi chung online được, người chơi chấm 4,4 trên 5 sao. Bản Deluxe có thêm hai vũ khí với vật phẩm dùng sớm, ảnh đại diện và nhạc phim. '+self.KL,
                   'Game bắn súng roguelike, chơi chung online được, người chơi chấm bốn phẩy bốn trên năm sao. Bản Delux có thêm 2 vũ khí với vật phẩm dùng sớm, ảnh đại diện và nhạc phim. '+self.KL):
            r=self.keo(dict(self.HK,gioi=ok)); self.assertTrue(r[1],r)
        for k,moi,dau in (('gioi','Game bắn súng roguelike, chơi chung online được, người chơi chấm 4.5 trên 5 sao. Bản Deluxe có thêm 2 vũ khí với vật phẩm dùng sớm, ảnh đại diện và nhạc phim. '+self.KL,'DIEM SAO'),
                          ('gioi','Game bắn súng roguelike, chơi chung online được, người chơi chấm 4.4 trên 5 sao.','TU KHOA phan them'),
                          ('gioi','Game bắn súng, người chơi chấm 4.4 trên 5 sao. Bản Deluxe có thêm 2 vũ khí với vật phẩm dùng sớm, ảnh đại diện và nhạc phim. '+self.KL,'TU KHOA')):
            r=self.keo(dict(self.HK,**{k:moi})); self.assertFalse(r[1],(k,r)); self.assertIn(dau,r[2],(k,r[2]))

    GOOD='Game bắn súng roguelike, chết là chơi lại từ đầu, chơi chung online được, người chơi chấm 4.4 trên 5 sao. Bản Deluxe có thêm 2 vũ khí với vật phẩm dùng sớm, ảnh đại diện và nhạc phim. '+KL
    def test_p2_d3_so_luong_dung_som_che_do_edition_phu_dinh_thang_diem(self):      # Sol 11/10: moi bien the SAI phai TRUOT
        self.assertTrue(self.keo(dict(self.HK,gioi=self.GOOD))[1])
        for ten,moi,dau in (('so luong',self.GOOD.replace('2 vũ khí','9 vũ khí'),'SO LUONG'),('thieu dung som',self.GOOD.replace(' dùng sớm',''),'DUNG SOM'),
                            ('che do',self.GOOD.replace('chơi chung online được','chơi chung trên một máy'),'TU KHOA'),('edition',self.GOOD.replace('Bản Deluxe','Bản Standard'),'TU'),
                            ('phu dinh','Game bắn súng roguelike, chơi chung online được, người chơi chấm 4.4 trên 5 sao. Bản Deluxe không có thêm vũ khí, vật phẩm, ảnh đại diện và nhạc phim. '+self.KL,'PHU DINH'),
                            ('thang 10',self.GOOD.replace('trên 5 sao','trên 10 sao'),'DIEM SAO'),
                            ('phien ban',self.GOOD.replace('chấm 4.4 trên 5 sao','chấm 4.5 sao, phiên bản 4.4'),'DIEM SAO')):
            r=self.keo(dict(self.HK,gioi=moi)); self.assertFalse(r[1],(ten,r)); self.assertIn(dau,r[2],(ten,r[2]))
    # ---- Keo v10 (12/10): cau mo tinh huong (tien / sao theo GIA TRI) + cau ket luan cuoi doan gioi ----
    MO_VAL='Returno Digital Deluxe Edition đang giảm 75% trên PS to Mỹ nè.'
    def test_v10_mo_so_gia_khong_doc_tien_nen_khong_kiem_tien(self):     # Opus 12/10: cau mo kieu 1 chi giu cum so sanh, KHONG doc so tien (gia con nam o doan `gia`)
        cau='Chưa bằng một bữa lẩu cho bốn người, mà mua được game này nè. '
        r=self.keo(dict(self.HK,mo=cau+self.MO_VAL),kieu='so_gia'); self.assertTrue(r[1],r)
        r=self.keo(dict(self.HK,mo='Rẻ hơn một ly trà sữa, mà mua được game này nè. '+self.MO_VAL),kieu='so_gia'); self.assertTrue(r[1],r)
        r=self.keo(dict(self.HK,mo=cau+self.MO_VAL)); self.assertTrue(r[1],r)      # kich-ban cu khong ghi `kieu`
    def test_v10_mo_so_gia_sao_va_so_sao_doc_diem_dung_gia_tri(self):     # gioi_mau diem 4,4
        g='Chưa bằng một bữa lẩu cho bốn người, mà mua được một game bốn phẩy bốn sao nè. '
        r=self.keo(dict(self.HK,mo=g+self.MO_VAL),kieu='so_gia_sao'); self.assertTrue(r[1],r)
        r=self.keo(dict(self.HK,mo=g.replace('bốn phẩy bốn','4,4')+self.MO_VAL),kieu='so_gia_sao'); self.assertTrue(r[1],r)
        for ten,moi in (('sao sai',g.replace('bốn phẩy bốn','bốn phẩy tám')),('sao nguyen sai',g.replace('bốn phẩy bốn','năm')),('mat sao','Chưa bằng một bữa lẩu cho bốn người, mà mua được game này nè. ')):
            r=self.keo(dict(self.HK,mo=moi+self.MO_VAL),kieu='so_gia_sao'); self.assertFalse(r[1],(ten,r)); self.assertIn('SAO (cau mo)',r[2],(ten,r[2]))
        r=self.keo(dict(self.HK,mo='Game bốn phẩy bốn sao mà giờ giảm sâu nè. '+self.MO_VAL),kieu='so_sao'); self.assertTrue(r[1],r)
        r=self.keo(dict(self.HK,mo='Game bốn phẩy chín sao mà giờ giảm sâu nè. '+self.MO_VAL),kieu='so_sao'); self.assertFalse(r[1],r); self.assertIn('SAO (cau mo)',r[2])
    def test_v10_mo_giam_sau_phan_tram_trong_cau_mo_van_phai_dung(self):
        r=self.keo(dict(self.HK,mo='Giảm bảy mươi lăm phần trăm, kèo này hiếm nha. '+self.MO_VAL),kieu='giam_sau'); self.assertTrue(r[1],r)
        r=self.keo(dict(self.HK,mo='Giảm sáu mươi phần trăm, kèo này hiếm nha. Returno Digital Deluxe Edition đang giảm trên PS to Mỹ nè.'),kieu='giam_sau'); self.assertFalse(r[1],r); self.assertIn('PHAN TRAM',r[2])
    def test_v10_mo_giam_sau_moi_lan_phan_tram_phai_bang_giam(self):      # Sol P1: du lieu 75% ma cau mo doc 60% -> TRUOT, du doan sau co 75%
        r=self.keo(dict(self.HK,mo='Giảm sáu mươi phần trăm, kèo này hiếm nha. '+self.MO_VAL),kieu='giam_sau'); self.assertFalse(r[1],r); self.assertIn('PHAN TRAM LAN KHAC',r[2])
        r=self.keo(dict(self.HK,mo='Giảm 60%, kèo này hiếm nha. '+self.MO_VAL),kieu='giam_sau'); self.assertFalse(r[1],r); self.assertIn('PHAN TRAM LAN KHAC',r[2])
        r=self.keo(dict(self.HK,mo='Giảm 75%, kèo này hiếm nha. '+self.MO_VAL),kieu='giam_sau'); self.assertTrue(r[1],r)
        r=self.keo(dict(self.HK,mo='Game bốn phẩy bốn sao mà giờ giảm sâu nè. Returno Digital Deluxe Edition đang giảm 60% trên PS to Mỹ nè.'),kieu='so_sao'); self.assertFalse(r[1],r)    # 60% o cau chinh: truot nhu cu (khong co 75%)
    def test_v10_ket_luan_phu_dinh_truot(self):      # Sol P1
        sau='Game bắn súng roguelike, chết là chơi lại từ đầu, chơi chung online được, người chơi chấm 4.4 trên 5 sao. Bản Deluxe có thêm 2 vũ khí với vật phẩm dùng sớm, ảnh đại diện và nhạc phim. '
        for moi in (sau+'Không hợp với ai thích thể loại này.',sau+'Chẳng hợp với ai thích thể loại này.'):
            r=self.keo(dict(self.HK,gioi=moi)); self.assertFalse(r[1],r); self.assertIn('PHU DINH',r[2])
        self.assertTrue(self.keo(dict(self.HK,gioi=sau+self.KL))[1])
    def test_v10_ket_luan_bat_buoc_dung_nhanh_va_cam_nhanh_khac(self):
        sau='Game bắn súng roguelike, chết là chơi lại từ đầu, chơi chung online được, người chơi chấm 4.4 trên 5 sao. Bản Deluxe có thêm 2 vũ khí với vật phẩm dùng sớm, ảnh đại diện và nhạc phim.'
        r=self.keo(dict(self.HK,gioi=sau)); self.assertFalse(r[1],r); self.assertIn('hop voi ai thich the loai nay',r[2])            # thieu ket luan
        r=self.keo(dict(self.HK,gioi=sau+' Hợp với ai thích thể loại nầy.')); self.assertTrue(r[1],r)                                   # Whisper sai dau thanh: van dat
        for sai in ('Với giá này thì đáng mua.','Chỉ nên mua nếu bạn thật sự thích game này.'):
            r=self.keo(dict(self.HK,gioi=sau+' '+self.KL+' '+sai)); self.assertFalse(r[1],(sai,r)); self.assertIn('TU CAM',r[2],(sai,r[2]))   # doc nham nhanh khac
            r=self.keo(dict(self.HK,gioi=sau+' '+sai)); self.assertFalse(r[1],(sai,r))
    def test_p1_d1_khong_sap_khi_diem_ban_the_loai_none(self):      # khoi so sanh D1 THAT trong kiem-tat-ca.py
        src=KIEM('keo-thom').read_text(encoding='utf-8'); a=src.index("_cs=lambda"); b=src.index("\n",a); g=dict(re=__import__('re')); exec(src[a:b].split(';')[-1].strip() if False else src[a:b],g)
        i=src.index("nd=d.get('noiDung',{}); sai=[]"); j=src.index("if not okk: sai.append",i); j=src.index("\n",j)
        for exp in ({'gioi.diem':None,'gioi.ban':None,'gioi.the_loai':None,'gioi.chip':[],'gioi.them':[]},):
            g2=dict(g,d=dict(noiDung={}),exp=exp); exec(src[i:j],g2); self.assertEqual(g2['sai'],[])


class D3BietTruoc(unittest.TestCase):      # G3 13/10 o CAP SCRIPT: khoi D3 THAT cua kiem-tat-ca.py (keo-thom) voi kich-ban.json.doan[gioi].bt + keo.json.biet_truoc; cau trai nghia -> TRUOT
    BT=dict(screenLanguages=['en','ja'],spokenLanguages=['en'],online='tuy_chon',can_plus_online=True,so_nguoi_online=16,mua_them=True)
    PD='Game chưa có phụ đề tiếng Việt, có tiếng Anh.'; PL='Chơi một mình không cần PS Plus, chơi online cần gói.'; SN='Chơi online được tối đa mười sáu người.'
    KL='Hợp với ai thích thể loại này.'
    TRUOC='Game bắn súng roguelike, chết là chơi lại từ đầu, chơi chung online được, người chơi chấm 4.4 trên 5 sao. Bản Deluxe có thêm 2 vũ khí với vật phẩm dùng sớm, ảnh đại diện và nhạc phim. '
    def chay(self,gioi,bt=None,kinds=('phu_de','online')):
        VN=datetime.timezone(datetime.timedelta(hours=7)); het=datetime.datetime(2026,10,22,13,59,tzinfo=VN); V=[dict(ma='US',vnd=560000),dict(ma='HK',vnd=1209000),dict(ma='SG',vnd=1319000)]
        KEO=dict(game=dict(ten='Returnal™ Digital Deluxe Edition',giam=75),goc_vnd=2240000,con_vnd=560000,vung=V,gioi_thieu=gioi_mau(),biet_truoc=self.BT if bt is None else bt)
        heard={'mo':'Returno Digital Deluxe Edition đang giảm 75% trên PS to Mỹ nè.','gia':'Từ hơn 2 triệu 2 giờ còn có 560.000 thôi','gioi':gioi,'dap':'Store Mỹ đáng rẻ nhất, rẻ hơn Hồng Kông 650, rẻ hơn Sinh 706.','han':'Nhưng mà nhanh tay nha, hết giảm trước 2h chiều ngày 22 tháng 10, cha dám!'}
        kb=dict(doan=[dict(k=k,loi=v,**({'bt':list(kinds)} if (k=='gioi' and kinds) else {})) for k,v in heard.items()])
        sys.path.insert(0,str(ROOT/'khuon'/'keo-thom'))
        try: return chay_d3('keo-thom','# 5d) D3 (B2)','# 5c) NEN',dict(KEO=KEO,_G=KEO['game'],_V=V,_h=het,_nd=datetime.date(2026,10,11),_kb=kb),heard,['mo','gia','gioi','dap','han'])[0]
        finally: sys.path.remove(str(ROOT/'khuon'/'keo-thom'))
    def test_cau_dung_dat_va_khong_bt_thi_khong_kiem(self):
        r=self.chay(self.TRUOC+self.PD+' '+self.PL+' '+self.KL); self.assertTrue(r[1],r)
        r=self.chay(self.TRUOC+self.KL,kinds=()); self.assertTrue(r[1],r)                          # kich-ban cu / khong cau bt: khong kiem them
        r=self.chay(self.TRUOC+self.SN+' '+self.PD+' '+self.KL,kinds=('so_nguoi','phu_de')); self.assertTrue(r[1],r)
    def test_phu_de_dao_nghia_truot(self):
        r=self.chay(self.TRUOC+self.PD.replace('chưa có','có')+' '+self.PL+' '+self.KL); self.assertFalse(r[1],r); self.assertIn('BIET TRUOC phu de',r[2])
        r=self.chay(self.TRUOC+self.PD+' '+self.PL+' '+self.KL,bt=dict(self.BT,screenLanguages=['vi','en'])); self.assertFalse(r[1],r); self.assertIn('DAO NGHIA',r[2])        # du lieu CO phu de, loi noi CHUA
    def test_online_dao_nghia_truot(self):
        for moi in ('Chơi một mình cần PS Plus, chơi online cần gói.','Chơi một mình không cần PS Plus, chơi online không cần gói.'):
            r=self.chay(self.TRUOC+self.PD+' '+moi+' '+self.KL); self.assertFalse(r[1],(moi,r)); self.assertIn('BIET TRUOC PS Plus',r[2],(moi,r[2]))
    def test_bo_mat_cau_hoac_so_nguoi_sai_truot(self):
        r=self.chay(self.TRUOC+self.PD+' '+self.KL); self.assertFalse(r[1],r); self.assertIn('BIET TRUOC PS Plus',r[2])
        r=self.chay(self.TRUOC+self.SN.replace('mười sáu','sáu')+' '+self.PD+' '+self.KL,kinds=('so_nguoi','phu_de')); self.assertFalse(r[1],r); self.assertIn('BIET TRUOC so nguoi',r[2])
        self.assertTrue(self.chay(self.TRUOC+self.SN.replace('mười sáu','16')+' '+self.PD+' '+self.KL,kinds=('so_nguoi','phu_de'))[1])
    def test_keo_json_thieu_bang_chung_ma_kich_ban_doc_cau_thi_truot(self):
        r=self.chay(self.TRUOC+self.PD+' '+self.PL+' '+self.KL,bt=dict(self.BT,screenLanguages=None)); self.assertFalse(r[1],r); self.assertIn('khong du du lieu',r[2])
    def test_sol_whisper_viet_1_minh_mat_dau_cau_va_khong_co_tieng_anh(self):      # Sol soi diff G3
        r=self.chay(self.TRUOC+'Game chưa có phụ đề tiếng Việt, có tiếng Anh. Chơi 1 mình không cần PS Plus, chơi online cần gói. '+self.KL); self.assertTrue(r[1],r)
        r=self.chay(self.TRUOC+'Chơi một mình không cần PS Plus chơi online cần gói Game chưa có phụ đề tiếng Việt có tiếng Anh '+self.KL,kinds=('online','phu_de')); self.assertTrue(r[1],r)
        r=self.chay(self.TRUOC+'Chơi một mình không cần PS Plus chơi online cần gói Game có phụ đề tiếng Việt '+self.KL,bt=dict(self.BT,screenLanguages=['vi','en']),kinds=('online','phu_de')); self.assertTrue(r[1],r)
        r=self.chay(self.TRUOC+'Game chưa có phụ đề tiếng Việt, không có tiếng Anh. '+self.PL+' '+self.KL); self.assertFalse(r[1],r); self.assertIn('tieng Anh',r[2])
        r=self.chay(self.TRUOC+'Chơi một mình cần PS Plus chơi online cần gói Game chưa có phụ đề tiếng Việt có tiếng Anh '+self.KL,kinds=('online','phu_de')); self.assertFalse(r[1],r)
    def test_ket_luan_van_cuoi_va_van_kiem(self):      # cau bt chen truoc ket luan khong lam hong kiem ket luan (phu dinh / thieu)
        r=self.chay(self.TRUOC+self.PD+' '+self.PL+' Không '+self.KL.lower()); self.assertFalse(r[1],r)
        r=self.chay(self.TRUOC+self.PD+' '+self.PL); self.assertFalse(r[1],r); self.assertIn('KET LUAN',r[2])

class D3TenSauCumMoKeo(unittest.TestCase):
    """12/10: 3 khung Keo doi CUM CAM THAN truoc ten game. Khoi 5b THAT (kiem-tat-ca.py «Whisper nghe dung ten game») tim chu `đang` DAU TIEN cua doan `mo`
    => voi MOI cum mo (loi_chu.CUM_MO) khoi phai chay (khong StopIteration) va DAT khi ten duoc nghe dung; ten sai van TRUOT."""
    def chay(self,cum,nghe_mo):
        sys.path.insert(0,str(ROOT/'khuon'/'keo-thom'))
        try:
            import loi_chu as lc
            src=KIEM('keo-thom').read_text(encoding='utf-8'); i=src.index('# 5b) Whisper nghe TEN GAME'); j=src.index('# 5e)',i)
            a=src.index('import unicodedata'); b=src.index('def nghe(x16)'); g0=dict(re=re); exec(src[a:b],g0)
            tok=cum.split()+'Returnal Digital Deluxe Edition đang giảm bảy mươi lăm phần trăm trên PS Store Mỹ nè!'.split()
            moc=[dict(w=w,s=0.2*k,e=0.2*k+0.15,doan='mo') for k,w in enumerate(tok)]; kq=[]
            with tempfile.TemporaryDirectory() as d:
                (pathlib.Path(d)/'kich-ban.json').write_text(json.dumps(dict(doan=[dict(k='mo',loi=' '.join(tok),neo=dict(ten=len(cum.split())))])),encoding='utf-8')
                g=dict(json=json,re=re,B=pathlib.Path(d),SOM=False,moc=moc,chuan=g0['chuan'],NS=ns,ten_noi=lc.ten_noi,_G=dict(ten='Returnal™ Digital Deluxe Edition'),TVS=[(0.0,9.0,'x')],
                       heard={'mo':nghe_mo},ghi=lambda t,ok,so,ma:kq.append((t,bool(ok),so)))
                exec(compile(src[i:j],'d3-5b-keo','exec'),g)
            return kq
        finally: sys.path.remove(str(ROOT/'khuon'/'keo-thom'))
    def test_moi_cum_mo_chay_duoc_va_dat(self):
        sys.path.insert(0,str(ROOT/'khuon'/'keo-thom'))
        try:
            import loi_chu as lc
            for cum in lc.CUM_MO:
                kq=self.chay(cum,cum+' Returnal Digital Deluxe Edition đang giảm 75% trên PS Store Mỹ nè!'); self.assertEqual(len(kq),1,cum); self.assertTrue(kq[0][1],(cum,kq))
                kq=self.chay(cum,cum+' Xin chao cac ban dang giảm 75% trên PS Store Mỹ nè!'); self.assertFalse(kq[0][1],(cum,kq))
        finally: sys.path.remove(str(ROOT/'khuon'/'keo-thom'))


class D2GioTheoKhungKeo(unittest.TestCase):
    """12/10: D2 (het giam >= gio dang CUA KHUNG + 1 ngay) cho 3 khung; thieu env GIO_DANG thi theo DANG, thieu ca hai thi khung goc 20:00."""
    def chay(self,env,het):
        src=KIEM('keo-thom').read_text(encoding='utf-8'); i=src.index('# D2: giay het giam'); j=src.index('# 2b) do tren LOP CHU',i); kq=[]
        VN=datetime.timezone(datetime.timedelta(hours=7)); old=dict(os.environ)
        try:
            for k in ('DANG','GIO_DANG'): os.environ.pop(k,None)
            os.environ.update(env)
            g=dict(os=os,NS=ns,_nd=datetime.date(2026,10,13),_h=het.replace(tzinfo=VN),HOI_QUY=False,KEO=dict(han=dict(ma='US')),ghi=lambda t,ok,so,ma:kq.append((t,bool(ok),so)))
            exec(compile(src[i:j],'d2-keo','exec'),g)
        finally: os.environ.clear(); os.environ.update(old)
        return kq[0]
    def test_nguong_ba_khung(self):
        for env,gio in (({'DANG':'keo-thom-2','GIO_DANG':'15:00'},'15:00'),({'DANG':'keo-thom','GIO_DANG':'20:00'},'20:00'),({'DANG':'keo-thom-3','GIO_DANG':'22:00'},'22:00'),
                        ({'DANG':'keo-thom-2'},'15:00'),({'DANG':'keo-thom-3'},'22:00'),({},'20:00')):
            h,m=map(int,gio.split(':')); can=datetime.datetime(2026,10,14,h,m)
            t,ok,_=self.chay(env,can); self.assertTrue(ok,(env,gio)); self.assertIn(f'>= {gio} ngay dang',t)
            t,ok,_=self.chay(env,can-datetime.timedelta(minutes=1)); self.assertFalse(ok,(env,gio))

if __name__=='__main__': unittest.main()


class TenNhayDonTinNhanh(unittest.TestCase):
    """CI that 11/10 (run 38111579743): tin DOT SALE «Player's Choice» bi bao «Player's» khong co trong tin.json vi so ca chuoi 'players'
    voi tap manh ['player','s']. Phep phai tach dau nhay giong bag()."""
    def test_tach_dau_nhay(self):
        import pathlib, re
        src = (pathlib.Path(__file__).resolve().parents[2] / 'khuon' / 'tin-nhanh' / 'kiem' / 'kiem-tat-ca.py').read_text(encoding='utf-8')
        self.assertIn("all(x in cho for x in re.findall(r'[a-z0-9]+',sc.bo_dau(tk)))", src)
        sys_path = str(pathlib.Path(__file__).resolve().parents[2] / 'khuon' / 'tin-nhanh')
        import sys
        if sys_path not in sys.path: sys.path.insert(0, sys_path)
        import so_chu as sc
        cho = set(re.findall(r'[a-z0-9]+', sc.bo_dau("Player's Choice ĐỢT SALE")))
        ok = lambda tk: all(x in cho for x in re.findall(r'[a-z0-9]+', sc.bo_dau(tk)))
        self.assertTrue(ok("Player's")); self.assertTrue(ok("Player’s")); self.assertTrue(ok("Đợt")); self.assertFalse(ok("Witcher"))
