#!/usr/bin/env python3
"""Decode every final video frame and report technical validity/motion diagnostics."""
import hashlib,json,subprocess
from pathlib import Path
from PIL import Image,ImageChops,ImageStat
ROOT=Path(__file__).resolve().parent.parent
story=json.loads((ROOT/'storyboard.json').read_text());spec=story['brief']
video=ROOT/'output/entropy.mp4'
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
streams=probe['streams'];assert len(streams)==1 and streams[0]['codec_type']=='video'
v=streams[0];count_expected=round(spec['duration_s']*spec['fps'])
assert (v['width'],v['height'],v['r_frame_rate'],v['pix_fmt'])==(spec['width'],spec['height'],f"{spec['fps']}/1",'yuv420p')
assert int(v['nb_frames'])==count_expected and abs(float(probe['format']['duration'])-spec['duration_s'])<.002
assert all(v.get(k)=='bt709' for k in ['color_space','color_transfer','color_primaries']), 'Incomplete BT.709 signaling'
decoder=subprocess.Popen(['ffmpeg','-v','error','-i',str(video),'-vf','scale=320:180','-pix_fmt','rgb24','-f','rawvideo','pipe:1'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
size=320*180*3;previous=None;count=0;means=[];blank=[];changes=[];still=0;longest=0
while True:
    buf=bytearray()
    while len(buf)<size:
        chunk=decoder.stdout.read(size-len(buf))
        if not chunk:break
        buf.extend(chunk)
    if not buf:break
    assert len(buf)==size,'Partial decoded frame'
    current=Image.frombytes('RGB',(320,180),bytes(buf)).convert('L');stats=ImageStat.Stat(current)
    means.append(stats.mean[0])
    if stats.extrema[0][1]<35 or stats.stddev[0]<1:blank.append(count)
    if previous is not None:
        delta=ImageStat.Stat(ImageChops.difference(previous,current)).mean[0]
        changes.append({'frame':count,'seconds':round(count/spec['fps'],3),'mean_absolute_difference':round(delta,5)})
        still=still+1 if delta<.006 else 0;longest=max(longest,still)
    previous=current;count+=1
err=decoder.stderr.read().decode();assert decoder.wait()==0,err
assert count==count_expected and not blank,(count,blank[:10])
report={'duration_s':spec['duration_s'],'frames_decoded':count,'width':v['width'],'height':v['height'],'fps':spec['fps'],
        'codec':v['codec_name'],'pixel_format':v['pix_fmt'],'color_space':v['color_space'],'color_transfer':v['color_transfer'],'color_primaries':v['color_primaries'],'audio_streams':0,'blank_frames':blank,
        'mean_luminance_range':[round(min(means),3),round(max(means),3)],
        'largest_frame_changes':sorted(changes,key=lambda d:d['mean_absolute_difference'],reverse=True)[:20],
        'longest_nearly_static_run_s':round(longest/spec['fps'],3),
        'video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),
        'scope':'自动检查覆盖全部编码帧和文件规格。变化量是诊断指标，文字阅读停留不视为故障；视觉审查见 visual_review.md。'}
(ROOT/'review/video_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
