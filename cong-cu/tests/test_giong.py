"""Gói A (Sol #2 #4 #5 #6): giong.py - cong/el/tai gia lap, khong mang."""
import argparse, contextlib, io, os, pathlib, sys, tempfile, unittest, urllib.error
from unittest import mock

CC = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CC)); sys.path.insert(0, str(CC.parent))
import giong  # noqa: E402

KHOA_GIA = 'KHOA-CONG-BI-MAT-123456'; ANON_GIA = 'ANON-BI-MAT-ABCDEF'; LINK_GIA = 'https://signed.example/mp3?token=LINKBIMAT999999'
PATH = 'giong/1760000000000-12345.mp3'


class Cong:
    def __init__(self, kho=None, hong=(), theo=None):
        self.so_dong_ghi = 1; self.goi_ds = []; self.kho = kho or {}; self.hong = set(hong); self.theo = theo or {}
    def goi(self, viec, lap_lai=True, **kw):
        self.goi_ds.append((viec, kw))
        if viec in self.hong: raise RuntimeError(f'cong hong {viec} {KHOA_GIA}')
        if viec == 'tim_credit_khoa':
            if kw['khoa_kho'] in self.theo: return {'ok': True, 'chua_ro': [], **self.theo[kw['khoa_kho']]}
            return {'ok': True, 'chua_ro': [], **self.kho} if self.kho else {'ok': True, 'dong': None, 'chua_ro': []}
        if viec == 'giu_credit': return {'ok': True, 'id': 7} if not self.kho.get('vuot') else {'ok': True, 'vuot_tran': True, 'id': None}
        if viec == 'ghi_tep_credit': return {'ok': True, 'so_dong': self.so_dong_ghi}
        return {'ok': True}
    def ten(self): return [v for v, _ in self.goi_ds]
    def kw(self, viec): return [k for v, k in self.goi_ds if v == viec]


class El:
    def __init__(self, tts=None, da_dung=(100.0, 100.0), exc=None, doc_loi=False):
        self.tts_n = 0; self.tts = tts if tts is not None else {'ok': True, 'bytes': 9000, 'path': PATH, 'nghe_thu': LINK_GIA}
        self.dd = list(da_dung); self.exc = exc; self.doc_loi = doc_loi; self.goi_n = 0
    def goi(self, body, timeout=180):
        if body['action'] == 'goi':
            self.goi_n += 1
            if self.doc_loi and self.goi_n > 1: raise RuntimeError('doc loi')
            return {'gioi_han': 100000, 'da_dung': self.dd.pop(0) if self.dd else 0}
        self.tts_n += 1
        if self.exc: raise self.exc
        return self.tts


def tai_ok(u, d): pathlib.Path(d).write_bytes(b'x' * 6000)
def tai_hong(u, d): raise ValueError('tai hong ' + u)


