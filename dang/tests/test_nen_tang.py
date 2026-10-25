import unittest
from unittest import mock

from dang import chung, fb, ig, threads, tiktok, yt
from dang.tests.gia_lap import Mang, P, tao_nc, TOKEN_GIA


class LuuGia:
    def __init__(self):
        self.ids = {}

    def __call__(self, **kw):
        self.ids.update(kw)


def patch_chung():
    return mock.patch.object(chung, "ngu", lambda s: None)


class TestFB(unittest.TestCase):
    def mang(self, **kw):
        m = Mang()
        m.them("GET", "/me", P(body={"id": "PAGE1"}))
        m.them("POST", "/PAGE1/video_reels", lambda me, u, k: P(body={"video_id": "V1"}) if k["form"]["upload_phase"] == "start"
               else P(body={"success": True}))
        m.them("POST", "rupload.facebook.com", P(body={"success": True}))
        m.them("GET", "/V1", P(body={"status": {"uploading_phase": {"status": "complete"}}, "published": False}))
        m.them("POST", "/V1/thumbnails", P(body={"success": True}))
        return m

    def test_that_chuan_bi_khong_finish_roi_cong_khai_finish_va_bia(self):
        nc, m, luu = tao_nc("that"), self.mang(), LuuGia()
        with mock.patch("dang.http.gui", m), patch_chung():
            ket = fb.chuan_bi(TOKEN_GIA["fb"], nc, luu)
            self.assertEqual(ket["id_tai"], "V1")
            self.assertEqual(luu.ids["id_tai"], "V1")
            fases = [k["form"]["upload_phase"] for me, u, k in m.goi if "video_reels" in u]
            self.assertEqual(fases, ["start"])           # chua finish
            self.assertEqual(m.dem("POST", "thumbnails"), 0)
            # rupload nhi phan co header offset/file_size
            up = [k for me, u, k in m.goi if "rupload" in u][0]
            self.assertEqual(up["headers"]["offset"], "0")
            self.assertEqual(up["headers"]["file_size"], str(len(up["data"])))
            self.assertTrue(up["headers"]["Authorization"].startswith("OAuth "))
            ket2 = fb.cong_khai(TOKEN_GIA["fb"], nc, {"id_tai": "V1"})
            fin = [k["form"] for me, u, k in m.goi if "video_reels" in u][-1]
            self.assertEqual((fin["upload_phase"], fin["video_state"]), ("finish", "PUBLISHED"))
            self.assertEqual(m.dem("POST", "thumbnails"), 1)
            self.assertIn("/reel/V1/", ket2["link"])

    def test_thu_finish_draft_va_bia_trong_chuan_bi(self):
        nc, m = tao_nc("thu"), self.mang()
        with mock.patch("dang.http.gui", m), patch_chung():
            fb.chuan_bi(TOKEN_GIA["fb"], nc, LuuGia())
        fin = [k["form"] for me, u, k in m.goi if "video_reels" in u][-1]
        self.assertEqual(fin["video_state"], "DRAFT")
        self.assertEqual(m.dem("POST", "thumbnails"), 1)

    def test_finish_mat_phan_hoi_nhung_da_dang_thi_coi_la_xong(self):
        nc, m = tao_nc("that"), Mang()
        m.them("GET", "/me", P(body={"id": "PAGE1"}))
        m.them("POST", "video_reels", P(502, {}))
        m.them("GET", "/V1", P(body={"published": True}))
        m.them("POST", "thumbnails", P(body={"success": True}))
        with mock.patch("dang.http.gui", m), patch_chung():
            self.assertEqual(fb.cong_khai(TOKEN_GIA["fb"], nc, {"id_tai": "V1"})["id_bai"], "V1")

    def test_finish_khong_ro_va_chua_dang_thi_khong_ro(self):
        nc, m = tao_nc("that"), Mang()
        m.them("GET", "/me", P(body={"id": "PAGE1"}))
        m.them("POST", "video_reels", P(502, {}))
        m.them("GET", "/V1", P(body={"published": False, "status": {}}))
        with mock.patch("dang.http.gui", m), patch_chung():
            with self.assertRaises(chung.LoiDang) as c:
                fb.cong_khai(TOKEN_GIA["fb"], nc, {"id_tai": "V1"})
        self.assertTrue(c.exception.khong_ro)
        self.assertEqual(m.dem("POST", "video_reels"), 1)   # khong goi lai

    def test_danh_tinh_lech_page_id_da_luu(self):
        m = Mang().them("GET", "/me", P(body={"id": "KHAC"}))
        with mock.patch("dang.http.gui", m):
            with self.assertRaises(chung.LoiDang):
                fb.danh_tinh(TOKEN_GIA["fb"])


