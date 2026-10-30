"""Transcrição com tempo por palavra (pt-BR) → transcript.json + transcript.txt

Uso:  python transcribe.py ../IMG_xxxx.MOV

Motor padrão: NVIDIA Parakeet TDT 0.6B v3 (multilíngue, inclui português) rodando
no sherpa-onnx (já instalado no ~/.venvs/edicao do Mac). O modelo (~490 MB) fica em
~/models/; se faltar, o script baixa do GitHub (github.com/k2-fsa/sherpa-onnx, release
"asr-models"). Leva poucos segundos por vídeo.

Se o sherpa-onnx falhar, tenta o faster-whisper (precisa de huggingface.co liberado).

Correções de vocabulário fixas da marca ficam em FIXES (o motor erra termos como
"Eletro" → "Electro", "plafon" → "plafão", "Inlumix" → "Ilumix"). Correções de um vídeo só vão no EDL
("captions": {"fix": {...}}; com espaço na chave junta palavras: "eletro company" → "Eletro Company").
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import wave

MODEL_NAME = "sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8"
MODEL_URL = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/{MODEL_NAME}.tar.bz2"
MODEL_DIR = os.path.expanduser(os.environ.get("ASR_MODELS", "~/models"))

# termos da área que o reconhecimento costuma errar (minúsculo, sem pontuação) → grafia certa
FIXES = {
    "electro": "Eletro", "eletro": "Eletro", "elétro": "Eletro", "company": "Company", "campany": "Company",
    "electrocompany": "Eletro Company", "eletrocompany": "Eletro Company", "electrocompre": "Eletro Company",
    "eletrocompre": "Eletro Company", "electrocomprene": "Eletro Company", "electrocompani": "Eletro Company",
    "xardentes": "Tiradentes", "eleetro": "Eletro", "eleetrocompany": "Eletro Company", "londrine": "Londrina",
    "dijuntor": "disjuntor", "dijuntores": "disjuntores", "steck": "Steck", "stack": "Steck",
    "devault": "DeWalt", "dewalt": "DeWalt", "tramontina": "Tramontina", "copel": "Copel",
    "bil": "Bio", "bio": "Bio",            # "link da Bio" (agência, 29/10)
    "compani": "Company", "companhia": "Company",
    "plafão": "plafon", "plafom": "plafon", "plafon": "plafon", "plafons": "plafons", "plafões": "plafons",
    "ilumix": "Inlumix", "inlumix": "Inlumix", "inlumics": "Inlumix", "illumix": "Inlumix",
    "taschibra": "Taschibra", "tachibra": "Taschibra", "tashibra": "Taschibra", "taxibra": "Taschibra",
    "led": "LED", "leds": "LEDs", "dps": "DPS", "dr": "DR",
    "londrina": "Londrina", "cambé": "Cambé", "ibiporã": "Ibiporã", "rolândia": "Rolândia",
    "tiradentes": "Tiradentes", "shangri-lá": "Shangri-Lá",
    "whatsapp": "WhatsApp", "zap": "Zap", "instagram": "Instagram", "pix": "Pix",
}
CHUNK_MAX = 40.0           # s — corta o áudio em silêncios para trechos de até isso


def ffmpeg_wav(src, wav):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000",
                    "-c:a", "pcm_s16le", wav], check=True)


def ensure_model():
    d = os.path.join(MODEL_DIR, MODEL_NAME)
    if os.path.exists(os.path.join(d, "encoder.int8.onnx")):
        return d
    os.makedirs(MODEL_DIR, exist_ok=True)
    tb = os.path.join(MODEL_DIR, MODEL_NAME + ".tar.bz2")
    print(f"baixando o modelo de transcrição (~490 MB) de {MODEL_URL} …")
    urllib.request.urlretrieve(MODEL_URL, tb)
    with tarfile.open(tb) as t:
        t.extractall(MODEL_DIR)
    os.remove(tb)
    return d


def silences(wav):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", wav, "-af",
                        "silencedetect=noise=-35dB:d=0.25", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r)]
    return [(a + b) / 2 for a, b in zip(st, en)]


def chunks(total, mids):
    cuts, last = [], 0.0
    for m in mids:
        if m - last >= CHUNK_MAX * 0.6 and m < total - 1:
            cuts.append(m)
            last = m
    edges = [0.0] + cuts + [total]
    out = []
    for a, b in zip(edges, edges[1:]):
        while b - a > CHUNK_MAX * 1.5:          # garante o máximo mesmo sem silêncio
            out.append((a, a + CHUNK_MAX))
            a += CHUNK_MAX
        out.append((a, b))
    return out


def fix_word(w):
    core = re.sub(r"[^\wáàâãéêíóôõúüç-]", "", w.lower())
    if core in FIXES:
        lead = re.match(r"^\W*", w).group(0)
        trail = re.search(r"\W*$", w).group(0)
        return lead + FIXES[core] + trail
    return w


def run_sherpa(wav):
    import numpy as np
    import sherpa_onnx
    d = ensure_model()
    rec = sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=os.path.join(d, "encoder.int8.onnx"), decoder=os.path.join(d, "decoder.int8.onnx"),
        joiner=os.path.join(d, "joiner.int8.onnx"), tokens=os.path.join(d, "tokens.txt"),
        model_type="nemo_transducer", num_threads=max(1, os.cpu_count() or 2))
    with wave.open(wav) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    total = len(x) / 16000
    words, lines = [], []
    for a, b in chunks(total, silences(wav)):
        s = rec.create_stream()
        s.accept_waveform(16000, x[int(a * 16000):int(b * 16000)])
        rec.decode_stream(s)
        r = s.result
        durs = list(getattr(r, "durations", []) or [0.08] * len(r.tokens))
        cur = None
        for tok, ts, du in zip(r.tokens, r.timestamps, durs):
            t0, t1 = a + ts, a + ts + max(du, 0.04)
            punct = re.fullmatch(r"\s*[.,;:?!…]+\s*", tok)
            if cur is None or (tok.startswith(" ") and not punct):
                if cur:
                    words.append(cur)
                cur = {"word": tok.strip(), "start": t0, "end": t1}
            else:
                cur["word"] += tok.strip()
                if not punct:
                    cur["end"] = t1
        if cur:
            words.append(cur)
        lines.append(f"[{a:7.2f} – {b:7.2f}] {r.text.strip()}")
    for w in words:
        w["word"] = fix_word(w["word"])
        w["start"], w["end"], w["p"] = round(w["start"], 3), round(w["end"], 3), 1.0
    return words, lines


def run_whisper(wav, model_name):
    from faster_whisper import WhisperModel
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segs, _ = model.transcribe(wav, language="pt", word_timestamps=True, vad_filter=False, beam_size=5,
                               initial_prompt="Eletro Company, materiais elétricos e iluminação, plafon de embutir, "
                                              "painel LED, lâmpada, Inlumix, Taschibra, disjuntor, cabo flexível, "
                                              "mangueira corrugada, tomada, Londrina e região.")
    words, lines = [], []
    for s in segs:
        lines.append(f"[{s.start:7.2f} – {s.end:7.2f}] {s.text.strip()}")
        for w in s.words or []:
            words.append({"word": fix_word(w.word.strip()), "start": round(w.start, 3),
                          "end": round(w.end, 3), "p": round(w.probability, 3)})
    return words, lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--engine", default="auto", choices=["auto", "parakeet", "whisper"])
    ap.add_argument("--model", default=os.environ.get("WHISPER_MODEL", "small"))
    ap.add_argument("--out", default="transcript.json")
    a = ap.parse_args()
    eng = None
    with tempfile.TemporaryDirectory() as td:
        wav = os.path.join(td, "a.wav")
        ffmpeg_wav(a.source, wav)
        words = lines = None
        if a.engine in ("auto", "parakeet"):
            try:
                words, lines = run_sherpa(wav)
                eng = "parakeet"
            except Exception as e:  # noqa: BLE001
                print(f"parakeet/sherpa-onnx falhou: {e}")
                if a.engine == "parakeet":
                    sys.exit(1)
        if words is None:
            try:
                words, lines = run_whisper(wav, a.model)
                eng = "whisper"
            except Exception as e:  # noqa: BLE001
                sys.exit(f"Sem transcrição: {e}\nInstale sherpa-onnx (pip) — o modelo vem do GitHub.")
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({"language": "pt", "engine": eng, "words": words}, f, ensure_ascii=False, indent=1)
    with open(os.path.splitext(a.out)[0] + ".txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{len(words)} palavras ({eng}) → {a.out}")


if __name__ == "__main__":
    main()
