"""Dot 2a (B, F): dieu phoi cong-cu/tu-sua-moc.sh (can_chu_tu_sua) voi can-chu.py va kiem_moc.py GIA (ghi lai lenh goi, tra ma theo hang doi).
kiem_moc gia chi gia ket qua kiem; lenh `ghi-tu-sua` chay kiem_moc.py THAT."""
import json, os, pathlib, subprocess, sys, tempfile, unittest

CC = pathlib.Path(__file__).resolve().parents[1]
SH = CC / 'tu-sua-moc.sh'
CAN_CHU_GIA = r'''import json, os, pathlib, sys
T = pathlib.Path(__file__).resolve().parent; q = T / 'hang-can-chu.txt'
dong = q.read_text().splitlines(); rc, cach = (dong[0].split(':') + [''])[:2]; q.write_text('\n'.join(dong[1:]))
with open(T / 'goi-can-chu.txt', 'a') as f: f.write(' '.join(sys.argv[1:]) + '\n')
a = sys.argv[1:]; ep = a[a.index('--cach') + 1] if '--cach' in a else None
(T / 'dau-vao').mkdir(exist_ok=True); json.dump([{'w': 'x', 's': 0, 'e': 1, 'doan': 'mo', 'cach': ep or cach}], open(T / 'dau-vao/moc-chu.json', 'w')); json.dump([], open(T / 'dau-vao/ws0.json', 'w'))
print('CACH CAN CHU:', ep or cach); sys.exit(int(rc))
'''
KIEM_MOC_GIA = r'''import json, os, pathlib, runpy, sys
THAT = os.environ['KIEM_MOC_THAT']
if sys.argv[1:2] == ['ghi-tu-sua']:
    sys.argv[0] = THAT; runpy.run_path(THAT, run_name='__main__')
else:
    q = pathlib.Path(os.environ['HANG_KIEM_MOC']); dong = q.read_text().splitlines(); rc = int(dong[0]); q.write_text('\n'.join(dong[1:]))
    ra = sys.argv[sys.argv.index('--ra') + 1]; pathlib.Path(ra).parent.mkdir(parents=True, exist_ok=True)
    with open(pathlib.Path(os.environ['HANG_KIEM_MOC']).parent / 'goi-kiem-moc.txt', 'a') as f: f.write(' '.join(sys.argv[1:3]) + '\n')
    kq = dict(ket_qua='lech' if rc == 5 else 'dat', so_doan=2, so_lech=1 if rc == 5 else 0, tran=0.6, lech_tung_doan=[dict(doan='h1', moc=1.0, trang_thai='lech' if rc == 5 else 'dat', loi=['gia'] if rc == 5 else [])])
    json.dump(kq, open(ra, 'w')); sys.exit(rc)
'''

SO_MOC_GIA = r'''import os, sys
open(os.environ['GHI_SO_MOC'], 'a').write('goi\n'); print('so-moc gia'); sys.exit(int(os.environ['RC_SO_MOC']))
'''


class Chay:
    def __init__(self, td, can_chu, kiem_moc):
        self.td = pathlib.Path(td); self.root = self.td / 'repo'; self.M = self.root / 'khuon' / 'x'
        (self.root / 'cong-cu').mkdir(parents=True); self.M.mkdir(parents=True); (self.M / 'kiem').mkdir()
        (self.M / 'can-chu.py').write_text(CAN_CHU_GIA); (self.root / 'cong-cu/kiem_moc.py').write_text(KIEM_MOC_GIA)
        (self.M / 'hang-can-chu.txt').write_text('\n'.join(can_chu)); (self.td / 'hang-kiem-moc.txt').write_text('\n'.join(map(str, kiem_moc)))

    def chay(self, *cachs, so_moc=None):   # so_moc = rc cua so-moc.py gia -> chay them so_moc_voi_mac (nhu chay.sh top5/tin-nhanh)
        (self.root / 'cong-cu/so-moc.py').write_text(SO_MOC_GIA); (self.M / 'dau-vao').mkdir(exist_ok=True); (self.M / 'dau-vao/moc-chu.mac.json').write_text('[]')
        script = f'set -euo pipefail\nROOT={self.root}; M={self.M}; PY=({sys.executable}); DO=/dev/null\n. {SH}\ncd "$M"\ncan_chu_tu_sua {" ".join(cachs)}\nso_moc_voi_mac\necho CHAY_TIEP\n'
        env = dict(os.environ, RC_SO_MOC=str(so_moc or 0), GHI_SO_MOC=str(self.td / 'goi-so-moc.txt'), KIEM_MOC_THAT=str(CC / 'kiem_moc.py'), HANG_KIEM_MOC=str(self.td / 'hang-kiem-moc.txt'))
        r = subprocess.run(['/bin/bash', '-c', script], capture_output=True, text=True, env=env)
        self.out = r.stdout + r.stderr; return r.returncode

    def goi_can_chu(self): return (self.M / 'goi-can-chu.txt').read_text().splitlines() if (self.M / 'goi-can-chu.txt').exists() else []
    def so_kiem_moc(self): p = self.td / 'goi-kiem-moc.txt'; return len(p.read_text().splitlines()) if p.exists() else 0
    def tu_sua(self): return json.loads((self.M / 'kiem/tu-sua.json').read_text())


