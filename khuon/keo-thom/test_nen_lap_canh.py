"""14/10: nen08.lay xep canh trailer: canh dung lai ('lap') cach lan dung truoc >= 10 s tren dong thoi gian, uu tien doan goc truoc; khong xep duoc thi giu hanh vi cu (khong dung). Ham thuan, khong goi ffmpeg."""
import ast, pathlib, unittest
SRC = pathlib.Path(__file__).with_name('nen08.py').read_text(encoding='utf-8')
_ns = {'SystemExit': SystemExit}
for node in ast.parse(SRC).body:
    if (isinstance(node, ast.FunctionDef) and node.name in ('lay', 'trung_canh')) or (isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') == 'CACH_LAP'):
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'nen08', 'exec'), _ns)
lay, trung_canh = _ns['lay'], _ns['trung_canh']

def P(src, s0, ln, lap=False):
    d = dict(src=src, s0=s0, len=ln, cr=None)
    if lap: d['lap'] = True
    return d
def xep(khe, pool):
    dung = []; ds = {}
    for i in sorted(range(len(khe)), key=lambda i: -khe[i][1]):
        a, D = khe[i]; ds[i] = lay(D, pool, a=a, dung=dung)
    return ds, dung

class LapCanh(unittest.TestCase):
    def test_trung_canh(self):
        dung = [('a', 0.0, 8.0, 0.0, 8.0)]
        self.assertTrue(trung_canh(dung, 'a', 0.0, 8.0, 8.0))        # cung s0 liền nhau
        self.assertTrue(trung_canh(dung, 'a', 5.0, 4.0, 17.9))       # chong hinh, cach 9,9 s
        self.assertFalse(trung_canh(dung, 'a', 0.0, 8.0, 18.0))      # cach dung 10 s
        self.assertFalse(trung_canh(dung, 'b', 0.0, 8.0, 8.0))       # nguon khac
        self.assertFalse(trung_canh(dung, 'a', 8.3, 4.0, 8.0))       # khong chong hinh (doan con lai)
    def test_lap_cach_ra_va_goc_truoc(self):
        pool = [P('A', 0, 8), P('B', 0, 8), P('B', 0, 8, True), P('A', 0, 8, True)]    # ban lap B dung truoc ban lap A: cach ngay chon B se sai
        ds, dung = xep([(0, 8), (9, 8), (18, 8)], pool)
        dung_thu_tu = sorted(dung, key=lambda u: u[3])
        self.assertEqual([u[0] for u in dung_thu_tu], ['A', 'B', 'A'])      # 2 khe dau dung doan GOC, khe 3 dung lai A (B vua dung 1 s truoc)
        for i, u in enumerate(dung_thu_tu):
            for v in dung_thu_tu[i + 1:]:
                if u[0] == v[0]: self.assertGreaterEqual(v[3] - u[4], 10.0 - 1e-9)
    def test_dung_het_goc_truoc_khi_lap(self):
        pool = [P('A', 0, 8, True), P('A', 0, 8), P('B', 0, 8), P('B', 0, 8, True)]
        ds, dung = xep([(0, 8), (20, 8), (40, 8)], pool)
        self.assertEqual(sorted(u[0] for u in dung[:2]), ['A', 'B'])     # hai khe dau = hai goc, khong lap
        self.assertEqual(len(ds[2]), 1)
    def test_khong_xep_duoc_thi_giu_hanh_vi_cu(self):      # chi 1 goc + ban lap, 2 khe sat nhau: khong the cach 10 s -> van dung lai (khong dung, khong loi)
        pool = [P('A', 0, 8), P('A', 0, 8, True)]
        ds, dung = xep([(0, 8), (8, 8)], pool)
        self.assertEqual(sum(d for v in ds.values() for _, _, d, *_ in v), 16.0)
    def test_khe_dai_hai_manh_cung_s0_khong_lien_nhau_neu_tranh_duoc(self):
        pool = [P('A', 0, 8), P('B', 0, 8), P('A', 0, 8, True)]
        ds, dung = xep([(0, 16)], pool)
        self.assertEqual([u[0] for u in sorted(dung, key=lambda u: u[3])], ['A', 'B'])      # 16 s = goc A + goc B, khong A + A
    def test_khong_lap_hanh_vi_nhu_cu(self):      # pool chi goc: chon vua khit nhat nhu truoc
        pool = [P('A', 0, 12), P('B', 0, 6), P('C', 0, 3.2)]
        out = lay(3.2, pool)
        self.assertEqual((out[0][0], out[0][2]), ('C', 3.2))
        out = lay(20, [P('A', 0, 12), P('B', 0, 9)])
        self.assertEqual([(o[0], o[2]) for o in out], [('A', 12), ('B', 8.0)])
    def test_het_doan_thi_thoat(self):
        with self.assertRaises(SystemExit): lay(5, [])

if __name__ == '__main__': unittest.main()


class SolVuaKhit(unittest.TestCase):
    def test_manh_ngan_vua_khit_van_dung(self):   # Sol soi diff bt2: khe [5.5, 0.8], pool [5, .5, .5, .5, .9] -> ban cu xep duoc; ban moi tung SystemExit
        pool=[P('a',0,5.0),P('b',0,0.5),P('c',0,0.5),P('d',0,0.5),P('e',0,0.9)]
        ds,_=xep([(0.0,5.5),(5.5,0.8)],pool)
        self.assertAlmostEqual(sum(x[2] for x in ds[0]),5.5,places=2); self.assertAlmostEqual(sum(x[2] for x in ds[1]),0.8,places=2)
