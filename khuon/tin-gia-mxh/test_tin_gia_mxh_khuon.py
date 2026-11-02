"""Test khuon tin gia fb/ig/threads (KE-HOACH SG-DU-KENH muc 3.3).
Phan thuan (kiem K1-K9 tren do.json mau, ffprobe/ffmpeg that) luon chay; phan dung that (Playwright) tu skip khi thieu
cong-cu/node_modules/playwright hoac trinh duyet. Chay: uv run --frozen python -m pytest khuon/tin-gia-mxh -q
"""
import copy, importlib.util, json, pathlib, shutil, subprocess, sys
import pytest

B = pathlib.Path(__file__).resolve().parent
REPO = B.parent.parent


def _nap(ten, tep):
    sp = importlib.util.spec_from_file_location(ten, B / tep)
    m = importlib.util.module_from_spec(sp)
    sys.modules[ten] = m
    sp.loader.exec_module(m)
    return m


KIEM = _nap('tin_gia_mxh_kiem', 'kiem.py')
DUNG = _nap('tin_gia_mxh_dung', 'dung.py')

TEN70 = ('MONSTER HUNTER RISE: SUNBREAK DELUXE EDITION + ULTIMATE BONUS PACK X' + 'XY')[:70]


def dl_fb(n=5, ten='MONSTER HUNTER RISE'):
    v = [{'ma': 'SG', 'ten': 'Singapore', 'vnd': 330000}, {'ma': 'HK', 'ten': 'Hồng Kông', 'vnd': 280000},
         {'ma': 'TH', 'ten': 'Thái Lan', 'vnd': 280000}, {'ma': 'ID', 'ten': 'Indonesia', 'vnd': 210000}, {'ma': 'US', 'ten': 'Mỹ', 'vnd': 180000}]
    v = v[:n - 1] + v[-1:]
    return {'kenh': 'fb', 'ngay': '2026-11-02', 'ten': ten, 'bia': 'bia.jpg', 'nen': ['c0.jpg', 'c1.jpg'], 'gia_vnd': 180000, 'vung': v,
            're_hon': {'ten': v[0]['ten'], 'vnd': v[0]['vnd'] - 180000},
            'the': {'ma': 'US', 'ten_vung': 'Mỹ', 'the': [{'menh_gia': '$5', 'so_luong': 1}], 'gia_game': '$4,79', 'du': '$0,21'},
            'goc': '$39,99', 'giam': 88, 'han_chu': '14:59 · 5/11'}


def dl_ig(n=4, ten_dau='FINAL FANTASY VII REBIRTH', **kw):
    gia = [460000, 460000, 316000, 216000, 180000][:n]
    g = [{'ten': ten_dau if i == 0 else f'FINAL FANTASY {i}', 'bia': 'bia.jpg', 'nen': 'c0.jpg', 'gia_vnd': p, 'ma_vung': 'US', 'giam': 70} for i, p in enumerate(gia)]
    d = {'kenh': 'ig', 'ngay': '2026-11-02', 'tieu_de': [f'{n} GAME', 'FINAL FANTASY', 'DƯỚI 500K'], 'game': g, 'han_chu': '14:59 · 5/11',
         'giam_chung': 70, 'vung_chung': 'Mỹ'}
    d.update(kw)
    return d


def dl_th(ten_a='FINAL FANTASY VII REBIRTH', ten_b='FINAL FANTASY XII THE ZODIAC AGE'):
    return {'kenh': 'threads', 'ngay': '2026-11-02', 'cau_hoi': ['Có 460 nghìn,', 'chọn bên nào?'],
            'a': {'ten': ten_a, 'bia': 'bia.jpg', 'nen': 'c0.jpg', 'gia_vnd': 460000, 'sao': '4,66', 'luot': '64.676'},
            'b': {'ten': ten_b, 'bia': 'bia.jpg', 'nen': 'c1.jpg', 'gia_vnd': 460000, 'sao': '4,75', 'luot': '11.893'},
            'chan': 'Store Mỹ $14,99 (−70%) · thẻ $10 + $5 · hết giảm 14:59 · 5/11'}


