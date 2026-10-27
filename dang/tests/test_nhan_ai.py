"""Nhan 'noi dung do AI tao' (giong doc AI): FB is_ai_generated (finish), IG is_ai_generated (container), TikTok/Zernio
video_made_with_ai, YouTube containsSyntheticMedia (insert + update, bang chung co trong phan hoi), dong nhan caption FB / text X.
Luat Hao 27/10: Meta tu choi nhan -> LOI, khong co duong lui dang khong nhan. Mock http, khong goi mang that."""
import contextlib
import io
import os
import unittest
from unittest import mock

from dang import chay, chung, fb, http, ig, ntfy, x, yt, zernio
from dang.tests.gia_lap import Mang, P, tao_nc, TOKEN_GIA, NGAY, DANG
from dang.tests.test_caption import nc as nc_caption, LOI_DANG
from dang.tests.test_dieu_phoi import Khung

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

    def test_400_nhac_is_ai_generated_la_loi_khong_thu_lai_khong_nhan(self):
        loi400 = P(400, {"error": {"message": "(#100) Param is_ai_generated is not supported", "code": 100}})
        m = _ig_mang([loi400, P(body={"id": "C1"})])
        with mock.patch("dang.http.gui", m):
            with self.assertRaises(chung.LoiDang) as c:
                ig.chuan_bi(TOKEN_GIA["ig"], tao_nc(), _Luu())
        self.assertFalse(c.exception.khong_ro)          # chac chan chua tao container
        forms = _form_media(m)
        self.assertEqual(len(forms), 1)                 # KHONG tao lai container khong nhan
        self.assertEqual(forms[0]["is_ai_generated"], "true")
        self.assertEqual(len(self.loi), 1)
        self.assertIn("IG từ chối nhãn AI", self.loi[0][0])

    def test_tham_container_thuan(self):
        t = ig.tham_container("https://v/a.mp4", None, "cap")
        self.assertEqual(t, {"media_type": "REELS", "video_url": "https://v/a.mp4", "caption": "cap", "share_to_feed": "true",
                             "is_ai_generated": "true"})
        self.assertEqual(ig.tham_container("https://v/a.mp4", "https://v/a.jpg", "cap")["cover_url"], "https://v/a.jpg")
        with mock.patch.object(chung, "CO_GIONG_AI", False):
            self.assertNotIn("is_ai_generated", ig.tham_container("u", "c", "cap"))

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


