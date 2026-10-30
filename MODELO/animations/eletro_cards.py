"""Grafismos Eletro Company → cards/*.mov|.mp4 + cards/index.json

Linguagem visual = manual de marca + "Padrão de Capas": títulos em Bebas Neue CAIXA-ALTA brancos com a parte
forte em VERDE VIVO ("KIT 10"), etiquetas verdes #007800 com Bebas branca ("LÂMPADAS TASCHIBRA"), o ⚡ dos
selos ("⚡ 40W"), apoio em Open Sans, a linha tracejada com bolinha dos títulos do manual e as listras
diagonais da capa "TOMADA AQUECENDO?". Da referência de legenda vêm as telas de cor (colorcard).

Tipos (no EDL, em "cards"; "at"/"dur" no tempo do vídeo FINAL, em segundos):
  topic       capa no alto: etiqueta branca + título em 1–2 linhas (branca / verde vivo) + linha tracejada
              {"type":"topic","at":0.2,"dur":2.2,"kicker":"Eletro Company","lines":["Promoção","relâmpago"],"y":"auto"}
  price       preço de promoção: chamada + "de R$ X" riscado (opcional) + valor gigante na caixa verde + obs.
              Esconde a legenda. SÓ com valor e condição falados/aprovados.
              {"type":"price","at":5,"dur":2.4,"kicker":"promoção","old":"R$ 39,90","value":"R$ 19,90","note":"no Pix"}
  product     painel branco com filete verde: nome do produto (Bebas verde) + detalhe (Open Sans cinza) + selo
              com ⚡ ("24W"). Fica embaixo, na frente; a legenda sobe/encolhe para ficar acima dele.
              {"type":"product","at":3,"dur":2.5,"name":"Plafon de embutir","details":"Inlumix · painel LED","spec":"24W"}
  label       etiqueta verde #007800 inclinada com ⚡ e Bebas branca, com pop; NA FRENTE, embaixo (a legenda fica
              acima dela). "y" opcional; "bolt": false tira o raio
              {"type":"label","at":5,"dur":2,"text":"Entrega para todo o Brasil"}
  tag         caixinha verde pequena (informação secundária)
              {"type":"tag","at":3,"dur":3,"text":"ep 02","x":250,"y":330}
  checklist   lista com quadrado verde vivo e ✓ (ou 1, 2, 3) + caixa verde; cada item no seu tempo (relativo ao card)
              {"type":"checklist","at":6,"dur":5,"title":"Na Eletro","items":[["Cabos",0.3],["Disjuntores",1.2]],"y":"auto"}
              "numbers": true → 1, 2, 3; "place": "below" → na frente, abaixo do pescoço; "align": "center"
  title       palavra GIGANTE (Bebas) atrás da pessoa, com a frase pequena em cima e a 2ª linha verde opcional
              {"type":"title","at":2.6,"dur":2.4,"kicker":"aqui na","line1":"Eletro","line2":"Company","cy":560}
  colorcard   TELA DE COR da referência: tela cheia verde (ou branca) com a fala em letra pequena no centro,
              palavra por palavra (do transcript; ou "text"). Corte seco com som de interruptor.
              {"type":"colorcard","at":4.1,"dur":0.6,"bg":"green"}   ("bg": "white" → fundo branco, texto verde)
  flash       luz acendendo (clarão branco frio, rápido): transição; 1–2 por vídeo
              {"type":"flash","at":5.3,"dur":0.45}
  broll       imagem de apoio (outro vídeo) por cima da fala, sem o som dele
              {"type":"broll","at":6,"dur":3.5,"file":"../IMG_0002.MOV","start":1.2,"zoom":1.0,"anchor":[540,960],"push":1.05}
  photo       foto em tela cheia (entra com desfoque e faz zoom lento)
              {"type":"photo","at":10,"dur":2.5,"file":"fotos/produto.jpg"}
  beforeafter antes e depois com a linha verde varrendo a tela (ex.: ambiente antes/depois da iluminação)
              {"type":"beforeafter","at":12,"dur":3.5,"before":"fotos/antes.jpg","after":"fotos/depois.jpg"}
  end         card final: a fachada da loja em verde fechado (assets/fundo_card_final.jpg, zoom lento), logo,
              linha fina e lisa, endereço / loja virtual / @ (dura o "hold" do EDL). Sem botão por padrão;
              "cta": "..." põe o botão branco em pílula
              {"type":"end","cta":"Garanta o melhor preço","lines":["Av. Tiradentes, 80 · Londrina",
               "Loja virtual: entrega em todo o Brasil"],"handle":""}

Uso:  python animations/eletro_cards.py [edl.json]
"""
import json
import math
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter, ImageOps  # noqa: E402

import brand as B  # noqa: E402
from frames import FrameWriter  # noqa: E402

SAFE_W = B.SAFE[2] - B.SAFE[0]
EDL = None
BEHIND = {"topic", "checklist", "title", "tag"}        # por padrão ficam atrás da pessoa
OFFWHITE = (247, 248, 246)


def place_above_head(c, top, height, default_top):
    """Topo e escala de um bloco que deve ficar ACIMA da cabeça (person.json). Sem dados: padrão."""
    ht = B.head_top(EDL, c["_t0"], c["_t0"] + c["dur"]) if EDL else None
    # com o logo no centro do alto ("logo": true), quem não esconde o logo começa abaixo dele
    logo_on = EDL.get("logo", B.LOGO_ON_VIDEO) if EDL else B.LOGO_ON_VIDEO
    lo = B.SAFE[1] + 8 if (not logo_on or c["type"] in B.HIDE_LOGO_TYPES or B.LOGO_POS != "top-center") \
        else B.badge_bottom() + 18
    if ht is None:
        return max(lo, default_top), 1.0
    avoid = ht - 26
    if avoid - height >= lo:
        return max(lo, min(default_top, avoid - height)), 1.0
    return lo, max(0.72, (avoid - lo) / height)


def below_neck(c, cy, height):
    nk = B.neck_line(EDL, c["_t0"], c["_t0"] + c["dur"]) if EDL else None
    if nk is not None:
        cy = max(cy, nk + 14 + height / 2)
    return min(cy, B.SAFE[3] - 6 - height / 2)


def fit(text, style, size, max_w):
    f = B.font(style, size)
    while f.getlength(text) > max_w and size > 20:
        size -= 2
        f = B.font(style, size)
    return f


def frames_of(dur):
    return int(round(B.snap(dur) * B.FPS))


def fade_out(t, dur, d=0.25):
    return 1 - B.ease_in_out((t - (dur - d)) / d)


