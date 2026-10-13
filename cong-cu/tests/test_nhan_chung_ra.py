"""cong-cu/nhan-chung-ra.sh: kiem sha256 tep chung-ra.enc lay tu cache; moi ca thoat 0, ok=1 chi khi sha khop."""
import hashlib, pathlib, subprocess, tempfile, unittest

SH = pathlib.Path(__file__).resolve().parents[1] / 'nhan-chung-ra.sh'
NOI_DUNG = b'noi dung gia lap chung-ra'
SHA = hashlib.sha256(NOI_DUNG).hexdigest()


class TestNhanChungRa(unittest.TestCase):
    def chay(self, d, sha, tao_tep=True, noi_dung=NOI_DUNG):
        tep = pathlib.Path(d) / 'chung-ra.enc'
        if tao_tep: tep.write_bytes(noi_dung)
        r = subprocess.run(['bash', str(SH), str(tep), sha, str(pathlib.Path(d) / 'chung-ra')], capture_output=True, text=True)
        return r, tep, pathlib.Path(d) / 'chung-ra' / 'chung-ra.enc'

    def test_khop_sha(self):
        with tempfile.TemporaryDirectory() as d:
            r, tep, dich = self.chay(d, SHA)
            self.assertEqual(r.returncode, 0, r.stderr); self.assertIn('ok=1', r.stdout.splitlines()); self.assertIn('nguon=cache', r.stdout)
            self.assertTrue(dich.is_file()); self.assertEqual(dich.read_bytes(), NOI_DUNG); self.assertFalse(tep.exists())

    def test_thieu_tep(self):
        with tempfile.TemporaryDirectory() as d:
            r, tep, dich = self.chay(d, SHA, tao_tep=False)
            self.assertEqual(r.returncode, 0, r.stderr); self.assertEqual(r.stdout.strip(), 'ok=0'); self.assertFalse(dich.exists())

    def test_sha_sai_xoa_tep(self):
        with tempfile.TemporaryDirectory() as d:
            r, tep, dich = self.chay(d, hashlib.sha256(b'khac').hexdigest())
            self.assertEqual(r.returncode, 0, r.stderr); self.assertEqual(r.stdout.strip(), 'ok=0'); self.assertFalse(tep.exists()); self.assertFalse(dich.exists())

    def test_sha_rong_hoac_sai_dinh_dang(self):
        for sha in ('', 'abc', SHA.upper(), SHA + '0'):
            with tempfile.TemporaryDirectory() as d:
                r, tep, dich = self.chay(d, sha)
                self.assertEqual(r.returncode, 0, r.stderr); self.assertEqual(r.stdout.strip(), 'ok=0', sha); self.assertFalse(tep.exists()); self.assertFalse(dich.exists())

    def test_thieu_tep_va_sha_rong(self):
        with tempfile.TemporaryDirectory() as d:
            r, tep, dich = self.chay(d, '', tao_tep=False)
            self.assertEqual(r.returncode, 0); self.assertEqual(r.stdout.strip(), 'ok=0')


if __name__ == '__main__': unittest.main()
