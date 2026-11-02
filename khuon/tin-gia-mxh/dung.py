#!/usr/bin/env python3
"""Dung tin gia cho Facebook / Instagram / Threads (Sang Game) tu dl.json — KE-HOACH muc 2-3.

  python3 khuon/tin-gia-mxh/dung.py --kenh fb|ig|threads --du-lieu dl.json --tai-san DIR --am DIR_SFX --nhac FILE.mp3 --ra OUT [--bo-video]

fb/ig  -> OUT/video.mp4 (1080x1920 30fps 11 s, nhac + tieng dong), OUT/bia.jpg, OUT/do.json
threads-> OUT/anh.png (1080x1350), OUT/do.json
--bo-video: chi do bo cuc (do.json), khong chup video/am (nhanh; dung cho test nhieu bien the).
Thoat != 0 khi dl sai hop dong, thieu tep, hoac capture/do/ffmpeg loi.
"""
import argparse, json, os, pathlib, re, shutil, subprocess, sys, tempfile

QUY = pathlib.Path(__file__).resolve().parent
KHUON = QUY.parent
REPO = KHUON.parent
CAP = pathlib.Path(os.environ.get('CAPTURE_MJS') or REPO / 'cong-cu' / 'capture.mjs')
DAI = 11.0
FPS = 30
MOC_DO = {'fb': [0, 0.3, 1.6, 3.0, 4.6, 5.6, 7.0, 8.6, 10.7], 'ig': [0, 0.3, 1.6, 3.0, 4.6, 5.6, 7.0, 8.6, 10.7], 'threads': [0]}
KICH = {'fb': (1080, 1920), 'ig': (1080, 1920), 'threads': (1080, 1350)}
# bang tieng dong (do tu am-phac.py): ten -> (tep, cat tu, cat den, giay "diem cham" trong tep, dB)
KIT = {'dap': ('dong-dau', 0, .32, .006, -4), 'dau': ('dau-nhe', .596, .8, .006, -6), 'vut': ('giay-vut', .05, .76, .445, -10),
       'lat': ('lat-trang', .10, .95, .362, -7), 'dem': ('dem-so', .04, .99, .008, -12), 'kaching': ('ka-ching', 0, .95, .015, -7),
       'go': ('danh-may', .030, .095, .004, -9), 'chuong': ('chuong-ket', 0, 1.48, 0, -8)}


class Loi(Exception):
    pass


def kiem_dl(dl):
    """Hop dong dl.json (muc 2). Nem Loi neu sai."""
    kenh = dl.get('kenh')
    if kenh not in KICH:
        raise Loi(f'kenh khong hop le: {kenh!r}')
    def can(o, *ks, ten='dl'):
        for k in ks:
            if k not in o or o[k] in (None, '', []):
                raise Loi(f'{ten} thieu "{k}"')
    def tien(v, ten):
        if not isinstance(v, int) or isinstance(v, bool) or v <= 0:
            raise Loi(f'{ten} phai la so nguyen VND duong: {v!r}')
    if kenh == 'fb':
        can(dl, 'ten', 'bia', 'nen', 'gia_vnd', 'vung', 'the', 'goc', 'giam', 'han_chu')
        tien(dl['gia_vnd'], 'gia_vnd')
        v = dl['vung']
        if not 3 <= len(v) <= 5:
            raise Loi(f'vung phai 3-5 dong (co {len(v)})')
        for r in v:
            can(r, 'ma', 'ten', 'vnd', ten='vung[]'); tien(r['vnd'], 'vung[].vnd')
        if any(v[i]['vnd'] < v[i + 1]['vnd'] for i in range(len(v) - 1)):
            raise Loi('vung phai xep GIAM dan theo vnd (re nhat o cuoi)')
        if v[-1]['vnd'] != dl['gia_vnd']:
            raise Loi('vung[-1].vnd (store re nhat) phai bang gia_vnd')
        can(dl['the'], 'ma', 'ten_vung', 'the', 'gia_game', 'du', ten='the')
        for k in dl['the']['the']:
            can(k, 'menh_gia', 'so_luong', ten='the.the[]')
        if len(dl['the']['the']) > 3:
            raise Loi('the.the toi da 3 loai the')
        if dl.get('re_hon'):
            can(dl['re_hon'], 'ten', 'vnd', ten='re_hon'); tien(dl['re_hon']['vnd'], 're_hon.vnd')
        for r in v:
            if not (QUY / 'co' / (str(r['ma']).lower() + '.svg')).exists():
                raise Loi(f'thieu co/{str(r["ma"]).lower()}.svg')
        if not (QUY / 'co' / (str(dl['the']['ma']).lower() + '.svg')).exists():
            raise Loi(f'thieu co/{str(dl["the"]["ma"]).lower()}.svg')
    elif kenh == 'ig':
        can(dl, 'tieu_de', 'game', 'han_chu')
        if not (isinstance(dl['tieu_de'], list) and len(dl['tieu_de']) == 3 and all(isinstance(x, str) and x for x in dl['tieu_de'])):
            raise Loi('tieu_de phai la 3 chuoi')
        g = dl['game']
        if not 3 <= len(g) <= 5:
            raise Loi(f'game phai 3-5 (co {len(g)})')
        for x in g:
            can(x, 'ten', 'bia', 'nen', 'gia_vnd', ten='game[]'); tien(x['gia_vnd'], 'game[].gia_vnd')
        if any(g[i]['gia_vnd'] < g[i + 1]['gia_vnd'] for i in range(len(g) - 1)):
            raise Loi('game phai xep GIAM dan theo gia_vnd (re nhat o cuoi)')
        if not dl.get('vung_chung'):
            for x in g:
                if not (x.get('ma_vung') and (QUY / 'co' / (str(x['ma_vung']).lower() + '.svg')).exists()):
                    raise Loi('vung_chung rong thi moi game can ma_vung co co/<ma>.svg')
    else:
        can(dl, 'cau_hoi', 'a', 'b', 'chan')
        if not (isinstance(dl['cau_hoi'], list) and len(dl['cau_hoi']) == 2):
            raise Loi('cau_hoi phai la 2 dong')
        for k in 'ab':
            can(dl[k], 'ten', 'bia', 'nen', 'gia_vnd', 'sao', 'luot', ten=k); tien(dl[k]['gia_vnd'], k + '.gia_vnd')


