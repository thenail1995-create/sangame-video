# Test 12/10: 3 khung Keo (keo-thom-2 15:00 · keo-thom 20:00 · keo-thom-3 22:00) dung chung khuon keo-thom.
#  - cum mo `loi_chu.cum_mo` (khac nhau giua 3 khung, khac hom truoc, khong chua `đang`, giu khoa `em`, chay duoc nhanh D3 tim `đang`)
#  - chon-keo.py: lich su chung MOI khung, co_hom_nay chi DUNG tag khung dang chay, gio dang/han toi thieu theo khung
import datetime,json,os,pathlib,re,subprocess,sys,tempfile,types,unittest
T=pathlib.Path(__file__).resolve().parent; sys.path.insert(0,str(T))
import loi_chu as lc
KHUNG=('keo-thom-2','keo-thom','keo-thom-3')
def ngay(i): return (datetime.date(2026,10,13)+datetime.timedelta(days=i)).isoformat()
def chay_kich_ban(ngay_dang,dang,giam=75,con_vnd=412000,diem=None):
    """Chay kich-ban.py that tren keo.json mau (thu muc tam) -> (doan, loi.txt). Mac dinh: giam 75%, con 412.000, khong diem (v10: cau mo kieu so gia/giam sau).
    Muon ep cau mo CUM CAM THAN (khong kieu nao du dieu kien) dung giam=40, con_vnd=1_200_000, diem=None — xem CUM_RIENG."""
    keo=dict(ngay_dang=ngay_dang,game=dict(ten='Returnal',giam=giam),goc_vnd=1650000,con_vnd=con_vnd,
             vung=[dict(ma='US',vnd=412000),dict(ma='HK',vnd=520000),dict(ma='SG',vnd=600000)],han=dict(endTime=int(datetime.datetime(2026,10,20,12,0,tzinfo=datetime.timezone.utc).timestamp()*1000)),
             gioi_thieu=dict(the_loai=[dict(vi='hành động')],dac_diem=[dict(noi='bắn súng góc nhìn thứ ba')],diem=diem,ban=None))
    with tempfile.TemporaryDirectory() as d:
        d=pathlib.Path(d)
        for f in ('kich-ban.py','loi_chu.py'): (d/f).write_text((T/f).read_text(encoding='utf-8'),encoding='utf-8')
        (d/'keo.json').write_text(json.dumps(keo,ensure_ascii=False),encoding='utf-8')
        env=dict(os.environ); env.pop('DANG',None)
        if dang: env['DANG']=dang
        r=subprocess.run([sys.executable,str(d/'kich-ban.py'),str(d/'keo.json')],capture_output=True,text=True,cwd=d,env=env)
        if r.returncode: raise AssertionError(r.stderr[-800:]+r.stdout[-300:])
        return json.load(open(d/'kich-ban.json'))['doan'],(d/'loi.txt').read_text(encoding='utf-8')

CUM_RIENG=dict(giam=40,con_vnd=1_200_000,diem=None)    # khong kieu cau mo v10 nao du dieu kien (gia > 600.000, khong diem, giam < 50) -> CUM_MO
class CumMo(unittest.TestCase):
    def test_bo_cum(self):
        self.assertGreaterEqual(len(lc.CUM_MO),6); self.assertIn('Ê anh em!!',lc.CUM_MO); self.assertEqual(len(set(lc.CUM_MO)),len(lc.CUM_MO))
        for c in lc.CUM_MO:
            ws=[w.lower().strip('!?.,…') for w in c.split()]
            self.assertNotIn('đang',ws,c); self.assertNotIn('đang',c.lower(),c); self.assertEqual(ws.count('em'),1,c); self.assertTrue(c.endswith('!!'),c)
    def test_ba_khung_cung_ngay_khac_nhau_va_khac_hom_truoc(self):
        for i in range(0,400):
            ba=[lc.cum_mo(ngay(i),k) for k in KHUNG]; self.assertEqual(len(set(ba)),3,(ngay(i),ba))
            for k in KHUNG: self.assertNotEqual(lc.cum_mo(ngay(i),k),lc.cum_mo(ngay(i+1),k),(ngay(i),k))
    def test_mac_dinh_hanh_vi_cu(self):
        self.assertEqual(lc.cum_mo(ngay(0),None),'Ê anh em!!'); self.assertEqual(lc.cum_mo(ngay(0),'khung-la'),'Ê anh em!!'); self.assertEqual(lc.cum_mo(None,'keo-thom'),'Ê anh em!!')
    def test_ngay_13_14(self):    # mo phong yeu cau: in cum mo
        for i in (0,1):
            print(ngay(i),{k:lc.cum_mo(ngay(i),k) for k in KHUNG})
    def test_kich_ban_giu_khoa_va_cau_mo(self):    # moi cum: doan `mo` = «<cum> <ten> đang giảm ... nè!», khoa em/ten/giam/ps/vung giu dung, `đang` dau tien dung ngay sau ten (nhanh D3)
        da=set()
        for i in range(0,8):
            for k in KHUNG+(None,):
                doan,loi=chay_kich_ban(ngay(i),k,**CUM_RIENG); mo=doan[0]; ws=mo['loi'].split(); neo=mo['neo']
                self.assertEqual(mo['kieu'],'cum')
                cum=lc.cum_mo(ngay(i),k); n=len(cum.split()); da.add(cum)
                self.assertEqual(' '.join(ws[:n]),cum); self.assertEqual(ws[neo['em']].lower().strip('!'),'em'); self.assertEqual(neo['ten'],n)
                for kh in ('ten','giam','ps','vung','em'): self.assertIn(kh,neo,kh)
                i1=next(j for j,w in enumerate(ws) if w.lower()=='đang')    # = D3 kiem-tat-ca.py:231
                self.assertGreater(i1,neo['ten']); self.assertEqual(ws[i1+1],'giảm'); self.assertEqual(neo['giam'],i1+1); self.assertEqual(ws[-1],'nè!')
                self.assertEqual(sum(1 for w in ws[:neo['ten']] if w.lower()=='đang'),0)
                for d in doan[1:]: self.assertNotIn('Ê anh',d['loi'])
        self.assertEqual(da,set(lc.CUM_MO))    # tat ca cum da chay qua kich-ban.py
    def test_khung_goc_khong_env_giu_nguyen(self):
        doan,loi=chay_kich_ban(ngay(0),None); self.assertEqual(doan[0]['kieu'],'cum'); self.assertTrue(loi.startswith('[excited] Ê anh em!! Returnal đang giảm'),loi[:80]); self.assertEqual(doan[0]['neo']['em'],2)

