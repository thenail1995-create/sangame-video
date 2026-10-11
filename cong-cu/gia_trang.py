"""Doc GIA + HAN + MEDIA cua DUNG 1 san pham tu trang san pham PS Store (Sol #14 #15).
Chi dung stdlib (job chon chay bang python3 he thong). Dung chung: khuon/keo-thom/chon-keo.py, khuon/top5/chon-top5.py, dang/gia.py.

Cau truc trang (da xem tren trang that en-us/en-hk/en-sg/en-id, 11/10/2026): nhieu the <script id="env:..."> moi the co JSON {"cache": {...}}.
  - Khoi gia: khoa `GameCTA:ADD_TO_CART:ADD_TO_CART:<PID>-<SKU>:OUTRIGHT` (mua dut; game PS4/CUSA khong co hau to `:OUTRIGHT`; UPSELL_*/DOWNLOAD_* la nut khac). Gia tri: {"price": {"discountedPrice": "HK$47.70", "basePrice": ...,
    "discountedValue": 4770, "basePriceValue": 31800, "currencyCode": "HKD", "endTime": "1792594740000" | null}}.
    `endTime` nam NGAY TRONG khoi price cua chinh GameCTA do (khong phai doi tuong khac tren trang).
  - Trang con chua GameCTA cua san pham KHAC (ban tieu chuan/ban PS4/game goi y) -> chi nhan khoa chua dung PID, SKU khong chua them dau '-'.
  - Media: `Product:<PID>` -> `media` va `personalizedMeta.media` (VIDEO/PREVIEW, IMAGE/SCREENSHOT/MASTER/EDITION_KEY_ART).
  - Gioi thieu game (11/10): `Product:<PID>` xuat hien o NHIEU the script, moi the mot manh (starRating o the nay, localizedGenres o the kia, descriptions + edition.features o the khac) -> hop nhat theo khoa (thong_tin_game).
Khong regex toan trang, khong "gia dau tien tren trang".
"""
import json
import re

_SCRIPT = re.compile(r'<script id="env:[^"]+"[^>]*>(.*?)</script>', re.S)
_SKU = re.compile(r"[A-Za-z0-9]+")


def doc_gia(chuoi):
    """Doc so tien theo ca dinh dang US (1,299.00 / HK$47.70) lan EU/VN (1.234.000 / 47,70) va ngan cach nghin don le:
      - co ca '.' va ',' -> dau xuat hien SAU CUNG la thap phan, dau con lai la ngan cach nghin;
      - mot loai dau xuat hien nhieu lan -> ngan cach nghin;
      - mot dau xuat hien 1 lan: sau no dung 3 chu so -> ngan cach nghin (1,299 / 1.299), nguoc lai -> thap phan (47,70)."""
    m = re.search(r"\d[\d.,\s  ]*\d|\d", str(chuoi or ""))
    if not m:
        return None
    s = re.sub(r"[\s  ]", "", m.group(0))
    if "." in s and "," in s:
        tp = "." if s.rfind(".") > s.rfind(",") else ","
        nghin = "," if tp == "." else "."
        s = s.replace(nghin, "").replace(tp, ".")
    else:
        for d in (".", ","):
            if d in s:
                if s.count(d) > 1 or len(s.rsplit(d, 1)[1]) == 3:
                    s = s.replace(d, "")
                else:
                    s = s.replace(d, ".")
    try:
        return float(s)
    except ValueError:
        return None


def _cache_cac_the(html):
    for m in _SCRIPT.finditer(html or ""):
        try:
            c = json.loads(m.group(1)).get("cache", {})
        except Exception:
            continue
        if isinstance(c, dict):
            yield c


def _khoa_cua_pid(khoa, pid):
    """Khoa nut MUA DUT cua DUNG pid -> SKU, nguoc lai None. Hai dang khoa that:
      `GameCTA:ADD_TO_CART:ADD_TO_CART:<PID>-<SKU>:OUTRIGHT`  (game PS5, PPSA)
      `GameCTA:ADD_TO_CART:ADD_TO_CART:<PID>-<SKU>`           (game PS4/CUSA, khong co hau to)
    Loai: UPSELL_* (PS Plus/EA Access: gia 'Included'), DOWNLOAD_* (demo/thu), UNAVAILABLE, khoa cua san pham khac."""
    p = khoa.split(":")
    if len(p) not in (4, 5) or p[:3] != ["GameCTA", "ADD_TO_CART", "ADD_TO_CART"] or (len(p) == 5 and p[4] != "OUTRIGHT"):
        return None
    if not p[3].startswith(pid + "-"):
        return None
    sku = p[3][len(pid) + 1:]
    return sku if _SKU.fullmatch(sku) else None


