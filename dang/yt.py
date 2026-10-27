"""YouTube Shorts qua videos.insert (tai resumable).
  Pha chuan bi: tai len voi privacyStatus=private, KHONG dat publishAt (lich da dat van chay du pha cong khai bi chan).
  Pha cong khai: sau MOI cong kiem cua chay.py (manifest, dich.json, gio, giu quyen so-va-dat) moi videos.update -> public.
Tai len: chunk la boi so cua 256 KB; loi mang / 5xx -> PHAI xac dinh offset bang 'Content-Range: bytes */tong' truoc khi gui
tiep du lieu (khong gui lai vung byte cu khi chua biet offset); toi da 5 lan loi lien tiep.
Can scope https://www.googleapis.com/auth/youtube (videos.update) - nap-token.py da xin.
Co AI: videos.list KHONG tra containsSyntheticMedia; videos.update part=status TRA no trong phan hoi (do 27/10) -> chuan_bi xac nhan co
qua phan hoi insert, thieu thi videos.update (van private) doc lai; khong xac nhan duoc = LoiDang khong_ro, KHONG dat bia/KHONG cong khai.
cong_khai kiem co trong phan hoi update public; thieu -> keo ve private + loi khong_ro (luat Hao 27/10: khong co video AI cong khai thieu nhan).
# CHUA KIEM: quota videos.insert (tai lieu mau thuan 1 vs 1600 don vi) - https://developers.google.com/youtube/v3/determine_quota_cost
# CHUA KIEM: Shorts duoc nhan dien nho video doc <= 3 phut + '#Shorts' trong mo ta - https://support.google.com/youtube/answer/10059070
# CHUA KIEM: categoryId=20 (Gaming), selfDeclaredMadeForKids=false; videos.update part=status ghi de ca khoi status - https://developers.google.com/youtube/v3/docs/videos/update
"""
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
    """PUT tung chunk. 200/201 -> tra resource (dict). Sau loi tam thoi: chi hoi offset (PUT rong 'bytes */tong'), chua biet
    offset thi KHONG gui du lieu."""
    tong = len(du_lieu)
    vt, loi, can_hoi = 0, 0, False
    hdr = _hdr(tk)

    def that_bai():
        nonlocal loi
        loi += 1
        if loi > toi_da_loi:
            raise chung.LoiDang(f"YouTube tai len: qua {toi_da_loi} lan loi tam thoi lien tiep", khong_ro=True)
        chung.ngu(min(2 ** loi, 30))

    while True:
        if can_hoi:
            try:
                q = http.gui("PUT", url_phien, timeout=60, data=b"", headers={**hdr, "Content-Range": f"bytes */{tong}"})
            except http.LoiMang:
                that_bai()
                continue
            if q.status in (200, 201):
                return q.json()
            if q.status == 308:
                vt, can_hoi = _vi_tri_tiep(q), False
                continue
            if q.status >= 500:
                that_bai()
                continue
            raise chung.LoiDang(f"YouTube hoi offset that bai: HTTP {q.status}", khong_ro=True)
        den = min(vt + CHUNK, tong)
        try:
            r = http.gui("PUT", url_phien, timeout=300, data=du_lieu[vt:den],
                         headers={**hdr, "Content-Type": mime, "Content-Range": f"bytes {vt}-{den - 1}/{tong}"})
        except http.LoiMang:
            can_hoi = True
            that_bai()
            continue
        if r.status in (200, 201):
            return r.json()
        if r.status == 308:
            vt, loi = _vi_tri_tiep(r), 0
            continue
        if r.status >= 500:
            can_hoi = True
            that_bai()
            continue
        raise chung.LoiDang(f"YouTube tai len that bai: HTTP {r.status} {chung.cat(r.json())}", khong_ro=True)


def trang_thai_ai():
    """containsSyntheticMedia phai co o CA insert lan update (update ghi de toan phan status)."""
    return {"containsSyntheticMedia": True} if chung.CO_GIONG_AI else {}


def trang_thai(privacy):
    """videos.update GHI DE ca muc status: thieu embeddable/publicStatsViewable la YouTube TAT nhung + an luot xem
    (15/10 moi Shorts tu dong playableInEmbed:false) -> insert lan update deu gui du truong."""
    return {"privacyStatus": privacy, "selfDeclaredMadeForKids": False, "embeddable": True,
            "publicStatsViewable": True, "license": "youtube", **trang_thai_ai()}