class FB(unittest.TestCase):
    def setUp(self):
        self.loi = []
        for p in (mock.patch.object(ntfy, "loi", lambda *a, **k: self.loi.append(a)), mock.patch.object(chung, "ngu", lambda s: None)):
            p.start()
            self.addCleanup(p.stop)

    def _mang(self, finish=None):
        m = Mang()
        m.them("GET", "/me", P(body={"id": "PAGE1"}))
        m.them("POST", "/PAGE1/video_reels", lambda me, u, k: P(body={"video_id": "V1"}) if k["form"]["upload_phase"] == "start"
               else (finish(k) if finish else P(body={"success": True})))
        m.them("POST", "rupload.facebook.com", P(body={"success": True}))
        m.them("GET", "/V1", P(body={"status": {"uploading_phase": {"status": "complete"}}, "published": False}))
        m.them("POST", "/V1/thumbnails", P(body={"success": True}))
        return m

    def _finish_forms(self, m):
        return [k["form"] for me, u, k in m.goi if "video_reels" in u and k["form"]["upload_phase"] == "finish"]

    def test_draft_va_published_deu_co_is_ai_generated(self):
        m = self._mang()
        with mock.patch("dang.http.gui", m):
            fb.chuan_bi(TOKEN_GIA["fb"], tao_nc("thu"), _Luu())          # che_do thu = finish DRAFT
        f = self._finish_forms(m)
        self.assertEqual((f[0]["video_state"], f[0]["is_ai_generated"]), ("DRAFT", "true"))
        m = self._mang()
        with mock.patch("dang.http.gui", m):
            fb.cong_khai(TOKEN_GIA["fb"], tao_nc("that"), {"id_tai": "V1"})
        f = self._finish_forms(m)
        self.assertEqual((f[0]["video_state"], f[0]["is_ai_generated"]), ("PUBLISHED", "true"))

    def test_tat_co_giong_ai_khong_co_co(self):
        m = self._mang()
        with mock.patch("dang.http.gui", m), mock.patch.object(chung, "CO_GIONG_AI", False):
            fb.cong_khai(TOKEN_GIA["fb"], tao_nc("that"), {"id_tai": "V1"})
        self.assertNotIn("is_ai_generated", self._finish_forms(m)[0])

    def test_400_nhac_is_ai_generated_nem_loi_chac_chan_chua_dang_goi_finish_1_lan(self):
        loi400 = lambda k: P(400, {"error": {"message": "(#100) Param is_ai_generated is not supported", "code": 100}})
        for che_do, ham in (("that", lambda m: fb.cong_khai(TOKEN_GIA["fb"], tao_nc("that"), {"id_tai": "V1"})),
                            ("thu", lambda m: fb.chuan_bi(TOKEN_GIA["fb"], tao_nc("thu"), _Luu()))):
            self.loi.clear()
            m = self._mang(loi400)
            with mock.patch("dang.http.gui", m):
                with self.assertRaises(chung.LoiDang) as c:
                    ham(m)
            self.assertFalse(c.exception.khong_ro, che_do)
            self.assertEqual(len(self._finish_forms(m)), 1, che_do)       # khong thu lai khong nhan
            self.assertEqual(len(self.loi), 1, che_do)
            self.assertIn("FB từ chối nhãn AI", self.loi[0][0])
            self.assertEqual(m.dem("POST", "thumbnails"), 0)

    def test_loi_khac_khong_bao_nhan_ai(self):
        m = self._mang(lambda k: P(400, {"error": {"message": "(#10) Permission denied", "code": 10}}))
        with mock.patch("dang.http.gui", m):
            with self.assertRaises(chung.LoiDang):
                fb.cong_khai(TOKEN_GIA["fb"], tao_nc("that"), {"id_tai": "V1"})
        self.assertEqual(self.loi, [])

    def test_tham_finish_thuan(self):
        d = fb.tham_finish("V1", "mo ta", "DRAFT")
        self.assertEqual(d, {"upload_phase": "finish", "video_id": "V1", "video_state": "DRAFT", "description": "mo ta", "is_ai_generated": "true"})
        s = fb.tham_finish("V1", "mo ta", "SCHEDULED", 1795000000)
        self.assertEqual((s["video_state"], s["scheduled_publish_time"], s["is_ai_generated"]), ("SCHEDULED", "1795000000", "true"))
        self.assertNotIn("scheduled_publish_time", fb.tham_finish("V1", "x", "PUBLISHED"))
        with mock.patch.object(chung, "CO_GIONG_AI", False):
            self.assertNotIn("is_ai_generated", fb.tham_finish("V1", "x", "SCHEDULED", 1))


