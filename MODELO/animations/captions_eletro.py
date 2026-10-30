"""Legenda Eletro Company → captions.mov (transparente)

Estilo tirado de REFERENCIAS/referencia_legenda.mp4, com as fontes e cores do manual
(Open Sans + Bebas Neue, verde #007800 / verde vivo das capas):
  • Palavras PEQUENAS e limpas no peito (Open Sans Bold branca, sombra suave), entrando UMA A UMA no tempo
    da fala, desfocadas → nítidas (4 quadros). Frases curtas (até 2 linhas de 3 palavras) que trocam rápido.
  • A palavra forte vira um LOCKUP (como "no / EMBALAMENTO / da sua mercadoria" e "pode / COMPROMETER /
    meses de trabalho" da referência): as palavras de antes ficam pequenas em cima, alinhadas à ESQUERDA da
    palavra forte; as de depois ficam embaixo, alinhadas à DIREITA. As pequenas do lockup são itálicas.
    Tipos (escolhidos no EDL, use pouco: 1 por frase no máximo):
      big       GRANDE: Open Sans ExtraBold branca, digitada letra a letra (revela da esquerda, suave).
      accents   VERDE-LIMÃO: Archivo Black CAIXA-ALTA com degradê (claro em cima → verde embaixo) e brilho verde,
                digitada; o brilho "acende" quando ela termina (estilo "MOTIVAÇÃO", pedido da agência em 28/10).
      strikes   RISCADA: Open Sans Bold Italic branca, digitada, e a barra verde vivo risca da esquerda
                ("comprometer"). Para o que é ruim/errado: "gambiarra", "caro", "curto-circuito".
      keywords  CHAVE: o mesmo verde-limão com brilho, gigante, entra com "pop" (preço, potência, produto:
                "R$ 19,90", "24W", "RELÂMPAGO").
      boxes     desde 28/10 sai igual a "accents" (verde-limão com brilho, sem a caixa verde): pedido da agência
                para o "METADE DO PREÇO". O desenho antigo (Bebas branca na caixa verde #007800, o "LÂMPADAS
                TASCHIBRA" da capa do manual) continua no código como o tipo "box", fora de uso.
  • Frase nova: o bloco anterior some rápido (3 quadros, desfocando), 2 quadros antes do novo entrar.
  • Posição: a 1ª linha começa logo abaixo do MEIO DO PESCOÇO (rosto do person.json); sem rosto, o bloco
    fica centrado em "cy". Tudo dentro da margem de segurança: o bloco encolhe se não couber.
    "hook_top": true põe o gancho ACIMA da cabeça (como o "um erro" da referência), se couber dentro da margem.

Uso:  python animations/captions_eletro.py [edl.json]
EDL:  "captions": {"style": "ELC", "cy": 1060, "hook_end": 2.4, "hook_top": false,
                   "big": ["relâmpago"], "accents": ["iluminação"], "strikes": ["gambiarra"],
                   "keywords": ["R$ 19,90", "24W"], "boxes": ["plafon de embutir"],
                   "fix": {"electro company": "Eletro Company"}, "breaks": [2.48], "keep_case": ["Eletro"],
                   "punct": false, "lower": false, "skip": [[t0, t1]]}
  big/accents/strikes/keywords/boxes  palavra solta ou expressão (vira o destaque do lockup).
  fix        correções; com espaço na chave, junta as palavras ("electro company" → "Eletro Company").
  breaks     tempos do vídeo ORIGINAL (início da palavra) onde começa uma frase nova.
  punct      true mantém vírgula e ponto no fim das palavras (padrão: só ? e !).
  lower      true deixa tudo minúsculo (menos keep_case); padrão: como o transcript escreveu.
  skip       janelas do vídeo FINAL sem legenda.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

import brand as B  # noqa: E402
from frames import FrameWriter  # noqa: E402

WORD_IN = 4              # quadros: palavra pequena entra desfocada e transparente → nítida
TYPE_MIN, TYPE_MAX = 0.20, 0.42   # s: a palavra forte é digitada nesse tempo (dentro da duração falada)
TYPE_FEATHER = 0.22      # borda suave da digitação (× largura da palavra)
KEY_IN = 6               # quadros: chave entra grande e desfocada → no lugar
FLARE = 0.35             # s: o brilho das palavras verde-limão "acende" e assenta quando a palavra termina de entrar
BOX_DELAY, BOX_IN = 1, 5         # caixa verde abre da esquerda por trás da palavra
STRIKE_IN = 5            # quadros: a barra risca a palavra (depois de digitada)
RECENTER = 4             # quadros: linha normal desliza para o centro quando ganha palavra
BLOCK_OUT = 3            # quadros: bloco some desfocando
GAP_BREAK = 0.40
MAX_DUR = 3.2            # frase longa demais quebra
TAIL = 0.30              # s que a última palavra fica na tela depois de falada
MARGIN = 90              # folga do bloco para sombra, brilho e pop
SIDE = 24                # folga lateral dentro da margem de segurança
MIN_SCALE = 0.75         # bloco que não cabe abaixo do pescoço encolhe até aqui
PRICE = re.compile(r"R\$|\d+,\d{2}")             # chave com valor → som de dinheiro
CLICK_WORDS = {"clique", "clica", "clicar", "clicando"}   # → som de clique de mouse
HERO = ("big", "accent", "strike", "key", "box")
FRONT_CARDS = ("product", "label")
CONNECTORS = {"de", "da", "do", "das", "dos", "e", "a", "o", "as", "os", "um", "uma", "no", "na", "em", "pela",
              "pelo", "com", "por", "pra", "para", "que", "seu", "sua"}
TYPED = ("big", "accent", "strike")


def norm(w):
    return re.sub(r"[^\w$áàâãéêíóôõúüç,-]", "", w.lower()).strip(",")


KEEP_CASE = set()
OPTS = {"punct": False, "lower": False}


def clean(w):
    w = re.sub(r'^["“”\']+|["“”\']+$', "", w.strip())
    if not OPTS["punct"]:
        w = re.sub(r"[.,;:…]+$", "", w)
    if OPTS["lower"] and norm(w) not in KEEP_CASE:
        w = w.lower()
    return w


# ---------------------------------------------------------------- agrupamento
def group(words, hidden, hook_end, breaks=(), phrases=(), breaths=()):
    """Frases (pausa, pontuação, respiro cortado, até MAX_DUR s). As frases longas são divididas
    depois, em blocos curtos e lockups (plan_phrase)."""
    caps, cur = [], []
    cont = [False] * len(words)                      # palavras no meio de uma expressão de destaque
    toks = [norm(w["word"]) for w in words]
    for ph in phrases:
        n = len(ph)
        for i in range(len(toks) - n + 1):
            if n > 1 and toks[i:i + n] == ph:
                for j in range(i + 1, i + n):
                    cont[j] = True

    def flush():
        nonlocal cur
        if cur:
            caps.append(cur)
        cur = []

    for wi, w in enumerate(words):
        if any(a - 0.05 <= w["start"] < b for a, b in hidden):
            flush()
            continue
        if cur and not cont[wi] and (any(abs(w.get("src", -9) - b) < 0.06 for b in breaks)
                                     or any(cur[-1]["start"] < b <= w["start"] + 0.03 for b in breaths)):
            flush()
        if cur and not cont[wi]:
            was_hook = cur[0]["start"] < hook_end
            is_hook = w["start"] < hook_end
            if (was_hook != is_hook or w["start"] - cur[-1]["end"] > GAP_BREAK
                    or w["end"] - cur[0]["start"] > MAX_DUR
                    or re.search(r"[.?!…]$", cur[-1]["word"])
                    or (re.search(r",$", cur[-1]["word"]) and len(cur) >= 2)):
                flush()
        cur.append(w)
    flush()
    return caps


def mark_spans(ws, special):
    """[(palavras, tipo)] — expressões de destaque viram um span só (tipo None = palavras normais)."""
    toks = [norm(w["word"]) for w in ws]
    flags = [None] * len(ws)
    sid = 0
    for ph, kind in sorted(special, key=lambda p: -len(p[0])):
        n = len(ph)
        for i in range(len(toks) - n + 1):
            if toks[i:i + n] == ph and not any(f is not None for f in flags[i:i + n]):
                for j in range(i, i + n):
                    flags[j] = (sid, kind)
                sid += 1
    spans = []
    for i, w in enumerate(ws):
        if flags[i] is not None and spans and spans[-1][2] == flags[i][0]:
            spans[-1][0].append(w)
        elif flags[i] is not None:
            spans.append([[w], flags[i][1], flags[i][0]])
        else:
            spans.append([[w], None, None])
    return [(s[0], s[1]) for s in spans]


def wrap(words, fnt, max_w, max_words=B.LINE_WORDS):
    """Quebra palavras em linhas curtas (até max_words / max_w px)."""
    space = fnt.getlength(" ")
    lines, cur = [], []
    for w in words:
        wid = sum(fnt.getlength(clean(x["word"])) for x in cur + [w]) + space * len(cur)
        if cur and (len(cur) >= max_words or wid > max_w):
            lines.append(cur)
            cur = []
        cur.append(w)
    if cur:
        lines.append(cur)
    # última linha com uma palavra sozinha → puxa uma da linha de cima (se couber)
    if len(lines) >= 2 and len(lines[-1]) == 1 and len(lines[-2]) >= 3:
        lines[-1] = lines[-2][-1:] + lines[-1]
        lines[-2] = lines[-2][:-1]
    return lines


def plan_phrase(ws, special, mult):
    """Frase → blocos. Sem destaque: blocos normais de até CAPTION_MAX_LINES linhas.
    Com destaque: lockup = até LEAD_MAX palavras antes (em cima, à esquerda) + destaque + até TAIL_MAX
    palavras depois (embaixo, à direita); o que sobra vira bloco normal."""
    f_s = B.font(B.CAPTION_FONT, B.CAPTION_SIZE * mult)
    plans, pending, lock = [], [], None

    def flush_pending():
        nonlocal pending
        if pending:
            ls = wrap(pending, f_s, B.LINE_W * mult)
            for i in range(0, len(ls), B.CAPTION_MAX_LINES):
                plans.append({"type": "normal", "lines": ls[i:i + B.CAPTION_MAX_LINES]})
        pending = []

    def close_lock():
        nonlocal lock
        if lock:
            plans.append(lock)
        lock = None

    for words, kind in mark_spans(ws, special):
        if kind:
            carry = []                              # "de", "da", "a"… no fim do lockup anterior vão para o próximo
            while lock and len(lock["tail"]) >= 2 and norm(lock["tail"][-1]["word"]) in CONNECTORS:
                carry.insert(0, lock["tail"].pop())
            close_lock()
            pending += carry
            n_lead = B.LEAD_MAX + 1 if len(pending) == B.LEAD_MAX + 1 else B.LEAD_MAX   # não deixa 1 palavra sozinha
            lead = pending[-n_lead:] if pending else []
            pending = pending[:len(pending) - len(lead)]
            flush_pending()
            lock = {"type": "lock", "kind": kind, "lead": lead, "hero": words, "tail": []}
        elif lock is not None and len(lock["tail"]) < B.TAIL_MAX:
            lock["tail"] += words
        else:
            close_lock()
            pending += words
    close_lock()
    flush_pending()
    plans.sort(key=lambda p: (p["lines"][0][0] if p["type"] == "normal" else (p["lead"] or p["hero"])[0])["start"])
    return plans


# ---------------------------------------------------------------- desenho
def premul_blur(im, r):
    if r < 0.4:
        return im
    return im.convert("RGBa").filter(ImageFilter.GaussianBlur(r)).convert("RGBA")


def with_alpha(im, k):
    if k >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * max(0.0, k))))
    return im


def word_image(kind, text, fnt):
    """Palavra pronta (sombra + letra) e o pad. Branca: sombra escura justa + halo largo (lê na loja clara e na
    camisa branca do apresentador). Verde vivo (chave, itálico verde): contorno verde-escuro fino e sombra."""
    if kind in ("key", "accent"):                   # verde-limão com degradê e brilho (28/10)
        return B.lime_text(text, fnt)
    s = fnt.size
    green = kind in ("key", "accent")
    stroke = max(2, int(round(s * (0.03 if kind == "key" else 0.022)))) if green else 0
    pad = int(s * 0.36) + stroke
    m = B.text_mask(text, fnt, pad)
    b = fnt.getbbox(text)
    if stroke:
        sm = Image.new("L", m.size, 0)
        ImageDraw.Draw(sm).text((pad - b[0], pad - b[1]), text, font=fnt, fill=255,
                                stroke_width=stroke, stroke_fill=255)
    else:
        sm = m
    tight = Image.new("L", m.size, 0)
    tight.paste(sm.filter(ImageFilter.GaussianBlur(s * 0.035)), (0, max(1, int(s * 0.035))))
    dark = np.asarray(tight, dtype=np.float32) * (0.45 if kind == "boxtext" else 0.9)
    if kind != "boxtext":                           # halo largo: segura a leitura na camisa branca e na loja clara
        dark = np.maximum(dark, np.clip(np.asarray(sm.filter(ImageFilter.GaussianBlur(s * 0.18)), np.float32)
                                        * 0.95, 0, 170))
    out = Image.new("RGBA", m.size, B.INK + (0,))
    out.putalpha(Image.fromarray(np.clip(dark, 0, 255).astype(np.uint8)))
    if stroke:
        st = Image.new("RGBA", m.size, B.GREEN_DARK + (0,))
        st.putalpha(sm)
        out.alpha_composite(st)
    fill = Image.new("RGBA", m.size, (B.GREEN_VIVID if green else B.WHITE) + (0,))
    fill.putalpha(m)
    out.alpha_composite(fill)
    return out, pad


def reveal(im, k, feather):
    """Digitação: revela da esquerda para a direita com borda suave (k 0..1)."""
    if k >= 1:
        return im
    w = im.width
    x = np.arange(w, dtype=np.float32)
    edge = k * (w + feather)
    a = np.clip((edge - x) / max(1.0, feather), 0, 1)
    al = np.asarray(im.getchannel("A"), np.float32) * a[None, :]
    out = im.copy()
    out.putalpha(Image.fromarray(al.astype(np.uint8)))
    return out


class Piece:
    """Uma palavra (ou a expressão de destaque inteira) já desenhada; x = início do texto na linha."""

    def __init__(self, kind, text, fnt, start, end):
        self.kind, self.text, self.font = kind, text, fnt
        self.start, self.end = B.snap(start), end
        self.img, self.pad = word_image("boxtext" if kind == "box" else kind, text, fnt)
        self.w = fnt.getlength(text)
        self.bb = fnt.getbbox(text)
        hb = fnt.getbbox("H")
        self.cap, self.hb = hb[3] - hb[1], hb
        self.x = 0.0
        self.box = None
        self.type_dur = min(TYPE_MAX, max(TYPE_MIN, end - start)) if kind in TYPED else 0.0
        if kind == "box":
            px, py = int(fnt.size * 0.20), int(fnt.size * 0.12)
            self.box_pad = (px, py)
            self.box = B.rounded((int(self.w + 2 * px), int(self.cap + 2 * py)), max(4, int(fnt.size * 0.12)),
                                 B.GREEN + (255,))
        self.flare = B.lime_flare(text, fnt, self.pad) if kind in ("key", "accent") else None
        if kind == "strike":
            self.bar_h = max(8, int(fnt.size * 0.15))
            xb = fnt.getbbox("x")
            self.bar_y = (xb[3] - xb[1]) / 2 if text != text.upper() else self.cap / 2   # meio do "x" ou da maiúscula

    def extra(self):
        """Espaço extra acima/abaixo da linha (caixa)."""
        if self.box is not None:
            return self.box_pad[1], self.box_pad[1]
        return 0, 0

    def img_pos(self, line_x, base):
        """Canto da imagem da palavra para o texto começar em line_x + x com a linha de base em base."""
        return (line_x + self.x + self.bb[0] - self.pad, base - self.hb[3] + self.bb[1] - self.pad)

    def done_t(self):
        """Quando a palavra termina de entrar (digitação + risco / pop)."""
        if self.kind == "strike":
            return self.start + self.type_dur + STRIKE_IN / B.FPS
        if self.kind == "key":
            return self.start + KEY_IN / B.FPS
        return self.start + self.type_dur


class Block:
    """Bloco normal (linhas centradas) ou lockup (pequenas à esquerda em cima, destaque, pequenas à direita
    embaixo). Coordenadas: x relativo ao centro, y ao topo da 1ª linha."""

    def __init__(self, plan, hook, scale, max_w):
        mult = (B.HOOK_K if hook else 1.0) * scale
        s_norm = B.CAPTION_SIZE * mult
        self.plan, self.max_w, self.lock = plan, max_w, plan["type"] == "lock"
        self.lines = []

        def small_line(words, align, style, size):
            f = B.font(style, size)
            ps = [Piece("small", clean(w["word"]), f, w["start"], w["end"]) for w in words]
            space = f.getlength(" ")
            x = 0.0
            for p in ps:
                p.x = x
                x += p.w + space
            return {"kind": "small", "align": align, "pieces": ps, "w": x - space, "size": size,
                    "cum": [p.x + p.w for p in ps], "starts": [p.start for p in ps],
                    "cap": max(p.cap for p in ps)}

        if not self.lock:
            for words in plan["lines"]:
                self.lines.append(small_line(words, "center", B.CAPTION_FONT, s_norm))
        else:
            kind = plan["kind"]
            s_small = s_norm * B.SMALL_K
            style, k = {"big": (B.BIG_FONT, B.BIG_K), "accent": (B.ACCENT_FONT, B.ACCENT_K),
                        "strike": (B.STRIKE_FONT, B.STRIKE_K), "key": (B.KEY_FONT, B.KEY_K),
                        "box": (B.BOX_FONT, B.BOX_K)}[kind]
            txt = " ".join(clean(w["word"]) for w in plan["hero"])
            if kind in ("key", "box", "accent"):
                txt = re.sub(r"R\$\s*(\d)", r"R$ \1", txt.upper())
            size = s_norm * k
            room = max_w - (0.4 * size if kind == "box" else 0)
            while B.font(style, size).getlength(txt) > room and size > 30:
                size -= 3
            hero = Piece(kind, txt, B.font(style, size), plan["hero"][0]["start"], plan["hero"][-1]["end"])
            f_sm = B.font("Sans SemiBold Italic", s_small)
            for words in wrap(plan["lead"], f_sm, max(B.LINE_W * mult, hero.w), 4) if plan["lead"] else []:
                self.lines.append(small_line(words, "left", "Sans SemiBold Italic", s_small))
            self.lines.append({"kind": kind, "align": "left", "pieces": [hero], "w": hero.w, "size": size,
                               "cum": [hero.w], "starts": [hero.start], "cap": hero.cap})
            for words in wrap(plan["tail"], f_sm, max(B.LINE_W * mult, hero.w), 4) if plan["tail"] else []:
                self.lines.append(small_line(words, "right", "Sans SemiBold Italic", s_small))
            # x fixo: pequenas de antes alinhadas à esquerda do destaque, as de depois à direita
            hw = hero.w
            ind = 0.04 * s_small
            for ln in self.lines:
                ln["x0"] = -hw / 2 + (ind if ln["align"] == "left" and ln["kind"] == "small" else 0)
                if ln["align"] == "right":
                    ln["x0"] = hw / 2 - ind - ln["w"]
            lo = min(ln["x0"] for ln in self.lines)
            hi = max(ln["x0"] + ln["w"] for ln in self.lines)
            for ln in self.lines:                    # o conjunto fica centrado
                ln["x0"] -= (lo + hi) / 2
        # vertical: linhas quase encostadas; lockup ainda mais justo
        y = 0.0
        for i, ln in enumerate(self.lines):
            up = max(p.extra()[0] for p in ln["pieces"])
            dn = max(p.extra()[1] for p in ln["pieces"])
            if i:
                prev = self.lines[i - 1]
                y += (0.22 if self.lock else B.LEADING) * min(prev["size"], ln["size"]) * \
                    (1.0 if prev["kind"] == ln["kind"] == "small" else 1.4)
            ln["top"] = y
            ln["base"] = y + up + ln["cap"]
            y = ln["base"] + dn
        self.height = y
        allp = [p for ln in self.lines for p in ln["pieces"]]
        self.t_in = min(p.start for p in allp)
        self.last = max(p.done_t() for p in allp)
        self.end_words = max(p.end for p in allp)
        self.kinds = [p.kind for p in allp]
        maxw = max(abs(ln.get("x0", -ln["w"] / 2)) * 2 if ln["align"] == "center" else
                   2 * max(abs(ln["x0"]), abs(ln["x0"] + ln["w"])) for ln in self.lines)
        maxw = max([maxw] + [ln["w"] for ln in self.lines])
        self.ox = int(-maxw / 2 - MARGIN)
        self.oy = int(-MARGIN)
        self.size = (int(maxw + 2 * MARGIN), int(self.height + 2 * MARGIN))
        bb = self.draw(self.last + 5).getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox()
        self.vis = (bb[0] + self.ox, bb[1] + self.oy, bb[2] + self.ox, bb[3] + self.oy)

    @staticmethod
    def stepped(points, t, frames):
        """Valor em degraus suavizados: [(t, v)] → v desliza do anterior para o novo em `frames` quadros."""
        prev, val, t_k = None, None, 0.0
        for tk, v in points:
            if t + 1e-6 < tk:
                break
            prev, val, t_k = val, v, tk
        if val is None:
            return points[0][1]
        if prev is None:
            return val
        e = B.ease_out_cubic((t - t_k) * B.FPS / frames)
        return prev + (val - prev) * e

    def line_x(self, ln, t):
        """Início (x) da linha: fixo no lockup; na frase normal, centrada pelo que já apareceu (desliza)."""
        if "x0" in ln:
            return ln["x0"]
        return self.stepped([(s, -c / 2) for s, c in zip(ln["starts"], ln["cum"])], t, RECENTER)

    def draw(self, t):
        """Bloco no instante t (sem a saída)."""
        c = Image.new("RGBA", self.size, (0, 0, 0, 0))
        for ln in self.lines:
            lx = self.line_x(ln, t) - self.ox
            base = ln["base"] - self.oy
            for p in ln["pieces"]:
                dt = (t - p.start) * B.FPS
                if dt < 0:
                    continue
                px, py = p.img_pos(lx, base)
                cx, cy = px + p.img.width / 2, py + p.img.height / 2
                if p.box is not None and dt >= BOX_DELAY:                 # caixa abre da esquerda
                    k = B.ease_out_cubic((dt - BOX_DELAY) / BOX_IN)
                    bw = max(1, int(p.box.width * k))
                    bx = int(round(lx + p.x - p.box_pad[0]))
                    by = int(round(base - p.cap - p.box_pad[1]))
                    B._safe_composite(c, p.box.crop((0, 0, bw, p.box.height)), bx, by)
                if p.kind == "key":                                       # pop: grande e desfocada → no lugar
                    k = dt / KEY_IN
                    if k >= 1:
                        c.alpha_composite(p.img, (int(round(px)), int(round(py))))
                        kf = (t - p.done_t()) / FLARE                     # brilho "acende" quando assenta
                        if kf < 1:
                            B._safe_composite(c, with_alpha(p.flare, (1 - kf) ** 2), int(round(px)), int(round(py)))
                    else:
                        e = B.ease_out_cubic(k)
                        s0 = max(1.0, min(1.25, (self.max_w + 2 * SIDE) / max(1.0, p.w)))   # não sai da margem
                        B.paste_center(c, B.scale_rgba(premul_blur(p.img, 9 * (1 - e)), s0 - (s0 - 1) * e),
                                       cx, cy, alpha=min(1.0, 2.2 * k))
                elif p.kind in TYPED:                                     # digitada letra a letra
                    k = (t - p.start) / max(1e-3, p.type_dur)
                    im = reveal(p.img, B.clamp01(k), TYPE_FEATHER * p.img.width)
                    if k < 1:
                        im = premul_blur(im, 2.5 * (1 - B.clamp01(k)))
                    B._safe_composite(c, im, int(round(px)), int(round(py)))
                    if p.flare is not None:                               # brilho "acende" quando termina de entrar
                        kf = (t - p.done_t()) / FLARE
                        if -0.5 <= kf < 1:
                            a = (1 - abs(kf) * 2) if kf < 0 else (1 - kf) ** 2
                            B._safe_composite(c, with_alpha(p.flare, max(0.0, a)), int(round(px)), int(round(py)))
                    if p.kind == "strike":                                # a barra risca depois de digitada
                        ks = B.ease_out_cubic((t - p.start - p.type_dur) * B.FPS / STRIKE_IN)
                        if ks > 0:
                            over = p.font.size * 0.10
                            x0 = lx + p.x - over
                            x1 = x0 + (p.w + 2 * over) * ks
                            ym = base - p.bar_y
                            h = p.bar_h
                            sh = Image.new("L", self.size, 0)
                            ImageDraw.Draw(sh).rounded_rectangle((x0, ym - h / 2 + 4, x1, ym + h / 2 + 4),
                                                                 h // 3, fill=140)
                            lay = Image.new("RGBA", self.size, B.INK + (0,))
                            lay.putalpha(sh.filter(ImageFilter.GaussianBlur(4)))
                            c.alpha_composite(lay)
                            ImageDraw.Draw(c).rounded_rectangle((x0, ym - h / 2, x1, ym + h / 2), h // 3,
                                                                fill=B.GREEN_VIVID + (255,))
                elif p.kind == "box":                                     # palavra entra junto com a caixa
                    k = B.clamp01((dt - BOX_DELAY) / BOX_IN)
                    B._safe_composite(c, reveal(p.img, k, 0.15 * p.img.width), int(round(px)), int(round(py)))
                else:                                                     # pequena: desfocada → nítida
                    k = dt / WORD_IN
                    if k >= 1:
                        c.alpha_composite(p.img, (int(round(px)), int(round(py))))
                    else:
                        e = B.ease_out_cubic(k)
                        im = premul_blur(p.img, 6 * (1 - e))
                        B.paste_center(c, B.scale_rgba(im, 0.94 + 0.06 * e), cx, cy + 8 * (1 - e),
                                       alpha=min(1.0, 0.2 + 1.1 * k))
        return c

    def frame(self, t):
        """Imagem no instante t, já com a saída; None fora da tela."""
        if t < self.t_in - 1e-6 or t >= self.t_gone - 1e-6:
            return None
        c = self.draw(t)
        if t < self.t_out:
            return c
        e = B.clamp01(((t - self.t_out) * B.FPS + 1) / (BLOCK_OUT + 1))
        return with_alpha(premul_blur(c, 6 * e), 1 - e)


def merge_fixes(words, fixes):
    """Correções com mais de uma palavra ("electro company" → "Eletro Company") juntam as palavras numa só."""
    multi = sorted([(k.split(), v) for k, v in fixes.items() if len(k.split()) > 1], key=lambda x: -len(x[0]))
    out, i = [], 0
    while i < len(words):
        for toks, v in multi:
            n = len(toks)
            if [norm(w["word"]) for w in words[i:i + n]] == [norm(t) for t in toks]:
                tail = re.sub(r"^.*?([.,;:?!]*)$", r"\1", words[i + n - 1]["word"])
                out.append(dict(words[i], word=v + tail, end=words[i + n - 1]["end"]))
                i += n
                break
        else:
            w = words[i]
            n = norm(w["word"])
            if n in fixes and len(n.split()) == 1:
                w = dict(w, word=fixes[n] + re.sub(r"^.*?([.,;:?!]*)$", r"\1", w["word"]))
            out.append(w)
            i += 1
    return out


def main():
    edl_path = sys.argv[1] if len(sys.argv) > 1 else "edl.json"
    edl = B.load_edl(edl_path)
    cfg = edl.get("captions", {})
    cy_default = cfg.get("cy", B.CAPTION_CY)
    hook_end = float(cfg.get("hook_end", 0))
    OPTS["punct"] = bool(cfg.get("punct", False))
    OPTS["lower"] = bool(cfg.get("lower", False))
    KEEP_CASE.update(norm(k) for k in cfg.get("keep_case", []))
    special = []
    for key, kind in (("big", "big"), ("accents", "accent"), ("strikes", "strike"), ("keywords", "key"),
                      ("boxes", "accent")):          # a caixa verde virou verde-limão (28/10)
        special += [([norm(x) for x in k.split()], kind) for k in cfg.get(key, [])]
    fixes = {" ".join(norm(t) for t in k.split()): v for k, v in cfg.get("fix", {}).items()}
    words = B.load_words(edl)
    if not words:
        sys.exit("Sem transcript.json — rode transcribe.py antes (ou desligue as legendas no EDL).")
    words = merge_fixes(words, fixes)
    max_w = B.SAFE[2] - B.SAFE[0] - 2 * SIDE
    hidden = B.opaque_windows(edl) + [tuple(x) for x in cfg.get("skip", [])]
    segs = B.segments_out(edl)
    # respiros cortados (o original pula entre dois trechos) também fecham a frase
    breaths = [segs[i][2] for i in range(1, len(segs)) if segs[i][0] - segs[i - 1][1] > 0.05]
    caps = group(words, hidden, hook_end, cfg.get("breaks", []), [p for p, _ in special], breaths)

    plans = []                                       # (plano, gancho) de cada bloco
    for ws in caps:
        hook = ws[0]["start"] < hook_end
        plans += [(p, hook) for p in plan_phrase(ws, special, B.HOOK_K if hook else 1.0)]
    blocks = [Block(p, hook, 1.0, max_w) for p, hook in plans]
    order = sorted(range(len(blocks)), key=lambda i: blocks[i].t_in)
    blocks = [blocks[i] for i in order]
    plans = [plans[i] for i in order]

    def seg_of(t):
        return next((i for i, s in enumerate(segs) if s[2] - 1e-6 <= t < s[3]), -1)

    # cards da frente (produto, etiqueta) já renderizados: a legenda termina acima deles
    try:
        front = [b for b in json.load(open(os.path.join(edl["_dir"], "bboxes.json"))).get("cards", [])
                 if b["tag"].split(":")[0] in FRONT_CARDS and "t_end" in b]
    except (OSError, ValueError):
        front = []

    total = B.total_duration(edl)
    prev = None
    for i in range(len(blocks)):
        u = blocks[i]
        # sai quando o próximo entra (ou um pouco depois da última palavra, se houver pausa)
        t_out = B.snap(max(u.last + 3 / B.FPS, u.end_words + TAIL))
        if i + 1 < len(blocks):                     # começa a sumir 2 quadros antes do próximo entrar
            t_out = min(t_out, max(B.snap(u.last + 2 / B.FPS), blocks[i + 1].t_in - 2 / B.FPS))
        for a, b in hidden:                         # sai inteiro antes do preço / tela de cor / card final
            if u.t_in < a < t_out + BLOCK_OUT / B.FPS:
                t_out = max(u.t_in + 2 / B.FPS, B.snap(a - BLOCK_OUT / B.FPS))
        t_out = min(t_out, B.snap(total - BLOCK_OUT / B.FPS))
        t_gone = t_out + BLOCK_OUT / B.FPS
        neck = B.neck_line(edl, u.t_in, t_gone)
        hook = plans[i][1]

        def place(b):
            """1ª linha logo abaixo do meio do pescoço; sem rosto, bloco centrado em cy."""
            return neck + B.NECK_GAP - b.vis[1] if neck is not None else cy_default - (b.vis[1] + b.vis[3]) / 2

        top = place(u)
        u.above = False
        if hook and cfg.get("hook_top"):            # gancho acima da cabeça (se couber na margem / abaixo do logo)
            ht = B.head_top(edl, u.t_in, t_gone)
            lo = (B.badge_bottom() + 16) if edl.get("logo", B.LOGO_ON_VIDEO) else B.SAFE[1] + 6
            if ht is not None and ht - 24 - (u.vis[3] - u.vis[1]) >= lo:
                top = ht - 24 - u.vis[3]
                u.above = True
        sg = seg_of(u.t_in)
        if prev and prev[0] == sg and prev[2] == hook and abs(prev[1] - top) < 40 and \
                (neck is None or prev[1] >= top - 6):
            top = prev[1]                           # mesma tomada: a legenda não fica pulando
        # não cabe até a margem de baixo (ou até o produto/etiqueta na tela) → encolhe o bloco (até MIN_SCALE)
        # e, no limite, sobe
        bottom_lim = min([B.SAFE[3] - 6] + [b["box"][1] - 14 for b in front
                                            if b["t"] < t_gone and u.t_in < b["t_end"]])
        if top + u.vis[3] > bottom_lim and not u.above:
            s = max(MIN_SCALE, (bottom_lim - top) / max(1, u.vis[3]))
            u = blocks[i] = Block(plans[i][0], hook, s, max_w)
            u.above = False
            top = min(place(u), bottom_lim - u.vis[3])
        top = max(top, B.SAFE[1] + 6 - u.vis[1])
        u.t_out, u.t_gone = t_out, t_gone
        u.top = int(round(top))
        u.cx = B.W // 2
        prev = (sg, u.top, hook)

    nfr = B.total_frames(edl)
    fw = FrameWriter(os.path.join(edl["_dir"], "captions.mov"), alpha=True)
    blank = Image.new("RGBA", (B.W, B.H), (0, 0, 0, 0))
    j0 = 0
    for f in range(nfr):
        t = f / B.FPS
        while j0 < len(blocks) and blocks[j0].t_gone <= t:
            j0 += 1
        live = []
        for u in blocks[j0:]:
            if u.t_in > t + 1e-6:
                break
            r = u.frame(t)
            if r:
                live.append((u, r))
        if not live:
            fw.write(blank)
            continue
        im = blank.copy()
        for u, c in live:
            B._safe_composite(im, c, u.cx + u.ox, u.top + u.oy)
        fw.write(im)
    fw.close()

    boxes = []
    for i, u in enumerate(blocks):
        txt = " / ".join(" ".join(p.text for p in ln["pieces"]) for ln in u.lines)
        kinds = sorted({k for k in u.kinds if k != "small"})
        boxes.append({"tag": f"legenda {i + 1}{' (gancho)' if plans[i][1] else ''}"
                             f"{' [' + ', '.join(kinds) + ']' if kinds else ''}: {txt}",
                      "t": round(u.t_in, 2), "t_end": round(u.t_gone, 2),
                      "hook_top": u.above,
                      "box": [u.cx + u.vis[0], u.top + u.vis[1], u.cx + u.vis[2] - 1, u.top + u.vis[3] - 1]})
    B.write_bboxes("captions", edl, boxes)

    # efeitos sonoros da legenda (o build.py mixa): impacto no destaque do gancho, dinheiro na chave com valor,
    # pop na caixa, risco de caneta na palavra riscada, clique no "clique". O resto fica sem som (não poluir)
    sfx = []
    for u in blocks:
        for ln in u.lines:
            for p in ln["pieces"]:
                if p.kind == "key" and PRICE.search(p.text):
                    sfx.append({"t": round(p.start, 3), "kind": "cash", "why": p.text})
                elif p.kind in HERO and u.t_in < hook_end:
                    sfx.append({"t": round(p.start, 3), "kind": "impact", "why": p.text})
                elif p.kind == "box":
                    sfx.append({"t": round(p.start + BOX_DELAY / B.FPS, 3), "kind": "pop", "why": p.text})
                elif p.kind == "strike":
                    sfx.append({"t": round(p.start + p.type_dur, 3), "kind": "swipe", "why": p.text})
    for w in words:
        if norm(w["word"]) in CLICK_WORDS and not any(a - 0.05 <= w["start"] < b for a, b in hidden):
            sfx.append({"t": round(B.snap(w["start"]), 3), "kind": "click", "why": w["word"]})
    with open(os.path.join(edl["_dir"], "captions_sfx.json"), "w") as f:
        json.dump(sorted(sfx, key=lambda e: e["t"]), f, ensure_ascii=False, indent=1)
    nk = sum(1 for u in blocks for k in u.kinds if k in HERO)
    print(f"{len(blocks)} blocos de legenda ({nk} destaques; gancho até {hook_end:.1f}s) → captions.mov")


if __name__ == "__main__":
    main()
