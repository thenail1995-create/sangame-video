"""cong-cu/ghep_am.py: ghep tieng theo ban (env BAN), thieu hinh o che do bat buoc = loi. Khong can ffmpeg."""
import json, os, pathlib, sys, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import ghep_am


class GhepAm(unittest.TestCase):
    def khuon(self, d):
        d = pathlib.Path(d); (d / 'nen-tang.json').write_text(json.dumps({'tiktok': {}, 'reels': {}, 'shorts': {}})); return d
    def test_ban_tu_env(self):
        with tempfile.TemporaryDirectory() as t:
            B = self.khuon(t)
            os.environ.pop('BAN', None); self.assertEqual(ghep_am.danh_sach_ban(B), ['tiktok', 'reels', 'shorts'])
            os.environ['BAN'] = 'reels'
            try: self.assertEqual(ghep_am.danh_sach_ban(B), ['reels'])
            finally: os.environ.pop('BAN', None)
            os.environ['BAN'] = 'youtube'
            try: self.assertRaises(SystemExit, ghep_am.danh_sach_ban, B)
            finally: os.environ.pop('BAN', None)
    def test_thieu_hinh(self):
        with tempfile.TemporaryDirectory() as t:
            B = self.khuon(t)
            self.assertEqual(ghep_am.ghep(B, B / 'am.wav', 1.0, nts=['reels']), [])   # che do Mac: bo qua ban chua co hinh
            with self.assertRaises(SystemExit) as c: ghep_am.ghep(B, B / 'am.wav', 1.0, nts=['reels'], bat_buoc=True)   # che do CI (job ban): thieu hinh = loi
            self.assertIn('hinh-reels.mp4', str(c.exception))


if __name__ == '__main__': unittest.main()
