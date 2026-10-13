#!/bin/bash
# Dung Tin nhanh 3 ban theo nen tang + kiem (A5, C1-C3). Hai che do:
#  * NGUON_DU_LIEU=<thu muc checkout kenh-game-du-lieu> + NGAY=<ngay DANG YYYY-MM-DD> (may dung hang ngay 21:00): chon-tin -> sinh-tin -> kich-ban -> giong -> ...
#      ma thoat 3 = KHONG DU 3 TIN, 4 = DU LIEU CU (ghi bo-khung.txt; workflow bo khung + ntfy, KHONG phai loi may), 5 = thieu giong (khong co giong.py / chua thu giong).
#  * khong dat NGUON_DU_LIEU (fixture A2/A6, hoac Mac da co san tin.json + giong.mp3 + loi-dang.json + kiem-lai.json): bo qua buoc chon/sinh.
# Dau vao (lay-tai-san.sh dat san o che do fixture): tin.json, kich-ban.json, dau-vao/giong.mp3 (+ moc-chu.json cua Mac de so K14), tai-san/, am-thanh/.
# Lop alpha: dung -> ghep -> XOA tung ban (~4,9 GB/ban).
# GD=chung | GD=ban BAN=<nt> | (de trong = tuan tu ca hai nhu cu) — xem cong-cu/chay-chung.sh. CI: job `chung` roi 3 job `ban` song song.
M="$(cd "$(dirname "$0")" && pwd)"; . "$M/../../cong-cu/chay-chung.sh"
cd "$M"
if la_chung; then
  if [ -n "${NGUON_DU_LIEU:-}" ]; then
    : "${NGAY:?can NGAY (ngay DANG YYYY-MM-DD)}"
    rm -f "$M/bo-khung.txt" "$M/tin.json" "$M/tin-chon.json" "$M/loi.txt" "$M/kich-ban.json"
    rc=0; "${PY[@]}" chon-tin.py --du-lieu "$NGUON_DU_LIEU" --ngay-dang "$NGAY" > "$M/chon-tin.log" 2>&1 || rc=$?
    cat "$M/chon-tin.log"
    if [ "$rc" = 3 ] || [ "$rc" = 4 ]; then cp "$M/chon-tin.log" "$M/bo-khung.txt"; moc "chon tin -> BO KHUNG (ma $rc)"; exit "$rc"; fi
    [ "$rc" = 0 ] || exit "$rc"
    moc "chon tin"
    "${PY[@]}" sinh-tin.py | tee -a "$DO";     moc "sinh tin.json + trailer.json"
    "${PY[@]}" kich-ban.py | tail -2;          moc "kich ban"
    mkdir -p dau-vao; LOI_SHA="$(shasum -a 256 loi.txt | cut -d' ' -f1)"
    if [ ! -s dau-vao/giong.mp3 ] || [ "$(cat dau-vao/giong.sha 2>/dev/null)" != "$LOI_SHA" ]; then
      rm -f dau-vao/giong.mp3 dau-vao/giong.sha dau-vao/moc-chu.json                    # giong cua ngay khac / loi khac KHONG duoc dung lai
      [ -f "$ROOT/cong-cu/giong.py" ] || { echo "THIEU giong: khong co dau-vao/giong.mp3 khop loi.txt va khong co cong-cu/giong.py"; exit 5; }
      "${PY[@]}" "$ROOT/cong-cu/giong.py" giong --loi-file loi.txt --ra dau-vao/giong.mp3 --du-an san-game --dang tin-nhanh
      echo "$LOI_SHA" > dau-vao/giong.sha;       moc "giong"
    fi
  else
    if [ -f dau-vao/moc-chu.json ]; then cp dau-vao/moc-chu.json dau-vao/moc-chu.mac.json; fi
  fi
  can_chu_tu_sua du_phong;                    moc "can chu (Whisper) + kiem moc"      # Tin nhanh chi co 1 cach -> kiem moc chi BAO
  if [ -f dau-vao/moc-chu.mac.json ]; then "${PY[@]}" "$ROOT/cong-cu/so-moc.py" dau-vao/moc-chu.mac.json dau-vao/moc-chu.json 0.08 | tee -a "$DO"; fi
fi
case "$GD" in
chung)   # CHI phan KHONG phu thuoc ban: chon doan nen, khung cham, tron tieng, KIEM SOM. Khong ma hoa nen / khong chup lop chu.
  "${PY[@]}" nen-tin.py chon | tail -4;       moc "chon doan nen trailer"
  "${PY[@]}" dung.py build tiktok && node do-khung.cjs tiktok; moc "khung cham"
  "${PY[@]}" am-tin.py | tail -1;             moc "tieng (chua ghep)"
  chay_kiem_som ;;
ban)     # MOT ban (BAN): nen -> lop chu -> ghep hinh -> ghep tieng -> bia -> kiem day du
  NEN_DUNG_LAI=1 "${PY[@]}" nen-tin.py "$BAN" | tail -4; moc "nen trailer $BAN"
  "${PY[@]}" dung.py lop "$BAN";              moc "lop chu $BAN"
  "${PY[@]}" dung.py hinh "$BAN"; rm -f "$M/lop-$BAN.mov"; moc "ghep hinh $BAN (xoa lop)"
  "${PY[@]}" "$ROOT/cong-cu/ghep_am.py" "$M" am.wav; moc "ghep tieng $BAN"
  "${PY[@]}" dung.py bia "$BAN" 1.6 | tail -1; moc "bia"
  chay_kiem ;;
*)       # tat-ca: tuan tu nhu cu (co BAN thi chi dung ban do)
  "${PY[@]}" nen-tin.py "${BAN:-tat-ca}" | tail -4; moc "nen trailer ${BAN:-3 ban}"
  for nt in "${NTS[@]}"; do
    "${PY[@]}" dung.py lop "$nt";             moc "lop chu $nt"
    "${PY[@]}" dung.py hinh "$nt"; rm -f "$M/lop-$nt.mov"; moc "ghep hinh $nt (xoa lop)"
  done
  "${PY[@]}" dung.py build tiktok && node do-khung.cjs tiktok; moc "khung cham"
  "${PY[@]}" am-tin.py | tail -1;             moc "tieng + ghep ${BAN:-3 ban}"
  "${PY[@]}" dung.py bia "${BAN:-tat-ca}" 1.6 | tail -1; moc "bia"
  chay_kiem ;;
esac
