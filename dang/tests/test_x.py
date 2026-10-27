"""X qua Buffer: mock http, khong goi mang that, khong ngu that."""
import contextlib
import io
import os
import unittest
from unittest import mock

from dang import chay, chung, http, ntfy, site, x
from dang.chung import LoiDang
from dang.tests import gia_lap as g
from dang.tests.gia_lap import Mang, P, NGAY, DANG, cong_day_du, tao_nc

KHOA = "bk_LIVE_BIMAT_1234567890abcdef"
LINK = "https://x.com/2109560997036146688/status/2109571869942636705"
# loi_dang that cua Ke 15:00 12/10/2026 (manifest keo-thom-2 chay thu)
LOI_DANG_THAT = {
    "tieu_de": "Indiana Jones and the Great Circle giảm 40% ở PS Store Hồng Kông: còn 1.048.000đ",
    "mo_ta": "Indiana Jones and the Great Circle đang giảm 40% ở PS Store Hồng Kông: còn 1.048.000đ (giá gốc 1.747.000đ) khi quy theo giá thẻ PSN. So với Mỹ: +128.000đ; Singapore: +271.000đ. Hết giảm 21:59 ngày 21/10 giờ Việt Nam. Giá quy đổi chỉ để tham khảo.\n\nXem giá ở 6 vùng PS Store: https://sangame.com.vn/game-indiana-jones-and-the-great-circle.html",
    "hashtag": ["#SănGame", "#PlayStation", "#PS5", "#GiảmGiá"],
    "link": "https://sangame.com.vn/",
}
LINK_GAME = "https://sangame.com.vn/game-indiana-jones-and-the-great-circle.html"


def tra_tao(status="sending", pid="BP1"):
    return P(200, {"data": {"createPost": {"__typename": "PostActionSuccess", "post": {"id": pid, "status": status}}}})


def tra_hoi(status, **kw):
    return P(200, {"data": {"post": {"id": "BP1", "status": status, "externalLink": LINK if status == "sent" else None, **kw}}})


def mang(tao=None, poll=None):
    """Mot URL cho ca createPost va post(): phan biet theo noi dung query."""
    tao = tao if tao is not None else tra_tao()
    poll = poll if poll is not None else tra_hoi("sent")
    m = Mang()
    lan = {"tao": tao, "poll": poll}

    def f(method, url, kw):
        k = "tao" if "createPost" in kw["json_body"]["query"] else "poll"
        t = lan[k]
        if isinstance(t, list):
            t = t.pop(0) if len(t) > 1 else t[0]
        if isinstance(t, Exception):
            raise t
        return t
    m.them("POST", "api.buffer.com", f)
    return m