def nap_lich_su(dang,che=None,**kw):
    """exec khoi `lich_su()` that cua chon-keo.py voi bien gia lap (gh, fixture)."""
    src=(T/'chon-keo.py').read_text(encoding='utf-8'); a=src.index('def lich_su():'); b=src.index('LS=lich_su()')
    ns=dict(datetime=datetime,json=json,re=re,subprocess=kw.get('subprocess',subprocess),SO_NGAY_LAP=14,NGAY=datetime.date.fromisoformat(kw.get('ngay','2026-10-13')),DANG=dang,
            A=types.SimpleNamespace(bo_lich_su=False,lich_su=kw.get('lich_su'),repo_phat_hanh='x/y'),t=types.SimpleNamespace(_ten_goc=lambda x:x.lower()),thoat=lambda m,s:(_ for _ in ()).throw(SystemExit(m)))
    exec(src[a:b],ns); return ns['lich_su']()

class LichSu(unittest.TestCase):
    SRC=(T/'chon-keo.py').read_text(encoding='utf-8')
    def test_regex_release_bat_ca_ba_khung(self):
        m=re.search(r"re\.fullmatch\(r'(v-[^']+)',tg\)",self.SRC); self.assertTrue(m); p=m.group(1)
        for tg,ok in (('v-2026-10-13-keo-thom',1),('v-2026-10-13-keo-thom-2',1),('v-2026-10-13-keo-thom-3',1),('v-2026-10-13-top5',0),('v-2026-10-13-keo-thom-x',0),('thu-2026-10-13-keo-thom-2',0),('v-2026-10-13-keo-thom-22-1',0)):
            self.assertEqual(bool(re.fullmatch(p,tg)),bool(ok),tg)
    def goi(self,tags,mani):
        def run(cmd,**k):
            if cmd[:3]==['gh','release','list']: return types.SimpleNamespace(returncode=0,stdout=json.dumps([dict(tagName=t) for t in tags]),stderr='')
            tg=cmd[3]; return types.SimpleNamespace(returncode=0,stdout=json.dumps(dict(kiem_lai=mani[tg])),stderr='')
        return types.SimpleNamespace(run=run)
    def test_release_thuc_loai_game_moi_khung_nhung_co_hom_nay_chi_dung_tag(self):
        tags=['v-2026-10-13-keo-thom','v-2026-10-13-keo-thom-2','v-2026-10-12-keo-thom-3','v-2026-09-01-keo-thom-2']
        mani={'v-2026-10-13-keo-thom':[dict(pid='A',ten='Alpha')],'v-2026-10-13-keo-thom-2':[dict(pid='B',ten='Beta')],'v-2026-10-12-keo-thom-3':[dict(pid='C',ten='Gamma')],'v-2026-09-01-keo-thom-2':[dict(pid='Z',ten='Zeta')]}
        sp=self.goi(tags,mani)
        for dang,hn in (('keo-thom-3',False),('keo-thom',True),('keo-thom-2',True)):
            ls=nap_lich_su(dang,subprocess=sp); self.assertEqual(ls['pid'],{'A','B','C'},dang); self.assertEqual(ls['goc'],{'alpha','beta','gamma'}); self.assertEqual(ls['co_hom_nay'],hn,dang)   # Z ngoai 14 ngay
    def test_fixture_co_dang(self):
        with tempfile.NamedTemporaryFile('w',suffix='.json',delete=False,encoding='utf-8') as f:
            json.dump(dict(so_ky=3,da_dang=[dict(ngay='2026-10-13',dang='keo-thom-2',pid=['B'],ten='Beta'),dict(ngay='2026-10-13',pid=['A'],ten='Alpha'),dict(ngay='2026-10-10',dang='keo-thom-3',pid=['C'],ten='Gamma')]),f)
        try:
            for dang,hn in (('keo-thom-3',False),('keo-thom-2',True),('keo-thom',True)):    # dong khong ghi `dang` = khung goc
                ls=nap_lich_su(dang,lich_su=f.name); self.assertEqual(ls['pid'],{'A','B','C'}); self.assertEqual(ls['co_hom_nay'],hn,dang)
        finally: os.unlink(f.name)
    def test_gio_dang_theo_khung(self):
        src=self.SRC; a=src.index("DANG=os.environ.get('DANG')"); b=src.index('HAN_TOI_THIEU=')+len('HAN_TOI_THIEU=GIO_DANG+datetime.timedelta(days=1)')
        VN=datetime.timezone(datetime.timedelta(hours=7))
        def chay(dang,gio):
            old=dict(os.environ)
            try:
                os.environ.pop('DANG',None); os.environ.pop('GIO_DANG',None)
                if dang: os.environ['DANG']=dang
                if gio: os.environ['GIO_DANG']=gio
                ns=dict(os=os,datetime=datetime,NGAY=datetime.date(2026,10,13),VN=VN); exec(src[a:b],ns); return ns['GIO_DANG'],ns['HAN_TOI_THIEU']
            finally: os.environ.clear(); os.environ.update(old)
        for dang,gio,h in (('keo-thom-2',None,15),('keo-thom',None,20),('keo-thom-3',None,22),(None,None,20),('keo-thom-3','22:00',22),('keo-thom','20:00',20)):
            g,han=chay(dang,gio); self.assertEqual((g.hour,g.minute),(h,0),(dang,gio)); self.assertEqual(han,g+datetime.timedelta(days=1))
if __name__=='__main__': unittest.main()


