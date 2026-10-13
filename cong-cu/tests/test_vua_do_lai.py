"""Dot 2a (D, F): vua() cua keo-thom + tin-nhanh full.html do lai sau khi thu chu (loi Top 5 #65: co chu khong ti le thuan be rong -> van tran 3 px).
Chay ham THAT trich tu full.html trong node voi phan tu gia (be rong = ham phi tuyen cua co chu)."""
import json, pathlib, re, shutil, subprocess, unittest

KHUON = pathlib.Path(__file__).resolve().parents[2] / 'khuon'
KIEU = r'''
const src = %s; const vua = new Function(src + '; return vua')();
function phanTu(rong) { const el = {style: {}, fs() { return parseFloat(this.style.fontSize); }}; Object.defineProperty(el, 'scrollWidth', {get() { return Math.round(rong(el.fs())); }}); el.getBoundingClientRect = () => ({width: rong(el.fs())}); return el; }
const kq = {};
// phi tuyen: moi 10 px co them 1 px (kerning/hinting) -> thu ti le lan dau van du 2-3 px
const rong = fs => 9.3 * fs + 3.5 * Math.floor(fs / 8);
const el = phanTu(rong); vua(el, 400, 60); kq.vua = [el.fs(), rong(el.fs())];
const el2 = phanTu(rong); vua(el2, 100000, 40); kq.du_cho = [el2.fs(), rong(el2.fs())];       // vua san: giu nguyen co
const el3 = phanTu(fs => 5000); vua(el3, 10, 50); kq.khong_the = el3.fs();                      // khong bao gio vua: phai ket thuc, khong lap vo han
console.log(JSON.stringify(kq));
'''


def trich(html):
    for dong in html.splitlines():
        if dong.startswith('function vua('): return dong
    raise AssertionError('khong thay function vua(')


@unittest.skipUnless(shutil.which('node'), 'can node')
class TestVuaDoLai(unittest.TestCase):
    def _chay(self, khuon):
        src = trich((KHUON / khuon / 'full.html').read_text(encoding='utf-8'))
        r = subprocess.run(['node', '-e', KIEU % json.dumps(src)], capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr); return json.loads(r.stdout)

    def test_vua_do_lai_ca_3_khuon(self):
        for k in ('keo-thom', 'tin-nhanh', 'top5'):
            kq = self._chay(k)
            fs, w = kq['vua']; self.assertLessEqual(w, 400, f'{k}: van tran {w}'); self.assertGreater(w, 400 - 12, f'{k}: thu qua tay ({w})')
            self.assertEqual(kq['du_cho'][0], 40, k); self.assertLessEqual(kq['khong_the'], 8, k)   # khong bao gio vua: ket thuc (khong lap vo han), khong xuong duoi san 8 px bang vong giam

    def test_keo_va_tin_nhanh_khong_con_ban_thu_mot_lan(self):
        for k in ('keo-thom', 'tin-nhanh'):
            self.assertIn('while(do_()>max', trich((KHUON / k / 'full.html').read_text(encoding='utf-8')), k)


if __name__ == '__main__':
    unittest.main()
