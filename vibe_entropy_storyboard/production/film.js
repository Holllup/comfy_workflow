(async function(){
 'use strict';
 const story=await(await fetch('../storyboard.json')).json();
 await document.fonts.ready;
 const {createTimeline,clamp,ease,mix,blend}=window.EntropyTimeline;
 const timeline=createTimeline(story),canvas=document.getElementById('film');
 canvas.width=story.brief.width;canvas.height=story.brief.height;
 const ctx=canvas.getContext('2d',{alpha:false}),W=canvas.width,H=canvas.height;
 const C={bg:'#070f19',white:'#edf5f9',cyan:'#77deeb',muted:'#94afc0',dim:'#425e70',line:'#2c4658',amber:'#efbd78'};
 const FONT='"Heiti SC", "STHeiti", sans-serif',MONO='"SFMono-Regular", Menlo, monospace';
 let bounds=[];
 const P=(s,id,i)=>timeline.actionProgress(s.t,id,i);
 const G=(t,a,b)=>timeline.progress(t,a,b);
 function txt(value,x,y,size=28,color=C.white,alpha=1,align='left',font=FONT){
  if(alpha<=0||!value)return;ctx.save();ctx.globalAlpha*=clamp(alpha);ctx.font=`400 ${size}px ${font}`;ctx.textAlign=align;ctx.textBaseline='alphabetic';ctx.fillStyle=color;ctx.fillText(value,x,y);
  if(ctx.globalAlpha>.5){const m=ctx.measureText(value),left=align==='center'?x-m.width/2:align==='right'?x-m.width:x;
   const tr=ctx.getTransform(),top=y-m.actualBoundingBoxAscent,bottom=y+m.actualBoundingBoxDescent;
   const corners=[[left,top],[left+m.width,top],[left,bottom],[left+m.width,bottom]].map(([a,b])=>({x:tr.a*a+tr.c*b+tr.e,y:tr.b*a+tr.d*b+tr.f}));
   bounds.push({text:value,x:Math.min(...corners.map(p=>p.x)),right:Math.max(...corners.map(p=>p.x)),top:Math.min(...corners.map(p=>p.y)),bottom:Math.max(...corners.map(p=>p.y))});
  }ctx.restore();
 }
 function line(x1,y1,x2,y2,color=C.line,width=1.5,alpha=1){ctx.save();ctx.globalAlpha*=clamp(alpha);ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();ctx.restore();}
 function circle(x,y,r,color=C.cyan,alpha=1,width=0){if(r<=0||alpha<=0)return;ctx.save();ctx.globalAlpha*=clamp(alpha);ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);if(width){ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke();}else{ctx.fillStyle=color;ctx.fill();}ctx.restore();}
 function box(x,y,w,h,r=8,fill=null,stroke=C.line,alpha=1,width=1.5){ctx.save();ctx.globalAlpha*=clamp(alpha);ctx.beginPath();ctx.roundRect(x,y,w,h,r);if(fill){ctx.fillStyle=fill;ctx.fill();}if(stroke){ctx.strokeStyle=stroke;ctx.lineWidth=width;ctx.stroke();}ctx.restore();}
 function glow(x,y,r,alpha=.12,color='91,199,221'){ctx.save();const g=ctx.createRadialGradient(x,y,0,x,y,r);g.addColorStop(0,`rgba(${color},${alpha})`);g.addColorStop(1,`rgba(${color},0)`);ctx.fillStyle=g;ctx.fillRect(x-r,y-r,r*2,r*2);ctx.restore();}
 function polygon(points,fill,stroke,width=2,alpha=1){ctx.save();ctx.globalAlpha*=alpha;ctx.beginPath();points.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.closePath();if(fill){ctx.fillStyle=fill;ctx.fill();}if(stroke){ctx.strokeStyle=stroke;ctx.lineWidth=width;ctx.stroke();}ctx.restore();}
 function bracket(x,y,w,h,alpha=1,color=C.cyan){const len=18;for(const [a,b,sx,sy] of [[x,y,1,1],[x+w,y,-1,1],[x,y+h,1,-1],[x+w,y+h,-1,-1]]){line(a,b,a+sx*len,b,color,1.8,alpha);line(a,b,a,b+sy*len,color,1.8,alpha);}}
 function background(s){
  ctx.fillStyle=C.bg;ctx.fillRect(0,0,W,H);const g=ctx.createRadialGradient(1000,480,30,1000,480,1100);g.addColorStop(0,'#112332');g.addColorStop(1,C.bg);ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
  txt('原理示意',1808,126,23,C.muted,G(s.t,.2,.7),'right');
 }
 function cup(p,solid,t,alpha=1){
  ctx.save();ctx.globalAlpha*=alpha;ctx.translate(p.x,p.y);ctx.scale(p.scale,p.scale);
  ctx.save();ctx.scale(1,.15);glow(0,70,150,.25,'0,0,0');ctx.restore();
  const cupPath=new Path2D();cupPath.moveTo(-124,-282);cupPath.lineTo(-104,-16);cupPath.quadraticCurveTo(-100,7,-78,8);cupPath.lineTo(78,8);cupPath.quadraticCurveTo(100,7,104,-16);cupPath.lineTo(124,-282);
  const glass=ctx.createLinearGradient(-120,0,120,0);glass.addColorStop(0,'#b7edff12');glass.addColorStop(.3,'#8ddfff02');glass.addColorStop(1,'#c8f6ff10');ctx.fillStyle=glass;ctx.fill(cupPath);
  ctx.save();ctx.clip(cupPath);
  const liquid=1-solid,h=96*liquid;
  if(liquid>.001){
   const water=ctx.createLinearGradient(0,-h,0,8);water.addColorStop(0,'#73dce846');water.addColorStop(1,'#4eafc126');ctx.fillStyle=water;
   ctx.beginPath();ctx.moveTo(-130,10);ctx.lineTo(-130,-h);
   for(let x=-130;x<=130;x+=5)ctx.lineTo(x,-h+2*liquid*Math.sin(x/35+t*1.8));ctx.lineTo(130,10);ctx.closePath();ctx.fill();
   ctx.strokeStyle='#a3eff3b0';ctx.lineWidth=1.5;ctx.beginPath();for(let x=-122;x<=122;x+=4){const y=-h+2*liquid*Math.sin(x/35+t*1.8);if(x===-122)ctx.moveTo(x,y);else ctx.lineTo(x,y);}ctx.stroke();
  }
  if(solid>.001){
   ctx.save();const k=Math.sqrt(solid);
   // Rest on the glass base until there is enough water to support floating ice.
   const iceBottom=Math.min(-7,-h+.9*160*k);
   ctx.translate(-2,iceBottom-67*k);ctx.scale(k,k);
   const ice=ctx.createLinearGradient(-80,-90,85,60);ice.addColorStop(0,'#e0fbff70');ice.addColorStop(.4,'#8ad8e74a');ice.addColorStop(1,'#4e8ba036');
   const pts=[[-70,-75],[55,-93],[95,-50],[70,50],[-45,67],[-86,19]];
   polygon(pts,ice,'#c8f7ffcc',2);
   polygon([[-70,-75],[55,-93],[95,-50],[-29,-29]],'#d9ffff23','#dafbff88',1.5);
   polygon([[-29,-29],[95,-50],[70,50],[-45,67]],'#8de0f011','#cbf8ff88',1.3);
   line(-29,-29,-45,67,'#dffcff99',1.4);line(-70,-75,-86,19,'#f2ffffcc',2);
   line(-48,-58,8,-67,'#f0ffffc0',2.4);line(77,-27,65,28,'#c5f7ff88',1.2);
   ctx.restore();
  }
  ctx.restore();ctx.strokeStyle='#b9dfe5a0';ctx.lineWidth=2.3;ctx.stroke(cupPath);
  ctx.beginPath();ctx.ellipse(0,-282,124,15,0,0,Math.PI*2);ctx.strokeStyle='#d9f1f4b0';ctx.lineWidth=1.7;ctx.stroke();
  line(-111,-244,-96,-32,'#e7fcff6c',1.3);line(110,-238,95,-45,'#cdeaf738',1.2);
  ctx.restore();
 }
 function fridge(s){
  const p=s.fridge,alpha=s.fridgeAlpha;if(alpha<=0)return;
  ctx.save();ctx.globalAlpha*=alpha;ctx.translate(p.x,p.y);ctx.scale(p.scale,p.scale);
  glow(0,-90,270,.075);box(-185,-255,370,510,18,'#0d1d29',C.muted,1,2);
  box(-163,-232,326,260,10,'#16313e66','#76c9d671',1,1.6);
  line(-161,29,161,29,C.muted,1.7,.7);box(-163,51,326,183,10,'#0b182266','#68889950',1,1.3);
  line(-154,21,154,21,C.cyan,1.7,.5);
  line(140,-180,140,-125,C.white,4,.7);line(140,83,140,142,C.white,4,.6);
  line(-142,-231,-142,18,'#6cbac34d',1.1);line(-149,251,-149,265,C.muted,4,.6);line(149,251,149,265,C.muted,4,.6);
  ctx.restore();
  const labelAlpha=(G(s.t,8,9)*(1-G(s.t,22,23)))+(G(s.t,99,101)*(1-G(s.t,133,135)));
  if(labelAlpha>.01)txt('冷冻室示意：−18℃',p.x,p.y-275*p.scale,26,C.cyan,labelAlpha,'center');
 }
 function drawLife(s){
  ctx.save();ctx.translate(960,500);ctx.scale(s.systemScale,s.systemScale);ctx.translate(-960,-500);
  const earlyTable=1-G(s.t,6,8),lateTable=G(s.t,133,136.4);
  if(earlyTable>0)line(580,737,1340,737,C.dim,1.6,earlyTable);
  if(lateTable>0)line(410,737,1090,737,C.dim,1.6,lateTable);
  fridge(s);cup(s.cup,s.solidFraction,s.t,.65+.35*G(s.t,0,.5));
  if(s.t<6){txt('室温示意：25℃',960,345,28,C.muted,G(s.t,.5,1),'center');}
  const note=(G(s.t,.5,1)*(1-G(s.t,5.7,6)))+(G(s.t,10.7,11.2)*(1-G(s.t,16.4,17.3)));
  if(note>0){const x=s.t<6?960:s.fridge.x;const y=s.t<6?795:800;txt('过程示意 · 时间压缩',x,y,24,C.muted,note,'center');}
  if(s.t>=102)drawEnergy(s);
  ctx.restore();
 }
 function cubicPoint(p,t){const q=1-t;return {x:q*q*q*p[0][0]+3*q*q*t*p[1][0]+3*q*t*t*p[2][0]+t*t*t*p[3][0],y:q*q*q*p[0][1]+3*q*q*t*p[1][1]+3*q*t*t*p[2][1]+t*t*t*p[3][1]};}
 function flowPath(points,progress,color,alpha,t,active=true){
  if(alpha<=0)return;ctx.save();ctx.globalAlpha*=alpha;ctx.strokeStyle=color;ctx.lineWidth=2.7;ctx.lineCap='round';ctx.beginPath();
  for(let i=0;i<=100;i++){const q=cubicPoint(points,i/100*progress);if(i===0)ctx.moveTo(q.x,q.y);else ctx.lineTo(q.x,q.y);}ctx.stroke();
  if(progress>.98){const end=cubicPoint(points,1),prev=cubicPoint(points,.98),angle=Math.atan2(end.y-prev.y,end.x-prev.x);ctx.translate(end.x,end.y);ctx.rotate(angle);line(-15,-7,0,0,color,2.2);line(-15,7,0,0,color,2.2);}
  ctx.restore();
  if(active&&progress>.98){
   // A continuous directional highlight, not countable energy/entropy packets.
   const head=(t*.12)%1,tail=Math.max(0,head-.18);ctx.save();ctx.globalAlpha*=alpha*.6;ctx.strokeStyle=color;ctx.lineWidth=4.5;ctx.lineCap='round';ctx.beginPath();
   for(let i=0;i<=24;i++){const q=cubicPoint(points,mix(tail,head,i/24));if(i===0)ctx.moveTo(q.x,q.y);else ctx.lineTo(q.x,q.y);}ctx.stroke();ctx.restore();
  }
 }
 function drawEnergy(s){
  const t=s.t,intro=G(t,102,106),end=G(t,133,134.4),a=intro*(1-end),unit=G(t,106,108.3);
  const coldRoute=[[750,424],[865,424],[875,486],[1015,486]],hotRoute=[[1175,486],[1300,486],[1380,486],[1570,486]];
  if(a>.001){
   circle(1095,486,72,C.line,a*unit,1.8);circle(1095,486,58,C.cyan,a*unit*.5,1.5);
   if(unit>0){line(1068,486,1122,486,C.cyan,2,a*unit);line(1095,459,1095,513,C.cyan,2,a*unit);}
   txt('制冷系统',1095,385,29,C.white,a*unit,'center');
   line(1095,742,1095,562,C.white,2.6,a*(.15+.85*unit));
   line(1087,578,1095,562,C.white,2,a*unit);line(1103,578,1095,562,C.white,2,a*unit);
   box(1075,716,40,33,5,null,C.white,a*unit,2);line(1085,749,1085,763,C.white,2,a*unit);line(1105,749,1105,763,C.white,2,a*unit);
   txt('电能输入',1095,803,28,C.white,a*unit,'center');
   flowPath(coldRoute,Math.max(.01,G(t,109,112)),C.amber,a*(.12+.88*G(t,109,109.6)),t,t>=112);
   flowPath(hotRoute,Math.max(.01,G(t,112,115)),C.amber,a*(.12+.88*G(t,112,112.6)),t,t>=115);
   txt('从内部吸热',864,389,28,C.amber,a*G(t,109.2,110),'center');
   txt('向环境排热',1430,427,28,C.amber,a*G(t,112.2,113),'center');
   // Receiving environment is an outlined region, not a visible heat substance.
   line(1600,348,1680,348,C.dim,1.4,a);line(1680,348,1680,650,C.dim,1.4,a);line(1600,650,1680,650,C.dim,1.4,a);
  }
  const local=G(t,118,120.6)*(1-G(t,133,134.4));
  if(local>0){
   const cp=s.cup,cx=cp.x;
   bracket(cx-93*cp.scale,cp.y-174*cp.scale,194*cp.scale,174*cp.scale,local,C.cyan);
   txt('从水到冰：水的熵 ↓',575,803,29,C.cyan,local,'center');
  }
  const whole=G(t,121.2,125.8)*(1-G(t,133,134.4));
  if(whole>0){
   box(143,180,1630,655,16,null,C.muted,whole*.55,1.5);bracket(143,180,1630,655,whole*.5,C.muted);
   txt('水＋冰箱＋相关环境',1080,258,30,C.muted,whole,'center');
   txt('相关整体总熵 ↑',1480,740,34,C.cyan,G(t,126.5,130)*(1-G(t,133,134.4)),'center');
  }
  const trace=G(t,135,138);
  if(trace>0){
   // A record of the completed process; animated flow has ended.
   line(1200,702,1585,702,C.dim,1.4,trace);
   line(1270,692,1270,712,C.muted,1.5,trace);line(1510,692,1510,712,C.amber,1.5,trace);
   txt('用过电 · 向环境排过热',1400,765,27,C.muted,trace,'center');
  }
 }
 function diagramParticle(label,x,y,r,alpha=1,highlight=false,labelSize=null){
  circle(x,y,r,C.cyan,alpha*(highlight?.15:.07));circle(x,y,r,C.cyan,alpha*(highlight?1:.75),1.5);
  txt(label,x,y+(labelSize||r)*.37,labelSize||Math.max(12,r*1.04),C.white,alpha,'center',MONO);
 }
 function configuration(x,y,w,h,left,alpha=1,highlight=false){
  ctx.save();ctx.globalAlpha*=alpha;box(x-w/2,y-h/2,w,h,7,highlight?'#15303c':'#0b1922',highlight?C.cyan:C.line,1,highlight?1.9:1.2);
  line(x,y-h/2+10,x,y+h/2-10,C.dim,1,highlight?.9:.6);
  const groups=[left,'ABCDEF'.split('').filter(c=>!left.includes(c))];
  groups.forEach((group,side)=>group.forEach((label,i)=>{
   const full=group.length===6;
   const px=x+(side?1:-1)*w*.25+(full?(i%2?1:-1)*w*.085:0);
   const py=y+(full?(Math.floor(i/2)-1)*h*.25:(i-(group.length-1)/2)*h*.25);
   diagramParticle(label,px,py,Math.max(8,Math.min(w/18,h/9)),1,highlight);
  }));ctx.restore();
 }
 function countLabel(prefix,num,x,y,alpha,size=36){
  ctx.save();ctx.font=`400 27px ${FONT}`;const a=ctx.measureText(prefix).width;ctx.font=`400 ${size}px ${FONT}`;const b=ctx.measureText(num+'种').width;
  const left=x-(a+b)/2;txt(prefix,left,y,27,C.muted,alpha);txt(num+'种',left+a,y,size,C.cyan,alpha);ctx.restore();
 }
 function drawModels(s){
  const t=s.t,a=s.modelAlpha;if(a<=0)return;const p=s.modelPose,u=s.statsMove;
  ctx.save();ctx.globalAlpha*=a;
  const titleX=mix(800,1180,u),titleY=mix(278,214,u),movingLabels=1-G(u,0,.2)*(1-G(u,.8,1));
  txt('教学模型 · 仅统计左右分配',titleX,titleY,mix(26,23,u),C.muted,movingLabels,'center');
  box(p.x-p.w/2,p.y-p.h/2,p.w,p.h,10,'#0b1b26',C.dim,1,1.5);
  line(p.x,p.y-p.h/2+14,p.x,p.y+p.h/2-14,C.dim,1.5,.8);
  bracket(p.x-p.w/2,p.y-p.h/2,p.w,p.h,.45);
  s.particles.forEach((d,i)=>{
   const reveal=G(t,28.5+i*.25,29.3+i*.25);
   const highlight=t>=33&&t<35.3?Math.max(0,1-Math.abs((t-33)/2.3*6-i))*.7:0;
   diagramParticle(d.label,p.x+d.x*p.w,p.y+d.y*p.h,mix(25,17,u),reveal,highlight>0,mix(26,22,u));
  });
  if(u>.01)txt('一种具体分配',p.x,p.y-p.h/2-18,24,C.muted,G(t,60,60.8),'center');
  const leftPose=blend({x:1510,y:485,w:240,h:170},{x:320,y:392,w:300,h:200},u);
  leftPose.y-=110*Math.sin(Math.PI*u);
  const leftAlpha=G(t,35.3,37.3);
  if(leftAlpha>0){
   configuration(leftPose.x,leftPose.y,leftPose.w,leftPose.h,['A','B','C','D','E','F'],leftAlpha,false);
   txt('全部在左',leftPose.x,leftPose.y-leftPose.h/2-26,27,C.muted,leftAlpha*movingLabels,'center');
   countLabel('全部在左：','1',leftPose.x,mix(660,565,u),G(t,38,40.3)*movingLabels,mix(38,48,u));
  }
  if(t>=47.2&&t<58)txt('三左三右',p.x,683,29,C.cyan,G(t,47.2,48.2),'center');
  for(let i=0;i<s.cards.length;i++){
   const c=s.cards[i],col=i%5,row=Math.floor(i/5);
   const target={x:796+col*201,y:348+row*115,w:182,h:94};
   let loc=target;
   if(i<3){loc=blend({x:650+i*255,y:754,w:215,h:102},target,u);loc.x+=140*Math.sin(Math.PI*u);}
   let birth=i===0?49.5:i===1?52:i===2?54:58.4+(i-3)/17*3.6;
   const reveal=G(t,birth,birth+.28);
   const selected=i===2||(t>71&&t<74.6&&i===8);
   configuration(loc.x,loc.y,loc.w,loc.h,c.left,reveal,selected);
  }
  if(t>=62)countLabel('三左三右：','20',1198,784,G(t,62,64),52);
  const group=G(t,69,71);
  if(group>0){
   box(684,278,1030,478,14,null,C.cyan,group*.55,1.7);
   txt('同一种宏观分布',1198,260,28,C.cyan,group,'center');
  }
  const entropy=G(t,75.3,77.3);
  if(entropy>0){txt('熵',563,535+18*(1-entropy),84,C.cyan,entropy,'center');line(563,557,563,585,C.cyan,1.4,entropy*.5);}
  ctx.restore();
 }
 let seed=61703;function random(){seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;}
 const cloud=Array.from({length:250},()=>({x:random(),y:random(),vx:(random()-.5)*.055,vy:(random()-.5)*.055,r:1.6+random()*1.8}));
 function drawMacro(s){
  const a=s.macroAlpha;if(a<=0)return;const t=s.t;
  ctx.save();ctx.globalAlpha*=a;
  glow(960,505,470,.07);box(380,314,1160,384,12,'#0b1b26',C.muted,.7,1.5);
  cloud.forEach(d=>{const reflect=v=>1-Math.abs((v%2+2)%2-1);const x=414+reflect(d.x+d.vx*(t-83.2))*1092,y=343+reflect(d.y+d.vy*(t-83.2))*326;circle(x,y,d.r,C.cyan,.5);});
  bracket(380,314,1160,384,.7,C.muted);
  txt('宏观系统示意',960,283,28,C.muted,1,'center');
  const label=G(t,86,90);txt('不与外界交换物质和能量',960,773,32,C.cyan,label,'center');
  // No numeric entropy trace: this is a scale/isolated-boundary diagram.
  for(const x of [300,1620]){line(x-22,505,x+22,505,C.dim,1.5,label);line(x-8,495,x+8,515,C.muted,1.8,label);line(x+8,495,x-8,515,C.muted,1.8,label);}
  ctx.restore();
 }
 function navigation(s){
  const nav=s.navigation;if(!nav.visible)return;const size=mix(23,29,nav.expand),gap=mix(32,43,nav.expand),y=mix(126,140,nav.expand);
  let x=112;const spans=[];
  for(let i=0;i<story.phases.length;i++){
   const label=story.phases[i].name;ctx.font=`400 ${size}px ${FONT}`;const width=ctx.measureText(label).width;spans.push({x,w:width});
   txt(label,x,y,size,i===nav.index?C.cyan:C.muted,nav.alpha*(i===nav.index?1:i<nav.index?.72:.42));
   if(i<story.phases.length-1)line(x+width+gap*.33,y-7,x+width+gap*.67,y-7,C.dim,1,nav.alpha*.65);
   x+=width+gap;
  }
  const lo=Math.floor(nav.underline),hi=Math.min(spans.length-1,lo+1),q=nav.underline-lo;
  const left=mix(spans[lo].x,spans[hi].x,q),width=mix(spans[lo].w,spans[hi].w,q);
  line(left,y+13,left+width,y+13,C.cyan,2,nav.alpha*.85);
 }
 function richLine(value,x,y,size,alpha,keys){
  ctx.font=`400 ${size}px ${FONT}`;let cursor=x-ctx.measureText(value).width/2;
  const sorted=[...keys].sort((a,b)=>b.length-a.length);
  for(let i=0;i<value.length;){const key=sorted.find(k=>value.startsWith(k,i)),part=key||value[i];txt(part,cursor,y,size,key?C.cyan:C.white,alpha);ctx.font=`400 ${size}px ${FONT}`;cursor+=ctx.measureText(part).width;i+=part.length;}
 }
 function captions(s){
  for(const cue of s.captions){const lines=cue.text.split('\n'),ys=lines.length===1?[935]:[890,958];lines.forEach((text,i)=>richLine(text,960,ys[i],52,cue.alpha,cue.emphasis||[]));}
 }
 function renderFrame(frame){
  const s=timeline.stateAtFrame(frame);bounds=[];
  background(s);drawLife(s);drawModels(s);drawMacro(s);navigation(s);
  if(s.t>=142.3)txt(story.brief.title,760,294+15*(1-G(s.t,142.3,143.5)),76,C.white,G(s.t,142.3,143.5),'center');
  captions(s);
  window.filmDiagnostics={frame:s.frame,time:s.t,shotId:s.shotId,phaseId:s.phaseId,textBounds:bounds,cardIds:s.cards.map(c=>c.card_id),solidFraction:s.solidFraction};
  document.getElementById('seek').value=s.frame;
  const minutes=Math.floor(s.t/60),seconds=(s.t%60).toFixed(2).padStart(5,'0');
  document.getElementById('time').textContent=`${String(minutes).padStart(2,'0')}:${seconds} / 02:30`;
  return {frame:s.frame,shotId:s.shotId};
 }
 window.renderFrame=renderFrame;window.stateAtFrame=timeline.stateAtFrame;
 let playing=false,startFrame=0,origin=0,raf=0;const play=document.getElementById('play'),seek=document.getElementById('seek');seek.max=timeline.totalFrames-1;
 function pause(){playing=false;cancelAnimationFrame(raf);play.textContent='播放';}
 function tick(now){if(!playing)return;const f=startFrame+Math.floor((now-origin)*timeline.fps/1000);renderFrame(f);if(f>=timeline.totalFrames-1){pause();return;}raf=requestAnimationFrame(tick);}
 function start(){if(window.filmDiagnostics.frame>=timeline.totalFrames-1)renderFrame(0);startFrame=window.filmDiagnostics.frame;origin=performance.now();playing=true;play.textContent='暂停';raf=requestAnimationFrame(tick);}
 play.onclick=()=>playing?pause():start();seek.addEventListener('input',e=>{pause();renderFrame(Number(e.target.value));});document.getElementById('restart').onclick=()=>{pause();renderFrame(0);start();};
 window.addEventListener('keydown',e=>{if(e.code==='Space'){e.preventDefault();playing?pause():start();}if(e.code==='ArrowLeft'||e.code==='ArrowRight'){e.preventDefault();pause();renderFrame(window.filmDiagnostics.frame+(e.code==='ArrowLeft'?-1:1));}});
 for(const phase of story.phases){const b=document.createElement('button');b.textContent=phase.name;const first=story.shots.find(s=>s.phase_id===phase.id);b.onclick=()=>{pause();renderFrame(first.start_s*timeline.fps);};document.querySelector('.chapters').append(b);}
 renderFrame(Number(new URLSearchParams(location.search).get('frame'))||0);window.filmReady=true;
})();