class TestTuSuaMoc(unittest.TestCase):
    def test_dat_ngay_khong_sua(self):
        with tempfile.TemporaryDirectory() as td:
            c = Chay(td, ['0:neo_doan'], [0]); self.assertEqual(c.chay('neo_doan', 'cum_cau', 'du_phong'), 0); self.assertIn('CHAY_TIEP', c.out)
            self.assertEqual(c.goi_can_chu(), ['']); t = c.tu_sua()
            self.assertEqual((t['da_sua'], t['cach_cuoi'], t['lan_dau']['ket_qua'], t['ket_qua_cuoi']), (False, 'neo_doan', 'dat', 'dat'))

    def test_lech_doi_cach_roi_dat(self):
        with tempfile.TemporaryDirectory() as td:
            c = Chay(td, ['0:neo_doan', '0'], [5, 0]); self.assertEqual(c.chay('neo_doan', 'cum_cau', 'du_phong'), 0)
            self.assertEqual(c.goi_can_chu(), ['', '--cach cum_cau'])   # cach ke tiep sau neo_doan, ep bang --cach
            t = c.tu_sua(); self.assertEqual((t['da_sua'], t['cach_dau'], t['cach_cuoi'], t['lan_dau']['ket_qua'], t['ket_qua_cuoi']), (True, 'neo_doan', 'cum_cau', 'lech', 'dat'))
            self.assertEqual([r['doan'] for r in t['lech_tung_doan']], ['h1']); self.assertEqual(t['lech_sau_sua'], [])
            self.assertTrue((c.M / 'dau-vao/moc-chu.lan1.json').exists())

    def test_cach_mac_dinh_la_cum_cau_thi_doi_sang_du_phong(self):   # top5 roi xuong cum_cau luc dau -> cach ke tiep la du_phong
        with tempfile.TemporaryDirectory() as td:
            c = Chay(td, ['0:cum_cau', '0'], [5, 0]); self.assertEqual(c.chay('neo_doan', 'cum_cau', 'du_phong'), 0); self.assertEqual(c.goi_can_chu(), ['', '--cach du_phong'])

    def test_doi_cach_van_lech_dung_ma_5_va_toi_da_mot_lan(self):
        with tempfile.TemporaryDirectory() as td:
            c = Chay(td, ['0:neo_doan', '0', '0'], [5, 5, 0]); self.assertEqual(c.chay('neo_doan', 'cum_cau', 'du_phong'), 5); self.assertNotIn('CHAY_TIEP', c.out)
            self.assertEqual(len(c.goi_can_chu()), 2); self.assertEqual(c.so_kiem_moc(), 2)
            t = c.tu_sua(); self.assertEqual((t['da_sua'], t['ket_qua_cuoi']), (True, 'lech')); self.assertEqual([r['doan'] for r in t['lech_sau_sua']], ['h1'])

    def test_cach_cuoi_danh_sach_lech_khong_con_cach_nao_dung(self):
        with tempfile.TemporaryDirectory() as td:
            c = Chay(td, ['0:du_phong', '0'], [5, 0]); self.assertEqual(c.chay('neo_doan', 'cum_cau', 'du_phong'), 5)
            self.assertEqual(c.goi_can_chu(), ['']); self.assertEqual(c.tu_sua()['da_sua'], False)

    def test_ep_cach_that_bai_dung_ro_rang_khong_roi_cach_khac(self):
        with tempfile.TemporaryDirectory() as td:
            c = Chay(td, ['0:neo_doan', '6'], [5, 0]); self.assertEqual(c.chay('neo_doan', 'cum_cau', 'du_phong'), 6)
            self.assertEqual(c.goi_can_chu(), ['', '--cach cum_cau']); self.assertEqual(c.so_kiem_moc(), 1)   # khong kiem lan 2, khong thu cach thu ba
            self.assertIn('THAT BAI', c.out); t = c.tu_sua(); self.assertFalse(t['da_sua']); self.assertIn('that bai', t['ghi_chu'])

    def test_khuon_chi_co_mot_cach_thi_chi_bao(self):   # Tin nhanh
        with tempfile.TemporaryDirectory() as td:
            c = Chay(td, ['0:du_phong'], [5]); self.assertEqual(c.chay('du_phong'), 0); self.assertIn('CHAY_TIEP', c.out); self.assertIn('CHI BAO', c.out)
            self.assertEqual(c.goi_can_chu(), ['']); t = c.tu_sua(); self.assertEqual((t['da_sua'], t['ket_qua_cuoi'], t['lan_dau']['ket_qua']), (False, 'lech', 'lech'))

    def test_bao_toan_ma_thoat_khi_can_chu_hoac_kiem_moc_crash(self):
        with tempfile.TemporaryDirectory() as td:
            c = Chay(td, ['9:neo_doan'], [0]); self.assertEqual(c.chay('neo_doan', 'cum_cau'), 9); self.assertEqual(c.so_kiem_moc(), 0); self.assertNotIn('CHAY_TIEP', c.out)
        with tempfile.TemporaryDirectory() as td:
            c = Chay(td, ['0:neo_doan'], [2]); self.assertEqual(c.chay('neo_doan', 'cum_cau'), 2); self.assertEqual(c.goi_can_chu(), ['']); self.assertFalse((c.M / 'kiem/tu-sua.json').exists())
        with tempfile.TemporaryDirectory() as td:   # kiem_moc lan 2 crash
            c = Chay(td, ['0:neo_doan', '0'], [5, 3]); self.assertEqual(c.chay('neo_doan', 'cum_cau'), 3)

    def test_so_moc_bo_qua_khi_da_doi_cach_nhung_giu_khi_khong_doi(self):   # Sol P1: so-moc vs moc Mac chi co y nghia cung thuat toan
        with tempfile.TemporaryDirectory() as td:
            c = Chay(td, ['0:neo_doan', '0'], [5, 0]); self.assertEqual(c.chay('neo_doan', 'cum_cau', 'du_phong', so_moc=1), 0)   # so-moc gia se tra 1 neu duoc goi
            self.assertIn('so-moc bo qua: cach can doi tu neo_doan sang cum_cau', c.out); self.assertFalse((c.td / 'goi-so-moc.txt').exists()); self.assertIn('CHAY_TIEP', c.out)
        with tempfile.TemporaryDirectory() as td:
            c = Chay(td, ['0:neo_doan'], [0]); self.assertEqual(c.chay('neo_doan', 'cum_cau', so_moc=1), 1)   # khong doi cach: so-moc van chay va that bai thi dung
            self.assertTrue((c.td / 'goi-so-moc.txt').exists()); self.assertNotIn('CHAY_TIEP', c.out)
        with tempfile.TemporaryDirectory() as td:
            c = Chay(td, ['0:neo_doan'], [0]); self.assertEqual(c.chay('neo_doan', 'cum_cau', so_moc=0), 0); self.assertIn('CHAY_TIEP', c.out)

    def test_xoa_ket_qua_cu_truoc_khi_chay(self):   # ws0 / tu-sua cua lan truoc khong duoc song sot
        with tempfile.TemporaryDirectory() as td:
            c = Chay(td, ['0:neo_doan'], [0]); (c.M / 'kiem/tu-sua.json').write_text('{"cu":1}'); c.chay('neo_doan'); self.assertNotIn('cu', c.tu_sua())


if __name__ == '__main__':
    unittest.main()
