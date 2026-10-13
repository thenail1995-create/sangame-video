"""TikTok dang THANG CONG KHAI qua dich vu Zernio (docs.zernio.com). Thay cho hop thu khi co env ZERNIO_KHOA.
Quy uoc loi (chay.py dua vao do de quyet dinh du phong hop thu):
  LoiDang(khong_ro=False) = CHAC CHAN chua co bai tren TikTok  -> duoc du phong hop thu.
  LoiDang(khong_ro=True)  = co the da dang / khong biet        -> KHONG du phong, KHONG dang lai.
Khoa Zernio va uploadUrl ky san duoc dang ky bi mat (chung.dang_ky_bi_mat) -> khong bao gio vao log / ngoai le.
# CHUA KIEM tren Zernio that: hinh dang JSON cua GET /accounts va creator-info (code doc kieu khoan dung); luong 200/207/409 theo tai lieu.
"""
import hashlib
import os

from . import chung, http

GOC = "https://zernio.com/api/v1"
ACC_MAC_DINH = "6acc93a0743f186282aa42e5"
USERNAME = "sangame.com.vn"
PUBLIC = "PUBLIC_TO_EVERYONE"
THU_TAO_BAI = 3
NHIP_HOI = 15
SO_LAN_HOI = 40          # 40 x 15 s = 10 phut
DANG_CHO = ("pending", "processing", "publishing", "scheduled", "queued", "uploading")


def co_khoa():
    return bool(os.environ.get("ZERNIO_KHOA", "").strip())


def _acc():
    return os.environ.get("ZERNIO_TIKTOK_ACC", "").strip() or ACC_MAC_DINH


def _hdr(khoa, **them):
    h = {"Authorization": "Bearer " + khoa}
    h.update(them)
    return h


def _chua(ly_do):
    return chung.LoiDang(f"Zernio: {ly_do} (chua tao bai)")


def _goi(method, url, khoa, ly_do, **kw):
    """Goi truoc khi tao bai: loi mang -> 'chua tao bai'."""
    kw.setdefault("timeout", 60)
    try:
        return http.gui(method, url, headers=_hdr(khoa), **kw)
    except http.LoiMang as e:
        raise _chua(f"{ly_do}: {e}") from None


def _lay(j, khoa_tim):
    """Tim khoa_tim trong dict j, roi trong cac dict con cap 1 (creator, creatorInfo, data...)."""
    if not isinstance(j, dict):
        return None
    if khoa_tim in j:
        return j[khoa_tim]
    for v in j.values():
        if isinstance(v, dict) and khoa_tim in v:
            return v[khoa_tim]
    return None


def kiem_truoc(khoa, acc):
    """Tai khoan dung + dang hoat dong + creator-info co PUBLIC va canPostMore. Sai -> 'chua tao bai'."""
    r = _goi("GET", f"{GOC}/accounts", khoa, "doc danh sach tai khoan")
    if r.status != 200:
        raise _chua(f"GET /accounts HTTP {r.status}")
    j = r.json()
    ds = j if isinstance(j, list) else (j.get("accounts") or j.get("data") or [])
    mot = next((a for a in ds if isinstance(a, dict) and str(a.get("_id") or a.get("id")) == acc), None)
    if not mot:
        raise _chua(f"khong thay tai khoan {acc}")
    if str(mot.get("platform")) != "tiktok" or str(mot.get("username")) != USERNAME or mot.get("isActive") is not True:
        raise _chua("tai khoan khong phai TikTok sangame.com.vn hoac khong active")
    r = _goi("GET", f"{GOC}/accounts/{acc}/tiktok/creator-info", khoa, "creator-info", params={"mediaType": "video"})
    if r.status != 200:
        raise _chua(f"creator-info HTTP {r.status}")
    ci = r.json()
    # API that (doc 12/10): privacyLevels = [{"value": "PUBLIC_TO_EVERYONE", "label": ...}] - chap nhan ca chuoi tron
    muc = [x.get("value") if isinstance(x, dict) else x for x in (_lay(ci, "privacyLevels") or [])]
    if PUBLIC not in muc:
        raise _chua("creator-info khong cho phep PUBLIC_TO_EVERYONE")
    if _lay(ci, "canPostMore") is not True:
        raise _chua("creator-info bao canPostMore khong true")


def tai_video(khoa, nc):
    du_lieu = nc.tep("tiktok").read_bytes()
    ten = f"sangame-{nc.ngay}-{nc.dang}-tiktok.mp4"
    try:
        r = http.gui("POST", f"{GOC}/media/presign", headers=_hdr(khoa), timeout=60,
                     json_body={"filename": ten, "contentType": "video/mp4", "size": len(du_lieu)})
    except http.LoiMang as e:
        raise _chua(f"presign: {e}") from None
    j = r.json()
    if r.status not in (200, 201) or not j.get("uploadUrl") or not j.get("publicUrl"):
        raise _chua(f"presign HTTP {r.status}")
    chung.dang_ky_bi_mat(j["uploadUrl"])
    try:
        u = http.gui("PUT", j["uploadUrl"], data=du_lieu, headers={"Content-Type": "video/mp4"}, timeout=600)
    except http.LoiMang as e:
        raise _chua(f"PUT video: {e}") from None
    if u.status != 200:
        raise _chua(f"PUT video HTTP {u.status}")
    return j["publicUrl"]


