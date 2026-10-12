"""Threads bai chu (dang/threads_chu.py): mock mang, khong goi Threads that, khong ngu that, khong gui ntfy.
Fixture = loi_dang + kiem_lai THAT cua manifest Release 12/10/2026 (tin-nhanh 07:30 va keo-thom-2 15:00), chep cung (kiem_lai tin-nhanh rut con 5/18 muc)."""
import contextlib
import datetime as dt
import io
import json
import pathlib
import unittest
from unittest import mock

from dang import chay, chung, gia, http, manifest, ntfy, site, threads, threads_chu as tc
from dang.chung import LoiDang
from dang.tests import gia_lap as g
from dang.tests.gia_lap import Mang, P, cong_day_du

NGAY = "2026-10-12"
BAY_GIO = dt.datetime(2026, 10, 12, 9, 30, tzinfo=chung.VN)
CHIEU = dt.datetime(2026, 10, 12, 17, 0, tzinfo=chung.VN)
LINK = "https://www.threads.com/@sangamecomvn/post/ABC"

SANG_LOI_DANG = {
 "tieu_de": "Tin nhanh PlayStation 12/10: 8 game bán chạy giảm 50–80% | 10 game bán chạy đang giảm 30–70%",
 "mo_ta": "Bản tin sáng Săn Game, Thứ Hai 12/10:\n1. GIẢM SÂU: 8 game bán chạy giảm 50–80%.\n2. DEAL HOT: 10 game bán chạy đang giảm 30–70%.\n3. ĐỢT SALE: Player's Choice.\nGiảm sâu: rẻ nhất Mafia III, 160.000đ ở Store Hồng Kông (giảm 80%).\nDeal hot: rẻ nhất It Takes Two, 335.000đ ở Store Hồng Kông (giảm 70%).\nTra giá mọi game ở 6 vùng PS Store: https://sangame.com.vn/",
 "hashtag": [
  "#SănGame",
  "#PlayStation",
  "#PS5"
 ],
 "link": "https://sangame.com.vn/"
}
SANG_KIEM_LAI = [
 {
  "ten": "Borderlands 4 Super Deluxe Edition",
  "pid": "UP1001-PPSA01494_00-SUPERDELUXEED000",
  "loc": "en-hk",
  "gia_vnd": 1799000,
  "gia_cuc_bo": 514.0,
  "tien_te": "HKD",
  "endTime": "1792594740000"
 },
 {
  "ten": "Mafia III: Definitive Edition for PS5®",
  "pid": "UP1001-PPSA36864_00-MAFIA3DEPS500000",
  "loc": "en-hk",
  "gia_vnd": 160000,
  "gia_cuc_bo": 45.8,
  "tien_te": "HKD",
  "endTime": "1792594740000"
 },
 {
  "ten": "DEATH STRANDING 2: ON THE BEACH Digital Deluxe Edition",
  "pid": "JP9000-PPSA02015_00-DS2OTBDDE0000001",
  "loc": "en-us",
  "gia_vnd": 1120000,
  "gia_cuc_bo": 39.99,
  "tien_te": "USD",
  "endTime": "1792652340000"
 },
 {
  "ten": "Overcooked! All You Can Eat",
  "pid": "EP4064-PPSA01528_00-0538983162460184",
  "loc": "en-hk",
  "gia_vnd": 323000,
  "gia_cuc_bo": 92.4,
  "tien_te": "HKD",
  "endTime": "1792594740000"
 },
 {
  "ten": "It Takes Two PS4™ & PS5™",
  "pid": "UP0006-PPSA02342_00-ITTAKESTWORETAIL",
  "loc": "en-hk",
  "gia_vnd": 335000,
  "gia_cuc_bo": 95.7,
  "tien_te": "HKD",
  "endTime": "1792594740000"
 }
]
CHIEU_LOI_DANG = {
 "tieu_de": "Indiana Jones and the Great Circle giảm 40% ở PS Store Hồng Kông: còn 1.048.000đ",
 "mo_ta": "Indiana Jones and the Great Circle đang giảm 40% ở PS Store Hồng Kông: còn 1.048.000đ (giá gốc 1.747.000đ) khi quy theo giá thẻ PSN. So với Mỹ: +128.000đ; Singapore: +271.000đ. Hết giảm 21:59 ngày 21/10 giờ Việt Nam. Giá quy đổi chỉ để tham khảo.\n\nXem giá ở 6 vùng PS Store: https://sangame.com.vn/game-indiana-jones-and-the-great-circle.html",
 "hashtag": [
  "#SănGame",
  "#PlayStation",
  "#PS5",
  "#GiảmGiá"
 ],
 "link": "https://sangame.com.vn/"
}
CHIEU_KIEM_LAI = [
 {
  "ten": "Indiana Jones and the Great Circle",
  "pid": "UP1003-PPSA26786_00-INDIANAJONESATGC",
  "loc": "en-hk",
  "gia_vnd": 1048000,
  "gia_cuc_bo": 299.4,
  "tien_te": "HKD",
  "endTime": "1792594740000"
 },
 {
  "ten": "Indiana Jones and the Great Circle",
  "pid": "UP1003-PPSA26786_00-INDIANAJONESATGC",
  "loc": "en-us",
  "gia_vnd": 1176000,
  "gia_cuc_bo": 41.99,
  "tien_te": "USD",
  "endTime": "1792652340000"
 },
 {
  "ten": "Indiana Jones and the Great Circle",
  "pid": "UP1003-PPSA26786_00-INDIANAJONESATGC",
  "loc": "en-sg",
  "gia_vnd": 1319000,
  "gia_cuc_bo": 59.94,
  "tien_te": "SGD",
  "endTime": "1792594740000"
 }
]


