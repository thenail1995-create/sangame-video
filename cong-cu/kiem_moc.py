# Kiem MOC CHU DAU MOI DOAN (sau can-chu.py, truoc moi buoc dung hinh/tieng) - khong can hinh, chay vai giay.
#   python3 kiem_moc.py <moc-chu.json> <giong.mp3|.wav> [--ws0 ws0.json] [--ra ket-qua.json] [--tran 1.0]
#   python3 kiem_moc.py ghi-tu-sua <ra.json> --lan-dau f1.json [--cuoi f2.json] --cach-dau X --cach-cuoi Y --da-sua 0|1 [--ghi-chu "..."]
# CHI BAT LECH LON (loi that da gap: Keo 13/10 lech ~8 s, Top 5 12/10 lech 1,5 s). Moc nho hon `tran` (1,0 s) so voi giong la CHAP NHAN (Top 5 13/10 neo_doan som 0,3-0,85 s da dat moi kiem + kiem-video).
# Voi MOI doan (khoa `doan` trong moc-chu.json) LECH khi moc chu DAU doan:
#   (a) cach diem BAT DAU NOI gan nhat (khung giong dau tien sau lang >= 120 ms, hoac dau file) > `tran`, HOAC
#   (b) co ws0.json (Whisper KHONG goi y, can-chu.py ghi) va tu dau doan Whisper nghe duoc (khop chuan hoa, bo so) cach moc > `tran`.
#       Neo thieu / nhap nhang (nhieu cho cung diem khop) = KHONG KIEM DUOC (khong tinh truot, khong tinh dat).
#       Whisper hay keo som dau tu vao quang lang truoc do: moc nam SAU ws0, khoang giua gan nhu toan lang => DAT (ws0_keo_som); co tieng noi o giua => LECH.
#   `co_giong` (moc co >= 5 khung giong trong 0,3 s sau) chi de THAM KHAO, khong con la dieu kien truot.
# Ma thoat: 0 dat · 5 co doan lech · 2 sai dau vao.
import json, re, subprocess, sys, unicodedata, pathlib
import numpy as np

HOP = 160                 # 10 ms o 16 kHz
SO_CHU = {'mot', 'hai', 'ba', 'bon', 'nam', 'sau', 'bay', 'tam', 'chin', 'muoi', 'tram', 'nghin', 'ngan', 'le', 'linh', 'trieu', 'lam', 'tu', 'nhat', 'muoi'}


def doc_giong(path):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True, check=True)
    return np.frombuffer(p.stdout, dtype=np.float32)


def nang_luong_db(x):
    n = len(x) // HOP
    return 20 * np.log10(np.sqrt(np.mean(x[:n * HOP].reshape(n, HOP) ** 2, axis=1)) + 1e-9)


def _chuan(t):
    t = ''.join(c for c in unicodedata.normalize('NFD', t.lower()) if unicodedata.category(c) != 'Mn').replace('đ', 'd')
    return re.sub(r'[^a-z0-9]', '', t)


def _bo_chop(v, toi_thieu):
    v = v.copy(); k = 0; n = len(v)
    while k < n:
        if v[k]:
            j = k
            while j < n and v[j]: j += 1
            if j - k < toi_thieu: v[k:j] = False
            k = j
        else: k += 1
    return v


def diem_bat_dau_noi(v, lang_min=12):
    """-> [giay]: khung dau cua moi cum giong (sau lang >= lang_min khung, hoac dau file), cum phai >= 5/8 khung co giong."""
    ons = []; n = len(v); k = 0
    while k < n:
        if v[k] and (k == 0 or not v[k - 1]):
            j = k - 1
            while j >= 0 and not v[j]: j -= 1
            lang = k - 1 - j                          # so khung lang ngay truoc (j = -1 => het dau file)
            if (j < 0 or lang >= lang_min) and v[k:k + 8].sum() >= 5: ons.append(k * 0.01)
        k += 1
    return ons


def _doan(moc):
    ds = []
    for g in moc:
        if not ds or ds[-1][0] != g['doan']: ds.append((g['doan'], []))
        ds[-1][1].append(g)
    return ds


