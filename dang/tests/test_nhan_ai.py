"""Nhan 'noi dung do AI tao' (giong doc AI): IG is_ai_generated, TikTok/Zernio video_made_with_ai, YouTube
containsSyntheticMedia (insert + update), dong nhan caption FB / text X. Mock http, khong goi mang that."""
import unittest
from unittest import mock

from dang import chung, ig, ntfy, x, yt, zernio
from dang.tests.gia_lap import Mang, P, tao_nc, TOKEN_GIA
from dang.tests.test_caption import nc as nc_caption, LOI_DANG

NHAN = "Video dùng giọng đọc AI."


class _Luu:
    def __call__(self, **kw):
        pass


def _ig_mang(lan_dau):
    m = Mang()
    m.them("POST", "/IGU1/media", lan_dau)
    m.them("GET", "/C1", P(body={"status_code": "FINISHED"}))
    return m


def _form_media(m):
    return [k["form"] for me, u, k in m.goi if me == "POST" and u.endswith("/IGU1/media")]


class IG(unittest.TestCase):
    def setUp(self):
        self.loi = []
        p = mock.patch.object(ntfy, "loi", lambda *a, **k: self.loi.append(a))
        p.start()
        self.addCleanup(p.stop)
        p = mock.patch.object(chung, "ngu", lambda s: None)
        p.start()
        self.addCleanup(p.stop)

    def test_container_co_is_ai_generated(self):
        m = _ig_mang(P(body={"id": "C1"}))
        with mock.patch("dang.http.gui", m):
            ig.chuan_bi(TOKEN_GIA["ig"], tao_nc(), _Luu())
        self.assertEqual(_form_media(m)[0]["is_ai_generated"], "true")
        self.assertEqual(self.loi, [])

    def test_tat_co_giong_ai_khong_co_co(self):
        m = _ig_mang(P(body={"id": "C1"}))
        with mock.patch("dang.http.gui", m), mock.patch.object(chung, "CO_GIONG_AI", False):
            ig.chuan_bi(TOKEN_GIA["ig"], tao_nc(), _Luu())
        self.assertNotIn("is_ai_generated", _form_media(m)[0])

    def test_400_nhac_is_ai_generated_thu_lai_khong_co_va_bao(self):
        loi400 = P(400, {"error": {"message": "(#100) Param is_ai_generated is not supported", "code": 100}})
        m = _ig_mang([loi400, P(body={"id": "C1"})])
        with mock.patch("dang.http.gui", m):
            r = ig.chuan_bi(TOKEN_GIA["ig"], tao_nc(), _Luu())
        self.assertEqual(r["id_container"], "C1")
        forms = _form_media(m)
        self.assertEqual(len(forms), 2)
        self.assertIn("is_ai_generated", forms[0])
        self.assertNotIn("is_ai_generated", forms[1])
        self.assertEqual(len(self.loi), 1)
        self.assertIn("mất nhãn AI", self.loi[0][0])

    def test_loi_quyen_khong_thu_lai(self):
        m = _ig_mang(P(400, {"error": {"message": "(#10) Permission denied", "code": 10}}))
        with mock.patch("dang.http.gui", m):
            with self.assertRaises(chung.LoiDang):
                ig.chuan_bi(TOKEN_GIA["ig"], tao_nc(), _Luu())
        self.assertEqual(len(_form_media(m)), 1)
        self.assertEqual(self.loi, [])

    def test_loi_500_khong_thu_lai(self):
        m = _ig_mang(P(500, {}))
        with mock.patch("dang.http.gui", m):
            with self.assertRaises(chung.LoiDang):
                ig.chuan_bi(TOKEN_GIA["ig"], tao_nc(), _Luu())
        self.assertEqual(len(_form_media(m)), 1)


