// Doc trang thai trang o tung khung (t = f/30, giong capture.mjs) -> khung.json: dung de dat tieng dong dung KHUNG CHAM.
// node do-khung.cjs [nen-tang]   -> khung.json (754 khung o ban v8.3; nay = ceil(DAI*30)) + neo.json (moc theo khoa doan M + moc chuyen canh TA, v9:
// MOT nguon duy nhat cho nen08.py / am08.py / kiem — khong con gio ghi cung)
const MG=process.env.MG_SCRIPTS||process.env.HOME+"/.claude/skills/motion-graphics/scripts";   // A3: khong ghi cung duong dan Mac
const {chromium}=require(process.env.PW_PATH||MG+"/node_modules/playwright");const fs=require("fs");
const B=__dirname; const NT=process.argv[2]||"tiktok";   // moc thoi gian giong nhau o 3 nen tang -> do 1 ban (v8.3)
(async()=>{const b=await chromium.launch();const pg=await b.newPage({viewport:{width:1080,height:1920}});
await pg.goto("file://"+B+"/full-"+NT+".build.html");await pg.waitForFunction(()=>window.__ready);
const neo=await pg.evaluate(()=>window.__NEO);const NF=await pg.evaluate(()=>Math.ceil(window.DAI*30));
const r=await pg.evaluate((NF)=>{
 const sc=el=>{const m=getComputedStyle(el).transform;if(!m||m==="none")return 1;const v=m.match(/matrix\(([^)]+)\)/);if(!v)return 1;const a=v[1].split(",").map(Number);return Math.hypot(a[0],a[1])};
 const vis=el=>{let c=el;while(c){const s=getComputedStyle(c);if(s.display==="none"||+s.opacity===0)return false;c=c.parentElement}return true};
 // gt*: ho so game (canh 3, 11/10); phan tu khong co trong du lieu = display:none -> 0
 const ids=["ronde","sao","tk","gtG","gtC1","gtC2","gtB","gtI1","gtI2","gtI3","gtI4","gtScore","d1","d2","d3","logoW","saoNho"];const ch=[...document.getElementById("chips").children];
 const rows=[];
 for(let f=0;f<NF;f++){const t=f/30;window.__seek(t);const o={f};
   for(const id of ids){const e=document.getElementById(id);o[id]=e&&vis(e)?+sc(e).toFixed(3):0}
   ch.forEach((e,i)=>o["chip"+i]=vis(e)?+sc(e).toFixed(3):0);
   o.url=document.getElementById("urlc").textContent.length;
   o.so=document.getElementById("moiso").textContent;
   o.lat=[1,2,3,4].map(i=>document.getElementById("o"+i).textContent).join("");
   o.keo=document.getElementById("keoA").getAttribute("transform");o.keoOn=getComputedStyle(document.getElementById("keo")).display!=="none";
   o.g1=+document.getElementById("g1").style.strokeDashoffset||0;
   o.b=[1,2,3].map(i=>parseFloat(document.getElementById("b"+i).style.width)||0);
   o.H=parseFloat(document.getElementById("band").style.height);
   rows.push(o)}
 return rows},NF);
fs.writeFileSync(B+"/khung.json",JSON.stringify(r));fs.writeFileSync(B+"/neo.json",JSON.stringify(neo));console.log("khung.json",r.length,"khung");await b.close()})()
