"""Facebook Page Reels. Phien ban Graph lay dung theo ban da chay that: The Nail dang-bai/xu-ly.ts (v26.0).
Luong: start -> rupload nhi phan (header offset/file_size) -> cho upload xong -> finish -> dat bia /thumbnails.
  che_do=thu : chuan_bi lam het toi finish video_state=DRAFT + bia (khong cong khai).
  che_do=that: chuan_bi dung o 'upload xong'; cong_khai moi finish PUBLISHED + bia.
# CHUA KIEM: finish PUBLISHED sau 25 phut ke tu start (phien upload con song khong?) - ban Nail luon finish ngay sau upload.
#   Tai lieu: https://developers.facebook.com/docs/video-api/guides/reels-publishing
"""
from . import chung, http, meta

G = "https://graph.facebook.com/v26.0"
RUPLOAD = "https://rupload.facebook.com/video-upload/v26.0"
BIA_TOI_DA = 10 * 1024 * 1024


def danh_tinh(tk, nc=None):
    me = meta.goi(G, "GET", "/me", token=tk["page_token"], tham_so={"fields": "id"})
    if tk.get("page_id") and str(me.get("id")) != str(tk["page_id"]):
        raise chung.LoiDang("token FB khong thuoc page_id da luu")
    return str(me.get("id"))


def _upload(tk, video_id, du_lieu):
    try:
        r = http.gui("POST", f"{RUPLOAD}/{video_id}", timeout=600, data=du_lieu,
                     headers={"Authorization": f"OAuth {tk['page_token']}", "offset": "0",
                              "file_size": str(len(du_lieu)), "Content-Type": "application/octet-stream"})
    except http.LoiMang as e:
        raise chung.LoiDang(f"rupload FB: {e}") from None
    if r.status != 200 or r.json().get("success") is not True:
        raise chung.LoiDang(f"rupload FB that bai: HTTP {r.status} {str(r.json())[:200]}")


def _trang_thai(tk, video_id):
    s = meta.goi(G, "GET", f"/{video_id}", token=tk["page_token"], tham_so={"fields": "status"}).get("status") or {}
    up = (s.get("uploading_phase") or {}).get("status")
    vs = s.get("video_status")
    if vs == "error":
        return "error"
    if up == "complete" or vs in ("upload_complete", "processing", "ready"):
        return "xong"
    return "dang"


def _dat_bia(tk, video_id, duong_bia):
    """Loi dat bia KHONG lam hong bai da dang: tra (ok, ly_do)."""
    du_lieu = __import__("pathlib").Path(duong_bia).read_bytes()
    if not du_lieu or len(du_lieu) > BIA_TOI_DA:
        return False, "bia rong hoac > 10 MB"
    mime = "image/png" if str(duong_bia).endswith(".png") else "image/jpeg"
    cho = [3, 5, 8]
    cuoi = ""
    for lan in range(len(cho) + 1):
        try:
            r = http.gui("POST", f"{G}/{video_id}/thumbnails", timeout=60, files={"source": ("bia.jpg", du_lieu, mime)},
                         form={"is_preferred": "true", "access_token": tk["page_token"]})
        except http.LoiMang as e:
            return False, str(e)
        j = r.json()
        if j.get("success") is True or j.get("id"):
            return True, ""
        e = j.get("error") or {}
        cuoi = f"{e.get('message')} (code {e.get('code')})"
        tam = e.get("is_transient") is True or any(t in str(e.get("message", "")).lower()
                                                  for t in ("process", "not ready", "try again", "not available yet"))
        if not tam or lan >= len(cho):
            break
        chung.ngu(cho[lan])
    return False, cuoi


def _finish(tk, page_id, video_id, mo_ta, cong_khai):
    return meta.goi(G, "POST", f"/{page_id}/video_reels", token=tk["page_token"], co_tac_dung=True, timeout=120,
                    tham_so={"upload_phase": "finish", "video_id": video_id,
                             "video_state": "PUBLISHED" if cong_khai else "DRAFT", "description": mo_ta})


def chuan_bi(tk, nc, luu):
    page = danh_tinh(tk)
    st = meta.goi(G, "POST", f"/{page}/video_reels", token=tk["page_token"], tham_so={"upload_phase": "start"})
    video_id = str(st.get("video_id") or "")
    if not video_id:
        raise chung.LoiDang("FB start khong tra video_id")
    luu(id_tai=video_id)
    _upload(tk, video_id, nc.tep("reels").read_bytes())
    meta.cho_trang_thai(lambda: _trang_thai(tk, video_id), {"xong"}, {"error"}, toi_da=40, ten="FB upload")
    ket = {"id_tai": video_id}
    if nc.che_do == "thu":
        f = _finish(tk, page, video_id, nc.caption_dai(), False)
        if f.get("success") is not True:
            raise chung.LoiDang("FB finish DRAFT khong thanh cong")
        ok, ly_do = _dat_bia(tk, video_id, nc.tep("reels", "bia"))
        ket["bia"] = ok if ok else f"loi: {ly_do}"
    return ket


def _da_cong_khai(tk, video_id):
    s = meta.goi(G, "GET", f"/{video_id}", token=tk["page_token"], tham_so={"fields": "status,published"})
    return s.get("published") is True or ((s.get("status") or {}).get("publishing_phase") or {}).get("status") == "complete"


def cong_khai(tk, nc, dong):
    """Chi goi khi che_do=that."""
    video_id = str(dong.get("id_tai") or "")
    if not video_id:
        raise chung.LoiDang("sg_dang khong co id_tai cho FB")
    page = danh_tinh(tk)
    try:
        f = _finish(tk, page, video_id, nc.caption_dai(), True)
        ok = f.get("success") is True
    except chung.LoiDang as e:
        if not e.khong_ro:
            raise
        # Khong chac: hoi lai 1 lan (chi doc). Da dang -> coi nhu xong; con lai -> khong_ro, KHONG dang lai.
        try:
            ok = _da_cong_khai(tk, video_id)
        except chung.LoiDang:
            ok = False
        if not ok:
            raise
    if not ok:
        raise chung.LoiDang("FB finish PUBLISHED khong tra success", khong_ro=True)
    bia_ok, bia_ly_do = _dat_bia(tk, video_id, nc.tep("reels", "bia"))
    ket = {"id_bai": video_id, "link": f"https://www.facebook.com/reel/{video_id}/"}
    if not bia_ok:
        ket["canh_bao"] = f"bia FB khong dat duoc: {bia_ly_do}"
    return ket
