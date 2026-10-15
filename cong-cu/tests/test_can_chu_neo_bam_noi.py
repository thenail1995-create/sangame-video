"""15/10 Top 5 truot A3 (run 38675292407): Whisper keo dau tu 'Hạng' som vao quang lang (7,60 -> noi that 8,09) -> neo_doan dat chu dau doan
len tieng tho, tieng dong so hang de len 'bốn:'. Neo nam trong lang phai doi toi diem bat dau noi; neo nam trong tieng noi giu nguyen."""
import json, pathlib, shutil, subprocess, sys, tempfile, unittest, wave
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
SR = 16000
TRINH = r'''
import sys, runpy
sys.path.insert(0, %(cc)r); import mo_hinh
class W:
    def __init__(s, w, a, b): s.word, s.start, s.end = w, a, b
class Seg:
    def __init__(s, ws): s.words = ws; s.text = ' '.join(w.word for w in ws)
class Mo:
    def transcribe(s, x, **kw): return iter([Seg([W(*t) for t in %(tu)r])]), None
mo_hinh.nap_whisper = lambda *a, **k: Mo()
sys.argv = [%(cc_py)r] + %(args)r
runpy.run_path(%(cc_py)r, run_name='__main__')
'''
KB = [dict(k='mo', loi='Top năm nè anh em!'), dict(k='h5', loi='Hạng năm: Alpha Beta.'), dict(k='h4', loi='Hạng bốn: Gamma Delta.'), dict(k='h3', loi='Hạng ba: Echo Foxtrot.')]
NOI = ((0.3, 1.5), (1.8, 3.0), (3.6, 4.8), (5.4, 6.4))
# Whisper: 'Hạng' doan h4 o 3.20 (trong lang 3.0-3.6, noi that 3.6); 'Hạng' doan h3 o 5.40 (dung diem noi)
NGHE = [('Top', 0.3, 0.6), ('năm', 0.6, 0.9), ('nè', 0.9, 1.1), ('anh', 1.1, 1.3), ('em', 1.3, 1.5),
        ('Hạng', 1.8, 2.0), ('năm', 2.0, 2.2), ('Alpha', 2.2, 2.6), ('Beta', 2.6, 3.0),
        ('Hạng', 3.2, 3.8), ('bốn', 3.8, 4.0), ('Gamma', 4.0, 4.4), ('Delta', 4.4, 4.8),
        ('Hạng', 5.4, 5.6), ('ba', 5.6, 5.8), ('Echo', 5.8, 6.1), ('Foxtrot', 6.1, 6.4)]


def giong(path):
    r = np.random.default_rng(3); x = (r.standard_normal(SR * 7) * 1e-4).astype(np.float32)
    for a, b in NOI: i, j = round(a * SR), round(b * SR); x[i:j] += (r.standard_normal(j - i) * 0.1).astype(np.float32)
    with wave.open(str(path), 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())


@unittest.skipUnless(shutil.which('ffmpeg'), 'can ffmpeg')
class TestNeoBamNoi(unittest.TestCase):
    def test_neo_trong_lang_doi_toi_diem_noi(self):
        td = pathlib.Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, td, True)
        M = td / 'khuon' / 'top5'; (M / 'dau-vao').mkdir(parents=True); (td / 'cong-cu').symlink_to(ROOT / 'cong-cu')
        shutil.copy(ROOT / 'khuon/top5/can-chu.py', M / 'can-chu.py'); (M / 'kich-ban.json').write_text(json.dumps(KB)); giong(M / 'dau-vao/giong.mp3')
        r = subprocess.run([sys.executable, '-c', TRINH % dict(cc=str(ROOT / 'cong-cu'), cc_py=str(M / 'can-chu.py'), args=['--cach', 'neo_doan'], tu=NGHE)],
                           capture_output=True, text=True, cwd=td)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        moc = json.loads((M / 'dau-vao/moc-chu.json').read_text())
        dau = {d: next(g for g in moc if g['doan'] == d)['s'] for d in ('h4', 'h3')}
        self.assertAlmostEqual(dau['h4'], 3.6, delta=0.05, msg=f'neo h4 nam trong lang phai doi toi 3.6: {dau}')   # truoc khi sua: 3.20
        self.assertAlmostEqual(dau['h3'], 5.4, delta=0.05, msg=f'neo h3 dung diem noi phai giu nguyen: {dau}')


if __name__ == '__main__':
    unittest.main()
