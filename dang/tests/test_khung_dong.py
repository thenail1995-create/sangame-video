"""SG-TOP5-hong 30/10: khung da dong trong sg_dang -> dung.yml khong dung (khong Release mo coi)."""
import unittest

from dang import khung_dong, so


class Cong:
    def __init__(self, dong=None, loi=None):
        self.dong, self.loi, self.goi_ = dong or [], loi, []

    def goi(self, viec, **kw):
        self.goi_.append((viec, kw))
        if self.loi:
            raise self.loi
        return {"ok": True, "dong": self.dong}


def D(kenh, tt, ngay="2026-10-29", dang="top5", che_do="that"):
    return dict(ngay=ngay, dang=dang, kenh=kenh, che_do=che_do, trang_thai=tt)


class KhungDong(unittest.TestCase):
    def test_chua_co_dong_la_mo(self):
        c = Cong()
        self.assertEqual(khung_dong.khung_da_dong(c, "2026-10-29", "top5"), (False, []))
        self.assertEqual(c.goi_, [("doc_dang", dict(tu="2026-10-29", den="2026-10-29", che_do="that"))])

    def test_bo_ca_5_kenh_la_dong(self):   # dung ca 29/10
        c = Cong([D(k, "bo") for k in ("fb", "ig", "youtube", "tiktok", "threads")])
        dong, chan = khung_dong.khung_da_dong(c, "2026-10-29", "top5")
        self.assertTrue(dong); self.assertEqual(len(chan), 5); self.assertIn("youtube=bo", chan)

    def test_da_dang_la_dong(self):
        self.assertTrue(khung_dong.khung_da_dong(Cong([D("youtube", "da_dang")]), "2026-10-29", "top5")[0])

    def test_moi_dong_that_bai_la_mo(self):   # dang bu hop le: dong da doi sang that_bai
        self.assertFalse(khung_dong.khung_da_dong(Cong([D("youtube", "that_bai"), D("tiktok", "that_bai")]), "2026-10-29", "top5")[0])

    def test_mot_that_bai_mot_bo_van_dong(self):
        self.assertTrue(khung_dong.khung_da_dong(Cong([D("youtube", "that_bai"), D("tiktok", "bo")]), "2026-10-29", "top5")[0])

    def test_dong_cua_dang_khac_hoac_ngay_khac_khong_tinh(self):
        c = Cong([D("youtube", "da_dang", dang="flagship"), D("youtube", "bo", ngay="2026-10-28"), D("youtube", "bo", che_do="thu")])
        self.assertFalse(khung_dong.khung_da_dong(c, "2026-10-29", "top5")[0])

    def test_main_loi_cong_coi_la_mo(self):
        import io, contextlib
        goc = so.Cong
        so.Cong = lambda: Cong(loi=so.LoiCong("cong doc_dang: HTTP 500"))
        try:
            o = io.StringIO()
            with contextlib.redirect_stdout(o):
                self.assertEqual(khung_dong.main(["--ngay", "2026-10-29", "--dang", "top5"]), 0)
            self.assertIn("dong=0", o.getvalue())
        finally:
            so.Cong = goc

    def test_main_dong_in_dong_1(self):
        import io, contextlib
        goc = so.Cong
        so.Cong = lambda: Cong([D("youtube", "bo")])
        try:
            o = io.StringIO()
            with contextlib.redirect_stdout(o):
                khung_dong.main(["--ngay", "2026-10-29", "--dang", "top5"])
            self.assertIn("dong=1", o.getvalue())
        finally:
            so.Cong = goc


if __name__ == "__main__":
    unittest.main()