class X(unittest.TestCase):
    def setUp(self):
        self.cong = cong_day_du()
        self.nc = tao_nc(cong=self.cong)
        self.nc.manifest_sha = "SHA1"
        self.ngu = []
        self.ntfy = []
        self.kiem_url = mock.Mock(return_value=True)
        for p in (mock.patch.dict(os.environ, {"BUFFER_KHOA": KHOA}),
                  mock.patch.object(chung, "bay_gio", lambda: g.GIO_DANG),
                  mock.patch.object(chung, "ngu", lambda s: self.ngu.append(s)),
                  mock.patch.object(site, "kiem_url", self.kiem_url),
                  mock.patch.object(ntfy, "loi", lambda *a, **k: self.ntfy.append(a))):
            p.start()
            self.addCleanup(p.stop)
        os.environ.pop("BUFFER_X_KENH", None)
        self.dich = g.DICH_DU

    def chay(self, m, cac_dong=()):
        with mock.patch.object(http, "gui", m):
            return chay.cong_khai_kenh("x", self.nc, self.dich, self.cong, None, list(cac_dong))

    def tt(self):
        return self.cong.trang_thai("x")

    def goi_tao(self, m):
        return [kw for mt, u, kw in m.goi if "createPost" in kw["json_body"]["query"]]

    # 1
    def test_thanh_cong(self):
        m = mang(poll=[tra_hoi("sending"), tra_hoi("sent")])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            kq, ket = self.chay(m)
            chung.log(f"thu {KHOA}")
        self.assertEqual(kq, "da_dang")
        self.assertEqual(ket["link"], LINK)
        self.assertEqual(self.tt(), "da_dang")
        d = self.cong.dong[(NGAY, DANG, "x", "that")]
        self.assertEqual((d["link"], d["id_bai"]), (LINK, "BP1"))
        tao = self.goi_tao(m)
        self.assertEqual(len(tao), 1)
        q = tao[0]["json_body"]["query"]
        self.assertIn('channelId: "6acca131778b240e2fe466f3"', q)
        self.assertIn("mode: shareNow", q)
        self.assertIn('assets: [{video: {url: "https://x.github.io/sangame-video/v/a.mp4"}}]', q)
        self.assertEqual(tao[0]["headers"]["Authorization"], "Bearer " + KHOA)
        self.assertEqual(self.ngu, [15, 15])
        self.assertNotIn(KHOA, buf.getvalue() + str(self.cong.dong))

    def test_loi_khong_lo_khoa(self):
        m = mang(tao=P(500, {"error": "x"}))
        with self.assertRaises(LoiDang) as cm:
            self.chay(m)
        self.assertNotIn(KHOA, str(cm.exception) + str(self.cong.dong))

    def test_video_url_pages_hong_dung_url_release(self):
        self.nc.url_video = None
        self.kiem_url.side_effect = LoiDang("404")
        m = mang()
        self.chay(m)
        q = self.goi_tao(m)[0]["json_body"]["query"]
        self.assertIn("github.com/thenail1995-create/sangame-video/releases/download/v-2026-10-12-top5/video-reels.mp4", q)

    def test_video_url_pages_dung_duoc(self):
        self.nc.url_video = None
        m = mang()
        self.chay(m)
        q = self.goi_tao(m)[0]["json_body"]["query"]
        self.assertIn("github.io/sangame-video/v/2026-10-12-top5-", q)
        self.assertIn(".mp4", q)

    # 2
    def test_mutation_error_that_bai(self):
        m = mang(tao=P(200, {"data": {"createPost": {"__typename": "MutationError", "message": "Channel limit"}}}))
        with self.assertRaises(LoiDang) as cm:
            self.chay(m)
        self.assertFalse(cm.exception.khong_ro)
        self.assertEqual(self.tt(), "that_bai")
        self.assertEqual(len(self.goi_tao(m)), 1)

    def test_errors_cap_tren_that_bai(self):
        m = mang(tao=P(200, {"errors": [{"message": "Unauthorized"}]}))
        with self.assertRaises(LoiDang) as cm:
            self.chay(m)
        self.assertFalse(cm.exception.khong_ro)
        self.assertEqual(self.tt(), "that_bai")

    def test_errors_kem_data_khong_ro(self):
        # GPT soi P1: errors luc thuc thi (co khoa data) -> co the da tao -> khong_ro, khong tao lan 2
        m = mang(tao=P(200, {"data": {"createPost": None}, "errors": [{"message": "internal"}]}))
        with self.assertRaises(LoiDang) as cm:
            self.chay(m)
        self.assertTrue(cm.exception.khong_ro)
        self.assertEqual(self.tt(), "khong_ro")
        self.assertEqual(len(self.goi_tao(m)), 1)

    def test_http_4xx_that_bai(self):
        m = mang(tao=P(401, {"error": "bad token"}))
        with self.assertRaises(LoiDang) as cm:
            self.chay(m)
        self.assertFalse(cm.exception.khong_ro)
        self.assertEqual(self.tt(), "that_bai")

    # 3
    def test_timeout_khong_ro_khong_tao_lan_2(self):
        m = mang(tao=http.LoiMang("POST x: TimeoutError"))
        with self.assertRaises(LoiDang) as cm:
            self.chay(m)
        self.assertTrue(cm.exception.khong_ro)
        self.assertEqual(self.tt(), "khong_ro")
        self.assertEqual(len(self.goi_tao(m)), 1)

    def test_5xx_khong_ro_khong_tao_lan_2(self):
        m = mang(tao=P(502))
        with self.assertRaises(LoiDang) as cm:
            self.chay(m)
        self.assertTrue(cm.exception.khong_ro)
        self.assertEqual(self.tt(), "khong_ro")
        self.assertEqual(len(self.goi_tao(m)), 1)

    # 4
    def test_poll_error_that_bai_kem_message(self):
        m = mang(poll=tra_hoi("error", error={"message": "Video too long"}))
        with self.assertRaises(LoiDang) as cm:
            self.chay(m)
        self.assertFalse(cm.exception.khong_ro)
        self.assertIn("Video too long", str(cm.exception))
        self.assertEqual(self.tt(), "that_bai")

    def test_poll_het_10_phut_khong_ro(self):
        m = mang(poll=tra_hoi("sending"))
        with self.assertRaises(LoiDang) as cm:
            self.chay(m)
        self.assertTrue(cm.exception.khong_ro)
        self.assertEqual(sum(self.ngu), 600)
        self.assertEqual(self.tt(), "khong_ro")
        self.assertEqual(len(self.goi_tao(m)), 1)

    def test_poll_loi_mang_roi_sent(self):
        m = mang(poll=[http.LoiMang("t"), P(502), tra_hoi("sent")])
        kq, ket = self.chay(m)
        self.assertEqual(kq, "da_dang")

    # 5
    def test_che_do_thu_khong_goi_mang_khong_ghi_so(self):
        self.nc.che_do = "thu"
        m = mang()
        kq, _ = self.chay(m)
        self.assertEqual(kq, "bo_qua")
        self.assertEqual(m.goi, [])
        self.assertEqual(self.cong.dong, {})

    # 6
    def test_thieu_khoa_loi_khong_goi_mang(self):
        os.environ.pop("BUFFER_KHOA")
        m = mang()
        with self.assertRaises(LoiDang) as cm:
            self.chay(m)
        self.assertIn("BUFFER_KHOA", str(cm.exception))
        self.assertEqual(m.goi, [])
        self.assertEqual(self.cong.dong, {})

    # 7
    def test_da_co_dong_khong_goi_mang(self):
        self.cong.giu_dang(NGAY, DANG, "x", "that")
        m = mang()
        kq, _ = self.chay(m)
        self.assertEqual(kq, "bo_qua")
        self.assertEqual(m.goi, [])

    def test_manifest_sha_khac_luc_chuan_bi_khong_gui(self):
        m = mang()
        with self.assertRaises(LoiDang):
            self.chay(m, [{"kenh": "fb", "manifest_sha": "SHA_KHAC"}])
        self.assertEqual(m.goi, [])
        self.assertEqual(self.cong.dong, {})

    def test_ghi_so_loi_sau_khi_dang_la_khong_ro(self):
        self.cong.hong_ghi_sau = lambda kenh, tr: kenh == "x" and tr.get("trang_thai") == "da_dang"
        m = mang()
        with self.assertRaises(LoiDang) as cm:
            self.chay(m)
        self.assertTrue(cm.exception.khong_ro)
        self.assertIn(LINK, str(cm.exception))

    def test_loi_bat_ngo_khong_ro(self):
        m = mang()
        with mock.patch.object(x, "hoi_den_xong", side_effect=KeyError("boom")):
            with self.assertRaises(LoiDang) as cm:
                self.chay(m)
        self.assertTrue(cm.exception.khong_ro)
        self.assertEqual(self.tt(), "khong_ro")

    # 8
    def test_do_dai_x(self):
        self.assertEqual(do_dai("abc"), 3)
        self.assertEqual(do_dai("ăâê"), 3)             # <= U+10FF tinh 1
        self.assertEqual(do_dai("ạế"), 4)              # U+1EA0.. tinh 2 (dung san)
        self.assertEqual(do_dai("e\u0323"), 2)         # NFD duoc chuan hoa NFC (ẹ = U+1EB9 -> 2)
        self.assertEqual(do_dai("…"), 2)
        self.assertEqual(do_dai("a\u2019b"), 3)        # dau nhay cong U+2019 tinh 1
        self.assertEqual(do_dai("\U0001F600"), 2)
        self.assertEqual(do_dai("https://sangame.com.vn/" + "a" * 200), 23)
        self.assertEqual(do_dai("xem https://sangame.com.vn/game-rat-dai-dai-dai.html nhe"), 4 + 23 + 4)

    def test_text_tu_manifest_that(self):
        self.nc.loi_dang = dict(LOI_DANG_THAT)
        s = x.text_x(self.nc)
        print("TEXT X:\n" + s, "\nDO DAI:", x.do_dai_x(s))
        self.assertLessEqual(x.do_dai_x(s), 280)
        self.assertIn(LINK_GAME, s)
        self.assertTrue(s.startswith("Indiana Jones and the Great Circle giảm 40%"))
        self.assertNotIn("\nXem giá", s)

    def test_text_giu_cau_han_neu_vua(self):
        self.nc.loi_dang = {"tieu_de": "Game X giam 40%", "mo_ta": "Mo ta. Hết giảm 21:59 ngày 21/10 giờ Việt Nam. Het.\n\nXem: https://sangame.com.vn/game-x.html",
                            "hashtag": ["#A", "#B"], "link": "https://sangame.com.vn/"}
        s = x.text_x(self.nc)
        self.assertEqual(s, "Game X giam 40%\nHết giảm 21:59 ngày 21/10 giờ Việt Nam.\nhttps://sangame.com.vn/game-x.html\n#PlayStation #PS5\n" + chung.DONG_NHAN_AI)

    def test_text_khong_co_link_trong_mo_ta_dung_link_dang(self):
        self.nc.loi_dang = {"tieu_de": "T", "mo_ta": "Mo ta.", "hashtag": [], "link": "https://sangame.com.vn/"}
        self.assertEqual(x.text_x(self.nc), "T\nhttps://sangame.com.vn/\n#PlayStation #PS5\n" + chung.DONG_NHAN_AI)

    def test_text_bo_han_roi_hashtag_khi_chat(self):
        # tieu de ~ 200 trong so: du cho link + vai tag nhung khong du cau han
        td = "a" * 190
        self.nc.loi_dang = {"tieu_de": td, "mo_ta": "Hết giảm 21:59 ngày 21/10 giờ Việt Nam.\nhttps://sangame.com.vn/g.html",
                            "hashtag": ["#SănGame", "#PlayStation", "#PS5", "#GiảmGiá"], "link": ""}
        s = x.text_x(self.nc)
        self.assertNotIn("Hết giảm", s)
        self.assertLessEqual(x.do_dai_x(s), 280)
        self.assertIn("https://sangame.com.vn/g.html", s)
        self.assertIn("#PlayStation", s)
        # chat hon nua: hashtag bi bot tu cuoi
        self.nc.loi_dang["tieu_de"] = "a" * 240
        s = x.text_x(self.nc)
        self.assertLessEqual(x.do_dai_x(s), 280)
        self.assertNotIn("#PS5", s)
        self.assertIn("a" * 200, s)   # nhan AI chiem cho nen tieu de 240 bi cat nhe
        self.assertTrue(s.endswith(chung.DONG_NHAN_AI))

    def test_tieu_de_cuc_dai_cat_co_dau_ba_cham(self):
        self.nc.loi_dang = {"tieu_de": "Ạ" * 400, "mo_ta": "Hết giảm 1 giờ.\nhttps://sangame.com.vn/g.html", "hashtag": ["#A"], "link": ""}
        s = x.text_x(self.nc)
        self.assertLessEqual(x.do_dai_x(s), 280)
        self.assertIn("…\nhttps://sangame.com.vn/g.html", s)
        self.assertGreater(x.do_dai_x(s), 250)   # cat vua du, khong cat lo tay

    # 9
    def kiem_gio(self, che_do, dang_ky=()):
        self.nc.che_do = che_do
        for k in chay.KENH:
            if k in dang_ky:
                self.cong.giu_dang(NGAY, DANG, k, che_do, "2026-10-12T05:00:00Z")
                self.cong.dong[(NGAY, DANG, k, che_do)]["trang_thai"] = "da_dang" if (che_do == "that" or k == "tiktok") else "chuan_bi_xong"
        self.ntfy.clear()
        a = type("A", (), {"ngay": NGAY, "dang": DANG, "che_do": che_do})()
        with mock.patch.object(chung, "bay_gio", lambda: g.GIO_DANG.replace(hour=13)):
            return chay.pha_kiem_gio(a, self.cong)

    def test_kiem_gio_thu_khong_bao_x(self):
        self.assertEqual(self.kiem_gio("thu", ("fb", "ig", "threads", "youtube", "tiktok")), 0)
        self.assertEqual(self.ntfy, [])

    def test_kiem_gio_that_khong_doi_dong_x_video(self):
        # 27/10 (SG-X-A): X thoi nhan video may -> kiem gio khong doi dong X cua khung video nua
        self.assertEqual(self.kiem_gio("that", ("fb", "ig", "threads", "youtube", "tiktok")), 0)
        self.assertEqual(self.ntfy, [])

    def test_kiem_gio_that_du_x_im(self):
        self.assertEqual(self.kiem_gio("that", chay.KENH), 0)

    def test_chua_toi_han_tinh_dung_so_kenh(self):
        a = type("A", (), {"ngay": NGAY, "dang": DANG, "che_do": "thu"})()
        with mock.patch.object(chung, "bay_gio", lambda: g.GIO_DANG.replace(hour=11)):
            self.assertEqual(chay.pha_kiem_gio(a, self.cong), 0)
        self.assertEqual(self.ntfy, [])

    # chuan bi / bo khung
    def test_bo_khung_chi_ghi_x_o_che_do_that(self):
        chay.bo_khung(self.cong, NGAY, DANG, "thu", g.GIO_DANG, "sai")
        self.assertNotIn((NGAY, DANG, "x", "thu"), self.cong.dong)
        chay.bo_khung(self.cong, NGAY, DANG, "that", g.GIO_DANG, "sai")
        self.assertEqual(self.tt(), "bo")
        # X da 'bo' -> luot cong khai khong dang
        m = mang()
        kq, _ = self.chay(m)
        self.assertEqual(kq, "bo_qua")
        self.assertEqual(m.goi, [])

    def test_chuan_bi_khong_dung_x(self):
        self.assertNotIn("x", chay.MOD)
        self.assertNotIn("x", chay.KHOA_DICH)
        self.assertEqual(chay.TEN["x"], "X")
        self.assertEqual(chay.KENH[-1], "x")


do_dai = x.do_dai_x

if __name__ == "__main__":
    unittest.main()
