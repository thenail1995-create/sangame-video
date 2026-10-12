"""Caption rieng tung nen tang: do dai, URL, tran hashtag, hook, nhan 'sang'. loi_dang = manifest THAT 12/10/2026
(gh release download v-2026-10-12-<dang> manifest.json), chep cung. Khong goi mang."""
import datetime as dt
import re
import unittest
from unittest import mock

from dang import chung, x

LOI_DANG = {
    "tin-nhanh": {
        "tieu_de": "Tin nhanh PlayStation 12/10: 8 game bán chạy giảm 50–80% | 10 game bán chạy đang giảm 30–70%",
        "mo_ta": "Bản tin sáng Săn Game, Thứ Hai 12/10:\n1. GIẢM SÂU: 8 game bán chạy giảm 50–80%.\n2. DEAL HOT: 10 game bán chạy đang giảm 30–70%.\n3. ĐỢT SALE: Player's Choice.\nGiảm sâu: rẻ nhất Mafia III, 160.000đ ở Store Hồng Kông (giảm 80%).\nDeal hot: rẻ nhất It Takes Two, 335.000đ ở Store Hồng Kông (giảm 70%).\nTra giá mọi game ở 6 vùng PS Store: https://sangame.com.vn/",
        "hashtag": [
            "#SănGame",
            "#PlayStation",
            "#PS5"
        ],
        "link": "https://sangame.com.vn/"
    },
    "top5": {
        "tieu_de": "Top 5 game PlayStation bán chạy dưới 300.000đ hôm nay (12/10)",
        "mo_ta": "Top 5 game PlayStation bán chạy đang giảm giá, dưới 300.000đ (ngày 12/10):\n1. Mafia III: Definitive Edition - 160.000đ (-80%, store Hồng Kông)\n2. Marvel's Spider-Man - 231.000đ (-40%, store Hồng Kông)\n3. STAR WARS Jedi: Survivor - 288.000đ (-85%, store Hồng Kông)\n4. A Way Out - 221.000đ (-70%, store Hồng Kông)\n5. Mortal Kombat 1 - 272.000đ (-80%, store Hồng Kông)\n\nCòn 102 game bán chạy nữa dưới 300.000đ. Deal sớm nhất hết lúc 21/10 21:59 (giờ VN).\nGiá quy đổi theo giá thẻ PSN ở Việt Nam, có thể đổi theo tỷ giá. Tra giá 6 vùng PS Store: https://sangame.com.vn/",
        "hashtag": [
            "#SănGame",
            "#PlayStation",
            "#PS5",
            "#GiảmGiá"
        ],
        "link": "https://sangame.com.vn/"
    },
    "keo-thom": {
        "tieu_de": "NINJA GAIDEN 2 Black giảm 60% ở PS Store Mỹ: còn 560.000đ",
        "mo_ta": "NINJA GAIDEN 2 Black đang giảm 60% ở PS Store Mỹ: còn 560.000đ (giá gốc 1.400.000đ) khi quy theo giá thẻ PSN. So với Hồng Kông: +27.000đ; Singapore: +170.000đ. Hết giảm 13:59 ngày 22/10 giờ Việt Nam. Giá quy đổi chỉ để tham khảo.\n\nXem giá ở 6 vùng PS Store: https://sangame.com.vn/game-ninja-gaiden-2-black.html",
        "hashtag": [
            "#SănGame",
            "#PlayStation",
            "#PS5",
            "#GiảmGiá"
        ],
        "link": "https://sangame.com.vn/"
    }
}

def setUpModule():
    """Dong ho gia: 'bay gio' truoc moi gio du kien (11/10), de gio_cong_khai = gio du kien."""
    global _P
    _P = mock.patch.object(chung, "bay_gio", return_value=dt.datetime(2026, 10, 11, 0, 0, tzinfo=dt.timezone.utc))
    _P.start()


def tearDownModule():
    _P.stop()


URL = re.compile(r"https?://", re.I)


def nc(dang, gio=14, ld=None):
    g = dt.datetime(2026, 10, 12, gio, 0, tzinfo=chung.VN)
    man = {"loi_dang": ld or LOI_DANG[dang]}
    return chung.NguCanh("2026-10-12", dang, "thu", g, man, "/tmp", None)


def dem_tag(s):
    return len(re.findall(r"#\w+", s))


