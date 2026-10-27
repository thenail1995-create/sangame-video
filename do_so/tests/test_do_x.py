"""Do bai X goc (do_so/chay.py do_x) qua FxTwitter: mock mang, khong goi that."""
import datetime as dt
import unittest

from dang.tests.gia_lap import P
from do_so import chay
from do_so.tests.test_do_so import CongDo, Chung, DONG_SO, mang_day_du


def dong_x(id_x, gio, dang="x-goc", kenh="x", link=None, ngay=None):
    t = dt.datetime.fromisoformat(gio.replace("Z", "+00:00"))
    return {"kenh": kenh, "id_bai": "BUF" + id_x, "dang": dang, "trang_thai": "da_dang", "gio_cong_khai": gio,
            "ngay": ngay or t.astimezone(dt.timezone(dt.timedelta(hours=7))).date().isoformat(),
            "link": link if link is not None else f"https://x.com/sangamecomvn/status/{id_x}"}


def tra_fx(id_x, views=None, **kv):
    st = {"id": id_x, "text": "Tomb Raider giảm 90%, còn 72 nghìn\n\nthân bài", "author": {"screen_name": "sangamecomvn", "id": "1"},
          "likes": 12, "replies": 3, "reposts": 4, "quotes": 2, "views": views}
    st.update(kv)
    return P(200, {"code": 200, "status": st})


