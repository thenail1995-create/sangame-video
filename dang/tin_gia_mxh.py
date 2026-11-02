"""May TIN GIA rieng cho Facebook Reel / Instagram Reel / Threads (anh + chu) cua Sang Game.
(khuon/tin-gia-mxh/KE-HOACH.md; BO SUNG OPUS 02/11 va SUA SAU SOI SOL S1-S18 DE len muc truoc; mau: dang/x_goc.py)

  python -m dang.tin_gia_mxh --kenh fb|ig|threads --ngay YYYY-MM-DD --che-do thu|that [--khong-api]
         [--du-lieu <thu muc kenh-game-du-lieu>] [--gia-the <gia-the.json>] [--ra <thu muc ra>]

Thu tu (giong x_goc, `khong_ro` sau moc co tac dung phu, KHONG BAO GIO dang lai khi khong_ro):
  doc sg_keo/sg_dang/lich su noi bat -> CHON (kiem trang PS Store moi gia hien ra) -> tai anh -> dung (khuon/tin-gia-mxh/dung.py) -> kiem.py
  -> chu + cong tin gia -> [--khong-api: dung o day] -> (that: qua som/qua gio?) -> dich.json dung tai khoan -> cong.giu_dang -> nhuong neu trung game (S7)
  -> chuan bi tren nen tang (KHONG cong khai) -> [thu: ghi that_bai "che do thu", chep RA_THU, thoat 0]
  -> ngu toi gio -> kiem lai gia (gia dung y) -> cong khai (han tuyet doi gio dang + 15 phut) -> da_dang.
Ma thoat: 0 xong | 1 loi dang / khong ro / ghi so loi | 2 thieu khoa/cau hinh | 3 KHONG dang.
Cong bat (pha THAT): bien repo SG_KENH_BAT phai co DUNG muc rieng khuon `<dang>:<kenh>` (fb-gia:fb, ig-gia:ig, threads-gia:threads).
Muc chung khong co ':' (vd "youtube") KHONG bat khuon nay. Pha thu khong can cong (chi giu sach nen tang, khong cong khai).
Trang thai sg_dang sau giu_dang (S15): loi chac chan truoc moi tac dung phu, hoac sau khi tao tai nguyen nhung CHUA goi cong khai -> that_bai
(cho chay lai, tai nguyen mo coi khong cong khai); loi khi/sau goi cong khai ma khong chung minh duoc chua dang -> khong_ro.
Runner bi huy giua chung -> dong ket o dang_dang: Opus doi soat tay (xem khuon/tin-gia-mxh/KE-HOACH.md muc "Đối soát dòng kẹt"), may KHONG tu doi.
"""
import argparse
import datetime as dt
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

from . import chay as dieu_phoi, chung, fb, http, ig, meta, ntfy, so, threads, tin_gia_chon as chon, tin_gia_chu as chu, x_goc, zernio
from .chung import LoiDang
from .gia import gia_trang, kiem_lai as kiem_lai_gia

REPO = pathlib.Path(__file__).resolve().parent.parent
KHUON = REPO / "khuon" / "tin-gia-mxh"
SCRIPT_DA_NOI_BAT = REPO / "cong-cu" / "da_noi_bat.py"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
NHAC = ("a", "c", "d", "e")             # nhac-<x>.mp3, chon theo ngay (BO SUNG 3)
QUA_GIO_PHUT = 2                        # that ma con < 2 phut toi gio dang (hoac qua) -> thoat 3, khong dang bu
SOM_TOI_DA_PHUT = 45                    # chuan bi xong ma con > 45 phut toi gio dang -> "chay qua som" (khong giu runner lau)
HAN_CONG_KHAI_PHUT = 15                 # han tuyet doi cong khai = gio dang + 15 phut (S16)
GIA_THE_TOI_DA_NGAY = 7
LAN_THU_CHON = 3                        # cong/chu truot thi loai game do, chon ung vien khac (toi da 3 lan)
NGAY_DOC_LICH_SU = 3
NGAY_DOC_BIEN_THE = 7
CHO_XAC_NHAN_FB = 18                    # x 10 s = ~3 phut (S17)
SO_LAN_TAI_TRANG = 2
ANH_RONG_TAI = 1280


class KhongDang(Exception):
    """Dung het, KHONG dang gi (ma thoat 3). ly_do da che bi mat."""


class MatDong(KhongDang):
    """Dong sg_dang KHONG CON la cua minh (trang thai khac chuan_bi_xong hoac id_bai khac): dung + ntfy, TUYET DOI khong doi trang thai dong do."""


# ---------------------------------------------------------------- cong bat rieng khuon (BO SUNG 10)
def kenh_bat_rieng(gia_tri, dang, kenh):
    """Bien repo SG_KENH_BAT -> True chi khi co DUNG muc rieng `<dang>:<kenh>` (tach phay, bo khoang trang). Muc chung khong ':' KHONG tinh.
    KHONG dung chay.doc_kenh_bat (ham do roi ve muc chung: SG_KENH_BAT="youtube" se bat khuon la)."""
    for muc in str(gia_tri or "").split(","):
        muc = muc.strip()
        if ":" not in muc:
            continue
        d, k = (p.strip() for p in muc.split(":", 1))
        if d == dang and k == kenh:
            return True
    return False


# ---------------------------------------------------------------- nap phu thuoc that
def gio_du_kien(ngay, kenh):
    h, m = (int(p) for p in chon.GIO[kenh].split(":"))
    return dt.datetime(ngay.year, ngay.month, ngay.day, h, m, tzinfo=chung.VN)


