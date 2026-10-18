"""Bo do so lieu: gia lap http.gui, khong mang that, khong ngu that, khong goi sg-cong that."""
import contextlib
import datetime as dt
import io
import json
import os
import re
import tempfile
import unittest
from unittest import mock

from dang import chung, http, ntfy, so, yt
from dang.tests import gia_lap as g
from dang.tests.gia_lap import Mang, P
from do_so import chay

NOW = dt.datetime(2026, 10, 15, 16, 0, 0, tzinfo=dt.timezone.utc)      # 23:00 VN
BAT_DAU = dt.datetime(2026, 10, 10, 17, 0, 0, tzinfo=dt.timezone.utc)  # 2026-10-11 00:00 VN
ZK = "zk_LIVE_BIMAT_1234567890abcdef"
FB_TOK, IG_TOK, TH_TOK = g.TOKEN_GIA["fb"]["page_token"], g.TOKEN_GIA["ig"]["page_token"], g.TOKEN_GIA["threads"]["token"]
YT_ACC = "ya29.YTACCESSGIA1234567890"
MOI = "2026-10-14T00:30:00+0000"      # 07:30 VN 14/10
MOI2 = "2026-10-14T05:00:00+0000"
CU = "2026-10-05T00:00:00+0000"       # truoc cua so


class CongDo:
    """Cong gia: doc_dang/doc_token nhu CongGia, goi() ghi lai cac lan ghi_so_lieu."""

    def __init__(self, dong=None, hong_ghi=None):
        self.dong = dong or []
        self.token = {k: {"du_lieu": dict(v)} for k, v in g.TOKEN_GIA.items()}
        self.ghi, self.hong_ghi, self.hoi_so = [], hong_ghi, []

    def doc_dang(self, tu, den=None, che_do=None):
        self.hoi_so.append((tu, den, che_do))
        if isinstance(self.dong, Exception):
            raise self.dong
        return [dict(r) for r in self.dong if tu <= r["ngay"] <= (den or tu)]

    def doc_token(self, kenh):
        return self.token.get(kenh)

    def goi(self, viec, **kw):
        assert viec == "ghi_so_lieu", viec
        if self.hong_ghi and self.hong_ghi(len(self.ghi)):
            self.ghi.append(None)
            raise so.LoiCong("gia lap loi ghi")
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T[\d:]+Z", kw["do_luc"]), kw["do_luc"]
        for b in kw["bai"]:        # validator tuong duong cong sg-cong: cong se tra 400 neu sai
            assert chay.hop_le_cong(b), b
        assert len(kw["bai"]) <= 2000 and len(kw["kenh"]) <= 10
        assert all(chay.hop_le_kenh(k) for k in kw["kenh"])
        assert len({k["nen_tang"] for k in kw["kenh"]}) == len(kw["kenh"])
        assert len({(b["nen_tang"], b["id_bai"]) for b in kw["bai"]}) == len(kw["bai"])
        self.ghi.append(kw)
        return {"ok": True, "so_bai": len(kw["bai"]), "so_kenh": len(kw["kenh"])}

    def bai_da_ghi(self):
        return [b for lan in self.ghi if lan for b in lan["bai"]]


def so_dang(kenh, id_bai, dang, gio="2026-10-14T00:30:00+00:00"):
    return {"kenh": kenh, "id_bai": id_bai, "dang": dang, "trang_thai": "da_dang", "ngay": "2026-10-14", "gio_cong_khai": gio}


def chi_so(**kv):
    return [{"name": k, "values": [{"value": v}]} for k, v in kv.items()]


