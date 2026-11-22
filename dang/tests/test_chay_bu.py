"""Test chay bu San Game khi Mac bat muon (dang/chay_bu.py): TDD, khong mang that, khong ngu that, khong goi sg-cong that."""
import contextlib
import datetime as dt
import io
import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from dang import chay_bu, chung, http, ntfy
from dang.tests.gia_lap import CongGia, Mang, P

NGAY = "2026-11-22"


def vn(h, m, s=0, ngay=NGAY):
    d = dt.date.fromisoformat(ngay)
    return dt.datetime(d.year, d.month, d.day, h, m, s, tzinfo=chung.VN)


def dong_dang(kenh="youtube", tt="bo", loi="manifest/Release khong hop le: khong co Release v-2026-11-22-top5",
              dang="top5", ngay=NGAY, che_do="that", gio_du_kien="2026-11-22T05:00:00Z"):
    return dict(ngay=ngay, dang=dang, kenh=kenh, che_do=che_do, trang_thai=tt, loi=loi, gio_du_kien=gio_du_kien)


def bo_5_kenh(loi="manifest/Release khong hop le: khong co Release v-2026-11-22-top5"):
    return [dong_dang(k, "bo", loi) for k in ("fb", "ig", "youtube", "tiktok", "x")]


class GitHubGia:
    """Gia lap GitHub API cho chay_bu: giu danh sach runs, releases, va kich ban ket qua khi doi_run."""

    def __init__(self, co_release=False, runs=None, ket_qua_run=None):
        self.co_release = co_release
        self.runs = {k: list(v) for k, v in (runs or {}).items()}
        self.ket_qua_run = list(ket_qua_run or [])   # list conclusion ("success"|"failure") cho moi lan dispatch
        self.da_dispatch = []                        # [(workflow, dict(inputs), luc_iso)]
        self._id = 1000

    def co_release_tag(self, tag):
        return self.co_release and tag == f"v-{NGAY}-top5"

    def danh_sach_runs(self, workflow, ngay):
        return [dict(r) for r in self.runs.get(workflow, [])]

    def dispatch(self, workflow, inputs, luc=None):
        self._id += 1
        rid = self._id
        conclusion = self.ket_qua_run.pop(0) if self.ket_qua_run else "success"
        luc_iso = chung.iso(luc or vn(12, 0))
        ten = workflow
        if workflow == "x-goc.yml" and inputs.get("gio_bu"):
            ten = f"X bai goc (bu {inputs['gio_bu']})"
        elif workflow == "tin-gia-mxh.yml" and inputs.get("gio_bu"):
            ten = f"Tin gia MXH ({inputs['kenh']} bu {inputs['gio_bu']})"
        elif workflow == "dung.yml":
            ten = f"Dung video [{inputs.get('dang')} {inputs.get('che_do')}]"
        elif workflow == "dang.yml":
            bu = f" bu {inputs['gio_bu']}" if inputs.get("gio_bu") else ""
            ten = f"Dang video [{inputs.get('pha')} {inputs.get('dang')} {inputs.get('che_do')}{bu}]"
        r = {
            "id": rid,
            "name": ten,
            "display_title": ten,
            "event": "workflow_dispatch",
            "status": "queued",
            "conclusion": None,
            "created_at": luc_iso,
            "html_url": f"https://github.com/thenail1995-create/sangame-video/actions/runs/{rid}",
            "_conclusion_dich": conclusion,
            "_inputs": dict(inputs),
        }
        self.runs.setdefault(workflow, []).insert(0, r)
        self.da_dispatch.append((workflow, dict(inputs)))
        return rid

    def doi_run(self, run_id, toi_da_giay=2700):
        for ds in self.runs.values():
            for r in ds:
                if r["id"] == run_id:
                    r["status"] = "completed"
                    r["conclusion"] = r.get("_conclusion_dich", "success")
                    return dict(r)
        raise AssertionError(f"khong tim thay run {run_id}")

    def jobs_cua_run(self, run_id):
        for wf, ds in self.runs.items():
            for r in ds:
                if r["id"] == run_id:
                    if "_jobs" in r:
                        return [dict(j) for j in r["_jobs"]]
                    inp = r.get("_inputs") or {}
                    if wf == "dang.yml":
                        pha = inp.get("pha", "chuan-bi")
                        return [
                            {"name": "kiem", "conclusion": "success" if pha == "chuan-bi" else "skipped"},
                            {"name": "cong-khai", "conclusion": "success" if pha == "cong-khai" else "skipped"},
                        ]
                    if wf == "dung.yml":
                        return [{"name": "chon", "conclusion": r.get("conclusion") or "success"}]
        return []

    def log_job_thuong(self, workflow, run_id):
        for r in self.runs.get(workflow, []):
            if r["id"] == run_id:
                return r.get("_log", "")
        return ""


