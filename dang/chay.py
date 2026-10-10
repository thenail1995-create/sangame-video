"""Dieu phoi bo dang. CLI:
  python -m dang.chay --pha chuan-bi|cong-khai|kiem-gio|gia-han --dang tin-nhanh|top5|keo-thom --ngay YYYY-MM-DD --che-do thu|that
Ma thoat: 0 xong · 1 co kenh loi / kiem that bai · 3 bo khung (manifest sai hoac gia/han lech)."""
import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
import tempfile
import types

from . import chung, fb, gia, ig, manifest, ntfy, site, threads, tiktok, yt
from .chung import LoiDang
from .so import Cong, LoiCong

GIO = {"tin-nhanh": "07:30", "top5": "12:00", "keo-thom": "20:00"}
KENH = ("fb", "ig", "threads", "youtube", "tiktok")
MOD = {"fb": fb, "ig": ig, "threads": threads, "youtube": yt, "tiktok": tiktok}
KHOA_DICH = {"fb": "page_id", "ig": "ig_user_id", "threads": "threads_user_id", "youtube": "channel_id", "tiktok": "open_id"}
TEN = {"fb": "Facebook", "ig": "Instagram", "threads": "Threads", "youtube": "YouTube", "tiktok": "TikTok"}
DICH_MAC_DINH = pathlib.Path(__file__).resolve().parent.parent / "dich.json"
TRE_KIEM_GIO = dt.timedelta(minutes=15)


def gio_dang_mac_dinh(ngay, dang):
    h, m = map(int, GIO[dang].split(":"))
    d = dt.date.fromisoformat(ngay)
    return dt.datetime(d.year, d.month, d.day, h, m, tzinfo=chung.VN)


def nap_dich(duong=None):
    return json.loads(pathlib.Path(duong or DICH_MAC_DINH).read_text("utf-8"))


def tai_token(cong, kenh):
    t = cong.doc_token(kenh)
    if not t or not t.get("du_lieu"):
        raise LoiDang(f"chua nap token {kenh} (sg_token)")
    chung.dang_ky_tu_du_lieu(t["du_lieu"])
    return t["du_lieu"]


def kiem_danh_tinh(kenh, tk, nc, dich):
    """Sol #6: id tai khoan doc tu token phai khop dich.json. dich null -> DUNG kenh."""
    mong = (dich.get(kenh) or {}).get(KHOA_DICH[kenh])
    if not mong:
        raise LoiDang(f"dich.json chua dien {KHOA_DICH[kenh]} cua {kenh} - dung kenh nay")
    thuc = MOD[kenh].danh_tinh(tk, nc)
    if str(thuc) != str(mong):
        raise LoiDang(f"danh tinh {kenh} lech dich.json (token tro toi tai khoan khac) - dung kenh nay")


def _khoa(nc, kenh):
    return dict(ngay=nc.ngay, dang=nc.dang, kenh=kenh, che_do=nc.che_do)


def bo_khung(cong, ngay, dang, che_do, gio, ly_do):
    """Ghi 'bo' + ly do cho ca 5 kenh (chi dong moi/that_bai), roi ntfy."""
    for k in KENH:
        try:
            if cong.giu_dang(ngay, dang, k, che_do, chung.iso(gio)):
                cong.cap_nhat_dang(ngay, dang, k, che_do, trang_thai="bo", loi=chung.che(ly_do)[:500])
        except LoiCong as e:
            chung.log_loi(f"bo_khung {k}: {e}")
    ntfy.loi(f"BO KHUNG {dang} {ngay}", ly_do)


def _ghi_loi(cong, nc, kenh, e):
    tt = "khong_ro" if getattr(e, "khong_ro", False) else "that_bai"
    try:
        cong.cap_nhat_dang(**_khoa(nc, kenh), trang_thai=tt, loi=chung.che(str(e))[:500])
    except LoiCong as e2:
        chung.log_loi(f"khong ghi duoc loi {kenh}: {e2}")
    return tt


