const test = require('node:test');
const assert = require('node:assert/strict');
let model;
try { model = require('../model.js'); } catch (e) { if (e.code !== 'MODULE_NOT_FOUND') throw e; }
function api() { assert.ok(model, 'The probability and timeline model must exist'); return model; }

// Catches unnormalised probabilities and negative density.
test('probability integrates to one on the visible detector', () => {
  const m = api(); let area = 0; const n = 20000;
  for (let i = 0; i < n; i++) {
    const p = m.density(-1 + (i + .5) * 2 / n);
    assert.ok(p >= 0 && Number.isFinite(p)); area += p * 2 / n;
  }
  assert.ok(Math.abs(area - 1) < 0.0001, `integral=${area}`);
});

// Catches an accidental incoherent sum that removes the interference minima.
test('symmetric coherent interference has dark fringes between bright fringes', () => {
  const m = api();
  assert.ok(m.density(0) > 1);
  assert.ok(m.density(.1) < 1e-12);
  for (const x of [.03, .27, .46, .72]) assert.ok(Math.abs(m.density(x) - m.density(-x)) < 1e-12);
});

// Catches sampling a uniform distribution while plotting an interference curve.
test('sampled electron positions follow the probability distribution', () => {
  const m = api(); const dots = m.sampleDots(30000, 613);
  const positions = dots.map(d => d.x).sort((a,b) => a-b);
  let maxError = 0;
  for (let i = 0; i < positions.length; i++) maxError = Math.max(maxError, Math.abs((i+1)/positions.length-m.cdf(positions[i])));
  assert.ok(maxError < .012, `empirical CDF error=${maxError}`);
  assert.ok(dots.every(d => d.x >= -1 && d.x <= 1 && d.y >= 0 && d.y <= 1));
});

// Catches reseeding per frame or using wall-clock randomness during a seek.
test('the same seed preserves all existing landing positions when more dots are requested', () => {
  const m = api();
  assert.deepEqual(m.sampleDots(200, 42), m.sampleDots(900, 42).slice(0,200));
  assert.notDeepEqual(m.sampleDots(20, 42), m.sampleDots(20, 43));
});

// Catches a transition resetting the accumulated detector or consuming mutable state.
test('scrubbing never changes a frame and accumulation never deletes an event', () => {
  const m = api(); let previous = -1;
  for (let frame=0; frame<1650; frame++) {
    const s = m.stateAt(frame);
    assert.ok(s.count >= previous); previous=s.count;
    assert.ok(s.count <= m.TOTAL_DOTS);
  }
  const expected = m.stateAt(810);
  m.stateAt(1649); m.stateAt(1);
  assert.deepEqual(m.stateAt(810), expected);
  assert.deepEqual(m.stateAt(-30), m.stateAt(0));
  assert.deepEqual(m.stateAt(5000), m.stateAt(1649));
});

// Catches showing several new detections for a single deliberately slowed event.
test('slow demonstration adds exactly one dot for each of six emissions', () => {
  const m = api();
  for (const t of [25.95,27.45,28.95,30.45,31.95,33.45]) {
    const frame = Math.ceil(t*30);
    assert.equal(m.stateAt(frame).count - m.stateAt(frame-1).count, 1);
  }
  assert.equal(m.stateAt(34*30).count-m.stateAt(25*30).count,6);
});

// Catches flashing the source during the apparatus introduction without a detection.
test('each introduction emission also creates exactly one persistent detector event', () => {
  const m=api();
  for(const t of [19.95,21.45,22.95,24.45]) {
    const f=Math.ceil(t*30);
    assert.equal(m.stateAt(f).count-m.stateAt(f-1).count,1);
  }
  assert.equal(m.stateAt(25*30).count-m.stateAt(19*30).count,4);
});

// Catches changing script timing while animation remains tied to old absolute seconds.
test('external scene timing retimes the same visual states', () => {
  const m=api();assert.equal(typeof m.mapTime,'function');
  const scenes=[{start:0,end:14},{start:14,end:20},{start:20,end:30},{start:30,end:39},{start:39,end:51},{start:51,end:60}];
  assert.equal(m.mapTime(7,scenes),3.5);
  assert.equal(m.mapTime(17,scenes),11);
  assert.equal(m.mapTime(30,scenes),25);
  assert.equal(m.mapTime(60,scenes),55);
});
