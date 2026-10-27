import contextlib
import datetime as dt
import io
import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from dang import chay, chung, gia, manifest, ntfy, site, so
from dang.chung import LoiDang
from dang.tests import gia_lap as g
from dang.tests.gia_lap import CongGia, Mang, P, NGAY, DANG, cong_day_du


def vo_ngu():
    return mock.patch.object(chung, "ngu", lambda s: None)


class KenhGia:
    """Module nen tang gia: dem so lan goi, co the bao loi."""

    def __init__(self, ten, loi_cb=None, loi_ck=None, danh_tinh=None):
        self.ten, self.loi_cb, self.loi_ck = ten, loi_cb, loi_ck
        self.dt = danh_tinh or g.DICH_DU[ten][chay.KHOA_DICH[ten]]
        self.cb = self.ck = self.hop = 0

    def danh_tinh(self, tk, nc=None):
        return self.dt

    def chuan_bi(self, tk, nc, luu):
        self.cb += 1
        if self.loi_cb:
            raise self.loi_cb
        luu(id_tai=f"{self.ten}-id")
        return {"id_tai": f"{self.ten}-id", "id_container": f"{self.ten}-c"}

    def cong_khai(self, tk, nc, dong):
        self.ck += 1
        if self.loi_ck:
            raise self.loi_ck
        return {"id_bai": f"{self.ten}-bai", "link": f"https://x/{self.ten}"}

    def hop_thu(self, tk, nc):
        self.hop += 1
        return {"id_tai": "PUB", "id_bai": "PUB", "link": None}


class Khung(unittest.TestCase):
    def setUp(self):
        self.thu_muc = tempfile.mkdtemp(prefix="sg-chay-")
        self.cong = cong_day_du()
        self.x_goi = 0
        self.kenh = {k: KenhGia(k) for k in chay.KENH if k in chay.KHOA_DICH}   # X (Buffer) khong co token/danh tinh
        self.ntfy = []
        self.dich = tempfile.mktemp(suffix=".json")
        self.viet_dich(g.DICH_DU)
        self.che_do = "that"
        self.man_kw = {}
        self.ps = [
            mock.patch.dict(chay.MOD, {k: v for k, v in self.kenh.items()}),
            mock.patch.object(chay.manifest, "tai_release", self.tai_release),
            mock.patch.object(chay.site, "kiem_url", lambda *a, **k: True),
            mock.patch.object(chay.gia, "kiem_lai", lambda m, gio: ([], [])),
            mock.patch.object(chay.ntfy, "tin", lambda t, n, **k: self.ntfy.append(("tin", t, n))),
            mock.patch.object(chay.ntfy, "loi", lambda t, n, **k: self.ntfy.append(("loi", t, n))),
            mock.patch.object(chay.ntfy, "chia_se_nhom", lambda d, n, l: self.ntfy.append(("nhom", d, l))),
            mock.patch.dict(os.environ, {"DICH_JSON": self.dich, "PAGES_URL": "https://x.github.io/sangame-video", "BUFFER_KHOA": "bk_test_123456"}),
            mock.patch.object(chay.x, "cong_khai", self.x_cong_khai),
            vo_ngu(),
            mock.patch.object(chung, "bay_gio", lambda: g.GIO_DANG),
        ]
        for p in self.ps:
            p.start()
            self.addCleanup(p.stop)
        # tiktok.hop_thu duoc goi qua module tiktok that -> tro vao KenhGia
        self.ps2 = mock.patch.object(chay.tiktok, "hop_thu", self.kenh["tiktok"].hop_thu)
        self.ps2.start()
        self.addCleanup(self.ps2.stop)

    def x_cong_khai(self, nc):
        self.x_goi += 1
        return {"id_bai": "x-bai", "link": "https://x/x", "kieu": "buffer"}

    def viet_dich(self, d):
        pathlib.Path(self.dich).write_text(json.dumps(d))

    def tai_release(self, ngay, dang, thu_muc, ban_can, repo=None, che_do=None):
        return g.tao_manifest(thu_muc, self.che_do, ngay, dang, **self.man_kw)

    def chay(self, pha, che_do=None):
        che_do = che_do or self.che_do
        return chay.main(["--pha", pha, "--dang", DANG, "--ngay", NGAY, "--che-do", che_do], cong=self.cong)


