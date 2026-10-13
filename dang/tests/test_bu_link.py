"""13/10: kiem-gio bu link TikTok (Zernio tra link cham -> so ghi link rong). Khong goi mang that."""
import os
import unittest
from unittest import mock

from dang import chay, zernio


class CongGia:
    def __init__(self, dong):
        self.dong, self.sua = dong, []

    def doc_dang(self, tu, den, che_do):
        self.hoi = (tu, den, che_do)
        return self.dong

    def cap_nhat_dang(self, ngay, dang, kenh, che_do, neu_trang_thai=None, **kw):
        self.sua.append((ngay, dang, kenh, che_do, neu_trang_thai, kw))
        return 1


DONG = [
    dict(ngay="2026-10-13", dang="tin-nhanh", kenh="tiktok", trang_thai="da_dang", link=None, id_bai="z1"),
    dict(ngay="2026-10-12", dang="keo-thom", kenh="tiktok", trang_thai="da_dang", link="https://x/co-roi", id_bai="z2"),
    dict(ngay="2026-10-13", dang="top5", kenh="tiktok", trang_thai="dang_dang", link=None, id_bai="z3"),
    dict(ngay="2026-10-13", dang="top5", kenh="fb", trang_thai="da_dang", link=None, id_bai="f1"),
]


class BuLink(unittest.TestCase):
    def test_chi_bu_dong_tiktok_da_dang_thieu_link(self):
        c = CongGia(DONG)
        with mock.patch.dict(os.environ, {"ZERNIO_KHOA": "k"}), \
                mock.patch.object(zernio, "lay_link", return_value="https://www.tiktok.com/@sangame.com.vn/video/1") as ll:
            self.assertEqual(chay.bu_link_tiktok(c, "2026-10-13", "that"), 1)
        ll.assert_called_once_with("k", "z1")
        self.assertEqual(c.hoi, ("2026-10-12", "2026-10-13", "that"))
        self.assertEqual(c.sua, [("2026-10-13", "tin-nhanh", "tiktok", "that", "da_dang",
                                  {"link": "https://www.tiktok.com/@sangame.com.vn/video/1"})])

    def test_chua_co_link_thi_khong_sua(self):
        c = CongGia(DONG)
        with mock.patch.dict(os.environ, {"ZERNIO_KHOA": "k"}), mock.patch.object(zernio, "lay_link", return_value=None):
            self.assertEqual(chay.bu_link_tiktok(c, "2026-10-13", "that"), 0)
        self.assertEqual(c.sua, [])

    def test_khong_khoa_khong_lam_gi(self):
        c = CongGia(DONG)
        with mock.patch.dict(os.environ, {"ZERNIO_KHOA": ""}), mock.patch.object(zernio, "lay_link") as ll:
            self.assertEqual(chay.bu_link_tiktok(c, "2026-10-13", "that"), 0)
        ll.assert_not_called()

    def test_loi_khong_nem(self):
        c = CongGia(DONG)
        c.doc_dang = mock.Mock(side_effect=RuntimeError("cong hong"))
        with mock.patch.dict(os.environ, {"ZERNIO_KHOA": "k"}):
            self.assertEqual(chay.bu_link_tiktok(c, "2026-10-13", "that"), 0)

    def test_lay_link_published(self):
        r = mock.Mock(status=200)
        r.json.return_value = {"post": {"_id": "z1", "status": "published",
                                        "platforms": [{"platformPostUrl": "https://www.tiktok.com/@a/video/9"}]}}
        with mock.patch.object(zernio.http, "gui", return_value=r):
            self.assertEqual(zernio.lay_link("k", "z1"), "https://www.tiktok.com/@a/video/9")

    def test_lay_link_chua_xong_hoac_loi_tra_none(self):
        r = mock.Mock(status=200)
        r.json.return_value = {"post": {"_id": "z1", "status": "publishing", "platforms": [{}]}}
        with mock.patch.object(zernio.http, "gui", return_value=r):
            self.assertIsNone(zernio.lay_link("k", "z1"))
        with mock.patch.object(zernio.http, "gui", side_effect=zernio.http.LoiMang("x")):
            self.assertIsNone(zernio.lay_link("k", "z1"))


if __name__ == "__main__":
    unittest.main()
