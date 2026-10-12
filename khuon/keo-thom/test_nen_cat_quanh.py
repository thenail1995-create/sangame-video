"""12/10: nen08.cat_quanh chi cat quanh khung phang, giu phan sang hai ben (khong bo ca doan)."""
import ast, pathlib, unittest
SRC = pathlib.Path(__file__).with_name('nen08.py').read_text(encoding='utf-8')
_ns = {}
for node in ast.parse(SRC).body:
    if isinstance(node, ast.FunctionDef) and node.name == 'cat_quanh':
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'nen08', 'exec'), _ns)
cat_quanh = _ns['cat_quanh']

class CatQuanh(unittest.TestCase):
    P = [dict(src='a.mp4', s0=20.0, len=30.0, cr=None), dict(src='b.mp4', s0=0.0, len=5.0, cr=None)]
    def test_giu_hai_ben(self):
        r = cat_quanh(self.P, [('a.mp4', 29.93)])
        a = [p for p in r if p['src'] == 'a.mp4']
        self.assertEqual(len(a), 2)
        self.assertAlmostEqual(a[0]['s0'] + a[0]['len'], 29.33, places=2)
        self.assertAlmostEqual(a[1]['s0'], 30.53, places=2)
        self.assertTrue(all(not (p['s0'] < 29.93 < p['s0'] + p['len']) for p in a))
    def test_khong_dung_doan_khac(self):
        r = cat_quanh(self.P, [('a.mp4', 29.93)])
        self.assertIn(dict(src='b.mp4', s0=0.0, len=5.0, cr=None), r)
    def test_bo_manh_qua_ngan(self):
        r = cat_quanh([dict(src='a.mp4', s0=0.0, len=1.5, cr=None)], [('a.mp4', 0.7)])
        self.assertEqual(r, [])
    def test_nhieu_khung(self):
        r = cat_quanh(self.P, [('a.mp4', 29.93), ('a.mp4', 44.84)])
        self.assertTrue(all(not (p['s0'] < t < p['s0'] + p['len']) for p in r for t in (29.93, 44.84) if p['src'] == 'a.mp4'))
        self.assertGreater(sum(p['len'] for p in r if p['src'] == 'a.mp4'), 25)
