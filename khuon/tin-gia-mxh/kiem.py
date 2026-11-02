#!/usr/bin/env python3
"""Kiem tin gia fb/ig/threads sau khi dung (KE-HOACH muc 3.3). In JSON {"dat":bool,"phep":[{"ten","dat","chi_tiet"}]}, thoat 0 khi dat het.

  python3 khuon/tin-gia-mxh/kiem.py --kenh fb|ig|threads --ra OUT --du-lieu dl.json
Doc OUT/video.mp4 + OUT/bia.jpg (fb/ig) hoac OUT/anh.png (threads) va OUT/do.json (do.mjs).
"""
import argparse, json, pathlib, re, subprocess, sys

AN_TOAN = (60, 269, 1020, 1248)       # fb/ig: chu trong vung nay (Reels/FB che tren 14 %, duoi 35 %)
AN_TOAN_TH = (30, 30, 1050, 1320)     # threads anh 1080x1350
KHUNG = {'fb': (1080, 1920), 'ig': (1080, 1920), 'threads': (1080, 1350)}
TOKEN = re.compile(r'\d+(?:[.,:/]\d+)*')
DEM = re.compile(r'^(s|gs)\d+$')       # o dem so (count-up): chi kiem gia tri cuoi
DUOI_ANH = ('.jpg', '.jpeg', '.png', '.webp', '.svg')


def P(ten, dat, ct=''):
    return {'ten': ten, 'dat': bool(dat), 'chi_tiet': ct}


def vnd(n):
    return f'{int(n):,}'.replace(',', '.') + 'đ'


def vk(n):
    return f'{n // 1000}K' if n % 1000 == 0 else vnd(n)


# ---------- do bang ffprobe / ffmpeg ----------
def chay_ff(lenh):
    r = subprocess.run(lenh, capture_output=True)
    return r.returncode, r.stdout, r.stderr.decode('utf-8', 'replace')


def ffprobe(path):
    rc, out, err = chay_ff(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)])
    if rc != 0:
        raise RuntimeError('ffprobe loi: ' + err[-200:])
    return json.loads(out)


def do_am(path):
    """-> dict(luufs, dinh_that, dau) hoac nem loi."""
    rc, _, err = chay_ff(['ffmpeg', '-nostats', '-hide_banner', '-i', str(path), '-vn', '-af', 'ebur128=peak=true', '-f', 'null', '-'])
    sm = err.split('Summary:')[-1] if 'Summary:' in err else ''
    mi = re.search(r'I:\s+(-?[\d.]+)\s+LUFS', sm)
    mp = re.search(r'True peak:\s+Peak:\s+(-?[\d.]+)\s+dBFS', sm) or re.search(r'Peak:\s+(-?[\d.]+)\s+dBFS', sm)
    rc2, _, err2 = chay_ff(['ffmpeg', '-nostats', '-hide_banner', '-t', '0.5', '-i', str(path), '-vn', '-af', 'volumedetect', '-f', 'null', '-'])
    md = re.search(r'mean_volume:\s+(-?[\d.]+|-inf)\s+dB', err2)
    return {'lufs': float(mi.group(1)) if mi else None, 'dinh_that': float(mp.group(1)) if mp else None,
            'dau_mean': (float(md.group(1)) if md and md.group(1) != '-inf' else (-99.0 if md else None))}


