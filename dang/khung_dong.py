"""Truoc khi DUNG che_do=that: so sg_dang da DONG khung (ngay, dang) nay chua? Dong roi thi KHONG dung -> khong tao Release mo coi.

Vi sao (SG-TOP5-hong, 30/10/2026): 29/10 Top 5 truot 10:15 + 10:45, 12:00 ghi `bo` ca 5 kenh. Run 40898972729 dung lai 22:11, tao
Release v-2026-10-29-top5 nhung "Dang video" 22:40 bo qua ("sg_dang da co dong cho khung nay") vi sg_giu_dang CHI mo lai dong
`that_bai`. Release do khong bao gio len.

Luat: khung DONG khi co it nhat 1 dong che_do=that cua (ngay, dang) mang trang thai khac `that_bai` (bo, da_dang, dang_dang,
chuan_bi_xong, khong_ro). Chua co dong nao, hoac moi dong deu `that_bai` (may dang se thu lai) -> MO, dung binh thuong.
Dang bu hop le: doi cac dong cua khung sang `that_bai` TRUOC (Hao duyet), roi moi chay dung + dang.
Cong loi / thieu khoa -> coi la MO (khong chan lich dung binh thuong 10:15/10:45 vi su co mang), in canh bao.

  python -m dang.khung_dong --ngay YYYY-MM-DD --dang top5 [--github-output]   -> in dong=0|1; ma thoat luon 0
"""
import argparse
import os

from . import chung, so

MO_LAI = "that_bai"   # trang thai duy nhat sg_giu_dang cho giu lai


def khung_da_dong(cong, ngay, dang):
    """-> (dong: bool, danh sach 'kenh=trang_thai' cua cac dong chan)."""
    j = cong.goi("doc_dang", tu=ngay, den=ngay, che_do="that")
    chan = [f"{r.get('kenh')}={r.get('trang_thai')}" for r in (j.get("dong") or [])
            if r.get("ngay") == ngay and r.get("dang") == dang and r.get("che_do") == "that" and r.get("trang_thai") != MO_LAI]
    return bool(chan), chan


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--ngay", required=True)
    p.add_argument("--dang", required=True)
    p.add_argument("--github-output", action="store_true")
    a = p.parse_args(argv)
    try:
        dong, chan = khung_da_dong(so.Cong(), a.ngay, a.dang)
    except Exception as e:   # noqa: BLE001 - moi loi cong = MO (fail-open co chu dich, xem docstring)
        chung.log(f"khung_dong: KHONG doc duoc sg_dang ({chung.cat(str(e), 200)}) -> coi la MO, dung tiep")
        dong, chan = False, []
    if dong:
        chung.log(f"khung_dong: {a.dang} {a.ngay} DA DONG trong sg_dang ({', '.join(chan)}) -> KHONG dung (tranh Release mo coi). "
                  f"Dang bu: doi cac dong nay sang '{MO_LAI}' truoc roi chay lai.")
    else:
        chung.log(f"khung_dong: {a.dang} {a.ngay} chua dong -> dung tiep")
    if a.github_output and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"dong={1 if dong else 0}\n")
    print(f"dong={1 if dong else 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
