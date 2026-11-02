// Ham dung chung cho fb.html / ig.html / threads.html (tat dinh: moi khung la ham thuan cua t)
window.__ready=false;
const E={lin:t=>t,oc:t=>1-Math.pow(1-t,3),oq:t=>1-Math.pow(1-t,4),
 ob:t=>{const c1=1.9,c3=c1+1;return 1+c3*Math.pow(t-1,3)+c1*Math.pow(t-1,2)},io:t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2};
const cl=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
const P=(t,t0,d,e='oc')=>E[e](cl((t-t0)/d));
const mix=(a,b,k)=>a+(b-a)*k;
const $=id=>document.getElementById(id);
function S(el,o){if(typeof el==='string')el=$(el);for(const k in o)el.style[k]=o[k]}
const vnd=n=>Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g,'.')+'đ';
const vk=n=>n%1000===0?(n/1000)+'K':vnd(n);
// tao phan tu: chu LUON di qua textContent (khong innerHTML)
function mk(tag,cls,id,text,cha){const e=document.createElement(tag);if(cls)e.className=cls;if(id)e.id=id;if(text!=null)e.textContent=text;if(cha)cha.appendChild(e);return e}
function anh(cls,src,cha,id){const e=mk('img',cls,id,null,cha);e.src=window.DL.__ts+src;return e}
function co(ma,cha){const e=mk('img','co-img',null,null,cha);e.src='co/'+String(ma).toLowerCase()+'.svg';return e}
const rong=e=>{const r=document.createRange();r.selectNodeContents(e);return r.getBoundingClientRect().width};
// Tu co chu: thu 1 dong (xuong toi mot), roi toi da `dong` dong (xuong toi min), cuoi cung moi cat "…"
function vua(e,w,o){o=o||{};const dong=o.dong||1,min=o.min||22,mot=o.mot||min;
  const cs=getComputedStyle(e);let f=parseFloat(cs.fontSize);
  const lh=(parseFloat(cs.lineHeight)/f)||1.2;
  if(cs.position==='absolute'&&cs.textAlign==='center'){e.style.left=(parseFloat(cs.left)+parseFloat(cs.width)/2-w/2)+'px'}
  e.style.width=w+'px';e.style.marginLeft=e.style.marginRight='auto';e.style.whiteSpace='nowrap';e.style.fontSize=f+'px';
  while(f>mot&&rong(e)>w){f-=2;e.style.fontSize=f+'px'}
  if(rong(e)<=w)return;
  if(dong>1){e.style.whiteSpace='normal';
    while(f>min&&e.scrollHeight>dong*f*lh+2){f-=2;e.style.fontSize=f+'px'}
    if(e.scrollHeight<=dong*f*lh+2)return;}
  let s=e.textContent;
  while(s.length>2&&(dong>1?e.scrollHeight>dong*f*lh+2:rong(e)>w)){s=s.slice(0,-2).trimEnd();e.textContent=s+'…'}
}
// fit() chay sau khi font + anh san sang; fn(t) ve khung t
async function san(fit,fn){
  window.__seek=t=>fn(t);
  try{
    await Promise.all(['500','600','700','800'].map(w=>document.fonts.load(w+' 40px BVP')));
    await document.fonts.ready;
    await Promise.all([...document.images].map(i=>i.decode()));
    if(fit)fit();fn(0);window.__ready=true;
  }catch(err){setTimeout(()=>{throw err})}
}