# ================= KHUON KEO v10 (12/10): cau mo tinh huong · cau ket luan · doan ket =================
sys.path.insert(0,str(T.parent.parent/'cong-cu')); import nghe_so as NS
def ngay_khung(kieu_mong,dang='keo-thom'):
    """Mot ngay (13..15/10) ma kieu UU TIEN cua khung `dang` = KIEU_MO[kieu_mong]."""
    return next(ngay(i) for i in range(3) if lc.kieu_uu_tien(ngay(i),dang)==lc.KIEU_MO.index(kieu_mong))
def D(tb,luot):    # dang keo.json.gioi_thieu.diem (kich-ban.py doc lam_tron / noi)
    r=lc.lam_tron_diem(tb); return dict(tb=tb,lam_tron=r,so_luot=luot,noi=lc.noi_diem(r),hien=lc.hien_diem(r),luot=str(luot))
class CauMoTinhHuong(unittest.TestCase):
    """Kich ban v10 A: 3 kieu xoay theo (ngay, khung); bang nguong; du lieu bien; fallback; moi so qua D3 (nghe_so doc theo GIA TRI)."""
    def mo(self,kieu,con=300000,giam=40,diem=None,dang='keo-thom'):
        return lc.cau_mo(ngay_khung(kieu,dang),dang,con,giam,diem)
    def test_ba_khung_cung_ngay_khac_kieu_uu_tien_va_khac_hom_truoc(self):
        for i in range(0,60):
            ba=[lc.kieu_uu_tien(ngay(i),k) for k in KHUNG]; self.assertEqual(sorted(ba),[0,1,2],(ngay(i),ba))
            for k in KHUNG: self.assertNotEqual(lc.kieu_uu_tien(ngay(i),k),lc.kieu_uu_tien(ngay(i+1),k),(ngay(i),k))
        self.assertIsNone(lc.kieu_uu_tien(ngay(0),None)); self.assertIsNone(lc.kieu_uu_tien(ngay(0),'khung-la')); self.assertIsNone(lc.kieu_uu_tien(None,'keo-thom'))
    def test_bang_so_gia_bien(self):    # <=45.000 tra sua · <=110.000 ve xem phim · <=600.000 bua lau · > 600.000 khong dung kieu nay
        for con,ss in ((1000,'trà sữa'),(45000,'trà sữa'),(45001,'vé xem phim'),(110000,'vé xem phim'),(110001,'bữa lẩu'),(600000,'bữa lẩu')):
            m=self.mo('so_gia',con=con); self.assertEqual(m['kieu'],'so_gia',con); self.assertIn(ss,m['loi'],(con,m['loi'])); self.assertIn('game này',m['loi'])
        for con,cau in ((45000,'Rẻ hơn một ly trà sữa, mà mua được game này nè.'),(45001,'Chưa bằng một vé xem phim, mà mua được game này nè.'),(300000,'Chưa bằng một bữa lẩu cho bốn người, mà mua được game này nè.')):
            self.assertEqual(self.mo('so_gia',con=con)['loi'],cau)      # khong doc so tien (Opus 12/10)
        for con in (600001,2_000_000):
            self.assertNotIn(self.mo('so_gia',con=con,giam=40)['kieu'],('so_gia','so_gia_sao'),con)
    def test_roi_sang_kieu_2_khi_gia_cao(self):     # ke hoach: >600.000 -> roi sang kieu 2 (so sao) neu du dieu kien
        m=self.mo('so_gia',con=600001,giam=40,diem=D(4.7,500)); self.assertEqual(m['kieu'],'so_sao')
        m=self.mo('so_gia',con=600001,giam=60,diem=D(4.3,500)); self.assertEqual(m['kieu'],'giam_sau')
        m=self.mo('so_gia',con=600001,giam=40,diem=D(4.3,500)); self.assertEqual(m['kieu'],'cum')
    def test_so_gia_co_game_x_sao_chi_khi_diem_tu_4(self):
        m=self.mo('so_gia',con=300000,diem=D(4.0,300)); self.assertEqual(m['kieu'],'so_gia_sao'); self.assertIn('một game bốn sao nè.',m['loi'])
        m=self.mo('so_gia',con=300000,diem=D(4.8,571)); self.assertIn('một game bốn phẩy tám sao nè.',m['loi'])
        m=self.mo('so_gia',con=300000,diem=D(3.95,300)); self.assertEqual(m['kieu'],'so_gia_sao')    # 3,95 -> 4,0 (lam tron nua len, nhu cau gioi thieu)
        m=self.mo('so_gia',con=300000,diem=D(3.94,300)); self.assertEqual(m['kieu'],'so_gia'); self.assertIn('game này nè.',m['loi'])
        m=self.mo('so_gia',con=300000,diem=None); self.assertEqual(m['kieu'],'so_gia')
    def test_so_sao_bien_diem_va_luot(self):     # diem DA LAM TRON (4,45 -> 4,5 la so video noi o cau gioi thieu); >= 200 luot
        for tb,luot,ok in ((4.44,500,False),(4.45,500,True),(4.49,500,True),(4.5,200,True),(4.5,199,False),(5.0,200,True),(4.9,0,False)):
            m=self.mo('so_sao',con=900000,giam=40,diem=D(tb,luot)); self.assertEqual(m['kieu']=='so_sao',ok,(tb,luot,m))
        m=self.mo('so_sao',con=900000,diem=D(4.78,571)); self.assertEqual(m['loi'],'Game bốn phẩy tám sao mà giờ giảm sâu nè.')
        self.assertEqual(self.mo('so_sao',con=900000,diem=D(5.0,300))['loi'],'Game năm sao mà giờ giảm sâu nè.')
    def test_du_phong_xoay_theo_khung(self):      # Sol P2: khung chan thu p+1 roi p+2; khung le thu p+2 roi p+1. Du lieu: chi so_sao va giam_sau hop le (so_gia khong: gia > 600.000)
        kw=dict(con_vnd=900000,giam=60,diem=D(4.8,571))
        for dang,mong in (('keo-thom-2','so_sao'),('keo-thom','giam_sau'),('keo-thom-3','so_sao')):
            ng=ngay_khung('so_gia',dang); self.assertEqual(lc.cau_mo(ng,dang,kw['con_vnd'],kw['giam'],kw['diem'])['kieu'],mong,dang)
        kw=dict(con_vnd=300000,giam=40,diem=None)    # chi so_gia hop le; kieu uu tien so_sao / giam_sau khong hop le -> du phong so_gia (khung nao cung vay)
        for dang in KHUNG: self.assertEqual(lc.cau_mo(ngay_khung('so_sao',dang),dang,**kw)['kieu'],'so_gia')
    def test_cau_that_3_khung_cung_ngay_cung_keo_json_khi_2_khung_uu_tien_khong_hop_le(self):
        """Chay kich-ban.py THAT cho 3 khung cung ngay, cung keo.json (chi kieu so_gia hop le -> 2 khung co kieu uu tien khong hop le). Cau mo = cau cua kieu hop le (neu du phong) hoac
        cum cam than; moi khung KHONG bi mat cau mo / khong co `đang`. GIOI HAN: voi cung du lieu, kieu du phong cua khung khac chinh la kieu uu tien hop le cua khung kia -> cau giong nhau la khong tranh khoi."""
        ng=ngay(0); cau={}
        for dang in KHUNG:
            doan,_=chay_kich_ban(ng,dang,giam=40,con_vnd=300000,diem=None); mo=doan[0]; self.assertEqual(mo['kieu'],'so_gia',dang)
            self.assertNotIn('đang',mo['loi'].split()[:mo['neo']['ten']]); cau[dang]=mo['loi']
        self.assertEqual(len(cau),3)
    def test_giam_sau_bien(self):
        for g,ok in ((49,False),(50,True),(51,True),(75,True)):
            m=self.mo('giam_sau',con=900000,giam=g); self.assertEqual(m['kieu']=='giam_sau',ok,g)
        self.assertEqual(self.mo('giam_sau',con=900000,giam=75)['loi'],'Giảm bảy mươi lăm phần trăm, kèo này hiếm nha.')
    def test_khong_kieu_nao_thi_cum_cam_than_cu(self):
        m=self.mo('so_gia',con=900000,giam=40,diem=D(4.0,300)); self.assertEqual((m['kieu'],m['loi']),('cum',lc.cum_mo(ngay_khung('so_gia'),'keo-thom')))
        m=lc.cau_mo(ngay(0),None,300000,75,D(4.8,500)); self.assertEqual((m['kieu'],m['loi']),('cum','Ê anh em!!'))     # khong biet khung -> hanh vi cu
    def test_moi_cau_mo_khong_co_dang_va_khong_vung_va_so_dung_gia_tri(self):
        """D3 doc theo GIA TRI: tien / sao / % trong cau mo = ky_vong, khong so nao khac; khong ten vung; khong tu `đang` (D3 5b cat ten tai `đang` dau)."""
        da=set()
        for dang in KHUNG:
            for i in range(0,9):
                for con in (30000,45001,300000,600000,900000):
                    for giam in (40,75):
                        for diem in (None,D(4.0,300),D(4.8,571)):
                            m=lc.cau_mo(ngay(i),dang,con,giam,diem); da.add(m['kieu']); L=m['loi']
                            self.assertNotIn('đang',[w.lower().strip('!?.,…') for w in L.split()],L); self.assertEqual(NS.doc_vung(L),[],L)
                            tien={v for v,*_ in NS.doc_tien(L)}; kv=set(m['ky_vong']['tien'])    # D3 kiem BAO HAM; doc_tien nghe «một ly / một vé / bốn sao» thanh 1.000-9.000 (phan thua khong gay hai) -> moi gia tri >= 10.000 PHAI la gia con
                            self.assertEqual(kv,set()); self.assertEqual({v for v in tien if v>=10000},set(),(L,tien))    # v10: cau mo khong doc tien
                            self.assertEqual(sorted(set(NS.doc_sao(L))),sorted(set(m['ky_vong']['sao'])),(L,NS.doc_sao(L)))
                            self.assertEqual(sorted({p for p,_ in NS.doc_phan_tram(L)}),sorted(m['ky_vong']['phan_tram']),L)
                            if m['kieu']=='cum': self.assertEqual(L,lc.cum_mo(ngay(i),dang))
        self.assertEqual(da,{'so_gia','so_gia_sao','so_sao','giam_sau','cum'})
    def test_kich_ban_that_ghi_kieu_khoa_em_va_khong_mat_khoa_doan(self):
        for kieu,kw in (('so_gia',dict(con_vnd=300000)),('so_gia_sao',dict(con_vnd=300000,diem=D(4.8,571))),('so_sao',dict(con_vnd=900000,giam=40,diem=D(4.8,571))),('giam_sau',dict(con_vnd=900000,giam=75))):
            ng=ngay_khung(kieu if kieu!='so_gia_sao' else 'so_gia')
            doan,loi=chay_kich_ban(ng,'keo-thom',**kw); self.assertEqual([d['k'] for d in doan],['mo','gia','gioi','dap','han','ket'])
            mo=doan[0]; ws=mo['loi'].split(); neo=mo['neo']; self.assertEqual(mo['kieu'],kieu,mo['loi'])
            for kh in ('ten','giam','ps','vung','em'): self.assertIn(kh,neo,kh)
            i1=next(j for j,w in enumerate(ws) if w.lower()=='đang'); self.assertGreater(i1,neo['ten']); self.assertEqual(neo['giam'],i1+1); self.assertEqual(ws[i1+1],'giảm')
            self.assertEqual(ws[neo['ten']],'Returnal'); self.assertEqual(neo['em'],1); self.assertEqual(sum(1 for w in ws[:neo['ten']] if w.lower()=='đang'),0)
            self.assertTrue(loi.startswith('[excited] '+lc.cau_mo(ng,'keo-thom',kw['con_vnd'],kw.get('giam',75),kw.get('diem'))['loi']),loi[:120]); self.assertEqual(ws[-1],'nè!')
            self.assertNotIn('kieu',doan[1])

