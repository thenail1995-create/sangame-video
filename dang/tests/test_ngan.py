"""dang/ngan.py: bo dang tay video ngan. Ham thuan (kiem_chu, kiem_tieu_de_yt, cach_gio_tiktok, gio_tiktok_zernio, tham_yt, chan)
+ chay main() voi HTTP gia: payload ig/fb/hen-fb/yt/hen-yt/tiktok co nhan AI, kiem chu/gio chan truoc moi goi mang, chay lai khi
dang_lam khong goi mang. Khong goi mang that."""
import contextlib
import datetime as dt
import io
import json
import pathlib
import tempfile
import unittest
from unittest import mock

from dang import chung, http, ngan, ntfy, yt, zernio
from dang.chung import LoiDang, VN
from dang.tests.gia_lap import Mang, P, TOKEN_GIA

BAY_GIO = dt.datetime(2026, 10, 27, 3, 0, tzinfo=dt.timezone.utc)      # 10:00 VN 27/10
HEN = "2026-10-28T12:00:00+07:00"
ACC = zernio.ACC_MAC_DINH


def vn(y, m, d, h, mi=0, s=0):
    return dt.datetime(y, m, d, h, mi, s, tzinfo=VN)


class KiemChu(unittest.TestCase):
    URL = ["https://sangame.com.vn", "http://x.vn/a", "HTTP://EXAMPLE.COM", "www.sangame.com.vn", "sangame.com.vn",
           "sangame.com.vn/game-x.html", "Sangame.Com.VN/Game", "abc.xyz/path", "shop.example.co.uk", "bit.ly/abc",
           "Xem tại example.com, nhé", "Giá ở sangame.com.vn."]
    KHONG_PHAI = ["email a@sangame.com.vn", "Dead Space Deluxe 496 nghìn", "$15,99 giá gốc $79,99", "giảm tới 5/11.", "PS5 còn 1.048.000đ",
                  "ba thẻ 10 đô, 5 đô, 1 đô là vừa khít"]

    def test_url_cac_dang_bi_bat_o_ca_ba_kenh(self):
        for kenh in ("fb", "ig", "tiktok"):
            for u in self.URL:
                loi = ngan.kiem_chu(kenh, f"Dead Space còn 496 nghìn. {u}")
                self.assertTrue(any("URL" in x for x in loi), (kenh, u, loi))

    def test_khong_phai_url_thi_dat(self):
        for kenh in ("fb", "ig", "tiktok"):
            for t in self.KHONG_PHAI:
                self.assertEqual(ngan.kiem_chu(kenh, t), [], (kenh, t))

    def test_tran_hashtag(self):
        self.assertEqual(ngan.kiem_chu("ig", "x #a #b #c #d #e"), [])
        self.assertEqual(len(ngan.kiem_chu("ig", "x #a #b #c #d #e #f")), 1)
        self.assertEqual(ngan.kiem_chu("fb", "x #a #b #c"), [])
        self.assertEqual(len(ngan.kiem_chu("fb", "x #a #b #c #d")), 1)
        self.assertEqual(ngan.kiem_chu("tiktok", "x #a #b #c"), [])
        self.assertEqual(len(ngan.kiem_chu("tiktok", "x #a #b #c #d")), 1)

    def test_tiktok_150_ky_tu(self):
        self.assertEqual(ngan.kiem_chu("tiktok", "a" * 150), [])
        self.assertTrue(any("150" in x for x in ngan.kiem_chu("tiktok", "a" * 151)))

    def test_tieu_de_yt_100(self):
        self.assertEqual(ngan.kiem_chu("youtube_tieu_de", "a" * 100), [])
        self.assertTrue(any("100" in x for x in ngan.kiem_chu("youtube_tieu_de", "a" * 101)))
        self.assertEqual(ngan.kiem_chu("youtube_tieu_de", "Xem sangame.com.vn"), [])   # YT tieu de khong cam URL theo ke hoach

    def test_rong(self):
        self.assertTrue(ngan.kiem_chu("fb", "  "))


class KiemTieuDeYT(unittest.TestCase):
    def test_mo_bang_ten_game_dat(self):
        self.assertEqual(ngan.kiem_tieu_de_yt("Dead Space Deluxe PS5 chỉ 496 nghìn #DeadSpace", "Dead Space"), [])
        self.assertEqual(ngan.kiem_tieu_de_yt("dead space còn rẻ", "DEAD SPACE"), [])                    # khong phan biet hoa thuong
        self.assertEqual(ngan.kiem_tieu_de_yt("Đấu Trường Ánh Sáng rẻ", "Dau Truong Anh Sang"), [])      # so khong dau
        self.assertEqual(ngan.kiem_tieu_de_yt("Marvel's Spider-Man 2 giảm sâu", "Marvels Spider Man 2"), [])

    def test_khong_mo_bang_ten_game_truot(self):
        self.assertTrue(ngan.kiem_tieu_de_yt("PS5 chỉ 496 nghìn: Dead Space Deluxe", "Dead Space"))
        self.assertTrue(ngan.kiem_tieu_de_yt("Dead Spaceship rẻ", "Dead Space"))                       # khong khop nua tu
        self.assertTrue(ngan.kiem_tieu_de_yt("Dead Space rẻ", ""))                                      # thieu ten game

    def test_viet_hoa_ca_cau_truot(self):
        self.assertTrue(any("viết hoa" in x for x in ngan.kiem_tieu_de_yt("DEAD SPACE DELUXE CHỈ 496 NGHÌN", "Dead Space")))
        self.assertFalse(any("viết hoa" in x for x in ngan.kiem_tieu_de_yt("Dead Space Deluxe PS5 chỉ 496 nghìn", "Dead Space")))


