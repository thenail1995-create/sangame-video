"""TikTok Content Posting API - Upload vao HOP THU (inbox) bang FILE_UPLOAD; Hao bam thong bao de dang.
  init (source_info FILE_UPLOAD) -> PUT chunk theo quy tac -> hoi trang thai den SEND_TO_USER_INBOX.
Quy tac chunk (tai lieu): moi chunk 5-64 MB, chunk cuoi duoc toi 128 MB; file <= 64 MB = 1 chunk. upload_url song 1 gio.
Access token 24 h: lam moi neu con < 2 h va LUU NGAY refresh token moi (co the xoay) qua ghi_token truoc khi lam gi khac.
Gioi han: 6 request/phut/token; toi da 5 'pending share'/24 h (loi spam_risk_too_many_pending_share).
# CHUA KIEM: duong dan /v2/post/publish/inbox/video/init/ va cac gia tri status (PROCESSING_UPLOAD, SEND_TO_USER_INBOX, FAILED)
#   - https://developers.tiktok.com/doc/content-posting-api-reference-upload-video
# nap-token.py xin scope user.info.basic,video.upload nen /v2/user/info/ dung duoc (open_id).
"""
import datetime as dt

from . import chung, http

TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
INFO_URL = "https://open.tiktokapis.com/v2/user/info/"
INIT_URL = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"
CHUNK_TOI_DA = 64 * 1024 * 1024
LAM_MOI_TRUOC = dt.timedelta(hours=2)


def _t(v):
    """nap-token.py ghi access_het_han / refresh_het_han la epoch giay (int); chap nhan ca ISO."""
    if isinstance(v, (int, float)):
        return dt.datetime.fromtimestamp(v, dt.timezone.utc)
    return dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))


def lam_moi(tk, nc, ep=False):
    """Lam moi access token neu con < 2 h (hoac ep=True). Tra tk moi; da ghi_token neu doi."""
    het = tk.get("access_het_han")
    if not ep and het and _t(het) - chung.bay_gio() > LAM_MOI_TRUOC:
        return tk
    try:
        r = http.gui("POST", TOKEN_URL, timeout=30, form={
            "client_key": tk["client_key"], "client_secret": tk["client_secret"],
            "grant_type": "refresh_token", "refresh_token": tk["refresh_token"]})
    except http.LoiMang as e:
        raise chung.LoiDang(f"TikTok refresh: {e}") from None
    j = r.json()
    if r.status != 200 or not j.get("access_token"):
        raise chung.LoiDang(f"TikTok refresh that bai: HTTP {r.status} {j.get('error') or j.get('error_description')}")
    chung.dang_ky_bi_mat(j["access_token"], j.get("refresh_token") or "")
    bay = chung.bay_gio()
    moi = dict(tk)
    moi["access_token"] = j["access_token"]
    moi["access_het_han"] = int(bay.timestamp()) + int(j.get("expires_in") or 86400)
    if j.get("refresh_token"):
        moi["refresh_token"] = j["refresh_token"]
        moi["refresh_het_han"] = int(bay.timestamp()) + int(j.get("refresh_expires_in") or 365 * 86400)
    # LUU NGAY (Sol #10): mat refresh token moi = het dung duoc ca kenh
    nc.cong.ghi_token("tiktok", moi, chung.iso(_t(moi["refresh_het_han"])))
    return moi


def danh_tinh(tk, nc):
    tk2 = lam_moi(tk, nc)
    try:
        r = http.gui("GET", INFO_URL, params={"fields": "open_id"},
                     headers={"Authorization": "Bearer " + tk2["access_token"]}, timeout=30)
    except http.LoiMang as e:
        raise chung.LoiDang(f"TikTok user info: {e}") from None
    oid = str(((r.json().get("data") or {}).get("user") or {}).get("open_id") or "")
    if r.status != 200 or not oid:
        raise chung.LoiDang(f"TikTok user info that bai: HTTP {r.status}")
    if tk2.get("open_id") and oid != str(tk2["open_id"]):
        raise chung.LoiDang("TikTok open_id tu token khac open_id da luu")
    return oid


