# Kế hoạch SG-DU-KENH — máy tin GIÁ riêng cho Facebook, Instagram, Threads (Săn Game)

Viết 02/11/2026 (Opus, phiên phụ SG-DU-KENH). Hào chốt 02/11: "săn game vẫn đủ social" + luật 01/11 "1 nội dung = 1 nền tảng", "luôn làm tin về giá".
Đọc HẾT file này trước khi làm. Mục "SỬA SAU SOI" (nếu có ở cuối) đè lên các mục trên.

## 0. Hào đã chốt (không hỏi lại)
| Kênh | Loại (dang trong sg_dang) | Nội dung mỗi ngày | Bản phác chốt |
|---|---|---|---|
| Facebook (Trang) | `fb-gia`, kênh `fb` | Reel 11 s KHÔNG giọng AI (nhạc + tiếng động + chữ): 1 game, bảng 3–5 store theo TIỀN THẺ THẬT phải mua, store rẻ nhất sáng lên, "rẻ hơn Store X N đ", thẻ PSN lật ra, giá gốc/% giảm/hạn, khung cuối logo | `phac/fb-chot.html` + ảnh `phac/fb-chot-khung.jpg` |
| Instagram | `ig-gia`, kênh `ig` | Reel ~11 s KHÔNG giọng AI, CÙNG KIỂU FB-A nhưng nội dung riêng: xếp hạng 3–5 game cùng IP/sự kiện theo giá (thanh ngang), game rẻ nhất sáng lên, khung cuối logo | Hào: "lấy kiểu này" (kiểu FB-A) |
| Threads | `threads-gia`, kênh `threads` | Bài CHỮ "hỏi chọn" (≤ 500 ký tự) + 1 ẢNH 1080×1350: 2 game CÙNG giá VNĐ, VS, mình chọn 1 bên có số (sao + lượt chấm PS Store), hỏi lại người đọc | `phac/threads-ban-phac.html` (đổi sang màu logo) |

**MÀU CHỐT (Hào: "lấy màu lô gô ấy")**: xanh ngọc `#20C3C0`, đỏ `#C92324`, đỏ nâu viền `#5F0B0F`, kem `#FDEBBD` (+ kem đậm `#F2D9A0`). Kiểu sticker như logo: viền dày đỏ nâu 5–8 px, bóng đổ cứng `Npx Npx 0 #5F0B0F`, chữ to viền đỏ nâu (`-webkit-text-stroke` + `paint-order:stroke fill`), lớp phủ ảnh game đỏ nâu tối. KHÔNG dùng xanh navy, xanh lơ #3ef0e0, đen #0b0b10 của bản cũ. Bản tham chiếu đúng màu: `phac/fb-chot.html` (khối `<style>` cuối = bảng màu logo).

Không giọng AI ở cả 3 kênh ⇒ KHÔNG gửi `is_ai_generated`, KHÔNG thêm dòng "Video dùng giọng đọc AI." (nội dung không có giọng/ảnh AI; nhạc nền là âm thanh ElevenLabs SFX — không phải giọng người, không thuộc diện nhãn "giọng AI nghe như thật"). Tránh được cổng nhãn AI (ma trận v3 luật 2) mà FB/IG/Threads qua máy đang chặn.

## 1. Kiến trúc (đi theo mẫu `dang/x_goc.py` + `x-goc.yml`, KHÔNG đụng dung.yml/dang.yml/chay.py)
Một workflow tự chứa mỗi lượt: chọn → kiểm trang PS Store → tải ảnh → dựng → kiểm tự động → giữ sổ → chuẩn bị trên nền tảng → chờ tới giờ → kiểm lại giá → công khai → ghi sổ.

Tệp MỚI (worker A = dựng, worker B = máy đăng; không ai sửa tệp của người kia):
- **Worker A** — `khuon/tin-gia-mxh/`: `fb.html`, `ig.html`, `threads.html`, `chung.css`, `dong.js`, `co/{us,hk,sg,th,id}.svg`, `dung.py`, `do.mjs`, `kiem.py`, `test_tin_gia_mxh_khuon.py`. Font + logo dùng lại `../flagship/BeVietnamPro-*.ttf`, `../flagship/logo.svg` (đường dẫn tương đối, không chép).
- **Worker B** — `dang/tin_gia_chon.py` (chọn, thuần, không mạng), `dang/tin_gia_chu.py` (chữ đăng + cổng, thuần), `dang/tin_gia_mxh.py` (điều phối, mạng), `dang/tests/test_tin_gia_mxh.py`, `.github/workflows/tin-gia-mxh.yml`; sửa NHỎ có tương thích ngược: `dang/fb.py` (`tham_finish(..., co_ai=None)`), `dang/ig.py` (`tham_container(..., co_ai=None)`), `dang/zernio.py` (thêm `tai_tep(khoa, duong, ten, content_type)` dùng chung cho mp4/jpg/png, giữ `tai_video`/`tai_anh` như cũ).
- **Opus** — Supabase (CHECK `sg_dang_dang_check` + edge `sg-cong` DANG thêm `fb-gia`, `ig-gia`, `threads-gia`), nhạc nền vào repo riêng tư `kenh-game-du-lieu/video/tai-san/nhac/`, PR, chạy thử CI.