def _nhat_quan(chuoi, gia_tri):
    """Chuoi gia hien thi khop gia tri nguyen trong cache (don vi nho nhat HOAC don vi tien khong co phan le: IDR)."""
    v = doc_gia(chuoi)
    if v is None or not isinstance(gia_tri, (int, float)) or isinstance(gia_tri, bool) or gia_tri < 0:
        return None
    for he in (0.01, 1.0):
        if abs(v - gia_tri * he) <= 0.005 * max(v, 1):
            return v
    return None


def khoi_gia(html, pid):
    """-> dict(gia_cuc_bo, gia_goc, tien_te, endTime (chuoi ms | None), sku) hoac None.
    None khi: khong co khoi mua dut gan DUNG pid; co nhieu khoi mua dut khac gia/han cho cung pid (mo ho); gia khong doc duoc/lech gia tri cache.
    endTime lay tu CHINH khoi gia do; khoi khong co hang -> endTime None (ben goi loai)."""
    if not pid or not isinstance(html, str):
        return None
    ung = {}
    for c in _cache_cac_the(html):
        for khoa, v in c.items():
            if not isinstance(v, dict) or not khoa.startswith("GameCTA:"):
                continue
            sku = _khoa_cua_pid(khoa, pid)
            pr = v.get("price")
            if sku is None or not isinstance(pr, dict) or pr.get("discountedValue") is None:
                continue
            ung[(pr.get("discountedValue"), pr.get("basePriceValue"), pr.get("currencyCode"), pr.get("endTime"))] = (sku, pr)
    if len(ung) != 1:
        return None   # 0 = khong co khoi cua pid; >1 = nhieu khoi mua dut khac nhau cho cung pid -> mo ho
    sku, pr = next(iter(ung.values()))
    con = _nhat_quan(pr.get("discountedPrice"), pr.get("discountedValue"))
    if con is None:
        return None
    goc = _nhat_quan(pr.get("basePrice"), pr.get("basePriceValue"))
    end = pr.get("endTime")
    end = str(end) if isinstance(end, (str, int)) and re.fullmatch(r"\d+", str(end)) else None
    return dict(gia_cuc_bo=con, gia_goc=goc, tien_te=pr.get("currencyCode"), endTime=end, sku=sku)


def media(html, pid):
    """-> dict(video[], anh_chup[], anh|None) CHI tu `Product:<pid>` (khong lay media cua game goi y/ban khac tren trang)."""
    video, shots, anh = [], [], []
    for c in _cache_cac_the(html):
        p = c.get(f"Product:{pid}")
        if not isinstance(p, dict):
            continue
        ds = list(p.get("media") or []) + list((p.get("personalizedMeta") or {}).get("media") or [])
        for x in ds:
            if not isinstance(x, dict) or not isinstance(x.get("url"), str):
                continue
            if x.get("type") == "VIDEO" and "vulcan.dl.playstation.net" in x["url"] and x["url"].endswith(".mp4"):
                video.append(x["url"])
            elif x.get("role") == "SCREENSHOT":
                shots.append(x["url"])
            elif x.get("role") in ("MASTER", "EDITION_KEY_ART"):
                anh.append(x["url"])
    return dict(video=list(dict.fromkeys(video)), anh_chup=list(dict.fromkeys(shots)), anh=anh[0] if anh else None)


