#!/usr/bin/env python3
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
font=ImageFont.truetype('/System/Library/Fonts/SFNSMono.ttf',16)
records=json.loads((ROOT/'review/frames.json').read_text())
def sheet(selected,name,columns,width):
    height=round(width*9/16);cellh=height+36
    canvas=Image.new('RGB',(columns*width,((len(selected)+columns-1)//columns)*cellh),(8,13,23))
    draw=ImageDraw.Draw(canvas)
    for i,r in enumerate(selected):
        x=(i%columns)*width;y=(i//columns)*cellh
        with Image.open(ROOT/'review/frames'/r['file']) as im:
            canvas.paste(im.resize((width,height),Image.Resampling.LANCZOS),(x,y))
        draw.text((x+12,y+height+8),f"{r['seconds']:05.2f}s   frame {r['frame']:04d}",font=font,fill=(145,169,185))
    canvas.save(ROOT/'review'/name)
keys=[90,300,420,540,690,779,869,1004,1110,1230,1440,1590]
sheet([r for f in keys for r in records if r['frame']==f],'contact_sheet.jpg',3,640)
sheet(records,'all_frames.jpg',4,480)
print('Created contact_sheet.jpg and all_frames.jpg')
