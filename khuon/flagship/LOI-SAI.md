<meta charset="utf-8">

# LOI-SAI khuôn FLAGSHIP

(Chưa có lỗi nào được ghi. Mỗi góp ý/lỗi mới của Hào: thêm một dòng ở đây + thêm phép kiểm nếu máy kiểm được, theo cách của `mau/video-tap-chi-v8/LOI-SAI.md`.)

| Ngày | Lỗi | Gốc | Sửa | Phép kiểm |
|---|---|---|---|---|
| 01/11/2026 | Chạy thử CI (run 41319190369, Assassin's Creed Valhalla Deluxe) dừng ở căn chữ: đoạn `gia` lệch 11 s, không ra video | Đoạn `gia` mở bằng "Game", chữ này LẶP ở "Săn Game" (móc thấp nhất + slogan). Whisper nghe "Game đang giảm" thành "viêm đăng giảm" → `can-chu.py neo_doan` và `cong-cu/kiem_moc.py` đều neo đoạn `gia` vào "Săn Game" ở 14,5 s | Đoạn `gia` mở bằng "Đang giảm …" (từ neo `dang` không xuất hiện ở đoạn nào khác). Thử lại trên Mac cùng game: 7/7 đoạn đạt, lệch ≤ 0,04 s | `test_flagship.py::NeoDoan` — từ neo của mỗi đoạn không được xuất hiện ở đoạn sau, với 7 kiểu câu mở × 4 loại móc |
| 01/11/2026 | Chạy thử CI lần 2 (run 41321247937): bản TikTok 22/23, trượt phép nền "máu me" — 1 khung ở 10,25 s có 6,6 % điểm ảnh đỏ (ngưỡng 6 %) | `nen-flagship.py mau_quet` chọn đoạn chỉ soi 4 khung/giây, khung đỏ nằm giữa hai lần soi | Soi 15 khung/giây khi chọn đoạn (ngưỡng chọn 5 % vẫn chặt hơn ngưỡng kiểm 6 %) | Phép kiểm nền của `kiem-tat-ca.py` (đã bắt được) |