class CachGioTikTok(unittest.TestCase):
    def test_cach_du_3h_dat(self):
        self.assertEqual(ngan.cach_gio_tiktok(vn(2026, 10, 28, 12), [vn(2026, 10, 28, 9), vn(2026, 10, 28, 15)]), [])
        self.assertEqual(ngan.cach_gio_tiktok(vn(2026, 10, 28, 12), []), [])

    def test_cach_duoi_3h_truot_ca_hai_phia(self):
        self.assertEqual(len(ngan.cach_gio_tiktok(vn(2026, 10, 28, 12), [vn(2026, 10, 28, 9, 1)])), 1)
        self.assertEqual(len(ngan.cach_gio_tiktok(vn(2026, 10, 28, 12), [vn(2026, 10, 28, 14, 59)])), 1)
        self.assertEqual(len(ngan.cach_gio_tiktok(vn(2026, 10, 28, 12), [vn(2026, 10, 28, 12)])), 1)
        self.assertEqual(len(ngan.cach_gio_tiktok(vn(2026, 10, 28, 12), [vn(2026, 10, 28, 11), vn(2026, 10, 28, 13)])), 2)

    def test_toi_thieu_tuy_chinh_va_mui_gio_khac_nhau(self):
        self.assertEqual(ngan.cach_gio_tiktok(vn(2026, 10, 28, 12), [vn(2026, 10, 28, 10)], dt.timedelta(hours=2)), [])
        utc = dt.datetime(2026, 10, 28, 4, 0, tzinfo=dt.timezone.utc)      # 11:00 VN
        self.assertEqual(len(ngan.cach_gio_tiktok(vn(2026, 10, 28, 12), [utc])), 1)


