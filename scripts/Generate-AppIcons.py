"""Reproducible authored controller icons; no downloaded artwork or runtime work."""
from pathlib import Path
from PIL import Image,ImageDraw

COLORS={'unified':'#22c8c1','preview-files':'#5aa4ff','preview-mods':'#ac8cff',
        'mod-controls':'#ffb75c','shadow':'#e1ca7c','wicked':'#7ccc80'}

def generate(folder):
    folder.mkdir(parents=True,exist_ok=True)
    for name,color in COLORS.items():
        svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
<rect x="4" y="4" width="120" height="120" rx="28" fill="#102336"/>
<rect x="9" y="9" width="110" height="110" rx="24" fill="none" stroke="{color}" stroke-width="6"/>
<path d="M35 41 Q25 41 22 53 L17 79 Q15 94 28 94 Q35 94 46 82 H82 Q93 94 100 94 Q113 94 111 79 L106 53 Q103 41 93 41 Z" fill="{color}"/>
<path d="M36 54 H46 V63 H55 V73 H46 V82 H36 V73 H27 V63 H36 Z" fill="#102336"/>
<circle cx="89" cy="57" r="6" fill="#102336"/><circle cx="99" cy="70" r="6" fill="#102336"/>
<rect x="58" y="61" width="12" height="5" rx="2" fill="#102336"/></svg>'''
        (folder/(name+'.svg')).write_text(svg+'\n',encoding='utf-8')
        im=Image.new('RGBA',(512,512));d=ImageDraw.Draw(im)
        def rect(box,r,fill,outline=None,width=1):d.rounded_rectangle(tuple(v*4 for v in box),radius=r*4,fill=fill,outline=outline,width=width*4)
        rect((4,4,124,124),28,'#102336');rect((9,9,119,119),24,None,color,6)
        d.polygon([(x*4,y*4)for x,y in [(30,41),(98,41),(106,49),(112,85),(108,94),(98,94),(82,82),(46,82),(30,94),(20,94),(16,85),(22,49)]],fill=color)
        d.rectangle((36*4,54*4,46*4,82*4),fill='#102336');d.rectangle((27*4,63*4,55*4,73*4),fill='#102336')
        for x,y in ((89,57),(99,70)):d.ellipse(((x-6)*4,(y-6)*4,(x+6)*4,(y+6)*4),fill='#102336')
        rect((58,61,70,66),2,'#102336')
        im=im.resize((256,256),Image.Resampling.LANCZOS);im.save(folder/(name+'.png'))
        im.save(folder/(name+'.ico'),sizes=[(16,16),(20,20),(24,24),(32,32),(40,40),(48,48),(64,64),(128,128),(256,256)])

if __name__=='__main__':generate(Path(__file__).with_name('app-icons'))
