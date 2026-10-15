(function(root){
 'use strict';
 const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
 const ease=x=>{x=clamp(x);return x*x*x*(x*(x*6-15)+10);};
 const mix=(a,b,p)=>a+(b-a)*p;
 const blend=(a,b,p)=>Object.fromEntries(Object.keys(a).map(k=>[k,mix(a[k],b[k],p)]));
 function createTimeline(story){
  const fps=story.brief.fps,totalFrames=Math.round(story.brief.duration_s*fps);
  const byId=Object.fromEntries(story.shots.map(s=>[s.id,s]));
  const progress=(t,a,b)=>ease((t-a)/(b-a));
  const actionProgress=(t,id,i)=>{const a=byId[id].actions[i];return progress(t,a.start_s,a.end_s);};
  const allCues=story.shots.flatMap(s=>s.subtitles);
  const configurations=story.production_notes.counting_model.balanced_assignments;
  const labels=story.production_notes.counting_model.particle_labels;
  function positions(left){
   const right=labels.filter(l=>!left.includes(l));
   return labels.map(label=>{
    const side=left.includes(label)?0:1, group=side?right:left,index=group.indexOf(label);
    let x=(side?1:-1)*.25,y=(index-(group.length-1)/2)*.26;
    if(group.length===6){x=-.25+(index%2?1:-1)*.09;y=(Math.floor(index/2)-1)*.27;}
    return {id:'particle_'+label.toLowerCase(),label,x,y,side};
   });
  }
  const layouts=[positions(labels),...configurations.slice(0,3).map(c=>positions(c.left))];
  function stateAtFrame(input){
   const frame=clamp(Math.round(input),0,totalFrames-1),t=frame/fps;
   const shot=story.shots.find(s=>t>=s.start_s&&t<s.end_s)||story.shots.at(-1);
   const phaseIndex=story.phases.findIndex(p=>p.id===shot.phase_id);
   const captions=allCues.filter(c=>t>=c.start_s&&t<c.end_s).map(c=>({...c,alpha:Math.min(clamp((t-c.start_s)/.2),c.end_s===story.brief.duration_s?1:clamp((c.end_s-t)/.2))}));
   const nav=story.production_notes.navigation;
   const navEvent=nav.events.find(e=>t>=e.start_s&&t<e.end_s);
   const navAge=navEvent?t-navEvent.start_s:0;
   const expand=navEvent?Math.min(ease(navAge/.35),1-ease((t-(navEvent.end_s-.7))/.7)):0;
   const underline=navEvent&&navEvent.start_s!==nav.first_visible_s?mix(Math.max(0,phaseIndex-1),phaseIndex,ease(navAge/.65)):phaseIndex;
   let fp={x:1220,y:495,scale:1};
   fp=blend(fp,{x:1170,y:495,scale:.93},actionProgress(t,'s03',3));
   fp=blend(fp,{x:1750,y:290,scale:.24},actionProgress(t,'s04',0));
   fp=blend(fp,{x:600,y:495,scale:.96},actionProgress(t,'s10',2));
   fp=blend(fp,{x:1480,y:510,scale:.62},actionProgress(t,'s13',1));
   const inside={x:fp.x,y:fp.y+10*fp.scale,scale:.6*fp.scale};
   let cp=blend({x:960,y:710,scale:1.1},inside,actionProgress(t,'s02',1));
   if(t>=byId.s13.start_s)cp=blend({x:600,y:504.6,scale:.576},{x:760,y:710,scale:1.08},actionProgress(t,'s13',1));
   let particles=layouts[0].map(p=>({...p}));
   const moves=[['s06',0],['s06',2],['s06',3]];
   for(let j=0;j<moves.length;j++){
    const u=actionProgress(t,...moves[j]);
    particles=particles.map((p,i)=>({...p,x:mix(p.x,layouts[j+1][i].x,u),y:mix(p.y,layouts[j+1][i].y,u),side:mix(p.side,layouts[j+1][i].side,u)}));
   }
   let cardCount=0;
   if(t>=byId.s06.actions[2].start_s)cardCount=1;
   if(t>=byId.s06.actions[3].start_s)cardCount=2;
   if(t>=byId.s06.actions[3].end_s)cardCount=3;
   if(t>=byId.s07.actions[1].start_s)cardCount=3+Math.floor((configurations.length-3)*actionProgress(t,'s07',1)+1e-8);
   const statsMove=progress(t,byId.s07.start_s,byId.s07.start_s+2.4);
   const modelPose=blend({x:800,y:485,w:1000,h:330},{x:340,y:710,w:350,h:150},statsMove);
   return {
    frame,t,shotId:shot.id,phaseId:shot.phase_id,phaseIndex,captions,
    solidFraction:clamp(1-actionProgress(t,'s01',1)+actionProgress(t,'s03',0)),
    fridge:fp,cup:cp,fridgeAlpha:actionProgress(t,'s02',0),
    modelPose,particles,cards:configurations.slice(0,cardCount).map(c=>({...c,left:[...c.left],right:[...c.right]})),statsMove,
    modelAlpha:actionProgress(t,'s04',2)*(1-actionProgress(t,'s09',0)),
    macroAlpha:actionProgress(t,'s09',1)*(1-actionProgress(t,'s10',1)),
    systemScale:1-.08*actionProgress(t,'s12',1)*(1-actionProgress(t,'s13',1)),
    navigation:{visible:t>=nav.first_visible_s,alpha:progress(t,nav.first_visible_s,nav.first_visible_s+.35)*(1-.45*actionProgress(t,'s14',0)),expand,index:phaseIndex,underline},
   };
  }
  return {story,totalFrames,fps,stateAtFrame,actionProgress,progress};
 }
 const api={createTimeline,clamp,ease,mix,blend};
 if(typeof module!=='undefined')module.exports=api;
 root.EntropyTimeline=api;
})(typeof globalThis==='undefined'?this:globalThis);
