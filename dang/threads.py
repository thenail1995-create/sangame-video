"""Threads: container VIDEO + video_url cong khai (GitHub Pages), cho FINISHED, threads_publish o pha cong khai.
Rang buoc video (tai lieu): MP4 moov o dau, H.264 4:2:0, AAC <= 48 kHz, 23-60 fps, <= 300 s - do khuon dung kiem.
# CHUA KIEM: truong status / PUBLISHED va permalink cua container Threads - https://developers.facebook.com/docs/threads/posts
"""
from . import chung, meta

TH = "https://graph.threads.net/v1.0"


def danh_tinh(tk, nc=None):
    r = meta.goi(TH, "GET", "/me", token=tk["token"], tham_so={"fields": "id,username"})
    if tk.get("threads_user_id") and str(r.get("id")) != str(tk["threads_user_id"]):
        raise chung.LoiDang("Threads /me tra id khac threads_user_id da luu")
    return str(r.get("id"))


def _status(tk, cid):
    return meta.goi(TH, "GET", f"/{cid}", token=tk["token"], tham_so={"fields": "status,error_message"}).get("status")


def chuan_bi(tk, nc, luu):
    if not nc.url_video:
        raise chung.LoiDang("thieu URL cong khai cua video (GitHub Pages)")
    c = meta.goi(TH, "POST", f"/{tk['threads_user_id']}/threads", token=tk["token"],
                 tham_so={"media_type": "VIDEO", "video_url": nc.url_video, "text": nc.text_ngan(500)})
    cid = str(c.get("id") or "")
    if not cid:
        raise chung.LoiDang("Threads khong tra container id")
    luu(id_container=cid)
    meta.cho_trang_thai(lambda: _status(tk, cid), {"FINISHED"}, {"ERROR", "EXPIRED"}, toi_da=80, ten="Threads container")
    return {"id_container": cid}


def cong_khai(tk, nc, dong):
    cid = str(dong.get("id_container") or "")
    if not cid:
        raise chung.LoiDang("sg_dang khong co id_container cho Threads")
    if _status(tk, cid) != "FINISHED":
        raise chung.LoiDang("Threads container khong con o trang thai FINISHED")
    try:
        p = meta.goi(TH, "POST", f"/{tk['threads_user_id']}/threads_publish", token=tk["token"], co_tac_dung=True,
                     timeout=120, tham_so={"creation_id": cid})
        mid = str(p.get("id") or "")
        if not mid:
            raise chung.LoiDang("Threads threads_publish khong tra id", khong_ro=True)
    except chung.LoiDang as e:
        if not e.khong_ro:
            raise
        try:
            da = _status(tk, cid) == "PUBLISHED"
        except chung.LoiDang:
            da = False
        if da:
            return {"id_bai": None, "link": None, "canh_bao": "Threads da PUBLISHED nhung khong lay duoc id bai"}
        raise
    link = None
    try:
        link = meta.goi(TH, "GET", f"/{mid}", token=tk["token"], tham_so={"fields": "permalink"}).get("permalink")
    except chung.LoiDang:
        pass
    return {"id_bai": mid, "link": link}


def gia_han(tk, bay_gio):
    """GET /refresh_access_token (grant_type=th_refresh_token). Tra (token_moi, giay_het_han). Goi khi token >= 24 h tuoi."""
    j = meta.goi("https://graph.threads.net", "GET", "/refresh_access_token", co_tac_dung=False,
                 tham_so={"grant_type": "th_refresh_token", "access_token": tk["token"]})
    if not j.get("access_token"):
        raise chung.LoiDang("Threads refresh khong tra access_token")
    return j["access_token"], int(j.get("expires_in") or 0)
