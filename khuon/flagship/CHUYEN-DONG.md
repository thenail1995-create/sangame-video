<meta charset="utf-8">

# Chuyển động khuôn FLAGSHIP — mẫu motion-prompt đã dùng

Chọn theo `ke-hoach.md` mục 2 (28/10/2026); lấy spec bằng `node ~/.claude/skills/motion-prompt/scripts/motion-prompt.mjs get <id>`; port GIỮ số spec vào `khuon/flagship/full.html`. Mọi khung là hàm thuần của t (`window.__seek(t)`), seek được tới/lui.

| Cảnh | Mục đích | Mẫu | Port vào `full.html` | Đổi so với spec (và vì sao) |
|---|---|---|---|---|
| mo | Giữ 3 giây đầu: số tiền đập vào mắt | **#024 Impact shake** | `ve()`: khối `#nmo` đập tại chỗ (scale 1,15→1, cubic ease-in `ei`), nén 22% trong 0,3 s sau chạm (neo đáy, giãn ngang bù); rung cả `#sh` (dải thông tin): x 15·e^(−5τ)·sin(2π5τ), y 11·e^(−5τ)·cos(2π6,5τ), xoay 0,02·e^(−5τ)·sin(2π5τ+0,6) trong 1,1 s; 6 vạch trắng + 6 đốm bụi từ sàn trong 0,55 s (`fx()`); bìa game nhảy ≤ 24 px, trễ 0,03 s, 0,5 s | KHÔNG rơi từ trên xuống (28/10, Opus soát khung 0: rơi 70 px làm nửa trên số bị dải cắt ở y 1000 đúng khung móc). Thay bằng ĐẬP TẠI CHỖ: số nằm trọn trong dải ngay giây 0, scale 1,15 → 1 (cubic ease-in 0,32 s, neo đáy giữa), chạm ở 0,32 s rồi nén 22% + rung dải đúng spec. Bỏ kéo giãn dọc 1,12× lúc rơi. Số tiền 184 px (vòng đo `vua` thu nếu rộng hơn cột 494 px). Rung CHỈ lớp nội dung: nền dải + vạch cyan đứng yên và dải cắt tại y 1000 để trailer không dính điểm ảnh nào. Bỏ thoát (slab bay lên): giữ tới hết cảnh (SAN #36) |
| mo (tên game) | Tên game trượt vào | **#005 Mask reveal** | vạch cyan 820 px mọc từ giữa (eIO 0,1→0,5 s), chữ `#tmo` trượt từ 150 px bên dưới lên trong vùng cắt (quintic ease-out 0,35→1,0 s), chỉ cắt không đổi độ mờ | Vạch rộng 820 (cả hàng dưới bìa) vì tên dài cần 2 dòng ≥ 56 px; không có chữ dòng phụ trên vạch |
| gia | Làm nổi con số giá | **#001 Pop-in** | `sp(t,15,6.5)` (1−e^(−6,5t)cos 15t) cho "−80%" to, giá, chip, nhãn; chip + nhãn dùng thêm xoay −0,35→0 rad theo `1−e^(−6t)cos(11t)`; "−80%" to thu đi 0,18 s khi giá bật, chip nhỏ lấy chỗ | Khối LỚN (−%, giá, VND) kẹp lò xo ≤ 1,05 (SAN #45: không vượt đích); chip/nhãn nhỏ nảy đủ 1,26. Gạch đỏ giá gốc mọc 0,25 s đúng chữ "còn" |
| the | Giải thích "thẻ nào cho khít" | **#002 Stagger** | mỗi thẻ PSN vào theo `bo(p,2.6)` (backOut s = 2,6) trong 0,5 s, so le 0,12 s; tới câu "đúng … nghìn": "= 280.000đ" bật (#001) | Thẻ bay từ phải (ngang) thay vì mọc từ đáy (dọc); thẻ cùng mệnh giá so le 0,12 s, nhóm khác theo chữ "thẻ" trong lời |
| moc | Chuyển ý, móc thời sự | **#005 Mask reveal** | hai nửa chữ trượt ra từ hai phía vạch cyan (nửa trên từ dưới lên 0,35→1,0 s, nửa dưới từ trên xuống 0,55→1,15 s) | Số px khác (khung 494 px, chữ 72 px thay 98 / 32 px); bỏ thoát |
| han | Nhấn hạn deal | **#022 Light sweep** | nhãn "GIẢM TỚI" + ô ngày bật (#001); dải sáng 116 px (0,72) + vạch 12 px (0,5) cách 78 px, xoay 0,42 rad, lướt −130→+rộng+130 trong 1,05 s (eIOs), bắt đầu 0,45 s sau khi ngày bật | Cắt bằng `overflow:hidden` của ô ngày; không vẽ tia sao cuối vệt (không có chỗ, và là hiệu ứng phụ) |
| vung | Cảnh báo điều kiện | **#001 Pop-in** | cờ bật trước (có xoay), "CẦN TÀI KHOẢN" rồi "PSN MỸ" bật theo từ của lời | — |
| ket | Khoá thương hiệu + slogan | **#022** + **#005** | logo + "SĂN GAME" nảy vào, dải sáng lướt; 2 dòng slogan trượt ra từ sau mép dưới ô cắt (quintic) | Slogan không dùng vạch kẻ (không còn chỗ); mỗi dòng ra đúng chữ "săn" / "chơi" |

Nguyên tắc chung: vào 0,18–0,5 s, ease mạnh; mọi khối CHỈ hiện đúng lúc giọng nói tới (sớm ≤ 0,15 s), ở tới hết cảnh; thoát cảnh bằng mờ + trượt 24 px trong 0,2 s cuối. Không `blur(` / `backdrop-filter`. Số không xáo/đếm (SAN #47).