class KetLuanVaDoanKet(unittest.TestCase):
    def test_ba_nhanh_ket_luan_va_bien(self):
        K=lambda tb,luot:lc.ket_luan(D(tb,luot) if tb is not None else None)
        for tb,luot,mong in ((4.5,200,lc.KET_LUAN_DANG_MUA),(4.45,200,lc.KET_LUAN_DANG_MUA),(4.44,200,lc.KET_LUAN_HOP),(4.4,200,lc.KET_LUAN_HOP),(4.0,200,lc.KET_LUAN_HOP),(3.95,200,lc.KET_LUAN_HOP),
                             (3.94,5000,lc.KET_LUAN_CAN_NHAC),(4.0,50,lc.KET_LUAN_HOP),(4.4,49,lc.KET_LUAN_CAN_NHAC),(4.9,199,lc.KET_LUAN_CAN_NHAC),(None,0,lc.KET_LUAN_CAN_NHAC),(2.0,9999,lc.KET_LUAN_CAN_NHAC)):
            self.assertEqual(K(tb,luot),mong,(tb,luot))
        self.assertEqual(lc.KET_LUAN_ALL,(lc.KET_LUAN_DANG_MUA,lc.KET_LUAN_HOP,lc.KET_LUAN_CAN_NHAC))
        for c in lc.KET_LUAN_ALL: self.assertEqual(NS.doc_tien(c),[],c); self.assertEqual(NS.doc_phan_tram(c),[]); self.assertEqual(NS.doc_diem(c),[]); self.assertFalse(re.search(r'\d',c))     # khong so moi
    def test_kich_ban_gioi_ket_bang_ket_luan_dung_nhanh_va_doan_ket_moi(self):
        for diem,kl in ((D(4.78,571),lc.KET_LUAN_DANG_MUA),(D(4.37,3000),lc.KET_LUAN_HOP),(D(3.5,900),lc.KET_LUAN_CAN_NHAC),(None,lc.KET_LUAN_CAN_NHAC)):
            doan,loi=chay_kich_ban(ngay(0),'keo-thom',diem=diem)
            g=next(d for d in doan if d['k']=='gioi'); self.assertTrue(g['loi'].endswith(kl),(g['loi'],kl))
            for kc in lc.KET_LUAN_ALL:
                if kc!=kl: self.assertNotIn(kc,g['loi'])
            ket=next(d for d in doan if d['k']=='ket'); self.assertEqual(ket['loi'],'Theo dõi Săn Game để không lỡ kèo nào nha!')
            self.assertEqual(ket['neo'],dict(theo=0,doi=1,san=2,game=3,de=4,nha=9)); self.assertEqual(next(d for d in doan if d['k']=='ket')['loi'].split()[-1],'nha!')
            self.assertTrue(loi.rstrip().endswith('[excited] Theo dõi Săn Game để không lỡ kèo nào nha!'),loi[-120:])
            for cu in ('Tra giá','sangame','chấm com','vi en'): self.assertNotIn(cu,ket['loi'])
    def test_ket_khong_vung_khong_so_cho_d3_luat_khuon(self):
        t='Theo dõi Săn Game để không lỡ kèo nào nha!'
        self.assertEqual(NS.doc_vung(t),[]); self.assertEqual(NS.doc_phan_tram(t),[]); self.assertEqual(NS.doc_tien(t),[])
    def test_full_html_va_am08_dung_neo_moi_cua_ket(self):
        h=(T/'full.html').read_text(encoding='utf-8'); a=(T/'am08.py').read_text(encoding='utf-8')
        for cu in ('M.ket.tra','M.ket.moi','M.ket.cham1','M.ket.vi','ket.en','sangame.com.vn',"'sangame'.slice"): self.assertNotIn(cu,h,cu)
        self.assertNotIn("['ket']['en_e']",a); self.assertIn("M['ket']['nha_e']",a)
        for cu in ('M.ket.theo','M.ket.doi','M.ket.san','M.ket.game','M.ket.de','M.ket.nha','@sangamecomvn'): self.assertIn(cu,h,cu)
        # moi ten moc ket ma full.html/am08 doc phai co trong neo cua kich-ban.py
        doan,_=chay_kich_ban(ngay(0),'keo-thom'); neo=next(d for d in doan if d['k']=='ket')['neo']
        for m in re.findall(r"M\.ket\.(\w+)",h)+re.findall(r"M\['ket'\]\['(\w+)'\]",a):
            if m not in ('s','e'): self.assertIn(m[:-2] if m.endswith('_e') else m,neo,m)    # s / e = bat dau / het doan

