#!/usr/bin/env python3
"""Kiem mot file video truoc khi giao (Reels/TikTok/Shorts) — chi doc, khong sua file.

Dung:  python3 kiem-video.py <video> [thu_muc_ket_qua] [--alpha]
In ra: thong so (codec, kich thuoc, fps, mau, faststart, am), loudness (EBU R128), khung den,
doan dung hinh (freezedetect), va tao contact sheet co moc gio + 3 khung full-size (dau/giua/cuoi).
Nhan: PASS / WARN / FAIL. WARN = kiem tra lai bang mat, khong phai loi chac chan.
"""
import json, math, os, re, subprocess, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(SKILL, 'fonts', 'BeVietnamPro-Regular.ttf')

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def mark(ok, warn=False):
    return 'PASS' if ok else ('WARN' if warn else 'FAIL')

def atoms_order(path):
    """Top-level MP4/MOV atoms in order (faststart = moov truoc mdat)."""
    order = []
    with open(path, 'rb') as f:
        while True:
            hdr = f.read(8)
            if len(hdr) < 8:
                break
            size = int.from_bytes(hdr[:4], 'big'); typ = hdr[4:8].decode('latin1')
            if size == 1:
                size = int.from_bytes(f.read(8), 'big'); skip = size - 16
            elif size == 0:
                order.append(typ); break
            else:
                skip = size - 8
            order.append(typ)
            if skip < 0:
                break
            f.seek(skip, 1)
    return order

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    alpha = '--alpha' in sys.argv
    if not args:
        print(__doc__); sys.exit(2)
    src = os.path.abspath(args[0])
    out = os.path.abspath(args[1]) if len(args) > 1 else os.path.splitext(src)[0] + '_kiem'
    os.makedirs(out, exist_ok=True)

    p = run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', src])
    if p.returncode:
        print('FAIL ffprobe:', p.stderr); sys.exit(1)
    info = json.loads(p.stdout)
    v = next((s for s in info['streams'] if s['codec_type'] == 'video'), None)
    a = next((s for s in info['streams'] if s['codec_type'] == 'audio'), None)
    dur = float(info['format'].get('duration', 0))
    rows = []
    if not v:
        print('FAIL khong co luong video'); sys.exit(1)
    def ratio(x):
        try:
            n_, d_ = (x or '0/1').split('/'); n_, d_ = float(n_), float(d_)
            return n_ / d_ if d_ else 0.0
        except ValueError:
            return 0.0
    fps = ratio(v.get('avg_frame_rate')) or ratio(v.get('r_frame_rate'))
    w, h = int(v['width']), int(v['height'])
    if alpha:
        rows.append(('INFO', f"codec video = {v['codec_name']} {v.get('profile','')} (che do --alpha: khong dung de dang mang xa hoi)"))
    else:
        rows.append((mark(v['codec_name'] in ('h264', 'hevc'), True), f"codec video = {v['codec_name']} {v.get('profile','')}"))
    rows.append((mark((w, h) == (1080, 1920), True), f'kich thuoc = {w}x{h} (Reels/TikTok chuan 1080x1920)'))
    rows.append((mark(23 <= fps <= 60), f'fps = {fps:g} (IG/TikTok 23–60, FB 24–60)'))
    pf = v.get('pix_fmt', '')
    if not alpha:
        rows.append((mark(pf == 'yuv420p', True), f'pix_fmt = {pf}'))
    else:  # kiem kenh trong suot THAT: giai ma 1 khung giua ra RGBA va do alpha nho nhat
        dec_a = ['-c:v', 'libvpx-vp9'] if v['codec_name'] == 'vp9' else []   # vp9 native decoder bo alpha
        ra = subprocess.run(['ffmpeg', '-v', 'error', *dec_a, '-ss', f'{dur / 2:.3f}', '-i', src, '-frames:v', '1',
                             '-vf', 'format=rgba,alphaextract,format=gray', '-f', 'rawvideo', '-'], capture_output=True)
        if ra.returncode or not ra.stdout:
            rows.append(('FAIL', f'khong giai ma duoc kenh alpha (pix_fmt={pf}): {ra.stderr.decode(errors="ignore")[:200]}'))
        else:
            amin, amax = min(ra.stdout), max(ra.stdout)
            rows.append((mark(amin < 255), f'alpha khung giua: min={amin} max={amax} (min<255 = co vung trong suot)'))
    tags = (v.get('color_space'), v.get('color_transfer'), v.get('color_primaries'), v.get('color_range'))
    rows.append((mark(tags[:3] == ('bt709',) * 3 and tags[3] == 'tv', True), f'mau space/trc/primaries/range = {tags}'))
    rows.append((mark(dur >= 3, True), f'thoi luong = {dur:.2f}s (IG/FB toi thieu 3s)'))
    br = int(info['format'].get('bit_rate', 0) or 0)
    rows.append((mark(br <= 25_000_000, True), f'bitrate tong = {br/1e6:.1f} Mbps (IG toi da 25)'))
    if src.lower().endswith(('.mp4', '.mov', '.m4v')):
        order = atoms_order(src)
        fs = 'moov' in order and 'mdat' in order and order.index('moov') < order.index('mdat')
        rows.append((mark(fs, True), f"faststart (moov truoc mdat) = {fs}  atoms={order[:6]}"))
    if a:
        rows.append((mark(a['codec_name'] == 'aac' and int(a.get('sample_rate', 0)) == 48000, True),
                     f"am = {a['codec_name']} {a.get('sample_rate')}Hz {a.get('channels')}ch {int(a.get('bit_rate', 0) or 0)//1000}kbps"))
    else:
        rows.append(('WARN', 'khong co luong am (vai app kho tinh; them anullsrc neu can)'))

    # loudness
    if a:
        r = run(['ffmpeg', '-nostats', '-i', src, '-af', 'ebur128=peak=true', '-f', 'null', '-'])
        if r.returncode:
            rows.append(('FAIL', f'do loudness loi: {r.stderr.strip()[-200:]}'))
        m_i = re.findall(r'I:\s+(-?[\d.]+) LUFS', r.stderr); m_tp = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r.stderr)
        m_lra = re.findall(r'LRA:\s+(-?[\d.]+) LU', r.stderr)
        if not m_i and not r.returncode:
            rows.append(('FAIL', 'khong doc duoc ket qua ebur128'))
        if m_i:
            I = float(m_i[-1]); TP = float(m_tp[-1]) if m_tp else None
            rows.append((mark(-17 <= I <= -13, True), f'loudness I = {I} LUFS (quy uoc -14..-16)'))
            if TP is not None:
                rows.append((mark(TP <= -1.0, True), f'true peak = {TP} dBTP (<= -1.0)'))
            if m_lra:
                rows.append(('INFO', f'LRA = {m_lra[-1]} LU'))

    # black + freeze
    r = run(['ffmpeg', '-nostats', '-i', src, '-vf', 'blackdetect=d=0.1:pix_th=0.10,freezedetect=n=-60dB:d=0.6', '-an', '-f', 'null', '-'])
    if r.returncode:
        rows.append(('FAIL', f'giai ma toan bo video loi (blackdetect/freezedetect): {r.stderr.strip()[-200:]}'))
    decoded_ok = not r.returncode
    blacks = re.findall(r'black_start:([\d.]+) black_end:([\d.]+)', r.stderr)
    fstart = re.findall(r'freeze_start: ([\d.]+)', r.stderr); fend = re.findall(r'freeze_end: ([\d.]+)', r.stderr)
    if decoded_ok:
        rows.append((mark(not blacks, True), f'khung den: {blacks or "khong"} (video alpha: vung trong suot cung bi tinh la den)'))
    freezes = list(zip(fstart, fend + [f'{dur:.2f}'] * (len(fstart) - len(fend))))
    frozen = sum(float(e) - float(s) for s, e in freezes)
    if decoded_ok:
        rows.append((mark(frozen <= max(1.0, dur / 30), True), f'dung hinh (>=0.6s): tong {frozen:.2f}s {freezes or ""} (giu logo/CTA co chu y thi chap nhan)'))

    # contact sheet (2 khung/giay, 8 cot) + 3 khung full-size
    cols = 8; n = max(1, math.ceil(dur * 2)); rows_t = math.ceil(n / cols)
    tw = 216 if h >= w else 384
    dt = (f"drawtext=fontfile='{FONT}':text='%{{pts\\:hms}} #%{{frame_num}}':fontsize=16:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=4:x=6:y=h-th-10,"
          if os.path.exists(FONT) else '')
    sheet = os.path.join(out, 'contact-sheet.png')
    rs = run(['ffmpeg', '-y', '-v', 'error', '-i', src, '-vf', f'fps=2,scale={tw}:-2,{dt}tile={cols}x{rows_t}:padding=4:margin=4', '-frames:v', '1', sheet])
    if rs.returncode or not os.path.exists(sheet):
        rows.append(('FAIL', f'khong tao duoc contact sheet: {rs.stderr.strip()[-200:]}'))
    fulls = []
    dec = ['-c:v', 'libvpx-vp9'] if alpha and src.endswith('.webm') else []
    for name, seek in (('dau', ['-ss', '0']), ('giua', ['-ss', f'{dur / 2:.3f}']), ('cuoi', ['-sseof', '-0.5'])):
        f = os.path.join(out, f'khung-{name}.png')
        extra = ['-update', '1'] if name == 'cuoi' else ['-frames:v', '1']   # 'cuoi': ghi de den khung cuoi cung
        if os.path.exists(f):
            os.remove(f)
        rf = run(['ffmpeg', '-y', '-v', 'error', *dec, *seek, '-i', src, *extra, f])
        if rf.returncode or not os.path.exists(f):
            rows.append(('FAIL', f'khong trich duoc khung {name}: {rf.stderr.strip()[-200:]}'))
        else:
            fulls.append(f)

    print(f'== kiem-video: {src}')
    for tag, msg in rows:
        print(f'[{tag}] {msg}')
    print(f'contact sheet: {sheet}')
    print('khung full-size (soi de/che mong, dau tieng Viet, vung an toan):', *fulls, sep='\n  ')
    fails = sum(1 for t, _ in rows if t == 'FAIL'); warns = sum(1 for t, _ in rows if t == 'WARN')
    print(f'== tong: {fails} FAIL, {warns} WARN. Contact sheet thu nho KHONG du de ket luan che mong — xem khung full-size.')
    sys.exit(1 if fails else 0)

if __name__ == '__main__':
    main()