class QuyetDinhTop5Test(unittest.TestCase):
    def test_truoc_10_50_khong_lam_gi(self):
        tt = chay_bu.TrangThai(ngay=NGAY, du_lieu_moi=True, co_release_top5=False)
        self.assertEqual(chay_bu.quyet_dinh(tt, vn(10, 15)), [])
        self.assertEqual(chay_bu.quyet_dinh(tt, vn(10, 49, 59)), [])

    def test_khac_ngay_hom_nay_vn_khong_lam_gi(self):
        tt = chay_bu.TrangThai(ngay="2026-11-21", du_lieu_moi=True, co_release_top5=False)
        # 2026-11-21 23:30 UTC = 2026-11-22 06:30 VN -> ngay hom nay VN la 2026-11-22 != 2026-11-21
        bay_utc = dt.datetime(2026, 11, 21, 23, 30, tzinfo=dt.timezone.utc)
        self.assertEqual(chay_bu.quyet_dinh(tt, bay_utc), [])
        self.assertEqual(chay_bu.quyet_dinh(tt, vn(13, 0, ngay="2026-11-22")), [])

    def test_du_lieu_chua_moi_khong_lam_gi(self):
        tt = chay_bu.TrangThai(ngay=NGAY, du_lieu_moi=False, co_release_top5=False, sg_dang=bo_5_kenh())
        self.assertEqual(chay_bu.quyet_dinh(tt, vn(11, 50)), [])

    def test_du_lieu_ve_11_28_sau_khi_11_35_ghi_bo_khong_co_release_thi_mo_lai_va_dung(self):
        tt = chay_bu.TrangThai(ngay=NGAY, du_lieu_moi=True, co_release_top5=False, sg_dang=bo_5_kenh())
        ds = chay_bu.quyet_dinh(tt, vn(11, 45))
        self.assertEqual([v.loai for v in ds], ["mo_khung", "dung_bu"])
        self.assertEqual(ds[0].dang, "top5")
        self.assertEqual(set(ds[0].kenh_ds), {"fb", "ig", "youtube", "tiktok", "x"})
        self.assertEqual(ds[1].workflow, "dung.yml")
        self.assertEqual(ds[1].inputs, {"dang": "top5", "ngay": NGAY, "che_do": "that", "lan": "2"})

    def test_bo_vi_chua_co_du_lieu_moi_cung_duoc_mo_lai_va_dung(self):
        tt = chay_bu.TrangThai(
            ngay=NGAY,
            du_lieu_moi=True,
            co_release_top5=False,
            sg_dang=[dong_dang("youtube", "bo", "chưa có dữ liệu mới: bang-gia.json cap_nhat = 2026-11-21")],
        )
        ds = chay_bu.quyet_dinh(tt, vn(11, 50))
        self.assertEqual([v.loai for v in ds], ["mo_khung", "dung_bu"])
        self.assertEqual(ds[0].kenh_ds, ("youtube",))

    def test_khung_bo_vi_gia_sai_hoac_noi_dung_truot_tuyet_doi_khong_mo(self):
        for loi_khac in (
            "kiem lai gia/han truoc gio dang: God of War gia tang HK$100 -> HK$200",
            "manifest/Release khong hop le: ban tiktok khong dat bo kiem (kiem.dat != true)",
            "manifest/Release khong hop le: sha256 video-shorts.mp4 khong khop manifest",
            "tin gia: dong 1 khong khop",
            "",
        ):
            with self.subTest(loi=loi_khac):
                tt = chay_bu.TrangThai(ngay=NGAY, du_lieu_moi=True, co_release_top5=False, sg_dang=[dong_dang("youtube", "bo", loi_khac)])
                self.assertEqual(chay_bu.quyet_dinh(tt, vn(12, 10)), [])
        # Tron 4 kenh thieu Release + 1 kenh gia sai -> cung TUYET DOI khong mo
        tron = bo_5_kenh()[:4] + [dong_dang("x", "bo", "kiem lai gia/han truoc gio dang: sai gia")]
        tt_tron = chay_bu.TrangThai(ngay=NGAY, du_lieu_moi=True, co_release_top5=False, sg_dang=tron)
        self.assertEqual(chay_bu.quyet_dinh(tt_tron, vn(12, 10)), [])

    def test_da_dang_dang_dang_chuan_bi_xong_khong_ro_khong_lam_gi(self):
        for trang_thai_dong in ("da_dang", "dang_dang", "chuan_bi_xong", "khong_ro"):
            for co_rel in (False, True):
                with self.subTest(tt=trang_thai_dong, rel=co_rel):
                    tt = chay_bu.TrangThai(
                        ngay=NGAY,
                        du_lieu_moi=True,
                        co_release_top5=co_rel,
                        sg_dang=[dong_dang("youtube", trang_thai_dong, "")],
                    )
                    self.assertEqual(chay_bu.quyet_dinh(tt, vn(13, 10)), [])

    def test_release_co_roi_truoc_11_35_de_lich_thuong_tu_lo(self):
        tt = chay_bu.TrangThai(ngay=NGAY, du_lieu_moi=True, co_release_top5=True, sg_dang=[])
        self.assertEqual(chay_bu.quyet_dinh(tt, vn(11, 20)), [])
        self.assertEqual(chay_bu.quyet_dinh(tt, vn(11, 35, 0)), [])

    def test_release_co_roi_13_07_chuan_bi_voi_gio_bu_13_40(self):
        tt = chay_bu.TrangThai(
            ngay=NGAY,
            du_lieu_moi=True,
            co_release_top5=True,
            sg_dang=[dong_dang(k, "that_bai", "mo lai") for k in ("fb", "ig", "youtube", "tiktok", "x")],
        )
        ds = chay_bu.quyet_dinh(tt, vn(13, 7))
        self.assertEqual([v.loai for v in ds], ["dang_bu_top5"])
        self.assertEqual(ds[0].gio_bu, "13:40")
        self.assertEqual(ds[0].workflow, "dang.yml")
        self.assertEqual(ds[0].inputs, {"dang": "top5", "ngay": NGAY, "che_do": "that", "gio_bu": "13:40"})

    def test_release_ra_sau_11_35_con_dong_bo_thieu_release_thi_mo_lai_roi_dang_bu(self):
        # Kich ban: dung bu bat dau 11:10, 11:35 dang.yml ghi bo "khong co Release", 11:42 Release ra
        tt = chay_bu.TrangThai(ngay=NGAY, du_lieu_moi=True, co_release_top5=True, sg_dang=bo_5_kenh())
        ds = chay_bu.quyet_dinh(tt, vn(12, 5))
        self.assertEqual([v.loai for v in ds], ["mo_khung", "dang_bu_top5"])
        self.assertEqual(ds[1].gio_bu, "12:35")

    def test_gio_bu_lon_hon_22_00_thi_bo_ngay_va_ntfy(self):
        # 21:31 + 30p = 22:01 -> lam tron 22:05 > 22:00 -> bo_ngay
        tt_dang = chay_bu.TrangThai(ngay=NGAY, du_lieu_moi=True, co_release_top5=True, sg_dang=[])
        ds = chay_bu.quyet_dinh(tt_dang, vn(21, 31))
        self.assertEqual([v.loai for v in ds], ["bo_ngay"])
        self.assertEqual(ds[0].dang, "top5")
        self.assertIn("22:00", ds[0].ly_do)
        # Chua co Release luc 21:45 cung bo_ngay (khong dung Release mo coi)
        tt_dung = chay_bu.TrangThai(ngay=NGAY, du_lieu_moi=True, co_release_top5=False, sg_dang=bo_5_kenh())
        ds2 = chay_bu.quyet_dinh(tt_dung, vn(21, 45))
        self.assertEqual([v.loai for v in ds2], ["bo_ngay"])
        # Bien 21:30:00 + 30p = 22:00 <= 22:00 -> van duoc dang bu
        ds_bien = chay_bu.quyet_dinh(tt_dang, vn(21, 30, 0))
        self.assertEqual([v.loai for v in ds_bien], ["dang_bu_top5"])
        self.assertEqual(ds_bien[0].gio_bu, "22:00")
        # Da bao qua-22h:top5 roi thi khong lap ntfy
        tt_da_bao = chay_bu.TrangThai(ngay=NGAY, du_lieu_moi=True, co_release_top5=True, da_bao={"qua-22h:top5"})
        self.assertEqual(chay_bu.quyet_dinh(tt_da_bao, vn(22, 20)), [])

    def test_dang_co_luot_dung_hoac_dang_xep_hang_khong_dispatch_them(self):
        tt_dung = chay_bu.TrangThai(ngay=NGAY, du_lieu_moi=True, co_release_top5=False, dung_top5_dang_chay=True)
        self.assertEqual(chay_bu.quyet_dinh(tt_dung, vn(11, 50)), [])
        tt_dang = chay_bu.TrangThai(ngay=NGAY, du_lieu_moi=True, co_release_top5=True, dang_top5_dang_chay=True)
        self.assertEqual(chay_bu.quyet_dinh(tt_dang, vn(13, 10)), [])

    def test_moi_ngay_toi_da_1_lan_dung_bu_va_1_lan_dang_bu(self):
        tt1 = chay_bu.TrangThai(ngay=NGAY, du_lieu_moi=True, co_release_top5=False, so_lan_dung_bu_top5=1)
        self.assertEqual(chay_bu.quyet_dinh(tt1, vn(14, 0)), [])
        tt2 = chay_bu.TrangThai(ngay=NGAY, du_lieu_moi=True, co_release_top5=True, so_lan_dang_bu_top5=1)
        self.assertEqual(chay_bu.quyet_dinh(tt2, vn(14, 0)), [])

    def test_luat_tiktok_cach_3_gio_sg_tt_1(self):
        # Co kenh tiktok bat cho top5, da co bai TikTok luc 12:00 VN
        gio_tt = [vn(12, 0)]
        # Luc 14:10 -> gio_bu goc 14:40 (< 3h so voi 12:00), lui thanh 15:00 (cach bay gio 50p <= 60p)
        tt_lui = chay_bu.TrangThai(
            ngay=NGAY, du_lieu_moi=True, co_release_top5=True, sg_kenh_bat="top5:tiktok", gio_tiktok=gio_tt
        )
        ds = chay_bu.quyet_dinh(tt_lui, vn(14, 10))
        self.assertEqual([v.loai for v in ds], ["dang_bu_top5"])
        self.assertEqual(ds[0].gio_bu, "15:00")
        # Luc 12:20 -> moc 15:00 con cach 160p (> 60p) -> chua giu runner, cho luot cron sau
        self.assertEqual(chay_bu.quyet_dinh(tt_lui, vn(12, 20)), [])
        # Bai TikTok luc 19:30 -> moc 22:30 > 22:00 -> bo_ngay
        tt_qua = chay_bu.TrangThai(
            ngay=NGAY, du_lieu_moi=True, co_release_top5=True, sg_kenh_bat="top5:tiktok", gio_tiktok=[vn(19, 30)]
        )
        ds_qua = chay_bu.quyet_dinh(tt_qua, vn(20, 0))
        self.assertEqual([v.loai for v in ds_qua], ["bo_ngay"])