import importlib.util as _iu,types
_spg=_iu.spec_from_file_location('gt_g3',str(T.parent.parent/'cong-cu'/'gia_trang.py')); GTMOD=_iu.module_from_spec(_spg); _spg.loader.exec_module(GTMOD)
PID_SNIPER='UP4363-PPSA01685_00-SNIPERELITE500CE'
def GTMOD_trang(ngon_ngu):
    """Trang PS Store toi gian cua Sniper Elite 5 (gia + thong bao that, ngon ngu tuy chon)."""
    cta={f'GameCTA:ADD_TO_CART:ADD_TO_CART:UP4363-PPSA01685_00-SNIPERELITE500CE-U001:OUTRIGHT':{'price':{'basePrice':'$59.99','discountedPrice':'$17.99','basePriceValue':5999,'discountedValue':1799,'currencyCode':'USD','endTime':'1792594740000'}}}
    prod={f'Product:{PID_SNIPER}':{'id':PID_SNIPER,'screenLanguages':ngon_ngu,'descriptions':[{'type':'COMPATIBILITY_NOTICE','value':'PS\xa0Plus required for online play<br/>Online play optional<br/>Supports up to 16 online players with PS Plus'}]}}
    return ''.join('<script id="env:x" type="application/json">'+json.dumps({'cache':c})+'</script>' for c in (cta,prod))


