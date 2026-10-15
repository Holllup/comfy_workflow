(function (root) {
  'use strict';
  const FPS = 30, FRAMES = 1650, TOTAL_DOTS = 12000;
  const GRID = 12000, STEP = 2 / GRID;
  const clamp = (v, lo=0, hi=1) => Math.min(hi,Math.max(lo,v));
  const smooth = v => { const x=clamp(v); return x*x*(3-2*x); };
  function raw(x) {
    const z = Math.PI * 1.1 * x;
    const envelope = Math.abs(z)<1e-10 ? 1 : Math.sin(z)/z;
    return envelope*envelope * Math.cos(5*Math.PI*x)**2;
  }
  const cumulative = new Float64Array(GRID+1);
  let norm=0;
  for (let i=1;i<=GRID;i++) {
    norm += (raw(-1+(i-1)*STEP)+raw(-1+i*STEP))*STEP/2;
    cumulative[i]=norm;
  }
  for (let i=0;i<=GRID;i++) cumulative[i]/=norm;
  function density(x) { return x < -1 || x > 1 ? 0 : raw(x)/norm; }
  function cdf(x) {
    if(x<=-1)return 0; if(x>=1)return 1;
    const p=(x+1)/STEP, i=Math.floor(p), f=p-i;
    return cumulative[i]*(1-f)+cumulative[i+1]*f;
  }
  function sampleDots(n, seed=613) {
    let s=seed>>>0;
    const random=()=>{ s=(s+0x6D2B79F5)>>>0;let t=s;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return ((t^(t>>>14))>>>0)/4294967296; };
    const result=[];
    for(let k=0;k<n;k++){
      const u=random();let lo=0,hi=GRID;
      while(hi-lo>1){const mid=(lo+hi)>>1;if(cumulative[mid]<u)lo=mid;else hi=mid;}
      const f=(u-cumulative[lo])/(cumulative[hi]-cumulative[lo]||1);
      result.push(Object.freeze({x:-1+(lo+f)*STEP,y:random(),shine:.65+.35*random()}));
    }
    return result;
  }
  const emissions=[19.5,21,22.5,24,25.5,27,28.5,30,31.5,33];
  const ANCHORS=[0,7,15,25,34,46,55];
  function mapTime(t, scenes) {
    if(t<=scenes[0].start)return 0;
    if(t>=scenes[scenes.length-1].end)return 55;
    const i=scenes.findIndex(sc=>t<sc.end),sc=scenes[i];
    return ANCHORS[i]+(t-sc.start)/(sc.end-sc.start)*(ANCHORS[i+1]-ANCHORS[i]);
  }
  function stateAt(frame) {
    const f=clamp(Math.round(frame),0,FRAMES-1),t=f/FPS;
    let count;
    if(t<7) count=1+Math.floor(35*(t/7));
    else if(t<15) count=36+Math.floor(5964*smooth((t-7)/8));
    else if(t<34) count=6000+emissions.filter(e=>t+1e-8>=e+.45).length;
    else count=6010+Math.floor((TOTAL_DOTS-6010)*smooth((t-34)/10));
    let stage=0;for(const start of [7,15,25,34,46])if(t>=start)stage++;
    return Object.freeze({frame:f,t,count,stage});
  }
  const api={FPS,FRAMES,TOTAL_DOTS,ANCHORS,density,cdf,sampleDots,stateAt,emissions,mapTime,smooth,clamp};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  root.QuantumModel=api;
})(typeof globalThis!=='undefined'?globalThis:this);