class TestIG(unittest.TestCase):
    def test_container_reels_roi_publish_chi_o_cong_khai(self):
        nc, luu, m = tao_nc(), LuuGia(), Mang()
        m.them("POST", "/IGU1/media_publish", P(body={"id": "M1"}))
        m.them("POST", "/IGU1/media", P(body={"id": "C1"}))
        m.them("GET", "/C1", [P(body={"status_code": "IN_PROGRESS"}), P(body={"status_code": "FINISHED"})])
        m.them("GET", "/M1", P(body={"permalink": "https://instagram.com/reel/M1"}))
        with mock.patch("dang.http.gui", m), patch_chung():
            ket = ig.chuan_bi(TOKEN_GIA["ig"], nc, luu)
            self.assertEqual(m.dem("POST", "media_publish"), 0)
            f = [k["form"] for me, u, k in m.goi if u.endswith("/IGU1/media")][0]
            self.assertEqual((f["media_type"], f["video_url"], f["cover_url"]), ("REELS", nc.url_video, nc.url_bia))
            self.assertEqual(luu.ids["id_container"], "C1")
            r = ig.cong_khai(TOKEN_GIA["ig"], nc, {"id_container": ket["id_container"]})
            self.assertEqual(r["id_bai"], "M1")
            self.assertEqual(m.dem("POST", "media_publish"), 1)

    def test_publish_mat_phan_hoi_da_published_khong_goi_lai(self):
        nc, m = tao_nc(), Mang()
        m.them("POST", "media_publish", P(504, {}))
        m.them("GET", "/C1", [P(body={"status_code": "FINISHED"}), P(body={"status_code": "PUBLISHED"})])
        with mock.patch("dang.http.gui", m), patch_chung():
            r = ig.cong_khai(TOKEN_GIA["ig"], nc, {"id_container": "C1"})
        self.assertIsNone(r["id_bai"])
        self.assertEqual(m.dem("POST", "media_publish"), 1)

    def test_container_loi_dung(self):
        m = Mang()
        m.them("POST", "/IGU1/media", P(body={"id": "C1"}))
        m.them("GET", "/C1", P(body={"status_code": "ERROR"}))
        with mock.patch("dang.http.gui", m), patch_chung():
            with self.assertRaises(chung.LoiDang):
                ig.chuan_bi(TOKEN_GIA["ig"], tao_nc(), LuuGia())


class TestThreads(unittest.TestCase):
    def test_video_container_cho_roi_publish(self):
        nc, m = tao_nc(), Mang()
        m.them("POST", "/THU1/threads_publish", P(body={"id": "T9"}))
        m.them("POST", "/THU1/threads", P(body={"id": "TC1"}))
        m.them("GET", "/TC1", P(body={"status": "FINISHED"}))
        m.them("GET", "/T9", P(body={"permalink": "https://threads.net/t/T9"}))
        with mock.patch("dang.http.gui", m), patch_chung():
            threads.chuan_bi(TOKEN_GIA["threads"], nc, LuuGia())
            self.assertEqual(m.dem("POST", "threads_publish"), 0)
            f = [k["form"] for me, u, k in m.goi if u.endswith("/THU1/threads")][0]
            self.assertEqual((f["media_type"], f["video_url"]), ("VIDEO", nc.url_video))
            self.assertLessEqual(len(f["text"]), 500)
            r = threads.cong_khai(TOKEN_GIA["threads"], nc, {"id_container": "TC1"})
            self.assertEqual(r["link"], "https://threads.net/t/T9")

    def test_gia_han(self):
        m = Mang().them("GET", "refresh_access_token", P(body={"access_token": "NEWTHTOKEN123456", "expires_in": 5184000}))
        with mock.patch("dang.http.gui", m):
            tk, giay = threads.gia_han(TOKEN_GIA["threads"], None)
        self.assertEqual((tk, giay), ("NEWTHTOKEN123456", 5184000))
        self.assertEqual(m.goi[0][2]["params"]["grant_type"], "th_refresh_token")


