# Test G2 (13/10, Sol #1-#3): cau mo Tin nhanh mo bang DEAL THAT (tin.json.mo_du_lieu) + `ket` moi + kiem khong con doi doc ngay trong mo.
#   uv run --frozen python -m pytest khuon/tin-nhanh/test_cau_mo.py -q       (chay script trong thu muc tam; khong mang, khong Whisper)
import datetime as dtm,json,pathlib,re,shutil,subprocess,sys,tempfile,unittest
T=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(T.parents[1]/'cong-cu')); import nghe_so as ns
VN=dtm.timezone(dtm.timedelta(hours=7))
END=int(dtm.datetime(2026,10,14,23,59,tzinfo=VN).timestamp()*1000)
def tin(kieu='giam-sau',gia=288000,giam=85,ten_doc='Star Wars Jedi Survivor'):
    return dict(kieu=kieu,khoa=f'{kieu}:x',mau='do',loai='GIẢM SÂU',nguon='PS STORE · 12/10',n=8,cum='giảm sâu',giam_min=50,giam_max=giam,
        re_nhat=dict(ten='Star Wars Jedi: Survivor',ten_hien='Star Wars Jedi: Survivor',ten_doc=ten_doc,gia_vnd=gia,gia='288.000đ',giam=giam,vung='Hồng Kông',ma='HK',
                     khoa='k',pid='UP0001-PPSA00000_00-X',loc='en-hk',end=END,gia_cuc_bo=14.9,tien_te='HKD'),
        nhan_dong='RẺ NHẤT · STORE HỒNG KÔNG',anh_url=['u'],anh_tep=['tai-san/a.jpg'],trailer=[],anh_chup=[],kiem_lai=[])
def tin_xanh():
    return dict(kieu='ps-plus-thang',khoa='ps-plus-thang:x',mau='xanh',loai='PS PLUS',nguon='PLAYSTATION SG · 12/10',n_moi=2,ten_game=['Game A','Game B'],ten_doc=['Game A','Game B'],ten_noi=['Game A','Game B'],
        anh_url=['u'],anh_tep=['tai-san/b.jpg'],nhan_dong='PS PLUS THÁNG NÀY',trailer=[],anh_chup=[])
def chay(tins,ngay='2026-10-13'):
    """sinh-tin.py -> tin.json, roi kich-ban.py -> kich-ban.json (cung thu muc tam, khong ghi vao cay git)."""
    with tempfile.TemporaryDirectory() as d:
        d=pathlib.Path(d)
        for f in ('sinh-tin.py','kich-ban.py','so_chu.py','ten-ngoai-le.json'): shutil.copy(T/f,d/f)
        (d/'tin-chon.json').write_text(json.dumps(dict(ngay_dang=ngay,ngay_dung='2026-10-12',sha_du_lieu='x',du_lieu_cap_nhat='2026-10-12',tin=tins),ensure_ascii=False),encoding='utf-8')
        r=subprocess.run([sys.executable,str(d/'sinh-tin.py'),str(d/'tin-chon.json')],capture_output=True,text=True,cwd=d); assert r.returncode==0,r.stdout+r.stderr
        j=json.load(open(d/'tin.json',encoding='utf-8'))
        r=subprocess.run([sys.executable,'-I',str(d/'kich-ban.py')],capture_output=True,text=True,cwd=d); assert r.returncode==0,r.stdout+r.stderr
        return j,{x['k']:x['loi'] for x in json.load(open(d/'kich-ban.json',encoding='utf-8'))}
def kich_ban_tu(tj):    # chi kich-ban.py voi tin.json cho san (kiem du lieu thieu/sai kieu)
    with tempfile.TemporaryDirectory() as d:
        d=pathlib.Path(d)
        for f in ('kich-ban.py','so_chu.py','ten-ngoai-le.json'): shutil.copy(T/f,d/f)
        (d/'tin.json').write_text(json.dumps(tj,ensure_ascii=False),encoding='utf-8')
        r=subprocess.run([sys.executable,'-I',str(d/'kich-ban.py')],capture_output=True,text=True,cwd=d); assert r.returncode==0,r.stdout+r.stderr
        return {x['k']:x['loi'] for x in json.load(open(d/'kich-ban.json',encoding='utf-8'))}