def do_luma(path):
    rc, out, err = chay_ff(['ffmpeg', '-v', 'error', '-i', str(path), '-an', '-vf', 'fps=2,scale=96:170,format=gray', '-f', 'rawvideo', '-'])
    if rc != 0:
        raise RuntimeError('ffmpeg luma loi: ' + err[-200:])
    n = 96 * 170
    return [sum(out[i * n:(i + 1) * n]) / n for i in range(len(out) // n)]


# ---------- cac phep thuan (kiem duoc khong can video) ----------
def k1(probe, kich_thuoc, w=1080, h=1920):
    vs = [s for s in probe['streams'] if s.get('codec_type') == 'video']
    au = [s for s in probe['streams'] if s.get('codec_type') == 'audio']
    if not vs:
        return P('K1 dinh dang', False, 'khong co luong hinh')
    v = vs[0]
    dai = float(probe['format'].get('duration') or v.get('duration') or 0)
    fps = v.get('r_frame_rate', '0/1'); a, b = (fps.split('/') + ['1'])[:2]
    fps_v = float(a) / float(b) if float(b) else 0
    loi = []
    if (v.get('width'), v.get('height')) != (w, h): loi.append(f'kich co {v.get("width")}x{v.get("height")}')
    if abs(fps_v - 30) > 0.01: loi.append(f'fps {fps_v}')
    if v.get('codec_name') != 'h264': loi.append(f'codec {v.get("codec_name")}')
    if v.get('pix_fmt') != 'yuv420p': loi.append(f'pix_fmt {v.get("pix_fmt")}')
    if not 10 <= dai <= 15: loi.append(f'dai {dai:.2f}s')
    if kich_thuoc > 100 * 1024 * 1024: loi.append(f'{kich_thuoc} byte > 100 MB')
    if not au: loi.append('khong co luong am')
    else:
        if au[0].get('codec_name') != 'aac': loi.append(f'am {au[0].get("codec_name")}')
        if str(au[0].get('sample_rate')) != '48000': loi.append(f'am {au[0].get("sample_rate")} Hz')
    return P('K1 dinh dang', not loi, '; '.join(loi) or f'{w}x{h} {fps_v:g}fps h264 yuv420p {dai:.2f}s aac 48k {kich_thuoc // 1024} KB')


def k2(am):
    loi = []
    if am['lufs'] is None or abs(am['lufs'] + 14) > 1.5: loi.append(f'tich hop {am["lufs"]} LUFS (can -14 ± 1,5)')
    if am['dinh_that'] is None or am['dinh_that'] > -1.0: loi.append(f'dinh that {am["dinh_that"]} dBTP (can ≤ -1,0)')
    if am['dau_mean'] is None or am['dau_mean'] <= -35: loi.append(f'0-0,5 s mean {am["dau_mean"]} dB (can > -35)')
    return P('K2 am thanh', not loi, '; '.join(loi) or f'{am["lufs"]} LUFS, dinh {am["dinh_that"]} dBTP, 0-0,5s {am["dau_mean"]} dB')


def k3(lumas):
    thap = [round(x, 1) for x in lumas if x < 12]
    return P('K3 khung toi', lumas and not thap, f'{len(thap)}/{len(lumas)} khung luma<12 {thap[:5]}' if thap or not lumas else f'{len(lumas)} khung, luma TB min {min(lumas):.1f}')


def hien(mau, nguong=0.5):
    return [(m['t'], e) for m in mau for e in m['phan_tu'] if e['op'] >= nguong]


def k4(do, vung=AN_TOAN, w=1080, h=1920, ten='K4 vung an toan'):
    x0, y0, x1, y1 = vung
    loi = []
    for t, e in hien(do['mau']):
        if e['x0'] < x0 or e['x1'] > x1 or e['y0'] < y0 or e['y1'] > y1:
            loi.append(f't={t} {e["id"] or e["lop"]} "{e["chu"][:24]}" [{e["x0"]:.0f},{e["y0"]:.0f},{e["x1"]:.0f},{e["y1"]:.0f}]')
        if e['x0'] < 0 or e['x1'] > w or e['y0'] < 0 or e['y1'] > h:
            loi.append(f't={t} NGOAI KHUNG {e["id"]}')
    return P(ten, not loi, '; '.join(loi[:6]) + (f' (+{len(loi) - 6})' if len(loi) > 6 else '') or f'{len(hien(do["mau"]))} chu trong {vung}')


def k5(do, ten='K5 tran chu'):
    loi = []
    for t, e in hien(do['mau']):
        if e['cw'] > 0 and e['sw'] > e['cw'] + 1:
            loi.append(f't={t} {e["id"] or e["lop"]} "{e["chu"][:24]}" scrollWidth={e["sw"]} > clientWidth={e["cw"]}')
    return P(ten, not loi, '; '.join(loi[:6]) or 'khong tran')


def k6(do, ten='K6 khong de nhau', ngoai_le=()):
    loi = []
    for m in do['mau']:
        es = [e for e in m['phan_tu'] if e['op'] >= 0.5]
        for i in range(len(es)):
            for j in range(i + 1, len(es)):
                a, b = es[i], es[j]
                if a['id'] and a['id'] == b['id']:      # hai doan chu lien nhau cung mot dong (vd chu + <span>)
                    continue
                if (a['id'], b['id']) in ngoai_le or (b['id'], a['id']) in ngoai_le:
                    continue
                dx = min(a['x1'], b['x1']) - max(a['x0'], b['x0']); dy = min(a['y1'], b['y1']) - max(a['y0'], b['y0'])
                if dx > 0 and dy > 0 and dx * dy > 4:
                    loi.append(f't={m["t"]} "{a["chu"][:16]}"({a["id"]}) x "{b["chu"][:16]}"({b["id"]}) {dx * dy:.0f}px2')
    return P(ten, not loi, '; '.join(loi[:6]) or 'khong cap nao giao nhau')


def _chu_so(dl, ra):
    for k, v in dl.items():
        if k in ('ngay', 'kenh', '__ts'):
            continue
        if isinstance(v, str):
            if not v.lower().endswith(DUOI_ANH):
                ra.update(TOKEN.findall(v))
        elif isinstance(v, bool):
            pass
        elif isinstance(v, int):
            ra.add(str(v))
            if v >= 1000:
                ra.add(vnd(v)[:-1])
                if v % 1000 == 0:
                    ra.add(str(v // 1000))
        elif isinstance(v, list):
            for x in v:
                _chu_so({'x': x}, ra)
        elif isinstance(v, dict):
            _chu_so(v, ra)


def tap_so(dl):
    """Tap token so duoc phep trong chu DOM, sinh tu dl (so tien, %, gio, so dong...)."""
    ra = set()
    _chu_so(dl, ra)
    for k in ('vung', 'game', 'the'):
        v = dl.get(k)
        if isinstance(v, list):
            ra.add(str(len(v)))
    th = (dl.get('the') or {}).get('the') if isinstance(dl.get('the'), dict) else None
    if isinstance(th, list):
        ra.add(str(sum(int(x.get('so_luong', 0)) for x in th)))      # "mua N the" = tong so tam
    return ra


def k7(do, dl, ten='K7 so dung'):
    ok = tap_so(dl)
    loi = []
    for t, e in hien(do['mau'], 0.05):
        if DEM.match(e['id'] or ''):
            continue
        for tk in TOKEN.findall(e['chu']):
            if tk not in ok:
                loi.append(f't={t} so la "{tk}" trong "{e["chu"][:30]}" ({e["id"]})')
    kenh = dl['kenh']
    by_t = {m['t']: m['phan_tu'] for m in do['mau']}
    def chu(t, id_):
        return next((e['chu'] for e in by_t.get(t, []) if e['id'] == id_), None)
    def dong(t):
        d = {}
        for e in by_t.get(t, []):
            if DEM.match(e['id'] or ''):
                d[e['id']] = e['chu']
        return d
    if kenh == 'fb':
        if chu(0, 'dau-gia') != vnd(dl['gia_vnd']): loi.append(f'gia dau t=0 = {chu(0, "dau-gia")!r}, can {vnd(dl["gia_vnd"])}')
        d = dong(4.6); can = [vnd(r['vnd']) for r in dl['vung']]
        got = [d.get(f's{i}') for i in range(len(d))]
        if got != can: loi.append(f'cac dong store t=4.6 {got} != {can}')
        if chu(8.6, 'bang') != '= ' + vnd(dl['gia_vnd']): loi.append(f'"= gia" t=8.6 = {chu(8.6, "bang")!r}')
    elif kenh == 'ig':
        d = dong(5.6); can = [vnd(g['gia_vnd']) for g in dl['game']]
        got = [d.get(f'gs{i}') for i in range(len(d))]
        if got != can: loi.append(f'cac dong game t=5.6 {got} != {can}')
        if chu(8.6, 'tem-gia') != vk(dl['game'][-1]['gia_vnd']): loi.append(f'tem gia t=8.6 = {chu(8.6, "tem-gia")!r}')
    else:
        gs = sorted(e['chu'] for e in by_t.get(0, []) if e['lop'] == 'g')
        can = sorted([vk(dl['a']['gia_vnd']), vk(dl['b']['gia_vnd'])])
        if gs != can: loi.append(f'gia hai ben {gs} != {can}')
    return P(ten, not loi, '; '.join(loi[:6]) or 'moi so thuoc tap so cua dl; gia/so dong khop')


def k8(do, dl):
    kenh = dl['kenh']
    ids = ['dau-gia'] if kenh == 'fb' else ['d1', 'd2', 'd3']
    m0 = next((m for m in do['mau'] if m['t'] == 0), None)
    loi = []
    for i in ids:
        e = next((e for e in (m0['phan_tu'] if m0 else []) if e['id'] == i), None)
        if e is None or e['op'] < 0.99:
            loi.append(f'{i} t=0 op={e and e["op"]}')
    return P('K8 khung 0', not loi, '; '.join(loi) or f'{",".join(ids)} hien ro o t=0')


def kich_anh(path, w, h, toi_da, ten):
    p = pathlib.Path(path)
    if not p.exists():
        return P(ten, False, f'thieu {p.name}')
    try:
        pr = ffprobe(p)
        s = pr['streams'][0]
    except Exception as e:  # noqa: BLE001
        return P(ten, False, str(e))
    sz = p.stat().st_size
    loi = []
    if (s.get('width'), s.get('height')) != (w, h): loi.append(f'{s.get("width")}x{s.get("height")}')
    if sz > toi_da: loi.append(f'{sz} byte > {toi_da}')
    return P(ten, not loi, '; '.join(loi) or f'{w}x{h} {sz // 1024} KB')


def kiem(kenh, ra, dl):
    ra = pathlib.Path(ra)
    phep = []
    dop = ra / 'do.json'
    do = json.load(open(dop, encoding='utf-8')) if dop.exists() else None
    if kenh in ('fb', 'ig'):
        v = ra / 'video.mp4'
        if not v.exists():
            phep += [P('K1 dinh dang', False, 'thieu video.mp4'), P('K2 am thanh', False, 'thieu video.mp4'), P('K3 khung toi', False, 'thieu video.mp4')]
        else:
            try:
                phep.append(k1(ffprobe(v), v.stat().st_size))
                phep.append(k2(do_am(v)))
                phep.append(k3(do_luma(v)))
            except Exception as e:  # noqa: BLE001
                phep.append(P('K1-K3 video', False, str(e)))
        if do is None:
            phep += [P(n, False, 'thieu do.json') for n in ('K4 vung an toan', 'K5 tran chu', 'K6 khong de nhau', 'K7 so dung', 'K8 khung 0')]
        else:
            phep += [k4(do), k5(do), k6(do), k7(do, dl), k8(do, dl)]
        phep.append(kich_anh(ra / 'bia.jpg', 1080, 1920, 10 * 1024 * 1024, 'K9 bia.jpg'))
    else:
        phep.append(kich_anh(ra / 'anh.png', 1080, 1350, 8 * 1024 * 1024, 'T1 anh.png'))
        if do is None:
            phep += [P(n, False, 'thieu do.json') for n in ('T2 vung/tran/de', 'T3 so dung')]
        else:
            a, b, c = k4(do, AN_TOAN_TH, 1080, 1350), k5(do), k6(do)
            ok = a['dat'] and b['dat'] and c['dat']
            phep.append(P('T2 vung/tran/de', ok, ' | '.join(f'{x["ten"][:2]}: {x["chi_tiet"]}' for x in (a, b, c) if not x['dat']) or 'trong vung, khong tran, khong de'))
            x = k7(do, dl, 'T3 so dung'); phep.append(x)
    return {'dat': all(p['dat'] for p in phep), 'phep': phep}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--kenh', required=True, choices=list(KHUNG))
    ap.add_argument('--ra', required=True)
    ap.add_argument('--du-lieu', required=True)
    a = ap.parse_args(argv)
    kq = kiem(a.kenh, a.ra, json.load(open(a.du_lieu, encoding='utf-8')))
    print(json.dumps(kq, ensure_ascii=False, indent=1))
    return 0 if kq['dat'] else 1


if __name__ == '__main__':
    sys.exit(main())
