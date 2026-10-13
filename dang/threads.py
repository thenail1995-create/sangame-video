"""Threads: container VIDEO + video_url cong khai (GitHub Pages), cho FINISHED, threads_publish o pha cong khai.
Rang buoc video (tai lieu): MP4 moov o dau, H.264 4:2:0, AAC <= 48 kHz, 23-60 fps, <= 300 s - do khuon dung kiem.
# CHUA KIEM: truong status / PUBLISHED va permalink cua container Threads - https://developers.facebook.com/docs/threads/posts
"""
import json

from . import chung, meta

TH = "https://graph.threads.net/v1.0"
POLL_KHOA = ("option_a", "option_b", "option_c", "option_d")
POLL_TOI_DA_KY_TU = 25   # tai lieu poll chinh chu: moi lua chon 1-25 ky tu, 2-4 lua chon (option_a, option_b bat buoc)


def kiem_poll(poll):
    """Kiem dict poll {option_a..option_d} theo tai lieu Threads (developers.facebook.com/documentation/threads/create-posts/polls):
    2-4 lua chon lien tiep tu option_a, moi lua chon la chuoi 1-25 ky tu, khong trung. Sai -> LoiDang. Tra chinh poll."""
    if not isinstance(poll, dict) or not (2 <= len(poll) <= 4):
        raise chung.LoiDang("poll phai la dict 2-4 lua chon option_a..option_d")
    for i, k in enumerate(poll):
        if k != POLL_KHOA[i]:
            raise chung.LoiDang(f"poll sai khoa '{k}': can {', '.join(POLL_KHOA[:len(poll)])} theo thu tu")
    gia_tri = []
    for k, v in poll.items():
        if not isinstance(v, str) or not v.strip() or len(v) > POLL_TOI_DA_KY_TU:
            raise chung.LoiDang(f"poll {k} phai la chuoi 1-{POLL_TOI_DA_KY_TU} ky tu: {v!r}")
        gia_tri.append(v.strip().casefold())
    if len(set(gia_tri)) != len(gia_tri):
        raise chung.LoiDang("poll co lua chon trung nhau")
    return poll


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
    chung.ngu(30)  # tai lieu khuyen cho ~30 giay sau FINISHED truoc khi publish (publish chay sau o pha cong khai)
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


def tao_container_chu(tk, text, anh=None, topic_tag=None, luu=None, poll=None):
    """Bai CHU RIENG (dang/threads_chu.py): container TEXT, hoac IMAGE neu co anh (URL cong khai). -> container id, da cho FINISHED.
    Tham so theo tai lieu chinh chu (doc 12/10/2026) https://developers.facebook.com/docs/threads/posts :
      media_type = TEXT | IMAGE | VIDEO ; text (<= 500 ky tu, dem theo byte UTF-8 cho emoji) ; image_url (bat buoc voi IMAGE, URL cong khai) ;
      topic_tag (1-50 ky tu, khong dau cham / '&'; chi tag hop le dau tien cua bai co tac dung) ; nen cho ~30 giay truoc threads_publish.
    poll (dict option_a..option_d): chi gan duoc vao bai TEXT -> gui `poll_attachment` = JSON string (form khong nhan dict). Co anh + poll = loi.
    Tao container CHUA dang gi len Threads -> loi o day la chac chan chua dang (khong_ro=False)."""
    if poll and anh:
        raise chung.LoiDang("poll chi gan duoc vao bai TEXT, khong kem anh (Threads API)")
    tham = {"media_type": "IMAGE" if anh else "TEXT", "text": text}
    if poll:
        tham["poll_attachment"] = json.dumps(kiem_poll(poll), ensure_ascii=False)
    if anh:
        tham["image_url"] = anh
    if topic_tag:
        tham["topic_tag"] = topic_tag
    c = meta.goi(TH, "POST", f"/{tk['threads_user_id']}/threads", token=tk["token"], tham_so=tham)
    cid = str(c.get("id") or "")
    if not cid:
        raise chung.LoiDang("Threads khong tra container id")
    if luu:
        luu(id_container=cid)
    meta.cho_trang_thai(lambda: _status(tk, cid), {"FINISHED"}, {"ERROR", "EXPIRED"}, toi_da=30, ten="Threads container")
    return cid


def gia_han(tk, bay_gio):
    """GET /refresh_access_token (grant_type=th_refresh_token). Tra (token_moi, giay_het_han). Goi khi token >= 24 h tuoi."""
    j = meta.goi("https://graph.threads.net", "GET", "/refresh_access_token", co_tac_dung=False,
                 tham_so={"grant_type": "th_refresh_token", "access_token": tk["token"]})
    if not j.get("access_token"):
        raise chung.LoiDang("Threads refresh khong tra access_token")
    return j["access_token"], int(j.get("expires_in") or 0)