class GioTikTokZernio(unittest.TestCase):
    def _post(self, gio, status="published", acc=ACC, pl_status=None, platform="tiktok", **them):
        pl = {"platform": platform, "accountId": acc}
        if pl_status:
            pl["status"] = pl_status
        return {"_id": "p" + gio, "status": status, "scheduledFor": gio, "platforms": [pl], **them}

    def _mang(self, zernio_trang, external_trang):
        """zernio_trang: cac trang theo cursor; external_trang: cac trang theo page (1, 2, ...)."""
        def f(me, u, kw):
            p = kw["params"]
            if p.get("source") == "external":
                i = p["page"] - 1
                return P(body={"posts": external_trang[i] if i < len(external_trang) else []})
            i = 0 if "cursor" not in p else int(p["cursor"][1:]) - 1
            return P(body={"posts": zernio_trang[i], "pagination": {"nextCursor": f"C{i + 2}" if i + 1 < len(zernio_trang) else None}})
        return Mang().them("GET", "/posts", f)

    def test_nhieu_trang_moc_sat_00h_va_loc_trang_thai(self):
        trang1 = [
            self._post("2026-10-26T17:30:00Z"),                       # 27/10 00:30 VN  -> lay
            self._post("2026-10-27T16:59:59Z"),                       # 27/10 23:59:59 VN -> lay
            self._post("2026-10-27T17:00:00Z"),                       # 28/10 00:00 VN -> bo
            self._post("2026-10-26T16:59:59Z"),                       # 26/10 23:59:59 VN -> bo
            self._post("2026-10-27T05:00:00Z", status="cancelled"),   # bo
        ]
        trang2 = [
            self._post("2026-10-27T06:00:00Z", status="draft"),                   # bo
            self._post("2026-10-27T07:00:00Z", pl_status="failed"),               # bo
            self._post("2026-10-27T08:00:00Z", acc="KHAC"),                       # tai khoan khac -> bo
            self._post("2026-10-27T03:00:00Z"),                                   # 10:00 VN -> lay
            {"_id": "q", "status": "scheduled", "platforms": [{"platform": "tiktok", "accountId": {"_id": ACC}, "publishedAt": "2026-10-27T09:00:00+00:00"}]},  # 16:00 VN -> lay
            self._post("2026-10-27T10:00:00Z", platform="instagram"),             # khong phai tiktok -> bo
        ]
        m = self._mang([trang1, trang2], [])
        with mock.patch("dang.http.gui", m):
            kq = ngan.gio_tiktok_zernio("KHOAZERNIO1", ACC, dt.date(2026, 10, 27))
        self.assertEqual(sorted(t.strftime("%d %H:%M:%S") for t in kq), ["27 00:30:00", "27 10:00:00", "27 16:00:00", "27 23:59:59"])
        self.assertTrue(all(t.utcoffset() == dt.timedelta(hours=7) for t in kq))
        zs = [k["params"] for me, u, k in m.goi if "source" not in k["params"]]
        self.assertEqual((zs[0]["platform"], zs[0]["accountId"], zs[0]["fromDate"], zs[0]["toDate"], zs[0]["limit"]), ("tiktok", ACC, "2026-10-26", "2026-10-28", 50))
        self.assertNotIn("cursor", zs[0])
        self.assertEqual(zs[1]["cursor"], "C2")
        self.assertEqual(m.goi[0][2]["headers"]["Authorization"], "Bearer KHOAZERNIO1")

    def test_hop_nhat_source_external_khu_trung_theo_id(self):
        # bai dang thang tren TikTok (Zernio dong bo ve) chi co o external; bai tao qua Zernio co the xuat hien o ca hai
        zn = [self._post("2026-10-27T03:00:00Z", platformPostId="TT1")]
        ngoai_p1 = [dict(self._post("2026-10-27T03:00:00Z"), _id="ex1", platformPostId="TT1")] + \
            [{"_id": f"e{i}", "status": "published", "platformPostId": f"E{i}", "publishedAt": "2026-10-27T12:00:00Z", "accountId": ACC} for i in range(49)]
        ngoai_p2 = [{"_id": "e99", "status": "published", "platformPostId": "E99", "publishedAt": "2026-10-27T13:00:00Z", "accountId": ACC}]
        m = self._mang([zn], [ngoai_p1, ngoai_p2])
        with mock.patch("dang.http.gui", m):
            kq = ngan.gio_tiktok_zernio("KHOAZERNIO1", ACC, dt.date(2026, 10, 27))
        gio = sorted(t.strftime("%H:%M") for t in kq)
        self.assertEqual(gio.count("10:00"), 1)        # TT1 khu trung giua hai nguon
        self.assertIn("20:00", gio)                    # bai chi co o external (trang 2) van duoc doc
        ex = [k["params"] for me, u, k in m.goi if k["params"].get("source") == "external"]
        self.assertEqual([p["page"] for p in ex], [1, 2])
        self.assertTrue(all(p["accountId"] == ACC and p["limit"] == 50 for p in ex))
        self.assertTrue(all("cursor" not in p for p in ex))     # docs: cursor khong dung duoc voi source=external

    def test_external_loi_thi_nem_khong_doan(self):
        def f(me, u, kw):
            return P(400, {"error": "khong ho tro"}) if kw["params"].get("source") == "external" else P(body={"posts": [], "pagination": {}})
        with mock.patch("dang.http.gui", Mang().them("GET", "/posts", f)):
            with self.assertRaises(LoiDang) as c:
                ngan.gio_tiktok_zernio("KHOAZERNIO1", ACC, dt.date(2026, 10, 27))
        self.assertIn("external", str(c.exception))

    def test_loi_thi_nem_khong_dang_mu(self):
        with self.assertRaises(LoiDang):
            ngan.gio_tiktok_zernio("", ACC, dt.date(2026, 10, 27))
        for tra in (P(400, {"error": "param la"}), P(500, {}), P(body={"khong": "co posts"}), http.LoiMang("GET /posts: timeout")):
            with mock.patch("dang.http.gui", Mang().them("GET", "/posts", tra)):
                with self.assertRaises(LoiDang):
                    ngan.gio_tiktok_zernio("KHOAZERNIO1", ACC, dt.date(2026, 10, 27))


class ThamYT(unittest.TestCase):
    def test_body_co_co_ai_va_publish_at(self):
        b = ngan.tham_yt("Dead Space rẻ", "mo ta", ["a", "b"], "private")
        self.assertEqual(b["status"], yt.trang_thai("private"))
        self.assertIs(b["status"]["containsSyntheticMedia"], True)
        self.assertNotIn("publishAt", b["status"])
        self.assertEqual((b["snippet"]["title"], b["snippet"]["tags"], b["snippet"]["categoryId"]), ("Dead Space rẻ", ["a", "b"], "20"))
        h = ngan.tham_yt("t", "m", [], "private", "2026-10-28T05:00:00Z")
        self.assertEqual((h["status"]["publishAt"], h["status"]["privacyStatus"], h["status"]["containsSyntheticMedia"]),
                         ("2026-10-28T05:00:00Z", "private", True))
        with mock.patch.object(chung, "CO_GIONG_AI", False):
            self.assertNotIn("containsSyntheticMedia", ngan.tham_yt("t", "m", [], "public")["status"])


class Chan(unittest.TestCase):
    def test_chan(self):
        ngan.chan([])
        with self.assertRaises(SystemExit) as c:
            ngan.chan(["loi 1", "loi 2"])
        self.assertIn("loi 1", str(c.exception))
        self.assertIn("loi 2", str(c.exception))


CHU = """# Chu

## YouTube · tiêu đề
```
Dead Space Deluxe PS5 chỉ 496 nghìn: mua sao cho khít tiền? #DeadSpace #PS5 #SănGame
```

## YouTube · mô tả
```
Dead Space Digital Deluxe Edition đang giảm 80% trên PS Store Mỹ.

#DeadSpace #PS5 #SănGame
```

## TikTok
```
Dead Space Deluxe còn 496 nghìn, mua sao cho khít tiền? #deadspace #ps5 #săngame
```

## Instagram
```
Dead Space Deluxe PS5 còn 496 nghìn. Bảng giá các vùng: link ở bio.
#DeadSpace #PS5 #SănGame #GiảmGiá
```

## Facebook
```
Dead Space Deluxe PS5 còn 496 nghìn: ba thẻ PSN 10 đô, 5 đô, 1 đô là vừa khít.
#DeadSpace #PS5 #SănGame
```
"""


