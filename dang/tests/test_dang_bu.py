"""Dang bu (12/10): DANG_BU_GIO=HH:MM thay gio dang cua manifest, cung ngay; sai dinh dang -> loi; rong -> gio manifest."""
import datetime as dt
import pytest
from dang import manifest

MAN = {"gio_dang": "2026-10-12T07:30:00+07:00"}


def test_rong_giu_gio_manifest(monkeypatch):
    monkeypatch.delenv("DANG_BU_GIO", raising=False)
    assert manifest.gio_dang(MAN) == dt.datetime.fromisoformat("2026-10-12T07:30:00+07:00")


def test_bu_doi_gio_cung_ngay_cung_mui(monkeypatch):
    monkeypatch.setenv("DANG_BU_GIO", "14:05")
    g = manifest.gio_dang(MAN)
    assert g == dt.datetime.fromisoformat("2026-10-12T14:05:00+07:00")


@pytest.mark.parametrize("sai", ["24:00", "7:30", "14h05", "2026-10-12T14:05"])
def test_bu_sai_dinh_dang(monkeypatch, sai):
    monkeypatch.setenv("DANG_BU_GIO", sai)
    with pytest.raises(manifest.LoiManifest):
        manifest.gio_dang(MAN)