class TikTokZernio(unittest.TestCase):
    def _body(self):
        m = Mang().them("POST", "/v1/posts", P(201, {"post": {"_id": "P1", "status": "published", "platforms": [{}]}}))
        with mock.patch("dang.http.gui", m), mock.patch.object(chung, "ngu", lambda s: None):
            zernio.tao_bai("KHOA", tao_nc(), "ACC", "https://cdn.example/v.mp4")
        return [k["json_body"] for me, u, k in m.goi if u.endswith("/v1/posts")][0]

    def test_co_video_made_with_ai(self):
        self.assertIs(self._body()["tiktokSettings"]["video_made_with_ai"], True)

    def test_tat_khong_co_co(self):
        with mock.patch.object(chung, "CO_GIONG_AI", False):
            self.assertNotIn("video_made_with_ai", self._body()["tiktokSettings"])


class YouTube(unittest.TestCase):
    def setUp(self):
        yt._cache.clear()

    def _mang(self):
        return Mang().them("POST", "oauth2.googleapis.com", P(body={"access_token": "ya29.GIA_ACCESS_123456"}))

    def _insert(self):
        m = self._mang()
        m.them("POST", "upload/youtube", P(headers={"Location": "https://up.example/s"}))
        m.them("PUT", "up.example", P(200, {"id": "YV1"}))
        with mock.patch("dang.http.gui", m):
            yt.chuan_bi(TOKEN_GIA["youtube"], tao_nc("that"), lambda **k: None)
        return [k["json_body"] for me, u, k in m.goi if "upload/youtube" in u][0]["status"]

    def _update(self):
        m = self._mang()
        m.them("GET", "youtube/v3/videos", P(body={"items": [{"status": {"privacyStatus": "private"}}]}))
        m.them("PUT", "youtube/v3/videos", P(body={}))
        with mock.patch("dang.http.gui", m):
            yt.cong_khai(TOKEN_GIA["youtube"], tao_nc("that"), {"id_tai": "YV1"})
        return [k["json_body"] for me, u, k in m.goi if me == "PUT" and "youtube/v3/videos" in u][0]["status"]

    def test_insert_va_update_deu_co_co(self):
        self.assertIs(self._insert()["containsSyntheticMedia"], True)
        st = self._update()
        self.assertIs(st["containsSyntheticMedia"], True)
        self.assertEqual(st["privacyStatus"], "public")

    def test_tat_khong_co_co(self):
        with mock.patch.object(chung, "CO_GIONG_AI", False):
            self.assertNotIn("containsSyntheticMedia", self._insert())
            self.assertNotIn("containsSyntheticMedia", self._update())


class Caption(unittest.TestCase):
    def test_fb_dong_cuoi_la_nhan(self):
        for dang in LOI_DANG:
            s = nc_caption(dang).caption_fb()
            self.assertTrue(s.endswith(NHAN), dang)

    def test_fb_noi_dung_dai_van_giu_nhan_trong_tran(self):
        ld = dict(LOI_DANG["top5"], mo_ta="x" * 3000)
        s = nc_caption("top5", ld=ld).caption_fb()
        self.assertTrue(s.endswith(NHAN))
        self.assertLessEqual(len(s), 2200)

    def test_x_co_nhan_va_trong_tran_ke_ca_noi_dung_dai(self):
        for dang in LOI_DANG:
            s = x.text_x(nc_caption(dang))
            self.assertTrue(s.endswith(NHAN), dang)
            self.assertLessEqual(x.do_dai_x(s), 280)
        ld = dict(LOI_DANG["keo-thom"], tieu_de="Tên game rất dài " * 20 + " giảm 60% ở PS Store Mỹ: còn 560.000đ")
        s = x.text_x(nc_caption("keo-thom", ld=ld))
        self.assertTrue(s.endswith(NHAN))
        self.assertLessEqual(x.do_dai_x(s), 280)

    def test_tat_khong_co_dong_nhan(self):
        with mock.patch.object(chung, "CO_GIONG_AI", False):
            for dang in LOI_DANG:
                self.assertNotIn(NHAN, nc_caption(dang).caption_fb())
                self.assertNotIn(NHAN, x.text_x(nc_caption(dang)))


if __name__ == "__main__":
    unittest.main()