class TestYT(unittest.TestCase):
    def setUp(self):
        yt._cache.clear()

    def mang_co_ban(self):
        m = Mang()
        m.them("POST", "oauth2.googleapis.com", P(body={"access_token": "ya29.GIA_ACCESS_123456"}))
        return m

    def test_chuan_bi_that_chi_private_khong_publish_at(self):
        nc, m, luu = tao_nc("that"), self.mang_co_ban(), LuuGia()
        m.them("POST", "upload/youtube/v3/videos", P(headers={"Location": "https://up.example/session1"}))
        m.them("PUT", "up.example", P(200, {"id": "YV1"}))
        with mock.patch("dang.http.gui", m), patch_chung():
            r = yt.chuan_bi(TOKEN_GIA["youtube"], nc, luu)
        body = [k["json_body"] for me, u, k in m.goi if "upload/youtube/v3/videos" in u][0]
        self.assertEqual(body["status"]["privacyStatus"], "private")
        self.assertNotIn("publishAt", body["status"])
        self.assertIn("#Shorts", body["snippet"]["description"])
        self.assertEqual((r["id_tai"], luu.ids["id_tai"]), ("YV1", "YV1"))

    def test_chuan_bi_dat_bia_shorts(self):
        nc, m = tao_nc("that"), self.mang_co_ban()
        m.them("POST", "upload/youtube/v3/videos", P(headers={"Location": "https://up.example/s"}))
        m.them("PUT", "up.example", P(200, {"id": "YV1"}))
        m.them("POST", "youtube/v3/thumbnails/set", P(200, {"kind": "youtube#thumbnailSetResponse"}))
        with mock.patch("dang.http.gui", m), patch_chung():
            r = yt.chuan_bi(TOKEN_GIA["youtube"], nc, LuuGia())
        goi = [(u, k) for me, u, k in m.goi if "thumbnails/set" in u]
        self.assertEqual(len(goi), 1)
        self.assertIn("YV1", goi[0][1]["params"]["videoId"])
        self.assertEqual(goi[0][1]["data"], nc.tep("shorts", "bia").read_bytes())
        self.assertIs(r["bia"], True)

    def test_chuan_bi_bia_loi_van_tra_id(self):  # loi bia khong lam hong video da tai
        nc, m = tao_nc("that"), self.mang_co_ban()
        m.them("POST", "upload/youtube/v3/videos", P(headers={"Location": "https://up.example/s"}))
        m.them("PUT", "up.example", P(200, {"id": "YV1"}))
        m.them("POST", "youtube/v3/thumbnails/set", P(403, {"error": {"message": "forbidden"}}))
        luu = LuuGia()
        with mock.patch("dang.http.gui", m), patch_chung():
            r = yt.chuan_bi(TOKEN_GIA["youtube"], nc, luu)
        self.assertEqual((r["id_tai"], luu.ids["id_tai"]), ("YV1", "YV1"))
        self.assertTrue(str(r["bia"]).startswith("loi: HTTP 403"))

    def test_chuan_bi_thu_chi_private(self):
        nc, m = tao_nc("thu"), self.mang_co_ban()
        m.them("POST", "upload/youtube/v3/videos", P(headers={"Location": "https://up.example/s"}))
        m.them("PUT", "up.example", P(200, {"id": "YV1"}))
        with mock.patch("dang.http.gui", m), patch_chung():
            yt.chuan_bi(TOKEN_GIA["youtube"], nc, LuuGia())
        body = [k["json_body"] for me, u, k in m.goi if "upload/youtube/v3/videos" in u][0]
        self.assertEqual(body["status"]["privacyStatus"], "private")
        self.assertNotIn("publishAt", body["status"])

    def test_chunk_boi_so_256kb_va_thu_lai_5xx_bang_content_range_sao(self):
        du = b"x" * (600 * 1024)
        m = self.mang_co_ban()
        lan = {"n": 0}

        def put(me, u, k):
            lan["n"] += 1
            cr = k["headers"]["Content-Range"]
            if cr.startswith("bytes */"):
                return P(308, {}, {"Range": "bytes=0-262143"})   # server chi nhan chunk dau
            if lan["n"] == 1:
                return P(308, {}, {"Range": "bytes=0-262143"})
            if lan["n"] == 2:
                return P(503, {})                                  # chunk 2 loi
            if cr.endswith("-614399/614400"):
                return P(200, {"id": "YV1"})
            return P(308, {}, {"Range": "bytes=0-" + str(int(cr.split(" ")[1].split("-")[1].split("/")[0]))})
        m.them("PUT", "up.example", put)
        with mock.patch("dang.http.gui", m), patch_chung(), mock.patch.object(yt, "CHUNK", 256 * 1024):
            r = yt.tai_len("https://up.example/s", du, TOKEN_GIA["youtube"])
        self.assertEqual(r["id"], "YV1")
        crs = [k["headers"]["Content-Range"] for me, u, k in m.goi if me == "PUT"]
        self.assertIn("bytes */614400", crs)
        for cr in crs:
            if cr.startswith("bytes */"):
                continue
            a, b = cr.split(" ")[1].split("/")[0].split("-")
            if int(b) + 1 != 614400:
                self.assertEqual((int(b) + 1 - int(a)) % (256 * 1024), 0)

    def test_cong_khai_da_public(self):
        nc, m = tao_nc("that"), self.mang_co_ban()
        m.them("GET", "youtube/v3/videos", P(body={"items": [{"status": {"privacyStatus": "public"}}]}))
        with mock.patch("dang.http.gui", m), patch_chung():
            r = yt.cong_khai(TOKEN_GIA["youtube"], nc, {"id_tai": "YV1"})
        self.assertIn("shorts/YV1", r["link"])
        self.assertEqual(m.dem("PUT", "youtube/v3/videos"), 0)

    def test_danh_tinh(self):
        m = self.mang_co_ban().them("GET", "youtube/v3/channels", P(body={"items": [{"id": "UCYT1"}]}))
        with mock.patch("dang.http.gui", m):
            self.assertEqual(yt.danh_tinh(TOKEN_GIA["youtube"]), "UCYT1")


