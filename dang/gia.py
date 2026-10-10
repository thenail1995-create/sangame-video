"""Kiem lai gia / han deal ngay truoc gio dang (B4, Sol #13). Cao trang san pham PS Store dung `loc` + `pid` cua manifest.
Regex endTime / gia theo dang-lam/video-top5-01/chon-top5.py (endTime) - gia la CHUA KIEM.
# CHUA KIEM: truong "discountedPrice" trong JSON nhung cua trang san pham (chua co mau that); lay gia tri DAU TIEN trong trang.
# CHUA KIEM: HOP-DONG kiem_lai chi co gia_vnd (da quy doi) -> khong so duoc gia thang. Bo so gia cuc bo `gia_cuc_bo`
#   (so, theo tien te cua `loc`) la TUY CHON: co thi so lech > 2%; khong co thi chi kiem han va ghi canh bao. Can Opus bo sung HOP-DONG.
"""
import re

from . import chung, http

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
DUNG_SAI_GIA = 0.02
DEM_SAU_GIO_DANG = 2 * 3600


def doc_gia(chuoi):
    s = re.sub(r"[^\d.,]", "", chuoi or "").replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def kiem_lai(muc, gio_dang):
    """-> (van_de [lam bo khung], canh_bao [chi bao]). gio_dang: datetime co mui gio."""
    van_de, canh_bao = [], []
    han_toi_thieu = gio_dang.timestamp() + DEM_SAU_GIO_DANG
    for m in muc or []:
        ten, pid, loc = m.get("ten", "?"), m.get("pid"), m.get("loc")
        if not pid or not loc or not re.fullmatch(r"[a-z]{2}-[a-z]{2}", loc) or not re.fullmatch(r"[A-Za-z0-9_\-]+", pid):
            van_de.append(f"{ten}: thieu/sai pid hoac loc trong kiem_lai")
            continue
        try:
            r = http.gui("GET", f"https://store.playstation.com/{loc}/product/{pid}", headers={"User-Agent": UA},
                         theo_chuyen_huong=True, timeout=30)
        except http.LoiMang as e:
            canh_bao.append(f"{ten}: khong cao duoc trang san pham ({e})")
            continue
        if r.status != 200:
            canh_bao.append(f"{ten}: trang san pham HTTP {r.status}, khong kiem lai duoc")
            continue
        html = r.text
        ends = re.findall(r'"endTime":"(\d+)"', html)
        if ends:
            if int(ends[0]) / 1000 < han_toi_thieu:
                van_de.append(f"{ten}: het han luc {ends[0]} (< gio dang + 2 h)")
        elif m.get("endTime"):
            canh_bao.append(f"{ten}: manifest co endTime nhung trang khong con endTime (co the deal da ket thuc)")
        gia_m = re.search(r'"discountedPrice":"([^"]+)"', html)
        goc = m.get("gia_cuc_bo")
        if goc is None:
            canh_bao.append(f"{ten}: manifest khong co gia_cuc_bo, bo qua so gia")
        elif not gia_m or doc_gia(gia_m.group(1)) is None:
            canh_bao.append(f"{ten}: khong doc duoc gia tren trang")
        else:
            moi = doc_gia(gia_m.group(1))
            if goc and abs(moi - goc) / goc > DUNG_SAI_GIA:
                van_de.append(f"{ten}: gia doi {goc} -> {moi} (> 2%)")
    return van_de, canh_bao
