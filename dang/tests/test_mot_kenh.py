"""SG-1KENH (Hao 01/11/2026: "khong lam chung 1 noi dung cho nhieu nen tang"): o che do that mot video chi len dung mot kenh.
Chan ngay trong may GitHub (dang/chay.py kiem_mot_kenh), truoc khi pha chuan-bi / cong-khai cham toi bat ky kenh nao."""
import os
import types
import unittest
from unittest import mock

from dang import chay, ntfy
from dang.tests.gia_lap import CongGia, NGAY, DANG


def a(dang=DANG, che_do="that"):
    return types.SimpleNamespace(dang=dang, ngay=NGAY, che_do=che_do)


class KiemMotKenh(unittest.TestCase):
    def setUp(self):
        self.cong = CongGia()
        for p in (mock.patch.object(chay, "MOT_KENH", True), mock.patch.dict(os.environ, {"SG_KENH_BAT": "youtube"})):
            p.start()
            self.addCleanup(p.stop)

    def test_mot_kenh_dat(self):
        self.assertIsNone(chay.kiem_mot_kenh(a(), self.cong))

    def test_bien_rong_hoac_nhieu_kenh_thi_dung(self):
        for bien in ("", "youtube,tiktok", "fb,ig"):
            with mock.patch.dict(os.environ, {"SG_KENH_BAT": bien}):
                ly = chay.kiem_mot_kenh(a(), self.cong)
                self.assertIsNotNone(ly, bien)
                self.assertIn("1 noi dung 1 nen tang", ly)

    def test_x_khong_tinh_la_kenh_video(self):
        with mock.patch.dict(os.environ, {"SG_KENH_BAT": "youtube,x"}):
            self.assertIsNone(chay.kiem_mot_kenh(a(), self.cong))

    def test_kenh_khac_da_giu_video_cua_khung_thi_dung(self):
        for tt in chay.GIU_KENH:
            self.cong.dong[(NGAY, DANG, "tiktok", "that")] = dict(ngay=NGAY, dang=DANG, kenh="tiktok", che_do="that", trang_thai=tt)
            ly = chay.kiem_mot_kenh(a(), self.cong)
            self.assertIn("tiktok", ly or "", tt)

    def test_kenh_khac_that_bai_bo_hoac_dang_khac_khong_tinh(self):
        self.cong.dong[(NGAY, DANG, "tiktok", "that")] = dict(ngay=NGAY, dang=DANG, kenh="tiktok", che_do="that", trang_thai="that_bai")
        self.cong.dong[(NGAY, DANG, "fb", "that")] = dict(ngay=NGAY, dang=DANG, kenh="fb", che_do="that", trang_thai="bo")
        self.cong.dong[(NGAY, "keo-thom", "tiktok", "that")] = dict(ngay=NGAY, dang="keo-thom", kenh="tiktok", che_do="that", trang_thai="da_dang")
        self.cong.dong[(NGAY, DANG, "youtube", "that")] = dict(ngay=NGAY, dang=DANG, kenh="youtube", che_do="that", trang_thai="chuan_bi_xong")
        self.assertIsNone(chay.kiem_mot_kenh(a(), self.cong))

    def test_flagship_tu_ngay_4_tiktok_youtube_bi_chan_neu_bien_rong(self):
        with mock.patch.dict(os.environ, {"SG_KENH_BAT": "", "SG_FLAGSHIP_NGAY_1": "2026-01-01"}):
            self.assertIn("youtube, tiktok", chay.kiem_mot_kenh(a("flagship"), self.cong))


class MainChan(unittest.TestCase):
    def chay(self, pha, che_do="that", bien=""):
        cong, bao = CongGia(), []
        with mock.patch.object(chay, "MOT_KENH", True), mock.patch.dict(os.environ, {"SG_KENH_BAT": bien}), \
                mock.patch.object(ntfy, "loi", lambda *x, **k: bao.append(x)), \
                mock.patch.object(chay, "pha_chuan_bi", side_effect=AssertionError("khong duoc goi")) as pcb, \
                mock.patch.object(chay, "pha_cong_khai", side_effect=AssertionError("khong duoc goi")) as pck:
            ma = chay.main(["--pha", pha, "--dang", DANG, "--ngay", NGAY, "--che-do", che_do], cong=cong)
        return ma, bao, pcb, pck

    def test_that_nhieu_kenh_dung_truoc_moi_kenh(self):
        for pha in ("chuan-bi", "cong-khai"):
            ma, bao, pcb, pck = self.chay(pha)
            self.assertEqual(ma, 1, pha)
            self.assertEqual(len(bao), 1)
            pcb.assert_not_called(); pck.assert_not_called()

    def test_thu_khong_chan(self):   # che do thu khong dang gi cong khai
        with mock.patch.object(chay, "pha_chuan_bi", return_value=0):
            cong = CongGia()
            with mock.patch.object(chay, "MOT_KENH", True), mock.patch.dict(os.environ, {"SG_KENH_BAT": ""}):
                self.assertEqual(chay.main(["--pha", "chuan-bi", "--dang", DANG, "--ngay", NGAY, "--che-do", "thu"], cong=cong), 0)

    def test_mac_dinh_luat_bat(self):
        self.assertIs(chay.MOT_KENH, True)


if __name__ == "__main__":
    unittest.main()
