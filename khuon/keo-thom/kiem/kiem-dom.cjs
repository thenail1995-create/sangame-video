// Kiem tren TRANG THAT (full.build.html), cung cach capture.mjs seek (t = f/30):
//  1) phu de tran khung o BAT KY khung nao (loi 14 lan nhap nhay cua ban 07/08)
//  3) (v9) NOI DUNG tren hinh o cac moc dung yen (ten, gia, vung, gio het giam) -> noiDung{} de kiem-tat-ca.py doi chieu keo.json (D1)
//  2) chu/gia/logo nam trong hop an toan CUA NEN TANG: x 120-888, y tren..duoi theo nen-tang.json (dung sai 6 px) o cac moc da dung yen
// node kiem/kiem-dom.cjs <tiktok|reels|shorts> [moc,...]  -> in JSON {tranPhuDe:[...], ngoaiVung:{t:[...]}}
const MG=process.env.MG_SCRIPTS||process.env.HOME+"/.claude/skills/motion-graphics/scripts";   // A3: khong ghi cung duong dan Mac
const {chromium}=require(process.env.PW_PATH||MG+"/node_modules/playwright");
const path=require("path");const B=path.resolve(__dirname,"..");
const NT=process.argv[2]||"tiktok", V=JSON.parse(require("fs").readFileSync(B+"/nen-tang.json"))[NT];
const MOC_DUNG=(process.argv[3]||"3.7,8.4,9.7,12.2,13.0,17.8,20.8,24.8").split(",").map(Number);
(async()=>{const b=await chromium.launch();const pg=await b.newPage({viewport:{width:1080,height:1920}});
await pg.goto("file://"+B+"/full-"+NT+".build.html");await pg.waitForFunction(()=>window.__ready);
const r=await pg.evaluate(([MOC_DUNG,V])=>{
 const out={tranPhuDe:[],ngoaiVung:{},trungId:[]};
 // ma phan tu TRUNG (Top 5 "so5", Tin nhanh "tit3": getElementById tra phan tu dau -> CSS/hieu ung ap nham cho)
 const dem={};document.querySelectorAll("[id]").forEach(e=>{dem[e.id]=(dem[e.id]||0)+1});out.trungId=Object.keys(dem).filter(k=>dem[k]>1);
 const nf=Math.round((window.DAI||25.12)*30);
 for(let f=0;f<nf;f++){const t=f/30;window.__seek(t);const s=document.getElementById("sub");const w=document.getElementById("subW");
   if(w&&w.style.display!=="none"&&s.scrollWidth>s.clientWidth+1)out.tranPhuDe.push(t.toFixed(2)+": "+s.textContent.trim())}
 // chi kiem phan tu CHUA CHU/GIA/LOGO (than sticker/tem giay la trang tri, duoc tran)
 const SEL=["#mast","#title","#issue","#hdr1","#focus","#chip1","#saoIn .c","#t2h","#t2g","#t2m","#tk","#gtH span","#gtG","#gtC1","#gtC2","#gtScore","#gtLuot","#gtB","#gtI1","#gtI2","#gtI3","#gtI4","#gtT1","#gtT2","#gtT3","#bang .tit2","#bang .dong .g","#bang .dong .n","#bang .pill","#h5","#lat","#p5a","#p5b","#b6a","#b6b","#chips","#url","#b6c","#logoW img","#sub","#mini","#toc"];
 const vis=el=>{let c=el;while(c){const s=getComputedStyle(c);if(s.display==="none"||+s.opacity===0)return false;c=c.parentElement}return true};
 for(const t of MOC_DUNG){window.__seek(t);
   for(const sel of SEL){for(const e of document.querySelectorAll(sel)){if(!vis(e))continue;const q=e.getBoundingClientRect();if(!q.width)continue;
     const L=Math.round(q.left),R=Math.round(q.right),T=Math.round(q.top),Bm=Math.round(q.bottom);
     if(L<114||R>894||T<V.tren-6||Bm>V.duoi+6)(out.ngoaiVung[t]=out.ngoaiVung[t]||[]).push(sel+" x"+L+"-"+R+" y"+T+"-"+Bm)}}}
 // CAT/TRAN CHU (Top 5 11/10: "Little Nightmares Complet…" cut cut tren the): moi phan tu chu — ten, gia, vung, gio — o MOI moc dung yen:
 //  (a) chu thuc (Range) rong/cao hon chinh phan tu > 1 px; (b) chu bi cat boi to tien overflow != visible; (c) tieu de the gia lan vao goc vat cheo cua the (#tag).
 out.catChu=[];
 const SELC=["#title","#issue","#chip1","#t2h","#t2g","#t2l2","#t2m","#tk","#gtG","#gtC1","#gtC2","#gtScore","#gtLuot","#gtB","#gtI1","#gtI2","#gtI3","#gtI4","#gtT1","#gtT2","#gtT3","#bang .tit","#bang .tit2","#bang .dong .n","#bang .dong .g","#bang .pill","#bang .chu","#p5a","#p5b","#lat","#b6a","#b6b","#b6c","#sub"];
 for(const t of MOC_DUNG){window.__seek(t);
   for(const sel of SELC){for(const e of document.querySelectorAll(sel)){if(!vis(e))continue;
     const rg=document.createRange();rg.selectNodeContents(e);const tb=rg.getBoundingClientRect(),eb=e.getBoundingClientRect();if(!tb.width||!eb.width)continue;
     let ly=null;
     if(tb.width>eb.width+1.5)ly="chu rong "+Math.round(tb.width)+" > o chua "+Math.round(eb.width);
     for(let c=e.parentElement;c&&!ly;c=c.parentElement){const cs=getComputedStyle(c);if(cs.overflow!=="visible"&&c.id!=="band"){const cb=c.getBoundingClientRect();
       if(tb.left<cb.left-1||tb.right>cb.right+1||tb.top<cb.top-1||tb.bottom>cb.bottom+1)ly="chu bi cat boi #"+(c.id||c.className)}}
     if(!ly&&sel==="#t2h"){const dy=Math.max(0,96-(tb.top-500));const L0=190+dy+24,R0=890-dy-24;if(tb.left<L0||tb.right>R0)ly="tieu de the lan vao goc vat cheo ("+Math.round(tb.left)+"-"+Math.round(tb.right)+" can "+L0+"-"+R0+")"}
     if(ly)out.catChu.push(t+"s "+sel+": "+ly+" «"+e.textContent.trim().slice(0,30)+"»")}}}
 // G3 (13/10): THE BIET TRUOC (#gtT1..3) khong de len / che hang khac cua ho so game (the loai, chip, sao+diem, nhan ban, phan them) va khong tran ra ngoai the #gt: o MOI moc dung yen
 out.chongGT=[];
 const HANG=["#gtG","#gtC1","#gtC2","#gtStar","#gtLuot","#gtScore","#gtB","#gtI1","#gtI2","#gtI3","#gtI4"];
 for(const t of MOC_DUNG){window.__seek(t);const cb=document.querySelector("#gt").getBoundingClientRect();
   for(const ts of ["#gtT1","#gtT2","#gtT3"]){const te=document.querySelector(ts);if(!te||!vis(te))continue;const a=te.getBoundingClientRect();
     if(a.left<cb.left||a.right>cb.right||a.bottom>cb.bottom+1)out.chongGT.push(t+"s "+ts+" tran khoi the ho so");
     for(const hs of HANG.concat(["#gtT1","#gtT2","#gtT3"].filter(x=>x!==ts))){const he=document.querySelector(hs);if(!he||!vis(he))continue;const b=he.getBoundingClientRect();if(!b.width)continue;
       const ox=Math.min(a.right,b.right)-Math.max(a.left,b.left),oy=Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);if(ox>2&&oy>2)out.chongGT.push(t+"s "+ts+" de len "+hs)}}}
 // noi dung hien thi (moc dung yen cua tung canh theo thu tu MOC_DUNG: bia, the gia, khoan, thu, ra, bang, phieu, bia sau)
 const tx=e=>e?e.textContent.replace(/\s+/g,' ').trim():null, q=s=>document.querySelector(s), nd={};
 if(MOC_DUNG.length>=8){
  window.__seek(MOC_DUNG[0]);nd['bia.issue']=tx(q('#issue span'));nd['bia.sao']=tx(q('#saoIn .c b'));nd['bia.chip']=tx(q('#chip1'));nd['bia.title']=tx(q('#title'));
  window.__seek(MOC_DUNG[1]);nd['the.goc']=tx(q('#t2g'));nd['the.con']=tx(q('#moiso'))+tx(q('#du2'));nd['the.tk']=tx(q('#tk b'));nd['the.vung']=tx(q('#t2l2'));
  // ho so game (canh 3, 11/10): CHI phan tu dang HIEN o moc nay (an/opacity 0 = khong tinh) -> hang bi ket an se lech keo.json (D1)
  window.__seek(MOC_DUNG[3]);const vt=sel=>{const e=q(sel);return e&&vis(e)?tx(e):null};
  nd['gioi.the_loai']=vt('#gtG');nd['gioi.chip']=[vt('#gtC1'),vt('#gtC2')].filter(Boolean);nd['gioi.diem']=vt('#gtScore');nd['gioi.luot']=vt('#gtLuot');nd['gioi.ban']=vt('#gtB');nd['gioi.them']=[1,2,3,4].map(i=>vt('#gtI'+i)).filter(Boolean);nd['gioi.the_bt']=[1,2,3].map(i=>vt('#gtT'+i)).filter(Boolean);
  window.__seek(MOC_DUNG[5]);nd['bang.tit']=tx(q('#bang .tit'));nd['bang.n']=[1,2,3].map(i=>tx(q('#r'+i+' .n')));nd['bang.g']=[1,2,3].map(i=>tx(q('#r'+i+' .g')));nd['bang.pill']=[1,2,3].map(i=>tx(q('#r'+i+' .pill')));
  window.__seek(MOC_DUNG[6]);nd['phieu.so']=[1,2,3,4].map(i=>tx(q('#o'+i))).join('');nd['phieu.ngay']=tx(q('#p5b'));
 }
 out.noiDung=nd;
 return out},[MOC_DUNG,V]);
console.log(JSON.stringify(r));await b.close()})();
