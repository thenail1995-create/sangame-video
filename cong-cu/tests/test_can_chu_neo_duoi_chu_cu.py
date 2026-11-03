"""03/11 Top 5 (run 41571082167 + 41574060674) - hai loi cua can-chu.py cach NEO DOAN:
 (1) Whisper keo tu dau doan ve DUOI chu cuoi cau truoc ('Con' 28,74 trong khi tieng noi that 29,70): `_bam` thay neo dang trong tieng noi nen giu nguyen
     -> doan `ket` som 1 s, cua so D3 dinh 1 s im lang + 1 manh 'Kong!' -> Whisper bia 'Hay subscribe cho kenh...'. Sua: neo nam trong cum co tieng NGAN (<= 0,30 s)
     roi toi khoang lang >= 0,25 s -> doi toi diem noi sau khoang lang; neo nam trong tieng noi dai -> giu nguyen.
 (2) chu trong doan chia deu CA quang nghi sau dau phay -> cua so chu 'giam' roi tron vao quang nghi (A3 -17,7 dB). Sua: chia chu theo am tiet CHI tren thoi gian co tieng.
Mau: test_can_chu_neo_bam_noi.py (Whisper gia lap + giong tong hop)."""
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
KB = [dict(k='mo', loi='Top năm nè anh em!'), dict(k='h5', loi='Hạng năm: Alpha Beta.'), dict(k='h4', loi='Hạng bốn: Gamma, Delta.'), dict(k='h3', loi='Hạng ba: Echo Foxtrot.')]
# tieng noi: h5 1,8-3,0 · h4 3,6-4,4 | NGHI 0,5 s (dau phay) | 4,9-5,3 · h3 5,9-6,9 (8 s, >50% co tieng de trung vi = muc tieng noi)
NOI = ((0.3, 1.5), (1.8, 3.0), (3.6, 4.4), (4.9, 5.3), (5.9, 6.9))
# Whisper: 'Hạng' doan h4 o 2,90 = DUOI 'Beta' (tieng noi h5 het 3,0; tieng noi that cua h4 bat dau 3,60)
NGHE = [('Top', 0.3, 0.6), ('năm', 0.6, 0.9), ('nè', 0.9, 1.1), ('anh', 1.1, 1.3), ('em', 1.3, 1.5),
        ('Hạng', 1.8, 2.0), ('năm', 2.0, 2.2), ('Alpha', 2.2, 2.6), ('Beta', 2.6, 3.0),
        ('Hạng', 2.9, 3.8), ('bốn', 3.8, 4.0), ('Gamma', 4.0, 4.4), ('Delta', 4.9, 5.3),
        ('Hạng', 5.9, 6.1), ('ba', 6.1, 6.3), ('Echo', 6.3, 6.6), ('Foxtrot', 6.6, 6.9)]


def giong(path):
    r = np.random.default_rng(3); x = (r.standard_normal(SR * 8) * 1e-4).astype(np.float32)
    for a, b in NOI: i, j = round(a * SR), round(b * SR); x[i:j] += (r.standard_normal(j - i) * 0.1).astype(np.float32)
    with wave.open(str(path), 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())


@unittest.skipUnless(shutil.which('ffmpeg'), 'can ffmpeg')
class TestNeoDuoiChuCu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        td = pathlib.Path(tempfile.mkdtemp()); cls.addClassCleanup(shutil.rmtree, td, True)
        M = td / 'khuon' / 'top5'; (M / 'dau-vao').mkdir(parents=True); (td / 'cong-cu').symlink_to(ROOT / 'cong-cu')
        shutil.copy(ROOT / 'khuon/top5/can-chu.py', M / 'can-chu.py'); (M / 'kich-ban.json').write_text(json.dumps(KB)); giong(M / 'dau-vao/giong.mp3')
        r = subprocess.run([sys.executable, '-c', TRINH % dict(cc=str(ROOT / 'cong-cu'), cc_py=str(M / 'can-chu.py'), args=['--cach', 'neo_doan'], tu=NGHE)],
                           capture_output=True, text=True, cwd=td)
        assert r.returncode == 0, r.stdout + r.stderr
        cls.moc = json.loads((M / 'dau-vao/moc-chu.json').read_text())

    def dau(self, d): return next(g for g in self.moc if g['doan'] == d)['s']

    def test_neo_trong_duoi_chu_cu_doi_sang_sau_khoang_lang(self):
        # neo h4 2,90: cum co tieng chi con 0,10 s (duoi 'Beta') roi lang 0,6 s -> tieng noi that o 3,60. Truoc khi sua: 2,90
        self.assertAlmostEqual(self.dau('h4'), 3.6, delta=0.05, msg=f'neo trong duoi chu cu phai doi toi 3.6: {self.dau("h4")}')

    def test_neo_trong_tieng_noi_dai_giu_nguyen(self):
        self.assertAlmostEqual(self.dau('h5'), 1.8, delta=0.05)      # tieng noi 1,2 s tu neo
        self.assertAlmostEqual(self.dau('h3'), 5.9, delta=0.05)      # tieng noi 1,0 s tu neo

    def test_chu_sau_dau_phay_khong_roi_vao_quang_nghi(self):
        # h4 co tieng 3,6-4,4 va 4,9-5,3; quang nghi 4,4-4,9 (>= 150 ms). Chu 'Gamma' (hết truoc dau phay) phai het <= 4,45 va 'Delta' bat dau >= 4,85.
        # Truoc khi sua (chia deu 3,6-5,35): Gamma het ~4,75 va Delta bat dau ~4,77 (nam trong quang nghi).
        h4 = {g['w']: g for g in self.moc if g['doan'] == 'h4'}
        self.assertLessEqual(h4['Gamma,']['e'], 4.45, h4)
        self.assertGreaterEqual(h4['Delta.']['s'], 4.85, h4)
        for g in h4.values():
            self.assertFalse(4.45 < (g['s'] + g['e']) / 2 < 4.85, f'chu nam giua quang nghi: {g}')


if __name__ == '__main__': unittest.main()