class QuyetDinhXVaThreadsTest(unittest.TestCase):
    def test_x_goc_va_threads_dang_bu_khi_keo_ve_muon(self):
        # 2026-11-22 la ngay 1 (le -> khung sang 10:00); Threads 11:30
        tt = chay_bu.TrangThai(
            ngay=NGAY,
            du_lieu_moi=True,
            co_keo_ps=True,
            co_release_top5=True,
            sg_dang=[dong_dang("youtube", "da_dang", "")],   # Top 5 da xong
            sg_kenh_bat="top5:youtube,threads-gia:threads",
            x_goc_bat=True,
            x_goc_ngay_1=NGAY,
        )
        ds = chay_bu.quyet_dinh(tt, vn(12, 7))
        self.assertEqual([v.loai for v in ds], ["dang_bu_x_goc", "dang_bu_tin_gia"])
        self.assertEqual(ds[0].inputs, {"che_do": "that", "khung": "sang", "ngay": NGAY, "gio_bu": "12:30"})
        self.assertEqual(ds[1].inputs, {"kenh": "threads", "che_do": "that", "ngay": NGAY, "gio_bu": "12:40"})

    def test_x_goc_khung_toi_chua_toi_gio_khong_lam_qua_20h_moi_bu(self):
        # ngay_1 = 2026-11-21 -> 2026-11-22 la ngay chan (khung toi 20:00)
        tt = chay_bu.TrangThai(
            ngay=NGAY,
            du_lieu_moi=True,
            co_keo_ps=True,
            sg_dang=[dong_dang("youtube", "da_dang", "")],
            sg_kenh_bat="top5:youtube",
            x_goc_bat=True,
            x_goc_ngay_1="2026-11-21",
        )
        self.assertEqual(chay_bu.quyet_dinh(tt, vn(15, 0)), [])
        ds = chay_bu.quyet_dinh(tt, vn(20, 12))
        self.assertEqual([v.loai for v in ds], ["dang_bu_x_goc"])
        self.assertEqual(ds[0].inputs["khung"], "toi")
        self.assertEqual(ds[0].gio_bu, "20:35")

    def test_x_va_threads_khong_bu_khi_chua_co_keo_hoac_da_co_dong_hoac_truot_ly_do_khac(self):
        # Chua co sg_keo -> []
        tt_khong_keo = chay_bu.TrangThai(
            ngay=NGAY, du_lieu_moi=True, co_keo_ps=False, sg_dang=[dong_dang("youtube", "da_dang", "")],
            sg_kenh_bat="top5:youtube,threads-gia:threads", x_goc_bat=True, x_goc_ngay_1=NGAY,
        )
        self.assertEqual(chay_bu.quyet_dinh(tt_khong_keo, vn(13, 0)), [])
        # Da co dong sg_dang cua x-goc va threads-gia -> []
        tt_da_co = chay_bu.TrangThai(
            ngay=NGAY, du_lieu_moi=True, co_keo_ps=True,
            sg_dang=[
                dong_dang("youtube", "da_dang", ""),
                dong_dang("x", "da_dang", "", dang="x-goc"),
                dong_dang("threads", "that_bai", "upload loi", dang="threads-gia"),
            ],
            sg_kenh_bat="top5:youtube,threads-gia:threads", x_goc_bat=True, x_goc_ngay_1=NGAY,
        )
        self.assertEqual(chay_bu.quyet_dinh(tt_da_co, vn(13, 0)), [])
        # Luot thuong truot vi khong chon duoc game (thieu_keo=False) hoac da bu 1 lan -> []
        tt_ly_do_khac = chay_bu.TrangThai(
            ngay=NGAY, du_lieu_moi=True, co_keo_ps=True, sg_dang=[dong_dang("youtube", "da_dang", "")],
            sg_kenh_bat="top5:youtube,threads-gia:threads", x_goc_bat=True, x_goc_ngay_1=NGAY,
            x_goc_thieu_keo=False, tin_gia_thieu_keo={"threads": False},
        )
        self.assertEqual(chay_bu.quyet_dinh(tt_ly_do_khac, vn(13, 0)), [])
        tt_da_bu = chay_bu.TrangThai(
            ngay=NGAY, du_lieu_moi=True, co_keo_ps=True, sg_dang=[dong_dang("youtube", "da_dang", "")],
            sg_kenh_bat="top5:youtube,threads-gia:threads", x_goc_bat=True, x_goc_ngay_1=NGAY,
            so_lan_bu_x_goc=1, so_lan_bu_tin_gia={"threads": 1},
        )
        self.assertEqual(chay_bu.quyet_dinh(tt_da_bu, vn(13, 0)), [])


