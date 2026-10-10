"""YouTube Shorts qua videos.insert (tai resumable).
  Pha chuan bi: tai len voi privacyStatus=private; che_do=that them publishAt = gio dang (YouTube tu cong khai dung gio).
  Pha cong khai: chi KIEM da public; qua gio +2 phut van private thi dat public bang videos.update (an toan, idempotent).
Tai len: chunk la boi so cua 256 KB; loi mang / 5xx -> hoi vi tri bang 'Content-Range: bytes */tong' roi PUT tiep (toi da 5 lan).
# CHUA KIEM: quota videos.insert (tai lieu mau thuan 1 vs 1600 don vi) - https://developers.google.com/youtube/v3/determine_quota_cost
# CHUA KIEM: Shorts duoc nhan dien nho video doc <= 3 phut + '#Shorts' trong mo ta - https://support.google.com/youtube/answer/10059070
# CHUA KIEM: categoryId=20 (Gaming), selfDeclaredMadeForKids=false - https://developers.google.com/youtube/v3/docs/videos/insert
"""
import datetime as dt

from . import chung, http

TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://www.googleapis.com/youtube/v3"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3/videos"
CHUNK = 32 * 256 * 1024  # 8 MiB
_cache = {}


def lam_moi_access(tk):
    """Doi refresh_token lay access_token (cache theo process). Google khong xoay refresh token; neu co tra moi thi tra kem."""
    k = tk["refresh_token"]
    if k in _cache:
        return _cache[k], None
    try:
        r = http.gui("POST", TOKEN_URL, timeout=30, form={
            "grant_type": "refresh_token", "client_id": tk["client_id"],
            "client_secret": tk["client_secret"], "refresh_token": tk["refresh_token"]})
    except http.LoiMang as e:
        raise chung.LoiDang(f"YouTube refresh: {e}") from None
    j = r.json()
    if r.status != 200 or not j.get("access_token"):
        # invalid_grant = refresh token het han / bi thu hoi (app dang Testing -> 7 ngay)
        raise chung.LoiDang(f"YouTube refresh that bai: HTTP {r.status} {j.get('error')}")
    chung.dang_ky_bi_mat(j["access_token"])
    _cache[k] = j["access_token"]
    return j["access_token"], j.get("refresh_token")


def _hdr(tk):
    return {"Authorization": "Bearer " + lam_moi_access(tk)[0]}


def danh_tinh(tk, nc=None):
    try:
        r = http.gui("GET", f"{API}/channels", headers=_hdr(tk), params={"part": "id", "mine": "true"}, timeout=30)
    except http.LoiMang as e:
        raise chung.LoiDang(f"YouTube channels: {e}") from None
    items = r.json().get("items") or []
    if r.status != 200 or not items:
        raise chung.LoiDang(f"YouTube channels?mine=true that bai: HTTP {r.status}")
    cid = str(items[0].get("id"))
    if tk.get("channel_id") and cid != str(tk["channel_id"]):
        raise chung.LoiDang("YouTube channel tu token khac channel_id da luu")
    return cid


def _vi_tri_tiep(r):
    rg = r.headers.get("range", "")  # "bytes=0-524287"
    if rg.startswith("bytes=") and "-" in rg:
        return int(rg.split("-")[-1]) + 1
    return 0


