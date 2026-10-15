const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const story=JSON.parse(fs.readFileSync(path.join(__dirname,'../../storyboard.json'),'utf8'));
let createTimeline;
try{({createTimeline}=require('../timeline.js'));}catch(e){if(e.code!=='MODULE_NOT_FOUND')throw e;}
function timeline(data=story){assert.equal(typeof createTimeline,'function','The data-driven timeline must exist');return createTimeline(data);}

// Catches the old 55-second/six-shot limits and incorrect boundary ownership.
test('all fourteen shots and the last frame follow the supplied storyboard',()=>{
 const m=timeline();assert.equal(m.totalFrames,4500);
 for(const s of story.shots){assert.equal(m.stateAtFrame(s.start_s*30).shotId,s.id);assert.equal(m.stateAtFrame(s.end_s*30-1).shotId,s.id);}
 assert.equal(m.stateAtFrame(4499).shotId,'s14');
 assert.deepEqual(m.stateAtFrame(-10),m.stateAtFrame(0));
 assert.deepEqual(m.stateAtFrame(9000),m.stateAtFrame(4499));
 const other=structuredClone(story);other.brief.fps=24;assert.equal(timeline(other).totalFrames,3600);
});

// Catches navigation appearing during the hook or restarting for every shot.
test('navigation expands only on the approved phase events',()=>{
 const m=timeline(),at=t=>m.stateAtFrame(Math.round(t*30));
 assert.equal(at(22).navigation.visible,false);
 assert.equal(at(23.5).navigation.visible,true);
 assert.ok(at(23.5).navigation.expand>.6);
 assert.equal(at(26).navigation.expand,0);
 assert.equal(at(35).navigation.expand,0);
 assert.equal(at(59).phaseId,'p3');assert.ok(at(59).navigation.expand>.6);
 assert.equal(at(61).navigation.expand,0);
});

// Catches a new cup/water state being reset at a scene boundary.
test('the same sample melts, freezes, then stays frozen',()=>{
 const m=timeline();
 for(const [t,want] of [[0,1],[6,0],[12,0],[16,1],[99,1],[149,1]])assert.equal(m.stateAtFrame(t*30).solidFraction,want);
 assert.ok(m.stateAtFrame(3*30).solidFraction>0 && m.stateAtFrame(3*30).solidFraction<1);
});

// Catches swapped identities and accidentally duplicating a particle during a move.
test('six persistent identities settle into the specified assignments',()=>{
 const m=timeline();
 for(const [t,left] of [[40,'ABCDEF'],[48,'ABC'],[51.7,'ABD'],[55,'ABE']]){
  const s=m.stateAtFrame(Math.round(t*30));
  assert.equal(new Set(s.particles.map(p=>p.id)).size,6);
  assert.equal(s.particles.filter(p=>p.side<.5).map(p=>p.label).sort().join(''),left);
 }
});

// Catches drawing twenty random samples instead of all twenty unique combinations.
test('configuration cards reveal the exact twenty supplied assignments',()=>{
 const m=timeline();
 for(const [t,n] of [[49,0],[51.5,1],[53,2],[55,3],[63,20]])assert.equal(m.stateAtFrame(t*30).cards.length,n);
 const cards=m.stateAtFrame(65*30).cards;
 assert.equal(new Set(cards.map(c=>c.left.join(''))).size,20);
 assert.equal(cards[0].left.join(''),'ABC');assert.equal(cards[2].left.join(''),'ABE');assert.equal(cards[19].left.join(''),'DEF');
 for(const c of cards){assert.equal(c.left.length,3);assert.equal(c.right.length,3);assert.equal(new Set([...c.left,...c.right]).size,6);}
});

// Catches wall-clock/mutable playback state and truncated final captions.
test('seeking backwards preserves exact states and the final caption survives',()=>{
 const m=timeline();const frames=[0,180,479,750,1800,2700,3600,4499];
 const snapshots=frames.map(f=>m.stateAtFrame(f));
 for(let i=frames.length-1;i>=0;i--)assert.deepEqual(m.stateAtFrame(frames[i]),snapshots[i]);
 const last=m.stateAtFrame(4499);assert.equal(last.captions.length,1);assert.equal(last.captions[0].alpha,1);
 assert.equal(last.captions[0].text,story.shots.at(-1).subtitles[0].text);
});
