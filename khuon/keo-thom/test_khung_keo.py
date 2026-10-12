# Test 12/10: 3 khung Keo (keo-thom-2 15:00 · keo-thom 20:00 · keo-thom-3 22:00) dung chung khuon keo-thom.
#  - cum mo `loi_chu.cum_mo` (khac nhau giua 3 khung, khac hom truoc, khong chua `đang`, giu khoa `em`, chay duoc nhanh D3 tim `đang`)
#  - chon-keo.py: lich su chung MOI khung, co_hom_nay chi DUNG tag khung dang chay, gio dang/han toi thieu theo khung
import datetime,json,os,pathlib,re,subprocess,sys,tempfile,types,unittest
T=pathlib.Path(__file__).resolve().parent; sys.path.insert(0,str(T))
import loi_chu as lc
KHUNG=('keo-thom-2','keo-thom','keo-thom-3')
def ngay(i): return (datetime.date(2026,10,13)+datetime.timedelta(days=i)).isoformat()
def chay_kich_ban(ngay_dang,dang):
    """Chay kich-ban.py that tren keo.json mau (thu muc tam) -> kich-ban.json dict."""
    keo=dict(ngay_dang=ngay_dang,game=dict(ten='Returnal',giam=75),goc_vnd=1650000,con_vnd=412000,
             vung=[dict(ma='US',vnd=412000),dict(ma='HK',vnd=520000),dict(ma='SG',vnd=600000)],han=dict(endTime=int(datetime.datetime(2026,10,20,12,0,tzinfo=datetime.timezone.utc).timestamp()*1000)),
             gioi_thieu=dict(the_loai=[dict(vi='hành động')],dac_diem=[dict(noi='bắn súng góc nhìn thứ ba')],diem=None,ban=None))
    with tempfile.TemporaryDirectory() as d:
        d=pathlib.Path(d)
        for f in ('kich-ban.py','loi_chu.py'): (d/f).write_text((T/f).read_text(encoding='utf-8'),encoding='utf-8')
        (d/'keo.json').write_text(json.dumps(keo,ensure_ascii=False),encoding='utf-8')
        env=dict(os.environ); env.pop('DANG',None)
        if dang: env['DANG']=dang
        r=subprocess.run([sys.executable,str(d/'kich-ban.py'),str(d/'keo.json')],capture_output=True,text=True,cwd=d,env=env)
        if r.returncode: raise AssertionError(r.stderr[-800:]+r.stdout[-300:])
        return json.load(open(d/'kich-ban.json'))['doan'],(d/'loi.txt').read_text(encoding='utf-8')

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
                doan,loi=chay_kich_ban(ngay(i),k); mo=doan[0]; ws=mo['loi'].split(); neo=mo['neo']
                cum=lc.cum_mo(ngay(i),k); n=len(cum.split()); da.add(cum)
                self.assertEqual(' '.join(ws[:n]),cum); self.assertEqual(ws[neo['em']].lower().strip('!'),'em'); self.assertEqual(neo['ten'],n)
                for kh in ('ten','giam','ps','vung','em'): self.assertIn(kh,neo,kh)
                i1=next(j for j,w in enumerate(ws) if w.lower()=='đang')    # = D3 kiem-tat-ca.py:231
                self.assertGreater(i1,neo['ten']); self.assertEqual(ws[i1+1],'giảm'); self.assertEqual(neo['giam'],i1+1); self.assertEqual(ws[-1],'nè!')
                self.assertEqual(sum(1 for w in ws[:neo['ten']] if w.lower()=='đang'),0)
                for d in doan[1:]: self.assertNotIn('Ê anh',d['loi'])
        self.assertEqual(da,set(lc.CUM_MO))    # tat ca cum da chay qua kich-ban.py
    def test_khung_goc_khong_env_giu_nguyen(self):
        doan,loi=chay_kich_ban(ngay(0),None); self.assertTrue(loi.startswith('[excited] Ê anh em!! Returnal đang giảm'),loi[:80]); self.assertEqual(doan[0]['neo']['em'],2)

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
