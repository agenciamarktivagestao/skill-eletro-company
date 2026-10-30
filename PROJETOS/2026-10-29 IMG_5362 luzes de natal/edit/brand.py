"""Marca, medidas e utilitários compartilhados da Eletro Company (materiais elétricos e iluminação).

Tudo o que é "regra do cliente" (cores, margem, fonte, tamanhos aprovados)
fica aqui, para os outros scripts só importarem.
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")

# ---------- formato ----------
W, H, FPS = 1080, 1920, 30
SAFE = (91, 100, 988, 1681)          # x0, y0, x1, y1 (inclusive) — nada sai daqui (foto margem_seguranca.jpeg)

# ---------- cores (manual de marca Eletro Company: "Nossas cores" #007800 + #ffffff) ----------
GREEN = (0, 120, 0)                  # #007800 — cor principal (caixas, card final, plaquinha do logo)
GREEN_VIVID = (20, 200, 50)          # #14c832 — verde vivo das capas ("PROMOÇÃO DA ELETRO", "KIT 10"): destaque no vídeo
GREEN_DEEP = (16, 88, 32)            # #105820 — verde escuro da capa "KIT 10" (fundo/gradiente)
GREEN_DARK = (4, 38, 10)             # contorno/sombra do texto verde
WHITE = (255, 255, 255)              # #ffffff — legenda e texto sobre o verde
GRAY = (96, 96, 96)                  # #606060 — página "Tipografia de apoio"
LIGHT = (222, 240, 222)              # texto secundário sobre o verde
INK = (4, 14, 6)                     # quase preto esverdeado — sombra da legenda

# ---------- textos fixos ----------
BRAND = "Eletro Company"
TAGLINE = "Materiais elétricos e iluminação"
REGION = "Londrina e região"
ADDRESS = "Av. Tiradentes, 80 · Londrina"   # manual: Av. Tiradentes, 80 - Jardim Shangri-Lá A
ONLINE = "Loja virtual: entrega em todo o Brasil"
CTA = ""                             # card final SEM botão: só logo, endereço e entrega (pedido da agência em 28/10);
                                     # "cta": "..." no card end volta com o botão branco em pílula
HANDLE = ""                          # @ do Instagram: ainda não informado (o card final sai sem ele)
PHONE = ""

# ---------- legenda (estilo da referência REFERENCIAS/referencia_legenda.mp4) ----------
# Palavras pequenas e limpas no peito, entrando uma a uma (desfocadas → nítidas); a palavra forte vira um
# "lockup": palavra pequena em cima à esquerda, a palavra GRANDE digitada letra a letra e o resto embaixo à direita.
CAPTION_FONT = "Sans Bold"           # Open Sans Bold branca, sombra escura suave
CAPTION_SIZE = 60
SMALL_K = 0.92                       # palavras pequenas em volta da palavra forte
HOOK_K = 1.15                        # gancho (até "hook_end"): tudo 15 % maior
BIG_FONT = "Sans ExtraBold"          # "big": Open Sans ExtraBold branca ("embalamento" da referência)
BIG_K = 2.2
ACCENT_FONT = "Glow"                 # "accents": palavra VERDE-LIMÃO com degradê e brilho, CAIXA-ALTA (pedido da
ACCENT_K = 1.9                       # agência em 28/10, referência "MOTIVAÇÃO"; antes era itálico verde)
STRIKE_FONT = "Sans Bold Italic"     # "strikes": itálico branco riscado pela barra verde ("comprometer")
STRIKE_K = 1.85
KEY_FONT = "Glow"                    # "keywords": verde-limão com brilho, gigante (preço, potência, produto)
KEY_K = 2.2
BOX_FONT = "Title"                   # "boxes": Bebas Neue branca na caixa verde #007800 ("LÂMPADAS TASCHIBRA")
BOX_K = 1.75
LINE_W = 600                         # largura da coluna de palavras normais
LINE_WORDS = 3                       # no máximo 3 palavras por linha
LEADING = 0.16                       # espaço entre linhas (× tamanho da palavra normal)
CAPTION_MAX_LINES = 2                # frase normal: no máximo 2 linhas curtas (troca rápido, como na referência)
CAPTION_MAX_WORDS = 5
LEAD_MAX = 3                         # palavras pequenas antes da palavra forte (o resto vira bloco próprio)
TAIL_MAX = 4                         # palavras pequenas depois da palavra forte
NECK_GAP = 18                        # 1ª linha começa logo abaixo do meio do pescoço (person.json)
CAPTION_CY = 1060                    # centro do bloco quando não há rosto (b-roll, produto em close)
CAPTION_MIN_TOP = 760                # selfeval: sem rosto detectado, nenhuma legenda começa acima disso

# ---------- logo ----------
LOGO_ON_VIDEO = False                # padrão SEM logo no alto durante o vídeo (pedido da agência em 27/10);
                                     # o logo fica só no card final. "logo": true no EDL volta com a plaquinha
LOGO_FILE = "logo_badge.png"         # gerado por make_badge(): logo branco numa plaquinha verde #007800
LOGO_W = 220
LOGO_OPACITY = 1.0
LOGO_POS = "top-center"
LOGO_Y = SAFE[1] + 20                # topo do logo
_BADGE_SIZE = None

# tipos de card que escondem a legenda / o logo
HIDE_CAPTION_TYPES = {"title", "photo", "beforeafter", "end", "price", "colorcard"}
HIDE_LOGO_TYPES = {"title", "topic", "beforeafter", "end", "colorcard"}   # topic/title ficam no alto


# =====================================================================
# Fontes do manual: Open Sans (título) e Bebas Neue (apoio) — assets/fonts, licença OFL
# =====================================================================
FONTS = {
    "Title": "BebasNeue-Regular.ttf",
    "Glow": "ArchivoBlack-Regular.ttf",   # só nas palavras verde-limão (estilo da referência "MOTIVAÇÃO", 28/10)
    "Sans": "OpenSans-SemiBold.ttf",
    "Sans Regular": "OpenSans-Regular.ttf",
    "Sans SemiBold": "OpenSans-SemiBold.ttf",
    "Sans Bold": "OpenSans-Bold.ttf",
    "Sans ExtraBold": "OpenSans-ExtraBold.ttf",
    "Sans Condensed": "OpenSans-CondensedExtraBold.ttf",
    "Sans Italic": "OpenSans-Italic.ttf",
    "Sans SemiBold Italic": "OpenSans-SemiBoldItalic.ttf",
    "Sans Bold Italic": "OpenSans-BoldItalic.ttf",
    "Sans ExtraBold Italic": "OpenSans-ExtraBoldItalic.ttf",
}
_cache = {}


def font(style, size):
    key = (style, int(size))
    if key not in _cache:
        _cache[key] = ImageFont.truetype(os.path.join(ASSETS, "fonts", FONTS[style]), int(size))
    return _cache[key]


# =====================================================================
# Desenho
# =====================================================================
def text_size(text, fnt):
    b = fnt.getbbox(text)
    return b[2] - b[0], b[3] - b[1]


def text_mask(text, fnt, pad=0):
    """Máscara 'L' justa do texto, com origem (offset) do bbox."""
    b = fnt.getbbox(text)
    w, h = b[2] - b[0] + 2 * pad, b[3] - b[1] + 2 * pad
    m = Image.new("L", (max(1, w), max(1, h)), 0)
    ImageDraw.Draw(m).text((pad - b[0], pad - b[1]), text, font=fnt, fill=255)
    return m


def vgradient(size, top, bottom):
    w, h = size
    g = Image.new("RGB", (1, max(2, h)))
    px = g.load()
    for y in range(h):
        t = y / max(1, h - 1)
        px[0, y] = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
    return g.resize((w, h))


def solid_text(text, fnt, color=WHITE, shadow=True, stroke=0, stroke_color=INK, shadow_k=0.55):
    """Texto com sombra suave e (opcional) contorno escuro — o contorno segura a leitura
    sobre o fundo claro e colorido da loja."""
    pad = int(fnt.size * 0.35) + stroke if shadow or stroke else 4
    m = text_mask(text, fnt, pad)
    out = Image.new("RGBA", m.size, (0, 0, 0, 0))
    if shadow:
        sh = m.filter(ImageFilter.GaussianBlur(fnt.size * 0.12))
        layer = Image.new("RGBA", m.size, (0, 0, 0, 0))
        layer.putalpha(sh.point(lambda v: int(min(255, v * shadow_k))))
        out = Image.alpha_composite(out, layer)
    if stroke:
        b = fnt.getbbox(text)
        sm = Image.new("L", m.size, 0)
        ImageDraw.Draw(sm).text((pad - b[0], pad - b[1]), text, font=fnt, fill=255,
                                stroke_width=stroke, stroke_fill=255)
        sl = Image.new("RGBA", m.size, tuple(stroke_color) + (0,))
        sl.putalpha(sm)
        out = Image.alpha_composite(out, sl)
    fill = Image.new("RGBA", m.size, color + (0,))
    fill.putalpha(m)
    return Image.alpha_composite(out, fill), pad


# verde-limão com degradê e brilho (pedido da agência em 28/10, referência "PARE DE / MOTIVAÇÃO / DE ESPERAR"
# e os letreiros verdes do Pinterest): todas as palavras-chave verdes da legenda e as linhas verdes dos cards
LIME_TOP, LIME_MID, LIME_BOT = (232, 255, 120), (172, 242, 52), (88, 204, 22)
LIME_GLOW = (150, 255, 60)


def _lime_layers(text, fnt, pad):
    import numpy as np
    m = text_mask(text, fnt, pad)
    glow = Image.new("RGBA", m.size, (0, 0, 0, 0))
    for r, k in ((0.38, 0.20), (0.13, 0.42)):              # brilho largo e fraco + brilho justo
        g = Image.new("RGBA", m.size, LIME_GLOW + (0,))
        g.putalpha(m.filter(ImageFilter.GaussianBlur(fnt.size * r)).point(lambda v, k=k: int(min(255, v * k))))
        glow.alpha_composite(g)
    bb = m.getbbox() or (0, 0, m.width, m.height)
    t = np.clip((np.arange(m.height) - bb[1]) / max(1, bb[3] - bb[1]), 0, 1)[:, None]
    top, mid, bot = (np.array(c, np.float32) for c in (LIME_TOP, LIME_MID, LIME_BOT))
    col = np.where(t < 0.5, top + (mid - top) * (t / 0.5), mid + (bot - mid) * ((t - 0.5) / 0.5))
    fill = Image.fromarray(np.repeat(col[:, None, :], m.width, axis=1).astype(np.uint8)).convert("RGBA")
    fill.putalpha(m)
    return m, glow, fill


def lime_text(text, fnt, pad=None):
    """Texto verde-limão: degradê vertical (claro em cima → verde embaixo), sombra escura justa (lê na loja
    clara e na camisa branca) e brilho verde em volta. Devolve (imagem, pad)."""
    pad = int(fnt.size * 0.6) if pad is None else pad
    m, glow, fill = _lime_layers(text, fnt, pad)
    out = Image.new("RGBA", m.size, (0, 0, 0, 0))
    sh = Image.new("RGBA", m.size, (2, 18, 4, 0))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(fnt.size * 0.06)).point(lambda v: int(v * 0.7)))
    out.paste(sh, (0, int(fnt.size * 0.04)))
    out.alpha_composite(glow)
    out.alpha_composite(fill)
    return out, pad


def lime_flare(text, fnt, pad=None):
    """Só o brilho (mais forte), para a palavra "acender" quando entra."""
    pad = int(fnt.size * 0.6) if pad is None else pad
    m, glow, _ = _lime_layers(text, fnt, pad)
    g = Image.new("RGBA", m.size, (200, 255, 140, 0))
    g.putalpha(m.filter(ImageFilter.GaussianBlur(fnt.size * 0.09)).point(lambda v: int(min(255, v * 0.9))))
    glow.alpha_composite(g)
    return glow


def rounded(size, radius, fill):
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius, fill=fill)
    return im


def scale_rgba(im, s):
    if abs(s - 1) < 1e-3:
        return im
    w, h = max(1, int(im.width * s)), max(1, int(im.height * s))
    return im.resize((w, h), Image.LANCZOS)


def paste_center(canvas, im, cx, cy, alpha=1.0, boxes=None, tag=None):
    if alpha <= 0.001 or im.width < 1:
        return
    if alpha < 0.999:
        im = im.copy()
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im.putalpha(a)
    x, y = int(round(cx - im.width / 2)), int(round(cy - im.height / 2))
    canvas.alpha_composite(im, (x, y)) if 0 <= x and 0 <= y and x + im.width <= canvas.width and y + im.height <= canvas.height \
        else _safe_composite(canvas, im, x, y)
    if boxes is not None:
        bb = im.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox()
        if bb:
            boxes.append({"tag": tag, "box": [x + bb[0], y + bb[1], x + bb[2] - 1, y + bb[3] - 1]})


def _safe_composite(canvas, im, x, y):
    # paste SEM máscara copia o RGBA como está; com máscara (paste(im, pos, im)) a transparência
    # saía multiplicada por ela mesma e brilho/sombras semitransparentes quase sumiam
    tmp = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    tmp.paste(im, (x, y))
    canvas.alpha_composite(tmp)


def load_logo(kind="original"):
    """kind: 'original' (EC metálico verde + nome verde), 'white' (EC prata + nome branco, versão "Cor Branca"
    do manual), 'black', 'icon' (só o EC), 'icon_white', 'name_white' (só o nome), 'compact_white'
    (EC + "ELETRO COMPANY") ou 'badge'."""
    p = os.path.join(ASSETS, f"logo_{kind}.png")
    return Image.open(p).convert("RGBA") if os.path.exists(p) else None


def _logo_split(alpha):
    """Linha (y) entre o EC e o nome: a 1ª faixa vazia abaixo do meio do EC."""
    rows = (alpha > 40).sum(1)
    ys = np.flatnonzero(rows)
    top = ys[0]
    for y in range(top + 40, ys[-1]):
        if rows[y] == 0:
            return y
    return int(alpha.shape[0] * 0.55)


def make_logos(src=None):
    """Versões do logo a partir do PNG da agência (assets/logo_fonte.png, 1250 px). Igual ao manual:
    'Cor Branca' = EC metálico em prata + nome branco; 'Cor Preta' = EC grafite + nome preto.
    Se vier o vetor (SVG/PDF), exporte um PNG grande no lugar do logo_fonte.png e rode de novo."""
    im = Image.open(src or os.path.join(ASSETS, "logo_fonte.png")).convert("RGBA")
    im = im.crop(im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox())
    a = np.asarray(im, dtype=np.float32)
    al = a[..., 3]
    cut = _logo_split(al)
    lum = (0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2])
    ec = lum[:cut][al[:cut] > 200]
    lo, hi = np.percentile(ec, 2), np.percentile(ec, 98)
    g = np.clip((lum - lo) / max(1.0, hi - lo), 0, 1)

    def build(icon_rgb, name_rgb):
        out = np.zeros_like(a)
        out[..., 3] = al
        out[:cut, :, :3] = icon_rgb[:cut]
        out[cut:, :, :3] = name_rgb
        return Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGBA")

    silver = (150 + 105 * g)[..., None].repeat(3, 2)           # brilho metálico em prata (versão branca)
    graphite = (18 + 70 * g)[..., None].repeat(3, 2)
    versions = {"original": im,
                "white": build(silver, np.array([255, 255, 255], np.float32)),
                "black": build(graphite, np.array([14, 14, 14], np.float32))}
    versions["icon"] = versions["original"].crop((0, 0, im.width, cut))
    versions["icon_white"] = versions["white"].crop((0, 0, im.width, cut))
    versions["name_white"] = versions["white"].crop((0, cut, im.width, im.height))
    # só "ELETRO COMPANY" (sem "materiais elétricos e iluminação"): a plaquinha pequena do vídeo usa o EC + nome
    rows = (al[cut:] > 40).sum(1)
    ys = np.flatnonzero(rows)
    gap = next((y for y in range(ys[0] + 10, ys[-1]) if rows[y] == 0), im.height - cut)
    versions["compact_white"] = versions["white"].crop((0, 0, im.width, cut + gap))
    for k, v in versions.items():
        v = v.crop(v.getchannel("A").point(lambda x: 255 if x > 8 else 0).getbbox())
        v.save(os.path.join(ASSETS, f"logo_{k}.png"))
    return versions


def make_badge(path=None, width=900):
    """Plaquinha do logo durante o vídeo: logo "Cor Branca" (EC prata + "ELETRO COMPANY" branco, sem a linha
    "materiais elétricos e iluminação", que ficaria ilegível pequena) sobre o verde #007800, cantos
    arredondados e sombra leve. Lê sobre o fundo claro e colorido da loja."""
    logo = load_logo("compact_white")
    if logo is None:
        make_logos()
        logo = load_logo("compact_white")
    pad_x, pad_y = int(width * 0.075), int(width * 0.06)
    lw = width - 2 * pad_x
    logo = scale_rgba(logo, lw / logo.width)
    bw, bh = width, logo.height + 2 * pad_y
    m = 24
    out = Image.new("RGBA", (bw + 2 * m, bh + 2 * m), (0, 0, 0, 0))
    sh = Image.new("L", out.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((m, m + 8, m + bw, m + bh + 8), int(bh * 0.16), fill=110)
    out.putalpha(sh.filter(ImageFilter.GaussianBlur(12)))
    out.alpha_composite(rounded((bw, bh), int(bh * 0.16), GREEN + (255,)), (m, m))
    out.alpha_composite(logo, (m + pad_x, m + pad_y))
    out.save(path or os.path.join(ASSETS, "logo_badge.png"))
    return out


def badge_bottom():
    """y da borda de baixo do logo no vídeo (os cards do alto começam abaixo dele)."""
    global _BADGE_SIZE
    if _BADGE_SIZE is None:
        im = load_logo("badge")
        _BADGE_SIZE = im.size if im else (900, 230)
    return LOGO_Y + round(LOGO_W * _BADGE_SIZE[1] / _BADGE_SIZE[0])


def box_text(text, fnt, fg=WHITE, bg=GREEN, radius=None, skew=0.0, pad=(0.30, 0.16), shadow=True):
    """Texto dentro de uma caixa (verde #007800 com texto branco, ou branca com texto verde).
    skew > 0 inclina (itálico)."""
    b = fnt.getbbox(text)
    tw = b[2] - b[0]
    hb = fnt.getbbox("H")
    th = hb[3] - hb[1]
    px, py = int(fnt.size * pad[0]), int(fnt.size * pad[1])
    size = (tw + 2 * px, th + 2 * py)
    r = max(2, int(fnt.size * 0.08)) if radius is None else radius
    im = rounded(size, r, tuple(bg[:3]) + (255,))
    ImageDraw.Draw(im).text((px - b[0], py - hb[1]), text, font=fnt, fill=tuple(fg[:3]) + (255,))
    if skew:
        sh = int(size[1] * skew)
        out = Image.new("RGBA", (size[0] + sh, size[1]), (0, 0, 0, 0))
        out.paste(im, (sh // 2, 0))
        im = out.transform(out.size, Image.AFFINE, (1, skew, -sh / 2, 0, 1, 0), resample=Image.BICUBIC)
    if shadow:
        m = 18
        sd = Image.new("RGBA", (im.width + 2 * m, im.height + 2 * m), (0, 0, 0, 0))
        a = im.getchannel("A").point(lambda v: int(v * 0.45))
        blk = Image.new("RGBA", im.size, (0, 0, 0, 255))
        blk.putalpha(a)
        sd.alpha_composite(blk, (m, m + 6))
        sd = sd.filter(ImageFilter.GaussianBlur(7))
        sd.alpha_composite(im, (m, m))
        im = sd
    return im


def dashed_line(width, progress=1.0, color=WHITE, dot=True, thick=4, dash=12, gap=8, dot_r=16):
    """Linha tracejada com bolinha na ponta (elemento dos títulos do manual de marca)."""
    h = dot_r * 2 + 2
    im = Image.new("RGBA", (width + dot_r * 2 + 2, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cy = h // 2
    end = int(width * clamp01(progress))
    x = 0
    while x < end:
        d.rectangle((x, cy - thick // 2, min(x + dash, end), cy + (thick - 1) // 2), fill=color)
        x += dash + gap
    if dot and progress > 0.0:
        r = dot_r * ease_out_back(clamp01((progress - 0.85) / 0.15))
        if r > 0.5:
            d.ellipse((end - r + dot_r, cy - r, end + r + dot_r, cy + r), fill=color)
    return im


# =====================================================================
# Fundo das telas: verde #007800 com as listras diagonais da capa "TOMADA AQUECENDO?" do manual
# =====================================================================
_bg = {}


def brand_background(t=0.0, stripes=True, color=None):
    """Fundo verde (gradiente #0a8a12 → #105820) com listras diagonais finas que correm devagar."""
    key = (stripes, color)
    if key not in _bg:
        top = tuple(color) if color else (12, 140, 22)
        bot = tuple(int(v * 0.62) for v in color) if color else GREEN_DEEP
        _bg[key] = vgradient((W, H), top, bot).convert("RGBA")
    im = _bg[key].copy()
    if stripes:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        step, off = 46, int(t * 24) % 46
        for x in range(-H - step, W + step, step):
            d.line([(x + off, H), (x + off + H, 0)], fill=(255, 255, 255, 14), width=12)
        im.alpha_composite(lay)
    return im


def bolt(h, color=WHITE):
    """Raio (⚡) desenhado: ícone das capas do manual ("⚡ 40W")."""
    w = int(h * 0.62)
    pts = [(0.62, 0.0), (0.08, 0.56), (0.44, 0.56), (0.30, 1.0), (0.92, 0.38), (0.54, 0.38), (0.74, 0.0)]
    im = Image.new("RGBA", (w + 4, h + 4), (0, 0, 0, 0))
    ImageDraw.Draw(im).polygon([(2 + x * w, 2 + y * h) for x, y in pts], fill=tuple(color) + (255,))
    return im


# =====================================================================
# Easing
# =====================================================================
def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def ease_out_cubic(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp01(x)
    return 3 * x * x - 2 * x * x * x


def ease_out_back(x, s=1.70158):
    x = clamp01(x)
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def elastic(x):
    """Pop elástico (0→1 com overshoot)."""
    x = clamp01(x)
    if x in (0, 1):
        return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi / 3)) + 1


# =====================================================================
# EDL e mapeamento de tempo
# =====================================================================
def load_edl(path="edl.json"):
    with open(path, encoding="utf-8") as f:
        edl = json.load(f)
    edl["_dir"] = os.path.dirname(os.path.abspath(path))
    return edl


def snap(t):
    return round(t * FPS) / FPS


def segments_out(edl):
    """Lista de (src_start, src_end, out_start, out_end) no grid de quadros."""
    res, o = [], 0.0
    for s in edl["segments"]:
        a, b = snap(s["start"]), snap(s["end"])
        if b <= a:
            continue
        res.append((a, b, o, o + (b - a)))
        o += b - a
    return res


def body_duration(edl):
    seg = segments_out(edl)
    return seg[-1][3] if seg else 0.0


def total_duration(edl):
    return body_duration(edl) + snap(edl.get("hold", 0.0))


def total_frames(edl):
    return int(round(total_duration(edl) * FPS))


def src_to_out(t, segs):
    for a, b, oa, ob in segs:
        if a - 1e-6 <= t <= b + 1e-6:
            return oa + (t - a)
    return None


def card_windows(edl, types=None):
    """Janelas (início, fim) dos cards no tempo de saída."""
    wins = []
    body = body_duration(edl)
    for c in edl.get("cards", []):
        if types and c["type"] not in types:
            continue
        if c["type"] == "end":
            wins.append((body, total_duration(edl), c))
        else:
            wins.append((snap(c["at"]), snap(c["at"]) + snap(c["dur"]), c))
    return wins


def opaque_windows(edl):
    """Janelas em que a legenda some."""
    return [(a, b) for a, b, c in card_windows(edl) if c["type"] in HIDE_CAPTION_TYPES]


def load_words(edl):
    """Palavras do transcript mapeadas para o tempo de saída (cortes removidos)."""
    p = os.path.join(edl["_dir"], edl.get("captions", {}).get("words_file", "transcript.json"))
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        tr = json.load(f)
    segs = segments_out(edl)
    out = []
    for w in tr["words"]:
        mid = (w["start"] + w["end"]) / 2
        if src_to_out(mid, segs) is None:
            continue
        s = src_to_out(max(w["start"], 0), segs)
        e = src_to_out(w["end"], segs)
        if s is None:
            s = src_to_out(mid, segs)
        if e is None:
            e = src_to_out(mid, segs) + 0.05
        out.append({"word": w["word"].strip(), "start": s, "end": max(e, s + 0.05), "src": w["start"]})
    return [w for w in out if w["word"]]


def write_bboxes(name, edl, boxes):
    p = os.path.join(edl["_dir"], "bboxes.json")
    data = {}
    if os.path.exists(p):
        with open(p) as f:
            data = json.load(f)
    data[name] = boxes
    with open(p, "w") as f:
        json.dump(data, f)


# =====================================================================
# Onde está a pessoa (person.json, gerado pelo person.py a partir do base.mkv)
# =====================================================================
NECK_K = 0.40            # meio do pescoço ≈ fim do rosto detectado + 0,40 × altura do rosto
HAIR_K = 0.55            # topo da cabeça ≈ início do rosto − 0,55 × altura (cabelo)
_person = {}


def load_person(edl):
    p = os.path.join(edl["_dir"], "person.json")
    if p not in _person:
        _person[p] = json.load(open(p)) if os.path.exists(p) else None
    return _person[p]


def _faces(edl, t0, t1):
    pj = load_person(edl)
    if not pj:
        return []
    fs = pj["faces"]
    a, b = max(0, int(t0 * FPS)), min(len(fs), int(math.ceil(t1 * FPS)) + 1)
    return [f for f in fs[a:b] if f]


def neck_line(edl, t0, t1):
    """y do meio do pescoço (o mais baixo no intervalo). Legenda/preço começam daqui para baixo."""
    fs = _faces(edl, t0, t1)
    return max(f[1] + f[3] * (1 + NECK_K) for f in fs) if fs else None


def head_top(edl, t0, t1):
    """y do topo da cabeça (o mais alto no intervalo). Capa/lista terminam acima disso."""
    fs = _faces(edl, t0, t1)
    return min(f[1] - f[3] * HAIR_K for f in fs) if fs else None


def scale_canvas(im, s, ax, ay):
    """Encolhe o quadro inteiro (RGBA) em torno do ponto (ax, ay)."""
    if s >= 0.999:
        return im
    sm = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(sm, (int(ax - ax * s), int(ay - ay * s)))
    return out
