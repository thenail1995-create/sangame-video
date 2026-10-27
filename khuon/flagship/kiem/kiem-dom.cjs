// Kiem tren TRANG THAT (full-<nt>.build.html), cung cach capture.mjs seek (t = f/30). node kiem/kiem-dom.cjs <tiktok|reels|shorts>
//  - trungId: id trung
//  - ngoaiVung: chu/bia ngoai x 70..890, y 1004..1480 (dung sai 1 px) o cac moc dung yen (cuoi moi canh - 0,3 s)
//  - noiDung: chu THAT tren hinh o cac moc dung yen (D1)
//  - soHien: moi chuoi SO dang hien o 10 khung/giay -> {so: giay hien dau} (D1-so, SAN #47)
//  - kich: co chu (px) cua cac khoi chinh o moc dung yen
//  - khung0: khoi so tien luc t = 0
const MG=process.env.MG_SCRIPTS||process.env.HOME+"/.claude/skills/motion-graphics/scripts";
const {chromium}=require(process.env.PW_PATH||MG+"/node_modules/playwright");
const path=require("path");const B=path.resolve(__dirname,"..");
const NT=process.argv[2]||"tiktok", V=JSON.parse(require("fs").readFileSync(B+"/nen-tang.json"))[NT];
const C=JSON.parse(require("fs").readFileSync(B+"/canh.json"));
(async()=>{const b=await chromium.launch();const pg=await b.newPage({viewport:{width:1080,height:1920}});
await pg.goto("file://"+B+"/full-"+NT+".build.html");await pg.waitForFunction(()=>window.__ready);
const r=await pg.evaluate(([V,CANH])=>{
 const out={trungId:[],ngoaiVung:{},soHien:{}};
 const dem={};document.querySelectorAll("[id]").forEach(e=>{dem[e.id]=(dem[e.id]||0)+1});out.trungId=Object.keys(dem).filter(k=>dem[k]>1);
 const vis=el=>{let c=el;while(c){const s=getComputedStyle(c);if(s.display==="none"||s.visibility==="hidden"||+s.opacity===0)return false;c=c.parentElement}return true};
 const tx=el=>el?el.textContent.replace(/\s+/g," ").trim():null;
 const CK=k=>CANH.find(c=>c.k===k);
 const MOC=CANH.map(c=>+(c.b-0.3).toFixed(2));
 const SEL=["#nmoT","#tmo","#pbigT","#chip","#giaT","#goc","#lblT","#tiles .tile .v","#vnd","#mt1","#mt2","#hlab","#hday","#hcon","#vcan","#vpsn","#kbrT","#kt1","#kt2"];
 for(const t of MOC){window.__seek(t);
   for(const sel of SEL)for(const e of document.querySelectorAll(sel)){if(!vis(e))continue;
     const rg=document.createRange();rg.selectNodeContents(e);const q=rg.getBoundingClientRect();if(!q.width)continue;
     const L=Math.round(q.left),R=Math.round(q.right),T=Math.round(q.top),Bm=Math.round(q.bottom);
     if(L<69||R>891||T<1004-1||Bm>1480+1)(out.ngoaiVung[t]=out.ngoaiVung[t]||[]).push(sel+" x"+L+"-"+R+" y"+T+"-"+Bm)}
   const cv=document.getElementById("cov");if(cv&&vis(cv)){const q=cv.getBoundingClientRect();if(q.left<69||q.right>891||q.top<1004||q.bottom>1480)(out.ngoaiVung[t]=out.ngoaiVung[t]||[]).push("#cov x"+Math.round(q.left)+"-"+Math.round(q.right)+" y"+Math.round(q.top)+"-"+Math.round(q.bottom))}}
 // D1: noi dung luc dung yen
 const nd={};const at=(k,fn)=>{if(!CK(k))return;window.__seek(+(CK(k).b-0.3).toFixed(2));nd[k]=fn()};
 const I=id=>document.getElementById(id);
 at("mo",()=>({so:tx(I("nmoT")),ten:tx(I("tmo")),hienSo:vis(I("nmoT")),hienTen:vis(I("tmo"))}));
 // -% to: do o giay T.pct + 0,5 (con hien)
 window.__seek(+(window.__T.pct+0.5).toFixed(2));nd.pct={t:+(window.__T.pct+0.5).toFixed(2),pct:tx(I("pbigT")),hien:vis(I("pbigT"))};
 at("gia",()=>({chip:tx(I("chip")),gia:tx(I("giaT")),goc:tx(I("gocV")),lbl:tx(I("lblT")),hien:[I("chip"),I("giaT"),I("goc"),I("lbl")].map(vis)}));
 at("the",()=>({tiles:[...document.querySelectorAll("#tiles .tile .v")].map(tx),vnd:tx(I("vnd")),hien:vis(I("vnd"))}));
 at("moc",()=>({l1:tx(I("mt1")),l2:tx(I("mt2"))}));
 at("han",()=>({lab:tx(I("hlab")),ngay:tx(I("hday")),con:vis(I("hcon"))?tx(I("hcon")):null}));
 at("vung",()=>({can:tx(I("vcan")),psn:tx(I("vpsn")),co:I("vflagi").getAttribute("src")}));
 at("ket",()=>({brand:tx(I("kbrT")),k1:tx(I("kt1")),k2:tx(I("kt2"))}));
 out.noiDung=nd;
 // co chu (px) o moc dung yen
 const kich={};const fs=(k,id,sel)=>{const e=sel?document.querySelector(sel):I(id);if(e)kich[k]=+parseFloat(getComputedStyle(e).fontSize).toFixed(1)};
 const cs=(k,t,list)=>{if(!CK(k))return;window.__seek(t);list.forEach(([n,id,sel])=>fs(n,id,sel))};
 cs("mo",+(CK("mo").b-0.3).toFixed(2),[["tien_mo","nmoT"],["ten","tmo"]]);
 cs("gia",+(CK("gia").b-0.3).toFixed(2),[["gia","giaT"],["goc","goc"],["nhan_vung","lblT"],["chip","chip"]]);
 window.__seek(+(window.__T.pct+0.5).toFixed(2));fs("pct","pbigT");
 cs("the",+(CK("the").b-0.3).toFixed(2),[["vnd","vnd"],["the_gia",null,"#tl0 .v"]]);
 if(CK("moc"))cs("moc",+(CK("moc").b-0.3).toFixed(2),[["moc1","mt1"],["moc2","mt2"]]);
 cs("han",+(CK("han").b-0.3).toFixed(2),[["han_lab","hlab"],["han_ngay","hday"],["han_con","hcon"]]);
 cs("vung",+(CK("vung").b-0.3).toFixed(2),[["vung_can","vcan"],["vung_psn","vpsn"]]);
 cs("ket",+(CK("ket").b-0.3).toFixed(2),[["slogan1","kt1"],["slogan2","kt2"],["thuong_hieu","kbrT"]]);
 out.kich=kich;

 // CAT NET (Opus 28/10): khung bao NET THAT (ink: canvas measureText + Range, ke ca transform) cua moi khoi chu dang hien phai nam TRON trong vung nhin thay cua dai
 // (y >= 1004, khong bi overflow/clip cua cha cat). Khoi bi cat MOT PHAN = LOI; khoi bi cat het (an cho truot ra) khong tinh.
 out.catNet=[];
 const cvs=document.createElement("canvas").getContext("2d");
 const ink=e=>{const cs=getComputedStyle(e),fs=parseFloat(cs.fontSize);cvs.font=cs.fontWeight+" "+fs+"px "+cs.fontFamily;
   const txt=e.textContent.replace(/\s+/g," ").trim(),m=cvs.measureText(txt),mH=cvs.measureText("H");
   const rg=document.createRange();rg.selectNodeContents(e);const rs=[...rg.getClientRects()].filter(r=>r.width>0&&r.height>0);if(!rs.length)return null;
   const fa=m.fontBoundingBoxAscent,fd=m.fontBoundingBoxDescent,sy=Math.max(...rs.map(r=>r.height))/(fa+fd);
   const tops=rs.map(r=>r.top),bots=rs.map(r=>r.bottom),multi=Math.max(...tops)-Math.min(...tops)>5;
   const top=Math.min(...tops)+(fa-(multi?mH:m).actualBoundingBoxAscent)*sy;
   const bot=Math.max(...bots)-(fd-(multi?0.5*fd:m.actualBoundingBoxDescent))*sy;
   return {l:Math.min(...rs.map(r=>r.left)),r:Math.max(...rs.map(r=>r.right)),t:top,b:bot}};
 const MN=[0,0.1,0.15,0.3,1.0].concat(CANH.map(c=>c.a),CANH.map(c=>+(c.a+0.1).toFixed(2)));
 for(const t of [...new Set(MN)].sort((a,b)=>a-b)){window.__seek(t);
   document.querySelectorAll("#sh *").forEach(e=>{if(!vis(e))return;let s="";e.childNodes.forEach(n=>{if(n.nodeType===3)s+=n.textContent});if(!s.trim())return;
     const k=ink(e);if(!k)return;let L=0,R=1080,T=1004,Bm=1480;
     for(let c=e.parentElement;c;c=c.parentElement){const cs=getComputedStyle(c);if(cs.overflow!=="visible"||cs.overflowX!=="visible"||cs.overflowY!=="visible"){const q=c.getBoundingClientRect();L=Math.max(L,q.left);R=Math.min(R,q.right);T=Math.max(T,q.top);Bm=Math.min(Bm,q.bottom)}}
     const hit=k.r>L&&k.l<R&&k.b>T&&k.t<Bm; if(!hit)return;
     if(k.t<T-1||k.b>Bm+1||k.l<L-1||k.r>R+1)out.catNet.push("t="+t+" "+(e.id?"#"+e.id:e.className||e.tagName)+" «"+s.trim().slice(0,14)+"» ink y"+Math.round(k.t)+"-"+Math.round(k.b)+" x"+Math.round(k.l)+"-"+Math.round(k.r)+" vung y"+Math.round(T)+"-"+Math.round(Bm)+" x"+Math.round(L)+"-"+Math.round(R))})}
 // t = 0
 window.__seek(0);out.khung0={so:tx(I("nmoT")),hien:vis(I("nmoT")),opa:+getComputedStyle(I("nmoT")).opacity};
 // D1-so: quet 10 khung/giay
 const nf=Math.round(window.DAI*30);
 for(let f=0;f<nf;f+=3){const t=f/30;window.__seek(t);
   document.querySelectorAll("#sh *").forEach(e=>{if(!vis(e))return;let s="";e.childNodes.forEach(n=>{if(n.nodeType===3)s+=n.textContent});s=s.trim();if(!s)return;
     (s.match(/\d+(?:[.,]\d+)*/g)||[]).forEach(k=>{if(!(k in out.soHien))out.soHien[k]=+t.toFixed(2)})})}
 return out},[V,C]);
console.log(JSON.stringify(r));await b.close()})();