def e(id_, chu, x0=100, y0=400, x1=300, y1=450, op=1.0, cw=200, sw=200, lop=''):
    return {'id': id_, 'lop': lop, 'chu': chu, 'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1, 'op': op, 'fs': 40, 'sw': sw, 'cw': cw, 'sh': 50, 'ch': 50, 'dong': 1}


# ---------- phan thuan ----------
def test_k4_vung_an_toan():
    ok = {'mau': [{'t': 0, 'phan_tu': [e('a', '1', 100, 300, 900, 400)]}]}
    assert KIEM.k4(ok)['dat']
    lo = {'mau': [{'t': 0, 'phan_tu': [e('a', '1', 100, 1230, 900, 1300)]}]}
    assert not KIEM.k4(lo)['dat']
    ngoai = {'mau': [{'t': 0, 'phan_tu': [e('a', '1', -5, 300, 900, 400)]}]}
    assert not KIEM.k4(ngoai)['dat']
    mo = {'mau': [{'t': 0, 'phan_tu': [e('a', '1', 100, 1300, 900, 1400, op=0.2)]}]}      # dang mo dan (op<0,5): khong tinh
    assert KIEM.k4(mo)['dat']


def test_k5_tran_chu():
    assert KIEM.k5({'mau': [{'t': 0, 'phan_tu': [e('a', 'x', cw=200, sw=201)]}]})['dat']
    assert not KIEM.k5({'mau': [{'t': 0, 'phan_tu': [e('a', 'x', cw=200, sw=260)]}]})['dat']


def test_k6_de_nhau():
    a, b = e('a', 'x', 100, 400, 300, 450), e('b', 'y', 290, 440, 400, 500)
    assert not KIEM.k6({'mau': [{'t': 0, 'phan_tu': [a, b]}]})['dat']
    c = e('c', 'y', 301, 400, 400, 450)
    assert KIEM.k6({'mau': [{'t': 0, 'phan_tu': [a, c]}]})['dat']
    m = copy.deepcopy(b); m['op'] = 0.3
    assert KIEM.k6({'mau': [{'t': 0, 'phan_tu': [a, m]}]})['dat']


def _do_fb(dl):
    r = [e(f's{i}', DUNG_vnd(x['vnd'])) for i, x in enumerate(dl['vung'])]
    return {'mau': [{'t': 0, 'phan_tu': [e('dau-gia', DUNG_vnd(dl['gia_vnd']))]}, {'t': 4.6, 'phan_tu': r},
                    {'t': 8.6, 'phan_tu': [e('bang', '= ' + DUNG_vnd(dl['gia_vnd'])), e('chip', 'Gốc $39,99'), e('chip2', '−88%'), e('h', '14:59 · 5/11')]}]}


def DUNG_vnd(n):
    return KIEM.vnd(n)


def test_k7_so_dung_va_so_la():
    dl = dl_fb()
    do = _do_fb(dl)
    assert KIEM.k7(do, dl)['dat'], KIEM.k7(do, dl)
    xau = copy.deepcopy(do); xau['mau'][1]['phan_tu'][2]['chu'] = '281.000đ'            # sua tay 1 so
    assert not KIEM.k7(xau, dl)['dat']
    la = copy.deepcopy(do); la['mau'][2]['phan_tu'].append(e('x', 'giảm 99%'))
    assert not KIEM.k7(la, dl)['dat']
    gia = copy.deepcopy(do); gia['mau'][0]['phan_tu'][0]['chu'] = '181.000đ'
    assert not KIEM.k7(gia, dl)['dat']
    it = copy.deepcopy(do); it['mau'][1]['phan_tu'].pop()                               # thieu 1 dong store
    assert not KIEM.k7(it, dl)['dat']
    dem = copy.deepcopy(do); dem['mau'][0]['phan_tu'].append(e('s0', '209.000đ'))       # o dem so giua chung: khong bi coi la so la
    assert KIEM.k7(dem, dl)['dat']


def test_k8_khung_0():
    dl = dl_fb()
    assert KIEM.k8({'mau': [{'t': 0, 'phan_tu': [e('dau-gia', '180.000đ')]}]}, dl)['dat']
    assert not KIEM.k8({'mau': [{'t': 0, 'phan_tu': [e('dau-gia', '180.000đ', op=0.5)]}]}, dl)['dat']
    assert not KIEM.k8({'mau': [{'t': 0, 'phan_tu': []}]}, dl)['dat']


def test_k2_k3_logic():
    assert KIEM.k2({'lufs': -14.1, 'dinh_that': -1.5, 'dau_mean': -20})['dat']
    assert not KIEM.k2({'lufs': -20, 'dinh_that': -1.5, 'dau_mean': -20})['dat']
    assert not KIEM.k2({'lufs': -14, 'dinh_that': -0.2, 'dau_mean': -20})['dat']
    assert not KIEM.k2({'lufs': -14, 'dinh_that': -1.5, 'dau_mean': -50})['dat']
    assert KIEM.k3([40, 30, 20])['dat'] and not KIEM.k3([40, 3])['dat']


def test_kiem_dl_hop_dong():
    DUNG.kiem_dl(dl_fb()); DUNG.kiem_dl(dl_fb(3)); DUNG.kiem_dl(dl_ig(3)); DUNG.kiem_dl(dl_ig(5)); DUNG.kiem_dl(dl_th())
    x = dl_fb(); x['vung'].reverse()
    with pytest.raises(DUNG.Loi): DUNG.kiem_dl(x)
    x = dl_fb(); x['vung'] = x['vung'][:2]
    with pytest.raises(DUNG.Loi): DUNG.kiem_dl(x)
    x = dl_fb(); x['gia_vnd'] = 190000
    with pytest.raises(DUNG.Loi): DUNG.kiem_dl(x)
    x = dl_ig(vung_chung=None); x['game'][1].pop('ma_vung')
    with pytest.raises(DUNG.Loi): DUNG.kiem_dl(x)
    DUNG.kiem_dl(dl_ig(vung_chung=None, giam_chung=None, han_khac=True))


def _ffmpeg(*a):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *a], check=True)


