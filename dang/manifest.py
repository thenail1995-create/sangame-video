"""Tai Release v-<ngay>-<dang> va kiem manifest theo HOP-DONG.md muc 1-2. Sai bat ky dieu gi -> LoiManifest (khong dang)."""
import datetime as dt
import re
import json
import os
import pathlib

from . import chung, http

REPO = os.environ.get("GITHUB_REPOSITORY", "thenail1995-create/sangame-video")
API = "https://api.github.com"
TAI_SAN_CHO_PHEP = {
    "video-tiktok.mp4", "video-reels.mp4", "video-shorts.mp4",
    "bia-tiktok.jpg", "bia-reels.jpg", "bia-shorts.jpg", "manifest.json",
}
DANG_HOP_LE = ("tin-nhanh", "top5", "keo-thom", "keo-thom-2", "keo-thom-3")
BAN = ("tiktok", "reels", "shorts")


class LoiManifest(Exception):
    pass


def tag(ngay, dang, che_do="that"):
    """HOP-DONG muc 1: that -> v-<ngay>-<dang>; thu -> thu-<ngay>-<dang> (pre-release, chi de thu may dang)."""
    return f"{'thu' if che_do == 'thu' else 'v'}-{ngay}-{dang}"


def _hdr_api():
    t = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    return {"Accept": "application/vnd.github+json", **({"Authorization": f"Bearer {t}"} if t else {})}


def _lay(url, **kw):
    try:
        return http.gui("GET", url, theo_chuyen_huong=True, timeout=300, **kw)
    except http.LoiMang as e:
        raise LoiManifest(str(e)) from None


def liet_ke_tai_san(ngay, dang, repo=None, che_do="that"):
    r = http.gui("GET", f"{API}/repos/{repo or REPO}/releases/tags/{tag(ngay, dang, che_do)}", headers=_hdr_api(), timeout=30)
    if r.status == 404:
        raise LoiManifest(f"khong co Release {tag(ngay, dang, che_do)}")
    if r.status != 200:
        raise LoiManifest(f"doc Release {tag(ngay, dang, che_do)}: HTTP {r.status}")
    ten = [a.get("name") for a in (r.json().get("assets") or [])]
    la = sorted(set(ten) - TAI_SAN_CHO_PHEP)
    if la:
        raise LoiManifest(f"Release co tai san ngoai danh sach cho phep: {la}")
    return ten


def tai_tep(ngay, dang, ten, thu_muc, repo=None, che_do="that") -> pathlib.Path:
    url = f"https://github.com/{repo or REPO}/releases/download/{tag(ngay, dang, che_do)}/{ten}"
    r = _lay(url)
    if r.status != 200 or not r.body:
        raise LoiManifest(f"tai {ten} tu Release {tag(ngay, dang, che_do)}: HTTP {r.status}")
    duong = pathlib.Path(thu_muc) / ten
    duong.write_bytes(r.body)
    return duong


def tai_release(ngay, dang, thu_muc, ban_can, repo=None, che_do="that") -> dict:
    """Tai manifest + video/bia cua cac ban trong ban_can vao thu_muc, tra manifest (dict) da kiem. ban_can: tap con cua BAN."""
    ten = liet_ke_tai_san(ngay, dang, repo, che_do)
    pathlib.Path(thu_muc).mkdir(parents=True, exist_ok=True)
    if "manifest.json" not in ten:
        raise LoiManifest("Release khong co manifest.json")
    man = _doc(tai_tep(ngay, dang, "manifest.json", thu_muc, repo, che_do))
    for b in ban_can:
        for k in ("video", "bia"):
            f = (man.get("ban", {}).get(b) or {}).get(k)
            if not f or f not in TAI_SAN_CHO_PHEP or f not in ten:
                raise LoiManifest(f"manifest ban {b}: thieu/khong hop le truong {k}={f}")
            tai_tep(ngay, dang, f, thu_muc, repo, che_do)
    return man


def _doc(duong) -> dict:
    try:
        m = json.loads(pathlib.Path(duong).read_text("utf-8"))
    except (OSError, ValueError) as e:
        raise LoiManifest(f"manifest.json khong doc duoc: {type(e).__name__}") from None
    if not isinstance(m, dict):
        raise LoiManifest("manifest.json khong phai object")
    return m


