"""Chon game cho 3 khuon TIN GIA rieng (Facebook Reel / Instagram Reel / Threads anh+chu) cua Sang Game.
(khuon/tin-gia-mxh/KE-HOACH.md muc 4.2 + BO SUNG OPUS + SUA SAU SOI SOL S3 S4 S5 S10: moi muc nay DE len cac muc truoc)

THUAN: moi I/O (mang, anh, quy VND, lich su noi bat) truyen qua `Boi`; module nay khong mo mang, khong doc tep, khong ghi so.
  chon_fb(boi) / chon_ig(boi) / chon_threads(boi, thu_chu)  ->  dict(kenh, dl, kiem_lai, su_that, ma, ...) hoac None (ly do bo o boi.bo)

FAIL-CLOSED: moi dieu kien khong xac minh duoc (trang hong, khong co khoi gia, quy VND khac sg_keo, thieu endTime, anh hong) = BO game, thu game ke.
Moi gia hien ra (store o FB, game o IG/Threads) deu qua xet_o: gia trang == gia sg_keo (+-0,011), endTime >= gio dang + 24 h,
% giam trang lech <= 1 diem, quy_vnd tren gia TRANG ra cach 'the', mua_duoc, vnd == vnd sg_keo, <= 4 tam the.
"""
import datetime as dt
import re

from . import chung
from .gia import gia_trang
from .x_goc import LOC_VUNG, VUNG_VN, ten_dep

GIO = {"threads": "11:30", "fb": "19:00", "ig": "20:30"}          # gio VN dang bai (cron-job.org goi truoc ~35 phut)
DANG = {"fb": "fb-gia", "ig": "ig-gia", "threads": "threads-gia"}  # sg_dang.dang (Opus da them vao CHECK + edge sg-cong)
DANG_LOC_TRUNG = ("fb-gia", "ig-gia", "threads-gia", "x-goc")      # dong sg_dang nao tinh la "game da dung"
GIA_MIN, GIA_MAX = 50_000, 1_500_000
HAN_TOI_THIEU_GIO = 24
TOI_DA_TAM = 4
THUA_TI_LE = 0.05                     # the dư <= 5% tong menh gia moi duoc noi "vua khit"
DUNG_SAI_GIA = 0.011
LECH_GIAM = 1
CHENH_FB_MIN = 30_000                 # store dat nhat - store re nhat >= 30.000d moi dang "re hon"
LECH_HAN_GIAY = 60
ANH_MIN = 600                         # canh ngan >= 600 px
TRAN_TRANG = {"fb": 18, "ig": 10, "threads": 8}   # tong so lan tai trang moi luot
TRAN_TRANG_UV_FB = 6                  # moi ung vien FB
TOI_DA_STORE_FB, TOI_THIEU_STORE_FB = 5, 3
TOI_DA_GAME_IG, TOI_THIEU_GAME_IG = 5, 3
GIA_DU_PHONG_IG = 300_000
SO_LUOT_TOI_THIEU = 100
RE_LINK = re.compile(r"https://store\.playstation\.com/([a-z]{2}-[a-z]{2})/product/([^/?#]+)", re.I)
RE_TITLE = re.compile(r"(?:PPSA|CUSA)\d+_\d{2}", re.I)
TIEN_TO = {"USD": "$", "HKD": "HK$", "SGD": "S$", "THB": "฿", "IDR": "Rp "}


class HetLuot(Exception):
    """Het tran tai trang cua luot nay (hoac cua ung vien)."""


# ---------------------------------------------------------------- tien ich thuan
def title_ids(*chuoi):
    return {m.upper() for s in chuoi for m in RE_TITLE.findall(str(s or ""))}


def title_hang(h):
    """Ma san pham (title id PPSA/CUSA) cua mot hang sg_keo: tu `ma` (truoc dau '|') va tu pid trong link."""
    return title_ids(str(h.get("ma") or "").split("|")[0], h.get("link") or "")


def khoa_ip(ten):
    """2 tu dau cua ten da chuan hoa (bo nhan hieu, chu thuong, bo dau cau) - KHONG dung dong_game (gop RE2/RE3/RE4 lam mot)."""
    s = re.sub(r"[™®©]", "", ten or "").lower()
    tu = re.sub(r"[^\w\s]", " ", s).split()
    return " ".join(tu[:2])


def ten_video(ten):
    """Ten tren video/anh: HOA toan bo, bo nhan hieu + duoi nen tang (Monster Hunter Rise PS4 & PS5 -> MONSTER HUNTER RISE)."""
    return ten_dep(ten).upper()


def hien_tien(so, tien):
    """19.99,'USD' -> '$19,99'; 5,'USD' -> '$5'; 73792,'IDR' -> 'Rp 73.792'. Dau phay thap phan, dau cham ngan nghin."""
    p = TIEN_TO.get(tien, f"{tien} ")
    xu = int(round(float(so) * 100))
    d, c = divmod(xu, 100)
    nguyen = f"{d:,}".replace(",", ".")
    return f"{p}{nguyen}" if c == 0 else f"{p}{nguyen},{c:02d}"


def han_chu(t):
    """datetime -> '14:59 · 5/11' (gio VN) - chuoi tren video/anh."""
    v = t.astimezone(chung.VN)
    return f"{v:%H:%M} · {v.day}/{v.month}"