def test_k1_k2_k3_ffmpeg_that(tmp_path):
    v = tmp_path / 'v.mp4'
    _ffmpeg('-f', 'lavfi', '-i', 'testsrc=s=1080x1920:r=30:d=11', '-f', 'lavfi', '-i', 'sine=f=440:sample_rate=48000:d=11', '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ar', '48000', '-ac', '2', str(v))
    pr = KIEM.ffprobe(v)
    assert KIEM.k1(pr, v.stat().st_size)['dat']
    am = KIEM.do_am(v)
    assert am['lufs'] is not None and am['dinh_that'] is not None and am['dau_mean'] is not None
    assert KIEM.k3(KIEM.do_luma(v))['dat']
    nho = tmp_path / 'n.mp4'
    _ffmpeg('-f', 'lavfi', '-i', 'testsrc=s=640x360:r=30:d=11', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(nho))
    assert not KIEM.k1(KIEM.ffprobe(nho), nho.stat().st_size)['dat']


# ---------- dung that ----------
def _co_trinh_duyet():
    if not (REPO / 'cong-cu/node_modules/playwright').exists() or not shutil.which('node'):
        return False
    js = ("import('" + (REPO / 'cong-cu/node_modules/playwright/index.mjs').as_uri() + "').then(async m=>{const b=await m.chromium.launch();await b.close()})"
          ".catch(e=>{console.error(e.message);process.exit(1)})")
    return subprocess.run(['node', '-e', js], capture_output=True).returncode == 0


@pytest.fixture(scope='module')
def tu_lieu(tmp_path_factory):
    d = tmp_path_factory.mktemp('tin_gia')
    ts = d / 'ts'; ts.mkdir()
    for ten, mau in [('bia.jpg', 'red'), ('c0.jpg', 'blue'), ('c1.jpg', 'green')]:
        _ffmpeg('-f', 'lavfi', '-i', f'color=c={mau}:s=900x900', '-frames:v', '1', str(ts / ten))
    sfx = d / 'sfx'; sfx.mkdir()
    for k in ['dong-dau', 'dau-nhe', 'giay-vut', 'lat-trang', 'dem-so', 'ka-ching', 'danh-may', 'chuong-ket']:
        _ffmpeg('-f', 'lavfi', '-i', 'sine=f=900:d=2', '-af', 'afade=t=out:st=0.3:d=1.5', str(sfx / (k + '.mp3')))
    nhac = d / 'nhac.mp3'
    _ffmpeg('-f', 'lavfi', '-i', 'sine=f=220:d=16', '-f', 'lavfi', '-i', 'sine=f=60:d=16', '-filter_complex',
            '[1:a]volume=if(lt(mod(t\\,0.5)\\,0.1)\\,1\\,0.0):eval=frame[k];[0:a]volume=0.4[m];[m][k]amix=inputs=2:normalize=0', str(nhac))
    return {'ts': ts, 'sfx': sfx, 'nhac': nhac, 'd': d}


@pytest.fixture(scope='module')
def trinh_duyet():
    if not _co_trinh_duyet():
        pytest.skip('thieu cong-cu/node_modules/playwright hoac trinh duyet')


def _dung(tl, dl, ten, bo_video=True, tmp=None):
    f = tl['d'] / (ten + '.json'); f.write_text(json.dumps(dl, ensure_ascii=False), encoding='utf-8')
    ra = tl['d'] / ten
    a = ['--kenh', dl['kenh'], '--du-lieu', str(f), '--tai-san', str(tl['ts']), '--am', str(tl['sfx']), '--nhac', str(tl['nhac']), '--ra', str(ra)]
    if bo_video:
        a.append('--bo-video')
    assert DUNG.main(a) == 0
    return ra


