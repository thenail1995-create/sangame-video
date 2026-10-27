"""Dieu phoi bo dang. CLI:
  python -m dang.chay --pha kiem|chuan-bi|cong-khai|kiem-gio|gia-han --dang tin-nhanh|top5|keo-thom-2|keo-thom|keo-thom-3|flagship --ngay YYYY-MM-DD --che-do thu|that
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

from . import chung, fb, gia, ig, manifest, ntfy, site, threads, tiktok, x, yt, zernio
from .chung import LoiDang
from .so import Cong, LoiCong

GIO = {"tin-nhanh": "07:30", "top5": "12:00", "keo-thom-2": "15:00", "keo-thom": "20:00", "keo-thom-3": "22:00", "flagship": "15:30"}
KENH = ("fb", "ig", "youtube", "tiktok", "x")   # x = Buffer, khong co token/danh tinh sg_token (khong nam trong MOD/KHOA_DICH)
# 12/10/2026 (Hao chot): Threads THOI dang lai video; Threads chi con bai chu rieng (dang/threads_chu.py) + gia han token (pha_gia_han). MOD/KHOA_DICH/TEN van giu threads.
MOD = {"fb": fb, "ig": ig, "threads": threads, "youtube": yt, "tiktok": tiktok}
KHOA_DICH = {"fb": "page_id", "ig": "ig_user_id", "threads": "threads_user_id", "youtube": "channel_id", "tiktok": "open_id"}
TEN = {"fb": "Facebook", "ig": "Instagram", "threads": "Threads", "youtube": "YouTube", "tiktok": "TikTok", "x": "X"}
DICH_MAC_DINH = pathlib.Path(__file__).resolve().parent.parent / "dich.json"
TRE_KIEM_GIO = dt.timedelta(minutes=15)


def kenh_flagship(ngay, ngay_1=None):
    """28/10/2026 (cong 10): khuon flagship 3 ngay dau chi 1 nen tang (tiktok); tu ngay thu 4 them youtube.
    ngay_1 = bien repo SG_FLAGSHIP_NGAY_1 (YYYY-MM-DD). Rong/sai dinh dang -> luon 'chi tiktok' (an toan)."""
    if ngay_1 is None:
        ngay_1 = os.environ.get("SG_FLAGSHIP_NGAY_1")
    ngay_1 = (ngay_1 or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", ngay_1):
        return ("tiktok",)
    try:
        n1 = dt.date.fromisoformat(ngay_1)
        n = dt.date.fromisoformat(ngay)
    except (ValueError, TypeError):
        return ("tiktok",)
    return ("tiktok",) if n < n1 + dt.timedelta(days=3) else ("tiktok", "youtube")


def kenh_bat(ds=KENH, dang=None, ngay=None):
    """24/10/2026 (Hao: "dung lai i chang video thang"): bien repo SG_KENH_BAT (vd "youtube") gioi han kenh may dang.
    Rong = moi kenh nhu cu.
    27/10/2026 (SG-X-A): X thoi dang "video may + link" -> luon bo "x" khoi luong video, ke ca khi bien rong; X chi con bai goc
    (dang/x_goc.py).
    28/10/2026: dang='flagship' -> giao them voi kenh_flagship(ngay) (3 ngay dau chi tiktok). Khuon khac khong doi."""
    bat = {k.strip() for k in (os.environ.get("SG_KENH_BAT") or "").split(",") if k.strip()}
    gioi_han = set(kenh_flagship(ngay)) if dang == "flagship" else None
    return [k for k in ds if k != "x" and (not bat or k in bat) and (gioi_han is None or k in gioi_han)]


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


def _doi(cong, nc, kenh, neu, **kw):
    """Chuyen trang thai so-va-dat. Tra so dong (0 = luot khac da doi truoc)."""
    return cong.cap_nhat_dang(**_khoa(nc, kenh), neu_trang_thai=neu, **kw)


def bo_khung(cong, ngay, dang, che_do, gio, ly_do, sha=None):
    """Ghi 'bo' + ly do cho ca 5 kenh roi ntfy. Dong moi -> bo; dong da chuan_bi_xong -> bo (so-va-dat); dong da dang/dang_dang
    KHONG dung (neu_trang_thai khong khop)."""
    ly = chung.che(ly_do)[:500]
    for k in KENH:
        if k == "x" and che_do != "that":
            continue   # X chi co o che do that
        try:
            if cong.giu_dang(ngay, dang, k, che_do, chung.iso(gio), sha):
                cong.cap_nhat_dang(ngay, dang, k, che_do, neu_trang_thai="dang_dang", trang_thai="bo", loi=ly)
            else:
                cong.cap_nhat_dang(ngay, dang, k, che_do, neu_trang_thai="chuan_bi_xong", trang_thai="bo", loi=ly)
        except LoiCong as e:
            chung.log_loi(f"bo_khung {k}: {e}")
    ntfy.loi(f"BO KHUNG {dang} {ngay}", ly_do)


def _ghi_loi(cong, nc, kenh, e, tu="dang_dang"):
    tt = "khong_ro" if getattr(e, "khong_ro", False) else "that_bai"
    try:
        cong.cap_nhat_dang(**_khoa(nc, kenh), neu_trang_thai=tu, trang_thai=tt, loi=chung.che(str(e))[:500])
    except LoiCong as e2:
        chung.log_loi(f"khong ghi duoc loi {kenh}: {e2}")
    return tt


def nap_va_kiem(a, cong, thu_muc):
    """Tai Release (du 3 ban), kiem manifest + sha256 moi tai san, kiem lai gia/han. Sai -> bo_khung, tra None.
    Tra (man, nc)."""
    gio = gio_dang_mac_dinh(a.ngay, a.dang)
    try:
        man = manifest.tai_release(a.ngay, a.dang, thu_muc, manifest.BAN, che_do=a.che_do)
        manifest.kiem(man, thu_muc, a.ngay, a.dang, a.che_do, manifest.BAN)
    except manifest.LoiManifest as e:
        bo_khung(cong, a.ngay, a.dang, a.che_do, gio, f"manifest/Release khong hop le: {e}")
        return None
    sha = chung.sha256_tep(pathlib.Path(thu_muc) / "manifest.json")
    gio = manifest.gio_dang(man)
    nc = chung.NguCanh(a.ngay, a.dang, a.che_do, gio, man, thu_muc, cong)
    nc.manifest_sha = sha
    return man, nc


def kiem_gia(a, cong, nc):
    muc = nc.man.get("kiem_lai")
    if a.dang == "tin-nhanh" and muc == []:
        # Sol soi cuoi P2 (11/10): Tin nhanh gom 3 tin bai/PS Plus/sale KHONG co the gia -> kiem_lai rong hop le
        # (may dung da kiem moi the gia co dung 1 ban ghi). Chi Tin nhanh; Top 5/Keo thom rong van bo khung.
        chung.log("kiem_lai: Tin nhanh khong co the gia - khong can kiem lai gia/han")
        return True
    van_de, canh_bao = gia.kiem_lai(muc, nc.gio_dang)
    for c in canh_bao:
        chung.log(f"kiem_lai canh bao: {c}")
    if van_de:
        bo_khung(cong, a.ngay, a.dang, a.che_do, nc.gio_dang, "kiem lai gia/han truoc gio dang: " + "; ".join(van_de), nc.manifest_sha)
        return False
    return True


# ---------------------------------------------------------------- kiem noi dung (truoc khi deploy Pages)
def pha_kiem(a, cong, thu_muc):
    r = nap_va_kiem(a, cong, thu_muc)
    if not r or not kiem_gia(a, cong, r[1]):
        return 3
    chung.log("kiem: manifest + tai san + gia/han deu dat")
    return 0


# ---------------------------------------------------------------- chuan bi
def chuan_bi_kenh(kenh, nc, dich, cong):
    tk = tai_token(cong, kenh)
    kiem_danh_tinh(kenh, tk, nc, dich)
    if kenh in ("ig", "threads") and not nc.url_video:
        raise LoiDang(getattr(nc, "loi_url", "") or "URL cong khai chua san sang")
    if not cong.giu_dang(nc.ngay, nc.dang, kenh, nc.che_do, chung.iso(nc.gio_dang), nc.manifest_sha):
        chung.log(f"{kenh}: sg_dang da co dong cho khung nay - bo qua")
        return "da_co"
    da_luu = []

    def luu(**kw):
        da_luu.append(kw)
        try:
            cong.cap_nhat_dang(**_khoa(nc, kenh), **kw)
        except LoiCong as e:   # nen tang DA nhan, ghi so loi -> khong_ro (that_bai se cho tai lai -> trung)
            raise LoiDang(f"nen tang da nhan {kw} nhung ghi so loi: {e}", khong_ro=True) from None

    try:
        ket = MOD[kenh].chuan_bi(tk, nc, luu)
    except LoiDang as e:
        _ghi_loi(cong, nc, kenh, e)
        raise
    except Exception as e:  # loi bat ngo: neu nen tang da nhan gi do (da_luu) thi khong_ro, chua thi that_bai
        err = LoiDang(f"{type(e).__name__}: {chung.cat(e, 300)}", khong_ro=bool(da_luu))
        _ghi_loi(cong, nc, kenh, err)
        raise err from None
    ids = {k: v for k, v in ket.items() if k in ("id_tai", "id_container")}
    try:
        n = _doi(cong, nc, kenh, "dang_dang", trang_thai="chuan_bi_xong", **ids)
        if n != 1:
            raise LoiCong("trang thai da bi doi boi luot khac")
    except LoiCong as e:
        err = LoiDang(f"da chuan bi xong tren nen tang nhung ghi so loi: {e}", khong_ro=True)
        _ghi_loi(cong, nc, kenh, err)
        raise err from None
    if ket.get("canh_bao") or ket.get("bia") or "nhan_ai" in ket:
        chung.log(f"{kenh}: {ket.get('canh_bao') or ''} bia={ket.get('bia')}" + (f" nhan_ai={ket['nhan_ai']}" if "nhan_ai" in ket else ""))
    chung.log(f"{kenh}: chuan bi xong ({', '.join(f'{k}={v}' for k, v in ids.items())})")
    return "xong"


def pha_chuan_bi(a, cong, thu_muc, kenh_chon=None):
    r = nap_va_kiem(a, cong, thu_muc)
    if not r:
        return 3
    man, nc = r
    if not kiem_gia(a, cong, nc):
        return 3
    kenh_chon = [k for k in kenh_bat(kenh_chon or KENH, a.dang, a.ngay) if k not in ("tiktok", "x")]   # TikTok va X chi lam o pha cong khai
    if any(k in ("ig", "threads") for k in kenh_chon):
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
    for kenh in kenh_chon:
        try:
            chuan_bi_kenh(kenh, nc, dich, cong)
        except Exception as e:
            loi.append(kenh)
            chung.log_loi(f"{kenh}: CHUAN BI LOI: {e}")
            ntfy.loi(f"{TEN[kenh]} loi chuan bi {a.dang} {a.ngay}", f"{type(e).__name__}: {e}")
    return 1 if loi else 0


# ---------------------------------------------------------------- cong khai
SOM_TOI_DA = dt.timedelta(minutes=1)
TRE_TOI_DA = dt.timedelta(minutes=90)   # gia/han da kiem cho gio dang + 2 h; tre hon 90 phut = khung cu, bo


def _tiktok_hop_thu(kenh, nc, cong, tk):
    """Duong cu: upload vao hop thu TikTok (Hao tu bam dang). Da giu_dang truoc khi goi."""
    try:
        ket = tiktok.hop_thu(tk, nc)
    except LoiDang as e:
        _ghi_loi(cong, nc, kenh, e)
        raise
    if chung.CO_GIONG_AI:   # duong hop thu khong co co video_made_with_ai: nhac Hao bat tay, KHONG ghi la da gan nhan
        ntfy.loi(f"TikTok hộp thư: nhớ bật nhãn AI {nc.dang} {nc.ngay}",
                 "Video vào hộp thư TikTok chưa gắn nhãn nội dung do AI tạo. Bật nhãn AI khi bấm đăng từ hộp thư.", uu_tien=4)
    try:
        _doi(cong, nc, kenh, "dang_dang", trang_thai="da_dang", id_tai=ket["id_tai"], id_bai=ket["id_bai"],
             gio_cong_khai=chung.iso(chung.bay_gio()))
    except LoiCong as e:
        raise LoiDang(f"TikTok da vao hop thu (publish_id {ket['id_tai']}) nhung ghi so loi: {e}", khong_ro=True) from None
    return "da_dang", ket


def _tiktok_zernio(kenh, nc, dich, cong):
    """Dang cong khai qua Zernio. Giu quyen nguyen tu TRUOC moi goi mang. Thua 'chua tao bai' -> du phong hop thu;
    khong_ro -> ghi khong_ro va dung (khong du phong, khong dang lai)."""
    if not cong.giu_dang(nc.ngay, nc.dang, kenh, nc.che_do, chung.iso(nc.gio_dang), nc.manifest_sha):
        chung.log("tiktok: da co dong cho khung nay - khong gui lai")
        return "bo_qua", {}
    try:
        ket = zernio.cong_khai(nc)
    except LoiDang as e:
        if getattr(e, "khong_ro", False):
            _ghi_loi(cong, nc, kenh, e)
            raise
        chung.log_loi(f"tiktok: Zernio chua dang duoc, chuyen du phong hop thu: {e}")
        ntfy.loi(f"TikTok: Zernio loi {nc.dang} {nc.ngay} - dung hop thu", f"{e}", uu_tien=3)
        try:
            tk = tai_token(cong, kenh)
            kiem_danh_tinh(kenh, tk, nc, dich)
            tk = tai_token(cong, kenh)
        except LoiDang as e2:
            _ghi_loi(cong, nc, kenh, e2)
            raise
        return _tiktok_hop_thu(kenh, nc, cong, tk)
    except Exception as e:   # loi bat ngo sau khi co the da goi Zernio: khong chac
        err = LoiDang(f"{type(e).__name__}: {chung.cat(e, 300)}", khong_ro=True)
        _ghi_loi(cong, nc, kenh, err)
        raise err from None
    try:
        _doi(cong, nc, kenh, "dang_dang", trang_thai="da_dang", id_tai=ket["id_tai"], id_bai=ket["id_bai"],
             link=ket.get("link"), gio_cong_khai=chung.iso(chung.bay_gio()))
    except LoiCong as e:
        raise LoiDang(f"TikTok DA dang cong khai qua Zernio ({ket.get('link') or ket['id_bai']}) nhung ghi so loi: {e}", khong_ro=True) from None
    return "da_dang", ket


def _x_buffer(kenh, nc, cong):
    """Dang X qua Buffer. Giu quyen nguyen tu TRUOC moi goi mang; Buffer khong co idempotency nen loi nao sau do cung khong dang lai."""
    if not cong.giu_dang(nc.ngay, nc.dang, kenh, nc.che_do, chung.iso(nc.gio_dang), nc.manifest_sha):
        chung.log("x: da co dong cho khung nay - khong gui lai")
        return "bo_qua", {}
    try:
        ket = x.cong_khai(nc)
    except LoiDang as e:
        _ghi_loi(cong, nc, kenh, e)
        raise
    except Exception as e:   # loi bat ngo sau khi co the da goi Buffer: khong chac
        err = LoiDang(f"{type(e).__name__}: {chung.cat(e, 300)}", khong_ro=True)
        _ghi_loi(cong, nc, kenh, err)
        raise err from None
    try:
        _doi(cong, nc, kenh, "dang_dang", trang_thai="da_dang", id_bai=ket.get("id_bai"), link=ket.get("link"),
             gio_cong_khai=chung.iso(chung.bay_gio()))
    except LoiCong as e:
        raise LoiDang(f"X DA dang cong khai ({ket.get('link') or ket.get('id_bai')}) nhung ghi so loi: {e}", khong_ro=True) from None
    return "da_dang", ket


def cong_khai_kenh(kenh, nc, dich, cong, dong, cac_dong=()):
    """-> ('bo_qua'|'da_dang', ket). Nem LoiDang neu loi. Thu tu cong: gio -> manifest_sha -> dich.json -> giu quyen so-va-dat."""
    if nc.che_do == "that" and chung.bay_gio() < nc.gio_dang - SOM_TOI_DA:
        raise LoiDang(f"chua toi gio dang ({chung.iso(nc.gio_dang)}) - khong cong khai som")
    if nc.che_do == "that" and chung.bay_gio() > nc.gio_dang + TRE_TOI_DA:
        # Sol soi cuoi P1 (11/10): cong chi chan dang SOM -> ban cua ngay truoc (hoac dispatch tre) van cong khai duoc.
        raise LoiDang(f"qua gio dang ({chung.iso(nc.gio_dang)}) hon {int(TRE_TOI_DA.total_seconds() // 60)} phut - khong cong khai ban cu")
    if kenh == "x":
        # X (Buffer): khong co pha chuan bi, chi chay o che_do that; cung rang buoc manifest nhu TikTok
        for r in cac_dong:
            if r.get("manifest_sha") and r["manifest_sha"] != nc.manifest_sha:
                raise LoiDang("manifest.json khac voi luc chuan bi (sha khac) - khong gui X")
        if nc.che_do != "that":
            chung.log("x: che do thu - khong cong khai")
            return "bo_qua", {}
        if not x.co_khoa():
            raise LoiDang("X: thieu BUFFER_KHOA")
        return _x_buffer(kenh, nc, cong)
    if kenh == "tiktok":
        # TikTok khong co pha chuan bi: ap dung cung rang buoc manifest voi cac kenh da chuan bi
        for r in cac_dong:
            if r.get("manifest_sha") and r["manifest_sha"] != nc.manifest_sha:
                raise LoiDang("manifest.json khac voi luc chuan bi (sha khac) - khong gui TikTok")
        if zernio.co_khoa() and nc.che_do == "that":   # Zernio dang CONG KHAI that -> che do thu KHONG bao gio di duong nay (vao hop thu nhu cu)
            return _tiktok_zernio(kenh, nc, dich, cong)
        tk = tai_token(cong, kenh)
        kiem_danh_tinh(kenh, tk, nc, dich)
        tk = tai_token(cong, kenh)  # lam_moi trong danh_tinh co the da doi token
        if not cong.giu_dang(nc.ngay, nc.dang, kenh, nc.che_do, chung.iso(nc.gio_dang), nc.manifest_sha):
            chung.log("tiktok: da co dong cho khung nay - khong gui lai")
            return "bo_qua", {}
        return _tiktok_hop_thu(kenh, nc, cong, tk)
    if nc.che_do == "thu":
        chung.log(f"{kenh}: che do thu - khong cong khai")
        return "bo_qua", {}
    st = (dong or {}).get("trang_thai")
    if st == "da_dang":
        return "bo_qua", {}
    if st != "chuan_bi_xong":
        raise LoiDang(f"sg_dang {kenh} o trang thai '{st}', can 'chuan_bi_xong' (chua chuan bi hoac da bo/loi)")
    if (dong or {}).get("manifest_sha") != nc.manifest_sha:
        ly = "manifest.json hien tai khac voi luc chuan bi (hoac so thieu manifest_sha) - huy khung"
        _doi(cong, nc, kenh, "chuan_bi_xong", trang_thai="bo", loi=ly)
        raise LoiDang(ly)
    tk = tai_token(cong, kenh)
    kiem_danh_tinh(kenh, tk, nc, dich)
    # Giu quyen NGUYEN TU (cong v2): chi luot doi duoc chuan_bi_xong -> dang_dang (so_dong == 1) moi duoc publish
    if _doi(cong, nc, kenh, "chuan_bi_xong", trang_thai="dang_dang") != 1:
        chung.log(f"{kenh}: luot khac da giu quyen cong khai - bo qua")
        return "bo_qua", {}
    try:
        ket = MOD[kenh].cong_khai(tk, nc, dong)
    except LoiDang as e:
        _ghi_loi(cong, nc, kenh, e)
        raise
    except Exception as e:
        err = LoiDang(f"{type(e).__name__}: {chung.cat(e, 300)}", khong_ro=True)  # sau khi goi nen tang: khong chac
        _ghi_loi(cong, nc, kenh, err)
        raise err from None
    try:
        _doi(cong, nc, kenh, "dang_dang", trang_thai="da_dang", id_bai=ket.get("id_bai"), link=ket.get("link"),
             gio_cong_khai=chung.iso(chung.bay_gio()))
    except LoiCong as e:
        raise LoiDang(f"{kenh} DA cong khai ({ket.get('link') or ket.get('id_bai')}) nhung ghi so loi: {e}", khong_ro=True) from None
    return "da_dang", ket


def pha_cong_khai(a, cong, thu_muc):
    gio = gio_dang_mac_dinh(a.ngay, a.dang)
    try:
        man = manifest.tai_release(a.ngay, a.dang, thu_muc, manifest.BAN, che_do=a.che_do)
        manifest.kiem(man, thu_muc, a.ngay, a.dang, a.che_do, manifest.BAN)
    except manifest.LoiManifest as e:
        ntfy.loi(f"Khong dang duoc {a.dang} {a.ngay}", f"manifest/Release khong hop le (cac dong chuan_bi_xong se bi huy): {e}")
        for r in cong.doc_dang(a.ngay, a.ngay, a.che_do):
            if r.get("dang") == a.dang and r.get("trang_thai") == "chuan_bi_xong":
                cong.cap_nhat_dang(a.ngay, a.dang, r["kenh"], a.che_do, neu_trang_thai="chuan_bi_xong", trang_thai="bo",
                                   loi=chung.cat(f"Release khong hop le luc cong khai: {e}", 400))
        return 3
    nc = chung.NguCanh(a.ngay, a.dang, a.che_do, manifest.gio_dang(man), man, thu_muc, cong)
    nc.manifest_sha = chung.sha256_tep(pathlib.Path(thu_muc) / "manifest.json")
    dich = nap_dich(os.environ.get("DICH_JSON"))
    cac_dong = [r for r in cong.doc_dang(a.ngay, a.ngay, a.che_do) if r.get("dang") == a.dang]
    dong_theo_kenh = {r["kenh"]: r for r in cac_dong}
    tin, loi = [], []
    for kenh in kenh_bat(dang=a.dang, ngay=a.ngay):
        try:
            kq, ket = cong_khai_kenh(kenh, nc, dich, cong, dong_theo_kenh.get(kenh), cac_dong)
            if kq == "da_dang":
                if kenh == "tiktok":
                    if ket.get("kieu") == "zernio":
                        tin.append(f"TikTok: da dang cong khai {ket.get('link') or ket.get('id_bai')}")
                    else:
                        tin.append("TikTok: video da vao hop thu - bam thong bao TikTok de dang")
                else:
                    tin.append(f"{TEN[kenh]}: {ket.get('link') or ket.get('id_bai') or 'da dang'}")
                if "nhan_ai" in ket:
                    chung.log(f"{kenh}: nhan_ai={ket['nhan_ai']}")
                if ket.get("canh_bao"):
                    chung.log(f"{kenh}: {ket['canh_bao']}")
                    ntfy.loi(f"{TEN[kenh]}: canh bao sau khi dang {a.dang} {a.ngay}", ket["canh_bao"], uu_tien=3)
        except Exception as e:
            loi.append(kenh)
            chung.log_loi(f"{kenh}: CONG KHAI LOI: {e}")
            ghi = "KHONG RO - KHONG tu dang lai, kiem tay. " if getattr(e, "khong_ro", False) else ""
            ntfy.loi(f"{TEN[kenh]} loi {a.dang} {a.ngay}", f"{ghi}{type(e).__name__}: {e}")
    if tin:
        ntfy.tin(f"Da dang {a.dang} {a.ngay}" + (" (che do thu)" if a.che_do == "thu" else ""), "\n".join(tin))
    # 14/10 (Hao chot "1 + 2"): Groups API bi Meta go tu 22/04/2024 -> may KHONG dang thang vao nhom FB duoc.
    # Bai Trang FB len xong thi nhac Hao chia se tay vao nhom (bam thong bao -> mo bai -> Chia se -> Chia se len nhom).
    fb = cong.doc_dang(a.ngay, a.ngay, a.che_do) if a.che_do == "that" else []
    link_fb = next((r.get("link") for r in fb if r.get("dang") == a.dang and r.get("kenh") == "fb"
                    and r.get("trang_thai") == "da_dang" and r.get("link")), None)
    if link_fb and "fb" not in loi:
        ntfy.chia_se_nhom(a.dang, a.ngay, link_fb)
    return 1 if loi else 0


# ---------------------------------------------------------------- kiem gio
def _gio_dong(r, mac_dinh):
    """Moc gio cua tung dong = gio_du_kien da ghi so (manifest cho phep gio bat ky); khong co thi dung gio mac dinh cua dang."""
    try:
        t = dt.datetime.fromisoformat(str(r["gio_du_kien"]).replace("Z", "+00:00"))
        return t if t.tzinfo else mac_dinh
    except (KeyError, TypeError, ValueError):
        return mac_dinh


def bu_link_tiktok(cong, ngay, che_do):
    """13/10: Zernio tra link TikTok cham (luc dang xong platformPostUrl con rong) -> so ghi link rong.
    Moi lan kiem-gio hoi lai cac dong TikTok da_dang thieu link cua hom qua + hom nay. KHONG bao gio nem; tra so dong da bu."""
    khoa = os.environ.get("ZERNIO_KHOA", "").strip()
    if not khoa:
        return 0
    so = 0
    try:
        chung.dang_ky_bi_mat(khoa)
        d = dt.date.fromisoformat(ngay)
        dong = cong.doc_dang((d - dt.timedelta(days=1)).isoformat(), ngay, che_do)
        for r in dong:
            if r.get("kenh") != "tiktok" or r.get("trang_thai") != "da_dang" or r.get("link") or not r.get("id_bai"):
                continue
            link = zernio.lay_link(khoa, r["id_bai"])
            if link and cong.cap_nhat_dang(r["ngay"], r["dang"], "tiktok", che_do, neu_trang_thai="da_dang", link=link):
                so += 1
                chung.log(f"kiem-gio: bu link TikTok {r['ngay']} {r['dang']}: {link}")
    except Exception as e:
        chung.log_loi(f"kiem-gio: bu link TikTok loi ({type(e).__name__}) - bo qua")
    return so


def pha_kiem_gio(a, cong):
    bu_link_tiktok(cong, a.ngay, a.che_do)
    mac_dinh = gio_dang_mac_dinh(a.ngay, a.dang)
    bay = chung.bay_gio()
    dong = {r["kenh"]: r for r in cong.doc_dang(a.ngay, a.ngay, a.che_do) if r.get("dang") == a.dang}
    van, chua_toi = [], 0
    xet = [k for k in kenh_bat(dang=a.dang, ngay=a.ngay) if k != "x" or a.che_do == "that"]   # X chi co o che do that
    for kenh in xet:
        r = dong.get(kenh)
        if bay < _gio_dong(r or {}, mac_dinh) + TRE_KIEM_GIO:
            chua_toi += 1
            continue
        if not r:
            van.append(f"{TEN[kenh]}: khong co dong so (chua chay hoac dung o buoc danh tinh/token)")
            continue
        tt = r.get("trang_thai")
        if tt == "bo":
            continue  # da bao luc bo khung
        xong = tt == "da_dang" or (a.che_do == "thu" and kenh != "tiktok" and tt == "chuan_bi_xong")
        if not xong:
            van.append(f"{TEN[kenh]}: trang thai '{tt}' - {r.get('loi') or 'khong co ly do ghi so'}")
    if chua_toi == len(xet):
        chung.log("kiem-gio: chua toi han (gio dang + 15 phut)")
        return 0
    if van:
        ntfy.loi(f"Qua gio chua dang du: {a.dang} {a.ngay}", "\n".join(van))
        return 1
    chung.log("kiem-gio: kenh den han deu on")
    return 0


# ---------------------------------------------------------------- gia han
def pha_gia_han(a, cong):
    loi = []
    nc = types.SimpleNamespace(cong=cong)
    bay = chung.bay_gio()

    def an_toan(v):
        try:
            return tiktok._t(v) if v else None
        except Exception:
            return None

    def bao(kenh, e, het=None):
        """Khong bao gio nem: loi o day khong duoc chan cac kenh sau."""
        loi.append(kenh)
        try:
            het = an_toan(het)
            gap = het is not None and (het - bay) < dt.timedelta(days=10)
            chung.log_loi(f"gia-han {kenh}: {e}")
            ntfy.loi(("GAP: " if gap else "") + f"gia han token {TEN[kenh]} loi", f"{type(e).__name__}: {e}",
                     uu_tien=5 if gap else 4)
        except Exception as e2:
            chung.log_loi(f"gia-han {kenh}: bao loi cung loi ({type(e2).__name__})")

    # Threads: >= 24 h tuoi va con < 30 ngay
    t = None
    try:
        t = cong.doc_token("threads")
        if t and t.get("du_lieu"):
            tk = t["du_lieu"]
            chung.dang_ky_tu_du_lieu(tk)
            tuoi = bay - dt.datetime.fromtimestamp(int(tk.get("cap_luc") or 0), dt.timezone.utc)
            het = tiktok._t(t["het_han"]) if t.get("het_han") else None  # sai dinh dang -> loi, bao() khong nem
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
        bao("threads", e, t.get("het_han") if isinstance(t, dict) else None)
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
        bao("tiktok", e, ((t or {}).get("du_lieu") or {}).get("refresh_het_han") if isinstance(t, dict) else None)
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
    ap.add_argument("--pha", required=True, choices=["kiem", "chuan-bi", "cong-khai", "kiem-gio", "gia-han"])
    ap.add_argument("--dang", choices=list(GIO))
    ap.add_argument("--ngay")
    ap.add_argument("--che-do", dest="che_do", choices=["thu", "that"])
    ap.add_argument("--kenh", help="chi pha chuan-bi: danh sach kenh, vd fb,youtube (mac dinh tat ca tru tiktok)")
    a = ap.parse_args(argv)
    kenh_chon = [k for k in (a.kenh or "").split(",") if k] or None
    if kenh_chon and not set(kenh_chon) <= set(KENH):
        ap.error("--kenh sai")
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
        if a.pha == "kiem":
            return pha_kiem(a, cong, thu_muc)
        if a.pha == "chuan-bi":
            return pha_chuan_bi(a, cong, thu_muc, kenh_chon)
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