def han_cau(t):
    """datetime -> '14:59 ngày 5/11' (gio VN) - chuoi trong caption."""
    v = t.astimezone(chung.VN)
    return f"{v:%H:%M} ngày {v.day}/{v.month}"


def so_vn(n):
    return f"{int(n):,}".replace(",", ".")


def nghin_dung(vnd):
    """Tien VND giu NGUYEN GIA TRI khi doc lai bang tien_vnd: boi cua 1.000 duoi 1 trieu -> '460 nghìn'; con lai -> '1.048.000đ' / '72.480đ'
    (KHONG lam tron nhu '1,05 triệu' = 1.050.000d la sai gia)."""
    return f"{vnd // 1000} nghìn" if vnd % 1000 == 0 and vnd < 1_000_000 else f"{so_vn(vnd)}đ"


def the_dl(the, tien):
    """[(menh_gia, so_luong, gia_vnd)] -> [{'menh_gia': '$5', 'so_luong': 1}] (dl.json)."""
    return [{"menh_gia": hien_tien(mg, tien), "so_luong": int(sl)} for mg, sl, _g in the]


def the_chu(the, tien):
    """'1 thẻ $10 + 1 thẻ $5' (dung trong caption)."""
    return " + ".join(f"{int(sl)} thẻ {hien_tien(mg, tien)}" for mg, sl, _g in the)


def the_ngan(the, tien):
    """'$10 + $5' (lap lai theo so luong) - dung tren anh Threads."""
    return " + ".join(" + ".join([hien_tien(mg, tien)] * int(sl)) for mg, sl, _g in the)


def so_tam(the):
    return sum(int(sl) for _mg, sl, _g in the)


def kich_anh(du_lieu):
    """(rong, cao) cua anh PNG/JPEG/GIF/WEBP tu byte dau; khong nhan ra -> None. Chi dung stdlib (job CI khong cai Pillow)."""
    b = du_lieu
    try:
        if b[:8] == b"\x89PNG\r\n\x1a\n":
            return int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big")
        if b[:6] in (b"GIF87a", b"GIF89a"):
            return int.from_bytes(b[6:8], "little"), int.from_bytes(b[8:10], "little")
        if b[:2] == b"\xff\xd8":
            i = 2
            while i + 9 < len(b):
                if b[i] != 0xFF:
                    i += 1
                    continue
                m = b[i + 1]
                if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
                    i += 2
                    continue
                ln = int.from_bytes(b[i + 2:i + 4], "big")
                if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    return int.from_bytes(b[i + 7:i + 9], "big"), int.from_bytes(b[i + 5:i + 7], "big")
                i += 2 + ln
        if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
            kieu = b[12:16]
            if kieu == b"VP8X":
                return 1 + int.from_bytes(b[24:27], "little"), 1 + int.from_bytes(b[27:30], "little")
            if kieu == b"VP8 ":
                return int.from_bytes(b[26:28], "little") & 0x3FFF, int.from_bytes(b[28:30], "little") & 0x3FFF
            if kieu == b"VP8L":
                v = int.from_bytes(b[21:25], "little")
                return 1 + (v & 0x3FFF), 1 + ((v >> 14) & 0x3FFF)
    except (IndexError, ValueError):
        return None
    return None


def da_dung_tu_dong(cac_dong):
    """Cac dong sg_dang (fb-gia/ig-gia/threads-gia/x-goc, trang thai khac that_bai/bo) -> set ma da dung: `ma` day du cua sg_keo
    VA title id (id_tai cua tin gia la cac `ma` noi bang ',')."""
    ra = set()
    for r in cac_dong:
        if r.get("dang") not in DANG_LOC_TRUNG or r.get("trang_thai") in ("that_bai", "bo"):
            continue
        for ma in str(r.get("id_tai") or "").split(","):
            ma = ma.strip()
            if ma:
                ra.add(ma)
                ra |= title_ids(ma)
    return ra


# ---------------------------------------------------------------- boi canh
class Boi:
    """Moi thu viec chon can biet. `lay_trang(link)` -> html | None (mang that o tin_gia_mxh); `tai_anh(url, ten_tep)` -> ten tep tuong doi
    thu muc tai san | None (da kiem canh ngan >= 600 px); `quy_vnd` = deal_diem.quy_vnd; `nb` = NoiBat (da_noi_bat) hoac None."""

    def __init__(self, kenh, ngay, gio_dang, keo, gia_the, quy_vnd, lay_trang, tai_anh, da_dung=(), nb=None, tran_trang=None):
        self.kenh, self.ngay, self.gio_dang, self.keo, self.gia_the = kenh, ngay, gio_dang, keo, gia_the
        self.quy_vnd, self.lay_trang, self.tai_anh = quy_vnd, lay_trang, tai_anh
        self.da_dung, self.nb = set(da_dung), nb
        self.tran_trang = TRAN_TRANG[kenh] if tran_trang is None else tran_trang
        self.so_trang, self.so_anh = 0, 0
        self.bo = []            # [{"ma","ten","ly"}] - ly do bo tung ung vien / store (vao chon.json)
        self.cache_trang, self.cache_game = {}, {}

    def ghi_bo(self, ma, ten, ly):
        self.bo.append({"ma": str(ma), "ten": str(ten), "ly": str(ly)})
        chung.log(f"tin_gia_chon: bo {str(ma)[:40]} ({str(ten)[:30]}): {ly}")

    def tai_trang(self, link):
        if link in self.cache_trang:
            return self.cache_trang[link]
        if self.so_trang >= self.tran_trang:
            raise HetLuot(f"het tran {self.tran_trang} lan tai trang cua luot")
        self.so_trang += 1
        html = self.lay_trang(link)
        self.cache_trang[link] = html if isinstance(html, str) and html else None
        return self.cache_trang[link]

    def anh(self, url, nhan):
        """Tai anh `url` thanh tep `{nhan}`; -> ten tep | None."""
        if not url:
            return None
        self.so_anh += 1
        try:
            return self.tai_anh(url, nhan)
        except Exception as e:   # noqa: BLE001 - anh hong = bo game, khong lam sap luot
            chung.log(f"tin_gia_chon: anh loi {nhan}: {chung.cat(f'{type(e).__name__}: {e}', 120)}")
            return None


