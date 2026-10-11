"""Tai hien tung diem Sol soi (nhanh dang, commit aafa592): moi test do truoc khi sua, xanh sau khi sua."""
import dataclasses  # noqa: F401
import datetime as dt
import json
import pathlib
import re
import tempfile
import unittest
from unittest import mock

from dang import chay, chung, fb, gia, http, manifest, site, so, tiktok, yt
from dang.chung import LoiDang
from dang.tests import gia_lap as g
from dang.tests.gia_lap import Mang, P, NGAY, DANG, TOKEN_GIA, tao_nc, trang_ps
from dang.tests.test_dieu_phoi import Khung, KenhGia, vo_ngu

GOC = pathlib.Path(__file__).resolve().parents[2]


class TestChayYoutubeGhiSo(Khung):
    def test_ghi_id_loi_sau_khi_youtube_da_nhan_la_khong_ro_va_khong_tai_lai(self):  # chay.py:94
        yt._cache.clear()
        m = Mang()
        m.them("POST", "oauth2.googleapis.com", P(body={"access_token": "ya29.GIA_ACCESS_123456"}))
        m.them("GET", "youtube/v3/channels", P(body={"items": [{"id": "UCYT1"}]}))
        m.them("POST", "upload/youtube", P(headers={"Location": "https://up.example/s"}))
        m.them("PUT", "up.example", P(200, {"id": "YV1"}))
        self.cong.hong_ghi_sau = lambda kenh, tr: kenh == "youtube" and "id_tai" in tr
        with mock.patch.dict(chay.MOD, {"youtube": yt}), mock.patch("dang.http.gui", m):
            self.assertEqual(self.chay("chuan-bi"), 1)
            self.assertEqual(self.cong.trang_thai("youtube"), "khong_ro")
            self.cong.hong_ghi_sau = None
            self.chay("chuan-bi")
        self.assertEqual(m.dem("POST", "upload/youtube"), 1)   # khong tai video thu 2


class TestGiuQuyenNguyenTu(Khung):
    def test_hai_runner_cung_ban_doc_chuan_bi_xong_chi_mot_publish(self):  # chay.py:174
        self.chay("chuan-bi")
        self.che_do = "that"
        man = g.tao_manifest(self.thu_muc)
        nc = chung.NguCanh(NGAY, DANG, "that", g.GIO_DANG, man, self.thu_muc, self.cong)
        nc.manifest_sha = chung.sha256_tep(pathlib.Path(self.thu_muc) / "manifest.json")
        dong_cu = dict(self.cong.dong[(NGAY, DANG, "fb", "that")])   # ca hai runner doc CUNG ban nay
        dong_cu["manifest_sha"] = nc.manifest_sha
        self.cong.dong[(NGAY, DANG, "fb", "that")]["manifest_sha"] = nc.manifest_sha
        dich = chay.nap_dich(self.dich)
        kq1 = chay.cong_khai_kenh("fb", nc, dich, self.cong, dong_cu)
        kq2 = chay.cong_khai_kenh("fb", nc, dich, self.cong, dong_cu)
        self.assertEqual((kq1[0], kq2[0]), ("da_dang", "bo_qua"))
        self.assertEqual(self.kenh["fb"].ck, 1)

    def test_cong_that_dung_neu_trang_thai(self):
        m = Mang().them("POST", "sg-cong", P(body={"ok": True, "so_dong": 0}))
        with mock.patch("dang.http.gui", m):
            c = so.Cong(khoa="KHOA_CONG_BI_MAT_123")
            self.assertEqual(c.cap_nhat_dang(NGAY, DANG, "fb", "that", neu_trang_thai="chuan_bi_xong", trang_thai="dang_dang"), 0)
        self.assertEqual(m.goi[0][2]["json_body"]["neu_trang_thai"], "chuan_bi_xong")


