// Chup khoi tieu de + gia cua trang san pham PS Store (bai X goc, dang/x_goc.py) va in 1 dong JSON de Python kiem.
//
// DUNG:  node cong-cu/chup-ps.mjs <url-san-pham> <ra.png>
// IN RA (stdout, 1 dong JSON):
//   {"tieu_de","gia_hien","gia_goc","giam_chu","han_chu","so_khoi","url_cuoi","rong","cao"}
//   gia_hien = gia cua khoi offer DAU TIEN khong phai "Included"/PS Plus (khoi Included bi bo); gia_goc, han_chu ("Offer ends ...") lay
//   TRONG CHINH khoi do; giam_chu = dong "Save N%" cua khoi do; so_khoi = so khoi gia thuong (khong Included/PS Plus) tren trang
//   (>1 = nhieu edition/offer -> Python fail-closed, khong chac khoi nao thuoc ma san pham dang dang). Khong co khoi gia thuong -> gia_hien = null (Python se dung, khong dang).
// Ngay gio "Offer ends M/D/YYYY hh:mm AM|PM GMT+7": locale en-US (M/D/Y) + timezoneId Asia/Ho_Chi_Minh co dinh -> giong nhau tren Mac va runner UTC.
// Loi: in ly do ra stderr, thoat 2 (khong tao anh dang tin).
// Quy tac: chi domcontentloaded + cho selector (networkidle khong bao gio xong tren PS Store); an OneTrust bang CSS, KHONG bam Accept.
// Anh chi nam tren runner/Mac, KHONG upload-artifact (anh Sony khong duoc vao repo cong khai).
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';

const [url, ra] = process.argv.slice(2);
if (!url || !ra) {
  console.error('dung: node chup-ps.mjs <url> <ra.png>');
  process.exit(2);
}

const CSS_AN = '#onetrust-consent-sdk,#onetrust-banner-sdk,#onetrust-pc-sdk,.onetrust-pc-dark-filter{display:none!important;visibility:hidden!important}';
const LE = 14;                                    // le quanh khoi (px CSS)

const trinh = await chromium.launch();
try {
  const ctx = await trinh.newContext({ locale: 'en-US', timezoneId: 'Asia/Ho_Chi_Minh', viewport: { width: 1280, height: 1000 }, deviceScaleFactor: 2 });
  const trang = await ctx.newPage();
  await trang.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await trang.waitForSelector('[data-qa="mfe-game-title#name"]', { timeout: 30000 });
  await trang.waitForSelector('[data-qa^="mfeCtaMain#offer"][data-qa$="#finalPrice"]', { timeout: 20000 });
  await trang.addStyleTag({ content: CSS_AN });
  await trang.waitForTimeout(1200);               // cho hinh/nen ve xong sau khi an lop phu

  const kq = await trang.evaluate(() => {
    const chu = (e) => (e ? e.innerText.trim() : null);
    const tieu_de = chu(document.querySelector('[data-qa="mfe-game-title#name"]'));
    const khoi = [...document.querySelectorAll('[data-qa^="mfeCtaMain#offer"]')]
      .filter((e) => /^mfeCtaMain#offer\d+$/.test(e.getAttribute('data-qa')));
    let chon = null, so_khoi = 0;
    for (const k of khoi) {
      const qa = k.getAttribute('data-qa');
      const gia = chu(k.querySelector(`[data-qa="${qa}#finalPrice"]`));
      const plus = !!k.querySelector(`[data-qa="${qa}#serviceIcon#ps-plus"]`);
      if (!gia || plus || /included/i.test(gia)) continue;
      so_khoi += 1;
      if (!chon) chon = { k, qa, gia };
    }
    const url_cuoi = location.href;
    if (!chon) return { tieu_de, gia_hien: null, gia_goc: null, giam_chu: null, han_chu: null, so_khoi, url_cuoi, hop: null };
    const dong = chon.k.innerText.split('\n').map((s) => s.trim());
    const han = dong.find((s) => /^offer ends/i.test(s)) || null;
    const giam = dong.find((x) => /(save|-)\s*\d{1,3}\s*%/i.test(x)) || null;
    const goc = chu(chon.k.querySelector(`[data-qa="${chon.qa}#originalPrice"]`));
    const r = (e) => { const x = e.getBoundingClientRect(); return { x: x.left + scrollX, y: x.top + scrollY, w: x.width, h: x.height }; };
    const the = document.querySelector('[data-qa="mfe-game-title"]').closest('.psw-c-bg-card-1') || document.querySelector('[data-qa="mfe-game-title"]');
    const a = r(the), b = r(chon.k);
    const duoi = b.y + b.h;
    return { tieu_de, gia_hien: chon.gia, gia_goc: goc, giam_chu: giam, han_chu: han, so_khoi, url_cuoi,
             hop: { x: a.x, y: a.y, w: a.w, h: duoi - a.y } };
  });

  let rong = 0, cao = 0;
  if (kq.hop) {
    const clip = { x: Math.max(0, kq.hop.x - LE), y: Math.max(0, kq.hop.y - LE), width: kq.hop.w + 2 * LE, height: kq.hop.h + LE + 8 };   // khoi gia co dong "Lowest price" tran xuong duoi rect mot chut
    await trang.screenshot({ path: ra, clip, fullPage: true });
    const dau = readFileSync(ra);                  // kich thuoc PNG that: IHDR (byte 16-23)
    rong = dau.readUInt32BE(16); cao = dau.readUInt32BE(20);
  }
  const { hop, ...ra_json } = kq;
  console.log(JSON.stringify({ ...ra_json, rong, cao }));
} catch (e) {
  console.error('chup-ps loi: ' + String(e && e.message ? e.message : e).split('\n')[0]);
  process.exitCode = 2;
} finally {
  await trinh.close();
}