def mang_day_du():
    """Mang gia 5 kenh. Moi luat la ham/list/Phan; ham tra Phan."""
    m = Mang()
    # --- Facebook ---
    def fb_videos(mt, url, kw):
        if "after=P2" in url:
            return P(body={"data": [
                {"id": "V3", "created_time": "2026-10-12T00:00:00+0000", "length": 30, "permalink_url": "/reel/V3", "published": True},
                {"id": "VCU2", "created_time": CU, "length": 30, "published": True}]})   # cu xen giua bai moi: bo, khong dung phan trang
        return P(body={"data": [
            {"id": "V1", "description": "Tin 1\ndong hai", "created_time": MOI, "length": 30, "permalink_url": "/reel/V1",
             "published": True, "likes": {"summary": {"total_count": 7}}, "comments": {"summary": {"total_count": 2}}},
            {"id": "VCHUA", "created_time": MOI, "published": False},
            {"id": "VCU", "created_time": CU, "length": 30, "published": True},     # bai cu nam GIUA bai moi
            {"id": "V2", "description": "Video dai", "created_time": MOI2, "length": 200.5, "permalink_url": "https://www.facebook.com/reel/V2",
             "published": True}],
            "paging": {"next": f"{g_fb}/PAGE1/videos?after=P2&access_token={FB_TOK}"}})
    g_fb = chay.G
    m.them("GET", "/PAGE1/videos", fb_videos)
    m.them("GET", "/V1/video_insights", P(body={"data": chi_so(fb_reels_total_plays=1000, post_video_view_time=20000000)}))
    m.them("GET", "/V2/video_insights", P(body={"data": chi_so(fb_reels_total_plays=10, post_video_view_time=50000)}))
    m.them("GET", "/V3/video_insights", P(body={"data": chi_so(total_video_views=50, post_video_view_time=100000)}))
    m.them("GET", "/PAGE1", P(body={"followers_count": 321}))
    # --- Instagram ---
    m.them("GET", "/IGU1/media", P(body={"data": [
        {"id": "M1", "caption": "Reel 1", "media_type": "VIDEO", "media_product_type": "REELS", "timestamp": MOI, "permalink": "https://www.instagram.com/reel/M1/"},
        {"id": "M2", "caption": "Anh", "media_type": "IMAGE", "media_product_type": "FEED", "timestamp": MOI2, "permalink": "https://www.instagram.com/p/M2/"},
        {"id": "MCU", "media_type": "VIDEO", "media_product_type": "REELS", "timestamp": CU}]}))   # cu: bo
    m.them("GET", "/M1/insights", P(body={"data": chi_so(views=500, reach=300, likes=9, comments=1, shares=2, saved=3, ig_reels_avg_watch_time=12345, reels_skip_rate=92.3)}))
    m.them("GET", "/M2/insights", P(body={"data": chi_so(views=40, reach=30, likes=1, comments=0, shares=0, saved=0)}))
    m.them("GET", "/IGU1", P(body={"followers_count": 111}))
    # --- Threads ---
    m.them("GET", "/THU1/threads_insights", P(body={"data": [{"name": "followers_count", "total_value": {"value": 55}}]}))
    m.them("GET", "/THU1/threads", P(body={"data": [
        {"id": "T1", "text": "Binh chon nao", "media_type": "TEXT_POST", "permalink": "https://www.threads.com/@x/post/T1", "timestamp": MOI},
        {"id": "T2", "text": "Anh", "media_type": "IMAGE", "permalink": "https://www.threads.com/@x/post/T2", "timestamp": MOI2},
        {"id": "T3", "text": "Video", "media_type": "VIDEO", "permalink": "https://www.threads.com/@x/post/T3", "timestamp": MOI2},
        {"id": "TCU", "media_type": "VIDEO", "timestamp": CU}]}))
    m.them("GET", "/T1/insights", P(body={"data": chi_so(views=100, likes=5, replies=3, reposts=1, quotes=2)}))
    m.them("GET", "/T2/insights", P(body={"data": chi_so(views=10, likes=0, replies=0, reposts=0, quotes=0)}))
    m.them("GET", "/T3/insights", P(body={"data": chi_so(views=20, likes=1, replies=0, reposts=0, quotes=0)}))
    # --- YouTube ---
    m.them("GET", "/youtube/v3/channels", P(body={"items": [{"contentDetails": {"relatedPlaylists": {"uploads": "UU1"}},
                                                             "statistics": {"subscriberCount": "77"}}]}))
    m.them("GET", "/youtube/v3/playlistItems", P(body={"items": [
        {"contentDetails": {"videoId": "Y1", "videoPublishedAt": MOI}, "status": {"privacyStatus": "public"}},
        {"contentDetails": {"videoId": "YP", "videoPublishedAt": MOI}, "status": {"privacyStatus": "private"}},
        {"contentDetails": {"videoId": "Y2", "videoPublishedAt": MOI2}, "status": {"privacyStatus": "public"}},
        {"contentDetails": {"videoId": "YCU", "videoPublishedAt": CU}, "status": {"privacyStatus": "public"}}]}))
    m.them("GET", "/youtube/v3/videos", P(body={"items": [
        {"id": "Y1", "snippet": {"title": "Top 5 hom nay", "publishedAt": MOI}, "contentDetails": {"duration": "PT28S"},
         "statistics": {"viewCount": "900", "likeCount": "30", "commentCount": "4"}},
        {"id": "Y2", "snippet": {"title": "Dai", "publishedAt": MOI2}, "contentDetails": {"duration": "PT5M10S"},
         "statistics": {"viewCount": "80", "likeCount": "3", "commentCount": "0"}}]}))
    m.them("GET", "youtubeanalytics.googleapis.com", P(body={
        "columnHeaders": [{"name": n} for n in ("video", "views", "averageViewDuration", "subscribersGained", "shares")],
        "rows": [["Y1", 850, 14.5, 2, 6], ["Y2", 0, 0, 0, 0]]}))
    # --- TikTok (Zernio) ---
    def pz(pid, gio, **kw):
        return {"_id": pid, "status": "published", "publishedAt": gio, "platformPostUrl": f"https://www.tiktok.com/@s/video/{pid}?lang=vi",
                "content": f"TT {pid}\nhai", "analytics": {"views": 1000, "likes": 50, "comments": 5, "shares": 4, "saves": 6, "follows": 2,
                                                          "videoDurationSeconds": 30, "completionRate": 0.456, "audienceTypes": {"nonFollower": 0.9},
                                                          "retentionCurve": {"0": 1, "1": 0.78, "2": 0.32, "3": 0.22, "4": 0.17}}, **kw}
    m.them("GET", "zernio.com/api/v1/analytics", lambda mt, url, kw: P(body={
        "posts": [pz("ZP1", "2026-10-14T13:00:00Z", latePostId="Z1"),
                  pz("ZP2", "2026-10-14T05:20:00Z"),           # lech 10 phut so dong hop thu ZH
                  pz("ZP6", "2026-10-14T05:00:00Z"),           # cung gan ZH nhung ZH da bi ZP2 lay
                  pz("ZP3", "2026-10-14T20:00:00Z"),           # ngoai so
                  pz("ZPCU", CU), dict(pz("ZPLICH", MOI), status="scheduled")],
        "accounts": [{"_id": "khac", "platform": "tiktok", "followersCount": 1}, {"_id": g_acc, "platform": "tiktok", "followersCount": 99}],
        "pagination": {"page": 1, "limit": 100, "total": 6, "pages": 1}}) if kw["params"]["page"] == 1 else AssertionError("khong co trang 2"))
    g_acc = chay.zernio.ACC_MAC_DINH
    return m


