"""Build original, AI-assisted experimental glyphs; no source font or tracing input."""
import json, math
from pathlib import Path
from shapely.geometry import LineString, Point
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT/'sources'))
from design_v02 import G, line, q, curve, oval, box

assert len(G)==24
(ROOT/'sources/v02').mkdir(exist_ok=True)
for ch,parts in G.items():
    (ROOT/'sources/v02'/f'uni{ord(ch):04X}.json').write_text(json.dumps({'character':ch,'advance':1000,'strokes':parts},ensure_ascii=False,indent=2)+'\n')

# Source JSON is exported separately for inspection; design_v02.py defines this study.
def geometry(parts):
    pieces=[]
    for part in parts:
        if 'dot' in part: pieces.append(Point(part['dot']).buffer(part['radius'],quad_segs=10))
        else: pieces.append(LineString(part['points']).buffer(part['width']/2,cap_style='round',join_style='round',quad_segs=8))
    return unary_union(pieces)
def glyph(parts):
    pen=TTGlyphPen(None)
    if not parts: return pen.glyph()
    geom=geometry(parts)
    polys=list(geom.geoms) if geom.geom_type=='MultiPolygon' else [geom]
    for poly in polys:
        poly=orient(poly,sign=1)
        for ring in [poly.exterior,*poly.interiors]:
            pts=[(round(x),round(900-y)) for x,y in ring.coords[:-1]]
            clean=[]
            for p in pts:
                if not clean or p!=clean[-1]: clean.append(p)
            if len(set(clean))<3: continue
            pen.moveTo(clean[0])
            for p in clean[1:]: pen.lineTo(p)
            pen.closePath()
    return pen.glyph()

punct={'。':[oval(500,760,55,55)],'，':[curve((520,700),(535,770),(465,830))],'！':[line((500,220),(495,605)),{'dot':[495,775],'radius':29}],'？':[curve((300,280),(330,100),(560,185)),curve((560,185),(820,300),(520,460)),curve((520,460),(465,505),(490,615)),{'dot':[490,775],'radius':29}]}
allglyphs={**G,**punct}
names={ch:f'uni{ord(ch):04X}' for ch in allglyphs}
fb=FontBuilder(1000,isTTF=True)
fb.setupGlyphOrder(['.notdef','space',*names.values()])
fb.setupCharacterMap({32:'space',**{ord(ch):name for ch,name in names.items()}})
glyphs={'.notdef':glyph([box(220,200,560,620),line((300,290),(700,720)),line((700,290),(300,720))]),'space':glyph([]),**{name:glyph(allglyphs[ch]) for ch,name in names.items()}}
fb.setupGlyf(glyphs)
fb.setupHorizontalMetrics({name:(500 if name=='space' else 1000,g.xMin if hasattr(g,'xMin') else 0) for name,g in glyphs.items()})
fb.setupHorizontalHeader(ascent=900,descent=-100)
fb.setupNameTable({'familyName':'Mood Hanzi Creature','styleName':'Regular','uniqueFontIdentifier':'MoodHanzi-Creature-0.200','fullName':'Mood Hanzi Creature Regular','psName':'MoodHanziCreature-Regular','version':'Version 0.200','licenseDescription':'Unreleased design study. Rights and commercial release subject to human review. No public redistribution license granted.'})
fb.setupOS2(sTypoAscender=900,sTypoDescender=-100,sTypoLineGap=0,usWinAscent=900,usWinDescent=100,fsType=0x0002)
fb.setupPost(); fb.setupMaxp()
# Fixed OpenType timestamp keeps repeated builds reproducible.
fb.font.recalcTimestamp=False
fb.font['head'].created=fb.font['head'].modified=3873484800
fb.save(ROOT/'fonts/MoodHanziCreature-Regular.ttf')
f=TTFont(ROOT/'fonts/MoodHanziCreature-Regular.ttf',recalcTimestamp=False); f.flavor='woff2'; f.save(ROOT/'fonts/MoodHanziCreature-Regular.woff2')
(ROOT/'charset/prototype-v02.txt').write_text(''.join(G)+'\n'+''.join(punct)+'\n')
manifest={'version':'0.2.0','hanzi_count':len(G),'punctuation_count':len(punct),'characters':''.join(allglyphs),'note':'AI-assisted original vector prototype; not a cleared commercial font.'}
(ROOT/'fonts/manifest-v02.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
# Render the compiled TTF, rather than a separate drawing, to verify the deliverable.
im=Image.new('RGB',(1600,1470),'#f7f3e8'); d=ImageDraw.Draw(im)
label='/System/Library/Fonts/STHeiti Light.ttc'
ui=ImageFont.truetype(label,26); title=ImageFont.truetype(label,54); small=ImageFont.truetype(label,22)
font=ImageFont.truetype(str(ROOT/'fonts/MoodHanziCreature-Regular.ttf'),158)
d.text((70,50),'小字生灵 · 字形实验 02',font=title,fill='#183d32')
d.text((72,133),'24 个样字 / 整字拟人 · 偏旁互动 · 细线手写 / 实际字体渲染',font=ui,fill='#597267')
for i,ch in enumerate(G):
    x=70+(i%6)*245; y=205+(i//6)*260
    d.rounded_rectangle((x,y,x+220,y+236),radius=20,fill='#fffdf7',outline='#e4dfd1',width=2)
    d.text((x+31,y+7),ch,font=font,fill='#193e34')
    d.text((x+24,y+193),f'{ch}  U+{ord(ch):04X}',font=small,fill='#78897d')
d.text((72,1285),'日月明，心有笑。',font=ImageFont.truetype(str(ROOT/'fonts/MoodHanziCreature-Regular.ttf'),88),fill='#193e34')
d.text((72,1410),'MOOD HANZI  /  v0.2  /  仅供风格评审，未完成商业发行审核',font=small,fill='#78897d')
im.save(ROOT/'specimens/prototype-v02.png')
print(json.dumps(manifest,ensure_ascii=False))

# Compare identical characters, with both rows rendered from their compiled fonts.
comparison=Image.new('RGB',(1600,720),'#f7f3e8'); cd=ImageDraw.Draw(comparison)
cd.text((70,40),'从表情装饰，到整字的小角色',font=title,fill='#183d32')
cd.text((70,126),'同一组汉字 / 上：第一版　下：第二版 / TTF 实际渲染',font=ui,fill='#597267')
compare_chars='人大小木水心中口'
for row,(filename,rowlabel) in enumerate([('MoodHanziPrototype-Regular.ttf','01'),('MoodHanziCreature-Regular.ttf','02')]):
    y=205+row*235
    cf=ImageFont.truetype(str(ROOT/'fonts'/filename),145)
    cd.text((36,y+52),rowlabel,font=ui,fill='#597267')
    for i,ch in enumerate(compare_chars):
        x=100+i*182
        cd.rounded_rectangle((x,y,x+163,y+206),radius=15,fill='#fffdf7',outline='#e4dfd1')
        cd.text((x+9,y+3),ch,font=cf,fill='#193e34')
        cd.text((x+68,y+168),ch,font=small,fill='#78897d')
comparison.save(ROOT/'specimens/comparison-v01-v02.png')