def khoa_lap(nc):
    return hashlib.sha256(f"sangame|{nc.ngay}|{nc.dang}|{nc.manifest_sha}|tiktok".encode()).hexdigest()


def _ket_qua(post):
    pl = (post.get("platforms") or [{}])[0] if isinstance(post.get("platforms"), list) else {}
    pid = str(post.get("_id") or post.get("id") or "")
    return {"id_tai": pid, "id_bai": pid, "link": pl.get("platformPostUrl"), "kieu": "zernio"}


def _xet(post, ma):
    """-> ('xong', ket) | ('cho', None); raise LoiDang neu failed / khong ro."""
    st = str(post.get("status") or "").lower()
    if st == "published":
        return "xong", _ket_qua(post)
    if st == "failed":
        raise chung.LoiDang(f"Zernio: bai that bai, khong nen tang nao dang (HTTP {ma}) - chua len TikTok")
    if st in DANG_CHO:
        return "cho", None
    raise chung.LoiDang(f"Zernio: trang thai bai '{st}' (HTTP {ma}) - khong ro da dang chua", khong_ro=True)


def tao_bai(khoa, nc, acc, url_video):
    body = {"content": nc.caption_tiktok(), "mediaItems": [{"type": "video", "url": url_video}],
            "platforms": [{"platform": "tiktok", "accountId": acc}],
            "tiktokSettings": {"privacy_level": PUBLIC, "allow_comment": True, "allow_duet": True, "allow_stitch": True,
                               "content_preview_confirmed": True, "express_consent_given": True},
            "publishNow": True}
    hdr = _hdr(khoa, **{"Idempotency-Key": khoa_lap(nc)})
    r, loi_cuoi = None, ""
    for lan in range(THU_TAO_BAI):
        try:
            r = http.gui("POST", f"{GOC}/posts", headers=hdr, json_body=body, timeout=120)
        except http.LoiMang as e:
            r, loi_cuoi = None, str(e)
        else:
            if r.status < 500:
                break
            loi_cuoi = f"HTTP {r.status}"
            r = None
        if lan < THU_TAO_BAI - 1:
            chung.ngu(5)
    if r is None:
        raise chung.LoiDang(f"Zernio: tao bai loi {THU_TAO_BAI} lan ({loi_cuoi}) - khong ro da tao chua", khong_ro=True)
    j = r.json()
    if r.status == 409:
        raise chung.LoiDang(f"Zernio: 409 trung bai/idempotency (existingPostId={j.get('existingPostId')}) - co the da dang", khong_ro=True)
    if 400 <= r.status < 500:
        raise _chua(f"tao bai HTTP {r.status} {chung.cat(j.get('error') or j.get('message') or '', 120)}")
    if r.status not in (200, 201, 207):
        raise chung.LoiDang(f"Zernio: tao bai HTTP {r.status} la - khong ro", khong_ro=True)
    post = j.get("post") if isinstance(j.get("post"), dict) else j
    if not (post.get("_id") or post.get("id")):
        raise chung.LoiDang(f"Zernio: HTTP {r.status} khong tra id bai - khong ro", khong_ro=True)
    return post, r.status


def hoi_den_xong(khoa, post_id):
    """Hoi GET /posts/{id} moi 15 s, toi da 10 phut."""
    for _ in range(SO_LAN_HOI):
        chung.ngu(NHIP_HOI)
        try:
            r = http.gui("GET", f"{GOC}/posts/{post_id}", headers=_hdr(khoa), timeout=30)
        except http.LoiMang:
            continue
        if r.status != 200:
            continue
        j = r.json()
        post = j.get("post") if isinstance(j.get("post"), dict) else j
        kq, ket = _xet(post, r.status)
        if kq == "xong":
            return ket
    raise chung.LoiDang(f"Zernio: het 10 phut cho bai {post_id} van chua published - khong ro", khong_ro=True)


def lay_link(khoa, post_id):
    """GET /posts/{id} -> platformPostUrl khi bai da published, nguoc lai None. KHONG nem (dung de bu link cho so)."""
    try:
        r = http.gui("GET", f"{GOC}/posts/{post_id}", headers=_hdr(khoa), timeout=30)
        if r.status != 200:
            return None
        j = r.json()
        post = j.get("post") if isinstance(j.get("post"), dict) else j
        if str(post.get("status") or "").lower() != "published":
            return None
        return _ket_qua(post).get("link") or None
    except Exception:
        return None


def cong_khai(nc):
    """Dang cong khai len TikTok. Tra {"id_tai","id_bai","link","kieu"}. Xem quy uoc loi o dau file."""
    khoa = os.environ.get("ZERNIO_KHOA", "").strip()
    if not khoa:
        raise _chua("thieu ZERNIO_KHOA")
    chung.dang_ky_bi_mat(khoa)
    acc = _acc()
    kiem_truoc(khoa, acc)
    url_video = tai_video(khoa, nc)
    post, ma = tao_bai(khoa, nc, acc, url_video)
    # Tu day bai CO THE da len TikTok: moi loi la khong_ro tru khi Zernio noi ro 'failed'.
    if ma == 207 and str(post.get("status") or "").lower() != "failed":
        raise chung.LoiDang(f"Zernio: HTTP 207 trang thai '{post.get('status')}' - khong ro da dang chua", khong_ro=True)
    kq, ket = _xet(post, ma)
    if kq == "xong":
        return ket
    return hoi_den_xong(khoa, str(post.get("_id") or post.get("id")))
