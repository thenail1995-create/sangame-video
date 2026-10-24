<meta charset="utf-8">

# Chuyển động Top 5 "A · Đua giá" — mẫu motion-prompt đã dùng

Chọn bằng `motion-prompt search` (24/10/2026). Port GIỮ số spec, chỉ đổi phần ghi chú dưới đây.

| Cảnh | Mục đích | Mẫu | Port vào `khuon/top5/full.html` | Đổi so với spec |
|---|---|---|---|---|
| 0–1,3 s: 5 thanh giá mọc | Giữ 3 giây đầu (thấy ngay "đua giá"), cho người xem so độ dài trước khi nghe giá | **#002 Stagger** (motion, Entrances & text) | `bo()` = backOut s = 2,6; thanh i bắt đầu `0,15 + 0,12·i` s, mọc 0,5 s từ mép trái; bìa trượt vào cùng nhịp | Chiều ngang thay chiều cao; chặn không vượt mép vạch X (`min(W·g, TRACK-2)`); bỏ chấm trắng trên đầu thanh (không có chỗ, và không cần) |
| Mỗi hạng 5→1: hàng sáng lên | Chuyển ý, chỉ đúng hàng đang nói | **#033 Rack focus** (camera, Shooting Style & Time) | `eio()` cubic in-out; khung góc xanh `#mk` chạy THẲNG từ hàng này sang hàng kế (kích thước khung "thở" 58 → 70 → 58 px giữa đường, tương ứng half-width 46 → 30 của spec); các hàng khác về mờ | Thời lượng 0,5 s thay 1,6 s (kịp nhịp đọc từng hạng ~4 s/hạng); "mờ" làm bằng độ mờ đục 0,45 của bìa + màu thanh tối, KHÔNG làm nhoè (luật SAN-CHAT-LUONG #1: không blur) |

Ghi chú:
- Số trên thanh KHÔNG đếm từ 0 (luật #47 / CAI-TIEN: không xáo số). Thanh chỉ dài ra, số hiện sẵn đúng giá.
- Hàng 1 có nhấn nảy nhẹ (scale 1 + 0,045·sin(π·p) trong 0,5 s), vì lời đọc hạng 1 có thêm tiếng "ka-ching".
- Cuối video: 5 hàng sáng lần lượt (0,13 s/hàng, thanh xanh trượt vào theo cùng cơ chế sáng của #033) + chip "−%" bật vào từng thanh.
