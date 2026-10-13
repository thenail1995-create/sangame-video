#!/bin/bash
# Phan dung chung cua chay.sh moi khuon (source file nay). Dat: ROOT, M (thu muc khuon), PY, ham moc, do tai nguyen.
#  - PY = moi truong Python KHOA cho MOI buoc (uv.lock; A4)
#  - moc "ten buoc"  : ghi thoi gian tung buoc vao do-thoi-gian.txt
#  - do RAM/dia dinh : cong-cu/do-tai-nguyen.py chay nen, ghi tai-nguyen.txt khi thoat
# KHONG dung '|| true' quanh bo kiem (A5, Sol #23): loi thi chay.sh thoat khac 0.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# MG_SCRIPTS: thu muc co capture.mjs + node_modules/playwright. CI: cong-cu/ trong repo (sau npm ci). Mac chua npm ci -> bo trong, script tu dung skill motion-graphics cua may.
if [ -z "${MG_SCRIPTS:-}" ] && [ -d "$ROOT/cong-cu/node_modules/playwright" ]; then export MG_SCRIPTS="$ROOT/cong-cu"; fi
export PATH="$ROOT/cong-cu/bin:$PATH"                    # ffmpeg/ffprobe tinh neu co (CI)
PY=(uv run -q --frozen --project "$ROOT" python)
# GIAI DOAN (CI chia job dung thanh job `chung` + 3 job `ban` chay song song; Mac khong dat gi = tuan tu nhu cu):
#   GD=chung   : du lieu/giong/can chu/chon doan nen/khung cham/tieng dong + KIEM SOM (khong can hinh da ve). Ban nen tang (NTS) = ca 3.
#   GD=ban     : CHI mot ban (env BAN=tiktok|reels|shorts bat buoc): ma hoa nen, chup lop chu, ghep, bia, kiem day du cua ban do.
#   GD=tat-ca  : (mac dinh) ca hai tuan tu; co BAN thi chi dung ban do (phan chung van lam 1 lan).
GD="${GD:-tat-ca}"
case "$GD" in chung|ban|tat-ca) ;; *) echo "GD khong hop le: $GD (chung|ban|tat-ca)"; exit 2;; esac
NTS=(tiktok reels shorts)
if [ "$GD" != chung ] && [ -n "${BAN:-}" ]; then
  case "$BAN" in tiktok|reels|shorts) NTS=("$BAN");; *) echo "BAN khong hop le: $BAN (tiktok|reels|shorts)"; exit 2;; esac
fi
if [ "$GD" = ban ] && [ -z "${BAN:-}" ]; then echo "GD=ban can BAN=tiktok|reels|shorts"; exit 2; fi
export BAN="${BAN:-}" GD
la_chung(){ [ "$GD" != ban ]; }     # chay phan DUNG CHUNG (true khi GD=chung hoac tat-ca)
SUFFIX=""; [ "$GD" = tat-ca ] || SUFFIX="-$GD${BAN:+-$BAN}"
T0=$(date +%s); T1=$T0; DO="$M/do-thoi-gian$SUFFIX.txt"; : > "$DO"
moc(){ local n=$(date +%s); printf '%-34s %5d s  (tong %5d s)\n' "$1" $((n-T1)) $((n-T0)) | tee -a "$DO"; T1=$n; }
"${PY[@]}" "$ROOT/cong-cu/mo_hinh.py" | tee -a "$DO"
python3 "$ROOT/cong-cu/do-tai-nguyen.py" "$M/tai-nguyen$SUFFIX.txt" & TN_PID=$!
trap 'kill "$TN_PID" 2>/dev/null || true; wait "$TN_PID" 2>/dev/null || true; cat "$M/tai-nguyen$SUFFIX.txt" 2>/dev/null | tee -a "$DO" || true' EXIT
# chay_kiem: kiem ca 3 ban (moi ban 1 bao cao kiem-<nt>.json); tra ma != 0 neu BAT KY ban nao trượt/crash, nhung van chay het de co du bao cao
chay_kiem(){ local rc=0 nt; for nt in "${NTS[@]}"; do "${PY[@]}" "$M/kiem/kiem-tat-ca.py" "$M/video-$nt.mp4" "$nt" || rc=$?; moc "kiem $nt"; done; return $rc; }
# chay_kiem_som: KIEM SOM (GD=chung) - cac phep KHONG can hinh da ve (DOM chu tran/phu de/vung an toan, D1 D2 B6 ngay/ten du lieu, D3 noi dung nghe tren giong sach,
# giong vs tieng dong 6 dB, tieng khop khung cham). Truot -> ma != 0 -> job chung dung NGAY (khong chup lop chu). Bo kiem cuoi (chay_kiem) VAN chay lai ca nhom nay.
chay_kiem_som(){ local rc=0 nt; for nt in "${NTS[@]}"; do KIEM_SOM=1 "${PY[@]}" "$M/kiem/kiem-tat-ca.py" "$M/video-$nt.mp4" "$nt" || rc=$?; moc "kiem som $nt"; done; return $rc; }
. "$ROOT/cong-cu/tu-sua-moc.sh"        # can_chu_tu_sua: can chu -> kiem moc dau doan -> (lech) doi cach 1 lan (DOT 2a)
