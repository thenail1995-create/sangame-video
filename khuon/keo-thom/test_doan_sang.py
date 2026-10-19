"""19/10: chon-keo loai game co trailer toi (Triangle Strategy 18/10: 18,0 s doan sang < 21 s). Ham quyet_dinh la ham thuan, khong goi ffmpeg."""
import sys, pathlib, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import doan_sang as D

def seg(*lens): return [('a.mp4', 10.0 + i * 5, l, 60.0, None) for i, l in enumerate(lens)]

class QuyetDinh(unittest.TestCase):
    def test_18s_bi_loai(self):
        dat, ly, tong = D.quyet_dinh(seg(10.0, 8.0))
        self.assertFalse(dat); self.assertAlmostEqual(tong, 18.0); self.assertIn('18.0s', ly); self.assertIn('21', ly)
    def test_25s_dat(self):
        dat, ly, tong = D.quyet_dinh(seg(15.0, 10.0))
        self.assertTrue(dat); self.assertIsNone(ly)
    def test_dung_nguong(self):
        self.assertTrue(D.quyet_dinh(seg(21.0))[0])
        self.assertFalse(D.quyet_dinh(seg(20.9))[0])
    def test_rong_bi_loai(self):
        self.assertFalse(D.quyet_dinh([])[0])
    def test_nhan_dict(self):
        self.assertFalse(D.quyet_dinh([dict(src='a', s0=1, len=18.0)])[0])
