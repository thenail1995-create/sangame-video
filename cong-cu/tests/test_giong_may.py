"""SG-GIONG-may: giong_may.py (VieNeu du phong) - `chay` gia, khong chay VieNeu that. Test that (cong vuot_tran -> VieNeu that) chi khi SG_THU_VIENEU=1."""
import contextlib, io, json, os, pathlib, sys, tempfile, types, unittest
from unittest import mock

CC = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CC)); sys.path.insert(0, str(CC.parent))
import giong, giong_may  # noqa: E402

LOI = 'Xin chao cac ban, day la ban tin game hom nay. ' * 4     # 192 ky tu


class ChayGia:
    """Gia subprocess.run: uv (ghi wav), ffmpeg (ghi mp3), ffprobe (tra thoi luong)."""
    def __init__(self, giay=10.0, ma_uv=0, byte=9000, ma_ff=0):
        self.giay = giay; self.ma_uv = ma_uv; self.byte = byte; self.ma_ff = ma_ff; self.goi = []; self.env_uv = None
    def __call__(self, cmd, **kw):
        self.goi.append(cmd); ten = cmd[0]
        if ten == 'uv':
            self.env_uv = kw.get('env'); self.kw_uv = kw
            if self.ma_uv == 0: pathlib.Path(cmd[cmd.index('--ra') + 1]).write_bytes(b'RIFF')
            return types.SimpleNamespace(returncode=self.ma_uv, stdout='', stderr='boom SG_CONG_KHOA=KHOABIMAT123456' if self.ma_uv else '')
        if ten == 'ffmpeg':
            if self.ma_ff == 0: pathlib.Path(cmd[-1]).write_bytes(b'x' * self.byte)
            return types.SimpleNamespace(returncode=self.ma_ff, stdout='', stderr='ff loi' if self.ma_ff else '')
        if ten == 'ffprobe': return types.SimpleNamespace(returncode=0, stdout=f'{self.giay}\n', stderr='')
        raise AssertionError(cmd)
    def so(self, ten): return [c for c in self.goi if c[0] == ten]