class TestYoutubeCong(unittest.TestCase):
    def setUp(self):
        yt._cache.clear()

    def mang(self):
        return Mang().them("POST", "oauth2.googleapis.com", P(body={"access_token": "ya29.GIA_ACCESS_123456"}))

    def test_pha_cong_khai_bi_chan_thi_youtube_van_private(self):  # yt.py:105 - chuan bi khong dat lich
        nc, m = tao_nc("that"), self.mang()
        m.them("POST", "upload/youtube", P(headers={"Location": "https://up.example/s"}))
        m.them("PUT", "up.example", P(200, {"id": "YV1"}))
        with mock.patch("dang.http.gui", m):
            yt.chuan_bi(TOKEN_GIA["youtube"], nc, lambda **k: None)
        meta = [k["json_body"] for me, u, k in m.goi if "upload/youtube" in u][0]
        self.assertEqual(meta["status"], {"privacyStatus": "private", "selfDeclaredMadeForKids": False})
        self.assertEqual(m.dem("PUT", "youtube/v3/videos"), 0)

    def test_cong_khai_dat_public_bang_update(self):
        nc, m = tao_nc("that"), self.mang()
        m.them("GET", "youtube/v3/videos", P(body={"items": [{"status": {"privacyStatus": "private"}}]}))
        m.them("PUT", "youtube/v3/videos", P(body={}))
        with mock.patch("dang.http.gui", m):
            yt.cong_khai(TOKEN_GIA["youtube"], nc, {"id_tai": "YV1"})
        body = [k["json_body"] for me, u, k in m.goi if me == "PUT" and "videos" in u][0]
        self.assertEqual(body["status"]["privacyStatus"], "public")

    def test_update_khong_chac_ket_qua_la_khong_ro(self):
        nc, m = tao_nc("that"), self.mang()
        m.them("GET", "youtube/v3/videos", P(body={"items": [{"status": {"privacyStatus": "private"}}]}))
        m.them("PUT", "youtube/v3/videos", P(503, {}))
        with mock.patch("dang.http.gui", m):
            with self.assertRaises(LoiDang) as c:
                yt.cong_khai(TOKEN_GIA["youtube"], nc, {"id_tai": "YV1"})
        self.assertTrue(c.exception.khong_ro)

    def test_resumable_khong_gui_lai_du_lieu_khi_chua_biet_offset(self):  # yt.py:91
        du = b"x" * (600 * 1024)
        m = self.mang()
        thu_tu = []

        def put(me, u, k):
            cr = k["headers"]["Content-Range"]
            thu_tu.append(cr)
            n = len(thu_tu)
            if cr.startswith("bytes */"):
                if n == 3:
                    return http.LoiMang("timeout hoi offset")
                return P(308, {}, {"Range": "bytes=0-262143"})
            if n == 1:
                return P(308, {}, {"Range": "bytes=0-262143"})
            if n == 2:
                return P(503, {})
            if cr.endswith("-614399/614400"):
                return P(200, {"id": "YV1"})
            return P(308, {}, {"Range": "bytes=0-" + cr.split(" ")[1].split("-")[1].split("/")[0]})
        m.them("PUT", "up.example", put)
        with mock.patch("dang.http.gui", m), vo_ngu(), mock.patch.object(yt, "CHUNK", 256 * 1024):
            self.assertEqual(yt.tai_len("https://up.example/s", du, TOKEN_GIA["youtube"])["id"], "YV1")
        # sau chunk 2 (503) phai la 2 lan hoi offset lien tiep (cai thu 2 timeout) TRUOC khi gui them byte nao
        self.assertTrue(thu_tu[2].startswith("bytes */") and thu_tu[3].startswith("bytes */"), thu_tu)
        self.assertFalse(thu_tu[2].startswith("bytes 262144"))


class TestManifestSha(Khung):
    def test_thay_manifest_giua_hai_pha_thi_huy_khung(self):  # chay.py:85
        self.chay("chuan-bi")
        self.assertTrue(self.cong.dong[(NGAY, DANG, "fb", "that")]["manifest_sha"])
        self.man_kw = {"kiem_lai": [{"ten": "doi noi dung"}]}   # manifest.json khac byte
        self.assertEqual(self.chay("cong-khai"), 1)
        self.assertEqual(self.kenh["fb"].ck, 0)
        self.assertEqual(self.cong.trang_thai("fb"), "bo")
        self.assertEqual(self.kenh["tiktok"].hop, 0)   # TikTok cung bi chan vi sha khac cac dong da chuan bi

    def test_sha_dung_thi_dang(self):
        self.chay("chuan-bi")
        self.assertEqual(self.chay("cong-khai"), 0)