def man_cua(dang, loi_dang, kiem_lai):
    ban = {b: {"video": f"video-{b}.mp4", "sha256": "a6c8f942" + "0" * 56, "bia": f"bia-{b}.jpg", "bia_sha256": "b" * 64,
               "kiem": {"dat": True, "phep": [{"ten": "x", "dat": True}]}} for b in ("tiktok", "reels", "shorts")}
    return {"phien_ban": 1, "ngay_dang": NGAY, "dang": dang, "gio_dang": f"{NGAY}T07:30:00+07:00", "che_do": "that",
            "sha_code": "c", "sha_du_lieu": "d", "tao_luc": "t", "ban": ban, "loi_dang": loi_dang, "kiem_lai": kiem_lai}


def man_sang():
    return man_cua("tin-nhanh", SANG_LOI_DANG, SANG_KIEM_LAI)


def man_chieu():
    return man_cua("keo-thom-2", CHIEU_LOI_DANG, CHIEU_KIEM_LAI)


def mang_threads(publish=None, tao=None):
    m = Mang()
    m.them("POST", "/THU1/threads_publish", publish or P(body={"id": "T9"}))
    m.them("POST", "/THU1/threads", tao or P(body={"id": "TC1"}))
    m.them("GET", "graph.threads.net/v1.0/me", P(body={"id": "THU1"}))
    m.them("GET", "graph.threads.net/v1.0/TC1", P(body={"status": "FINISHED"}))
    m.them("GET", "graph.threads.net/v1.0/T9", P(body={"permalink": LINK}))
    return m