class Khung(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory(); self.addCleanup(self.td.cleanup); self.t = pathlib.Path(self.td.name)
        p = mock.patch.dict(os.environ, {'GIONG_KHO': str(self.t / 'kho'), 'SG_CONG_KHOA': 'KHOABIMAT123456', 'SUPABASE_ANON_THENAIL': 'ANONBIMAT123456', 'HF_HOME': '/x/hf', 'UV_CACHE_DIR': '/x/uv'})
        p.start(); self.addCleanup(p.stop); self.ra = self.t / 'ra' / 'giong.mp3'
    def doc(self, chay, loi=LOI, **kw):
        o = io.StringIO()
        with contextlib.redirect_stdout(o): r = giong_may.doc_may(loi, self.ra, ly_do=kw.pop('ly_do', 'vuot_tran'), chay=chay, **kw)
        return r, o.getvalue()


class TestBoThe(unittest.TestCase):
    def test_bo_the_cam_xuc(self):
        self.assertEqual(giong_may.bo_the('[excited] Xin chao [whispers]  cac   ban [dry-tone] nhe'), 'Xin chao cac ban nhe')
        self.assertEqual(giong_may.bo_the('Gia [PS5] 100 [ok] nua'), 'Gia [PS5] 100 nua')   # [PS5] co chu so => giu nguyen (khong phai the)

    def test_chi_co_the_thi_raise(self):
        for x in ('[excited]', ' [excited] [whispers] ', ''):
            with self.assertRaises(giong.Loi): giong_may.bo_the(x)


class TestDocMay(Khung):
    def test_doc_may_ra_mp3_va_giong_nguon(self):
        c = ChayGia(giay=10.0); r, out = self.doc(c)
        self.assertEqual(r, ('may', 0)); self.assertTrue(self.ra.exists())
        d = json.loads((self.ra.parent / 'giong-nguon.json').read_text(encoding='utf-8'))
        self.assertEqual((d['nguon'], d['dong_co'], d['phien_ban'], d['giong'], d['ly_do']), ('may', 'vieneu', '3.8.3', 'Adam bựa', 'vuot_tran'))
        self.assertEqual(d['mo_hinh'][giong_may.REV_BACKBONE[0]], giong_may.REV_BACKBONE[1]); self.assertIn('GIONG MAY', out)
        uv = c.so('uv')[0]; self.assertIn('vieneu==3.8.3', uv); self.assertTrue(pathlib.Path(uv[uv.index('-I') + 1]).is_absolute())   # duong dan vieneu_doc.py tuyet doi
        self.assertEqual(pathlib.Path(uv[uv.index('-I') + 1]).name, 'vieneu_doc.py'); self.assertEqual(uv[uv.index('--giong') + 1], 'Adam bựa')
        self.assertEqual(list(giong.kho_dir().glob('*.tmp')), [])

    def test_kho_may_co_san_khong_goi_uv(self):
        c = ChayGia(); self.doc(c); c2 = ChayGia(); r, out = self.doc(c2)
        self.assertEqual(r, ('may-kho', 0)); self.assertEqual(c2.so('uv'), []); self.assertEqual(c2.so('ffmpeg'), []); self.assertEqual(json.loads((self.ra.parent / 'giong-nguon.json').read_text(encoding='utf-8'))['cach'], 'may-kho')

    def test_kho_may_khac_khoa_elevenlabs(self):
        sach = giong_may.bo_the(LOI); k_el = giong.khoa_kho(sach, giong.VOICE_MAC_DINH, 'eleven_v3', 0.0, 1.0)
        c = ChayGia(); self.doc(c); self.assertFalse((giong.kho_dir() / f'{k_el}.mp3').exists())
        (giong.kho_dir() / f'{k_el}.mp3').write_bytes(b'x' * 6000)   # kho ElevenLabs cung loi KHONG duoc dung cho may
        c2 = ChayGia(); r, _ = self.doc(c2, muoi='lan2'); self.assertEqual(r, ('may', 0)); self.assertEqual(len(c2.so('uv')), 1)   # muoi doi khoa => doc lai

    def test_khoa_gom_giong_va_muoi(self):
        c = ChayGia(); self.doc(c); n1 = len(list(giong.kho_dir().glob('*.mp3')))
        self.doc(ChayGia(), giong='Trúc Ly'); self.doc(ChayGia(), muoi='x'); self.assertEqual(len(list(giong.kho_dir().glob('*.mp3'))), n1 + 2)

    def test_loi_tieu_thoi_luong_ngoai_khoang_raise_khong_vao_kho(self):
        n = len(giong_may.bo_the(LOI))
        for giay in (0.04 * n - 1, 0.12 * n + 1):
            with self.assertRaises(giong.Loi) as e: self.doc(ChayGia(giay=giay))
            self.assertIn('ngoai khoang', str(e.exception.code)); self.assertEqual(list(giong.kho_dir().glob('*')), []); self.assertFalse(self.ra.exists())

    def test_cache_hong_thi_xoa_va_doc_lai(self):
        c = ChayGia(); self.doc(c); f = next(giong.kho_dir().glob('*.mp3'))
        c2 = ChayGia(giay=1.0)   # ffprobe bao 1 s => cache hong
        with self.assertRaises(giong.Loi): self.doc(c2)   # doc lai cung ra 1 s => cung bi chan; cache hong da bi xoa
        self.assertFalse(f.exists()); self.assertEqual(len(c2.so('uv')), 1)
        c3 = ChayGia(giay=10.0); r, _ = self.doc(c3); self.assertEqual(r, ('may', 0))

    def test_tep_nho_qua_va_loi_con(self):
        with self.assertRaises(giong.Loi): self.doc(ChayGia(byte=100))
        with self.assertRaises(giong.Loi) as e: self.doc(ChayGia(ma_uv=1), bi_mat=['KHOABIMAT123456'])
        self.assertIn('VieNeu thoat 1', str(e.exception.code)); self.assertNotIn('KHOABIMAT123456', str(e.exception.code))
        with self.assertRaises(giong.Loi): self.doc(ChayGia(ma_ff=1))
        self.assertEqual(list(giong.kho_dir().glob('*')), [])

    def test_env_con_toi_thieu(self):
        with mock.patch.dict(os.environ, {'SUPABASE_ANON_THENAIL': 'a', 'THENAIL_KHOA_GIONG': 'b', 'SG_GIONG_MAY': '1', 'HF_TOKEN_X': 'c', 'PATH': '/usr/bin'}):
            c = ChayGia(); self.doc(c)
        e = c.env_uv
        for k in e: self.assertFalse(k.startswith(('SUPABASE_', 'SG_', 'THENAIL_', 'GIONG_')), k)
        self.assertEqual(e['HF_HUB_DISABLE_TELEMETRY'], '1'); self.assertEqual(e['HF_HOME'], '/x/hf'); self.assertEqual(e['UV_CACHE_DIR'], '/x/uv'); self.assertEqual(c.kw_uv['timeout'], 900)

    def test_loi_chi_co_the_raise(self):
        with self.assertRaises(giong.Loi): self.doc(ChayGia(), loi='[excited] [whispers]')


@unittest.skipUnless(os.environ.get('SG_THU_VIENEU') == '1', 'SG_THU_VIENEU=1 de chay VieNeu that (tai ~765 MB, ~10-20 s)')
class TestVieneuThat(Khung):
    def setUp(self):
        super().setUp(); p = mock.patch.dict(os.environ); p.start(); self.addCleanup(p.stop)
        for k in ('HF_HOME', 'UV_CACHE_DIR'): os.environ.pop(k, None)   # gia tri gia cua Khung chi de kiem env con; that thi dung cache that
    def test_cong_vuot_tran_di_toi_doc_may_that(self):
        class Cong:   # cong gia: giu_credit tra vuot_tran
            def goi(self, viec, **kw): return {'ok': True, 'id': None, 'vuot_tran': True, 'chua_ro': [], 'dong': None}
        loi = 'Chào các bạn, đây là bản tin game hôm nay. Có ba tin nóng cần nghe ngay.'
        a = types.SimpleNamespace(loi=loi, loi_file=None, voice=giong.VOICE_MAC_DINH, model='eleven_v3', on_dinh=0.0, toc_do=1.0, muoi='', ra=str(self.ra), du_an='san-game', dang='top5',
                                  tran=None, du_phong=10000, cho_vuot=False, khong_may=False)
        o = io.StringIO()
        with contextlib.redirect_stdout(o): r = giong.cmd_giong(a, cong=Cong(), el=object(), ngu=lambda s: None)
        self.assertEqual(r, ('may', 0)); self.assertGreater(self.ra.stat().st_size, 5000)
        d = json.loads((self.ra.parent / 'giong-nguon.json').read_text(encoding='utf-8')); self.assertEqual((d['nguon'], d['ly_do']), ('may', 'vuot_tran'))


if __name__ == '__main__': unittest.main()
