import io
import textwrap
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont

from .models import Category

FONTS_DIR = Path(__file__).resolve().parent / 'fonts'

SCALE = 2
WIDTH, HEIGHT = 900, 675

CATEGORY_COLORS = {
    Category.Kind.CPU: (79, 140, 255),
    Category.Kind.MOTHERBOARD: (34, 197, 94),
    Category.Kind.RAM: (168, 85, 247),
    Category.Kind.GPU: (239, 68, 68),
    Category.Kind.STORAGE: (245, 158, 11),
    Category.Kind.PSU: (6, 182, 212),
    Category.Kind.CASE: (100, 116, 139),
}

BRAND_COLORS = {
    'AMD': (237, 28, 36), 'Intel': (0, 113, 197), 'ASUS': (255, 255, 255), 'MSI': (255, 59, 59),
    'Gigabyte': (255, 140, 0), 'Kingston': (255, 59, 59), 'Corsair': (255, 214, 0), 'G.Skill': (255, 59, 59),
    'Samsung': (20, 40, 160), 'Sapphire': (0, 102, 204), 'be quiet!': (255, 152, 0), 'Seasonic': (0, 170, 255),
    'DeepCool': (0, 200, 255), 'Lian Li': (255, 255, 255), 'NZXT': (152, 81, 255), 'WD': (0, 160, 220),
}

DARK = (11, 18, 32)
WHITE = (255, 255, 255)


def font(weight, size):
    return ImageFont.truetype(str(FONTS_DIR / f'Inter-{weight}.ttf'), size * SCALE)


def s(value):
    return int(value * SCALE)