# ---------------------------------------------------------------- chuan bi
def chuan_bi_kenh(kenh, nc, dich, cong):
    tk = tai_token(cong, kenh)
    kiem_danh_tinh(kenh, tk, nc, dich)
    if kenh in ("ig", "threads") and not nc.url_video:
        raise LoiDang(getattr(nc, "loi_url", "") or "URL cong khai chua san sang")
    if not cong.giu_dang(nc.ngay, nc.dang, kenh, nc.che_do, chung.iso(nc.gio_dang), nc.man.get("sha_code")):
        chung.log(f"{kenh}: sg_dang da co dong cho khung nay - bo qua")
        return "da_co"
    luu = lambda **kw: cong.cap_nhat_dang(**_khoa(nc, kenh), **kw)  # noqa: E731
    try:
        ket = MOD[kenh].chuan_bi(tk, nc, luu)
    except LoiDang as e:
        _ghi_loi(cong, nc, kenh, e)
        raise
    except Exception as e:  # loi bat ngo trong pha chuan bi: chua cong khai gi -> that_bai
        err = LoiDang(f"{type(e).__name__}: {e}")
        _ghi_loi(cong, nc, kenh, err)
        raise err from None
    ids = {k: v for k, v in ket.items() if k in ("id_tai", "id_container")}
    cong.cap_nhat_dang(**_khoa(nc, kenh), trang_thai="chuan_bi_xong", **ids)
    if ket.get("canh_bao") or ket.get("bia"):
        chung.log(f"{kenh}: {ket.get('canh_bao') or ''} bia={ket.get('bia')}")
    chung.log(f"{kenh}: chuan bi xong ({', '.join(f'{k}={v}' for k, v in ids.items())})")
    return "xong"


def pha_chuan_bi(a, cong, thu_muc):
    gio = gio_dang_mac_dinh(a.ngay, a.dang)
    try:
        man = manifest.tai_release(a.ngay, a.dang, thu_muc, ("reels", "shorts"))
        manifest.kiem(man, thu_muc, a.ngay, a.dang, a.che_do, ("reels", "shorts"))
    except manifest.LoiManifest as e:
        bo_khung(cong, a.ngay, a.dang, a.che_do, gio, f"manifest/Release khong hop le: {e}")
        return 3
    gio = manifest.gio_dang(man)
    van_de, canh_bao = gia.kiem_lai(man.get("kiem_lai"), gio)
    for c in canh_bao:
        chung.log(f"kiem_lai canh bao: {c}")
    if van_de:
        bo_khung(cong, a.ngay, a.dang, a.che_do, gio, "kiem lai gia/han truoc gio dang: " + "; ".join(van_de))
        return 3
    nc = chung.NguCanh(a.ngay, a.dang, a.che_do, gio, man, thu_muc, cong)
    goc = os.environ.get("PAGES_URL") or "https://{}.github.io/{}".format(*manifest.REPO.split("/"))
    u_video, u_bia = site.url_cong_khai(goc, a.ngay, a.dang, man)
    try:
        site.kiem_url(u_video, "video/mp4")
        site.kiem_url(u_bia, "image/jpeg")
        nc.url_video, nc.url_bia = u_video, u_bia
    except LoiDang as e:
        nc.loi_url = str(e)
        chung.log_loi(f"URL cong khai khong dat - IG/Threads se dung: {e}")
    dich = nap_dich(os.environ.get("DICH_JSON"))
    loi = []
    for kenh in KENH:
        if kenh == "tiktok":
            continue  # TikTok chi lam o pha cong khai
        try:
            chuan_bi_kenh(kenh, nc, dich, cong)
        except Exception as e:
            loi.append(kenh)
            chung.log_loi(f"{kenh}: CHUAN BI LOI: {e}")
            ntfy.loi(f"{TEN[kenh]} loi chuan bi {a.dang} {a.ngay}", f"{type(e).__name__}: {e}")
    return 1 if loi else 0


# ---------------------------------------------------------------- cong khai
def cong_khai_kenh(kenh, nc, dich, cong, dong):
    """-> ('bo_qua'|'da_dang', ket). Nem LoiDang neu loi."""
    if kenh == "tiktok":
        tk = tai_token(cong, kenh)
        kiem_danh_tinh(kenh, tk, nc, dich)
        tk = tai_token(cong, kenh)  # lam_moi trong danh_tinh co the da doi token
        if not cong.giu_dang(nc.ngay, nc.dang, kenh, nc.che_do, chung.iso(nc.gio_dang), nc.man.get("sha_code")):
            chung.log("tiktok: da co dong cho khung nay - khong gui lai")
            return "bo_qua", {}
        try:
            ket = tiktok.hop_thu(tk, nc)
        except LoiDang as e:
            _ghi_loi(cong, nc, kenh, e)
            raise
        cong.cap_nhat_dang(**_khoa(nc, kenh), trang_thai="da_dang", id_tai=ket["id_tai"], id_bai=ket["id_bai"],
                           gio_cong_khai=chung.iso(chung.bay_gio()))
        return "da_dang", ket
    if nc.che_do == "thu":
        chung.log(f"{kenh}: che do thu - khong cong khai")
        return "bo_qua", {}
    st = (dong or {}).get("trang_thai")
    if st == "da_dang":
        return "bo_qua", {}
    if st != "chuan_bi_xong":
        raise LoiDang(f"sg_dang {kenh} o trang thai '{st}', can 'chuan_bi_xong' (chua chuan bi hoac da bo/loi)")
    tk = tai_token(cong, kenh)
    kiem_danh_tinh(kenh, tk, nc, dich)
    # Giu cho: sg-cong chua co cap nhat co dieu kien, nen tranh dang lan 2 bang concurrency cua workflow + doi trang thai nay.
    cong.cap_nhat_dang(**_khoa(nc, kenh), trang_thai="dang_dang")
    try:
        ket = MOD[kenh].cong_khai(tk, nc, dong)
    except LoiDang as e:
        _ghi_loi(cong, nc, kenh, e)
        raise
    except Exception as e:
        err = LoiDang(f"{type(e).__name__}: {e}", khong_ro=True)  # sau khi goi nen tang: khong chac
        _ghi_loi(cong, nc, kenh, err)
        raise err from None
    cong.cap_nhat_dang(**_khoa(nc, kenh), trang_thai="da_dang", id_bai=ket.get("id_bai"), link=ket.get("link"),
                       gio_cong_khai=chung.iso(chung.bay_gio()))
    return "da_dang", ket


