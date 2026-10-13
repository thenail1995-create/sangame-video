"""Sol soi diff P1/P2: chay THAT khuon/{top5,keo-thom}/can-chu.py nhanh --cach du_phong (Whisper gia, giong gia) - khong crash, ghi moc + ws0 + dong CACH CAN CHU;
--cach ep that bai => ma 6, khong roi cach khac."""
import json, pathlib, shutil, subprocess, sys, tempfile, unittest, wave
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
SR = 16000
TRINH = r'''
import json, pathlib, runpy, sys, types
sys.path.insert(0, %(cc)r); import mo_hinh
class W:
    def __init__(s, w, a, b): s.word, s.start, s.end = w, a, b
class Seg:
    def __init__(s, ws): s.words = ws; s.text = ' '.join(w.word for w in ws)
class Mo:
    def transcribe(s, x, **kw):
        ws = [W(w, 0.3 + i * 0.35, 0.6 + i * 0.35) for i, w in enumerate(%(tu)r)]; return iter([Seg(ws)]), None
mo_hinh.nap_whisper = lambda *a, **k: Mo()
sys.argv = [%(cc_py)r] + %(args)r
runpy.run_path(%(cc_py)r, run_name='__main__')
'''


def giong(path):
    r = np.random.default_rng(3); x = (r.standard_normal(SR * 6) * 1e-4).astype(np.float32)
    for a, b in ((0.3, 2.0), (2.6, 4.2), (4.8, 5.8)): i, j = round(a * SR), round(b * SR); x[i:j] += (r.standard_normal(j - i) * 0.1).astype(np.float32)
    with wave.open(str(path), 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())


@unittest.skipUnless(shutil.which('ffmpeg'), 'can ffmpeg')
class TestCanChuDuPhong(unittest.TestCase):
    def _chay(self, khuon, kich_ban, args, nghe=None):
        td = pathlib.Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, td, True)
        M = td / 'khuon' / khuon; (M / 'dau-vao').mkdir(parents=True); (td / 'cong-cu').symlink_to(ROOT / 'cong-cu')
        shutil.copy(ROOT / 'khuon' / khuon / 'can-chu.py', M / 'can-chu.py'); (M / 'kich-ban.json').write_text(json.dumps(kich_ban)); giong(M / 'dau-vao/giong.mp3')
        tu = [w for d in (kich_ban['doan'] if isinstance(kich_ban, dict) else kich_ban) for w in d['loi'].split()]
        r = subprocess.run([sys.executable, '-c', TRINH % dict(cc=str(ROOT / 'cong-cu'), cc_py=str(M / 'can-chu.py'), args=args, tu=nghe or tu)], capture_output=True, text=True, cwd=td)
        return r, M, len(tu)

    def test_du_phong_khong_crash_ca_hai_khuon(self):
        top5 = [{'k': 'mo', 'loi': 'Top nam game ban chay nhe.'}, {'k': 'h5', 'loi': 'Hang nam Sifu giam gia.'}, {'k': 'ket', 'loi': 'Theo doi San Game.'}]
        keo = {'doan': [{'k': 'mo', 'loi': 'Chua bang mot bua lau nhe.'}, {'k': 'gia', 'loi': 'Tu mot trieu con ba tram.'}, {'k': 'ket', 'loi': 'Theo doi San Game.'}]}
        for khuon, kb in (('top5', top5), ('keo-thom', keo)):
            r, M, n = self._chay(khuon, kb, ['--cach', 'du_phong'])
            self.assertEqual(r.returncode, 0, f'{khuon}: {r.stderr[-600:]}'); self.assertIn('CACH CAN CHU: du_phong', r.stdout)
            self.assertEqual(len(json.loads((M / 'dau-vao/moc-chu.json').read_text())), n); self.assertTrue((M / 'dau-vao/ws0.json').exists())

    def test_ep_cach_that_bai_ma_6_khong_roi_cach_khac(self):
        top5 = [{'k': 'mo', 'loi': 'Top nam game ban chay nhe.'}, {'k': 'h5', 'loi': 'Hang nam Sifu giam gia.'}, {'k': 'ket', 'loi': 'Theo doi San Game.'}]
        r, M, _ = self._chay('top5', top5, ['--cach', 'neo_doan'], nghe=['abc', 'def', 'ghi'])   # Whisper gia khong nghe «hang» o dau doan => neo that bai
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr[-400:]); self.assertIn('THAT BAI', r.stdout); self.assertFalse((M / 'dau-vao/moc-chu.json').exists())

    def test_cach_khong_hop_le(self):
        r, _, _ = self._chay('top5', [{'k': 'mo', 'loi': 'Xin chao.'}], ['--cach', 'abc']); self.assertNotEqual(r.returncode, 0)


if __name__ == '__main__':
    unittest.main()