class TestChuanBiVaCongKhai(Khung):
    def test_luong_that_day_du(self):
        self.assertEqual(self.chay("chuan-bi"), 0)
        for k in ("fb", "ig", "youtube"):
            self.assertEqual(self.cong.trang_thai(k), "chuan_bi_xong")
            self.assertEqual(self.kenh[k].cb, 1)
        self.assertEqual(self.kenh["tiktok"].cb, 0)
        self.assertEqual(self.cong.dong[(NGAY, DANG, "ig", "that")]["id_container"], "ig-c")
        self.assertEqual(self.chay("cong-khai"), 0)
        for k in ("fb", "ig", "youtube"):
            self.assertEqual(self.cong.trang_thai(k), "da_dang")
            self.assertEqual(self.kenh[k].ck, 1)
            self.assertTrue(self.cong.dong[(NGAY, DANG, k, "that")]["gio_cong_khai"])
        self.assertEqual(self.cong.trang_thai("tiktok"), "da_dang")
        self.assertEqual(self.kenh["tiktok"].hop, 1)
        tin = [x for x in self.ntfy if x[0] == "tin"]
        self.assertEqual(len(tin), 1)
        self.assertIn("https://x/fb", tin[0][2])
        self.assertIn("hop thu", tin[0][2])
        # 14/10: nhac chia se bai Trang vao nhom FB (nhom khong co API) - dung 1 lan, kem link bai FB
        self.assertEqual([x for x in self.ntfy if x[0] == "nhom"], [("nhom", DANG, "https://x/fb")])
        # duy nhat 1 ntfy loi: nhac bat nhan AI khi TikTok vao hop thu (khong co co video_made_with_ai)
        self.assertEqual([x[1] for x in self.ntfy if x[0] == "loi"], ["TikTok hộp thư: nhớ bật nhãn AI top5 2026-10-12"])

    def test_che_do_thu_khong_publish(self):
        self.che_do = "thu"
        self.assertEqual(self.chay("chuan-bi"), 0)
        self.assertEqual(self.chay("cong-khai"), 0)
        for k in ("fb", "ig", "youtube"):
            self.assertEqual(self.kenh[k].ck, 0)
            self.assertEqual(self.cong.trang_thai(k, "thu"), "chuan_bi_xong")
        self.assertEqual(self.kenh["tiktok"].hop, 1)   # hop thu TikTok van thu
        self.assertEqual([x for x in self.ntfy if x[0] == "nhom"], [])   # che do thu: khong nhac chia se nhom

    def test_giu_cho_lan_2_khong_dang_lai(self):
        self.chay("chuan-bi")
        self.chay("chuan-bi")
        self.assertTrue(all(self.kenh[k].cb == 1 for k in ("fb", "ig", "youtube")))
        self.chay("cong-khai")
        self.chay("cong-khai")
        self.assertTrue(all(self.kenh[k].ck == 1 for k in ("fb", "ig", "youtube")))
        self.assertEqual(self.kenh["tiktok"].hop, 1)

    def test_khong_ro_khong_dang_lai(self):
        self.kenh["ig"].loi_ck = LoiDang("mat phan hoi", khong_ro=True)
        self.chay("chuan-bi")
        self.assertEqual(self.chay("cong-khai"), 1)
        self.assertEqual(self.cong.trang_thai("ig"), "khong_ro")
        self.assertEqual(self.kenh["fb"].ck, 1)          # kenh khac khong bi chan
        self.kenh["ig"].loi_ck = None
        self.chay("cong-khai")
        self.assertEqual(self.kenh["ig"].ck, 1)          # khong goi lai
        self.assertEqual(self.cong.trang_thai("ig"), "khong_ro")
        self.assertTrue(any("KHONG RO" in x[2] for x in self.ntfy if x[0] == "loi"))

    def test_loi_chuan_bi_la_that_bai_va_cho_thu_lai(self):
        self.kenh["ig"].loi_cb = LoiDang("hong")   # 12/10: Threads het nam trong KENH -> doi sang ig
        self.assertEqual(self.chay("chuan-bi"), 1)
        self.assertEqual(self.cong.trang_thai("ig"), "that_bai")
        self.assertEqual(self.cong.trang_thai("fb"), "chuan_bi_xong")
        self.kenh["ig"].loi_cb = None
        self.chay("chuan-bi")
        self.assertEqual(self.cong.trang_thai("ig"), "chuan_bi_xong")
        self.assertEqual(self.kenh["fb"].cb, 1)

    def test_cong_khai_khi_chua_chuan_bi_thi_bao_loi_khong_dang(self):
        self.assertEqual(self.chay("cong-khai"), 1)
        self.assertEqual(self.kenh["fb"].ck, 0)

    def test_dich_null_dung_kenh(self):
        self.viet_dich({**g.DICH_DU, "ig": {"ig_user_id": None}})
        self.assertEqual(self.chay("chuan-bi"), 1)
        self.assertEqual(self.kenh["ig"].cb, 0)
        self.assertNotIn((NGAY, DANG, "ig", "that"), self.cong.dong)
        self.assertEqual(self.cong.trang_thai("fb"), "chuan_bi_xong")
        self.assertTrue(any(x[0] == "loi" and "dich.json" in x[2] for x in self.ntfy))

    def test_dich_lech_danh_tinh_dung_kenh(self):
        self.kenh["fb"].dt = "PAGE_KHAC"
        self.assertEqual(self.chay("chuan-bi"), 1)
        self.assertEqual(self.kenh["fb"].cb, 0)
        self.assertTrue(any("lech dich.json" in x[2] for x in self.ntfy))

    def test_dich_lech_luc_cong_khai_khong_publish(self):
        self.chay("chuan-bi")
        self.kenh["fb"].dt = "PAGE_KHAC"
        self.chay("cong-khai")
        self.assertEqual(self.kenh["fb"].ck, 0)
        self.assertEqual(self.cong.trang_thai("fb"), "chuan_bi_xong")

    def test_manifest_sai_sha_bo_khung_khong_goi_kenh(self):
        def hong(ngay, dang, thu_muc, ban_can, repo=None, che_do=None):
            m = g.tao_manifest(thu_muc, self.che_do, ngay, dang)
            (pathlib.Path(thu_muc) / "video-reels.mp4").write_bytes(b"bi sua")
            return m
        with mock.patch.object(chay.manifest, "tai_release", hong):
            self.assertEqual(self.chay("chuan-bi"), 3)
        self.assertTrue(all(self.kenh[k].cb == 0 for k in self.kenh))
        self.assertEqual({r["trang_thai"] for r in self.cong.dong.values()}, {"bo"})
        self.assertTrue(any("sha256" in x[2] for x in self.ntfy if x[0] == "loi"))

    def test_manifest_kiem_khong_dat_thi_bo_khung(self):
        self.man_kw = {"dat": False}
        self.assertEqual(self.chay("chuan-bi"), 3)
        self.assertEqual(self.kenh["fb"].cb, 0)

    def test_gia_lech_bo_khung(self):
        with mock.patch.object(chay.gia, "kiem_lai", lambda m, gio: (["X: gia doi 100 -> 150"], [])):
            self.assertEqual(self.chay("chuan-bi"), 3)
        self.assertEqual(self.cong.trang_thai("ig"), "bo")
        self.assertTrue(all(self.kenh[k].cb == 0 for k in self.kenh))

    def test_url_cong_khai_hong_chi_ig_dung(self):
        def hong(url, kieu="video/mp4", **k):
            raise LoiDang("404")
        with mock.patch.object(chay.site, "kiem_url", hong):
            self.assertEqual(self.chay("chuan-bi"), 1)
        self.assertEqual(self.kenh["ig"].cb, 0)   # 12/10: chi con IG can URL cong khai
        self.assertEqual(self.cong.trang_thai("fb"), "chuan_bi_xong")
        self.assertEqual(self.cong.trang_thai("youtube"), "chuan_bi_xong")