def pha_cong_khai(a, cong, thu_muc):
    try:
        man = manifest.tai_release(a.ngay, a.dang, thu_muc, ("tiktok",))
        manifest.kiem(man, thu_muc, a.ngay, a.dang, a.che_do, ("tiktok",))
    except manifest.LoiManifest as e:
        ntfy.loi(f"Khong dang duoc {a.dang} {a.ngay}", f"manifest/Release khong hop le: {e}")
        return 3
    nc = chung.NguCanh(a.ngay, a.dang, a.che_do, manifest.gio_dang(man), man, thu_muc, cong)
    dich = nap_dich(os.environ.get("DICH_JSON"))
    dong_theo_kenh = {r["kenh"]: r for r in cong.doc_dang(a.ngay, a.ngay, a.che_do) if r.get("dang") == a.dang}
    tin, loi = [], []
    for kenh in KENH:
        try:
            kq, ket = cong_khai_kenh(kenh, nc, dich, cong, dong_theo_kenh.get(kenh))
            if kq == "da_dang":
                if kenh == "tiktok":
                    tin.append("TikTok: video da vao hop thu - bam thong bao TikTok de dang")
                else:
                    tin.append(f"{TEN[kenh]}: {ket.get('link') or ket.get('id_bai') or 'da dang'}")
                if ket.get("canh_bao"):
                    chung.log(f"{kenh}: {ket['canh_bao']}")
        except Exception as e:
            loi.append(kenh)
            chung.log_loi(f"{kenh}: CONG KHAI LOI: {e}")
            ghi = "KHONG RO - KHONG tu dang lai, kiem tay. " if getattr(e, "khong_ro", False) else ""
            ntfy.loi(f"{TEN[kenh]} loi {a.dang} {a.ngay}", f"{ghi}{type(e).__name__}: {e}")
    if tin:
        ntfy.tin(f"Da dang {a.dang} {a.ngay}" + (" (che do thu)" if a.che_do == "thu" else ""), "\n".join(tin))
    return 1 if loi else 0


# ---------------------------------------------------------------- kiem gio
def pha_kiem_gio(a, cong):
    gio = gio_dang_mac_dinh(a.ngay, a.dang)
    if chung.bay_gio() < gio + TRE_KIEM_GIO:
        chung.log("kiem-gio: chua toi han (gio dang + 15 phut)")
        return 0
    dong = {r["kenh"]: r for r in cong.doc_dang(a.ngay, a.ngay, a.che_do) if r.get("dang") == a.dang}
    van = []
    for kenh in KENH:
        r = dong.get(kenh)
        if not r:
            van.append(f"{TEN[kenh]}: khong co dong so (chua chay hoac dung o buoc danh tinh/token)")
            continue
        tt = r.get("trang_thai")
        if tt == "bo":
            continue  # da bao luc bo khung
        xong = tt == "da_dang" or (a.che_do == "thu" and kenh != "tiktok" and tt == "chuan_bi_xong")
        if not xong:
            van.append(f"{TEN[kenh]}: trang thai '{tt}' - {r.get('loi') or 'khong co ly do ghi so'}")
    if van:
        ntfy.loi(f"Qua gio chua dang du: {a.dang} {a.ngay}", "\n".join(van))
        return 1
    chung.log("kiem-gio: du 5 kenh")
    return 0