# ================= BIET TRUOC KHI MUA (G3 13/10): cau chen cuoi `gioi` truoc ket luan; chon-keo lay trang vung re nhat =================
BT_DU=dict(screenLanguages=['en','es','ja'],spokenLanguages=['en'],online='tuy_chon',can_plus_online=True,so_nguoi_online=16,mua_them=True)
def chay_kich_ban_bt(ngay_dang,dang,bt,diem=None,ban=None,the_loai=True,dac_diem=None):
    keo=dict(ngay_dang=ngay_dang,game=dict(ten='Sniper Elite 5',giam=70),goc_vnd=1650000,con_vnd=495000,vung=[dict(ma='US',vnd=495000),dict(ma='HK',vnd=560000),dict(ma='SG',vnd=640000)],
             han=dict(endTime=int(datetime.datetime(2026,10,20,12,0,tzinfo=datetime.timezone.utc).timestamp()*1000)),
             gioi_thieu=dict(the_loai=[dict(vi='bắn súng')] if the_loai else [],dac_diem=dac_diem or [],diem=diem,ban=ban),biet_truoc=bt)
    if bt is None: keo.pop('biet_truoc')
    with tempfile.TemporaryDirectory() as d:
        d=pathlib.Path(d)
        for f in ('kich-ban.py','loi_chu.py'): (d/f).write_text((T/f).read_text(encoding='utf-8'),encoding='utf-8')
        (d/'keo.json').write_text(json.dumps(keo,ensure_ascii=False),encoding='utf-8')
        env=dict(os.environ); env.pop('DANG',None)
        if dang: env['DANG']=dang
        r=subprocess.run([sys.executable,str(d/'kich-ban.py'),str(d/'keo.json')],capture_output=True,text=True,cwd=d,env=env)
        if r.returncode: raise AssertionError(r.stderr[-800:]+r.stdout[-300:])
        return json.load(open(d/'kich-ban.json'))['doan'],(d/'loi.txt').read_text(encoding='utf-8')
