"""Goi Graph API (FB / IG / Threads) va doi ket qua thanh LoiDang.

co_tac_dung=True: loi mang / HTTP 5xx / loi tam thoi cua Graph -> khong_ro (khong chac da xay ra hay chua)."""
from . import chung, http


def goi(base, method, duong, *, token=None, tham_so=None, co_tac_dung=False, timeout=60):
    tham = dict(tham_so or {})
    if token:
        tham["access_token"] = token
    kw = {"params": tham} if method == "GET" else {"form": tham}
    try:
        r = http.gui(method, base + duong, timeout=timeout, **kw)
    except http.LoiMang as e:
        raise chung.LoiDang(str(e), khong_ro=co_tac_dung) from None
    j = r.json()
    if r.status >= 500 or (not j and r.status >= 300):
        raise chung.LoiDang(f"{method} {duong}: HTTP {r.status}", khong_ro=co_tac_dung, ma_http=r.status)
    if isinstance(j, dict) and "error" in j:
        e = j["error"] if isinstance(j["error"], dict) else {"message": j["error"]}
        tam_thoi = bool(e.get("is_transient")) or e.get("code") in (1, 2)
        raise chung.LoiDang(f"{method} {duong}: {e.get('message')} (code {e.get('code')})",
                            khong_ro=co_tac_dung and tam_thoi, ma_http=r.status, thong_diep=str(e.get("message") or ""))
    return j


def cho_trang_thai(doc, tot, xau, *, toi_da=60, nhip=lambda i: min(2 + 2 * i, 15), ten="container"):
    """Hoi lai den khi doc() tra gia tri thuoc tot (-> True) hoac xau (-> LoiDang). Het luot -> LoiDang."""
    cuoi = None
    for i in range(toi_da):
        cuoi = doc()
        if cuoi in tot:
            return cuoi
        if cuoi in xau:
            raise chung.LoiDang(f"{ten} loi trang thai {cuoi}")
        chung.ngu(nhip(i))
    raise chung.LoiDang(f"{ten} het gio cho (trang thai cuoi: {cuoi})")
