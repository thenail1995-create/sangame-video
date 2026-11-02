"""Tin gia FB / IG / Threads (dang/tin_gia_chon.py + tin_gia_chu.py + tin_gia_mxh.py): khong mang that, khong ngu that, khong nen tang that.
Du lieu: hang sg_keo ngay 2026-11-02 chep NGUYEN VAN tu edge sg-cong (14 cot cua doc_keo, dang/tests/du_lieu_tin_gia/keo-2026-11-02.json);
trang PS Store dung lai tu chinh o gia cua hang (gia, tien te, giam) + gia tri that rut tu trang that (diem sao, endTime); quy VND = bang tra
sinh bang deal_diem.quy_vnd THAT tren gia-the.json 02/11 (quy-vnd-mau.json) - test nay khong can repo rieng tu.
"""
import contextlib
import copy
import datetime as dt
import io
import json
import os
import pathlib
import tempfile
import types
import unittest
from unittest import mock

from dang import chung, fb, gia, http, ig, meta, ntfy, threads, tin_gia_chon as chon, tin_gia_chu as chu, tin_gia_mxh as mxh, zernio
from dang.gia import gia_trang
from dang.tests.gia_lap import CongGia, Mang, P

DL = pathlib.Path(__file__).resolve().parent / "du_lieu_tin_gia"
NGAY = dt.date(2026, 11, 2)
END_MS = 1793865540000                                   # 2026-11-05 07:59 UTC = 14:59 VN 5/11 (gia tri that tren trang)
DIEM = {"PPSA08666_00": (4.66, 64683), "CUSA05532_00": (4.75, 11893), "PPSA08033_00": (4.25, 19405)}   # that, tu trang PS Store 02/11
GOC = {"PPSA08033_00": "$39.99", "PPSA08666_00": "$49.99", "CUSA05532_00": "$49.99"}            # gia goc that tren trang
ZK = "zk_LIVE_BIMAT_1234567890abcdef"
TOKEN_FB = {"page_id": "PAGE1", "page_token": "EAAFBTOKENGIA1234567890abcdef"}


def gio(kenh, ngay=NGAY):
    return mxh.gio_du_kien(ngay, kenh)


def keo(*hang):
    """Hang sg_keo that (14 cot). Khong tham so = tat ca 25 dong; co tham so = chi cac `hang` do."""
    ds = json.load(open(DL / "keo-2026-11-02.json", encoding="utf-8"))
    return [h for h in ds if not hang or h["hang"] in hang]


def dong_keo(hang):
    return keo(hang)[0]


QUY = json.load(open(DL / "quy-vnd-mau.json", encoding="utf-8"))


def quy_gia(nen_tang, vung, g, tien, gia_the, ty_gia, hom_nay=None):
    """Thay deal_diem.quy_vnd: tra ket qua THAT da tinh san cho tung (vung, gia, tien)."""
    r = QUY.get(f"{vung}|{g:.2f}|{tien}")
    if r is None:
        return {"vnd": None, "cach": None, "the": [], "tong_menh_gia": None, "thua": None, "mua_duoc": False, "ly_do": "khong co trong bang mau"}
    r = dict(r)
    r["the"] = [tuple(t) for t in r["the"]]
    return r


TIEN_TO_TRANG = {"USD": "$", "HKD": "HK$", "SGD": "SGD", "THB": "THB ", "IDR": "Rp "}


def trang_html(pid, con, goc, tien, end_ms=END_MS, diem=None, the_loai=("Action",), shots=3, bia=True):
    """HTML trang san pham toi gian cung cau truc that: khoi GameCTA mua dut cua dung pid + Product:<pid> (media, starRating, genres)."""
    val = lambda s: int(round(gia_trang.doc_gia(s) * 100))
    cache = {f"GameCTA:ADD_TO_CART:ADD_TO_CART:{pid}-U001:OUTRIGHT": {"__typename": "GameCTA", "price": {
        "discountedPrice": con, "basePrice": goc, "discountedValue": val(con), "basePriceValue": val(goc), "currencyCode": tien,
        "endTime": str(end_ms) if end_ms else None}}}
    prod = {"id": pid, "media": ([{"type": "IMAGE", "role": "EDITION_KEY_ART", "url": f"https://img.test/{pid}/bia.jpg"}] if bia else [])
            + [{"type": "IMAGE", "role": "SCREENSHOT", "url": f"https://img.test/{pid}/s{i}.jpg"} for i in range(shots)],
            "localizedGenres": [{"value": g} for g in the_loai]}
    if diem:
        prod["starRating"] = {"averageRating": diem[0], "totalRatingsCount": diem[1]}
    cache[f"Product:{pid}"] = prod
    return '<html><script id="env:a" type="application/json">' + json.dumps({"cache": cache}) + "</script></html>"


class Trang:
    """lay_trang gia: dung trang tu o gia cua hang sg_keo (gia/tien/giam y nguyen). `ghi_de[link]` = html | None | ham(link)."""

    def __init__(self, ds, ghi_de=None, end_ms=END_MS):
        self.o, self.ghi_de, self.end_ms, self.goi = {}, ghi_de if ghi_de is not None else {}, end_ms, []
        for h in ds:
            for ma, o in h["gia_vung"].items():
                if o.get("link"):
                    self.o[o["link"]] = (h, ma, o)
            self.o.setdefault(h["link"], (h, h["vung_re_nhat"], h["gia_vung"][h["vung_re_nhat"]]))

    def __call__(self, link):
        self.goi.append(link)
        if link in self.ghi_de:
            v = self.ghi_de[link]
            return v(link) if callable(v) else v
        return self.dung(link)

    def dung(self, link, **kw):
        """Trang binh thuong cua link, co the ghi de tham so (con=, goc=, tien=, end_ms=, diem=...)."""
        h, ma, o = self.o[link]
        pid = link.rsplit("/", 1)[-1]
        goc_so = gia_trang.doc_gia(o["gia"]) / (1 - (o["giam"] if isinstance(o.get("giam"), int) else h["giam"]) / 100)
        goc = next((v for k, v in GOC.items() if k in pid), f"{TIEN_TO_TRANG[o['tien']]}{goc_so:,.2f}")
        t = dict(con=o["gia"], goc=goc, tien=o["tien"], end_ms=self.end_ms, diem=next((v for k, v in DIEM.items() if k in pid), (4.1, 2000)))
        t.update(kw)
        return trang_html(pid, t.pop("con"), t.pop("goc"), t.pop("tien"), **t)


class NB:
    """Gia NoiBat (da_noi_bat): trung(ten, pids) -> ly do | None."""

    def __init__(self, ten_trung=(), canh_bao=None):
        self.ten_trung, self.canh_bao = tuple(ten_trung), canh_bao

    def trung(self, ten, pids=()):
        return f'ten "{ten}" (v-test)' if any(t.lower() in (ten or "").lower() for t in self.ten_trung) else None


def tai_anh_gia(hong=(), ghi=None):
    ghi = ghi if ghi is not None else []

    def tai(url, nhan):
        ghi.append((url, nhan))
        if any(h in url for h in hong):
            return None
        return nhan + ".jpg"
    return tai


def boi(kenh, ds=None, trang=None, nb=None, da_dung=(), tai_anh=None, quy=quy_gia, ngay=NGAY, **kw):
    ds = keo() if ds is None else ds
    return chon.Boi(kenh, ngay, gio(kenh, ngay), ds, {"ty_gia_ngan_hang": {}, "vung": {"US": {}}}, quy, trang or Trang(ds),
                    tai_anh or tai_anh_gia(), da_dung, nb, **kw)


# ================================================================ tien ich thuan
class TienIch(unittest.TestCase):
    def test_hien_tien(self):
        self.assertEqual([chon.hien_tien(*a) for a in ((4.79, "USD"), (5.0, "USD"), (0.21, "USD"), (73792, "IDR"), (36.96, "HKD"), (6.6, "SGD"))],
                         ["$4,79", "$5", "$0,21", "Rp 73.792", "HK$36,96", "S$6,60"])

    def test_han(self):
        t = dt.datetime.fromtimestamp(END_MS / 1000, dt.timezone.utc)
        self.assertEqual(chon.han_chu(t), "14:59 · 5/11")
        self.assertEqual(chon.han_cau(t), "14:59 ngày 5/11")

    def test_ten_chu(self):
        for vao, ra in (("FINAL FANTASY VII REBIRTH", "Final Fantasy VII Rebirth"), ("FINAL FANTASY TYPE-0 HD", "Final Fantasy Type-0 HD"),
                        ("FINAL FANTASY XV MULTIPLAYER: COMRADES", "Final Fantasy XV Multiplayer: Comrades"),
                        ("Monster Hunter Rise PS4 & PS5", "Monster Hunter Rise"), ("Resident Evil™ 2 Deluxe Edition", "Resident Evil 2 Deluxe Edition"),
                        ("RESIDENT EVIL 7 biohazard Gold Edition", "Resident Evil 7 biohazard Gold Edition"),
                        ("FINAL FANTASY XII THE ZODIAC AGE", "Final Fantasy XII The Zodiac Age"), ("NBA 2K24", "NBA 2K24"),
                        ("FINAL FANTASY XVI COMPLETE EDITION", "Final Fantasy XVI Complete Edition")):
            self.assertEqual(chu.ten_chu(vao), ra, vao)

    def test_ten_chu_ngan(self):
        self.assertEqual(chu.ten_chu_ngan("FINAL FANTASY XVI COMPLETE EDITION"), "Final Fantasy XVI")

    def test_kich_anh(self):
        png = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + (1280).to_bytes(4, "big") + (720).to_bytes(4, "big") + b"\x08\x02\x00\x00\x00"
        self.assertEqual(chon.kich_anh(png), (1280, 720))
        jpg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"\xff\xc0\x00\x11\x08" + (600).to_bytes(2, "big") + (800).to_bytes(2, "big") + b"\x03" * 10
        self.assertEqual(chon.kich_anh(jpg), (800, 600))
        self.assertIsNone(chon.kich_anh(b"not an image"))

    def test_title_ids_va_khoa_ip(self):
        self.assertEqual(chon.title_ids("PPSA08038_00|monster", "https://store.playstation.com/en-us/product/UP0102-PPSA08033_00-FULL"),
                         {"PPSA08038_00", "PPSA08033_00"})
        self.assertEqual(chon.khoa_ip("FINAL FANTASY™ VII"), "final fantasy")
        self.assertEqual(chon.khoa_ip("Resident Evil 2 Deluxe"), "resident evil")

    def test_da_dung_tu_dong(self):
        rows = [dict(dang="x-goc", trang_thai="da_dang", id_tai="PPSA1_00|a"), dict(dang="fb-gia", trang_thai="that_bai", id_tai="B"),
                dict(dang="ig-gia", trang_thai="khong_ro", id_tai="CUSA2_00|b,CUSA3_00|c"), dict(dang="top5", trang_thai="da_dang", id_tai="D"),
                dict(dang="threads-gia", trang_thai="bo", id_tai="E")]
        r = chon.da_dung_tu_dong(rows)
        self.assertEqual(r, {"PPSA1_00|a", "PPSA1_00", "CUSA2_00|b", "CUSA2_00", "CUSA3_00|c", "CUSA3_00"})


