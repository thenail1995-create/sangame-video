# Luật chọn 3 tin (thuần, không mạng — có unit test: test_chon_tin.py). Opus chốt 12/10:
#  (a) bài tin-nong chỉ nhận khi ngay >= ngày ĐĂNG - 1; cũ hơn -> dùng tin dữ liệu.
#  (b) đa dạng: không 2 tin cùng loại "danh sách giảm giá" (giam-sau / vua-giam / deal-hot); chỉ khi hết loại khác mới chấp nhận trùng loại.
import datetime as dtm
LOAI_DS_GIA=frozenset({'giam-sau','vua-giam','deal-hot'})

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
