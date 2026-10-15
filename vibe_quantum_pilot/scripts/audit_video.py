#!/usr/bin/env python3
"""Decode every encoded frame; report dark/blank frames and motion changes."""
import hashlib
import json
import subprocess
from pathlib import Path
from PIL import Image,ImageChops,ImageStat

ROOT=Path(__file__).resolve().parents[1]
video=ROOT/'output/quantum_pilot.mp4'
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
streams=probe['streams'];v=streams[0]
assert len(streams)==1 and v['codec_type']=='video'
assert v['width']==1920 and v['height']==1080 and v['r_frame_rate']=='30/1'
assert int(v['nb_frames'])==1650 and abs(float(probe['format']['duration'])-55)<.001
decode=subprocess.Popen(['ffmpeg','-v','error','-i',str(video),'-vf','scale=320:180','-pix_fmt','rgb24','-f','rawvideo','pipe:1'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
size=320*180*3;count=0;previous=None;diffs=[];means=[];blanks=[];longest_static=0;static_run=0
while True:
    buf=bytearray()
    while len(buf)<size:
        chunk=decode.stdout.read(size-len(buf))
        if not chunk:break
        buf.extend(chunk)
    if not buf:break
    assert len(buf)==size, 'Truncated decoded frame'
    im=Image.frombytes('RGB',(320,180),bytes(buf));gray=im.convert('L');st=ImageStat.Stat(gray)
    means.append(st.mean[0])
    if st.extrema[0][1]<35 or st.stddev[0]<1:blanks.append(count)
    if previous is not None:
        delta=ImageStat.Stat(ImageChops.difference(gray,previous)).mean[0];diffs.append({'frame':count,'mean_abs_delta':round(delta,5)})
        if delta<.006:static_run+=1;longest_static=max(longest_static,static_run)
        else:static_run=0
    previous=gray;count+=1
err=decode.stderr.read().decode();assert decode.wait()==0,err
assert count==1650 and not blanks,(count,blanks)
largest=sorted(diffs,key=lambda x:x['mean_abs_delta'],reverse=True)[:12]
report={'video':str(video),'dimensions':[1920,1080],'duration_seconds':55,'fps':30,'frames_decoded':count,'audio_streams':0,
        'blank_frames':blanks,'mean_luminance_range':[round(min(means),3),round(max(means),3)],
        'largest_frame_changes':largest,'longest_nearly_static_run_seconds':round(longest_static/30,3),
        'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),
        'review_method':'所有编码帧完成解码与空帧扫描；关键画面、转场与字幕另以联系表检查。静止停留用于阅读，变化量仅作诊断。'}
(ROOT/'review/qa_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
