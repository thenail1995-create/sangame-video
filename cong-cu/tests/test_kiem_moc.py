"""Dot 2a (A, F): cong-cu/kiem_moc.py - moc chu dau doan vs giong that + ws0. Giong gia = tieng on co bien do, im lang xen ke (khong can Whisper)."""
import json, pathlib, subprocess, sys, tempfile, unittest, wave
import numpy as np

CC = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CC))
import kiem_moc as km  # noqa: E402

SR = 16000
# doan: mo 0.2-2.0 | gia 2.6-4.5 | gioi 5.2-7.0 | ket 9.0-11.0 (im 7.0-9.0)
VUNG = [(0.2, 2.0), (2.6, 4.5), (5.2, 7.0), (9.0, 11.0)]


def giong_gia(dai=12.0, vung=VUNG, seed=1):
    r = np.random.default_rng(seed); x = (r.standard_normal(int(dai * SR)) * 1e-4).astype(np.float32)   # nen ~ -80 dB
    for a, b in vung:
        i, j = round(a * SR), round(b * SR); x[i:j] += (r.standard_normal(j - i) * 0.1).astype(np.float32)
    return x


def moc_cho(t_dau, ten=('mo', 'gia', 'gioi', 'ket')):
    out = []
    for k, t in zip(ten, t_dau):
        for i, w in enumerate(('Xin', 'chao', 'cac', 'ban')): out.append(dict(w=w, s=round(t + i * 0.2, 2), e=round(t + i * 0.2 + 0.18, 2), doan=k))
    return out


def ws0_cho(t_dau, tu=(('Hạng', 'năm'), ('Mortal', 'Kombat'), ('Little', 'Nightmares'), ('Theo', 'dõi'))):
    return [[w, t + i * 0.2, t + i * 0.2 + 0.18] for t, ws in zip(t_dau, tu) for i, w in enumerate(ws)]


def moc_ten(tu=(('Hạng', 'năm'), ('Mortal', 'Kombat'), ('Little', 'Nightmares'), ('Theo', 'dõi')), t_dau=(0.2, 2.6, 5.2, 9.0)):
    return [dict(w=w, s=round(t + i * .2, 2), e=round(t + i * .2 + .18, 2), doan=k) for k, t, ws in zip(('mo', 'gia', 'gioi', 'ket'), t_dau, tu) for i, w in enumerate(ws)]


class TestKiemMoc(unittest.TestCase):
    def setUp(self): self.db = km.nang_luong_db(giong_gia())

    def test_moc_dung_dat(self):
        kq = km.kiem(moc_cho([0.2, 2.6, 5.2, 9.0]), self.db)
        self.assertEqual(kq['ket_qua'], 'dat', kq); self.assertEqual(kq['so_lech'], 0)

    def test_moc_dung_lech_nho_van_dat(self):
        self.assertEqual(km.kiem(moc_cho([0.3, 2.5, 5.4, 9.2]), self.db)['ket_qua'], 'dat')

    def test_moc_lech_8_giay_la_lech(self):   # loi Keo Taxi Life 13/10: 4 doan sau cung 1 moc, lech ~8 s
        kq = km.kiem(moc_cho([0.2, 8.0, 8.0, 8.0]), self.db)
        self.assertEqual(kq['ket_qua'], 'lech'); self.assertEqual([r['doan'] for r in kq['lech_tung_doan'] if r['trang_thai'] == 'lech'], ['gia', 'gioi', 'ket'])
        self.assertFalse(kq['lech_tung_doan'][1]['co_giong'])   # 8.0 s nam trong quang im 7.0-9.0

    def test_moc_trong_giong_nhung_xa_diem_bat_dau_la_lech(self):   # 3.8 s dang noi (doan gia 2.6-4.5) nhung khong phai dau cum: cach diem bat dau 1,2 s
        kq = km.kiem(moc_cho([0.2, 3.8, 5.2, 9.0]), self.db)
        r = kq['lech_tung_doan'][1]; self.assertTrue(r['co_giong']); self.assertEqual(r['trang_thai'], 'lech'); self.assertGreater(r['lech_bat_dau'], 0.6)

    def test_ws0_dung_dat_va_lech_thi_truot(self):
        tu = [0.2, 2.6, 5.2, 9.0]
        self.assertEqual(km.kiem(moc_ten(), self.db, ws0_cho(tu))['ket_qua'], 'dat')
        sai = ws0_cho([0.2, 2.6, 6.0, 9.0])    # Whisper nghe dau doan gioi o 6.0 s nhung moc o 5.2 s: lech 0,8 s > 0,6 s
        kq = km.kiem(moc_ten(), self.db, sai)
        self.assertEqual(kq['ket_qua'], 'lech'); self.assertEqual(kq['lech_tung_doan'][2]['ws0'], 'lech')

    def test_whisper_keo_som_vao_quang_lang_khong_phai_lech(self):   # top5 13/10: ws0 «Còn» 27,68 trong khi giong that bat dau 28,53 (moc dung)
        ws0 = ws0_cho([0.2, 2.6, 5.2, 7.9])    # doan ket: Whisper tinh 7.9 s (giua quang im 7.0-9.0), giong that vao 9.0 s, moc 9.0 s dung
        r = km.kiem(moc_ten(), self.db, ws0)['lech_tung_doan'][3]
        self.assertEqual((r['ws0'], r.get('ws0_keo_som'), r['trang_thai']), ('dat', True, 'dat'))

    def test_ws0_cach_xa_nhung_giua_co_tieng_noi_van_lech(self):   # Keo Taxi Life cu: ws0 8,5 s, moc 19,1 s, giua la ca doan dang noi
        ws0 = ws0_cho([0.2, 2.6, 5.2, 0.5])    # «Theo dõi» (doan ket) nghe o 0.5 s, moc o 9.0 s, giua co tieng noi
        r = km.kiem(moc_ten(), self.db, ws0)['lech_tung_doan'][3]
        self.assertEqual(r['ws0'], 'lech'); self.assertNotIn('ws0_keo_som', r)

    def test_neo_nhap_nhang_la_khong_kiem_duoc_khong_tinh_truot_khong_tinh_dat(self):
        tu = (('Hạng', 'năm'), ('Hạng', 'năm'), ('Little', 'Nightmares'), ('Theo', 'dõi'))   # hai doan cung tu «hạng năm»
        ws0 = ws0_cho([0.2, 2.6, 5.2, 9.0], tu)
        kq = km.kiem(moc_ten(tu), self.db, ws0)
        r = kq['lech_tung_doan']
        self.assertEqual([x['ws0'] for x in r], ['khong_kiem_duoc', 'khong_kiem_duoc', 'dat', 'dat'])
        self.assertIn('nhap nhang', r[0]['ly_do_ws0']); self.assertIsNone(r[0]['lech_ws0'])
        self.assertEqual(kq['ket_qua'], 'dat')   # khong kiem duoc != truot
        # khong kiem duoc cung KHONG che loi: moc lech 8 s van bi bat boi phep (1)/(2)
        bad = moc_ten(tu, t_dau=(0.2, 8.0, 5.2, 9.0))
        self.assertEqual(km.kiem(bad, self.db, ws0)['ket_qua'], 'lech')

    def test_doan_toan_so_hoac_thieu_ws0_khong_kiem_duoc(self):
        moc = [dict(w='100', s=2.6, e=2.8, doan='gia'), dict(w='mot', s=2.8, e=3.0, doan='gia')]
        kq = km.kiem(moc, self.db, [['x', 1, 1.1]]); self.assertEqual(kq['lech_tung_doan'][0]['ws0'], 'khong_kiem_duoc')
        self.assertEqual(km.kiem(moc, self.db, None)['lech_tung_doan'][0]['ws0'], 'khong_co_ws0')


