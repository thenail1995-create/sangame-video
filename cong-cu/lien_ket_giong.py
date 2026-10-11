# Phep "giong trong video = giong da kiem" (D3 doi thiet ke 11/10/2026, Sol #10).
# Ly do: D3 cu cho Whisper nghe AM THANH MP4 CUOI (giong + nhac + tieng dong) -> nghe sai ten/so du loi dung (CI that 11/10 run 38106949664, Keo thom Returnal Digital Deluxe).
# Thiet ke moi: noi dung (ten/tien/%/vung/han) nghe tren GIONG SACH (dung tep dau-vao/giong.mp3 da duoc tron vao video); con bang chung "giong sach do CHINH LA giong phat ra trong MP4" la phep nay:
#   trich am 16 kHz mono tu MP4, so voi giong sach DAT DUNG VI TRI tren dong thoi gian video (am08.py / am-top5.py / am-tin.py tron giong tu t=0, khong tre) bang TUONG QUAN DUONG BAO NANG LUONG
#   (RMS khung 20 ms), CHI tren cac khung co giong, do lech +-300 ms. Cung loi nhung KHAC lan thu (nhip noi lech vai chuc ms) => tuong quan thap => TRUOT.
#   Sol soi cuoi 11/10 bo sung (RMS don thuan khong chung minh cung giong): (a) PHU >= 95% khung co giong nam trong thoi luong MP4 va con nang luong (cat con nua giong => truot);
#   (b) giong THUA > 1 s ngoai khoang giong sach (doan to, co nhip am tiet, nhac nen deu khong tinh) => truot; (c) tuong quan THEO TUNG cua so moc-chu (<= 2,5 s, phu ca loi: ten/gia/han) >= 0,80.
#   Gioi han con lai: so sanh duong bao nang luong, KHONG so pho — tin hieu khac giu dung duong bao van lot (can so pho/Whisper-align neu muon chan).
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

NGUONG_PHU = 0.95                # >= 95% khung co giong cua giong sach phai NAM TRONG thoi luong MP4 (o dung do lech) VA con nang luong (khong bi cat / tat)
NGUONG_TQ_CUA_SO = 0.80          # tung cua so moc-chu (ten / gia / han) toi thieu
SAN_NANG = 0.25                  # khung "con nang luong": RMS MP4 >= 25% muc RMS giong sach da quy ve cung gain (gain = trung vi ti le tren khung co giong)
NGUONG_NGOAI_S = 1.0             # giong noi KEO DAI > 1 s o NGOAI khoang giong sach (cach khung co giong >= 0,4 s) => truot (giong khac noi them / ghep them bai)
SAN_NGOAI = 0.35                 # khung ngoai khoang "to nhu giong": RMS MP4 >= 35% (gain * trung vi RMS giong sach). Do that: nhac outro dai nhat 0,38 s / 1,2 s ngoai khoang
CV_GIONG = 0.35                  # he so bien thien duong bao toi thieu de coi doan ngoai khoang la GIONG (nhac nen deu ~0,06)
NGHI_DONG = 15                   # dong khe nghi <= 0,3 s giua cac tu
NGHI_NGOAI = 20                  # 0,4 s quanh khung co giong coi la 'trong khoang giong'
CUA_SO_TOI_DA_S = 2.5            # cua so moc-chu dai toi da (giay)
CUA_SO_TOI_THIEU_KHUNG = 25      # < 25 khung co giong (0,5 s) trong cua so => gop vao cua so ke ben (khong du de tinh tuong quan)

def cua_so_moc_chu(moc, toi_da=CUA_SO_TOI_DA_S, nghi=0.35):
    """Chia lai moc-chu [{w,s,e,doan}] thanh cac CUA SO lien tiep <= `toi_da` giay (cat o khoang nghi >= `nghi` s hoac khi qua dai, khong vuot ranh gioi doan) — phu TOAN BO loi noi,
    nen moi cum ten / gia / han deu nam trong mot cua so. -> [(s, e)] giay."""
    ws = [w for w in moc if str(w.get('w', '')).strip()]
    out = []; cur = None
    for i, w in enumerate(ws):
        if cur is None: cur = [w['s'], w['e'], w.get('doan')]; continue
        qua_dai = w['e'] - cur[0] > toi_da; doi_doan = w.get('doan') != cur[2]; nghi_dai = w['s'] - cur[1] >= nghi
        if doi_doan or (qua_dai and nghi_dai) or w['e'] - cur[0] > toi_da * 1.6: out.append((cur[0], cur[1])); cur = [w['s'], w['e'], w.get('doan')]
        else: cur[1] = w['e']
    if cur: out.append((cur[0], cur[1]))
    return out