def _neo_ws0(ws, ws0):
    """-> (tu_giay | None, ly_do_khong_kiem). Neo = tu khong-so dau doan; chon cho Whisper nghe co nhieu tu ke tiep khop nhat; hoa => nhap nhang."""
    khoa = [t for t in (_chuan(g['w']) for g in ws[:6]) if t and not t.isdigit() and t not in SO_CHU]
    if not khoa: return None, 'doan toan so/khong co tu de neo'
    wsn = [(_chuan(w[0]), w[1]) for w in ws0]
    ung = [j for j in range(len(wsn)) if wsn[j][0] == khoa[0]]
    if not ung: return None, f'Whisper khong nghe thay tu dau «{khoa[0]}»'
    diem = lambda j: sum(c in {x[0] for x in wsn[j + 1:j + 8]} for c in khoa[1:4])
    sc = [(diem(j), j) for j in ung]; best = max(s for s, _ in sc); tot = [j for s, j in sc if s == best]
    if len(tot) > 1: return None, f'nhap nhang: {len(tot)} cho khop «{khoa[0]}» ngang diem'
    if len(khoa) > 1 and best == 0 and len(ung) > 1: return None, 'khong khop tu ke tiep'
    return wsn[tot[0]][1], ''


def _keo_som(v, tw, t0):
    """True neu moc t0 nam SAU tw (ws0) va khoang [tw, t0-0,05 s] (gan nhu) toan lang: Whisper keo som dau tu vao quang lang."""
    a, b = int(tw * 100), int((t0 - 0.05) * 100)
    return t0 > tw and b > a and float(v[a:b].mean()) <= 0.1


def kiem(moc, db, ws0=None, tran=1.0, cua_so=0.3, toi_thieu_giong=5):
    nen = float(np.percentile(db, 50)); n = len(db)
    v = _bo_chop(db >= nen - 16, 4); ons = diem_bat_dau_noi(v)
    out = []
    for dk, ws in _doan(moc):
        t0 = float(ws[0]['s']); loi = []; r = dict(doan=dk, moc=round(t0, 2))
        a = int(round(t0 * 100)); r['co_giong'] = bool(a < n and v[a:a + int(cua_so * 100)].sum() >= toi_thieu_giong)
        if ons:
            o = min(ons, key=lambda o: abs(o - t0)); r['bat_dau_noi_gan'] = round(o, 2); r['lech_bat_dau'] = round(abs(o - t0), 2)
            if r['lech_bat_dau'] > tran: loi.append(f'cach diem bat dau noi gan nhat ({o:.2f}s) {r["lech_bat_dau"]:.2f}s > {tran}s')
        else: r['bat_dau_noi_gan'] = r['lech_bat_dau'] = None
        if ws0 is None:
            r['ws0'] = 'khong_co_ws0'; r['lech_ws0'] = None
        else:
            tw, ly = _neo_ws0(ws, ws0)
            if tw is None: r['ws0'] = 'khong_kiem_duoc'; r['lech_ws0'] = None; r['ly_do_ws0'] = ly
            else:
                r['lech_ws0'] = round(abs(tw - t0), 2); r['ws0'] = 'dat' if r['lech_ws0'] <= tran else 'lech'
                # Whisper hay KEO moc dau tu SOM vao quang lang truoc do (top5 13/10: «Còn» 27,68 trong khi giong that bat dau 28,53): moc nam SAU ws0 va khoang giua
                # (gan nhu) toan lang = Whisper keo som, KHONG phai moc lech. Neu giua co tieng noi (Taxi Life cu: ws0 8,5 s, moc 19,1 s) thi van la lech.
                if r['ws0'] == 'lech' and _keo_som(v, tw, t0):
                    r['ws0'] = 'dat'; r['ws0_keo_som'] = True
                if r['ws0'] == 'lech': loi.append(f'Whisper nghe dau doan o {tw:.2f}s, lech {r["lech_ws0"]:.2f}s > {tran}s')
        r['trang_thai'] = 'lech' if loi else 'dat'; r['loi'] = loi; out.append(r)
    so_lech = sum(1 for r in out if r['trang_thai'] == 'lech')
    return dict(ket_qua='lech' if so_lech else 'dat', so_doan=len(out), so_lech=so_lech, tran=tran, nen_db=round(nen, 1), lech_tung_doan=out)