class TestBoKhung(Khung):
    def test_khung_da_chuan_bi_roi_phat_hien_sai_thi_bo(self):  # chay.py:63
        self.chay("chuan-bi")
        self.assertEqual(self.cong.trang_thai("fb"), "chuan_bi_xong")
        self.man_kw = {"dat": False}
        self.assertEqual(self.chay("chuan-bi"), 3)
        for k in ("fb", "ig", "threads", "youtube"):
            self.assertEqual(self.cong.trang_thai(k), "bo")
        self.chay("cong-khai")
        self.assertEqual(self.kenh["fb"].ck, 0)

    def test_khung_da_dang_khong_bi_bo(self):
        self.chay("chuan-bi")
        self.chay("cong-khai")
        self.man_kw = {"dat": False}
        self.chay("chuan-bi")
        self.assertEqual(self.cong.trang_thai("fb"), "da_dang")


class TestGio(Khung):
    def test_dispatch_som_khong_cong_khai(self):  # chay.py:146
        self.chay("chuan-bi")
        with mock.patch.object(chung, "bay_gio", lambda: g.GIO_DANG - dt.timedelta(minutes=25)):
            self.assertEqual(self.chay("cong-khai"), 1)
        self.assertTrue(all(self.kenh[k].ck == 0 for k in ("fb", "ig", "threads", "youtube")))
        self.assertEqual(self.kenh["tiktok"].hop, 0)
        self.assertEqual(self.cong.trang_thai("fb"), "chuan_bi_xong")
        with mock.patch.object(chung, "bay_gio", lambda: g.GIO_DANG - dt.timedelta(seconds=30)):
            self.assertEqual(self.chay("cong-khai"), 0)

    def test_youtube_khong_public_som(self):
        yt._cache.clear()
        self.chay("chuan-bi")
        m = Mang()
        with mock.patch.dict(chay.MOD, {"youtube": yt}), mock.patch("dang.http.gui", m), \
                mock.patch.object(chung, "bay_gio", lambda: g.GIO_DANG - dt.timedelta(minutes=25)):
            self.chay("cong-khai")
        self.assertEqual(m.goi, [])


class TestTaiSanDay(Khung):
    def _hong(self, ten):
        def tai(ngay, dang, thu_muc, ban_can, repo=None, che_do=None):
            man = g.tao_manifest(thu_muc, self.che_do, ngay, dang)
            (pathlib.Path(thu_muc) / ten).write_bytes(b"sai")
            return man
        return tai

    def test_chuan_bi_kiem_ca_ban_tiktok(self):  # chay.py:109
        with mock.patch.object(chay.manifest, "tai_release", self._hong("video-tiktok.mp4")):
            self.assertEqual(self.chay("chuan-bi"), 3)
        self.assertTrue(all(self.kenh[k].cb == 0 for k in chay.KENH))

    def test_cong_khai_kiem_ca_ban_reels_va_bia(self):
        self.chay("chuan-bi")
        with mock.patch.object(chay.manifest, "tai_release", self._hong("bia-reels.jpg")):
            self.assertEqual(self.chay("cong-khai"), 3)
        self.assertTrue(all(self.kenh[k].ck == 0 for k in ("fb", "ig", "threads", "youtube")))
        self.assertEqual(self.kenh["tiktok"].hop, 0)
        self.assertEqual(self.cong.trang_thai("fb"), "bo")