class BietTruocLoi(unittest.TestCase):
    def test_du_bang_chung_ra_ba_cau_ung_vien_thieu_thi_khong_cau(self):
        self.assertEqual([c['kieu'] for c in lc.cac_cau_biet_truoc(BT_DU)],['phu_de','online','so_nguoi'])
        for bt in (None,{},dict(screenLanguages=None,online=None,can_plus_online=None,so_nguoi_online=None)): self.assertEqual(lc.cac_cau_biet_truoc(bt),[],bt)
        self.assertEqual(lc.cau_biet_truoc(None,ngay(0),'keo-thom'),[])
    def test_phu_de_co_chua_va_khong_du_ngon_ngu(self):
        self.assertEqual(lc.phu_de_viet(dict(screenLanguages=['vi','en'])),'co'); self.assertEqual(lc.phu_de_viet(dict(screenLanguages=['en'])),'chua'); self.assertEqual(lc.phu_de_viet(dict(screenLanguages=['en_US','ja'])),'chua')
        self.assertIsNone(lc.phu_de_viet(dict(screenLanguages=['ja','ko']))); self.assertIsNone(lc.phu_de_viet(dict(screenLanguages=[]))); self.assertIsNone(lc.phu_de_viet(dict(screenLanguages=None)))   # khong co en -> khong noi «co tieng Anh»
        self.assertEqual([c['loi'] for c in lc.cac_cau_biet_truoc(dict(screenLanguages=['vi']))],[lc.CAU_PHU_DE_CO]); self.assertEqual([c['loi'] for c in lc.cac_cau_biet_truoc(dict(screenLanguages=['en']))],[lc.CAU_PHU_DE_CHUA])
    def test_online_chi_khi_du_bang_chung(self):
        self.assertEqual(lc.che_do_online(BT_DU),'tuy_chon'); self.assertEqual(lc.che_do_online(dict(online='bat_buoc',can_plus_online=True)),'bat_buoc')
        for bt in (dict(online='tuy_chon',can_plus_online=None),dict(online='tuy_chon',can_plus_online=False),dict(online='khong',can_plus_online=True),dict(online=None,can_plus_online=True),dict(can_plus_online=True)): self.assertIsNone(lc.che_do_online(bt),bt)
        self.assertEqual([c['loi'] for c in lc.cac_cau_biet_truoc(dict(online='tuy_chon',can_plus_online=True))],[lc.CAU_ONLINE_TUY_CHON]); self.assertEqual([c['loi'] for c in lc.cac_cau_biet_truoc(dict(online='bat_buoc',can_plus_online=True))],[lc.CAU_ONLINE_BAT_BUOC])
    def test_so_nguoi_chi_khi_tu_2_va_co_online(self):
        for n,mong in ((16,16),(2,2),(1,None),(0,None),(None,None),(True,None),(100,None)): self.assertEqual(lc.so_nguoi_online(dict(BT_DU,so_nguoi_online=n)),mong,n)
        self.assertIsNone(lc.so_nguoi_online(dict(BT_DU,can_plus_online=None)))    # khong ro online -> khong noi so nguoi
        self.assertEqual([c['loi'] for c in lc.cac_cau_biet_truoc(BT_DU)][-1],'Chơi online được tối đa mười sáu người.')
    def test_toi_da_2_cau_va_xoay_theo_ngay_khung(self):
        da=set()
        for i in range(0,60):
            for k in KHUNG:
                r=lc.cau_biet_truoc(BT_DU,ngay(i),k); self.assertEqual(len(r),2,(ngay(i),k)); self.assertEqual(len({c['kieu'] for c in r}),2); da.add(tuple(c['kieu'] for c in r))
                self.assertEqual(r,lc.cau_biet_truoc(BT_DU,ngay(i),k))                       # tat dinh
            self.assertEqual(len({tuple(c['kieu'] for c in lc.cau_biet_truoc(BT_DU,ngay(i),k)) for k in KHUNG}),3,ngay(i))       # 3 khung cung ngay ra 3 cap khac nhau (3 ung vien)
        self.assertEqual(da,{('phu_de','online'),('online','so_nguoi'),('so_nguoi','phu_de')})
        self.assertEqual(len(lc.cau_biet_truoc(dict(screenLanguages=['en']),ngay(0),'keo-thom')),1)
        self.assertEqual([c['kieu'] for c in lc.cau_biet_truoc(BT_DU,ngay(0),None)],['phu_de','online'])      # khung la -> vi tri 0
        hai=dict(screenLanguages=['en'],online='bat_buoc',can_plus_online=True)
        self.assertEqual({tuple(c['kieu'] for c in lc.cau_biet_truoc(hai,ngay(i),'keo-thom')) for i in range(6)},{('phu_de','online'),('online','phu_de')})       # 2 ung vien: doi thu tu
    def test_cau_khong_mang_phan_tram_vung_diem_sao_cho_d3(self):      # doan gioi khong doi chieu tien (doc_tien co the doc «mot minh ... PS» thanh 1.000d nhung D3 gioi khong co ky vong tien)
        for c in (lc.CAU_PHU_DE_CO,lc.CAU_PHU_DE_CHUA,lc.CAU_ONLINE_TUY_CHON,lc.CAU_ONLINE_BAT_BUOC,'Chơi online được tối đa mười sáu người.'):
            self.assertEqual(NS.doc_phan_tram(c),[],c); self.assertEqual(NS.doc_vung(c),[],c); self.assertEqual(NS.doc_diem_cham(c),[],c); self.assertEqual(NS.doc_sao(c),[],c)
    def test_kich_ban_chen_cuoi_gioi_truoc_ket_luan_giu_6_khoa_va_neo(self):
        goc,loi0=chay_kich_ban_bt(ngay(0),'keo-thom',None,diem=D(4.37,3000))
        self.assertEqual([d['k'] for d in goc],['mo','gia','gioi','dap','han','ket'])
        for dang in KHUNG+(None,):
            doan,loi=chay_kich_ban_bt(ngay(0),dang,BT_DU,diem=D(4.37,3000))
            self.assertEqual([d['k'] for d in doan],['mo','gia','gioi','dap','han','ket'])
            g=next(d for d in doan if d['k']=='gioi'); g0=next(d for d in goc if d['k']=='gioi'); cau=lc.cau_biet_truoc(BT_DU,ngay(0),dang)
            self.assertEqual(g['bt'],[c['kieu'] for c in cau]); self.assertTrue(g['loi'].endswith(' '.join(c['loi'] for c in cau)+' '+lc.KET_LUAN_HOP),g['loi'])    # cau moi NGAY TRUOC ket luan, ket luan van cuoi doan
            for k,v in g0['neo'].items(): self.assertEqual(g['neo'][k],v,k)                                                                      # moi neo cu giu nguyen chi so
            ws=g['loi'].split(); self.assertEqual(ws[g['neo']['bt1']],cau[0]['loi'].split()[0]); self.assertEqual(ws[g['neo']['bt2']],cau[1]['loi'].split()[0]); self.assertEqual(g['neo']['bt2'],g['neo']['bt1']+len(cau[0]['loi'].split()))
            self.assertEqual(g['loi'].split()[:len(g0['loi'].split())-len(lc.KET_LUAN_HOP.split())],g0['loi'].split()[:-len(lc.KET_LUAN_HOP.split())])    # phan truoc khong doi
            for d in doan:
                if d['k']!='gioi': self.assertNotIn('bt',d); self.assertEqual(d['loi'],next(x for x in goc if x['k']==d['k'])['loi'],d['k']) if d['k'] in ('gia','dap','han','ket') else None
    def test_so_cau_theo_do_dai_ho_so(self):      # Sol soi diff G3: ho so dai -> the xuong qua vung an toan Shorts -> giam SO CAU (nguon loi) de hinh va loi khop
        chip=lambda *h:[dict(hien=x) for x in h]; them=lambda n:dict(them=[dict()]*n)
        ngan=dict(the_loai=[1],dac_diem=chip('ROGUELIKE'),diem=dict(tb=4.5),ban=None)
        self.assertEqual(lc.so_cau_toi_da(ngan),2); self.assertEqual(lc.so_cau_toi_da(None),2)
        vua=dict(the_loai=[1],dac_diem=chip('ROGUELIKE','CHƠI CHUNG ONLINE'),diem=dict(tb=4.5),ban=them(4)); self.assertEqual(lc.so_cau_toi_da(vua),2)       # 2 chip van 1 hang (do that 1129..1177 < 1254)
        hai_hang=dict(the_loai=[1],dac_diem=chip('CHƠI CHUNG ONLINE','KHÓ KIỂU SOULS'),diem=dict(tb=4.5),ban=them(2)); self.assertEqual(lc.so_cau_toi_da(hai_hang),1)
        xau=dict(the_loai=[1],dac_diem=chip('CHƠI CHUNG ONLINE','KHÓ KIỂU SOULS'),diem=dict(tb=4.5),ban=them(4)); self.assertEqual(lc.so_cau_toi_da(xau),0)
        self.assertEqual(lc.cau_biet_truoc(BT_DU,ngay(0),'keo-thom',gt=xau),[]); self.assertEqual(len(lc.cau_biet_truoc(BT_DU,ngay(0),'keo-thom',gt=hai_hang)),1); self.assertEqual(len(lc.cau_biet_truoc(BT_DU,ngay(0),'keo-thom',gt=ngan)),2)
        self.assertEqual(len(lc.cau_biet_truoc(BT_DU,ngay(0),'keo-thom')),2)             # khong truyen gt -> nhu cu
        # moi uoc luong >= do that (do Shorts, the bat dau y 474): xau nhat 1127-474=653 <= 697; 2 chip 1 hang + 4 muc 1177-474-120 -> 583 <= 629
        self.assertGreaterEqual(lc.uoc_cao_ho_so(xau),653); self.assertGreaterEqual(lc.uoc_cao_ho_so(vua),583)
    def test_kich_ban_ho_so_dai_giam_so_cau(self):
        ban=dict(ten='Deluxe Edition',ten_noi='Deluxe',them=[dict(k='vu_khi',so=2,noi='hai vũ khí',hien='2 vũ khí'),dict(k='trang_phuc',noi='trang phục',hien='trang phục'),dict(k='mo_rong',noi='gói mở rộng',hien='gói mở rộng'),dict(k='tien',noi='tiền trong game',hien='tiền trong game')],dung_som=False,them_goc=[])
        co=dict(k='co_op_online',noi='chơi chung online được',hien='CHƠI CHUNG ONLINE'); so=dict(k='souls',noi='khó kiểu Souls',hien='KHÓ KIỂU SOULS'); rg=dict(k='roguelike',noi='roguelike, chết là chơi lại từ đầu',hien='ROGUELIKE')
        for dd,ban_,n in (([rg],None,2),([rg,co],ban,2),([co,so],dict(ban,them=ban['them'][:2]),1),([co,so],ban,0)):
            doan,loi=chay_kich_ban_bt(ngay(0),'keo-thom',BT_DU,diem=D(4.5,3000),ban=ban_,dac_diem=dd); g=next(d for d in doan if d['k']=='gioi')
            self.assertEqual(len(g.get('bt',[])),n,(dd,n)); self.assertTrue(g['loi'].endswith(lc.KET_LUAN_DANG_MUA))
            self.assertEqual('bt1' in g['neo'],n>=1); self.assertEqual('bt2' in g['neo'],n>=2)
    def test_thieu_bang_chung_thi_kich_ban_nhu_cu_khong_co_bt(self):
        goc,loi0=chay_kich_ban_bt(ngay(0),'keo-thom',None,diem=D(4.37,3000))
        for bt in (dict(online='tuy_chon',can_plus_online=None),dict(screenLanguages=None),{}):
            doan,loi=chay_kich_ban_bt(ngay(0),'keo-thom',bt,diem=D(4.37,3000)); self.assertEqual(loi,loi0); g=next(d for d in doan if d['k']=='gioi'); self.assertNotIn('bt',g); self.assertNotIn('bt1',g['neo'])
    def test_mot_cau_chi_neo_bt1(self):
        doan,_=chay_kich_ban_bt(ngay(0),'keo-thom',dict(screenLanguages=['vi','en']),diem=D(4.5,500)); g=next(d for d in doan if d['k']=='gioi')
        self.assertEqual(g['bt'],['phu_de']); self.assertIn('bt1',g['neo']); self.assertNotIn('bt2',g['neo']); self.assertTrue(g['loi'].endswith(lc.CAU_PHU_DE_CO+' '+lc.KET_LUAN_DANG_MUA))
    def test_ky_vong_d3_tinh_lai_tu_keo_json_khong_tin_kich_ban(self):
        self.assertEqual(lc.biet_truoc_ky_vong(BT_DU,['phu_de','online','so_nguoi']),[('phu_de','chua'),('ps_plus','tuy_chon'),('so_nguoi',16)])
        self.assertEqual(lc.biet_truoc_ky_vong(dict(screenLanguages=['vi']),['phu_de']),[('phu_de','co')])
        self.assertEqual(lc.biet_truoc_ky_vong({},['phu_de','online','so_nguoi','la']),[('phu_de',None),('ps_plus',None),('so_nguoi',None),('la',None)])    # kich-ban doc cau ma keo.json thieu -> None -> D3 truot
        self.assertEqual(lc.biet_truoc_ky_vong(BT_DU,None),[])
    def test_the_hinh_khop_cau_da_doc(self):
        self.assertEqual(lc.the_biet_truoc(BT_DU,['phu_de','online','so_nguoi']),['PHỤ ĐỀ VIỆT ✗','ONLINE CẦN PS PLUS','TỐI ĐA 16 NGƯỜI ONLINE'])
        self.assertEqual(lc.the_biet_truoc(dict(screenLanguages=['vi'],online='bat_buoc',can_plus_online=True),['online','phu_de']),['PHẢI ONLINE + PS PLUS','PHỤ ĐỀ VIỆT ✓'])
        self.assertEqual(lc.the_biet_truoc({},['phu_de','x']),['?phu_de','?x']); self.assertEqual(lc.the_biet_truoc(BT_DU,None),[])
    def test_full_html_co_the_theo_cau_da_doc_va_moc_bt(self):
        h=(T/'full.html').read_text(encoding='utf-8')
        for cu in ('id="gtT1"','id="gtT2"','id="gtT3"','function theBT()',"d.k==='gioi'",'GT.T[gi]',"G_['bt'+i]","'PHỤ ĐỀ VIỆT '","'ONLINE CẦN PS PLUS'","'PHẢI ONLINE + PS PLUS'","'TỐI ĐA '+X.so_nguoi_online+' NGƯỜI ONLINE'"): self.assertIn(cu,h,cu)
        k=(T/'kiem'/'kiem-dom.cjs').read_text(encoding='utf-8')
        for cu in ('"#gtT1"','gioi.the_bt','chongGT'): self.assertIn(cu,k,cu)
        for ten in ('M.gioi.e','TA.ra3'): self.assertIn(ten,h)
    def test_chon_keo_lay_biet_truoc_tu_vung_re_nhat_khong_bu(self):
        src=(T/'chon-keo.py').read_text(encoding='utf-8')
        a=src.index('def doc_trang('); b=src.index('def kiem_ung_vien('); GTm=types.SimpleNamespace(**{n:getattr(GTMOD,n) for n in ('khoi_gia','media','ps_plus_catalog','thong_tin_game','biet_truoc')})
        g=dict(GT=GTm); exec(src[a:b],g)
        from_us=GTMOD_trang(['en','es']); from_hk=GTMOD_trang(['vi','en','zh'])
        us=g['doc_trang'](from_us,PID_SNIPER); hk=g['doc_trang'](from_hk,PID_SNIPER)
        self.assertEqual(us['biet_truoc']['screenLanguages'],['en','es']); self.assertEqual(hk['biet_truoc']['screenLanguages'],['vi','en','zh'])    # moi trang giu ngon ngu cua CHINH no
        i=src.index("tr[0]['biet_truoc']=dict("); dong=src[i:src.index('\n',i)]
        self.assertIn("tr[0]['biet_truoc']",dong); self.assertIn("nguon=dict(loc=LOC[v3[0]['ma']],pid=v3[0]['id'])",dong); self.assertNotIn('tr[1]',dong); self.assertNotIn('tr[2]',dong)
        self.assertIn("biet_truoc=tr[0]['biet_truoc'],han=dict(",src)