DONG_SO = [so_dang("fb", "V1", "tin-nhanh"), so_dang("ig", "M1", "tin-nhanh"), so_dang("threads", "T1", "binh-chon"),
           so_dang("youtube", "Y1", "top5"), so_dang("tiktok", "Z1", "keo-thom"),
           so_dang("tiktok", "ZH", "top5", gio="2026-10-14T05:30:00+00:00")]


class Chung(unittest.TestCase):
    def setUp(self):
        self.ntfy = []
        for p in (mock.patch.dict(os.environ, {"ZERNIO_KHOA": ZK}),
                  mock.patch.object(chung, "bay_gio", lambda: NOW),
                  mock.patch.object(chung, "ngu", lambda s: None),
                  mock.patch.object(yt, "lam_moi_access", lambda tk: (YT_ACC, None)),
                  mock.patch.object(ntfy, "loi", lambda *a, **k: self.ntfy.append(a))):
            p.start()
            self.addCleanup(p.stop)

    def chay(self, m, cong=None, che_do="that", ra=None):
        cong = cong or CongDo(DONG_SO)
        buf = io.StringIO()
        with mock.patch.object(http, "gui", m), contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            ma = chay.main(["--che-do", che_do] + (["--ra", ra] if ra else []), cong=cong)
        self.log = buf.getvalue()
        return ma, cong

    def hang(self, cong, nen_tang, id_bai):
        return next(b for b in cong.bai_da_ghi() if b["nen_tang"] == nen_tang and b["id_bai"] == id_bai)


