#!/bin/bash
# Dung FLAGSHIP 3 ban theo nen tang + kiem (A5). Dau vao (lay-tai-san.sh dat san): flagship.json, cau-hinh.json, kich-ban.json, loi.txt, dau-vao/giong.mp3 (+ moc-chu.json cua Mac de so K14), tai-san/, am-thanh/.
# Lop alpha: dung -> ghep -> XOA tung ban (~4,9 GB/ban).
# GD=chung | GD=ban BAN=<nt> | (de trong = tuan tu ca hai nhu cu) — xem cong-cu/chay-chung.sh. CI: job `chung` roi 3 job `ban` song song.
M="$(cd "$(dirname "$0")" && pwd)"; . "$M/../../cong-cu/chay-chung.sh"
cd "$M"
if la_chung; then
  # LIVE=1 (B2): chon game + loi (chuan-bi.sh) + thu giong (cong-cu/giong.py) neu workflow/nguoi dung chua lam. LIVE khac => fixture (dau vao co san).
  if [ "${LIVE:-0}" = 1 ]; then
    if [ ! -f flagship.json ] || [ ! -f kich-ban.json ]; then bash "$M/chuan-bi.sh"; moc "chon game + loi"; fi
    if [ ! -f dau-vao/giong.mp3 ]; then mkdir -p dau-vao; "${PY[@]}" "$ROOT/cong-cu/giong.py" giong --loi-file loi.txt --ra dau-vao/giong.mp3 --du-an san-game --dang flagship; moc "giong"; fi
  fi
  if [ -f dau-vao/moc-chu.json ]; then cp dau-vao/moc-chu.json dau-vao/moc-chu.mac.json; fi
  can_chu_tu_sua neo_doan cum_cau du_phong;   moc "can chu (Whisper) + kiem moc"      # cong-cu/tu-sua-moc.sh: kiem moc dau doan, lech thi doi cach 1 lan
  so_moc_voi_mac                              # cong-cu/tu-sua-moc.sh: bo qua khi tu sua da doi cach
fi
case "$GD" in
chung)   # CHI phan KHONG phu thuoc ban: chon doan nen, khung cham, tron tieng, KIEM SOM. Khong ma hoa nen / khong chup lop chu.
  "${PY[@]}" nen-flagship.py chon | tail -3;      moc "chon doan nen trailer"
  "${PY[@]}" dung.py build tiktok && node do-khung.cjs tiktok; moc "khung cham"
  "${PY[@]}" am-flagship.py | tail -1;            moc "tieng (chua ghep)"
  chay_kiem_som ;;
ban)     # MOT ban (BAN): nen -> lop chu -> ghep hinh -> ghep tieng -> bia -> kiem day du
  NEN_DUNG_LAI=1 "${PY[@]}" nen-flagship.py "$BAN" | tail -3; moc "nen trailer $BAN"
  "${PY[@]}" dung.py lop "$BAN";              moc "lop chu $BAN"
  "${PY[@]}" dung.py hinh "$BAN"; rm -f "$M/lop-$BAN.mov"; moc "ghep hinh $BAN (xoa lop)"
  "${PY[@]}" "$ROOT/cong-cu/ghep_am.py" "$M" am.wav; moc "ghep tieng $BAN"
  "${PY[@]}" dung.py bia "$BAN" 2.2 | tail -1; moc "bia"
  chay_kiem ;;
*)       # tat-ca: tuan tu nhu cu (co BAN thi chi dung ban do)
  "${PY[@]}" nen-flagship.py "${BAN:-tat-ca}" | tail -3; moc "nen trailer ${BAN:-3 ban}"
  for nt in "${NTS[@]}"; do
    "${PY[@]}" dung.py lop "$nt";             moc "lop chu $nt"
    "${PY[@]}" dung.py hinh "$nt"; rm -f "$M/lop-$nt.mov"; moc "ghep hinh $nt (xoa lop)"
  done
  "${PY[@]}" dung.py build tiktok && node do-khung.cjs tiktok; moc "khung cham"
  "${PY[@]}" am-flagship.py | tail -1;            moc "tieng + ghep ${BAN:-3 ban}"
  "${PY[@]}" dung.py bia "${BAN:-tat-ca}" 2.2 | tail -1; moc "bia"
  chay_kiem ;;
esac