class Chung(unittest.TestCase):
    def setUp(self):
        self.cong = cong_day_du()
        self.ngu, self.ntfy, self.kiem_lai_goi = [], [], []
        self.man = man_sang()
        self.kiem_url = mock.Mock(return_value=True)
        self.thu_muc = pathlib.Path(__import__("tempfile").mkdtemp(prefix="sg-tc-"))
        self.van_de = []
        self.van_de_my = []
        self.bay = BAY_GIO
        self.loi_release = None

        def tai_tep(ngay, dang, ten, thu_muc, repo=None, che_do="that"):
            if self.loi_release:
                raise manifest.LoiManifest(self.loi_release)
            assert che_do == "that" and ten == "manifest.json"
            p = pathlib.Path(thu_muc) / ten
            p.write_text(json.dumps(self.man), "utf-8")
            return p

        def kiem_lai(muc, gio):
            self.kiem_lai_goi.append((list(muc), gio))
            if muc and muc[0].get("loc") == "en-us":
                if self.van_de_my == "no":
                    raise LoiDang("Sony 503")
                return list(self.van_de_my), []
            return list(self.van_de), []

        for p in (mock.patch.object(chung, "bay_gio", lambda: self.bay),
                  mock.patch.object(chung, "ngu", lambda s: self.ngu.append(s)),
                  mock.patch.object(site, "kiem_url", self.kiem_url),
                  mock.patch.object(manifest, "tai_tep", tai_tep),
                  mock.patch.object(gia, "kiem_lai", kiem_lai),
                  mock.patch.object(ntfy, "loi", lambda t, n, **k: self.ntfy.append(("loi", t, n))),
                  mock.patch.object(ntfy, "tin", lambda t, n, **k: self.ntfy.append(("tin", t, n))),
                  mock.patch.dict("os.environ", {"PAGES_URL": "https://x.github.io/sangame-video"})):
            p.start()
            self.addCleanup(p.stop)

    def chay(self, loai, che_do="that", m=None, cong="mac_dinh"):
        a = type("A", (), {"loai": loai, "ngay": NGAY, "che_do": che_do})()
        cong = self.cong if cong == "mac_dinh" else cong
        buf = io.StringIO()
        with mock.patch.object(http, "gui", m or mang_threads()), contextlib.redirect_stdout(buf):
            rc = tc.chay_loai(a, cong, str(self.thu_muc), g.DICH_DU)
        self.in_ra = buf.getvalue()
        return rc


