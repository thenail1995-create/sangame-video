"""03/11 Top 5 (run 41574060674): 'Dung 1 hang sang o moi khung cham' bao 8 sai du hinh dung. Nguyen nhan: kiem-dom.cjs luu bang do bang OBJECT khoa theo thoi diem t;
khi t la so nguyen (vd c.b-0,3 = 24.0 -> khoa "24") JS dua khoa nguyen len DAU object -> kiem-tat-ca.py (doc theo thu tu j) so moc 24.0 voi 'mo' (mong 0 hang), v.v.
Sua: out.bang la MANG [t, {...}] theo thu tu moc. Test: (1) nguon kiem-dom.cjs khong con gan out.bang[t]=...; (2) doi chung: object JS that su dao thu tu; (3) dong doc `bang=` trong
kiem-tat-ca.py giu thu tu mang kieu 'khong nguyen truoc, 24 giua'.  (Khong chay trinh duyet: khong mang, khong Playwright.)"""
import ast, json, pathlib, shutil, subprocess, unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
CJS = ROOT / 'khuon/top5/kiem/kiem-dom.cjs'
KIEM = ROOT / 'khuon/top5/kiem/kiem-tat-ca.py'


class ThuTuMocBang(unittest.TestCase):
    def test_kiem_dom_xuat_bang_la_mang_khong_phai_object(self):
        src = CJS.read_text(encoding='utf-8')
        self.assertIn('out.bang=[]', src.replace(' ', ''))
        self.assertIn('out.bang.push(', src)
        self.assertNotIn('out.bang[t]', src, 'object khoa theo t: khoa so nguyen ("24") bi JS dua len dau')

    @unittest.skipUnless(shutil.which('node'), 'can node')
    def test_doi_chung_object_js_dao_thu_tu_khoa_nguyen(self):
        mocs = [1.8, 8.32, 14.95, 18.77, 24.0, 28.44, 35.01]       # chinh la MOC_DUNG cua run 41574060674
        r = subprocess.run(['node', '-e', f'const o={{}};for(const t of {json.dumps(mocs)})o[t]=1;const a=[];for(const t of {json.dumps(mocs)})a.push([t,1]);'
                            'console.log(JSON.stringify([Object.keys(o),a.map(x=>x[0])]))'], capture_output=True, text=True, check=True)
        obj, mang = json.loads(r.stdout)
        self.assertEqual(obj[0], '24', 'doi chung: object dua khoa nguyen len dau (day la nguyen nhan loi)')
        self.assertEqual(mang, mocs, 'mang giu nguyen thu tu moc')

    def test_kiem_tat_ca_doc_bang_giu_thu_tu_mang(self):
        tree = ast.parse(KIEM.read_text(encoding='utf-8'))
        dong = next(n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'bang' for t in n.targets))
        d = {'bang': [[1.8, 'mo'], [8.32, 'h5'], [24, 'h2'], [28.44, 'h1']]}
        ns = {'d': d}
        exec(compile(ast.Module(body=[dong], type_ignores=[]), 'kiem-tat-ca.py', 'exec'), ns)
        self.assertEqual([t for t, _ in ns['bang']], [1.8, 8.32, 24, 28.44])


if __name__ == '__main__': unittest.main()