def kiem(man, thu_muc, ngay, dang, che_do, ban_can=BAN):
    """Kiem day du; tra man neu dung. Moi file thuoc ban_can phai co mat va dung sha256."""
    if man.get("phien_ban") != 1:
        raise LoiManifest(f"phien_ban manifest = {man.get('phien_ban')}, can 1")
    if man.get("ngay_dang") != ngay:
        raise LoiManifest(f"ngay_dang {man.get('ngay_dang')} != {ngay}")
    if man.get("dang") != dang or dang not in DANG_HOP_LE:
        raise LoiManifest(f"dang {man.get('dang')} != {dang}")
    if man.get("che_do") != che_do:
        raise LoiManifest(f"che_do {man.get('che_do')} != {che_do}")
    try:
        gio = dt.datetime.fromisoformat(man["gio_dang"])
        if gio.tzinfo is None:
            raise ValueError
    except (KeyError, ValueError, TypeError):
        raise LoiManifest("gio_dang thieu hoac sai dinh dang ISO co mui gio") from None
    if gio.astimezone(chung.VN).date().isoformat() != ngay:
        raise LoiManifest(f"gio_dang {man['gio_dang']} khong thuoc ngay {ngay} (gio VN)")
    for truong in ("sha_code", "sha_du_lieu", "tao_luc"):
        if not isinstance(man.get(truong), str) or not man[truong].strip():
            raise LoiManifest(f"manifest thieu nguon/{truong}")
    ban = man.get("ban") or {}
    for b in BAN:
        k = (ban.get(b) or {}).get("kiem") or {}
        if k.get("dat") is not True:
            raise LoiManifest(f"ban {b} khong dat bo kiem (kiem.dat != true)")
        phep = k.get("phep")
        if not isinstance(phep, list) or not phep:
            raise LoiManifest(f"ban {b}: kiem.phep rong")
        sai = [p.get("ten") for p in phep if not isinstance(p, dict) or p.get("dat") is not True]
        if sai:
            raise LoiManifest(f"ban {b}: kiem.dat=true nhung phep con khong dat: {sai}")
        if ban[b].get("video") != f"video-{b}.mp4" or ban[b].get("bia") != f"bia-{b}.jpg":
            raise LoiManifest(f"ban {b}: ten video/bia khong dung quy uoc video-{b}.mp4 / bia-{b}.jpg")
    for b in ban_can:
        for fk, sk in (("video", "sha256"), ("bia", "bia_sha256")):
            ten, sha = ban[b].get(fk), ban[b].get(sk)
            if ten not in TAI_SAN_CHO_PHEP or not sha:
                raise LoiManifest(f"ban {b}: thieu {fk}/{sk}")
            duong = pathlib.Path(thu_muc) / ten
            if not duong.is_file():
                raise LoiManifest(f"thieu file {ten}")
            if chung.sha256_tep(duong) != sha:
                raise LoiManifest(f"sha256 {ten} khong khop manifest")
    ld = man.get("loi_dang") or {}
    if not ld.get("tieu_de") or len(ld["tieu_de"]) > 100 or len(ld.get("mo_ta", "")) > 2000:
        raise LoiManifest("loi_dang thieu tieu_de hoac vuot gioi han (tieu_de<=100, mo_ta<=2000)")
    return man


def gio_dang(man) -> dt.datetime:
    """Gio dang cua khung. DANG BU (Hao 12/10 "phai sua roi dang"): env DANG_BU_GIO=HH:MM (gio VN, CUNG ngay dang cua manifest) thay gio
    trong manifest cho moi chot gio (som/tre 90 phut, kiem lai gia/han = gio moi + 2 h). Rong -> gio cua manifest."""
    g = dt.datetime.fromisoformat(man["gio_dang"])
    bu = (os.environ.get("DANG_BU_GIO") or "").strip()
    if not bu:
        return g
    m = re.fullmatch(r"([01]\d|2[0-3]):([0-5]\d)", bu)
    if not m:
        raise LoiManifest(f"DANG_BU_GIO sai dinh dang HH:MM: {bu!r}")
    return g.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)
