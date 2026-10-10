"""Kiem lai gia / han deal ngay truoc gio dang (B4, Sol #13). Cao trang san pham PS Store dung `loc` + `pid` cua manifest.
FAIL-CLOSED: khong xac minh duoc (timeout, HTTP loi, mat endTime, khong doc duoc gia, thieu gia_cuc_bo) -> coi la van de, bo khung.
# CHUA KIEM: truong "discountedPrice" trong JSON nhung cua trang san pham (chua co mau that); lay gia tri DAU TIEN trong trang.
"""
import re

from . import http

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
DUNG_SAI_GIA = 0.02
DEM_SAU_GIO_DANG = 2 * 3600


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


def kiem_lai(muc, gio_dang):
    """-> (van_de, canh_bao). van_de khac rong = BO KHUNG. gio_dang: datetime co mui gio."""
    van_de, canh_bao = [], []
    if not muc:
        return ["manifest khong co kiem_lai - khong xac minh duoc gia/han"], canh_bao
    han_toi_thieu = gio_dang.timestamp() + DEM_SAU_GIO_DANG
    for m in muc:
        ten, pid, loc = m.get("ten", "?"), m.get("pid"), m.get("loc")
        if not pid or not loc or not re.fullmatch(r"[a-z]{2}-[a-z]{2}", loc) or not re.fullmatch(r"[A-Za-z0-9_\-]+", pid):
            van_de.append(f"{ten}: thieu/sai pid hoac loc trong kiem_lai")
            continue
        try:
            r = http.gui("GET", f"https://store.playstation.com/{loc}/product/{pid}", headers={"User-Agent": UA},
                         theo_chuyen_huong=True, timeout=30)
        except http.LoiMang as e:
            van_de.append(f"{ten}: khong cao duoc trang san pham ({e})")
            continue
        if r.status != 200:
            van_de.append(f"{ten}: trang san pham HTTP {r.status}, khong kiem lai duoc")
            continue
        html = r.text
        ends = re.findall(r'"endTime":"(\d+)"', html)
        if not ends:
            van_de.append(f"{ten}: trang khong con endTime (deal co the da ket thuc hoac doi cau truc trang)")
        elif int(ends[0]) / 1000 < han_toi_thieu:
            van_de.append(f"{ten}: het han luc {ends[0]} (< gio dang + 2 h)")
        goc = m.get("gia_cuc_bo")
        gia_m = re.search(r'"discountedPrice":"([^"]+)"', html)
        moi = doc_gia(gia_m.group(1)) if gia_m else None
        if not isinstance(goc, (int, float)) or goc <= 0:
            van_de.append(f"{ten}: manifest thieu gia_cuc_bo hop le - khong so gia duoc")
        elif moi is None:
            van_de.append(f"{ten}: khong doc duoc gia tren trang")
        elif abs(moi - goc) / goc > DUNG_SAI_GIA:
            van_de.append(f"{ten}: gia doi {goc} -> {moi} (> 2%)")
    return van_de, canh_bao