class ToanLuot(Chung):
    def test_luot_day_du(self):
        m = mang_day_du()
        ma, cong = self.chay(m)
        self.assertEqual(ma, 0, self.log)
        self.assertEqual(self.ntfy, [])
        # so doc: cua so tu 2026-10-11 (VN) den hom nay, che do that
        # so doc TUNG NGAY (cong khong phan trang)
        self.assertEqual(cong.hoi_so, [(f"2026-10-{d}", f"2026-10-{d}", "that") for d in (11, 12, 13, 14, 15)])
        # FB duyet het 2 trang (khong dung o bai cu dau tien), loc tung bai: V3 (sau bai cu) co, VCU/VCU2 khong
        self.assertEqual(m.dem("GET", "/PAGE1/videos"), 2)
        ids = {(b["nen_tang"], b["id_bai"]) for b in cong.bai_da_ghi()}
        self.assertIn(("Facebook", "V3"), ids)
        self.assertNotIn(("Facebook", "VCU"), ids)
        self.assertNotIn(("Facebook", "VCU2"), ids)
        self.assertNotIn(("Facebook", "VCHUA"), ids)          # published=false bo
        self.assertEqual(m.dem("GET", "/VCU/"), 0)
        # YouTube: bo private + cu, khong sang trang sau
        yids = {b["id_bai"] for b in cong.bai_da_ghi() if b["nen_tang"] == "YouTube"}
        self.assertEqual(yids, {"Y1", "Y2"})
        self.assertEqual(m.dem("GET", "/youtube/v3/playlistItems"), 1)
        # tong dong: FB 3 + IG 2 + Threads 3 + YT 2 + TikTok 4
        self.assertEqual(len(cong.bai_da_ghi()), 14)
        # nguoi theo doi 5 kenh
        kenh = {k["nen_tang"]: k["nguoi_theo_doi"] for k in cong.ghi[0]["kenh"]}
        self.assertEqual(kenh, {"Facebook": 321, "Instagram": 111, "Threads": 55, "YouTube": 77, "TikTok": 99})
        self.assertEqual(cong.ghi[0]["do_luc"], "2026-10-15T16:00:00Z")

    def test_facebook(self):
        _, cong = self.chay(mang_day_du())
        v1 = self.hang(cong, "Facebook", "V1")
        self.assertEqual((v1["luot_xem"], v1["xem_tb_giay"], v1["thich"], v1["binh_luan"], v1["do_dai_giay"]), (1000, 20.0, 7, 2, 30))
        self.assertEqual((v1["dang"], v1["khuon"], v1["ngay"], v1["tieu_de"]), ("tin-nhanh", "Tin nhanh 07:30", "2026-10-14", "Tin 1"))
        self.assertEqual((v1["link"], v1["gio_dang"]), ("https://www.facebook.com/reel/V1", "2026-10-14T00:30:00Z"))
        v3 = self.hang(cong, "Facebook", "V3")                       # khong co fb_reels_total_plays -> total_video_views
        self.assertEqual((v3["luot_xem"], v3["xem_tb_giay"]), (50, 2.0))
        v2 = self.hang(cong, "Facebook", "V2")
        self.assertEqual((v2["khuon"], v2["dang"], v2["do_dai_giay"]), ("Video dài", None, 200.5))
        self.assertIn("Facebook: 3 bai, 0 loi bai", self.log)

    def test_instagram_bo_metric_theo_loai_va_do_dai(self):
        m = mang_day_du()
        _, cong = self.chay(m)
        metric = {u.split("/")[-2]: kw["params"]["metric"] for mt, u, kw in m.goi if u.endswith("/insights") and "/M" in u}
        self.assertIn("ig_reels_avg_watch_time", metric["M1"])
        self.assertNotIn("ig_reels_avg_watch_time", metric["M2"])
        m1 = self.hang(cong, "Instagram", "M1")
        self.assertEqual((m1["luot_xem"], m1["xem_tb_giay"], m1["luu"], m1["chia_se"]), (500, 12.3, 3, 2))
        self.assertEqual(m1["bo_qua_3s_pct"], 92.3)
        self.assertIsNone(self.hang(cong, "Instagram", "M2")["bo_qua_3s_pct"])
        self.assertEqual(m1["do_dai_giay"], 30)                      # lay tu bai FB cung (ngay, dang)
        self.assertEqual(m1["khuon"], "Tin nhanh 07:30")
        m2 = self.hang(cong, "Instagram", "M2")
        self.assertEqual(m2["khuon"], "tin-nóng / ngoài lịch (chữ)")
        self.assertIsNone(m2["do_dai_giay"])

    def test_threads(self):
        _, cong = self.chay(mang_day_du())
        t1 = self.hang(cong, "Threads", "T1")
        self.assertEqual((t1["khuon"], t1["chia_se"], t1["binh_luan"]), ("Bình chọn", 3, 3))     # binh-chon khong them (chu)
        self.assertEqual(self.hang(cong, "Threads", "T2")["khuon"], "tin-nóng / ngoài lịch (chữ)")
        self.assertEqual(self.hang(cong, "Threads", "T3")["khuon"], "tin-nóng / ngoài lịch")

    def test_youtube(self):
        _, cong = self.chay(mang_day_du())
        y1 = self.hang(cong, "YouTube", "Y1")
        self.assertEqual((y1["luot_xem"], y1["xem_tb_giay"], y1["theo_doi_moi"], y1["chia_se"], y1["do_dai_giay"]), (900, 14.5, 2, 6, 28))
        self.assertEqual((y1["link"], y1["khuon"]), ("https://www.youtube.com/shorts/Y1", "Top 5 12:00"))
        y2 = self.hang(cong, "YouTube", "Y2")                        # Analytics views=0 -> chua co so; 310 giay > 180 -> watch
        self.assertIsNone(y2["xem_tb_giay"])
        self.assertEqual((y2["link"], y2["khuon"]), ("https://www.youtube.com/watch?v=Y2", "Video dài"))

    def test_tiktok_ghep_khuon(self):
        _, cong = self.chay(mang_day_du())
        ids = {b["id_bai"]: b for b in cong.bai_da_ghi() if b["nen_tang"] == "TikTok"}
        self.assertEqual(set(ids), {"ZP1", "ZP2", "ZP3", "ZP6"})                  # scheduled + cu bi bo
        self.assertEqual(ids["ZP1"]["dang"], "keo-thom")                          # luot 1: trung latePostId
        self.assertEqual(ids["ZP2"]["dang"], "top5")                              # luot 2: gan gio nhat
        self.assertIsNone(ids["ZP6"]["dang"])                                     # ZH da dung 1 lan
        self.assertEqual(ids["ZP6"]["khuon"], "tin-nóng / ngoài lịch")
        self.assertIsNone(ids["ZP3"]["dang"])
        z = ids["ZP1"]
        self.assertEqual((z["luot_xem"], z["luu"], z["theo_doi_moi"], z["nguoi_la_pct"], z["xem_het_pct"], z["do_dai_giay"]),
                         (1000, 6, 2, 90.0, 45.6, 30))
        self.assertEqual(z["con_giay_3_pct"], 22.0)
        self.assertEqual(z["link"], "https://www.tiktok.com/@s/video/ZP1")        # bo ?query
        self.assertEqual(z["khuon"], "Kèo 20:00")

    def test_payload_dung_khoa(self):
        _, cong = self.chay(mang_day_du())
        co = {"nen_tang", "id_bai", "ngay", "gio_dang", "dang", "khuon", "link", "tieu_de", "luot_xem", "thich", "binh_luan",
              "chia_se", "luu", "theo_doi_moi", "xem_tb_giay", "do_dai_giay", "nguoi_la_pct", "xem_het_pct",
              "con_giay_3_pct", "bo_qua_3s_pct"}
        for b in cong.bai_da_ghi():
            self.assertEqual(set(b), co)
        self.assertEqual(set(cong.ghi[0]), {"do_luc", "bai", "kenh"})
        for k in cong.ghi[0]["kenh"]:
            self.assertEqual(set(k), {"nen_tang", "nguoi_theo_doi"})

    def test_che_do_thu_khong_ghi_nhung_ra_file_dung_payload(self):
        d = tempfile.mkdtemp(prefix="sg-do-")
        ra_thu, ra_that = os.path.join(d, "thu.json"), os.path.join(d, "that.json")
        ma, cong_thu = self.chay(mang_day_du(), che_do="thu", ra=ra_thu)
        self.assertEqual(ma, 0)
        self.assertEqual(cong_thu.ghi, [])
        _, cong_that = self.chay(mang_day_du(), che_do="that", ra=ra_that)
        a, b = json.load(open(ra_thu, encoding="utf-8")), json.load(open(ra_that, encoding="utf-8"))
        self.assertEqual(a, b)
        self.assertEqual(b["bai"], cong_that.bai_da_ghi())
        self.assertEqual(b["kenh"], cong_that.ghi[0]["kenh"])
        self.assertEqual(self.ntfy, [])

    def test_log_khong_lo_token_va_so_tung_bai(self):
        _, cong = self.chay(mang_day_du())
        for bi_mat in (FB_TOK, IG_TOK, TH_TOK, YT_ACC, ZK, g.TOKEN_GIA["youtube"]["refresh_token"]):
            self.assertNotIn(bi_mat, self.log)
        for rieng in ("Tin 1", "TT ZP1", "Top 5 hom nay", "1000", "V1"):
            self.assertNotIn(rieng, self.log)