class YouTubeXacNhanCo(unittest.TestCase):
    """S1/S2: bang chung co containsSyntheticMedia trong phan hoi insert / update; thieu = khong dat bia, khong cong khai."""
    CO = {"status": {"containsSyntheticMedia": True}}

    def setUp(self):
        yt._cache.clear()
        p = mock.patch.object(chung, "ngu", lambda s: None)
        p.start()
        self.addCleanup(p.stop)

    def _mang(self, insert_res, put=None):
        m = Mang().them("POST", "oauth2.googleapis.com", P(body={"access_token": "ya29.GIA_ACCESS_123456"}))
        m.them("POST", "upload/youtube", P(headers={"Location": "https://up.example/s"}))
        m.them("PUT", "up.example", P(200, insert_res))
        m.them("POST", "youtube/v3/thumbnails/set", P(200, {"kind": "youtube#thumbnailSetResponse"}))
        if put is not None:
            m.them("PUT", "youtube/v3/videos", put)
        return m

    def _chuan_bi(self, m):
        with mock.patch("dang.http.gui", m):
            return yt.chuan_bi(TOKEN_GIA["youtube"], tao_nc("that"), _Luu())

    def _puts(self, m):
        return [k["json_body"]["status"]["privacyStatus"] for me, u, k in m.goi if me == "PUT" and "youtube/v3/videos" in u]

    def test_insert_co_co_true_khong_goi_update(self):
        m = self._mang({"id": "YV1", **self.CO})
        r = self._chuan_bi(m)
        self.assertEqual((r["id_tai"], r["nhan_ai"], r["nhan_ai_tu"], r["bia"]), ("YV1", True, "insert", True))
        self.assertEqual(self._puts(m), [])
        self.assertEqual(m.dem("POST", "upload/youtube/v3/videos"), 1)

    def test_insert_thieu_co_update_private_tra_co(self):
        m = self._mang({"id": "YV1"}, P(body=self.CO))
        r = self._chuan_bi(m)
        self.assertEqual((r["nhan_ai"], r["nhan_ai_tu"]), (True, "update"))
        self.assertEqual(self._puts(m), ["private"])                      # van rieng tu
        self.assertEqual(m.dem("POST", "thumbnails/set"), 1)
        self.assertEqual(m.dem("POST", "upload/youtube/v3/videos"), 1)

    def test_khong_xac_nhan_duoc_la_khong_ro_khong_dat_bia_khong_tai_lai(self):
        for ten, put in (("update thieu co", P(body={"status": {"privacyStatus": "private"}})),
                         ("update co False", P(body={"status": {"containsSyntheticMedia": False}})),
                         ("update 400", P(400, {"error": {"message": "bad"}})),
                         ("update 500", P(500, {})),
                         ("loi mang", http.LoiMang("PUT videos: timeout"))):
            luu = []
            m = self._mang({"id": "YV1"}, put)
            with mock.patch("dang.http.gui", m):
                with self.assertRaises(chung.LoiDang) as c:
                    yt.chuan_bi(TOKEN_GIA["youtube"], tao_nc("that"), lambda **k: luu.append(k))
            self.assertTrue(c.exception.khong_ro, ten)
            self.assertIn("YV1", str(c.exception), ten)
            self.assertEqual(luu, [{"id_tai": "YV1"}], ten)                # id da ghi so truoc khi xac nhan
            self.assertEqual(m.dem("POST", "thumbnails/set"), 0, ten)
            self.assertEqual(m.dem("POST", "upload/youtube/v3/videos"), 1, ten)

    def test_tat_co_giong_ai_khong_xac_nhan(self):
        m = self._mang({"id": "YV1"})
        with mock.patch.object(chung, "CO_GIONG_AI", False):
            r = self._chuan_bi(m)
        self.assertNotIn("nhan_ai", r)
        self.assertEqual(self._puts(m), [])

    def test_cong_khai_doc_co_tu_phan_hoi_update_public(self):
        m = self._mang({}, P(body=self.CO))
        m.them("GET", "youtube/v3/videos", P(body={"items": [{"status": {"privacyStatus": "private"}}]}))
        with mock.patch("dang.http.gui", m):
            r = yt.cong_khai(TOKEN_GIA["youtube"], tao_nc("that"), {"id_tai": "YV1"})
        self.assertIs(r["nhan_ai"], True)
        self.assertEqual(self._puts(m), ["public"])

    def test_cong_khai_phan_hoi_thieu_co_keo_ve_private_va_nem_khong_ro(self):
        put = [P(body={"status": {"privacyStatus": "public"}}), P(body={"status": {"privacyStatus": "private"}})]
        m = self._mang({}, put)
        m.them("GET", "youtube/v3/videos", P(body={"items": [{"status": {"privacyStatus": "private"}}]}))
        with mock.patch("dang.http.gui", m):
            with self.assertRaises(chung.LoiDang) as c:
                yt.cong_khai(TOKEN_GIA["youtube"], tao_nc("that"), {"id_tai": "YV1"})
        self.assertTrue(c.exception.khong_ro)
        self.assertIn("kéo về riêng tư", str(c.exception))
        self.assertEqual(self._puts(m), ["public", "private"])

    def test_cong_khai_keo_ve_private_that_bai_bao_dang_cong_khai(self):
        put = [P(body={"status": {"privacyStatus": "public"}}), P(500, {})]
        m = self._mang({}, put)
        m.them("GET", "youtube/v3/videos", P(body={"items": [{"status": {"privacyStatus": "private"}}]}))
        with mock.patch("dang.http.gui", m):
            with self.assertRaises(chung.LoiDang) as c:
                yt.cong_khai(TOKEN_GIA["youtube"], tao_nc("that"), {"id_tai": "YV1"})
        self.assertTrue(c.exception.khong_ro)
        self.assertIn("THẤT BẠI", str(c.exception))

    def _public_san(self, put):
        m = self._mang({}, put)
        m.them("GET", "youtube/v3/videos", P(body={"items": [{"status": {"privacyStatus": "public"}}]}))
        return m

    def test_da_public_tu_truoc_goi_lai_put_public_va_doc_co(self):
        m = self._public_san(P(body=self.CO))
        with mock.patch("dang.http.gui", m):
            r = yt.cong_khai(TOKEN_GIA["youtube"], tao_nc("that"), {"id_tai": "YV1"})
        self.assertIs(r["nhan_ai"], True)
        self.assertEqual(self._puts(m), ["public"])

    def test_da_public_ma_khong_co_bang_chung_keo_ve_private(self):
        for put in ([P(body={"status": {"privacyStatus": "public"}}), P(body={})], [http.LoiMang("PUT: timeout"), P(body={})], [P(500, {}), P(body={})]):
            m = self._public_san(put)
            with mock.patch("dang.http.gui", m):
                with self.assertRaises(chung.LoiDang) as c:
                    yt.cong_khai(TOKEN_GIA["youtube"], tao_nc("that"), {"id_tai": "YV1"})
            self.assertTrue(c.exception.khong_ro)
            self.assertEqual(self._puts(m)[-1], "private")

    def test_put_public_5xx_roi_privacy_public_van_doi_bang_chung_co(self):
        m = self._mang({}, [P(503, {}), P(body=self.CO)])
        m.them("GET", "youtube/v3/videos", [P(body={"items": [{"status": {"privacyStatus": "private"}}]}),
                                            P(body={"items": [{"status": {"privacyStatus": "public"}}]})])
        with mock.patch("dang.http.gui", m):
            r = yt.cong_khai(TOKEN_GIA["youtube"], tao_nc("that"), {"id_tai": "YV1"})
        self.assertIs(r["nhan_ai"], True)
        self.assertEqual(self._puts(m), ["public", "public"])
        # cung duong do nhung PUT lan 2 thieu co -> keo ve private
        m = self._mang({}, [P(503, {}), P(body={}), P(body={})])
        m.them("GET", "youtube/v3/videos", [P(body={"items": [{"status": {"privacyStatus": "private"}}]}),
                                            P(body={"items": [{"status": {"privacyStatus": "public"}}]})])
        with mock.patch("dang.http.gui", m):
            with self.assertRaises(chung.LoiDang) as c:
                yt.cong_khai(TOKEN_GIA["youtube"], tao_nc("that"), {"id_tai": "YV1"})
        self.assertTrue(c.exception.khong_ro)
        self.assertEqual(self._puts(m)[-1], "private")

    def test_tat_co_giong_ai_da_public_khong_put(self):
        m = self._public_san(P(body={}))
        with mock.patch("dang.http.gui", m), mock.patch.object(chung, "CO_GIONG_AI", False):
            r = yt.cong_khai(TOKEN_GIA["youtube"], tao_nc("that"), {"id_tai": "YV1"})
        self.assertNotIn("nhan_ai", r)
        self.assertEqual(self._puts(m), [])

    def test_tags_youtube_khong_doi_so_voi_truoc_bo_tag_ig(self):
        m = self._mang({"id": "YV1", **self.CO})
        self._chuan_bi(m)
        body = [k["json_body"] for me, u, k in m.goi if "upload/youtube/v3/videos" in u][0]
        self.assertEqual(body["snippet"]["tags"], ["PlayStation", "PS5", "SănGame", "GiảmGiá"])   # tao_nc: manifest khong co ten game
        self.assertIn("PlayStation", body["snippet"]["tags"])
        self.assertIn("GiảmGiá", body["snippet"]["tags"])
        self.assertLessEqual(len(body["snippet"]["tags"]), 15)


