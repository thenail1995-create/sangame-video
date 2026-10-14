# 15/10/2026: Tin nhanh 15/10 truot D3 — moc «Spec IV» (GT7), giong doc «bốn», Whisper turbo viet «Specs 4» -> 'iv' != 'bon', diem 0,50.
#   uv run --frozen python -m pytest khuon/tin-nhanh/test_so_la_ma.py -q
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import so_chu as sc


def test_spec_iv_va_specs_4_cung_ve_bon():
    assert sc.chuan_so_sanh('Spec IV') == ['spec', 'bon']
    assert sc.chuan_so_sanh('Tin 3, Part 1 miễn phí, tay cầm GT, bán 10 tháng 12, Specs 4.')[-2:] == ['specs', 'bon']


def test_so_la_ma_khac():
    assert sc.chuan_so_sanh('Final Fantasy VII') == ['final', 'fantasy', 'bay']
    assert sc.chuan_so_sanh('Kingdom Hearts III') == ['kingdom', 'hearts', 'ba']


def test_khong_doi_chu_cai_don_va_chu_thuong():
    assert sc.chuan_so_sanh('Grand Theft Auto V') == ['grand', 'theft', 'auto', 'v']
    assert sc.chuan_so_sanh('phiên bản X') == ['phien', 'ban', 'x']
    assert sc.chuan_so_sanh('vi du iv') == ['vi', 'du', 'iv']
    assert sc.chuan_so_sanh('VIP') == ['vip']
