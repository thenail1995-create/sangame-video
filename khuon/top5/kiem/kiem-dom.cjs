// Kiem tren TRANG THAT (full.build.html), cung cach capture.mjs seek (t = f/30):
//  1) phu de tran khung o BAT KY khung nao (loi 14 lan nhap nhay cua ban 07/08)
//  2) chu/gia/logo nam trong hop an toan CUA NEN TANG: x 120-888, y tren..duoi theo nen-tang.json (dung sai 6 px) o cac moc da dung yen
//  3) bo cuc A "Dua gia": do thanh gia (chieu dai, hang dang sang, vach X) o cac moc dung yen -> out.bang
// node kiem/kiem-dom.cjs <tiktok|reels|shorts> [moc,...]  -> in JSON {tranPhuDe:[...], ngoaiVung:{t:[...]}}
const MG=process.env.MG_SCRIPTS||process.env.HOME+"/.claude/skills/motion-graphics/scripts";   // A3: khong ghi cung duong dan Mac
const {chromium}=require(process.env.PW_PATH||MG+"/node_modules/playwright");
const path=require("path");const B=path.resolve(__dirname,"..");
const NT=process.argv[2]||"tiktok", V=JSON.parse(require("fs").readFileSync(B+"/nen-tang.json"))[NT];
const C=JSON.parse(require("fs").readFileSync(B+"/canh.json"));const MOC_DUNG=(process.argv[3]?process.argv[3].split(",").map(Number):[1.8].concat(C.filter(c=>/^h/.test(c.k)).map(c=>+(c.b-0.3).toFixed(2)),[C[C.length-1].b-0.4]));
(async()=>{const b=await chromium.launch();const pg=await b.newPage({viewport:{width:1080,height:1920}});
await pg.goto("file://"+B+"/full-"+NT+".build.html");await pg.waitForFunction(()=>window.__ready);
const r=await pg.evaluate(([MOC_DUNG,V,CANH])=>{
 const out={tranPhuDe:[],ngoaiVung:{},trungId:[]};
 // ma phan tu TRUNG (Top 5 "so5", Tin nhanh "tit3": getElementById tra phan tu dau -> CSS/hieu ung ap nham cho)
 const dem={};document.querySelectorAll("[id]").forEach(e=>{dem[e.id]=(dem[e.id]||0)+1});out.trungId=Object.keys(dem).filter(k=>dem[k]>1);
 const nf=Math.round((window.DAI||25.12)*30);
 for(let f=0;f<nf;f++){const t=f/30;window.__seek(t);const s=document.getElementById("sub");const w=document.getElementById("subW");
   if(w&&w.style.display!=="none"&&s.scrollWidth>s.clientWidth+1)out.tranPhuDe.push(t.toFixed(2)+": "+s.textContent.trim())}
 // chi kiem phan tu CHUA CHU/GIA/LOGO (than sticker/tem giay la trang tri, duoc tran)
 const SEL=["#tit3","#tem200","#phu1","#ngay1","#ngay6",".rk",".so",".bar > .v",".chip",".l3 .ten",".l3 .gia",".l3 .dong","#con3","#url3","#logo3 img"];
 const vis=el=>{let c=el;while(c){const s=getComputedStyle(c);if(s.display==="none"||+s.opacity===0)return false;c=c.parentElement}return true};
 for(const t of MOC_DUNG){window.__seek(t);
   for(const sel of SEL){for(const e of document.querySelectorAll(sel)){if(!vis(e))continue;const q=e.getBoundingClientRect();if(!q.width)continue;
     const L=Math.round(q.left),R=Math.round(q.right),T=Math.round(q.top),Bm=Math.round(q.bottom);
     if(L<114||R>894||T<V.tren-6||Bm>V.duoi+6)(out.ngoaiVung[t]=out.ngoaiVung[t]||[]).push(sel+" x"+L+"-"+R+" y"+T+"-"+Bm)}}}
 // D1 (B4): noi dung THAT tren hinh luc dung yen — ten/gia/giam/goc/vung/may cua tung hang, bang ket, tit, ngay
 const nd={hang:{},ket:[],tit:"",xlab:"",con:"",ngay1:"",ngay6:""};
 const tx=el=>el?el.textContent.replace(/\s+/g," ").trim():null;
 for(let r=1;r<=5;r++){const c=CANH.find(c=>c.k==="h"+r);window.__seek(+(c.b-0.3).toFixed(2));
   const dg=document.getElementById("dong"+r);
   nd.hang[r]={ten:tx(document.getElementById("ten"+r)),gia:tx(document.getElementById("gia"+r)),giam:tx(document.getElementById("giam"+r)),
     goc:tx(dg&&dg.querySelector("s")),vung:tx(dg&&dg.querySelector(".vung")),may:tx(dg&&dg.querySelector(".may")),
     hienTen:vis(document.getElementById("ten"+r)),hienGia:vis(document.getElementById("gia"+r))}}
 window.__seek(CANH[CANH.length-1].b-0.4);
 for(let r=5;r>=1;r--){const v=document.getElementById("v"+r),ck=document.getElementById("dk"+(5-r));nd.ket.push({r,gia:tx(v),giam:tx(ck),hien:vis(v)&&vis(ck)})}
 nd.tit=tx(document.getElementById("tit3"));nd.xlab=tx(document.getElementById("tem200"));nd.con=tx(document.getElementById("con3"));nd.ngay1=tx(document.getElementById("ngay1"));nd.ngay6=tx(document.getElementById("ngay6"));
 out.noiDung=nd;
 // K19: chu KHONG tran hop chua (ten/gia/vung o the hang + trang ket). Do bang Range (be rong CHU that, khong phai be rong khoi) so voi hop chua, o moi moc dung yen
 out.tranChu=[];
 const CAP=[[".l3 .ten",".tt"],[".l3 .gia",".tt"],[".l3 .dong",".tt"],[".bar > .v",".bar"],[".chip",".bar"],["#con3","#ket"],["#ngay6","#ket"],["#tit3",null]];
 for(const t of MOC_DUNG.concat([CANH[CANH.length-1].b-0.4])){window.__seek(t);
   for(const [sel,cs] of CAP){for(const e of document.querySelectorAll(sel)){if(!vis(e))continue;
     const rg=document.createRange();rg.selectNodeContents(e);const q=rg.getBoundingClientRect();if(!q.width)continue;
     let ho;if(cs){const c=e.closest(cs);if(!c)continue;const k=c.getBoundingClientRect();ho=[k.left,k.right,k.top,k.bottom]}else ho=[120,888,0,1920];
     const dd=(e.scrollWidth>e.clientWidth+1&&getComputedStyle(e).display!=="inline"&&getComputedStyle(e).transform==="none"&&e.clientWidth>0)?" scrollW":"";
     if(q.right>ho[1]+1||q.left<ho[0]-1||q.bottom>ho[3]+1||dd)out.tranChu.push(t.toFixed(2)+" "+sel+" "+e.textContent.trim().slice(0,28)+" chu "+Math.round(q.left)+"-"+Math.round(q.right)+" hop "+Math.round(ho[0])+"-"+Math.round(ho[1])+dd)}}}
 // bo cuc A: do thanh gia o MOI moc dung yen (chieu dai that tren hinh, hang dang sang, vach X, nhan X)
 out.bang={};
 for(const t of MOC_DUNG){window.__seek(t);const rows={};
   for(let r=1;r<=5;r++){const row=document.getElementById("row"+r),bar=document.getElementById("bar"+r).getBoundingClientRect();
     rows[r]={sang:+row.dataset.sang,w:+bar.width.toFixed(2),left:+bar.left.toFixed(2)}}
   const xl=document.getElementById("xl").getBoundingClientRect(),lb=document.getElementById("tem200").getBoundingClientRect();
   out.bang[t]={rows,xl:+(xl.left+xl.width/2).toFixed(2),lbR:+lb.right.toFixed(2)}}
 return out},[MOC_DUNG,V,C]);
console.log(JSON.stringify(r));await b.close()})();