# ---------------------------------------------------------------- loc chung
def _int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def ly_loai_hang(boi, h):
    """Ly do loai mot hang sg_keo (None = hop le). Loc chung 4.2 + S4."""
    if not isinstance(h, dict) or not _int(h.get("hang")):
        return "hang khong hop le"
    ten, ma, link = h.get("ten"), h.get("ma"), str(h.get("link") or "")
    if not ten or not ma:
        return "thieu ten/ma"
    if h.get("lech_gia") is not False:
        return "lech_gia khong phai False"
    if h.get("da_kiem_trang") not in (True, False, None):
        return "da_kiem_trang la"
    if not link.startswith("https://store.playstation.com/"):
        return "link khong phai PS Store"
    vung = h.get("vung_re_nhat")
    if vung not in LOC_VUNG:
        return f"vung {vung} khong ho tro"
    gv = (h.get("gia_vung") or {}).get(vung) if isinstance(h.get("gia_vung"), dict) else None
    if not isinstance(gv, dict) or gv.get("mua_duoc") is not True or gv.get("cach") != "the" or gv.get("chi_plus"):
        return "vung re nhat khong mua duoc bang the (hoac chi PS Plus)"
    if not _int(h.get("gia_vnd")) or not GIA_MIN <= h["gia_vnd"] <= GIA_MAX:
        return f"gia {h.get('gia_vnd')} ngoai {GIA_MIN}-{GIA_MAX}"
    if gv.get("vnd") != h["gia_vnd"]:
        return "gia_vnd cua hang khac vnd cua gia_vung (S4)"
    if not _int(h.get("giam")) or not 1 <= h["giam"] <= 100:
        return "giam khong hop le"
    m = RE_LINK.match(link)
    if not m or m.group(1).lower() != LOC_VUNG[vung]:
        return f"link khong dung locale vung {vung}"
    if h["ma"] in boi.da_dung or title_hang(h) & boi.da_dung:
        return "game da dung (sg_dang 3 ngay / cung ngay)"
    if boi.nb is not None:
        ly = boi.nb.trung(ten, [m.group(2)])
        if ly:
            return f"da noi bat 3 ngay: {ly}"
    return None


def ung_vien(boi, bo_trung_san_pham=False):
    """Cac hang hop le, thu tu: da_kiem_trang truoc, roi `hang`. bo_trung_san_pham: S10 - cung title id = cung game, giu hang nho hon."""
    hop = []
    for h in sorted((h for h in boi.keo if isinstance(h, dict) and _int(h.get("hang"))), key=lambda r: r["hang"]):
        ly = ly_loai_hang(boi, h)
        if ly:
            boi.ghi_bo(h.get("ma"), h.get("ten"), ly)
            continue
        hop.append(h)
    if bo_trung_san_pham:
        thay, giu = set(), []
        for h in hop:
            t = title_hang(h)
            if t and t & thay:
                boi.ghi_bo(h["ma"], h["ten"], "trung san pham (cung title id) voi hang nho hon")
                continue
            thay |= t
            giu.append(h)
        hop = giu
    return sorted(hop, key=lambda r: (r.get("da_kiem_trang") is not True, r["hang"]))