class TestLoCheBiMat(unittest.TestCase):
    def test_khoa_nam_giua_vi_tri_cat_200(self):  # so.py:37
        khoa = "KHOA_CONG_BI_MAT_123"
        m = Mang().them("POST", "sg-cong", P(400, {"loi": "A" * 185 + khoa + "tail"}))
        with mock.patch("dang.http.gui", m):
            c = so.Cong(khoa=khoa)
            with self.assertRaises(so.LoiCong) as e:
                c.doc_token("fb")
        self.assertNotIn("KHOA_CONG", str(e.exception))
        self.assertNotIn("_BI_MAT_", str(e.exception))

    def test_fb_rupload_loi_phan_chieu_token(self):  # fb.py:30
        tk = dict(TOKEN_GIA["fb"])
        chung.dang_ky_bi_mat(tk["page_token"])
        m = Mang().them("POST", "rupload", P(400, {"echo": "B" * 185 + tk["page_token"]}))
        with mock.patch("dang.http.gui", m):
            with self.assertRaises(LoiDang) as e:
                fb._upload(tk, "V1", b"x")
        self.assertNotIn("EAAFB", str(e.exception))

    def test_yt_khoi_tao_loi_phan_chieu(self):  # yt.py:98
        yt._cache.clear()
        nc = tao_nc("that")
        m = Mang().them("POST", "oauth2.googleapis.com", P(body={"access_token": "ya29.GIA_ACCESS_123456"}))
        m.them("POST", "upload/youtube", P(400, {"e": "C" * 185 + "ya29.GIA_ACCESS_123456"}))
        with mock.patch("dang.http.gui", m):
            with self.assertRaises(LoiDang) as e:
                yt.chuan_bi(TOKEN_GIA["youtube"], nc, lambda **k: None)
        self.assertNotIn("ya29", str(e.exception))


class TestPagesKiemTruoc(unittest.TestCase):
    def _lap(self, hong):
        d = tempfile.mkdtemp()
        man = g.tao_manifest(d, "that", "2026-10-12", "top5")
        files = {f.name: f.read_bytes() for f in pathlib.Path(d).iterdir()}
        if hong:
            files["video-shorts.mp4"] = b"bi sua"
        m = Mang().them("GET", "/download/", lambda me, u, k: P(raw=files[u.rsplit("/", 1)[1]]))
        m.them("GET", "/releases/tags/", P(body={"assets": [{"name": n} for n in files]}))
        m.them("GET", "/releases", P(body=[{"tag_name": "v-2026-10-12-top5"}]))
        return m

    def test_ban_dich_hong_thi_khong_len_site(self):  # site.py:55
        ra = tempfile.mkdtemp()
        with mock.patch("dang.http.gui", self._lap(True)):
            with self.assertRaises(manifest.LoiManifest):
                site.dung(ra, "2026-10-12", "top5", "o/r")
        self.assertEqual(list((pathlib.Path(ra) / "v").glob("*")), [])

    def test_ban_dich_dung_len_site(self):
        ra = tempfile.mkdtemp()
        with mock.patch("dang.http.gui", self._lap(False)):
            self.assertTrue(site.dung(ra, "2026-10-12", "top5", "o/r"))

    def test_chi_giu_2_ngay_va_khong_lay_ngay_ke(self):  # site.py:15
        tag = lambda n: f"v-{n}-top5"
        ds = [tag("2026-10-13"), tag("2026-10-12"), tag("2026-10-11"), tag("2026-10-10")]
        m = Mang().them("GET", "/releases", P(body=[{"tag_name": t} for t in ds]))
        with mock.patch("dang.http.gui", m):
            r = site._danh_sach_tag("o/r", "2026-10-11", "2026-10-12")
        self.assertEqual(r, [("2026-10-12", "top5"), ("2026-10-11", "top5")])
        self.assertEqual(site.SO_NGAY, 2)

    def test_che_do_thu_dung_tag_thu(self):  # manifest.py:23
        self.assertEqual(manifest.tag("2026-10-12", "top5", "thu"), "thu-2026-10-12-top5")
        self.assertEqual(manifest.tag("2026-10-12", "top5"), "v-2026-10-12-top5")
        m = Mang().them("GET", "/releases", P(body=[{"tag_name": "thu-2026-10-12-top5"}, {"tag_name": "v-2026-10-12-keo-thom"}]))
        with mock.patch("dang.http.gui", m):
            self.assertEqual(site._danh_sach_tag("o/r", "2026-10-11", "2026-10-12", "thu"), [("2026-10-12", "top5")])
        m = Mang().them("GET", "/releases/tags/", P(body={"assets": [{"name": "manifest.json"}]}))
        with mock.patch("dang.http.gui", m):
            manifest.liet_ke_tai_san("2026-10-12", "top5", "o/r", "thu")
        self.assertIn("/releases/tags/thu-2026-10-12-top5", m.goi[0][1])