## 2. Hợp đồng dữ liệu giữa B (chọn) và A (dựng): `dl.json`
Mọi số tiền là số nguyên VNĐ; mọi chuỗi hiển thị đã định dạng sẵn ở B (A chỉ hiển thị, không tự tính). Đường dẫn ảnh tương đối với thư mục `--tai-san`.
```json
// fb
{"kenh":"fb","ngay":"2026-11-02","ten":"MONSTER HUNTER RISE","bia":"g0-bia.jpg","nen":["g0-c0.jpg","g0-c1.jpg"],
 "gia_vnd":180000,
 "vung":[{"ma":"SG","ten":"Singapore","vnd":330000},{"ma":"HK","ten":"Hồng Kông","vnd":280000},{"ma":"TH","ten":"Thái Lan","vnd":280000},
         {"ma":"ID","ten":"Indonesia","vnd":210000},{"ma":"US","ten":"Mỹ","vnd":180000}],
 "re_hon":{"ten":"Singapore","vnd":150000},
 "the":{"ma":"US","ten_vung":"Mỹ","the":[{"menh_gia":"$5","so_luong":1}],"gia_game":"$4,79","du":"$0,21"},
 "goc":"$39,99","giam":88,"han_chu":"14:59 · 5/11"}
// ig
{"kenh":"ig","ngay":"2026-11-02","tieu_de":["4 GAME","FINAL FANTASY","DƯỚI 500K"],
 "game":[{"ten":"FINAL FANTASY VII REBIRTH","bia":"g0-bia.jpg","nen":"g0-c0.jpg","gia_vnd":460000,"ma_vung":"US","giam":70}, …],
 "han_chu":"14:59 · 5/11","giam_chung":70,"vung_chung":"Mỹ"}
// threads
{"kenh":"threads","ngay":"2026-11-02","cau_hoi":["Có 460 nghìn,","chọn bên nào?"],
 "a":{"ten":"FINAL FANTASY VII REBIRTH","bia":"a-bia.jpg","nen":"a-c0.jpg","gia_vnd":460000,"sao":"4,66","luot":"64.676"},
 "b":{"ten":"FINAL FANTASY XII THE ZODIAC AGE","bia":"b-bia.jpg","nen":"b-c0.jpg","gia_vnd":460000,"sao":"4,75","luot":"11.893"},
 "chan":"Store Mỹ $14,99 (−70%) · thẻ $10 + $5 · hết giảm 14:59 · 5/11"}
```
Quy ước: `vung` (fb) xếp GIẢM dần, store rẻ nhất ở CUỐI, 3–5 dòng. `game` (ig) xếp GIẢM dần theo `gia_vnd`, rẻ nhất cuối, 3–5 game. `han_chu` giờ VN.

## 3. Worker A — dựng + kiểm (`khuon/tin-gia-mxh/`)
### 3.1 Khuôn HTML (1080×1920, 30 fps; threads 1080×1350 ảnh tĩnh)
- Hợp đồng chụp tất định của `cong-cu/capture.mjs`: `window.__ready=false` → true khi font + ảnh xong; `window.__seek(t)` vẽ khung t (hàm thuần theo t). Dữ liệu nạp qua `<script src="du-lieu.js">` (`window.DL = {...dl.json}`) do `dung.py` viết.
- **fb.html**: dựng lại đúng `phac/fb-chot.html` (bố cục + mốc giây + màu logo), nhưng sinh từ `DL`: số dòng 3–5, độ dài thanh ∝ vnd/max, cờ theo `ma` (`co/<ma>.svg`), tên game tự co (canvas measureText, tối đa 960 px), giá đầu "180.000đ", dòng "Rẻ hơn Store {re_hon.ten} {vnd}", thẻ PSN hiện mệnh giá `the[0].menh_gia` (≥2 loại thẻ → xếp 2 thẻ cạnh nhau, ví dụ "$10" + "$5"), "game {gia_game} · dư {du} trong ví", chip "Gốc {goc} −{giam}%" + "Hết giảm {han_chu}". Nền: Ken Burns `nen[0]` (đổi sang `nen[1]` lúc 6,0 s nếu có). Khung cuối: bìa + `logo.svg` + "Săn đúng kèo, chơi đỡ nghèo!".
- **ig.html**: CÙNG phong cách fb.html (Hào chốt). Mốc: 0–1 s tiêu đề 3 dòng (`tieu_de`) to giữa khung (dòng 2 xanh ngọc, dòng 3 kem viền đỏ nâu bóng đỏ) → 1,0 s tiêu đề thu lên trên (y≈300) → bảng kem viền đỏ nâu, thanh tiêu đề xanh ngọc "GIÁ THẺ RẺ NHẤT · {n} GAME"; mỗi dòng: bìa vuông 84 px viền đỏ nâu + tên game (tự co) + giá đỏ + thanh ∝ giá; các dòng vào so le 0,5 s từ 1,5 s; nền đổi sang ảnh của game vừa vào (mờ 10 px, phủ đỏ nâu); dòng rẻ nhất sáng lên (nền kem sáng + viền đỏ + nhãn "RẺ NHẤT" đỏ chữ kem) tại 1,5+0,5·n+0,3 s → 6,0 s bảng rút, bìa game rẻ nhất to giữa khung (viền + bóng cứng) + tem giá "216K" xoay −7° → 8,0 s chip "Giảm {giam_chung}% · Store {vung_chung}" (bỏ phần nào null) + "Hết giảm {han_chu}" → 9,6 s khung cuối logo như fb. Tổng 11,0 s.
- **threads.html** (ảnh tĩnh): bố cục `phac/threads-ban-phac.html` đổi sang màu logo: hai nửa ảnh nền phủ đỏ nâu, câu hỏi 2 dòng chữ kem viền đỏ nâu trên dải xanh ngọc, 2 bìa viền đỏ nâu bóng cứng, tròn "VS" đỏ chữ kem, giá kem viền đỏ nâu "460K", dòng "★ {sao} · {luot} lượt chấm", chân trang chip kem chữ đỏ nâu `chan` (tự co 1 dòng ≤ 1000 px).
- Vùng an toàn chữ quan trọng (fb/ig): x 60–1020, y 269–1248 (Reels/FB che trên 14 %, dưới 35 %). Không chữ nào tràn khung hay đè nhau.