class TestKiemGioVaGiaHan(Khung):
    def test_kiem_gio_chua_toi_han_thi_im(self):
        with mock.patch.object(chung, "bay_gio", lambda: g.GIO_DANG + dt.timedelta(minutes=5)):
            self.assertEqual(self.chay("kiem-gio"), 0)
        self.assertEqual(self.ntfy, [])

    def test_kiem_gio_bao_kenh_thieu(self):
        self.chay("chuan-bi")
        self.chay("cong-khai")
        self.cong.dong[(NGAY, DANG, "youtube", "that")]["trang_thai"] = "that_bai"
        self.cong.dong[(NGAY, DANG, "youtube", "that")]["loi"] = "container het han"
        del self.cong.dong[(NGAY, DANG, "ig", "that")]
        with mock.patch.object(chung, "bay_gio", lambda: g.GIO_DANG + dt.timedelta(minutes=16)):
            self.assertEqual(self.chay("kiem-gio"), 1)
        n = [x for x in self.ntfy if x[0] == "loi"][-1][2]
        self.assertIn("YouTube", n)
        self.assertIn("container het han", n)
        self.assertIn("Instagram", n)
        self.assertNotIn("Facebook", n)

    def test_kiem_gio_du_thi_im(self):
        self.chay("chuan-bi")
        self.chay("cong-khai")
        self.ntfy.clear()
        with mock.patch.object(chung, "bay_gio", lambda: g.GIO_DANG + dt.timedelta(minutes=16)):
            self.assertEqual(self.chay("kiem-gio"), 0)
        self.assertEqual(self.ntfy, [])

    def test_gia_han_threads_chi_khi_du_24h_va_con_duoi_30_ngay(self):
        bay = dt.datetime(2026, 10, 12, tzinfo=dt.timezone.utc)
        tk = dict(g.TOKEN_GIA["threads"], cap_luc=int((bay - dt.timedelta(days=40)).timestamp()))
        self.cong.token["threads"] = {"du_lieu": tk, "het_han": chung.iso(bay + dt.timedelta(days=20)), "cap_nhat": "x"}
        for k in ("tiktok", "youtube"):
            del self.cong.token[k]
        m = Mang().them("GET", "refresh_access_token", P(body={"access_token": "THNEWTOKEN1234567", "expires_in": 5184000}))
        with mock.patch("dang.http.gui", m), mock.patch.object(chung, "bay_gio", lambda: bay):
            self.assertEqual(chay.main(["--pha", "gia-han"], cong=self.cong), 0)
        self.assertEqual(self.cong.token["threads"]["du_lieu"]["token"], "THNEWTOKEN1234567")
        # lan 2: vua lam moi (< 24 h) -> khong goi lai
        m2 = Mang()
        with mock.patch("dang.http.gui", m2), mock.patch.object(chung, "bay_gio", lambda: bay + dt.timedelta(hours=1)):
            chay.main(["--pha", "gia-han"], cong=self.cong)
        self.assertEqual(m2.goi, [])

    def test_gia_han_tiktok_luu_refresh_moi_va_loi_thi_ntfy(self):
        for k in ("threads", "youtube"):
            del self.cong.token[k]
        m = Mang().them("POST", "oauth/token", P(body={"access_token": "TTNEW123456789", "refresh_token": "TTNEWRF123456789",  # gitleaks:allow (token gia cho test)
                                                      "expires_in": 86400, "refresh_expires_in": 31536000}))
        with mock.patch("dang.http.gui", m):
            self.assertEqual(chay.main(["--pha", "gia-han"], cong=self.cong), 0)
        self.assertEqual(self.cong.token["tiktok"]["du_lieu"]["refresh_token"], "TTNEWRF123456789")
        m = Mang().them("POST", "oauth/token", P(400, {"error": "invalid_grant"}))
        with mock.patch("dang.http.gui", m):
            self.assertEqual(chay.main(["--pha", "gia-han"], cong=self.cong), 1)
        self.assertTrue(any(x[0] == "loi" and "TikTok" in x[1] for x in self.ntfy))


