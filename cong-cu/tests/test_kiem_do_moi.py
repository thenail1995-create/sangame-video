"""Gói A8 (Sol #19 #22 #25): kiem_do_moi.py - mốc giờ VN, mốc riêng từng feed, báo ntfy theo dạng."""
import json, pathlib, sys, tempfile, unittest
from unittest import mock

CC = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CC)); sys.path.insert(0, str(CC.parent))
import kiem_do_moi as k  # noqa: E402

VUNG = k.VUNG


def dung_repo(td, feed_cap_nhat='2026-10-11', tong='2026-10-11', bo_truong=()):
    dl = pathlib.Path(td) / 'du-lieu'; dl.mkdir(parents=True)
    (dl / 'bang-gia.json').write_text(json.dumps({'cap_nhat': tong, 'so_mon_giu_lai': {v: 5 for v in VUNG}}))
    (dl / 'trang-game.json').write_text(json.dumps({'cap_nhat': tong}))
    (dl / 'gia-the.json').write_text(json.dumps({'ngay': tong}))
    for v in VUNG:
        d = {'vung': 'en-' + v, 'so_mon': 3, 'mon': {'UP1': {'gia': 1}}}
        if v not in bo_truong: d['cap_nhat'] = feed_cap_nhat[v] if isinstance(feed_cap_nhat, dict) else feed_cap_nhat
        (dl / f'giam-gia-en-{v}.json').write_text(json.dumps(d))
    return td


class TestUaTuyChon(unittest.TestCase):   # 15/10: UA = vung TUY CHON, khong bao gio la dieu kien 'moi'
    def test_ua_khong_nam_trong_vung_bat_buoc(self):
        self.assertNotIn('UA', k.VUNG); self.assertEqual(sorted(k.VUNG), ['HK', 'ID', 'IN', 'SG', 'TH', 'US'])

    def test_thieu_giam_gia_uk_ua_van_moi(self):
        with tempfile.TemporaryDirectory() as td:
            dung_repo(td)
            self.assertFalse((pathlib.Path(td) / 'du-lieu' / 'giam-gia-uk-UA.json').exists())
            self.assertEqual(k.kiem(td, '2026-10-11'), (True, []))

    def test_co_uk_ua_cu_hoac_hong_van_moi(self):
        for noi_dung in ('{}', 'khong phai json', json.dumps({'so_mon': 0, 'mon': {}, 'cap_nhat': '2020-01-01'})):
            with tempfile.TemporaryDirectory() as td:
                dung_repo(td)
                (pathlib.Path(td) / 'du-lieu' / 'giam-gia-uk-UA.json').write_text(noi_dung)
                self.assertEqual(k.kiem(td, '2026-10-11'), (True, []), noi_dung)
                (pathlib.Path(td) / 'du-lieu' / 'bang-gia.json').write_text(json.dumps({'cap_nhat': '2026-10-11', 'so_mon_giu_lai': {**{v: 5 for v in VUNG}, 'UA': 0}}))
                self.assertEqual(k.kiem(td, '2026-10-11'), (True, []), 'so_mon_giu_lai UA = 0 khong duoc lam cu')


class TestMonRong(unittest.TestCase):   # vong 2 #4: so_mon > 0 nhung mon rong / sai kieu => cu/thieu
    def test_mon_rong_hoac_khong_phai_dict_la_cu(self):
        for mon in ({}, [], None, 'x'):
            with tempfile.TemporaryDirectory() as td:
                dung_repo(td)
                f = pathlib.Path(td) / 'du-lieu' / 'giam-gia-en-SG.json'
                d = json.loads(f.read_text()); d['mon'] = mon; f.write_text(json.dumps(d))
                moi, ly = k.kiem(td, '2026-10-11')
                self.assertFalse(moi, mon); self.assertTrue(any('SG' in x for x in ly), ly)

    def test_mon_co_noi_dung_van_moi(self):
        with tempfile.TemporaryDirectory() as td:
            dung_repo(td)
            for v in VUNG:
                f = pathlib.Path(td) / 'du-lieu' / f'giam-gia-en-{v}.json'; d = json.loads(f.read_text()); d['mon'] = {'UP1': {'gia': 1}}; f.write_text(json.dumps(d))
            self.assertEqual(k.kiem(td, '2026-10-11'), (True, []))


