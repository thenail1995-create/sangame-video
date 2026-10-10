# sangame-video

May dung video ngan cho kenh Sang Game (https://sangame.com.vn): 3 dang video moi ngay
(Tin nhanh, Top 5 game re, Keo thom), moi video xuat 3 ban theo nen tang (TikTok / Reels / Shorts).

Repo nay CONG KHAI va chi chua **khuon dung** (code, khuon HTML, font OFL, logo Sang Game).

## Khong nam trong repo nay
- Am thanh (tieng dong), giong doc, trailer cua nha phat hanh, anh bia game, du lieu gia/bai viet:
  nam o repo rieng tu va duoc keo ve luc dung. Ly do: giay phep cua cac tai nguyen do khong cho phep phat hanh lai.
- Khoa, token: chi o GitHub Secrets / kho bi mat. Khong bao gio commit.

## Cau truc
- `khuon/{tin-nhanh,top5,keo-thom}/` - 3 khuon dung (HTML + script Python/Node).
- `cong-cu/` - `capture.mjs` (HTML -> video tat dinh), `kiem-video.py`, `package.json` + lockfile (Playwright ghim ban).
- `lay-tai-san.sh` - keo tai san/fixture tu repo rieng tu ve dung cho khuon.
- `.github/workflows/` - chi nhan `workflow_dispatch` / `repository_dispatch` / `push` vao `main`.

## Ghi chu bao mat
- Khong dung `pull_request_target`; khong co workflow `pull_request` nao co secret.
- Moi action ghim theo SHA commit. Khong `curl | sh`.
- Truoc moi commit chay `gitleaks protect --staged` (hook: `git config core.hooksPath .githooks`).

Giay phep ma nguon: MIT (xem `LICENSE`). Font: SIL OFL (Be Vietnam Pro, Newsreader, Playfair Display).
Logo/ten "Sang Game": quyen cua chu kenh, khong nam trong giay phep MIT.
