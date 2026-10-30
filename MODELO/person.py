"""Onde está a pessoa em cada quadro → person.json (+ person_mask.mkv)

Uso:  python person.py [edl.json]      (o build.py chama sozinho quando precisa)

  • Rosto (OpenCV Haar, quadro a quadro, suavizado): a legenda e os cards de preço/serviço
    começam sempre do MEIO DO PESCOÇO PARA BAIXO; capa e lista ficam ACIMA DA CABEÇA.
  • Recorte da pessoa (U²-Net human seg, só nas janelas dos cards "behind"): o build.py
    põe a pessoa de novo por cima desses cards — o título fica ATRÁS dela, nunca na frente.

Modelos em ~/models (baixa na 1ª vez, do GitHub):
  haarcascade_frontalface_default.xml (opencv) · u2net_human_seg.onnx (rembg)
"""
import json
import math
import os
import subprocess
import sys
import urllib.request

import cv2
import numpy as np

import brand as B

MODELS = os.path.expanduser(os.environ.get("ASR_MODELS", "~/models"))
HAAR_URL = "https://raw.githubusercontent.com/opencv/opencv/4.x/data/haarcascades/haarcascade_frontalface_default.xml"
SEG_URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net_human_seg.onnx"
BEHIND_DEFAULT = {"topic", "checklist", "title", "tag"}   # label fica na frente (abaixo da legenda, no corpo)
SEG_EVERY = 2            # recorte a cada 2 quadros (ela se mexe devagar); o do meio repete


def model(name, url):
    p = os.path.join(MODELS, name)
    if not os.path.exists(p):
        os.makedirs(MODELS, exist_ok=True)
        print(f"baixando {name} …")
        urllib.request.urlretrieve(url, p)
    return p


def behind_windows(edl):
    out = []
    for a, b, c in B.card_windows(edl):
        if c.get("behind", c["type"] in BEHIND_DEFAULT and c.get("place") != "below"):
            out.append((a, b))
    return out


def no_person_frames(edl):
    """Quadros dos trechos com "person": false (imagens de apoio que já vêm no bruto): sem rosto. O detector
    achava "rostos" nas luminárias e a legenda pulava de altura no meio do b-roll."""
    valid = [s for s in edl["segments"] if B.snap(s["end"]) > B.snap(s["start"])]
    out = set()
    for (a, b, oa, ob), s in zip(B.segments_out(edl), valid):
        if s.get("person", True) is False:
            out.update(range(int(round(oa * B.FPS)), int(round(ob * B.FPS))))
    return out


def frames(path, w, h):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={w}:{h}", "-f", "rawvideo",
                          "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    n = w * h * 3
    while True:
        raw = p.stdout.read(n)
        if len(raw) < n:
            break
        yield np.frombuffer(raw, np.uint8).reshape(h, w, 3)
    p.wait()


def track(cands, win=12, tol=0.8):
    """Um rosto por quadro, seguindo o caminho do rosto: o detector às vezes acha "rostos" no chão ou
    na parede por vários quadros seguidos (e a legenda descia para fugir deles). 1ª passada: o maior
    de cada quadro → mediana móvel de ±win quadros (centro e tamanho). 2ª: em cada quadro fica o
    candidato mais perto desse caminho; longe demais (> tol × tamanho) = sem rosto."""
    big = np.array([max(c, key=lambda f: f[2]) if c else [np.nan] * 4 for c in cands], float)
    if not np.isfinite(big).any():
        return [None] * len(cands)
    cx, cy, sz = big[:, 0] + big[:, 2] / 2, big[:, 1] + big[:, 3] / 2, big[:, 2]
    out = []
    for i, c in enumerate(cands):
        a, b = max(0, i - win), i + win + 1
        if not c or not np.isfinite(sz[a:b]).any():
            out.append(None)
            continue
        mx, my, ms = np.nanmedian(cx[a:b]), np.nanmedian(cy[a:b]), np.nanmedian(sz[a:b])
        best = min(c, key=lambda f: math.hypot(f[0] + f[2] / 2 - mx, f[1] + f[3] / 2 - my))
        d = math.hypot(best[0] + best[2] / 2 - mx, best[1] + best[3] / 2 - my)
        ok = d <= tol * ms and 0.55 * ms <= best[2] <= 1.8 * ms
        out.append(best if ok else None)
    return out


