"""Dot 2a (E, F): manifest.json co truong `tu_sua` (lich su vong tu sua moc chu) - giu ca khi rong; dung.yml dua kiem/tu-sua.json vao chung-meta."""
import json, os, pathlib, re, subprocess, sys, tempfile, unittest

CC = pathlib.Path(__file__).resolve().parents[1]
ROOT = CC.parent


def dung_khuon(td):
    td = pathlib.Path(td); K = td / 'khuon' / 'top5'; (K / 'kiem').mkdir(parents=True)
    (K / 'nen-tang.json').write_text(json.dumps({'tiktok': {}}))
    (K / 'video-tiktok.mp4').write_bytes(b'\0' * 1_000_100); (K / 'bia-tiktok.jpg').write_bytes(b'\xff\xd8x')
    (K / 'kiem' / 'kiem-tiktok.json').write_text(json.dumps({'dat': True, 'so_dat': 1, 'tong': 1, 'phep': [{'ten': 'A1', 'dat': True, 'so_do': 'ok'}]}))
    (K / 'loi.txt').write_text('Xin chao'); bin_ = td / 'bin'; bin_.mkdir()
    f = bin_ / 'ffprobe'; f.write_text('#!/bin/sh\necho 12.5\n'); f.chmod(0o755)
    return K, td, bin_


def chay_manifest(K, td, bin_):
    env = dict(os.environ, PATH=f'{bin_}:{os.environ["PATH"]}', CODE_SHA='abc', DATA_SHA='def')
    r = subprocess.run([sys.executable, str(CC / 'manifest.py'), '--khuon', str(K), '--ra', str(td / 'out'), '--dang', 'top5', '--ngay', '2026-10-13'], capture_output=True, text=True, env=env, cwd=td)
    assert r.returncode == 0, r.stdout + r.stderr
    return json.loads((td / 'out' / 'manifest.json').read_text())


class TestManifestTuSua(unittest.TestCase):
    def test_khong_co_tu_sua_thi_rong_nhung_truong_van_co(self):
        with tempfile.TemporaryDirectory() as t:
            m = chay_manifest(*dung_khuon(t)); self.assertIn('tu_sua', m); self.assertEqual(m['tu_sua'], {})

    def test_giu_nguyen_lich_su_ke_ca_khi_khong_phai_sua(self):
        with tempfile.TemporaryDirectory() as t:
            K, td, b = dung_khuon(t); ts = {'phien_ban': 1, 'lan_dau': {'ket_qua': 'dat', 'so_doan': 7, 'so_lech': 0}, 'cach_dau': 'neo_doan', 'cach_cuoi': 'neo_doan', 'da_sua': False}
            (K / 'kiem' / 'tu-sua.json').write_text(json.dumps(ts)); self.assertEqual(chay_manifest(K, td, b)['tu_sua'], ts)

    def test_giu_lich_su_da_sua(self):
        with tempfile.TemporaryDirectory() as t:
            K, td, b = dung_khuon(t); ts = {'lan_dau': {'ket_qua': 'lech', 'so_doan': 6, 'so_lech': 3}, 'cach_cuoi': 'cum_cau', 'da_sua': True, 'lech_tung_doan': [{'doan': 'gia'}]}
            (K / 'kiem' / 'tu-sua.json').write_text(json.dumps(ts)); self.assertEqual(chay_manifest(K, td, b)['tu_sua'], ts)

    def test_file_hong_khong_lam_hong_manifest(self):
        with tempfile.TemporaryDirectory() as t:
            K, td, b = dung_khuon(t); (K / 'kiem' / 'tu-sua.json').write_text('{hong'); self.assertIn('loi', chay_manifest(K, td, b)['tu_sua'])


class TestDungYmlMeta(unittest.TestCase):
    def test_bo_loc_chung_meta_nhan_tu_sua_json_va_van_loai_kiem_khac(self):
        y = (ROOT / '.github/workflows/dung.yml').read_text(encoding='utf-8')
        m = re.search(r'grep -E "([^"]*tu-sua[^"]*)" \| tr', y); self.assertIsNotNone(m, 'bo loc meta khong co tu-sua')
        pat = m.group(1).replace('$K', 'khuon/top5'); rx = re.compile(pat)
        for dung in ('khuon/top5/kiem/tu-sua.json', 'khuon/top5/top5.json', 'khuon/top5/loi.txt'): self.assertTrue(rx.search(dung), dung)
        for sai in ('khuon/top5/kiem/kiem-tiktok.json', 'khuon/top5/kiem/log-x.txt', 'khuon/top5/dau-vao/moc-chu.json', 'khuon/top5/kiem/tu-sua.json.bak'): self.assertFalse(rx.search(sai), sai)


if __name__ == '__main__':
    unittest.main()
