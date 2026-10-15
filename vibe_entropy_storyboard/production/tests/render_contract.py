"""Verify rendered pixels, scene boundaries, safe text and the preview clock."""
import hashlib,json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
assert (ROOT/'production/index.html').is_file(), 'The film page must exist'
story=json.loads((ROOT/'storyboard.json').read_text())
fps=story['brief']['fps'];last=round(story['brief']['duration_s']*fps)-1
url=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8767/production/'
samples={0,last}
for s in story['shots']:
    samples.add(round((s['start_s']+s['end_s'])*fps/2))
    samples.update(f for f in [round(s['start_s']*fps)-1,round(s['start_s']*fps),round(s['start_s']*fps)+1] if 0<=f<=last)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1920,'height':1080},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(url+'?capture=1');page.wait_for_function('window.filmReady===true')
    def pixels(frame):
        return page.evaluate('f=>{window.renderFrame(f);return document.querySelector("canvas").toDataURL()}',frame)
    baseline={f:hashlib.sha256(pixels(f).encode()).hexdigest() for f in sorted(samples)}
    for f in sorted(samples,reverse=True):
        assert hashlib.sha256(pixels(f).encode()).hexdigest()==baseline[f],f'Pixel mismatch at {f}'
    bad=[]
    for f in range(0,last+1,15):
        page.evaluate('f=>window.renderFrame(f)',f)
        bounds=page.evaluate('window.filmDiagnostics.textBounds')
        for b in bounds:
            if b['x']<94 or b['right']>1826 or b['top']<94 or b['bottom']>986:bad.append({'frame':f,**b})
    assert not bad, json.dumps(bad[:12],ensure_ascii=False)
    page.goto(url);page.wait_for_function('window.filmReady===true')
    page.locator('#seek').fill('1800');assert page.evaluate('window.filmDiagnostics.frame')==1800
    page.locator('#play').click();page.wait_for_function('window.filmDiagnostics.frame>1804');page.locator('#play').click()
    stopped=page.evaluate('window.filmDiagnostics.frame');page.wait_for_timeout(140)
    assert page.evaluate('window.filmDiagnostics.frame')==stopped
    page.get_by_role('button',name='看整体',exact=True).click()
    assert page.evaluate('window.filmDiagnostics.frame')==94*fps
    assert not errors,errors
    browser.close()
result={'pixel_determinism':'passed','pixel_sample_frames':sorted(samples),'text_bounds':'passed','text_sample_step_frames':15,'preview_controls':'passed','page_errors':errors}
(ROOT/'review/render_contract.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False))
