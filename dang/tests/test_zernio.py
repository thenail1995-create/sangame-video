"""Zernio (TikTok cong khai): mock http, khong goi mang that, khong ngu that."""
import io
import contextlib
import os
import unittest
from unittest import mock

from dang import chay, chung, http, ntfy, zernio
from dang.chung import LoiDang
from dang.tests import gia_lap as g
from dang.tests.gia_lap import Mang, P, NGAY, DANG, cong_day_du, tao_nc

KHOA = "zk_LIVE_BIMAT_1234567890abcdef"
UPLOAD = "https://storage.example/up/abc?X-Sig=BIMATUPLOAD123456"
ACC = zernio.ACC_MAC_DINH
TK = {"_id": ACC, "platform": "tiktok", "username": "sangame.com.vn", "isActive": True}
CI = {"creator": {"canPostMore": True}, "privacyLevels": [{"value": "PUBLIC_TO_EVERYONE", "label": "Public To Everyone"}]}   # dang that (API 12/10)
LINK = "https://www.tiktok.com/@sangame.com.vn/video/123"


def post(status, **kw):
    return {"_id": "POST1", "status": status, "platforms": [{"platform": "tiktok", "platformPostUrl": LINK}], **kw}


def mang_chuan(tao=None, tk=None, ci=None, poll=None):
    m = Mang()
    m.them("GET", "/accounts/" + ACC + "/tiktok/creator-info", P(body=ci or CI))
    m.them("GET", "/accounts", P(body={"accounts": [tk or TK]}))
    m.them("POST", "/media/presign", P(body={"uploadUrl": UPLOAD, "publicUrl": "https://cdn.example/v.mp4", "expiresIn": 3600}))
    m.them("PUT", "storage.example", P(200))
    m.them("POST", "/v1/posts", tao if tao is not None else P(201, {"post": post("published")}))
    if poll is not None:
        m.them("GET", "/v1/posts/POST1", poll)
    return m