class HashtagGame(unittest.TestCase):
    def test_vi_du(self):
        self.assertEqual(chung.hashtag_game("NINJA GAIDEN 2 Black"), "#NinjaGaiden2Black")
        self.assertEqual(chung.hashtag_game("Mafia III"), "#MafiaIII")
        self.assertEqual(chung.hashtag_game("Marvel's Spider-Man 2"), "#MarvelsSpiderMan2")
        self.assertEqual(chung.hashtag_game("Mafia III: Definitive Edition"), "#MafiaIII")
        self.assertEqual(chung.hashtag_game("Đấu Trường Ánh Sáng"), "#DauTruongAnhSang")

    def test_tran_25_va_rong(self):
        t = chung.hashtag_game("A" * 10 + " " + "B" * 30)
        self.assertLessEqual(len(t) - 1, 25)
        self.assertEqual(chung.hashtag_game(""), "")
        self.assertEqual(chung.hashtag_game(None), "")
        self.assertEqual(chung.hashtag_game("!!! ???"), "")

    def test_bo_hashtag_cat_theo_tran(self):
        self.assertEqual(chung.bo_hashtag("Mafia III", 5), ["#MafiaIII", "#PlayStation", "#PS5", "#SănGame", "#GiảmGiá"])
        self.assertEqual(chung.bo_hashtag("Mafia III", 2), ["#MafiaIII", "#PlayStation"])
        self.assertEqual(chung.bo_hashtag(None, 3), ["#PlayStation", "#PS5", "#SănGame"])


class Hook(unittest.TestCase):
    def test_tin_nhanh_lay_game_re_nhat_tu_manifest(self):
        h = nc("tin-nhanh").hook()
        self.assertEqual(h, "Mafia III chỉ còn 160.000đ — 3 tin giảm giá PS hôm nay")

    def test_tin_nhanh_chon_dong_re_hon(self):
        ld = dict(LOI_DANG["tin-nhanh"], mo_ta="1. A.\n2. B.\nGiảm sâu: rẻ nhất Alpha, 500.000đ ở X (giảm 50%).\nDeal hot: rẻ nhất Beta, 90.000đ ở X (giảm 70%).")
        self.assertTrue(nc("tin-nhanh", ld=ld).hook().startswith("Beta chỉ còn 90.000đ — 2 tin"))

    def test_tin_nhanh_khong_parse_duoc_dung_tieu_de(self):
        ld = dict(LOI_DANG["tin-nhanh"], mo_ta="khong co dong re nhat")
        self.assertEqual(nc("tin-nhanh", ld=ld).hook(), ld["tieu_de"])

    def test_top5(self):
        self.assertEqual(nc("top5").hook(), "Top 5 game PS dưới 300.000đ hôm nay")

    def test_keo_giu_tieu_de_co_ten_game_va_gia(self):
        c = nc("keo-thom")
        self.assertEqual(c.hook(), LOI_DANG["keo-thom"]["tieu_de"])
        self.assertIn("NINJA GAIDEN 2 Black", c.hook())
        self.assertIn("560.000đ", c.hook())


