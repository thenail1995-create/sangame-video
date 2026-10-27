"""Bai X goc (dang/x_goc.py): mock toan bo mang + chup trang, khong ngu that, khong Buffer/Zernio that."""
import contextlib
import datetime as dt
import io
import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from dang import chung, http, ntfy, so, x, x_goc, zernio
from dang.tests.gia_lap import CongGia, Mang, P

NGAY = dt.date(2026, 10, 28)       # = SG_X_GOC_NGAY_1 -> ngay 1 (le) -> khung sang 10:00
NGAY_1 = NGAY
DUE = dt.datetime(2026, 10, 28, 10, 0, tzinfo=chung.VN)
BK, ZK = "bk_LIVE_BIMAT_1234567890abcdef", "zk_LIVE_BIMAT_1234567890abcdef"
URL_ANH = "https://cdn.zernio.test/media/BIMAT-ANH-12345.png"
URL_UP = "https://up.zernio.test/put?sig=BIMATUPLOAD12345"
SENT_AT = "2026-10-28T03:00:30.000Z"       # 10:00:30 VN
LINK_PS = "https://store.playstation.com/en-us/product/UP0082-CUSA00107_00-000000TOMBRAIDER"
HAN = "2026-11-05T07:59:00+00:00"


def hang(**kw):
    h = {"ngay": "2026-10-28", "hang": 1, "ma": "UP0082-CUSA00107_00-000000TOMBRAIDER", "ten": "Tomb Raider: Definitive Edition",
         "vung_re_nhat": "US", "gia_vnd": 72000, "gia_goc_vnd": 560000, "giam": 90, "han": HAN,
         "meo": [{"loai": "vua_khit", "can_kiem": False, "chu": "2 thẻ 1 USD (72.000đ) là vừa khít, dư $0,01"}],
         "link": LINK_PS, "lech_gia": False, "da_kiem_trang": True,
         "gia_vung": {"US": {"vnd": 72000, "mua_duoc": True, "giam": 90, "tien": "USD", "gia": "$1.99", "cach": "the", "chi_plus": False}}}
    h.update(kw)
    return h


def kq_chup(**kw):
    k = {"tieu_de": "Tomb Raider: Definitive Edition", "gia_hien": "$1.99", "gia_goc": "$19.99", "han_chu": "Offer ends 11/5/2026 02:59 PM GMT+7",
         "giam_chu": "Save 90%", "so_khoi": 1, "url_cuoi": LINK_PS, "rong": 978, "cao": 800}
    k.update(kw)
    return k


class CongXG(CongGia):
    """CongGia + doc_keo + nhat ky thu tu su kien chung voi mang."""

    def __init__(self, keo=None, su_kien=None):
        super().__init__()
        self.keo = keo if keo is not None else [hang()]
        self.su_kien = su_kien if su_kien is not None else []

    def doc_keo(self, ngay):
        return [dict(h) for h in self.keo]

    def giu_dang(self, *a, **k):
        self.su_kien.append("giu_dang")
        return super().giu_dang(*a, **k)


def chup_gia(kq=None):
    def f(url, duong):
        pathlib.Path(duong).write_bytes(b"\x89PNG-GIA")
        return kq if kq is not None else kq_chup()
    return f


def gia_the_file(thu_muc, ngay="2026-10-27", khoa="cap_nhat", vung=None):
    p = pathlib.Path(thu_muc) / "gia-the.json"
    p.write_text(json.dumps({khoa: ngay, "vung": vung if vung is not None else {"US": {"tien": "USD"}, "HK": {"tien": "HKD"}}}))
    return str(p)