### 3.2 `dung.py`
`python3 khuon/tin-gia-mxh/dung.py --kenh fb|ig|threads --du-lieu dl.json --tai-san DIR --am DIR_SFX --nhac FILE.mp3 --ra OUT`
- Chép khuôn + `du-lieu.js` + ảnh vào thư mục tạm có đủ đường dẫn tương đối (font/logo của flagship), chạy `node cong-cu/capture.mjs <html> OUT/hinh.mp4 30 11 1080 1920 --root=<goc> --workers=4 --quiet` (threads: `--stills=0` 1080×1350 → `OUT/anh.png`).
- Bìa fb/ig: still t=0,3 s → `OUT/bia.jpg` (JPEG q≈90, 1080×1920).
- Âm: nhạc `--nhac` cắt 11 s, fade-out 0,7 s cuối, + tiếng động theo mốc (bảng cue như `phac/am-phac.py`, KIT điểm chạm đã đo), `loudnorm I=-14:TP=-1.5:LRA=11`, AAC 192k 48 kHz stereo → ghép `OUT/video.mp4` (`-movflags +faststart`, h264 yuv420p).
- `do.mjs` (Playwright): mở trang, tại các mốc kiểm (fb/ig: 0, 0,3, 1,6, 3,0, 4,6, 5,6, 7,0, 8,6, 10,7; threads: 0) ghi `OUT/do.json`: mỗi phần tử chữ hiển thị (opacity>0.05): id/class, text, bbox sau transform (getBoundingClientRect), scrollWidth/clientWidth, opacity.
- Thoát ≠0 khi lỗi trang (capture.mjs đã ABORT khi pageerror/ảnh hỏng).

### 3.3 `kiem.py` → JSON `{"dat":bool,"phep":[{"ten","dat","chi_tiet"}]}`, thoát 0 khi đạt hết
fb/ig: K1 ffprobe 1080×1920 · 30 fps · h264 yuv420p · 10–15 s · ≤ 100 MB; K2 âm AAC 48 kHz, tích hợp −14 ± 1,5 LUFS, đỉnh thật ≤ −1,0 dBTP, 0–0,5 s mean > −35 dB (có tiếng ngay); K3 không khung tối (mẫu 2 khung/s, luma TB ≥ 12); K4 vùng an toàn: chữ quan trọng trong x 60–1020, y 269–1248, mọi chữ trong 0–1080 × 0–1920; K5 không tràn chữ (scrollWidth ≤ clientWidth + 1); K6 không đè nhau: các cặp phần tử chữ cùng hiện (opacity ≥ 0,5) không giao nhau > 4 px² (trừ cặp được khai báo là lồng nhau, vd nhãn trong dòng); K7 SỐ ĐÚNG: mọi số tiền/% /giờ xuất hiện trong chữ DOM thuộc tập số sinh từ dl.json (không số lạ), giá đầu = `gia_vnd`, số dòng = len(vung|game); K8 khung 0: phần tử giá đầu (fb) / tiêu đề (ig) có opacity ≥ 0,99 tại t=0; K9 `bia.jpg` 1080×1920 ≤ 10 MB.
threads: T1 `anh.png` 1080×1350 ≤ 8 MB; T2 vùng/tràn/đè như K4–K6 trong 30–1050 × 30–1320; T3 số đúng như K7.
Test (`test_tin_gia_mxh_khuon.py`, pytest): dựng 3 khuôn với dl mẫu (ảnh mẫu tự tạo bằng ffmpeg/magick màu đặc, không ảnh Sony vào repo), kiem.py đạt; dl có tên game 70 ký tự vẫn đạt (tự co); dl 3 dòng và 5 dòng đều đạt; thử hỏng (sửa tay một số trong DOM qua dl lệch) thì K7 trượt.

## 4. Worker B — máy chọn + đăng
### 4.1 Lịch + cổng
`GIO = {"threads": "11:30", "fb": "19:00", "ig": "20:30"}` (giờ VN; cron-job.org gọi workflow lúc T−35 phút; Opus KHÔNG tạo lịch). Pha thật chỉ chạy khi biến repo `SG_KENH_BAT` có ĐÚNG mục riêng khuôn `<dang>:<kenh>` (`fb-gia:fb`, `ig-gia:ig`, `threads-gia:threads`) — xem BỔ SUNG OPUS mục 10; KHÔNG dùng `dang.chay.doc_kenh_bat` (hàm đó rơi về mục chung). Thật mà đã quá T−2 phút thì thoát 3, không đăng bù.