def chuan_bi(tk, nc, luu):
    du_lieu = nc.tep("shorts").read_bytes()
    trang_thai_moi = trang_thai("private")
    thong_tin = {"snippet": {"title": nc.tieu_de_youtube(), "description": nc.mo_ta_youtube(),
                        "categoryId": "20", "tags": nc.tags_youtube()},
            "status": trang_thai_moi}
    try:
        r = http.gui("POST", UPLOAD, timeout=60, params={"uploadType": "resumable", "part": "snippet,status"},
                     json_body=thong_tin, headers={**_hdr(tk), "X-Upload-Content-Length": str(len(du_lieu)),
                                              "X-Upload-Content-Type": "video/mp4"})
    except http.LoiMang as e:
        raise chung.LoiDang(f"YouTube khoi tao tai len: {e}") from None
    url_phien = r.headers.get("location")
    if r.status != 200 or not url_phien:
        raise chung.LoiDang(f"YouTube khoi tao tai len that bai: HTTP {r.status} {chung.cat(r.json())}")
    chung.dang_ky_bi_mat(url_phien)
    res = tai_len(url_phien, du_lieu, tk)
    vid = str(res.get("id") or "")
    if not vid:
        raise chung.LoiDang("YouTube tai xong nhung khong tra video id", khong_ro=True)
    try:
        luu(id_tai=vid)
    except Exception as e:  # video DA len YouTube ma khong ghi duoc id -> khong_ro, KHONG tai lai
        raise chung.LoiDang(f"YouTube da nhan video {vid} nhung ghi so loi: {type(e).__name__}", khong_ro=True) from None
    ket = {"id_tai": vid, **xac_nhan_ai(tk, vid, res)}   # co AI phai xac nhan TRUOC khi dat bia / cong khai
    ok, ly_do = dat_bia(tk, vid, nc)
    ket["bia"] = True if ok else f"loi: {ly_do}"
    return ket


def doc_co_ai(res):
    """containsSyntheticMedia trong phan hoi videos.insert/update (khoi status co the thieu)."""
    j = res if isinstance(res, dict) else {}
    return (j.get("status") or {}).get("containsSyntheticMedia")


def xac_nhan_ai(tk, vid, res):
    """Bang chung co AI cua video DA tai (private). res = phan hoi insert. Tra {} khi CO_GIONG_AI tat;
    {"nhan_ai": True, "nhan_ai_tu": "insert"|"update"} khi xac nhan duoc. Insert thieu co -> videos.update part=status (van private)
    doc lai trong phan hoi. Khong xac nhan duoc / loi bat ky -> LoiDang(khong_ro=True): video da len YouTube, KHONG tai lai."""
    if not chung.CO_GIONG_AI:
        return {}
    if doc_co_ai(res) is True:
        return {"nhan_ai": True, "nhan_ai_tu": "insert"}
    ly_do = "insert khong tra co"
    try:
        r = http.gui("PUT", f"{API}/videos", headers=_hdr(tk), params={"part": "status"},
                     json_body={"id": vid, "status": trang_thai("private")}, timeout=30)
        if r.status == 200 and doc_co_ai(r.json()) is True:
            return {"nhan_ai": True, "nhan_ai_tu": "update"}
        ly_do = f"update HTTP {r.status} " + ("khong tra co" if r.status == 200 else chung.cat(r.json(), 120))
    except http.LoiMang as e:
        ly_do = f"update loi mang: {e}"
    raise chung.LoiDang(f"YouTube khong xac nhan duoc co AI ({ly_do}), video {vid} de rieng tu", khong_ro=True)


BIA_TOI_DA = 2 * 1024 * 1024   # thumbnails.set: toi da 2 MB