class Loi(Chung):
    def test_loi_insights_mot_bai_bo_bai_khong_ghi_null_va_vuot_nguong_la_loi_kenh(self):
        m = mang_day_du()
        m.luat.insert(0, ["GET", "/V2/video_insights", P(400, {"error": {"code": 100, "message": "loi bai"}})])
        ma, cong = self.chay(m)
        fb = {b["id_bai"] for b in cong.bai_da_ghi() if b["nen_tang"] == "Facebook"}
        self.assertEqual(fb, {"V1", "V3"})                         # V2 bo han, khong co dong null
        self.assertIn("Facebook: 2 bai, 1 loi bai, LOI KENH: qua nhieu loi bai (1/3)", self.log)
        self.assertEqual(ma, 1)                                    # 1/3 > 25%
        self.assertEqual(len(self.ntfy), 1)

    def test_nguong(self):
        self.assertTrue(chay.qua_nguong(2, 1))
        self.assertFalse(chay.qua_nguong(0, 0))
        self.assertFalse(chay.qua_nguong(26, 0))
        self.assertFalse(chay.qua_nguong(75, 25))                 # dung 25% khong vuot
        self.assertTrue(chay.qua_nguong(74, 26))

    def test_vuot_20_trang_la_loi_kenh(self):
        m = mang_day_du()
        trang = lambda mt, url, kw: P(body={"data": [{"id": "V1", "created_time": MOI, "length": 30, "published": True}],
                                            "paging": {"next": f"{chay.G}/PAGE1/videos?after=X&access_token={FB_TOK}"}})
        m.luat.insert(0, ["GET", "/PAGE1/videos", trang])
        ma, cong = self.chay(m)
        self.assertEqual(ma, 1)
        self.assertEqual(m.dem("GET", "/PAGE1/videos"), chay.TOI_DA_TRANG)
        self.assertIn("qua 20 trang", self.log)

    def test_tiktok_bo_bai_tai_khoan_khac_va_thieu_truong_khong_hong(self):
        m = mang_day_du()
        def z(mt, url, kw):
            return P(body={"posts": [
                {"_id": "OK1", "status": "published", "publishedAt": MOI, "accountId": chay.zernio.ACC_MAC_DINH,
                 "analytics": {"views": 5}},                      # thieu completionRate/audienceTypes -> null, khong loi
                {"_id": "OK2", "status": "published", "publishedAt": MOI, "platforms": [{"platform": "tiktok", "accountId": chay.zernio.ACC_MAC_DINH}]},
                {"_id": "KHAC", "status": "published", "publishedAt": MOI, "accountId": "tai-khoan-khac", "analytics": {"views": 9}},
                {"_id": "KHAC2", "status": "published", "publishedAt": MOI, "platforms": [{"accountId": "tai-khoan-khac"}]}],
                "accounts": [{"_id": "tai-khoan-khac", "platform": "tiktok", "followersCount": 7},
                             {"_id": chay.zernio.ACC_MAC_DINH, "followersCount": 42}]})
        m.luat.insert(0, ["GET", "zernio.com/api/v1/analytics", z])
        ma, cong = self.chay(m)
        self.assertEqual(ma, 0, self.log)
        tt = {b["id_bai"]: b for b in cong.bai_da_ghi() if b["nen_tang"] == "TikTok"}
        self.assertEqual(set(tt), {"OK1", "OK2"})
        self.assertIsNone(tt["OK1"]["xem_het_pct"])
        self.assertIsNone(tt["OK1"]["nguoi_la_pct"])
        kenh = {k["nen_tang"]: k["nguoi_theo_doi"] for k in cong.ghi[0]["kenh"]}
        self.assertEqual(kenh["TikTok"], 42)

    def test_youtube_analytics_end_date_theo_gio_los_angeles(self):
        m = mang_day_du()
        with mock.patch.object(chung, "bay_gio", lambda: dt.datetime(2026, 10, 15, 3, 0, tzinfo=dt.timezone.utc)):   # 14/10 20:00 PDT
            self.chay(m)
        an = [kw["params"] for mt, u, kw in m.goi if "youtubeanalytics" in u][0]
        self.assertEqual(an["endDate"], "2026-10-14")
        self.assertEqual(an["startDate"], "2026-10-09")   # dau cua so (UTC) lui 1 ngay cho kip mui gio


    def test_mot_kenh_loi_kenh_khac_van_ghi_ma_1_va_ntfy(self):
        m = mang_day_du()
        m.luat.insert(0, ["GET", "/PAGE1/videos", P(500, {"error": {"code": 1, "message": f"hong {FB_TOK}"}})])
        ma, cong = self.chay(m)
        self.assertEqual(ma, 1)
        self.assertEqual(len(cong.ghi), 1)                         # phan dat van ghi
        nen = {b["nen_tang"] for b in cong.bai_da_ghi()}
        self.assertEqual(nen, {"Instagram", "Threads", "YouTube", "TikTok"})
        self.assertEqual(len(self.ntfy), 1)
        self.assertEqual(self.ntfy[0][0], "Đo số liệu: 1 kênh lỗi")
        self.assertNotIn(FB_TOK, str(self.ntfy) + self.log)
        self.assertIn("Facebook: 0 bai", self.log)

    def test_gioi_han_toc_do_dung_kenh_giu_dong_da_co(self):
        m = mang_day_du()
        m.luat.insert(0, ["GET", "/V2/video_insights", P(400, {"error": {"code": 4, "message": "limit"}})])
        ma, cong = self.chay(m)
        self.assertEqual(ma, 1)
        fb = [b["id_bai"] for b in cong.bai_da_ghi() if b["nen_tang"] == "Facebook"]
        self.assertEqual(fb, ["V1"])                               # V1 truoc V2 giu; V2 + trang 2 khong duoc goi
        self.assertEqual(m.dem("GET", "/V3/"), 0)
        self.assertEqual(m.dem("GET", "/PAGE1/videos"), 1)
        self.assertEqual(len(self.ntfy), 1)

    def test_thieu_khoa_zernio_loi_kenh_tiktok(self):
        os.environ.pop("ZERNIO_KHOA")
        ma, cong = self.chay(mang_day_du())
        self.assertEqual(ma, 1)
        self.assertNotIn("TikTok", {b["nen_tang"] for b in cong.bai_da_ghi()})
        self.assertIn("TikTok", self.ntfy[0][1])

    def test_thieu_token_kenh(self):
        cong = CongDo(DONG_SO)
        cong.token["threads"] = None
        ma, cong = self.chay(mang_day_du(), cong)
        self.assertEqual(ma, 1)
        self.assertIn("Threads", self.ntfy[0][1])

    def test_thu_loi_khong_ntfy(self):
        os.environ.pop("ZERNIO_KHOA")
        ma, _ = self.chay(mang_day_du(), che_do="thu")
        self.assertEqual(ma, 1)
        self.assertEqual(self.ntfy, [])

    def test_thieu_sg_cong_khoa_ma_2(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SG_CONG_KHOA", None)
            buf = io.StringIO()
            with contextlib.redirect_stderr(buf):
                self.assertEqual(chay.main(["--che-do", "thu"]), 2)

    def test_doc_so_loi_khong_ghi_gi(self):
        cong = CongDo(so.LoiCong("so hong"))
        ma, cong = self.chay(mang_day_du(), cong)
        self.assertEqual((ma, cong.ghi), (1, []))
        self.assertEqual(len(self.ntfy), 1)

    def test_ngoai_le_bat_ngo_bat_o_main(self):
        cong = CongDo(ZeroDivisionError("boom"))
        ma, _ = self.chay(mang_day_du(), cong)
        self.assertEqual(ma, 1)
        self.assertEqual(self.ntfy[0][0], "Đo số liệu: lỗi bất ngờ")

    def test_loi_ghi_van_ghi_lo_con_lai_va_ma_1(self):
        cong = CongDo(DONG_SO, hong_ghi=lambda i: i == 0)
        with mock.patch.object(chay, "LO_GHI", 5):
            ma, cong = self.chay(mang_day_du(), cong)
        self.assertEqual(ma, 1)
        self.assertGreaterEqual(len(cong.ghi), 3)                  # lo dau loi, cac lo sau van ghi
        self.assertEqual(self.ntfy[0][0], "Đo số liệu: lỗi ghi sổ")


class Review(Chung):
    def _fb(self, m, quy_tac):
        m.luat.insert(0, ["GET", "/V2/video_insights", quy_tac])

    def test_200_than_khong_phai_json_la_loi_bai(self):
        m = mang_day_du()
        self._fb(m, P(200, raw=b"<html>oops</html>"))
        ma, cong = self.chay(m)
        self.assertEqual({b["id_bai"] for b in cong.bai_da_ghi() if b["nen_tang"] == "Facebook"}, {"V1", "V3"})
        self.assertIn("Facebook: 2 bai, 1 loi bai", self.log)

    def test_insights_rong_hoac_thieu_luot_xem_bo_bai(self):
        for thieu in (P(body={"data": []}), P(body={}), P(body={"data": chi_so(post_video_view_time=5)}),
                      P(body={"data": [{"name": "fb_reels_total_plays", "values": "sai"}]})):
            m = mang_day_du()
            self._fb(m, thieu)
            _, cong = self.chay(m)
            self.assertNotIn("V2", {b["id_bai"] for b in cong.bai_da_ghi() if b["nen_tang"] == "Facebook"})
            self.assertIn("1 loi bai", self.log)

    def test_loi_bat_ngo_mot_bai_co_lap_con_gioi_han_van_dung_kenh(self):
        m = mang_day_du()
        # 'length' kieu la gay loi bat ngo? dung mock truc tiep: _dong nem o dung bai V1
        that = chay._dong
        def nem(ten, id_bai, *a, **k):
            if id_bai == "V2":
                raise RuntimeError("boom")
            return that(ten, id_bai, *a, **k)
        with mock.patch.object(chay, "_dong", nem):
            _, cong = self.chay(m)
        fb = {b["id_bai"] for b in cong.bai_da_ghi() if b["nen_tang"] == "Facebook"}
        self.assertEqual(fb, {"V1", "V3"})
        self.assertIn("Facebook: 2 bai, 1 loi bai", self.log)

    def test_nguoi_theo_doi_loi_la_loi_kenh_nhung_van_ghi_bai(self):
        for ten, duoi, tra in (("Facebook", "/PAGE1", P(500, {"error": {"code": 1}})), ("Instagram", "/IGU1", P(body={})),
                               ("Threads", "/THU1/threads_insights", P(body={"data": []}))):
            m = mang_day_du()

            def goi(method, url, _m=m, _d=duoi, _t=tra, **kw):
                return _t if url.split("?")[0].endswith(_d) else _m(method, url, **kw)
            self.ntfy.clear()
            ma, cong = self.chay(goi)
            self.assertEqual(ma, 1, ten)
            self.assertIn("nguoi theo doi " + ten, self.log)
            self.assertNotIn(ten, {k["nen_tang"] for k in cong.ghi[0]["kenh"]})
            self.assertIn(ten, {b["nen_tang"] for b in cong.bai_da_ghi()})     # bai da do van ghi
            self.assertEqual(len(self.ntfy), 1)

    def test_tiktok_gio_bien_90_phut(self):
        for lech, ky_vong in ((5400, "top5"), (5401, None)):
            gio_post = dt.datetime(2026, 10, 14, 5, 30, tzinfo=dt.timezone.utc)
            gio_so = (gio_post + dt.timedelta(seconds=lech)).isoformat()
            m = mang_day_du()
            m.luat.insert(0, ["GET", "zernio.com/api/v1/analytics", P(body={
                "posts": [{"_id": "B1", "status": "published", "publishedAt": gio_post.isoformat(), "analytics": {"views": 1}}],
                "accounts": [{"_id": chay.zernio.ACC_MAC_DINH, "followersCount": 3}]})])
            cong = CongDo([so_dang("tiktok", "ZH", "top5", gio=gio_so)])
            _, cong = self.chay(m, cong)
            tt = [b for b in cong.bai_da_ghi() if b["nen_tang"] == "TikTok"]
            self.assertEqual(tt[0]["dang"], ky_vong, lech)

    def test_tiktok_chi_nhan_tai_khoan_dich_khi_env_doi(self):
        m = mang_day_du()
        m.luat.insert(0, ["GET", "zernio.com/api/v1/analytics", P(body={
            "posts": [{"_id": "B1", "status": "published", "publishedAt": MOI, "accountId": chay.zernio.ACC_MAC_DINH, "analytics": {"views": 1}},
                      {"_id": "B2", "status": "published", "publishedAt": MOI, "accountId": "TK-MOI", "analytics": {"views": 1}},
                      {"_id": "B3", "status": "published", "publishedAt": MOI, "analytics": {"views": 1}}],     # khong ghi tai khoan: nhan
            "accounts": [{"_id": chay.zernio.ACC_MAC_DINH, "followersCount": 1}, {"_id": "TK-MOI", "followersCount": 8}]})])
        with mock.patch.dict(os.environ, {"ZERNIO_TIKTOK_ACC": "TK-MOI"}):
            _, cong = self.chay(m)
        self.assertEqual({b["id_bai"] for b in cong.bai_da_ghi() if b["nen_tang"] == "TikTok"}, {"B2", "B3"})
        self.assertEqual({k["nen_tang"]: k["nguoi_theo_doi"] for k in cong.ghi[0]["kenh"]}["TikTok"], 8)

    def test_co_da_bao_chi_khi_ntfy_thanh_cong(self):
        d = tempfile.mkdtemp(prefix="sg-do-")
        for tra, co_file in ((True, True), (False, False), (None, False)):
            f = os.path.join(d, f"co-{tra}")
            os.environ["DA_BAO_FILE"] = f
            self.addCleanup(os.environ.pop, "DA_BAO_FILE", None)
            with mock.patch.object(ntfy, "loi", lambda *a, **k: tra):
                os.environ.pop("ZERNIO_KHOA", None)
                self.chay(mang_day_du())
            self.assertEqual(os.path.exists(f), co_file, tra)
            os.environ["ZERNIO_KHOA"] = ZK


class NhoLe(unittest.TestCase):
    def test_con_giay_3_tu_duong_cong(self):
        f = chay.con_giay_3
        self.assertEqual(f({"0": 1, "1": 0.78, "2": 0.32, "3": 0.22, "4": 0.17}), 22.0)       # co dung khoa 3
        self.assertEqual(f({"0": 1, "2": 0.4, "4": 0.2}), 30.0)                               # buoc 2 s: noi suy 2->4
        self.assertEqual(f({"0": 1, "6": 0.4}), 70.0)                                          # buoc 6 s
        self.assertIsNone(f({"0": 1, "1": 0.5, "2": 0.3}))                                     # video ngan hon 3 s
        self.assertIsNone(f({}))
        self.assertIsNone(f(None))
        self.assertIsNone(f({"4": 0.2, "5": 0.1}))                                             # khong co diem truoc giay 3
        self.assertEqual(f({"0": 1, "x": 5, "3": "0.5", "4": None}), 50.0)                     # khoa/gia tri rac bi bo
        self.assertIsNone(f({"0": 1, "3": 7}))                                                 # ti le vo ly

    def test_chia_lo_500_kenh_chi_o_lo_dau(self):
        cong = CongDo()
        gio = dt.datetime(2026, 10, 14, 0, 30, tzinfo=dt.timezone.utc)
        bai = [chay._dong("Facebook", str(i), gio, None, None, False, None, None) for i in range(1200)]
        kenh = [{"nen_tang": "Facebook", "nguoi_theo_doi": 1}]
        self.assertEqual(chay.ghi(cong, "2026-10-15T16:00:00Z", bai, kenh), [])
        self.assertEqual([len(l["bai"]) for l in cong.ghi], [500, 500, 200])
        self.assertEqual([len(l["kenh"]) for l in cong.ghi], [1, 0, 0])
        self.assertTrue(all(l["do_luc"] == "2026-10-15T16:00:00Z" for l in cong.ghi))

    def test_chi_kenh_khong_bai_van_ghi_mot_lan(self):
        cong = CongDo()
        chay.ghi(cong, "2026-10-15T16:00:00Z", [], [{"nen_tang": "Facebook", "nguoi_theo_doi": 1}])
        self.assertEqual(len(cong.ghi), 1)
        cong2 = CongDo()
        chay.ghi(cong2, "2026-10-15T16:00:00Z", [], [])
        self.assertEqual(cong2.ghi, [])

    def test_nhan_khuon(self):
        self.assertEqual(chay.nhan_khuon("keo-thom-2", 30, False), "Kèo 15:00")
        self.assertEqual(chay.nhan_khuon("carousel", None, False), "carousel")
        self.assertEqual(chay.nhan_khuon("carousel", None, True), "carousel (chữ)")
        self.assertEqual(chay.nhan_khuon("tin-web", None, True), "Tin web")
        self.assertEqual(chay.nhan_khuon(None, 121, False), "Video dài")
        self.assertEqual(chay.nhan_khuon(None, 120, False), "tin-nóng / ngoài lịch")
        self.assertEqual(chay.nhan_khuon(None, None, True), "tin-nóng / ngoài lịch (chữ)")

    def test_dong_loai_id_sai_va_so_am(self):
        gio = dt.datetime(2026, 10, 14, 0, 30, tzinfo=dt.timezone.utc)
        self.assertIsNone(chay._dong("Facebook", "a b", gio, None, None, False, None, None))
        self.assertIsNone(chay._dong("Facebook", "ok", None, None, None, False, None, None))
        d = chay._dong("Facebook", "ok", gio, None, None, False, "http://x", "t", luot_xem=3, thich="5", xem_tb_giay=float("nan"))
        self.assertEqual((d["luot_xem"], d["thich"], d["xem_tb_giay"], d["link"]), (3, 5, None, None))
        # vuot gioi han cong -> BO BAI (None), khong ghi null
        self.assertIsNone(chay._dong("Facebook", "ok", gio, None, None, False, None, None, luot_xem=-1))
        self.assertIsNone(chay._dong("Facebook", "ok", gio, None, None, False, None, None, luot_xem=2 ** 53))
        self.assertIsNone(chay._dong("Facebook", "ok", gio, None, None, False, None, None, xem_tb_giay=1e7))
        self.assertIsNone(chay._dong("Facebook", "ok", gio, None, None, False, None, None, do_dai_giay=-0.5))
        self.assertIsNotNone(chay._dong("Facebook", "ok", gio, None, None, False, None, None, luot_xem=2 ** 53 - 1, xem_tb_giay=9999999.9))

    def test_hop_le_cong(self):
        gio = dt.datetime(2026, 10, 14, 0, 30, tzinfo=dt.timezone.utc)
        d = chay._dong("Facebook", "ok", gio, None, None, False, None, None)
        self.assertTrue(chay.hop_le_cong(d))
        for sai in ({"nen_tang": "X"}, {"id_bai": "a b"}, {"ngay": "2026-02-30"}, {"gio_dang": "2026-10-14T00:30:00"},
                    {"gio_dang": None}, {"ngay": None}, {"link": "http://x"}, {"thich": 1.5}, {"thich": True}, {"khuon": 5}):
            self.assertFalse(chay.hop_le_cong({**d, **sai}), sai)

    def test_ins_sai_cau_truc(self):
        for bad in (None, {}, "x", [1], [{"name": "views", "values": "abc"}], [{"name": "views", "values": []}],
                    [{"name": "views", "values": [5]}], [{"name": "views", "total_value": 5}], [{"name": "views"}]):
            self.assertIsNone(chay._ins(bad, "views"), bad)
        self.assertEqual(chay._ins([{"name": "views", "values": [{"value": 4}]}], "views"), 4)
        self.assertEqual(chay._ins([{"name": "views", "total_value": {"value": 6}}], "views"), 6)
        self.assertIsNone(chay._so({"a": 1}))

    def test_thoi_gian_va_thoi_luong(self):
        self.assertEqual(chay.tg("2026-10-14T00:30:00+0000"), dt.datetime(2026, 10, 14, 0, 30, tzinfo=dt.timezone.utc))
        self.assertEqual(chay.tg("2026-10-14T07:30:00+07:00").utcoffset(), dt.timedelta(hours=7))
        self.assertIsNone(chay.tg("khong phai gio"))
        self.assertEqual(chay.giay_iso("PT1M5S"), 65)
        self.assertEqual(chay.giay_iso("PT1H"), 3600)
        self.assertEqual(chay.giay_iso("PT1H2M3S"), 3723)
        self.assertEqual(chay.giay_iso("PT45S"), 45)
        self.assertEqual(chay.giay_iso("P1DT2H"), 93600)
        for la in ("P0D", "", "abc", "PT", None):
            self.assertIsNone(chay.giay_iso(la), la)

    def test_cua_so_so_ngay_ngan_hon_dau_cua_so(self):
        cong = CongDo(DONG_SO)
        with mock.patch.object(chung, "bay_gio", lambda: NOW), mock.patch.object(http, "gui", mang_day_du()), \
                mock.patch.dict(os.environ, {"ZERNIO_KHOA": ZK}), mock.patch.object(yt, "lam_moi_access", lambda tk: (YT_ACC, None)), \
                contextlib.redirect_stdout(io.StringIO()):
            chay.main(["--che-do", "thu", "--so-ngay", "1"], cong=cong)
        self.assertEqual(cong.hoi_so[0][0], "2026-10-14")            # 15/10 16:00Z - 1 ngay = 14/10 23:00 VN
        self.assertEqual(len(cong.hoi_so), 2)


if __name__ == "__main__":
    unittest.main()
