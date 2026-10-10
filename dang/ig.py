"""Instagram Reels qua Content Publishing API (Graph v26.0, cung phien ban voi fb.py).
Container REELS: video_url + cover_url PHAI la URL cong khai truc tiep (GitHub Pages, khong chuyen huong).
Chi media_publish o pha cong_khai cua che_do=that.
# CHUA KIEM: cover_url va share_to_feed tren REELS - https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/content-publishing
"""
from . import chung, meta

G = "https://graph.facebook.com/v26.0"


def danh_tinh(tk, nc=None):
    r = meta.goi(G, "GET", f"/{tk['ig_user_id']}", token=tk["page_token"], tham_so={"fields": "id,username"})
    if str(r.get("id")) != str(tk["ig_user_id"]):
        raise chung.LoiDang("IG tra id khac ig_user_id da luu")
    return str(r.get("id"))


def _status(tk, container):
    return meta.goi(G, "GET", f"/{container}", token=tk["page_token"], tham_so={"fields": "status_code"}).get("status_code")


def chuan_bi(tk, nc, luu):
    if not nc.url_video or not nc.url_bia:
        raise chung.LoiDang("thieu URL cong khai cua video/bia (GitHub Pages)")
    c = meta.goi(G, "POST", f"/{tk['ig_user_id']}/media", token=tk["page_token"],
                 tham_so={"media_type": "REELS", "video_url": nc.url_video, "cover_url": nc.url_bia,
                          "caption": nc.caption_dai(2200), "share_to_feed": "true"})
    cid = str(c.get("id") or "")
    if not cid:
        raise chung.LoiDang("IG khong tra container id")
    luu(id_container=cid)
    meta.cho_trang_thai(lambda: _status(tk, cid), {"FINISHED"}, {"ERROR", "EXPIRED"}, toi_da=80, ten="IG container")
    return {"id_container": cid}


def cong_khai(tk, nc, dong):
    cid = str(dong.get("id_container") or "")
    if not cid:
        raise chung.LoiDang("sg_dang khong co id_container cho IG")
    if _status(tk, cid) != "FINISHED":
        raise chung.LoiDang("IG container khong con o trang thai FINISHED")
    try:
        p = meta.goi(G, "POST", f"/{tk['ig_user_id']}/media_publish", token=tk["page_token"], co_tac_dung=True,
                     timeout=120, tham_so={"creation_id": cid})
        mid = str(p.get("id") or "")
        if not mid:
            raise chung.LoiDang("IG media_publish khong tra id", khong_ro=True)
    except chung.LoiDang as e:
        if not e.khong_ro:
            raise
        try:
            da = _status(tk, cid) == "PUBLISHED"
        except chung.LoiDang:
            da = False
        if da:
            return {"id_bai": None, "link": None, "canh_bao": "IG da PUBLISHED nhung khong lay duoc id bai"}
        raise
    link = None
    try:
        link = meta.goi(G, "GET", f"/{mid}", token=tk["page_token"], tham_so={"fields": "permalink"}).get("permalink")
    except chung.LoiDang:
        pass
    return {"id_bai": mid, "link": link}
