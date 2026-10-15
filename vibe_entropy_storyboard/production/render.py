#!/usr/bin/env python3
"""Capture the authored film at explicit frame numbers and encode silent MP4."""
import argparse,base64,hashlib,json,subprocess,time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser()
parser.add_argument('--url',default='http://127.0.0.1:8767/production/')
parser.add_argument('--review',action='store_true')
parser.add_argument('--start',type=float,default=0)
parser.add_argument('--end',type=float)
parser.add_argument('--output',default='entropy.mp4')
args=parser.parse_args()
source=ROOT/'storyboard.json';story=json.loads(source.read_text())
brief=story['brief'];fps=brief['fps'];total=round(brief['duration_s']*fps)
out=ROOT/'output';review=ROOT/'review';out.mkdir(exist_ok=True);review.mkdir(exist_ok=True)
errors=[]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':brief['width'],'height':brief['height']},device_scale_factor=1)
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(args.url+'?capture=1');page.wait_for_function('window.filmReady===true')
    def capture(frame):
        value=page.evaluate('f=>{window.renderFrame(f);return document.querySelector("canvas").toDataURL("image/png").split(",")[1]}',frame)
        if errors:raise RuntimeError('; '.join(errors))
        return base64.b64decode(value)
    if args.review:
        dest=review/'frames';dest.mkdir(exist_ok=True)
        frames=set(range(0,total,fps*3));frames.add(total-1)
        for s in story['shots']:
            frames.add(round((s['start_s']+s['end_s'])*fps/2))
            frames.update(f for f in [round(s['start_s']*fps)-1,round(s['start_s']*fps),round(s['start_s']*fps)+1] if 0<=f<total)
        for t in [3,10.8,18,31,41,48,55,65,78,90,102,115,129,139,147,23.7,59,95,134,119.5,124,136,149.9]:frames.add(round(t*fps))
        records=[]
        for f in sorted(frames):
            filename=f'frame_{f:05d}.png';(dest/filename).write_bytes(capture(f));records.append({'frame':f,'seconds':f/fps,'file':filename})
        (review/'frames.json').write_text(json.dumps(records,indent=2))
        (out/'poster.png').write_bytes(capture(round(147*fps)))
        print(f'Captured {len(records)} source-frame review images.',flush=True)
    else:
        start=round(args.start*fps);end=min(total,round((args.end if args.end is not None else brief['duration_s'])*fps))
        if not 0<=start<end<=total:raise ValueError('Invalid frame range')
        dest=out/Path(args.output).name;partial=dest.with_suffix('.partial.mp4')
        command=['ffmpeg','-hide_banner','-loglevel','warning','-y','-f','image2pipe','-framerate',str(fps),'-vcodec','png','-i','pipe:0',
                 '-an','-c:v','libx264','-preset','medium','-crf','17','-vf','scale=in_range=full:out_range=tv:out_color_matrix=bt709',
                 '-pix_fmt','yuv420p','-movflags','+faststart','-threads','4','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',
                 '-bsf:v','h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0',
                 '-metadata','title='+brief['title'],str(partial)]
        begin=time.monotonic()
        with (review/(dest.stem+'_encode.log')).open('w') as log:
            encoder=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=log)
            try:
                for f in range(start,end):
                    encoder.stdin.write(capture(f))
                    if (f-start)%150==0:print(f'{f-start+1}/{end-start} frames | {time.monotonic()-begin:.1f}s',flush=True)
                encoder.stdin.close()
                if encoder.wait()!=0:raise RuntimeError('Encoding failed; inspect encode log')
            except BaseException:
                encoder.terminate();encoder.wait();raise
        partial.replace(dest)
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(dest)]))
        streams=probe['streams'];assert len(streams)==1 and streams[0]['codec_type']=='video'
        v=streams[0]
        assert (v['width'],v['height'],v['r_frame_rate'])==(brief['width'],brief['height'],f'{fps}/1')
        assert int(v['nb_frames'])==end-start
        assert all(v.get(k)=='bt709' for k in ['color_space','color_transfer','color_primaries']), 'Incomplete BT.709 signaling'
        assert abs(float(probe['format']['duration'])-(end-start)/fps)<.002
        (review/(dest.stem+'_probe.json')).write_text(json.dumps(probe,ensure_ascii=False,indent=2))
        manifest={'video':str(dest),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'start_frame':start,'end_frame_exclusive':end,
                  'fps':fps,'frames':end-start,'audio_streams':0,'render_elapsed_s':round(time.monotonic()-begin,2),
                  'software':'Authored Canvas 2D; isolated headless Chrome via Playwright; FFmpeg/libx264'}
        (review/(dest.stem+'_render.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
        print('Validated '+str(dest),flush=True)
    browser.close()
