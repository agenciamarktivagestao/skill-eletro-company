"""Desfoca placas de carro no vídeo bruto (segurança dos carros dos clientes).

Uso:  python blur_plates.py ../IMG_xxxx.MOV placas.json  → ../IMG_xxxx_placas.mp4 (+ placas_check.jpg)
Depois aponte o "source" do edl.json para o arquivo _placas.mp4.

placas.json (coordenadas no quadro ORIGINAL, ex.: 2160×3840; tempos do bruto, em segundos):
  [{"t0": 0.0, "t1": 6.9, "box": [180, 1850, 420, 190], "track": true}]
  box    x, y, largura, altura da placa no 1º quadro do trecho (com folga de ~20 px)
  track  segue a placa quadro a quadro (casamento de imagem na região em volta da placa),
         para acompanhar a câmera na mão. false = retângulo parado.
  ref    (opcional) região usada para seguir [x, y, w, h]; padrão = a placa com 120 px de borda.

Cor: o vídeo é processado direto em YUV 4:2:0 — fora dos retângulos os pixels saem idênticos
ao bruto (só o encode final, x264 crf 8, tags bt709). Nada de filtro, LUT ou conversão RGB.
"""
import json
import os
import subprocess
import sys

import cv2
import numpy as np


def probe(src):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate,color_transfer:stream_side_data=rotation",
                          "-of", "json", src], capture_output=True, text=True).stdout
    s = json.loads(out)["streams"][0]
    rot = 0
    for sd in s.get("side_data_list", []):
        rot = int(sd.get("rotation", 0))
    a, b = s["r_frame_rate"].split("/")
    return int(s["width"]), int(s["height"]), float(a) / float(b), rot, s.get("color_transfer")


def blur_plane(p, x, y, w, h, k):
    H, W = p.shape
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    roi = p[y0:y1, x0:x1]
    # pixeliza + desfoca: a placa fica ilegível, sem "quadradinhos" duros
    sm = cv2.resize(roi, (max(1, roi.shape[1] // k), max(1, roi.shape[0] // k)), interpolation=cv2.INTER_AREA)
    big = cv2.resize(sm, (roi.shape[1], roi.shape[0]), interpolation=cv2.INTER_LINEAR)
    big = cv2.GaussianBlur(big, (0, 0), k * 0.8)
    # borda suave (máscara com degradê de ~12% da altura)
    m = np.zeros(roi.shape, np.float32)
    pad = max(2, int(min(roi.shape) * 0.12))
    m[pad:-pad or None, pad:-pad or None] = 1
    m = cv2.GaussianBlur(m, (0, 0), pad / 2 + 0.1)
    p[y0:y1, x0:x1] = (big * m + roi * (1 - m)).astype(np.uint8)


def main():
    src, cfg = sys.argv[1], sys.argv[2]
    regions = json.load(open(cfg))
    W, H, fps, rot, trc = probe(src)
    if rot % 360:
        sys.exit(f"vídeo com rotação {rot}°: ajuste o script (coordenadas giradas)")
    base, _ = os.path.splitext(src)
    out = base + "_placas.mp4"
    fsz = W * H * 3 // 2
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "yuv420p",
                            "-s", f"{W}x{H}", "-r", f"{fps}", "-i", "-", "-i", src, "-map", "0:v", "-map", "1:a?",
                            "-c:v", "libx264", "-crf", "8", "-preset", "fast", "-pix_fmt", "yuv420p",
                            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", trc or "bt709",
                            "-color_range", "tv", "-c:a", "copy", out], stdin=subprocess.PIPE)
    state = [{} for _ in regions]
    checks = []
    n = 0
    while True:
        raw = dec.stdout.read(fsz)
        if len(raw) < fsz:
            break
        f = np.frombuffer(raw, np.uint8).copy()
        Y = f[:W * H].reshape(H, W)
        U = f[W * H:W * H + W * H // 4].reshape(H // 2, W // 2)
        V = f[W * H + W * H // 4:].reshape(H // 2, W // 2)
        t = n / fps
        for r, st in zip(regions, state):
            if not (r["t0"] - 1e-6 <= t < r["t1"]):
                continue
            x, y, w, h = r["box"]
            dx = dy = 0
            if r.get("track"):
                rx, ry, rw, rh = r.get("ref", [x - 120, y - 120, w + 240, h + 240])
                rx, ry = max(0, rx), max(0, ry)
                if "tpl" not in st:
                    st["tpl"] = Y[ry:ry + rh, rx:rx + rw].copy()
                    st["off"] = (0, 0)
                    st["hist"] = []
                    st["ref"] = (rx, ry)
                ox, oy = st["off"]
                s = 160
                sx0, sy0 = max(0, rx + ox - s), max(0, ry + oy - s)
                win = Y[sy0:sy0 + rh + 2 * s, sx0:sx0 + rw + 2 * s]
                res = cv2.matchTemplate(win, st["tpl"], cv2.TM_CCOEFF_NORMED)
                _, score, _, loc = cv2.minMaxLoc(res)
                if score > 0.45:
                    st["off"] = (sx0 + loc[0] - rx, sy0 + loc[1] - ry)
                st["hist"].append(st["off"])
                hh = st["hist"][-5:]
                dx = int(np.median([a for a, _ in hh]))
                dy = int(np.median([b for _, b in hh]))
                st.setdefault("scores", []).append(score)
            k = max(8, int(h / 5))
            blur_plane(Y, x + dx, y + dy, w, h, k)
            blur_plane(U, (x + dx) // 2, (y + dy) // 2, w // 2 + 1, h // 2 + 1, max(4, k // 2))
            blur_plane(V, (x + dx) // 2, (y + dy) // 2, w // 2 + 1, h // 2 + 1, max(4, k // 2))
            if n % int(fps) == 0:
                checks.append((t, x + dx, y + dy, w, h))
        enc.stdin.write(f.tobytes())
        if n % int(fps) == 0 and any(c[0] == t for c in checks):
            bgr = cv2.cvtColor(np.frombuffer(f.tobytes(), np.uint8).reshape(H * 3 // 2, W), cv2.COLOR_YUV2BGR_I420)
            c = checks[-1]
            pad = 260
            crop = bgr[max(0, c[2] - pad):c[2] + c[4] + pad, max(0, c[1] - pad):c[1] + c[3] + pad]
            cv2.putText(crop, f"{t:.1f}s", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)
            checks[-1] = checks[-1] + (cv2.resize(crop, (360, int(360 * crop.shape[0] / crop.shape[1]))),)
        n += 1
    enc.stdin.close()
    enc.wait()
    dec.wait()
    imgs = [c[5] for c in checks if len(c) > 5]
    if imgs:
        hmax = max(i.shape[0] for i in imgs)
        imgs = [cv2.copyMakeBorder(i, 0, hmax - i.shape[0], 0, 0, cv2.BORDER_CONSTANT) for i in imgs]
        rows = [np.hstack(imgs[i:i + 6] + [np.zeros_like(imgs[0])] * (6 - len(imgs[i:i + 6])))
                for i in range(0, len(imgs), 6)]
        cv2.imwrite(os.path.join(os.path.dirname(os.path.abspath(cfg)), "placas_check.jpg"), np.vstack(rows))
    for r, st in zip(regions, state):
        if st.get("scores"):
            print(f"trecho {r['t0']}–{r['t1']}s: seguiu a placa, confiança mín. {min(st['scores']):.2f}, "
                  f"deslocamento final {st['off']}")
    print(f"{n} quadros → {out}")


if __name__ == "__main__":
    main()
