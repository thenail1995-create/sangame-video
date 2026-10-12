#!/bin/bash
# Dung Keo thom v9 3 ban theo nen tang + kiem. DAU VAO phai co san (xem NHAT-KY GD D):
#   keo.json (chon-keo.py) · kich-ban.json + loi.txt (kich-ban.py) · dau-vao/giong.mp3 (cong-cu/giong.py hoac el.py) · am-thanh/ (lay-tai-san.sh)
#   · trailer: dau-vao/trailer/*.mp4 (neu khong co, nen08.py tai tu keo.json)
# Thu tu v9: can chu (Whisper) -> trang that + do khung/neo.json (moc theo khoa doan) -> nen trailer TU CHON -> (lop -> ghep -> xoa) x 3 -> tieng -> bia -> kiem.
# HOI_QUY=1: dung moc-chu.json co san (mau Spider-Man 2 v8.3, da gan khoa doan bang hoi-quy/gan-doan.py) — bo buoc can chu.
# Lop alpha dung -> ghep -> XOA tung ban (~4,9 GB/ban; may GitHub co ~14 GB trong).
# GD=chung | GD=ban BAN=<nt> | (de trong = tuan tu ca hai nhu cu) — xem cong-cu/chay-chung.sh. CI: job `chung` roi 3 job `ban` song song.
M="$(cd "$(dirname "$0")" && pwd)"; . "$M/../../cong-cu/chay-chung.sh"
cd "$M"
if la_chung; then
  # LIVE=1 (workflow tu dong, cung quy uoc voi Top 5): chon keo + loi (chuan-bi.sh) va thu giong (cong-cu/giong.py) neu chua co. LIVE khac => dau vao co san (fixture/thu tay).
  if [ "${LIVE:-0}" = 1 ]; then
    if [ ! -f keo.json ] || [ ! -f kich-ban.json ]; then bash "$M/chuan-bi.sh"; moc "chon keo + loi"; fi
    if [ ! -f dau-vao/giong.mp3 ]; then mkdir -p dau-vao; "${PY[@]}" "$ROOT/cong-cu/giong.py" giong --loi-file loi.txt --ra dau-vao/giong.mp3 --du-an san-game --dang "${DANG:-keo-thom}"; moc "giong"; fi
  fi
  for f in keo.json kich-ban.json dau-vao/giong.mp3; do [ -f "$f" ] || { echo "THIEU $f"; exit 2; }; done
  if [ -z "${HOI_QUY:-}" ]; then
    "${PY[@]}" can-chu.py | tail -4;          moc "can chu (Whisper)"
  fi
  [ -f dau-vao/moc-chu.json ] || { echo "THIEU dau-vao/moc-chu.json"; exit 2; }
  "${PY[@]}" dung.py build tiktok && node do-khung.cjs tiktok; moc "khung cham + neo.json"
fi
case "$GD" in
chung)   # CHI phan KHONG phu thuoc ban: chon doan nen, tron tieng, KIEM SOM. Khong ma hoa nen / khong chup lop chu.
  "${PY[@]}" nen08.py chon | tail -3;         moc "chon doan nen trailer"
  "${PY[@]}" am08.py | tail -1;               moc "tieng (chua ghep)"
  chay_kiem_som ;;
ban)     # MOT ban (BAN): nen -> lop chu -> ghep hinh -> ghep tieng -> bia -> kiem day du
  NEN_DUNG_LAI=1 "${PY[@]}" nen08.py "$BAN" | tail -3; moc "nen trailer $BAN"
  "${PY[@]}" dung.py lop "$BAN";              moc "lop chu $BAN"
  "${PY[@]}" ghep08.py "$BAN"; rm -f "$M/lop-$BAN.mov"; moc "ghep hinh $BAN (xoa lop)"
  "${PY[@]}" "$ROOT/cong-cu/ghep_am.py" "$M" am08.wav; moc "ghep tieng $BAN"
  "${PY[@]}" dung.py bia "$BAN" | tail -1;    moc "bia"
  chay_kiem ;;
*)       # tat-ca: tuan tu nhu cu (co BAN thi chi dung ban do)
  "${PY[@]}" nen08.py "${BAN:-tat-ca}" | tail -3; moc "nen trailer ${BAN:-3 ban}"
  for nt in "${NTS[@]}"; do
    "${PY[@]}" dung.py lop "$nt";             moc "lop chu $nt"
    "${PY[@]}" ghep08.py "$nt"; rm -f "$M/lop-$nt.mov"; moc "ghep hinh $nt (xoa lop)"
  done
  "${PY[@]}" am08.py | tail -1;               moc "tieng + ghep ${BAN:-3 ban}"
  "${PY[@]}" dung.py bia "${BAN:-tat-ca}" | tail -1;    moc "bia"
  chay_kiem ;;
esac