### 4.2 Chọn (`tin_gia_chon.py`, thuần — mọi I/O truyền vào)
Đầu vào chung: hàng sg_keo hôm nay (`cong.doc_keo`, chờ như `x_goc.doc_keo_cho`), `gia-the.json` (≤ 7 ngày, không thì dừng), tập game đã nổi bật 3 ngày (`cong-cu/da_noi_bat.py da_noi_bat(ngay, dang)` + `id_tai` của các dòng sg_dang `fb-gia|ig-gia|threads-gia|x-goc` 3 ngày gần nhất và CÙNG ngày, mọi trạng thái trừ `that_bai`/`bo`), hàm `lay_trang(link)` (tải trang PS Store, trả khoi_gia/media/thong_tin) và `quy_vnd` của `deal_diem` (repo riêng tư).
Lọc chung mỗi hàng: `nen_tang=='ps'`, `lech_gia is False`, link `https://store.playstation.com/`, `gia_vung[vung_re_nhat]` có `mua_duoc` + `cach=='the'` + không `chi_plus`, `gia_vnd` 50.000–1.500.000, không trùng tập đã nổi bật. Kiểm trang (fail-closed, như `x_goc.kiem_trang` nhưng đọc JSON trang qua `cong-cu/gia_trang.py`): giá trang == `gia_vung[vung].gia` (±0,011), endTime có và ≥ giờ đăng + 24 h, % giảm trang lệch ≤ 1 điểm; tính lại thẻ bằng `quy_vnd` trên giá trang → phải `cach=='the'`, `mua_duoc`, `vnd == gia_vung[vung].vnd`, ≤ 4 tấm. Ảnh: bìa (`media.anh`) + ≥ 1 ảnh chụp (`anh_chup`), tải được, ≥ 600 px cạnh ngắn.
- **fb**: thêm điều kiện ≥ 3 store `mua_duoc && cach=='the'` trong `gia_vung` (tính cả store rẻ nhất), store rẻ nhất có vnd NHỎ NHẤT duy nhất, `max − min ≥ 30.000`. Lấy tối đa 5 store (luôn có rẻ nhất + đắt nhất). Thứ tự ứng viên: `da_kiem_trang` trước, rồi `hang`. Tối đa 4 lần tải trang.
- **ig**: gom nhóm theo khoá IP = 2 từ đầu của `dong_game(ten)` (vd "final fantasy", "resident evil", "monster hunter"); bỏ trùng sản phẩm (cùng mã `PPSA…/CUSA…` trước dấu `|` của `ma`, hoặc cùng `dong_game`). Nhóm hợp lệ có ≥ 3 game qua kiểm trang; chọn nhóm nhiều game nhất (hoà → tổng `diem` cao hơn); lấy tối đa 5 game. Không có nhóm IP → nhóm dự phòng "N GAME PS DƯỚI X" từ các game qua kiểm có `gia_vnd ≤ 300.000`, ≥ 3 game. `tieu_de` = [`{n} GAME`, tên IP viết HOA (hoặc "PS4 · PS5"), `DƯỚI {X}K`] với X = bội 100 nghìn nhỏ nhất > giá lớn nhất. Tối đa 10 lần tải trang.
- **threads**: cặp 2 game qua kiểm có CÙNG `gia_vnd` (ưu tiên cùng nhóm IP, rồi cùng thể loại `the_loai` trang, rồi tổng `diem`); cả hai có điểm sao trang (`thong_tin_game.diem.tb`, `so_luot ≥ 100`). "Mình chọn": game có `so_luot` ≥ 3× game kia và `tb` thấp hơn không quá 0,2 → chọn game nhiều lượt; còn lại chọn `tb` cao hơn; hoà → nhiều lượt hơn. Tối đa 8 lần tải trang.
Ra: `dl.json` (mục 2) + `chon.json` (đã chọn gì, vì sao; mỗi ứng viên bị bỏ + lý do) + danh sách `kiem_lai` `[{ten,pid,loc,gia,endTime}]` cho bước kiểm lại trước giờ đăng (`dang/gia.py kiem_lai`, giá phải đúng y).

### 4.3 Chữ đăng (`tin_gia_chu.py`, thuần)
- **FB caption** (`description`): dòng 1 `{Tên} còn {N nghìn} ở Store {vùng}: {thẻ} là đủ, rẻ hơn Store {re_hon} {M nghìn}.`; dòng 2 `Giảm {g}% (gốc {goc}) tới {HH:MM} ngày {d/m}. Thẻ nạp phải cùng vùng tài khoản PSN.`; dòng 3 ≤ 3 hashtag (`hashtag_game`, `#PS5`, `#SănGame`). Không URL/tên miền (luật SG-FB-2), không "like/follow".
- **IG caption**: dòng 1 `{n} game {IP} từ {giá rẻ nhất} nghìn, giảm tới {HH:MM} ngày {d/m} ở PS Store {vùng}.`; dòng 2 liệt kê `Tên – N nghìn` ngắn; dòng 3 `Cần tài khoản PSN {vùng}, thẻ nạp phải cùng vùng.`; dòng 4 `Bảng giá đủ vùng: link ở bio.`; ≤ 5 hashtag (tag IP, `#PS5`, `#SănGame`, …). Không URL.
- **Threads text**: ≤ 450 ký tự VÀ ≤ 500 byte UTF-8, 3 đoạn: (1) câu hỏi có số tiền "Có {N} nghìn, anh em chọn {A} hay {B}?" (2) giá đô + vùng + % + hạn + thẻ khít + "Mình chọn {X}: {lý do bằng số}" (3) "Mua store {vùng} cần tài khoản PSN {vùng}. {câu hỏi kết}". KHÔNG mẫu câu cố định: ≥ 4 biến thể câu mở × ≥ 4 biến thể câu kết, chọn theo (ngày − 2026-11-01) và KHÔNG lặp câu mở trong 7 ngày (lưu mã biến thể vào `id_container`… xem 4.4). 0 hashtag, 0 URL; `topic_tag="PlayStation"`; `alt_text` 1 câu tả ảnh (≤ 1.000 ký tự).
- **Cổng tin giá (mọi kênh, fail-closed)**: dòng 1 phải có ≥ 1 số tiền VNĐ và MỌI số tiền VNĐ ở dòng 1 ∈ tập `gia_vnd` đã kiểm (dùng `dang.chay.tien_vnd`). Mọi số tiền trong toàn caption ∈ tập số sinh từ dl. Tên game trong caption = tên trong dl.