class TestFBBiaVaTrangThai(unittest.TestCase):
    def mang(self, video_status):
        m = Mang()
        m.them("GET", "graph.facebook.com/v26.0/me", P(body={"id": "PAGE1"}))
        m.them("POST", "/PAGE1/video_reels", lambda me, u, k: P(body={"video_id": "V2"}) if k["form"]["upload_phase"] == "start"
               else P(body={"success": True}))
        m.them("POST", "rupload", P(body={"success": True}))
        m.them("GET", "/V1", P(body={"status": {"video_status": video_status}}))
        m.them("GET", "/V2", P(body={"status": {"uploading_phase": {"status": "completed"}}}))
        m.them("POST", "thumbnails", P(body={"success": True}))
        return m

    def test_thieu_bia_thi_dung_truoc_finish(self):  # fb.py:122
        nc = tao_nc("that")
        nc.tep("reels", "bia").unlink()
        m = self.mang("ready")
        with mock.patch("dang.http.gui", m):
            with self.assertRaises(LoiDang) as c:
                fb.cong_khai(TOKEN_GIA["fb"], nc, {"id_tai": "V1"})
        self.assertFalse(c.exception.khong_ro)
        self.assertEqual([k for me, u, k in m.goi if "video_reels" in u], [])

    def test_loi_bia_sau_khi_dang_chi_la_canh_bao(self):
        nc = tao_nc("that")
        m = self.mang("ready")
        m.luat.insert(0, ["POST", "thumbnails", P(400, {"error": {"message": "Invalid image", "code": 100}})])
        with mock.patch("dang.http.gui", m), vo_ngu():
            r = fb.cong_khai(TOKEN_GIA["fb"], nc, {"id_tai": "V1"})
        self.assertEqual(r["id_bai"], "V1")
        self.assertIn("bia FB", r["canh_bao"])

    def test_phien_het_han_thi_tai_lai_va_ghi_id_moi(self):
        nc = tao_nc("that")
        nc.cong.dong[(NGAY, DANG, "fb", "that")] = {"trang_thai": "dang_dang", "ngay": NGAY, "dang": DANG, "kenh": "fb", "che_do": "that"}
        m = self.mang("expired")
        with mock.patch("dang.http.gui", m), vo_ngu():
            r = fb.cong_khai(TOKEN_GIA["fb"], nc, {"id_tai": "V1"})
        self.assertEqual(r["id_bai"], "V2")
        self.assertEqual(nc.cong.dong[(NGAY, DANG, "fb", "that")]["id_tai"], "V2")
        fin = [k["form"] for me, u, k in m.goi if "video_reels" in u][-1]
        self.assertEqual((fin["video_id"], fin["video_state"]), ("V2", "PUBLISHED"))

    def test_trang_thai_loi_va_completed(self):
        tk = TOKEN_GIA["fb"]
        for vs, up, mong in [("expired", None, "error"), ("upload_failed", None, "error"), (None, "completed", "xong"),
                             (None, "complete", "xong"), (None, "in_progress", "dang")]:
            st = {"video_status": vs} if vs else {"uploading_phase": {"status": up}}
            with mock.patch("dang.http.gui", Mang().them("GET", "/V1", P(body={"status": st}))):
                self.assertEqual(fb._trang_thai(tk, "V1"), mong, (vs, up))


class TestThreadsCho(unittest.TestCase):
    def test_cho_30_giay_sau_finished(self):
        from dang import threads
        nc, m, ngu = tao_nc(), Mang(), []
        m.them("POST", "/THU1/threads", P(body={"id": "TC1"}))
        m.them("GET", "/TC1", P(body={"status": "FINISHED"}))
        with mock.patch("dang.http.gui", m), mock.patch.object(chung, "ngu", ngu.append):
            threads.chuan_bi(TOKEN_GIA["threads"], nc, lambda **k: None)
        self.assertIn(30, ngu)


