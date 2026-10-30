"""Revisão automática antes de mostrar ao cliente.

  python selfeval.py preview.mp4 base.mkv [--edl edl.json]

Confere: nº de quadros = EDL · áudio = vídeo · sincronismo em cada corte
(áudio da base × original) · margem de segurança (bboxes.json) · legenda do
meio do pescoço para baixo · loudness (−14 LUFS, pico ≤ −1,5 dBTP). Gera contact.jpg (folha de
contato) e card_edges.jpg (quadros nas bordas de cada card).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

import brand as B

OK, BAD = "OK  ", "FALHA"


def count_frames(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
                          "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", p],
                         capture_output=True, text=True).stdout
    return int(out.strip().split(",")[0])


def stream_dur(p, kind):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", f"{kind}:0", "-show_entries",
                          "stream=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout
    try:
        return float(out.strip())
    except ValueError:
        return None


def mono16(p, start, dur):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{start:.4f}", "-t", f"{dur:.4f}", "-i", p,
                          "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def best_lag(x, y, max_ms=60):
    """lag (ms) que melhor alinha x (saída) com y (original, com margem)."""
    m = int(16 * max_ms)
    best, bl = -1e9, 0
    for lag in range(-m, m + 1, 4):
        seg = y[m + lag: m + lag + len(x)]
        if len(seg) < len(x):
            continue
        c = float(np.dot(x, seg) / (np.linalg.norm(x) * np.linalg.norm(seg) + 1e-9))
        if c > best:
            best, bl = c, lag
    return bl / 16, best


def frame_at(p, t, path):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{max(0, t):.4f}", "-i", p, "-frames:v", "1",
                    "-vf", "scale=270:480", path])
    return Image.open(path).convert("RGB") if os.path.exists(path) else Image.new("RGB", (270, 480))


def sheet(items, out, cols=6):
    rows = (len(items) + cols - 1) // cols
    im = Image.new("RGB", (cols * 280, rows * 520), (20, 20, 20))
    d = ImageDraw.Draw(im)
    safe = [int(v / 4) for v in B.SAFE]
    for i, (fr, label) in enumerate(items):
        x, y = (i % cols) * 280 + 5, (i // cols) * 520 + 5
        im.paste(fr, (x, y))
        d.rectangle((x + safe[0], y + safe[1], x + safe[2], y + safe[3]), outline=(255, 60, 60))
        d.text((x + 2, y + 484), label[:44], fill=(230, 230, 230))
    im.save(out, quality=88)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("base")
    ap.add_argument("--edl", default="edl.json")
    a = ap.parse_args()
    edl = B.load_edl(a.edl)
    d = edl["_dir"]
    problems = 0

    # 1) quadros
    nf, want = count_frames(a.video), B.total_frames(edl)
    st = OK if nf == want else BAD
    problems += st == BAD
    print(f"[{st}] quadros: {nf} (EDL pede {want})")

    # 2) áudio x vídeo
    va, vv = stream_dur(a.video, "a"), stream_dur(a.video, "v")
    if va and vv:
        st = OK if abs(va - vv) <= 1.5 / B.FPS else BAD
        problems += st == BAD
        print(f"[{st}] duração: vídeo {vv:.3f}s, áudio {va:.3f}s")

    # 3) sincronismo em cada trecho (base × original)
    src = os.path.normpath(os.path.join(d, edl["source"]))
    lags = []
    for i, (s0, s1, o0, o1) in enumerate(B.segments_out(edl)):
        L = min(0.6, (s1 - s0) - 0.1)
        if L < 0.2:
            continue
        x = mono16(a.base, o0 + 0.05, L)
        y = mono16(src, max(0, s0 + 0.05 - 0.06), L + 0.12)
        if len(x) < 1000 or np.sqrt(np.mean(x ** 2)) < 0.003:
            continue
        if s0 + 0.05 - 0.06 < 0:
            continue
        lag, c = best_lag(x, y)
        lags.append((i, lag, c))
    if lags:
        worst = max(lags, key=lambda z: abs(z[1]))
        st = OK if abs(worst[1]) <= 5 else BAD
        problems += st == BAD
        print(f"[{st}] sincronismo: {len(lags)} trechos medidos, pior desvio {worst[1]:+.1f} ms (trecho {worst[0]})")
    else:
        print("[ -- ] sincronismo: sem trechos com fala para medir")

    # 4) margem de segurança e posição da legenda
    bp = os.path.join(d, "bboxes.json")
    if os.path.exists(bp):
        boxes = json.load(open(bp))
        x0, y0, x1, y1 = B.SAFE
        bad = [b for grp in boxes.values() for b in grp
               if b["box"][0] < x0 or b["box"][1] < y0 or b["box"][2] > x1 or b["box"][3] > y1]
        st = OK if not bad else BAD
        problems += st == BAD
        print(f"[{st}] margem de segurança: {sum(len(v) for v in boxes.values())} elementos, {len(bad)} fora")
        for b in bad[:10]:
            print(f"        fora: {b['tag']} {b['box']}")
        caps = boxes.get("captions", [])
        # legenda e cards da frente nunca no rosto: topo ≥ meio do pescoço (person.json)
        front = [b for b in caps if not b.get("hook_top")] + \
            [b for b in boxes.get("cards", []) if b["tag"].split(":")[0] in ("price", "product", "label")]
        high = []
        for b in [b for b in caps if b.get("hook_top")]:     # gancho acima da cabeça: tem que terminar antes dela
            ht = B.head_top(edl, b["t"], b.get("t_end", b["t"] + 0.8))
            if ht is not None and b["box"][3] > ht + 4:
                high.append((b, ht))
        for b in front:
            nk = B.neck_line(edl, b.get("t", 0), b.get("t_end", b.get("t", 0) + 0.8))
            lim = nk if nk is not None else B.CAPTION_MIN_TOP
            if b["box"][1] < lim - 4:
                high.append((b, lim))
        st = OK if not high else BAD
        problems += st == BAD
        print(f"[{st}] legenda/preço do meio do pescoço para baixo (nunca no rosto): {len(front) - len(high)}/{len(front)}"
              + (" (+ gancho acima da cabeça)" if any(b.get("hook_top") for b in caps) else ""))
        for b, lim in high[:6]:
            print(f"        no rosto: {b['tag']} topo {b['box'][1]} < pescoço {int(lim)}")
        pj = B.load_person(edl)
        if pj:
            n = sum(1 for f in pj["faces"] if f)
            print(f"[ -- ] rosto encontrado em {n} quadros; títulos atrás da pessoa: {len(pj.get('windows', []))} janelas")

    # 4b) cor: etiquetas BT.709 e cor da base igual à do bruto (trechos sem zoom, média Y/U/V do quadro inteiro)
    tags = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                           "stream=color_range,color_space,color_transfer,color_primaries", "-of", "csv=p=0", a.video],
                          capture_output=True, text=True).stdout.strip()
    st = OK if tags.split(",") == ["tv", "bt709", "bt709", "bt709"] else BAD
    problems += st == BAD
    print(f"[{st}] etiquetas de cor: {tags} (esperado tv, bt709, bt709, bt709)")
    hdr_src = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=color_transfer",
                              "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip() in ("arib-std-b67", "smpte2084")
    valid = [sg for sg in edl["segments"] if B.snap(sg["end"]) > B.snap(sg["start"])]
    diffs = []
    for (s0, s1, o0, o1), sg in zip(B.segments_out(edl), valid):
        if float(sg.get("zoom", 1.0)) != 1.0 or len(diffs) >= 3 or hdr_src:
            continue
        tm = round((o0 + o1) / 2 * B.FPS) / B.FPS
        ys = []
        for p_, t_, vf in ((src, s0 + (tm - o0), "scale=1080:1920:flags=lanczos"), (a.base, tm, "null")):
            raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t_:.4f}", "-i", p_, "-frames:v", "1", "-vf", vf,
                                  "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"], capture_output=True).stdout
            q = np.frombuffer(raw, np.uint8).astype(float)
            n_ = 1080 * 1920
            ys.append(np.array([q[:n_].mean(), q[n_:n_ * 5 // 4].mean(), q[n_ * 5 // 4:].mean()]))
        if len(ys) == 2:
            diffs.append(np.abs(ys[0] - ys[1]).max())
    if diffs:
        st = OK if max(diffs) <= 0.8 else BAD
        problems += st == BAD
        print(f"[{st}] cor igual ao bruto: maior diferença {max(diffs):.2f} níveis em {len(diffs)} trechos sem zoom (máx. 0,8)")
    elif hdr_src:
        print("[ -- ] cor: bruto HDR convertido para SDR (não dá para comparar com o original)")

    # 5) loudness
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", a.video, "-vn", "-af", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    summ = r[r.rfind("Summary:"):]
    I = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summ).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summ).group(1))
    st = OK if abs(I + 14) <= 1.0 and tp <= -1.5 else BAD
    problems += st == BAD
    print(f"[{st}] loudness: {I:.1f} LUFS, pico {tp:.1f} dBTP (alvo −14 / ≤ −1,5)")

    # 6) folhas de contato
    td = tempfile.mkdtemp()
    items = []
    segs = B.segments_out(edl)
    step = max(1, len(segs) // 18)
    for i in range(0, len(segs), step):
        t = (segs[i][2] + segs[i][3]) / 2
        z = [s for s in edl["segments"] if B.snap(s["end"]) > B.snap(s["start"])][i].get("zoom", 1)
        items.append((frame_at(a.video, t, f"{td}/s{i}.png"), f"trecho {i} z{z} {t:.1f}s"))
    if os.path.exists(bp):
        for j, b in enumerate(json.load(open(bp)).get("captions", [])[:12]):
            items.append((frame_at(a.video, b["t"] + 0.35, f"{td}/c{j}.png"), f"leg {b['t']:.1f}s"))
    sheet(items, os.path.join(d, "contact.jpg"))
    edges = []
    for k, (c0, c1, c) in enumerate(B.card_windows(edl)):
        for lab, t in (("antes", c0 - 1 / B.FPS), ("1º", c0), ("último", c1 - 1 / B.FPS),
                       ("depois", c1 if c1 < B.total_duration(edl) - 1e-3 else None)):
            if t is None:
                continue
            edges.append((frame_at(a.video, t - 0.25 / B.FPS, f"{td}/e{k}{lab}.png"), f"{c['type']} {lab} {t:.2f}s"))
    if edges:
        sheet(edges, os.path.join(d, "card_edges.jpg"), cols=4)
    print(f"folhas: contact.jpg ({len(items)} quadros)" + (f", card_edges.jpg ({len(edges)})" if edges else ""))
    print("RESULTADO:", "tudo certo" if not problems else f"{problems} problema(s) — corrigir antes de mostrar")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