def lien_ket(g16, x16, lech_toi_da=LECH_TOI_DA_S, san_db=SAN_DB, so_doan=3, cua_so=None):
    """Tuong quan duong bao giua giong sach `g16` (dat tu t=0) va am thanh MP4 `x16` (16 kHz mono float).
    -> dict(r, lech_ms, r_doan_min, so_khung, phu, ngoai_s, r_cua_so_min, so_cua_so, cua_so_thap): r = tuong quan lon nhat trong +-lech_toi_da; r_doan_min = tuong quan THAP NHAT cua `so_doan` doan lien tiep (cung do lech);
    phu = ti le khung co giong cua giong sach nam TRONG thoi luong MP4 o do lech do VA con nang luong (giong bi cat / tat / thieu => phu thap, du r = 1);
    r_cua_so_min = tuong quan thap nhat theo tung cua so moc-chu `cua_so` [(s,e) giay] (None neu khong truyen cua_so)."""
    eg = bao_rms(g16); ex = bao_rms(x16); h = int(round(lech_toi_da * SR / KHUNG))
    rong = dict(r=-1.0, lech_ms=0, r_doan_min=-1.0, so_khung=0, phu=0.0, ngoai_s=0.0, r_cua_so_min=(-1.0 if cua_so else None), so_cua_so=0, cua_so_thap=None)
    if len(eg) == 0 or len(ex) == 0: return rong
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
    tat_ca = np.nonzero(co)[0]; idx = tat_ca[(tat_ca + d >= 0) & (tat_ca + d < len(ex))]
    rd = 1.0
    if len(idx) >= 20 * so_doan:
        cac = np.array_split(idx, so_doan)
        rd = min(_tq(sg[c], sx[c + d]) for c in cac)
    elif len(idx): rd = r
    # PHU: moi khung co giong cua giong sach phai (1) nam trong thoi luong MP4 o do lech d, (2) con nang luong tuong ung (ex >= SAN_NANG * gain * eg) — cat con nua giong / tat tieng => phu ~ 0,5
    phu = 0.0
    if len(tat_ca) and len(idx):
        gain = float(np.median(ex[idx + d] / np.maximum(eg[idx], 1e-9)))
        con = np.zeros(len(tat_ca), dtype=bool); trong = (tat_ca + d >= 0) & (tat_ca + d < len(ex))
        con[trong] = ex[tat_ca[trong] + d] >= SAN_NANG * gain * eg[tat_ca[trong]]
        phu = float(con.mean())
    # GIONG THUA: khung MP4 ngoai khoang giong sach (cach khung co giong >= 0,4 s, ke ca duoi sau khi giong het) ma van to nhu giong, keo dai > NGUONG_NGOAI_S => ngoai_s
    ngoai_s = 0.0
    if len(idx):
        gain_ = float(np.median(ex[idx + d] / np.maximum(eg[idx], 1e-9))); med_ = float(np.median(eg[idx]))
        gan = np.zeros(len(ex), dtype=bool); vi = tat_ca + d; vi = vi[(vi >= 0) & (vi < len(ex))]; gan[vi] = True
        cs_ = np.concatenate([[0], np.cumsum(gan)]); lo = np.maximum(np.arange(len(gan)) - NGHI_NGOAI, 0); hi = np.minimum(np.arange(len(gan)) + NGHI_NGOAI + 1, len(gan)); gan = (cs_[hi] - cs_[lo]) > 0
        to = (ex >= SAN_NGOAI * gain_ * med_) & ~gan; sxe = np.sqrt(ex)
        # 'giong' = doan to keo dai (khe nghi <= 0,3 s dong lai) CO nhip am tiet (he so bien thien cua sqrt-RMS >= CV_GIONG): nhac nen deu (cv ~ 0,06) khong tinh; giong that cv 0,4-0,9
        best = 0; i = 0; n_ = len(to)
        while i < n_:
            if not to[i]: i += 1; continue
            j = i; cuoi = i; kh = 0
            while j < n_ and kh <= NGHI_DONG:
                if to[j]: cuoi = j; kh = 0
                else: kh += 1
                j += 1
            seg = sxe[i:cuoi + 1]
            if len(seg) > best and seg.mean() > 0 and seg.std() / seg.mean() >= CV_GIONG: best = len(seg)
            i = cuoi + 1
        ngoai_s = best * KHUNG / SR
    # CUA SO moc-chu: tuong quan theo TUNG cua so (ten / gia / han), cung do lech d, chi tren khung co giong
    rcs = None; thap = None; n_cs = 0
    if cua_so:
        rcs = 2.0; cs_ = [list(c) for c in cua_so]; i = 0
        gop = []
        for s_, e_ in cs_:                                              # gop cua so qua ngan (it khung co giong) vao cua so truoc
            f0 = int(s_ * SR / KHUNG); f1 = int(np.ceil(e_ * SR / KHUNG)); nk = int(co[f0:f1].sum()) if f0 < len(co) else 0
            if gop and nk < CUA_SO_TOI_THIEU_KHUNG: gop[-1][1] = e_
            else: gop.append([s_, e_])
        for s_, e_ in gop:
            f0 = int(s_ * SR / KHUNG); f1 = int(np.ceil(e_ * SR / KHUNG)); c = np.arange(f0, min(f1, len(co)))
            c = c[co[c]] if len(c) else c
            c = c[(c + d >= 0) & (c + d < len(ex))]
            q = _tq(sg[c], sx[c + d]) if len(c) >= 20 else -1.0
            n_cs += 1
            if q < rcs: rcs = q; thap = (round(s_, 2), round(e_, 2))
        if n_cs == 0: rcs = -1.0
    return dict(r=round(r, 4), lech_ms=int(round(d * KHUNG / SR * 1000)), r_doan_min=round(rd, 4), so_khung=int(len(idx)), phu=round(phu, 4), ngoai_s=round(ngoai_s, 2),
                r_cua_so_min=(None if rcs is None else round(rcs, 4)), so_cua_so=n_cs, cua_so_thap=thap)