# ---------------------------------------------------------------- kiem mot o gia (mot store cua mot game)
def xet_o(boi, ma, o, link, giam_mong, khit=False):
    """Tai trang `link` va kiem o gia `o` cua vung `ma`. -> (rec | None, ly). Co the nem HetLuot.
    rec: dict(ma_vung, pid, loc, link, tien, gia_cuc_bo, gia_goc, giam, end_ms, vnd, the, thua, tong, html).
    khit=True: the du <= 5% tong menh gia (store chinh cua bai - caption noi 'vua khit')."""
    m = RE_LINK.match(str(link or ""))
    if not m:
        return None, "link khong dung dang PS Store"
    loc, pid = m.group(1).lower(), m.group(2)
    if loc != LOC_VUNG.get(ma):
        return None, f"link locale {loc} lech vung {ma}"
    html = boi.tai_trang(link)
    if not html:
        return None, "khong tai duoc trang"
    k = gia_trang.khoi_gia(html, pid)
    if k is None:
        return None, "trang khong co khoi gia mua dut ro rang cua dung pid"
    tien = o.get("tien")
    if k.get("tien_te") != tien:
        return None, f"tien te trang {k.get('tien_te')} khac {tien}"
    mong = gia_trang.doc_gia(o.get("gia"))
    con, goc = k["gia_cuc_bo"], k.get("gia_goc")
    if not mong or abs(con - mong) > DUNG_SAI_GIA:
        return None, f"gia trang {con} khac gia sg_keo {o.get('gia')}"
    end = k.get("endTime")
    if not end:
        return None, "trang khong co endTime"
    if int(end) < (boi.gio_dang + dt.timedelta(hours=HAN_TOI_THIEU_GIO)).timestamp() * 1000:
        return None, f"het giam som (endTime {end} < gio dang + {HAN_TOI_THIEU_GIO} h)"
    if not goc or goc <= con:
        return None, "trang khong cho gia goc lon hon gia ban"
    giam_t = int(round(100 * (1 - con / goc)))
    if not _int(giam_mong) or abs(giam_t - giam_mong) > LECH_GIAM:
        return None, f"% giam trang {giam_t} lech {giam_mong} > {LECH_GIAM}"
    ty_gia = (boi.gia_the or {}).get("ty_gia_ngan_hang") or {}
    kq = boi.quy_vnd("ps", ma, con, tien, boi.gia_the, ty_gia, boi.ngay)
    if kq.get("cach") != "the" or kq.get("mua_duoc") is not True:
        return None, f"quy VND tren gia trang khong ra cach the mua duoc ({kq.get('cach')}: {kq.get('ly_do')})"
    if kq.get("vnd") != o.get("vnd"):
        return None, f"quy VND tren gia trang {kq.get('vnd')} khac vnd sg_keo {o.get('vnd')}"
    the = [tuple(t) for t in kq.get("the") or []]
    if not the or so_tam(the) > TOI_DA_TAM:
        return None, f"can {so_tam(the)} tam the (> {TOI_DA_TAM})"
    tong, thua = kq.get("tong_menh_gia"), kq.get("thua")
    if tong is None or thua is None or thua < 0:
        return None, "quy VND khong tra tong menh gia/du"
    if khit and thua > THUA_TI_LE * tong + 1e-9:
        return None, f"the du {thua} tren tong {tong} (> {THUA_TI_LE:.0%}) - khong gọi được 'vua khit'"
    return {"ma_vung": ma, "pid": pid, "loc": loc, "link": str(link), "tien": tien, "gia_cuc_bo": con, "gia_goc": goc, "giam": giam_t,
            "end_ms": int(end), "vnd": kq["vnd"], "the": the, "thua": round(float(thua), 2), "tong": float(tong), "html": html}, None


def _end_dt(rec):
    return dt.datetime.fromtimestamp(rec["end_ms"] / 1000, dt.timezone.utc)


def _kiem_lai(ten, rec):
    """Muc cho gia.kiem_lai (S2): gia_cuc_bo float cua trang, endTime ms, gia_dung_y. P2-d: them gia_goc + giam (gia.kiem_lai bo qua truong la;
    tin_gia_mxh.kiem_goc_giam so voi trang truoc cong khai)."""
    return {"ten": f"{ten} ({rec['ma_vung']})", "pid": rec["pid"], "loc": rec["loc"], "gia_cuc_bo": float(rec["gia_cuc_bo"]),
            "endTime": str(rec["end_ms"]), "gia_dung_y": True, "gia_goc": float(rec["gia_goc"]), "giam": int(rec["giam"])}


def _anh_game(boi, html, pid, stem, so_nen):
    """Bia (key art) + >= 1 anh chup man hinh tu `Product:<pid>`. -> (bia, [nen...]) hoac (None, ly)."""
    m = gia_trang.media(html, pid)
    bia = boi.anh(m.get("anh"), f"{stem}-bia")
    if not bia:
        return None, "khong tai duoc anh bia hop le"
    nen = []
    for i, url in enumerate(m.get("anh_chup") or []):
        if len(nen) >= so_nen or i >= so_nen + 3:
            break
        f = boi.anh(url, f"{stem}-c{len(nen)}")
        if f:
            nen.append(f)
    if not nen:
        return None, "khong tai duoc anh chup man hinh nao hop le"
    return bia, nen


# ---------------------------------------------------------------- FB: 1 game, 3-5 store
def chon_fb(boi):
    """-> dict hoac None. Moi store hien trong video deu qua xet_o (S3); store truot bi bo, can >= 3 store dat gom store re nhat."""
    dau = boi.so_trang
    for h in ung_vien(boi):
        try:
            kq = _xet_fb(boi, h)
        except HetLuot as e:
            chung.log(f"tin_gia_chon fb: dung - {e}")
            break
        if kq:
            return kq
        if boi.so_trang - dau >= boi.tran_trang:
            break
    return None