def main():
    edl_path = sys.argv[1] if len(sys.argv) > 1 else "edl.json"
    edl = B.load_edl(edl_path)
    d = edl["_dir"]
    base = os.path.join(d, "base.mkv")
    nfr = B.total_frames(edl)
    body = int(round(B.body_duration(edl) * B.FPS))
    wins = behind_windows(edl)
    noface = no_person_frames(edl)
    need_mask = [any(a - 0.1 <= i / B.FPS <= b + 0.1 for a, b in wins) for i in range(nfr)]

    cc = cv2.CascadeClassifier(model("haarcascade_frontalface_default.xml", HAAR_URL))
    seg = None
    if any(need_mask):
        import onnxruntime as ort
        so = ort.SessionOptions()
        so.intra_op_num_threads = os.cpu_count() or 4
        seg = ort.InferenceSession(model("u2net_human_seg.onnx", SEG_URL), so, providers=["CPUExecutionProvider"])
        enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "gray",
                                "-s", f"{B.W}x{B.H}", "-r", str(B.FPS), "-i", "-", "-c:v", "ffv1",
                                os.path.join(d, "person_mask.mkv")], stdin=subprocess.PIPE)
    cands, last_m = [], None
    zero = np.zeros((B.H, B.W), np.uint8)
    for i, fr in enumerate(frames(base, 540, 960)):
        if i >= nfr:
            break
        if i < body and i not in noface:
            g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
            fs = [f for f in cc.detectMultiScale(g, 1.1, 5, minSize=(28, 28)) if f[1] + f[3] / 2 < 960 * 0.7]
            cands.append([[int(v * 2) for v in f] for f in fs])
        else:
            cands.append([])                            # quadro congelado do card final / trecho sem pessoa
        if seg is not None:
            if need_mask[i]:
                if last_m is None or i % SEG_EVERY == 0:
                    rgb = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
                    x = cv2.resize(rgb, (320, 320), interpolation=cv2.INTER_AREA).astype(np.float32)
                    x /= max(1.0, x.max())
                    x = ((x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]).transpose(2, 0, 1)[None]
                    p = seg.run(None, {seg.get_inputs()[0].name: x.astype(np.float32)})[0][0, 0]
                    p = (p - p.min()) / (p.max() - p.min() + 1e-6)
                    p = cv2.resize(p, (B.W, B.H), interpolation=cv2.INTER_CUBIC)
                    p = np.clip((p - 0.35) / 0.3, 0, 1)            # borda mais firme
                    last_m = (cv2.GaussianBlur(p, (0, 0), 1.2) * 255).astype(np.uint8)
                enc.stdin.write(last_m.tobytes())
            else:
                enc.stdin.write(zero.tobytes())
    if seg is not None:
        for _ in range(len(cands), nfr):
            enc.stdin.write(zero.tobytes())
        enc.stdin.close()
        enc.wait()
    faces = track(cands)
    # suaviza: completa buracos com o vizinho e tira a mediana de 9 quadros
    arr = np.array([f if f else [np.nan] * 4 for f in faces], float)
    for k in range(4):
        col = arr[:, k]
        ok = ~np.isnan(col)
        if ok.any():
            col[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), col[ok])
    sm = arr.copy()
    for i in range(len(arr)):
        sm[i] = np.nanmedian(arr[max(0, i - 4):i + 5], axis=0)
    out = [None if (i >= body or i in noface or np.isnan(sm[i]).any()) else [int(v) for v in sm[i]]
           for i in range(len(sm))]
    found = sum(1 for f in faces if f)
    json.dump({"faces": out, "mask": bool(seg is not None), "windows": wins,
               "key": open(os.path.join(d, "base.key")).read() if os.path.exists(os.path.join(d, "base.key")) else ""},
              open(os.path.join(d, "person.json"), "w"))
    print(f"pessoa: rosto em {found}/{body - len(noface)} quadros, recorte em {sum(need_mask)} quadros "
          f"({len(wins)} cards atrás dela)" + (f", {len(noface)} quadros sem pessoa (b-roll do bruto)" if noface else ""))


if __name__ == "__main__":
    main()
