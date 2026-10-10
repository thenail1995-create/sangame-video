// Kiem tren TRANG THAT (full.build.html), cung cach capture.mjs seek (t = f/30):
//  1) phu de tran khung o BAT KY khung nao (loi 14 lan nhap nhay cua ban 07/08)
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
 const SEL=["#mast","#title","#issue","#hdr1","#focus","#chip1","#saoIn .c","#t2h","#t2g","#t2m","#tk","#khoan","#hoiN","#hoiS","#q1","#q2","#q3",
   ".tem .in span","#khong","#bang .tit2","#bang .dong .g","#bang .dong .n","#bang .pill","#h5","#lat","#p5a","#p5b","#b6a","#b6b","#chips","#url","#b6c","#logoW img","#sub","#mini","#toc"];
 const vis=el=>{let c=el;while(c){const s=getComputedStyle(c);if(s.display==="none"||+s.opacity===0)return false;c=c.parentElement}return true};
 for(const t of MOC_DUNG){window.__seek(t);
   for(const sel of SEL){for(const e of document.querySelectorAll(sel)){if(!vis(e))continue;const q=e.getBoundingClientRect();if(!q.width)continue;
     const L=Math.round(q.left),R=Math.round(q.right),T=Math.round(q.top),Bm=Math.round(q.bottom);
     if(L<114||R>894||T<V.tren-6||Bm>V.duoi+6)(out.ngoaiVung[t]=out.ngoaiVung[t]||[]).push(sel+" x"+L+"-"+R+" y"+T+"-"+Bm)}}}
 return out},[MOC_DUNG,V]);
console.log(JSON.stringify(r));await b.close()})();