class TestSoVaManifest(unittest.TestCase):
    def test_cong_header_khoa_va_khong_lo_khoa(self):
        m = Mang().them("POST", "sg-cong", P(body={"ok": True, "giu_duoc": True}))
        with mock.patch("dang.http.gui", m):
            c = so.Cong(khoa="KHOA_CONG_BI_MAT_123")
            self.assertTrue(c.giu_dang(NGAY, DANG, "fb", "that", "t", "sha"))
        _, _, kw = m.goi[0]
        self.assertEqual(kw["headers"]["x-sg-khoa"], "KHOA_CONG_BI_MAT_123")
        self.assertEqual(kw["json_body"]["viec"], "giu_dang")
        m = Mang().them("POST", "sg-cong", P(401, {"loi": "sai khoa KHOA_CONG_BI_MAT_123"}))
        with mock.patch("dang.http.gui", m):
            with self.assertRaises(so.LoiCong) as e:
                c.doc_token("fb")
        self.assertNotIn("KHOA_CONG_BI_MAT_123", str(e.exception))

    def test_giu_dang_khong_thu_lai_khi_mat_phan_hoi(self):
        from dang import http
        m = Mang().them("POST", "sg-cong", http.LoiMang("timeout"))
        with mock.patch("dang.http.gui", m), vo_ngu():
            with self.assertRaises(so.LoiCong):
                so.Cong(khoa="KHOA_CONG_BI_MAT_123").giu_dang(NGAY, DANG, "fb", "that")
        self.assertEqual(len(m.goi), 1)

    def test_thieu_khoa(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(so.LoiCong):
                so.Cong()

    def _man(self, **kw):
        d = tempfile.mkdtemp()
        return d, g.tao_manifest(d, **kw)

    def test_manifest_dung(self):
        d, m = self._man()
        self.assertIs(manifest.kiem(m, d, NGAY, DANG, "that"), m)

    def test_manifest_sai(self):
        d, m = self._man()
        for sai, kw in [("ngay", (("2026-10-13", DANG, "that"))), ("dang", ((NGAY, "tin-nhanh", "that"))), ("che_do", ((NGAY, DANG, "thu")))]:
            with self.assertRaises(manifest.LoiManifest, msg=sai):
                manifest.kiem(m, d, *kw)
        d, m = self._man(dat=False)
        with self.assertRaises(manifest.LoiManifest):
            manifest.kiem(m, d, NGAY, DANG, "that")
        d, m = self._man()
        (pathlib.Path(d) / "video-shorts.mp4").write_bytes(b"khac")
        with self.assertRaises(manifest.LoiManifest) as e:
            manifest.kiem(m, d, NGAY, DANG, "that")
        self.assertIn("sha256", str(e.exception))
        d, m = self._man()
        (pathlib.Path(d) / "bia-tiktok.jpg").unlink()
        with self.assertRaises(manifest.LoiManifest):
            manifest.kiem(m, d, NGAY, DANG, "that")

    def test_tai_release_tai_san_la_bi_chan_va_tai_dung(self):
        nguon, man = self._man()
        files = {f.name: f.read_bytes() for f in pathlib.Path(nguon).iterdir()}
        ds = lambda ten: P(body={"assets": [{"name": n} for n in ten]})
        m = Mang().them("GET", "api.github.com", ds(list(files) + ["giong-tho.mp3"]))
        with mock.patch("dang.http.gui", m):
            with self.assertRaises(manifest.LoiManifest):
                manifest.tai_release(NGAY, DANG, tempfile.mkdtemp(), ("reels",), "o/r")
        m = Mang().them("GET", "api.github.com", ds(list(files)))
        m.them("GET", "github.com/o/r/releases/download", lambda me, u, k: P(raw=files[u.rsplit("/", 1)[1]]))
        dich = tempfile.mkdtemp()
        with mock.patch("dang.http.gui", m):
            got = manifest.tai_release(NGAY, DANG, dich, ("reels",), "o/r")
        manifest.kiem(got, dich, NGAY, DANG, "that", ("reels",))
        self.assertFalse((pathlib.Path(dich) / "video-shorts.mp4").exists())


class TestGiaVaSite(unittest.TestCase):
    def test_het_han_va_lech_gia(self):
        muc = [{"ten": "A", "pid": "UP1001-X_00", "loc": "en-hk", "gia_cuc_bo": 100.0, "endTime": "1"}]
        gio = g.GIO_DANG
        html = lambda end, gia_: g.trang_ps("UP1001-X_00", f"HK$ {gia_}", end)
        con = str(int((gio.timestamp() + 5 * 3600) * 1000))
        het = str(int((gio.timestamp() + 3600) * 1000))
        for end, gia_, mong in [(con, "101.00", 0), (het, "100.00", 1), (con, "130.00", 1), (con, "1,001.00", 1)]:
            m = Mang().them("GET", "store.playstation.com/en-hk/product/UP1001-X_00", P(raw=html(end, gia_)))
            with mock.patch("dang.http.gui", m):
                van_de, _ = gia.kiem_lai([{**muc[0], "endTime": end}], gio)   # han video = han trang (chi thu het han/gia)
            self.assertEqual(len(van_de), mong, (end, gia_, van_de))

    def test_loc_pid_la_bi_chan_khong_cao(self):
        m = Mang()
        with mock.patch("dang.http.gui", m):
            van_de, _ = gia.kiem_lai([{"ten": "A", "pid": "../x", "loc": "en-hk"}], g.GIO_DANG)
        self.assertEqual((len(van_de), m.goi), (1, []))

    def test_kiem_url(self):
        m = Mang().them("HEAD", "a.mp4", P(headers={"Content-Type": "video/mp4"}))
        with mock.patch("dang.http.gui", m):
            self.assertTrue(site.kiem_url("https://h/a.mp4"))
        m = Mang().them("HEAD", "a.mp4", P(302, {}, {"Location": "https://khac"}))
        with mock.patch("dang.http.gui", m), vo_ngu():
            with self.assertRaises(LoiDang):
                site.kiem_url("https://h/a.mp4", lan=2)

    def test_dung_site_ten_bat_bien_va_tran_dung_luong(self):
        # 3 release: dich + 2 cu; tran chi du cho dich
        nguon = {}
        for ngay, dang in [("2026-10-12", "top5"), ("2026-10-11", "top5"), ("2026-10-10", "top5")]:
            d = tempfile.mkdtemp()
            nguon[(ngay, dang)] = (g.tao_manifest(d, "that", ngay, dang), d)
        rels = P(body=[{"tag_name": f"v-{n}-{d}"} for (n, d) in nguon])
        cur = {}

        def api(me, u, k):
            tag = u.rsplit("/", 1)[1]
            key = (tag[2:12], tag[13:])
            cur["k"] = key
            d = nguon[key][1]
            return P(body={"assets": [{"name": f.name} for f in pathlib.Path(d).iterdir()]})

        def tai(me, u, k):
            tag, ten = u.split("/download/")[1].split("/")
            return P(raw=(pathlib.Path(nguon[(tag[2:12], tag[13:])][1]) / ten).read_bytes())
        m = Mang().them("GET", "/download/", tai).them("GET", "/releases/tags/", api).them("GET", "/releases", rels)
        ra = tempfile.mkdtemp()
        with mock.patch("dang.http.gui", m):
            sha8 = site.dung(ra, "2026-10-12", "top5", "o/r", toi_da_mb=0.0001)
        ds = sorted(p.name for p in (pathlib.Path(ra) / "v").iterdir())
        self.assertEqual(ds, [f"2026-10-12-top5-{sha8}.jpg", f"2026-10-12-top5-{sha8}.mp4"])


class TestKhongLoToken(Khung):
    """Chay luong that voi module that + mang gia: khong chuoi bi mat nao xuat hien o stdout/stderr/ntfy."""

    BI_MAT = ["KHOA_CONG_BI_MAT_123", "EAAFBTOKENGIA1234567890abcdef", "EAAIGTOKENGIA1234567890abcdef",
              "THTOKENGIA1234567890abcdef", "YTSECRETGIA123456", "YTREFRESHGIA123456", "TTSECRETGIA123456",  # gitleaks:allow (token gia cho test)
              "TTACCESSGIA123456", "TTREFRESHGIA123456", "ya29.GIA_ACCESS_123456", "NTFYTOPICBIMAT1"]

    def mang(self):
        m = Mang()
        # ntfy
        m.them("POST", "ntfy.sh", P(body={}))
        # FB
        m.them("GET", "graph.facebook.com/v26.0/me", P(body={"id": "PAGE1"}))
        m.them("POST", "/PAGE1/video_reels", lambda me, u, k: P(body={"video_id": "V1"}) if k["form"]["upload_phase"] == "start"
               else P(body={"success": True}))
        m.them("POST", "rupload", P(body={"success": True}))
        m.them("GET", "graph.facebook.com/v26.0/V1", P(body={"status": {"uploading_phase": {"status": "complete"}}}))
        m.them("POST", "/V1/thumbnails", P(body={"success": True}))
        # IG: container tra loi loi co nhac lai token (kiem tra che)
        m.them("GET", "graph.facebook.com/v26.0/IGU1", P(body={"id": "IGU1"}))
        m.them("POST", "/IGU1/media", P(body={"id": "C1"}))
        m.them("GET", "graph.facebook.com/v26.0/C1", P(400, {"error": {"message": "Invalid OAuth access token EAAIGTOKENGIA1234567890abcdef access_token=EAAIGTOKENGIA1234567890abcdef", "code": 190}}))
        # Threads
        m.them("GET", "graph.threads.net/v1.0/me", P(body={"id": "THU1"}))
        m.them("POST", "/THU1/threads_publish", P(body={"id": "T9"}))
        m.them("POST", "/THU1/threads", P(body={"id": "TC1"}))
        m.them("GET", "graph.threads.net/v1.0/TC1", P(body={"status": "FINISHED"}))
        m.them("GET", "graph.threads.net/v1.0/T9", P(body={"permalink": "https://threads.net/t/T9"}))
        # YouTube
        m.them("POST", "oauth2.googleapis.com", P(body={"access_token": "ya29.GIA_ACCESS_123456"}))
        m.them("GET", "youtube/v3/channels", P(body={"items": [{"id": "UCYT1"}]}))
        m.them("POST", "upload/youtube", P(headers={"Location": "https://up.example/s?upload_id=BIMATUPLOAD123"}))
        m.them("PUT", "up.example", P(200, {"id": "YV1"}))
        m.them("GET", "youtube/v3/videos", P(body={"items": [{"status": {"privacyStatus": "public"}}]}))
        # TikTok
        m.them("GET", "open.tiktokapis.com/v2/user/info", P(body={"data": {"user": {"open_id": "TTO1"}}}))
        m.them("POST", "inbox/video/init", P(body={"data": {"publish_id": "P1", "upload_url": "https://up.tt/u"}, "error": {"code": "ok"}}))
        m.them("PUT", "up.tt", P(201, {}))
        m.them("POST", "status/fetch", P(body={"data": {"status": "SEND_TO_USER_INBOX"}}))
        return m

    def test_khong_lo(self):
        # dung module that, KHONG patch MOD
        for p in self.ps2, :
            p.stop()
        patch_mod = mock.patch.dict(chay.MOD, {"fb": chay.fb, "ig": chay.ig, "threads": chay.threads, "youtube": chay.yt, "tiktok": chay.tiktok})
        patch_mod.start()
        self.addCleanup(patch_mod.stop)
        for p in (self.ps[4], self.ps[5]):  # dung ntfy that (qua mang gia)
            p.stop()
        chay.yt._cache.clear()
        m = self.mang()
        out, err = io.StringIO(), io.StringIO()
        env = {"NTFY_TIN": "NTFYTOPICBIMAT1", "NTFY_BAO_LOI": "NTFYTOPICBIMAT1"}
        cong = self.cong
        with mock.patch.dict(os.environ, env), mock.patch("dang.http.gui", m), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            so.Cong(khoa="KHOA_CONG_BI_MAT_123")  # dang ky khoa de che
            ma1 = chay.main(["--pha", "chuan-bi", "--dang", DANG, "--ngay", NGAY, "--che-do", "that"], cong=cong)
            ma2 = chay.main(["--pha", "cong-khai", "--dang", DANG, "--ngay", NGAY, "--che-do", "that"], cong=cong)
        self.assertEqual(ma1, 1)   # IG loi o chuan bi (cho co chu dich)
        tat_ca = out.getvalue() + err.getvalue() + json.dumps([kw.get("json_body") for _, _, kw in m.goi if kw.get("json_body")])
        # json_body gui di ntfy phai sach; json_body gui toi cong/nen tang (Authorization header) khong nam trong chuoi nay
        ntfy_bodies = json.dumps([kw["json_body"] for me, u, kw in m.goi if "ntfy.sh" in u])
        for b in self.BI_MAT:
            self.assertNotIn(b, out.getvalue(), f"lo {b} o stdout")
            self.assertNotIn(b, err.getvalue(), f"lo {b} o stderr")
            if b != "NTFYTOPICBIMAT1":   # topic buoc phai co trong body gui di; chi can khong ra log
                self.assertNotIn(b, ntfy_bodies, f"lo {b} o ntfy")
        self.assertGreater(m.dem("POST", "ntfy.sh"), 0)
        self.assertEqual(self.cong.trang_thai("ig"), "that_bai")
        self.assertEqual(self.cong.trang_thai("fb"), "da_dang")
        self.assertEqual(self.cong.trang_thai("tiktok"), "da_dang")


if __name__ == "__main__":
    unittest.main()


class TestChiMotKenh(Khung):
    """24/10/2026: SG_KENH_BAT=youtube -> may chi dang YouTube (Top 5 i chang ban thang), kenh khac khong dung toi."""

    def test_chi_youtube(self):
        with mock.patch.dict(os.environ, {"SG_KENH_BAT": "youtube"}):
            self.assertEqual(self.chay("chuan-bi"), 0)
            self.assertEqual(self.chay("cong-khai"), 0)
            self.ntfy.clear()
            with mock.patch.object(chung, "bay_gio", lambda: g.GIO_DANG + dt.timedelta(minutes=16)):
                self.assertEqual(self.chay("kiem-gio"), 0)
        self.assertEqual(self.cong.trang_thai("youtube"), "da_dang")
        self.assertEqual(self.kenh["youtube"].ck, 1)
        for k in ("fb", "ig", "tiktok"):
            self.assertEqual(self.kenh[k].cb + self.kenh[k].ck + self.kenh[k].hop, 0, k)
        self.assertEqual(self.ntfy, [])

    def test_rong_la_moi_kenh_tru_x(self):
        # 27/10 (SG-X-A): X thoi nhan video may, ke ca khi bien rong hoac ghi ro "x"
        with mock.patch.dict(os.environ, {"SG_KENH_BAT": ""}):
            self.assertEqual(chay.kenh_bat(), [k for k in chay.KENH if k != "x"])
        with mock.patch.dict(os.environ, {"SG_KENH_BAT": " youtube , fb "}):
            self.assertEqual(chay.kenh_bat(), ["fb", "youtube"])
        with mock.patch.dict(os.environ, {"SG_KENH_BAT": "fb,ig,x"}):
            self.assertEqual(chay.kenh_bat(), ["fb", "ig"])


class TestKenhFlagship(Khung):
    """28/10/2026 (cong 10): flagship 3 ngay dau chi TikTok (SG_FLAGSHIP_NGAY_1 + 0..2), tu ngay thu 4 them YouTube; luon giao voi SG_KENH_BAT;
    khuon khac (top5...) KHONG doi hanh vi."""
    NGAY_FS = "2026-10-30"

    def setUp(self):
        super().setUp()
        p = mock.patch.object(chung, "bay_gio", lambda: dt.datetime(2026, 10, 30, 12, 0, tzinfo=chung.VN))   # = gio_dang trong manifest gia (T12:00)
        p.start()
        self.addCleanup(p.stop)

    def chay_fs(self, pha, dang="flagship"):
        return chay.main(["--pha", pha, "--dang", dang, "--ngay", self.NGAY_FS, "--che-do", "that"], cong=self.cong)

    def dem(self, *ks):
        return {k: (self.kenh[k].cb, self.kenh[k].ck, self.kenh[k].hop) for k in ks}

    def trong_env(self, **kw):
        return mock.patch.dict(os.environ, kw)

    # ---- ham thuan ----
    def test_kenh_flagship_ba_nhanh(self):
        f = chay.kenh_flagship
        self.assertEqual(f(self.NGAY_FS, ""), ("tiktok",))            # khong dat bien
        self.assertEqual(f(self.NGAY_FS, "28/10/2026"), ("tiktok",))  # sai dinh dang
        self.assertEqual(f(self.NGAY_FS, "2026-13-45"), ("tiktok",))  # dung dang chuoi nhung khong phai ngay
        self.assertEqual(f("2026-10-28", "2026-10-28"), ("tiktok",))  # ngay 1
        self.assertEqual(f("2026-10-30", "2026-10-28"), ("tiktok",))  # ngay 3
        self.assertEqual(f("2026-10-31", "2026-10-28"), ("tiktok", "youtube"))   # ngay 4
        self.assertEqual(f("2026-11-15", "2026-10-28"), ("tiktok", "youtube"))
        self.assertEqual(f("2026-10-27", "2026-10-28"), ("tiktok",))  # truoc ngay 1 van chi tiktok
        with self.trong_env(SG_FLAGSHIP_NGAY_1="2026-10-28"):
            self.assertEqual(f("2026-10-31"), ("tiktok", "youtube"))  # doc tu env

    def test_kenh_bat_flagship_giao_voi_sg_kenh_bat(self):
        with self.trong_env(SG_KENH_BAT="", SG_FLAGSHIP_NGAY_1="2026-10-28"):
            self.assertEqual(chay.kenh_bat(dang="flagship", ngay="2026-10-30"), ["tiktok"])
            self.assertEqual(chay.kenh_bat(dang="flagship", ngay="2026-10-31"), ["youtube", "tiktok"])
        with self.trong_env(SG_KENH_BAT="youtube", SG_FLAGSHIP_NGAY_1="2026-10-28"):
            self.assertEqual(chay.kenh_bat(dang="flagship", ngay="2026-10-30"), [])        # 3 ngay dau: youtube bi chan
            self.assertEqual(chay.kenh_bat(dang="flagship", ngay="2026-10-31"), ["youtube"])
        with self.trong_env(SG_KENH_BAT="fb,ig,x,tiktok", SG_FLAGSHIP_NGAY_1="2026-10-28"):
            self.assertEqual(chay.kenh_bat(dang="flagship", ngay="2026-10-31"), ["tiktok"])  # fb/ig khong bao gio; x luon bo

    def test_khuon_khac_khong_doi(self):
        tat_ca = [k for k in chay.KENH if k != "x"]
        for env in ({"SG_FLAGSHIP_NGAY_1": ""}, {"SG_FLAGSHIP_NGAY_1": "2026-10-28"}):
            with self.trong_env(SG_KENH_BAT="", **env):
                for d in ("top5", "tin-nhanh", "keo-thom", "keo-thom-2", "keo-thom-3"):
                    for ngay in ("2026-10-28", "2026-10-31"):
                        self.assertEqual(chay.kenh_bat(dang=d, ngay=ngay), tat_ca, (d, ngay))
                self.assertEqual(chay.kenh_bat(), tat_ca)
            with self.trong_env(SG_KENH_BAT="youtube", **env):
                self.assertEqual(chay.kenh_bat(dang="top5", ngay="2026-10-28"), ["youtube"])

    def test_gio_flagship(self):
        self.assertEqual(chay.GIO["flagship"], "15:30")
        self.assertEqual(chay.gio_dang_mac_dinh("2026-10-30", "flagship"), dt.datetime(2026, 10, 30, 15, 30, tzinfo=chung.VN))

    # ---- qua cac pha (fake cong) ----
    def test_ngay_1_den_3_chi_tiktok_chuan_bi_cong_khai_kiem_gio(self):
        for ngay_1 in ("", "2026-10-30", "2026-10-28", "rac"):   # khong bien / ngay 1 / ngay 3 / sai dinh dang
            self.setUp()
            with self.trong_env(SG_KENH_BAT="", SG_FLAGSHIP_NGAY_1=ngay_1):
                self.assertEqual(self.chay_fs("chuan-bi"), 0, ngay_1)
                self.assertEqual(self.dem("fb", "ig", "youtube"), {k: (0, 0, 0) for k in ("fb", "ig", "youtube")}, ngay_1)
                self.assertEqual(self.chay_fs("cong-khai"), 0, ngay_1)
                self.assertEqual(self.dem("fb", "ig", "youtube"), {k: (0, 0, 0) for k in ("fb", "ig", "youtube")}, ngay_1)
                self.assertEqual(self.kenh["tiktok"].hop, 1, ngay_1)
                self.assertEqual(set(k[2] for k in self.cong.dong if k[1] == "flagship"), {"tiktok"}, ngay_1)
                with mock.patch.object(chung, "bay_gio", lambda: dt.datetime(2026, 10, 30, 15, 50, tzinfo=chung.VN)):
                    self.assertEqual(self.chay_fs("kiem-gio"), 0, ngay_1)
                self.assertEqual([x for x in self.ntfy if x[0] == "loi" and "Qua gio" in x[1]], [], ngay_1)

    def test_tu_ngay_thu_4_them_youtube(self):
        with self.trong_env(SG_KENH_BAT="", SG_FLAGSHIP_NGAY_1="2026-10-27"):   # 30/10 = ngay thu 4
            self.assertEqual(self.chay_fs("chuan-bi"), 0)
            self.assertEqual(self.kenh["youtube"].cb, 1)
            self.assertEqual((self.kenh["fb"].cb, self.kenh["ig"].cb), (0, 0))
            self.assertEqual(self.chay_fs("cong-khai"), 0)
            self.assertEqual(self.kenh["youtube"].ck, 1)
            self.assertEqual(self.kenh["tiktok"].hop, 1)
            self.assertEqual((self.kenh["fb"].ck, self.kenh["ig"].ck), (0, 0))
            self.assertEqual(self.cong.dong[(self.NGAY_FS, "flagship", "youtube", "that")]["trang_thai"], "da_dang")
            with mock.patch.object(chung, "bay_gio", lambda: dt.datetime(2026, 10, 30, 15, 50, tzinfo=chung.VN)):
                self.assertEqual(self.chay_fs("kiem-gio"), 0)

    def test_sg_kenh_bat_chan_youtube_ke_ca_ngay_thu_4(self):
        with self.trong_env(SG_KENH_BAT="tiktok", SG_FLAGSHIP_NGAY_1="2026-10-20"):
            self.assertEqual(self.chay_fs("chuan-bi"), 0)
            self.assertEqual(self.chay_fs("cong-khai"), 0)
        self.assertEqual((self.kenh["youtube"].cb, self.kenh["youtube"].ck), (0, 0))
        self.assertEqual(self.kenh["tiktok"].hop, 1)

    def test_kiem_gio_flagship_bao_thieu_tiktok_nhung_khong_doi_youtube_3_ngay_dau(self):
        with self.trong_env(SG_KENH_BAT="", SG_FLAGSHIP_NGAY_1="2026-10-30"):
            with mock.patch.object(chung, "bay_gio", lambda: dt.datetime(2026, 10, 30, 15, 50, tzinfo=chung.VN)):
                self.assertEqual(self.chay_fs("kiem-gio"), 1)   # chua chay gi -> thieu dong TikTok
        loi = [x for x in self.ntfy if x[0] == "loi"]
        self.assertEqual(len(loi), 1)
        self.assertIn("TikTok", loi[0][2])
        self.assertNotIn("YouTube", loi[0][2])

    def test_top5_van_du_kenh_du_da_dat_bien_flagship(self):
        with self.trong_env(SG_KENH_BAT="", SG_FLAGSHIP_NGAY_1="2026-10-29"), mock.patch.object(chung, "bay_gio", lambda: g.GIO_DANG):
            self.assertEqual(self.chay("chuan-bi"), 0)    # top5 NGAY 12/10 cua Khung
            self.assertEqual(self.chay("cong-khai"), 0)
        for k in ("fb", "ig", "youtube"):
            self.assertEqual((self.kenh[k].cb, self.kenh[k].ck), (1, 1), k)