class DungChu(unittest.TestCase):
    def test_chu_hop_le(self):
        for d in range(9):
            ng = NGAY + dt.timedelta(days=d)
            text, dong1, ma = x_goc.dung_chu(hang(), ng, NGAY_1, set())
            self.assertLessEqual(x.do_dai_x(dong1), 60)
            self.assertTrue(150 <= x.do_dai_x(text) <= 260, x.do_dai_x(text))
            self.assertNotIn("#", text)
            self.assertIsNone(x._URL.search(text))
            self.assertFalse(dong1.startswith("Săn Game"))
            self.assertTrue(text.startswith("Tomb Raider: Definitive Edition giảm 90%, còn 72 nghìn\n\n"))
            self.assertIn("14:59 ngày 5/11 (giờ VN)", text)
            self.assertIn("560 nghìn", text)

    def test_9_to_hop_khong_lap_trong_7_ngay(self):
        cap = [x_goc.chon_to_hop(NGAY + dt.timedelta(days=d), NGAY_1) for d in range(30)]
        for i in range(len(cap) - 6):
            self.assertEqual(len(set(cap[i:i + 7])), 7)

    def test_ten_khong_cat_sau_hai_cham(self):
        # Miles Morales la san pham khac Spider-Man: bo duoi "Ultimate Edition" van 61 > 60 -> bo game, KHONG cat thanh "Marvel's Spider-Man"
        h = hang(ten="Marvel's Spider-Man: Miles Morales Ultimate Edition (English, Korean)", giam=75, gia_vnd=1048000)
        self.assertIsNone(x_goc.ten_ngan(h["ten"], 75, 1048000))
        self.assertIsNone(x_goc.dung_chu(h, NGAY, NGAY_1, set()))

    def test_chi_bo_duoi_edition_chuan_khi_can(self):
        self.assertEqual(x_goc.ten_ngan("Horizon Zero Dawn Complete Edition", 75, 72000), "Horizon Zero Dawn Complete Edition")
        self.assertEqual(x_goc.ten_ngan("Horizon Forbidden West Complete Edition", 75, 1048000), "Horizon Forbidden West")
        self.assertEqual(x_goc.ten_ngan("Tomb Raider: Definitive Edition (English, Korean)", 90, 72000), "Tomb Raider: Definitive Edition")   # du 60 thi giu
        self.assertIsNone(x_goc.ten_ngan("Ghost of Tsushima: Director's Cut Remastered", 75, 1048000))    # Remastered giu, khong cat
        self.assertIsNone(x_goc.ten_ngan("Marvel's Guardians of the Galaxy: Mot Phan Rat Dai Deluxe Xyz", 75, 1048000))

    def test_ten_qua_dai_khong_dung_duoc_thi_none(self):
        self.assertIsNone(x_goc.dung_chu(hang(ten="A" * 80), NGAY, NGAY_1, set()))

    def test_lap_dong_1_trong_7_ngay_bi_loai(self):
        text, dong1, _ = x_goc.dung_chu(hang(), NGAY, NGAY_1, set())
        self.assertIsNone(x_goc.dung_chu(hang(), NGAY, NGAY_1, {x_goc.sha_dong1(dong1)}))

    def test_to_hop_da_dung_trong_7_ngay_bi_loai_va_het_to_hop_thi_bo_game(self):
        _, _, ma0 = x_goc.dung_chu(hang(), NGAY, NGAY_1, set())
        self.assertEqual(ma0, "k0-t0")
        _, _, ma1 = x_goc.dung_chu(hang(), NGAY, NGAY_1, set(), {"k0-t0"})
        self.assertNotEqual(ma1, "k0-t0")
        tat_ca = {f"k{k}-t{c}" for k in range(3) for c in range(3)}
        self.assertIsNone(x_goc.dung_chu(hang(), NGAY, NGAY_1, set(), tat_ca))
        # con dung 1 to hop thi dung dung no
        con = tat_ca - {"k2-t1"}
        self.assertEqual(x_goc.dung_chu(hang(), NGAY, NGAY_1, set(), con)[2], "k2-t1")

    def test_nghin(self):
        self.assertEqual(x_goc._nghin(72000), "72 nghìn")
        self.assertEqual(x_goc._nghin(72480), "72,5 nghìn")
        self.assertEqual(x_goc._nghin(1_048_000), "1,05 triệu")

    def test_meo_the_nap_viet_thuong_chu_dau(self):
        h = hang(meo=[{"loai": "the_nap", "can_kiem": False, "chu": "Nạp 3 thẻ 10 USD = 78.000đ, dư $1 trong ví"}])
        text, _, _ = x_goc.dung_chu(h, NGAY, NGAY_1, set())
        self.assertIn("nạp 3 thẻ 10 USD", text)

    def test_alt(self):
        alt = x_goc.tao_alt(hang(), "$1.99", NGAY)
        self.assertEqual(alt, "Tomb Raider: Definitive Edition trên PS Store Mỹ: $1.99 (giảm 90%), chụp 28/10/2026. Giá niêm yết, chưa gồm thuế nếu có.")
        self.assertLessEqual(len(x_goc.tao_alt(hang(ten="B" * 2000), "$1.99", NGAY)), 1000)


