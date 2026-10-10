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
T0=$(date +%s); T1=$T0; DO="$M/do-thoi-gian.txt"; : > "$DO"
moc(){ local n=$(date +%s); printf '%-34s %5d s  (tong %5d s)\n' "$1" $((n-T1)) $((n-T0)) | tee -a "$DO"; T1=$n; }
"${PY[@]}" "$ROOT/cong-cu/mo_hinh.py" | tee -a "$DO"
python3 "$ROOT/cong-cu/do-tai-nguyen.py" "$M/tai-nguyen.txt" & TN_PID=$!
trap 'kill "$TN_PID" 2>/dev/null || true; wait "$TN_PID" 2>/dev/null || true; cat "$M/tai-nguyen.txt" 2>/dev/null | tee -a "$DO" || true' EXIT
NTS=(tiktok reels shorts)
# chay_kiem: kiem ca 3 ban (moi ban 1 bao cao kiem-<nt>.json); tra ma != 0 neu BAT KY ban nao trượt/crash, nhung van chay het de co du bao cao
chay_kiem(){ local rc=0 nt; for nt in "${NTS[@]}"; do "${PY[@]}" "$M/kiem/kiem-tat-ca.py" "$M/video-$nt.mp4" "$nt" || rc=$?; moc "kiem $nt"; done; return $rc; }