# ================================================================ chon FB
class ChonFB(unittest.TestCase):
    def test_chon_mh_rise_5_store_us_re_nhat(self):
        b = boi("fb")
        kq = chon.chon_fb(b)
        self.assertEqual(kq["chon"]["ma"], dong_keo(4)["ma"])
        dl = kq["dl"]
        self.assertEqual([(v["ma"], v["vnd"]) for v in dl["vung"]], [("SG", 330000), ("HK", 280000), ("TH", 280000), ("ID", 210000), ("US", 180000)])
        self.assertEqual(dl["gia_vnd"], 180000)
        self.assertEqual(dl["re_hon"], {"ten": "Singapore", "vnd": 150000})
        self.assertEqual(dl["ten"], "MONSTER HUNTER RISE")
        self.assertEqual(dl["the"], {"ma": "US", "ten_vung": "Mỹ", "the": [{"menh_gia": "$5", "so_luong": 1}], "gia_game": "$4,79", "du": "$0,21"})
        self.assertEqual((dl["goc"], dl["giam"], dl["han_chu"]), ("$39,99", 88, "14:59 · 5/11"))
        self.assertEqual(dl["bia"], "g0-bia.jpg")
        self.assertEqual(dl["nen"], ["g0-c0.jpg", "g0-c1.jpg"])
        self.assertEqual(b.so_trang, 5)

    def test_kiem_lai_dung_schema_s2_cho_moi_store(self):
        kq = chon.chon_fb(boi("fb"))
        self.assertEqual(len(kq["kiem_lai"]), 5)
        m = next(x for x in kq["kiem_lai"] if x["ten"].endswith("(US)"))
        self.assertEqual(m, {"ten": "Monster Hunter Rise PS4 & PS5 (US)", "pid": "UP0102-PPSA08033_00-FULLGAME00000001", "loc": "en-us",
                             "gia_cuc_bo": 4.79, "endTime": str(END_MS), "gia_dung_y": True, "gia_goc": 39.99, "giam": 88, "tien": "USD"})      # P2-d: them gia goc + % giam
        self.assertIsInstance(m["gia_cuc_bo"], float)

    def test_ff_chi_co_store_my_thi_fb_bo(self):
        b = boi("fb", keo(6, 7, 8, 11))
        self.assertIsNone(chon.chon_fb(b))
        self.assertTrue(any("store mua duoc" in x["ly"] for x in b.bo))

    def test_game_da_noi_bat_thi_bo_chon_game_ke(self):
        kq = chon.chon_fb(boi("fb", nb=NB(["monster hunter"])))
        self.assertEqual(kq["chon"]["hang"], 5)
        self.assertEqual(kq["dl"]["vung"][-1]["ma"], "HK")

    def test_game_da_dung_trong_sg_dang_thi_bo(self):
        da = chon.da_dung_tu_dong([dict(dang="x-goc", trang_thai="da_dang", id_tai="PPSA08038_00|monster hunter rise ps4 ps5")])
        self.assertEqual(chon.chon_fb(boi("fb", da_dung=da))["chon"]["hang"], 5)

    def test_gia_trang_lech_thi_bo(self):
        d = keo()
        t = Trang(d)
        link = dong_keo(4)["link"]
        t.ghi_de[link] = t.dung(link, con="$4.99")
        b = boi("fb", d, t)
        self.assertEqual(chon.chon_fb(b)["chon"]["hang"], 5)
        self.assertTrue(any("gia trang" in x["ly"] for x in b.bo))

    def test_endtime_duoi_24h_thi_bo(self):
        d = keo()
        t = Trang(d)
        link = dong_keo(4)["link"]
        t.ghi_de[link] = t.dung(link, end_ms=int((gio("fb") + dt.timedelta(hours=23)).timestamp() * 1000))
        b = boi("fb", d, t)
        self.assertEqual(chon.chon_fb(b)["chon"]["hang"], 5)
        self.assertTrue(any("het giam som" in x["ly"] for x in b.bo))

    def test_thieu_endtime_thi_bo(self):
        d = keo()
        t = Trang(d)
        link = dong_keo(4)["link"]
        t.ghi_de[link] = t.dung(link, end_ms=None)
        b = boi("fb", d, t)
        self.assertEqual(chon.chon_fb(b)["chon"]["hang"], 5)
        self.assertTrue(any("endTime" in x["ly"] for x in b.bo))

    def test_phan_tram_giam_trang_lech_thi_bo(self):
        d = keo()
        t = Trang(d)
        link = dong_keo(4)["link"]
        t.ghi_de[link] = t.dung(link, goc="$12.00")      # 4.79/12 -> giam 60% khac 88%
        self.assertEqual(chon.chon_fb(boi("fb", d, t))["chon"]["hang"], 5)

    def test_quy_vnd_khac_gia_vung_thi_bo(self):
        def lech(nt, vung, g, tien, gt, ty, hn=None):
            r = quy_gia(nt, vung, g, tien, gt, ty, hn)
            return dict(r, vnd=r["vnd"] + 1000) if (vung, round(g, 2)) == ("US", 4.79) else r
        b = boi("fb", quy=lech)
        self.assertEqual(chon.chon_fb(b)["chon"]["hang"], 5)
        self.assertTrue(any("quy VND" in x["ly"] for x in b.bo))

    def test_quy_ra_khong_phai_the_hoac_qua_4_tam_thi_bo(self):
        def ngan_hang(nt, vung, g, tien, gt, ty, hn=None):
            r = quy_gia(nt, vung, g, tien, gt, ty, hn)
            return dict(r, cach="ngan_hang", mua_duoc=False) if vung == "US" and round(g, 2) == 4.79 else r
        def nam_tam(nt, vung, g, tien, gt, ty, hn=None):
            r = quy_gia(nt, vung, g, tien, gt, ty, hn)
            return dict(r, the=[(1.0, 5, 28000.0)]) if vung == "US" and round(g, 2) == 4.79 else r
        for q in (ngan_hang, nam_tam):
            self.assertEqual(chon.chon_fb(boi("fb", quy=q))["chon"]["hang"], 5)

    def test_the_du_qua_5_phan_tram_thi_bo_vi_khong_goi_duoc_vua_khit(self):
        def du_nhieu(nt, vung, g, tien, gt, ty, hn=None):
            r = quy_gia(nt, vung, g, tien, gt, ty, hn)
            return dict(r, the=[(10.0, 1, 280000.0)], tong_menh_gia=10.0, thua=5.21) if vung == "US" and round(g, 2) == 4.79 else r
        b = boi("fb", quy=du_nhieu)
        self.assertEqual(chon.chon_fb(b)["chon"]["hang"], 5)
        self.assertTrue(any("vua khit" in x["ly"] for x in b.bo))

    def test_s4_hang_gia_vnd_lech_gia_vung_thi_bo(self):
        d = keo()
        d[0]["gia_vnd"] = 181000
        b = boi("fb", d)
        self.assertEqual(chon.chon_fb(b)["chon"]["hang"], 5)
        self.assertTrue(any("S4" in x["ly"] for x in b.bo))

    def test_s3_store_thieu_link_bi_bo_van_du_3_store(self):
        d = keo()
        del d[0]["gia_vung"]["SG"]["link"]
        kq = chon.chon_fb(boi("fb", d))
        self.assertEqual([v["ma"] for v in kq["dl"]["vung"]], ["HK", "TH", "ID", "US"])
        self.assertEqual(kq["dl"]["re_hon"], {"ten": "Hồng Kông", "vnd": 100000})       # re_hon tinh tren store DAT (280 - 180)
        self.assertEqual(len(kq["kiem_lai"]), 4)

    def test_s3_store_truot_trang_bi_bo_khoi_bang(self):
        d = keo()
        t = Trang(d)
        sg = d[0]["gia_vung"]["SG"]["link"]
        t.ghi_de[sg] = t.dung(sg, con="SGD6.70")
        kq = chon.chon_fb(boi("fb", d, t))
        self.assertNotIn("SG", [v["ma"] for v in kq["dl"]["vung"]])
        self.assertEqual(kq["dl"]["re_hon"]["vnd"], 100000)

    def test_s3_duoi_3_store_dat_thi_bo_ung_vien(self):
        d = keo()
        t = Trang(d)
        for ma in ("SG", "HK", "TH"):
            l = d[0]["gia_vung"][ma]["link"]
            t.ghi_de[l] = None
        b = boi("fb", d, t)
        self.assertEqual(chon.chon_fb(b)["chon"]["hang"], 5)
        self.assertTrue(any("store qua kiem trang" in x["ly"] for x in b.bo))

    def test_s3_store_re_nhat_truot_thi_bo_ung_vien(self):
        d = keo()
        t = Trang(d)
        t.ghi_de[d[0]["link"]] = None
        b = boi("fb", d, t)
        self.assertEqual(chon.chon_fb(b)["chon"]["hang"], 5)

    def test_s3_tran_tai_trang_moi_luot(self):
        d = keo()
        t = Trang(d)
        for h in d:
            for o in h["gia_vung"].values():
                if o.get("link"):
                    t.ghi_de[o["link"]] = None
        b = boi("fb", d, t)
        self.assertIsNone(chon.chon_fb(b))
        self.assertLessEqual(b.so_trang, chon.TRAN_TRANG["fb"])

    def test_anh_hong_thi_bo(self):
        b = boi("fb", tai_anh=tai_anh_gia(hong=["PPSA08033_00-FULLGAME00000001/bia"]))
        self.assertEqual(chon.chon_fb(b)["chon"]["hang"], 5)
        kq = chon.chon_fb(boi("fb", tai_anh=tai_anh_gia(hong=["/s0.jpg", "/s1.jpg"])))      # con 1 anh chup tai duoc: van dat (>= 1)
        self.assertEqual(kq["dl"]["nen"], ["g0-c0.jpg"])
        b = boi("fb", tai_anh=tai_anh_gia(hong=["/s"]))        # khong anh chup nao tai duoc -> khong game nao dung duoc
        self.assertIsNone(chon.chon_fb(b))

    def test_chenh_gia_duoi_30000_thi_bo(self):
        d = keo()
        for ma, v in (("SG", 200000), ("HK", 190000), ("TH", 190000), ("ID", 190000)):
            d[0]["gia_vung"][ma]["vnd"] = v
        b = boi("fb", d)
        self.assertEqual(chon.chon_fb(b)["chon"]["hang"], 5)
        self.assertTrue(any("chenh gia" in x["ly"] for x in b.bo))

    def test_store_re_nhat_khong_duy_nhat_thi_bo(self):
        d = keo()
        d[0]["gia_vung"]["ID"]["vnd"] = 180000
        b = boi("fb", d)
        self.assertEqual(chon.chon_fb(b)["chon"]["hang"], 5)
        self.assertTrue(any("duy nhat" in x["ly"] for x in b.bo))

    def test_lech_gia_khong_phai_false_thi_bo(self):
        d = keo()
        d[0]["lech_gia"] = None
        self.assertEqual(chon.chon_fb(boi("fb", d))["chon"]["hang"], 5)

    def test_gia_ngoai_khoang_thi_bo(self):
        d = keo()
        d[0]["gia_vnd"] = 40000
        d[0]["gia_vung"]["US"]["vnd"] = 40000
        self.assertEqual(chon.chon_fb(boi("fb", d))["chon"]["hang"], 5)


# ================================================================ chon IG
class ChonIG(unittest.TestCase):
    def test_ff_chon_nhom_ff_xep_giam_dan_re_nhat_cuoi(self):
        b = boi("ig", keo(6, 7, 8, 11))
        kq = chon.chon_ig(b)
        dl = kq["dl"]
        self.assertEqual(dl["tieu_de"], ["4 GAME", "FINAL FANTASY", "DƯỚI 500K"])
        self.assertEqual([(g["ten"], g["gia_vnd"]) for g in dl["game"]],
                         [("FINAL FANTASY XII THE ZODIAC AGE", 460000), ("FINAL FANTASY VII REBIRTH", 460000), ("FINAL FANTASY XV ROYAL EDITION", 316000),
                          ("FINAL FANTASY TYPE-0 HD", 216000)])
        self.assertEqual((dl["giam_chung"], dl["vung_chung"], dl["han_chu"]), (70, "Mỹ", "14:59 · 5/11"))
        self.assertNotIn("han_khac", dl)
        self.assertEqual(len(kq["kiem_lai"]), 4)

    def test_s10_trung_san_pham_cung_title_id_giu_hang_nho(self):
        b = boi("ig")
        chon.ung_vien(b, bo_trung_san_pham=True)
        self.assertTrue(any(x["ma"].startswith("PPSA08038_00") and "trung san pham" in x["ly"] for x in b.bo))       # hang 19 MH Rise + Sunbreak
        self.assertTrue(any("trung san pham" in x["ly"] and x["ma"].startswith("CUSA06314_00") for x in b.bo))

    def test_s10_khoa_ip_hai_tu_khong_gop_ten_ra_cac_so(self):
        b = boi("ig")
        kq = chon.chon_ig(b)
        self.assertIsNotNone(kq)
        self.assertGreaterEqual(len(kq["dl"]["game"]), 3)
        self.assertLessEqual(len(kq["dl"]["game"]), 5)
        ten = {chon.khoa_ip(g["ten_goc"]) for g in kq["su_that"]["game"]}
        self.assertEqual(len(ten), 1)

    def test_nhom_du_phong_n_game_ps_duoi_x_khi_khong_co_nhom_ip(self):
        d = keo(18, 19, 22, 23, 27, 28)      # Outward x2 la 1 nhom IP 'outward definitive'/'outward the' (<3) + Little Strays 2 + MotoGP: 72.000 moi game
        b = boi("ig", d)
        kq = chon.chon_ig(b)
        self.assertIsNotNone(kq)
        self.assertIsNone(kq["su_that"]["ip"])
        self.assertEqual(kq["dl"]["tieu_de"][1], "PS4 · PS5")
        self.assertTrue(kq["dl"]["tieu_de"][2].startswith("DƯỚI "))
        self.assertTrue(all(g["gia_vnd"] <= 300000 for g in kq["dl"]["game"]))

    def test_han_khac_nhau_hon_60s_ghi_han_som_nhat(self):
        d = keo(6, 7, 8, 11)
        t = Trang(d)
        l = d[3]["link"]
        t.ghi_de[l] = t.dung(l, end_ms=END_MS - 3600 * 1000)      # hang 11 het som 1 gio
        kq = chon.chon_ig(boi("ig", d, t))
        self.assertTrue(kq["dl"]["han_khac"])
        self.assertEqual(kq["dl"]["han_chu"], "13:59 · 5/11")

    def test_it_hon_3_game_qua_kiem_thi_none(self):
        d = keo(6, 7, 8, 11)
        t = Trang(d)
        t.ghi_de[d[0]["link"]] = None
        t.ghi_de[d[1]["link"]] = None
        self.assertIsNone(chon.chon_ig(boi("ig", d, t)))

    def test_tran_tai_trang_ig_10(self):
        b = boi("ig")
        chon.chon_ig(b)
        self.assertLessEqual(b.so_trang, 10)

    def test_toi_da_5_game(self):
        d = keo(12, 13, 14, 15, 17, 18, 20, 21, 22)       # Resident Evil nhieu hang
        kq = chon.chon_ig(boi("ig", [h for h in keo() if chon.khoa_ip(h["ten"]) == "resident evil"]))
        self.assertLessEqual(len(kq["dl"]["game"]), 5)


