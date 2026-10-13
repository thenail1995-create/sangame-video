"""Gói A2-A7 (Sol #1 #2 #3 #21 #23 #24): kiem tinh dung.yml (khong chay duoc CI that o day)."""
import pathlib, re, unittest

Y = (pathlib.Path(__file__).resolve().parents[2] / '.github/workflows/dung.yml').read_text(encoding='utf-8')
TATCA = {p.name: p.read_text(encoding='utf-8') for p in (pathlib.Path(__file__).resolve().parents[2] / '.github/workflows').glob('*.yml')}


def buoc(ten):
    i = Y.index(ten); j = Y.find('\n      - ', i + 10); return Y[i:j if j > 0 else len(Y)]


class TestDungYml(unittest.TestCase):
    def test_a2_khong_con_cache_giong(self):  # #2
        self.assertNotIn('giong-kho', Y.replace('/giong-kho', '').replace('runner.temp', ''))   # chi con GIONG_KHO tro runner.temp
        # 13/10: cache /save va /restore CHI cho chung-ra.enc (da ma hoa GOI_KHOA, sha chot tu output job chung); moi cache khac van bi cam o duoi
        for ten, n in TATCA.items():
            self.assertEqual(len(re.findall(r'actions/cache/(?:save|restore)@', n)), len(re.findall(r'actions/cache/(?:save|restore)@[^\n]*\n(?:        [^\n]*\n)*?        with:\n          path: chung-ra\.enc\n          key: chung-ra-\$\{\{ github\.run_id \}\}-', n)), f'{ten}: cache save/restore ngoai chung-ra.enc')
        self.assertEqual(len(re.findall(r'actions/cache/(?:save|restore)@', Y)), 2)
        self.assertEqual(Y.count('GIONG_KHO: ${{ runner.temp }}/giong-kho'), 2)   # chi job chung (thu giong + chay chung); job ban/gom KHONG thay giong tho qua cache
        # dung nhanh 11/10: duoc cache MO HINH, trinh duyet, goi Python, .deb - KHONG BAO GIO giong / khoa / du lieu rieng tu / khuon
        CHO_PHEP = ('whisper', 'apt-deb', 'playwright', 'uv-')
        dem = 0
        for ten, n in TATCA.items():
            for m in re.finditer(r'actions/cache@[^\n]*\n        with:\n          path:([^\n]*(?:\n            [^\n]*)*)\n          key: ([^\n]*)', n):
                path, key = m.group(1), m.group(2); dem += 1
                self.assertTrue(any(key.startswith(k) for k in CHO_PHEP), f'{ten}: cache la gi? {key}')
                for cam in ('giong', 'khuon', 'du-lieu', 'dau-vao', 'tai-san', 'am-thanh', 'GOI_KHOA', 'secrets'):
                    self.assertNotIn(cam, path + key, f'{ten}: cache {key} chua {cam}')
            self.assertEqual(n.count('actions/cache@'), len(re.findall(r'actions/cache@[^\n]*\n        with:\n          path:', n)), f'{ten}: co cache khong khop mau kiem tra')
        self.assertGreaterEqual(dem, 10)

    def test_a3_chon_ra_ma_hoa(self):  # #3
        self.assertNotIn('chon-ra.tar\n          retention', Y); self.assertIn('path: chon-ra.enc', Y)
        for ten in ('- name: Dong goi + MA HOA ket qua chon', '- name: Giai ma + giai nen ket qua chon', '- name: Dong goi + MA HOA ket qua chung',
                    '- name: Giai ma + giai nen ket qua chung', '- name: Dong goi + MA HOA ket qua ban', '- name: Giai ma vao khuon'):
            b = buoc(ten)
            self.assertIn('-iter 200000', b, ten); self.assertIn('GOI_KHOA', b, ten); self.assertIn('[ -n "${GOI_KHOA:-}" ]', b, ten)
            if 'Dong goi' in ten: self.assertIn('-pass env:GOI_KHOA', b, ten)
        self.assertIn('-iter 200000', buoc('- name: Go loi'))

    def test_moi_artifact_trung_gian_ma_hoa(self):   # repo CONG KHAI: artifact tai duoc -> giong tho / loi / anh Sony chi qua tep .enc (GOI_KHOA); chi `ban-dung` (7 tai san cong khai) va go-loi (ARTIFACT_KEY) khac
        thay = []
        for m in re.finditer(r'uses: actions/upload-artifact@[^\n]*\n        with:\n          name: ([^\n]+)\n          path: ([^\n]+)\n', Y):
            ten, duong = m.group(1), m.group(2); thay.append(ten)
            if ten == 'ban-dung': self.assertEqual(duong, 'out/')
            else: self.assertTrue(duong.endswith('.enc'), f'artifact {ten} khong ma hoa: {duong}')
        for ten in ('chon-ra', 'chung-ra', 'chung-meta', 'kq-ban-${{ matrix.ban }}', 'ban-dung', 'go-loi-${{ matrix.ban }}'): self.assertIn(ten, thay)
        self.assertEqual(Y.count('uses: actions/upload-artifact@'), len(thay))   # khong co upload nao thoat khoi mau kiem tra
        goi = buoc('- name: Dong goi + MA HOA ket qua chung')   # bo loc tep chung: khong keo am-thanh (nang) / lop alpha / soi; co danh sach tep ro rang
        for loai in ('am-thanh', 'lop-', 'soi'): self.assertIn(loai, goi)
        self.assertIn('git ls-files --others', goi)

    def test_go_loi_khoa_rong_thoat_1_truoc_khi_dong_goi(self):   # Sol soi cuoi: ARTIFACT_KEY rong van ma hoa duoc bang mat khau rong roi upload
        import subprocess, tempfile, os
        b = buoc('- name: Go loi - dong goi'); run = b[b.index('run: |') + len('run: |'):]
        run = '\n'.join(l[10:] if l.startswith(' ' * 10) else l for l in run.split('\n'))
        self.assertLess(run.index('ARTIFACT_KEY:-'), run.index('mkdir -p go-loi')); self.assertLess(run.index('ARTIFACT_KEY:-'), run.index('openssl enc'))
        with tempfile.TemporaryDirectory() as d:
            for k in ('', None):
                env = {kk: vv for kk, vv in os.environ.items() if kk != 'ARTIFACT_KEY'}
                if k is not None: env['ARTIFACT_KEY'] = k
                r = subprocess.run(['bash', '-c', run], cwd=d, env=env, capture_output=True, text=True)
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr); self.assertIn('ARTIFACT_KEY', r.stdout)
                self.assertFalse(os.path.exists(os.path.join(d, 'go-loi.enc'))); self.assertFalse(os.path.exists(os.path.join(d, 'go-loi')))

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

    def test_hoi_quy_chi_khi_co_fixture(self):  # dot 2 / 5
        for ten in ('- name: Dung chung + KIEM SOM', '- name: "Dung + kiem DAY DU'):
            self.assertIn("HOI_QUY: ${{ env.FIXTURE != '' && '1' || '' }}", buoc(ten))
        self.assertEqual(Y.count('HOI_QUY'), 2)   # chi o 2 buoc chay.sh (chung + ban), khong dat o cho nao khac (vd job-level)

    def test_pytest_ghim_trong_moi_truong_khoa(self):  # dot 2 / 6
        root = pathlib.Path(__file__).resolve().parents[2]
        self.assertRegex((root / 'pyproject.toml').read_text(), r'pytest==\d')
        self.assertRegex((root / 'uv.lock').read_text(), r'name = "pytest"')