### 4.4 Đăng (`tin_gia_mxh.py`)
Thứ tự (giống x_goc, `khong_ro` sau mốc có tác dụng phụ, KHÔNG bao giờ đăng lại khi khong_ro):
1. Chọn + tải ảnh + `dung.py` + `kiem.py` (phải đạt hết) + chữ + cổng → mọi lỗi trước bước 2 = KhongDang (thoát 3, ntfy ở pha thật).
2. `cong.giu_dang(ngay, dang, kenh, che_do, gio_du_kien, manifest_sha=sha256(dòng 1 chuẩn hoá))`; không giữ được → thoát 3. Ngay sau đó `cap_nhat_dang(id_tai=",".join(mã sản phẩm), id_container=<mã biến thể threads | "fb" | "ig">)`.
3. Chuẩn bị trên nền tảng (KHÔNG công khai):
   - fb: `fb.danh_tinh` khớp `dich.json` → start + rupload `video.mp4` → chờ xong; ghi `id_bai=<video_id>` (sổ) ngay khi có.
   - ig: `zernio.tai_tep` mp4 + jpg → URL công khai (kiểm 200 + content-type) → container REELS (`ig.tham_container(url, bia_url, caption, co_ai=False)`) → chờ FINISHED; ghi `id_bai=<container>`.
   - threads: `zernio.tai_tep` png → container IMAGE (`threads.tao_container_chu(tk, text, anh=url, topic_tag="PlayStation")` + `alt_text` — thêm tham số `alt_text=None` vào `tao_container_chu` nếu cần, tương thích ngược) → chờ FINISHED; ghi `id_bai=<container>`.
   - `trang_thai="chuan_bi_xong"`.
4. **thu**: fb finish `video_state=DRAFT` + đặt bìa (không công khai); ig/threads dừng ở container (không publish). Ghi `trang_thai="that_bai", loi="che do thu: da chuan bi <id>, khong dang"` (cho chạy thử lại), in caption + đường dẫn, chép `OUT/` + `caption.txt` + `chon.json` + `kiem.json` vào `RA_THU` (workflow upload artifact). Thoát 0.
5. **that**: ngủ tới giờ đăng (kiểm không quá T+15 phút) → `gia.kiem_lai(kiem_lai, gio_dang)` (giá đúng y) → sai thì `trang_thai="bo"`, ntfy, thoát 3 (container bỏ, FB video không finish) → công khai: fb finish `PUBLISHED` (`co_ai=False`) + bìa; ig `media_publish`; threads `threads_publish` → `da_dang` + `id_bai` + `link` (permalink) + `gio_cong_khai` → ntfy "Đã đăng …". Lỗi sau khi gọi công khai mà không chứng minh được chưa đăng → `khong_ro`.
6. Mọi URL Zernio, token che khỏi log (`chung.dang_ky_bi_mat`).

### 4.5 Workflow `.github/workflows/tin-gia-mxh.yml`
Mẫu `x-goc.yml`: `workflow_dispatch` inputs `kenh` (fb|ig|threads), `che_do` (thu|that, mặc định thu), `ngay`; `if: github.ref == 'refs/heads/main'`; cổng `SG_KENH_BAT` (mục riêng khuôn); concurrency `tin-gia-${{ inputs.kenh }}-${{ inputs.che_do }}`; checkout repo + repo riêng tư `kenh-game-du-lieu` (DATA_DEPLOY_KEY, sparse: `du-lieu`, `deal_diem.py`, `video/tai-san/am-thanh`, `video/tai-san/nhac`); python 3.13; node 22 + `npm ci` trong `cong-cu` + Playwright chromium (cache như x-goc); `sudo apt-get install -y ffmpeg`; env: SG_CONG_KHOA, ZERNIO_KHOA, NTFY_TIN, NTFY_BAO_LOI, GH_TOKEN (da_noi_bat), SG_KENH_BAT, DU_LIEU_REPO; chạy `python -m dang.tin_gia_mxh --kenh … --ngay … --che-do …`; thu: `actions/upload-artifact` thư mục `RA_THU` (retention 7 ngày); bước báo lỗi như x-goc. `timeout-minutes: 75` (chờ tới giờ đăng ≤ 40 phút).

### 4.6 Test (`dang/tests/test_tin_gia_mxh.py`, không mạng)
Hàng sg_keo mẫu chép từ dữ liệu thật 02/11 (Monster Hunter Rise, FF Type-0/XV Royal/XII/VII Rebirth, Resident Evil ×4, Outward…) + trang giả: fb chọn MH Rise (5 store, US rẻ nhất 180.000, rẻ hơn SG 150.000); FF chỉ có store Mỹ mua được → fb bỏ, ig chọn nhóm FF; threads ra cặp cùng giá; trùng `da_noi_bat` thì bỏ; giá trang lệch → bỏ; endTime < +24 h → bỏ; quy_vnd ra vnd khác `gia_vung` → bỏ; cổng tin giá chặn dòng 1 có "500 nghìn" không phải giá đã kiểm; caption không URL, hashtag đúng trần; threads ≤ 500 byte và câu mở không lặp 7 ngày; luồng đăng với cong/nền tảng giả: thu không gọi publish, that gọi publish đúng 1 lần, lỗi sau publish → khong_ro, giu_dang thất bại → không gọi nền tảng; cổng: `SG_KENH_BAT` rỗng, `"youtube"`, `"fb,ig"`, `"top5:youtube,flagship:tiktok"` → cả 3 khuôn TẮT (pha thật thoát sạch, không giữ sổ, không gọi nền tảng); `"top5:youtube,fb-gia:fb"` → chỉ fb-gia bật; khoảng trắng quanh mục vẫn nhận.
Chạy: `uv run --frozen python -m pytest dang/tests khuon cong-cu -q; echo exit=$?` (KHÔNG pipe qua tail).

## 5. Xong nghĩa là
- PR gộp vào main (squash), check `test` SUCCESS.
- Chạy thử CI `tin-gia-mxh.yml che_do=thu` cho từng kênh: kiem.py đạt hết, fb tạo DRAFT, ig/threads tạo container FINISHED, sổ sg_dang `che_do=thu` có dòng, artifact có video/ảnh + caption; Hào xem bài thử từng kênh.
- `SG_KENH_BAT` chưa có mục `fb-gia:fb` / `ig-gia:ig` / `threads-gia:threads` (3 khuôn tắt); không tạo lịch cron-job.org.