class MoTinNhanh(unittest.TestCase):
    def test_mo_du_lieu_va_loi_mo(self):
        j,kb=chay([tin_xanh(),tin()])
        self.assertEqual(j['mo_du_lieu'],dict(ten_doc='Star Wars Jedi Survivor',gia_vnd=288000,giam=85))
        self.assertEqual(kb['mo'],'Star Wars Jedi Survivor còn hai trăm tám mươi tám nghìn, giảm tám mươi lăm phần trăm, sáng nay PS Store có deal mới nè!')
    def test_khong_ten_kenh_khong_ngay_khong_chu_so_trong_mo(self):
        j,kb=chay([tin()]); mo=kb['mo'].lower()
        self.assertNotIn('săn game',mo); self.assertNotIn(j['ngay_doc'].lower(),mo); self.assertNotIn('bản tin sáng',mo); self.assertIsNone(re.search(r'\d',kb['mo']))
    def test_thieu_muc_giam_sau_thi_mo_chung(self):
        j,kb=chay([tin_xanh(),tin(kieu='deal-hot')]); self.assertIsNone(j['mo_du_lieu'])
        self.assertEqual(kb['mo'],'Sáng nay PS Store có deal mới nè anh em!')
    def test_du_lieu_mo_thieu_hoac_sai_kieu_thi_mo_chung(self):
        j,_=chay([tin()]); chung='Sáng nay PS Store có deal mới nè anh em!'
        for md in (None,{},dict(ten_doc='X',gia_vnd=288000),dict(ten_doc='',gia_vnd=288000,giam=85),dict(ten_doc='X',gia_vnd='288000',giam=85),dict(ten_doc='X',gia_vnd=288000,giam=0),dict(ten_doc='X',gia_vnd=0,giam=85),'x'):
            self.assertEqual(kich_ban_tu(dict(j,mo_du_lieu=md))['mo'],chung,md)
        tj=dict(j); tj.pop('mo_du_lieu'); self.assertEqual(kich_ban_tu(tj)['mo'],chung)       # tin.json cu (fixture truoc 13/10)
    def test_sinh_tin_khong_nhan_giam_khong_hop_le(self):
        j,_=chay([tin(giam=0)]); self.assertIsNone(j['mo_du_lieu'])
    def test_ket_moi(self):
        _,kb=chay([tin()]); self.assertEqual(kb['ket'],'Theo dõi Săn Game để không lỡ kèo nào nha!'); self.assertNotIn('chấm com',kb['ket'])
    def test_mo_dung_nguoc_gia_tri_d3(self):          # D3 doc cau mo theo GIA TRI: tien + % phai nghe duoc; sai tien / thieu % -> loi (doi_chieu cua nghe_so.py)
        _,kb=chay([tin()])
        self.assertEqual(ns.doi_chieu(kb['mo'],tien=[288000],phan_tram=[85],ten=['Star Wars Jedi Survivor'],kiem_ten=False),[])
        self.assertTrue(ns.doi_chieu('Star Wars Jedi Survivor còn hai trăm tám mươi tám nghìn, giảm tám mươi lăm phần trăm',tien=[388000],phan_tram=[85],ten=['Star Wars Jedi Survivor'],kiem_ten=False))
        self.assertTrue(ns.doi_chieu('Star Wars Jedi Survivor còn hai trăm tám mươi tám nghìn, sáng nay PS Store có deal mới nè',tien=[288000],phan_tram=[85],ten=['Star Wars Jedi Survivor'],kiem_ten=False))

class KiemKhongDoiDocNgayTrongMo(unittest.TestCase):
    SRC=(T/'kiem'/'kiem-tat-ca.py').read_text(encoding='utf-8')
    def test_bo_dieu_kien_doc_ngay_trong_mo(self):
        self.assertNotIn("if sc.ngay_doc(exp) not in KB['mo']",self.SRC)                  # dieu kien cu (bat buoc doc ngay) da go
        self.assertIn("sai_ngay.append(f\"loi mo van mo bang ten kenh/ngay",self.SRC)    # thay bang phep CAM khuon cu
    def test_van_kiem_ngay_tren_giay_hinh_va_tin_json(self):                              # GIU kiem ngay du lieu + giay
        for s in ("TJ['ngay_dang']!=exp.isoformat()","giay dau trang '{n1}'","giay cuoi '{n6}'","B6 ngay du lieu (tin.json)"): self.assertIn(s,self.SRC)
    def test_d3_cho_mo_co_ten_tien_phan_tram(self):
        for s in ("MO_DL=TJ.get('mo_du_lieu')","cs['mo']=","phan_tram=[MO_DL['giam']]","tien=[MO_DL['gia_vnd']]","NS.ten_hai_bo(MO_DL['ten_doc']"): self.assertIn(s,self.SRC)
    def test_khoi_cam_mo_chay_that(self):             # chay dung dong cam: loi mo cu (ten kenh / ngay) bi bat, loi mo moi khong bi
        a=self.SRC.index("if 'săn game' in KB['mo'].lower()"); b=self.SRC.index('\n',a)
        class SC:
            @staticmethod
            def ngay_doc(d): return 'Thứ Ba mười ba tháng mười'
        def cam(mo):
            g=dict(KB=dict(mo=mo),sc=SC,exp=None,sai_ngay=[]); exec(self.SRC[a:b],g); return g['sai_ngay']
        self.assertTrue(cam('[excited] Bản tin sáng Săn Game, Thứ Ba mười ba tháng mười!')); self.assertTrue(cam('Hôm nay Thứ Ba mười ba tháng mười có deal'))
        self.assertFalse(cam('Star Wars Jedi Survivor còn hai trăm tám mươi tám nghìn, giảm tám mươi lăm phần trăm, sáng nay PS Store có deal mới nè!'))

class HinhCuoi(unittest.TestCase):
    HTML=(T/'full.html').read_text(encoding='utf-8')
    def test_hinh_cuoi_go_ten_kenh_theo_tu_khong_theo_vi_tri_cu(self):
        self.assertIn("var KENH='@sangamecomvn'",self.HTML); self.assertIn('Theo dõi Săn Game</div>',self.HTML)
        for cu in ("'sangame'.slice","'.com'.slice","'.vn'.slice","ws[iS+3]","ws[iS+5]","Mai lại có bản tin mới nhé"): self.assertNotIn(cu,self.HTML)
        self.assertIn("/^để$/i",self.HTML)     # moc go chu bat dau o chu `de`, theo TU trong loi

if __name__=='__main__': unittest.main()