def tep_anh(dl):
    """Danh sach duong dan anh (tuong doi --tai-san) ma dl dung."""
    ds = []
    def them(x):
        if isinstance(x, str) and x:
            ds.append(x)
        elif isinstance(x, list):
            for y in x:
                them(y)
    k = dl['kenh']
    if k == 'fb':
        them(dl['bia']); them(dl['nen'])
    elif k == 'ig':
        for g in dl['game']:
            them(g['bia']); them(g['nen'])
    else:
        for s in 'ab':
            them(dl[s]['bia']); them(dl[s]['nen'])
    return list(dict.fromkeys(ds))


def chay(lenh, **kw):
    r = subprocess.run(lenh, **kw)
    if r.returncode != 0:
        raise Loi(f'lenh loi ({r.returncode}): ' + ' '.join(map(str, lenh[:3])))
    return r


def cue(kenh, dl):
    """Danh sach (ten tieng dong, giay) theo mon thoi gian cua khuon."""
    if kenh == 'fb':
        n = len(dl['vung']); d = 1.0 if n == 3 else .5; s0 = 3.5 - d * (n - 1)
        return [('dap', 0.0), ('vut', 1.0), ('dem', s0), ('dem', s0 + 2 * d), ('dap', 4.0), ('vut', 5.0), ('lat', 6.5), ('kaching', 7.1),
                ('vut', 9.4), ('chuong', 9.65)]
    n = len(dl['game'])
    return [('dap', 0.0), ('vut', 1.0)] + [('dau', 1.5 + .5 * i) for i in range(n)] + [('dap', 1.5 + .5 * n + .3), ('vut', 6.0),
            ('kaching', 8.0), ('vut', 9.4), ('chuong', 9.65)]