class TestGiaFailClosed(unittest.TestCase):
    MUC = {"ten": "A", "pid": "UP1001-X_00", "loc": "en-hk", "gia_cuc_bo": 100.0}

    def kiem(self, tra, muc=None):
        con = str(int((g.GIO_DANG.timestamp() + 5 * 3600) * 1000))
        m = Mang().them("GET", "store.playstation.com", tra(con) if callable(tra) else tra)
        with mock.patch("dang.http.gui", m):
            return gia.kiem_lai([muc or self.MUC], g.GIO_DANG)[0]

    def test_timeout_http_thieu_endtime_gia_deu_bo_khung(self):  # gia.py:37
        pid = self.MUC["pid"]
        self.assertTrue(self.kiem(http.LoiMang("timeout")))
        self.assertTrue(self.kiem(P(503, {})))
        self.assertTrue(self.kiem(lambda con: P(raw=trang_ps(pid, "HK$100.00", None))))              # mat endTime
        self.assertTrue(self.kiem(lambda con: P(raw=trang_ps(pid, "Included", con))))                # khong doc duoc gia
        self.assertTrue(self.kiem(lambda con: P(raw=trang_ps(pid, "HK$100", con)),
                                  {**self.MUC, "gia_cuc_bo": None}))                                  # thieu gia_cuc_bo
        self.assertEqual(self.kiem(lambda con: P(raw=trang_ps(pid, "HK$100.00", con))), [])

    def test_gia_han_lay_tu_khoi_dung_pid_khong_muon_cua_khoi_khac(self):  # Sol bcd #14/#15
        pid = self.MUC["pid"]
        # SKU chinh khong co endTime, game goi y tren trang co han + cung gia -> KHONG duoc muon han do (code cu: dat)
        self.assertTrue(self.kiem(lambda con: P(raw=trang_ps(pid, "HK$100.00", None, khac=[("UP2000-Y_00-GOIY", "HK$100.00", con)]))))
        # trang chi co khoi gia cua san pham khac (khong chua pid) -> khong nhan (code cu: dat vi regex toan trang)
        self.assertTrue(self.kiem(lambda con: P(raw=trang_ps(None, None, None, khac=[("UP2000-Y_00-GOIY", "HK$100.00", con)]))))
        # khoi gia khac cua san pham khac KHONG lam hong ket qua khi khoi dung pid day du
        self.assertEqual(self.kiem(lambda con: P(raw=trang_ps(pid, "HK$100.00", con, khac=[("UP2000-Y_00-GOIY", "HK$999.00", None)]))), [])

    def test_manifest_khong_co_kiem_lai_thi_bo(self):
        self.assertTrue(gia.kiem_lai([], g.GIO_DANG)[0])

    def test_doc_gia_theo_locale(self):
        for s, v in [("HK$47.70", 47.7), ("1.234.000₫", 1234000), ("Rp 1.299.000", 1299000), ("₹1,299", 1299),
                     ("1,299.00", 1299), ("47,70", 47.7), ("$ 1.299,50", 1299.5)]:
            self.assertEqual(gia.doc_gia(s), v, s)
        self.assertIsNone(gia.doc_gia("Mien phi"))