class TichHopYouTubeQuaChay(Khung):
    """S6: chay.pha_chuan_bi + pha_cong_khai voi yt THAT (chi gia HTTP + cong): ghi so dung, log co nhan_ai=True."""

    def test_chuan_bi_roi_cong_khai_ghi_so_va_log_nhan_ai(self):
        yt._cache.clear()
        for p in (mock.patch.dict(chay.MOD, {"youtube": yt}), mock.patch.dict(os.environ, {"SG_KENH_BAT": "youtube"})):
            p.start()
            self.addCleanup(p.stop)
        m = Mang().them("POST", "oauth2.googleapis.com", P(body={"access_token": "ya29.GIA_ACCESS_123456"}))
        m.them("GET", "youtube/v3/channels", P(body={"items": [{"id": "UCYT1"}]}))
        m.them("POST", "upload/youtube", P(headers={"Location": "https://up.example/s"}))
        m.them("PUT", "up.example", P(200, {"id": "YV1"}))                                   # insert KHONG tra status
        m.them("PUT", "youtube/v3/videos", P(body={"status": {"containsSyntheticMedia": True}}))
        m.them("GET", "youtube/v3/videos", P(body={"items": [{"status": {"privacyStatus": "private"}}]}))
        m.them("POST", "youtube/v3/thumbnails/set", P(200, {}))
        out = io.StringIO()
        with mock.patch("dang.http.gui", m), contextlib.redirect_stdout(out):
            self.assertEqual(self.chay("chuan-bi"), 0)
            self.assertEqual(self.cong.trang_thai("youtube"), "chuan_bi_xong")
            self.assertEqual(self.cong.dong[(NGAY, DANG, "youtube", "that")]["id_tai"], "YV1")
            self.assertIn("youtube:  bia=True nhan_ai=True", out.getvalue())
            self.assertEqual(self.chay("cong-khai"), 0)
        self.assertEqual(self.cong.trang_thai("youtube"), "da_dang")
        self.assertIn("youtube: nhan_ai=True", out.getvalue())
        self.assertEqual(m.dem("POST", "upload/youtube/v3/videos"), 1)
        self.assertEqual([k["json_body"]["status"]["privacyStatus"] for me, u, k in m.goi if me == "PUT" and "youtube/v3/videos" in u],
                         ["private", "public"])


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
        m.them("PUT", "up.example", P(200, {"id": "YV1", "status": {"containsSyntheticMedia": True}}))
        with mock.patch("dang.http.gui", m):
            yt.chuan_bi(TOKEN_GIA["youtube"], tao_nc("that"), lambda **k: None)
        return [k["json_body"] for me, u, k in m.goi if "upload/youtube/v3/videos" in u][0]["status"]

    def _update(self):
        m = self._mang()
        m.them("GET", "youtube/v3/videos", P(body={"items": [{"status": {"privacyStatus": "private"}}]}))
        m.them("PUT", "youtube/v3/videos", P(body={"status": {"containsSyntheticMedia": True}}))
        with mock.patch("dang.http.gui", m):
            yt.cong_khai(TOKEN_GIA["youtube"], tao_nc("that"), {"id_tai": "YV1"})
        return [k["json_body"] for me, u, k in m.goi if me == "PUT" and "youtube/v3/videos" in u][0]["status"]

    def test_insert_va_update_deu_co_co(self):
        self.assertEqual(self._insert(), {"privacyStatus": "private", "selfDeclaredMadeForKids": False,
                                          "embeddable": True, "publicStatsViewable": True, "license": "youtube", "containsSyntheticMedia": True})
        self.assertEqual(self._update(), {"privacyStatus": "public", "selfDeclaredMadeForKids": False,
                                          "embeddable": True, "publicStatsViewable": True, "license": "youtube", "containsSyntheticMedia": True})

    def test_update_giu_nhung_va_luot_xem(self):  # 15/10: update ghi de status -> thieu truong la YouTube tat nhung
        for st in (self._insert(), self._update()):
            self.assertIs(st["embeddable"], True)
            self.assertIs(st["publicStatsViewable"], True)
            self.assertEqual(st["license"], "youtube")

    def test_tat_khong_co_co(self):
        with mock.patch.object(chung, "CO_GIONG_AI", False):
            self.assertEqual(self._insert(), {"privacyStatus": "private", "selfDeclaredMadeForKids": False, "embeddable": True, "publicStatsViewable": True, "license": "youtube"})
            self.assertEqual(self._update(), {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "embeddable": True, "publicStatsViewable": True, "license": "youtube"})


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