class ThucThiVaChongDuaTest(unittest.TestCase):
    def setUp(self):
        self.ntfy_loi = []
        self.ngu_ds = []
        self.gio = vn(11, 50)
        p_ntfy = mock.patch.object(ntfy, "loi", side_effect=lambda *a, **k: (self.ntfy_loi.append((a, k)), True)[1])
        p_ntfy.start()
        self.addCleanup(p_ntfy.stop)

    def ngu_gia(self, giay):
        self.ngu_ds.append(giay)
        self.gio += dt.timedelta(seconds=giay)

    def test_goi_hai_lan_lien_chi_mot_lan_dispatch_dung(self):
        cong = CongGia()
        for r in bo_5_kenh():
            cong.dong[(r["ngay"], r["dang"], r["kenh"], r["che_do"])] = dict(r)
        gh = GitHubGia(co_release=False)
        # Lan 1: mo khung + dispatch dung.yml (run o trang thai queued)
        kq1 = chay_bu.chay_mot_luot(
            cong=cong, gh=gh, du_lieu_moi=True, co_keo_ps=False, bay_gio_fn=lambda: self.gio, ngu_fn=self.ngu_gia,
            sg_dang_bat="top5", sg_kenh_bat="top5:youtube", x_goc_bat=False,
        )
        self.assertEqual(kq1, 0)
        self.assertEqual(len(gh.da_dispatch), 1)
        self.assertEqual(gh.da_dispatch[0][0], "dung.yml")
        for k in ("fb", "ig", "youtube", "tiktok", "x"):
            self.assertEqual(cong.dong[(NGAY, "top5", k, "that")]["trang_thai"], "that_bai")
        # Lan 2 goi ngay lap tuc: dang co luot dung xep hang + so_lan_dung_bu=1 -> KHONG dispatch them
        kq2 = chay_bu.chay_mot_luot(
            cong=cong, gh=gh, du_lieu_moi=True, co_keo_ps=False, bay_gio_fn=lambda: self.gio, ngu_fn=self.ngu_gia,
            sg_dang_bat="top5", sg_kenh_bat="top5:youtube", x_goc_bat=False,
        )
        self.assertEqual(kq2, 0)
        self.assertEqual(len(gh.da_dispatch), 1)

    def test_hai_luot_dua_nhau_so_va_dat_bo_sang_that_bai_chi_mot_luot_dispatch(self):
        cong = CongGia()
        for r in bo_5_kenh():
            cong.dong[(r["ngay"], r["dang"], r["kenh"], r["che_do"])] = dict(r)
        tt = chay_bu.TrangThai(ngay=NGAY, du_lieu_moi=True, co_release_top5=False, sg_dang=bo_5_kenh(), sg_kenh_bat="top5:youtube")
        ds_viec = chay_bu.quyet_dinh(tt, vn(11, 50))
        gh1, gh2 = GitHubGia(), GitHubGia()
        # Ca hai tien trinh cung nhan cung ds_viec tren snapshot cu va dua nhau thuc_thi:
        chay_bu.thuc_thi(ds_viec, cong, gh1, bay_gio_fn=lambda: self.gio, ngu_fn=self.ngu_gia)
        chay_bu.thuc_thi(ds_viec, cong, gh2, bay_gio_fn=lambda: self.gio, ngu_fn=self.ngu_gia)
        self.assertEqual(len(gh1.da_dispatch) + len(gh2.da_dispatch), 1)

    def test_dang_bu_top5_doi_chuan_bi_ngu_toi_gio_bu_va_dispatch_cong_khai_cung_gio_bu(self):
        self.gio = vn(13, 7)
        cong = CongGia()
        gh = GitHubGia(co_release=True, ket_qua_run=["success", "success", "success"])
        # Cung luot co ca Top 5 (can ngu toi 13:40) va Threads tin gia (dispatch ngay truoc khi ngu!)
        luc_dispatch = []
        goc_dispatch = gh.dispatch

        def theo_doi(wf, inp, luc=None):
            luc_dispatch.append((wf, inp.get("pha") or inp.get("kenh"), self.gio))
            return goc_dispatch(wf, inp, luc=self.gio)

        gh.dispatch = theo_doi
        kq = chay_bu.chay_mot_luot(
            cong=cong, gh=gh, du_lieu_moi=True, co_keo_ps=True, bay_gio_fn=lambda: self.gio, ngu_fn=self.ngu_gia,
            sg_dang_bat="top5", sg_kenh_bat="top5:youtube,threads-gia:threads", x_goc_bat=False,
        )
        self.assertEqual(kq, 0)
        # Thu tu: chuan-bi Top 5 luc 13:07 -> tin-gia-mxh threads luc 13:07 (TRUOC khi ngu!) -> ngu 33 phut -> cong-khai Top 5 luc 13:40
        self.assertEqual(
            [(wf, k, t) for wf, k, t in luc_dispatch],
            [
                ("dang.yml", "chuan-bi", vn(13, 7)),
                ("tin-gia-mxh.yml", "threads", vn(13, 7)),
                ("dang.yml", "cong-khai", vn(13, 40)),
            ],
        )
        self.assertEqual(gh.da_dispatch[0][1]["gio_bu"], "13:40")
        self.assertEqual(gh.da_dispatch[2][1]["gio_bu"], "13:40")
        self.assertEqual(self.ngu_ds, [33 * 60.0])
        self.assertEqual(self.ntfy_loi, [])

    def test_pha_chuan_bi_hong_thi_dung_khong_dispatch_cong_khai_va_ntfy(self):
        self.gio = vn(13, 7)
        cong = CongGia()
        gh = GitHubGia(co_release=True, ket_qua_run=["failure"])
        kq = chay_bu.chay_mot_luot(
            cong=cong, gh=gh, du_lieu_moi=True, co_keo_ps=False, bay_gio_fn=lambda: self.gio, ngu_fn=self.ngu_gia,
            sg_dang_bat="top5", sg_kenh_bat="top5:youtube", x_goc_bat=False,
        )
        self.assertEqual(kq, 1)
        self.assertEqual(len(gh.da_dispatch), 1)
        self.assertEqual(gh.da_dispatch[0][1]["pha"], "chuan-bi")
        self.assertEqual(self.ngu_ds, [])
        self.assertEqual(len(self.ntfy_loi), 1)

    def test_bo_ngay_qua_22h_thuc_thi_gui_ntfy(self):
        self.gio = vn(21, 50)
        cong = CongGia()
        gh = GitHubGia(co_release=True)
        kq = chay_bu.chay_mot_luot(
            cong=cong, gh=gh, du_lieu_moi=True, co_keo_ps=False, bay_gio_fn=lambda: self.gio, ngu_fn=self.ngu_gia,
            sg_dang_bat="top5", sg_kenh_bat="top5:youtube", x_goc_bat=False,
        )
        self.assertEqual(kq, 0)
        self.assertEqual(gh.da_dispatch, [])
        self.assertEqual(len(self.ntfy_loi), 1)
        self.assertIn("22:00", self.ntfy_loi[0][0][1])

    def test_loi_dispatch_tin_gia_khong_lam_dut_cong_khai_top5(self):
        self.gio = vn(13, 7)
        cong = CongGia()
        gh = GitHubGia(co_release=True, ket_qua_run=["success", "success"])
        goc_dispatch = gh.dispatch

        def dispatch_loi_threads(wf, inp, luc=None):
            if wf == "tin-gia-mxh.yml":
                raise chay_bu.LoiChayBu("HTTP 502 Bad Gateway")
            return goc_dispatch(wf, inp, luc=luc)

        gh.dispatch = dispatch_loi_threads
        kq = chay_bu.chay_mot_luot(
            cong=cong, gh=gh, du_lieu_moi=True, co_keo_ps=True, bay_gio_fn=lambda: self.gio, ngu_fn=self.ngu_gia,
            sg_dang_bat="top5", sg_kenh_bat="top5:youtube,threads-gia:threads", x_goc_bat=False,
        )
        # Top 5 van phai di tron chuan-bi -> ngu -> cong-khai; loi tin-gia duoc bao ntfy va ma thoat = 1
        self.assertEqual(kq, 1)
        self.assertEqual([x[0] for x in gh.da_dispatch], ["dang.yml", "dang.yml"])
        self.assertEqual([x[1]["pha"] for x in gh.da_dispatch], ["chuan-bi", "cong-khai"])
        self.assertEqual(len(self.ntfy_loi), 1)

    def test_cong_tu_choi_doi_bo_sang_that_bai_thi_bao_loi_khong_dispatch_dung_nhung_van_chay_threads(self):
        from dang.so import LoiCong
        self.gio = vn(12, 10)
        cong = CongGia()
        for r in bo_5_kenh():
            cong.dong[(r["ngay"], r["dang"], r["kenh"], r["che_do"])] = dict(r)
        cong.hong_ghi_sau = lambda kenh, truong: truong.get("trang_thai") == "that_bai"
        gh = GitHubGia(co_release=False)
        kq = chay_bu.chay_mot_luot(
            cong=cong, gh=gh, du_lieu_moi=True, co_keo_ps=True, bay_gio_fn=lambda: self.gio, ngu_fn=self.ngu_gia,
            sg_dang_bat="top5", sg_kenh_bat="top5:youtube,threads-gia:threads", x_goc_bat=False,
        )
        self.assertEqual(kq, 1)
        # Khong dispatch dung.yml (vi khung van bo), nhung threads-gia doc lap van duoc dispatch
        self.assertEqual([x[0] for x in gh.da_dispatch], ["tin-gia-mxh.yml"])
        self.assertEqual(len(self.ntfy_loi), 1)


