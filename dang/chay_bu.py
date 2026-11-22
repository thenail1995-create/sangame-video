"""Chay bu San Game khi Mac bat muon: Mac bat gio nao thi dung + dang gio do (uu tien Top 5, kem X goc + Tin gia MXH).

  python -m dang.chay_bu [--ngay YYYY-MM-DD] [--du-lieu du-lieu] [--kho-chay]

Nguyen tac:
  - `quyet_dinh(trang_thai, bay_gio) -> list[Viec]` la ham THUAN (khong mang, khong dong ho that).
  - Chi xet NGAY HOM NAY (gio VN). Khong lam truoc moc lich thuong (Top 5: 10:50 dung, 11:35 dang; X goc: 10:00/20:00; Threads: 11:30).
  - Khong dang sau 22:00 gio VN (gio bu > 22:00 -> bo ngay + ntfy).
  - Top 5 chua co Release: chi mo lai khung `bo` khi MOI dong `bo` deu do thieu Release / chua co du lieu moi (so-va-dat neu_trang_thai='bo').
  - Moi ngay moi dang toi da 1 lan dung bu va 1 lan dang bu; hong thi ntfy, khong thu lai vong tron.
"""
import argparse
from dataclasses import dataclass, field
import datetime as dt
import importlib.util
import os
import pathlib
import re
import sys

from . import chay as dieu_phoi, chung, http, manifest, ngan, ntfy, so, tin_gia_chon, tin_gia_mxh, x_goc, zernio

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT_KIEM_MOI = REPO_ROOT / "cong-cu" / "kiem_do_moi.py"
MOC_DUNG_TOP5 = (10, 50)
MOC_DANG_TOP5 = (11, 35)
GIO_TOI_DA_BU = (22, 0)
PHUT_BU_TOP5 = 30
PHUT_BU_TIN_GIA = 30
PHUT_BU_X_GOC = 20
CHO_TIKTOK_TOI_DA_PHUT = 60


class LoiChayBu(Exception):
    pass


@dataclass(frozen=True)
class Viec:
    loai: str                       # mo_khung | dung_bu | dang_bu_top5 | dang_bu_x_goc | dang_bu_tin_gia | bo_ngay
    dang: str                       # top5 | x-goc | threads-gia | fb-gia | ig-gia
    workflow: str = ""              # dung.yml | dang.yml | x-goc.yml | tin-gia-mxh.yml
    inputs: dict = field(default_factory=dict)
    gio_bu: str = ""                # HH:MM gio VN
    kenh_ds: tuple[str, ...] = ()   # cho mo_khung: cac kenh dang 'bo' can doi sang 'that_bai'
    ly_do: str = ""


@dataclass
class TrangThai:
    ngay: str
    du_lieu_moi: bool = False
    co_keo_ps: bool = False
    co_release_top5: bool = False
    sg_dang: list[dict] = field(default_factory=list)
    dung_top5_dang_chay: bool = False
    so_lan_dung_bu_top5: int = 0
    dang_top5_dang_chay: bool = False
    so_lan_dang_bu_top5: int = 0
    sg_dang_bat: str = "top5"
    sg_kenh_bat: str = "top5:youtube,threads-gia:threads"
    x_goc_bat: bool = False
    x_goc_ngay_1: str = ""
    x_goc_dang_chay: bool = False
    x_goc_thieu_keo: bool | None = None
    so_lan_bu_x_goc: int = 0
    tin_gia_dang_chay: bool = False
    tin_gia_thieu_keo: dict[str, bool] = field(default_factory=dict)
    so_lan_bu_tin_gia: dict[str, int] = field(default_factory=dict)
    gio_tiktok: list[dt.datetime] = field(default_factory=list)
    da_bao: set[str] = field(default_factory=set)


# ---------------------------------------------------------------- tien ich thuan
def _sang_vn(t: dt.datetime) -> dt.datetime:
    return t.replace(tzinfo=chung.VN) if t.tzinfo is None else t.astimezone(chung.VN)


def _moc_vn(ngay: str, gio: int, phut: int = 0) -> dt.datetime:
    d = dt.date.fromisoformat(ngay)
    return dt.datetime(d.year, d.month, d.day, gio, phut, tzinfo=chung.VN)


def _moc_tu_hhmm(ngay: str, hhmm: str) -> dt.datetime:
    h, m = (int(p) for p in hhmm.split(":"))
    return _moc_vn(ngay, h, m)


def _nhan_gio(t_vn: dt.datetime, ngay: str) -> str:
    return f"{t_vn:%H:%M}" if t_vn.date().isoformat() == ngay else f"{t_vn:%Y-%m-%d %H:%M}"


