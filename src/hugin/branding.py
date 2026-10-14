"""Original deterministic Hugin mark and a restrained night palette."""
BACKGROUND='#07091c'
CARD='#11152e'
FIELD='#0b1026'
BORDER='#2a3154'
TEXT='#eef0ff'
MUTED='#a6afcf'
ACCENT='#7b69ff'
BLUE='#5a66ff'
ACTIVITY_COLORS={'idle':'#7dd6b2','recording':'#ff8a96','playing':'#7cbbff',
                 'error':'#ffbe73','preparing':ACCENT}


def hugin_icon(size=64,color=ACCENT):
    """Draw our angular raven, wing notch and status jewel at any icon size."""
    from PIL import Image, ImageDraw
    if type(size) is not int or not 16<=size<=512:
        raise ValueError('icon size outside supported range')
    factor=size*4/64
    image=Image.new('RGBA',(size*4,size*4),(0,0,0,0))
    draw=ImageDraw.Draw(image)
    def box(values):return tuple(round(value*factor) for value in values)
    def polygon(values,fill):draw.polygon([box(point) for point in values],fill=fill)
    draw.rounded_rectangle(box((2,2,62,62)),radius=round(17*factor),fill=BACKGROUND,
        outline='#3b3c75',width=max(1,round(factor)))
    draw.rounded_rectangle(box((6,6,58,58)),radius=round(13*factor),fill='#151938')
    # Swept wing, upright head and sharp beak: no lettering or third-party mark.
    polygon(((12,43),(22,28),(32,23),(38,33),(30,46),(19,51)), '#7774d8')
    polygon(((22,47),(26,31),(31,24),(32,17),(40,12),(48,16),(50,24),
             (58,28),(49,32),(45,42),(37,47),(29,43)), '#d7d9ff')
    polygon(((16,43),(29,31),(32,36),(25,44)), '#a6a4ff')
    polygon(((29,30),(33,34),(29,41),(27,38)), BACKGROUND)
    draw.ellipse(box((42,20,45,23)),fill=BACKGROUND)
    draw.ellipse(box((45,45,60,60)),fill=BACKGROUND)
    draw.ellipse(box((48,48,57,57)),fill=color)
    return image.resize((size,size),Image.Resampling.LANCZOS)


def header_backdrop(width,height):
    """Bounded decorative blue horizon; contains no user or application text."""
    from PIL import Image, ImageDraw, ImageFilter
    width=max(1,min(int(width),2048));height=max(1,min(int(height),512))
    image=Image.new('RGBA',(width,height),BACKGROUND)
    glow=Image.new('RGBA',image.size,(0,0,0,0))
    draw=ImageDraw.Draw(glow)
    # Keep the horizon in the unlabelled upper-right area: Tk labels have
    # opaque backgrounds, so a glow behind them would produce dark patches.
    horizon=(width*.43,height*.49,width*1.22,height*1.12)
    draw.arc(horizon,195,340,fill=(104,106,255,230),width=max(4,round(height*.08)))
    glow=glow.filter(ImageFilter.GaussianBlur(max(3,height*.035)))
    mask=Image.new('L',image.size,0)
    ImageDraw.Draw(mask).rectangle((width*.46,0,width,height*.72),fill=255)
    mask=mask.filter(ImageFilter.GaussianBlur(max(3,height*.04)))
    glow.putalpha(Image.composite(glow.getchannel('A'),Image.new('L',image.size),mask))
    return Image.alpha_composite(image,glow)