class Khung(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory(); self.addCleanup(self.td.cleanup)
        self.t = pathlib.Path(self.td.name)
        p = mock.patch.dict(os.environ, {'GIONG_KHO': str(self.t / 'kho'), 'SUPABASE_ANON_THENAIL': ANON_GIA, 'SG_CONG_KHOA': KHOA_GIA}); p.start(); self.addCleanup(p.stop)
    def args(self, loi='xin chao ' * 10, **kw):
        d = dict(loi=loi, loi_file=None, voice=giong.VOICE_MAC_DINH, model='eleven_v3', on_dinh=0.0, toc_do=1.0, muoi='', ra=str(self.t / 'ra' / 'g.mp3'),
                 du_an='san-game', dang='top5', tran=None, du_phong=10000, cho_vuot=False, khong_may=False); d.update(kw); return argparse.Namespace(**d)
    def chay(self, cong, el, tai=tai_ok, **kw):
        o = io.StringIO(); e = io.StringIO()
        with contextlib.redirect_stdout(o), contextlib.redirect_stderr(e):
            try: r = giong.cmd_giong(self.args(**kw), cong=cong, el=el, ngu=lambda s: None, tai=tai); exc = None
            except giong.Loi as x: r = None; exc = x
        return r, exc, o.getvalue() + e.getvalue()


class TestGiong(Khung):
    def test_kho_rieng_co_thi_0_tts(self):  # #2 (thay cache Actions cong khai)
        cong = Cong(kho={'dong': {'id': 5, 'trang_thai': 'giu', 'tep': PATH}, 'link': LINK_GIA}); el = El()
        r, exc, out = self.chay(cong, el)
        self.assertIsNone(exc); self.assertEqual(r, ('kho-rieng', 0)); self.assertEqual(el.tts_n, 0)
        self.assertNotIn('giu_credit', cong.ten())
        self.assertEqual(cong.kw('khong_ro_credit')[0]['id'], 5); self.assertEqual(cong.kw('khong_ro_credit')[0]['ghi_chu'], 'phuc hoi tu tep')
        self.assertTrue((self.t / 'ra' / 'g.mp3').exists()); self.assertIn('KHO RIENG', out)

    def test_kho_rieng_dong_da_xong_khong_dong_vao_so(self):
        cong = Cong(kho={'dong': {'id': 5, 'trang_thai': 'xong', 'tep': PATH}, 'link': LINK_GIA})
        r, exc, _ = self.chay(cong, El()); self.assertEqual(r[0], 'kho-rieng'); self.assertNotIn('khong_ro_credit', cong.ten())

    def test_tts_xong_tai_hong_giu_trang_thai_va_luot_sau_phuc_hoi(self):  # #5
        cong = Cong(); el = El()
        r, exc, _ = self.chay(cong, el, tai=tai_hong)
        self.assertIsNotNone(exc); self.assertIn('phuc hoi', str(exc)); self.assertEqual(el.tts_n, 1)
        self.assertEqual(cong.kw('ghi_tep_credit')[0]['tep'], PATH)
        for v in ('xong_credit', 'huy_credit', 'khong_ro_credit'): self.assertNotIn(v, cong.ten())   # GIU nguyen 'giu'
        cong2 = Cong(kho={'dong': {'id': 7, 'trang_thai': 'giu', 'tep': PATH}, 'link': LINK_GIA}); el2 = El()
        r2, exc2, _ = self.chay(cong2, el2); self.assertIsNone(exc2); self.assertEqual(el2.tts_n, 0)   # luot 2: 0 TTS

    def test_ghi_tep_ngay_sau_tts_truoc_tai_va_thu_3_lan(self):  # #5
        cong = Cong(hong={'ghi_tep_credit'}); r, exc, out = self.chay(cong, El())
        self.assertIsNone(exc); self.assertEqual(cong.ten().count('ghi_tep_credit'), 3)
        self.assertIn('CANH BAO', out)

    def test_quyet_toan_hong_khong_thu_lai_va_khong_raise(self):  # #5
        cong = Cong(hong={'xong_credit'}); el = El(da_dung=(100.0, 150.0, 150.0))
        r, exc, out = self.chay(cong, el)
        self.assertIsNone(exc); self.assertEqual(el.tts_n, 1); self.assertTrue((self.t / 'ra' / 'g.mp3').exists()); self.assertIn('CANH BAO', out)

    def test_loi_luu_la_khong_ro_khong_huy(self):  # #6
        cong = Cong(); el = El(tts={'ok': False, 'loi': 'luu: storage 500'})
        r, exc, _ = self.chay(cong, el)
        self.assertIsNotNone(exc); self.assertIn('khong_ro_credit', cong.ten()); self.assertNotIn('huy_credit', cong.ten())

    def test_tts_4xx_trong_200_thi_huy(self):  # #6
        cong = Cong(); el = El(tts={'ok': False, 'loi': 'tts 401: bad key'})
        r, exc, _ = self.chay(cong, el); self.assertIsNotNone(exc); self.assertIn('huy_credit', cong.ten()); self.assertNotIn('khong_ro_credit', cong.ten())

    def test_tts_5xx_va_mat_ket_noi_la_khong_ro(self):  # #6
        for i, exc_ in enumerate((urllib.error.HTTPError('u', 502, 'x', {}, None), ConnectionError('dut'))):
            cong = Cong(); r, exc, _ = self.chay(cong, El(exc=exc_), loi='c' * 20 + str(i)); self.assertIsNotNone(exc)
            self.assertIn('khong_ro_credit', cong.ten()); self.assertNotIn('huy_credit', cong.ten())

    def test_chenh_ngoai_khoang_la_khong_ro(self):  # #6
        for i, dd in enumerate(((100.0, 100.0), (100.0, 90.0), (100.0, 5000.0))):   # 0, am, > giu (n=100 -> giu 100)
            cong = Cong(); r, exc, _ = self.chay(cong, El(da_dung=dd), loi='b' * 99 + str(i))
            self.assertIsNone(exc); self.assertIn('khong_ro_credit', cong.ten()); self.assertNotIn('xong_credit', cong.ten())

    def test_doc_da_dung_sau_loi_la_khong_ro(self):  # #6
        cong = Cong(); r, exc, _ = self.chay(cong, El(doc_loi=True)); self.assertIsNone(exc); self.assertIn('khong_ro_credit', cong.ten())

    def test_chenh_trong_khoang_xong_credit_dung_so(self):
        cong = Cong(); r, exc, _ = self.chay(cong, El(da_dung=(100.0, 137.2, 137.2)))
        self.assertEqual(cong.kw('xong_credit')[0]['credit_that'], 37.2); self.assertEqual(r, ('goi', 37.2))

    def test_giu_bang_n_nhan_1(self):  # #4
        cong = Cong(); self.chay(cong, El(), loi='a' * 250)
        self.assertEqual(cong.kw('giu_credit')[0]['credit_uoc'], 250.0)
        self.assertEqual(giong.GIA_TOI_DA[(giong.VOICE_MAC_DINH, 'eleven_v3')], 1.0)

    def test_vuot_tran_tu_choi_truoc_tts(self):  # #4: SG_GIONG_MAY=0 (hoac --khong-may) => giu raise cu
        for kw, env in (({}, {'SG_GIONG_MAY': '0'}), ({'khong_may': True}, {})):
            cong = Cong(kho={'vuot': True}); el = El()
            with mock.patch.dict(os.environ, env), mock.patch.object(giong.giong_may, 'doc_may') as dm: r, exc, _ = self.chay(cong, el, **kw)
            self.assertIsNotNone(exc); self.assertIn('TU CHOI', str(exc)); self.assertEqual(el.tts_n, 0); dm.assert_not_called()

    def test_vuot_tran_thi_doc_bang_may(self):   # SG-GIONG-may: vuot_tran la True => dich vu may, khong goi ElevenLabs, ly do vuot_tran
        cong = Cong(kho={'vuot': True}); el = El()
        with mock.patch.object(giong.giong_may, 'doc_may', return_value=('may', 0)) as dm: r, exc, out = self.chay(cong, el, muoi='lan2')
        self.assertIsNone(exc); self.assertEqual(r, ('may', 0)); self.assertEqual(el.tts_n, 0); self.assertEqual(el.goi_n, 0)
        self.assertEqual(dm.call_args.kwargs['ly_do'], 'vuot_tran'); self.assertEqual(dm.call_args.kwargs['muoi'], 'lan2'); self.assertEqual(dm.call_args.args[0].strip(), ('xin chao ' * 10).strip())
        self.assertNotIn('huy_credit', cong.ten()); self.assertIn('DU PHONG', out)

    def test_thieu_id_ma_khong_vuot_tran_thi_van_raise(self):   # Sol #1: id None nhung vuot_tran khong phai True => KHONG dung may
        class Cong2(Cong):
            def goi(s, viec, lap_lai=True, **kw):
                return {'ok': True, 'id': None} if viec == 'giu_credit' else super().goi(viec, lap_lai, **kw)
        with mock.patch.object(giong.giong_may, 'doc_may') as dm: r, exc, _ = self.chay(Cong2(), El())
        self.assertIsNotNone(exc); dm.assert_not_called()

    def test_loi_may_thi_loi_ca_hai_ly_do(self):
        with mock.patch.object(giong.giong_may, 'doc_may', side_effect=giong.Loi('LOI giong may: x')): r, exc, _ = self.chay(Cong(kho={'vuot': True}), El())
        self.assertIn('vuot tran', str(exc.code)); self.assertIn('LOI giong may: x', str(exc.code))

    class El2(El):
        def goi(s, body, timeout=180):
            return {'gioi_han': 20000, 'da_dung': 9950} if body['action'] == 'goi' else super().goi(body)

    def test_du_phong_tinh_theo_giu_khong_theo_uoc_thap(self):  # #4: con 10050, giu 100 -> con-giu=9950 < 10000 => tu choi, huy, 0 tts (SG_GIONG_MAY=0)
        cong = Cong(); el = self.El2()
        with mock.patch.dict(os.environ, {'SG_GIONG_MAY': '0'}): r, exc, _ = self.chay(cong, el)
        self.assertIsNotNone(exc); self.assertEqual(el.tts_n, 0); self.assertIn('huy_credit', cong.ten())

    def test_du_phong_tai_khoan_huy_roi_doc_may(self):   # huy_credit nhu cu roi doc bang may, ly do du_phong_tai_khoan
        cong = Cong(); el = self.El2()
        with mock.patch.object(giong.giong_may, 'doc_may', return_value=('may', 0)) as dm: r, exc, _ = self.chay(cong, el)
        self.assertIsNone(exc); self.assertEqual(r, ('may', 0)); self.assertEqual(el.tts_n, 0); self.assertEqual(cong.ten()[-1], 'huy_credit')
        self.assertEqual(dm.call_args.kwargs['ly_do'], 'du_phong_tai_khoan')

    def test_tts_quota_exceeded_huy_roi_doc_may(self):   # chi 'tts 4xx: quota_exceeded'
        cong = Cong(); el = El(tts={'ok': False, 'loi': 'tts 401: quota_exceeded'})
        with mock.patch.object(giong.giong_may, 'doc_may', return_value=('may', 0)) as dm: r, exc, _ = self.chay(cong, el)
        self.assertIsNone(exc); self.assertEqual(r, ('may', 0)); self.assertEqual(cong.ten()[-1], 'huy_credit'); self.assertNotIn('khong_ro_credit', cong.ten())
        self.assertEqual(dm.call_args.kwargs['ly_do'], 'quota_exceeded')
        cong = Cong(); el = El(tts={'ok': False, 'loi': 'tts 401: quota_exceeded'})
        with mock.patch.dict(os.environ, {'SG_GIONG_MAY': '0'}), mock.patch.object(giong.giong_may, 'doc_may') as dm: r, exc, _ = self.chay(cong, el)
        self.assertIsNotNone(exc); self.assertIn('huy_credit', cong.ten()); dm.assert_not_called()

    def test_tts_4xx_khac_hoac_khong_ro_khong_doc_may(self):   # khoa sai, loi 5xx, chua_ro, cong hong, HTTPError => nguyen hanh vi dung
        for tts, exc_ in (({'ok': False, 'loi': 'tts 401: bad key'}, None), ({'ok': False, 'loi': 'tts 500: quota_exceeded'}, None), ({'ok': False, 'loi': 'luu: quota_exceeded'}, None),
                          ({'ok': False, 'loi': 'tts 429: not_quota_exceeded_x'}, None), (None, urllib.error.HTTPError('u', 429, 'quota_exceeded', {}, None))):
            cong = Cong(); el = El(tts=tts, exc=exc_)
            with mock.patch.object(giong.giong_may, 'doc_may') as dm: r, exc, _ = self.chay(cong, el)
            self.assertIsNotNone(exc, tts); dm.assert_not_called()
        for cong in (Cong(hong={'tim_credit_khoa'}), Cong(kho={'dong': None, 'chua_ro': [{'id': 3}]})):
            with mock.patch.object(giong.giong_may, 'doc_may') as dm: r, exc, _ = self.chay(cong, El())
            self.assertIsNotNone(exc); dm.assert_not_called()

    def test_giong_nguon_ghi_moi_lan_thanh_cong(self):
        import json
        g = self.t / 'ra' / 'giong-nguon.json'
        r, exc, _ = self.chay(Cong(), El(da_dung=(100.0, 137.2, 137.2))); self.assertEqual(r[0], 'goi')
        d = json.loads(g.read_text(encoding='utf-8')); self.assertEqual((d['nguon'], d['cach']), ('elevenlabs', 'goi'))
        r, exc, _ = self.chay(Cong(), El()); self.assertEqual(r, ('kho', 0)); self.assertEqual(json.loads(g.read_text(encoding='utf-8'))['cach'], 'kho')
        r, exc, _ = self.chay(Cong(kho={'dong': {'id': 5, 'trang_thai': 'xong', 'tep': PATH}, 'link': LINK_GIA}), El(), loi='kho rieng ' * 10)
        self.assertEqual(json.loads(g.read_text(encoding='utf-8'))['cach'], 'kho-rieng')
        g.write_text('{"nguon":"may"}')   # tep cu khong duoc lan sang luot loi
        r, exc, _ = self.chay(Cong(hong={'tim_credit_khoa'}), El(), loi='loi khac ' * 10); self.assertIsNotNone(exc); self.assertFalse(g.exists())

    def test_khong_in_khoa(self):
        cong = Cong(hong={'ghi_tep_credit', 'xong_credit'}); r, exc, out = self.chay(cong, El(da_dung=(1.0, 2.0)))
        for b in (KHOA_GIA, ANON_GIA, 'LINKBIMAT999999'): self.assertNotIn(b, out)
        r, exc, out = self.chay(Cong(), El(), tai=tai_hong, loi='khac hoan toan ' * 5)
        for b in (KHOA_GIA, ANON_GIA, 'LINKBIMAT999999'): self.assertNotIn(b, out + str(exc))

    def test_kho_cuc_bo_co_thi_khong_goi_cong(self):
        cong = Cong(); f = giong.kho_dir() / (giong.khoa_kho('xin chao ' * 10, giong.VOICE_MAC_DINH, 'eleven_v3', 0.0, 1.0) + '.mp3'); f.write_bytes(b'x' * 6000)
        r, exc, _ = self.chay(cong, El()); self.assertEqual(r, ('kho', 0)); self.assertEqual(cong.goi_ds, [])


class TestGoiA2(Khung):
    """Dot 2 (Sol soi ke hoach): tran theo cap giong, dong/chua_ro, muoi lan2, HOI_QUY, pytest."""
    def test_cap_giong_khong_co_trong_bang_bi_tu_choi_truoc_khi_giu(self):  # 1
        cong = Cong(); el = El()
        for kw in ({'voice': 'KHAC_VOICE_ID'}, {'model': 'eleven_v4'}):
            r, exc, _ = self.chay(cong, el, loi='d' * 50 + str(kw), **kw)
            self.assertIsNotNone(exc); self.assertIn('TU CHOI', str(exc))
        self.assertNotIn('giu_credit', cong.ten()); self.assertEqual(el.tts_n, 0)

    def test_dong_ma_link_null_thi_dung_khong_tts(self):  # 2
        cong = Cong(kho={'dong': {'id': 5, 'trang_thai': 'giu', 'tep': PATH}, 'link': None}); el = El()
        r, exc, _ = self.chay(cong, el); self.assertIn('DUNG', str(exc)); self.assertEqual(el.tts_n, 0); self.assertNotIn('giu_credit', cong.ten())

    def test_dong_ma_tai_hong_thi_dung_khong_tts(self):  # 2
        cong = Cong(kho={'dong': {'id': 5, 'trang_thai': 'giu', 'tep': PATH}, 'link': LINK_GIA}); el = El()
        r, exc, out = self.chay(cong, el, tai=tai_hong); self.assertIn('KHONG thu moi', str(exc)); self.assertEqual(el.tts_n, 0)
        self.assertNotIn('giu_credit', cong.ten()); self.assertNotIn('LINKBIMAT999999', str(exc) + out)

    def test_chua_ro_ma_khong_dong_thi_dung(self):  # 2
        cong = Cong(kho={'dong': None, 'chua_ro': [{'id': 41, 'trang_thai': 'khong_ro'}, {'id': 42, 'trang_thai': 'giu'}]}); el = El()
        r, exc, _ = self.chay(cong, el); self.assertIn('41', str(exc)); self.assertIn('42', str(exc)); self.assertIn('doi soat', str(exc))
        self.assertEqual(el.tts_n, 0); self.assertNotIn('giu_credit', cong.ten())

    def test_cong_hong_khi_tra_kho_thi_dung(self):  # 2
        cong = Cong(hong={'tim_credit_khoa'}); el = El(); r, exc, _ = self.chay(cong, el)
        self.assertIn('DUNG', str(exc)); self.assertNotIn(KHOA_GIA, str(exc)); self.assertEqual(el.tts_n, 0); self.assertNotIn('giu_credit', cong.ten())

    def test_ghi_tep_hong_3_lan_va_tai_hong_bao_bi_chan(self):  # 3
        cong = Cong(hong={'ghi_tep_credit'}); el = El(); r, exc, _ = self.chay(cong, el, tai=tai_hong)
        self.assertEqual(cong.ten().count('ghi_tep_credit'), 3); self.assertIn('BI CHAN', str(exc)); self.assertNotIn('tu phuc hoi', str(exc))

    def test_ghi_tep_hong_nhung_tai_duoc_thi_di_tiep_nhung_khong_xong(self):  # 3 + vong 2 #2
        cong = Cong(hong={'ghi_tep_credit'}); r, exc, _ = self.chay(cong, El(da_dung=(10.0, 20.0)))
        self.assertIsNone(exc); self.assertEqual(r[0], 'goi'); self.assertNotIn('xong_credit', cong.ten())
        self.assertEqual(cong.kw('khong_ro_credit')[0]['ghi_chu'], 'chua ghi duoc tep')

    def test_ghi_tep_so_dong_khac_1_cung_la_chua_ghi(self):   # vong 2 #2: chi coi ghi thanh cong khi so_dong == 1
        cong = Cong(); cong.so_dong_ghi = 0; r, exc, _ = self.chay(cong, El(da_dung=(10.0, 20.0)))
        self.assertIsNone(exc); self.assertNotIn('xong_credit', cong.ten()); self.assertIn('khong_ro_credit', cong.ten())

    def test_doc_lai_da_dung_cho_cap_nhat_tre(self):   # vong 2 #1: lan 1-2 chenh=0, lan 3 = 230
        cong = Cong(); el = El(da_dung=(100.0, 100.0, 100.0, 330.0, 330.0)); waits = []
        o = io.StringIO()
        with contextlib.redirect_stdout(o):
            r = giong.cmd_giong(self.args(loi='xin chao ' * 30), cong=cong, el=el, ngu=waits.append, tai=tai_ok)
        self.assertEqual(r, ('goi', 230.0)); self.assertEqual(cong.kw('xong_credit')[0]['credit_that'], 230.0)
        self.assertEqual(waits.count(10), 3); self.assertIn('4 lan', o.getvalue())

    def test_doc_lai_het_8_lan_van_0_la_khong_ro(self):   # vong 2 #1
        cong = Cong(); el = El(da_dung=(100.0,) * 9); waits = []
        with contextlib.redirect_stdout(io.StringIO()):
            r = giong.cmd_giong(self.args(loi='xin chao ' * 30), cong=cong, el=el, ngu=waits.append, tai=tai_ok)
        self.assertIn('khong_ro_credit', cong.ten()); self.assertNotIn('xong_credit', cong.ten()); self.assertEqual(el.goi_n, 9)

    def test_quyet_toan_doi_on_dinh_100_110_160_160_ghi_60(self):   # Sol soi cuoi P1: cu dung o 110 ghi 10
        cong = Cong(); el = El(da_dung=(100.0, 110.0, 160.0, 160.0)); waits = []
        with contextlib.redirect_stdout(io.StringIO()):
            r = giong.cmd_giong(self.args(loi='xin chao ' * 30), cong=cong, el=el, ngu=waits.append, tai=tai_ok)
        self.assertEqual(r, ('goi', 60.0)); self.assertEqual(cong.kw('xong_credit')[0]['credit_that'], 60.0)

    def test_quyet_toan_khong_on_dinh_het_8_lan_la_khong_ro(self):
        cong = Cong(); el = El(da_dung=(100.0, 110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0, 180.0)); waits = []
        with contextlib.redirect_stdout(io.StringIO()):
            giong.cmd_giong(self.args(loi='xin chao ' * 30), cong=cong, el=el, ngu=waits.append, tai=tai_ok)
        self.assertNotIn('xong_credit', cong.ten()); self.assertIn('khong_ro_credit', cong.ten()); self.assertEqual(el.goi_n, 9)

    def keys(self, muoi='lan2', loi='xin chao ' * 10):
        return (giong.khoa_kho(loi, giong.VOICE_MAC_DINH, 'eleven_v3', 0.0, 1.0), giong.khoa_kho(loi, giong.VOICE_MAC_DINH, 'eleven_v3', 0.0, 1.0, muoi))

    def test_muoi_khoa_goc_co_dong_thi_dung_khoa_muoi(self):  # 4
        goc, muoi = self.keys(); cong = Cong(theo={goc: {'dong': {'id': 1, 'trang_thai': 'xong', 'tep': PATH}, 'link': LINK_GIA}}); el = El()
        r, exc, out = self.chay(cong, el, muoi='lan2'); self.assertIsNone(exc); self.assertEqual(el.tts_n, 1)
        self.assertEqual(cong.kw('giu_credit')[0]['khoa_kho'], muoi); self.assertIn('muoi', out)

    def test_muoi_khoa_goc_chua_ro_thi_dung(self):  # 4
        goc, muoi = self.keys(); cong = Cong(theo={goc: {'dong': None, 'chua_ro': [{'id': 9}]}}); el = El()
        r, exc, _ = self.chay(cong, el, muoi='lan2'); self.assertIn('9', str(exc)); self.assertEqual(el.tts_n, 0); self.assertNotIn('giu_credit', cong.ten())

    def test_muoi_khoa_goc_khong_co_gi_thi_dung_khoa_goc(self):  # 4
        goc, muoi = self.keys(); cong = Cong(); el = El()
        r, exc, out = self.chay(cong, el, muoi='lan2'); self.assertIsNone(exc)
        self.assertEqual(cong.kw('giu_credit')[0]['khoa_kho'], goc); self.assertIn('KHOA GOC', out)

    def test_muoi_khoa_muoi_co_dong_thi_chi_phuc_hoi(self):  # 4 + 2
        goc, muoi = self.keys(); cong = Cong(theo={goc: {'dong': {'id': 1, 'trang_thai': 'xong', 'tep': PATH}, 'link': LINK_GIA},
                                                    muoi: {'dong': {'id': 2, 'trang_thai': 'giu', 'tep': PATH}, 'link': LINK_GIA}}); el = El()
        r, exc, _ = self.chay(cong, el, muoi='lan2'); self.assertEqual(r, ('kho-rieng', 0)); self.assertEqual(el.tts_n, 0)

    def test_muoi_khoa_goc_dong_giu_thi_phuc_hoi_khoa_goc(self):   # vong 2 #3
        goc, muoi = self.keys(); cong = Cong(theo={goc: {'dong': {'id': 1, 'trang_thai': 'giu', 'tep': PATH}, 'link': LINK_GIA}}); el = El()
        r, exc, _ = self.chay(cong, el, muoi='lan2'); self.assertIsNone(exc); self.assertEqual(r, ('kho-rieng', 0)); self.assertEqual(el.tts_n, 0)
        self.assertNotIn('giu_credit', cong.ten()); self.assertNotIn(muoi, [k.get('khoa_kho') for k in cong.kw('tim_credit_khoa')])

    def test_muoi_khoa_goc_dong_khong_ro_thi_dung_khoa_muoi(self):   # vong 2 #3
        goc, muoi = self.keys(); cong = Cong(theo={goc: {'dong': {'id': 1, 'trang_thai': 'khong_ro', 'tep': PATH}, 'link': LINK_GIA}}); el = El()
        r, exc, _ = self.chay(cong, el, muoi='lan2'); self.assertIsNone(exc); self.assertEqual(cong.kw('giu_credit')[0]['khoa_kho'], muoi)

    def test_docstring_ghi_gioi_han_khong_nguyen_tu(self):  # 7
        self.assertIn('KHONG nguyen tu', giong.__doc__); self.assertIn('khong chong gio', giong.__doc__)


if __name__ == '__main__': unittest.main()