# ---------------------------------------------------------------- gia han
def pha_gia_han(a, cong):
    loi = []
    nc = types.SimpleNamespace(cong=cong)
    bay = chung.bay_gio()

    def bao(kenh, e, het=None):
        loi.append(kenh)
        gap = het is not None and (het - bay) < dt.timedelta(days=10)
        chung.log_loi(f"gia-han {kenh}: {e}")
        ntfy.loi(("GAP: " if gap else "") + f"gia han token {TEN[kenh]} loi", f"{type(e).__name__}: {e}", uu_tien=5 if gap else 4)

    # Threads: >= 24 h tuoi va con < 30 ngay
    t = None
    try:
        t = cong.doc_token("threads")
        if t and t.get("du_lieu"):
            tk = t["du_lieu"]
            chung.dang_ky_tu_du_lieu(tk)
            tuoi = bay - dt.datetime.fromtimestamp(int(tk.get("cap_luc") or 0), dt.timezone.utc)
            het = tiktok._t(t["het_han"]) if t.get("het_han") else None
            if tuoi >= dt.timedelta(hours=24) and (het is None or het - bay < dt.timedelta(days=30)):
                moi, giay = threads.gia_han(tk, bay)
                chung.dang_ky_bi_mat(moi)
                het_moi = chung.iso(bay + dt.timedelta(seconds=giay)) if giay else None
                cong.ghi_token("threads", {**tk, "token": moi, "cap_luc": int(bay.timestamp())}, het_moi)
                chung.log("gia-han threads: da lam moi")
            else:
                chung.log("gia-han threads: chua can")
        else:
            chung.log("gia-han threads: chua nap token")
    except Exception as e:
        bao("threads", e, tiktok._t(t["het_han"]) if t and t.get("het_han") else None)
    # TikTok: refresh (luu refresh token moi ngay trong lam_moi)
    t = None
    try:
        t = cong.doc_token("tiktok")
        if t and t.get("du_lieu"):
            tk = t["du_lieu"]
            chung.dang_ky_tu_du_lieu(tk)
            tiktok.gia_han(tk, nc)
            chung.log("gia-han tiktok: da lam moi")
        else:
            chung.log("gia-han tiktok: chua nap token")
    except Exception as e:
        bao("tiktok", e, tiktok._t(t["du_lieu"]["refresh_het_han"]) if t and (t.get("du_lieu") or {}).get("refresh_het_han") else None)
    # YouTube: thu doi refresh token lay access token
    try:
        t = cong.doc_token("youtube")
        if t and t.get("du_lieu"):
            tk = t["du_lieu"]
            chung.dang_ky_tu_du_lieu(tk)
            yt._cache.pop(tk.get("refresh_token"), None)
            _, moi_rf = yt.lam_moi_access(tk)
            if moi_rf and moi_rf != tk.get("refresh_token"):
                chung.dang_ky_bi_mat(moi_rf)
                cong.ghi_token("youtube", {**tk, "refresh_token": moi_rf}, t.get("het_han"))
            chung.log("gia-han youtube: refresh token con dung duoc")
        else:
            chung.log("gia-han youtube: chua nap token")
    except Exception as e:
        bao("youtube", e)
    return 1 if loi else 0


# ---------------------------------------------------------------- CLI
def main(argv=None, cong=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pha", required=True, choices=["chuan-bi", "cong-khai", "kiem-gio", "gia-han"])
    ap.add_argument("--dang", choices=list(GIO))
    ap.add_argument("--ngay")
    ap.add_argument("--che-do", dest="che_do", choices=["thu", "that"])
    a = ap.parse_args(argv)
    if a.pha != "gia-han":
        if not (a.dang and a.ngay and a.che_do):
            ap.error("can --dang --ngay --che-do")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.ngay):
            ap.error("--ngay phai la YYYY-MM-DD")
    try:
        cong = cong or Cong()
    except LoiCong as e:
        chung.log_loi(str(e))
        return 1
    thu_muc = os.environ.get("DANG_THU_MUC") or tempfile.mkdtemp(prefix="sg-dang-")
    try:
        if a.pha == "chuan-bi":
            return pha_chuan_bi(a, cong, thu_muc)
        if a.pha == "cong-khai":
            return pha_cong_khai(a, cong, thu_muc)
        if a.pha == "kiem-gio":
            return pha_kiem_gio(a, cong)
        return pha_gia_han(a, cong)
    except Exception as e:
        chung.log_loi(f"LOI KHONG LUONG TRUOC: {type(e).__name__}: {e}")
        ntfy.loi(f"Bo dang loi ({a.pha})", f"{type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
