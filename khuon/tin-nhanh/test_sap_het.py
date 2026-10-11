# Test the SAP HET GIAM: loi doc + kiem.han (sinh-tin.py chay trong thu muc tam, khong ghi vao cay git) va D3 doc ngay (cong-cu/nghe_so.py).
#   uv run --frozen python -m pytest khuon/tin-nhanh/test_sap_het.py -q
import datetime as dtm,json,pathlib,shutil,subprocess,sys,tempfile,unittest
T=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(T.parents[1]/'cong-cu')); import nghe_so as ns
VN=dtm.timezone(dtm.timedelta(hours=7))
END=int(dtm.datetime(2026,10,14,23,59,tzinfo=VN).timestamp()*1000)    # het giam 14/10 (gio VN)
def tin(kieu='sap-het'):
    return dict(kieu=kieu,khoa=f'{kieu}:x',mau='do',loai='SẮP HẾT GIẢM',nguon='PS STORE · 11/10',n=7,cum='sắp hết giảm',giam_min=40,giam_max=70,
        re_nhat=dict(ten='Resident Evil Requiem',ten_hien='Resident Evil Requiem',ten_doc='Resident Evil Requiem',gia_vnd=288000,gia='288.000đ',giam=60,vung='Singapore',ma='SG',
                     khoa='k',pid='UP0001-PPSA00000_00-X',loc='en-sg',end=END,gia_cuc_bo=14.9,tien_te='SGD'),
        nhan_dong='RẺ NHẤT · STORE SINGAPORE',anh_url=['u'],anh_tep=['tai-san/a.jpg'],trailer=[],anh_chup=[],kiem_lai=[])
def chay(tins):
    with tempfile.TemporaryDirectory() as d:
        d=pathlib.Path(d)
        for f in ('sinh-tin.py','so_chu.py','ten-ngoai-le.json'): shutil.copy(T/f,d/f)
        (d/'tin-chon.json').write_text(json.dumps(dict(ngay_dang='2026-10-12',ngay_dung='2026-10-11',sha_du_lieu='x',du_lieu_cap_nhat='2026-10-11',tin=tins),ensure_ascii=False),encoding='utf-8')
        r=subprocess.run([sys.executable,str(d/'sinh-tin.py'),str(d/'tin-chon.json')],capture_output=True,text=True,cwd=d)
        return r,(json.load(open(d/'tin.json',encoding='utf-8')) if (d/'tin.json').exists() else None)
class SinhTinSapHet(unittest.TestCase):
    def test_loi_va_kiem_han(self):
        r,j=chay([tin()]); self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        g=j['tin'][0]
        self.assertEqual(g['loi'],'Tin một: bảy game bán chạy sắp hết giảm. Rẻ nhất Resident Evil Requiem, giảm sáu mươi phần trăm, hai trăm tám mươi tám nghìn ở store Singapore, hết giảm ngày mười bốn tháng mười.')
        self.assertEqual(g['kiem']['han'],'2026-10-14'); self.assertEqual(g['tit'],'7 game bán chạy sắp hết giảm')
        self.assertIn(', hai trăm tám mươi tám nghìn',g['loi'])    # dau phay truoc gia giu nguyen
    def test_thang_tu_va_gio_vn(self):                        # 21:00 UTC 30/09 = 04:00 VN 01/10 ; thang 4 doc 'tư'
        e=int(dtm.datetime(2026,4,9,20,0,tzinfo=dtm.timezone.utc).timestamp()*1000)    # 03:00 VN 10/04
        x=tin(); x['re_nhat']['end']=e; r,j=chay([x]); g=j['tin'][0]
        self.assertTrue(g['loi'].endswith('hết giảm ngày mười tháng tư.')); self.assertEqual(g['kiem']['han'],'2026-04-10')
    def test_the_giam_sau_khong_co_han(self):
        x=tin('giam-sau'); x['cum']='giảm sâu'; r,j=chay([x]); g=j['tin'][0]
        self.assertNotIn('han',g['kiem']); self.assertNotIn('hết giảm',g['loi'])
class DocNgayD3(unittest.TestCase):
    def test_doc_ngay(self):
        self.assertEqual(ns.doc_ngay('hết giảm ngày mười bốn tháng mười.'),[(14,10)])
        self.assertEqual(ns.doc_ngay('hết giảm ngày 21 tháng 10'),[(21,10)]); self.assertEqual(ns.doc_ngay('ngày 21/10'),[(21,10)])
        self.assertEqual(ns.doc_ngay('hết giảm ngày mười tháng tư'),[(10,4)])
        self.assertEqual(ns.doc_ngay('hai mươi mốt'),[])
    def test_d3_nghe_dung_ngay(self):
        self.assertEqual(ns.doi_chieu('hết giảm ngày mười bốn tháng mười',ngay=[(14,10)]),[])
    def test_d3_nghe_sai_ngay_truot(self):
        for sai in ('hết giảm ngày mười lăm tháng mười','hết giảm ngày mười bốn tháng chín','hết giảm'):
            l=ns.doi_chieu(sai,ngay=[(14,10)]); self.assertTrue(l and l[0].startswith('NGAY'),(sai,l))
    def test_so_gia_tri_khong_so_chu(self):                    # '14 tháng 10' khop (14,10); '1' va '4' roi rac khong khop
        self.assertEqual(ns.doi_chieu('ngày 14 tháng 10',ngay=[(14,10)]),[])
        self.assertTrue(ns.doi_chieu('ngày một tháng bốn mười',ngay=[(14,10)]))
if __name__=='__main__': unittest.main()