# ================================================================ chon Threads
class ChonThreads(unittest.TestCase):
    def test_cap_cung_gia_ff7_va_ff12_chon_ben_nhieu_luot(self):
        kq = chon.chon_threads(boi("threads", keo(6, 7, 8, 11)))
        dl = kq["dl"]
        self.assertEqual([dl["cau_hoi"], dl["a"]["ten"], dl["b"]["ten"]], [["Có 460 nghìn,", "chọn bên nào?"], "FINAL FANTASY VII REBIRTH", "FINAL FANTASY XII THE ZODIAC AGE"])
        self.assertEqual((dl["a"]["sao"], dl["a"]["luot"], dl["b"]["sao"], dl["b"]["luot"]), ("4,66", "64.683", "4,75", "11.893"))
        self.assertEqual(dl["chan"], "Store Mỹ $14,99 (−70%) · thẻ $10 + $5 · hết giảm 14:59 · 5/11")
        self.assertEqual((kq["su_that"]["ben"], kq["su_that"]["ly_chon"]), ("a", "luot"))
        self.assertEqual(len(kq["kiem_lai"]), 2)

    def test_chon_ben_quy_tac(self):
        mk = lambda tb, n: {"diem": {"tb": tb, "so_luot": n}}
        self.assertEqual(chon.chon_ben(mk(4.66, 64683), mk(4.75, 11893)), ("a", "luot"))      # 5,4x luot, thap hon 0,09 <= 0,2
        self.assertEqual(chon.chon_ben(mk(4.30, 64683), mk(4.75, 11893)), ("b", "sao"))       # thap hon 0,45 > 0,2 -> sao cao hon
        self.assertEqual(chon.chon_ben(mk(4.5, 2000), mk(4.8, 1000)), ("b", "sao"))
        self.assertEqual(chon.chon_ben(mk(4.5, 2000), mk(4.5, 1000)), ("a", "luot"))          # hoa -> nhieu luot
        self.assertEqual(chon.chon_ben(mk(4.9, 9000), mk(4.5, 1000)), ("a", "luot"))

    def test_s5_khac_endtime_hon_60s_thi_bo_cap(self):
        d = keo(7, 8)
        t = Trang(d)
        t.ghi_de[d[1]["link"]] = t.dung(d[1]["link"], end_ms=END_MS - 3600 * 1000)
        b = boi("threads", d, t)
        self.assertIsNone(chon.chon_threads(b))
        self.assertTrue(any("khac endTime" in x["ly"] for x in b.bo))

    def test_s5_lech_60s_van_nhan(self):
        d = keo(7, 8)
        t = Trang(d)
        t.ghi_de[d[1]["link"]] = t.dung(d[1]["link"], end_ms=END_MS - 30 * 1000)
        self.assertIsNotNone(chon.chon_threads(boi("threads", d, t)))

    def test_thieu_diem_hoac_duoi_100_luot_thi_bo(self):
        d = keo(7, 8)
        t = Trang(d)
        t.ghi_de[d[1]["link"]] = trang_html("UP0082-CUSA05532_00-FFXIIGAMEPS400NA", "$14.99", "$49.99", "USD", diem=(4.9, 99))
        b = boi("threads", d, t)
        self.assertIsNone(chon.chon_threads(b))
        t.ghi_de[d[1]["link"]] = trang_html("UP0082-CUSA05532_00-FFXIIGAMEPS400NA", "$14.99", "$49.99", "USD", diem=None)
        self.assertIsNone(chon.chon_threads(boi("threads", d, t)))

    def test_khong_co_2_game_cung_gia_thi_none(self):
        self.assertIsNone(chon.chon_threads(boi("threads", keo(6, 8, 11))))

    def test_uu_tien_cung_ip_roi_hang_nho(self):
        kq = chon.chon_threads(boi("threads", keo(6, 7, 8, 11, 18, 19, 27, 28)))
        self.assertEqual(kq["chon"]["a"]["hang"], 7)       # FF VII Rebirth + FF XII (cung IP) truoc Outward x2 / Little Strays...

    def test_thu_chu_none_thi_thu_cap_ke(self):
        goi = []
        def thu(sv, kq):
            goi.append(sv["a"])
            return None if len(goi) == 1 else {"text": "x"}
        d = keo(7, 8, 12, 16, 27, 28)  # 460k: 7,8 ; 180k US: RE5 (12) + RE6 (16) ; Outward 27/28 la 2 ban cung game -> khong ghep (cung_dong)
        kq = chon.chon_threads(boi("threads", d), thu)
        self.assertEqual(len(goi), 2)
        self.assertEqual(kq["chu_san"], {"text": "x"})
        self.assertNotEqual(kq["chon"]["a"]["hang"], 7)

    def test_giu_gia_moi_game_la_quy_vnd_da_kiem(self):
        d = keo(7, 8)
        d[1]["gia_vnd"] = 459000
        b = boi("threads", d)
        self.assertIsNone(chon.chon_threads(b))


# ================================================================ chu
def sv_fb():
    return chon.chon_fb(boi("fb"))["su_that"]


def sv_ig(*hang):
    return chon.chon_ig(boi("ig", keo(*hang) if hang else None))["su_that"]


def sv_th(*hang):
    return chon.chon_threads(boi("threads", keo(*(hang or (7, 8)))))["su_that"]


class Chu(unittest.TestCase):
    def test_fb_caption_dong_1_chi_gia_mua_va_re_hon_o_dong_2(self):
        sv = sv_fb()
        text = chu.dung_chu("fb", sv)["text"]
        d = text.split("\n")
        self.assertEqual(d[0], "Monster Hunter Rise còn 180 nghìn ở Store Mỹ: 1 thẻ $5 vừa khít với giá niêm yết $4,79.")
        self.assertIn("Rẻ hơn Store Singapore 150 nghìn.", d[2])
        self.assertIn("Giảm 88% (gốc $39,99) tới 14:59 ngày 5/11.", d[2])
        self.assertIn("Giá niêm yết, chưa gồm thuế nếu có.", text)
        self.assertEqual(d[-1], "#MonsterHunterRise #PS5 #SănGame")
        self.assertEqual(chu.cong("fb", text, sv), [])

    def test_fb_caption_khong_url_hashtag_dung_tran_va_ngan(self):
        text = chu.dung_chu("fb", sv_fb())["text"]
        self.assertNotRegex(text, r"https?://|www\.|\.com|\.vn")
        self.assertLessEqual(len(chu.TAG.findall(text)), 3)
        self.assertLessEqual(len(text), 600)
        self.assertNotIn("là đủ", text)

    def test_ig_caption_khong_url_hashtag_dung_tran_va_cap_ten_gia(self):
        sv = sv_ig(6, 7, 8, 11)
        text = chu.dung_chu("ig", sv)["text"]
        d = text.split("\n")
        self.assertEqual(d[0], "4 game Final Fantasy từ 216 nghìn, giảm tới 14:59 ngày 5/11 ở PS Store Mỹ.")
        self.assertIn("Final Fantasy Type-0 HD – 216 nghìn; Final Fantasy XV Royal Edition – 316 nghìn; "
                      "Final Fantasy VII Rebirth – 460 nghìn; Final Fantasy XII The Zodiac Age – 460 nghìn.", text)
        self.assertIn("Bảng giá đủ vùng: link ở bio.", text)
        self.assertIn("Giá niêm yết, chưa gồm thuế nếu có.", text)
        self.assertLessEqual(len(chu.TAG.findall(text)), 5)
        self.assertNotRegex(text, r"https?://|www\.|\.com|\.vn")
        self.assertEqual(chu.cong("ig", text, sv), [])

    def test_ig_han_khac_noi_giam_som_nhat(self):
        sv = sv_ig(6, 7, 8, 11)
        sv["han_khac"] = True
        self.assertIn("giảm sớm nhất tới", chu.dung_chu("ig", sv)["text"].split("\n")[0])

    def test_cong_chan_dong_1_co_500_nghin_khong_phai_gia_da_kiem(self):
        sv = sv_fb()
        text = chu.dung_chu("fb", sv)["text"]
        xau = text.replace("còn 180 nghìn", "còn 500 nghìn", 1)
        self.assertTrue(any("dong 1" in l for l in chu.cong("fb", xau, sv)))

    def test_s6_dong_1_co_180_va_150_nghin_thi_truot(self):
        sv = sv_fb()
        text = chu.dung_chu("fb", sv)["text"]
        d = text.split("\n")
        d[0] = d[0].replace("giá niêm yết $4,79.", "giá niêm yết $4,79, rẻ hơn 150 nghìn.")
        loi = chu.cong("fb", "\n".join(d), sv)
        self.assertTrue(any("dong 1" in l and "150000" in l for l in loi), loi)

    def test_s6_re_hon_phai_la_hieu_hai_gia_da_kiem(self):
        sv = sv_fb()
        text = chu.dung_chu("fb", sv)["text"]
        sai = text.replace("Rẻ hơn Store Singapore 150 nghìn.", "Rẻ hơn Store Singapore 160 nghìn.")
        self.assertTrue(chu.cong("fb", sai, sv))
        sv2 = dict(sv, re_hon={"ten": "Singapore", "vnd": 160000})
        self.assertTrue(any("re_hon" in l for l in chu.cong("fb", sai, sv2)))

    def test_cong_chan_tien_ngoai_tap(self):
        sv = sv_fb()
        text = chu.dung_chu("fb", sv)["text"]
        self.assertTrue(any("ngoai tap" in l for l in chu.cong("fb", text + "\nSale 99 nghìn", sv)))

    def test_s11_caption_khong_dung_dang_K(self):
        sv = sv_ig(6, 7, 8, 11)
        text = chu.dung_chu("ig", sv)["text"].replace("216 nghìn", "216K")
        self.assertTrue(any("K" in l for l in chu.cong("ig", text, sv)))

    def test_s11_dao_gia_hai_game_thi_truot(self):
        sv = sv_ig(6, 7, 8, 11)
        text = chu.dung_chu("ig", sv)["text"]
        dao = (text.replace("Type-0 HD – 216 nghìn", "Type-0 HD – @A").replace("Royal Edition – 316 nghìn", "Royal Edition – 216 nghìn")
               .replace("@A", "316 nghìn"))
        loi = chu.cong("ig", dao, sv)
        self.assertTrue(any("sai gia" in l for l in loi), loi)

    def test_s9_thieu_cau_niem_yet_hoac_co_la_du_thi_truot(self):
        sv = sv_fb()
        text = chu.dung_chu("fb", sv)["text"]
        self.assertTrue(chu.cong("fb", text.replace(chu.NIEM_YET, ""), sv))
        self.assertTrue(chu.cong("fb", text.replace("vừa khít", "là đủ"), sv))

    def test_cam_tuong_tac_url_hashtag(self):
        sv = sv_fb()
        text = chu.dung_chu("fb", sv)["text"]
        for them in ("Follow để xem thêm", "Bình luận bên dưới", "xem sangame.com.vn", "#A #B #C"):
            self.assertTrue(chu.cong("fb", text + "\n" + them, sv), them)

    def test_fb_tran_600(self):
        sv = sv_fb()
        self.assertTrue(any("dai" in l for l in chu.cong("fb", chu.dung_chu("fb", sv)["text"] + "x" * 600, sv)))

    # ---- Threads
    def test_threads_text_vua_gioi_han_va_dang_cau_hoi(self):
        sv = sv_th()
        kq = chu.dung_chu("threads", sv, NGAY)
        text = kq["text"]
        self.assertLessEqual(len(text), 450)
        self.assertLessEqual(len(text.encode("utf-8")), 500)
        d = [x for x in text.split("\n") if x.strip()]
        self.assertTrue(d[0].endswith("?") and d[-1].endswith("?"))
        self.assertIn("460 nghìn", d[0])
        self.assertNotIn("#", text)
        self.assertIn("Mình chọn Final Fantasy VII Rebirth: 64.683 người chấm, trung bình 4,66 sao.", text)
        self.assertIn("1 thẻ $10 + 1 thẻ $5 vừa khít với giá niêm yết", text)       # S9
        self.assertEqual(chu.cong("threads", text, sv), [])
        self.assertLessEqual(len(kq["alt"]), 1000)
        self.assertIn(kq["ma_bien_the"][:2], ("m0", "m1", "m2", "m3", "m4", "m5", "m6", "m7"))

    def test_threads_mo_khong_lap_trong_7_ngay(self):
        sv = sv_th()
        da, mo = set(), []
        for i in range(30):
            ngay = NGAY + dt.timedelta(days=i)
            text, ma = chu.chu_threads(sv, ngay, set(mo[-7:]))
            m = ma.split("-")[0]
            self.assertNotIn(m, mo[-7:])
            mo.append(m)
        self.assertEqual(len(set(mo[:8])), 8)

    def test_s14_8_cau_mo_het_thi_none(self):
        sv = sv_th()
        self.assertEqual(len({chu.chu_threads(sv, NGAY, {f"m{j}" for j in range(8) if j != i})[1].split("-")[0] for i in range(8)}), 8)
        self.assertIsNone(chu.chu_threads(sv, NGAY, {f"m{i}" for i in range(8)}))
        self.assertEqual(len(chu.MO), 8)

    def test_mo_da_dung_tu_dong_doc_id_container_bo_that_bai(self):
        rows = [dict(dang="threads-gia", trang_thai="da_dang", id_container="m3-k1"), dict(dang="threads-gia", trang_thai="that_bai", id_container="m4-k0"),
                dict(dang="threads-gia", trang_thai="khong_ro", id_container="m5-k2"), dict(dang="fb-gia", trang_thai="da_dang", id_container="fb"),
                dict(dang="threads-gia", trang_thai="bo", id_container="m6-k3")]
        self.assertEqual(chu.mo_da_dung_tu_dong(rows), {"m3", "m5"})

    def test_threads_ten_dai_phai_rut_hoac_bo_cap(self):
        sv = sv_th()
        sv.update(a="X" * 90, b="Y" * 90, chon_ten="X" * 90, khac_ten="Y" * 90)
        self.assertIsNone(chu.chu_threads(sv, NGAY))      # vuot 450/500 du da rut -> None (chon_threads se thu cap ke)

    def test_threads_rut_theo_muc_van_giu_cau_niem_yet(self):
        sv = sv_th()
        sv.update(a="Final Fantasy VII Rebirth Complete Edition Deluxe", chon_ten="Final Fantasy VII Rebirth Complete Edition Deluxe")
        r = chu.chu_threads(sv, NGAY)
        if r:
            self.assertIn(chu.NIEM_YET, r[0])
            self.assertTrue(chu.vua_threads(r[0]))

    def test_threads_cong_chan_thieu_dau_hoi_va_hashtag(self):
        sv = sv_th()
        text = chu.dung_chu("threads", sv, NGAY)["text"]
        self.assertTrue(chu.cong("threads", text[:-1] + ".", sv))
        self.assertTrue(chu.cong("threads", text + " #PS5", sv))
        self.assertTrue(chu.cong("threads", text + "x" * 300, sv))

    def test_ghi_bai_json_khop_khuon_kiem_khuon(self):
        # kiem-khuon.py sg-threads-gia: dong dau co '?' + tien VND (TIEN_VND), cau cuoi '?', 0 hashtag/URL, khong CAM_THREADS
        import re
        tien = re.compile(r"\d[\d.,]*\s*(nghìn|ngàn|k\b|đ\b|₫|vnđ|vnd|triệu|tr\b)", re.I)
        text = chu.dung_chu("threads", sv_th(), NGAY)["text"]
        d = [x for x in text.split("\n") if x.strip()]
        self.assertTrue(tien.search(d[0]) and "?" in d[0] and "?" in d[-1])
        for t in ["bình luận", "tag bạn", "share", "chia sẻ", "giveaway", "tặng", "!!!"]:
            self.assertNotIn(t, text.lower())