if __name__ == '__main__': unittest.main()


class PhatHanhKhiChonBiBoQua(unittest.TestCase):
    """CI that 11/10 (38113783849): Tin nhanh 1 pha bo qua job chon -> phat-hanh khong co ham trang thai nen bi GitHub bo qua theo chuoi needs."""
    def test_phat_hanh_co_ham_trang_thai(self):
        import pathlib, re
        y = (pathlib.Path(__file__).resolve().parents[2] / '.github' / 'workflows' / 'dung.yml').read_text(encoding='utf-8')
        khoi = y.split('\n  phat-hanh:\n', 1)[1].split('\n  bao-loi:', 1)[0]
        dong_if = next(l for l in khoi.splitlines() if l.strip().startswith('if:'))
        self.assertRegex(dong_if, r"!cancelled\(\)|always\(\)")
        self.assertIn("needs.gom.result == 'success'", dong_if)   # dung nhanh 11/10: job dung tach thanh chung + ban x3 + gom; phat-hanh cho gom


def khoi_job(ten):
    """Noi dung job `ten` trong dung.yml (tu '  ten:' toi job ke tiep)."""
    i = Y.index(f'\n  {ten}:\n') + 1; j = re.search(r'\n  [a-z-]+:\n', Y[i + 5:]); return Y[i:i + 5 + j.start() if j else len(Y)]