def chia_chunk(kich_thuoc):
    """-> (chunk_size, total_chunk_count). Chunk cuoi nuot phan du (< chunk_size nen chunk cuoi < 128 MB)."""
    if kich_thuoc <= CHUNK_TOI_DA:
        return kich_thuoc, 1
    return CHUNK_TOI_DA, kich_thuoc // CHUNK_TOI_DA


def _loi_api(j):
    e = j.get("error") or {}
    return None if e.get("code") in (None, "ok") else e


def hop_thu(tk, nc):
    """Upload vao hop thu. Tra {"id_tai": publish_id, ...}. Thanh cong khi trang thai SEND_TO_USER_INBOX."""
    tk = lam_moi(tk, nc)
    hdr = {"Authorization": "Bearer " + tk["access_token"]}
    du_lieu = nc.tep("tiktok").read_bytes()
    n = len(du_lieu)
    chunk, tong = chia_chunk(n)
    try:
        r = http.gui("POST", INIT_URL, headers=hdr, timeout=60, json_body={"source_info": {
            "source": "FILE_UPLOAD", "video_size": n, "chunk_size": chunk, "total_chunk_count": tong}})
    except http.LoiMang as e:
        raise chung.LoiDang(f"TikTok init: {e}", khong_ro=True) from None
    j = r.json()
    e = _loi_api(j)
    if r.status >= 500:
        raise chung.LoiDang(f"TikTok init: HTTP {r.status}", khong_ro=True)
    if e or r.status != 200:
        ma = (e or {}).get("code")
        if ma == "spam_risk_too_many_pending_share":
            raise chung.LoiDang("TikTok: qua 5 video dang cho dang trong hop thu (Hao chua bam dang) - bo TikTok khung nay")
        raise chung.LoiDang(f"TikTok init that bai: HTTP {r.status} {ma} {(e or {}).get('message')}")
    d = j.get("data") or {}
    publish_id, url_up = str(d.get("publish_id") or ""), d.get("upload_url")
    if not publish_id or not url_up:
        raise chung.LoiDang("TikTok init khong tra publish_id/upload_url", khong_ro=True)
    chung.dang_ky_bi_mat(url_up)
    for i in range(tong):
        a = i * chunk
        b = n - 1 if i == tong - 1 else a + chunk - 1
        try:
            u = http.gui("PUT", url_up, timeout=600, data=du_lieu[a:b + 1],
                         headers={"Content-Type": "video/mp4", "Content-Range": f"bytes {a}-{b}/{n}"})
        except http.LoiMang as ex:
            raise chung.LoiDang(f"TikTok PUT chunk {i + 1}/{tong}: {ex}", khong_ro=True) from None
        if u.status not in (200, 201, 206):
            raise chung.LoiDang(f"TikTok PUT chunk {i + 1}/{tong}: HTTP {u.status}", khong_ro=True)
    # Hoi trang thai (<= 6 request/phut -> nhip >= 10 giay)
    cuoi = None
    for i in range(30):
        try:
            s = http.gui("POST", STATUS_URL, headers=hdr, json_body={"publish_id": publish_id}, timeout=30)
        except http.LoiMang:
            chung.ngu(10)
            continue
        dd = s.json().get("data") or {}
        cuoi = dd.get("status")
        if cuoi in ("SEND_TO_USER_INBOX", "PUBLISH_COMPLETE"):
            return {"id_tai": publish_id, "id_bai": publish_id, "link": None}
        if cuoi == "FAILED":
            raise chung.LoiDang(f"TikTok bao FAILED: {dd.get('fail_reason')}", khong_ro=True)
        chung.ngu(10)
    raise chung.LoiDang(f"TikTok het gio cho (trang thai cuoi: {cuoi})", khong_ro=True)


def gia_han(tk, nc):
    """Dung cho gia-han.yml: lam moi ep buoc, tra tk moi."""
    return lam_moi(tk, nc, ep=True)