class DocTrangThaiVaGitHubClientTest(unittest.TestCase):
    def test_cron_dang_tre_11_42_truoc_khi_co_release_khong_bi_tinh_la_da_dang_bu(self):
        cong = CongGia()
        for r in bo_5_kenh():
            cong.dong[(r["ngay"], r["dang"], r["kenh"], r["che_do"])] = dict(r)
        # Run dang.yml cua cron-job.org bi tre sang 11:42 VN (04:42Z), nhung Release ra luc 12:15 VN (05:15Z)
        runs = {
            "dang.yml": [{
                "id": 501, "status": "completed", "conclusion": "failure",
                "created_at": "2026-11-22T04:42:00Z", "_inputs": {"pha": "chuan-bi"},
            }],
        }
        gh = GitHubGia(co_release=True, runs=runs)
        gh.release_tao_luc = vn(12, 15)
        gh.thong_tin_release = lambda tag: (True, vn(12, 15))
        tt = chay_bu.doc_trang_thai(
            ngay=NGAY, cong=cong, gh=gh, du_lieu_moi=True, co_keo_ps=False,
            sg_dang_bat="top5", sg_kenh_bat="top5:youtube", x_goc_bat=False,
        )
        self.assertEqual(tt.so_lan_dang_bu_top5, 0)
        ds = chay_bu.quyet_dinh(tt, vn(12, 20))
        self.assertEqual([v.loai for v in ds], ["mo_khung", "dang_bu_top5"])

    def _tt_dung_thuong_1045(self, chon_ket_luan):
        """Luot dung.yml THUONG cua cron 10:45 VN (03:45Z): chon_ket_luan='skipped' = thoat o kiem-moi vi du lieu cu;
        'failure' = da dung voi du lieu moi va truot (kiem noi dung / ha tang)."""
        cong = CongGia()
        for r in bo_5_kenh():
            cong.dong[(r["ngay"], r["dang"], r["kenh"], r["che_do"])] = dict(r)
        ket_luan_run = "success" if chon_ket_luan == "skipped" else "failure"
        runs = {"dung.yml": [{
            "id": 701, "status": "completed", "conclusion": ket_luan_run, "created_at": "2026-11-22T03:45:00Z",
            "_jobs": [{"name": "kiem-moi", "conclusion": "success"}, {"name": "chon", "conclusion": chon_ket_luan}],
        }]}
        gh = GitHubGia(co_release=False, runs=runs)
        return chay_bu.doc_trang_thai(
            ngay=NGAY, cong=cong, gh=gh, du_lieu_moi=True, co_keo_ps=False,
            sg_dang_bat="top5", sg_kenh_bat="top5:youtube", x_goc_bat=False,
        )

    def test_luot_thuong_1045_da_dung_that_roi_truot_thi_khong_dung_bu(self):
        # 22/11 Claude soi: lượt 10:45 đã dựng với dữ liệu mới (job chon chạy) mà trượt -> 11:35 vẫn ghi `bo` "khong co Release".
        # Lý do thật là trượt khi dựng, không phải thiếu dữ liệu -> KHÔNG mở khung, KHÔNG dựng bù.
        tt = self._tt_dung_thuong_1045("failure")
        self.assertEqual(chay_bu.quyet_dinh(tt, vn(13, 7)), [])

    def test_luot_thuong_1045_thoat_vi_du_lieu_cu_thi_van_dung_bu(self):
        # Ca thật 22/11: 10:45 thoát ở kiem-moi (chon skipped), dữ liệu về 11:28 -> mở khung + dựng bù.
        tt = self._tt_dung_thuong_1045("skipped")
        self.assertEqual([v.loai for v in chay_bu.quyet_dinh(tt, vn(13, 7))], ["mo_khung", "dung_bu"])

    def test_luot_dung_bi_huy_tay_khong_tinh_la_da_dung_bu(self):
        # Ca thật 22/11: Claude gọi tay dung.yml 11:28 rồi huỷ (cancelled) -> không phải một lần dựng bù đã thử.
        cong = CongGia()
        for r in bo_5_kenh():
            cong.dong[(r["ngay"], r["dang"], r["kenh"], r["che_do"])] = dict(r)
        runs = {"dung.yml": [{"id": 702, "status": "completed", "conclusion": "cancelled", "created_at": "2026-11-22T04:28:53Z",
                              "_jobs": [{"name": "kiem-moi", "conclusion": "success"}, {"name": "chon", "conclusion": "cancelled"}]}]}
        tt = chay_bu.doc_trang_thai(ngay=NGAY, cong=cong, gh=GitHubGia(runs=runs), du_lieu_moi=True, co_keo_ps=False,
                                    sg_dang_bat="top5", sg_kenh_bat="top5:youtube", x_goc_bat=False)
        self.assertEqual(tt.so_lan_dung_bu_top5, 0)
        self.assertEqual([v.loai for v in chay_bu.quyet_dinh(tt, vn(13, 20))], ["mo_khung", "dung_bu"])

    def test_github_client_dispatch_va_fallback_204_va_che_token(self):
        tk = "ghs_TOKEN_BI_MAT_9876543210abcdef"
        m = Mang()
        m.them("GET", "/releases/tags/v-2026-11-22-top5", P(200, {"draft": False, "published_at": "2026-11-22T05:10:00Z"}))
        m.them("GET", "/workflows/dung.yml/runs", [
            P(200, {"workflow_runs": [{"id": 10, "status": "completed", "event": "workflow_dispatch", "created_at": "2026-11-22T03:15:00Z"}]}),
            P(200, {"workflow_runs": [
                {"id": 11, "status": "queued", "event": "workflow_dispatch", "created_at": "2026-11-22T05:20:02Z"},
                {"id": 10, "status": "completed", "event": "workflow_dispatch", "created_at": "2026-11-22T03:15:00Z"},
            ]}),
        ])
        m.them("POST", "/workflows/dung.yml/dispatches", P(204, raw=b""))
        m.them("GET", "/actions/runs/11", [
            P(200, {"id": 11, "status": "in_progress", "conclusion": None}),
            P(200, {"id": 11, "status": "completed", "conclusion": "success"}),
        ])
        gio = [vn(12, 20)]
        with mock.patch.object(http, "gui", m):
            gh = chay_bu.GitHubClient(repo="thenail1995-create/sangame-video", token=tk,
                                      ngu_fn=lambda s: gio.__setitem__(0, gio[0] + dt.timedelta(seconds=s)),
                                      bay_gio_fn=lambda: gio[0])
            self.assertEqual(gh.thong_tin_release("v-2026-11-22-top5"), (True, dt.datetime(2026, 11, 22, 5, 10, tzinfo=dt.timezone.utc)))
            rid = gh.dispatch("dung.yml", {"dang": "top5"}, luc=vn(12, 20))
            self.assertEqual(rid, 11)
            kq = gh.doi_run(11)
            self.assertEqual(kq["conclusion"], "success")
        self.assertNotIn(tk, chung.che(f"Bearer {tk} va {tk}"))

    def test_main_du_lieu_cu_thoat_0_khong_goi_cong(self):
        with tempfile.TemporaryDirectory() as d:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                rc = chay_bu.main(["--ngay", NGAY, "--du-lieu", d])
            self.assertEqual(rc, 0)
            self.assertIn("chua co du lieu moi", buf.getvalue())