def buoc_trong(khoi, ten):
    i = khoi.index(ten); j = khoi.find('\n      - ', i + 10); return khoi[i:j if j > 0 else len(khoi)]


class DungNhanhMatrix(unittest.TestCase):
    """11/10 dung nhanh: job dung -> chung + matrix ban x3 song song + gom. Co/khong 'chon' (Tin nhanh 1 pha bo qua chon) deu phai chay dung."""
    def test_so_do_job(self):
        self.assertNotIn('\n  dung:\n', Y); self.assertNotIn('needs.dung', Y)
        self.assertRegex(khoi_job('chung'), r"needs: \[kiem-moi, chon\]")
        self.assertRegex(khoi_job('ban'), r"needs: \[kiem-moi, chung\]")
        self.assertRegex(khoi_job('gom'), r"needs: \[kiem-moi, chung, ban\]")
        self.assertRegex(khoi_job('phat-hanh'), r"needs: \[kiem-moi, gom\]")
        self.assertRegex(khoi_job('bao-loi'), r"needs: \[kiem-moi, chon, chung, ban, gom, phat-hanh\]")
        for j in ('chung', 'ban', 'gom'): self.assertIn("github.ref == 'refs/heads/main'", khoi_job(j).split('runs-on')[0], j)

    def test_matrix_ba_ban_song_song(self):
        b = khoi_job('ban')
        self.assertRegex(b, r"strategy:\s+fail-fast: true\s+matrix:\s+ban: \[tiktok, reels, shorts\]")
        self.assertIn('BAN: ${{ matrix.ban }}', b); self.assertIn('GD: ban', b); self.assertIn("NEN_DUNG_LAI: '1'", b)
        self.assertIn('GD: chung', khoi_job('chung')); self.assertNotIn('matrix', khoi_job('chung')); self.assertNotIn('matrix.ban', khoi_job('gom'))
        for nt in ('tiktok', 'reels', 'shorts'): self.assertIn(nt, buoc_trong(khoi_job('gom'), '- name: Giai ma vao khuon'))

    def test_if_dung_cho_3_dang_ban_va_gom_co_ham_trang_thai(self):   # bai hoc #35: chon bi bo qua (Tin nhanh) -> thieu !cancelled()/always() GitHub bo qua luon job sau
        self.assertRegex(khoi_job('chung').split('runs-on')[0], r"if: always\(\) &&")
        for j in ('ban', 'gom', 'phat-hanh'):
            dong = next(l for l in khoi_job(j).splitlines() if l.strip().startswith('if:'))
            self.assertRegex(dong, r"!cancelled\(\)", j)
        ban_if = next(l for l in khoi_job('ban').splitlines() if l.strip().startswith('if:'))
        self.assertIn("needs.chung.result == 'success'", ban_if); self.assertIn("needs.chung.outputs.bo_khung != '1'", ban_if)   # Tin nhanh bo khung = chung xanh nhung KHONG co artifact -> ban bo qua
        gom_if = next(l for l in khoi_job('gom').splitlines() if l.strip().startswith('if:'))
        self.assertIn("needs.ban.result == 'success'", gom_if); self.assertIn("needs.chung.outputs.bo_khung != '1'", gom_if)
        ph_if = next(l for l in khoi_job('phat-hanh').splitlines() if l.strip().startswith('if:'))
        self.assertIn("needs.gom.result == 'success' && needs.gom.outputs.xong == '1'", ph_if)
        self.assertNotIn('needs.chon', khoi_job('ban')); self.assertNotIn('needs.chon', khoi_job('gom'))   # khong phu thuoc truc tiep job chon (co the bi bo qua)

    def test_concurrency_van_theo_dang(self):
        # 12/10: 3 khung Keo (keo-thom-2 / keo-thom / keo-thom-3) CUNG nhom `dung-keo-thom` de chay tuan tu (chong chon trung game); tin-nhanh / top5 van nhom rieng
        self.assertIn("group: dung-${{ startsWith(github.event.inputs.dang || github.event.client_payload.dang, 'keo-thom') && 'keo-thom' || (github.event.inputs.dang || github.event.client_payload.dang) }}", Y)
        self.assertIn('cancel-in-progress: false', Y)

    def test_khuon_tach_khoi_dang(self):    # DANG = khoa rieng (tag Release, sg_dang, URL, manifest); KHUON = thu muc khuon (bo hau to -<so>)
        self.assertNotRegex(Y, r'khuon/\$DANG|khuon/"\$DANG"|khuon/\'\+d\+\'')
        for j in ('kiem-moi', 'chon', 'chung', 'ban', 'gom'):
            self.assertIn("KHUON: ${{ startsWith(github.event.inputs.dang || github.event.client_payload.dang, 'keo-thom') && 'keo-thom' ||", khoi_job(j), j)
        self.assertIn('lay-tai-san.sh "$KHUON"', Y); self.assertIn('--dang "$DANG"', khoi_job('chung')); self.assertIn('--dang "$DANG"', khoi_job('gom'))
        self.assertIn('v-${NGAY}-${DANG}', Y); self.assertIn('thu-${NGAY}-${DANG}', Y)
        self.assertIn("os.environ['KHUON']+'/ket-qua-chon.json'", khoi_job('chon'))
        self.assertIn('keo-thom|keo-thom-2|keo-thom-3', khoi_job('kiem-moi'))
        for d in ('keo-thom-2', 'keo-thom', 'keo-thom-3'): self.assertIn(d, Y.split('jobs:')[0])   # options cua workflow_dispatch

    def test_gio_dang_nam_khung(self):    # bieu thuc GIO_DANG o 3 job = bang 5 gia tri
        bt = re.findall(r"GIO_DANG: \$\{\{ (.+?) \}\}\n", Y); self.assertEqual(len(bt), 3)
        def tinh(dang):    # 'X == a && V1 || X == b && V2 || ... || MAC_DINH'
            bang = dict(re.findall(r"== '([a-z0-9-]+)' && '(\d\d:\d\d)'", bt[0]))
            return bang.get(dang) or re.search(r"\|\| '(\d\d:\d\d)'$", bt[0]).group(1)
        self.assertEqual([tinh(d) for d in ('tin-nhanh', 'top5', 'keo-thom-2', 'keo-thom', 'keo-thom-3')], ['07:30', '12:00', '15:00', '20:00', '22:00'])
        self.assertEqual(bt[0], bt[1]); self.assertEqual(bt[1], bt[2])

    def test_bo_khung_khong_vao_ban(self):    # chung xuat bo_khung; chi buoc dong goi/upload chay khi bo_khung != 1
        c = khoi_job('chung'); self.assertIn('bo_khung: ${{ steps.dung.outputs.bo_khung }}', c)
        for ten in ('- name: Dong goi + MA HOA ket qua chung', '- name: Chuyen ket qua chung', '- name: Chuyen thong tin manifest'): self.assertIn("steps.dung.outputs.bo_khung != '1'", buoc_trong(c, ten), ten)
        self.assertIn('bo_khung=1', c); self.assertIn('khuon/$KHUON/chay.sh', c)

    def test_ban_gom_it_bi_mat_nhat(self):    # job ban/gom khong cam khoa thu giong / ntfy / Supabase: chi DATA_DEPLOY_KEY + GOI_KHOA (+ ARTIFACT_KEY o buoc go-loi)
        for j in ('ban', 'gom'):
            khoi = khoi_job(j)
            for cam in ('SUPABASE', 'SG_CONG_KHOA', 'NTFY', 'ELEVEN', 'GH_TOKEN', 'contents: write'): self.assertNotIn(cam, khoi, f'{j}: {cam}')
            for m in re.finditer(r'secrets\.([A-Z_]+)', khoi): self.assertIn(m.group(1), ('DATA_DEPLOY_KEY', 'GOI_KHOA', 'ARTIFACT_KEY'), j)
        self.assertNotIn('GIONG_KHO', khoi_job('ban')); self.assertNotIn('GIONG_KHO', khoi_job('gom'))

    def test_giu_luat_an_toan(self):
        for j in ('chung', 'ban', 'gom'):
            khoi = khoi_job(j)
            # máy GitHub, hoặc (chung/ban) máy chọn qua input `may` — chỉ 2 giá trị: ubuntu-24.04 | ubicloud-standard-8 (thử đo 13/10)
            self.assertTrue('runs-on: ubuntu-24.04' in khoi or "runs-on: ${{ github.event.inputs.may || 'ubicloud-standard-8' }}" in khoi, j)
            for m in re.finditer(r'uses: ([\w./-]+)@([^\s]+)', khoi): self.assertRegex(m.group(2), r'^[0-9a-f]{40}$', f'{j}: {m.group(0)} chua ghim SHA')
        self.assertIn('options: [ubuntu-24.04, ubicloud-standard-8]', Y)
        self.assertRegex(Y, r'options: \[ubuntu-24\.04, ubicloud-standard-8\]\n        default: ubicloud-standard-8\n')
        self.assertEqual(Y.count("runs-on: ${{ github.event.inputs.may || 'ubicloud-standard-8' }}"), 3)
        for j in ('kiem-moi', 'gom', 'phat-hanh', 'bao-loi'): self.assertIn('runs-on: ubuntu-24.04', khoi_job(j), j)   # job nhe giu may GitHub
        self.assertIn('thieu secret GOI_KHOA', khoi_job('ban')); self.assertIn("os.environ['LIVE']=='1'", khoi_job('phat-hanh'))

    def test_workers_theo_may(self):
        bt = "WORKERS: ${{ (github.event.inputs.may || 'ubicloud-standard-8') == 'ubicloud-standard-8' && '8' || '4' }}"
        self.assertIn(bt, khoi_job('chung')); self.assertIn(bt, khoi_job('ban')); self.assertEqual(Y.count('WORKERS:'), 2)

    def test_chung_ra_qua_cache_artifact_du_phong(self):
        c = khoi_job('chung')
        self.assertIn('chung_sha: ${{ steps.sha_chung.outputs.sha }}', c)
        sha = buoc_trong(c, '- name: Tinh sha256 chung-ra.enc'); self.assertIn('id: sha_chung', sha); self.assertIn("steps.dung.outputs.bo_khung != '1'", sha); self.assertIn('sha256sum chung-ra.enc', sha)
        sv = buoc_trong(c, '- name: Luu chung-ra vao cache')
        self.assertIn('continue-on-error: true', sv); self.assertIn("steps.dung.outputs.bo_khung != '1'", sv)
        self.assertIn('uses: actions/cache/save@55cc8345863c7cc4c66a329aec7e433d2d1c52a9', sv)
        self.assertIn('path: chung-ra.enc', sv); self.assertIn('key: chung-ra-${{ github.run_id }}-${{ github.run_attempt }}', sv)
        self.assertLess(c.index('Dong goi + MA HOA ket qua chung'), c.index('id: sha_chung')); self.assertLess(c.index('id: sha_chung'), c.index('actions/cache/save@')); self.assertLess(c.index('actions/cache/save@'), c.index('name: chung-ra\n'))
        self.assertIn('name: chung-ra\n          path: chung-ra.enc', c)   # artifact du phong van con
        b = khoi_job('ban')
        rs = buoc_trong(b, '- name: Lay chung-ra tu cache')
        self.assertIn('id: cache_chung', rs); self.assertIn('continue-on-error: true', rs); self.assertIn('uses: actions/cache/restore@55cc8345863c7cc4c66a329aec7e433d2d1c52a9', rs)
        self.assertIn('restore-keys: chung-ra-${{ github.run_id }}-', rs)
        kt = buoc_trong(b, '- name: Kiem sha chung-ra tu cache')
        self.assertIn('id: kiem_chung', kt); self.assertIn('CHUNG_SHA: ${{ needs.chung.outputs.chung_sha }}', kt)
        self.assertIn('bash cong-cu/nhan-chung-ra.sh chung-ra.enc "$CHUNG_SHA" chung-ra >> "$GITHUB_OUTPUT"', kt); self.assertNotIn('${{', kt.split('run:')[1])
        dl = buoc_trong(b, '- name: Ket qua chung (tu job chung)')
        self.assertIn("if: steps.kiem_chung.outputs.ok != '1'", dl); self.assertIn('actions/download-artifact@634f93cb2916e3fdff6788551b99b062d0335ce0', dl)
        self.assertIn('name: chung-ra\n          path: chung-ra\n', dl + '\n')   # Sol 13/10: duong du phong phai tai DUNG thu muc ma buoc giai ma doc
        # Sol 13/10: tep chung-ra.enc (cache + artifact) chi duoc tao boi openssl enc (MA HOA) - khong buoc nao khac ghi/copy tep tho vao ten nay
        ghi = [l for l in c.splitlines() if re.search(r'(-out|>|\bcp\b|\bmv\b|\btar\b|\btee\b)[^\n]*chung-ra\.enc', l)]
        self.assertEqual(ghi, ['          openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt -pass env:GOI_KHOA -in "$RUNNER_TEMP/chung-ra.tar" -out "$GITHUB_WORKSPACE/chung-ra.enc"'])
        gm = buoc_trong(b, '- name: Giai ma + giai nen ket qua chung vao khuon')
        self.assertIn('-in chung-ra/chung-ra.enc', gm); self.assertIn('nguon chung-ra:', gm)
        self.assertLess(b.index('actions/cache/restore@'), b.index('id: kiem_chung')); self.assertLess(b.index('id: kiem_chung'), b.index('actions/download-artifact')); self.assertLess(b.index('actions/download-artifact'), b.index('Giai ma + giai nen ket qua chung'))

    def test_cache_ghim(self):    # Playwright theo package-lock, uv theo uv.lock, apt .deb theo tuan; npm qua setup-node
        for j in ('chung', 'ban'):
            k = khoi_job(j)
            self.assertIn("key: playwright-${{ runner.os }}-${{ hashFiles('cong-cu/package-lock.json') }}", k)
            self.assertIn("key: uv-${{ runner.os }}-0.11.17-${{ hashFiles('uv.lock') }}", k)
            self.assertIn('cache: npm', k); self.assertIn('apt-deb-tesseract-ubuntu-24.04-', k); self.assertIn('apt-get install -y -qq "$D"/*.deb', k)
            self.assertLess(k.index('apt-deb-tesseract'), k.index('npx playwright install'))   # apt truoc Playwright --with-deps: bo .deb cache khong lan goi cua Playwright
        self.assertIn('apt-deb-tesseract-ffmpeg-ubuntu-24.04-', khoi_job('chon'))
        for ten, n in TATCA.items():
            for m in re.finditer(r'actions/cache@([^\s]+)', n): self.assertRegex(m.group(1), r'^[0-9a-f]{40}$')

    def test_gom_chay_hop_dong_7_tai_san(self):
        g = khoi_job('gom'); self.assertIn('cong-cu/manifest.py', g); self.assertIn('name: ban-dung\n          path: out/', g); self.assertIn('THIEU ket qua ban $nt', g)
        ph = khoi_job('phat-hanh'); self.assertIn('len(cho)==7', ph); self.assertIn("b['kiem']['dat'] is True", ph)   # phat-hanh van doi chieu DUNG 7 tai san + kiem.dat ca 3 ban