def dat_lien_ket(kq, nguong=None, nguong_doan=None, nguong_phu=None, nguong_cua_so=None):
    """-> (dat, so_do) ; nguong mac dinh = NGUONG_TQ / NGUONG_TQ_DOAN / NGUONG_PHU / NGUONG_TQ_CUA_SO (hieu chinh bang so that). Co `cua_so` thi r_cua_so_min >= nguong_cua_so la BAT BUOC."""
    n = NGUONG_TQ if nguong is None else nguong; nd = NGUONG_TQ_DOAN if nguong_doan is None else nguong_doan
    npu = NGUONG_PHU if nguong_phu is None else nguong_phu; nc = NGUONG_TQ_CUA_SO if nguong_cua_so is None else nguong_cua_so
    phu = kq.get('phu', 0.0); rc = kq.get('r_cua_so_min')
    dat = kq['r'] >= n and kq['r_doan_min'] >= nd and phu >= npu and kq.get('ngoai_s', 0.0) <= NGUONG_NGOAI_S and (rc is not None and rc >= nc)
    so = f"tuong quan duong bao {kq['r']:.3f} (>= {n}), doan thap nhat {kq['r_doan_min']:.3f} (>= {nd}), phu {phu:.3f} (>= {npu}), giong thua ngoai khoang {kq.get('ngoai_s', 0.0):.2f} s (<= {NGUONG_NGOAI_S}), "
    so += (f"cua so moc-chu thap nhat {rc:.3f} (>= {nc}; {kq.get('so_cua_so', 0)} cua so" + (f", thap tai {kq['cua_so_thap']}" if kq.get('cua_so_thap') else '') + ')') if rc is not None else 'THIEU cua so moc-chu (bat buoc)'
    return dat, so + f", lech {kq['lech_ms']:+d} ms, {kq['so_khung']} khung co giong"