class Zer(unittest.TestCase):
    def setUp(self):
        self.cong = cong_day_du()
        self.nc = tao_nc(cong=self.cong)
        self.nc.manifest_sha = "SHA1"
        self.ngu = []
        self.hop = mock.Mock(return_value={"id_tai": "PUB", "id_bai": "PUB", "link": None})
        self.ntfy = []
        for p in (mock.patch.dict(os.environ, {"ZERNIO_KHOA": KHOA}),
                  mock.patch.object(chung, "bay_gio", lambda: g.GIO_DANG),
                  mock.patch.object(chung, "ngu", lambda s: self.ngu.append(s)),
                  mock.patch.object(chay.tiktok, "hop_thu", self.hop),
                  mock.patch.object(chay.tiktok, "danh_tinh", lambda tk, nc=None: "TTO1"),
                  mock.patch.object(ntfy, "loi", lambda *a, **k: self.ntfy.append(a))):
            p.start()
            self.addCleanup(p.stop)
        os.environ.pop("ZERNIO_TIKTOK_ACC", None)
        self.dich = g.DICH_DU

    def chay(self, m):
        with mock.patch.object(http, "gui", m):
            return chay.cong_khai_kenh("tiktok", self.nc, self.dich, self.cong, None, [])

    def tt(self):
        return self.cong.trang_thai("tiktok")

    def test_thanh_cong(self):
        m = mang_chuan()
        kq, ket = self.chay(m)
        self.assertEqual(kq, "da_dang")
        self.assertEqual(ket["link"], LINK)
        self.assertEqual(self.tt(), "da_dang")
        self.assertEqual(self.cong.dong[(NGAY, DANG, "tiktok", "that")]["link"], LINK)
        self.assertEqual(self.cong.dong[(NGAY, DANG, "tiktok", "that")]["id_bai"], "POST1")
        self.hop.assert_not_called()
        self.assertEqual(m.dem("POST", "/v1/posts"), 1)
        # body bai: cong khai, dung tai khoan, dung video, publishNow
        body = [kw for mt, u, kw in m.goi if mt == "POST" and u.endswith("/v1/posts")][0]["json_body"]
        self.assertEqual(body["tiktokSettings"]["privacy_level"], "PUBLIC_TO_EVERYONE")
        self.assertEqual(body["platforms"][0]["accountId"], ACC)
        self.assertEqual(body["mediaItems"][0]["url"], "https://cdn.example/v.mp4")
        self.assertTrue(body["publishNow"])
        # PUT video khong gui khoa Zernio
        put = [kw for mt, u, kw in m.goi if mt == "PUT"][0]
        self.assertNotIn("Authorization", put["headers"])
        # khong can token TikTok: khong goi API TikTok
        self.assertNotIn("tiktokapis", m.tat_ca_text())

    def test_207_failed_du_phong_hop_thu(self):
        m = mang_chuan(tao=P(207, {"post": post("failed")}))
        kq, ket = self.chay(m)
        self.assertEqual(self.hop.call_count, 1)
        self.assertEqual(ket["id_tai"], "PUB")
        self.assertEqual(self.tt(), "da_dang")
        self.assertTrue(self.ntfy)

    def test_207_partial_khong_ro_khong_hop_thu(self):
        m = mang_chuan(tao=P(207, {"post": post("partial")}))
        with self.assertRaises(LoiDang) as cm:
            self.chay(m)
        self.assertTrue(cm.exception.khong_ro)
        self.assertEqual(self.tt(), "khong_ro")
        self.hop.assert_not_called()

    def test_409_trung_khong_ro(self):
        m = mang_chuan(tao=P(409, {"error": "duplicate", "existingPostId": "P0"}))
        with self.assertRaises(LoiDang) as cm:
            self.chay(m)
        self.assertTrue(cm.exception.khong_ro)
        self.assertEqual(self.tt(), "khong_ro")
        self.hop.assert_not_called()

    def test_5xx_hai_lan_roi_200_mot_bai_cung_idempotency(self):
        m = mang_chuan(tao=[P(502), P(503), P(201, {"post": post("published")})])
        kq, _ = self.chay(m)
        self.assertEqual(kq, "da_dang")
        lan = [kw for mt, u, kw in m.goi if mt == "POST" and u.endswith("/v1/posts")]
        self.assertEqual(len(lan), 3)
        keys = {kw["headers"]["Idempotency-Key"] for kw in lan}
        self.assertEqual(keys, {zernio.khoa_lap(self.nc)})
        self.assertEqual(self.hop.call_count, 0)

    def test_timeout_het_3_lan_khong_ro(self):
        m = mang_chuan(tao=http.LoiMang("POST x: TimeoutError"))
        with self.assertRaises(LoiDang) as cm:
            self.chay(m)
        self.assertTrue(cm.exception.khong_ro)
        self.assertEqual(m.dem("POST", "/v1/posts"), 3)
        self.assertEqual(self.tt(), "khong_ro")
        self.hop.assert_not_called()

    def test_4xx_chua_tao_bai_du_phong(self):
        m = mang_chuan(tao=P(400, {"error": "bad"}))
        self.chay(m)
        self.assertEqual(self.hop.call_count, 1)

    def test_tai_khoan_sai_username_du_phong(self):
        m = mang_chuan(tk=dict(TK, username="khac"))
        self.chay(m)
        self.assertEqual(m.dem("POST", "/v1/posts"), 0)
        self.assertEqual(self.hop.call_count, 1)

    def test_tai_khoan_khong_active_du_phong(self):
        m = mang_chuan(tk=dict(TK, isActive=False))
        self.chay(m)
        self.assertEqual(m.dem("POST", "/v1/posts"), 0)
        self.assertEqual(self.hop.call_count, 1)

    def test_creator_info_thieu_public_du_phong(self):
        m = mang_chuan(ci={"creator": {"canPostMore": True}, "privacyLevels": [{"value": "SELF_ONLY", "label": "Self Only"}]})
        self.chay(m)
        self.assertEqual(m.dem("POST", "/v1/posts"), 0)
        self.assertEqual(self.hop.call_count, 1)

    def test_poll_pending_roi_published(self):
        m = mang_chuan(tao=P(201, {"post": post("pending")}),
                       poll=[P(200, {"post": post("processing")}), P(200, {"post": post("published")})])
        kq, ket = self.chay(m)
        self.assertEqual(kq, "da_dang")
        self.assertEqual(ket["link"], LINK)
        self.assertEqual(m.dem("GET", "/v1/posts/POST1"), 2)
        self.assertEqual(self.ngu, [15, 15])

    def test_poll_qua_10_phut_khong_ro(self):
        m = mang_chuan(tao=P(201, {"post": post("pending")}), poll=P(200, {"post": post("publishing")}))
        with self.assertRaises(LoiDang) as cm:
            self.chay(m)
        self.assertTrue(cm.exception.khong_ro)
        self.assertEqual(sum(self.ngu), 600)
        self.assertEqual(self.tt(), "khong_ro")
        self.hop.assert_not_called()

    def test_poll_failed_du_phong(self):
        m = mang_chuan(tao=P(201, {"post": post("pending")}), poll=P(200, {"post": post("failed")}))
        self.chay(m)
        self.assertEqual(self.hop.call_count, 1)

    def test_khong_co_khoa_duong_cu(self):
        os.environ.pop("ZERNIO_KHOA")
        m = Mang()
        kq, ket = self.chay(m)
        self.assertEqual(self.hop.call_count, 1)
        self.assertEqual(m.goi, [])
        self.assertEqual(kq, "da_dang")

    def test_che_do_thu_co_khoa_van_vao_hop_thu_khong_goi_zernio(self):
        # 12/10 Opus: Zernio dang CONG KHAI that - che do thu tuyet doi khong di duong nay
        self.nc.che_do = "thu"
        m = mang_chuan()
        kq, _ = self.chay(m)
        self.assertEqual(self.hop.call_count, 1)
        self.assertFalse(any("zernio.com" in str(c) for c in m.goi))
        self.assertEqual(kq, "da_dang")

    def test_da_co_dong_khong_goi_mang(self):
        self.cong.giu_dang(NGAY, DANG, "tiktok", "that")
        m = mang_chuan()
        kq, _ = self.chay(m)
        self.assertEqual(kq, "bo_qua")
        self.assertEqual(m.goi, [])

    def test_khoa_khong_lo_trong_log_va_loi(self):
        buf = io.StringIO()
        m = mang_chuan(tao=P(207, {"post": post("partial")}))
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            with self.assertRaises(LoiDang) as cm:
                self.chay(m)
            chung.log(f"thu {KHOA} {UPLOAD}")
        self.assertNotIn(KHOA, buf.getvalue() + str(cm.exception))
        self.assertNotIn("BIMATUPLOAD", buf.getvalue() + str(cm.exception))
        self.assertIn("***", buf.getvalue())
        self.assertNotIn(KHOA, str(self.cong.dong))


if __name__ == "__main__":
    unittest.main()
