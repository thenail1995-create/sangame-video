"""Instagram Reels qua Content Publishing API (Graph v26.0, cung phien ban voi fb.py).
Container REELS: video_url + cover_url PHAI la URL cong khai truc tiep (GitHub Pages, khong chuyen huong).
Chi media_publish o pha cong_khai cua che_do=that.
Nhan AI: is_ai_generated dat khi tao container. Meta tu choi nhan -> LOI, KHONG tao lai container khong nhan (luat Hao 27/10).
# CHUA KIEM: cover_url va share_to_feed tren REELS - https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/content-publishing
"""
from . import chung, meta, ntfy

G = "https://graph.facebook.com/v26.0"


def danh_tinh(tk, nc=None):
    r = meta.goi(G, "GET", f"/{tk['ig_user_id']}", token=tk["page_token"], tham_so={"fields": "id,username"})
    if str(r.get("id")) != str(tk["ig_user_id"]):
        raise chung.LoiDang("IG tra id khac ig_user_id da luu")
    return str(r.get("id"))


def _status(tk, container):
    return meta.goi(G, "GET", f"/{container}", token=tk["page_token"], tham_so={"fields": "status_code"}).get("status_code")


def tham_container(video_url, cover_url, caption):
    """Tham so container REELS. cover_url co the None (script dang tay khong co bia). Nhan AI khi CO_GIONG_AI.
    Thuan, khong goi mang - dung chung voi bo dang tay (dang/ngan.py)."""
    tham = {"media_type": "REELS", "video_url": video_url, "caption": caption, "share_to_feed": "true"}
    if cover_url:
        tham["cover_url"] = cover_url
    if chung.CO_GIONG_AI:
        tham["is_ai_generated"] = "true"   # Meta changelog 22/06/2026: dat khi tao container
    return tham


def tao_container(tk, tham):
    """POST /media. Meta TU CHOI nhan AI (400 + nhac is_ai_generated) -> LoiDang chac chan chua tao container + ntfy;
    KHONG tao lai khong nhan. Loi quyen/mang/khac nem nhu cu."""
    try:
        return meta.goi(G, "POST", f"/{tk['ig_user_id']}/media", token=tk["page_token"], tham_so=tham)
    except chung.LoiDang as e:
        if chung.CO_GIONG_AI and e.ma_http == 400 and "is_ai_generated" in (e.thong_diep or "").lower():
            ntfy.loi("IG từ chối nhãn AI — chưa đăng", f"Meta từ chối is_ai_generated khi tạo container; KHÔNG tạo lại không nhãn: {e}", uu_tien=4)
            raise chung.LoiDang(f"IG tu choi nhan AI (is_ai_generated), chua tao container: {e}", ma_http=400, thong_diep=e.thong_diep) from None
        raise


def chuan_bi(tk, nc, luu):
    if not nc.url_video or not nc.url_bia:
        raise chung.LoiDang("thieu URL cong khai cua video/bia (GitHub Pages)")
    c = tao_container(tk, tham_container(nc.url_video, nc.url_bia, nc.caption_ig(2200)))
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