def run_gia(rid, gio_vn, ten, status="completed", conclusion="success", **them):
    return {"id": rid, "status": status, "conclusion": conclusion if status == "completed" else None,
            "event": "workflow_dispatch", "created_at": chung.iso(gio_vn), "display_title": ten, "name": ten, **them}


class SoiCheo2211Test(unittest.TestCase):
    """22/11 soi chéo độc lập: 5 lỗi, mỗi lỗi một phép thử tái hiện."""

    def _tt(self, runs, sg_dang=None, co_release=False, rel_luc=None):
        cong = CongGia()
        for r in (bo_5_kenh() if sg_dang is None else sg_dang):
            cong.dong[(r["ngay"], r["dang"], r["kenh"], r["che_do"])] = dict(r)
        gh = GitHubGia(co_release=co_release, runs=runs)
        if co_release:
            gh.thong_tin_release = lambda tag: (True, rel_luc or vn(14, 30))
        return chay_bu.doc_trang_thai(ngay=NGAY, cong=cong, gh=gh, du_lieu_moi=True, co_keo_ps=False,
                                      sg_dang_bat="top5,flagship", sg_kenh_bat="top5:youtube", x_goc_bat=False)

    # --- Lỗi 1: lượt của khung khác (flagship 13:35/14:05) bị đếm là "đã dựng bù / đã đăng bù Top 5"
    def test_luot_dung_flagship_co_nhan_khong_tinh_la_dung_bu_top5(self):
        runs = {"dung.yml": [run_gia(801, vn(13, 35), "Dung video [flagship that]", conclusion="failure")]}
        tt = self._tt(runs)
        self.assertEqual(tt.so_lan_dung_bu_top5, 0)
        self.assertEqual([v.loai for v in chay_bu.quyet_dinh(tt, vn(15, 30))], ["mo_khung", "dung_bu"])

    def test_luot_dung_cu_chua_nhan_sau_10_50_la_khung_khac_khong_tinh(self):
        # Ca thật 22/11: 13:35 và 14:05 "Dung video" (chưa có nhãn) thất bại -> chạy khô 15:30 chỉ còn Threads
        runs = {"dung.yml": [run_gia(803, vn(14, 5), "Dung video", conclusion="failure"),
                             run_gia(802, vn(13, 35), "Dung video", conclusion="failure")]}
        tt = self._tt(runs)
        self.assertEqual(tt.so_lan_dung_bu_top5, 0)
        self.assertEqual([v.loai for v in chay_bu.quyet_dinh(tt, vn(15, 30))], ["mo_khung", "dung_bu"])

    def test_luot_dung_top5_that_co_nhan_sau_10_50_van_tinh(self):
        runs = {"dung.yml": [run_gia(804, vn(13, 0), "Dung video [top5 that]", conclusion="failure")]}
        self.assertEqual(self._tt(runs).so_lan_dung_bu_top5, 1)

    def test_luot_dung_top5_thu_khong_tinh(self):
        runs = {"dung.yml": [run_gia(805, vn(13, 0), "Dung video [top5 thu]", conclusion="failure")]}
        self.assertEqual(self._tt(runs).so_lan_dung_bu_top5, 0)

    def test_luot_dang_flagship_sau_release_khong_tinh_la_dang_bu_top5(self):
        runs = {"dang.yml": [run_gia(811, vn(15, 5), "Dang video [chuan-bi flagship that]", conclusion="failure")]}
        tt = self._tt(runs, co_release=True, rel_luc=vn(14, 30))
        self.assertEqual(tt.so_lan_dang_bu_top5, 0)
        self.assertEqual([v.loai for v in chay_bu.quyet_dinh(tt, vn(15, 20))], ["mo_khung", "dang_bu_top5"])

    def test_luot_dang_top5_chuan_bi_co_nhan_sau_release_van_tinh(self):
        runs = {"dang.yml": [run_gia(812, vn(15, 5), "Dang video [chuan-bi top5 that bu 15:35]", conclusion="failure",
                                     _inputs={"pha": "chuan-bi"})]}
        self.assertEqual(self._tt(runs, co_release=True, rel_luc=vn(14, 30)).so_lan_dang_bu_top5, 1)

    def test_luot_dung_flagship_dang_chay_khong_chan_top5(self):
        runs = {"dung.yml": [run_gia(806, vn(13, 35), "Dung video [flagship that]", status="in_progress")]}
        self.assertFalse(self._tt(runs).dung_top5_dang_chay)

    # --- Lỗi 2: chuẩn bị xong mà mất dấu, không có lượt công khai -> khung kẹt ở chuan_bi_xong cả ngày
    def _ke_chuan_bi_xong(self, runs, bay):
        sg = [dong_dang(k, "chuan_bi_xong", None) for k in ("youtube",)] + [dong_dang(k, "bo") for k in ("fb", "ig", "tiktok", "x")]
        tt = self._tt(runs, sg_dang=sg, co_release=True, rel_luc=vn(14, 30))
        return tt, chay_bu.quyet_dinh(tt, bay)

    def test_chuan_bi_bu_xong_mat_cong_khai_thi_cong_khai_lai_cung_gio_bu(self):
        runs = {"dang.yml": [run_gia(821, vn(14, 40), "Dang video [chuan-bi top5 that bu 15:10]", _inputs={"pha": "chuan-bi"})]}
        tt, ds = self._ke_chuan_bi_xong(runs, vn(15, 30))
        self.assertEqual(tt.cho_cong_khai_top5, "15:10")
        self.assertEqual([v.loai for v in ds], ["cong_khai_bu_top5"])
        self.assertEqual(ds[0].inputs, {"pha": "cong-khai", "dang": "top5", "ngay": NGAY, "che_do": "that", "gio_bu": "15:10"})

    def test_chuan_bi_thuong_1135_mat_cong_khai_12h_thi_cong_khai_lai_khong_gio_bu(self):
        runs = {"dang.yml": [run_gia(822, vn(11, 35), "Dang video [chuan-bi top5 that]", _inputs={"pha": "chuan-bi"})]}
        _tt, ds = self._ke_chuan_bi_xong(runs, vn(12, 20))
        self.assertEqual([v.loai for v in ds], ["cong_khai_bu_top5"])
        self.assertEqual(ds[0].inputs["gio_bu"], "")

    def test_chua_toi_gio_cong_khai_thuong_thi_khong_cong_khai_lai(self):
        runs = {"dang.yml": [run_gia(823, vn(11, 35), "Dang video [chuan-bi top5 that]", _inputs={"pha": "chuan-bi"})]}
        self.assertEqual(self._ke_chuan_bi_xong(runs, vn(11, 50))[1], [])
        self.assertEqual(self._ke_chuan_bi_xong(runs, vn(12, 10))[1], [])

    def test_da_co_luot_cong_khai_sau_chuan_bi_thi_khong_cong_khai_lai(self):
        runs = {"dang.yml": [
            run_gia(825, vn(15, 10), "Dang video [cong-khai top5 that bu 15:10]", conclusion="failure", _inputs={"pha": "cong-khai"}),
            run_gia(824, vn(14, 40), "Dang video [chuan-bi top5 that bu 15:10]", _inputs={"pha": "chuan-bi"}),
        ]}
        tt, ds = self._ke_chuan_bi_xong(runs, vn(15, 30))
        self.assertIsNone(tt.cho_cong_khai_top5)
        self.assertEqual(ds, [])

    def test_qua_cua_so_80_phut_thi_khong_cong_khai_lai(self):
        runs = {"dang.yml": [run_gia(826, vn(14, 40), "Dang video [chuan-bi top5 that bu 15:10]", _inputs={"pha": "chuan-bi"})]}
        self.assertEqual(self._ke_chuan_bi_xong(runs, vn(16, 35))[1], [])

    def test_chuan_bi_het_gio_thi_khong_cong_khai_lai(self):
        # failure (do một phần) thì vẫn công khai lại - xem SoiCheo2211Vong2Test; timed_out/cancelled thì không
        runs = {"dang.yml": [run_gia(827, vn(14, 40), "Dang video [chuan-bi top5 that bu 15:10]", conclusion="timed_out",
                                     _inputs={"pha": "chuan-bi"})]}
        self.assertEqual(self._ke_chuan_bi_xong(runs, vn(15, 30))[1], [])

    def test_doi_run_chiu_duoc_loi_tam_thoi(self):
        m = Mang()
        m.them("GET", "/actions/runs/11", [
            P(502, {}),
            P(200, {"id": 11, "status": "in_progress", "conclusion": None}),
            P(503, {}),
            P(200, {"id": 11, "status": "completed", "conclusion": "success"}),
        ])
        gio = [vn(12, 20)]
        with mock.patch.object(http, "gui", m):
            gh = chay_bu.GitHubClient(repo="thenail1995-create/sangame-video", token="ghs_x",
                                      ngu_fn=lambda s: gio.__setitem__(0, gio[0] + dt.timedelta(seconds=s)),
                                      bay_gio_fn=lambda: gio[0])
            self.assertEqual(gh.doi_run(11)["conclusion"], "success")

    def test_doi_run_loi_lien_tiep_qua_nhieu_thi_dung(self):
        m = Mang()
        m.them("GET", "/actions/runs/11", [P(502, {})] * 10)
        gio = [vn(12, 20)]
        with mock.patch.object(http, "gui", m):
            gh = chay_bu.GitHubClient(repo="thenail1995-create/sangame-video", token="ghs_x",
                                      ngu_fn=lambda s: gio.__setitem__(0, gio[0] + dt.timedelta(seconds=s)),
                                      bay_gio_fn=lambda: gio[0])
            with self.assertRaises(chay_bu.LoiChayBu):
                gh.doi_run(11)

    # --- Lỗi 3: chuẩn bị chạy lâu -> công khai sau 22:00
    def test_chuan_bi_xong_sau_22_15_thi_khong_cong_khai(self):
        ntfy_ds = []
        gio = [vn(21, 40)]
        with mock.patch.object(ntfy, "loi", side_effect=lambda *a, **k: (ntfy_ds.append(a), True)[1]):
            gh = GitHubGia(co_release=True)
            orig = gh.doi_run

            def doi_lau(rid, toi_da_giay=2700):
                gio[0] = vn(22, 20)   # chuẩn bị chạy 40 phút
                return orig(rid, toi_da_giay)
            gh.doi_run = doi_lau
            v = chay_bu.Viec(loai="dang_bu_top5", dang="top5", workflow="dang.yml", gio_bu="22:00",
                             inputs={"dang": "top5", "ngay": NGAY, "che_do": "that", "gio_bu": "22:00"})
            rc = chay_bu.thuc_thi([v], CongGia(), gh, bay_gio_fn=lambda: gio[0], ngu_fn=lambda s: None)
        self.assertEqual(rc, 1)
        self.assertEqual([i.get("pha") for _w, i in gh.da_dispatch], ["chuan-bi"])
        self.assertTrue(any("22" in str(a) for a in ntfy_ds))

    def test_thuc_thi_cong_khai_bu_top5_dispatch_va_doi(self):
        gh = GitHubGia(co_release=True)
        v = chay_bu.Viec(loai="cong_khai_bu_top5", dang="top5", workflow="dang.yml", gio_bu="15:10",
                         inputs={"pha": "cong-khai", "dang": "top5", "ngay": NGAY, "che_do": "that", "gio_bu": "15:10"})
        rc = chay_bu.thuc_thi([v], CongGia(), gh, bay_gio_fn=lambda: vn(15, 30), ngu_fn=lambda s: None)
        self.assertEqual(rc, 0)
        self.assertEqual(gh.da_dispatch, [("dang.yml", v.inputs)])

    # --- Lỗi 4: lượt 21:50 thoát sớm (dữ liệu cũ) không được coi là đã báo "bỏ ngày"
    def test_luot_chay_bu_sau_21_31_khong_bao_gi_thi_chua_tinh_da_bao(self):
        runs = {"chay-bu.yml": [run_gia(831, vn(21, 50), "Chay bu San Game", _log="chay_bu: chua co du lieu moi -> khong lam gi")]}
        self.assertEqual(self._tt(runs).da_bao, set())

    def test_luot_chay_bu_da_bao_qua_22h_thi_tinh_dung_muc_da_bao(self):
        runs = {"chay-bu.yml": [run_gia(832, vn(22, 20), "Chay bu San Game",
                                        _log="... chay_bu: DA_BAO qua-22h:top5\n... chay_bu: DA_BAO qua-22h:threads-gia\n")]}
        self.assertEqual(self._tt(runs).da_bao, {"qua-22h:top5", "qua-22h:threads-gia"})

    def test_bo_ngay_ghi_dau_da_bao_vao_log(self):
        buf = io.StringIO()
        with mock.patch.object(ntfy, "loi", return_value=True), contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            chay_bu.thuc_thi([chay_bu.Viec(loai="bo_ngay", dang="top5", ly_do="qua 22h")], CongGia(), GitHubGia(),
                             bay_gio_fn=lambda: vn(22, 20), ngu_fn=lambda s: None)
        self.assertIn("DA_BAO qua-22h:top5", buf.getvalue())


