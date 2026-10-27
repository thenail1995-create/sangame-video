"""Bai X GOC moi ngay (@sangamecomvn) qua Buffer: 1 deal PS tu sg_keo + anh chup trang PS Store + ALT, KHONG link, KHONG hashtag.
(ke-hoach-x-goc-27-10.md + muc "SUA SAU SOI SOL" + vong sua sau soi diff 27/10: nhanh (ii) cua THU-NGHIEM SG-X-A/SG-X-B)

  SG_X_GOC_NGAY_1=YYYY-MM-DD python -m dang.x_goc --ngay YYYY-MM-DD --khung sang|toi --che-do thu|that [--gia-the du-lieu/du-lieu/gia-the.json]

Lich: ngay 1 = SG_X_GOC_NGAY_1; ngay le (1,3,5...) dang 10:00 VN (khung sang), ngay chan 20:00 VN (khung toi). Khung khong khop ngay ->
in "khong phai khung hom nay", thoat 0, KHONG giu_dang. Thieu/sai SG_X_GOC_NGAY_1 -> thoat 2. Khong co ngay cuoi (Opus tat lich sau 30 ngay).
Thu tu: chon game + dung chu + chup + kiem (cuc bo) -> cong.giu_dang -> [thu: in chu/ALT/kich thuoc anh roi thoat]
  -> kiem gio -> upload Zernio -> kiem gio -> danh dau "da gui mutation" -> Buffer createPost (hen dueAt) -> NGAY cap_nhat_dang(id_bai)
  -> cho sent (han tuyet doi dueAt + 15 phut, chua 60 s ghi so) -> da_dang.
Ma thoat: 0 xong (hoac thu xong / khung khong khop) | 1 loi dang / khong ro / ghi so loi | 2 thieu khoa/cau hinh | 3 KHONG dang.
Quy uoc loi giong x.py: khong_ro = co the da len X -> KHONG dang lai. Moi ngoai le SAU moc "da gui mutation" ma chua chung minh chua tao
-> khong_ro, khong bao gio that_bai. Dong giu quyen luon con -> luot sau khong dang lai.
Module nay KHONG co ham nao thich / tra loi / chia se lai bai nguoi khac (luat Automation cua X).
Anh Sony chi nam trong thu muc tam cua runner, bi xoa khi xong; URL anh (Zernio) duoc che khoi log.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata

from . import chung, http, ntfy, so, x, zernio

DANG, KENH = "x-goc", "x"
CO_LINK = False                       # theo spec SG-X-A: moi bai KHONG link (code ngay le/chan chua lam, tat). Doi sang True = chua ho tro.
GIO_KHUNG = {"sang": "10:00", "toi": "20:00"}   # SG-X-B: ngay le 10:00, ngay chan 20:00 (gio VN)
CHUA_SO_GIAY = 60                     # chua 60 s truoc han tuyet doi de ghi so khong_ro
TRE_TOI_DA_PHUT = 2                   # con < 2 phut toi dueAt thi khong len lich / khong upload / khong createPost
CHO_SAU_DUE_PHUT = 15                 # cho Buffer 'sent' toi dueAt + 15 phut
DONG1_TOI_DA, CHU_MIN, CHU_MAX = 60, 150, 260    # theo x.do_dai_x
HAN_TOI_THIEU_GIO = 24
NGAY_KHONG_LAP = 7
GIA_THE_TOI_DA_NGAY = 7
ANH_RONG_MIN, ANH_CAO_MIN = 400, 300
ALT_TOI_DA = 1000
SCRIPT_CHUP = pathlib.Path(__file__).resolve().parent.parent / "cong-cu" / "chup-ps.mjs"

VUNG_VN = {"US": "Mỹ", "HK": "Hồng Kông", "SG": "Singapore", "TH": "Thái Lan", "ID": "Indonesia", "IN": "Ấn Độ", "UA": "Ukraina"}
LOC_VUNG = {"US": "en-us", "HK": "en-hk", "SG": "en-sg", "TH": "en-th", "ID": "en-id", "IN": "en-in", "UA": "uk-ua"}
# tien te -> ky hieu hop le tren trang (so sanh dung ky hieu dai truoc: "HK$" khong duoc nham voi "$")
KY_HIEU_TIEN = {"USD": ("$",), "HKD": ("HK$",), "SGD": ("SGD", "S$"), "THB": ("THB", "฿"), "IDR": ("Rp", "IDR"), "INR": ("₹", "INR", "Rs"),
                "UAH": ("₴", "UAH", "грн")}
LOAI_MEO_DUNG = ("vua_khit", "the_nap")

# 3 khuon than x 3 cau ket; chon theo (so ngay tu NGAY_1) % 9 -> 9 to hop khac nhau, khong lap trong 7 ngay (T7)
KHUON_THAN = (
    "Tài khoản {vung}: {meo}.\nGiá gốc {goc}, giảm tới {han} (giờ VN).",
    "Giá cho tài khoản vùng {vung}: {meo}.\nGiá gốc {goc}. Hết giảm {han} (giờ VN).",
    "Hết giảm {han} (giờ VN), giá gốc {goc}.\nTài khoản {vung}: {meo}.",
)
KET = (
    "Ai đang chờ {ten} giảm sâu?",
    "Thẻ nạp phải đúng vùng tài khoản PSN, nhầm vùng là mất tiền.",
    "Tài khoản PSN chỉ dùng thẻ cùng vùng, kiểm kỹ trước khi mua.",
)


class KhongDang(Exception):
    """Dung het, KHONG dang gi (ma thoat 3). ly_do da che bi mat."""


# ---------------------------------------------------------------- tien ich
def _tg(s):
    """Chuoi ISO (Z / +00:00) -> datetime co mui gio; sai -> None."""
    if not isinstance(s, str) or not s.strip():
        return None
    try:
        t = dt.datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def _khong_dau(s):
    s = unicodedata.normalize("NFD", (s or "").replace("Đ", "D").replace("đ", "d"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def sha_dong1(dong1):
    return hashlib.sha256(" ".join(_khong_dau(dong1).lower().split()).encode()).hexdigest()


_RE_NHAN_HIEU = re.compile(r"[™®©]")
_RE_NGOAC_NGON_NGU = re.compile(r"\s*\((?:[^()]*(?:Chinese|English|Korean|Japanese|Thai|Ver\.?|Version)[^()]*)\)\s*$", re.I)
# CHI duoi edition chuan o CUOI ten (Remastered va phan sau dau ':' giu nguyen - doi no la doi nhan dang game)
_RE_BAN = re.compile(r"[\s\-–:]*(?:Definitive|Deluxe|Standard|Complete|Ultimate|Gold)\s+Edition\s*$", re.I)


def chuan_ten(s):
    """Dung de SO SANH ten (T2b): bo nhan hieu, ngoac ngon ngu cuoi, khoang trang, hoa thuong. Ca chuoi, khong 'mot tu chinh'."""
    s = _RE_NHAN_HIEU.sub("", s or "")
    s = _RE_NGOAC_NGON_NGU.sub("", s)
    return " ".join(s.split()).casefold()


def ten_dep(ten):
    """Ten de in len bai: bo nhan hieu, ngoac ngon ngu, duoi nen tang (PS4/PS5 Version...)."""
    s = _RE_NHAN_HIEU.sub("", ten or "")
    s = _RE_NGOAC_NGON_NGU.sub("", s)
    return " ".join(chung.bo_duoi_nen_tang(" ".join(s.split())).split())


def _nghin(vnd):
    """72000 -> '72 nghìn'; 72480 -> '72,5 nghìn'; tu 1.000.000 tro len -> '1,05 triệu' (them so voi spec 'nghìn' de khong ra '1.048 nghìn')."""
    if vnd >= 1_000_000:
        t = f"{vnd / 1_000_000:.2f}".rstrip("0").rstrip(".").replace(".", ",")
        return f"{t} triệu"
    if vnd % 1000 == 0:
        return f"{vnd // 1000} nghìn"
    return f"{vnd / 1000:.1f}".rstrip("0").rstrip(".").replace(".", ",") + " nghìn"


def ten_ngan(ten, giam, vnd):
    """Dong 1 phai <= 60 theo do_dai_x. Giu ten day du; chi khi can moi bo duoi edition chuan o CUOI ten. KHONG cat sau ':' hay ' - '.
    Van qua dai -> None (bo game, thu game ke)."""
    day_du = ten_dep(ten)
    ung = [day_du]
    bo = _RE_BAN.sub("", day_du).strip(" -–:")
    if bo and bo != day_du:
        ung.append(bo)
    for u in ung:
        if x.do_dai_x(dong1_tu(u, giam, vnd)) <= DONG1_TOI_DA:
            return u
    return None


def dong1_tu(ten_n, giam, vnd):
    return f"{ten_n} giảm {giam}%, còn {_nghin(vnd)}"


def _hoa_dau_meo(meo):
    """'Nạp 3 thẻ ...' -> 'nạp 3 thẻ ...' (dung sau dau ':'), giu nguyen neu chu thu hai viet hoa (USD, PS)."""
    if len(meo) > 1 and meo[0].isalpha() and meo[0].isupper() and meo[1].islower():
        return meo[0].lower() + meo[1:]
    return meo


# ---------------------------------------------------------------- chon game
def vung_co_gia_the(duong, hom_nay):
    """Tap ma vung co du lieu the trong gia-the.json: file ton tai, doc duoc, `cap_nhat` (khong co thi `ngay`) khong cu hon 7 ngay (T4)
    VA khoa `vung[<ma>]` khong rong. Khong dat -> set() (khong dung duoc cau the)."""
    try:
        d = json.loads(pathlib.Path(duong).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return set()
    if not isinstance(d, dict) or not isinstance(d.get("vung"), dict):
        return set()
    try:
        ngay = dt.date.fromisoformat(str(d.get("cap_nhat") or d.get("ngay"))[:10])
    except ValueError:
        return set()
    if not 0 <= (hom_nay - ngay).days <= GIA_THE_TOI_DA_NGAY:
        return set()
    return {k for k, v in d["vung"].items() if isinstance(v, dict) and v}


def meo_hop_le(hang):
    """Cau meo the cho than bai: loai vua_khit/the_nap, can_kiem False, co chu. Khong co -> None."""
    for m in hang.get("meo") or []:
        if isinstance(m, dict) and m.get("loai") in LOAI_MEO_DUNG and m.get("can_kiem") is False and str(m.get("chu") or "").strip():
            return str(m["chu"]).strip().rstrip(".")
    return None


def ung_vien(hang_ds, ngay_dang, gio_dang, da_dung_ma, vung_the):
    """Cac hang PS hop le, theo `hang` tang dan: ngay == ngay dang, vung co du lieu the, da kiem trang, khong lech gia, co meo the,
    han >= gio dang + 24 h, khong trung ma 7 ngay."""
    ra = []
    for h in sorted((h for h in hang_ds if isinstance(h, dict) and isinstance(h.get("hang"), int)), key=lambda r: r["hang"]):
        vung = h.get("vung_re_nhat")
        gv = (h.get("gia_vung") or {}).get(vung) if isinstance(h.get("gia_vung"), dict) else None
        han = _tg(h.get("han"))
        if (h.get("ngay") != ngay_dang or vung not in vung_the or h.get("da_kiem_trang") is not True or h.get("lech_gia")
                or vung not in LOC_VUNG or not isinstance(gv, dict) or not gv.get("mua_duoc") or gv.get("chi_plus")
                or not str(h.get("link") or "").startswith("https://store.playstation.com/") or not h.get("ten") or not h.get("ma")
                or h["ma"] in da_dung_ma or han is None or han < gio_dang + dt.timedelta(hours=HAN_TOI_THIEU_GIO)
                or not all(isinstance(h.get(k), int) and not isinstance(h.get(k), bool) and h[k] > 0 for k in ("gia_vnd", "gia_goc_vnd"))
                or not isinstance(h.get("giam"), int) or not 1 <= h["giam"] <= 100 or meo_hop_le(h) is None):
            continue
        ra.append(h)
    return ra


def da_dung_gan_day(cac_dong):
    """-> (set ma da dang/dang giu trong 7 ngay, set sha dong 1, set to hop khuon da dung). Dong 'that_bai'/'bo' khong tinh."""
    ma, sha, to_hop = set(), set(), set()
    for r in cac_dong:
        if r.get("kenh") != KENH or r.get("dang") != DANG or r.get("trang_thai") in ("that_bai", "bo"):
            continue
        if r.get("id_tai"):
            ma.add(str(r["id_tai"]))
        if r.get("manifest_sha"):
            sha.add(str(r["manifest_sha"]))
        if r.get("id_container"):
            to_hop.add(str(r["id_container"]))
    return ma, sha, to_hop


# ---------------------------------------------------------------- dung chu
def chon_to_hop(ngay, ngay_1):
    """(khuon than, cau ket) uu tien theo so ngay tu ngay 1: 9 to hop quay vong."""
    i = (ngay - ngay_1).days % 9
    return i % 3, (i // 3) % 3


def dung_chu(hang, ngay, ngay_1, sha_da_dung, to_hop_da_dung=()):
    """-> (text, dong1, ma_to_hop 'k<khuon>-t<ket>') hoac None: dong 1 > 60, dong 1 lap trong 7 ngay, hoac het to hop hop le
    (moi to hop phai dung do dai 150-260, khong URL/hashtag VA CHUA dung trong 7 ngay qua - doc tu id_container)."""
    ten_n = ten_ngan(hang["ten"], hang["giam"], hang["gia_vnd"])
    if ten_n is None:
        return None
    dong1 = dong1_tu(ten_n, hang["giam"], hang["gia_vnd"])
    if sha_dong1(dong1) in sha_da_dung:
        return None
    han = _tg(hang["han"]).astimezone(chung.VN)
    meo = _hoa_dau_meo(meo_hop_le(hang))
    k0, c0 = chon_to_hop(ngay, ngay_1)
    thu_tu = [((k0 + dk) % 3, (c0 + dc) % 3) for dc in range(3) for dk in range(3)]   # to hop cua ngay truoc, roi cac to hop con lai
    for k, c in thu_tu:
        ma = f"k{k}-t{c}"
        if ma in to_hop_da_dung:
            continue
        than = KHUON_THAN[k].format(vung=VUNG_VN[hang["vung_re_nhat"]], meo=meo, goc=_nghin(hang["gia_goc_vnd"]),
                                    han=f"{han:%H:%M} ngày {han.day}/{han.month}")
        text = f"{dong1}\n\n{than}\n\n{KET[c].format(ten=ten_n)}"
        if CHU_MIN <= x.do_dai_x(text) <= CHU_MAX and "#" not in text and "@" not in text and not x._URL.search(text):
            return text, dong1, ma
    return None


def tao_alt(hang, gia_hien, ngay):
    t = f"{ten_dep(hang['ten'])} trên PS Store {VUNG_VN[hang['vung_re_nhat']]}: {gia_hien} (giảm {hang['giam']}%), chụp {ngay:%d/%m/%Y}. " \
        "Giá niêm yết, chưa gồm thuế nếu có."
    return t[:ALT_TOI_DA]


# ---------------------------------------------------------------- chup + kiem anh/trang (T1, T2)
def chup_trang(url, duong, timeout=150):
    """Chay node cong-cu/chup-ps.mjs -> dict JSON 1 dong. Loi -> KhongDang."""
    try:
        p = subprocess.run(["node", str(SCRIPT_CHUP), url, str(duong)], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise KhongDang(f"chup trang loi ({type(e).__name__})") from None
    if p.returncode != 0:
        raise KhongDang("chup trang loi: " + chung.cat((p.stderr or "").strip().splitlines()[-1:] or ["?"], 160))
    try:
        d = json.loads((p.stdout or "").strip().splitlines()[-1])
    except (ValueError, IndexError):
        raise KhongDang("chup trang: dau ra khong phai JSON") from None
    if not isinstance(d, dict):
        raise KhongDang("chup trang: dau ra khong phai JSON object")
    return d


def _so_tien(s):
    """'HK$1,323.00' / 'Rp 224,941' / 'SGD60.13' -> float. Ca hai dau: dau o cuoi la thap phan. Mot dau: 3 chu so sau = nghin, con lai = thap phan."""
    t = re.sub(r"[^\d.,]", "", str(s or "")).strip(".,")
    if not t:
        return None
    if "," in t and "." in t:
        thap = "," if t.rfind(",") > t.rfind(".") else "."
        nghin = "." if thap == "," else ","
        return float(t.replace(nghin, "").replace(thap, "."))
    sep = "," if "," in t else "." if "." in t else None
    if sep is None:
        return float(t)
    nhom = t.split(sep)
    if len(nhom) > 2 or len(nhom[-1]) == 3:
        return float("".join(nhom))
    return float(t.replace(sep, "."))


def cung_tien(chuoi, tien):
    """Chuoi gia tren trang co ky hieu dung cua `tien` (USD khong duoc la 'HK$'/'S$')."""
    ky = KY_HIEU_TIEN.get(tien)
    if not ky:
        return False
    s = (chuoi or "").strip()
    if tien == "USD" and re.search(r"[A-Za-z]\$", s):
        return False
    return any(k in s for k in ky)


def _han_chu_ra_utc(han_chu):
    """'Offer ends 11/5/2026 02:59 PM GMT+7' (M/D/YYYY, locale en-US; GMT khong lech = UTC) -> datetime UTC; sai -> None."""
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})\s*([AP]M)(?:\s*(?:GMT|UTC)\s*(?:([+-])(\d{1,2})(?::?(\d{2}))?)?)?", han_chu or "", re.I)
    if not m:
        return None
    mo, d, y, h, mi, ap, dau, lech_g, lech_p = m.groups()
    gio = int(h) % 12 + (12 if ap.upper() == "PM" else 0)
    lech = dt.timedelta(hours=int(lech_g or 0), minutes=int(lech_p or 0)) * (-1 if dau == "-" else 1)
    try:
        return dt.datetime(int(y), int(mo), int(d), gio, int(mi), tzinfo=dt.timezone(lech)).astimezone(dt.timezone.utc)
    except ValueError:
        return None


def kiem_trang(hang, kq):
    """T2 (a)-(e), fail-closed. kq = JSON cua chup-ps.mjs. Sai -> KhongDang(ly do). Dung -> None."""
    vung, link = hang["vung_re_nhat"], str(hang["link"])
    m_link = re.match(r"https://store\.playstation\.com/([a-z]{2}-[a-z]{2})/product/([^/?#]+)", link, re.I)
    m_cuoi = re.match(r"https://store\.playstation\.com/([a-z]{2}-[a-z]{2})/product/([^/?#]+)", str(kq.get("url_cuoi") or ""), re.I)
    if not m_link or m_link.group(1).lower() != LOC_VUNG[vung]:
        raise KhongDang(f"link khong phai vung {vung} (locale {LOC_VUNG[vung]})")
    if not m_cuoi or m_cuoi.group(1).lower() != m_link.group(1).lower() or m_cuoi.group(2).upper() != m_link.group(2).upper():
        raise KhongDang("trang mo ra khac vung / khac product id so voi link (bi chuyen huong?)")
    if chuan_ten(kq.get("tieu_de")) != chuan_ten(hang["ten"]):
        raise KhongDang("tieu de trang khac ten game")
    gv = hang["gia_vung"][vung]
    hien, mong = kq.get("gia_hien"), gv.get("gia")
    if not hien or not mong or not cung_tien(hien, gv.get("tien")):
        raise KhongDang("gia tren trang thieu hoac khac tien te cua vung")
    a, b = _so_tien(hien), _so_tien(mong)
    if a is None or b is None or abs(a - b) > 0.011:
        raise KhongDang("gia tren trang khac gia vung trong sg_keo")
    # nhat quan gia VND / gia vung / gia goc / % giam (fail-closed khi khong doc duoc)
    if kq.get("so_khoi") != 1:
        raise KhongDang("trang co nhieu hon 1 khoi gia thuong (khong chac khoi nao la cua san pham)")
    if gv.get("vnd") != hang["gia_vnd"]:
        raise KhongDang("gia VND trong gia_vung khac gia_vnd cua hang")
    if isinstance(gv.get("giam"), (int, float)) and abs(gv["giam"] - hang["giam"]) > 1:
        raise KhongDang("giam trong gia_vung khac giam cua hang")
    m_giam = re.search(r"(\d{1,3})\s*%", str(kq.get("giam_chu") or ""))
    goc_trang = _so_tien(kq.get("gia_goc"))
    if not m_giam or goc_trang is None or goc_trang <= 0 or not cung_tien(kq.get("gia_goc"), gv.get("tien")):
        raise KhongDang("khong doc duoc 'Save N%' hoac gia goc tren trang")
    if abs(int(m_giam.group(1)) - hang["giam"]) > 1 or abs(100 * (1 - a / goc_trang) - hang["giam"]) > 1.5:
        raise KhongDang("% giam / gia goc tren trang khong khop giam cua hang")
    han_trang, han_keo = _han_chu_ra_utc(kq.get("han_chu")), _tg(hang["han"])
    if han_trang is None or han_keo is None or abs((han_trang - han_keo).total_seconds()) > 60:
        raise KhongDang("han 'Offer ends' tren trang khac han trong sg_keo")
    if int(kq.get("rong") or 0) < ANH_RONG_MIN or int(kq.get("cao") or 0) < ANH_CAO_MIN:
        raise KhongDang("anh cat qua nho")


# ---------------------------------------------------------------- luong chinh
def _bao(tieu_de, noi_dung):
    """ntfy loi; gui THANH CONG + co env DA_BAO_FILE -> tao file co de buoc cuoi workflow khong bao lai (nhu do_so/chay.py)."""
    chung.log_loi(f"x_goc: {tieu_de}: {noi_dung}")
    if ntfy.loi(tieu_de, noi_dung) is True and os.environ.get("DA_BAO_FILE"):
        try:
            open(os.environ["DA_BAO_FILE"], "w").close()
        except OSError:
            pass


def _gio_du_kien(ngay, gio):
    h, m = (int(p) for p in gio.split(":"))
    return dt.datetime(ngay.year, ngay.month, ngay.day, h, m, tzinfo=chung.VN)


def khung_hom_nay(ngay, ngay_1):
    """'sang' (ngay le tinh tu ngay 1 = ngay_1) hoac 'toi' (ngay chan)."""
    return "sang" if (ngay - ngay_1).days % 2 == 0 else "toi"


def chuan_bi(cong, ngay, ngay_1, gio, gia_the, chup=chup_trang, thu_muc=None):
    """Phan cuc bo, khong tac dung phu: chon game -> chu -> chup -> kiem. -> dict(hang, text, dong1, to_hop, alt, anh, kq_chup, due)."""
    due = _gio_du_kien(ngay, gio)
    cac_dong = cong.doc_dang((ngay - dt.timedelta(days=NGAY_KHONG_LAP)).isoformat(), (ngay - dt.timedelta(days=1)).isoformat(), "that")
    ma_da, sha_da, to_hop_da = da_dung_gan_day(cac_dong)
    ds = ung_vien(cong.doc_keo(ngay.isoformat()), ngay.isoformat(), due, ma_da, vung_co_gia_the(gia_the, ngay))
    if not ds:
        raise KhongDang("khong con game hop le hom nay (hoac gia-the.json thieu/cu hon 7 ngay/khong co du lieu vung cua game)")
    for hang in ds:
        ct = dung_chu(hang, ngay, ngay_1, sha_da, to_hop_da)
        if ct is None:
            chung.log(f"x_goc: bo {hang['ma']}: khong dung duoc chu hop le (ten qua dai / lap dong 1 / het to hop khuon)")
            continue
        text, dong1, to_hop = ct
        anh = pathlib.Path(thu_muc) / "anh-ps.png"
        kq = chup(str(hang["link"]), str(anh))
        kiem_trang(hang, kq)
        return {"hang": hang, "text": text, "dong1": dong1, "to_hop": to_hop, "alt": tao_alt(hang, kq["gia_hien"], ngay), "anh": anh,
                "kq_chup": kq, "due": due}
    raise KhongDang("khong game nao dung duoc chu hop le")


def kiem_url_anh(url):
    """URL cong khai cua anh (Zernio) phai tra 200 + image/png truoc khi dua cho Buffer."""
    try:
        r = http.gui("GET", url, timeout=60)
    except http.LoiMang as e:
        raise chung.LoiDang(f"Zernio: URL anh khong tai duoc ({e}) (chua tao bai)") from None
    if r.status != 200 or not r.headers.get("content-type", "").lower().startswith("image/png"):
        raise chung.LoiDang(f"Zernio: URL anh khong dat (HTTP {r.status}, {chung.cat(r.headers.get('content-type'), 40)}) (chua tao bai)")


def kiem_gio(due, buoc):
    """Con < 2 phut toi dueAt (hoac da qua) -> KhongDang. Goi truoc moi buoc khong the huy: upload anh, createPost."""
    if chung.bay_gio() > due - dt.timedelta(minutes=TRE_TOI_DA_PHUT):
        raise KhongDang(f"con < {TRE_TOI_DA_PHUT} phut toi gio dang ({due.astimezone(chung.VN):%H:%M} VN) o buoc {buoc} - khong len lich")


def dang_bai(cong, che_do, ngay, goi, buffer_khoa, zernio_khoa):
    """Giu quyen -> (thu: dung) -> upload -> Buffer -> cho sent -> da_dang. -> ma thoat."""
    hang, due = goi["hang"], goi["due"]
    if not cong.giu_dang(ngay.isoformat(), DANG, KENH, che_do, chung.iso(due), sha_dong1(goi["dong1"])):
        raise KhongDang("da co dong sg_dang cua hom nay (luot khac giu quyen)")
    khoa_dong = dict(ngay=ngay.isoformat(), dang=DANG, kenh=KENH, che_do=che_do)
    cong.cap_nhat_dang(**khoa_dong, id_tai=str(hang["ma"]), id_container=goi["to_hop"])
    if che_do == "thu":
        chung.log(f"x_goc [thu] chu ({x.do_dai_x(goi['text'])} ky tu X, to hop {goi['to_hop']}):\n{goi['text']}\n--- ALT ({len(goi['alt'])}):\n{goi['alt']}\n"
                  f"--- anh: {goi['kq_chup'].get('rong')}x{goi['kq_chup'].get('cao')} px ({goi['anh']})")
        cong.cap_nhat_dang(**khoa_dong, trang_thai="that_bai", loi="che do thu: khong dang")   # cho phep chay thu lai
        return 0
    post_id, da_gui, loi_so = None, False, False
    try:
        chung.dang_ky_bi_mat(buffer_khoa, zernio_khoa)
        kiem_gio(due, "truoc upload anh")
        url_anh = zernio.tai_anh(zernio_khoa, goi["anh"], f"sangame-x-goc-{ngay.isoformat()}.png")
        kiem_url_anh(url_anh)
        kiem_gio(due, "truoc createPost")
        da_gui = True       # tu day moi ngoai le chua chung minh 'chua tao' deu la khong_ro
        post_id = x.tao_bai_anh(buffer_khoa, goi["text"], url_anh, goi["alt"], chung.iso(due))
        try:
            cong.cap_nhat_dang(**khoa_dong, id_bai=post_id)
        except Exception as e:
            loi_so = True
            _bao("X goc: khong ghi duoc id_bai", f"Buffer id {post_id}: {chung.cat(e, 150)}. Doi soat Buffer theo id.")
        han = due + dt.timedelta(minutes=CHO_SAU_DUE_PHUT)
        cho = max(CHUA_SO_GIAY, (han - chung.bay_gio()).total_seconds() - CHUA_SO_GIAY)
        ket = x.hoi_den_xong(buffer_khoa, post_id, toi_da_giay=cho, han_tuyet_doi=han - dt.timedelta(seconds=CHUA_SO_GIAY))
        link, sent_luc = ket.get("link"), ket.get("sent_luc")
        if not link:                                  # 'sent' nhung chua co externalLink: hoi them toi da 2 phut
            link, sent_luc2 = x.hoi_them_link(buffer_khoa, post_id, 120)
            sent_luc = sent_luc or sent_luc2
    except KhongDang as e:
        try:
            cong.cap_nhat_dang(**khoa_dong, trang_thai="that_bai", loi=chung.cat(e, 300))   # chua tao bai (kiem_gio chay truoc createPost)
        except Exception:
            pass
        _bao("X goc: khong dang hom nay", chung.cat(e, 300))
        return 3
    except Exception as e:   # LoiDang theo quy uoc x.py (khong_ro ro rang); ngoai le la SAU moc da_gui = khong ro
        khong_ro = e.khong_ro if isinstance(e, chung.LoiDang) else da_gui
        trang_thai = "khong_ro" if khong_ro else "that_bai"
        try:
            cong.cap_nhat_dang(**khoa_dong, trang_thai=trang_thai, loi=chung.cat(e, 300))
        except Exception:
            pass
        _bao("X goc: " + ("khong ro da dang chua" if khong_ro else "chua dang"), chung.cat(f"{type(e).__name__}: {e}", 300))
        return 1
    gio_ck = _tg(sent_luc) if isinstance(sent_luc, str) else None
    try:
        cong.cap_nhat_dang(**khoa_dong, trang_thai="da_dang", id_bai=post_id, link=link,
                           gio_cong_khai=chung.iso(gio_ck or chung.bay_gio()), id_tai=str(hang["ma"]))
    except Exception as e:
        _bao("X goc: ĐÃ đăng nhưng ghi sổ lỗi", f"đối soát Buffer id {post_id} (link {link or 'chưa có'}): {chung.cat(f'{type(e).__name__}: {e}', 150)}")
        return 1
    if loi_so:
        _bao("X goc: đã đăng, id_bai từng ghi lỗi", f"Buffer id {post_id}: đã ghi lại da_dang, kiểm sổ.")
        return 1
    if not link:
        _bao("X goc: đã đăng nhưng Buffer chưa trả link", f"Buffer id {post_id}: da_dang không link, bổ sung tay để đo.")
    ntfy.tin("Đã đăng bài X gốc", f"{goi['dong1']}\n{link or ''}", click=link or None)
    return 0


def chay(a, cong=None, chup=chup_trang):
    ngay_1_chuoi = os.environ.get("SG_X_GOC_NGAY_1", "").strip()
    try:
        ngay_1 = dt.date.fromisoformat(ngay_1_chuoi)
    except ValueError:
        _bao("X goc: thieu/sai SG_X_GOC_NGAY_1", "can bien repo SG_X_GOC_NGAY_1 = YYYY-MM-DD (ngay 1 cua lich X goc)")
        return 2
    ngay = dt.date.fromisoformat(a.ngay)
    hom_nay = khung_hom_nay(ngay, ngay_1)
    if a.khung != hom_nay:
        chung.log(f"x_goc: không phải khung hôm nay (ngày {a.ngay} là khung {hom_nay}, đã gọi khung {a.khung}) - không làm gì")
        return 0
    gio = GIO_KHUNG[a.khung]
    try:
        cong = cong or so.Cong()
    except so.LoiCong as e:
        _bao("X goc: thieu khoa cong", str(e))
        return 2
    buffer_khoa, zernio_khoa = os.environ.get("BUFFER_KHOA", "").strip(), os.environ.get("ZERNIO_KHOA", "").strip()
    if a.che_do == "that" and not (buffer_khoa and zernio_khoa):
        _bao("X goc: thieu khoa", "can BUFFER_KHOA va ZERNIO_KHOA o che do that")
        return 2
    due = _gio_du_kien(ngay, gio)
    if a.che_do == "that" and chung.bay_gio() > due - dt.timedelta(minutes=TRE_TOI_DA_PHUT):
        _bao("X goc: qua gio len lich", f"bay gio da qua {gio} VN - {TRE_TOI_DA_PHUT} phut, khong len lich (khong dang bu)")
        return 3
    thu_muc = tempfile.mkdtemp(prefix="sg-xgoc-")
    try:
        try:
            goi = chuan_bi(cong, ngay, ngay_1, gio, a.gia_the, chup, thu_muc)
            return dang_bai(cong, a.che_do, ngay, goi, buffer_khoa, zernio_khoa)
        except KhongDang as e:
            _bao("X goc: khong dang hom nay", chung.cat(e, 300))
            return 3
    finally:
        shutil.rmtree(thu_muc, ignore_errors=True)   # anh Sony khong o lai may


def main(argv=None):
    ap = argparse.ArgumentParser(description="Bai X goc Sang Game")
    ap.add_argument("--ngay", default=chung.bay_gio().astimezone(chung.VN).date().isoformat())
    ap.add_argument("--khung", required=True, choices=["sang", "toi"])
    ap.add_argument("--che-do", required=True, choices=["thu", "that"])
    ap.add_argument("--gia-the", default="du-lieu/du-lieu/gia-the.json")
    a = ap.parse_args(argv)
    try:
        dt.date.fromisoformat(a.ngay)
    except ValueError:
        ap.error("--ngay phai la YYYY-MM-DD")
    try:
        return chay(a)
    except Exception as e:
        _bao("X goc: loi bat ngo", chung.cat(f"{type(e).__name__}: {e}", 300))
        return 1


if __name__ == "__main__":
    sys.exit(main())
