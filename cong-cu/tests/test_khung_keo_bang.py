# 12/10: 5 gia tri `dang` (tin-nhanh, top5, keo-thom-2, keo-thom, keo-thom-3) phai dong nhat o MOI bang ten/gio trong repo.
#   uv run --frozen python -m pytest cong-cu/tests/test_khung_keo_bang.py -q
import ast,pathlib,re,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
for p in (ROOT,ROOT/'cong-cu'): sys.path.insert(0,str(p))
GIO={'tin-nhanh':'07:30','top5':'12:00','keo-thom-2':'15:00','keo-thom':'20:00','keo-thom-3':'22:00'}
def khuon(dang): return re.sub(r'-\d+$','',dang)    # = bieu thuc KHUON cua dung.yml (startsWith keo-thom)
class BangKhungKeo(unittest.TestCase):
    def test_khuon_bo_hau_to(self):
        self.assertEqual({d:khuon(d) for d in GIO},{'tin-nhanh':'tin-nhanh','top5':'top5','keo-thom-2':'keo-thom','keo-thom':'keo-thom','keo-thom-3':'keo-thom'})
        for d in GIO: self.assertTrue((ROOT/'khuon'/khuon(d)).is_dir(),d)
    def test_dang_chay_gio(self):
        from dang import chay; self.assertEqual(chay.GIO,GIO)
    def test_dang_manifest_hop_le(self):
        from dang import manifest; self.assertEqual(set(manifest.DANG_HOP_LE),set(GIO))
    def test_nghe_so_gio_mac_dinh(self):
        import nghe_so as ns; self.assertEqual(ns.GIO_DANG_MAC_DINH,GIO)
    def test_kiem_do_moi_ten(self):
        import kiem_do_moi as k; self.assertEqual(set(k.TEN_DANG),set(GIO)); self.assertEqual(len(set(k.TEN_DANG.values())),5)    # moi khung ten rieng de canh bao biet khung nao
    def test_cong_cu_manifest_gio_va_tieu_de(self):
        src=(ROOT/'cong-cu'/'manifest.py').read_text(encoding='utf-8')
        gio=ast.literal_eval(re.search(r'^GIO=(\{.*\})$',src,re.M).group(1)); self.assertEqual(gio,GIO)
        td=ast.literal_eval(re.search(r'^TD=(\{.*\})$',src,re.M).group(1)); self.assertEqual(set(td),set(GIO))
        for d in ('keo-thom-2','keo-thom-3'): self.assertEqual(td[d],td['keo-thom'])    # tieu de bai dang giong keo-thom
    def test_site_regex_tag(self):
        src=(ROOT/'dang'/'site.py').read_text(encoding='utf-8'); m=re.search(r'r"%s-(\(\\d\{4\}.*?)" %',src); self.assertTrue(m)
        mau=r'(?:v)-'+m.group(1)
        for d in GIO: self.assertTrue(re.fullmatch(mau,f'v-2026-10-13-{d}'),d); self.assertEqual(re.fullmatch(mau,f'v-2026-10-13-{d}').group(2),d)    # keo-thom-2 khong bi nuot thanh keo-thom
        self.assertFalse(re.fullmatch(mau,'v-2026-10-13-keo-thom-4'))
    def test_workflow_options_va_regex(self):
        for f in ('dung.yml','dang.yml','kiem-gio.yml'):
            y=(ROOT/'.github'/'workflows'/f).read_text(encoding='utf-8'); self.assertIn('options: [tin-nhanh, top5, keo-thom-2, keo-thom, keo-thom-3]',y,f)
        self.assertIn('^(tin-nhanh|top5|keo-thom|keo-thom-2|keo-thom-3)$',(ROOT/'.github'/'workflows'/'dang.yml').read_text(encoding='utf-8'))
    def test_chay_sh_dang_cho_giong(self):
        sh=(ROOT/'khuon'/'keo-thom'/'chay.sh').read_text(encoding='utf-8'); self.assertIn('--dang "${DANG:-keo-thom}"',sh); self.assertNotIn('--dang keo-thom',sh)
if __name__=='__main__': unittest.main()
