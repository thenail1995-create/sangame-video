"""Dung thu muc site cho GitHub Pages: video reels + bia cua Release 2 ngay gan nhat (cung che do), duong dan bat bien v/<ngay>-<dang>-<sha8>.mp4.
Chay trong workflow (job khong co secret):  python -m dang.site --ra _site --ngay 2026-10-12 --dang top5
Ghi sha8 vao $GITHUB_OUTPUT. Trang Pages gioi han ~1 GB nen cat bot ban cu (tru ban dich) khi vuot SITE_TOI_DA_MB (mac dinh 800).
"""
import argparse
import datetime as dt
import os
import pathlib
import re
import shutil
import sys

from . import chung, http, manifest

SO_NGAY = 2   # HOP-DONG muc 1: Pages chi giu video 2 ngay gan nhat


def ten_tep(ngay, dang, sha256, duoi):
    return f"{ngay}-{dang}-{sha256[:8]}.{duoi}"


def url_cong_khai(goc, ngay, dang, man):
    r = man["ban"]["reels"]
    return (f"{goc.rstrip('/')}/v/{ten_tep(ngay, dang, r['sha256'], 'mp4')}",
            f"{goc.rstrip('/')}/v/{ten_tep(ngay, dang, r['sha256'], 'jpg')}")


def _danh_sach_tag(repo, tu, den, che_do="that"):
    r = http.gui("GET", f"{manifest.API}/repos/{repo}/releases", headers=manifest._hdr_api(), params={"per_page": 50}, timeout=30)
    if r.status != 200:
        raise manifest.LoiManifest(f"liet ke Release: HTTP {r.status}")
    ra = []
    for rel in r.json():
        m = re.fullmatch(r"%s-(\d{4}-\d{2}-\d{2})-(tin-nhanh|top5|keo-thom-2|keo-thom-3|keo-thom|flagship)" % ("thu" if che_do == "thu" else "v"),
                         str(rel.get("tag_name", "")))
        if m and tu <= m.group(1) <= den:
            ra.append((m.group(1), m.group(2)))
    return sorted(ra, reverse=True)


def dung(thu_muc_ra, ngay, dang, repo=None, so_ngay=SO_NGAY, toi_da_mb=None, che_do="that"):
    repo = repo or manifest.REPO
    toi_da = int((toi_da_mb or float(os.environ.get("SITE_TOI_DA_MB", "800"))) * 1024 * 1024)
    ra = pathlib.Path(thu_muc_ra)
    (ra / "v").mkdir(parents=True, exist_ok=True)
    (ra / ".nojekyll").write_text("")
    (ra / "index.html").write_text('<!doctype html><meta charset="utf-8"><title>sangame-video</title>sangame-video')
    d0 = dt.date.fromisoformat(ngay)
    tu, den = (d0 - dt.timedelta(days=so_ngay - 1)).isoformat(), d0.isoformat()
    ung_vien = [(ngay, dang)] + [t for t in _danh_sach_tag(repo, tu, den, che_do) if t != (ngay, dang)]
    tong, sha_dich = 0, None
    tam = ra / "_tam"
    for n, d in ung_vien:
        la_dich = (n, d) == (ngay, dang)
        try:
            man = manifest.tai_release(n, d, tam, ("reels",) if not la_dich else manifest.BAN, repo, che_do)
            if la_dich:   # ban dich: kiem day du nhu may dang TRUOC khi cho len Pages (Sol: khong cong khai tai san chua qua cong)
                manifest.kiem(man, tam, n, d, che_do)
            r = man["ban"]["reels"]
            for k, sk in (("video", "sha256"), ("bia", "bia_sha256")):
                if chung.sha256_tep(tam / r[k]) != r[sk]:
                    raise manifest.LoiManifest(f"sha256 {r[k]} khong khop")
        except manifest.LoiManifest as e:
            if la_dich:
                raise
            chung.log(f"site: bo {n}-{d}: {e}")
            continue
        kich = (tam / r["video"]).stat().st_size + (tam / r["bia"]).stat().st_size
        if not la_dich and tong + kich > toi_da:
            chung.log(f"site: bo {n}-{d}: vuot tran {toi_da // 1048576} MB")
            continue
        tong += kich
        shutil.move(str(tam / r["video"]), ra / "v" / ten_tep(n, d, r["sha256"], "mp4"))
        shutil.move(str(tam / r["bia"]), ra / "v" / ten_tep(n, d, r["sha256"], "jpg"))
        if la_dich:
            sha_dich = r["sha256"][:8]
    shutil.rmtree(tam, ignore_errors=True)
    chung.log(f"site: {len(list((ra / 'v').glob('*.mp4')))} video, {tong // 1048576} MB")
    return sha_dich


def kiem_url(url, kieu="video/mp4", lan=12, nghi=10):
    """HEAD khong theo chuyen huong: phai 200 + content-type dung (tuong duong curl -sI)."""
    cuoi = ""
    for i in range(lan):
        try:
            r = http.gui("HEAD", url, timeout=30)
            ct = r.headers.get("content-type", "").split(";")[0].strip().lower()
            if r.status == 200 and ct == kieu:
                return True
            cuoi = f"HTTP {r.status} {ct}"
        except http.LoiMang as e:
            cuoi = str(e)
        chung.ngu(nghi)
    raise chung.LoiDang(f"URL cong khai {url} khong dat (200, {kieu}): {cuoi}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ra", required=True)
    ap.add_argument("--ngay", required=True)
    ap.add_argument("--dang", required=True)
    ap.add_argument("--che-do", dest="che_do", choices=["thu", "that"], default="that")
    a = ap.parse_args(argv)
    try:
        sha8 = dung(a.ra, a.ngay, a.dang, che_do=a.che_do)
    except manifest.LoiManifest as e:
        chung.log_loi(f"site: {e}")
        return 1
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"sha8={sha8}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