def _kiem_do(kenh, ra, dl):
    do = json.load(open(ra / 'do.json', encoding='utf-8'))
    if kenh == 'threads':
        return [KIEM.k4(do, KIEM.AN_TOAN_TH, 1080, 1350), KIEM.k5(do), KIEM.k6(do), KIEM.k7(do, dl, 'T3')]
    return [KIEM.k4(do), KIEM.k5(do), KIEM.k6(do), KIEM.k7(do, dl), KIEM.k8(do, dl)]


def _dat(ps):
    sai = [p for p in ps if not p['dat']]
    assert not sai, sai


def test_dung_that_3_khuon_day_du(trinh_duyet, tu_lieu):
    for dl, ten in [(dl_fb(), 'fb'), (dl_ig(), 'ig'), (dl_th(), 'th')]:
        ra = _dung(tu_lieu, dl, ten, bo_video=False)
        kq = KIEM.kiem(dl['kenh'], ra, dl)
        assert kq['dat'], json.dumps(kq, ensure_ascii=False, indent=1)


@pytest.mark.parametrize('ten,dl', [
    ('fb3', dl_fb(3)), ('fb4', dl_fb(4)), ('fb5', dl_fb(5)), ('fb70', dl_fb(5, TEN70)),
    ('ig3', dl_ig(3)), ('ig5', dl_ig(5)), ('ig70', dl_ig(4, TEN70)),
    ('ig5-70', dl_ig(5, TEN70)),
    ('th70', dl_th(TEN70, TEN70[::-1])),
])
def test_bien_the_bo_cuc(trinh_duyet, tu_lieu, ten, dl):
    _dat(_kiem_do(dl['kenh'], _dung(tu_lieu, dl, ten), dl))


def test_fb_the_hai_loai_va_dong_niem_yet(trinh_duyet, tu_lieu):
    dl = dl_fb()
    dl['the'] = {'ma': 'US', 'ten_vung': 'Mỹ', 'the': [{'menh_gia': '$10', 'so_luong': 1}, {'menh_gia': '$5', 'so_luong': 1}], 'gia_game': '$14,99', 'du': '$0,01'}
    ra = _dung(tu_lieu, dl, 'fb2the')
    _dat(_kiem_do('fb', ra, dl))
    chu = [x['chu'] for m in json.load(open(ra / 'do.json'))['mau'] for x in m['phan_tu']]
    assert 'giá niêm yết $14,99 · dư $0,01 trong ví' in chu
    assert '$10' in chu and '$5' in chu


def test_ig_vung_khac_va_han_khac(trinh_duyet, tu_lieu):
    dl = dl_ig(vung_chung=None, giam_chung=None, han_khac=True)
    for g, m in zip(dl['game'], ['US', 'HK', 'SG', 'TH']):
        g['ma_vung'] = m
    ra = _dung(tu_lieu, dl, 'igkhac')
    _dat(_kiem_do('ig', ra, dl))
    chu = [x['chu'] for m in json.load(open(ra / 'do.json'))['mau'] for x in m['phan_tu']]
    assert 'Hết giảm sớm nhất' in chu
    assert not any(c.startswith('Giảm') or c.startswith('Store') for c in chu)       # khong chip % / vung chung


def test_k7_truot_khi_dl_lech_voi_dom(trinh_duyet, tu_lieu):
    dl = dl_fb()
    ra = _dung(tu_lieu, dl, 'fblech')
    lech = copy.deepcopy(dl); lech['vung'][1]['vnd'] = 281000                      # DOM ve 280.000, dl noi 281.000
    do = json.load(open(ra / 'do.json', encoding='utf-8'))
    assert not KIEM.k7(do, lech)['dat']
    lech2 = copy.deepcopy(dl); lech2['gia_vnd'] = 170000; lech2['vung'][-1]['vnd'] = 170000
    assert not KIEM.k7(do, lech2)['dat']


def test_dung_loi_anh_thieu(trinh_duyet, tu_lieu):
    dl = dl_fb(); dl['bia'] = 'khong-co.jpg'
    f = tu_lieu['d'] / 'xau.json'; f.write_text(json.dumps(dl), encoding='utf-8')
    assert DUNG.main(['--kenh', 'fb', '--du-lieu', str(f), '--tai-san', str(tu_lieu['ts']), '--ra', str(tu_lieu['d'] / 'xau'), '--bo-video']) == 1