class TestTikTok(unittest.TestCase):
    def test_chia_chunk(self):
        self.assertEqual(tiktok.chia_chunk(40 * 1024 * 1024), (40 * 1024 * 1024, 1))
        c, n = tiktok.chia_chunk(150 * 1024 * 1024)
        self.assertEqual((c, n), (64 * 1024 * 1024, 2))   # chunk cuoi 86 MB <= 128 MB

    def test_hop_thu_init_put_status(self):
        nc, m = tao_nc("that"), Mang()
        m.them("POST", "inbox/video/init", P(body={"data": {"publish_id": "PUB1", "upload_url": "https://up.tt/u1"}, "error": {"code": "ok"}}))
        m.them("PUT", "up.tt", P(201, {}))
        m.them("POST", "status/fetch", [P(body={"data": {"status": "PROCESSING_UPLOAD"}}), P(body={"data": {"status": "SEND_TO_USER_INBOX"}})])
        with mock.patch("dang.http.gui", m), patch_chung():
            r = tiktok.hop_thu(dict(TOKEN_GIA["tiktok"]), nc)
        self.assertEqual(r["id_tai"], "PUB1")
        init = [k["json_body"] for me, u, k in m.goi if "init" in u][0]["source_info"]
        n = len(nc.tep("tiktok").read_bytes())
        self.assertEqual(init, {"source": "FILE_UPLOAD", "video_size": n, "chunk_size": n, "total_chunk_count": 1})
        put = [k["headers"] for me, u, k in m.goi if me == "PUT"][0]
        self.assertEqual(put["Content-Range"], f"bytes 0-{n - 1}/{n}")

    def test_lam_moi_neu_con_duoi_2h_va_luu_refresh_token_moi_ngay(self):
        nc = tao_nc("that")
        tk = dict(TOKEN_GIA["tiktok"], access_het_han=int(chung.bay_gio().timestamp()) + 3600)
        m = Mang().them("POST", "oauth/token", P(body={"access_token": "TTNEWACCESS123456", "refresh_token": "TTNEWREFRESH123456",
                                                      "expires_in": 86400, "refresh_expires_in": 31536000}))
        with mock.patch("dang.http.gui", m):
            moi = tiktok.lam_moi(tk, nc)
        self.assertEqual(moi["refresh_token"], "TTNEWREFRESH123456")
        self.assertEqual(nc.cong.ghi, ["tiktok"])
        self.assertEqual(nc.cong.token["tiktok"]["du_lieu"]["refresh_token"], "TTNEWREFRESH123456")

    def test_khong_lam_moi_khi_con_hon_2h(self):
        nc = tao_nc("that")
        m = Mang()
        with mock.patch("dang.http.gui", m):
            tiktok.lam_moi(dict(TOKEN_GIA["tiktok"]), nc)
        self.assertEqual(m.goi, [])

    def test_loi_qua_5_video_cho(self):
        nc, m = tao_nc("that"), Mang()
        m.them("POST", "init", P(403, {"error": {"code": "spam_risk_too_many_pending_share", "message": "x"}}))
        with mock.patch("dang.http.gui", m), patch_chung():
            with self.assertRaises(chung.LoiDang) as c:
                tiktok.hop_thu(dict(TOKEN_GIA["tiktok"]), nc)
        self.assertFalse(c.exception.khong_ro)
        self.assertIn("5 video", str(c.exception))

    def test_put_chunk_loi_la_khong_ro(self):
        nc, m = tao_nc("that"), Mang()
        m.them("POST", "init", P(body={"data": {"publish_id": "P", "upload_url": "https://up.tt/u"}, "error": {"code": "ok"}}))
        m.them("PUT", "up.tt", P(500, {}))
        with mock.patch("dang.http.gui", m), patch_chung():
            with self.assertRaises(chung.LoiDang) as c:
                tiktok.hop_thu(dict(TOKEN_GIA["tiktok"]), nc)
        self.assertTrue(c.exception.khong_ro)


if __name__ == "__main__":
    unittest.main()
