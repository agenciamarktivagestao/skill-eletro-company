"""Enquadramento automático → "zoom"/"anchor" de cada trecho do EDL (padrão desde 29/10)

Uso:  python frame.py [edl.json]      (o build.py chama sozinho antes da base)

Pedido da agência: sem título no alto, o vídeo não deixa "teto" vazio em cima da cabeça. Em cada trecho com o
apresentador, o rosto é achado no bruto (Haar, 2 quadros por segundo) e o trecho ganha:
  • a pessoa centralizada na horizontal (com duas pessoas, o meio das duas);
  • o alto da cabeça a HEAD_TOP px do topo no plano aberto: o zoom mínimo que tira o teto (zoom in) ou, se a
    cabeça já está no alto, o zoom 1.0 (zoom out até o quadro inteiro);
  • o nível do trecho ("level": aberto / medio / fechado) multiplica esse zoom mínimo (LEVEL). Sem "level", ele
    vem do zoom escrito no EDL: 1.0 aberto, ~1.15 médio (produto), ≥1.2 fechado (frase forte, CTA).
Ficam como estão: "frame": "manual" no trecho (ex.: duas pessoas, em que o Haar às vezes só acha um rosto),
"person": false (imagens de apoio) e os trechos com título no
alto (capa, título, tag, lista acima da cabeça, gancho com "hook_top"), que precisam do espaço em cima.
O rosto medido fica no trecho ("_face"); só é medido de novo se o início/fim do trecho mudar.
"""
import json
import os
import subprocess
import sys

import cv2
import numpy as np

import brand as B

HEAD_TOP = 230            # px (quadro 1080×1920): alto da cabeça no plano aberto
LEVEL = {"aberto": 1.0, "medio": 1.1, "fechado": 1.22}
ZOOM_MAX = 1.8            # a tela 9:16 do bruto 4K tem 2× a resolução da saída
SIDE = 1.3                # com duas pessoas, a janela tem pelo menos 1,3× a largura dos rostos
HAIR = 0.25               # o cabelo começa ~25% da altura do rosto acima do retângulo do Haar (medido em 29/10;
                          # o B.HAIR_K = 0,55 é folgado de propósito, para os títulos ficarem acima da cabeça)
TOP_CARDS = {"topic", "title", "tag"}


def level_of(s):
    if s.get("level") in LEVEL:
        return s["level"]
    z = float(s.get("zoom", 1.0))
    return "aberto" if z < 1.08 else "medio" if z < 1.2 else "fechado"


def top_windows(edl):
    """Janelas (tempo de saída) com algo no alto: capa, título, tag, lista acima da cabeça, gancho em cima."""
    w = [(c["at"], c["at"] + c.get("dur", 0)) for c in edl.get("cards", [])
         if c["type"] in TOP_CARDS or (c["type"] == "checklist" and c.get("place") != "below")]
    cap = edl.get("captions", {})
    if cap.get("hook_top") and cap.get("hook_end"):
        w.append((0.0, float(cap["hook_end"])))
    return w


def measure(src, sw, sh, a, b):
    """[centro x, alto da cabeça y, largura dos rostos] no quadro 9:16 de zoom 1 (1080×1920), ou None."""
    import person as PS
    cc = cv2.CascadeClassifier(PS.model("haarcascade_frontalface_default.xml", PS.HAAR_URL))
    if sw / sh > 9 / 16:
        bw, bh = sh * 9 / 16, sh
    else:
        bw, bh = sw, sw * 16 / 9
    bx, by = (sw - bw) / 2, (sh - bh) / 2
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{max(0.1, b - a):.3f}", "-i", src,
                        "-vf", f"fps=2,crop={int(bw)}:{int(bh)}:{int(bx)}:{int(by)},scale=540:960",
                        "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    xs, tops, ws = [], [], []
    for i in range(len(p) // (540 * 960)):
        g = np.frombuffer(p, np.uint8, 540 * 960, i * 540 * 960).reshape(960, 540)
        fs = [f for f in cc.detectMultiScale(g, 1.1, 5, minSize=(28, 28)) if f[1] + f[3] / 2 < 960 * 0.7]
        if not fs:
            continue
        big = max(f[3] for f in fs)
        fs = [f for f in fs if f[3] >= 0.6 * big]                  # rostos de verdade (não detalhes do fundo)
        x0, x1 = min(f[0] for f in fs), max(f[0] + f[2] for f in fs)
        xs.append((x0 + x1)); ws.append((x1 - x0) * 2)
        tops.append(min(f[1] - f[3] * HAIR for f in fs) * 2)
    if len(xs) < 2:
        return None
    # a cabeça mais alta do trecho (percentil 20) não pode passar do topo; o centro é a mediana
    return [round(float(np.median(xs)), 1), round(float(np.percentile(tops, 20)), 1), round(float(np.median(ws)), 1)]


def framing(face, level):
    xc, yt, fw = face
    k0 = max(1.0, (B.H - HEAD_TOP) / max(1.0, B.H - yt))       # zoom mínimo que põe a cabeça em HEAD_TOP
    k = min(ZOOM_MAX, k0 * LEVEL[level], max(1.0, B.W / (fw * SIDE)) if fw > 0.35 * B.W else ZOOM_MAX)
    ay = yt + (B.H / 2 - HEAD_TOP) / k
    ay = min(max(ay, B.H / 2 / k), B.H - B.H / 2 / k)
    ax = min(max(xc, B.W / 2 / k), B.W - B.W / 2 / k)
    return round(k, 3), [round(ax), round(ay)]


def auto_frame(edl, src):
    """Atualiza zoom/anchor dos trechos (no próprio dicionário). Devolve True se algo mudou."""
    import build as BLD
    if edl.get("frame", "auto") != "auto":
        return False
    src = BLD.sdr_proxy(src, edl["_dir"]) if edl.get("hdr", "auto") else src
    sw, sh, _, _ = BLD.video_geom(BLD.probe(src))
    segs = B.segments_out(edl)
    valid = [s for s in edl["segments"] if B.snap(s["end"]) > B.snap(s["start"])]
    tops = top_windows(edl)
    changed = False
    for s, (a, b, oa, ob) in zip(valid, segs):
        if s.get("frame") == "manual" or s.get("person") is False or any(x < ob and oa < y for x, y in tops):
            continue
        lv = level_of(s)
        if s.get("_face_t") != [s["start"], s["end"]]:
            s["_face"] = measure(src, sw, sh, a, b)
            s["_face_t"] = [s["start"], s["end"]]
        if not s.get("_face"):
            continue
        z, anc = framing(s["_face"], lv)
        if s.get("zoom") != z or s.get("anchor") != anc or s.get("level") != lv:
            s.update(level=lv, zoom=z, anchor=anc, _frame="auto")
            changed = True
    return changed


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "edl.json"
    edl = B.load_edl(path)
    src = os.path.normpath(os.path.join(edl["_dir"], edl["source"]))
    if auto_frame(edl, src):
        json.dump({k: v for k, v in edl.items() if k != "_dir"}, open(path, "w"), ensure_ascii=False, indent=1)
    for s in edl["segments"]:
        print(f"  {s['start']:6.2f}–{s['end']:6.2f}  {s.get('level', '-'):8s} zoom {s.get('zoom')}  anchor {s.get('anchor')}"
              f"  rosto {s.get('_face')}")


if __name__ == "__main__":
    main()
