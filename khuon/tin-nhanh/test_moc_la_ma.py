# Test D3 moc tin vang co so La Ma (14/10, Tin nhanh 15/10 run 38598718701): moc «spec IV», giong doc 'bốn', Whisper viet «Specs 4» -> phai DAT;
# doc sai so (Whisper «Specs 3») van phai TRUOT. Chay dung dong code trong kiem-tat-ca.py (khong Whisper, khong mang).
#   uv run --frozen python -m pytest khuon/tin-nhanh/test_moc_la_ma.py -q
import difflib,pathlib,re,sys,unittest
T=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(T.parents[1]/'cong-cu')); sys.path.insert(0,str(T)); import nghe_so as NS, so_chu as sc
SRC=(T/'kiem'/'kiem-tat-ca.py').read_text(encoding='utf-8')
def _lay(dau,cuoi):
    a=SRC.index(dau); return SRC[a:SRC.index(cuoi,a)]
G={'re':re,'difflib':difflib,'NS':NS,'sc':sc}
exec(_lay('def dau_hieu(','def _diem_ten('),G)
exec(_lay('_lm=lambda','\n',),G)
def diem(nghe,moc):
    return G['dau_hieu'](sc.chuan_so_sanh(G['_lm'](nghe)),sc.chuan_so_sanh(G['_lm'](moc)),'mem')

class MocLaMa(unittest.TestCase):
    def test_spec_iv_nghe_specs_4_dat(self):
        self.assertGreaterEqual(diem('Tin 3, Part 1 miễn phí, tay cầm GT, bán 10 tháng 12, Specs 4.','spec IV'),0.75)
    def test_whisper_viet_la_ma_van_dat(self):
        self.assertGreaterEqual(diem('Tin 3, tay cầm GT, Spec IV.','spec IV'),0.75)
    def test_nghe_sai_so_truot(self):
        self.assertLess(diem('Tin 3, tay cầm GT, Specs 3.','spec IV'),0.75)
    def test_kiem_dung_ban_da_doi(self):
        self.assertIn("heard_mem=sc.chuan_so_sanh(_lm(nghe_raw))",SRC)
        self.assertIn("dau_hieu(heard_mem,sc.chuan_so_sanh(_lm(ng)),'mem')",SRC)

if __name__=='__main__': unittest.main()
