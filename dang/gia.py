"""Kiem lai gia / han deal ngay truoc gio dang (B4, Sol #13; C1 Sol bcd #14/#15). Cao trang san pham PS Store dung `loc` + `pid` cua manifest.
FAIL-CLOSED: khong xac minh duoc (timeout, HTTP loi, khong co khoi gia mua dut gan DUNG pid, khoi gia mo ho, mat endTime, thieu gia_cuc_bo) -> coi la van de, bo khung.
Gia + han doc tu KHOI GIA CUA DUNG PID trong cache JSON cua trang (cong-cu/gia_trang.py), KHONG lay "gia dau tien tren trang".
"""
import importlib.util
import pathlib
import re
import time

from . import http

_f = pathlib.Path(__file__).resolve().parent.parent / "cong-cu" / "gia_trang.py"   # nap theo duong dan (cong-cu khong phai package, tranh them sys.path)
_spec = importlib.util.spec_from_file_location("sangame_gia_trang", _f)
gia_trang = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gia_trang)
doc_gia = gia_trang.doc_gia

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
DUNG_SAI_GIA = 0.02
DEM_SAU_GIO_DANG = 2 * 3600
LECH_HAN_MS = 60 * 1000   # cho lech lam tron toi 1 phut


SO_LAN_TAI = 3           # 12/10: Sony tra trang bat thuong 1 lan -> bo ca khung Tin nhanh. Tai lai toi da 3 lan moi ket luan.
CHO_GIUA_LAN = 20        # giay


def _tai_khoi(loc, pid, so_lan=None, cho=None):
    """-> (khoi, None) hoac (None, ly_do). Tai lai khi HTTP loi/timeout/khong co khoi gia dung pid; van fail-closed neu
    ca so_lan deu hong. Ghi log do dai HTML + so lan xuat hien pid de chan doan lan sau."""
    so_lan = SO_LAN_TAI if so_lan is None else so_lan
    cho = CHO_GIUA_LAN if cho is None else cho
    ly_do = "khong tai duoc"
    for lan in range(1, so_lan + 1):
        if lan > 1:
            time.sleep(cho)
        try:
            r = http.gui("GET", f"https://store.playstation.com/{loc}/product/{pid}", headers={"User-Agent": UA},
                         theo_chuyen_huong=True, timeout=30)
        except http.LoiMang as e:
            ly_do = f"khong cao duoc trang san pham ({e})"
            print(f"kiem_lai {pid} {loc} lan {lan}/{so_lan}: {ly_do}", flush=True)
            continue
        if r.status != 200:
            ly_do = f"trang san pham HTTP {r.status}, khong kiem lai duoc"
            print(f"kiem_lai {pid} {loc} lan {lan}/{so_lan}: {ly_do}", flush=True)
            continue
        khoi = gia_trang.khoi_gia(r.text, pid)
        if khoi is not None:
            if lan > 1:
                print(f"kiem_lai {pid} {loc}: dat o lan {lan}", flush=True)
            return khoi, None
        ly_do = "trang khong co khoi gia mua dut ro rang cua dung pid (doi cau truc trang, het ban hoac nhieu khoi gia khac nhau)"
        html = r.text or ""
        print(f"kiem_lai {pid} {loc} lan {lan}/{so_lan}: khong co khoi gia; html {len(html)} ky tu, pid xuat hien "
              f"{html.count(pid)} lan, 'discountedPrice' {html.count('discountedPrice')} lan", flush=True)
    return None, f"{ly_do} (sau {so_lan} lan tai)"


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
        khoi, loi = _tai_khoi(loc, pid)
        if khoi is None:
            van_de.append(f"{ten}: {loi}")
            continue
        end = khoi["endTime"]
        if not end:
            van_de.append(f"{ten}: khoi gia khong con endTime (deal co the da ket thuc hoac doi cau truc trang)")
        elif int(end) / 1000 < han_toi_thieu:
            van_de.append(f"{ten}: het han luc {end} (< gio dang + 2 h)")
        # Sol soi cuoi P1 (11/10): han tren trang phai TRUNG han da noi/hien trong video (kiem_lai.endTime).
        # Han doi (keo dai hay rut ngan) -> video noi sai han -> bo khung, dung lai.
        han_video = m.get("endTime")
        if not han_video or not str(han_video).isdigit():
            van_de.append(f"{ten}: manifest thieu endTime - khong so duoc han da noi trong video")
        elif end and abs(int(end) - int(han_video)) > LECH_HAN_MS:
            van_de.append(f"{ten}: han doi {han_video} -> {end} (video noi han cu)")
        goc = m.get("gia_cuc_bo")
        moi = khoi["gia_cuc_bo"]
        if not isinstance(goc, (int, float)) or goc <= 0:
            van_de.append(f"{ten}: manifest thieu gia_cuc_bo hop le - khong so gia duoc")
        elif abs(moi - goc) / goc > DUNG_SAI_GIA:
            van_de.append(f"{ten}: gia doi {goc} -> {moi} (> 2%)")
    return van_de, canh_bao
