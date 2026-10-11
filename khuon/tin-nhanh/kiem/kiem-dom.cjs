// Kiem tren TRANG THAT (full.build.html), cung cach capture.mjs seek (t = f/30):
//  1) phu de tran khung o BAT KY khung nao (loi 14 lan nhap nhay cua ban 07/08)
//  3) (goi B / B3) NOI DUNG tung the tin tren hinh (tit, nguon, ten game, nhan, giam %, gia, moc) -> noiDung{} de kiem-tat-ca.py doi chieu CHINH XAC voi tin.json
//  2) chu/gia/logo nam trong hop an toan CUA NEN TANG: x 120-888, y tren..duoi theo nen-tang.json (dung sai 6 px) o cac moc da dung yen
// node kiem/kiem-dom.cjs <tiktok|reels|shorts> [moc,...]  -> in JSON {tranPhuDe:[...], ngoaiVung:{t:[...]}}
const MG=process.env.MG_SCRIPTS||process.env.HOME+"/.claude/skills/motion-graphics/scripts";   // A3: khong ghi cung duong dan Mac
const {chromium}=require(process.env.PW_PATH||MG+"/node_modules/playwright");
const path=require("path");const B=path.resolve(__dirname,"..");
const NT=process.argv[2]||"tiktok", V=JSON.parse(require("fs").readFileSync(B+"/nen-tang.json"))[NT];
const C=JSON.parse(require("fs").readFileSync(B+"/canh.json"));const MOC_DUNG=(process.argv[3]?process.argv[3].split(",").map(Number):[1.8].concat(C.filter(c=>/^t\d/.test(c.k)).map(c=>+(c.b-0.3).toFixed(2)),[C[C.length-1].b-0.4]));
(async()=>{const b=await chromium.launch();const pg=await b.newPage({viewport:{width:1080,height:1920}});
await pg.goto("file://"+B+"/full-"+NT+".build.html");await pg.waitForFunction(()=>window.__ready);
const r=await pg.evaluate(([MOC_DUNG,V,C])=>{
 const out={tranPhuDe:[],ngoaiVung:{},trungId:[],ngay:{n1:(document.getElementById('ngay1')||{}).textContent||'',n6:(document.getElementById('ngay6')||{}).textContent||''}};   // ngay tren giay (C3)
 // ma phan tu TRUNG (Top 5 "so5", Tin nhanh "tit3": getElementById tra phan tu dau -> CSS/hieu ung ap nham cho)
 const dem={};document.querySelectorAll("[id]").forEach(e=>{dem[e.id]=(dem[e.id]||0)+1});out.trungId=Object.keys(dem).filter(k=>dem[k]>1);
 const nf=Math.round((window.DAI||25.12)*30);
 for(let f=0;f<nf;f++){const t=f/30;window.__seek(t);const s=document.getElementById("sub");const w=document.getElementById("subW");
   if(w&&w.style.display!=="none"&&s.scrollWidth>s.clientWidth+1)out.tranPhuDe.push(t.toFixed(2)+": "+s.textContent.trim())}
 // chi kiem phan tu CHUA CHU/GIA/LOGO (than sticker/tem giay la trang tri, duoc tran)
 const SEL=["#mast","#chip","#so3","#nong","#hdr1","#hdr6","#toc",".mucluc .t",".cat .k",".cat .tit",".cat .dong",".dau","#tieuK",".dongK .t","#mai","#url3","#logo3 img","#sub"];
 const vis=el=>{let c=el;while(c){const s=getComputedStyle(c);if(s.display==="none"||+s.opacity===0)return false;c=c.parentElement}return true};
 for(const t of MOC_DUNG){window.__seek(t);
   for(const sel of SEL){for(const e of document.querySelectorAll(sel)){if(!vis(e))continue;const q=e.getBoundingClientRect();if(!q.width)continue;
     const L=Math.round(q.left),R=Math.round(q.right),T=Math.round(q.top),Bm=Math.round(q.bottom);
     if(L<114||R>894||T<V.tren-6||Bm>V.duoi+6)(out.ngoaiVung[t]=out.ngoaiVung[t]||[]).push(sel+" x"+L+"-"+R+" y"+T+"-"+Bm)}}}
 // chu KHONG tran / bi cat / co qua nho (Top 5 11/10: ten game dai bi cat cut 'Little Nightmares Complet...'): moi phan tu chu, o moi moc dung yen
 const MIN={".cat .tit":34,".cat .tt b":19,".mucluc .t b":24,".dongK .t b":26,".cat .k":18,".cat .g":40,".cat .gm":28};
 out.catChu=[];out.coChu=[];
 for(const t of MOC_DUNG){window.__seek(t);
   for(const sel of Object.keys(MIN)){for(const e of document.querySelectorAll(sel)){if(!vis(e))continue;
     const q=e.getBoundingClientRect(),c=(e.closest(".cat,.mucluc,.dongK")||e.parentElement).getBoundingClientRect();
     const fs=parseFloat(getComputedStyle(e).fontSize);
     if(e.scrollWidth>e.clientWidth+1&&getComputedStyle(e).display!=="inline")out.catChu.push(t+"s "+sel+" scrollW "+e.scrollWidth+">"+e.clientWidth+": "+e.textContent.slice(0,40));
     const gh=e.closest(".cat")?c.right-8:c.right+1;if(q.right>gh||q.left<c.left-1)out.catChu.push(t+"s "+sel+" tran khoi the "+Math.round(q.right)+">"+Math.round(gh)+": "+e.textContent.slice(0,40));
     if(fs<MIN[sel]-0.01)out.catChu.push(t+"s "+sel+" co chu "+fs.toFixed(1)+"px < "+MIN[sel]+": "+e.textContent.slice(0,40));
     out.coChu.push(sel+" "+fs.toFixed(0))}}}
 out.coChu=[...new Set(out.coChu)];
 // noi dung hien thi cua tung the tin (moc dung yen cua canh t<r>), cung nguon voi chu nguoi xem thay
 const tx=e=>e?e.textContent.replace(/\u00a0/g,' ').replace(/\s+/g,' ').trim():null, nd={tin:[]};
 for(const c of C.filter(c=>/^t\d$/.test(c.k))){const r=+c.k.slice(1);window.__seek(+(c.b-0.3).toFixed(2));
   const cat=document.getElementById('cat'+r);if(!cat)continue;
   nd.tin.push({r,k:tx(cat.querySelector('.k')),tit:tx(document.getElementById('tit'+r)),ten:[...cat.querySelectorAll('.dong .tt b')].map(tx),nhan:tx(cat.querySelector('.dong .tt small')),
     gm:tx(document.getElementById('gm'+r)),g:tx(document.getElementById('g'+r)),loai:tx(document.getElementById('dau'+r)),
     muc:tx(document.querySelector('#m'+(r-1)+' .t b')),dk:tx(document.querySelector('#dk'+(r-1)+' .t b'))})}
 nd.tieuK=tx(document.getElementById('tieuK'));nd.so3=tx(document.getElementById('so3'));out.noiDung=nd;
 return out},[MOC_DUNG,V,C]);
console.log(JSON.stringify(r));await b.close()})();