class DoX(Chung):
    # NOW = 2026-10-15 16:00Z; do-so-lieu chay 16:30 + 23:30 -> cua so [48 h, 60 h)
    def chay_x(self, dong_them, fx):
        m = mang_day_du()
        m.them("GET", "api.fxtwitter.com/2/status/", fx)
        cong = CongDo(DONG_SO + dong_them)
        ma, cong = self.chay(m, cong)
        self.m = m
        return ma, cong

    def x_rows(self, cong):
        return [b for b in cong.bai_da_ghi() if b["nen_tang"] == "X"]

    def test_do_bai_48h_den_60h_va_map_truong(self):
        dong = [dong_x("1000000000000000001", "2026-10-13T16:00:00Z"),      # 48 h dung: do
                dong_x("1000000000000000002", "2026-10-13T04:00:01Z"),      # 59 h 59: do
                dong_x("1000000000000000003", "2026-10-13T04:00:00Z"),      # 60 h: bo
                dong_x("1000000000000000004", "2026-10-13T16:00:01Z"),      # 47 h 59: bo
                dong_x("1000000000000000005", "2026-10-14T05:00:00Z"),      # 35 h: bo
                dong_x("1000000000000000006", "2026-10-13T16:00:00Z", link="https://x.com/sangamecomvn/status/abc"),   # link sai: bo
                dong_x("1000000000000000007", "2026-10-13T16:00:00Z", kenh="fb")]                                       # kenh khac: bo
        ma, cong = self.chay_x(dong, lambda mt, u, kw: tra_fx(u.rsplit("/", 1)[1], views=None))
        self.assertEqual(ma, 0, self.log)
        r = {b["id_bai"]: b for b in self.x_rows(cong)}
        self.assertEqual(set(r), {"1000000000000000001", "1000000000000000002"})
        b = r["1000000000000000001"]
        self.assertEqual((b["luot_xem"], b["thich"], b["binh_luan"], b["chia_se"]), (None, 12, 3, 6))   # chia_se = reposts + quotes
        self.assertEqual((b["dang"], b["khuon"], b["ngay"], b["link"]), ("x-goc", "X bài gốc", "2026-10-13", "https://x.com/sangamecomvn/status/1000000000000000001"))
        self.assertEqual(b["tieu_de"], "Tomb Raider giảm 90%, còn 72 nghìn")
        self.assertEqual(self.m.dem("GET", "api.fxtwitter.com"), 2)
        self.assertIn("X: 2 bai, 0 loi bai", self.log)

    def test_hai_luot_lien_tiep_khong_do_trung(self):
        dong = [dong_x("1000000000000000001", "2026-10-13T08:00:00Z")]         # 56 h: nam trong cua so o ca hai luot
        m = mang_day_du()
        m.them("GET", "api.fxtwitter.com/2/status/", lambda mt, u, kw: tra_fx(u.rsplit("/", 1)[1]))
        cong = CongDo(DONG_SO + dong)
        self.chay(m, cong)
        self.assertEqual(len(self.x_rows(cong)), 1)
        ma, cong = self.chay(m, cong)                                            # luot 2: sg_so_lieu da co id nay
        self.assertEqual(ma, 0, self.log)
        self.assertEqual(len(self.x_rows(cong)), 1)                              # khong them dong X nao
        self.assertEqual(m.dem("GET", "api.fxtwitter.com"), 1)

    def test_chi_do_x_goc_da_dang(self):
        dong = [dong_x("1000000000000000001", "2026-10-13T16:00:00Z", dang="tin-nhanh"),
                {**dong_x("1000000000000000002", "2026-10-13T16:00:00Z"), "trang_thai": "that_bai"}]
        ma, cong = self.chay_x(dong, lambda mt, u, kw: tra_fx(u.rsplit("/", 1)[1]))
        self.assertEqual(self.x_rows(cong), [])
        self.assertEqual(self.m.dem("GET", "api.fxtwitter.com"), 0)

    def test_doc_so_da_do_loi_thi_loi_kenh_khong_do_bai(self):
        cong = CongDo(DONG_SO + [dong_x("1000000000000000001", "2026-10-13T16:00:00Z")])
        cong.doc_so_lieu_x = lambda: (_ for _ in ()).throw(RuntimeError("db"))
        m = mang_day_du()
        m.them("GET", "api.fxtwitter.com/2/status/", lambda mt, u, kw: tra_fx(u.rsplit("/", 1)[1]))
        ma, cong = self.chay(m, cong)
        self.assertEqual(ma, 1)
        self.assertEqual(m.dem("GET", "api.fxtwitter.com"), 0)
        self.assertEqual(self.x_rows(cong), [])

    def test_views_co_thi_ghi(self):
        ma, cong = self.chay_x([dong_x("1000000000000000001", "2026-10-13T16:00:00Z")],
                               lambda mt, u, kw: tra_fx("1000000000000000001", views=1234))
        self.assertEqual(self.x_rows(cong)[0]["luot_xem"], 1234)

    def test_ban_v1_retweets_van_doc_duoc(self):
        def fx(mt, u, kw):
            r = tra_fx("1000000000000000001")
            st = r.json()["status"]
            st.pop("reposts")
            st["retweets"] = 5
            return P(200, {"status": st})
        ma, cong = self.chay_x([dong_x("1000000000000000001", "2026-10-13T16:00:00Z")], fx)
        self.assertEqual(self.x_rows(cong)[0]["chia_se"], 7)

    def test_sai_tai_khoan_hoac_id_khong_ghi_va_khong_chan_kenh_khac(self):
        dong = [dong_x("1000000000000000001", "2026-10-13T16:00:00Z"), dong_x("1000000000000000002", "2026-10-13T16:00:00Z")]

        def fx(mt, u, kw):
            id_x = u.rsplit("/", 1)[1]
            if id_x.endswith("1"):
                return tra_fx(id_x, author={"screen_name": "nguoikhac"})
            return tra_fx("9999")                                     # id khong khop
        ma, cong = self.chay_x(dong, fx)
        self.assertEqual(self.x_rows(cong), [])
        self.assertEqual(ma, 1)                                       # kenh X bao loi (2/2 bai loi)
        self.assertIn("LOI KENH", self.log)
        self.assertEqual(len([b for b in cong.bai_da_ghi() if b["nen_tang"] == "Facebook"]), 3)   # 5 kenh con lai van ghi

    def test_fx_loi_mang_khong_chan_kenh_khac(self):
        ma, cong = self.chay_x([dong_x("1000000000000000001", "2026-10-13T16:00:00Z")], lambda mt, u, kw: P(502))
        self.assertEqual(self.x_rows(cong), [])
        self.assertEqual(len(cong.bai_da_ghi()), 14)

    def test_khong_co_bai_x_thi_khong_goi_fxtwitter(self):
        ma, cong = self.chay_x([], lambda mt, u, kw: P(500))
        self.assertEqual(ma, 0, self.log)
        self.assertEqual(self.m.dem("GET", "api.fxtwitter.com"), 0)
        self.assertIn("X: 0 bai, 0 loi bai", self.log)


if __name__ == "__main__":
    unittest.main()