def nap_deal_diem(du_lieu):
    """deal_diem.py (+ nguon.py) trong repo rieng tu `kenh-game-du-lieu` (thu muc `du_lieu`)."""
    d = pathlib.Path(du_lieu)
    f = d / "deal_diem.py"
    if not f.exists():
        raise KhongDang(f"khong thay deal_diem.py trong {d} (can repo rieng tu kenh-game-du-lieu)")
    cu = list(sys.path)
    sys.path.insert(0, str(d))
    try:
        sys.modules.pop("deal_diem", None)
        sys.modules.pop("nguon", None)
        spec = importlib.util.spec_from_file_location("sangame_deal_diem", f)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    except Exception as e:   # noqa: BLE001
        raise KhongDang(f"khong nap duoc deal_diem.py: {type(e).__name__}: {e}") from None
    finally:
        sys.path[:] = cu


def nap_da_noi_bat():
    spec = importlib.util.spec_from_file_location("sangame_da_noi_bat", SCRIPT_DA_NOI_BAT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def doc_gia_the(duong, ngay):
    """gia-the.json phai doc duoc va khong cu hon 7 ngay (ngay/cap_nhat), co `vung`. Khong -> KhongDang."""
    try:
        d = json.loads(pathlib.Path(duong).read_text(encoding="utf-8"))
        n = dt.date.fromisoformat(str(d.get("ngay") or d.get("cap_nhat"))[:10])
    except (OSError, ValueError, TypeError, AttributeError):
        raise KhongDang(f"gia-the.json ({duong}) thieu/hong") from None
    if not isinstance(d.get("vung"), dict) or not d["vung"] or not 0 <= (ngay - n).days <= GIA_THE_TOI_DA_NGAY:
        raise KhongDang(f"gia-the.json cu/thieu vung (ngay {n}, can <= {GIA_THE_TOI_DA_NGAY} ngay so voi {ngay})")
    return d


def lay_trang_mang(link):
    """Tai trang san pham PS Store (theo chuyen huong). Loi/khong 200 -> None (fail-closed o xet_o)."""
    for lan in range(SO_LAN_TAI_TRANG):
        try:
            r = http.gui("GET", link, headers={"User-Agent": UA}, theo_chuyen_huong=True, timeout=40)
        except http.LoiMang:
            r = None
        if r is not None and r.status == 200 and r.body:
            return r.text
        if lan + 1 < SO_LAN_TAI_TRANG:
            chung.ngu(3)
    return None


def tai_anh_mang(thu_muc_tai_san):
    """-> ham (url, nhan) -> ten tep tuong doi thu muc tai san | None. Canh ngan >= 600 px, anh Sony chi nam trong thu muc tam cua runner."""
    goc = pathlib.Path(thu_muc_tai_san)

    def tai(url, nhan):
        u = url.split("?")[0] + f"?w={ANH_RONG_TAI}"
        r = http.gui("GET", u, headers={"User-Agent": UA}, theo_chuyen_huong=True, timeout=60)
        if r.status != 200 or not r.body or len(r.body) > 25 * 1024 * 1024:
            return None
        kich = chon.kich_anh(r.body)
        if not kich or min(kich) < chon.ANH_MIN:
            return None
        duoi = ".png" if r.body[:8] == b"\x89PNG\r\n\x1a\n" else ".webp" if r.body[:4] == b"RIFF" else ".gif" if r.body[:3] == b"GIF" else ".jpg"
        ten = nhan + duoi
        (goc / ten).write_bytes(r.body)
        return ten
    return tai


def chon_nhac(du_lieu, ngay):
    """nhac-<a|c|d|e>.mp3 theo ngay; thieu tep thi tep co san dau tien theo thu tu; khong co tep nao -> KhongDang."""
    d = pathlib.Path(du_lieu) / "video" / "tai-san" / "nhac"
    chinh = NHAC[ngay.toordinal() % len(NHAC)]
    for x in (chinh, *(c for c in NHAC if c != chinh)):
        if (d / f"nhac-{x}.mp3").is_file():
            return d / f"nhac-{x}.mp3"
    raise KhongDang(f"khong co tep nhac nao trong {d}")


def dung_that(kenh, dl_path, tai_san, am, nhac, ra):
    lenh = [sys.executable, str(KHUON / "dung.py"), "--kenh", kenh, "--du-lieu", str(dl_path), "--tai-san", str(tai_san), "--ra", str(ra)]
    if kenh != "threads":
        lenh += ["--am", str(am), "--nhac", str(nhac)]
    try:
        p = subprocess.run(lenh, capture_output=True, text=True, timeout=900, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise KhongDang(f"dung.py loi ({type(e).__name__})") from None
    if p.returncode != 0:
        raise KhongDang("dung.py loi: " + chung.cat((p.stderr or p.stdout or "?").strip()[-300:], 300))


def kiem_that(kenh, ra, dl_path):
    lenh = [sys.executable, str(KHUON / "kiem.py"), "--kenh", kenh, "--ra", str(ra), "--du-lieu", str(dl_path)]
    try:
        p = subprocess.run(lenh, capture_output=True, text=True, timeout=600, stdin=subprocess.DEVNULL)
        kq = json.loads(p.stdout)
    except (OSError, subprocess.TimeoutExpired, ValueError) as e:
        raise KhongDang(f"kiem.py loi ({type(e).__name__})") from None
    # P2-b: dat khi va chi khi ma thoat 0 VA JSON la dict VA dat is True; mau thuan (vd thoat 1 ma dat true) = khong dat
    if p.returncode != 0 or not isinstance(kq, dict) or kq.get("dat") is not True:
        sai = [f"{x.get('ten')}: {x.get('chi_tiet')}" for x in (kq.get("phep") or []) if isinstance(x, dict) and not x.get("dat")] if isinstance(kq, dict) else []
        raise KhongDang(f"kiem.py khong dat (ma thoat {p.returncode}, dat={kq.get('dat') if isinstance(kq, dict) else '?'}): " + "; ".join(sai)[:300])
    return kq


def kiem_han(han, buoc):
    """P2-a / S16: NGAY truoc request co tac dung phu (finish / media_publish / threads_publish, sau moi GET) - qua han tuyet doi -> LoiDang
    CHAC CHAN chua dang (khong_ro=False): khong POST."""
    if han is not None and chung.bay_gio() > han:
        raise LoiDang(f"qua han cong khai (gio dang + {HAN_CONG_KHAI_PHUT} phut) o buoc {buoc} - KHONG goi cong khai")


def kiem_goc_giam(muc, lay_trang):
    """P2-d: kiem_lai mang them gia_goc + giam + tien; cung lan GET so luon gia ban (dung y) + tien te; doc lai trang, doi -> van de (fail-closed: khong tai duoc / khong co khoi gia = van de).
    Khong sua dang/gia.kiem_lai (cac khuon cu)."""
    van_de = []
    for m in muc or []:
        ten = m.get("ten", "?")
        if not isinstance(m.get("gia_goc"), (int, float)) or not isinstance(m.get("giam"), int):
            van_de.append(f"{ten}: kiem_lai thieu gia_goc/giam")
            continue
        html = lay_trang(f"https://store.playstation.com/{m.get('loc')}/product/{m.get('pid')}")
        k = gia_trang.khoi_gia(html, m.get("pid")) if html else None
        if k is None or not k.get("gia_goc") or k["gia_goc"] <= k["gia_cuc_bo"]:
            van_de.append(f"{ten}: khong doc lai duoc gia goc tren trang")
            continue
        if k.get("tien_te") != m.get("tien"):
            van_de.append(f"{ten}: tien te doi {m.get('tien')} -> {k.get('tien_te')}")
        if not isinstance(m.get("gia_cuc_bo"), (int, float)) or round(k["gia_cuc_bo"], 2) != round(m["gia_cuc_bo"], 2):
            van_de.append(f"{ten}: gia ban doi {m.get('gia_cuc_bo')} -> {k['gia_cuc_bo']}")
        giam = int(round(100 * (1 - k["gia_cuc_bo"] / k["gia_goc"])))
        if round(k["gia_goc"], 2) != round(m["gia_goc"], 2):
            van_de.append(f"{ten}: gia goc doi {m['gia_goc']} -> {k['gia_goc']}")
        if giam != m["giam"]:
            van_de.append(f"{ten}: % giam doi {m['giam']} -> {giam}")
    return van_de


def kiem_url_cong_khai(url, loai):
    """URL Zernio phai tra 200/206 + content-type bat dau bang `loai` truoc khi dua cho Meta. Loi -> LoiDang (chua tao container)."""
    try:
        r = http.gui("GET", url, headers={"Range": "bytes=0-1023"}, timeout=60)
    except http.LoiMang as e:
        raise LoiDang(f"URL Zernio khong tai duoc ({e}) (chua tao container)") from None
    if r.status not in (200, 206) or not r.headers.get("content-type", "").lower().startswith(loai):
        raise LoiDang(f"URL Zernio khong dat (HTTP {r.status}, {chung.cat(r.headers.get('content-type'), 40)}) (chua tao container)")


# ---------------------------------------------------------------- nen tang that (S12: ID Graph luu o id_bai, KHONG dung fb/ig/threads.cong_khai cu)
class NenFB:
    ten = "fb"

    def __init__(self, tk, zernio_khoa=None):
        self.tk = tk

    def kiem_danh_tinh(self, dich):
        dieu_phoi.kiem_danh_tinh("fb", self.tk, None, dich)

    def chuan_bi(self, goi, che_do, luu):
        tk = self.tk
        page = fb.danh_tinh(tk)
        st = meta.goi(fb.G, "POST", f"/{page}/video_reels", token=tk["page_token"], tham_so={"upload_phase": "start"})
        video_id = str(st.get("video_id") or "")
        if not video_id:
            raise LoiDang("FB start khong tra video_id")
        luu(id_bai=video_id)
        fb._upload(tk, video_id, pathlib.Path(goi["video"]).read_bytes())
        meta.cho_trang_thai(lambda: fb._trang_thai(tk, video_id), {"xong"}, {"error"}, toi_da=40, ten="FB upload")
        bia = fb._nap_bia(goi["bia"])
        ghi_chu = "da upload"
        if che_do == "thu":
            f = fb.finish(tk, page, fb.tham_finish(video_id, goi["text"], "DRAFT", co_ai=False))
            if f.get("success") is not True:
                raise LoiDang("FB finish DRAFT khong thanh cong")
            ok, ly = fb._dat_bia(tk, video_id, bia)
            ghi_chu = "finish DRAFT + bia " + ("ok" if ok else f"loi: {ly}")
        return {"id_bai": video_id, "ghi_chu": ghi_chu}

    def cong_khai(self, goi, id_bai, han=None):
        tk = self.tk
        page = fb.danh_tinh(tk)
        bia = fb._nap_bia(goi["bia"])
        if fb._doc_status(tk, id_bai).get("video_status") in fb.LOI_VIDEO:
            raise LoiDang("FB upload da het han/hong - chua dang gi")
        kiem_han(han, "FB finish PUBLISHED")
        try:
            f = fb.finish(tk, page, fb.tham_finish(id_bai, goi["text"], "PUBLISHED", co_ai=False))
            ok = f.get("success") is True
        except LoiDang as e:
            if not e.khong_ro:
                raise
            try:
                ok = fb._da_cong_khai(tk, id_bai)
            except LoiDang:
                ok = False
            if not ok:
                raise
        if not ok:
            raise LoiDang("FB finish PUBLISHED khong tra success", khong_ro=True)
        xac = False
        for lan in range(CHO_XAC_NHAN_FB):       # S17: doc lai trang thai, chua xac nhan thi khong_ro
            try:
                if fb._da_cong_khai(tk, id_bai):
                    xac = True
                    break
            except LoiDang:
                pass
            chung.ngu(10)
        if not xac:
            raise LoiDang("FB da finish PUBLISHED nhung chua xac nhan published sau ~3 phut", khong_ro=True)
        ket = {"id_bai": id_bai, "link": f"https://www.facebook.com/reel/{id_bai}/"}
        ok_bia, ly = fb._dat_bia(tk, id_bai, bia)
        if not ok_bia:
            ket["canh_bao"] = f"bia FB khong dat duoc: {ly}"
        return ket


class NenIG:
    ten = "ig"

    def __init__(self, tk, zernio_khoa):
        self.tk, self.zk = tk, zernio_khoa

    def kiem_danh_tinh(self, dich):
        dieu_phoi.kiem_danh_tinh("ig", self.tk, None, dich)

    def chuan_bi(self, goi, che_do, luu):
        tk, ngay = self.tk, goi["ngay"]
        url_v = zernio.tai_tep(self.zk, goi["video"], f"sangame-ig-gia-{ngay}.mp4", "video/mp4")
        kiem_url_cong_khai(url_v, "video/")
        url_b = zernio.tai_tep(self.zk, goi["bia"], f"sangame-ig-gia-{ngay}.jpg", "image/jpeg")
        kiem_url_cong_khai(url_b, "image/")
        c = ig.tao_container(tk, ig.tham_container(url_v, url_b, goi["text"], co_ai=False))
        cid = str(c.get("id") or "")
        if not cid:
            raise LoiDang("IG khong tra container id")
        luu(id_bai=cid)
        meta.cho_trang_thai(lambda: ig._status(tk, cid), {"FINISHED"}, {"ERROR", "EXPIRED"}, toi_da=80, ten="IG container")
        return {"id_bai": cid, "ghi_chu": "container FINISHED (khong publish)"}

    def cong_khai(self, goi, id_bai, han=None):
        tk = self.tk
        if ig._status(tk, id_bai) != "FINISHED":
            raise LoiDang("IG container khong con o trang thai FINISHED")
        kiem_han(han, "IG media_publish")
        mid = None
        try:
            p = meta.goi(ig.G, "POST", f"/{tk['ig_user_id']}/media_publish", token=tk["page_token"], co_tac_dung=True, timeout=120,
                         tham_so={"creation_id": id_bai})
            mid = str(p.get("id") or "")
            if not mid:
                raise LoiDang("IG media_publish khong tra id", khong_ro=True)
        except LoiDang as e:
            if not e.khong_ro:
                raise
            try:
                da = ig._status(tk, id_bai) == "PUBLISHED"
            except LoiDang:
                da = False
            if not da:
                raise
            return {"id_bai": id_bai, "link": None, "canh_bao": "IG da PUBLISHED nhung khong lay duoc id bai"}
        link = None
        try:
            link = meta.goi(ig.G, "GET", f"/{mid}", token=tk["page_token"], tham_so={"fields": "permalink"}).get("permalink")
        except LoiDang:
            pass
        return {"id_bai": mid, "link": link}


class NenThreads:
    ten = "threads"

    def __init__(self, tk, zernio_khoa):
        self.tk, self.zk = tk, zernio_khoa

    def kiem_danh_tinh(self, dich):
        dieu_phoi.kiem_danh_tinh("threads", self.tk, None, dich)

    def chuan_bi(self, goi, che_do, luu):
        tk = self.tk
        url = zernio.tai_tep(self.zk, goi["anh"], f"sangame-threads-gia-{goi['ngay']}.png", "image/png")
        kiem_url_cong_khai(url, "image/")
        cid = threads.tao_container_chu(tk, goi["text"], anh=url, topic_tag=chu.TOPIC_TAG, alt_text=goi.get("alt"),
                                        luu=lambda **kw: luu(id_bai=kw["id_container"]))
        if che_do == "that":
            chung.ngu(30)   # tai lieu Threads: cho ~30 giay sau FINISHED truoc khi publish
        return {"id_bai": cid, "ghi_chu": "container FINISHED (khong publish)"}

    def cong_khai(self, goi, id_bai, han=None):
        tk = self.tk
        if threads._status(tk, id_bai) != "FINISHED":
            raise LoiDang("Threads container khong con o trang thai FINISHED")
        kiem_han(han, "Threads threads_publish")
        try:
            p = meta.goi(threads.TH, "POST", f"/{tk['threads_user_id']}/threads_publish", token=tk["token"], co_tac_dung=True, timeout=120,
                         tham_so={"creation_id": id_bai})
            mid = str(p.get("id") or "")
            if not mid:
                raise LoiDang("Threads threads_publish khong tra id", khong_ro=True)
        except LoiDang as e:
            if not e.khong_ro:
                raise
            try:
                da = threads._status(tk, id_bai) == "PUBLISHED"
            except LoiDang:
                da = False
            if not da:
                raise
            return {"id_bai": id_bai, "link": None, "canh_bao": "Threads da PUBLISHED nhung khong lay duoc id bai"}
        link = None
        try:
            link = meta.goi(threads.TH, "GET", f"/{mid}", token=tk["token"], tham_so={"fields": "permalink"}).get("permalink")
        except LoiDang:
            pass
        return {"id_bai": mid, "link": link}


NEN = {"fb": NenFB, "ig": NenIG, "threads": NenThreads}


class Phu:
    """Cac phu thuoc co mang/qua trinh con: test thay bang gia. Mac dinh = that."""

    def __init__(self, du_lieu=None, **thay):
        self.du_lieu = du_lieu
        self.lay_trang = lay_trang_mang
        self.tai_anh = tai_anh_mang                  # (thu muc tai san) -> ham (url, nhan)
        self.quy_vnd = None                          # None -> deal_diem.quy_vnd cua du_lieu
        self.nb = lambda ngay, dang: nap_da_noi_bat().da_noi_bat(ngay, dang, NGAY_DOC_LICH_SU)
        self.dung = dung_that
        self.kiem = kiem_that
        self.tai_token = dieu_phoi.tai_token
        self.nen = lambda kenh, tk, zk: NEN[kenh](tk, zk)
        self.ngu = chung.ngu
        self.kiem_lai = kiem_lai_gia
        self.kiem_them = lambda muc: kiem_goc_giam(muc, self.lay_trang)      # P2-d: gia goc + % giam
        self.nhac = chon_nhac
        self.dich = dieu_phoi.nap_dich
        for k, v in thay.items():
            if not hasattr(self, k):
                raise AttributeError(k)
            setattr(self, k, v)

    def lay_quy_vnd(self):
        if self.quy_vnd is None:
            self.quy_vnd = nap_deal_diem(self.du_lieu).quy_vnd
        return self.quy_vnd


# ---------------------------------------------------------------- so dang
def _bao(tieu_de, noi_dung):
    """ntfy loi; gui THANH CONG + co env DA_BAO_FILE -> tao file de buoc cuoi workflow khong bao lai (nhu x_goc)."""
    chung.log_loi(f"tin_gia_mxh: {tieu_de}: {noi_dung}")
    if ntfy.loi(tieu_de, noi_dung) is True and os.environ.get("DA_BAO_FILE"):
        try:
            open(os.environ["DA_BAO_FILE"], "w").close()
        except OSError:
            pass


def doi_that_bai(cong, khoa, loi, tu=("dang_dang", "chuan_bi_xong")):
    """that_bai co dieu kien: chi doi khi dong con o trang thai truoc cong khai (S15)."""
    for tt in tu:
        try:
            if cong.cap_nhat_dang(**khoa, neu_trang_thai=tt, trang_thai="that_bai", loi=chung.cat(loi, 300)):
                return True
        except Exception:   # noqa: BLE001
            pass
    return False


def doi_trang_thai(cong, khoa, tu, **truong):
    """Doi trang thai CO DIEU KIEN (neu_trang_thai): thu lan luot cac trang thai trong `tu`; -> True neu doi duoc 1 dong."""
    for tt in tu:
        try:
            if cong.cap_nhat_dang(**khoa, neu_trang_thai=tt, **truong) == 1:
                return True
        except Exception:   # noqa: BLE001
            pass
    return False


def dong_truoc_cong_khai(cong, ngay, dang, kenh, che_do, id_bai):
    """P1-a: NGAY truoc cong khai doc lai dong sg_dang cua minh: phai la chuan_bi_xong va id_bai dung tai nguyen minh tao. -> ly do sai hoac None."""
    rows = cong.doc_dang(ngay.isoformat(), ngay.isoformat(), che_do)
    toi = next((r for r in rows if r.get("ngay") == ngay.isoformat() and r.get("dang") == dang and r.get("kenh") == kenh), None)
    if toi is None:
        return "khong doc lai duoc dong sg_dang cua minh truoc khi cong khai"
    if toi.get("trang_thai") != "chuan_bi_xong" or str(toi.get("id_bai")) != str(id_bai):
        return f"dong sg_dang truoc cong khai la {toi.get('trang_thai')}/id_bai {toi.get('id_bai')} (can chuan_bi_xong/{id_bai}) - dung, khong ghi de"
    return None


def nhuong_neu_trung(cong, ngay, dang, kenh, che_do, ma_cua_toi):
    """S7 + P1-b: sau giu_dang + ghi id_tai, doc lai sg_dang +-3 ngay. Dong KHAC (fb-gia/ig-gia/threads-gia/x-goc, khac that_bai/bo, cung che_do) trung
    ma game: o trang thai khong_ro/da_dang/chuan_bi_xong -> LUON chan; o dang_dang -> so `luc` (som hon thang, bang nhau thi `dang` lon hon nhuong).
    Khong doc lai duoc dong cua minh = nhuong (fail-closed). -> ly do hoac None."""
    d = dt.timedelta(days=3)
    rows = cong.doc_dang((ngay - d).isoformat(), (ngay + d).isoformat(), che_do)
    toi = next((r for r in rows if r.get("ngay") == ngay.isoformat() and r.get("dang") == dang and r.get("kenh") == kenh), None)
    luc_toi = x_goc._tg((toi or {}).get("luc"))
    if toi is None or luc_toi is None:
        return "khong doc lai duoc dong sg_dang cua minh (thieu luc) - nhuong"
    ids_toi = set()
    for m in ma_cua_toi:
        ids_toi.add(m)
        ids_toi |= chon.title_ids(m)
    for r in rows:
        if r is toi or (r.get("ngay"), r.get("dang"), r.get("kenh")) == (toi.get("ngay"), toi.get("dang"), toi.get("kenh")):
            continue
        if r.get("dang") not in chon.DANG_LOC_TRUNG or r.get("trang_thai") in ("that_bai", "bo"):
            continue
        ids = set()
        for m in str(r.get("id_tai") or "").split(","):
            if m.strip():
                ids.add(m.strip())
                ids |= chon.title_ids(m)
        if not ids & ids_toi:
            continue
        if r.get("trang_thai") in ("khong_ro", "da_dang", "chuan_bi_xong"):      # P1-b: da/dang chuan bi/co the da dang -> LUON chan, bat ke `luc`
            return f"trung game voi {r.get('dang')} ({r.get('kenh')}) dang o trang thai {r.get('trang_thai')}"
        luc_r = x_goc._tg(r.get("luc"))          # chi dong dang_dang moi so `luc`: som hon thang; bang nhau -> `dang` lon hon (chu cai) nhuong
        if luc_r is None or (luc_r, str(r.get("dang"))) < (luc_toi, dang):
            return f"trung game voi {r.get('dang')} ({r.get('kenh')}) dang_dang som hon"
    return None


def ra_thu(ra):
    """Chep ket qua pha thu (video/anh, chu, chon.json, kiem.json...) vao RA_THU de workflow upload artifact. KHONG chep anh Sony (tai-san)."""
    dich = os.environ.get("RA_THU", "").strip()
    if not dich or not pathlib.Path(ra).is_dir():
        return None
    d = pathlib.Path(dich)
    d.mkdir(parents=True, exist_ok=True)
    for f in pathlib.Path(ra).iterdir():
        if f.is_file():
            shutil.copy2(f, d / f.name)
    return d


def viet_json(duong, du_lieu):
    pathlib.Path(duong).write_text(json.dumps(du_lieu, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


# ---------------------------------------------------------------- luong chinh
def lam(a, cong, phu, thu_muc):
    kenh, che_do = a.kenh, a.che_do
    ngay = dt.date.fromisoformat(a.ngay)
    dang = chon.DANG[kenh]
    due = gio_du_kien(ngay, kenh)
    ra, ts = pathlib.Path(a.ra) if a.ra else pathlib.Path(thu_muc) / "ra", pathlib.Path(thu_muc) / "tai-san"
    ra.mkdir(parents=True, exist_ok=True)
    ts.mkdir(parents=True, exist_ok=True)
    khoa = dict(ngay=ngay.isoformat(), dang=dang, kenh=kenh, che_do=che_do)

    # ---- 1. doc du lieu (chua tac dung phu)
    dong_gan = cong.doc_dang((ngay - dt.timedelta(days=NGAY_DOC_LICH_SU)).isoformat(), ngay.isoformat(), "that")
    dong_7 = cong.doc_dang((ngay - dt.timedelta(days=NGAY_DOC_BIEN_THE)).isoformat(), ngay.isoformat(), "that")
    nb = phu.nb(ngay, dang)
    if getattr(nb, "canh_bao", None):          # S8: khong doc duoc lich su noi bat = KhongDang (khac 'doc duoc, rong')
        raise KhongDang("khong doc duoc lich su game da noi bat (fail-closed): " + chung.cat(nb.canh_bao, 200))
    gia_the = doc_gia_the(a.gia_the, ngay)
    keo = x_goc.doc_keo_cho(cong, ngay, due, phu.ngu)
    if not keo:
        raise KhongDang(f"sg_keo {ngay.isoformat()} chua co dong PS nao")
    boi = chon.Boi(kenh, ngay, due, keo, gia_the, phu.lay_quy_vnd(), phu.lay_trang, phu.tai_anh(ts), chon.da_dung_tu_dong(dong_gan), nb)

    # ---- 2+3. chon (+ chu Threads trong luc chon) + kiem trang + chu + cong tin gia. P2-e: cong/chu truot (vd do dinh dang) -> LOAI game do,
    # chon ung vien khac (toi da LAN_THU_CHON lan), khong dung ca luot.
    mo_da = chu.mo_da_dung_tu_dong(dong_7) if kenh == "threads" else ()
    tin = ck = None
    ly_cuoi = ""
    for lan in range(LAN_THU_CHON):
        if kenh == "threads":
            tin = chon.chon_threads(boi, lambda sv, kq: chu.dung_chu("threads", sv, ngay, mo_da))
        else:
            tin = chon.CHON[kenh](boi)
        viet_json(ra / "chon.json", {"kenh": kenh, "ngay": ngay.isoformat(), "dang": dang, "gio_dang": chung.iso(due), "chon": (tin or {}).get("chon"),
                                     "bo": boi.bo[-300:], "so_trang": boi.so_trang, "lan_chon": lan + 1})
        if tin is None:
            break
        ck = tin.get("chu_san") or chu.dung_chu(kenh, tin["su_that"], ngay)
        loi = ["khong dung duoc chu hop le"] if ck is None else chu.cong(kenh, ck["text"], tin["su_that"])
        if not loi:
            break
        ly_cuoi = "cong tin gia truot: " + "; ".join(loi)[:300]
        boi.ghi_bo("+".join(tin["ma"]), "/".join(tin["tieu_de_hang"]), ly_cuoi)
        boi.da_dung.update(tin["ma"])            # loai cac game nay, chon ung vien khac
        tin = ck = None
    if tin is None:
        raise KhongDang(ly_cuoi or "khong chon duoc tin gia " + kenh + ": " + "; ".join(f"{b['ten'][:24]}: {b['ly'][:70]}" for b in boi.bo[-4:]))
    sv, dl = tin["su_that"], tin["dl"]
    text = ck["text"]
    dong1 = next(d.strip() for d in text.split("\n") if d.strip())
    (ra / "caption.txt").write_text(text + "\n", encoding="utf-8")

    # ---- 4. dung + kiem
    dl_path = ra / "dl.json"
    viet_json(dl_path, dl)
    nhac = phu.nhac(a.du_lieu, ngay) if kenh != "threads" else None
    am = pathlib.Path(a.du_lieu) / "video" / "tai-san" / "am-thanh"
    phu.dung(kenh, dl_path, ts, am, nhac, ra)
    kq_kiem = phu.kiem(kenh, ra, dl_path)
    viet_json(ra / "kiem.json", kq_kiem)
    if not kq_kiem.get("dat"):
        sai = [f"{p.get('ten')}: {p.get('chi_tiet')}" for p in kq_kiem.get("phep") or [] if not p.get("dat")]
        raise KhongDang("kiem.py khong dat: " + "; ".join(sai)[:400])
    bai = {"kenh": kenh, "loai": dang, "chu": text, "captions": {kenh: text}, "giong_ai": False}
    if kenh == "threads":
        bai.update(anh="anh.png", topic_tag=chu.TOPIC_TAG, alt=ck.get("alt"))     # ten tep TUONG DOI: chay kiem-khuon.py tu thu muc chua bai.json
    else:
        bai.update(video="video.mp4", bia="bia.jpg")
    viet_json(ra / "bai.json", bai)
    goi = {"text": text, "ngay": ngay.isoformat(), "video": ra / "video.mp4", "bia": ra / "bia.jpg", "anh": ra / "anh.png", "alt": ck.get("alt")}
    chung.log(f"tin_gia_mxh [{kenh}] chon {tin['tieu_de_hang']} - bien the {ck.get('ma_bien_the', '-')}\n--- CHU ({len(text)} ky tu):\n{text}\n"
              + (f"--- ALT:\n{ck['alt']}\n" if ck.get("alt") else "") + f"--- ra: {ra}")
    if a.khong_api:
        chung.log("tin_gia_mxh: --khong-api - dung o day (khong giu so, khong goi nen tang)")
        return 0

    # ---- 5. truoc tac dung phu: qua som?, dich, giu quyen
    if che_do == "that" and due - chung.bay_gio() > dt.timedelta(minutes=SOM_TOI_DA_PHUT):
        raise KhongDang(f"chay qua som: con {int((due - chung.bay_gio()).total_seconds() // 60)} phut toi gio dang (> {SOM_TOI_DA_PHUT}) - khong giu runner lau")
    zk = os.environ.get("ZERNIO_KHOA", "").strip()
    chung.dang_ky_bi_mat(zk)
    try:
        tk = phu.tai_token(cong, kenh)
        nen = phu.nen(kenh, tk, zk)
        nen.kiem_danh_tinh(phu.dich())             # S13: dung tai khoan dich TRUOC khi tao tai nguyen
    except LoiDang as e:
        raise KhongDang("doi chieu tai khoan dich that bai: " + chung.cat(e, 200)) from None
    if not cong.giu_dang(ngay.isoformat(), dang, kenh, che_do, chung.iso(due), x_goc.sha_dong1(dong1)):
        raise KhongDang("da co dong sg_dang cua hom nay (luot khac giu quyen)")
    han = due + dt.timedelta(minutes=HAN_CONG_KHAI_PHUT)
    da_gui = False
    try:
        cong.cap_nhat_dang(**khoa, id_tai=",".join(tin["ma"]), id_container=ck.get("ma_bien_the") or kenh)
        ly = nhuong_neu_trung(cong, ngay, dang, kenh, che_do, tin["ma"])
        if ly:
            raise KhongDang(ly)
        # ---- 6. chuan bi tren nen tang (KHONG cong khai)
        pb = nen.chuan_bi(goi, che_do, lambda **kw: cong.cap_nhat_dang(**khoa, **kw))
        id_bai = pb["id_bai"]
        if cong.cap_nhat_dang(**khoa, neu_trang_thai="dang_dang", trang_thai="chuan_bi_xong", id_bai=id_bai) != 1:      # P1-a
            raise KhongDang("khong doi duoc sg_dang sang chuan_bi_xong (dong da bi doi boi luot khac) - dung, KHONG cong khai")
        if che_do == "thu":
            chung.log(f"tin_gia_mxh [thu] da chuan bi {kenh} id {id_bai} ({pb.get('ghi_chu', '')}); khong dang")
            doi_that_bai(cong, khoa, f"che do thu: da chuan bi {id_bai}, khong dang")
            return 0
        # ---- 7. cho toi gio, kiem lai gia, cong khai
        bay_gio = chung.bay_gio()
        if bay_gio > han:
            raise KhongDang("da qua han cong khai (gio dang + 15 phut) truoc khi cho")
        if bay_gio < due:
            phu.ngu((due - bay_gio).total_seconds())
        sai = dong_truoc_cong_khai(cong, ngay, dang, kenh, che_do, id_bai)   # Sol luot 3: kiem quyen TRUOC moi nhanh co the ghi so (bo/that_bai)
        if sai:
            raise MatDong(sai)
        van_de, canh_bao = phu.kiem_lai(tin["kiem_lai"], due)
        for c in canh_bao:
            chung.log(f"kiem_lai canh bao: {c}")
        if van_de:
            doi_trang_thai(cong, khoa, ("chuan_bi_xong",), trang_thai="bo", loi=chung.cat("kiem lai gia/han truoc gio dang: " + "; ".join(van_de), 300))
            _bao("Tin giá " + kenh + ": bỏ khung, giá/hạn đổi", chung.cat("; ".join(van_de), 300))
            return 3
        doi_goc = phu.kiem_them(tin["kiem_lai"])     # P2-d: gia goc + % giam doi -> bo (that_bai), khong cong khai
        if doi_goc:
            raise KhongDang("kiem lai gia goc/% giam truoc gio dang: " + "; ".join(doi_goc))
        if chung.bay_gio() > han:                   # S16: kiem han NGAY truoc request cong khai
            raise KhongDang("da qua han cong khai (gio dang + 15 phut) - khong cong khai")
        sai = dong_truoc_cong_khai(cong, ngay, dang, kenh, che_do, id_bai)   # Sol luot 3: dong da sang luot khac thi KHONG duoc doi that_bai o nhanh nhuong
        if sai:
            raise MatDong(sai)
        ly = nhuong_neu_trung(cong, ngay, dang, kenh, che_do, tin["ma"])         # kiem trung game LAN 2 (sau khi ngu + kiem lai)
        if ly:                                   # dong van la cua minh (chuan_bi_xong) nhung game da co ben khac giu -> that_bai co dieu kien, chua cong khai
            doi_trang_thai(cong, khoa, ("chuan_bi_xong",), trang_thai="that_bai", loi=chung.cat("kiem trung lan 2: " + ly, 300))
            _bao("Tin giá " + kenh + ": nhường game trùng trước công khai", chung.cat(ly, 300))
            return 3
        sai = dong_truoc_cong_khai(cong, ngay, dang, kenh, che_do, id_bai)       # P1-a
        if sai:
            raise MatDong(sai)
        da_gui = True
        kq = nen.cong_khai(goi, id_bai, han)
    except MatDong as e:                         # dong khong con la cua minh: KHONG dong vao so
        _bao("Tin giá " + kenh + ": dòng sổ không còn của máy này, dừng", chung.cat(e, 300))
        return 3
    except KhongDang as e:
        doi_that_bai(cong, khoa, e)
        _bao("Tin giá " + kenh + ": không đăng hôm nay", chung.cat(e, 300))
        return 3
    except Exception as e:   # noqa: BLE001 - LoiDang theo quy uoc: khong_ro ro rang; ngoai le khac SAU moc goi cong khai = khong ro
        khong_ro = e.khong_ro if isinstance(e, LoiDang) else da_gui
        try:
            if khong_ro:
                doi_trang_thai(cong, khoa, ("chuan_bi_xong", "dang_dang"), trang_thai="khong_ro", loi=chung.cat(e, 300))
            else:
                doi_that_bai(cong, khoa, f"{type(e).__name__}: {e}")
        except Exception:   # noqa: BLE001
            pass
        _bao("Tin giá " + kenh + (": không rõ đã đăng chưa" if khong_ro else ": chưa đăng"), chung.cat(f"{type(e).__name__}: {e}", 300))
        return 1
    link, id_bai = kq.get("link"), kq.get("id_bai") or id_bai
    try:
        if cong.cap_nhat_dang(**khoa, neu_trang_thai="chuan_bi_xong", trang_thai="da_dang", id_bai=id_bai, link=link,
                              gio_cong_khai=chung.iso(chung.bay_gio())) != 1:
            raise so.LoiCong("dong sg_dang khong con o chuan_bi_xong khi ghi da_dang")
    except Exception as e:   # noqa: BLE001
        _bao("Tin giá " + kenh + ": ĐÃ đăng nhưng ghi sổ lỗi", f"id {id_bai} (link {link or 'chưa có'}): {chung.cat(f'{type(e).__name__}: {e}', 150)}")
        return 1
    if kq.get("canh_bao"):
        _bao("Tin giá " + kenh + ": đã đăng, có cảnh báo", chung.cat(kq["canh_bao"], 200))
    ntfy.tin("Đã đăng tin giá " + kenh, f"{dong1}\n{link or ''}", click=link or None)
    return 0


def chay(a, cong=None, phu=None):
    kenh, che_do = a.kenh, a.che_do
    dang = chon.DANG[kenh]
    if che_do == "that" and not kenh_bat_rieng(os.environ.get("SG_KENH_BAT"), dang, kenh):
        chung.log(f"tin_gia_mxh: SG_KENH_BAT khong co muc rieng {dang}:{kenh} - pha that dang tat, khong lam gi (khong giu so, khong goi nen tang)")
        return 0
    ngay = dt.date.fromisoformat(a.ngay)
    due = gio_du_kien(ngay, kenh)
    if che_do == "that" and chung.bay_gio() > due - dt.timedelta(minutes=QUA_GIO_PHUT):
        _bao("Tin giá " + kenh + ": quá giờ", f"bây giờ đã quá {chon.GIO[kenh]} VN - {QUA_GIO_PHUT} phút, không đăng bù")
        return 3
    try:
        cong = cong or so.Cong()
    except so.LoiCong as e:
        _bao("Tin giá " + kenh + ": thiếu khoá cổng", str(e))
        return 2
    if not a.khong_api and kenh != "fb" and not os.environ.get("ZERNIO_KHOA", "").strip():
        _bao("Tin giá " + kenh + ": thiếu ZERNIO_KHOA", "IG/Threads cần ZERNIO_KHOA để đưa video/ảnh lên URL công khai")
        return 2
    phu = phu or Phu(a.du_lieu)
    if getattr(a, "bo_noi_bat", False):
        if che_do != "thu":
            _bao("Tin giá " + kenh + ": --bo-noi-bat chỉ dùng ở chế độ thử", "pha thật luôn lọc game đã nổi bật 3 ngày")
            return 2
        chung.log("tin_gia_mxh [thu]: --bo-noi-bat - BO QUA loc game da noi bat o khuon khac (chi de xem mau bai, khong bao gio o pha that)")
        phu.nb = lambda ngay, dang: nap_da_noi_bat().NoiBat()
    thu_muc = tempfile.mkdtemp(prefix="sg-tingia-")
    try:
        try:
            return lam(a, cong, phu, thu_muc)
        except KhongDang as e:
            _bao("Tin giá " + kenh + ": không đăng hôm nay", chung.cat(e, 300))
            return 3
    finally:
        if che_do == "thu":                        # ket qua pha thu (ke ca khi KhongDang/loi) len artifact; KHONG chep tai-san (anh Sony)
            ra_thu(pathlib.Path(a.ra) if a.ra else pathlib.Path(thu_muc) / "ra")
        shutil.rmtree(thu_muc, ignore_errors=True)   # anh Sony khong o lai may (ra/ chi giu khi --ra hoac RA_THU)


def main(argv=None):
    ap = argparse.ArgumentParser(description="May tin gia FB/IG/Threads Sang Game")
    ap.add_argument("--kenh", required=True, choices=["fb", "ig", "threads"])
    ap.add_argument("--ngay", default=chung.bay_gio().astimezone(chung.VN).date().isoformat())
    ap.add_argument("--che-do", required=True, choices=["thu", "that"])
    ap.add_argument("--khong-api", action="store_true", help="chi tren Mac: chon + dung + kiem + chu, KHONG giu so, KHONG goi nen tang")
    ap.add_argument("--du-lieu", default=os.environ.get("DU_LIEU_REPO") or "du-lieu", help="thu muc repo rieng tu kenh-game-du-lieu")
    ap.add_argument("--gia-the", default=None)
    ap.add_argument("--bo-noi-bat", action="store_true", help="CHI che do thu: bo loc game da noi bat o khuon khac (xem mau bai khi hom nay het ung vien)")
    ap.add_argument("--ra", default=None, help="thu muc ra (mac dinh: thu muc tam, chi RA_THU duoc chep)")
    a = ap.parse_args(argv)
    try:
        dt.date.fromisoformat(a.ngay)
    except ValueError:
        ap.error("--ngay phai la YYYY-MM-DD")
    a.gia_the = a.gia_the or str(pathlib.Path(a.du_lieu) / "du-lieu" / "gia-the.json")
    try:
        return chay(a)
    except Exception as e:   # noqa: BLE001
        _bao("Tin giá " + a.kenh + ": lỗi bất ngờ", chung.cat(f"{type(e).__name__}: {e}", 300))
        return 1


if __name__ == "__main__":
    sys.exit(main())
