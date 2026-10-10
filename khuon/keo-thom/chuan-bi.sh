#!/bin/bash
# D1+D2: chon 1 keo + viet loi doc cho ngay DANG (che do tu dong, cung quy uoc voi khuon/top5/chuan-bi.sh).
# Ra: keo.json, loi-dang.json, ket-qua-chon.json, kich-ban.json, loi.txt (danh sach goi cho workflow: chon-ra.txt).
# Thoat 3 = khong chon duoc keo dat dieu kien -> BO KHUNG (workflow ntfy). Bien: NGAY (YYYY-MM-DD, ngay DANG), DU_LIEU_REPO (thu muc checkout kenh-game-du-lieu), CHUAN_BI_PY.
set -euo pipefail
M="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$M/../.." && pwd)"
if [ -n "${CHUAN_BI_PY:-}" ]; then PY=("$CHUAN_BI_PY"); else PY=(uv run -q --frozen --project "$ROOT" python); fi   # CI: job chon dung python3 he thong (chi stdlib)
cd "$M"
"${PY[@]}" chon-keo.py ${DU_LIEU_REPO:+--repo "$DU_LIEU_REPO"} ${NGAY:+--ngay "$NGAY"}
"${PY[@]}" kich-ban.py