def tai_len(url_phien, du_lieu, tk, mime="video/mp4", toi_da_loi=5):
    """PUT tung chunk. 200/201 -> tra resource (dict). Loi tam thoi -> hoi vi tri roi tiep tuc."""
    tong = len(du_lieu)
    vt, loi = 0, 0
    hdr = _hdr(tk)
    while True:
        den = min(vt + CHUNK, tong)
        try:
            r = http.gui("PUT", url_phien, timeout=300, data=du_lieu[vt:den],
                         headers={**hdr, "Content-Type": mime, "Content-Range": f"bytes {vt}-{den - 1}/{tong}"})
            loi_mang = False
        except http.LoiMang:
            r, loi_mang = None, True
        if r is not None and r.status in (200, 201):
            return r.json()
        if r is not None and r.status == 308:
            vt, loi = _vi_tri_tiep(r), 0
            continue
        if loi_mang or r.status >= 500:
            loi += 1
            if loi > toi_da_loi:
                raise chung.LoiDang(f"YouTube tai len: qua {toi_da_loi} lan loi tam thoi lien tiep")
            chung.ngu(min(2 ** loi, 30))
            try:
                q = http.gui("PUT", url_phien, timeout=60, data=b"",
                             headers={**hdr, "Content-Range": f"bytes */{tong}"})
            except http.LoiMang:
                continue
            if q.status in (200, 201):
                return q.json()
            if q.status == 308:
                vt = _vi_tri_tiep(q)
            continue
        raise chung.LoiDang(f"YouTube tai len that bai: HTTP {r.status} {str(r.json())[:200]}")


def chuan_bi(tk, nc, luu):
    du_lieu = nc.tep("shorts").read_bytes()
    trang_thai = {"privacyStatus": "private", "selfDeclaredMadeForKids": False}
    if nc.che_do == "that":
        trang_thai["publishAt"] = chung.iso(nc.gio_dang)
    thong_tin = {"snippet": {"title": nc.loi_dang["tieu_de"][:100], "description": nc.mo_ta_youtube(),
                        "categoryId": "20", "tags": [h.lstrip("#") for h in (nc.loi_dang.get("hashtag") or [])][:15]},
            "status": trang_thai}
    try:
        r = http.gui("POST", UPLOAD, timeout=60, params={"uploadType": "resumable", "part": "snippet,status"},
                     json_body=thong_tin, headers={**_hdr(tk), "X-Upload-Content-Length": str(len(du_lieu)),
                                              "X-Upload-Content-Type": "video/mp4"})
    except http.LoiMang as e:
        raise chung.LoiDang(f"YouTube khoi tao tai len: {e}") from None
    url_phien = r.headers.get("location")
    if r.status != 200 or not url_phien:
        raise chung.LoiDang(f"YouTube khoi tao tai len that bai: HTTP {r.status} {str(r.json())[:200]}")
    chung.dang_ky_bi_mat(url_phien)
    res = tai_len(url_phien, du_lieu, tk)
    vid = str(res.get("id") or "")
    if not vid:
        raise chung.LoiDang("YouTube tai xong nhung khong tra video id", khong_ro=True)
    luu(id_tai=vid)
    return {"id_tai": vid}


def _privacy(tk, vid):
    r = http.gui("GET", f"{API}/videos", headers=_hdr(tk), params={"part": "status", "id": vid}, timeout=30)
    items = r.json().get("items") or []
    if r.status != 200 or not items:
        raise chung.LoiDang(f"YouTube doc trang thai video {vid}: HTTP {r.status}")
    return (items[0].get("status") or {}).get("privacyStatus")


def cong_khai(tk, nc, dong):
    vid = str(dong.get("id_tai") or "")
    if not vid:
        raise chung.LoiDang("sg_dang khong co id_tai cho YouTube")
    ket = {"id_bai": vid, "link": f"https://www.youtube.com/shorts/{vid}"}
    try:
        for i in range(8):
            if _privacy(tk, vid) == "public":
                return ket
            if chung.bay_gio() >= nc.gio_dang + dt.timedelta(minutes=2):
                break
            chung.ngu(20)
        # Qua gio dang +2 phut ma chua public: dat public truc tiep (publishAt khong chay / bi lech)
        body = {"id": vid, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
        r = http.gui("PUT", f"{API}/videos", headers=_hdr(tk), params={"part": "status"}, json_body=body, timeout=30)
        if r.status != 200:
            raise chung.LoiDang(f"YouTube videos.update public that bai: HTTP {r.status}", khong_ro=True)
    except http.LoiMang as e:
        raise chung.LoiDang(f"YouTube: {e}", khong_ro=True) from None
    ket["canh_bao"] = "publishAt khong tu cong khai - da dat public bang videos.update"
    return ket