class ChonGame(unittest.TestCase):
    def ds(self, hs, ma_da=(), vung_the=("US", "HK")):
        return [h["hang"] for h in x_goc.ung_vien(hs, "2026-10-28", DUE, set(ma_da), set(vung_the))]

    def test_hop_le_theo_hang_tang_dan(self):
        self.assertEqual(self.ds([hang(hang=3, ma="C"), hang(hang=1, ma="A"), hang(hang=2, ma="B")]), [1, 2, 3])

    def test_loai(self):
        hs = [hang(hang=1, ma="A", da_kiem_trang=False), hang(hang=2, ma="B", lech_gia=True),
              hang(hang=3, ma="C", han=(DUE + dt.timedelta(hours=23)).isoformat()),
              hang(hang=4, ma="D", meo=[{"loai": "vua_khit", "can_kiem": True, "chu": "x"}]),
              hang(hang=5, ma="E", meo=[{"loai": "thap_nhat", "can_kiem": False, "chu": "x"}]),
              hang(hang=6, ma="F", gia_vung={"US": {"vnd": 1, "mua_duoc": True, "tien": "USD", "gia": "$1", "chi_plus": True}}),
              hang(hang=7, ma="G", link="https://example.com/x"),
              hang(hang=8, ma="H", vung_re_nhat="IN"),
              hang(hang=9, ma="TRUNG"),
              hang(hang=10, ma="I", ngay="2026-10-27"), hang(hang=12, ma="J", ngay=None), hang(hang=13, ma="K", ngay=""),
              hang(hang=11, ma="OK")]
        self.assertEqual(self.ds(hs, ma_da=["TRUNG"]), [11])

    def test_han_dung_24h_van_nhan(self):
        self.assertEqual(self.ds([hang(han=(DUE + dt.timedelta(hours=24)).isoformat())]), [1])

    def test_khong_co_du_lieu_vung_cua_game_thi_rong(self):
        self.assertEqual(self.ds([hang()], vung_the=()), [])
        self.assertEqual(self.ds([hang()], vung_the=("HK",)), [])

    def test_da_dung_gan_day(self):
        rows = [dict(kenh="x", dang="x-goc", trang_thai="da_dang", id_tai="A", manifest_sha="s1"),
                dict(kenh="x", dang="x-goc", trang_thai="that_bai", id_tai="B", manifest_sha="s2"),
                dict(kenh="x", dang="x-goc", trang_thai="khong_ro", id_tai="C", manifest_sha="s3"),
                dict(kenh="x", dang="tin-nhanh", trang_thai="da_dang", id_tai="D", manifest_sha="s4"),
                dict(kenh="fb", dang="x-goc", trang_thai="da_dang", id_tai="E", manifest_sha="s5")]
        self.assertEqual(x_goc.da_dung_gan_day(rows), ({"A", "C"}, {"s1", "s3"}, set()))
        rows[0]["id_container"], rows[1]["id_container"], rows[2]["id_container"] = "k0-t0", "k1-t1", "k2-t2"
        self.assertEqual(x_goc.da_dung_gan_day(rows)[2], {"k0-t0", "k2-t2"})   # that_bai khong tinh