class SoiCheo2211Vong2Test(unittest.TestCase):
    """Vòng 2 soi chéo: chuẩn bị đỏ một phần vẫn công khai các kênh đã chuan_bi_xong (giống lịch 12:00); DA_BAO chỉ khi ntfy gửi được."""

    def _cong(self, tt_youtube):
        cong = CongGia()
        for k, t in (("youtube", tt_youtube), ("fb", "that_bai")):
            r = dong_dang(k, t, None)
            cong.dong[(r["ngay"], r["dang"], r["kenh"], r["che_do"])] = r
        return cong

    def _chay(self, cong):
        gh = GitHubGia(co_release=True, ket_qua_run=["failure", "success"])
        v = chay_bu.Viec(loai="dang_bu_top5", dang="top5", workflow="dang.yml", gio_bu="15:10",
                         inputs={"dang": "top5", "ngay": NGAY, "che_do": "that", "gio_bu": "15:10"})
        with mock.patch.object(ntfy, "loi", return_value=True):
            rc = chay_bu.thuc_thi([v], cong, gh, bay_gio_fn=lambda: vn(15, 10), ngu_fn=lambda s: None)
        return rc, [i.get("pha") for _w, i in gh.da_dispatch]

    def test_chuan_bi_do_mot_phan_van_cong_khai_kenh_da_san_sang(self):
        rc, pha = self._chay(self._cong("chuan_bi_xong"))
        self.assertEqual(pha, ["chuan-bi", "cong-khai"])
        self.assertEqual(rc, 1)   # vẫn báo đỏ vì chuẩn bị có kênh lỗi

    def test_chuan_bi_do_khong_kenh_nao_san_sang_thi_khong_cong_khai(self):
        rc, pha = self._chay(self._cong("that_bai"))
        self.assertEqual(pha, ["chuan-bi"])
        self.assertEqual(rc, 1)

    def test_cong_khai_lai_nhan_ca_chuan_bi_do_mot_phan(self):
        cong = self._cong("chuan_bi_xong")
        runs = {"dang.yml": [run_gia(851, vn(14, 40), "Dang video [chuan-bi top5 that bu 15:10]", conclusion="failure",
                                     _inputs={"pha": "chuan-bi"})]}
        gh = GitHubGia(co_release=True, runs=runs)
        gh.thong_tin_release = lambda tag: (True, vn(14, 30))
        tt = chay_bu.doc_trang_thai(ngay=NGAY, cong=cong, gh=gh, du_lieu_moi=True, co_keo_ps=False,
                                    sg_dang_bat="top5", sg_kenh_bat="top5:youtube", x_goc_bat=False)
        self.assertEqual(tt.cho_cong_khai_top5, "15:10")
        self.assertEqual([v.loai for v in chay_bu.quyet_dinh(tt, vn(15, 30))], ["cong_khai_bu_top5"])

    def test_chuan_bi_bi_huy_thi_khong_cong_khai_lai(self):
        cong = self._cong("chuan_bi_xong")
        runs = {"dang.yml": [run_gia(852, vn(14, 40), "Dang video [chuan-bi top5 that bu 15:10]", conclusion="cancelled",
                                     _inputs={"pha": "chuan-bi"})]}
        gh = GitHubGia(co_release=True, runs=runs)
        gh.thong_tin_release = lambda tag: (True, vn(14, 30))
        tt = chay_bu.doc_trang_thai(ngay=NGAY, cong=cong, gh=gh, du_lieu_moi=True, co_keo_ps=False,
                                    sg_dang_bat="top5", sg_kenh_bat="top5:youtube", x_goc_bat=False)
        self.assertIsNone(tt.cho_cong_khai_top5)

    def test_ntfy_hong_thi_khong_ghi_da_bao(self):
        buf = io.StringIO()
        with mock.patch.object(ntfy, "loi", return_value=False), contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            chay_bu.thuc_thi([chay_bu.Viec(loai="bo_ngay", dang="top5", ly_do="qua 22h")], CongGia(), GitHubGia(),
                             bay_gio_fn=lambda: vn(22, 20), ngu_fn=lambda s: None)
        self.assertNotIn("DA_BAO", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