def in_bang(kq):
    print(f"KIEM MOC: {kq['so_doan']} doan, {kq['so_lech']} lech (tran {kq['tran']} s)")
    for r in kq['lech_tung_doan']:
        f = lambda x: '  -  ' if x is None else f'{x:5.2f}'
        print(f"  {r['doan']:6s} moc {r['moc']:6.2f}  giong {'co ' if r['co_giong'] else 'KHONG'}  bat dau noi {f(r['bat_dau_noi_gan'])} (lech {f(r['lech_bat_dau'])})  "
              f"ws0 {r['ws0']:16s} (lech {f(r['lech_ws0'])})  {'DAT' if r['trang_thai'] == 'dat' else 'LECH: ' + '; '.join(r['loi'])}"
              + (f"  [{r['ly_do_ws0']}]" if r.get('ly_do_ws0') else ''))


def ghi_tu_sua(ra, lan_dau, cuoi, cach_dau, cach_cuoi, da_sua, ghi_chu=''):
    """kiem/tu-sua.json (vao manifest.tu_sua): lan_dau = ket qua kiem_moc LAN 1 (do ty le 'dat lan dau'), cach_cuoi, lech_tung_doan (lan 1)."""
    ld = json.load(open(lan_dau)); cu = json.load(open(cuoi)) if cuoi else ld
    d = dict(phien_ban=1, lan_dau=dict(ket_qua=ld['ket_qua'], so_doan=ld['so_doan'], so_lech=ld['so_lech']), cach_dau=cach_dau, cach_cuoi=cach_cuoi, da_sua=bool(da_sua),
             ket_qua_cuoi=cu['ket_qua'], lech_tung_doan=[r for r in ld['lech_tung_doan'] if r['trang_thai'] == 'lech'],
             lech_sau_sua=[r for r in cu['lech_tung_doan'] if r['trang_thai'] == 'lech'] if cuoi else [], ghi_chu=ghi_chu)
    pathlib.Path(ra).parent.mkdir(parents=True, exist_ok=True)
    json.dump(d, open(ra, 'w'), ensure_ascii=False, indent=1)
    return d


def _arg(a, ten, mac_dinh=None):
    if ten in a:
        i = a.index(ten); v = a[i + 1]; del a[i:i + 2]; return v
    return mac_dinh


def main(argv):
    a = list(argv)
    if a and a[0] == 'ghi-tu-sua':
        a = a[1:]; lan_dau = _arg(a, '--lan-dau'); cuoi = _arg(a, '--cuoi'); cd = _arg(a, '--cach-dau', ''); cc = _arg(a, '--cach-cuoi', ''); ds = _arg(a, '--da-sua', '0'); gc = _arg(a, '--ghi-chu', '')
        if len(a) != 1 or not lan_dau: print('cach dung: kiem_moc.py ghi-tu-sua <ra.json> --lan-dau f1.json ...'); return 2
        d = ghi_tu_sua(a[0], lan_dau, cuoi, cd, cc, ds == '1', gc); print(f"TU SUA: lan dau {d['lan_dau']['ket_qua']} ({d['lan_dau']['so_lech']} doan lech), cach {cd or '?'} -> {cc or '?'}, da_sua={d['da_sua']}, cuoi {d['ket_qua_cuoi']}"); return 0
    ws0p = _arg(a, '--ws0'); ra = _arg(a, '--ra'); tran = float(_arg(a, '--tran', '1.0'))
    if len(a) != 2: print('cach dung: kiem_moc.py <moc-chu.json> <giong> [--ws0 ws0.json] [--ra ket-qua.json] [--tran 1.0]'); return 2
    try:
        moc = json.load(open(a[0])); x = doc_giong(a[1])
        ws0 = json.load(open(ws0p)) if ws0p and pathlib.Path(ws0p).exists() else None
    except (OSError, ValueError, subprocess.CalledProcessError) as e:
        print('KIEM MOC: sai dau vao:', e); return 2
    if not moc or len(x) < 16000: print('KIEM MOC: moc-chu rong / giong qua ngan'); return 2
    kq = kiem(moc, nang_luong_db(x), ws0, tran); in_bang(kq)
    if ra: pathlib.Path(ra).parent.mkdir(parents=True, exist_ok=True); json.dump(kq, open(ra, 'w'), ensure_ascii=False, indent=1)
    return 5 if kq['ket_qua'] == 'lech' else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