class TungNenTang(unittest.TestCase):
    CAC = ("tin-nhanh", "top5", "keo-thom")

    def test_tiktok(self):
        for d in self.CAC:
            c = nc(d)
            s = c.caption_tiktok()
            self.assertLessEqual(len(s), 150, d)
            self.assertFalse(URL.search(s), d)
            self.assertEqual(dem_tag(s), 3, d)
            self.assertTrue(s.split("\n")[0] == c.hook(), d)

    def test_tiktok_hook_dai_bi_cat_van_du_hashtag(self):
        ld = dict(LOI_DANG["keo-thom"], tieu_de="NINJA GAIDEN 2 Black giảm 60% " + "x" * 300)
        s = nc("keo-thom", ld=ld).caption_tiktok()
        self.assertLessEqual(len(s), 150)
        self.assertEqual(dem_tag(s), 3)
        self.assertIn("…\n#NinjaGaiden2Black", s)

    def test_youtube(self):
        for d in self.CAC:
            c = nc(d)
            tt, mt = c.tieu_de_youtube(), c.mo_ta_youtube()
            self.assertLessEqual(len(tt), 100, d)
            self.assertFalse(URL.search(mt), d)
            self.assertFalse(URL.search(tt), d)
            dau = re.findall(r"#\w+", mt)
            self.assertEqual(dau[-1], "#Shorts")
            self.assertEqual(len(dau[:3]), 3)
            self.assertTrue(mt.startswith(" ".join(dau[:3])), d)   # 3 hashtag dau o dau mo ta
            self.assertLessEqual(len(dau), 4, d)

    def test_youtube_tieu_de_cuc_dai_cat_100(self):
        ld = dict(LOI_DANG["keo-thom"], tieu_de="NINJA GAIDEN 2 Black giảm 60% " + "x" * 300)
        self.assertEqual(len(nc("keo-thom", ld=ld).tieu_de_youtube()), 100)

    def test_instagram(self):
        for d in self.CAC:
            c = nc(d)
            s = c.caption_ig()
            self.assertLessEqual(len(s), 2200)
            self.assertFalse(URL.search(s), d)
            self.assertLessEqual(dem_tag(s), 5, d)
            self.assertIn("Link ở bio", s, d)
            self.assertTrue(s.startswith(c.hook()), d)
            self.assertLessEqual(len(c._than()), 2, d)

    def test_facebook(self):
        for d in self.CAC:
            c = nc(d)
            s = c.caption_fb()
            self.assertTrue(s.startswith(c.hook() + "\n\n"), d)
            self.assertIn("https://sangame.com.vn/", s, d)
            self.assertLessEqual(dem_tag(s), 3, d)
            self.assertEqual(s.count("https://sangame.com.vn/"), 1, d)   # khong lap link
        self.assertIn("https://sangame.com.vn/game-ninja-gaiden-2-black.html", nc("keo-thom").caption_fb())

    def test_x_hashtag_toi_da_2(self):
        for d in self.CAC:
            s = x.text_x(nc(d))
            self.assertLessEqual(dem_tag(s), 2, d)
            self.assertLessEqual(x.do_dai_x(s), 280, d)

    def test_hook_chua_ten_game_va_con_so_dung_manifest(self):
        # ten game + gia lay dung tu mo_ta/tieu_de that
        self.assertIn("Mafia III", nc("tin-nhanh").caption_tiktok())
        self.assertIn("160.000đ", nc("tin-nhanh").caption_tiktok())
        self.assertIn("300.000đ", nc("top5").caption_tiktok())
        self.assertIn("#NinjaGaiden2Black", nc("keo-thom").caption_tiktok())

    def test_hashtag_game_mat_thi_van_du_bo_co_dinh(self):
        ld = dict(LOI_DANG["keo-thom"], tieu_de="khong dung mau")
        self.assertEqual(nc("keo-thom", ld=ld).hashtags("ig"), ["#PlayStation", "#PS5", "#SănGame", "#GiảmGiá"])

    def test_dang_la_van_chay_dung_tieu_de(self):
        ld = dict(LOI_DANG["keo-thom"])
        s = nc("keo-thom-2", ld=ld).caption_tiktok()
        self.assertIn("#NinjaGaiden2Black", s)


class NhanSang(unittest.TestCase):
    def test_truoc_10h_giu_sang(self):
        for g in (7, 9):
            self.assertIn("Bản tin sáng", nc("tin-nhanh", gio=g).caption_fb())
            self.assertIn("Bản tin sáng", nc("tin-nhanh", gio=g).mo_ta_youtube())

    def test_tu_10h_doi_thanh_hom_nay(self):
        for g in (10, 14, 22):
            for s in (nc("tin-nhanh", gio=g).caption_fb(), nc("tin-nhanh", gio=g).mo_ta_youtube()):
                self.assertNotIn("sáng", s)
                self.assertIn("Bản tin hôm nay", s)

    def test_dung_gio_cong_khai_thuc_te_khong_phai_gio_du_kien(self):
        c = nc("tin-nhanh", gio=7)     # du kien 07:30 nhung that su dang luc 14:00
        muon = dt.datetime(2026, 10, 12, 14, 0, tzinfo=chung.VN)
        with mock.patch.object(chung, "bay_gio", return_value=muon.astimezone(dt.timezone.utc)):
            self.assertNotIn("sáng", c.caption_fb())
        som = dt.datetime(2026, 10, 12, 6, 0, tzinfo=chung.VN)
        with mock.patch.object(chung, "bay_gio", return_value=som.astimezone(dt.timezone.utc)):
            self.assertIn("Bản tin sáng", c.caption_fb())     # chuan bi som: lay gio du kien 07:00

    def test_sang_nay(self):
        ld = dict(LOI_DANG["keo-thom"], mo_ta="Deal sáng nay rất hời. Hết giảm 1 giờ.")
        self.assertIn("hôm nay", nc("keo-thom", gio=15, ld=ld).caption_fb())
        self.assertIn("sáng nay", nc("keo-thom", gio=8, ld=ld).caption_fb())


if __name__ == "__main__":
    unittest.main()