class Van(Chung):
    def test_sang_tu_manifest_that(self):
        s, muc = tc.soan_sang(man_sang(), NGAY)
        print("BAI SANG:", s, len(s))
        for can in ("Mafia III", "160.000đ", "Hồng Kông"):
            self.assertIn(can, s)
        self.assertIn("bản tin giảm giá", s.casefold())
        for cam in ("8 game", "50–80", "nhóm giảm sâu", "%"):
            self.assertNotIn(cam, s)
        self.assertEqual(len(muc), 1)
        self.assertEqual(muc[0]["pid"], "UP1001-PPSA36864_00-MAFIA3DEPS500000")
        self.assertLessEqual(len(s), 500)
        self.assertEqual(s.count("?"), 1)

    def test_chieu_tu_manifest_that(self):
        s, muc = tc.soan_chieu(man_chieu(), NGAY)
        print("BAI CHIEU:", s, len(s))
        for can in ("Indiana Jones and the Great Circle", "1.048.000đ", "Hồng Kông", "128.000đ", "21:59 ngày 21/10"):
            self.assertIn(can, s)
        self.assertNotIn("%", s)
        self.assertNotIn("Singapore", s)
        self.assertEqual([m["loc"] for m in muc], ["en-hk", "en-us"])
        self.assertLessEqual(len(s), 500)
        self.assertIn("?", s)

    def test_chieu_khong_co_my_thi_bo_so_sanh(self):
        m = man_chieu()
        m["kiem_lai"] = [x for x in m["kiem_lai"] if x["loc"] != "en-us"]
        s, muc = tc.soan_chieu(m, NGAY)
        self.assertNotIn("Store Mỹ", s)
        self.assertEqual(len(muc), 1)

    def test_sang_khong_phu_thuoc_mo_ta(self):
        m = man_sang()
        m["loi_dang"] = dict(SANG_LOI_DANG, mo_ta="Khong co muc nao.")
        self.assertEqual(tc.soan_sang(m, NGAY), tc.soan_sang(man_sang(), NGAY))

    def test_chieu_pid_my_khac_van_ra_cau_chenh(self):
        m = man_chieu()
        for x in m["kiem_lai"]:
            if x["loc"] == "en-us":
                x["pid"] = "UP1003-PPSA26786_00-INDIANAJONESUS1"   # pid rieng cua vung Mỹ
                x["ten"] = "Indiana Jones and the Great Circle™"
        s, muc = tc.soan_chieu(m, NGAY)
        self.assertIn("Rẻ hơn Store Mỹ 128.000đ", s)
        self.assertEqual([x["pid"] for x in muc], ["UP1003-PPSA26786_00-INDIANAJONESATGC", "UP1003-PPSA26786_00-INDIANAJONESUS1"])

    def test_chieu_my_khac_ten_khong_ghep(self):
        m = man_chieu()
        for x in m["kiem_lai"]:
            if x["loc"] == "en-us":
                x["ten"] = "Indiana Jones and the Great Circle Deluxe Edition"
        s, muc = tc.soan_chieu(m, NGAY)
        self.assertNotIn("Store Mỹ", s)
        self.assertEqual(len(muc), 1)

    def test_thieu_kiem_lai_khong_soan(self):
        m = man_sang()
        m["kiem_lai"] = []
        with self.assertRaises(LoiDang):
            tc.soan_sang(m, NGAY)

    def test_so_luong_mau_va_doi_ngay_khong_lap(self):
        for pool in (tc.MO_SANG, tc.HOI_SANG, tc.MO_CHIEU, tc.HOI_CHIEU):
            self.assertGreaterEqual(len(pool), 4)
        ngay = dt.date(2026, 10, 1)
        for loai, man in ((tc.soan_sang, man_sang()), (tc.soan_chieu, man_chieu())):
            truoc = None
            for i in range(40):
                s, _ = loai(man, (ngay + dt.timedelta(days=i)).isoformat())
                cau = s.split(". ")[0], s[s.rfind(". ") + 2:]
                if truoc:
                    self.assertNotEqual(cau[0], truoc[0])   # cau mo
                    self.assertNotEqual(cau[1], truoc[1])   # cau hoi
                truoc = cau

    def test_moi_mau_deu_qua_kiem_van(self):
        for i in range(8):
            ngay = (dt.date(2026, 10, 1) + dt.timedelta(days=i)).isoformat()
            tc.soan_sang(man_sang(), ngay)
            tc.soan_chieu(man_chieu(), ngay)

    def test_kiem_van_chan_bait_link_hoa(self):
        for xau in ("Game A rẻ. Bình luận 1 để nhận mã?", "Game A rẻ. Tag bạn bè vào nhé?", "Xem https://sangame.com.vn?",
                    "Game A rẻ. Share bài này nhé?", "Giveaway game A, ai muốn?", "Game A rẻ!!! Mua chưa?", "Game A #PS5, mua chưa?",
                    "CHƠI NGAY HÔM NAY ĐI. Mua chưa?", "Không có câu hỏi.", "a" * 390 + " bạn mua chưa? rồi nữa"):
            with self.assertRaises(LoiDang, msg=xau):
                tc.kiem_van(xau)
        self.assertEqual(tc.kiem_van("Game A rẻ. Bạn mua chưa?"), "Game A rẻ. Bạn mua chưa?")

    def test_gon_ten(self):
        self.assertEqual(tc.gon_ten("Mafia III: Definitive Edition for PS5®"), "Mafia III: Definitive Edition")
        self.assertEqual(tc.gon_ten("It Takes Two PS4™ & PS5™"), "It Takes Two")
        self.assertEqual(tc.gon_ten("Grand Theft Auto: The Trilogy – The Definitive Edition (PS5 & PS4)"),
                         "Grand Theft Auto: The Trilogy – The Definitive Edition")
        self.assertEqual(tc.gon_ten("EA SPORTS™ Madden NFL 27"), "EA SPORTS Madden NFL 27")


