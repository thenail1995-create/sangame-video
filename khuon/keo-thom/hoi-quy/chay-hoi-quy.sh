#!/bin/bash
# HOI QUY D3 (bat buoc truoc khi lam game moi): dung khuon v9 voi mau Spider-Man 2 (giong + moc chu cu) o thu muc RIENG ngoai cay git,
# roi so voi video v8.3 dung tu CUNG fixture (anh 6 moc: SSIM 135x240 >= 0,97, ghi ca 270x480; cue tieng tung cu; kiem-tat-ca 3 ban DAT het).
#   bash chay-hoi-quy.sh <thu-muc-chay> <kenh-game-du-lieu> <thu-muc-nang: co video/fixture/keo-thom-v83/dau-vao/trailer/*.mp4> [thu-muc-khuon-v83-da-dung-de-so]
# Khong dong vao cay git. WORKERS (mac dinh 4) = so luong capture.
set -euo pipefail
RUN="${1:?thu muc chay}"; DATA="${2:?kenh-game-du-lieu}"; NANG="${3:?thu muc nang (trailer)}"; V83="${4:-}"
SRC="$(cd "$(dirname "$0")/../../.." && pwd)"
mkdir -p "$RUN"; rsync -a --exclude .git --exclude node_modules --exclude .venv "$SRC/" "$RUN/repo/"
cd "$RUN/repo" && bash lay-tai-san.sh keo-thom keo-thom-v83 --data "$DATA" --nang "$NANG"
cd khuon/keo-thom
cp hoi-quy/keo-hoi-quy.json keo.json
python3 kich-ban.py > /dev/null
cmp <(tr -d '\n' < loi.txt) <(tr -d '\n' < dau-vao/loi.txt) && echo "loi.txt = loi v8.3 (kich-ban.py tai tao dung)"
python3 hoi-quy/gan-doan.py dau-vao/moc-chu.json kich-ban.json dau-vao/moc-chu.gan.json && mv dau-vao/moc-chu.gan.json dau-vao/moc-chu.json
HOI_QUY=1 WORKERS="${WORKERS:-4}" bash chay.sh
M=$(python3 -c "import json;print(','.join(str(x) for x in json.load(open('neo.json'))['TA']['moc']))")
RC=0
for nt in tiktok reels shorts; do
  # (a) anh tham chieu cua fixture (5 moc, video Mac v8.3): nguong 0,97 o 135x240
  uv run -q --frozen --project ../.. python ../../cong-cu/so-anh.py "video-$nt.mp4" "$DATA/video/fixture/keo-thom-v83/ref" "$nt" 0.97 || RC=1
  # (b) video v8.3 dung lai tu cung fixture: 6 moc, ca 135x240 va 270x480 + tung cu tieng
  if [ -n "$V83" ]; then python3 hoi-quy/so-hai-ban.py "video-$nt.mp4" "$V83/video-$nt.mp4" "$nt" "$M" cue-am08.json "$V83/cue-am08.json" || RC=1; fi
done
exit $RC