def dat_bia(tk, vid, nc):
    """thumbnails.set bang bia ban shorts (Hao 25/10: video Top 5 len YouTube khong co bia). Loi bia KHONG lam hong
    video da tai: tra (ok, ly_do), chay.py ghi log 'bia=...'."""
    try:
        du_lieu = nc.tep("shorts", "bia").read_bytes()
    except (OSError, KeyError) as e:
        return False, f"khong doc duoc bia: {type(e).__name__}"
    if not du_lieu or len(du_lieu) > BIA_TOI_DA:
        return False, "bia rong hoac > 2 MB"
    try:
        r = http.gui("POST", f"{UPLOAD.rsplit('/', 1)[0]}/thumbnails/set", timeout=60,
                     params={"videoId": vid, "uploadType": "media"}, data=du_lieu,
                     headers={**_hdr(tk), "Content-Type": "image/jpeg"})
        if r.status == 200:
            return True, ""
        return False, f"HTTP {r.status} {chung.cat(r.json())}"
    except Exception as e:   # moi loi bia (ke ca loi la) KHONG duoc lam hong video da tai len
        return False, chung.cat(f"{type(e).__name__}: {e}")


def _privacy(tk, vid):
    try:
        r = http.gui("GET", f"{API}/videos", headers=_hdr(tk), params={"part": "status", "id": vid}, timeout=30)
    except http.LoiMang as e:
        raise chung.LoiDang(f"YouTube doc trang thai: {e}") from None
    items = r.json().get("items") or []
    if r.status != 200 or not items:
        raise chung.LoiDang(f"YouTube doc trang thai video {vid}: HTTP {r.status}")
    return (items[0].get("status") or {}).get("privacyStatus")


def cong_khai(tk, nc, dong):
    """Chi duoc goi SAU cac cong kiem va giu quyen so-va-dat. Da public thi khong cap nhat; khong chac thi hoi lai 1 lan."""
    vid = str(dong.get("id_tai") or "")
    if not vid:
        raise chung.LoiDang("sg_dang khong co id_tai cho YouTube")
    ket = {"id_bai": vid, "link": f"https://www.youtube.com/shorts/{vid}"}
    if _privacy(tk, vid) == "public":
        return _chot_nhan_ai(tk, vid, ket, _put_public(tk, vid) if chung.CO_GIONG_AI else None)   # da public tu truoc: khong co bang chung co -> PUT public (idempotent) doc lai
    r = _put_public(tk, vid)
    ok = r is not None and r.status == 200
    if not ok:
        ly_do = "mạng" if r is None else f"HTTP {r.status}"
        if r is not None and 400 <= r.status < 500:
            raise chung.LoiDang(f"YouTube videos.update public bi tu choi: {ly_do}")
        try:
            da_public = _privacy(tk, vid) == "public"
        except (chung.LoiDang, http.LoiMang):
            da_public = False
        if da_public:   # PUT bi mat phan hoi nhung video da public: van phai co bang chung co AI
            return _chot_nhan_ai(tk, vid, ket, _put_public(tk, vid) if chung.CO_GIONG_AI else None)
        raise chung.LoiDang(f"YouTube videos.update public khong chac ket qua: {ly_do}", khong_ro=True)
    return _chot_nhan_ai(tk, vid, ket, r)


def _put_public(tk, vid):
    """videos.update part=status -> public. Tra Phan hoac None khi loi mang."""
    try:
        return http.gui("PUT", f"{API}/videos", headers=_hdr(tk), params={"part": "status"},
                        json_body={"id": vid, "status": trang_thai("public")}, timeout=30)
    except http.LoiMang:
        return None


def _chot_nhan_ai(tk, vid, ket, r):
    """r = phan hoi PUT public (None/khong 200 = khong co bang chung). Video AI public ma thieu co -> keo ve private + loi khong_ro."""
    nhan = doc_co_ai(r.json()) if r is not None and r.status == 200 else None
    if chung.CO_GIONG_AI and nhan is not True:
        try:
            q = http.gui("PUT", f"{API}/videos", headers=_hdr(tk), params={"part": "status"},
                         json_body={"id": vid, "status": trang_thai("private")}, timeout=30)
            keo_ve = q.status == 200
        except http.LoiMang:
            keo_ve = False
        if keo_ve:
            raise chung.LoiDang(f"YouTube public không xác nhận nhãn AI — đã kéo về riêng tư, kiểm tay (video {vid})", khong_ro=True)
        raise chung.LoiDang(f"YouTube public không xác nhận nhãn AI VÀ kéo về riêng tư THẤT BẠI — video {vid} đang CÔNG KHAI, xử lý tay ngay", khong_ro=True)
    if nhan is True:
        ket["nhan_ai"] = True
    return ket