# ================================================================ cong bat rieng khuon
class CongBat(unittest.TestCase):
    def test_bang_su_that(self):
        f = mxh.kenh_bat_rieng
        for v in ("", None, "youtube", "fb,ig", "top5:youtube,flagship:tiktok", "fb-gia", "fb-gia:ig", "ig-gia:fb", "fb-gia:", ":fb"):
            self.assertFalse(f(v, "fb-gia", "fb"), repr(v))
        self.assertTrue(f("fb-gia:fb", "fb-gia", "fb"))
        self.assertTrue(f(" top5:youtube , fb-gia:fb ", "fb-gia", "fb"))
        self.assertTrue(f("top5:youtube,fb-gia:fb", "fb-gia", "fb"))
        self.assertFalse(f(" top5:youtube , fb-gia:fb ", "ig-gia", "ig"))
        self.assertTrue(f("ig-gia:ig,threads-gia:threads", "threads-gia", "threads"))
        self.assertFalse(f("ig-gia:ig,threads-gia:threads", "fb-gia", "fb"))

    def chay_that(self, bien, kenh="fb"):
        cong = mock.Mock(side_effect=AssertionError("khong duoc cham vao cong khi cong tat"))
        a = types.SimpleNamespace(kenh=kenh, ngay="2026-11-02", che_do="that", khong_api=False, du_lieu="x", gia_the="x", ra=None)
        with mock.patch.dict(os.environ, {"SG_KENH_BAT": bien}), mock.patch.object(chung, "bay_gio", lambda: gio(kenh) - dt.timedelta(minutes=30)), \
                mock.patch.object(mxh, "lam", return_value=77) as lam, mock.patch.object(mxh.so, "Cong", cong):
            kq = mxh.chay(a)
        return kq, lam

    def test_3_khuon_tat_voi_cac_gia_tri_khong_dung(self):
        for bien in ("", "youtube", "fb,ig", "top5:youtube,flagship:tiktok"):
            for kenh in ("fb", "ig", "threads"):
                kq, lam = self.chay_that(bien, kenh)
                self.assertEqual(kq, 0, (bien, kenh))
                lam.assert_not_called()

    def test_chi_fb_gia_bat_khi_co_muc_rieng_dung_kenh(self):
        for bien, kenh, bat in ((" top5:youtube , fb-gia:fb ", "fb", True), (" top5:youtube , fb-gia:fb ", "ig", False), ("fb-gia:ig", "fb", False),
                                ("top5:youtube,fb-gia:fb", "threads", False)):
            cong_ = mock.Mock()
            a = types.SimpleNamespace(kenh=kenh, ngay="2026-11-02", che_do="that", khong_api=False, du_lieu="x", gia_the="x", ra=None)
            with mock.patch.dict(os.environ, {"SG_KENH_BAT": bien, "SG_CONG_KHOA": "kh_cong_1234567890", "ZERNIO_KHOA": ZK}), \
                    mock.patch.object(chung, "bay_gio", lambda: gio(kenh) - dt.timedelta(minutes=30)), \
                    mock.patch.object(mxh, "lam", return_value=77) as lam, mock.patch.object(mxh.so, "Cong", return_value=cong_):
                kq = mxh.chay(a, phu=object())
            self.assertEqual(kq, 77 if bat else 0, (bien, kenh))
            self.assertEqual(lam.called, bat)

    def test_pha_thu_khong_can_cong(self):
        a = types.SimpleNamespace(kenh="fb", ngay="2026-11-02", che_do="thu", khong_api=False, du_lieu="x", gia_the="x", ra=None)
        with mock.patch.dict(os.environ, {"SG_KENH_BAT": "", "SG_CONG_KHOA": "kh_cong_1234567890"}), mock.patch.object(mxh, "lam", return_value=0) as lam, \
                mock.patch.object(mxh.so, "Cong", return_value=mock.Mock()):
            self.assertEqual(mxh.chay(a, phu=object()), 0)
        lam.assert_called_once()

    def test_that_qua_gio_thoat_3_khong_dang_bu(self):
        a = types.SimpleNamespace(kenh="fb", ngay="2026-11-02", che_do="that", khong_api=False, du_lieu="x", gia_the="x", ra=None)
        with mock.patch.dict(os.environ, {"SG_KENH_BAT": "fb-gia:fb"}), mock.patch.object(chung, "bay_gio", lambda: gio("fb") - dt.timedelta(minutes=1)), \
                mock.patch.object(ntfy, "loi", lambda *a, **k: None), mock.patch.object(mxh, "lam") as lam:
            self.assertEqual(mxh.chay(a), 3)
        lam.assert_not_called()

    def test_thieu_khoa_cong_thoat_2(self):
        a = types.SimpleNamespace(kenh="fb", ngay="2026-11-02", che_do="thu", khong_api=False, du_lieu="x", gia_the="x", ra=None)
        with mock.patch.dict(os.environ, {"SG_CONG_KHOA": ""}), mock.patch.object(ntfy, "loi", lambda *a, **k: None):
            self.assertEqual(mxh.chay(a), 2)

    def test_ig_threads_that_thieu_zernio_thoat_2(self):
        a = types.SimpleNamespace(kenh="ig", ngay="2026-11-02", che_do="thu", khong_api=False, du_lieu="x", gia_the="x", ra=None)
        with mock.patch.dict(os.environ, {"SG_CONG_KHOA": "kh_cong_1234567890", "ZERNIO_KHOA": ""}), mock.patch.object(ntfy, "loi", lambda *a, **k: None), \
                mock.patch.object(mxh.so, "Cong", return_value=mock.Mock()):
            self.assertEqual(mxh.chay(a), 2)


# ================================================================ luong dang (cong + nen tang gia)
class CongTG(CongGia):
    """CongGia + doc_keo + `luc` (giong sg_dang that) + dong cua luot khac xuat hien NGAY SAU giu_dang cua minh (dua chon S7)."""

    def __init__(self, ds=None, su_kien=None, sau_giu=()):
        super().__init__()
        self.ds, self.su_kien, self.sau_giu, self.t = ds if ds is not None else keo(), su_kien if su_kien is not None else [], list(sau_giu), 0

    def doc_keo(self, ngay):
        return copy.deepcopy(self.ds)

    def _luc(self):
        self.t += 1
        return (dt.datetime(2026, 11, 2, 10, 0, tzinfo=dt.timezone.utc) + dt.timedelta(seconds=self.t)).isoformat()

    def them(self, **row):
        row.setdefault("che_do", "that")
        row.setdefault("luc", self._luc())
        row.setdefault("ngay", "2026-11-02")
        row.setdefault("kenh", "x")
        self.dong[(row["ngay"], row["dang"], row["kenh"], row["che_do"], row.get("id_tai"))] = row
        return row

    def giu_dang(self, ngay, dang, kenh, che_do, gio_du_kien=None, manifest_sha=None):
        self.su_kien.append("giu_dang")
        ok = super().giu_dang(ngay, dang, kenh, che_do, gio_du_kien, manifest_sha)
        if ok:
            self.dong[(ngay, dang, kenh, che_do)]["luc"] = self._luc()
            for r in self.sau_giu:
                self.them(**r)
            self.sau_giu = []
        return ok

    def cap_cuoi(self, kenh, dang=None):
        return next(v for k, v in self.dong.items() if len(k) == 4 and k[2] == kenh)


class NenGia:
    def __init__(self, su_kien, kenh="fb", loi_chuan_bi=None, loi_cong_khai=None, danh_tinh_loi=None):
        self.su_kien, self.kenh, self.loi_chuan_bi, self.loi_cong_khai, self.danh_tinh_loi, self.goi = su_kien, kenh, loi_chuan_bi, loi_cong_khai, danh_tinh_loi, {}

    def kiem_danh_tinh(self, dich):
        self.su_kien.append("danh_tinh")
        if self.danh_tinh_loi:
            raise self.danh_tinh_loi

    def chuan_bi(self, goi, che_do, luu):
        self.su_kien.append("chuan_bi")
        self.goi = goi
        luu(id_bai="VID1")
        if self.loi_chuan_bi:
            raise self.loi_chuan_bi
        return {"id_bai": "VID1", "ghi_chu": "gia"}

    def cong_khai(self, goi, id_bai, han=None):
        self.han = han
        self.su_kien.append("cong_khai")
        if self.loi_cong_khai:
            raise self.loi_cong_khai
        return {"id_bai": id_bai, "link": "https://www.facebook.com/reel/VID1/"}


