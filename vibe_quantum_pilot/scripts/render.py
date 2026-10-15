#!/usr/bin/env python3
"""Render deterministic canvas frames in a fresh, headless browser.

Start the local preview server first. No signed-in browser profile is used.
"""
import argparse
import base64
import json
import subprocess
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--url',default='http://127.0.0.1:8766')
parser.add_argument('--review',action='store_true')
parser.add_argument('--start',type=float,default=0)
parser.add_argument('--end',type=float,default=55)
parser.add_argument('--output',default='quantum_pilot.mp4')
args=parser.parse_args()
config=json.loads((ROOT/'scenes.json').read_text())
fps=config['fps']
errors=[]

with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1920,'height':1080},device_scale_factor=1)
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(args.url+'/?capture=1')
    page.wait_for_function('window.filmReady === true')
    def frame_png(frame):
        data=page.evaluate('''f => {
            window.renderFrame(f);
            return document.querySelector('canvas').toDataURL('image/png').split(',')[1];
        }''',frame)
        if errors:
            raise RuntimeError('; '.join(errors))
        return base64.b64decode(data)

    if args.review:
        dest=ROOT/'review'/'frames';dest.mkdir(parents=True,exist_ok=True)
        frames=set(range(0,1650,30))
        for f in [210,450,750,1020,1380]:
            frames.update([f-1,f,f+1])
        frames.update([1590,1649,779,824,869,914,959,1004])
        records=[]
        for f in sorted(frames):
            name=f'frame_{f:04d}.png';(dest/name).write_bytes(frame_png(f))
            records.append({'frame':f,'seconds':f/fps,'file':name})
        (ROOT/'review'/'frames.json').write_text(json.dumps(records,indent=2))
        (ROOT/'output'/'poster.png').write_bytes(frame_png(1590))
        print(f'Captured {len(records)} review frames.',flush=True)
    else:
        start=round(args.start*fps);end=min(1650,round(args.end*fps))
        if not 0<=start<end<=1650:
            raise ValueError('Frame range must be within the 55-second film')
        dest=ROOT/'output'/Path(args.output).name
        partial=dest.with_suffix('.partial.mp4')
        dest.parent.mkdir(exist_ok=True)
        command=['ffmpeg','-hide_banner','-loglevel','warning','-y',
                 '-f','image2pipe','-framerate',str(fps),'-vcodec','png','-i','pipe:0',
                 '-an','-c:v','libx264','-preset','medium','-crf','17',
                 '-vf','scale=in_range=full:out_range=tv:out_color_matrix=bt709',
                 '-pix_fmt','yuv420p','-movflags','+faststart','-threads','4',
                 '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',
                 '-metadata','title='+config['title'],str(partial)]
        begin=time.monotonic()
        with (ROOT/'review'/(dest.stem+'_encode.log')).open('w') as log:
            proc=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=log)
            try:
                for f in range(start,end):
                    proc.stdin.write(frame_png(f))
                    if (f-start)%60==0:
                        print(f'{f-start+1}/{end-start} frames | {time.monotonic()-begin:.1f}s elapsed',flush=True)
                proc.stdin.close()
                if proc.wait()!=0:
                    raise RuntimeError('FFmpeg encoding failed; see review log')
            except BaseException:
                proc.terminate();proc.wait();raise
        partial.replace(dest)
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(dest)]))
        streams=probe['streams']
        assert len(streams)==1 and streams[0]['codec_type']=='video','Unexpected audio or extra streams'
        v=streams[0]
        assert (v['width'],v['height'],v['r_frame_rate'])==(1920,1080,'30/1')
        assert int(v['nb_frames'])==end-start
        assert abs(float(probe['format']['duration'])-(end-start)/fps)<.002
        (ROOT/'review'/(dest.stem+'_probe.json')).write_text(json.dumps(probe,indent=2,ensure_ascii=False))
        print(f'Validated: {dest} ({end-start} frames, no audio)',flush=True)
    browser.close()
