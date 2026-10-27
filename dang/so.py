"""Client cong sg-cong (HOP-DONG.md muc 3). Khoa doc tu env SG_CONG_KHOA, khong bao gio in ra."""
import os

from . import chung, http

URL = "https://qkpbokksubmqvinetdtv.supabase.co/functions/v1/sg-cong"


class LoiCong(Exception):
    pass


class Cong:
    def __init__(self, khoa=None, url=URL):
        self.khoa = khoa if khoa is not None else os.environ.get("SG_CONG_KHOA", "")
        if not self.khoa:
            raise LoiCong("thieu env SG_CONG_KHOA")
        chung.dang_ky_bi_mat(self.khoa)
        self.url = url

    def goi(self, viec, *, lap_lai=True, **tham_so):
        """lap_lai=False cho viec KHONG luy dang (giu_dang): mat phan hoi thi bao loi, khong goi lai."""
        so_lan = 3 if lap_lai else 1
        loi_cuoi = "?"
        for lan in range(so_lan):
            try:
                r = http.gui("POST", self.url, headers={"x-sg-khoa": self.khoa}, json_body={"viec": viec, **tham_so},
                             timeout=30)
            except http.LoiMang as e:
                loi_cuoi = str(e)
            else:
                if r.status >= 500:
                    loi_cuoi = f"HTTP {r.status}"
                else:
                    j = r.json()
                    if r.status != 200 or not isinstance(j, dict) or j.get("ok") is not True:
                        raise LoiCong(chung.cat(f"cong {viec}: HTTP {r.status} {j}", 300))
                    return j
            if lan + 1 < so_lan:
                chung.ngu(2 * (lan + 1))
        raise LoiCong(chung.che(f"cong {viec}: {loi_cuoi}"))

    # --- sg_dang ---
    def giu_dang(self, ngay, dang, kenh, che_do, gio_du_kien=None, manifest_sha=None) -> bool:
        j = self.goi("giu_dang", lap_lai=False, ngay=ngay, dang=dang, kenh=kenh, che_do=che_do,
                     gio_du_kien=gio_du_kien, manifest_sha=manifest_sha)
        return j.get("giu_duoc") is True

    def cap_nhat_dang(self, ngay, dang, kenh, che_do, neu_trang_thai=None, **truong) -> int:
        """neu_trang_thai: so-va-dat nguyen tu (cong v2) - chi sua khi trang thai hien tai dung gia tri do; tra so_dong (0 = luot
        khac da doi, KHONG nem loi). Khong co neu_trang_thai thi 0 dong la loi."""
        if neu_trang_thai is not None:
            truong["neu_trang_thai"] = neu_trang_thai
        j = self.goi("cap_nhat_dang", ngay=ngay, dang=dang, kenh=kenh, che_do=che_do, **truong)
        so = int(j.get("so_dong", 0))
        if neu_trang_thai is not None:
            return so
        if so < 1:
            raise LoiCong(f"cap_nhat_dang {dang}/{kenh}: khong co dong nao duoc cap nhat")
        return so

    def doc_dang(self, tu, den=None, che_do=None) -> list:
        tham = {"tu": tu, "den": den or tu}
        if che_do:
            tham["che_do"] = che_do
        return self.goi("doc_dang", **tham).get("dong") or []

    # --- sg_keo (bang keo san deal, cong v11) ---
    def doc_keo(self, ngay) -> list:
        """Cac hang PS (nen_tang='ps') cua sg_keo ngay `ngay`, da sap theo hang (chi cac cot cong cho phep, toi da 50 dong)."""
        return self.goi("doc_keo", ngay=ngay).get("dong") or []

    def doc_so_lieu_x(self) -> list:
        """id_bai cac bai X da co dong trong sg_so_lieu (cong v11, toi da 500) - do_x dung de khong do trung."""
        return [str(i) for i in (self.goi("doc_so_lieu_x").get("id_bai") or [])]

    # --- sg_token ---
    def doc_token(self, kenh):
        """Tra {"du_lieu":…, "het_han":…, "cap_nhat":…} hoac None neu chua nap."""
        return self.goi("doc_token", kenh=kenh).get("token")

    def ghi_token(self, kenh, du_lieu, het_han=None):
        self.goi("ghi_token", kenh=kenh, du_lieu=du_lieu, het_han=het_han)