class MainVoiHttpGia(unittest.TestCase):
    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp(prefix="sg-ngan-"))
        self.bai = {"ten": "sangame-2026-10-27-dead-space", "ngay": "2026-10-27", "video": "v.mp4", "game": "Dead Space", "gio_hen": HEN, "tags": ["PS5"]}
        self.viet()
        (self.dir / "v.mp4").write_bytes(b"VIDEO" * 100)
        self.loi = []
        yt._cache.clear()
        for p in (mock.patch.object(ngan, "_tk", lambda kenh: dict(TOKEN_GIA[kenh])),
                  mock.patch.object(ngan, "_khoa_zernio", lambda: "ZKHOAGIA123456"),
                  mock.patch.object(chung, "ngu", lambda s: None),
                  mock.patch.object(chung, "bay_gio", lambda: BAY_GIO),
                  mock.patch.object(ntfy, "loi", lambda *a, **k: self.loi.append(a))):
            p.start()
            self.addCleanup(p.stop)

    def viet(self, chu=CHU, **sua):
        (self.dir / "bai.json").write_text(json.dumps({**self.bai, **sua}))
        (self.dir / "chu-video.md").write_text(chu, "utf-8")

    def chay(self, lenh, m):
        out = io.StringIO()
        with mock.patch("dang.http.gui", m), contextlib.redirect_stdout(out):
            try:
                ngan.main([str(self.dir), lenh])
                return None
            except SystemExit as e:
                return str(e)

    def ra(self, kenh):
        f = self.dir / "ra" / f"{kenh}.json"
        return json.loads(f.read_text("utf-8")) if f.exists() else None

    # ---- mang gia
    def m_zernio(self, bai_khac=()):
        m = Mang()
        m.them("GET", "tiktok/creator-info", P(body={"privacyLevels": [{"value": "PUBLIC_TO_EVERYONE"}], "canPostMore": True}))
        m.them("GET", "/accounts", P(body={"accounts": [{"_id": ACC, "platform": "tiktok", "username": "sangame.com.vn", "isActive": True}]}))
        m.them("GET", "/posts", lambda me, u, k: P(body={"posts": [] if k["params"].get("source") == "external" else list(bai_khac), "pagination": {}}))
        m.them("POST", "media/presign", P(body={"uploadUrl": "https://up.zernio/u", "publicUrl": "https://cdn.zernio/v.mp4"}))
        m.them("PUT", "up.zernio", P(200, {}))
        m.them("POST", "/posts", P(201, {"post": {"_id": "P1", "status": "published", "platforms": [{"platformPostUrl": "https://tiktok.com/p1"}]}}))
        return m

    def m_ig(self, tao=None):
        m = self.m_zernio()
        m.them("POST", "/IGU1/media_publish", P(body={"id": "M1"}))
        m.them("POST", "/IGU1/media", tao or P(body={"id": "C1"}))
        m.them("GET", "/C1", P(body={"status_code": "FINISHED"}))
        m.them("GET", "/M1", P(body={"permalink": "https://instagram.com/reel/M1"}))
        return m

    def m_fb(self, finish=None):
        m = Mang()
        m.them("POST", "/PAGE1/video_reels", lambda me, u, k: P(body={"video_id": "V1"}) if k["form"]["upload_phase"] == "start"
               else (finish or P(body={"success": True})))
        m.them("POST", "rupload.facebook.com", P(body={"success": True}))
        m.them("GET", "/V1", P(body={"status": {"uploading_phase": {"status": "complete"}}, "published": False}))
        m.them("POST", "/V1/comments", P(body={"id": "CM1"}))
        return m

    def m_yt(self, put):
        m = Mang().them("POST", "oauth2.googleapis.com", P(body={"access_token": "ya29.GIA_ACCESS_123456"}))
        m.them("POST", "upload/youtube", P(headers={"Location": "https://up.example/s"}))
        m.them("PUT", "up.example", P(200, {"id": "YV1"}))                 # insert KHONG tra status
        m.them("GET", "youtube/v3/videos", P(body={"items": [{"status": {"privacyStatus": "private"}}]}))
        m.them("PUT", "youtube/v3/videos", put)
        return m

    def tac_dung(self, m):
        """Cac goi co tac dung (khac GET)."""
        return [(me, u) for me, u, _ in m.goi if me != "GET"]

    CO = P(body={"status": {"containsSyntheticMedia": True}})

    # ---- IG
    def test_ig_payload_co_nhan_ai_va_ghi_so(self):
        m = self.m_ig()
        self.assertIsNone(self.chay("ig", m))
        f = [k["form"] for me, u, k in m.goi if me == "POST" and u.endswith("/IGU1/media")]
        self.assertEqual(len(f), 1)
        self.assertEqual((f[0]["media_type"], f[0]["is_ai_generated"], f[0]["share_to_feed"]), ("REELS", "true", "true"))
        self.assertNotIn("cover_url", f[0])
        self.assertEqual(f[0]["video_url"], "https://cdn.zernio/v.mp4")
        self.assertIn("link ở bio", f[0]["caption"])
        r = self.ra("ig")
        self.assertEqual((r["trang_thai"], r["id"], r["id_container"]), ("xong", "M1", "C1"))

    def test_chay_lai_khi_xong_khong_goi_mang(self):
        self.chay("ig", self.m_ig())
        m = self.m_ig()
        self.assertIsNone(self.chay("ig", m))
        self.assertEqual(m.goi, [])

    def test_chay_lai_khi_dang_lam_dung_kiem_tay_khong_goi_mang(self):
        (self.dir / "ra").mkdir()
        (self.dir / "ra" / "ig.json").write_text(json.dumps({"kenh": "ig", "trang_thai": "dang_lam", "id_container": "C9"}))
        m = self.m_ig()
        msg = self.chay("ig", m)
        self.assertIn("kiểm tay id", msg)
        self.assertIn("C9", msg)
        self.assertEqual(m.goi, [])

    def test_ig_meta_tu_choi_nhan_ai_loi_khong_tao_lai_va_go_dau_dang_lam(self):
        loi400 = P(400, {"error": {"message": "(#100) Param is_ai_generated is not supported", "code": 100}})
        m = self.m_ig(loi400)
        msg = self.chay("ig", m)
        self.assertIn("LỖI", msg)
        self.assertEqual(m.dem("POST", "/IGU1/media"), 1)
        self.assertEqual(m.dem("POST", "media_publish"), 0)
        self.assertIsNone(self.ra("ig"))                  # chac chan chua dang, chua co id -> chay lai duoc
        self.assertEqual(len(self.loi), 1)

    # ---- FB
    def test_fb_dang_ngay_va_hen_deu_co_nhan_ai(self):
        m = self.m_fb()
        self.assertIsNone(self.chay("fb", m))
        f = [k["form"] for me, u, k in m.goi if "video_reels" in u][-1]
        self.assertEqual((f["upload_phase"], f["video_state"], f["is_ai_generated"]), ("finish", "PUBLISHED", "true"))
        self.assertIn(chung.DONG_NHAN_AI, f["description"])
        self.assertEqual(self.ra("fb")["trang_thai"], "xong")
        (self.dir / "ra" / "fb.json").unlink()
        m = self.m_fb()
        self.assertIsNone(self.chay("hen-fb", m))
        f = [k["form"] for me, u, k in m.goi if "video_reels" in u][-1]
        self.assertEqual((f["video_state"], f["is_ai_generated"]), ("SCHEDULED", "true"))
        self.assertEqual(f["scheduled_publish_time"], str(int(dt.datetime.fromisoformat(HEN).timestamp())))

    def test_fb_meta_tu_choi_nhan_ai_giu_dang_lam_co_id_khong_thu_lai(self):
        m = self.m_fb(P(400, {"error": {"message": "(#100) Param is_ai_generated is not supported", "code": 100}}))
        msg = self.chay("fb", m)
        self.assertIn("LỖI", msg)
        self.assertEqual(len([1 for me, u, k in m.goi if "video_reels" in u and k["form"]["upload_phase"] == "finish"]), 1)
        r = self.ra("fb")
        self.assertEqual((r["trang_thai"], r["video_id"]), ("dang_lam", "V1"))     # da co video_id -> khong tu tao bai moi
        self.assertIn("kiểm tay id", self.chay("fb", self.m_fb()))

    # ---- YouTube
    def test_yt_private_xac_nhan_co_roi_moi_public(self):
        m = self.m_yt(self.CO)
        self.assertIsNone(self.chay("yt", m))
        body = [k["json_body"] for me, u, k in m.goi if "upload/youtube/v3/videos" in u][0]
        self.assertEqual((body["status"]["privacyStatus"], body["status"]["containsSyntheticMedia"]), ("private", True))
        self.assertNotIn("publishAt", body["status"])
        self.assertIn(chung.DONG_NHAN_AI, body["snippet"]["description"])
        puts = [k["json_body"]["status"] for me, u, k in m.goi if me == "PUT" and "youtube/v3/videos" in u]
        self.assertEqual([p["privacyStatus"] for p in puts], ["private", "public"])    # xac nhan co TRUOC khi public
        self.assertTrue(all(p["containsSyntheticMedia"] is True for p in puts))
        self.assertEqual(self.ra("youtube")["trang_thai"], "xong")

    def test_hen_yt_private_roi_private_kem_publish_at(self):
        m = self.m_yt(self.CO)
        self.assertIsNone(self.chay("hen-yt", m))
        body = [k["json_body"] for me, u, k in m.goi if "upload/youtube/v3/videos" in u][0]
        self.assertNotIn("publishAt", body["status"])                                    # tai len khong hen
        puts = [k["json_body"]["status"] for me, u, k in m.goi if me == "PUT" and "youtube/v3/videos" in u]
        self.assertEqual([p["privacyStatus"] for p in puts], ["private", "private"])
        self.assertNotIn("publishAt", puts[0])
        self.assertEqual(puts[1]["publishAt"], "2026-10-28T05:00:00Z")
        self.assertTrue(all(p["containsSyntheticMedia"] is True for p in puts))

    def test_yt_khong_xac_nhan_duoc_co_thi_khong_bao_gio_public(self):
        for put in (P(body={"status": {"privacyStatus": "private"}}), P(500, {}), P(400, {"error": {"message": "x"}})):
            (self.dir / "ra").mkdir(exist_ok=True)
            for f in (self.dir / "ra").glob("*.json"):
                f.unlink()
            m = self.m_yt(put)
            msg = self.chay("yt", m)
            self.assertIn("KHÔNG RÕ", msg)
            self.assertNotIn("public", [k["json_body"]["status"]["privacyStatus"] for me, u, k in m.goi if me == "PUT" and "youtube/v3/videos" in u])
            self.assertEqual(self.ra("youtube")["trang_thai"], "dang_lam")
            self.assertEqual(self.ra("youtube")["video_id"], "YV1")

    def test_hen_yt_phan_hoi_thieu_co_go_publish_at(self):
        m = self.m_yt([self.CO, P(body={"status": {"privacyStatus": "private"}}), self.CO])
        msg = self.chay("hen-yt", m)
        self.assertIn("KHÔNG RÕ", msg)
        puts = [k["json_body"]["status"] for me, u, k in m.goi if me == "PUT" and "youtube/v3/videos" in u]
        self.assertEqual(len(puts), 3)
        self.assertIn("publishAt", puts[1])
        self.assertNotIn("publishAt", puts[2])                                           # da go publishAt

    def test_yt_tieu_de_khong_mo_bang_ten_game_chan_truoc_moi_goi_mang(self):
        self.viet(CHU.replace("Dead Space Deluxe PS5 chỉ 496 nghìn: mua sao", "PS5: Dead Space Deluxe chỉ 496 nghìn: mua sao"))
        m = self.m_yt(self.CO)
        self.assertIn("MỞ bằng tên game", self.chay("yt", m))
        self.assertEqual(m.goi, [])
        self.assertIsNone(self.ra("youtube"))

    # ---- TikTok
    def test_tiktok_ngay_body_co_nhan_ai_va_publish_now(self):
        m = self.m_zernio()
        self.assertIsNone(self.chay("tiktok", m))
        body = [k["json_body"] for me, u, k in m.goi if me == "POST" and u.endswith("/posts")][0]
        self.assertIs(body["tiktokSettings"]["video_made_with_ai"], True)
        self.assertIs(body["publishNow"], True)
        self.assertNotIn("scheduledFor", body)
        self.assertEqual(body["mediaItems"][0]["url"], "https://cdn.zernio/v.mp4")
        self.assertEqual(self.ra("tiktok")["trang_thai"], "xong")

    def test_hen_tiktok_body_co_scheduled_for_va_nhan_ai(self):
        m = self.m_zernio()
        self.assertIsNone(self.chay("hen-tiktok", m))
        body = [k["json_body"] for me, u, k in m.goi if me == "POST" and u.endswith("/posts")][0]
        self.assertIs(body["tiktokSettings"]["video_made_with_ai"], True)
        self.assertEqual(dt.datetime.fromisoformat(body["scheduledFor"]), dt.datetime.fromisoformat(HEN))
        self.assertNotIn("publishNow", body)

    def test_hen_tiktok_cach_bai_khac_duoi_3h_chan_truoc_moi_goi_co_tac_dung(self):
        khac = {"_id": "k", "status": "scheduled", "scheduledFor": "2026-10-28T03:00:00Z", "platforms": [{"platform": "tiktok", "accountId": ACC}]}   # 10:00 VN, cach 2h
        m = self.m_zernio([khac])
        msg = self.chay("hen-tiktok", m)
        self.assertIn("cách", msg)
        self.assertEqual(self.tac_dung(m), [])             # khong presign, khong tao bai
        self.assertIsNone(self.ra("tiktok"))

    def test_tiktok_zernio_loi_thi_dung_khong_dang_mu(self):
        m = self.m_zernio()
        m.luat.insert(0, ["GET", "/posts", P(500, {})])
        msg = self.chay("hen-tiktok", m)
        self.assertIn("dừng", msg)
        self.assertEqual(self.tac_dung(m), [])

    def test_hen_qua_gan_bi_chan(self):
        self.viet(gio_hen="2026-10-27T10:05:00+07:00")      # bay gio 10:00 VN
        m = self.m_zernio()
        self.assertIn("10 phút", self.chay("hen-tiktok", m))

    # ---- kiem chu chan truoc moi goi mang
    def test_fb_co_url_chan_truoc_moi_goi_mang(self):
        self.viet(CHU.replace("là vừa khít.", "là vừa khít. Tra giá: https://sangame.com.vn"))
        m = self.m_fb()
        self.assertIn("URL", self.chay("fb", m))
        self.assertEqual(m.goi, [])
        self.assertIsNone(self.ra("fb"))

    def test_ig_qua_5_hashtag_chan(self):
        self.viet(CHU.replace("#GiảmGiá", "#GiảmGiá #A #B"))
        m = self.m_ig()
        self.assertIn("hashtag", self.chay("ig", m))
        self.assertEqual(m.goi, [])

    # ---- hen-yt: ket qua go publishAt
    def test_hen_yt_go_publish_at_ok_thong_bao_nhu_cu(self):
        m = self.m_yt([self.CO, P(body={"status": {"privacyStatus": "private"}}), self.CO])
        msg = self.chay("hen-yt", m)
        self.assertIn("đã gỡ publishAt", msg)
        self.assertNotIn("CÓ THỂ VẪN HẸN", msg)

    def test_hen_yt_go_publish_at_loi_bao_gỡ_tay(self):
        for rb in (P(500, {}), http.LoiMang("PUT: timeout")):
            for f in (self.dir / "ra").glob("*.json") if (self.dir / "ra").exists() else []:
                f.unlink()
            m = self.m_yt([self.CO, P(body={"status": {"privacyStatus": "private"}}), rb])
            msg = self.chay("hen-yt", m)
            self.assertIn("CÓ THỂ VẪN HẸN publishAt", msg)
            self.assertIn("YouTube Studio", msg)
            self.assertIn("KHÔNG RÕ", msg)

    # ---- khoa doc quyen + ghi nguyen tu
    def test_lock_dang_ton_tai_dung_khong_goi_mang_va_khong_xoa_lock(self):
        (self.dir / "ra").mkdir()
        (self.dir / "ra" / "ig.lock").write_text("123")
        m = self.m_ig()
        self.assertIn("ra/ig.lock", self.chay("ig", m))
        self.assertEqual(m.goi, [])
        self.assertTrue((self.dir / "ra" / "ig.lock").exists())
        self.assertIsNone(self.ra("ig"))

    def test_lock_chi_theo_kenh_va_xoa_sau_khi_xong_hoac_loi(self):
        (self.dir / "ra").mkdir()
        (self.dir / "ra" / "fb.lock").write_text("1")            # lock cua kenh khac khong chan ig
        self.assertIsNone(self.chay("ig", self.m_ig()))
        self.assertFalse((self.dir / "ra" / "ig.lock").exists())
        (self.dir / "ra" / "ig.json").unlink()
        loi400 = P(400, {"error": {"message": "(#100) Param is_ai_generated is not supported", "code": 100}})
        self.chay("ig", self.m_ig(loi400))
        self.assertFalse((self.dir / "ra" / "ig.lock").exists())  # loi cung nha lock

    def test_ghi_nguyen_tu_khong_de_lai_file_tam(self):
        from dang.ngan import Bai, _ghi, _doc
        b = Bai(self.dir)
        with mock.patch("os.replace", wraps=__import__("os").replace) as rp:
            _ghi(b, "ig", trang_thai="dang_lam")
            _ghi(b, "ig", id_container="C1")
        self.assertEqual(rp.call_count, 2)
        self.assertEqual(sorted(f.name for f in (self.dir / "ra").iterdir()), ["ig.json"])
        self.assertEqual(_doc(b, "ig")["id_container"], "C1")
        # ghi do (loi giua chung) khong lam hong file cu
        with mock.patch("os.replace", side_effect=OSError("het cho")):
            with self.assertRaises(OSError):
                _ghi(b, "ig", id="M1")
        self.assertEqual(_doc(b, "ig")["id_container"], "C1")
        self.assertNotIn("id", _doc(b, "ig"))

    # ---- gio_hen
    def test_gio_hen_thieu_mui_gio_bi_chan(self):
        self.viet(gio_hen="2026-10-28T12:00:00")
        m = self.m_zernio()
        msg = self.chay("hen-tiktok", m)
        self.assertIn("múi giờ", msg)
        self.assertIn("+07:00", msg)
        self.assertEqual(m.goi, [])

    def test_hen_tiktok_toi_da_6_ngay(self):
        self.viet(gio_hen="2026-11-03T10:00:00+07:00")           # bay gio 27/10 10:00 VN -> dung 7 ngay
        m = self.m_zernio()
        self.assertIn("6 ngày", self.chay("hen-tiktok", m))
        self.assertEqual(self.tac_dung(m), [])
        self.viet(gio_hen="2026-11-02T09:59:00+07:00")           # < 6 ngay -> dat
        self.assertIsNone(self.chay("hen-tiktok", self.m_zernio()))

    # ---- binh luan
    def test_binh_luan_fb_ig_tu_khoi_binh_luan(self):
        self.viet(CHU + "\n## Bình luận\n```\nBảng giá đủ vùng ở bio, game đang rẻ nhất ở Mỹ.\n```\n")
        (self.dir / "ra").mkdir()
        (self.dir / "ra" / "fb.json").write_text(json.dumps({"trang_thai": "xong", "video_id": "V1"}))
        (self.dir / "ra" / "ig.json").write_text(json.dumps({"trang_thai": "xong", "id": "M1"}))
        m = self.m_fb()
        m.them("POST", "/M1/comments", P(body={"id": "CM2"}))
        self.assertIsNone(self.chay("binh-luan", m))
        cm = [(u.rsplit("/", 2)[-2], k["form"]["message"]) for me, u, k in m.goi if u.endswith("/comments")]
        self.assertEqual([c[0] for c in cm], ["V1", "M1"])
        self.assertIn("Bảng giá đủ vùng", cm[0][1])
        self.assertEqual(self.ra("binh-luan")["trang_thai"], "xong")

    def test_binh_luan_khong_co_khoi_thi_khong_binh_luan(self):
        (self.dir / "ra").mkdir()
        (self.dir / "ra" / "fb.json").write_text(json.dumps({"trang_thai": "xong", "video_id": "V1"}))
        m = self.m_fb()
        self.assertIsNone(self.chay("binh-luan", m))
        self.assertEqual(m.goi, [])
        self.assertEqual(sorted(f.name for f in (self.dir / "ra").iterdir()), ["fb.json"])    # khong lock, khong trang thai dang_lam

    def test_binh_luan_theo_doi_rieng_tung_dich_chua_dang_thi_bo_qua_khong_danh_xong(self):
        self.viet(CHU + "\n## Bình luận\n```\nBảng giá đủ vùng ở bio.\n```\n")
        (self.dir / "ra").mkdir()
        (self.dir / "ra" / "fb.json").write_text(json.dumps({"trang_thai": "xong", "video_id": "V1"}))
        (self.dir / "ra" / "ig.json").write_text(json.dumps({"trang_thai": "dang_lam", "id_container": "C1"}))     # IG chua dang xong
        m = self.m_fb()
        self.assertIsNone(self.chay("binh-luan", m))
        self.assertEqual(self.ra("binh-luan")["fb"], "CM1")
        self.assertNotIn("trang_thai", self.ra("binh-luan"))                  # IG chua dang -> khong danh xong
        self.assertEqual(self.ra("binh-luan").get("ig"), None)
        # IG dang xong sau do: chay lai chi binh luan IG, khong binh luan FB lan nua
        (self.dir / "ra" / "ig.json").write_text(json.dumps({"trang_thai": "xong", "id": "M1"}))
        m = self.m_fb()
        m.them("POST", "/M1/comments", P(body={"id": "CM2"}))
        self.assertIsNone(self.chay("binh-luan", m))
        self.assertEqual([u for me, u, k in m.goi if u.endswith("/comments")], [m.goi[0][1]])
        self.assertTrue(m.goi[0][1].endswith("/M1/comments"))
        r = self.ra("binh-luan")
        self.assertEqual((r["fb"], r["ig"], r["trang_thai"]), ("CM1", "CM2", "xong"))

    def test_binh_luan_da_gui_chua_ghi_id_dung_kiem_tay(self):
        self.viet(CHU + "\n## Bình luận\n```\nok\n```\n")
        (self.dir / "ra").mkdir()
        (self.dir / "ra" / "fb.json").write_text(json.dumps({"trang_thai": "xong", "video_id": "V1"}))
        (self.dir / "ra" / "binh-luan.json").write_text(json.dumps({"fb_dang_lam": True}))
        m = self.m_fb()
        self.assertIn("kiểm tay", self.chay("binh-luan", m))
        self.assertEqual(m.goi, [])

    def test_binh_luan_fb_bai_hen_chua_cong_khai_bo_qua_da_cong_khai_thi_binh_luan(self):
        self.viet(CHU + "\n## Bình luận\n```\nok\n```\n")
        (self.dir / "ra").mkdir()
        (self.dir / "ra" / "fb.json").write_text(json.dumps({"trang_thai": "xong", "video_id": "V1", "hen": "1795000000"}))
        m = self.m_fb()                                                   # GET /V1 -> published False
        self.assertIsNone(self.chay("binh-luan", m))
        self.assertEqual(m.dem("POST", "/comments"), 0)
        self.assertEqual(m.dem("GET", "/V1"), 1)
        self.assertNotIn("fb", self.ra("binh-luan") or {})
        m = self.m_fb()
        m.luat.insert(0, ["GET", "/V1", P(body={"published": True})])
        self.assertIsNone(self.chay("binh-luan", m))
        self.assertEqual(m.dem("POST", "/V1/comments"), 1)
        self.assertEqual(self.ra("binh-luan")["fb"], "CM1")

    def test_binh_luan_ig_co_url_cung_tu_choi(self):
        self.viet(CHU + "\n## Bình luận\n```\nTra giá ở shop.vn/a nhé.\n```\n")
        (self.dir / "ra").mkdir()
        (self.dir / "ra" / "ig.json").write_text(json.dumps({"trang_thai": "xong", "id": "M1"}))
        m = self.m_fb()
        self.assertIn("SG-FB-2", self.chay("binh-luan", m))
        self.assertEqual(m.goi, [])

    def test_binh_luan_fb_co_url_tu_choi(self):
        self.viet(CHU + "\n## Bình luận\n```\nTra giá ở sangame.com.vn nhé.\n```\n")
        (self.dir / "ra").mkdir()
        (self.dir / "ra" / "fb.json").write_text(json.dumps({"trang_thai": "xong", "video_id": "V1"}))
        m = self.m_fb()
        self.assertIn("SG-FB-2", self.chay("binh-luan", m))
        self.assertEqual(m.goi, [])


if __name__ == "__main__":
    unittest.main()