class GiaThe(unittest.TestCase):
    def test_han_va_vung(self):
        with tempfile.TemporaryDirectory() as d:
            for ngay, dung in (("2026-10-27", {"US", "HK"}), ("2026-10-21", {"US", "HK"}), ("2026-10-20", set())):
                self.assertEqual(x_goc.vung_co_gia_the(gia_the_file(d, ngay), NGAY), dung, ngay)
            self.assertEqual(x_goc.vung_co_gia_the(gia_the_file(d, "2026-10-27", "ngay"), NGAY), {"US", "HK"})   # file that chi co `ngay`
            self.assertEqual(x_goc.vung_co_gia_the(pathlib.Path(d) / "khong-co.json", NGAY), set())
            (pathlib.Path(d) / "hong.json").write_text("{")
            self.assertEqual(x_goc.vung_co_gia_the(pathlib.Path(d) / "hong.json", NGAY), set())

    def test_du_lieu_vung_rong_hoac_thieu_khong_dung_duoc(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(x_goc.vung_co_gia_the(gia_the_file(d, vung={}), NGAY), set())
            self.assertEqual(x_goc.vung_co_gia_the(gia_the_file(d, vung={"US": {}, "HK": None, "SG": {"tien": "SGD"}}), NGAY), {"SG"})
            (pathlib.Path(d) / "khong-vung.json").write_text(json.dumps({"ngay": "2026-10-27"}))
            self.assertEqual(x_goc.vung_co_gia_the(pathlib.Path(d) / "khong-vung.json", NGAY), set())


class KiemTrang(unittest.TestCase):
    def sai(self, kq=None, **kw):
        with self.assertRaises(x_goc.KhongDang) as cm:
            x_goc.kiem_trang(hang(**kw), kq if kq is not None else kq_chup())
        return str(cm.exception)

    def test_dat(self):
        x_goc.kiem_trang(hang(), kq_chup())
        x_goc.kiem_trang(hang(ten="Tomb Raider™: Definitive  Edition"), kq_chup(tieu_de="TOMB RAIDER: Definitive Edition"))

    def test_url_cuoi_khac_vung_hoac_id(self):
        self.assertIn("khac vung", self.sai(kq_chup(url_cuoi=LINK_PS.replace("en-us", "en-hk"))))
        self.assertIn("khac vung", self.sai(kq_chup(url_cuoi=LINK_PS.replace("TOMBRAIDER", "KHACGAME"))))
        self.assertIn("khong phai vung", self.sai(link=LINK_PS.replace("en-us", "en-hk")))

    def test_tieu_de_ca_chuoi(self):
        self.assertIn("tieu de", self.sai(kq_chup(tieu_de="Tomb Raider")))

    def test_gia(self):
        self.assertIn("gia", self.sai(kq_chup(gia_hien="$2.99")))
        self.assertIn("tien te", self.sai(kq_chup(gia_hien="HK$1.99")))
        self.assertIn("gia", self.sai(kq_chup(gia_hien=None)))

    def test_gia_vung_khac_tien_te(self):
        h = hang(vung_re_nhat="HK", link=LINK_PS.replace("en-us", "en-hk"),
                 gia_vung={"HK": {"vnd": 72000, "mua_duoc": True, "tien": "HKD", "gia": "HK$362.60", "chi_plus": False}})
        x_goc.kiem_trang(h, kq_chup(gia_hien="HK$362.60", gia_goc="HK$3,626.00", url_cuoi=h["link"]))
        with self.assertRaises(x_goc.KhongDang):
            x_goc.kiem_trang(h, kq_chup(gia_hien="$362.60", url_cuoi=h["link"]))

    def test_han(self):
        self.assertIn("han", self.sai(kq_chup(han_chu="Offer ends 11/5/2026 03:05 PM GMT+7")))
        self.assertIn("han", self.sai(kq_chup(han_chu=None)))
        x_goc.kiem_trang(hang(), kq_chup(han_chu="Offer ends 11/5/2026 02:59:30 PM GMT+7".replace(":30", "")))

    def test_nhat_quan_gia_giam_va_khoi(self):
        self.assertIn("nhieu hon 1 khoi", self.sai(kq_chup(so_khoi=2)))
        self.assertIn("nhieu hon 1 khoi", self.sai(kq_chup(so_khoi=None)))
        self.assertIn("gia VND", self.sai(gia_vung={"US": {"vnd": 99000, "mua_duoc": True, "giam": 90, "tien": "USD", "gia": "$1.99", "chi_plus": False}}))
        self.assertIn("giam trong gia_vung", self.sai(gia_vung={"US": {"vnd": 72000, "mua_duoc": True, "giam": 50, "tien": "USD", "gia": "$1.99", "chi_plus": False}}))
        self.assertIn("Save", self.sai(kq_chup(giam_chu=None)))
        self.assertIn("Save", self.sai(kq_chup(gia_goc=None)))
        self.assertIn("giam", self.sai(kq_chup(giam_chu="Save 50%")))
        self.assertIn("giam", self.sai(kq_chup(gia_goc="$3.99")))          # 1.99/3.99 -> giam ~50% khong khop 90%
        x_goc.kiem_trang(hang(), kq_chup(giam_chu="Save 89%"))             # +-1 chap nhan

    def test_anh_nho(self):
        self.assertIn("nho", self.sai(kq_chup(rong=399)))
        self.assertIn("nho", self.sai(kq_chup(cao=299)))

    def test_so_tien_va_han(self):
        self.assertEqual([x_goc._so_tien(s) for s in ("$1.99", "HK$362.60", "THB 1,323.00", "Rp 224,941", "SGD60.13")],
                         [1.99, 362.6, 1323.0, 224941.0, 60.13])
        self.assertEqual(x_goc._han_chu_ra_utc("Offer ends 11/5/2026 02:59 PM GMT+7"), dt.datetime(2026, 11, 5, 7, 59, tzinfo=dt.timezone.utc))
        self.assertEqual(x_goc._han_chu_ra_utc("Offer ends 12/1/2026 12:00 AM GMT"), dt.datetime(2026, 12, 1, 0, 0, tzinfo=dt.timezone.utc))
        self.assertIsNone(x_goc._han_chu_ra_utc("hom nay"))


def mang_dang(su_kien, poll=None):
    """Mang gia: Zernio presign/PUT/GET anh + Buffer createPost/post()."""
    m = Mang()
    m.them("POST", "zernio.com/api/v1/media/presign",
           lambda mt, u, kw: (su_kien.append("presign"), P(200, {"uploadUrl": URL_UP, "publicUrl": URL_ANH}))[1])
    m.them("PUT", "up.zernio.test", lambda mt, u, kw: (su_kien.append("put"), P(200))[1])
    m.them("GET", "cdn.zernio.test", P(200, headers={"content-type": "image/png"}, raw=b"PNG"))
    pl = poll if poll is not None else [P(200, {"data": {"post": {"id": "BP1", "status": "scheduled", "externalLink": None}}}),
                                        P(200, {"data": {"post": {"id": "BP1", "status": "sent", "externalLink": "https://x.com/sangamecomvn/status/1234567890123", "sentAt": SENT_AT}}})]

    def buffer(mt, u, kw):
        q = kw["json_body"]["query"]
        if "createPost" in q:
            su_kien.append("createPost")
            return P(200, {"data": {"createPost": {"__typename": "PostActionSuccess", "post": {"id": "BP1", "status": "scheduled"}}}})
        su_kien.append("poll")
        return pl.pop(0) if len(pl) > 1 else pl[0]
    m.them("POST", "api.buffer.com", buffer)
    return m


class Luong(unittest.TestCase):
    def setUp(self):
        self.su_kien, self.ntfy, self.tin, self.ngu = [], [], [], []
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.gia_the = gia_the_file(self.tmp.name)
        self.bay_gio = dt.datetime(2026, 10, 28, 9, 40, tzinfo=chung.VN)
        for p in (mock.patch.dict(os.environ, {"BUFFER_KHOA": BK, "ZERNIO_KHOA": ZK, "SG_CONG_KHOA": "kh_cong_1234567890", "SG_X_GOC_NGAY_1": "2026-10-28"}),
                  mock.patch.object(chung, "bay_gio", lambda: self.bay_gio),
                  mock.patch.object(chung, "ngu", lambda s: self.ngu.append(s)),
                  mock.patch.object(ntfy, "loi", lambda *a, **k: self.ntfy.append(a)),
                  mock.patch.object(ntfy, "tin", lambda *a, **k: self.tin.append(a))):
            p.start()
            self.addCleanup(p.stop)
        os.environ.pop("BUFFER_X_KENH", None)
        os.environ.pop("DA_BAO_FILE", None)

    def args(self, che_do="that", khung="sang", ngay="2026-10-28"):
        return mock.Mock(ngay=ngay, che_do=che_do, khung=khung, gia_the=self.gia_the)

    def chay(self, che_do="that", cong=None, m=None, kq=None, khung="sang", ngay="2026-10-28", chup=None):
        cong = cong or CongXG(su_kien=self.su_kien)
        m = m or mang_dang(self.su_kien)
        buf = io.StringIO()
        with mock.patch.object(http, "gui", m), contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            ma = x_goc.chay(self.args(che_do, khung, ngay), cong, chup or chup_gia(kq))
        self.log = buf.getvalue()
        self.m, self.cong = m, cong
        return ma

    def dong(self, cong=None, che_do="that"):
        return (cong or self.cong).dong[("2026-10-28", "x-goc", "x", che_do)]

    def test_that_thanh_cong_dung_thu_tu(self):
        self.assertEqual(self.chay(), 0)
        self.assertEqual(self.su_kien, ["giu_dang", "presign", "put", "createPost", "poll", "poll"])   # giu quyen TRUOC moi goi mang
        d = self.dong()
        self.assertEqual((d["trang_thai"], d["id_bai"], d["link"], d["id_tai"]),
                         ("da_dang", "BP1", "https://x.com/sangamecomvn/status/1234567890123", hang()["ma"]))
        self.assertEqual(d["manifest_sha"], x_goc.sha_dong1("Tomb Raider: Definitive Edition giảm 90%, còn 72 nghìn"))
        self.assertEqual(d["gio_cong_khai"], "2026-10-28T03:00:30Z")     # = sentAt cua Buffer
        self.assertEqual(d["id_container"], "k0-t0")
        # Buffer: anh + ALT dung truong schema that, hen 10:00 VN = 03:00Z
        q = [kw["json_body"]["query"] for mt, u, kw in self.m.goi if "api.buffer.com" in u and "createPost" in kw["json_body"]["query"]]
        self.assertEqual(len(q), 1)
        for mau in ("mode: customScheduled", "schedulingType: automatic", 'dueAt: "2026-10-28T03:00:00Z"',
                    'assets: [{image: {url: "%s", metadata: {altText: "Tomb Raider: Definitive Edition trên PS Store Mỹ: $1.99' % URL_ANH,
                    'channelId: "6acca131778b240e2fe466f3"'):
            self.assertIn(mau, q[0])
        self.assertNotIn("video", q[0])
        # id_bai ghi NGAY sau createPost, truoc khi poll
        ghi = [t for k, t in self.cong.cap_nhat if k == "x"]
        self.assertEqual(ghi[0], {"id_tai": hang()["ma"], "id_container": "k0-t0"})
        self.assertEqual(ghi[1], {"id_bai": "BP1"})
        self.assertEqual(self.tin[0][0], "Đã đăng bài X gốc")
        self.assertEqual(self.ntfy, [])

    def test_khong_ro_url_anh_va_khoa_khong_vao_log(self):
        self.chay()
        for bi_mat in (URL_ANH, URL_UP, BK, ZK):
            self.assertNotIn(bi_mat, self.log + str(self.cong.dong))
        with mock.patch.object(chung, "bay_gio", lambda: self.bay_gio), contextlib.redirect_stdout(io.StringIO()) as b:
            chung.log(f"thu {URL_ANH} {URL_UP}")
        self.assertNotIn("BIMAT", b.getvalue())

    def test_thu_khong_goi_buffer_khong_upload(self):
        m = Mang()                                           # khong co luat nao: goi mang = AssertionError
        self.assertEqual(self.chay("thu", m=m), 0)
        self.assertEqual(m.goi, [])
        self.assertEqual(self.su_kien, ["giu_dang"])
        self.assertIn("ALT", self.log)
        self.assertIn("Tomb Raider: Definitive Edition giảm 90%", self.log)
        self.assertEqual(self.dong(che_do="thu")["trang_thai"], "that_bai")   # cho phep chay thu lai
        self.assertEqual(self.chay("thu", cong=self.cong, m=Mang()), 0)       # chay thu lai duoc

    def test_khong_con_game_thi_thoat_3_va_ntfy(self):
        self.assertEqual(self.chay(cong=CongXG([hang(da_kiem_trang=False)], self.su_kien), m=Mang()), 3)
        self.assertEqual(self.su_kien, [])
        self.assertEqual(len(self.ntfy), 1)

    def test_gia_the_cu_thi_dung(self):
        self.gia_the = gia_the_file(self.tmp.name, "2026-10-01")
        self.assertEqual(self.chay(m=Mang()), 3)
        self.assertEqual(self.su_kien, [])

    def test_trang_ps_sai_thi_khong_giu_quyen_khong_dang(self):
        self.assertEqual(self.chay(m=Mang(), kq=kq_chup(gia_hien="$9.99")), 3)
        self.assertEqual(self.su_kien, [])
        self.assertEqual(len(self.ntfy), 1)

    def test_qua_gio_len_lich(self):
        self.bay_gio = dt.datetime(2026, 10, 28, 9, 59, tzinfo=chung.VN)
        self.assertEqual(self.chay(m=Mang()), 3)
        self.assertEqual(self.su_kien, [])
        self.assertIn("qua gio", self.ntfy[0][0])
        self.bay_gio = dt.datetime(2026, 10, 28, 9, 57, tzinfo=chung.VN)
        self.assertEqual(self.chay(), 0)

    def test_het_gio_trong_luc_chup_thi_dung_truoc_giu_quyen(self):
        def chup(url, duong):
            self.bay_gio = dt.datetime(2026, 10, 28, 9, 59, tzinfo=chung.VN)
            return chup_gia()(url, duong)
        # chup xong qua 09:58 nhung chuan_bi khong kiem -> giu quyen roi KIEM LAI TRUOC upload
        self.assertEqual(self.chay(chup=chup), 3)
        self.assertNotIn("presign", self.su_kien)
        self.assertNotIn("createPost", self.su_kien)
        self.assertEqual(self.dong()["trang_thai"], "that_bai")
        self.assertEqual(len(self.ntfy), 1)

    def test_het_gio_giua_upload_va_createpost(self):
        m = mang_dang(self.su_kien)

        def presign(mt, u, kw):
            self.su_kien.append("presign")
            self.bay_gio = dt.datetime(2026, 10, 28, 9, 58, 30, tzinfo=chung.VN)   # upload cham: con 1,5 phut
            return P(200, {"uploadUrl": URL_UP, "publicUrl": URL_ANH})
        m.luat[0][2] = presign
        self.assertEqual(self.chay(m=m), 3)
        self.assertIn("presign", self.su_kien)
        self.assertNotIn("createPost", self.su_kien)
        self.assertEqual(self.dong()["trang_thai"], "that_bai")

    def test_khung_khong_khop_ngay_thoat_0_khong_giu_quyen(self):
        m = Mang()
        self.assertEqual(self.chay(khung="toi", m=m), 0)           # ngay 1 (le) la khung sang
        self.assertIn("không phải khung hôm nay", self.log)
        self.assertEqual(self.su_kien, [])
        self.assertEqual(m.goi, [])
        self.assertEqual(self.chay(khung="sang", ngay="2026-10-29", m=m), 0)   # ngay 2 (chan) la khung toi
        self.assertEqual(self.su_kien, [])

    def test_khung_toi_ngay_chan_dang_20h(self):
        self.bay_gio = dt.datetime(2026, 10, 29, 19, 40, tzinfo=chung.VN)
        cong = CongXG([hang(ngay="2026-10-29")], self.su_kien)
        self.assertEqual(self.chay(khung="toi", ngay="2026-10-29", cong=cong), 0)
        q = [kw["json_body"]["query"] for mt, u, kw in self.m.goi if "api.buffer.com" in u and "createPost" in kw["json_body"]["query"]][0]
        self.assertIn('dueAt: "2026-10-29T13:00:00Z"', q)                      # 20:00 VN
        self.assertEqual(self.cong.dong[("2026-10-29", "x-goc", "x", "that")]["id_container"], "k1-t0")

    def test_thieu_hoac_sai_ngay_1_thoat_2(self):
        for v in ("", "28/10", "2026-13-01"):
            with mock.patch.dict(os.environ, {"SG_X_GOC_NGAY_1": v}):
                self.assertEqual(self.chay(m=Mang()), 2)
        self.assertEqual(self.su_kien, [])

    def test_to_hop_dung_7_ngay_truoc_bi_loai_chon_to_hop_chua_dung(self):
        cong = CongXG(su_kien=self.su_kien)
        da = [f"k{k}-t{c}" for k in range(3) for c in range(3)][:7]          # 7 ngay 21-27/10 da dung 7 to hop (k0-t0 .. k0-t2... )
        for i, ma in enumerate(da):
            ngay = (NGAY - dt.timedelta(days=7 - i)).isoformat()
            cong.dong[(ngay, "x-goc", "x", "that")] = dict(ngay=ngay, dang="x-goc", kenh="x", che_do="that", trang_thai="da_dang",
                                                          id_tai=f"M{i}", id_container=ma)
        self.assertEqual(self.chay(cong=cong), 0, self.log)
        dung = self.dong(cong)["id_container"]
        self.assertNotIn(dung, da)
        self.assertEqual(dung, "k2-t1")

    def test_thieu_khoa_that(self):
        with mock.patch.dict(os.environ, {"BUFFER_KHOA": ""}):
            self.assertEqual(self.chay(m=Mang()), 2)

    def test_da_co_dong_hom_nay_thi_khong_dang(self):
        cong = CongXG(su_kien=self.su_kien)
        cong.dong[("2026-10-28", "x-goc", "x", "that")] = dict(ngay="2026-10-28", dang="x-goc", kenh="x", che_do="that", trang_thai="da_dang")
        self.assertEqual(self.chay(cong=cong, m=Mang()), 3)

    def test_buffer_het_gio_cho_khong_ro_khong_dang_lai(self):
        m = mang_dang(self.su_kien, poll=[P(200, {"data": {"post": {"id": "BP1", "status": "scheduled"}}})])
        self.assertEqual(self.chay(m=m), 1)
        self.assertEqual(self.dong()["trang_thai"], "khong_ro")
        self.assertEqual(self.dong()["id_bai"], "BP1")
        self.assertEqual(self.su_kien.count("createPost"), 1)
        # 09:40 -> han 10:15 chua 60 s = 2040 s = 136 lan hoi (15 s)
        self.assertEqual(self.su_kien.count("poll"), 136)

    def test_buffer_bai_loi_la_that_bai(self):
        m = mang_dang(self.su_kien, poll=[P(200, {"data": {"post": {"id": "BP1", "status": "error", "error": {"message": "bi tu choi"}}}})])
        self.assertEqual(self.chay(m=m), 1)
        self.assertEqual(self.dong()["trang_thai"], "that_bai")

    def test_anh_upload_hong_la_that_bai_chua_tao_bai(self):
        m = mang_dang(self.su_kien)
        m.luat[1][2] = P(500)           # PUT loi
        self.assertEqual(self.chay(m=m), 1)
        self.assertEqual(self.dong()["trang_thai"], "that_bai")
        self.assertNotIn("createPost", self.su_kien)

    def test_url_anh_khong_phai_png(self):
        m = mang_dang(self.su_kien)
        m.luat[2][2] = P(200, headers={"content-type": "text/html"}, raw=b"x")
        self.assertEqual(self.chay(m=m), 1)
        self.assertNotIn("createPost", self.su_kien)

    def test_ngoai_le_la_sau_khi_gui_mutation_la_khong_ro(self):
        with mock.patch.object(x, "tao_bai_anh", side_effect=RuntimeError("boom")):
            self.assertEqual(self.chay(), 1)
        self.assertEqual(self.dong()["trang_thai"], "khong_ro")
        self.assertEqual(self.chay(cong=self.cong, m=Mang()), 3)           # khong dang lai
        self.assertEqual(self.su_kien.count("createPost"), 0)              # (mock thay createPost; luot 2 khong goi mang)

    def test_loi_truoc_moc_gui_la_that_bai(self):
        with mock.patch.object(zernio, "tai_anh", side_effect=RuntimeError("boom")):
            self.assertEqual(self.chay(), 1)
        self.assertEqual(self.dong()["trang_thai"], "that_bai")

    def test_ghi_da_dang_cuoi_loi_thi_bao_va_khong_dang_lai(self):
        cong = CongXG(su_kien=self.su_kien)
        cong.hong_ghi_sau = lambda kenh, truong: truong.get("trang_thai") == "da_dang"
        self.assertEqual(self.chay(cong=cong), 1)
        self.assertIn("ĐÃ đăng nhưng ghi sổ lỗi", self.ntfy[0][0])
        self.assertIn("BP1", self.ntfy[0][1])
        self.assertEqual(self.dong(cong)["trang_thai"], "dang_dang")        # dong giu quyen con nguyen
        self.assertEqual(self.dong(cong)["id_bai"], "BP1")
        cong.hong_ghi_sau = None
        m2 = Mang()
        self.assertEqual(self.chay(cong=cong, m=m2), 3)                     # luot sau KHONG dang lai
        self.assertEqual(m2.goi, [])
        self.assertEqual(self.su_kien.count("createPost"), 1)

    def test_ghi_id_bai_loi_thi_bao_thoat_1_nhung_van_ghi_da_dang(self):
        cong = CongXG(su_kien=self.su_kien)
        cong.hong_ghi_sau = lambda kenh, truong: "id_bai" in truong and "trang_thai" not in truong
        self.assertEqual(self.chay(cong=cong), 1)
        self.assertEqual(self.dong(cong)["trang_thai"], "da_dang")
        self.assertTrue(any("id_bai" in n[0] for n in self.ntfy))

    def test_sent_thieu_link_hoi_them_va_dung_sentat(self):
        sent = lambda link: P(200, {"data": {"post": {"id": "BP1", "status": "sent", "externalLink": link, "sentAt": SENT_AT}}})
        m = mang_dang(self.su_kien, poll=[sent(None), sent("https://x.com/sangamecomvn/status/777777777777")])
        self.assertEqual(self.chay(m=m), 0)
        self.assertEqual(self.dong()["link"], "https://x.com/sangamecomvn/status/777777777777")
        self.assertEqual(self.ntfy, [])

    def test_sent_van_thieu_link_sau_2_phut_ghi_da_dang_khong_link_va_bao(self):
        m = mang_dang(self.su_kien, poll=[P(200, {"data": {"post": {"id": "BP1", "status": "sent", "externalLink": None, "sentAt": SENT_AT}}})])
        self.assertEqual(self.chay(m=m), 0)
        d = self.dong()
        self.assertEqual((d["trang_thai"], d["link"], d["gio_cong_khai"]), ("da_dang", None, "2026-10-28T03:00:30Z"))
        self.assertEqual(self.su_kien.count("poll"), 1 + 8)                 # 1 lan hoi chinh + 8 x 15 s = 2 phut
        self.assertEqual(len(self.ntfy), 1)

    def test_khong_co_ham_thich_tra_loi(self):
        self.assertEqual([n for n in dir(x_goc) if any(t in n.lower() for t in ("like", "reply", "retweet", "favorite", "follow"))], [])

    def test_da_bao_file(self):
        f = pathlib.Path(self.tmp.name) / "da-bao"
        with mock.patch.dict(os.environ, {"DA_BAO_FILE": str(f)}), mock.patch.object(ntfy, "loi", lambda *a, **k: True):
            self.assertEqual(self.chay(cong=CongXG([], self.su_kien), m=Mang()), 3)
        self.assertTrue(f.exists())


class TaiAnhZernio(unittest.TestCase):
    def test_presign_png_va_che_url(self):
        su_kien = []
        m = mang_dang(su_kien)
        with tempfile.TemporaryDirectory() as d, mock.patch.object(http, "gui", m):
            p = pathlib.Path(d) / "a.png"
            p.write_bytes(b"\x89PNG0123")
            self.assertEqual(zernio.tai_anh(ZK, p, "a.png"), URL_ANH)
        body = m.goi[0][2]["json_body"]
        self.assertEqual(body, {"filename": "a.png", "contentType": "image/png", "size": 8})
        self.assertNotIn("BIMAT", chung.che(f"{URL_ANH} {URL_UP}"))

    def test_loi_presign_la_chua_tao_bai(self):
        m = Mang().them("POST", "media/presign", P(403, {}))
        with tempfile.TemporaryDirectory() as d, mock.patch.object(http, "gui", m):
            p = pathlib.Path(d) / "a.png"
            p.write_bytes(b"x")
            with self.assertRaises(chung.LoiDang) as cm:
                zernio.tai_anh(ZK, p, "a.png")
        self.assertFalse(cm.exception.khong_ro)


class HanTuyetDoi(unittest.TestCase):
    def test_han_tuyet_doi_dung_hoi_du_so_lan_con_lai(self):
        m = Mang().them("POST", "api.buffer.com", P(200, {"data": {"post": {"id": "B", "status": "scheduled"}}}))
        gio = [dt.datetime(2026, 10, 28, 10, 0, tzinfo=chung.VN)]
        with mock.patch.object(http, "gui", m), mock.patch.object(chung, "bay_gio", lambda: gio[0]), \
                mock.patch.object(chung, "ngu", lambda s: gio.__setitem__(0, gio[0] + dt.timedelta(seconds=s + 5))):   # moi vong 15 s + 5 s mang
            with self.assertRaises(chung.LoiDang) as cm:
                x.hoi_den_xong(BK, "B", toi_da_giay=3600, han_tuyet_doi=dt.datetime(2026, 10, 28, 10, 1, tzinfo=chung.VN))
        self.assertTrue(cm.exception.khong_ro)
        self.assertEqual(len(m.goi), 3)        # 60 s / 20 s thuc te, khong phai 240 vong


class DocKeo(unittest.TestCase):
    def test_client_goi_viec_doc_keo(self):
        c = so.Cong(khoa="kh_cong_1234567890")
        with mock.patch.object(c, "goi", return_value={"ok": True, "dong": [{"hang": 1}]}) as g:
            self.assertEqual(c.doc_keo("2026-10-28"), [{"hang": 1}])
        g.assert_called_once_with("doc_keo", ngay="2026-10-28")


if __name__ == "__main__":
    unittest.main()
