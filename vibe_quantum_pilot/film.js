(async function () {
  'use strict';
  const M=window.QuantumModel;
  const CONFIG=await (await fetch('scenes.json')).json();
  const TOTAL_FRAMES=Math.round(CONFIG.duration*CONFIG.fps);
  const SCENES=CONFIG.scenes.map((sc,i)=>({...sc,start:M.ANCHORS[i],end:M.ANCHORS[i+1]}));
  await document.fonts.ready;
  const canvas=document.getElementById('film'),ctx=canvas.getContext('2d',{alpha:false});
  const W=1920,H=1080;
  const C={bg:'#080d17',white:'#edf3f8',cyan:'#72e2ed',muted:'#91a9b9',dim:'#425967',line:'#29404e'};
  const FONT='"Heiti SC", "STHeiti", sans-serif';
  const MONO='"SFMono-Regular", "Menlo", monospace';
  const dots=M.sampleDots(M.TOTAL_DOTS,CONFIG.seed);
  const texture=document.createElement('canvas');texture.width=1440;texture.height=520;
  const tx=texture.getContext('2d');let textureCount=0;
  let textBounds=[];
  const clamp=M.clamp, smooth=M.smooth;
  const ease=x=>{const p=clamp(x);return p<.5?4*p*p*p:1-(-2*p+2)**3/2;};
  const lerp=(a,b,p)=>a+(b-a)*p;
  const gate=(t,a,b)=>smooth((t-a)/(b-a));
  function line(x1,y1,x2,y2,color=C.line,width=1.5,alpha=1){ctx.save();ctx.globalAlpha=clamp(alpha);ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();ctx.restore();}
  function text(s,x,y,size=30,color=C.white,alpha=1,align='left',weight=400,font=FONT){
    if(alpha<=0)return;ctx.save();ctx.globalAlpha=clamp(alpha);ctx.fillStyle=color;ctx.font=`${weight} ${size}px ${font}`;ctx.textAlign=align;ctx.textBaseline='alphabetic';ctx.fillText(s,x,y);
    const m=ctx.measureText(s),left=align==='center'?x-m.width/2:align==='right'?x-m.width:x;
    if(alpha>.5)textBounds.push({text:s,x:left,right:left+m.width,top:y-m.actualBoundingBoxAscent,bottom:y+m.actualBoundingBoxDescent});ctx.restore();
  }
  function circle(x,y,r,color,alpha=1,width=0){if(r<=0||alpha<=0)return;ctx.save();ctx.globalAlpha=clamp(alpha);ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);if(width){ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke();}else{ctx.fillStyle=color;ctx.fill();}ctx.restore();}
  function glow(x,y,r,strength=.3){ctx.save();const g=ctx.createRadialGradient(x,y,0,x,y,r);g.addColorStop(0,`rgba(101,226,239,${strength})`);g.addColorStop(.25,`rgba(65,174,198,${strength*.3})`);g.addColorStop(1,'rgba(40,100,150,0)');ctx.fillStyle=g;ctx.fillRect(x-r,y-r,r*2,r*2);ctx.restore();}
  function roundedRect(x,y,w,h,r){ctx.beginPath();ctx.roundRect(x,y,w,h,r);}
  function updateTexture(count){
    if(count<textureCount){tx.clearRect(0,0,texture.width,texture.height);textureCount=0;}
    for(let i=textureCount;i<count;i++){
      const d=dots[i],x=(d.x+1)/2*texture.width,y=d.y*texture.height;
      tx.globalAlpha=d.shine*.88;tx.fillStyle='#a3eff7';tx.beginPath();tx.arc(x,y,1.35,0,Math.PI*2);tx.fill();
    }
    textureCount=count;tx.globalAlpha=1;
  }
  function panelAt(t){
    const wide={x:380,y:338,w:1160,h:382};
    const small={x:1284,y:350,w:346,h:330};
    const chart={x:380,y:331,w:1160,h:281};
    let a,b,p;
    if(t<15){return wide;}
    if(t<18){a=wide;b=small;p=ease((t-15)/3);}
    else if(t<34){return small;}
    else if(t<37){a=small;b=chart;p=ease((t-34)/3);}
    else return chart;
    return {x:lerp(a.x,b.x,p),y:lerp(a.y,b.y,p),w:lerp(a.w,b.w,p),h:lerp(a.h,b.h,p)};
  }
  function dotPosition(i,p){const d=dots[Math.max(0,Math.min(i,dots.length-1))];return {x:p.x+(d.x+1)/2*p.w,y:p.y+d.y*p.h};}
  function background(){
    ctx.fillStyle=C.bg;ctx.fillRect(0,0,W,H);
    const g=ctx.createRadialGradient(1000,500,60,1000,500,1100);g.addColorStop(0,'#0d1b29');g.addColorStop(1,C.bg);ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
    // Quiet registration marks create depth without decorative moving particles.
    ctx.save();ctx.fillStyle='#557285';ctx.globalAlpha=.12;
    for(let x=112;x<=1808;x+=64)for(let y=304;y<816;y+=64)ctx.fillRect(x,y,1,1);
    ctx.restore();
    text('量 子 之 问',112,126,26,C.muted,1,'left',400);
    line(306,116,364,116,C.cyan,1.6,.6);
    text('01',387,124,20,C.cyan,1,'left',400,MONO);
    text('原理示意',1808,126,24,C.muted,1,'right');
    line(112,158,1808,158,C.line,1,.6);
  }
  function chapterHeading(s,t){
    const finalReveal=gate(t,49.5,51.5);
    if(finalReveal<1){
      for(let i=0;i<SCENES.length;i++){
        const sc=SCENES[i];let a=(i===0?1:gate(t,sc.start,sc.start+.7))*(1-gate(t,sc.end-.45,sc.end));
        a*=1-finalReveal;
        const slide=i===0?0:(1-gate(t,sc.start,sc.start+.8))*20;
        text(sc.heading,112,260+slide,74,C.white,a,'left',400);
      }
    }
    if(finalReveal>0)text(CONFIG.title,960,260+12*(1-finalReveal),80,C.white,finalReveal,'center',400);
    if(t<49.5){
      const section=['单次事件','累积结果','实验装置','放慢观察','统计分布','从偶然到规律'][s.stage];
      text(section,1808,248,26,C.muted,gate(t,0,.6)*(1-finalReveal),'right');
    }
  }
  function drawPanel(p,s){
    const t=s.t;updateTexture(s.count);
    ctx.save();const g=ctx.createLinearGradient(p.x,p.y,p.x,p.y+p.h);g.addColorStop(0,'#0b1723');g.addColorStop(1,'#0d1c28');ctx.fillStyle=g;roundedRect(p.x,p.y,p.w,p.h,4);ctx.fill();
    ctx.strokeStyle=C.line;ctx.lineWidth=1.3;ctx.stroke();
    ctx.drawImage(texture,p.x,p.y,p.w,p.h);ctx.restore();
    const L=22;
    for(const [x,y,sx,sy] of [[p.x,p.y,1,1],[p.x+p.w,p.y,-1,1],[p.x,p.y+p.h,1,-1],[p.x+p.w,p.y+p.h,-1,-1]]){
      line(x,y,x+sx*L,y,C.cyan,1.7,.7);line(x,y,x,y+sy*L,C.cyan,1.7,.7);
    }
    const isApp=gate(t,15,18)*(1-gate(t,34,37));
    text('探测屏',p.x,p.y-25,26,C.muted,1-isApp);
    text(s.count.toLocaleString('en-US')+' 次探测',p.x+p.w,p.y-25,26,C.cyan,1,'right',400,MONO);
    if(t<7){
      const eventTime=Math.floor(t*5)/5;
      const a=1-clamp((t-eventTime)/.2);
      const q=dotPosition(s.count-1,p);circle(q.x,q.y,4,C.white,1);glow(q.x,q.y,26,.35*a);
      circle(q.x,q.y,9+14*(1-a),C.cyan,a*.65,1);
    }
    const compress=gate(t,7,7.7)*(1-gate(t,14.2,15)) + gate(t,34.7,35.4)*(1-gate(t,43.2,44));
    if(compress>.01){
      const labelX=p.x+(t>=34?250:0);
      text('时间压缩',labelX,p.y+p.h+37,23,C.muted,compress);
      for(let i=0;i<3;i++){const x=labelX+126+i*14;line(x,p.y+p.h+20,x+7,p.y+p.h+26,C.cyan,1.4,compress*.65);line(x+7,p.y+p.h+26,x,p.y+p.h+32,C.cyan,1.4,compress*.65);}
    }
    if(t>=7&&t<14.8){
      const a=gate(t,8.5,10)*(1-gate(t,13.8,14.8));
      // A non-moving construction line points at a dark fringe.
      const x=p.x+.55*p.w;
      line(x,p.y-8,x,p.y-56,C.cyan,1,a*.6);
      text('明暗开始分开',x+15,p.y-48,25,C.muted,a);
    }
  }
  function apparatus(s,p){
    const t=s.t,alpha=gate(t,16,18.8)*(1-gate(t,34,36.2));if(alpha<=0)return;
    const reveal=gate(t,16.2,19.5),sx=345,sy=522,bx=905;
    ctx.save();ctx.globalAlpha=alpha;
    // Electron source: its flash indicates an emission, not a tracked trajectory.
    ctx.strokeStyle=C.muted;ctx.lineWidth=2;
    roundedRect(sx-80,sy-35,135,70,10);ctx.stroke();
    line(sx+55,sy-20,sx+87,sy-11,C.muted,2,1);line(sx+55,sy+20,sx+87,sy+11,C.muted,2,1);
    line(sx+87,sy-11,sx+87,sy+11,C.cyan,3,1);
    for(let x=sx-58;x<sx+35;x+=22)line(x,sy-12,x+10,sy+12,C.dim,1.5,1);
    const beamEnd=lerp(sx+100,bx-62,reveal);
    line(sx+100,sy,beamEnd,sy,C.dim,1.3,.55);
    // Two physical openings. No asserted post-slit electron path is shown.
    for(const [y1,y2] of [[338,458],[486,558],[586,710]])line(bx,y1,bx,y1+(y2-y1)*reveal,C.muted,5,1);
    for(const y of [472,572]){line(bx-9,y-14,bx+9,y-14,C.cyan,1.5,1);line(bx-9,y+14,bx+9,y+14,C.cyan,1.5,1);}
    line(sx,748,bx,748,C.line,1,1);line(bx,748,p.x+p.w/2,748,C.line,1,1);
    for(const x of [sx,bx,p.x+p.w/2])line(x,741,x,755,C.dim,1.2,1);
    ctx.restore();
    text('电子源',sx,800,28,C.white,alpha,'center');text('双缝',bx,800,28,C.white,alpha,'center');text('探测屏',p.x+p.w/2,800,28,C.white,alpha,'center');
    if(t<25){
      text('一次一个',sx,421,30,C.cyan,alpha*gate(t,19,20),'center');
    }
    for(let i=0;i<M.emissions.length;i++){
      const age=t-M.emissions[i],arrivalAge=age-.45;
      if(age>=0&&age<.45){const a=1-age/.45;glow(sx+88,sy,78,alpha*.48*a);circle(sx+88,sy,5,C.white,alpha*a);circle(sx+88,sy,13+age*50,C.cyan,alpha*a,1.5);}
      if(arrivalAge>=0&&arrivalAge<1.05){
        const q=dotPosition(6000+i,p),a=(1-smooth(arrivalAge/1.05))*alpha;
        glow(q.x,q.y,48,.6*a);circle(q.x,q.y,4,C.white,a);circle(q.x,q.y,10+arrivalAge*22,C.cyan,a,1.5);
      }
    }
    if(t>=25){
      const i=clamp(Math.floor((t-25.5)/1.5)+1,0,6);
      text('单次事件  '+String(i).padStart(2,'0'),sx,421,26,C.cyan,alpha*gate(t,25,25.7),'center');
    }
  }
  function probabilityPlot(s,p){
    const t=s.t,a=gate(t,35.5,37.8);if(a<=0)return;
    const base=793,height=124;
    const axis=gate(t,35.5,38);
    line(p.x,base,p.x+p.w*axis,base,C.muted,1.5,a*.7);
    line(p.x,base,p.x,base-height*axis-14,C.muted,1.5,a*.7);
    const curve=gate(t,37.3,40.6),peak=M.density(0);
    ctx.save();ctx.globalAlpha=a;ctx.beginPath();ctx.moveTo(p.x,base);
    for(let i=0;i<=Math.floor(900*curve);i++){
      const u=-1+2*i/900,x=p.x+i/900*p.w,y=base-height*M.density(u)/peak;ctx.lineTo(x,y);
    }
    const end=p.x+Math.floor(900*curve)/900*p.w;ctx.lineTo(end,base);ctx.closePath();
    const fill=ctx.createLinearGradient(0,base-height,0,base);fill.addColorStop(0,'#72e2ed39');fill.addColorStop(1,'#72e2ed00');ctx.fillStyle=fill;ctx.fill();
    ctx.beginPath();for(let i=0;i<=Math.floor(900*curve);i++){const u=-1+2*i/900,x=p.x+i/900*p.w,y=base-height*M.density(u)/peak;if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);}ctx.strokeStyle=C.cyan;ctx.lineWidth=2.5;ctx.stroke();ctx.restore();
    for(const u of [-.4,-.2,0,.2,.4]){
      const x=p.x+(u+1)/2*p.w,y=base-height*M.density(u)/peak;
      const strength=gate(t,40.5,42)*.24;
      ctx.save();ctx.setLineDash([3,8]);line(x,p.y+p.h+5,x,y-9,C.cyan,1,strength);ctx.restore();
    }
    text('落点概率密度',p.x,650,24,C.cyan,gate(t,38.5,39.5));
    text('屏上位置',p.x+p.w,826,22,C.muted,a,'right');
    text('0',p.x-18,802,18,C.muted,a,'right',400,MONO);
    if(t>40.8){const x=p.x+p.w*.5,y=base-height;circle(x,y,4,C.white,gate(t,40.8,41.7));}
  }
  function richLine(s,x,y,size,alpha,emphasis){
    ctx.font=`400 ${size}px ${FONT}`;const width=ctx.measureText(s).width;
    let offset=x-width/2;
    for(let i=0;i<s.length;){
      const key=emphasis.find(k=>s.startsWith(k,i));const part=key||s[i];
      text(part,offset,y,size,key?C.cyan:C.white,alpha);
      ctx.font=`400 ${size}px ${FONT}`;offset+=ctx.measureText(part).width;i+=part.length;
    }
  }
  function captions(s){
    const t=s.t;
    for(const sc of SCENES){
      const entry=gate(t,sc.start+.25,sc.start+1.05);
      const exit=sc.end===55?1:1-gate(t,sc.end-.4,sc.end);
      const a=entry*exit;if(a<=0)continue;
      const dy=(1-entry)*16;
      if(sc.lines.length===1)richLine(sc.lines[0],960,925+dy,48,a,sc.emphasis);
      else {richLine(sc.lines[0],960,885+dy,48,a,sc.emphasis);richLine(sc.lines[1],960,951+dy,48,a,sc.emphasis);}
    }
  }
  function finalLabels(s,p){
    const t=s.t,a=gate(t,47,49);if(a<=0)return;
    const d=dotPosition(11999,p);
    const shift=ease((t-47)/2);
    // The emphasis words detach from the caption area and settle as diagram labels.
    const x=lerp(700,1680,shift),y1=lerp(884,448,shift),y2=lerp(950,728,shift);
    text('单次',x,y1,32,C.cyan,a,'center');text('整体',x,y2,32,C.cyan,a,'center');
    const settled=gate(t,49,50);
    text('一个落点',1680,487,24,C.muted,settled,'center');text('概率分布',1680,767,24,C.muted,settled,'center');
    line(p.x+p.w+22,465,1607,465,C.line,1.5,settled);line(p.x+p.w+22,744,1607,744,C.line,1.5,settled);
    circle(d.x,d.y,8,C.white,settled*.9,1.8);
    text('单电子累积现象 · 原理示意',112,979,18,C.dim,gate(t,51,52));
  }
  function renderFrame(frame){
    const actualFrame=clamp(Math.round(frame),0,TOTAL_FRAMES-1);
    const s=M.stateAt(M.mapTime(actualFrame/CONFIG.fps,CONFIG.scenes)*M.FPS);textBounds=[];
    background();chapterHeading(s,s.t);
    const p=panelAt(s.t);
    drawPanel(p,s);apparatus(s,p);probabilityPlot(s,p);finalLabels(s,p);captions(s);
    window.filmDiagnostics={frame:actualFrame,time:actualFrame/CONFIG.fps,count:s.count,stage:s.stage,textBounds};
    const slider=document.getElementById('seek');slider.value=actualFrame;
    document.getElementById('time').textContent=`00:${(actualFrame/CONFIG.fps).toFixed(2).padStart(5,'0')} / 00:${CONFIG.duration}`;
    return {frame:actualFrame,count:s.count};
  }
  window.renderFrame=renderFrame;
  let playing=false,raf=0,origin=0,startFrame=0;
  const play=document.getElementById('play');
  function pause(){playing=false;cancelAnimationFrame(raf);play.textContent='播放';}
  function tick(now){if(!playing)return;const frame=startFrame+Math.floor((now-origin)*CONFIG.fps/1000);renderFrame(frame);if(frame>=TOTAL_FRAMES-1){pause();return;}raf=requestAnimationFrame(tick);}
  function start(){if(window.filmDiagnostics.frame>=TOTAL_FRAMES-1)renderFrame(0);playing=true;startFrame=window.filmDiagnostics.frame;origin=performance.now();play.textContent='暂停';raf=requestAnimationFrame(tick);}
  play.onclick=()=>playing?pause():start();
  document.getElementById('restart').onclick=()=>{pause();renderFrame(0);start();};
  document.getElementById('seek').addEventListener('input',e=>{pause();renderFrame(Number(e.target.value));});
  document.getElementById('seek').max=TOTAL_FRAMES-1;
  window.addEventListener('keydown',e=>{if(e.code==='Space'){e.preventDefault();playing?pause():start();}if(e.code==='ArrowLeft'||e.code==='ArrowRight'){e.preventDefault();pause();renderFrame(window.filmDiagnostics.frame+(e.code==='ArrowLeft'?-1:1));}});
  const nav=document.querySelector('.chapter-nav');
  CONFIG.scenes.forEach(sc=>{const button=document.createElement('button');button.textContent=`${String(sc.start).padStart(2,'0')}s · ${sc.heading}`;button.onclick=()=>{pause();renderFrame(sc.start*30);};nav.append(button);});
  renderFrame(Number(new URLSearchParams(location.search).get('frame'))||0);
  window.filmReady=true;
})();
