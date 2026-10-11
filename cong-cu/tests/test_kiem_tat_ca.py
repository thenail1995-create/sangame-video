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
        keo=dict(ngay_dang='2026-10-11',game=dict(ten='Returnal Digital Deluxe Edition',giam=75),goc_vnd=2240000,con_vnd=560000,han=dict(endTime=het,ma='US'),
                 vung=[dict(ma='US',vnd=560000),dict(ma='HK',vnd=1210000),dict(ma='SG',vnd=1320000)])
        kb=chay_kich_ban('keo-thom',['kich-ban.py','loi_chu.py'],{'keo.json':keo}); loi={x['k']:x['loi'] for x in kb['doan']}
        ma=lambda s:[m for m,_ in ns.doc_vung(s)]
        for k,t in loi.items():
            self.assertEqual(bool(ns.doc_phan_tram(t)),k in ns.KEO_PHAN_TRAM,(k,t))
            mong=[keo['vung']['ABC'.index(x)]['ma'] for x in ns.KEO_VUNG.get(k,())]
            self.assertEqual(sorted(set(ma(t))),sorted(set(mong)),(k,t))
        self.assertEqual(ma(loi['dap']),['US','HK','SG']); self.assertIn('rẻ hơn',loi['dap'])      # chieu so sanh 'A rẻ hơn B' (phep chu_the trong doi_chieu)

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
    def keo(self,heard):
        VN=datetime.timezone(datetime.timedelta(hours=7)); het=datetime.datetime(2026,10,22,13,59,tzinfo=VN)
        V=[dict(ma='US',vnd=560000),dict(ma='HK',vnd=1209000),dict(ma='SG',vnd=1319000)]
        KEO=dict(game=dict(ten='Returnal™ Digital Deluxe Edition',giam=75),goc_vnd=2240000,con_vnd=560000,vung=V)
        sys.path.insert(0,str(ROOT/'khuon'/'keo-thom'))
        try: return chay_d3('keo-thom','# 5d) D3 (B2)','# 5c) NEN',dict(KEO=KEO,_G=KEO['game'],_V=V,_h=het,_nd=datetime.date(2026,10,11),_kb=dict(doan=[dict(k=k,loi=v) for k,v in heard.items()])),heard,['mo','gia','hoi','dap','han'])[0]
        finally: sys.path.remove(str(ROOT/'khuon'/'keo-thom'))
    HK={'mo':'Returno Digital Deluxe Edition đang giảm 75% trên PS to Mỹ nè.','gia':'Từ hơn 2 triệu 2 giờ còn có 560.000 thôi','hoi':'Ủa mà khoan, mua store hồng kông hay sinh có dạy hơn không ta? Ha ha, không...',
        'dap':'Không nha! Quy ra tiền Việt, Mỹ vẫn dạy hơn Hồng Kông 600 rưỡi, dạy hơn sinh tới 706 lận.','han':'Nhưng mà nhanh tay nha, hết giảm trước 2h chiều ngày 22 tháng 10, cha dám!'}
    def test_keo_cau_that_dat(self):
        r=self.keo(self.HK); self.assertTrue(r[1],r)
    def test_keo_delux_thieu_chu_e_van_dat_nhung_thieu_phien_ban_van_truot(self):      # CI that 11/10: Whisper nghe 'Delux' thay 'Deluxe'
        r=self.keo(dict(self.HK,mo='Returnal Digital Delux Edition đang giảm 75% trên PS to Mỹ nè.')); self.assertTrue(r[1],r)
        r=self.keo(dict(self.HK,mo='Returnal Digital Edition đang giảm 75% trên PS to Mỹ nè.')); self.assertFalse(r[1],r); self.assertIn('thieu phien ban deluxe',r[2])
    def test_keo_bo_cau_phan_tram_vung_hoac_dao_chieu_thi_truot(self):
        for k,moi,dau in (('mo','Returno Digital Deluxe Edition đang giảm trên PS Store nè.','VUNG'),('mo','Returno Digital Deluxe Edition đang giảm trên PS to Mỹ nè.','PHAN TRAM'),('hoi','Ủa mà khoan, mua store hay có dạy hơn không ta?','VUNG'),
                          ('dap','Không nha! Quy ra tiền Việt, Mỹ vẫn đắt hơn Hồng Kông 600 rưỡi, dạy hơn sinh tới 706 lận.','CHIEU SO SANH')):
            r=self.keo(dict(self.HK,**{k:moi})); self.assertFalse(r[1],(k,r)); self.assertIn(dau,r[2],(k,r[2]))

if __name__=='__main__': unittest.main()