## BỔ SUNG OPUS (02/11 ~14:30, đè lên mục 1–4 khi khác)
1. `cong.doc_keo` (sg-cong v11–v13) CHỈ trả các cột `ngay,hang,ma,ten,vung_re_nhat,gia_vnd,gia_goc_vnd,giam,han,meo,link,gia_vung,lech_gia,da_kiem_trang` — KHÔNG có `nen_tang` (đã lọc 'ps'), `diem`, `anh`, `nong`. Mọi chỗ kế hoạch nói "tổng diem" → dùng `hang` nhỏ hơn = ưu tiên. Ảnh lấy từ trang PS Store (`gia_trang.media`), không từ `anh`.
2. Supabase ĐÃ SẴN (Opus làm 02/11 14:20): CHECK `sg_dang_dang_check` có `fb-gia`, `ig-gia`, `threads-gia`; edge `sg-cong` bản 13 nhận 3 giá trị đó (kiểm: doc_dang/doc_keo 200, dang lạ 400).
3. Nhạc nền ĐÃ SẴN ở repo riêng tư `kenh-game-du-lieu` (PR #10 gộp, fe75c9f): `video/tai-san/nhac/nhac-{a,c,d,e}.mp3` (120 BPM, nhịp khớp lưới 1 giây). Máy chọn theo ngày: `["a","c","d","e"][ngay.toordinal() % 4]`; thiếu tệp → dùng tệp có sẵn đầu tiên theo thứ tự; không có tệp nào → KhongDang. Tiếng động: `video/tai-san/am-thanh/*.mp3`.
4. Tên game trong CHỮ ĐĂNG (caption/Threads): đổi từ viết HOA toàn bộ sang dạng thường đọc được: từ viết HOA dài > 3 ký tự → Viết Hoa Chữ Đầu, giữ số La Mã (II, III, IV, VII, XII, XV, XVI…) và từ ≤ 3 ký tự (HD, PS4, RE); bỏ ™®©, bỏ đuôi nền tảng (`chung.bo_duoi_nen_tang`). Ví dụ "FINAL FANTASY VII REBIRTH" → "Final Fantasy VII Rebirth". Trong VIDEO/ẢNH giữ tên HOA như bản phác.
5. Threads — biến thể câu (mỗi bài viết lại theo biến thể, số chèn đúng chỗ; không lặp câu mở trong 7 ngày, đọc các dòng sg_dang `threads-gia` 7 ngày, mã biến thể lưu ở `id_container` dạng `m<i>-k<j>`):
   Mở: m0 "Có {N}, anh em chọn {A} hay {B}?" · m1 "{N} trong túi: {A} hay {B}, chọn game nào?" · m2 "Cùng {N}, mua {A} hay {B}?" · m3 "Ngân sách {N} thì nên lấy {A} hay {B}?" · m4 "Hai game cùng {N}: {A} và {B}. Bạn chọn bên nào?"
   Kết (sau câu tài khoản): k0 "Bạn chọn bản nào, vì sao?" · k1 "Anh em nghiêng về bên nào?" · k2 "Nếu là bạn thì lấy game nào trước?" · k3 "Ai chơi rồi thấy game nào đáng tiền hơn?"
   Thân: cùng vùng + cùng giá gốc tiền tệ → "Cả hai đang {giá} ở PS Store {vùng} (giảm {g}%) tới {HH:MM} ngày {d/m}, {thẻ} là vừa khít, khoảng {N}." ; khác → hai vế "{A} {giá A} ở Store {vùng A}, {B} {giá B} ở Store {vùng B}, đều tới…" (bỏ % nếu khác nhau). Lý do: "Mình chọn {X}: {luot} người chấm, trung bình {sao} sao{, lại là bản PS5 nếu X là PPSA còn bên kia CUSA}." hoặc khi chọn theo sao: "Mình chọn {X}: {sao} sao so với {sao_kia} của {Y}." Số `{N}` dạng "460 nghìn" (dùng `x_goc._nghin`).
   Quá 450 ký tự / 500 byte → rút tên game (bỏ đuôi edition chuẩn như `x_goc.ten_ngan`), rồi bỏ cụm "khoảng {N}", rồi bỏ "(giảm g%)"; vẫn quá → bỏ cặp, thử cặp kế.
6. Ngủ chờ giờ đăng: dùng `chung.ngu` (test thay được). Chuẩn bị xong mà còn > 45 phút tới giờ đăng (vd chạy tay sớm ở pha thật) → KhongDang "chạy quá sớm" (không giữ runner quá lâu), TRƯỚC giu_dang.
7. Artifact chạy thử: `RA_THU` = `${{ runner.temp }}/ra-thu` ; workflow upload với tên `tin-gia-<kenh>-<ngay>` khi `che_do == 'thu'` (kể cả khi bước script thất bại: `if: always() && inputs.che_do == 'thu'`), `if-no-files-found: warn`, retention 7 ngày.
8. Chế độ thu trên CI phải đi tới bước chuẩn bị trên nền tảng (fb DRAFT, ig/threads container) để chứng minh đường API; cờ `--khong-api` (chỉ dùng trên Mac) dừng sau kiem + chữ, không giữ sổ, không gọi nền tảng.
9. Bìa FB khi `che_do=thu`: dùng `fb._dat_bia` sau finish DRAFT (như `fb.chuan_bi`).
10. CỔNG BẬT ĐỔI (điều phối 02/11 ~14:40: TikTok tin giá đã bật bằng `SG_KENH_BAT=top5:youtube,flagship:tiktok`; "muốn cộng kênh mới thì thêm mục ,<khuôn>:<kênh>"): BỎ biến `SG_TIN_GIA_BAT`. Pha thật chỉ chạy khi biến repo `SG_KENH_BAT` có ĐÚNG mục riêng khuôn `<dang>:<kenh>` (`fb-gia:fb`, `ig-gia:ig`, `threads-gia:threads`; tách phẩy, bỏ khoảng trắng). Mục chung không có dấu ':' (vd "youtube") KHÔNG bật khuôn này. Chặn ở CẢ workflow (`contains(format(',{0},', vars.SG_KENH_BAT), format(',{0}-gia:{0},', inputs.kenh))` — chú ý vars có thể có khoảng trắng: script là chốt chặn chính) lẫn script (env `SG_KENH_BAT`). Hiện biến = `top5:youtube,flagship:tiktok` ⇒ 3 khuôn mới TẮT. Viết hàm đọc RIÊNG (chỉ nhận mục có ':'), KHÔNG gọi lại `dang.chay.doc_kenh_bat` (hàm đó rơi về mục chung: `SG_KENH_BAT="youtube"` sẽ trả {youtube} cho dang lạ). Test bắt buộc: "", "youtube", "fb,ig", "top5:youtube,flagship:tiktok" → cả 3 tắt; " top5:youtube , fb-gia:fb " → chỉ fb-gia bật; "fb-gia:ig" → fb-gia TẮT (sai kênh).
11. Thuật ngữ (Hào 02/11): "loại nội dung thắng ở kênh X", bảng luật đổi tên `CHUNG/LOAI-THANG-THEO-KENH.json` (KENH-THANG.json còn là lối tắt). Ghi chú trong code/doc dùng cách gọi này.
12. Khớp máy kiểm của điều phối (`~/Kho-luu/chuyen-gia-nen-tang/CHUNG/cong-cu/kiem-khuon.py --loai sg-fb-gia|sg-ig-gia|sg-threads-gia`, 02/11): fb/ig dòng 1 có tiền VNĐ; không URL/tên miền (.com/.vn/.net…); hashtag fb ≤ 3, ig ≤ 5; không xin tương tác (like/follow/share/tag/bình luận/tặng); `giong_ai=false`; video 1080×1920, 10–15 s, có nhạc; **caption FB ≤ 600 ký tự**. threads: ≤ 500 ký tự; **dòng 1 là câu hỏi** (kết bằng "?") có tiền VNĐ; **câu cuối là câu hỏi** (kết bằng "?"); 0 hashtag, 0 URL; `topic_tag="PlayStation"`; ảnh 1080×1350. `tin_gia_chu.py` phải tự kiểm đúng các luật này (fail-closed) và ghi `bai.json` {"kenh","loai","chu","video"|"anh","giong_ai":false,"topic_tag"?} vào thư mục ra để Opus chạy được kiem-khuon trên Mac.

## SỬA SAU SOI SOL (lượt 1, 02/11 ~14:45 — GPT-6.1 Sol qua `codex exec`; Opus đã đối chiếu từng điểm với code). MỤC NÀY ĐÈ LÊN MỌI MỤC TRÊN.
S1 (P1) `doc_keo` không có `nen_tang`, `diem`, `anh` → đã sửa ở BỔ SUNG 1. Test dùng ĐÚNG hình JSON edge trả (14 cột liệt kê ở BỔ SUNG 1), không thêm trường.
S2 (P1) `kiem_lai` dùng đúng schema `dang/gia.py`: mỗi mục `{"ten","pid","loc","gia_cuc_bo": <float giá trang>,"endTime": "<ms>","gia_dung_y": true}` (pid = phần cuối URL sản phẩm, loc = "en-us"…). Test: giá đổi 0,01 → bị chặn.
S3 (P1) FB: kiểm trang của MỌI store hiện trong video. Từ 02/11 (kenh-game-du-lieu PR #11, fe…) mỗi ô `gia_vung[ma]` có `link` trang đúng vùng. Với từng store `mua_duoc && cach=='the' && !chi_plus` CÓ `link`: tải trang (`gia_trang.khoi_gia(html,pid)`), giá trang == `gia_vung[ma].gia` (±0,011, đúng tiền tệ), endTime có và ≥ giờ đăng + 24 h, `quy_vnd` trên giá trang ra `cach=='the'`, `mua_duoc`, `vnd == gia_vung[ma].vnd`. Store trượt → BỎ khỏi bảng (ghi lý do vào chon.json). Cần ≥ 3 store đạt, gồm store rẻ nhất; thứ hạng, `re_hon` (= đắt nhất − rẻ nhất trong các store ĐẠT) tính từ store đạt. Mọi store hiện ra đều vào `kiem_lai` (kiểm lại trước giờ đăng). Thiếu `link` → coi như trượt. Trần tải trang FB: 6/ứng viên, 18/lượt.
S4 (P1) Một giá chuẩn: `hang.gia_vnd == gia_vung[vung_re_nhat].vnd == quy_vnd(giá trang).vnd == dl.gia_vnd` (fb), tương tự từng game ig/threads. Lệch → bỏ game. Test làm lệch `hang.gia_vnd`.
S5 (P1) Trường chung: IG — `giam_chung` chỉ khi mọi game cùng % giảm, `vung_chung` chỉ khi cùng vùng (khác vùng → mỗi dòng hiện cờ vùng của game đó, dl thêm `game[i].ma_vung` đã có), `han_chu` = hạn SỚM NHẤT và dl thêm `han_khac: true` khi các hạn lệch nhau > 60 s (khuôn hiện "Hết giảm sớm nhất …"). Threads — CHỈ ghép cặp khi hai game cùng vùng, cùng chuỗi giá trang, cùng tổ hợp thẻ, cùng endTime (±60 s); không thì bỏ cặp.
S6 (P1) Caption FB: dòng 1 CHỈ có giá mua ("… còn 180 nghìn ở Store Mỹ: …"); câu "rẻ hơn Store X M nghìn" chuyển xuống dòng 2. Cổng theo vai trò: tiền VNĐ dòng 1 ⊆ giá mua đã kiểm; mọi tiền VNĐ toàn caption ⊆ (giá mua đã kiểm ∪ {re_hon}), và re_hon phải = phép trừ của hai giá đã kiểm. Giữ ca test "180 nghìn + 150 nghìn ở dòng 1 → trượt".
S7 (P1) Đua chọn trùng game: (a) workflow concurrency pha thật DÙNG CHUNG cho 3 kênh: `group: tin-gia-that` (pha thu: `tin-gia-thu-${{ inputs.kenh }}`); (b) sau `giu_dang` + ghi `id_tai`, đọc lại sg_dang cùng ngày ±3 ngày: có dòng KHÁC (dang ∈ fb-gia/ig-gia/threads-gia/x-goc, trạng thái ∉ that_bai/bo, cùng che_do) trùng mã game với mình và `luc` sớm hơn → nhả dòng của mình (`trang_thai="that_bai"`, `loi="trung game voi <dang>"`) và dừng TRƯỚC mọi thao tác nền tảng. `khong_ro` vẫn tính là đã dùng game.
S8 (P1) `da_noi_bat` fail-closed: `nb.canh_bao` khác rỗng (không đọc được lịch sử Release) → KhongDang. Phân biệt "đọc được, rỗng" với "không đọc được".
S9 (P1) Thuế: mọi câu thẻ dùng chữ "vừa khít với giá niêm yết"/"khoảng" — KHÔNG "là đủ"; caption FB/IG/Threads có cụm "Giá niêm yết, chưa gồm thuế nếu có." (FB/IG dòng cuối trước hashtag; Threads ghép vào câu tài khoản nếu còn chỗ, không thì bỏ "(giảm g%)" trước). Khuôn FB (worker A): dòng nhỏ dưới "= 180.000đ" thành "giá niêm yết $4,79 · dư $0,21 trong ví".
S10 (P2) IG gom nhóm: khoá IP = 2 từ đầu của tên đã chuẩn hoá (bỏ ™®©, chữ thường, bỏ dấu câu) — KHÔNG dùng `dong_game` (gộp RE2/RE3/RE4 làm một). Bỏ trùng SẢN PHẨM theo title id (`PPSA…_00`/`CUSA…_00` trong `ma` trước '|' và trong pid) — cùng title id = cùng game (bản thường vs bản gói) → giữ hàng `hang` nhỏ hơn.
S11 (P2) Cổng số theo bộ: kiểm từng bộ (tên game ↔ giá VNĐ) trong caption IG/Threads (đảo giá hai game → trượt). Caption KHÔNG dùng dạng "K" (chỉ "nghìn"/"triệu"); cổng trượt nếu caption có `\d+\s*[kK]\b`.
S12 (P2) Không truyền dòng sg_dang vào `fb.cong_khai`/`ig.cong_khai`/`threads.cong_khai` (chúng đọc id_tai/id_container theo quy ước cũ). Viết hàm công khai riêng trong `tin_gia_mxh.py` nhận ID Graph trực tiếp (có thể gọi lại `fb.finish/_dat_bia/_doc_status`, `meta.goi`); ID Graph lưu ở `id_bai`; `id_tai` = mã game, `id_container` = mã biến thể. Test: đúng ID được gửi, mã game không bị ghi đè (kể cả nhánh FB upload lại).
S13 (P2) Đối chiếu tài khoản đích với `dich.json` cho CẢ 3 kênh (như `chay.kiem_danh_tinh`) TRƯỚC khi tạo tài nguyên.
S14 (P2) Threads câu mở: 8 biến thể (m0–m7) và kiểm 7 ngày (đọc sg_dang `threads-gia` 7 ngày, mọi trạng thái trừ that_bai/bo); hết biến thể → KhongDang. Thêm m5 "Túi còn {N}, chọn {A} hay {B} cho tuần này?" · m6 "{N} mua được một game: {A} hay {B}?" · m7 "Đang phân vân giữa {A} và {B}, cùng giá {N}, bạn chọn gì?".
S15 (P2) Bảng trạng thái sau giữ sổ: lỗi chắc chắn TRƯỚC mọi tác dụng phụ nền tảng → `cap_nhat_dang(neu_trang_thai="dang_dang", trang_thai="that_bai")`; lỗi sau khi tạo tài nguyên (upload/container) nhưng CHƯA gọi công khai → `that_bai` (cho chạy lại; tài nguyên mồ côi không công khai); lỗi khi/sau gọi công khai mà không chứng minh được chưa đăng → `khong_ro` (không bao giờ đăng lại). Runner bị huỷ → dòng kẹt `dang_dang`: ghi trong README cách Opus đối soát tay, máy KHÔNG tự đổi.
S16 (P2) Hạn tuyệt đối: một `han_cong_khai = gio_dang + 15 phút`; mọi bước mạng sau giờ đăng (kiem_lai, publish) kiểm còn hạn ngay TRƯỚC request công khai; quá → `that_bai` (chưa công khai) + ntfy.
S17 (P2) FB: sau finish PUBLISHED đọc lại trạng thái (`published` true hoặc publishing_phase complete, tối đa ~3 phút) mới `da_dang`; chưa xác nhận → `khong_ro`. IG/Threads: có media id trả về (hoặc đọc lại container `PUBLISHED`) → `da_dang` dù thiếu permalink.
S18 (P3) Lệnh test giữ mã thoát: `uv run --frozen python -m pytest dang/tests khuon cong-cu -q; e=$?; echo exit=$e`.