def khoi_khop(html, pid, gia_du_lieu, dung_sai=0.02):
    """Khoi gia cua DUNG pid + doi chieu voi gia trong du lieu vung (so hoac chuoi 'HK$47.70'; lech <= dung_sai) + khoi phai dang GIAM (goc > con).
    -> (khoi, None) hoac (None, ly do loai)."""
    k = khoi_gia(html, pid)
    if k is None:
        return None, "trang khong co khoi gia mua dut ro rang cua dung pid (khong co khoi cua pid, nhieu khoi gia khac nhau, hoac gia khong doc duoc)"
    a = gia_du_lieu if isinstance(gia_du_lieu, (int, float)) and not isinstance(gia_du_lieu, bool) else doc_gia(gia_du_lieu)
    if not a or a <= 0:
        return None, f"gia trong du lieu khong doc duoc ({gia_du_lieu})"
    if abs(k["gia_cuc_bo"] - a) / a > dung_sai:
        return None, f"gia khoi pid tren trang {k['gia_cuc_bo']} lech du lieu {gia_du_lieu} > {dung_sai:.0%}"
    if not k["gia_goc"] or k["gia_goc"] <= k["gia_cuc_bo"]:
        return None, "khoi gia cua pid khong dang giam (gia goc <= gia hien tai)"
    return k, None


def ps_plus_catalog(html, pid):
    """True neu trang co nut `UPSELL_PS_PLUS_GAME_CATALOG` gan DUNG pid (game nam trong PS Plus Game Catalog: nguoi co Extra choi duoc)."""
    if not pid or not isinstance(html, str):
        return False
    for c in _cache_cac_the(html):
        for khoa in c:
            p = khoa.split(":")
            if khoa.startswith("GameCTA:") and len(p) >= 4 and p[1] == "UPSELL_PS_PLUS_GAME_CATALOG" and p[3].startswith(pid + "-") and "-" not in p[3][len(pid) + 1:]:
                return True
    return False


def thong_tin_game(html, pid):
    """Thong tin GIOI THIEU cua DUNG san pham (khong lay cua game goi y): hop nhat moi manh `Product:<pid>` tren trang (ghi de khong; manh nao co truoc thi dung).
    -> dict(the_loai[str], diem{tb, so_luot}|None, edition{ten, loai, tinh_nang[str]}|None, mo_ta_dai str ('<br/>' giu nguyen), mo_ta_ngan str). Truong khong co = rong/None (KHONG doan).
    Chi doc du lieu co san tren trang (PS Store: starRating, localizedGenres, edition, descriptions); noi dung tieng Anh goc, viec dich sang loi doc o khuon/keo-thom/loi_chu.py (bang co dinh)."""
    hop = {}
    if pid and isinstance(html, str):
        for c in _cache_cac_the(html):
            p = c.get(f"Product:{pid}")
            if not isinstance(p, dict):
                continue
            for k in ("starRating", "localizedGenres", "edition", "descriptions"):
                if not p.get(k):
                    continue
                if k == "edition" and isinstance(p[k], dict):   # edition cung bi chia manh ({name} o the nay, {name, features, type} o the kia): hop nhat tung truong
                    cu = hop.get(k) or {}
                    hop[k] = {**{a: b for a, b in p[k].items() if b}, **{a: b for a, b in cu.items() if b}}
                elif not hop.get(k):
                    hop[k] = p[k]
    sr = hop.get("starRating") if isinstance(hop.get("starRating"), dict) else {}
    tb, n = sr.get("averageRating"), sr.get("totalRatingsCount")
    diem = dict(tb=float(tb), so_luot=int(n)) if isinstance(tb, (int, float)) and not isinstance(tb, bool) and isinstance(n, int) and not isinstance(n, bool) and n >= 0 else None
    gen = [x.get("value") for x in (hop.get("localizedGenres") or []) if isinstance(x, dict) and isinstance(x.get("value"), str)]
    ed = hop.get("edition") if isinstance(hop.get("edition"), dict) else None
    edition = dict(ten=ed.get("name") or "", loai=ed.get("type") or "", tinh_nang=[x for x in (ed.get("features") or []) if isinstance(x, str)]) if ed and ed.get("name") else None
    mo = {x.get("type"): x.get("value") for x in (hop.get("descriptions") or []) if isinstance(x, dict) and isinstance(x.get("value"), str)}
    return dict(the_loai=gen, diem=diem, edition=edition, mo_ta_dai=mo.get("LONG", ""), mo_ta_ngan=mo.get("SHORT", ""))


def hop_nhat_thong_tin(ds):
    """Nhieu trang (vung re nhat truoc) -> mot dict: moi truong lay tu trang DAU TIEN co truong do."""
    ra = dict(the_loai=[], diem=None, edition=None, mo_ta_dai="", mo_ta_ngan="")
    for d in ds:
        for k, v in d.items():
            if v and not ra.get(k):
                ra[k] = v
    return ra
