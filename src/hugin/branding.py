"""Owned vector geometry and bounded Obsidian surfaces; no external artwork."""
from __future__ import annotations

BACKGROUND = '#080b12'
CARD = '#151a27'
FIELD = '#0e1420'
BORDER = '#303d58'
TEXT = '#e9eef7'
MUTED = '#a5b1c9'
ACCENT = '#5166dd'
BLUE = '#8daaff'
MAX_SURFACE_SIDE = 2048
ACTIVITY_COLORS = {
    'idle':'#8295cb', 'recording':'#a9bdff', 'processing':'#6378e6',
    'playing':'#91a8ed', 'complete':'#cfddff', 'error':'#e9b780',
    'preparing':'#7684b5',
}


def mix(a, b, amount):
    amount = max(0.0, min(1.0, amount))
    first = tuple(int(a[i:i+2], 16) for i in (1,3,5))
    last = tuple(int(b[i:i+2], 16) for i in (1,3,5))
    return '#' + ''.join(f'{round(x+(y-x)*amount):02x}' for x,y in zip(first,last))


def _curve(start, segments):
    """Sample cubic design curves once per rasterization, in normalized units."""
    points = [start]
    for a,b,end in segments:
        for index in range(1,25):
            t=index/24; u=1-t
            points.append(tuple(u**3*start[j]+3*u*u*t*a[j]+3*u*t*t*b[j]+t**3*end[j]
                                for j in (0,1)))
        start=end
    return points


# Two swept facets of the approved Nocturne mark, independent of its material.
_WING = _curve((8,54), (
    ((30,40),(66,17),(93,8)),
    ((82,20),(72,32),(62,39)),
    ((42,51),(23,57),(8,54)),
))
_RAVEN = _curve((15,66), (
    ((34,58),(50,46),(65,41)),
    ((73,37),(80,41),(84,47)),
    ((76,43),(68,48),(63,55)),
    ((56,69),(43,83),(28,91)),
    ((37,80),(44,68),(46,59)),
    ((34,65),(25,69),(15,66)),
))


def raven_mark(size, *, silver=True):
    from PIL import Image, ImageDraw, ImageOps
    if type(size) is not int or not 16 <= size <= 1024:
        raise ValueError('mark size outside supported range')
    extent=size*3
    mask=Image.new('L',(extent,extent))
    draw=ImageDraw.Draw(mask)
    for facet in (_WING,_RAVEN):
        draw.polygon([(x*extent/100,y*extent/100) for x,y in facet],fill=255)
    if silver:
        ramp=Image.linear_gradient('L').resize((extent,extent))
        result=ImageOps.colorize(ramp, '#f4f7ff', '#687ead').convert('RGBA')
        edge=ImageDraw.Draw(result)
        for facet in (_WING,_RAVEN):
            edge.line([(x*extent/100,y*extent/100) for x,y in facet],
                      fill='#cfdcff',width=max(1,extent//250))
    else:
        result=Image.new('RGBA',(extent,extent),TEXT)
    result.putalpha(mask)
    return result.resize((size,size),Image.Resampling.LANCZOS)


def surface_size(width, height):
    """A raster has exactly its requested size; oversized layout is an error."""
    width,height=int(width),int(height)
    if not (1 <= width <= MAX_SURFACE_SIDE and 1 <= height <= MAX_SURFACE_SIDE):
        raise ValueError('surface size outside supported range')
    return width,height


def panel_surface(width, height, *, accent=False, radius=18, strength=0.0, highlighted=False):
    from PIL import Image, ImageDraw, ImageOps
    width,height=surface_size(width,height)
    ramp=Image.linear_gradient('L').resize((width,height))
    top=mix('#1c263a','#304786',strength) if not accent else mix('#253b79','#3f5ab3',strength)
    bottom='#101620' if not accent else '#142042'
    if highlighted:top,bottom='#286894','#163750'
    result=ImageOps.colorize(ramp,top,bottom).convert('RGBA')
    mask=Image.new('L',(width,height))
    ImageDraw.Draw(mask).rounded_rectangle((0,0,width-1,height-1),radius=radius,fill=255)
    result.putalpha(mask)
    ImageDraw.Draw(result).rounded_rectangle((.5,.5,width-1.5,height-1.5),radius=radius,
                          outline='#9bd8ff' if highlighted else mix(BORDER,BLUE,.25+strength*.55),width=1)
    return result


def hugin_icon(size=64,color=ACCENT):
    from PIL import Image, ImageDraw
    if type(size) is not int or not 16 <= size <= 512:
        raise ValueError('icon size outside supported range')
    extent=size*3
    icon=panel_surface(extent,extent,radius=extent*.24,strength=.15)
    mark_size=round(extent*.81)
    mark=raven_mark(min(1024,mark_size))
    if mark.size != (mark_size,mark_size):mark=mark.resize((mark_size,mark_size))
    icon.alpha_composite(mark,(round(extent*.085),round(extent*.065)))
    draw=ImageDraw.Draw(icon)
    # Only this lower-right jewel changes with state; the mark stays stable.
    draw.ellipse((extent*.72,extent*.72,extent*.93,extent*.93),fill=BACKGROUND)
    draw.ellipse((extent*.76,extent*.76,extent*.89,extent*.89),fill=color)
    return icon.resize((size,size),Image.Resampling.LANCZOS)


def backdrop(width, height):
    """Low-resolution soft light plus vector ribbons, generated only on resize."""
    from PIL import Image, ImageDraw, ImageFilter
    width,height=surface_size(width,height)
    result=Image.new('RGBA',(width,height),BACKGROUND)
    small=(max(1,width//4),max(1,height//4))
    glow=Image.new('RGBA',small)
    draw=ImageDraw.Draw(glow);w,h=small
    draw.ellipse((w*.25,-h*.22,w*1.45,h*.45),fill=(40,66,128,100))
    draw.ellipse((-w*.5,h*.1,w*.4,h*.66),fill=(45,65,117,65))
    draw.ellipse((w*.5,h*.75,w*1.5,h*1.2),fill=(42,58,106,55))
    glow=glow.filter(ImageFilter.GaussianBlur(max(8,w*.09)))
    result=Image.alpha_composite(result,glow.resize((width,height),Image.Resampling.BILINEAR))
    ribbons=Image.new('RGBA',result.size);draw=ImageDraw.Draw(ribbons)
    for offset in (0,.15):
        points=_curve((0,22+offset*100),(
            ((29,48+offset*60),(56,22),(100,13+offset*20)),
            ((69,36),(42,61+offset*55),(0,29+offset*100)),
        ))
        draw.polygon([(x*width/100,y*height*.52/100) for x,y in points],fill=(51,76,133,28))
        draw.line([(x*width/100,y*height*.52/100) for x,y in points[:25]],
                  fill=(103,137,208,32),width=max(1,width//750))
    return Image.alpha_composite(result,ribbons)


def ambient_light(width,height,strength):
    """Small cached alpha light; no per-frame rasterization or growing cache."""
    from PIL import Image, ImageDraw, ImageFilter
    width=max(1,min(int(width),1024));height=max(1,min(int(height),512))
    small=(max(1,width//3),max(1,height//3))
    light=Image.new('RGBA',small)
    ImageDraw.Draw(light).ellipse((small[0]*.17,small[1]*.15,small[0]*.83,small[1]*.85),
        fill=(72,94,169,round(12+max(0,min(1,strength))*30)))
    return light.filter(ImageFilter.GaussianBlur(max(2,small[1]*.23))).resize(
        (width,height),Image.Resampling.BILINEAR)