def gradient_background(color):
    w, h = s(WIDTH), s(HEIGHT)
    d = int((w ** 2 + h ** 2) ** 0.5)
    mask = Image.linear_gradient('L').resize((d, d)).rotate(-50)
    mask = mask.crop(((d - w) // 2, (d - h) // 2, (d - w) // 2 + w, (d - h) // 2 + h))
    return Image.composite(Image.new('RGB', (w, h), DARK), Image.new('RGB', (w, h), color), mask)


def draw_icon(draw, kind, ox, oy, k):
    def p(x, y):
        return ox + x * k, oy + y * k

    def rect(x1, y1, x2, y2, width=0, radius=0, fill=None):
        draw.rounded_rectangle([p(x1, y1), p(x2, y2)], radius=radius * k, fill=fill,
                               outline=None if fill else WHITE, width=int(width * k))

    def line(x1, y1, x2, y2, width):
        draw.line([p(x1, y1), p(x2, y2)], fill=WHITE, width=int(width * k))

    def circle(cx, cy, r, width=0, fill=None):
        draw.ellipse([p(cx - r, cy - r), p(cx + r, cy + r)], fill=fill,
                     outline=None if fill else WHITE, width=int(width * k))

    if kind == Category.Kind.CPU:
        rect(110, 70, 210, 170, width=8, radius=10)
        rect(135, 95, 185, 145, fill=WHITE, radius=4)
        for x in (130, 160, 190):
            line(x, 52, x, 70, 6)
            line(x, 170, x, 188, 6)
        for y in (90, 120, 150):
            line(92, y, 110, y, 6)
            line(210, y, 228, y, 6)
    elif kind == Category.Kind.MOTHERBOARD:
        rect(90, 55, 230, 185, width=8, radius=8)
        rect(110, 75, 155, 120, fill=WHITE)
        rect(170, 75, 180, 165, fill=WHITE)
        rect(190, 75, 200, 165, fill=WHITE)
        rect(110, 140, 155, 150, fill=WHITE)
        rect(110, 158, 155, 168, fill=WHITE)
    elif kind == Category.Kind.RAM:
        rect(70, 95, 250, 150, width=8, radius=6)
        for x in (88, 118, 148, 178, 208):
            rect(x, 108, x + 22, 136, fill=WHITE)
        for x in range(85, 250, 15):
            line(x, 150, x, 168, 5)
    elif kind == Category.Kind.GPU:
        rect(65, 80, 255, 165, width=8, radius=10)
        circle(120, 122, 26, width=7)
        circle(200, 122, 26, width=7)
        rect(85, 165, 165, 177, fill=WHITE)
    elif kind == Category.Kind.STORAGE:
        rect(70, 100, 250, 145, width=8, radius=6)
        rect(90, 113, 130, 133, fill=WHITE)
        rect(140, 113, 180, 133, fill=WHITE)
        circle(225, 123, 7, fill=WHITE)
    elif kind == Category.Kind.PSU:
        rect(90, 65, 230, 180, width=8, radius=8)
        circle(160, 122, 36, width=7)
        line(160, 92, 160, 152, 5)
        line(130, 122, 190, 122, 5)
        line(139, 101, 181, 143, 5)
        line(181, 101, 139, 143, 5)
    else:
        rect(115, 45, 205, 195, width=8, radius=8)
        circle(160, 80, 8, fill=WHITE)
        for y in (110, 125, 140):
            line(135, y, 185, y, 5)


def spec_chips(product):
    chips = []
    if product.socket:
        chips.append(product.socket)
    if product.memory_type:
        chips.append(product.memory_type)
    if product.form_factor:
        chips.append(product.form_factor)
    if product.psu_power:
        chips.append(f'{product.psu_power} W')
    elif product.power_draw >= 20:
        chips.append(f'{product.power_draw} W')
    for line in product.specs.splitlines():
        if ':' in line and len(chips) < 4:
            value = line.split(':', 1)[1].strip()
            if len(value) <= 18 and value not in chips:
                chips.append(value)
            break
    return chips[:4]


def fit_title(draw, text, max_width):
    for size in (46, 42, 38, 34, 30):
        f = font('ExtraBold', size)
        for width in (22, 26, 30, 36, 44):
            lines = textwrap.wrap(text, width=width)
            if len(lines) <= 2 and all(draw.textlength(line, font=f) <= max_width for line in lines):
                return f, lines
    f = font('ExtraBold', 30)
    return f, textwrap.wrap(text, width=44)[:2]


def render_product_image(product):
    kind = product.category.kind
    color = CATEGORY_COLORS.get(kind, (79, 140, 255))
    img = gradient_background(color)

    deco = Image.new('RGBA', img.size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(deco)
    for i, y in enumerate((150, 230, 310)):
        x0 = s(560 + i * 40)
        dd.line([(x0, s(y)), (s(700 + i * 30), s(y)), (s(760 + i * 30), s(y - 60)), (s(WIDTH), s(y - 60))],
                fill=(255, 255, 255, 40), width=s(3))
        dd.ellipse([x0 - s(7), s(y) - s(7), x0 + s(7), s(y) + s(7)], outline=(255, 255, 255, 60), width=s(3))
    img = Image.alpha_composite(img.convert('RGBA'), deco).convert('RGB')
    draw = ImageDraw.Draw(img, 'RGBA')

    label = product.category.name.upper()
    f_label = font('Bold', 18)
    tw = draw.textlength(label, font=f_label)
    draw.rounded_rectangle([s(36), s(32), s(36) + tw + s(36), s(72)], radius=s(20), fill=(255, 255, 255, 46))
    draw.text((s(54), s(41)), label, font=f_label, fill=WHITE)

    if product.discount_percent:
        sale = f'-{product.discount_percent}%'
        f_sale = font('ExtraBold', 24)
        sw = draw.textlength(sale, font=f_sale)
        draw.rounded_rectangle([s(WIDTH - 36) - sw - s(32), s(30), s(WIDTH - 36), s(76)], radius=s(12),
                               fill=(220, 38, 38))
        draw.text((s(WIDTH - 36) - sw - s(16), s(38)), sale, font=f_sale, fill=WHITE)

    draw_icon(draw, kind, s(285), s(55), 1.2 * SCALE)

    panel_top = 370
    draw.rounded_rectangle([s(28), s(panel_top), s(WIDTH - 28), s(HEIGHT - 28)], radius=s(24), fill=(8, 12, 24, 190))

    brand_color = BRAND_COLORS.get(product.brand.name, (143, 179, 255))
    draw.rounded_rectangle([s(56), s(panel_top + 30), s(62), s(panel_top + 58)], radius=s(3), fill=brand_color)
    draw.text((s(74), s(panel_top + 28)), product.brand.name.upper(), font=font('Bold', 24), fill=WHITE)

    f_title, lines = fit_title(draw, product.name, s(WIDTH - 112))
    y = s(panel_top + 76)
    for line in lines:
        draw.text((s(56), y), line, font=f_title, fill=WHITE)
        y += int(f_title.size * 1.18)

    f_chip = font('Bold', 20)
    x, y = s(56), s(HEIGHT - 92)
    for chip in spec_chips(product):
        cw = draw.textlength(chip, font=f_chip)
        if x + cw + s(28) > s(WIDTH - 56):
            break
        draw.rounded_rectangle([x, y, x + cw + s(28), y + s(40)], radius=s(10), fill=(255, 255, 255, 36),
                               outline=(255, 255, 255, 90), width=s(1))
        draw.text((x + s(14), y + s(8)), chip, font=f_chip, fill=WHITE)
        x += cw + s(40)

    final = img.resize((WIDTH, HEIGHT), Image.LANCZOS)
    buffer = io.BytesIO()
    final.save(buffer, format='WEBP', quality=88, method=6)
    return ContentFile(buffer.getvalue())


def generate_product_image(product, force=False):
    if product.image and not force and not product.image.name.startswith('products/generated/'):
        return False
    if product.image:
        product.image.delete(save=False)
    product.image.save(f'generated/{product.slug}.webp', render_product_image(product), save=True)
    return True
