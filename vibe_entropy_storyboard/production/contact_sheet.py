#!/usr/bin/env python3
import json,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent.parent
records=json.loads((ROOT/'review/frames.json').read_text())
font=ImageFont.truetype('/System/Library/Fonts/SFNSMono.ttf',16)
def make(selected,name,columns,width):
    height=round(width*9/16);cell_h=height+34
    sheet=Image.new('RGB',(width*columns,math.ceil(len(selected)/columns)*cell_h),(7,15,25));draw=ImageDraw.Draw(sheet)
    for i,r in enumerate(selected):
        x=i%columns*width;y=i//columns*cell_h
        with Image.open(ROOT/'review/frames'/r['file']) as im:sheet.paste(im.resize((width,height),Image.Resampling.LANCZOS),(x,y))
        draw.text((x+12,y+height+8),f"{r['seconds']:06.2f}s  /  {r['frame']:04d}",font=font,fill=(148,175,192))
    sheet.save(ROOT/'review'/name,quality=92)
keys=[3,10.8,18,31,41,48,55,65,78,90,102,115,129,139,147]
selected=[next(r for r in records if abs(r['seconds']-t)<.02) for t in keys]
make(selected,'contact_sheet.jpg',3,640)
for start in range(0,len(records),36):make(records[start:start+36],f'sequence_{start//36+1:02}.jpg',4,480)
print('Created contact sheet and sequential source-frame review pages')
