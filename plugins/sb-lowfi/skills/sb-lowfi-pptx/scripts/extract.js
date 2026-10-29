(function(){
const out=[];
function extract(f,cap){
 const R=f.getBoundingClientRect(), items=[], marks=[];
 const walk=(el)=>{
  const cs=getComputedStyle(el); if(cs.display==='none'||cs.visibility==='hidden') return;
  const r=el.getBoundingClientRect();
  const rel={x:r.left-R.left,y:r.top-R.top,w:r.width,h:r.height};
  if(r.width>0&&r.height>0){
   const bg=cs.backgroundColor, hasBg=bg!=='rgba(0, 0, 0, 0)';
   const S=['Top','Right','Bottom','Left'];
   const bw=S.map(s=>cs['border'+s+'Style']==='none'?0:parseFloat(cs['border'+s+'Width']));
   if(hasBg||bw.some(x=>x>0)) items.push(Object.assign({t:'box',bg:hasBg?bg:null,bw:bw,bc:S.map(s=>cs['border'+s+'Color']),bs:cs.borderTopStyle,rad:parseFloat(cs.borderTopLeftRadius)||0,pct:cs.borderTopLeftRadius.indexOf('%')>=0},rel));
   if(el.dataset&&el.dataset.n){
     const b=getComputedStyle(el,'::before'); const bwid=parseFloat(b.width)||18, bh=parseFloat(b.height)||18;
     let l=parseFloat(b.left), tp=parseFloat(b.top); if(isNaN(l)) l=-8; if(isNaN(tp)) tp=-8;
     let ty=0; const m=b.transform.match(/matrix\(([^)]+)\)/); if(m){ty=parseFloat(m[1].split(',')[5])||0;}
     const mk={n:el.dataset.n,x:rel.x+l,y:rel.y+tp+ty,w:bwid,h:bh,ex:rel.x,ey:rel.y,ew:rel.w,eh:rel.h,txt:(el.innerText||'').replace(/\s+/g,' ').trim().slice(0,60)}; items.push(Object.assign({t:'mark'},mk)); marks.push(el.dataset.n);
   }
   const a=getComputedStyle(el,'::after');
   if(a.content!=='none'&&a.content!=='normal'&&a.position==='absolute'&&a.backgroundColor!=='rgba(0, 0, 0, 0)'&&!(el.dataset&&el.dataset.n&&false)){
     const aw=parseFloat(a.width),ah=parseFloat(a.height),al=parseFloat(a.left),at=parseFloat(a.top);
     if(!isNaN(aw)&&!isNaN(ah)&&!isNaN(al)&&!isNaN(at)) items.push({t:'box',x:rel.x+al,y:rel.y+at,w:aw,h:ah,bg:a.backgroundColor,bw:[0,0,0,0],bc:[],bs:'none',rad:parseFloat(a.borderTopLeftRadius)||0,pct:a.borderTopLeftRadius.indexOf('%')>=0});
   }
  }
  for(const n of el.childNodes){
   if(n.nodeType===3&&n.textContent.trim()){
    const rg=document.createRange(); rg.selectNodeContents(n);
    const rects=[...rg.getClientRects()].filter(q=>q.width>0&&q.height>0); if(!rects.length) continue;
    let x1=1e9,y1=1e9,x2=-1e9,y2=-1e9; const tops=new Set();
    rects.forEach(q=>{x1=Math.min(x1,q.left);y1=Math.min(y1,q.top);x2=Math.max(x2,q.right);y2=Math.max(y2,q.bottom);tops.add(Math.round(q.top/3));});
    items.push({t:'text',text:n.textContent.replace(/\s+/g,' ').trim(),x:x1-R.left,y:y1-R.top,w:x2-x1,h:y2-y1,lines:tops.size,size:parseFloat(cs.fontSize),color:cs.color,bold:parseInt(cs.fontWeight)>=600,italic:cs.fontStyle==='italic',mono:/mono|Menlo|Consolas/i.test(cs.fontFamily),serif:/Georgia|Serif KR/i.test(cs.fontFamily)&&!/sans/i.test(cs.fontFamily.split(',')[0]),align:cs.textAlign,ul:cs.textDecorationLine.indexOf('underline')>=0,st:cs.textDecorationLine.indexOf('line-through')>=0});
   }
  }
  for(const c of el.children) walk(c);
 };
 walk(f);
 return {cap:cap,kind:f.classList.contains('mo')?'mo':'pc',w:R.width,h:R.height,items:items,marks:marks};
}
const norm=t=>(t||'').replace(/\s+/g,' ').trim();
function autoMark(f, srcMap){
 // 마커가 하나도 없는 프레임: 같은 화면의 다른 프레임에서 마커가 붙은 요소와 글자가 같은 요소를 찾아 같은 번호를 붙인다
 const used=new Set(), R=f.getBoundingClientRect(), out=[];
 const els=[...f.querySelectorAll('*')];
 for(const [txt,n] of srcMap){
  if(used.has(n)||txt.length<2) continue;
  const hit=els.find(e=>norm(e.innerText)===txt&&![...e.children].some(c=>norm(c.innerText)===txt)&&e.getBoundingClientRect().width>0);
  if(!hit) continue;
  const r=hit.getBoundingClientRect(); used.add(n);
  out.push({t:'mark',n:n,x:r.left-R.left-8,y:r.top-R.top-8,w:18,h:18,ex:r.left-R.left,ey:r.top-R.top,ew:r.width,eh:r.height,txt:txt.slice(0,60),auto:true});
 }
 return out;
}
document.querySelectorAll('.screen-section').forEach(sec=>{
 const frames=[], doms=[];
 sec.querySelectorAll('.pc,.mo').forEach(f=>{
  if(f.parentElement.closest('.pc,.mo')) return;
  let cap=''; const p=f.previousElementSibling; if(p&&p.classList.contains('cap')) cap=p.textContent.trim();
  frames.push(extract(f,cap)); doms.push(f);
 });
 const srcMap=new Map();
 sec.querySelectorAll('[data-n]').forEach(e=>{const t=norm(e.innerText); if(t&&!srcMap.has(t)) srcMap.set(t,e.dataset.n);});
 frames.forEach((fr,i)=>{ if(!fr.marks.length){ const am=autoMark(doms[i],srcMap); fr.items.push(...am); fr.marks=am.map(m=>m.n); fr.auto=am.length>0; } });
 const spec=[...sec.querySelectorAll('.spec tbody tr')].map(tr=>[...tr.children].map(td=>td.innerText.trim()));
 const stbls=[...sec.querySelectorAll('.stbl')].map(s=>({title:(s.querySelector('h4')||{}).textContent||'',rows:[...s.querySelectorAll('tr')].map(tr=>[...tr.children].map(td=>td.innerText.trim())),items:[...s.querySelectorAll('li')].map(li=>li.innerText.trim())}));
 out.push({sid:sec.id,h2:sec.querySelector('h2').textContent.trim(),meta:((sec.querySelector('.meta')||{}).textContent||'').trim(),frames:frames,spec:spec,stbls:stbls});
});
const pre=document.createElement('pre'); pre.id='__out'; pre.textContent=JSON.stringify(out); document.body.appendChild(pre);
})();
