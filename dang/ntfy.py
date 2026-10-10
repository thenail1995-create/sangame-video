"""Thong bao ntfy. Kenh tu env: NTFY_TIN (tin dang xong), NTFY_BAO_LOI (loi). Gia tri la ten topic hoac URL day du.
Gui bang JSON publish de tieng Viet khong bi hong header. Loi gui KHONG lam hong luong dang."""
import os
import urllib.parse

from . import chung, http


def _dich(gia_tri):
    if not gia_tri:
        return None
    if gia_tri.startswith(("http://", "https://")):
        p = urllib.parse.urlsplit(gia_tri)
        topic = p.path.rstrip("/").rsplit("/", 1)[-1]
        goc = f"{p.scheme}://{p.netloc}" + p.path.rstrip("/").rsplit("/", 1)[0]
        return goc.rstrip("/") + "/", topic
    return "https://ntfy.sh/", gia_tri.strip("/")


def gui(bien_env, tieu_de, noi_dung, *, uu_tien=3, tags=(), click=None):
    dich = _dich(os.environ.get(bien_env, ""))
    if not dich:
        chung.log_loi(f"ntfy: thieu env {bien_env}, bo qua: {tieu_de}")
        return False
    goc, topic = dich
    chung.dang_ky_bi_mat(topic)
    body = {"topic": topic, "title": chung.che(tieu_de), "message": chung.che(noi_dung)[:3500],
            "priority": uu_tien, "tags": list(tags)}
    if click:
        body["click"] = click
    try:
        r = http.gui("POST", goc, json_body=body, timeout=20)
        if r.status >= 300:
            chung.log_loi(f"ntfy {bien_env}: HTTP {r.status}")
            return False
        return True
    except http.LoiMang as e:
        chung.log_loi(f"ntfy {bien_env}: {e}")
        return False


def tin(tieu_de, noi_dung, **kw):
    return gui("NTFY_TIN", tieu_de, noi_dung, **kw)


def loi(tieu_de, noi_dung, **kw):
    kw.setdefault("uu_tien", 4)
    kw.setdefault("tags", ("warning",))
    return gui("NTFY_BAO_LOI", tieu_de, noi_dung, **kw)
