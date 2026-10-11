# Phep "giong trong video = giong da kiem" (D3 doi thiet ke 11/10/2026, Sol #10).
# Ly do: D3 cu cho Whisper nghe AM THANH MP4 CUOI (giong + nhac + tieng dong) -> nghe sai ten/so du loi dung (CI that 11/10 run 38106949664, Keo thom Returnal Digital Deluxe).
# Thiet ke moi: noi dung (ten/tien/%/vung/han) nghe tren GIONG SACH (dung tep dau-vao/giong.mp3 da duoc tron vao video); con bang chung "giong sach do CHINH LA giong phat ra trong MP4" la phep nay:
#   trich am 16 kHz mono tu MP4, so voi giong sach DAT DUNG VI TRI tren dong thoi gian video (am08.py / am-top5.py / am-tin.py tron giong tu t=0, khong tre) bang TUONG QUAN DUONG BAO NANG LUONG
#   (RMS khung 20 ms), CHI tren cac khung co giong, do lech +-300 ms. Cung loi nhung KHAC lan thu (nhip noi lech vai chuc ms) => tuong quan thap => TRUOT.
#   Bien thien theo gain/nhac nen (loudnorm tuyen tinh, tieng dong, ducking) it anh huong vi so duong bao tren khung co giong.
import numpy as np, pathlib

SR = 16000
KHUNG = 320                      # 20 ms @ 16 kHz
LECH_TOI_DA_S = 0.30             # do lech +-300 ms
SAN_DB = 35.0                    # khung "co giong": RMS giong >= dinh giong (phan vi 99) - 35 dB
NGUONG_TQ = 0.92                 # tuong quan toan bai toi thieu: cap DUNG do duoc >= 0,96; cap SAI cao nhat 0,87 (bang hieu chinh: bao cao + test)
NGUONG_TQ_DOAN = 0.82            # moi doan (1/3 bai) toi thieu: cap DUNG >= 0,93; cap SAI cao nhat 0,70

def ten_giong_sach(thu_muc_dau_vao):
    """Tep giong SACH = dung tep da dung de tron vao video (am08.py / am-top5.py / am-tin.py doc `dau-vao/giong.mp3`). Khong co -> FileNotFoundError (kiem THAT BAI, khong am tham)."""
    p = pathlib.Path(thu_muc_dau_vao) / 'giong.mp3'
    if not p.is_file(): raise FileNotFoundError(f'thieu giong sach {p} (tep giong.mp3 dung de tron video)')
    return p

def bao_rms(x, khung=KHUNG):
    """Duong bao nang luong: RMS tung khung 20 ms (float64)."""
    x = np.asarray(x, dtype=np.float64); n = len(x) // khung
    if n <= 0: return np.zeros(0)
    return np.sqrt(np.mean(x[:n * khung].reshape(n, khung) ** 2, axis=1))

def _tq(a, b):
    if len(a) < 20 or a.std() < 1e-9 or b.std() < 1e-9: return -1.0
    return float(np.corrcoef(a, b)[0, 1])

def lien_ket(g16, x16, lech_toi_da=LECH_TOI_DA_S, san_db=SAN_DB, so_doan=3):
    """Tuong quan duong bao giua giong sach `g16` (dat tu t=0) va am thanh MP4 `x16` (16 kHz mono float).
    -> dict(r, lech_ms, r_doan_min, so_khung): r = tuong quan lon nhat trong +-lech_toi_da; r_doan_min = tuong quan THAP NHAT cua `so_doan` doan lien tiep (cung do lech) — giong bi thay
    mot phan (vd cau cuoi thu lai) keo r_doan_min xuong du r toan bai van cao."""
    eg = bao_rms(g16); ex = bao_rms(x16); h = int(round(lech_toi_da * SR / KHUNG))
    if len(eg) == 0 or len(ex) == 0: return dict(r=-1.0, lech_ms=0, r_doan_min=-1.0, so_khung=0)
    dinh = np.percentile(eg, 99); co = eg >= dinh * 10 ** (-san_db / 20)
    sg = np.sqrt(eg)                                                    # nen nhe: giam anh huong dinh don le
    sx = np.sqrt(ex)
    tot = (-2.0, 0)
    for d in range(-h, h + 1):                                          # video[i + d] ~ giong[i]
        idx = np.nonzero(co)[0]; idx = idx[(idx + d >= 0) & (idx + d < len(ex))]
        if len(idx) < 20: continue
        r = _tq(sg[idx], sx[idx + d])
        if r > tot[0]: tot = (r, d)
    r, d = tot
    idx = np.nonzero(co)[0]; idx = idx[(idx + d >= 0) & (idx + d < len(ex))]
    rd = 1.0
    if len(idx) >= 20 * so_doan:
        cac = np.array_split(idx, so_doan)
        rd = min(_tq(sg[c], sx[c + d]) for c in cac)
    elif len(idx): rd = r
    return dict(r=round(r, 4), lech_ms=int(round(d * KHUNG / SR * 1000)), r_doan_min=round(rd, 4), so_khung=int(len(idx)))

def dat_lien_ket(kq, nguong=None, nguong_doan=None):
    """-> (dat, so_do) ; nguong mac dinh = NGUONG_TQ / NGUONG_TQ_DOAN (hieu chinh bang so that)."""
    n = NGUONG_TQ if nguong is None else nguong; nd = NGUONG_TQ_DOAN if nguong_doan is None else nguong_doan
    dat = kq['r'] >= n and kq['r_doan_min'] >= nd
    return dat, f"tuong quan duong bao {kq['r']:.3f} (>= {n}), doan thap nhat {kq['r_doan_min']:.3f} (>= {nd}), lech {kq['lech_ms']:+d} ms, {kq['so_khung']} khung co giong"