def _xet_fb(boi, h):
    ma_h, ten, main = h["ma"], h["ten"], h["vung_re_nhat"]
    cac = {m: o for m, o in h["gia_vung"].items()
           if m in LOC_VUNG and isinstance(o, dict) and o.get("mua_duoc") is True and o.get("cach") == "the" and not o.get("chi_plus")
           and _int(o.get("vnd")) and o["vnd"] > 0}
    if len(cac) < TOI_THIEU_STORE_FB:
        return boi.ghi_bo(ma_h, ten, f"chi {len(cac)} store mua duoc bang the (can >= {TOI_THIEU_STORE_FB})")
    vmin = min(o["vnd"] for o in cac.values())
    if main not in cac or cac[main]["vnd"] != vmin or sum(1 for o in cac.values() if o["vnd"] == vmin) != 1:
        return boi.ghi_bo(ma_h, ten, "store re nhat khong duy nhat / khong phai vung_re_nhat")
    if max(o["vnd"] for o in cac.values()) - vmin < CHENH_FB_MIN:
        return boi.ghi_bo(ma_h, ten, f"chenh gia store < {CHENH_FB_MIN}")
    thu_tu = [main] + sorted((m for m in cac if m != main), key=lambda m: (-cac[m]["vnd"], m))
    dau, ok = boi.so_trang, {}
    for m in thu_tu:
        if boi.so_trang - dau >= TRAN_TRANG_UV_FB or len(ok) >= TOI_DA_STORE_FB:
            break
        o = cac[m]
        link = o.get("link") or (h["link"] if m == main else None)
        if not link:
            boi.ghi_bo(f"{ma_h}/{m}", ten, "o gia thieu link trang vung (S3: thieu link = truot)")
        else:
            rec, ly = xet_o(boi, m, o, link, o["giam"] if _int(o.get("giam")) else h["giam"], khit=(m == main))
            if rec is not None:
                ok[m] = rec
                continue
            boi.ghi_bo(f"{ma_h}/{m}", ten, ly)
        if m == main:
            return boi.ghi_bo(ma_h, ten, "store re nhat truot kiem trang")
    if main not in ok or len(ok) < TOI_THIEU_STORE_FB:
        return boi.ghi_bo(ma_h, ten, f"chi {len(ok)} store qua kiem trang (can >= {TOI_THIEU_STORE_FB})")
    if ok[main]["vnd"] != h["gia_vnd"]:
        return boi.ghi_bo(ma_h, ten, "gia_vnd khac quy VND tren trang (S4)")
    ds = sorted(ok.values(), key=lambda r: (-r["vnd"], r["ma_vung"]))     # dat -> re, store re nhat o cuoi
    if ds[-1]["ma_vung"] != main or ds[0]["vnd"] - ds[-1]["vnd"] < CHENH_FB_MIN or (len(ds) > 1 and ds[-2]["vnd"] == ds[-1]["vnd"]):
        return boi.ghi_bo(ma_h, ten, "sau kiem trang: store re nhat khong duy nhat hoac chenh gia < 30.000")
    r = ok[main]
    bia, nen = _anh_game(boi, r["html"], r["pid"], "g0", 2)
    if bia is None:
        return boi.ghi_bo(ma_h, ten, nen)
    han = _end_dt(r)   # Opus 02/11: 'Giam g% toi ...' noi ve DEAL cua store re nhat -> han cua chinh store do (store khac da buoc >= gio dang + 24 h trong xet_o)
    re_hon = {"ten": VUNG_VN[ds[0]["ma_vung"]], "vnd": ds[0]["vnd"] - ds[-1]["vnd"]}
    dl = {"kenh": "fb", "ngay": boi.ngay.isoformat(), "ten": ten_video(ten), "bia": bia, "nen": nen, "gia_vnd": r["vnd"],
          "vung": [{"ma": x["ma_vung"], "ten": VUNG_VN[x["ma_vung"]], "vnd": x["vnd"]} for x in ds], "re_hon": re_hon,
          "the": {"ma": main, "ten_vung": VUNG_VN[main], "the": the_dl(r["the"], r["tien"]), "gia_game": hien_tien(r["gia_cuc_bo"], r["tien"]),
                  "du": hien_tien(r["thua"], r["tien"])},
          "goc": hien_tien(r["gia_goc"], r["tien"]), "giam": r["giam"], "han_chu": han_chu(han)}
    su_that = {"kenh": "fb", "ten_goc": ten, "gia_vnd": r["vnd"], "ma_vung": main, "vung": VUNG_VN[main], "the": r["the"], "tien": r["tien"],
               "the_chu": the_chu(r["the"], r["tien"]), "gia_game": dl["the"]["gia_game"], "du": dl["the"]["du"], "goc": dl["goc"],
               "giam": r["giam"], "han": han, "cua_hang": [{"ma": x["ma_vung"], "ten": VUNG_VN[x["ma_vung"]], "vnd": x["vnd"]} for x in ds],
               "re_hon": re_hon, "gia_mua": [r["vnd"]], "gia_da_kiem": sorted({x["vnd"] for x in ds}),
               "ten_dung": [], "pid": r["pid"]}
    return {"kenh": "fb", "dl": dl, "su_that": su_that, "ma": [ma_h], "tieu_de_hang": [ten],
            "kiem_lai": [_kiem_lai(ten, x) for x in ds],
            "chon": {"hang": h["hang"], "ma": ma_h, "ten": ten, "store": [x["ma_vung"] for x in ds], "re_hon": re_hon, "han": chung.iso(han)}}