class Dang(Chung):
    def form_tao(self, m):
        return [k["form"] for me, u, k in m.goi if me == "POST" and u.endswith("/THU1/threads")]

    def test_kenh_khong_con_threads_nhung_giu_gia_han(self):
        self.assertNotIn("threads", chay.KENH)
        self.assertIn("threads", chay.MOD)
        self.assertEqual(chay.KHOA_DICH["threads"], "threads_user_id")

    def test_sang_chi_chu_that(self):
        m = mang_threads()
        self.assertEqual(self.chay("sang", m=m), 0)
        f = self.form_tao(m)
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0]["media_type"], "TEXT")
        self.assertNotIn("image_url", f[0])
        self.assertEqual(f[0]["topic_tag"], "PlayStation")
        self.assertIn("Mafia III", f[0]["text"])
        self.assertNotIn("#", f[0]["text"])
        self.assertEqual(m.dem("POST", "threads_publish"), 1)
        self.assertEqual(self.ngu, [30])
        d = self.cong.dong[(NGAY, "tin-nhanh", "threads", "that")]
        self.assertEqual((d["trang_thai"], d["id_bai"], d["link"], d["id_container"]), ("da_dang", "T9", LINK, "TC1"))
        self.assertEqual(d["gio_du_kien"], "2026-10-12T02:30:00Z")   # 09:30 VN
        self.assertTrue(d["manifest_sha"])
        self.assertEqual([n[0] for n in self.ntfy], ["tin"])
        # kiem lai dung muc nhac trong bai, tai gio hien tai
        self.assertEqual([[x["pid"] for x in c[0]] for c in self.kiem_lai_goi], [["UP1001-PPSA36864_00-MAFIA3DEPS500000"]])
        self.assertEqual(self.kiem_lai_goi[0][1], BAY_GIO)

    def test_chieu_co_anh(self):
        self.man = man_chieu()
        self.bay = CHIEU
        m = mang_threads()
        self.assertEqual(self.chay("chieu", m=m), 0)
        f = self.form_tao(m)[0]
        self.assertEqual(f["media_type"], "IMAGE")
        self.assertEqual(f["image_url"], "https://x.github.io/sangame-video/v/2026-10-12-keo-thom-2-a6c8f942.jpg")
        self.assertEqual(f["topic_tag"], "PlayStation")
        self.assertIn("Indiana Jones", f["text"])
        self.assertEqual(self.kiem_url.call_args[0][1], "image/jpeg")
        self.assertEqual(self.cong.dong[(NGAY, "keo-thom-2", "threads", "that")]["trang_thai"], "da_dang")
        self.assertEqual([[x["loc"] for x in c[0]] for c in self.kiem_lai_goi], [["en-hk"], ["en-us"]])   # kiem rieng tung vung, dung pid cua vung
        self.assertIn("Rẻ hơn Store Mỹ 128.000đ", f["text"])
        self.assertNotIn("%", f["text"])

    def test_chieu_gia_my_lech_bo_cau_chenh_van_dang(self):
        self.man = man_chieu()
        self.bay = CHIEU
        self.van_de_my = ["gia doi 41.99 -> 49.99 (> 2%)"]
        m = mang_threads()
        self.assertEqual(self.chay("chieu", m=m), 0)
        t = self.form_tao(m)[0]["text"]
        self.assertNotIn("Store Mỹ", t)
        self.assertIn("1.048.000đ", t)
        self.assertEqual(self.cong.dong[(NGAY, "keo-thom-2", "threads", "that")]["trang_thai"], "da_dang")

    def test_chieu_kiem_my_loi_bo_cau_chenh_van_dang(self):
        self.man = man_chieu()
        self.bay = CHIEU
        self.van_de_my = "no"
        m = mang_threads()
        self.assertEqual(self.chay("chieu", m=m), 0)
        self.assertNotIn("Store Mỹ", self.form_tao(m)[0]["text"])

    def test_chieu_gia_hk_lech_khong_dang(self):
        self.man = man_chieu()
        self.bay = CHIEU
        self.van_de = ["gia doi"]
        self.assertEqual(self.chay("chieu", m=mang_threads()), 3)
        self.assertEqual(self.cong.dong, {})

    # --- chan ngay/gio (che_do that)
    def chan(self, loai, bay, man=None):
        self.bay = bay
        if man:
            self.man = man
        m = mang_threads()
        self.assertEqual(self.chay(loai, m=m), 3)
        self.assertEqual(m.goi, [])
        self.assertEqual(self.cong.dong, {})
        self.assertEqual(self.ntfy[0][0], "loi")

    def test_chan_sang_06h(self):
        self.chan("sang", dt.datetime(2026, 10, 12, 6, 0, tzinfo=chung.VN))

    def test_chan_sang_13h(self):
        self.chan("sang", dt.datetime(2026, 10, 12, 13, 0, tzinfo=chung.VN))

    def test_chan_chieu_13h_va_21h(self):
        self.man = man_chieu()
        self.chan("chieu", dt.datetime(2026, 10, 12, 13, 0, tzinfo=chung.VN))
        self.ntfy.clear()
        self.chan("chieu", dt.datetime(2026, 10, 12, 21, 0, tzinfo=chung.VN))

    def test_chan_ngay_khong_phai_hom_nay(self):
        self.chan("sang", dt.datetime(2026, 10, 13, 9, 30, tzinfo=chung.VN))   # --ngay 12/10 nhung hom nay 13/10

    def test_chan_manifest_hom_truoc(self):
        m = man_sang()
        m["ngay_dang"] = "2026-10-11"
        self.chan("sang", BAY_GIO, man=m)

    def test_cua_so_bien_trong_cho_dang(self):
        for loai, man, gio in (("sang", man_sang(), (9, 0)), ("sang", man_sang(), (12, 0)),
                               ("chieu", man_chieu(), (16, 30)), ("chieu", man_chieu(), (20, 0))):
            self.cong.dong.clear()
            self.man, self.bay = man, dt.datetime(2026, 10, 12, *gio, tzinfo=chung.VN)
            self.assertEqual(self.chay(loai, m=mang_threads()), 0, (loai, gio))

    def test_che_do_thu_khong_bi_chan_gio(self):
        self.bay = dt.datetime(2026, 10, 12, 3, 0, tzinfo=chung.VN)
        self.assertEqual(self.chay("sang", che_do="thu", m=Mang(), cong=None), 0)

    def test_chieu_pages_hong_dang_chi_chu(self):
        self.man = man_chieu()
        self.bay = CHIEU
        self.kiem_url.side_effect = LoiDang("404")
        m = mang_threads()
        self.assertEqual(self.chay("chieu", m=m), 0)
        f = self.form_tao(m)[0]
        self.assertEqual(f["media_type"], "TEXT")
        self.assertNotIn("image_url", f)
        self.assertEqual(self.cong.dong[(NGAY, "keo-thom-2", "threads", "that")]["trang_thai"], "da_dang")

    def test_giu_dang_false_khong_tao_container(self):
        self.cong.giu_dang(NGAY, "tin-nhanh", "threads", "that")
        m = mang_threads()
        self.assertEqual(self.chay("sang", m=m), 0)
        self.assertEqual(m.dem("POST", "graph.threads.net"), 0)
        self.assertEqual(self.ngu, [])

    def test_che_do_thu_chi_in_khong_mang_threads_khong_so(self):
        m = Mang()   # bat ky goi nao toi Threads se AssertionError
        self.assertEqual(self.chay("sang", che_do="thu", m=m, cong=None), 0)
        self.assertEqual(m.goi, [])
        self.assertEqual(self.cong.dong, {})
        self.assertEqual(self.ntfy, [])
        self.assertIn("Mafia III", self.in_ra)
        self.assertIn("topic_tag=PlayStation", self.in_ra)

    def test_che_do_thu_chieu_in_ca_anh(self):
        self.man = man_chieu()
        self.bay = CHIEU
        self.assertEqual(self.chay("chieu", che_do="thu", m=Mang(), cong=None), 0)
        self.assertIn("anh https://x.github.io/sangame-video/v/2026-10-12-keo-thom-2-a6c8f942.jpg", self.in_ra)

    def test_gia_lech_khong_dang(self):
        self.van_de = ["Mafia III: gia doi 45.8 -> 60 (> 2%)"]
        m = mang_threads()
        self.assertEqual(self.chay("sang", m=m), 3)
        self.assertEqual(m.goi, [])
        self.assertEqual(self.cong.dong, {})
        self.assertEqual(self.ntfy[0][0], "loi")
        self.assertIn("gia doi", self.ntfy[0][2])

    def test_thieu_release_khong_dang_va_bao_loi(self):
        self.loi_release = "khong co Release v-2026-10-12-tin-nhanh"
        m = mang_threads()
        self.assertEqual(self.chay("sang", m=m), 3)
        self.assertEqual(m.goi, [])
        self.assertEqual(self.cong.dong, {})
        self.assertEqual(self.ntfy[0][0], "loi")

    def test_manifest_sai_khung_khong_dang(self):
        self.man["dang"] = "top5"
        self.assertEqual(self.chay("sang", m=mang_threads()), 3)
        self.assertEqual(self.cong.dong, {})

    def test_tin_nhanh_kiem_lai_rong_khong_dang(self):
        self.man["kiem_lai"] = []
        m = mang_threads()
        self.assertEqual(self.chay("sang", m=m), 3)
        self.assertEqual(m.goi, [])

    def test_tao_container_loi_la_that_bai_cho_thu_lai(self):
        m = mang_threads(tao=P(400, {"error": {"message": "bad topic", "code": 100}}))
        with self.assertRaises(LoiDang) as cm:
            self.chay("sang", m=m)
        self.assertFalse(cm.exception.khong_ro)
        self.assertEqual(self.cong.dong[(NGAY, "tin-nhanh", "threads", "that")]["trang_thai"], "that_bai")
        self.assertEqual(m.dem("POST", "threads_publish"), 0)
        self.assertTrue(self.cong.giu_dang(NGAY, "tin-nhanh", "threads", "that"))   # that_bai thi duoc thu lai

    def test_publish_5xx_khong_ro_khong_dang_lai(self):
        m = mang_threads(publish=P(502))
        with self.assertRaises(LoiDang) as cm:
            self.chay("sang", m=m)
        self.assertTrue(cm.exception.khong_ro)
        self.assertEqual(self.cong.dong[(NGAY, "tin-nhanh", "threads", "that")]["trang_thai"], "khong_ro")
        self.assertEqual(m.dem("POST", "threads_publish"), 1)
        self.assertFalse(self.cong.giu_dang(NGAY, "tin-nhanh", "threads", "that"))

    def test_ghi_so_loi_sau_khi_dang_la_khong_ro(self):
        self.cong.hong_ghi_sau = lambda kenh, tr: tr.get("trang_thai") == "da_dang"
        with self.assertRaises(LoiDang) as cm:
            self.chay("sang", m=mang_threads())
        self.assertTrue(cm.exception.khong_ro)
        self.assertIn(LINK, str(cm.exception))

    def test_danh_tinh_lech_dung(self):
        m = mang_threads()
        m.luat[2][2] = P(body={"id": "NGUOI_KHAC"})
        with self.assertRaises(LoiDang):
            self.chay("sang", m=m)
        self.assertEqual(self.cong.dong, {})
        self.assertEqual(m.dem("POST", "graph.threads.net"), 0)

    def test_main_cli_thu_khong_can_cong(self):
        m = Mang()
        with mock.patch.object(http, "gui", m), contextlib.redirect_stdout(io.StringIO()) as buf:
            self.assertEqual(tc.main(["--loai", "sang", "--ngay", NGAY, "--che-do", "thu"]), 0)
        self.assertIn("Mafia III", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