class KiemSomTruocKhiChup(unittest.TestCase):
    """KIEM SOM: GD=chung chay cac phep khong can hinh va DUNG NGAY (truoc khi chup lop chu / ma hoa nen); bo kiem cuoi van chay lai ca nhom do."""
    ROOT = pathlib.Path(__file__).resolve().parents[2]
    def chay_sh(self, khuon): return (self.ROOT / 'khuon' / khuon / 'chay.sh').read_text(encoding='utf-8')
    def test_chung_kiem_som_va_khong_chup(self):
        for k in ('top5', 'keo-thom', 'tin-nhanh'):
            sh = self.chay_sh(k); chung = sh[sh.index('chung)'):sh.index('\nban)')]; ban = sh[sh.index('\nban)'):sh.index('\n*)')]
            self.assertIn('chay_kiem_som', chung, k); self.assertIn('chon', chung, k)
            for cam in ('dung.py lop', 'dung.py hinh', 'dung.py bia', 'ghep08.py', 'ghep_am.py', 'chay_kiem ;;'): self.assertNotIn(cam, chung, f'{k}: job chung khong duoc {cam}')
            self.assertLess(chung.index('chon'), chung.index('chay_kiem_som'))
            for can in ('NEN_DUNG_LAI=1', 'dung.py lop "$BAN"', 'ghep_am.py', 'chay_kiem ;;'): self.assertIn(can, ban, f'{k}: {can}')
            self.assertNotIn('chay_kiem_som', ban, k)
    def test_kiem_som_chi_bo_phep_can_video(self):
        for k in ('top5', 'keo-thom', 'tin-nhanh'):
            src = (self.ROOT / 'khuon' / k / 'kiem' / 'kiem-tat-ca.py').read_text(encoding='utf-8')
            self.assertIn("SOM=os.environ.get('KIEM_SOM')=='1'", src); self.assertIn("X16=None if SOM else doc(VID,16000)", src)
            dong = src.split('\n')
            for i, l in enumerate(dong):   # moi phep dung VIDEO nam sau `if not SOM:` (dong thut le)
                if "str(SK/'kiem-video.py')" in l or 'LK.lien_ket(' in l or 'tv=nghe(X16' in l or 'ly_do_video(VID' in l: self.assertTrue(l.startswith('    '), f'{k}: dong {i + 1} dung video ngoai `if not SOM:`')
            for phai_chay_som in ('NS.kiem_ngay', 'NS.nghe_doan', 'kiem-dom.cjs', "np.load(B/'sfx-bus.npy')"):   # D3 noi dung / ngay / DOM / giong-tieng dong: khong bi bo o kiem som
                self.assertTrue(any(phai_chay_som in l and not l.startswith('    ') for l in dong), f'{k}: {phai_chay_som} phai chay o kiem som')
            self.assertIn("kiem/kiem-{TT}.json", src)   # SOM ghi kiem-som-<nt>.json, KHONG ghi de kiem-<nt>.json (manifest chi tin bao cao cuoi)
    def test_chay_chung_giai_doan_va_ban(self):
        s = (self.ROOT / 'cong-cu' / 'chay-chung.sh').read_text(encoding='utf-8')
        self.assertIn('case "$GD" in chung|ban|tat-ca)', s); self.assertIn('case "$BAN" in tiktok|reels|shorts)', s); self.assertIn('GD=ban can BAN', s)
        self.assertIn('chay_kiem_som()', s); self.assertIn('KIEM_SOM=1', s)