class TestCLI(unittest.TestCase):
    def _wav(self, td, x):
        p = pathlib.Path(td) / 'g.wav'
        with wave.open(str(p), 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())
        return p

    def test_ma_thoat_0_5_2(self):
        with tempfile.TemporaryDirectory() as td:
            g = self._wav(td, giong_gia()); m = pathlib.Path(td) / 'm.json'; ra = pathlib.Path(td) / 'kq' / 'k.json'
            m.write_text(json.dumps(moc_cho([0.2, 2.6, 5.2, 9.0]))); self.assertEqual(km.main([str(m), str(g), '--ra', str(ra)]), 0)
            self.assertEqual(json.loads(ra.read_text())['ket_qua'], 'dat')
            m.write_text(json.dumps(moc_cho([0.2, 8.0, 8.0, 8.0]))); self.assertEqual(km.main([str(m), str(g), '--ra', str(ra)]), 5)
            self.assertEqual(km.main([str(pathlib.Path(td) / 'khong-co.json'), str(g)]), 2)
            self.assertEqual(km.main([]), 2)

    def test_ghi_tu_sua(self):
        with tempfile.TemporaryDirectory() as td:
            t = pathlib.Path(td); a = km.kiem(moc_cho([0.2, 8.0, 8.0, 8.0]), km.nang_luong_db(giong_gia())); b = km.kiem(moc_cho([0.2, 2.6, 5.2, 9.0]), km.nang_luong_db(giong_gia()))
            (t / 'a.json').write_text(json.dumps(a)); (t / 'b.json').write_text(json.dumps(b))
            self.assertEqual(km.main(['ghi-tu-sua', str(t / 'k' / 'tu-sua.json'), '--lan-dau', str(t / 'a.json'), '--cuoi', str(t / 'b.json'), '--cach-dau', 'cum_cau', '--cach-cuoi', 'du_phong', '--da-sua', '1']), 0)
            d = json.loads((t / 'k' / 'tu-sua.json').read_text())
            self.assertEqual((d['lan_dau']['ket_qua'], d['ket_qua_cuoi'], d['cach_cuoi'], d['da_sua']), ('lech', 'dat', 'du_phong', True))
            self.assertEqual([r['doan'] for r in d['lech_tung_doan']], ['gia', 'gioi', 'ket']); self.assertEqual(d['lech_sau_sua'], [])
            km.main(['ghi-tu-sua', str(t / 'k' / 'tu-sua.json'), '--lan-dau', str(t / 'b.json'), '--cuoi', '', '--cach-dau', 'neo_doan', '--cach-cuoi', 'neo_doan', '--da-sua', '0'])
            d = json.loads((t / 'k' / 'tu-sua.json').read_text()); self.assertEqual((d['lan_dau']['ket_qua'], d['da_sua'], d['lech_tung_doan']), ('dat', False, []))


if __name__ == '__main__':
    unittest.main()