# ---------------------------------------------------------------- xet mot game (IG / Threads): store re nhat cua no
def xet_game(boi, h):
    """-> rec game da kiem (store chinh + anh + thong tin trang) hoac None. Co cache theo `ma` (khong tai lai). Co the nem HetLuot."""
    if h["ma"] in boi.cache_game:
        return boi.cache_game[h["ma"]]
    vung = h["vung_re_nhat"]
    o = h["gia_vung"][vung]
    boi.cache_game[h["ma"]] = None
    rec, ly = xet_o(boi, vung, o, h["link"], o["giam"] if _int(o.get("giam")) else h["giam"], khit=True)
    if rec is None:
        boi.ghi_bo(h["ma"], h["ten"], ly)
        return None
    if rec["vnd"] != h["gia_vnd"]:
        boi.ghi_bo(h["ma"], h["ten"], "gia_vnd khac quy VND tren trang (S4)")
        return None
    stem = f"p{boi.so_anh}"
    bia, nen = _anh_game(boi, rec["html"], rec["pid"], stem, 1)
    if bia is None:
        boi.ghi_bo(h["ma"], h["ten"], nen)
        return None
    tt = gia_trang.thong_tin_game(rec["html"], rec["pid"])
    g = {"hang": h, "ten_goc": h["ten"], "ma": h["ma"], "titles": title_hang(h), "rec": {k: v for k, v in rec.items() if k != "html"},
         "bia": bia, "nen": nen[0], "diem": tt.get("diem"), "the_loai": [x for x in tt.get("the_loai") or [] if x]}
    boi.cache_game[h["ma"]] = g
    return g


# ---------------------------------------------------------------- IG: 3-5 game cung IP, xep hang theo gia
def chon_ig(boi):
    ds = ung_vien(boi, bo_trung_san_pham=True)
    nhom = {}
    for h in ds:
        nhom.setdefault(khoa_ip(h["ten"]), []).append(h)
    xep = sorted(((ip, rows) for ip, rows in nhom.items() if ip and len(rows) >= TOI_THIEU_GAME_IG),
                 key=lambda t: (-len(t[1]), sum(r["hang"] for r in t[1])))
    for ip, rows in nhom.items():
        if len(rows) < TOI_THIEU_GAME_IG:
            boi.ghi_bo(f"ip:{ip}", ip, f"nhom IP chi {len(rows)} game (can >= {TOI_THIEU_GAME_IG})")
    tot, tot_ip, het = None, None, False
    for ip, rows in xep:
        if tot is not None and len(tot) >= min(TOI_DA_GAME_IG, len(rows)):
            break
        ok = []
        for h in rows:
            if len(ok) >= TOI_DA_GAME_IG:
                break
            try:
                g = xet_game(boi, h)
            except HetLuot as e:
                chung.log(f"tin_gia_chon ig: dung - {e}")
                het = True
                break
            if g:
                ok.append(g)
        if len(ok) >= TOI_THIEU_GAME_IG and (tot is None or len(ok) > len(tot)):
            tot, tot_ip = ok, ip
        if het:
            break
    if tot is None and not het:
        re_ = [h for h in ds if h["gia_vnd"] <= GIA_DU_PHONG_IG]
        ok = []
        for h in re_:
            if len(ok) >= TOI_DA_GAME_IG:
                break
            try:
                g = xet_game(boi, h)
            except HetLuot as e:
                chung.log(f"tin_gia_chon ig: dung - {e}")
                break
            if g:
                ok.append(g)
        if len(ok) >= TOI_THIEU_GAME_IG:
            tot, tot_ip = ok, None
    if tot is None:
        return None
    return _dl_ig(boi, tot, tot_ip)