class TestMoc(unittest.TestCase):
    def test_utc_cuoi_ngay_la_ngay_sau_o_vn(self):  # #25
        import datetime
        self.assertEqual(k.ngay_vn('2026-10-10T18:00:00Z'), datetime.date(2026, 10, 11))
        self.assertTrue(k.du_ngay('2026-10-10T18:00:00Z', '2026-10-11'))
        self.assertFalse(k.du_ngay('2026-10-10T16:59:59Z', '2026-10-11'))
        self.assertTrue(k.du_ngay('2026-10-11T00:00:00+07:00', '2026-10-11'))
        self.assertFalse(k.du_ngay('2026-10-11T00:30:00+09:00', '2026-10-11'))   # = 10/10 22:30 VN
        self.assertTrue(k.du_ngay('2026-10-11', '2026-10-11')); self.assertFalse(k.du_ngay(None, '2026-10-11')); self.assertFalse(k.du_ngay('rac', '2026-10-11'))

    def test_tong_moi_nhung_mot_moc_utc_van_dat(self):
        with tempfile.TemporaryDirectory() as td:
            dung_repo(td, feed_cap_nhat='2026-10-10T18:00:00Z', tong='2026-10-10T18:00:00Z')
            self.assertEqual(k.kiem(td, '2026-10-11'), (True, []))


class TestFeed(unittest.TestCase):
    def test_metadata_tong_moi_nhung_6_feed_cu(self):  # #19
        with tempfile.TemporaryDirectory() as td:
            dung_repo(td, feed_cap_nhat='2026-10-10')
            moi, ly = k.kiem(td, '2026-10-11'); self.assertFalse(moi); self.assertEqual(len([x for x in ly if 'giam-gia-en' in x]), 6)

    def test_feed_thieu_truong_la_cu(self):  # #19
        with tempfile.TemporaryDirectory() as td:
            dung_repo(td, bo_truong=('IN',)); moi, ly = k.kiem(td, '2026-10-11')
            self.assertFalse(moi); self.assertTrue(any('giam-gia-en-IN' in x and 'thieu' in x for x in ly))

    def test_mot_feed_cu_la_truot(self):
        with tempfile.TemporaryDirectory() as td:
            f = {v: '2026-10-11' for v in VUNG}; f['HK'] = '2026-10-10'
            dung_repo(td, feed_cap_nhat=f); moi, ly = k.kiem(td, '2026-10-11'); self.assertFalse(moi); self.assertEqual(len(ly), 1)

    def test_tat_ca_moi_va_so_mon_0_van_truot(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(k.kiem(dung_repo(td), '2026-10-11'), (True, []))
            p = pathlib.Path(td) / 'du-lieu/giam-gia-en-US.json'; d = json.loads(p.read_text()); d['so_mon'] = 0; p.write_text(json.dumps(d))
            self.assertFalse(k.kiem(td, '2026-10-11')[0])


class TestNtfy(unittest.TestCase):
    def chay(self, dang, lan_cuoi, ntfy_ok=True):
        with tempfile.TemporaryDirectory() as td:
            dung_repo(td, feed_cap_nhat='2026-10-10')
            goi = mock.Mock(return_value=ntfy_ok)
            with mock.patch('dang.ntfy.loi', goi):
                argv = [td, '--ngay', '2026-10-11', '--dang', dang] + (['--lan-cuoi'] if lan_cuoi else [])
                return k.main(argv), goi

    def test_luot_cuoi_bao_theo_ten_dang(self):  # #22
        for dang, ten in (('top5', 'Top 5'), ('keo-thom', 'Keo thom'), ('tin-nhanh', 'Tin nhanh')):
            rc, goi = self.chay(dang, True); self.assertEqual(rc, 0); self.assertEqual(goi.call_count, 1)
            self.assertIn(ten, goi.call_args[0][0])
            if dang != 'top5': self.assertNotIn('Top 5', goi.call_args[0][0])

    def test_chua_luot_cuoi_khong_bao(self):
        rc, goi = self.chay('top5', False); self.assertEqual(rc, 0); goi.assert_not_called()

    def test_gui_ntfy_hong_thoat_1(self):  # #22
        rc, goi = self.chay('keo-thom', True, ntfy_ok=False); self.assertEqual(rc, 1)

    def test_ntfy_nem_loi_thoat_1(self):
        with tempfile.TemporaryDirectory() as td:
            dung_repo(td, feed_cap_nhat='2026-10-10')
            with mock.patch('dang.ntfy.loi', side_effect=RuntimeError('x')):
                self.assertEqual(k.main([td, '--ngay', '2026-10-11', '--dang', 'tin-nhanh', '--lan-cuoi']), 1)


if __name__ == '__main__': unittest.main()
