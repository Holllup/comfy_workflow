"""Integration checks for real pixels, scrubbing, and preview transport.

Breaks caught: wall-clock animation, stale accumulation after backward seek,
missing text, different preview/export clocks, and canvas initialization failure.
"""
import hashlib
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
assert (ROOT / 'index.html').exists(), 'The rendered film page must exist'
url = sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8766'
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1920,'height':1080},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(url+'/?capture=1')
    page.wait_for_function('window.filmReady === true')
    def capture(frame):
        page.evaluate('(f)=>window.renderFrame(f)',frame)
        return page.locator('canvas').screenshot()
    samples=[0,209,210,449,450,749,750,1019,1020,1379,1380,1649]
    baseline={f:hashlib.sha256(capture(f)).hexdigest() for f in samples}
    assert len(set(baseline.values()))>8, 'The film must change over time'
    for f in reversed(samples):
        assert hashlib.sha256(capture(f)).hexdigest()==baseline[f], f'Non-deterministic frame {f}'
    for f in [90,300,600,870,1200,1500]:
        capture(f)
        bounds=page.evaluate('window.filmDiagnostics.textBounds')
        assert bounds and all(b['x']>=94 and b['right']<=1826 and b['top']>=90 and b['bottom']<=986 for b in bounds), (f,bounds)
    page.goto(url)
    page.wait_for_function('window.filmReady === true')
    page.locator('#seek').fill('810')
    assert page.evaluate('window.filmDiagnostics.frame')==810, 'Slider must use the render clock'
    page.locator('#play').click()
    page.wait_for_function('window.filmDiagnostics.frame > 815')
    page.locator('#play').click()
    paused=page.evaluate('window.filmDiagnostics.frame')
    page.wait_for_timeout(160)
    assert page.evaluate('window.filmDiagnostics.frame')==paused, 'Pause must stop the transport'
    assert not errors,errors
    browser.close()
print(json.dumps({'pixel_determinism':'passed','safe_text_bounds':'passed','transport':'passed','frames_checked':samples}))
