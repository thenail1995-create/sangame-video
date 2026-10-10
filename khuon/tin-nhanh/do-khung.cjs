// Doc trang thai trang Top 5 o tung khung (t = f/30) -> khung.json: khung CHAM de dat tieng dong (LOI-SAI A1)
const MG=process.env.MG_SCRIPTS||process.env.HOME+"/.claude/skills/motion-graphics/scripts";   // A3: khong ghi cung duong dan Mac
const {chromium}=require(process.env.PW_PATH||MG+"/node_modules/playwright");const fs=require("fs");
const B=__dirname; const NT=process.argv[2]||"tiktok";   // moc thoi gian giong nhau o 3 nen tang -> do tren 1 ban
(async()=>{const b=await chromium.launch();const pg=await b.newPage({viewport:{width:1080,height:1920}});
await pg.goto("file://"+B+"/full-"+NT+".build.html");await pg.waitForFunction(()=>window.__ready);
const r=await pg.evaluate(()=>{
 const mt=el=>{const m=getComputedStyle(el).transform;if(!m||m==="none")return [1,0,0];const v=m.match(/matrix\(([^)]+)\)/);if(!v)return [1,0,0];const a=v[1].split(",").map(Number);return [Math.hypot(a[0],a[1]),a[4],a[5]]};
 const vis=el=>{let c=el;while(c){const s=getComputedStyle(c);if(s.display==="none"||+s.opacity===0)return false;c=c.parentElement}return true};
 const ids=["logo3","b1_1","b1_2","gm1","gm2","gm3"];for(let r=1;r<=3;r++)ids.push("dau"+r,"dauW"+r,"b"+r+"_0","g"+r,"cat"+r);for(let i=0;i<3;i++)ids.push("m"+i,"dk"+i);
 const nf=Math.round(window.DAI*30), rows=[];
 for(let f=0;f<nf;f++){window.__seek(f/30);const o={f};
   for(const id of ids){const e=document.getElementById(id);o[id]=(e&&vis(e))?mt(e).map(x=>+x.toFixed(3)):0}
   o.url=document.getElementById("urlc").textContent.length; o.H=parseFloat(document.getElementById("band").style.height); rows.push(o)}
 return rows});
fs.writeFileSync(B+"/khung.json",JSON.stringify(r));console.log("khung.json",r.length,"khung");await b.close()})();
