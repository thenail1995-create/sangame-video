# Luật chọn 3 tin (thuần, không mạng — có unit test: test_chon_tin.py). Opus chốt 12/10:
#  (a) bài tin-nong chỉ nhận khi ngay >= ngày ĐĂNG - 1; cũ hơn -> dùng tin dữ liệu.
#  (b) đa dạng: không 2 tin cùng loại "danh sách giảm giá" (giam-sau / vua-giam / deal-hot); chỉ khi hết loại khác mới chấp nhận trùng loại.
import datetime as dtm
LOAI_DS_GIA=frozenset({'giam-sau','vua-giam','deal-hot'})
#  (c) 'sap-het' (SẮP HẾT GIẢM) là tin DỰ PHÒNG, KHÔNG thuộc LOAI_DS_GIA: coi như loại khác, xếp SAU vua-giam/deal-hot trong ung_vien() (chon-tin.py);
#      bộ chọn lười nên ngày đủ tin không bao giờ tới nó. Hạn: HAN_MIN <= end <= HAN_MIN + 2 ngày (hết giảm trong 2–4 ngày kể từ 07:30 ngày đăng).
KHOANG_SAP_HET_MS=2*24*3600*1000
def trong_khoang_sap_het(end_ms,han_min_ms):
    """endTime (ms) nằm trong [han_min, han_min + 2 ngày] (biên hai đầu đều nhận)."""
    return han_min_ms<=int(end_ms)<=han_min_ms+KHOANG_SAP_HET_MS

def tin_nong_hop_le(ngay_bai_iso,ngay_dang):
    """Bài tin-nong còn đủ 'tươi' để lên bản tin ngày ngay_dang: ngay >= ngay_dang - 1."""
    return str(ngay_bai_iso)[:10]>=(ngay_dang-dtm.timedelta(days=1)).isoformat()

def chon_ba(ung_vien,toi_da=3):
    """ung_vien: iterable (lười) các dict có 'khoa' và 'kieu', đã xếp theo ưu tiên. Lượt 1 bỏ qua tin 'danh sách giảm giá' thứ 2 trở đi
    (để dành); nếu chưa đủ thì lượt 2 điền bằng các tin để dành theo thứ tự. Trả list tối đa toi_da tin."""
    chon,hoan,khoa=[],[],set(); da_gia=False
    for r in ung_vien:
        if r['khoa'] in khoa: continue
        if r['kieu'] in LOAI_DS_GIA:
            if da_gia: hoan.append(r); continue
            da_gia=True
        chon.append(r); khoa.add(r['khoa'])
        if len(chon)==toi_da: return chon
    for r in hoan:
        if len(chon)==toi_da: break
        if r['khoa'] not in khoa: chon.append(r); khoa.add(r['khoa'])
    return chon

def loc_noi_bat_truoc_khi_cat(ds_day_du,trung,toi_da):
    """Bo game da noi bat TRUOC khi cat gioi han (toi_da), de con du ung vien bu (Sol P1: lay 10 roi loc co the con 2). ds_day_du = danh sach CHUA cat theo thu tu uu tien;
    trung(h) -> ly do|None. -> (list sau loc va cat toi_da, list (h,ly) bi bo)."""
    bo,giu=[],[]
    for h in ds_day_du:
        ly=trung(h)
        (bo if ly else giu).append((h,ly) if ly else h)
    return giu[:toi_da],bo