def _dl_ig(boi, games, ip):
    games = sorted(games, key=lambda g: (-g["rec"]["vnd"], -g["hang"]["hang"]))      # dat -> re, game re nhat o cuoi
    n = len(games)
    gia_max = max(g["rec"]["vnd"] for g in games)
    x = (gia_max // 100_000 + 1) * 100_000
    ten_ip = ip.upper() if ip else "PS4 · PS5"
    ends = [_end_dt(g["rec"]) for g in games]
    han = min(ends)
    han_khac = (max(ends) - han).total_seconds() > LECH_HAN_GIAY
    giams = {g["rec"]["giam"] for g in games}
    vungs = {g["rec"]["ma_vung"] for g in games}
    dl = {"kenh": "ig", "ngay": boi.ngay.isoformat(), "tieu_de": [f"{n} GAME", ten_ip, f"DƯỚI {x // 1000}K"],
          "game": [{"ten": ten_video(g["ten_goc"]), "bia": g["bia"], "nen": g["nen"], "gia_vnd": g["rec"]["vnd"], "ma_vung": g["rec"]["ma_vung"],
                    "giam": g["rec"]["giam"]} for g in games],
          "han_chu": han_chu(han), "giam_chung": giams.pop() if len(giams) == 1 else None,
          "vung_chung": VUNG_VN[next(iter(vungs))] if len(vungs) == 1 else None}
    if han_khac:
        dl["han_khac"] = True
    su_that = {"kenh": "ig", "ip": ip, "ten_ip": ten_ip, "han": han, "han_khac": han_khac, "vung_chung": dl["vung_chung"],
               "game": [{"ten_goc": g["ten_goc"], "gia_vnd": g["rec"]["vnd"], "ma_vung": g["rec"]["ma_vung"], "vung": VUNG_VN[g["rec"]["ma_vung"]],
                         "giam": g["rec"]["giam"]} for g in games],
               "gia_mua": sorted({g["rec"]["vnd"] for g in games}), "gia_da_kiem": sorted({g["rec"]["vnd"] for g in games}), "re_hon": None,
               "ten_dung": []}
    return {"kenh": "ig", "dl": dl, "su_that": su_that, "ma": [g["ma"] for g in games], "tieu_de_hang": [g["ten_goc"] for g in games],
            "kiem_lai": [_kiem_lai(g["ten_goc"], g["rec"]) for g in games],
            "chon": {"ip": ip, "game": [{"hang": g["hang"]["hang"], "ma": g["ma"], "ten": g["ten_goc"], "vnd": g["rec"]["vnd"],
                                          "vung": g["rec"]["ma_vung"]} for g in games], "han": chung.iso(han), "han_khac": han_khac}}


# ---------------------------------------------------------------- Threads: 2 game CUNG gia, "minh chon" 1 ben co so
def chon_ben(a, b):
    """-> ('a'|'b', 'luot'|'sao'). Ben nhieu luot >= 3 lan ben kia VA diem TB khong thap hon qua 0,2 -> nhieu luot;
    con lai -> diem TB cao hon; hoa -> nhieu luot hon."""
    da, db = a["diem"], b["diem"]
    for x, y, ten in ((da, db, "a"), (db, da, "b")):
        if x["so_luot"] >= 3 * y["so_luot"] and y["tb"] - x["tb"] <= 0.2 + 1e-9:
            return ten, "luot"
    if abs(da["tb"] - db["tb"]) > 1e-9:
        return ("a" if da["tb"] > db["tb"] else "b"), "sao"
    return ("a" if da["so_luot"] >= db["so_luot"] else "b"), "luot"


def _cap_hop_le(a, b):
    """S5: cung vung, cung gia trang, cung to hop the, cung endTime (+-60 s); ca hai co diem sao >= 100 luot. -> ly do loai hoac None."""
    ra, rb = a["rec"], b["rec"]
    if ra["ma_vung"] != rb["ma_vung"] or ra["tien"] != rb["tien"]:
        return "khac vung"
    if abs(ra["gia_cuc_bo"] - rb["gia_cuc_bo"]) > 1e-9 or ra["vnd"] != rb["vnd"]:
        return "khac chuoi gia trang"
    if [(float(m), int(s)) for m, s, _ in ra["the"]] != [(float(m), int(s)) for m, s, _ in rb["the"]]:
        return "khac to hop the"
    if abs(ra["end_ms"] - rb["end_ms"]) > LECH_HAN_GIAY * 1000:
        return "khac endTime"
    for g in (a, b):
        d = g["diem"]
        if not d or d["so_luot"] < SO_LUOT_TOI_THIEU:
            return f"{g['ten_goc'][:30]}: thieu diem sao / duoi {SO_LUOT_TOI_THIEU} luot cham"
    return None


_BO_BAN = re.compile(r"\b(definitive|deluxe|standard|complete|ultimate|gold|premium|digital|edition|bundle|collection|pack|remastered|remaster|hd|goty|game|of|the|year|ps4|ps5|and)\b")


def _goc_ten(ten):
    """Ten goc de so 'cung mot game': chu thuong, bo nhan hieu/dau cau, bo tu chi phien ban (Definitive, Bundle, HD...)."""
    s = re.sub(r"[™®©]", "", ten or "").lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return _BO_BAN.sub(" ", s).split()


def cung_dong(ten_a, ten_b):
    """Opus 02/11 (chay thu ra cap Outward Definitive Edition vs Outward: The Adventurer Bundle): hai ten la CUNG MOT game khi ten goc
    cua ben nay la DAU (theo tu) cua ben kia. Than trong: 'Final Fantasy VII' vs 'Final Fantasy VII Rebirth' cung bi coi la cung dong -> bo cap
    (chi mat 1 cap, khong dang sai)."""
    a, b = _goc_ten(ten_a), _goc_ten(ten_b)
    if not a or not b:
        return True
    n = min(len(a), len(b))
    return a[:n] == b[:n]


def chon_threads(boi, thu_chu=None):
    """thu_chu(su_that, cap) -> ket qua chu (truthy) hoac None; None = chu khong vua gioi han -> bo cap, thu cap ke (BO SUNG 5)."""
    ds = ung_vien(boi, bo_trung_san_pham=True)
    nhom = {}
    for h in ds:
        nhom.setdefault((h["gia_vnd"], h["vung_re_nhat"]), []).append(h)
    cap_ds = []
    for rows in nhom.values():
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                a, b = rows[i], rows[j]
                if title_hang(a) & title_hang(b):
                    continue
                if cung_dong(a["ten"], b["ten"]):
                    continue
                cap_ds.append((khoa_ip(a["ten"]) != khoa_ip(b["ten"]), a["hang"] + b["hang"], a, b))
    cap_ds.sort(key=lambda t: (t[0], t[1]))
    if not cap_ds:
        boi.ghi_bo("cap", "-", "khong co 2 game cung gia VND cung vung")
        return None
    hop, i = [], 0
    # Pha 1: quet cap theo thu tu uu tien, thu thap cap hop le (dung som khi gap cap cung IP + cung the loai = tot nhat); Pha 2: neu moi cap
    # tot deu co chu khong vua (BO SUNG 5) thi quet tiep cac cap con lai, cap nao hop le la thu chu ngay.
    def xet_cap(khac_ip, tong_hang, a, b):
        ga = xet_game(boi, a)
        gb = xet_game(boi, b) if ga else None
        if not (ga and gb):
            return None
        ly = _cap_hop_le(ga, gb)
        if ly:
            boi.ghi_bo(f"{a['ma']}+{b['ma']}", f"{a['ten']} / {b['ten']}", f"cap bi loai: {ly}")
            return None
        cung_the_loai = bool(set(ga["the_loai"]) & set(gb["the_loai"]))
        return (khac_ip, not cung_the_loai, tong_hang, ga, gb)

    def thu(c):
        _k1, _k2, _t, ga, gb = c
        ben, ly_chon = chon_ben(ga, gb)
        kq = _dl_threads(boi, ga, gb, ben, ly_chon)
        if thu_chu is None:
            return kq
        chu = thu_chu(kq["su_that"], kq)
        if chu:
            kq["chu_san"] = chu
            return kq
        boi.ghi_bo(f"{ga['ma']}+{gb['ma']}", f"{ga['ten_goc']} / {gb['ten_goc']}", "chu Threads khong vua gioi han / het bien the cau mo")
        return None
    het = False
    try:
        while i < len(cap_ds):
            c = xet_cap(*cap_ds[i])
            i += 1
            if c:
                hop.append(c)
                if not c[0] and not c[1]:
                    break
    except HetLuot as e:
        chung.log(f"tin_gia_chon threads: dung - {e}")
        het = True
    hop.sort(key=lambda t: t[:3])
    for c in hop:
        kq = thu(c)
        if kq:
            return kq
    if not het:
        try:
            while i < len(cap_ds):                       # pha 2
                c = xet_cap(*cap_ds[i])
                i += 1
                kq = thu(c) if c else None
                if kq:
                    return kq
        except HetLuot as e:
            chung.log(f"tin_gia_chon threads: dung - {e}")
    if not hop:
        boi.ghi_bo("cap", "-", "khong cap nao qua kiem trang + diem sao")
    return None


def _dl_threads(boi, ga, gb, ben, ly_chon):
    ra, rb = ga["rec"], gb["rec"]
    han = min(_end_dt(ra), _end_dt(rb))
    gia_hien = hien_tien(ra["gia_cuc_bo"], ra["tien"])
    cung_giam = ra["giam"] == rb["giam"]
    chan = (f"Store {VUNG_VN[ra['ma_vung']]} {gia_hien}" + (f" (−{ra['giam']}%)" if cung_giam else "")
            + f" · thẻ {the_ngan(ra['the'], ra['tien'])} · hết giảm {han_chu(han)}")

    def mat(g):
        d = g["diem"]
        return {"ten": ten_video(g["ten_goc"]), "bia": g["bia"], "nen": g["nen"], "gia_vnd": g["rec"]["vnd"],
                "sao": f"{d['tb']:.2f}".replace(".", ","), "luot": so_vn(d["so_luot"])}
    dl = {"kenh": "threads", "ngay": boi.ngay.isoformat(), "cau_hoi": [f"Có {nghin_dung(ra['vnd'])},", "chọn bên nào?"], "a": mat(ga), "b": mat(gb),
          "chan": chan}
    chon_g, khac = (ga, gb) if ben == "a" else (gb, ga)
    su_that = {"kenh": "threads", "gia_vnd": ra["vnd"], "ma_vung": ra["ma_vung"], "vung": VUNG_VN[ra["ma_vung"]], "tien": ra["tien"],
               "gia_hien": gia_hien, "giam": ra["giam"] if cung_giam else None, "han": han, "the": ra["the"],
               "the_chu": the_chu(ra["the"], ra["tien"]), "a": ga["ten_goc"], "b": gb["ten_goc"],
               "diem": {"a": ga["diem"], "b": gb["diem"]}, "ben": ben, "ly_chon": ly_chon,
               "chon_ten": chon_g["ten_goc"], "chon_diem": chon_g["diem"], "khac_ten": khac["ten_goc"], "khac_diem": khac["diem"],
               "chon_la_ps5": str(chon_g["ma"]).upper().startswith("PPSA") and str(khac["ma"]).upper().startswith("CUSA"),
               "gia_mua": [ra["vnd"]], "gia_da_kiem": [ra["vnd"]], "re_hon": None, "ten_dung": []}
    return {"kenh": "threads", "dl": dl, "su_that": su_that, "ma": [ga["ma"], gb["ma"]], "tieu_de_hang": [ga["ten_goc"], gb["ten_goc"]],
            "kiem_lai": [_kiem_lai(ga["ten_goc"], ra), _kiem_lai(gb["ten_goc"], rb)],
            "chon": {"a": {"hang": ga["hang"]["hang"], "ma": ga["ma"], "ten": ga["ten_goc"], "diem": ga["diem"]},
                     "b": {"hang": gb["hang"]["hang"], "ma": gb["ma"], "ten": gb["ten_goc"], "diem": gb["diem"]},
                     "minh_chon": ben, "ly_do_chon": ly_chon, "vnd": ra["vnd"], "han": chung.iso(han)}}


CHON = {"fb": chon_fb, "ig": chon_ig, "threads": chon_threads}