def am(kenh, dl, dir_sfx, nhac, ra_wav, tam):
    ins = ['-i', str(nhac)]
    f = [f'[0:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:{DAI},asetpts=PTS-STARTPTS,volume=-3dB,apad=whole_dur={DAI}[m]']
    lab = ['[m]']
    for i, (k, t) in enumerate(cue(kenh, dl)):
        fn, a, b, hit, g = KIT[k]
        p = pathlib.Path(dir_sfx) / (fn + '.mp3')
        if not p.exists():
            raise Loi(f'thieu tieng dong {p}')
        ins += ['-i', str(p)]
        dms = max(0, int((t - hit) * 1000))
        f.append(f'[{i + 1}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim={a}:{b},asetpts=PTS-STARTPTS,volume={g}dB,adelay={dms}|{dms},apad=whole_dur={DAI}[s{i}]')
        lab.append(f'[s{i}]')
    tron = ';'.join(f) + ';' + ''.join(lab) + f'amix=inputs={len(lab)}:duration=longest,atrim=0:{DAI},afade=t=out:st={DAI - .7}:d=0.7'
    # loudnorm 2 luot (do roi ap tuyen tinh) de ra dung -14 LUFS, dinh that <= -1,5 dBTP
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-y', *ins, '-filter_complex', tron + ',loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json[o]',
                        '-map', '[o]', '-f', 'null', '-'], capture_output=True, text=True)
    if r.returncode != 0:
        raise Loi('ffmpeg am luot 1 loi: ' + r.stderr[-400:])
    m = re.search(r'\{[^{}]*"input_i"[^{}]*\}', r.stderr, re.S)
    if not m:
        raise Loi('khong doc duoc do loudnorm')
    j = json.loads(m.group(0))
    ln = (f'loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j["input_i"]}:measured_TP={j["input_tp"]}:measured_LRA={j["input_lra"]}'
          f':measured_thresh={j["input_thresh"]}:offset={j["target_offset"]}:linear=true')
    # 02/11 (Opus): IG chay that ra dinh that -0,5 dBTP (K2 truot) - loudnorm linear khong chan duoc dinh khi phai tang gain, AAC con day dinh them
    # -> them alimiter tran -2,5 dBFS (lay mau x4 de chan dinh giua mau) sau loudnorm
    lim = 'aresample=192000,alimiter=limit=0.75:attack=1:release=50:level=false,aresample=48000'
    chay(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', tron + ',' + ln + ',' + lim + '[o]', '-map', '[o]', '-ar', '48000', '-ac', '2', str(ra_wav)])


def dung(kenh, dl_path, tai_san, dir_sfx, nhac, ra, bo_video=False):
    dl = json.load(open(dl_path, encoding='utf-8'))
    kiem_dl(dl)
    if dl['kenh'] != kenh:
        raise Loi(f'--kenh {kenh} nhung dl.kenh={dl["kenh"]}')
    ra = pathlib.Path(ra); ra.mkdir(parents=True, exist_ok=True)
    ts = pathlib.Path(tai_san).resolve()
    if not bo_video:
        if not CAP.exists():
            raise Loi(f'khong thay capture.mjs: {CAP}')
        if kenh != 'threads' and not (nhac and pathlib.Path(nhac).exists()):
            raise Loi(f'thieu nhac {nhac}')
    w, h = KICH[kenh]
    with tempfile.TemporaryDirectory(prefix='tin-gia-mxh-') as tam:
        tam = pathlib.Path(tam)
        goc = tam / 'tin-gia-mxh'; goc.mkdir()
        (tam / 'flagship').mkdir()
        for f in ['BeVietnamPro-Medium.ttf', 'BeVietnamPro-SemiBold.ttf', 'BeVietnamPro-Bold.ttf', 'BeVietnamPro-ExtraBold.ttf', 'logo.svg']:
            shutil.copy(KHUON / 'flagship' / f, tam / 'flagship' / f)
        for f in [kenh + '.html', 'chung.css', 'dong.js']:
            shutil.copy(QUY / f, goc / f)
        shutil.copytree(QUY / 'co', goc / 'co')
        for rel in tep_anh(dl):
            p = (ts / rel).resolve()
            if '..' in pathlib.PurePosixPath(rel).parts or pathlib.PurePosixPath(rel).is_absolute() or ts not in p.parents or not p.is_file():
                raise Loi(f'anh khong hop le / thieu: {rel}')
            (goc / 'ts' / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(p, goc / 'ts' / rel)
        dl['__ts'] = 'ts/'
        (goc / 'du-lieu.js').write_text('window.DL=' + json.dumps(dl, ensure_ascii=False) + ';\n', encoding='utf-8')
        trang = goc / (kenh + '.html')
        chay(['node', str(QUY / 'do.mjs'), f'--trang={trang}', f'--root={tam}', f'--ra={ra / "do.json"}',
              '--t=' + ','.join(str(t) for t in MOC_DO[kenh]), f'--w={w}', f'--h={h}'])
        if bo_video:
            return
        if kenh == 'threads':
            chay(['node', str(CAP), str(trang), str(tam / 'anh'), '30', '1', str(w), str(h), '--stills=0', f'--root={tam}', '--quiet'])
            shutil.copy(tam / 'anh_0.00s.png', ra / 'anh.png')
            return
        hinh = tam / 'hinh.mp4'
        chay(['node', str(CAP), str(trang), str(hinh), str(FPS), str(int(DAI)), str(w), str(h), f'--root={tam}', '--workers=4', '--quiet'])
        chay(['node', str(CAP), str(trang), str(tam / 'bia'), '30', '1', str(w), str(h), '--stills=0.3', f'--root={tam}', '--quiet'])
        chay(['ffmpeg', '-v', 'error', '-y', '-i', str(tam / 'bia_0.30s.png'), '-q:v', '3', str(ra / 'bia.jpg')])
        wav = tam / 'am.wav'
        am(kenh, dl, dir_sfx, nhac, wav, tam)
        chay(['ffmpeg', '-v', 'error', '-y', '-i', str(hinh), '-i', str(wav), '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac',
              '-b:a', '192k', '-ar', '48000', '-ac', '2', '-t', str(DAI), '-movflags', '+faststart', str(ra / 'video.mp4')])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--kenh', required=True, choices=list(KICH))
    ap.add_argument('--du-lieu', required=True)
    ap.add_argument('--tai-san', required=True)
    ap.add_argument('--am')
    ap.add_argument('--nhac')
    ap.add_argument('--ra', required=True)
    ap.add_argument('--bo-video', action='store_true')
    a = ap.parse_args(argv)
    if not a.bo_video and a.kenh != 'threads' and not (a.am and a.nhac):
        ap.error('fb/ig can --am va --nhac')
    try:
        dung(a.kenh, a.du_lieu, a.tai_san, a.am, a.nhac, a.ra, a.bo_video)
    except Loi as e:
        print('LOI:', e, file=sys.stderr)
        return 1
    print('xong', a.kenh, a.ra)
    return 0


if __name__ == '__main__':
    sys.exit(main())