def wipe(im, k):
    """Revela a imagem da esquerda para a direita (k 0..1)."""
    w = max(0, int(im.width * B.clamp01(k)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    if w > 0:
        out.paste(im.crop((0, 0, w, im.height)), (0, 0))
    return out


def blur_in(im, k, r=10):
    """Desfocado → nítido (k 0..1), como a entrada das palavras da legenda."""
    rr = r * (1 - B.clamp01(k))
    return im if rr < 0.4 else im.convert("RGBa").filter(ImageFilter.GaussianBlur(rr)).convert("RGBA")


def shadowed(im, k=0.4, dy=6, r=7):
    """Sombra suave por baixo de uma peça (caixas, etiquetas)."""
    m = 18
    sd = Image.new("RGBA", (im.width + 2 * m, im.height + 2 * m), (0, 0, 0, 0))
    blk = Image.new("RGBA", im.size, (0, 0, 0, 255))
    blk.putalpha(im.getchannel("A").point(lambda v: int(v * k)))
    sd.alpha_composite(blk, (m, m + dy))
    sd = sd.filter(ImageFilter.GaussianBlur(r))
    sd.alpha_composite(im, (m, m))
    return sd


def kicker_box(text, size=34, bg=B.WHITE, fg=B.GREEN):
    """Etiqueta pequena: Open Sans ExtraBold CAIXA-ALTA."""
    return B.box_text(text.upper(), B.font("Sans ExtraBold", size), fg=fg, bg=bg, pad=(0.45, 0.32))


def bebas_box(text, size, fg=B.WHITE, bg=B.GREEN, bolt=False, skew=0.0, shadow=True):
    """Caixa verde com Bebas Neue branca (a etiqueta "LÂMPADAS TASCHIBRA" da capa), com ⚡ opcional."""
    f = B.font("Title", size)
    t = text.upper()
    b = f.getbbox(t)
    hb = f.getbbox("H")
    cap = hb[3] - hb[1]
    px, py = int(size * 0.30), int(size * 0.20)
    ic = B.bolt(int(cap * 1.12), color=B.GREEN_VIVID if bg != B.GREEN_VIVID else fg) if bolt else None
    gap = int(size * 0.16) if ic else 0
    w = int((ic.width + gap if ic else 0) + b[2] - b[0] + 2 * px)
    h = cap + 2 * py
    im = B.rounded((w, h), max(4, int(size * 0.14)), tuple(bg) + (255,))
    d = ImageDraw.Draw(im)
    x = px
    if ic:
        im.alpha_composite(ic, (x, int(h / 2 - ic.height / 2)))
        x += ic.width + gap
    d.text((x - b[0], py - hb[1]), t, font=f, fill=tuple(fg) + (255,))
    if skew:
        sh = int(h * skew)
        out = Image.new("RGBA", (w + sh, h), (0, 0, 0, 0))
        out.paste(im, (sh // 2, 0))
        im = out.transform(out.size, Image.AFFINE, (1, skew, -sh / 2, 0, 1, 0), resample=Image.BICUBIC)
    return shadowed(im) if shadow else im


def title_text(text, size, color=B.WHITE, max_w=None):
    """Título das capas: Bebas Neue CAIXA-ALTA; a linha verde sai verde-limão com degradê e brilho (28/10)."""
    f = fit(text.upper(), "Title", size, max_w or SAFE_W - 60)
    if color == B.GREEN_VIVID:
        return B.lime_text(text.upper(), f, pad=int(f.size * 0.45))[0]
    stroke = max(2, int(f.size * 0.03)) if color != B.WHITE else 0
    im, _ = B.solid_text(text.upper(), f, color=color, stroke=stroke, stroke_color=B.GREEN_DARK, shadow_k=0.8)
    return im


def scale_boxes(lb, s, ax, ay):
    if lb and s < 1:
        for bx in lb:
            bx["box"] = [int(ax + (bx["box"][0] - ax) * s), int(ay + (bx["box"][1] - ay) * s),
                         int(ax + (bx["box"][2] - ax) * s), int(ay + (bx["box"][3] - ay) * s)]


# ------------------------------------------------------------------ topic (capa)
def render_topic(c, path):
    dur = c["dur"]
    kick = kicker_box(c.get("kicker", B.BRAND)) if c.get("kicker", "x") else None
    lines = c.get("lines") or [c.get("text", "")]
    imgs = [title_text(l, c.get("size", 170), B.WHITE if i % 2 == 0 else B.GREEN_VIVID) for i, l in enumerate(lines)]
    cx = c.get("x", B.W / 2)
    y = c.get("y", 300) if c.get("y") != "auto" else 300
    items = ([kick] if kick else []) + imgs
    ys, yy = [], y
    for j, im in enumerate(items):
        ov = 0.30 * im.height if (j and items[j] is not kick) else 0.0    # títulos quase encostados
        yy -= ov
        ys.append(yy + im.height / 2)
        yy += im.height
    line_w = int(max(im.width for im in imgs) * 0.7)
    y_ln = yy - 14
    top0, h_blk = y + 12, (y_ln + 18) - (y + 12)
    top, sc = place_above_head(c, top0, h_blk, c.get("y", 300) + 12 if c.get("y") != "auto" else 10 ** 6)
    ys = [v + top - top0 for v in ys]
    y_ln += top - top0
    boxes, n = [], frames_of(dur)
    fw = FrameWriter(path, alpha=True)
    for i in range(n):
        t = i / B.FPS
        im = Image.new("RGBA", (B.W, B.H), (0, 0, 0, 0))
        k_out = B.ease_in_out((t - (dur - 0.3)) / 0.3)
        lb = boxes if i == int(n * 0.5) else None
        for j, (piece, py) in enumerate(zip(items, ys)):
            k = B.ease_out_cubic((t - 0.08 * j) / 0.35)
            if k <= 0:
                continue
            x = cx - 150 * (1 - k) * (1 if j % 2 == 0 else -1)
            pulse = 1 + 0.03 * math.sin(math.pi * B.clamp01((t - dur * 0.5 - 0.05 * j) / 0.4))
            pc = wipe(piece, k * 1.3) if piece is kick else blur_in(piece, k)
            B.paste_center(im, B.scale_rgba(pc, pulse), x - 40 * k_out, py, alpha=min(1, 1.5 * k) * (1 - k_out),
                           boxes=lb, tag=f"capa {j}")
        kl = B.ease_in_out((t - 0.35) / 0.5)
        if kl > 0:
            B.paste_center(im, B.dashed_line(line_w, kl), cx, y_ln, alpha=1 - k_out, boxes=lb, tag="linha")
        if sc < 1:
            im = B.scale_canvas(im, sc, cx, top)
            scale_boxes(lb, sc, cx, top)
        fw.write(im)
    fw.close()
    return boxes, [{"t": 0.0, "kind": "whoosh"}, {"t": 0.35, "kind": "pop"}], True


# ------------------------------------------------------------------ checklist
def render_checklist(c, path):
    dur = c["dur"]
    title = c.get("title", "")
    size = c.get("size", 60)
    items = []
    for it in c["items"]:
        text, at = (it if isinstance(it, (list, tuple)) else (it, None))
        items.append([text, at])
    for k, it in enumerate(items):
        if it[1] is None:
            it[1] = 0.3 + k * 0.6
    head = kicker_box(title, 36) if title else None
    widest = max(items, key=lambda it: B.font("Title", size).getlength(it[0].upper()))[0].upper()
    while size > 34 and B.font("Title", size).getlength(widest) + size * 1.9 > SAFE_W - 40:
        size -= 2                                          # item longo encolhe para caber na margem
    rows = []
    for n_, (text, at) in enumerate(items):
        box = bebas_box(text, size, shadow=False)
        s = box.height
        chk = Image.new("RGBA", (s, s), B.GREEN_VIVID + (255,))
        if c.get("numbers"):
            fn = B.font("Title", int(s * 0.78))
            num = str(n_ + 1)
            bb = fn.getbbox(num)
            ImageDraw.Draw(chk).text(((s - (bb[2] - bb[0])) / 2 - bb[0], (s - (bb[3] - bb[1])) / 2 - bb[1]), num,
                                     font=fn, fill=B.WHITE)
        else:
            ImageDraw.Draw(chk).line([(s * 0.24, s * 0.52), (s * 0.43, s * 0.70), (s * 0.77, s * 0.30)],
                                     fill=B.WHITE, width=max(5, s // 9), joint="curve")
        row = Image.new("RGBA", (s + box.width, s), (0, 0, 0, 0))
        row.paste(chk, (0, 0))
        row.paste(box, (s, 0))
        rows.append((shadowed(row), at))
    wmax = max([r[0].width - 36 for r in rows] + ([head.width - 36] if head else []))
    x0 = c.get("x", (B.W - wmax) / 2 if c.get("align") == "center" else B.SAFE[0] + 10)
    y = c.get("y", 300) if c.get("y") not in ("auto", None) else 300
    step = rows[0][0].height - 36 + 14 if rows else 0
    hy = y
    if head:
        y += head.height - 18
    top0 = hy + 18
    h_blk = (y + (len(rows) - 1) * step + rows[-1][0].height - 18) - top0
    if c.get("place") == "below":                    # na frente, logo abaixo do meio do pescoço
        top = below_neck(c, c.get("y", 0) + h_blk / 2 if isinstance(c.get("y"), (int, float)) else 0, h_blk) - h_blk / 2
        sc = 1.0
    else:
        top, sc = place_above_head(c, top0, h_blk, top0 if c.get("y") != "auto" else 10 ** 6)
    hy += top - top0
    y += top - top0
    boxes, n = [], frames_of(dur)
    fw = FrameWriter(path, alpha=True)
    for i in range(n):
        t = i / B.FPS
        im = Image.new("RGBA", (B.W, B.H), (0, 0, 0, 0))
        out = fade_out(t, dur, 0.3)
        lb = boxes if i == n - 1 - int(0.3 * B.FPS) else None
        if head:
            k = B.ease_out_cubic(t / 0.3)
            B.paste_center(im, wipe(head, k * 1.2), x0 + head.width / 2 - 18, hy + head.height / 2, alpha=out,
                           boxes=lb, tag="lista: título")
        for j, (row, at) in enumerate(rows):
            if t < at:
                continue
            k = B.ease_out_back((t - at) / 0.35, 1.4)
            ry = y + j * step + row.height / 2
            B.paste_center(im, wipe(row, B.clamp01((t - at) / 0.25)), x0 + row.width / 2 - 18 - 60 * (1 - B.clamp01(k)),
                           ry, alpha=out, boxes=lb, tag=f"lista: item {j}")
        if sc < 1:
            im = B.scale_canvas(im, sc, x0, top)
            scale_boxes(lb, sc, x0, top)
        fw.write(im)
    fw.close()
    ev = [{"t": 0.0, "kind": "whoosh"}] + [{"t": at, "kind": "pop"} for _, at in rows]
    return boxes, ev, True


# ------------------------------------------------------------------ price
def vis_box(im):
    """Caixa visível (alfa > 40) da peça: (x0, y0, x1, y1)."""
    return im.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox() or (0, 0, im.width, im.height)


def old_price_line(old, k_strike=1.0):
    """'de R$ 39,90' (branco, riscado pela barra verde vivo) + 'por' (itálico verde-limão com brilho)."""
    f_old, f_por = B.font("Sans Bold", 54), B.font("Sans ExtraBold Italic", 58)
    a, pa = B.solid_text(f"de {old}", f_old, shadow_k=0.85)
    b, pb = B.lime_text("por", f_por, pad=int(f_por.size * 0.35))
    gap = int(f_old.size * 0.35)
    w = a.width - pa + gap + b.width - pb
    h = max(a.height, b.height)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    base_a = pa + f_old.getbbox("de")[3] - f_old.getbbox("de")[1]
    im.alpha_composite(a, (0, (h - a.height) // 2))
    im.alpha_composite(b, (a.width - pa + gap - pb, (h - b.height) // 2))
    if k_strike > 0:                                 # barra no meio da altura do "x"
        xb = f_old.getbbox("x")
        hh = max(6, int(f_old.size * 0.12))
        y = (h - a.height) // 2 + base_a - (xb[3] - xb[1]) / 2 - 2
        x0 = pa - 6
        x1 = x0 + (a.width - 2 * pa + 12) * B.clamp01(k_strike)
        ImageDraw.Draw(im).rounded_rectangle((x0, y - hh / 2, x1, y + hh / 2), hh // 3, fill=B.GREEN_VIVID + (255,))
    return im


def letters(text, fnt, pad):
    """Caixa das letras dentro da imagem de um texto desenhado com text_mask(pad): (x0, y0, x1, y1)."""
    b = fnt.getbbox(text)
    return pad, pad, pad + b[2] - b[0], pad + b[3] - b[1]


def render_price(c, path):
    """Lockup do preço, no padrão das palavras verde-limão da legenda (28/10): chamada pequena em itálico branco
    alinhada à esquerda em cima, "de R$ X por" (opcional), o valor gigante verde-limão com degradê e brilho
    (Archivo Black, sem caixa) e a observação verde-limão alinhada à direita embaixo.
    Fica do meio do pescoço para baixo; se não couber até a margem, o conjunto encolhe (até 72 %)."""
    dur = c["dur"]
    val = c["value"].upper()
    f_v = fit(val, B.KEY_FONT, c.get("size", 240), SAFE_W - 80)
    vimg, vpad = B.lime_text(val, f_v)
    vflare = B.lime_flare(val, f_v, vpad)
    vl = letters(val, f_v, vpad)
    f_k = B.font("Sans SemiBold Italic", 56)
    kick, kpad = B.solid_text(c.get("kicker", "promoção"), f_k, shadow_k=0.9)
    kl = letters(c.get("kicker", "promoção"), f_k, kpad)
    note = c.get("note", "").upper()
    if note:
        f_n = fit(note, B.KEY_FONT, 72, SAFE_W - 80)
        nimg, npad = B.lime_text(note, f_n)
        nflare = B.lime_flare(note, f_n, npad)
        nl = letters(note, f_n, npad)
    old = c.get("old")
    oline = old_price_line(old) if old else None
    # posições pelas letras: a chamada começa na 1ª letra do valor e a observação termina na última
    vw = vl[2] - vl[0]
    x_v0 = B.W / 2 - vw / 2
    gap = f_v.size * 0.14
    rows = [("kick", kl[3] - kl[1])] + ([("old", vis_box(oline)[3] - vis_box(oline)[1])] if oline else []) + \
        [("val", vl[3] - vl[1])] + ([("note", nl[3] - nl[1])] if note else [])
    tot = sum(h for _, h in rows) + gap * (len(rows) - 1)
    nk = B.neck_line(EDL, c["_t0"], c["_t0"] + c["dur"]) if EDL else None
    top = (nk + 16) if nk is not None else c.get("cy", 1150) - tot / 2
    room = B.SAFE[3] - 8 - top
    sc = 1.0 if tot <= room else max(0.72, room / tot)
    if top + tot * sc > B.SAFE[3] - 8:
        top = B.SAFE[3] - 8 - tot * sc
    lt, y = {}, top                                   # topo das letras de cada linha
    for name, h in rows:
        lt[name] = y
        y += h + gap
    # centro de cada imagem na tela
    ctr = {"kick": (x_v0 - kl[0] + kick.width / 2, lt["kick"] - kl[1] + kick.height / 2),
           "val": (B.W / 2 - (vl[0] + vl[2]) / 2 + vimg.width / 2, lt["val"] - vl[1] + vimg.height / 2)}
    if oline is not None:
        ob = vis_box(oline)
        ctr["old"] = (B.W / 2, lt["old"] - ob[1] + oline.height / 2)
    if note:
        ctr["note"] = (x_v0 + vw - nl[2] + nimg.width / 2, lt["note"] - nl[1] + nimg.height / 2)
    boxes, n = [], frames_of(dur)
    t_val = 0.45 if oline else 0.2
    t_note = t_val + 0.45
    key_in = 6 / B.FPS
    s0 = min(1.25, (SAFE_W + 40) / max(1.0, vimg.width - 2 * vpad))       # o pop não passa da margem
    fw = FrameWriter(path, alpha=True)
    for i in range(n):
        t = i / B.FPS
        im = Image.new("RGBA", (B.W, B.H), (0, 0, 0, 0))
        out = fade_out(t, dur, 0.25)
        lb = boxes if i == n - 1 - int(0.3 * B.FPS) else None          # tudo já na tela, antes de sumir
        k1 = B.ease_out_cubic(t / 0.3)
        B.paste_center(im, blur_in(kick, k1, 6), ctr["kick"][0] - 24 * (1 - k1), ctr["kick"][1],
                       alpha=min(1, k1 * 1.5) * out, boxes=lb, tag="preço: chamada")
        if oline is not None and t >= 0.1:
            ko = B.ease_out_cubic((t - 0.1) / 0.25)
            img = old_price_line(old, k_strike=B.ease_out_cubic((t - 0.3) / 0.18))
            B.paste_center(im, blur_in(img, ko, 6), ctr["old"][0], ctr["old"][1] + 12 * (1 - ko), alpha=ko * out,
                           boxes=lb, tag="preço: de/por")
        if t >= t_val:                                # pop: grande e desfocado → no lugar, e o brilho "acende"
            k2 = (t - t_val) / key_in
            if k2 < 1:
                e = B.ease_out_cubic(k2)
                B.paste_center(im, B.scale_rgba(blur_in(vimg, e, 9), s0 - (s0 - 1) * e), *ctr["val"],
                               alpha=min(1.0, 2.2 * k2) * out)
            else:
                B.paste_center(im, vimg, *ctr["val"], alpha=out, boxes=lb, tag="preço: valor")
                kf = (t - t_val - key_in) / 0.45
                if kf < 1:
                    B.paste_center(im, vflare, *ctr["val"], alpha=(1 - kf) ** 2 * out)
        if note and t >= t_note:                      # digitada da esquerda, e o brilho acende no fim
            k3 = B.ease_out_cubic((t - t_note) / 0.3)
            B.paste_center(im, wipe(nimg, k3 * 1.15), *ctr["note"], alpha=out, boxes=lb, tag="preço: obs")
            kf = (t - t_note - 0.3) / 0.35
            if 0 <= kf < 1:
                B.paste_center(im, nflare, *ctr["note"], alpha=(1 - kf) ** 2 * out)
        if sc < 1:
            im = B.scale_canvas(im, sc, B.W / 2, top)
            scale_boxes(lb, sc, B.W / 2, top)
        fw.write(im)
    fw.close()
    ev = [{"t": 0.0, "kind": "pop"}, {"t": t_val, "kind": "cash"}]
    if oline is not None:
        ev.insert(1, {"t": 0.3, "kind": "swipe"})
    return boxes, ev, True


# ------------------------------------------------------------------ product
def render_product(c, path):
    """Painel branco com filete verde vivo: nome do produto (Bebas verde) + detalhe (Open Sans cinza)
    + selo com ⚡ (o "⚡ 40W" da capa do manual). Fica embaixo, na frente; a legenda fica acima dele."""
    dur = c["dur"]
    name = c["name"].upper()
    det = c.get("details", "")
    spec = c.get("spec", "")
    fn = fit(name, "Title", c.get("size", 92), SAFE_W - 130)
    fd = fit(det, "Sans SemiBold", 38, SAFE_W - 130) if det else None
    chip = None
    if spec:
        fs = B.font("Sans ExtraBold", 50)
        hb = fs.getbbox("H")
        cap = hb[3] - hb[1]
        ic = B.bolt(int(cap * 1.3), color=B.GREEN)
        tw = fs.getlength(spec)
        cw, ch = int(ic.width + 16 + tw + 50), int(cap + 40)
        chip = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        dc = ImageDraw.Draw(chip)
        dc.rounded_rectangle((1, 1, cw - 2, ch - 2), 12, outline=B.GREEN + (255,), width=5, fill=B.WHITE + (255,))
        chip.alpha_composite(ic, (22, int(ch / 2 - ic.height / 2)))
        dc.text((22 + ic.width + 14, 20 - hb[1]), spec, font=fs, fill=B.GREEN + (255,))
        chip = shadowed(chip, 0.35)
    hn = fn.getbbox("H")[3] - fn.getbbox("H")[1]
    w_txt = max(fn.getlength(name), fd.getlength(det) if fd else 0)
    pw = int(w_txt + 96)
    ph = int(hn + 60 + (fd.size + 22 if fd else 0))
    ch_ = (chip.height - 36 + 12) if chip else 0
    x0 = B.SAFE[0] + 24
    if c.get("cy") is not None:
        cy = int(below_neck(c, c["cy"], ph + ch_)) - ch_ // 2
    else:                                            # padrão: encostado na margem de baixo
        cy = int(B.SAFE[3] - 10 - ch_ - ph / 2)
    boxes, n = [], frames_of(dur)
    fw = FrameWriter(path, alpha=True)
    for i in range(n):
        t = i / B.FPS
        im = Image.new("RGBA", (B.W, B.H), (0, 0, 0, 0))
        k = B.ease_out_cubic(t / 0.4)
        out = fade_out(t, dur)
        panel = B.rounded((pw, ph), 10, B.WHITE + (int(250 * out),))
        d = ImageDraw.Draw(panel)
        d.rectangle((0, 0, 14, ph), fill=B.GREEN_VIVID + (int(255 * out),))
        a_txt = int(255 * B.ease_out_cubic((t - 0.2) / 0.3) * out)
        d.text((46, 28 - fn.getbbox("H")[1]), name, font=fn, fill=B.GREEN + (a_txt,))
        if fd:
            d.text((46, 28 + hn + 18), det, font=fd, fill=B.GRAY + (a_txt,))
        w = max(1, int(pw * k))
        B._safe_composite(im, shadowed(panel.crop((0, 0, w, ph)), 0.35), x0 - 18, cy - ph // 2 - 18)
        lb = boxes if i == n // 2 else None
        if chip is not None:
            kc = B.ease_out_back((t - 0.45) / 0.35)
            if kc > 0:
                B.paste_center(im, B.scale_rgba(chip, max(0.01, kc)), x0 + 12 + chip.width / 2,
                               cy + ph / 2 + 12 + (chip.height - 36) / 2, alpha=B.clamp01(kc) * out,
                               boxes=lb, tag="selo")
        if lb is not None:
            boxes.append({"tag": "painel", "box": [x0, cy - ph // 2, x0 + pw - 1, cy + ph // 2 - 1]})
        fw.write(im)
    fw.close()
    ev = [{"t": 0.0, "kind": "whoosh"}] + ([{"t": 0.45, "kind": "zap"}] if chip else [])
    return boxes, ev, True


# ------------------------------------------------------------------ label
def render_label(c, path):
    dur = c["dur"]
    lab = bebas_box(c["text"], c.get("size", 64), bg=tuple(c["bg"]) if c.get("bg") else B.GREEN,
                    bolt=c.get("bolt", True), skew=0.14)
    if c.get("rot"):
        lab = lab.rotate(c["rot"], resample=Image.BICUBIC, expand=True)
    x = c.get("x", B.W / 2)
    y = c.get("y", B.SAFE[3] - 10 - (lab.height - 36) / 2)      # padrão: encostada na margem de baixo
    x = min(max(x, B.SAFE[0] + lab.width / 2 - 18), B.SAFE[2] - lab.width / 2 + 18)
    y = min(y, B.SAFE[3] - lab.height / 2 + 12)
    boxes, n = [], frames_of(dur)
    fw = FrameWriter(path, alpha=True)
    for i in range(n):
        t = i / B.FPS
        im = Image.new("RGBA", (B.W, B.H), (0, 0, 0, 0))
        p = B.elastic(t / 0.55)
        out = 1 - B.ease_in_out((t - (dur - 0.15)) / 0.15)
        s = max(0.01, p * (0.6 + 0.4 * out))
        B.paste_center(im, B.scale_rgba(lab, s), x, y, alpha=min(1, p * 1.5) * out,
                       boxes=boxes if i == n // 2 else None, tag=c["text"])
        fw.write(im)
    fw.close()
    return boxes, [{"t": 0.0, "kind": "pop"}], True


# ------------------------------------------------------------------ tag
def render_tag(c, path):
    dur = c["dur"]
    tag = kicker_box(c["text"], c.get("size", 32), bg=B.GREEN, fg=B.WHITE)
    x, y = c.get("x", 250), c.get("y", 330)
    boxes, n = [], frames_of(dur)
    fw = FrameWriter(path, alpha=True)
    for i in range(n):
        t = i / B.FPS
        im = Image.new("RGBA", (B.W, B.H), (0, 0, 0, 0))
        k = B.ease_out_back(t / 0.35)
        B.paste_center(im, B.scale_rgba(tag, max(0.01, k)), x, y, alpha=B.clamp01(k) * fade_out(t, dur, 0.2),
                       boxes=boxes if i == n // 2 else None, tag=c["text"])
        fw.write(im)
    fw.close()
    return boxes, [{"t": 0.0, "kind": "pop"}], True


# ------------------------------------------------------------------ title
def render_title(c, path):
    """Frase pequena em cima (Open Sans itálico) + palavra GIGANTE (Bebas branca) + 2ª linha verde vivo
    opcional + linha tracejada. Por padrão fica ATRÁS da pessoa (o build.py recorta ela por cima)."""
    dur = c["dur"]
    kick_t, l1, l2 = c.get("kicker", ""), c.get("line1", "").upper(), c.get("line2", "").upper()
    f1 = fit(l1, "Title", c.get("size", 330), SAFE_W - 40)
    i1, _ = B.solid_text(l1, f1, shadow_k=0.8)
    i2 = title_text(l2, int(f1.size * 0.62), B.GREEN_VIVID) if l2 else None
    ik = B.solid_text(kick_t, fit(kick_t, "Sans SemiBold Italic", int(f1.size * 0.20), SAFE_W - 60),
                      shadow_k=0.8)[0] if kick_t else None
    cap1 = f1.getbbox("H")[3] - f1.getbbox("H")[1]
    hk = (ik.height * 0.55) if ik is not None else 0
    h2 = (i2.height * 0.55) if i2 is not None else 0
    blk_h = hk + cap1 + h2 + 40
    cy = c.get("cy", 560)
    if c.get("y") == "auto":
        top, _ = place_above_head(c, cy - blk_h / 2, blk_h, cy - blk_h / 2)
        cy = top + blk_h / 2
    y_k = cy - blk_h / 2 + hk / 2
    y1 = cy - blk_h / 2 + hk + cap1 / 2
    y2 = y1 + cap1 / 2 + h2 / 2 + 6
    y_ln = (y2 + h2 / 2 if i2 is not None else y1 + cap1 / 2) + 30
    boxes, n = [], frames_of(dur)
    fw = FrameWriter(path, alpha=True)
    for i in range(n):
        t = i / B.FPS
        im = Image.new("RGBA", (B.W, B.H), (0, 0, 0, 0))
        out = fade_out(t, dur)
        lb = boxes if i == n // 2 else None
        if ik is not None:
            kk = B.ease_out_cubic(t / 0.3)
            B.paste_center(im, blur_in(ik, kk, 8), B.W / 2, y_k + 16 * (1 - kk), alpha=kk * out, boxes=lb,
                           tag="título: chamada")
        k1 = B.ease_out_cubic((t - 0.12) / 0.4)
        if k1 > 0:
            B.paste_center(im, B.scale_rgba(blur_in(i1, k1, 14), 1.25 - 0.25 * k1), B.W / 2, y1,
                           alpha=min(1, 1.6 * k1) * out, boxes=lb, tag="título")
        if i2 is not None:
            k2 = B.ease_out_back((t - 0.3) / 0.4)
            if k2 > 0:
                B.paste_center(im, B.scale_rgba(i2, max(0.01, k2)), B.W / 2, y2, alpha=B.clamp01(k2) * out,
                               boxes=lb, tag="título: 2ª linha")
        kl = B.ease_in_out((t - 0.4) / 0.5)
        if kl > 0:
            B.paste_center(im, B.dashed_line(int(min(SAFE_W - 160, i1.width * 0.6)), kl), B.W / 2, y_ln,
                           alpha=out, boxes=lb, tag="linha")
        fw.write(im)
    fw.close()
    return boxes, [{"t": 0.0, "kind": "whoosh"}, {"t": 0.15, "kind": "impact"}], True


# ------------------------------------------------------------------ colorcard (tela de cor da referência)
def render_colorcard(c, path):
    """Tela cheia de cor (verde #007800 ou branca), corte seco, com a fala em letra pequena no centro,
    palavra por palavra no tempo do transcript (ou "text", espalhado na 1ª metade)."""
    dur = c["dur"]
    green = c.get("bg", "green") != "white"
    bg = B.GREEN if green else OFFWHITE
    fg = B.WHITE if green else B.GREEN
    f = B.font(c.get("font", "Sans Bold"), c.get("size", 64))
    if c.get("text"):
        ws = c["text"].split()
        times = [i * min(0.12, dur * 0.5 / max(1, len(ws))) for i in range(len(ws))]
    else:
        a = c["_t0"]
        src = [w for w in B.load_words(EDL) if a - 0.08 <= w["start"] < a + dur - 0.05] if EDL else []
        ws = [w["word"] for w in src] or [""]
        times = [max(0.0, w["start"] - a) for w in src] or [0.0]
    ws = [re.sub(r"[.,;:…]+$", "", w) for w in ws]
    space = f.getlength(" ")
    # quebra em até 2 linhas centradas
    lines, cur = [], []
    for j, w in enumerate(ws):
        if cur and f.getlength(" ".join(ws[k] for k in cur + [j])) > SAFE_W - 160:
            lines.append(cur)
            cur = []
        cur.append(j)
    lines.append(cur)
    hb = f.getbbox("H")
    lh = (hb[3] - hb[1]) * 1.55
    y0 = B.H * 0.5 - lh * (len(lines) - 1) / 2
    boxes, n = [], frames_of(dur)
    fw = FrameWriter(path)
    for i in range(n):
        t = i / B.FPS
        im = Image.new("RGBA", (B.W, B.H), bg + (255,))
        d = ImageDraw.Draw(im)
        for li, idx in enumerate(lines):
            vis = [j for j in idx if t >= times[j] - 1e-6]
            if not vis:
                continue
            tw = f.getlength(" ".join(ws[j] for j in vis))
            x = B.W / 2 - tw / 2
            yb = y0 + li * lh + (hb[3] - hb[1]) / 2
            for j in vis:
                k = B.clamp01((t - times[j]) * B.FPS / 3)
                col = tuple(int(bg[q] + (fg[q] - bg[q]) * k) for q in range(3))
                d.text((x, yb), ws[j], font=f, fill=col + (255,), anchor="ls")
                x += f.getlength(ws[j]) + space
        if i == n - 1:
            arr = np.abs(np.asarray(im.convert("RGB"), np.int16) - np.array(bg, np.int16)).sum(2) > 30
            ys_, xs_ = np.nonzero(arr)
            if len(xs_):
                boxes.append({"tag": "texto", "box": [int(xs_.min()), int(ys_.min()), int(xs_.max()), int(ys_.max())]})
        fw.write(im.convert("RGB"))
    fw.close()
    return boxes, [{"t": 0.0, "kind": "switch"}], False


# ------------------------------------------------------------------ flash (transição)
def render_flash(c, path):
    """Luz acendendo: clarão branco frio e rápido, do centro para fora (sobe em 30 % do tempo e apaga)."""
    dur = c["dur"]
    yy, xx = np.mgrid[0:B.H // 4, 0:B.W // 4].astype(np.float32)
    cx, cy = c.get("x", B.W / 2) / 4, c.get("y", 760) / 4
    d = np.sqrt(((xx - cx) / (B.W / 4)) ** 2 + ((yy - cy) / (B.H / 4)) ** 2)
    color = tuple(c.get("color", (240, 250, 255)))
    n = frames_of(dur)
    fw = FrameWriter(path, alpha=True)
    for i in range(n):
        t = i / max(1, n - 1)
        k = B.ease_out_cubic(t / 0.3) if t < 0.3 else 1 - B.ease_in_out((t - 0.3) / 0.7)
        r = 0.25 + 1.1 * B.ease_out_cubic(t / 0.5)
        a = np.clip(1.15 - d / r, 0, 1) ** 1.4 * k * c.get("strength", 0.8)
        lay = Image.new("RGBA", (B.W // 4, B.H // 4), color + (0,))
        lay.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
        fw.write(lay.resize((B.W, B.H), Image.BILINEAR))
    fw.close()
    return [], [{"t": 0.0, "kind": "zap"}], True


# ------------------------------------------------------------------ broll
BROLL_LOCK_MAX = 1.06     # zoom fixo máximo para esconder as bordas que a trava abre


def lock_moves(ys, w, h):
    """Correção (dx, dy, ângulo) de cada quadro para a posição média da câmera no trecho ("tripé")."""
    import cv2
    sw_, sh_ = w // 4, h // 4
    gs = [cv2.resize(y, (sw_, sh_), interpolation=cv2.INTER_AREA) for y in ys]
    moves = [(0.0, 0.0, 0.0)]
    for g0, g1 in zip(gs, gs[1:]):
        dx = dy = da = 0.0
        pts = cv2.goodFeaturesToTrack(g0, 400, 0.01, 8)
        if pts is not None and len(pts) >= 8:
            nxt, st, _ = cv2.calcOpticalFlowPyrLK(g0, g1, pts, None)
            ok = st.ravel() == 1
            if ok.sum() >= 8:
                m, _ = cv2.estimateAffinePartial2D(pts[ok], nxt[ok], method=cv2.RANSAC, ransacReprojThreshold=2.0)
                if m is not None:
                    dx, dy, da = m[0, 2] * 4, m[1, 2] * 4, math.atan2(m[1, 0], m[0, 0])
        moves.append((dx, dy, da))
    traj = np.cumsum(np.array(moves), axis=0)
    corr = traj.mean(axis=0) - traj
    need = 1 + 2 * max(np.abs(corr[:, 0]).max() / w, np.abs(corr[:, 1]).max() / h) + np.abs(corr[:, 2]).max() * h / w
    if need > BROLL_LOCK_MAX:                       # movimento grande: trava só o quanto o zoom máximo esconde
        corr *= (BROLL_LOCK_MAX - 1) / (need - 1)
        need = BROLL_LOCK_MAX
    return corr, need + 0.004


def render_broll(c, path, base_dir):
    """Imagem de apoio (mudo), HDR → SDR. Cada trecho sai "travado" como num tripé ("stab": false desliga): o
    movimento da câmera (pontos do OpenCV + RANSAC, que ignora as mãos mexendo) é medido e cada quadro volta para
    a posição média do trecho, com o menor zoom FIXO que esconde as bordas (até BROLL_LOCK_MAX). Sem zoom animado
    e corte seco entre os trechos (29/10: "não precisa dar zoom in na camada"; "push" opcional, com subpixel).
    A correção é feita nos planos Y/U/V, sem passar por RGB (cor igual)."""
    import cv2
    import build as BLD
    src = BLD.sdr_proxy(os.path.normpath(os.path.join(base_dir, c["file"])), base_dir)   # HDR → cópia SDR
    info = BLD.probe(src)
    sw, sh, is_hdr, vst = BLD.video_geom(info)
    cw, ch, x, y = BLD.crop_for(c, sw, sh)
    n = frames_of(c["dur"])
    z_end = float(c.get("push", 1.0))
    vst_ = next(v for v in info["streams"] if v["codec_type"] == "video")
    untagged = vst_.get("color_space") in (None, "unknown") and not is_hdr     # sem etiqueta: vídeo HD = BT.709
    vf = (f"setpts=PTS-{vst}/TB,fps={B.FPS},{BLD.TAG709 + ',' if untagged else ''}crop={cw}:{ch}:{x}:{y},"
          f"scale={B.W}:{B.H}:flags=lanczos,setsar=1,format=yuv420p")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{c.get('start', 0):.3f}", "-i", src, "-an", "-vf", vf,
                          "-frames:v", str(n), "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    fs, ny, nc = B.W * B.H * 3 // 2, B.W * B.H, B.W * B.H // 4
    frs = [raw[i * fs:(i + 1) * fs] for i in range(len(raw) // fs)]
    frs += [frs[-1]] * (n - len(frs))                 # fim do arquivo: repete o último quadro
    planes = [(np.frombuffer(f, np.uint8, ny).reshape(B.H, B.W),
               np.frombuffer(f, np.uint8, nc, ny).reshape(B.H // 2, B.W // 2),
               np.frombuffer(f, np.uint8, nc, ny + nc).reshape(B.H // 2, B.W // 2)) for f in frs[:n]]
    if c.get("stab", True) and n > 2:
        corr, z0 = lock_moves([p[0] for p in planes], B.W, B.H)
    else:
        corr, z0 = np.zeros((n, 3)), 1.0
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{B.W}x{B.H}",
                            "-r", str(B.FPS), *BLD.BT709, "-i", "-", "-frames:v", str(n), "-c:v", "libx264",
                            "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", *BLD.BT709, path],
                           stdin=subprocess.PIPE)
    for i, pls in enumerate(planes):
        z = z0 * (1 + (z_end - 1) * i / max(1, n - 1))
        dx, dy, da = corr[i]
        if abs(z - 1) < 1e-4 and abs(dx) < 1e-3 and abs(dy) < 1e-3 and abs(da) < 1e-6:
            enc.stdin.write(frs[i])
            continue
        for pl, f in zip(pls, (1.0, 0.5, 0.5)):
            h_, w_ = pl.shape
            m = cv2.getRotationMatrix2D((w_ / 2, h_ / 2), math.degrees(-da), z)   # OpenCV: ângulo + = anti-horário
            m[0, 2] += dx * f * z
            m[1, 2] += dy * f * z
            enc.stdin.write(cv2.warpAffine(pl, m, (w_, h_), flags=cv2.INTER_LINEAR,
                                           borderMode=cv2.BORDER_REFLECT).tobytes())
    enc.stdin.close()
    enc.wait()
    return [], [], False


# ------------------------------------------------------------------ photo
# "Quadrinho" (pedido da agência em 29/10, no lugar da foto em tela cheia): a foto recortada em 4:5 em volta do
# produto, com borda branca, cantos arredondados, sombra e uma leve inclinação, que entra com um pop suave na
# frente do peito (do meio do pescoço para baixo, nunca no rosto). A legenda dá licença enquanto ele está na tela.
PHOTO_W = 500             # px: largura do quadrinho (~46% da tela); encolhe se não couber até a margem (até 72%)
PHOTO_AR = 4 / 5          # recorte da foto (largura/altura), centrado em "focus": [x, y] (0–1, padrão o centro)
PHOTO_BORDER = 12
PHOTO_RADIUS = 30
PHOTO_TILT = 4.0          # graus; alterna − / + a cada foto do vídeo ("tilt" no card troca)
PHOTO_IN, PHOTO_OUT = 0.38, 0.22
PHOTO_GAP = 40            # px abaixo do meio do pescoço


def ease_out_back(x, k=1.6):
    x = B.clamp01(x) - 1
    return 1 + (k + 1) * x ** 3 + k * x ** 2


def photo_card(c, base_dir, w):
    src = ImageOps.exif_transpose(Image.open(os.path.join(base_dir, c["file"]))).convert("RGB")
    sw, sh = src.size
    cw, ch = (sh * PHOTO_AR, sh) if sw / sh > PHOTO_AR else (sw, sw / PHOTO_AR)
    fx, fy = c.get("focus", [0.5, 0.5])
    x0 = min(max(fx * sw - cw / 2, 0), sw - cw)
    y0 = min(max(fy * sh - ch / 2, 0), sh - ch)
    h = int(round(w / PHOTO_AR))
    b = PHOTO_BORDER
    ph = src.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((w - 2 * b, h - 2 * b), Image.LANCZOS)
    card = B.rounded((w, h), PHOTO_RADIUS, (255, 255, 255, 255))
    m = Image.new("L", ph.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, ph.width - 1, ph.height - 1), PHOTO_RADIUS - b, fill=255)
    card.paste(ph, (b, b), m)
    return shadowed(card, k=0.5, dy=10, r=14)


def render_photo(c, path, base_dir):
    dur = c["dur"]
    n = frames_of(dur)
    nk = B.neck_line(EDL, c["_t0"], c["_t0"] + dur) if EDL else None
    w = int(c.get("w", PHOTO_W))
    h = int(round(w / PHOTO_AR))
    top = (nk + PHOTO_GAP) if nk is not None else c.get("cy", 1150) - h / 2
    room = B.SAFE[3] - 12 - top
    sc = 1.0 if h + 40 <= room else max(0.72, (room - 40) / h)
    w = int(w * sc)
    if top + w / PHOTO_AR + 40 > B.SAFE[3] - 12:
        top = B.SAFE[3] - 12 - w / PHOTO_AR - 40
    card = photo_card(c, base_dir, w)
    others = [x for x in EDL.get("cards", []) if x["type"] == "photo"] if EDL else [c]
    idx = next((i for i, x in enumerate(others) if x.get("at") == c.get("at")), 0)
    tilt = float(c.get("tilt", PHOTO_TILT if idx % 2 == 0 else -PHOTO_TILT))
    card = card.rotate(tilt, resample=Image.BICUBIC, expand=True)
    cx, cy = c.get("x", B.W / 2), top + (w / PHOTO_AR) / 2
    boxes = []
    fw = FrameWriter(path, alpha=True)
    for i in range(n):
        t = i / B.FPS
        im = Image.new("RGBA", (B.W, B.H), (0, 0, 0, 0))
        k_in = t / PHOTO_IN
        k_out = B.clamp01((t - (dur - PHOTO_OUT)) / PHOTO_OUT)
        s = 0.55 + 0.45 * ease_out_back(k_in) if k_in < 1 else 1.0 + 0.02 * (t - PHOTO_IN) / max(0.1, dur)
        s *= 1 - 0.12 * B.ease_in_out(k_out)
        a = min(1.0, k_in * 2.5) * (1 - B.ease_in_out(k_out))
        lb = boxes if i == n - 1 - int(0.3 * B.FPS) else None
        B.paste_center(im, B.scale_rgba(card, s), cx, cy, alpha=a, boxes=lb, tag="foto")
        fw.write(im)
    fw.close()
    return boxes, [{"t": 0.0, "kind": "pop"}], True


# ------------------------------------------------------------------ beforeafter
def _fit_photo(path, base_dir):
    src = ImageOps.exif_transpose(Image.open(os.path.join(base_dir, path))).convert("RGB")
    return ImageOps.fit(src, (B.W, B.H), Image.LANCZOS)


def render_beforeafter(c, path, base_dir):
    dur = c["dur"]
    before, after = _fit_photo(c["before"], base_dir), _fit_photo(c["after"], base_dir)
    wipe_at, wipe_d = c.get("wipe_at", dur * 0.42), c.get("wipe_dur", 0.55)
    lab_b = bebas_box(c.get("before_label", "antes"), 80, fg=B.GREEN, bg=B.WHITE)
    lab_a = bebas_box(c.get("after_label", "depois"), 80, bolt=True)
    ly = c.get("label_y", 330)
    boxes, n = [], frames_of(dur)
    fw = FrameWriter(path)
    for i in range(n):
        t = i / B.FPS
        k = B.ease_in_out((t - wipe_at) / wipe_d)
        x = int(B.W * k)
        z = 1 + 0.04 * (t / dur)
        fr = before.copy()
        if x > 0:
            fr.paste(after.crop((0, 0, x, B.H)), (0, 0))
        if 0 < k < 1:
            ImageDraw.Draw(fr).rectangle((x - 5, 0, x + 5, B.H), fill=B.GREEN_VIVID)
        if z > 1.001:
            cw, ch = B.W / z, B.H / z
            fr = fr.crop((int((B.W - cw) / 2), int((B.H - ch) / 2), int((B.W + cw) / 2),
                          int((B.H + ch) / 2))).resize((B.W, B.H), Image.BILINEAR)
        im = fr.convert("RGBA")
        ka = B.ease_out_back(t / 0.35)
        if k < 0.5:
            B.paste_center(im, B.scale_rgba(lab_b, max(0.01, ka)), B.W / 2, ly, alpha=B.clamp01(ka) * (1 - k * 2),
                           boxes=boxes if i == n // 4 else None, tag="antes")
        else:
            kb = B.elastic((t - wipe_at - wipe_d * 0.6) / 0.5)
            B.paste_center(im, B.scale_rgba(lab_a, max(0.01, kb)), B.W / 2, ly, alpha=B.clamp01(kb * 1.5),
                           boxes=boxes if i == n - 1 else None, tag="depois")
        fw.write(im)
    fw.close()
    return boxes, [{"t": 0.0, "kind": "whoosh"}, {"t": wipe_at, "kind": "whoosh"},
                   {"t": wipe_at + wipe_d * 0.6, "kind": "zap"}], False


# ------------------------------------------------------------------ end
END_PHOTO = "fundo_card_final.jpg"       # fachada da loja em verde (enviada pela agência em 28/10)
END_SHADE = (3, 38, 12)                  # verde fechado por cima da foto
END_ZOOM = 1.04                          # zoom lento na foto durante o card


def end_background(c):
    """Fundo do card final: a foto da fachada (já em verde) cobrindo a tela, puxada para um verde mais fechado,
    com uma faixa mais escura no meio (onde fica o texto) e cantos levemente escuros. Sem listras (28/10).
    "photo": outro arquivo de assets/; "shade": 0–1 (quanto do verde fechado vai por cima, padrão 0,55)."""
    p = c.get("photo", END_PHOTO)
    p = p if os.path.isabs(p) else os.path.join(B.ASSETS, p)
    if not os.path.exists(p):
        return None
    w, h = int(B.W * END_ZOOM), int(B.H * END_ZOOM)
    im = ImageOps.fit(ImageOps.exif_transpose(Image.open(p)).convert("RGB"), (w, h), Image.LANCZOS)
    a = np.asarray(im, np.float32)
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    xx = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    k = c.get("shade", 0.55) + 0.14 * np.exp(-((yy - 0.50) / 0.22) ** 2)          # faixa do texto (meio)
    k = k + 0.10 * np.clip(xx ** 2 + ((yy - 0.5) * 2) ** 2 - 0.6, 0, 1)             # cantos
    k = np.clip(k, 0, 0.92)[..., None]
    out = a * (1 - k) + np.array(END_SHADE, np.float32) * k
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))


def thin_line(width, progress, color=B.WHITE, alpha=0.75, thick=3):
    """Linha fina e lisa que abre do centro para as pontas (no lugar da tracejada com bolinha)."""
    im = Image.new("RGBA", (width + 4, thick + 4), (0, 0, 0, 0))
    half = width / 2 * B.clamp01(progress)
    if half >= 1:
        ImageDraw.Draw(im).rectangle((width / 2 + 2 - half, 2, width / 2 + 2 + half, 2 + thick - 1),
                                     fill=tuple(color) + (int(255 * alpha),))
    return im


def render_end(c, path, dur):
    """Card final: a fachada da loja em verde fechado (zoom lento), o logo entra subindo com um brilho suave,
    linha fina e lisa abrindo do centro e o principal embaixo: endereço, entrega / loja virtual e @.
    Mais limpo (pedidos da agência em 28/10): sem listras, sem tracejado, sem o logo piscando e sem botão
    ("cta": "..." volta com o botão branco em pílula)."""
    T = {"bg": 0.0, "logo": 0.12, "name": 0.32, "line": 0.55, "cta": 0.8, "small": 1.05}
    T.update(c.get("T", {}))
    icon = B.scale_rgba(B.load_logo("icon_white"), c.get("logo_w", 760) * 0.6 / B.load_logo("icon_white").width)
    name = B.scale_rgba(B.load_logo("name_white"), c.get("logo_w", 760) / B.load_logo("name_white").width)
    gsrc = Image.new("RGBA", (icon.width + 200, icon.height + 200), (0, 0, 0, 0))
    gsrc.alpha_composite(icon, (100, 100))
    glow = Image.new("RGBA", gsrc.size, (225, 255, 225, 0))
    glow.putalpha(gsrc.getchannel("A").filter(ImageFilter.GaussianBlur(34)).point(lambda v: int(v * 0.8)))
    cta_t = c.get("cta", B.CTA).upper()
    cta = None
    if cta_t:
        f_cta = fit(cta_t, "Sans ExtraBold", 50, SAFE_W - 200)
        pill = B.box_text(cta_t, f_cta, fg=B.GREEN, bg=B.WHITE, pad=(0.85, 0.55), shadow=False)
        pill = B.box_text(cta_t, f_cta, fg=B.GREEN, bg=B.WHITE, pad=(0.85, 0.55), shadow=False,
                          radius=pill.height // 2)                   # botão em pílula
        cta = shadowed(pill, 0.3, dy=8, r=10)
    else:
        T["small"] = T["cta"]                        # sem botão: o endereço entra no lugar dele
    small_t = [x for x in (c.get("lines", [B.ADDRESS, B.ONLINE]) + [c.get("handle", B.HANDLE)]) if x]
    fs = 38 if cta is not None else 44               # sem botão, endereço e entrega são o principal: maiores
    small = [B.solid_text(x, fit(x, "Sans SemiBold" if j else "Sans Bold", fs, SAFE_W - 80),
                          color=B.WHITE if (j == 0 and cta is None) else B.LIGHT, shadow_k=0.5)[0]
             for j, x in enumerate(small_t)]
    gap = 54 if cta is not None else 62
    line_w = int(c.get("line_w", 420))
    ys = {"icon": 0.0}
    ys["name"] = ys["icon"] + icon.height / 2 + 30 + name.height / 2
    ys["line"] = ys["name"] + name.height / 2 + 64
    if cta is not None:
        ys["cta"] = ys["line"] + 64 + (cta.height - 36) / 2
        ys["small"] = ys["cta"] + (cta.height - 36) / 2 + 62
    else:
        ys["small"] = ys["line"] + 72
    # centro exato do conjunto (pela parte visível: topo do EC até o pé da última linha) no meio da tela
    # (pedido da agência em 28/10: "centralize as informações no meio, na vertical e na horizontal")
    vb = vis_box(small[-1]) if small else (0, 0, 0, 0)
    top = ys["icon"] - icon.height / 2
    bottom = (ys["small"] + gap * (len(small) - 1) - small[-1].height / 2 + vb[3]) if small else ys["line"]
    off = c.get("cy", B.H / 2) - (top + bottom) / 2
    ys = {k: v + off for k, v in ys.items()}
    photo = end_background(c)
    boxes, events = [], [{"t": 0.0, "kind": "whoosh"}, {"t": T["logo"] + 0.25, "kind": "chime"}] + \
        ([{"t": T["cta"] + 0.05, "kind": "softpop"}] if cta is not None else [])
    fw = FrameWriter(path, alpha=True)
    n = frames_of(dur)
    for i in range(n):
        t = i / B.FPS
        if photo is not None:                            # zoom lento na foto
            z = 1 + (END_ZOOM - 1) * B.ease_in_out(t / max(dur, 0.1))
            cw, ch = photo.width / z, photo.height / z
            x0, y0 = (photo.width - cw) / 2, (photo.height - ch) / 2
            im = photo.resize((B.W, B.H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch)).convert("RGBA")
        else:
            im = B.brand_background(t, stripes=False)
        im.putalpha(int(255 * B.ease_out_cubic((t - T["bg"]) / 0.3)))
        lb = boxes if i == n - 1 else None
        e = lambda k, d=0.45: B.ease_out_cubic((t - T[k]) / d)  # noqa: E731
        ki = e("logo", 0.5)
        if ki > 0:                                       # EC sobe e aparece, com um brilho que acende e assenta
            kg = B.clamp01((t - T["logo"]) / 0.35)
            g = (kg if kg < 1 else max(0.0, 1 - (t - T["logo"] - 0.35) / 0.6)) * 0.55
            if g > 0.01:
                B.paste_center(im, glow, B.W / 2, ys["icon"] + 24 * (1 - ki), alpha=g)
            B.paste_center(im, B.scale_rgba(icon, 0.96 + 0.04 * ki), B.W / 2, ys["icon"] + 24 * (1 - ki),
                           alpha=ki, boxes=lb, tag="logo: EC")
        kn = e("name")
        if kn > 0:
            B.paste_center(im, name, B.W / 2, ys["name"] + 18 * (1 - kn), alpha=kn, boxes=lb, tag="logo: nome")
        kl = B.ease_in_out((t - T["line"]) / 0.45)
        if kl > 0:
            B.paste_center(im, thin_line(line_w, kl), B.W / 2, ys["line"], boxes=lb, tag="linha")
        kc = B.clamp01((t - T["cta"]) / 0.45)
        if kc > 0 and cta is not None:
            s_ = 0.92 + 0.08 * B.ease_out_back(kc, 1.2)
            B.paste_center(im, B.scale_rgba(cta, s_), B.W / 2, ys["cta"], alpha=min(1.0, kc * 2), boxes=lb, tag="cta")
        ks = e("small")
        for j, s_im in enumerate(small):
            if ks > 0:
                B.paste_center(im, s_im, B.W / 2, ys["small"] + gap * j + 12 * (1 - ks), alpha=ks,
                               boxes=lb, tag=f"rodapé {j}")
        fw.write(im)
    fw.close()
    return boxes, events, True


def main():
    edl_path = sys.argv[1] if len(sys.argv) > 1 else "edl.json"
    global EDL
    edl = B.load_edl(edl_path)
    EDL = edl
    outdir = os.path.join(edl["_dir"], "cards")
    os.makedirs(outdir, exist_ok=True)
    for old in os.listdir(outdir):
        os.remove(os.path.join(outdir, old))
    index, allboxes = [], []
    renderers = {"title": render_title, "label": render_label, "tag": render_tag, "product": render_product,
                 "topic": render_topic, "checklist": render_checklist, "price": render_price,
                 "flash": render_flash, "colorcard": render_colorcard}
    for k, (a, b, c) in enumerate(B.card_windows(edl)):
        typ = c["type"]
        c = dict(c, dur=b - a, _t0=a)
        alpha = typ not in ("beforeafter", "broll", "colorcard")          # a foto virou quadrinho com alfa (29/10)
        path = os.path.join(outdir, f"{k:02d}_{typ}.{'mov' if alpha else 'mp4'}")
        if typ in renderers:
            boxes, ev, alpha = renderers[typ](c, path)
        elif typ == "photo":
            boxes, ev, alpha = render_photo(c, path, edl["_dir"])
        elif typ == "broll":
            boxes, ev, alpha = render_broll(c, path, edl["_dir"])
        elif typ == "beforeafter":
            boxes, ev, alpha = render_beforeafter(c, path, edl["_dir"])
        elif typ == "end":
            boxes, ev, alpha = render_end(c, path, b - a)
        else:
            print(f"tipo de card desconhecido: {typ}")
            continue
        if c.get("sfx") is False:                    # EDL: "sfx": false = card mudo
            ev = []
        elif isinstance(c.get("sfx"), str) and ev:   # EDL: "sfx": "pling" troca o som principal do card
            ev = [dict(ev[0], kind=c["sfx"])] + ev[1:]
        for bx in boxes:
            bx["t"] = round(a, 2)
            bx["t_end"] = round(b, 2)
            bx["tag"] = f"{typ}: {bx['tag']}"
        allboxes += boxes
        index.append({"file": os.path.relpath(path, edl["_dir"]), "type": typ, "at": a, "dur": b - a,
                      "alpha": alpha, "hide_logo": typ in B.HIDE_LOGO_TYPES,
                      "behind": bool(c.get("behind", typ in BEHIND and c.get("place") != "below")),
                      "events": [{"t": a + e["t"], "kind": e["kind"]} for e in ev]})
        print(f"card {k}: {typ} {a:.2f}–{b:.2f}s → {os.path.basename(path)}")
    with open(os.path.join(outdir, "index.json"), "w") as f:
        json.dump(index, f, indent=1)
    B.write_bboxes("cards", edl, allboxes)


if __name__ == "__main__":
    main()