def tinh_gio_bu(bay_gio_vn: dt.datetime, phut_cong: int = PHUT_BU_TOP5) -> dt.datetime:
    """bay_gio_vn + phut_cong, lam tron LEN boi 5 phut (ceiling)."""
    v = _sang_vn(bay_gio_vn)
    dich = v + dt.timedelta(minutes=phut_cong)
    dau_ngay = dt.datetime(dich.year, dich.month, dich.day, 0, 0, tzinfo=chung.VN)
    tong_giay = (dich - dau_ngay).total_seconds()
    nguyen = int(tong_giay) + (1 if tong_giay > int(tong_giay) else 0)
    tron = ((nguyen + 299) // 300) * 300
    return dau_ngay + dt.timedelta(seconds=tron)


def la_loi_thieu_du_lieu_hoac_release(loi: str | None) -> bool:
    """Chi True khi loi `bo` la thieu Release hoac chua co du lieu moi (fail-closed voi moi ly do khac / rong)."""
    s = (loi or "").strip()
    if not s:
        return False
    if s.startswith("manifest/Release khong hop le: khong co Release"):
        return True
    kd = x_goc._khong_dau(s).lower()
    return (
        kd.startswith("chua co du lieu moi")
        or kd.startswith("khong co du lieu moi")
        or "du lieu gia chua ve" in kd
    )


def _dang_duoc_bat(sg_dang_bat: str, dang: str) -> bool:
    ds = {x.strip() for x in (sg_dang_bat or "").split(",") if x.strip()}
    return not ds or dang in ds


def _kenh_bat_cua_khuon(sg_kenh_bat: str, dang: str) -> set[str]:
    """Thuan, giong chay.doc_kenh_bat + chay.kenh_bat (loai 'x' khoi video)."""
    rieng: dict[str, set[str]] = {}
    chung_: set[str] = set()
    for muc in (sg_kenh_bat or "").split(","):
        muc = muc.strip()
        if not muc:
            continue
        if ":" in muc:
            d, k = (p.strip() for p in muc.split(":", 1))
            if d and k:
                rieng.setdefault(d, set()).add(k)
        else:
            chung_.add(muc)
    if dang in rieng:
        chon = rieng[dang]
    elif chung_:
        chon = chung_
    elif rieng:
        return set()
    else:
        chon = set(dieu_phoi.KENH)
    return {k for k in chon if k in dieu_phoi.KENH and k != "x"}


def _da_tung_chay_gio_bu(dong_ds: list[dict], gio_mac_dinh: str = "12:00") -> bool:
    """True neu co dong sg_dang cua khuon nay mang gio_du_kien khac gio mac dinh (tuc la da tung chay voi gio_bu)."""
    for r in dong_ds:
        gdk = r.get("gio_du_kien")
        t = x_goc._tg(gdk) if gdk else None
        if t is not None and f"{t.astimezone(chung.VN):%H:%M}" != gio_mac_dinh:
            return True
    return False


def _dieu_chinh_gio_tiktok(gio_bu_dt: dt.datetime, bay_gio_vn: dt.datetime, gio_tiktok: list[dt.datetime],
                           tran_22h: dt.datetime) -> dt.datetime | None:
    """SG-TT-1: cach moi bai TikTok khac >= 3 gio. -> datetime hop le (hoac > 22:00 de bo ngay), None neu con xa (> 60p) cho luot sau."""
    cac = [_sang_vn(g) for g in (gio_tiktok or [])]
    if not cac or not ngan.cach_gio_tiktok(gio_bu_dt, cac):
        return gio_bu_dt
    ung = gio_bu_dt
    for _ in range(len(cac) + 2):
        vi_pham = [k for k in cac if abs(ung - k) < ngan.CACH_TIKTOK]
        if not vi_pham:
            break
        moc_sau = max(k + ngan.CACH_TIKTOK for k in vi_pham)
        ung = tinh_gio_bu(moc_sau, phut_cong=0)
    if ung > tran_22h:
        return ung
    if ung - bay_gio_vn > dt.timedelta(minutes=CHO_TIKTOK_TOI_DA_PHUT):
        return None
    return ung


# ---------------------------------------------------------------- ham quyet dinh THUAN
def quyet_dinh(trang_thai: TrangThai | dict, bay_gio: dt.datetime) -> list[Viec]:
    """Ham quyet dinh thuan (khong mang, khong dong ho that): (trang_thai, bay_gio) -> list[Viec]."""
    tt = TrangThai(**trang_thai) if isinstance(trang_thai, dict) else trang_thai
    bay_vn = _sang_vn(bay_gio)
    ngay_vn = bay_vn.date().isoformat()
    if tt.ngay != ngay_vn:
        return []
    if not tt.du_lieu_moi:
        return []

    ngay = tt.ngay
    tran_22h = _moc_vn(ngay, *GIO_TOI_DA_BU)
    viec: list[Viec] = []

    # ---- 1. Top 5 (uu tien so 1)
    if _dang_duoc_bat(tt.sg_dang_bat, "top5") and bay_vn >= _moc_vn(ngay, *MOC_DUNG_TOP5):
        dong_top5 = [
            r for r in tt.sg_dang
            if r.get("ngay") == ngay and r.get("dang") == "top5" and r.get("che_do") == "that"
        ]
        dong_chan = [r for r in dong_top5 if r.get("trang_thai") != "that_bai"]
        khung_khoa_vinh_vien = any(
            r.get("trang_thai") != "bo" or not la_loi_thieu_du_lieu_hoac_release(r.get("loi"))
            for r in dong_chan
        )
        if not khung_khoa_vinh_vien:
            kenh_can_mo = tuple(sorted({str(r["kenh"]) for r in dong_chan if r.get("trang_thai") == "bo" and r.get("kenh")}))
            if not tt.co_release_top5:
                if not tt.dung_top5_dang_chay and tt.so_lan_dung_bu_top5 < 1:
                    gio_uoc = tinh_gio_bu(bay_vn, PHUT_BU_TOP5)
                    if gio_uoc > tran_22h:
                        if "qua-22h:top5" not in tt.da_bao:
                            viec.append(Viec(
                                loai="bo_ngay",
                                dang="top5",
                                ly_do=f"Top 5 {ngay}: gio bu {_nhan_gio(gio_uoc, ngay)} > 22:00 VN -> bo ngay (khong dung Release mo coi)",
                            ))
                    else:
                        if kenh_can_mo:
                            viec.append(Viec(
                                loai="mo_khung",
                                dang="top5",
                                kenh_ds=kenh_can_mo,
                                ly_do="mo lai khung bo do thieu du lieu/Release de dung bu",
                            ))
                        viec.append(Viec(
                            loai="dung_bu",
                            dang="top5",
                            workflow="dung.yml",
                            inputs={"dang": "top5", "ngay": ngay, "che_do": "that", "lan": "2"},
                        ))
            elif bay_vn > _moc_vn(ngay, *MOC_DANG_TOP5):
                da_thu_bu = tt.so_lan_dang_bu_top5 >= 1 or (not kenh_can_mo and _da_tung_chay_gio_bu(dong_top5, "12:00"))
                if not tt.dang_top5_dang_chay and not da_thu_bu:
                    gio_bu_dt: dt.datetime | None = tinh_gio_bu(bay_vn, PHUT_BU_TOP5)
                    if "tiktok" in _kenh_bat_cua_khuon(tt.sg_kenh_bat, "top5"):
                        gio_bu_dt = _dieu_chinh_gio_tiktok(gio_bu_dt, bay_vn, tt.gio_tiktok, tran_22h)
                    if gio_bu_dt is not None:
                        if gio_bu_dt > tran_22h:
                            if "qua-22h:top5" not in tt.da_bao:
                                viec.append(Viec(
                                    loai="bo_ngay",
                                    dang="top5",
                                    ly_do=f"Top 5 {ngay}: gio bu {_nhan_gio(gio_bu_dt, ngay)} > 22:00 VN -> bo ngay",
                                ))
                        else:
                            gio_bu_s = f"{gio_bu_dt:%H:%M}"
                            if kenh_can_mo:
                                viec.append(Viec(
                                    loai="mo_khung",
                                    dang="top5",
                                    kenh_ds=kenh_can_mo,
                                    ly_do="mo lai khung bo do thieu Release de dang bu",
                                ))
                            viec.append(Viec(
                                loai="dang_bu_top5",
                                dang="top5",
                                workflow="dang.yml",
                                gio_bu=gio_bu_s,
                                inputs={"dang": "top5", "ngay": ngay, "che_do": "that", "gio_bu": gio_bu_s},
                            ))

    # ---- 2. X bai goc
    if tt.x_goc_bat and tt.co_keo_ps:
        try:
            ngay_d = dt.date.fromisoformat(ngay)
            ngay_1_d = dt.date.fromisoformat(tt.x_goc_ngay_1.strip())
        except ValueError:
            ngay_d = ngay_1_d = None
        if ngay_d is not None and ngay_1_d is not None and ngay_d >= ngay_1_d:
            khung = x_goc.khung_hom_nay(ngay_d, ngay_1_d)
            moc_x = _moc_tu_hhmm(ngay, x_goc.GIO_KHUNG[khung])
            dong_x = [
                r for r in tt.sg_dang
                if r.get("ngay") == ngay and r.get("dang") == x_goc.DANG and r.get("kenh") == x_goc.KENH and r.get("che_do") == "that"
            ]
            if (
                bay_vn > moc_x
                and not dong_x
                and tt.x_goc_thieu_keo is not False
                and not tt.x_goc_dang_chay
                and tt.so_lan_bu_x_goc < 1
            ):
                gio_x = tinh_gio_bu(bay_vn, PHUT_BU_X_GOC)
                if gio_x > tran_22h:
                    if "qua-22h:x-goc" not in tt.da_bao:
                        viec.append(Viec(
                            loai="bo_ngay",
                            dang="x-goc",
                            ly_do=f"X goc {ngay}: gio bu {_nhan_gio(gio_x, ngay)} > 22:00 VN -> bo ngay",
                        ))
                else:
                    gio_x_s = f"{gio_x:%H:%M}"
                    viec.append(Viec(
                        loai="dang_bu_x_goc",
                        dang="x-goc",
                        workflow="x-goc.yml",
                        gio_bu=gio_x_s,
                        inputs={"che_do": "that", "khung": khung, "ngay": ngay, "gio_bu": gio_x_s},
                    ))

    # ---- 3. Tin gia MXH (Threads 11:30, FB 19:00, IG 20:30 - moi luot chon toi da 1 kenh vi dung chung concurrency tin-gia-that)
    if tt.co_keo_ps and not tt.tin_gia_dang_chay:
        for kenh in ("threads", "fb", "ig"):
            dang_tg = tin_gia_chon.DANG[kenh]
            if not tin_gia_mxh.kenh_bat_rieng(tt.sg_kenh_bat, dang_tg, kenh):
                continue
            moc_tg = _moc_tu_hhmm(ngay, tin_gia_chon.GIO[kenh])
            dong_tg = [
                r for r in tt.sg_dang
                if r.get("ngay") == ngay and r.get("dang") == dang_tg and r.get("kenh") == kenh and r.get("che_do") == "that"
            ]
            if (
                bay_vn <= moc_tg
                or dong_tg
                or tt.tin_gia_thieu_keo.get(kenh) is False
                or tt.so_lan_bu_tin_gia.get(kenh, 0) >= 1
            ):
                continue
            gio_tg = tinh_gio_bu(bay_vn, PHUT_BU_TIN_GIA)
            if gio_tg > tran_22h:
                if f"qua-22h:{dang_tg}" not in tt.da_bao:
                    viec.append(Viec(
                        loai="bo_ngay",
                        dang=dang_tg,
                        ly_do=f"Tin gia {kenh} {ngay}: gio bu {_nhan_gio(gio_tg, ngay)} > 22:00 VN -> bo ngay",
                    ))
                continue
            gio_tg_s = f"{gio_tg:%H:%M}"
            viec.append(Viec(
                loai="dang_bu_tin_gia",
                dang=dang_tg,
                workflow="tin-gia-mxh.yml",
                gio_bu=gio_tg_s,
                inputs={"kenh": kenh, "che_do": "that", "ngay": ngay, "gio_bu": gio_tg_s},
            ))
            break   # mot luot chi dispatch 1 kenh tin-gia-mxh de khong xep hang qua gio_bu

    return viec


# ---------------------------------------------------------------- GitHub API client + doc trang thai
def _bao(tieu_de: str, noi_dung: str, click: str | None = None):
    chung.log_loi(f"chay_bu: {tieu_de}: {noi_dung}")
    if ntfy.loi(tieu_de, noi_dung, click=click) is True and os.environ.get("DA_BAO_FILE"):
        try:
            open(os.environ["DA_BAO_FILE"], "w").close()
        except OSError:
            pass


def nap_kiem_do_moi():
    spec = importlib.util.spec_from_file_location("sangame_kiem_do_moi", SCRIPT_KIEM_MOI)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class GitHubClient:
    """Lop mong goi GitHub REST API bang GITHUB_TOKEN qua dang.http."""

    def __init__(self, repo: str | None = None, token: str | None = None, ref: str = "main", ngu_fn=None, bay_gio_fn=None):
        self.repo = repo or os.environ.get("GITHUB_REPOSITORY") or manifest.REPO
        self.token = (token if token is not None else (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "")).strip()
        if not self.token:
            raise LoiChayBu("thieu GITHUB_TOKEN")
        chung.dang_ky_bi_mat(self.token)
        self.ref = ref
        self._ngu = ngu_fn or chung.ngu
        self._bay_gio = bay_gio_fn or chung.bay_gio

    def _hdr(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _get(self, duong: str, *, params: dict | None = None, theo_chuyen_huong: bool = False, timeout: int = 30) -> http.Phan:
        try:
            return http.gui("GET", f"{manifest.API}{duong}", headers=self._hdr(), params=params,
                            theo_chuyen_huong=theo_chuyen_huong, timeout=timeout)
        except http.LoiMang as e:
            raise LoiChayBu(str(e)) from None

    def thong_tin_release(self, tag: str) -> tuple[bool, dt.datetime | None]:
        r = self._get(f"/repos/{self.repo}/releases/tags/{tag}")
        if r.status == 404:
            return False, None
        if r.status != 200:
            raise LoiChayBu(f"doc Release {tag}: HTTP {r.status}")
        j = r.json()
        if not isinstance(j, dict) or j.get("draft"):
            return False, None
        tao = x_goc._tg(j.get("published_at") or j.get("created_at"))
        return True, tao

    def co_release_tag(self, tag: str) -> bool:
        return self.thong_tin_release(tag)[0]

    def danh_sach_runs(self, workflow: str, ngay: str) -> list[dict]:
        r = self._get(f"/repos/{self.repo}/actions/workflows/{workflow}/runs", params={"per_page": "50"})
        if r.status == 404 and workflow == "chay-bu.yml":
            return []   # 22/11: chính workflow này chưa có trên GitHub (chạy thử trước khi gộp) -> chưa có lượt nào
        if r.status != 200:
            raise LoiChayBu(f"doc runs {workflow}: HTTP {r.status}")
        ds = (r.json() or {}).get("workflow_runs")
        return [x for x in (ds or []) if isinstance(x, dict)]

    def dispatch(self, workflow: str, inputs: dict, luc: dt.datetime | None = None) -> int:
        luc_gui = luc or self._bay_gio()
        ids_cu = {r.get("id") for r in self.danh_sach_runs(workflow, "") if r.get("id")}
        url = f"{manifest.API}/repos/{self.repo}/actions/workflows/{workflow}/dispatches"
        body_chi_tiet = {"ref": self.ref, "inputs": inputs, "return_run_details": True}
        try:
            r = http.gui("POST", url, headers=self._hdr(), json_body=body_chi_tiet, timeout=30)
            if r.status == 422:
                r = http.gui("POST", url, headers=self._hdr(), json_body={"ref": self.ref, "inputs": inputs}, timeout=30)
        except http.LoiMang as e:
            raise LoiChayBu(str(e)) from None
        if r.status == 200:
            rid = (r.json() or {}).get("workflow_run_id")
            if rid:
                return int(rid)
        elif r.status != 204:
            raise LoiChayBu(f"dispatch {workflow} HTTP {r.status}: {chung.cat(r.text, 200)}")
        moc_tu = luc_gui - dt.timedelta(seconds=15)
        for _ in range(18):
            self._ngu(5)
            for run in self.danh_sach_runs(workflow, ""):
                rid = run.get("id")
                tao = x_goc._tg(run.get("created_at"))
                if rid and rid not in ids_cu and run.get("event") == "workflow_dispatch" and (tao is None or tao >= moc_tu):
                    return int(rid)
        raise LoiChayBu(f"da dispatch {workflow} nhung khong tim thay run moi sau 90 giay")

    def doi_run(self, run_id: int, toi_da_giay: int = 2700) -> dict:
        han = self._bay_gio() + dt.timedelta(seconds=toi_da_giay)
        while True:
            r = self._get(f"/repos/{self.repo}/actions/runs/{run_id}")
            if r.status != 200:
                raise LoiChayBu(f"doc run {run_id}: HTTP {r.status}")
            j = r.json()
            if isinstance(j, dict) and j.get("status") == "completed":
                return j
            if self._bay_gio() >= han:
                raise LoiChayBu(f"het gio doi run {run_id} ({toi_da_giay} s)")
            self._ngu(15)

    def jobs_cua_run(self, run_id: int) -> list[dict]:
        r = self._get(f"/repos/{self.repo}/actions/runs/{run_id}/jobs", params={"per_page": "30"})
        if r.status != 200:
            return []
        return [j for j in ((r.json() or {}).get("jobs") or []) if isinstance(j, dict)]

    def log_job_thuong(self, workflow: str, run_id: int) -> str:
        for j in self.jobs_cua_run(run_id):
            jid = j.get("id")
            if not jid:
                continue
            try:
                r = self._get(f"/repos/{self.repo}/actions/jobs/{jid}/logs", theo_chuyen_huong=True, timeout=30)
            except LoiChayBu:
                return ""
            if r.status == 200 and r.body:
                return r.text
        return ""


def _runs_hom_nay(runs: list[dict], ngay: str) -> list[tuple[dict, dt.datetime]]:
    ra = []
    for r in runs:
        if r.get("head_branch") not in (None, "main"):
            continue
        t = x_goc._tg(r.get("created_at"))
        if t is None:
            continue
        tv = t.astimezone(chung.VN)
        if tv.date().isoformat() == ngay:
            ra.append((r, tv))
    return ra


def _co_run_dang_chay(runs: list[dict]) -> bool:
    return any(r.get("head_branch") in (None, "main") and r.get("status") != "completed" for r in runs)


def doc_trang_thai(
    *,
    ngay: str,
    cong,
    gh,
    du_lieu_moi: bool,
    co_keo_ps: bool | None = None,
    sg_dang_bat: str | None = None,
    sg_kenh_bat: str | None = None,
    x_goc_bat: bool | None = None,
    x_goc_ngay_1: str | None = None,
) -> TrangThai:
    sg_dang_bat = os.environ.get("SG_DANG_BAT", "") if sg_dang_bat is None else sg_dang_bat
    sg_kenh_bat = os.environ.get("SG_KENH_BAT", "") if sg_kenh_bat is None else sg_kenh_bat
    x_goc_bat = (os.environ.get("SG_X_GOC_BAT", "").strip() == "1") if x_goc_bat is None else x_goc_bat
    x_goc_ngay_1 = os.environ.get("SG_X_GOC_NGAY_1", "").strip() if x_goc_ngay_1 is None else x_goc_ngay_1

    sg_dang = cong.doc_dang(ngay, ngay, "that")
    if co_keo_ps is None:
        co_keo_ps = bool(cong.doc_keo(ngay)) if hasattr(cong, "doc_keo") else False
    tag_top5 = manifest.tag(ngay, "top5", "that")
    if hasattr(gh, "thong_tin_release"):
        co_rel, rel_tao_luc = gh.thong_tin_release(tag_top5)
    else:
        co_rel, rel_tao_luc = gh.co_release_tag(tag_top5), None

    # --- dung.yml & dang.yml (Top 5)
    runs_dung = gh.danh_sach_runs("dung.yml", ngay)
    dung_chay = _co_run_dang_chay(runs_dung)
    moc_1050 = _moc_vn(ngay, *MOC_DUNG_TOP5)
    so_dung_bu = 0
    for r, tv in _runs_hom_nay(runs_dung, ngay):
        if r.get("conclusion") in ("skipped", "cancelled"):   # 22/11: lượt bị huỷ (tay) không phải một lần dựng đã thử
            continue
        if tv < moc_1050:
            # 22/11 (Claude soi): lượt THƯỜNG 10:15/10:45 đã dựng thật với dữ liệu mới (job chon chạy) mà không ra Release
            # -> 11:35 ghi `bo` "khong co Release" nhưng lý do thật là trượt khi dựng -> tính như đã thử, KHÔNG dựng bù.
            if r.get("status") == "completed" and not co_rel:
                jobs = gh.jobs_cua_run(r["id"])
                chon_job = next((j for j in jobs if j.get("name") == "chon"), None)
                if chon_job and chon_job.get("conclusion") not in (None, "skipped"):
                    so_dung_bu += 1
            continue
        if r.get("status") == "completed" and r.get("conclusion") == "success" and not co_rel:
            jobs = gh.jobs_cua_run(r["id"])
            chon_job = next((j for j in jobs if j.get("name") == "chon"), None)
            if chon_job and chon_job.get("conclusion") == "skipped":
                continue   # luot thoat o kiem-moi vi du lieu chua moi / khung dong -> khong phai da dung bu
        so_dung_bu += 1

    runs_dang = gh.danh_sach_runs("dang.yml", ngay)
    dang_chay = _co_run_dang_chay(runs_dang)
    moc_1140 = _moc_vn(ngay, 11, 40)
    moc_dang_bu = max(moc_1140, _sang_vn(rel_tao_luc) - dt.timedelta(seconds=5)) if rel_tao_luc is not None else moc_1140
    so_dang_bu = 0
    for r, tv in _runs_hom_nay(runs_dang, ngay):
        if tv < moc_dang_bu or r.get("conclusion") == "skipped":
            continue
        if r.get("status") != "completed":
            so_dang_bu += 1
            continue
        jobs = gh.jobs_cua_run(r["id"])
        kiem_job = next((j for j in jobs if j.get("name") == "kiem"), None)
        if kiem_job and kiem_job.get("conclusion") != "skipped":
            so_dang_bu += 1   # pha=chuan-bi chay sau khi co Release = luot dang bu

    # --- x-goc.yml
    x_dang_chay = False
    so_bu_x = 0
    x_thieu_keo: bool | None = None
    if x_goc_bat:
        runs_x = gh.danh_sach_runs("x-goc.yml", ngay)
        x_dang_chay = _co_run_dang_chay(runs_x)
        for r, _tv in _runs_hom_nay(runs_x, ngay):
            tieu_de = f"{r.get('display_title') or ''} {r.get('name') or ''}"
            if "(bu " in tieu_de and r.get("conclusion") != "skipped":
                so_bu_x += 1
            elif r.get("status") == "completed" and r.get("conclusion") != "skipped" and x_thieu_keo is None:
                log = gh.log_job_thuong("x-goc.yml", r["id"])
                if "chua co dong PS nao" in log:
                    x_thieu_keo = True
                elif "x_goc:" in log and "không phải khung hôm nay" not in log:
                    x_thieu_keo = False

    # --- tin-gia-mxh.yml
    tg_dang_chay = False
    so_bu_tg: dict[str, int] = {}
    tg_thieu_keo: dict[str, bool] = {}
    kenh_tg_bat = [k for k in ("threads", "fb", "ig") if tin_gia_mxh.kenh_bat_rieng(sg_kenh_bat, tin_gia_chon.DANG[k], k)]
    if kenh_tg_bat:
        runs_tg = gh.danh_sach_runs("tin-gia-mxh.yml", ngay)
        tg_dang_chay = _co_run_dang_chay(runs_tg)
        for r, _tv in _runs_hom_nay(runs_tg, ngay):
            tieu_de = f"{r.get('display_title') or ''} {r.get('name') or ''}"
            for k in kenh_tg_bat:
                if f"({k} bu " in tieu_de and r.get("conclusion") != "skipped":
                    so_bu_tg[k] = so_bu_tg.get(k, 0) + 1
            if " bu " not in tieu_de and r.get("status") == "completed" and r.get("conclusion") != "skipped":
                log = gh.log_job_thuong("tin-gia-mxh.yml", r["id"])
                for k in kenh_tg_bat:
                    if k in tg_thieu_keo:
                        continue
                    if f"Tin giá {k}" in log or f"tin_gia_mxh [{k}]" in log:
                        tg_thieu_keo[k] = "chua co dong PS nao" in log

    # --- TikTok SG-TT-1 (chi doc Zernio khi top5 bat kenh tiktok)
    gio_tt: list[dt.datetime] = []
    if "tiktok" in _kenh_bat_cua_khuon(sg_kenh_bat, "top5"):
        for r in sg_dang:
            if r.get("kenh") == "tiktok" and r.get("trang_thai") not in ("that_bai", "bo"):
                t_tt = x_goc._tg(r.get("gio_cong_khai") or r.get("gio_du_kien"))
                if t_tt is not None:
                    gio_tt.append(t_tt.astimezone(chung.VN))
        zk = os.environ.get("ZERNIO_KHOA", "").strip()
        if zk:
            try:
                gio_tt.extend(ngan.gio_tiktok_zernio(zk, zernio._acc(), dt.date.fromisoformat(ngay)))
            except chung.LoiDang as e:
                chung.log_loi(f"chay_bu: khong doc duoc gio TikTok Zernio: {e}")

    # --- Chong gui lap ntfy qua 22:00 luc dem
    da_bao: set[str] = set()
    moc_2131 = _moc_vn(ngay, 21, 31)
    for r, tv in _runs_hom_nay(gh.danh_sach_runs("chay-bu.yml", ngay), ngay):
        if tv >= moc_2131 and r.get("status") == "completed" and r.get("conclusion") == "success":
            da_bao.update({"qua-22h:top5", "qua-22h:x-goc", "qua-22h:threads-gia", "qua-22h:fb-gia", "qua-22h:ig-gia"})
            break

    return TrangThai(
        ngay=ngay,
        du_lieu_moi=du_lieu_moi,
        co_keo_ps=bool(co_keo_ps),
        co_release_top5=co_rel,
        sg_dang=sg_dang,
        dung_top5_dang_chay=dung_chay,
        so_lan_dung_bu_top5=so_dung_bu,
        dang_top5_dang_chay=dang_chay,
        so_lan_dang_bu_top5=so_dang_bu,
        sg_dang_bat=sg_dang_bat,
        sg_kenh_bat=sg_kenh_bat,
        x_goc_bat=x_goc_bat,
        x_goc_ngay_1=x_goc_ngay_1,
        x_goc_dang_chay=x_dang_chay,
        x_goc_thieu_keo=x_thieu_keo,
        so_lan_bu_x_goc=so_bu_x,
        tin_gia_dang_chay=tg_dang_chay,
        tin_gia_thieu_keo=tg_thieu_keo,
        so_lan_bu_tin_gia=so_bu_tg,
        gio_tiktok=gio_tt,
        da_bao=da_bao,
    )


# ---------------------------------------------------------------- thuc thi
def thuc_thi(ds_viec: list[Viec], cong, gh, *, bay_gio_fn=None, ngu_fn=None) -> int:
    """Thuc hien danh sach Viec. Tra 0 neu on, 1 neu co buoc loi (da ntfy)."""
    bay_gio_fn = bay_gio_fn or chung.bay_gio
    ngu_fn = ngu_fn or chung.ngu
    if not ds_viec:
        chung.log("chay_bu: khong co viec can lam")
        return 0

    ngay = _sang_vn(bay_gio_fn()).date().isoformat()
    for v in ds_viec:
        if v.inputs.get("ngay"):
            ngay = v.inputs["ngay"]
            break

    loi = False
    mo_thang: dict[str, bool] = {}

    # 1. Thong bao bo ngay + mo khung so-va-dat
    for v in ds_viec:
        if v.loai == "bo_ngay":
            _bao(f"Chạy bù {v.dang}: bỏ ngày {ngay}", v.ly_do)
        elif v.loai == "mo_khung":
            tong = 0
            loi_mo: str | None = None
            for kenh in v.kenh_ds:
                try:
                    tong += cong.cap_nhat_dang(ngay, v.dang, kenh, "that", neu_trang_thai="bo", trang_thai="that_bai", loi=v.ly_do)
                except Exception as e:   # noqa: BLE001
                    loi_mo = f"{type(e).__name__}: {e}"
                    break
            try:
                con_bo = [
                    r for r in cong.doc_dang(ngay, ngay, "that")
                    if r.get("dang") == v.dang and r.get("trang_thai") == "bo"
                ]
            except Exception as e:   # noqa: BLE001
                con_bo = []
                loi_mo = loi_mo or f"{type(e).__name__}: {e}"
            if loi_mo or con_bo:
                chi_tiet = loi_mo or "cap_nhat_dang(neu_trang_thai='bo', trang_thai='that_bai') trả 0 dòng nhưng dòng vẫn ở 'bo'"
                _bao(f"Chạy bù {v.dang} {ngay}: không mở được khung bo", chung.cat(chi_tiet, 300))
                loi = True
                mo_thang[v.dang] = False
            elif tong == 0:
                chung.log(f"chay_bu: {v.dang} {ngay}: luot khac da mo khung truoc (so_dong=0) -> nhuong, khong dispatch")
                mo_thang[v.dang] = False
            else:
                chung.log(f"chay_bu: da mo lai {tong} dong 'bo' -> 'that_bai' cho {v.dang} {ngay}")
                mo_thang[v.dang] = True

    def duoc_phep(dang: str) -> bool:
        return mo_thang.get(dang, True)

    # 2. Uu tien Top 5: dispatch dung_bu hoac pha chuan-bi cua dang_bu_top5 TRUOC
    cho_top5: tuple[Viec, int] | None = None
    for v in ds_viec:
        if not duoc_phep(v.dang):
            continue
        try:
            if v.loai == "dung_bu":
                rid = gh.dispatch(v.workflow, v.inputs, luc=bay_gio_fn())
                chung.log(f"chay_bu: da dispatch {v.workflow} ({v.dang} {ngay}) -> run {rid}")
            elif v.loai == "dang_bu_top5":
                inp_cb = {**v.inputs, "pha": "chuan-bi"}
                rid_cb = gh.dispatch(v.workflow, inp_cb, luc=bay_gio_fn())
                chung.log(f"chay_bu: da dispatch {v.workflow} pha=chuan-bi gio_bu={v.gio_bu} -> run {rid_cb}")
                cho_top5 = (v, rid_cb)
        except Exception as e:   # noqa: BLE001
            _bao(f"Chạy bù {v.dang} {ngay}: dispatch lỗi", chung.cat(f"{type(e).__name__}: {e}", 300))
            loi = True

    # 3. Dispatch cac luong khong ngu (X goc / Tin gia MXH) TRUOC khi job ngu doi gio_bu cua Top 5 (loi rieng KHONG chan Top 5)
    for v in ds_viec:
        if not duoc_phep(v.dang):
            continue
        if v.loai in ("dang_bu_x_goc", "dang_bu_tin_gia"):
            try:
                rid = gh.dispatch(v.workflow, v.inputs, luc=bay_gio_fn())
                chung.log(f"chay_bu: da dispatch {v.workflow} ({v.dang} gio_bu={v.gio_bu}) -> run {rid}")
            except Exception as e:   # noqa: BLE001
                _bao(f"Chạy bù {v.dang} {ngay}: dispatch lỗi", chung.cat(f"{type(e).__name__}: {e}", 300))
                loi = True

    # 4. Doi pha chuan-bi Top 5 -> ngu toi gio_bu -> dispatch cong-khai cung gio_bu -> doi xong
    if cho_top5 is not None:
        v, rid_cb = cho_top5
        try:
            r_cb = gh.doi_run(rid_cb)
        except Exception as e:   # noqa: BLE001
            _bao(f"Đăng bù Top 5 {ngay}: đợi pha chuẩn bị lỗi", chung.cat(f"{type(e).__name__}: {e}", 300))
            return 1
        if r_cb.get("conclusion") != "success":
            _bao(
                f"Đăng bù Top 5 {ngay}: pha chuẩn bị lỗi",
                f"Run {rid_cb} kết thúc với conclusion={r_cb.get('conclusion')!r}, dừng không công khai.",
                click=r_cb.get("html_url"),
            )
            return 1
        dich = _moc_tu_hhmm(ngay, v.gio_bu)
        con = (dich - _sang_vn(bay_gio_fn())).total_seconds()
        if con > 0:
            chung.log(f"chay_bu: pha chuan-bi Top 5 xong, ngu {int(con)} giay toi gio_bu {v.gio_bu} VN")
            ngu_fn(con)
        inp_ck = {**v.inputs, "pha": "cong-khai"}
        try:
            rid_ck = gh.dispatch(v.workflow, inp_ck, luc=bay_gio_fn())
            chung.log(f"chay_bu: da dispatch {v.workflow} pha=cong-khai gio_bu={v.gio_bu} -> run {rid_ck}")
            r_ck = gh.doi_run(rid_ck)
        except Exception as e:   # noqa: BLE001
            _bao(f"Đăng bù Top 5 {ngay}: pha công khai lỗi", chung.cat(f"{type(e).__name__}: {e}", 300))
            return 1
        if r_ck.get("conclusion") != "success":
            _bao(
                f"Đăng bù Top 5 {ngay}: pha công khai lỗi",
                f"Run {rid_ck} kết thúc với conclusion={r_ck.get('conclusion')!r}.",
                click=r_ck.get("html_url"),
            )
            return 1
        chung.log(f"chay_bu: dang bu Top 5 {ngay} (gio_bu={v.gio_bu}) hoan tat")

    return 1 if loi else 0


def chay_mot_luot(
    *,
    cong,
    gh,
    du_lieu_moi: bool,
    co_keo_ps: bool | None = None,
    ngay: str | None = None,
    bay_gio_fn=None,
    ngu_fn=None,
    kho_chay: bool = False,
    sg_dang_bat: str | None = None,
    sg_kenh_bat: str | None = None,
    x_goc_bat: bool | None = None,
    x_goc_ngay_1: str | None = None,
) -> int:
    bay_gio_fn = bay_gio_fn or chung.bay_gio
    ngu_fn = ngu_fn or chung.ngu
    now = bay_gio_fn()
    ngay = ngay or _sang_vn(now).date().isoformat()
    tt = doc_trang_thai(
        ngay=ngay,
        cong=cong,
        gh=gh,
        du_lieu_moi=du_lieu_moi,
        co_keo_ps=co_keo_ps,
        sg_dang_bat=sg_dang_bat,
        sg_kenh_bat=sg_kenh_bat,
        x_goc_bat=x_goc_bat,
        x_goc_ngay_1=x_goc_ngay_1,
    )
    ds_viec = quyet_dinh(tt, now)
    chung.log(f"chay_bu [{ngay} {_sang_vn(now):%H:%M} VN]: moi={tt.du_lieu_moi} keo={tt.co_keo_ps} rel={tt.co_release_top5} -> {[v.loai + ':' + v.dang for v in ds_viec]}")
    if kho_chay:
        return 0
    return thuc_thi(ds_viec, cong, gh, bay_gio_fn=bay_gio_fn, ngu_fn=ngu_fn)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Chay bu San Game khi Mac bat muon")
    ap.add_argument("--ngay", default=None, help="YYYY-MM-DD (mac dinh: hom nay gio VN)")
    ap.add_argument("--du-lieu", default="du-lieu", help="Thu muc checkout kenh-game-du-lieu")
    ap.add_argument("--kho-chay", action="store_true", help="Chi in quyet dinh, khong ghi so, khong dispatch")
    a = ap.parse_args(argv)
    ngay = a.ngay or chung.bay_gio().astimezone(chung.VN).date().isoformat()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", ngay):
        ap.error("--ngay phai la YYYY-MM-DD")
    try:
        kdm = nap_kiem_do_moi()
        moi, ly_do = kdm.kiem(a.du_lieu, ngay)
        if not moi:
            chung.log(f"chay_bu: chua co du lieu moi ({ngay}): {'; '.join(ly_do)[:300]} -> khong lam gi")
            return 0
        cong = so.Cong()
        gh = GitHubClient()
        return chay_mot_luot(cong=cong, gh=gh, du_lieu_moi=True, ngay=ngay, kho_chay=a.kho_chay)
    except (so.LoiCong, LoiChayBu) as e:
        _bao("Chạy bù Săn Game: lỗi cổng / GitHub API", chung.cat(e, 300))
        return 1
    except Exception as e:   # noqa: BLE001
        _bao("Chạy bù Săn Game: lỗi bất ngờ", chung.cat(f"{type(e).__name__}: {e}", 300))
        return 1


if __name__ == "__main__":
    sys.exit(main())