class TestManifestSchema(unittest.TestCase):
    def kiem(self, sua):
        d = tempfile.mkdtemp()
        m = g.tao_manifest(d)
        sua(m)
        manifest.kiem(m, d, NGAY, DANG, "that")

    def test_thieu_nguon(self):  # manifest.py:108
        for truong in ("sha_code", "sha_du_lieu", "tao_luc"):
            with self.assertRaises(manifest.LoiManifest, msg=truong):
                self.kiem(lambda m: m.pop(truong))

    def test_dat_true_nhung_phep_con_false(self):
        with self.assertRaises(manifest.LoiManifest):
            self.kiem(lambda m: m["ban"]["reels"]["kiem"]["phep"].append({"ten": "x", "dat": False, "so_do": "0"}))
        with self.assertRaises(manifest.LoiManifest):
            self.kiem(lambda m: m["ban"]["reels"]["kiem"].__setitem__("phep", []))

    def test_reels_tro_vao_file_shorts(self):  # manifest.py:114
        def sai(m):
            m["ban"]["reels"]["video"] = "video-shorts.mp4"
            m["ban"]["reels"]["sha256"] = m["ban"]["shorts"]["sha256"]
        with self.assertRaises(manifest.LoiManifest):
            self.kiem(sai)


class TestGiaHanKhongChan(Khung):
    def test_het_han_threads_sai_dinh_dang_khong_chan_kenh_sau(self):  # chay.py:278
        self.cong.token["threads"] = {"du_lieu": dict(g.TOKEN_GIA["threads"], cap_luc=1), "het_han": "khong-phai-ngay", "cap_nhat": "x"}
        m = Mang().them("POST", "oauth/token", P(body={"access_token": "TTNEW123456789", "refresh_token": "TTNEWRF123456789"}))  # gitleaks:allow (token gia cho test)
        m.them("POST", "oauth2.googleapis.com", P(body={"access_token": "ya29.GIA_ACCESS_123456"}))
        yt._cache.clear()
        with mock.patch("dang.http.gui", m):
            self.assertEqual(chay.main(["--pha", "gia-han"], cong=self.cong), 1)
        self.assertEqual(self.cong.token["tiktok"]["du_lieu"]["refresh_token"], "TTNEWRF123456789")   # TikTok van duoc lam moi
        self.assertEqual(m.dem("POST", "oauth2.googleapis.com"), 1)                                       # YouTube van duoc kiem


class TestKiemGioTheoDong(Khung):
    def test_dung_gio_du_kien_cua_dong_khong_dung_gio_cung(self):  # chay.py:222
        for k in chay.KENH:
            self.cong.giu_dang(NGAY, DANG, k, "that", "2026-10-12T09:00:00+07:00")
        with mock.patch.object(chung, "bay_gio", lambda: dt.datetime(2026, 10, 12, 9, 16, tzinfo=chung.VN)):
            self.assertEqual(self.chay("kiem-gio"), 1)    # 09:16 > 09:00 + 15', du gio mac dinh 12:00 chua toi
        self.assertTrue(any(x[0] == "loi" for x in self.ntfy))
        self.ntfy.clear()
        with mock.patch.object(chung, "bay_gio", lambda: dt.datetime(2026, 10, 12, 9, 10, tzinfo=chung.VN)):
            self.assertEqual(self.chay("kiem-gio"), 0)


class TestWorkflow(unittest.TestCase):
    def doc(self, ten):
        return (GOC / ".github/workflows" / ten).read_text()

    def test_pages_va_phu_thuoc(self):  # dang.yml:118, :28, :29
        y = self.doc("dang.yml")
        self.assertIn("queue: max", y)
        self.assertIn("group: pages-sangame-video", y)
        job = lambda ten: re.search(rf"\n  {ten}:\n(.*?)(?=\n  [a-z-]+:\n|\Z)", y, re.S).group(1)
        self.assertNotIn("pages", re.search(r"needs:.*", job("chuan-bi-chung")).group(0))
        self.assertIn("--kenh fb,youtube", job("chuan-bi-chung"))
        self.assertIn("--kenh ig,threads", job("chuan-bi-pages"))
        self.assertRegex(job("chuan-bi-pages"), r"needs:.*pages")
        self.assertRegex(job("pages"), r"needs:.*kiem")      # deploy chi sau kiem noi dung
        self.assertIn("--pha kiem ", job("kiem"))
        self.assertNotIn("cancel-in-progress: true", y)

    def test_nhom_token_dung_chung(self):  # tiktok.py:52
        for f in ("dang.yml", "gia-han.yml"):
            self.assertIn("group: token-tiktok", self.doc(f))


if __name__ == "__main__":
    unittest.main()