class Luong(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.d = pathlib.Path(self.tmp.name)
        self.su_kien, self.ntfy_loi, self.ntfy_tin, self.ngu = [], [], [], []
        self.t = None
        gt = self.d / "gia-the.json"
        gt.write_text(json.dumps({"ngay": "2026-11-02", "vung": {"US": {"tien": "USD"}}, "ty_gia_ngan_hang": {}}))
        self.gia_the = str(gt)
        self.ra_thu_dir = self.d / "ra-thu"
        for p in (mock.patch.object(chung, "bay_gio", lambda: self.t), mock.patch.object(chung, "ngu", self.ngu_gia),
                  mock.patch.object(ntfy, "loi", lambda *a, **k: self.ntfy_loi.append(a)), mock.patch.object(ntfy, "tin", lambda *a, **k: self.ntfy_tin.append(a)),
                  mock.patch.dict(os.environ, {"RA_THU": str(self.ra_thu_dir), "SG_KENH_BAT": "fb-gia:fb,ig-gia:ig,threads-gia:threads", "ZERNIO_KHOA": ZK})):
            p.start()
            self.addCleanup(p.stop)

    def ngu_gia(self, giay):
        self.ngu.append(giay)
        self.t += dt.timedelta(seconds=giay)

    def phu(self, kenh, ds=None, nen=None, nb=None, kiem_lai=None, kiem=None, **kw):
        ds = keo() if ds is None else ds
        nen = nen or NenGia(self.su_kien, kenh)

        def dung(k, dl_path, ts, am, nhac, ra):
            self.su_kien.append("dung")
            (pathlib.Path(ra) / ("anh.png" if k == "threads" else "video.mp4")).write_bytes(b"X")
            if k != "threads":
                (pathlib.Path(ra) / "bia.jpg").write_bytes(b"J")
        p = mxh.Phu(str(self.d), lay_trang=Trang(ds), tai_anh=lambda ts: tai_anh_gia(), quy_vnd=quy_gia, nb=lambda ngay, dang: nb or NB(),
                    dung=dung, kiem=kiem or (lambda k, ra, dl: {"dat": True, "phep": []}), tai_token=lambda cong, k: dict(TOKEN_FB),
                    nen=lambda k, tk, zk: nen, ngu=self.ngu_gia, kiem_lai=kiem_lai or (lambda muc, g: ([], [])), nhac=lambda d, n: pathlib.Path("nhac.mp3"),
                    dich=lambda: {}, **kw)
        p.nen_gia = nen
        return p

    def args(self, kenh="fb", che_do="that", **kw):
        return types.SimpleNamespace(kenh=kenh, ngay="2026-11-02", che_do=che_do, khong_api=kw.get("khong_api", False), du_lieu=str(self.d), gia_the=self.gia_the,
                                     ra=kw.get("ra"))

    def chay(self, kenh="fb", che_do="that", cong=None, phu=None, truoc_gio=dt.timedelta(minutes=30), **kw):
        self.t = gio(kenh) - truoc_gio
        cong = cong or CongTG(su_kien=self.su_kien)
        phu = phu or self.phu(kenh)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            kq = mxh.chay(self.args(kenh, che_do, **kw), cong, phu)
        return kq, cong, phu

    # ---- pha thu
    def test_thu_fb_chuan_bi_khong_cong_khai_ghi_that_bai_chep_ra_thu(self):
        kq, cong, phu = self.chay("fb", "thu")
        self.assertEqual(kq, 0)
        self.assertEqual(self.su_kien, ["dung", "danh_tinh", "giu_dang", "chuan_bi"])        # dung + kiem TRUOC, doi chieu tai khoan TRUOC giu_dang
        self.assertNotIn("cong_khai", self.su_kien)
        d = cong.cap_cuoi("fb")
        self.assertEqual((d["trang_thai"], d["id_bai"], d["id_container"]), ("that_bai", "VID1", "fb"))
        self.assertIn("che do thu", d["loi"])
        self.assertEqual(d["id_tai"], dong_keo(4)["ma"])
        self.assertTrue((self.ra_thu_dir / "caption.txt").exists() and (self.ra_thu_dir / "chon.json").exists() and (self.ra_thu_dir / "kiem.json").exists())
        bai = json.loads((self.ra_thu_dir / "bai.json").read_text())
        self.assertEqual((bai["kenh"], bai["loai"], bai["giong_ai"]), ("fb", "fb-gia", False))
        self.assertTrue(bai["chu"].startswith("Monster Hunter Rise còn 180 nghìn"))
        self.assertEqual(bai["captions"], {"fb": bai["chu"]})
        self.assertEqual(self.ngu, [])
        self.assertEqual(self.ntfy_tin, [])

    def test_thu_threads_ghi_bien_the_o_id_container_va_alt(self):
        kq, cong, phu = self.chay("threads", "thu", phu=self.phu("threads", keo(6, 7, 8, 11)), cong=CongTG(keo(6, 7, 8, 11), self.su_kien))
        self.assertEqual(kq, 0)
        d = cong.cap_cuoi("threads")
        self.assertRegex(d["id_container"], r"^m\d-k\d$")
        self.assertEqual(d["id_tai"], ",".join([dong_keo(7)["ma"], dong_keo(8)["ma"]]))
        self.assertIn("Ảnh so sánh", phu.nen_gia.goi["alt"])
        bai = json.loads((self.ra_thu_dir / "bai.json").read_text())
        self.assertEqual((bai["topic_tag"], bai["giong_ai"]), ("PlayStation", False))
        self.assertTrue(bai["anh"].endswith("anh.png"))

    def test_thu_ig_ghi_id_tai_la_cac_ma_noi_bang_phay(self):
        kq, cong, phu = self.chay("ig", "thu", phu=self.phu("ig", keo(6, 7, 8, 11)), cong=CongTG(keo(6, 7, 8, 11), self.su_kien))
        self.assertEqual(kq, 0)
        d = cong.cap_cuoi("ig")
        self.assertEqual(sorted(d["id_tai"].split(",")), sorted(dong_keo(h)["ma"] for h in (6, 7, 8, 11)))
        self.assertEqual(d["id_container"], "ig")

    def test_khong_api_chi_chon_dung_kiem_khong_giu_so_khong_nen_tang(self):
        kq, cong, phu = self.chay("fb", "thu", khong_api=True)
        self.assertEqual(kq, 0)
        self.assertEqual(self.su_kien, ["dung"])
        self.assertEqual(cong.dong, {})
        self.assertTrue((self.ra_thu_dir / "caption.txt").exists())

    # ---- pha that
    def test_that_fb_cong_khai_dung_1_lan_ghi_da_dang_khong_ghi_de_id_tai(self):
        kls = []
        kq, cong, phu = self.chay("fb", "that", phu=self.phu("fb", kiem_lai=lambda muc, g: (kls.append((muc, g)), ([], []))[1]))
        self.assertEqual(kq, 0)
        self.assertEqual([e for e in self.su_kien if e in ("chuan_bi", "cong_khai")], ["chuan_bi", "cong_khai"])
        self.assertEqual(self.su_kien.count("cong_khai"), 1)
        d = cong.cap_cuoi("fb")
        self.assertEqual((d["trang_thai"], d["id_bai"], d["link"]), ("da_dang", "VID1", "https://www.facebook.com/reel/VID1/"))
        self.assertEqual(d["id_tai"], dong_keo(4)["ma"])        # S12: ma game KHONG bi ghi de boi ID Graph
        self.assertEqual(d["id_container"], "fb")
        self.assertTrue(d["gio_cong_khai"])
        self.assertEqual(self.ngu, [30 * 60.0])                  # ngu toi 19:00
        muc, gio_ = kls[0]
        self.assertEqual((len(muc), gio_), (5, gio("fb")))
        self.assertTrue(all(m["gia_dung_y"] and set(m) == {"ten", "pid", "loc", "gia_cuc_bo", "endTime", "gia_dung_y", "gia_goc", "giam", "tien"} for m in muc))
        self.assertEqual(len(self.ntfy_tin), 1)

    def test_that_threads_va_ig_chay_tron(self):
        for kenh in ("ig", "threads"):
            self.su_kien.clear()
            d = keo(6, 7, 8, 11)
            kq, cong, phu = self.chay(kenh, "that", phu=self.phu(kenh, d), cong=CongTG(d, self.su_kien))
            self.assertEqual(kq, 0, kenh)
            self.assertEqual(self.su_kien.count("cong_khai"), 1)
            self.assertEqual(cong.cap_cuoi(kenh)["trang_thai"], "da_dang")

    def test_that_kiem_lai_thay_doi_thi_bo_khung_khong_cong_khai(self):
        kq, cong, phu = self.chay("fb", "that", phu=self.phu("fb", kiem_lai=lambda muc, g: (["gia doi 4.79 -> 4.80"], [])))
        self.assertEqual(kq, 3)
        self.assertNotIn("cong_khai", self.su_kien)
        self.assertEqual(cong.cap_cuoi("fb")["trang_thai"], "bo")
        self.assertEqual(len(self.ntfy_loi), 1)

    def test_s2_kiem_lai_that_gia_doi_0_01_bi_chan(self):
        d = keo()
        kq = chon.chon_fb(boi("fb", d))
        t = Trang(d)

        def mang(method, url, **kw):
            return P(200, raw=t(url).encode(), headers={"content-type": "text/html"})
        with mock.patch.object(http, "gui", mang), mock.patch.object(gia.time, "sleep", lambda s: None):
            self.assertEqual(gia.kiem_lai(kq["kiem_lai"], gio("fb")), ([], []))
            link = dong_keo(4)["link"]
            t.ghi_de[link] = t.dung(link, con="$4.80")
            van_de, _ = gia.kiem_lai(kq["kiem_lai"], gio("fb"))
        self.assertEqual(len(van_de), 1)
        self.assertIn("gia doi", van_de[0])

    def test_s16_qua_han_cong_khai_sau_kiem_lai_thi_that_bai_khong_cong_khai(self):
        def cham(muc, g):
            self.t += dt.timedelta(minutes=20)
            return [], []
        kq, cong, phu = self.chay("fb", "that", phu=self.phu("fb", kiem_lai=cham))
        self.assertEqual(kq, 3)
        self.assertNotIn("cong_khai", self.su_kien)
        d = cong.cap_cuoi("fb")
        self.assertEqual(d["trang_thai"], "that_bai")
        self.assertIn("han cong khai", d["loi"])

    def test_chay_qua_som_thi_dung_truoc_giu_dang(self):
        kq, cong, phu = self.chay("fb", "that", truoc_gio=dt.timedelta(minutes=50))
        self.assertEqual(kq, 3)
        self.assertNotIn("giu_dang", self.su_kien)
        self.assertEqual(cong.dong, {})
        self.assertTrue(any("qua som" in str(a) for a in self.ntfy_loi))

    # ---- giu dang / nhuong / loi
    def test_giu_dang_that_bai_thi_khong_goi_nen_tang(self):
        cong = CongTG(su_kien=self.su_kien)
        cong.giu_dang("2026-11-02", "fb-gia", "fb", "that", None, "s")
        self.su_kien.clear()
        kq, cong, phu = self.chay("fb", "that", cong=cong)
        self.assertEqual(kq, 3)
        self.assertNotIn("chuan_bi", self.su_kien)
        self.assertNotIn("cong_khai", self.su_kien)
        self.assertEqual(cong.cap_cuoi("fb")["trang_thai"], "dang_dang")        # luot khac giu: KHONG dong vao dong cua ho

    def test_danh_tinh_lech_thi_dung_truoc_giu_dang(self):
        nen = NenGia(self.su_kien, danh_tinh_loi=chung.LoiDang("danh tinh fb lech dich.json"))
        kq, cong, phu = self.chay("fb", "that", phu=self.phu("fb", nen=nen))
        self.assertEqual(kq, 3)
        self.assertNotIn("giu_dang", self.su_kien)
        self.assertNotIn("chuan_bi", self.su_kien)

    def test_s7_dua_chon_trung_game_voi_dong_som_hon_thi_nhuong_truoc_nen_tang(self):
        som = dict(dang="x-goc", kenh="x", trang_thai="da_dang", id_tai=dong_keo(4)["ma"])
        cong = CongTG(su_kien=self.su_kien, sau_giu=[dict(som, trang_thai="dang_dang")])
        kq, cong, phu = self.chay("fb", "that", cong=cong)
        self.assertEqual(kq, 0)        # dong dang_dang xuat hien SAU giu_dang cua minh (luc lon hon) -> minh giu, khong nhuong
        self.su_kien.clear()           # dong kia co luc SOM hon luc cua minh -> minh nhuong
        som2 = dict(som, trang_thai="dang_dang", luc="2026-11-02T09:00:00+00:00")
        cong2 = CongTG(su_kien=self.su_kien, sau_giu=[som2])
        kq, cong2, phu = self.chay("fb", "that", cong=cong2)
        self.assertEqual(kq, 3)
        self.assertNotIn("chuan_bi", self.su_kien)
        d = cong2.cap_cuoi("fb")
        self.assertEqual(d["trang_thai"], "that_bai")
        self.assertIn("trung game", d["loi"])

    def test_s7_dong_khac_that_bai_hoac_khac_game_khong_lam_nhuong(self):
        for row in (dict(dang="x-goc", kenh="x", trang_thai="that_bai", id_tai=dong_keo(4)["ma"], luc="2026-11-02T09:00:00+00:00"),
                    dict(dang="x-goc", kenh="x", trang_thai="da_dang", id_tai="CUSA99999_00|khac", luc="2026-11-02T09:00:00+00:00"),
                    dict(dang="top5", kenh="x", trang_thai="da_dang", id_tai=dong_keo(4)["ma"], luc="2026-11-02T09:00:00+00:00")):
            self.su_kien.clear()
            kq, cong, phu = self.chay("fb", "that", cong=CongTG(su_kien=self.su_kien, sau_giu=[row]))
            self.assertEqual(kq, 0, row)

    def test_s7_khong_doc_lai_duoc_dong_cua_minh_thi_nhuong(self):
        cong = CongTG(su_kien=self.su_kien)
        cong.doc_dang_goc = cong.doc_dang
        cong.doc_dang = lambda tu, den=None, che_do=None: [r for r in cong.doc_dang_goc(tu, den, che_do) if r.get("dang") != "fb-gia"]
        kq, cong, phu = self.chay("fb", "that", cong=cong)
        self.assertEqual(kq, 3)
        self.assertNotIn("chuan_bi", self.su_kien)

    def test_s8_lich_su_noi_bat_khong_doc_duoc_thi_khong_dang(self):
        kq, cong, phu = self.chay("fb", "that", phu=self.phu("fb", nb=NB(canh_bao="CANH BAO: khong doc duoc lich su")))
        self.assertEqual(kq, 3)
        self.assertEqual(self.su_kien, [])
        self.assertEqual(cong.dong, {})

    def test_s15_loi_truoc_tac_dung_phu_va_loi_sau_tao_tai_nguyen_deu_that_bai(self):
        kq, cong, phu = self.chay("fb", "that", phu=self.phu("fb", nen=NenGia(self.su_kien, loi_chuan_bi=chung.LoiDang("upload FB hong"))))
        self.assertEqual(kq, 1)
        d = cong.cap_cuoi("fb")
        self.assertEqual((d["trang_thai"], d["id_bai"]), ("that_bai", "VID1"))       # tai nguyen mo coi (khong cong khai)
        self.assertNotIn("cong_khai", self.su_kien)

    def test_s15_loi_cong_khai_khong_ro_thi_khong_ro_khong_dang_lai(self):
        for loi, mong in ((chung.LoiDang("mang dut", khong_ro=True), "khong_ro"), (RuntimeError("boom"), "khong_ro"),
                          (chung.LoiDang("Meta 400 ro rang", khong_ro=False), "that_bai")):
            self.su_kien.clear()
            kq, cong, phu = self.chay("fb", "that", phu=self.phu("fb", nen=NenGia(self.su_kien, loi_cong_khai=loi)))
            self.assertEqual(kq, 1)
            self.assertEqual(cong.cap_cuoi("fb")["trang_thai"], mong, loi)
            self.assertEqual(self.su_kien.count("cong_khai"), 1)

    def test_loi_ghi_so_sau_khi_da_dang_thi_bao_nhung_khong_dang_lai(self):
        cong = CongTG(su_kien=self.su_kien)
        cong.hong_ghi_sau = lambda kenh, truong: truong.get("trang_thai") == "da_dang"
        kq, cong, phu = self.chay("fb", "that", cong=cong)
        self.assertEqual(kq, 1)
        self.assertEqual(self.su_kien.count("cong_khai"), 1)
        self.assertTrue(any("ghi sổ lỗi" in str(a) for a in self.ntfy_loi))

    def test_cong_tin_gia_truot_thi_khong_giu_so(self):
        with mock.patch.object(chu, "chu_fb", lambda sv: "Monster Hunter Rise còn 500 nghìn ở Store Mỹ"):
            kq, cong, phu = self.chay("fb", "that")
        self.assertEqual(kq, 3)
        self.assertEqual(self.su_kien, [])
        self.assertTrue(any("cong tin gia" in str(a) for a in self.ntfy_loi))

    def test_kiem_py_khong_dat_thi_khong_dang(self):
        kiem = lambda k, ra, dl: {"dat": False, "phep": [{"ten": "K2 am thanh", "dat": False, "chi_tiet": "dinh -0.5"}]}
        kq, cong, phu = self.chay("fb", "that", phu=self.phu("fb", kiem=kiem))
        self.assertEqual(kq, 3)
        self.assertNotIn("giu_dang", self.su_kien)

    def test_gia_the_cu_thi_khong_dang(self):
        pathlib.Path(self.gia_the).write_text(json.dumps({"ngay": "2026-10-20", "vung": {"US": {}}}))
        kq, cong, phu = self.chay("fb", "that")
        self.assertEqual(kq, 3)
        self.assertEqual(self.su_kien, [])

    def test_khong_co_dong_keo_thi_khong_dang(self):
        with mock.patch.object(mxh.x_goc, "doc_keo_cho", lambda *a, **k: []):
            kq, cong, phu = self.chay("fb", "that")
        self.assertEqual(kq, 3)


# ================================================================ sua sau soi Sol (P1-P3)
class CongDem(CongTG):
    """CongTG + ghi lai moi cap_nhat_dang co neu_trang_thai; `tu_choi` = trang_thai dich bi tu choi (tra 0 nhu luot khac da doi dong)."""

    def __init__(self, *a, tu_choi=(), **kw):
        super().__init__(*a, **kw)
        self.goi_cn, self.tu_choi = [], tu_choi

    def cap_nhat_dang(self, ngay, dang, kenh, che_do, neu_trang_thai=None, **truong):
        self.goi_cn.append((neu_trang_thai, dict(truong)))
        if neu_trang_thai is not None and truong.get("trang_thai") in self.tu_choi:
            return 0
        return super().cap_nhat_dang(ngay, dang, kenh, che_do, neu_trang_thai, **truong)


class LuongSol(unittest.TestCase):
    setUp, ngu_gia, phu, args, chay = Luong.setUp, Luong.ngu_gia, Luong.phu, Luong.args, Luong.chay

    # ---- P1-a
    def test_p1a_khong_doi_duoc_sang_chuan_bi_xong_thi_dung_khong_cong_khai(self):
        cong = CongDem(su_kien=self.su_kien, tu_choi=("chuan_bi_xong",))
        kq, cong, phu = self.chay("fb", "that", cong=cong)
        self.assertEqual(kq, 3)
        self.assertNotIn("cong_khai", self.su_kien)
        self.assertEqual(cong.cap_cuoi("fb")["trang_thai"], "that_bai")        # doi_that_bai co dieu kien, khong ghi de dong cua luot khac

    def test_p1a_dong_bi_doi_truoc_cong_khai_thi_dung_va_khong_ghi_de(self):
        for doi in (dict(trang_thai="khong_ro"), dict(id_bai="TAI-NGUYEN-KHAC"), dict(trang_thai="that_bai")):
            self.su_kien.clear()
            cong = CongTG(su_kien=self.su_kien)

            def kiem_lai(muc, g, cong=cong, doi=doi):
                cong.cap_cuoi("fb").update(doi)           # luot khac / nguoi doi dong NGAY truoc cong khai
                return [], []
            kq, cong, phu = self.chay("fb", "that", cong=cong, phu=self.phu("fb", kiem_lai=kiem_lai))
            self.assertEqual(kq, 3, doi)
            self.assertTrue(self.ntfy_loi)
            self.assertNotIn("cong_khai", self.su_kien)
            d = cong.cap_cuoi("fb")
            for k, v in doi.items():
                self.assertEqual(d[k], v, doi)            # KHONG bi ghi de

    def test_p1a_cap_nhat_sau_cong_khai_dung_neu_trang_thai_chuan_bi_xong(self):
        cong = CongDem(su_kien=self.su_kien)
        kq, cong, phu = self.chay("fb", "that", cong=cong)
        self.assertEqual(kq, 0)
        cuoi = [c for c in cong.goi_cn if c[1].get("trang_thai") == "da_dang"]
        self.assertEqual(len(cuoi), 1)
        self.assertEqual(cuoi[0][0], "chuan_bi_xong")
        self.su_kien.clear()
        cong = CongDem(su_kien=self.su_kien)
        kq, cong, phu = self.chay("fb", "that", cong=cong, phu=self.phu("fb", nen=NenGia(self.su_kien, loi_cong_khai=chung.LoiDang("mang", khong_ro=True))))
        self.assertEqual(kq, 1)
        kr = [c for c in cong.goi_cn if c[1].get("trang_thai") == "khong_ro"]
        self.assertEqual([c[0] for c in kr], ["chuan_bi_xong"])
        self.assertEqual(cong.cap_cuoi("fb")["trang_thai"], "khong_ro")

    def test_p1a_da_dang_ghi_khong_duoc_vi_dong_khong_con_chuan_bi_xong_thi_bao_loi(self):
        cong = CongDem(su_kien=self.su_kien, tu_choi=("da_dang",))
        kq, cong, phu = self.chay("fb", "that", cong=cong)
        self.assertEqual(kq, 1)
        self.assertEqual(self.su_kien.count("cong_khai"), 1)
        self.assertTrue(any("ghi sổ lỗi" in str(a) for a in self.ntfy_loi))

    # ---- P1-b
    def nhuong(self, mine_dang, mine_luc, khac, **hang):
        cong = CongTG()
        cong.dong[("2026-11-02", mine_dang, "x", "that")] = dict(ngay="2026-11-02", dang=mine_dang, kenh="x", che_do="that", trang_thai="dang_dang", luc=mine_luc)
        row = dict(ngay="2026-11-02", dang=khac, kenh="y", che_do="that", id_tai="PPSA1_00|a")
        row.update(hang)
        cong.dong[("2026-11-02", khac, "y", "that")] = row
        return mxh.nhuong_neu_trung(cong, NGAY, mine_dang, "x", "that", ["PPSA1_00|a"])

    def test_p1b_dong_khac_da_dang_khong_ro_chuan_bi_xong_luon_chan_ke_ca_luc_muon_hon(self):
        for tt in ("khong_ro", "da_dang", "chuan_bi_xong"):
            ly = self.nhuong("fb-gia", "2026-11-02T10:00:00+00:00", "x-goc", trang_thai=tt, luc="2026-11-02T11:00:00+00:00")
            self.assertIsNotNone(ly, tt)
            self.assertIn(tt, ly)
            self.assertIsNotNone(self.nhuong("fb-gia", "2026-11-02T10:00:00+00:00", "x-goc", trang_thai=tt, luc=None), tt)

    def test_p1b_dang_dang_chi_so_luc(self):
        mine = "2026-11-02T10:00:00+00:00"
        self.assertIsNone(self.nhuong("fb-gia", mine, "x-goc", trang_thai="dang_dang", luc="2026-11-02T11:00:00+00:00"))       # muon hon -> minh thang
        self.assertIsNotNone(self.nhuong("fb-gia", mine, "x-goc", trang_thai="dang_dang", luc="2026-11-02T09:00:00+00:00"))     # som hon -> minh nhuong
        # bang nhau: dang theo chu cai, ben LON HON nhuong
        self.assertIsNotNone(self.nhuong("ig-gia", mine, "fb-gia", trang_thai="dang_dang", luc=mine))
        self.assertIsNone(self.nhuong("fb-gia", mine, "ig-gia", trang_thai="dang_dang", luc=mine))

    def test_p1b_that_bai_bo_hoac_khac_game_khong_chan(self):
        mine = "2026-11-02T10:00:00+00:00"
        for tt in ("that_bai", "bo"):
            self.assertIsNone(self.nhuong("fb-gia", mine, "x-goc", trang_thai=tt, luc=mine))
        self.assertIsNone(self.nhuong("fb-gia", mine, "x-goc", trang_thai="da_dang", luc=mine, id_tai="CUSA9_00|khac"))

    # ---- P2-a
    def test_p2a_han_tuyet_doi_duoc_truyen_cho_nen_tang(self):
        kq, cong, phu = self.chay("fb", "that")
        self.assertEqual(kq, 0)
        self.assertEqual(phu.nen_gia.han, gio("fb") + dt.timedelta(minutes=15))

    def test_p2a_kiem_han_ngay_truoc_post_khong_post_khi_qua_han(self):
        self.t = gio("fb")
        han = self.t - dt.timedelta(seconds=1)
        bia = pathlib.Path(tempfile.mkdtemp()) / "bia.jpg"
        bia.write_bytes(b"J")
        tk_ig = {"ig_user_id": "IGU1", "page_token": "EAAIGTOKENGIA1234567890abcdef"}
        tk_th = {"threads_user_id": "THU1", "token": "THTOKENGIA1234567890abcdef"}
        casos = (("fb", lambda: mxh.NenFB(dict(TOKEN_FB)).cong_khai({"text": "c", "bia": bia}, "VID9", han),
                  NenThat.mang_fb_cong_khai(NenThat(), published=True), "video_reels"),
                 ("ig", lambda: mxh.NenIG(tk_ig, ZK).cong_khai({}, "CNT1", han),
                  Mang().them("GET", "/CNT1", P(200, {"status_code": "FINISHED"})), "media_publish"),
                 ("threads", lambda: mxh.NenThreads(tk_th, ZK).cong_khai({}, "CNT1", han),
                  Mang().them("GET", "/CNT1", P(200, {"status": "FINISHED"})), "threads_publish"))
        for ten, f, m, post in casos:
            with mock.patch.object(http, "gui", m), self.assertRaises(chung.LoiDang) as cm:
                f()
            self.assertFalse(cm.exception.khong_ro, ten)
            self.assertIn("qua han", str(cm.exception))
            self.assertFalse(any(mt == "POST" and post in u for mt, u, kw in m.goi), ten)      # KHONG POST
            self.assertTrue(any(mt == "GET" for mt, u, kw in m.goi), ten)                       # kiem han sau moi GET

    def test_p2a_con_han_thi_van_post(self):
        self.t = gio("fb")
        bia = pathlib.Path(tempfile.mkdtemp()) / "bia.jpg"
        bia.write_bytes(b"J")
        m = NenThat.mang_fb_cong_khai(NenThat())
        with mock.patch.object(http, "gui", m):
            kq = mxh.NenFB(dict(TOKEN_FB)).cong_khai({"text": "c", "bia": bia}, "VID9", self.t + dt.timedelta(minutes=15))
        self.assertEqual(kq["id_bai"], "VID9")

    def test_p2a_qua_han_o_nen_tang_thi_that_bai_khong_khong_ro(self):
        kq, cong, phu = self.chay("fb", "that", phu=self.phu("fb", nen=NenGia(self.su_kien, loi_cong_khai=chung.LoiDang("qua han cong khai ... KHONG goi cong khai"))))
        self.assertEqual(kq, 1)
        self.assertEqual(cong.cap_cuoi("fb")["trang_thai"], "that_bai")

    # ---- P2-b
    def kiem_that(self, rc, out):
        r = types.SimpleNamespace(returncode=rc, stdout=out, stderr="")
        with mock.patch.object(mxh.subprocess, "run", return_value=r):
            return mxh.kiem_that("fb", "ra", "dl.json")

    def test_p2b_kiem_that_chi_dat_khi_ma_0_va_dict_va_dat_true(self):
        ok = json.dumps({"dat": True, "phep": []})
        self.assertEqual(self.kiem_that(0, ok)["dat"], True)
        for rc, out in ((1, ok), (0, json.dumps({"dat": False, "phep": [{"ten": "K2", "dat": False, "chi_tiet": "dinh"}]})), (1, json.dumps({"dat": False, "phep": []})),
                        (0, json.dumps({"phep": []})), (0, json.dumps({"dat": "true"})), (0, json.dumps([1])), (0, "khong phai json"), (0, "")):
            with self.assertRaises(mxh.KhongDang, msg=(rc, out)):
                self.kiem_that(rc, out)

    # ---- P2-d
    def test_p2d_kiem_goc_giam_phat_hien_goc_hoac_giam_doi(self):
        d = keo()
        kq = chon.chon_fb(boi("fb", d))
        t = Trang(d)
        self.assertEqual(mxh.kiem_goc_giam(kq["kiem_lai"], t), [])
        link = dong_keo(4)["link"]
        t.ghi_de[link] = t.dung(link, goc="$44.99")
        v = mxh.kiem_goc_giam(kq["kiem_lai"], t)
        self.assertTrue(any("gia goc doi" in x for x in v) and any("% giam doi" in x for x in v), v)
        t.ghi_de[link] = None
        self.assertTrue(any("khong doc lai duoc" in x for x in mxh.kiem_goc_giam(kq["kiem_lai"], t)))
        self.assertTrue(mxh.kiem_goc_giam([{"ten": "x", "pid": "p", "loc": "en-us"}], t))        # thieu truong = van de

    def test_p2d_goc_doi_truoc_cong_khai_thi_that_bai_khong_cong_khai_co_ntfy(self):
        d = keo()
        link = dong_keo(4)["link"]
        phu = self.phu("fb")

        def kiem_lai(muc, g):
            phu.lay_trang.ghi_de[link] = phu.lay_trang.dung(link, goc="$44.99")      # goc doi SAU khi chon
            return [], []
        phu.kiem_lai = kiem_lai
        kq, cong, phu = self.chay("fb", "that", phu=phu)
        self.assertEqual(kq, 3)
        self.assertNotIn("cong_khai", self.su_kien)
        self.assertEqual(cong.cap_cuoi("fb")["trang_thai"], "that_bai")
        self.assertIn("gia goc", cong.cap_cuoi("fb")["loi"])
        self.assertTrue(self.ntfy_loi)

    # ---- P2-e
    def test_p2e_cong_truot_thi_thu_ung_vien_khac_khong_dung_ca_luot(self):
        thuc = chu.cong

        def cong_gia(kenh, text, sv):
            return ["dinh dang sai"] if "Monster Hunter" in text else thuc(kenh, text, sv)
        with mock.patch.object(chu, "cong", cong_gia):
            kq, cong, phu = self.chay("fb", "thu", khong_api=True)
        self.assertEqual(kq, 0)
        bai = json.loads((self.ra_thu_dir / "bai.json").read_text())
        self.assertNotIn("Monster Hunter", bai["chu"])
        chon_json = json.loads((self.ra_thu_dir / "chon.json").read_text())
        self.assertEqual(chon_json["lan_chon"], 2)
        self.assertTrue(any("cong tin gia truot" in b["ly"] for b in chon_json["bo"]))

    def test_p2e_cong_truot_het_lan_thu_thi_khong_dang(self):
        with mock.patch.object(chu, "cong", lambda k, t, s: ["luon sai"]):
            kq, cong, phu = self.chay("fb", "that")
        self.assertEqual(kq, 3)
        self.assertEqual(self.su_kien, [])
        self.assertTrue(any("cong tin gia truot" in str(a) for a in self.ntfy_loi))


class DinhDangTien(unittest.TestCase):
    def test_nghin_dung_giu_nguyen_gia_tri_khi_doc_lai_bang_tien_vnd(self):
        from dang.chay import tien_vnd
        for v, s in ((460000, "460 nghìn"), (72000, "72 nghìn"), (999000, "999 nghìn"), (1048000, "1.048.000đ"), (1000000, "1.000.000đ"),
                     (72480, "72.480đ"), (1234567, "1.234.567đ"), (50500, "50.500đ")):
            self.assertEqual(chon.nghin_dung(v), s)
            self.assertEqual(tien_vnd(f"con {chon.nghin_dung(v)}."), [v], v)
            self.assertEqual(tien_vnd(f"{chon.nghin_dung(v)}; xong"), [v], v)

    def sv_gia(self, gia, kia):
        sv = sv_fb()
        sv.update(gia_vnd=gia, gia_mua=[gia], gia_da_kiem=[gia, kia], re_hon={"ten": "Singapore", "vnd": kia - gia},
                  cua_hang=[{"ma": "SG", "ten": "Singapore", "vnd": kia}, {"ma": "US", "ten": "Mỹ", "vnd": gia}])
        return sv

    def test_fb_gia_lon_hon_1_trieu_va_khong_tron_nghin_duoc_cong_chap_nhan(self):
        from dang.chay import tien_vnd
        for gia, kia in ((1048000, 1328000), (72480, 150480), (1048000, 1500000)):
            sv = self.sv_gia(gia, kia)
            text = chu.dung_chu("fb", sv)["text"]
            self.assertEqual(tien_vnd(text.split("\n")[0]), [gia])
            self.assertIn(chon.nghin_dung(kia - gia), text)
            self.assertEqual(chu.cong("fb", text, sv), [], text)
            self.assertNotIn("triệu", text)

    def test_ig_gia_lon_hon_1_trieu_cap_ten_gia_dung_dinh_dang(self):
        sv = sv_ig(6, 7, 8, 11)
        sv["game"][0]["gia_vnd"] = 1048000
        sv["gia_mua"] = sorted({g["gia_vnd"] for g in sv["game"]})
        sv["gia_da_kiem"] = sv["gia_mua"]
        text = chu.dung_chu("ig", sv)["text"]
        self.assertIn("– 1.048.000đ", text)
        self.assertEqual(chu.cong("ig", text, sv), [], text)
        self.assertTrue(chu.cong("ig", text.replace("– 1.048.000đ", "– 1.084.000đ"), sv))

    def test_threads_gia_khong_tron_nghin(self):
        sv = sv_th()
        sv.update(gia_vnd=72480, gia_mua=[72480], gia_da_kiem=[72480])
        r = chu.dung_chu("threads", sv, NGAY)
        self.assertIn("72.480đ", r["text"])
        self.assertEqual(chu.cong("threads", r["text"], sv), [])


class CongNgoaiTe(unittest.TestCase):
    def test_p2c_doi_gia_game_hoac_gia_goc_thi_truot(self):
        sv = sv_fb()
        text = chu.dung_chu("fb", sv)["text"]
        self.assertEqual(chu.cong("fb", text, sv), [])
        a = chu.cong("fb", text.replace("$4,79", "$99,99"), sv)
        self.assertTrue(any("ngoai te" in l and "$99,99" in l for l in a), a)
        b = chu.cong("fb", text.replace("$39,99", "$999,99"), sv)
        self.assertTrue(any("ngoai te" in l and "$999,99" in l for l in b), b)
        self.assertTrue(chu.cong("fb", text.replace("1 thẻ $5", "1 thẻ $50"), sv))                 # menh gia the la

    def test_p2c_cac_ky_hieu_va_phan_tram(self):
        sv = sv_fb()
        text = chu.dung_chu("fb", sv)["text"]
        for them in ("giá HK$36,96", "giá S$6,60", "giá Rp 73.792", "giá 154 THB 154", "giá ฿154", "giá SGD 6.60", "giá US$4,79"):
            if them.startswith("giá US$4"):
                continue
            self.assertTrue(any("ngoai te" in l for l in chu.cong("fb", text + "\n" + them, sv)), them)
        self.assertTrue(any("phan tram" in l for l in chu.cong("fb", text.replace("88%", "80%"), sv)))
        self.assertTrue(any("phan tram" in l for l in chu.cong("fb", text + " Giảm thêm 10%", sv)))

    def test_p2c_threads_va_ig(self):
        sv = sv_th()
        text = chu.dung_chu("threads", sv, NGAY)["text"]
        self.assertEqual(chu.cong("threads", text, sv), [])
        self.assertTrue(any("ngoai te" in l for l in chu.cong("threads", text.replace("$14,99", "$1,99"), sv)))
        self.assertTrue(any("phan tram" in l for l in chu.cong("threads", text.replace("70%", "7%"), sv)))
        sv = sv_ig(6, 7, 8, 11)
        text = chu.dung_chu("ig", sv)["text"]
        self.assertTrue(any("ngoai te" in l for l in chu.cong("ig", text + "\nChi $5", sv)))


# ================================================================ sua sau soi Sol luot 2
class LuongSol2(unittest.TestCase):
    setUp, ngu_gia, phu, args, chay = Luong.setUp, Luong.ngu_gia, Luong.phu, Luong.args, Luong.chay

    def test_1_id_bai_bi_doi_trang_thai_van_chuan_bi_xong_thi_khong_ghi_gi_vao_so(self):
        cong = CongDem(su_kien=self.su_kien)
        dem = []

        def kiem_lai(muc, g):
            cong.cap_cuoi("fb")["id_bai"] = "TAI-NGUYEN-CUA-LUOT-KHAC"       # trang thai GIU chuan_bi_xong
            dem.append(len(cong.goi_cn))
            return [], []
        kq, cong, phu = self.chay("fb", "that", cong=cong, phu=self.phu("fb", kiem_lai=kiem_lai))
        self.assertEqual(kq, 3)
        self.assertNotIn("cong_khai", self.su_kien)
        self.assertEqual(len(cong.goi_cn), dem[0])                              # KHONG goi cap_nhat_dang nao sau do (khong doi_that_bai)
        d = cong.cap_cuoi("fb")
        self.assertEqual((d["trang_thai"], d["id_bai"]), ("chuan_bi_xong", "TAI-NGUYEN-CUA-LUOT-KHAC"))
        self.assertTrue(self.ntfy_loi)

    def test_2_x_goc_cung_game_xuat_hien_khong_ro_luc_ngu_thi_nhuong_that_bai_co_dieu_kien(self):
        cong = CongDem(su_kien=self.su_kien)
        phu = self.phu("fb")

        def ngu(s):
            self.ngu_gia(s)
            cong.them(dang="x-goc", kenh="x", trang_thai="khong_ro", id_tai=dong_keo(4)["ma"])
        phu.ngu = ngu
        kq, cong, phu = self.chay("fb", "that", cong=cong, phu=phu)
        self.assertEqual(kq, 3)
        self.assertNotIn("cong_khai", self.su_kien)
        d = cong.cap_cuoi("fb")
        self.assertEqual(d["trang_thai"], "that_bai")
        self.assertIn("kiem trung lan 2", d["loi"])
        self.assertIn(("chuan_bi_xong", "that_bai"), [(c[0], c[1].get("trang_thai")) for c in cong.goi_cn])
        self.assertTrue(any("trùng" in str(a) for a in self.ntfy_loi))

    def test_2_khong_trung_thi_van_dang(self):
        kq, cong, phu = self.chay("fb", "that")
        self.assertEqual(kq, 0)

    # ---- 4
    def test_4_gia_ban_doi_001_hoac_tien_te_doi_thi_that_bai_khong_cong_khai_co_ntfy(self):
        link = dong_keo(4)["link"]
        for ten, kw in (("gia ban", dict(con="$4.78")), ("tien te", dict(con="HK$4.79", goc="HK$39.99", tien="HKD"))):
            self.su_kien.clear()
            self.ntfy_loi.clear()
            phu = self.phu("fb")

            def kiem_lai(muc, g, phu=phu, kw=kw):
                phu.lay_trang.ghi_de[link] = phu.lay_trang.dung(link, **kw)
                return [], []
            phu.kiem_lai = kiem_lai
            kq, cong, phu = self.chay("fb", "that", phu=phu)
            self.assertEqual(kq, 3, ten)
            self.assertNotIn("cong_khai", self.su_kien)
            d = cong.cap_cuoi("fb")
            self.assertEqual(d["trang_thai"], "that_bai", ten)
            self.assertTrue(self.ntfy_loi, ten)

    def test_4_kiem_goc_giam_don_vi(self):
        d = keo()
        kq = chon.chon_fb(boi("fb", d))
        t = Trang(d)
        link = dong_keo(4)["link"]
        t.ghi_de[link] = t.dung(link, con="$4.78")
        self.assertTrue(any("gia ban doi" in v for v in mxh.kiem_goc_giam(kq["kiem_lai"], t)))
        t.ghi_de[link] = t.dung(link, con="HK$4.79", goc="HK$39.99", tien="HKD")
        self.assertTrue(any("tien te doi" in v for v in mxh.kiem_goc_giam(kq["kiem_lai"], t)))
        self.assertTrue(all(m["tien"] for m in kq["kiem_lai"]))


class CongVaiTro(unittest.TestCase):
    def test_3_fb_doi_vai_tro_gia_hoac_the_hoac_phan_tram_thi_truot(self):
        sv = sv_fb()
        text = chu.dung_chu("fb", sv)["text"]
        self.assertEqual(chu.cong("fb", text, sv), [])
        for ten, a, b in (("gia ban $4,79 -> $39,99", "giá niêm yết $4,79", "giá niêm yết $39,99"),
                          ("gia goc $39,99 -> $4,79", "gốc $39,99)", "gốc $4,79)"),
                          ("the $5 -> $4,79", "1 thẻ $5", "1 thẻ $4,79"), ("so tam 1 -> 9", "1 thẻ $5", "9 thẻ $5"),
                          ("88% -> 88,99%", "Giảm 88%", "Giảm 88,99%"), ("88% -> 80%", "Giảm 88%", "Giảm 80%")):
            self.assertIn(a, text, ten)
            loi = chu.cong("fb", text.replace(a, b), sv)
            self.assertTrue(loi, ten)

    def test_3_phan_tram_thap_phan_bi_bat(self):
        sv = sv_fb()
        text = chu.dung_chu("fb", sv)["text"].replace("Giảm 88%", "Giảm 88,99%")
        self.assertTrue(any("phan tram" in l and "88,99" in l for l in chu.cong("fb", text, sv)))

    def test_3_fb_thieu_cum_gia_goc_hoac_ten_vung_thi_truot(self):
        sv = sv_fb()
        text = chu.dung_chu("fb", sv)["text"]
        self.assertTrue(any("cum bat buoc" in l for l in chu.cong("fb", text.replace("ở Store Mỹ", "ở Store Singapore"), sv)))
        han = chon.han_cau(sv["han"])
        self.assertIn(f"tới {han}", text)
        self.assertTrue(any("cum bat buoc" in l for l in chu.cong("fb", text.replace(f"tới {han}", "tới 03:00 ngày 1/1"), sv)))

    def test_3_ig_han_va_threads_gia_hien_the(self):
        sv = sv_ig(6, 7, 8, 11)
        text = chu.dung_chu("ig", sv)["text"]
        self.assertEqual(chu.cong("ig", text, sv), [])
        self.assertTrue(any("cum bat buoc" in l for l in chu.cong("ig", text.replace("giảm tới 14:59 ngày 5/11", "giảm tới 15:59 ngày 5/11"), sv)))
        sv = sv_th()
        text = chu.dung_chu("threads", sv, NGAY)["text"]
        self.assertEqual(chu.cong("threads", text, sv), [])
        for a, b in (("Cả hai đang $14,99", "Cả hai đang $4,99"), ("1 thẻ $10 + 1 thẻ $5 vừa khít với giá niêm yết", "1 thẻ $10 + 1 thẻ $5 vừa khít")):
            self.assertIn(a, text)
            self.assertTrue(chu.cong("threads", text.replace(a, b), sv), a)


# ================================================================ nen tang that (Mang gia)
class NenThat(unittest.TestCase):
    def setUp(self):
        for p in (mock.patch.object(chung, "ngu", lambda s: None),):
            p.start()
            self.addCleanup(p.stop)

    def goi(self, mang, f):
        with mock.patch.object(http, "gui", mang):
            return f()

    def mang_fb_cong_khai(self, finish_ok=True, published=True):
        m = Mang()
        m.them("GET", "/me", P(200, {"id": "PAGE1"}))

        def doc(mt, u, kw):
            f = kw.get("params", {}).get("fields", "")
            if f == "status":
                return P(200, {"status": {"video_status": "ready"}})
            return P(200, {"published": published, "status": {}})
        m.them("GET", "/VID9", doc)
        m.them("POST", "/PAGE1/video_reels", P(200, {"success": finish_ok}))
        m.them("POST", "/VID9/thumbnails", P(200, {"success": True}))
        return m

    def test_s12_fb_cong_khai_gui_dung_id_graph_khong_nhan_ai_va_s17_xac_nhan(self):
        bia = pathlib.Path(tempfile.mkdtemp()) / "bia.jpg"
        bia.write_bytes(b"J")
        m = self.mang_fb_cong_khai()
        nen = mxh.NenFB(dict(TOKEN_FB))
        kq = self.goi(m, lambda: nen.cong_khai({"text": "caption", "bia": bia}, "VID9"))
        self.assertEqual((kq["id_bai"], kq["link"]), ("VID9", "https://www.facebook.com/reel/VID9/"))
        fin = next(kw for mt, u, kw in m.goi if mt == "POST" and u.endswith("/PAGE1/video_reels"))["form"]
        self.assertEqual((fin["video_id"], fin["video_state"], fin["upload_phase"], fin["description"]), ("VID9", "PUBLISHED", "finish", "caption"))
        self.assertNotIn("is_ai_generated", fin)

    def test_s17_fb_chua_xac_nhan_published_thi_khong_ro(self):
        bia = pathlib.Path(tempfile.mkdtemp()) / "bia.jpg"
        bia.write_bytes(b"J")
        m = self.mang_fb_cong_khai(published=False)
        nen = mxh.NenFB(dict(TOKEN_FB))
        with self.assertRaises(chung.LoiDang) as cm:
            self.goi(m, lambda: nen.cong_khai({"text": "c", "bia": bia}, "VID9"))
        self.assertTrue(cm.exception.khong_ro)

    def test_fb_finish_khong_success_thi_khong_ro(self):
        bia = pathlib.Path(tempfile.mkdtemp()) / "bia.jpg"
        bia.write_bytes(b"J")
        nen = mxh.NenFB(dict(TOKEN_FB))
        with self.assertRaises(chung.LoiDang) as cm:
            self.goi(self.mang_fb_cong_khai(finish_ok=False, published=False), lambda: nen.cong_khai({"text": "c", "bia": bia}, "VID9"))
        self.assertTrue(cm.exception.khong_ro)

    def test_fb_upload_het_han_thi_loi_chac_chan_chua_dang(self):
        bia = pathlib.Path(tempfile.mkdtemp()) / "bia.jpg"
        bia.write_bytes(b"J")
        m = Mang()
        m.them("GET", "/me", P(200, {"id": "PAGE1"}))
        m.them("GET", "/VID9", P(200, {"status": {"video_status": "expired"}}))
        with self.assertRaises(chung.LoiDang) as cm:
            self.goi(m, lambda: mxh.NenFB(dict(TOKEN_FB)).cong_khai({"text": "c", "bia": bia}, "VID9"))
        self.assertFalse(cm.exception.khong_ro)
        self.assertFalse(any(mt == "POST" for mt, u, kw in m.goi))

    def test_ig_cong_khai_dung_container_va_s17_co_id_la_da_dang(self):
        tk = {"ig_user_id": "IGU1", "page_token": "EAAIGTOKENGIA1234567890abcdef"}
        m = Mang()
        m.them("GET", "/CNT1", P(200, {"status_code": "FINISHED"}))
        m.them("POST", "/IGU1/media_publish", P(200, {"id": "MED1"}))
        m.them("GET", "/MED1", P(200, {"permalink": "https://www.instagram.com/reel/abc/"}))
        kq = self.goi(m, lambda: mxh.NenIG(tk, ZK).cong_khai({}, "CNT1"))
        self.assertEqual((kq["id_bai"], kq["link"]), ("MED1", "https://www.instagram.com/reel/abc/"))
        pub = next(kw for mt, u, kw in m.goi if u.endswith("/media_publish"))["form"]
        self.assertEqual(pub["creation_id"], "CNT1")
        # thieu permalink van la da_dang
        m2 = Mang().them("GET", "/CNT1", P(200, {"status_code": "FINISHED"})).them("POST", "/IGU1/media_publish", P(200, {"id": "MED1"})).them("GET", "/MED1", P(500))
        kq = self.goi(m2, lambda: mxh.NenIG(tk, ZK).cong_khai({}, "CNT1"))
        self.assertEqual((kq["id_bai"], kq["link"]), ("MED1", None))

    def test_ig_container_khong_finished_thi_chua_dang(self):
        tk = {"ig_user_id": "IGU1", "page_token": "EAAIGTOKENGIA1234567890abcdef"}
        m = Mang().them("GET", "/CNT1", P(200, {"status_code": "IN_PROGRESS"}))
        with self.assertRaises(chung.LoiDang) as cm:
            self.goi(m, lambda: mxh.NenIG(tk, ZK).cong_khai({}, "CNT1"))
        self.assertFalse(cm.exception.khong_ro)

    def test_threads_cong_khai_loi_mang_khi_publish_la_khong_ro(self):
        tk = {"threads_user_id": "THU1", "token": "THTOKENGIA1234567890abcdef"}
        m = Mang()
        m.them("GET", "/CNT1", P(200, {"status": "FINISHED"}))
        m.them("POST", "/THU1/threads_publish", http.LoiMang("mat ket noi"))
        with self.assertRaises(chung.LoiDang) as cm:
            self.goi(m, lambda: mxh.NenThreads(tk, ZK).cong_khai({}, "CNT1"))
        self.assertTrue(cm.exception.khong_ro)

    def test_threads_chuan_bi_gui_alt_text_topic_tag_va_image_url(self):
        tk = {"threads_user_id": "THU1", "token": "THTOKENGIA1234567890abcdef"}
        tep = pathlib.Path(tempfile.mkdtemp()) / "anh.png"
        tep.write_bytes(b"PNG")
        m = Mang()
        m.them("POST", "media/presign", P(200, {"uploadUrl": "https://up.test/put?sig=BIMATUP12345", "publicUrl": "https://cdn.test/BIMAT-ANH.png"}))
        m.them("PUT", "up.test", P(200))
        m.them("GET", "cdn.test", P(200, headers={"content-type": "image/png"}, raw=b"PNG"))
        m.them("POST", "/THU1/threads", P(200, {"id": "CNT7"}))
        m.them("GET", "/CNT7", P(200, {"status": "FINISHED"}))
        luu = []
        kq = self.goi(m, lambda: mxh.NenThreads(tk, ZK).chuan_bi({"anh": tep, "text": "T", "alt": "mo ta anh", "ngay": "2026-11-02"}, "thu", lambda **kw: luu.append(kw)))
        form = next(kw for mt, u, kw in m.goi if mt == "POST" and u.endswith("/THU1/threads"))["form"]
        self.assertEqual((form["media_type"], form["image_url"], form["alt_text"], form["topic_tag"], form["text"]),
                         ("IMAGE", "https://cdn.test/BIMAT-ANH.png", "mo ta anh", "PlayStation", "T"))
        self.assertEqual((kq["id_bai"], luu), ("CNT7", [{"id_bai": "CNT7"}]))

    def test_zernio_tai_tep_va_tuong_thich_nguoc(self):
        tep = pathlib.Path(tempfile.mkdtemp()) / "v.mp4"
        tep.write_bytes(b"VIDEO")
        m = Mang()
        m.them("POST", "media/presign", P(200, {"uploadUrl": "https://up.test/put?sig=BIMATUP12345", "publicUrl": "https://cdn.test/BIMAT.mp4"}))
        m.them("PUT", "up.test", P(200))
        url = self.goi(m, lambda: zernio.tai_tep(ZK, tep, "v.mp4", "video/mp4"))
        self.assertEqual(url, "https://cdn.test/BIMAT.mp4")
        body = next(kw for mt, u, kw in m.goi if "presign" in u)["json_body"]
        self.assertEqual((body["filename"], body["contentType"], body["size"]), ("v.mp4", "video/mp4", 5))
        self.assertNotIn("BIMATUP12345", chung.che("https://up.test/put?sig=BIMATUP12345"))
        # tai_anh cu giu nguyen hanh vi
        png = tep.with_name("a.png")
        png.write_bytes(b"PNG")
        self.goi(m, lambda: zernio.tai_anh(ZK, png, "a.png"))
        self.assertEqual([kw["json_body"]["contentType"] for mt, u, kw in m.goi if "presign" in u], ["video/mp4", "image/png"])

    def test_zernio_tai_tep_loi_la_chua_tao_bai(self):
        tep = pathlib.Path(tempfile.mkdtemp()) / "v.mp4"
        tep.write_bytes(b"V")
        with self.assertRaises(chung.LoiDang) as cm:
            self.goi(Mang().them("POST", "media/presign", P(500)), lambda: zernio.tai_tep(ZK, tep, "v.mp4", "video/mp4"))
        self.assertFalse(cm.exception.khong_ro)

    def test_tham_finish_va_container_tuong_thich_nguoc_va_co_ai_false(self):
        self.assertEqual(fb.tham_finish("V", "m", "DRAFT").get("is_ai_generated"), "true")                 # mac dinh = CO_GIONG_AI (True)
        self.assertNotIn("is_ai_generated", fb.tham_finish("V", "m", "DRAFT", co_ai=False))
        self.assertEqual(fb.tham_finish("V", "m", "DRAFT", co_ai=True).get("is_ai_generated"), "true")
        self.assertEqual(ig.tham_container("u", "c", "x").get("is_ai_generated"), "true")
        self.assertNotIn("is_ai_generated", ig.tham_container("u", "c", "x", co_ai=False))
        with mock.patch.object(chung, "CO_GIONG_AI", False):
            self.assertNotIn("is_ai_generated", fb.tham_finish("V", "m", "DRAFT"))
            self.assertEqual(fb.tham_finish("V", "m", "DRAFT", co_ai=True).get("is_ai_generated"), "true")


# ================================================================ khac
class KhacTest(unittest.TestCase):
    def test_gia_the_con_han(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "g.json"
            for ngay, ok in (("2026-11-02", True), ("2026-10-26", True), ("2026-10-25", False), ("2026-11-05", False)):
                p.write_text(json.dumps({"ngay": ngay, "vung": {"US": {}}}))
                if ok:
                    mxh.doc_gia_the(p, NGAY)
                else:
                    with self.assertRaises(mxh.KhongDang):
                        mxh.doc_gia_the(p, NGAY)
            p.write_text(json.dumps({"ngay": "2026-11-02", "vung": {}}))
            with self.assertRaises(mxh.KhongDang):
                mxh.doc_gia_the(p, NGAY)
            with self.assertRaises(mxh.KhongDang):
                mxh.doc_gia_the(pathlib.Path(d) / "khong-co.json", NGAY)

    def test_chon_nhac_theo_ngay_va_du_phong(self):
        with tempfile.TemporaryDirectory() as d:
            n = pathlib.Path(d) / "video" / "tai-san" / "nhac"
            n.mkdir(parents=True)
            with self.assertRaises(mxh.KhongDang):
                mxh.chon_nhac(d, NGAY)
            for x in "ace":
                (n / f"nhac-{x}.mp3").write_bytes(b"1")
            chinh = mxh.NHAC[NGAY.toordinal() % 4]
            kq = mxh.chon_nhac(d, NGAY)
            self.assertTrue(kq.name == f"nhac-{chinh}.mp3" or chinh == "d")
            if chinh == "d":
                self.assertEqual(kq.name, "nhac-a.mp3")      # thieu nhac-d -> tep co san dau tien theo thu tu a,c,d,e
            self.assertEqual({mxh.NHAC[(NGAY + dt.timedelta(days=i)).toordinal() % 4] for i in range(4)}, set("acde"))

    def test_gio_dang_va_dang(self):
        self.assertEqual({k: chon.GIO[k] for k in chon.GIO}, {"threads": "11:30", "fb": "19:00", "ig": "20:30"})
        self.assertEqual(chon.DANG, {"fb": "fb-gia", "ig": "ig-gia", "threads": "threads-gia"})

    def test_lay_trang_mang_thu_lai_roi_none(self):
        m = Mang().them("GET", "store.playstation.com", [http.LoiMang("x"), P(200, raw=b"<html>ok</html>")])
        with mock.patch.object(http, "gui", m), mock.patch.object(chung, "ngu", lambda s: None):
            self.assertEqual(mxh.lay_trang_mang("https://store.playstation.com/en-us/product/X"), "<html>ok</html>")
        m = Mang().them("GET", "store.playstation.com", P(404))
        with mock.patch.object(http, "gui", m), mock.patch.object(chung, "ngu", lambda s: None):
            self.assertIsNone(mxh.lay_trang_mang("https://store.playstation.com/en-us/product/X"))

    def test_tai_anh_mang_kiem_canh_ngan_600(self):
        png = lambda w, h: b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + w.to_bytes(4, "big") + h.to_bytes(4, "big") + b"\x08\x02\x00\x00\x00"
        with tempfile.TemporaryDirectory() as d:
            tai = mxh.tai_anh_mang(d)
            with mock.patch.object(http, "gui", Mang().them("GET", "big", P(200, raw=png(1280, 720))).them("GET", "nho", P(200, raw=png(1280, 500)))
                                   .them("GET", "loi", P(404))):
                self.assertEqual(tai("https://image.test/big.png?w=1", "p0-bia"), "p0-bia.png")
                self.assertTrue((pathlib.Path(d) / "p0-bia.png").exists())
                self.assertIsNone(tai("https://image.test/nho", "p1"))
                self.assertIsNone(tai("https://image.test/loi", "p2"))


@unittest.skipUnless(pathlib.Path(os.environ.get("DU_LIEU_REPO", "/nonexistent")).joinpath("deal_diem.py").exists(), "can DU_LIEU_REPO (repo rieng tu kenh-game-du-lieu)")
class VoiDealDiemThat(unittest.TestCase):
    def test_quy_vnd_that_khop_bang_mau(self):
        dd = mxh.nap_deal_diem(os.environ["DU_LIEU_REPO"])
        gt = json.load(open(pathlib.Path(os.environ["DU_LIEU_REPO"]) / "du-lieu" / "gia-the.json"))
        r = dd.quy_vnd("ps", "US", 4.79, "USD", gt, gt["ty_gia_ngan_hang"], NGAY)
        self.assertEqual((r["cach"], r["mua_duoc"], r["vnd"]), ("the", True, 180000))


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------- Opus 02/11 sau chay thu --khong-api
def test_cung_dong_khong_ghep_hai_ban_cung_game():
    from dang.tin_gia_chon import cung_dong
    assert cung_dong("Outward Definitive Edition", "Outward: The Adventurer Bundle")
    assert cung_dong("Monster Hunter Rise PS4 & PS5", "Monster Hunter Rise + Sunbreak")
    assert not cung_dong("FINAL FANTASY VII REBIRTH", "FINAL FANTASY XII THE ZODIAC AGE")
    assert not cung_dong("Dying Light - Essentials Edition", "Little Strays 2")


def test_sol_luot3_mat_quyen_va_trung_game_khong_ghi_so():
    """Sol luot 3: id_bai doi sang luot khac + x-goc trung game -> phai dung vi MAT QUYEN truoc, khong doi dong kia sang that_bai."""
    import inspect
    from dang import tin_gia_mxh as m
    src = inspect.getsource(m)
    i_quyen = src.index("Sol luot 3: dong da sang luot khac")
    i_nhuong = src.index("kiem trung game LAN 2")
    assert i_quyen < i_nhuong
