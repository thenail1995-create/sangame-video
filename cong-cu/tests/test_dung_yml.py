"""Gói A2-A7 (Sol #1 #2 #3 #21 #23 #24): kiem tinh dung.yml (khong chay duoc CI that o day)."""
import pathlib, re, unittest

Y = (pathlib.Path(__file__).resolve().parents[2] / '.github/workflows/dung.yml').read_text(encoding='utf-8')
TATCA = {p.name: p.read_text(encoding='utf-8') for p in (pathlib.Path(__file__).resolve().parents[2] / '.github/workflows').glob('*.yml')}


def buoc(ten):
    i = Y.index(ten); j = Y.find('\n      - ', i + 10); return Y[i:j if j > 0 else len(Y)]


class TestDungYml(unittest.TestCase):
    def test_a2_khong_con_cache_giong(self):  # #2
        self.assertNotIn('giong-kho', Y.replace('/giong-kho', '').replace('runner.temp', ''))   # chi con GIONG_KHO tro runner.temp
        self.assertNotIn('actions/cache/restore', Y); self.assertNotIn('actions/cache/save', Y)
        self.assertEqual(Y.count('GIONG_KHO: ${{ runner.temp }}/giong-kho'), 2)
        for ten, n in TATCA.items():
            for m in re.finditer(r'actions/cache[^\n]*\n(?:[^\n]*\n){0,6}', n):
                self.assertIn('whisper', m.group(0), f'{ten}: cache la gi?')

    def test_a3_chon_ra_ma_hoa(self):  # #3
        self.assertNotIn('chon-ra.tar\n          retention', Y); self.assertIn('path: chon-ra.enc', Y)
        for b in (buoc('- name: Dong goi + MA HOA'), buoc('- name: Giai ma + giai nen')):
            self.assertIn('-iter 200000', b); self.assertIn('GOI_KHOA', b); self.assertIn('[ -n "${GOI_KHOA:-}" ]', b)
        self.assertIn('-pass env:GOI_KHOA', buoc('- name: Dong goi + MA HOA'))
        self.assertIn('-iter 200000', buoc('- name: Go loi'))

    def test_a4_cam_fixture_that(self):  # #1
        v = buoc('- name: Kiem dau vao'); self.assertRegex(v, r'\[ -n "\$FIXTURE" \] && \[ "\$CHE_DO" = "that" \].*exit 1')
        ph = Y[Y.index('  phat-hanh:'):Y.index('  bao-loi:')]
        self.assertIn("needs.kiem-moi.outputs.live == '1'", ph.split('runs-on')[0]); self.assertIn("LIVE: ${{ needs.kiem-moi.outputs.live }}", ph)
        self.assertIn("m['che_do']==os.environ['CHE_DO']", ph); self.assertIn("os.environ['LIVE']=='1'", ph)

    def test_a5_release_target_va_xac_nhan_tag(self):  # #21
        ph = Y[Y.index('  phat-hanh:'):Y.index('  bao-loi:')]
        self.assertIn('--target "$GITHUB_SHA"', ph); self.assertIn('git/ref/tags/$TAG', ph); self.assertIn('gh release delete', ph)
        self.assertRegex(ph, r'"\$THAT" != "\$GITHUB_SHA"\ \]; then(?s:.*)exit 1')

    def test_a6_ntfy_khong_nuot_loi(self):  # #23
        for dong in Y.splitlines():
            if 'ntfy' in dong: self.assertNotIn('|| true', dong)
        self.assertEqual(Y.count('ntfy.loi('), 3); self.assertEqual(Y.count('sys.exit(0 if ntfy.loi('), 3)
        self.assertIn('|| { echo "gui ntfy bo khung THAT BAI"; exit 1; }', Y)

    def test_a7_ngay_du_lieu_tin_nhanh_tu_ngay_da_chon(self):  # #24
        self.assertIn('NGAY_DL="$(date -d "$NGAY -1 day" +%F)"', Y); self.assertNotIn('NGAY_DL="$(TZ=Asia/Ho_Chi_Minh date +%F)"', Y)

    def test_a8_truyen_lan_cuoi(self):
        self.assertIn('--lan-cuoi', Y); self.assertNotIn('--lan "$LAN"', Y)


if __name__ == '__main__': unittest.main()
