"""Trilha e efeitos sintetizados (sem problema de licença)."""
import numpy as np

SR = 48000


def _note(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def _env(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def _pluck(f, dur, bright=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) + 0.35 * bright * np.sin(4 * np.pi * f * t) + 0.12 * bright * np.sin(6 * np.pi * f * t)
    return y * np.exp(-t * 5.5) * _env(n, 0.004, 0.05)


def _pad(freqs, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for f in freqs:
        for det in (-0.6, 0.6):
            ff = f * (1 + det / 1200 * 8)
            y += np.sin(2 * np.pi * ff * t) + 0.25 * np.sin(4 * np.pi * ff * t + 0.3)
    y *= (1 + 0.15 * np.sin(2 * np.pi * 0.25 * t))
    return y / (len(freqs) * 2) * _env(n, min(0.8, dur / 3), min(0.8, dur / 3))


def music(dur, style="calm", seed=1, bpm=None):
    if style == "lofi":
        return _lofi(dur, seed, bpm or LOFI_BPM)
    rng = np.random.default_rng(seed)
    bpm = 82 if style == "calm" else 112
    beat = 60 / bpm
    bar = beat * 4
    # Ré maior: D – A – Bm – G
    prog = [[62, 66, 69], [57, 61, 64], [59, 62, 66], [55, 59, 62]]
    n = int((dur + 1) * SR)
    out = np.zeros((n, 2))
    t0, k = 0.0, 0
    while t0 < dur + 0.5:
        ch = prog[k % 4]
        L = bar * (2 if style == "calm" else 1)
        p = _pad([_note(m) for m in ch], L + 0.6) * (0.55 if style == "calm" else 0.35)
        i0 = int(t0 * SR)
        seg = p[: max(0, min(len(p), n - i0))]
        out[i0:i0 + len(seg)] += seg[:, None]
        # baixo
        b = _pluck(_note(ch[0] - 24), L * 0.9, bright=0.3) * 0.5
        seg = b[: max(0, min(len(b), n - i0))]
        out[i0:i0 + len(seg)] += seg[:, None]
        # arpejo
        step = beat / 2
        arp = ch + [ch[0] + 12, ch[1] + 12]
        j = 0
        tt = t0
        while tt < t0 + L - 1e-6:
            m = arp[j % len(arp)] + 12
            if style == "calm" and j % 2 == 1 and rng.random() < 0.5:
                j += 1
                tt += step
                continue
            pl = _pluck(_note(m), 0.6) * (0.22 if style == "calm" else 0.28)
            pan = 0.5 + 0.35 * np.sin(j * 1.3)
            i = int(tt * SR)
            seg = pl[: max(0, min(len(pl), n - i))]
            out[i:i + len(seg), 0] += seg * (1 - pan)
            out[i:i + len(seg), 1] += seg * pan
            j += 1
            tt += step
        if style == "upbeat":
            for q in range(int(L / beat)):
                i = int((t0 + q * beat) * SR)
                kk = _kick()
                seg = kk[: max(0, min(len(kk), n - i))]
                out[i:i + len(seg)] += seg[:, None] * 0.45
                i2 = int((t0 + q * beat + beat / 2) * SR)
                sh = _shaker(rng)
                seg = sh[: max(0, min(len(sh), n - i2))]
                out[i2:i2 + len(seg)] += seg[:, None] * 0.12
        t0 += L
        k += 1
    out = out[: int(dur * SR)]
    fade = int(min(1.5, dur / 4) * SR)
    out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return out


# ------------------------------------------------------------------ lo-fi (trilha padrão desde 28/10)
# Pedido da agência: "não quero que nem esse do modelo que está infantil demais, quero um Lo-fi", na vibe da
# referência REFERENCIAS/referencia_trilha_lofi_IMG_8755.MOV, que é um lo-fi house: 121 BPM, bumbo em todo
# tempo, chimbal em semicolcheias, acordes quentes e abafados Am9 → Dm9 (2 compassos cada), muito grave e
# quase nada acima de 1 kHz. Tudo sintetizado (piano elétrico, pad, sub, bateria, fita e vinil): sem licença.
LOFI_BPM = 121
LOFI_PROG = [(33, [55, 59, 60, 64]), (38, [53, 57, 60, 64])]     # (baixo, vozes): Am9 e Dm9 sem a fundamental
LOFI_STABS = [0, 2.5, 5.5, 7]                                    # piano, em tempos dentro dos 2 compassos
MUSIC_DB = {"lofi": -20, "upbeat": -22, "calm": -22}             # nível sob a voz (RMS). O lo-fi tem mais grave:
# com -20, a parte acima de 250 Hz (a que o celular toca) fica ~26 dB abaixo da voz, como na trilha antiga aprovada


def _butter(x, fc, kind="low", order=2):
    from scipy import signal
    b, a = signal.butter(order, np.asarray(fc) / (SR / 2), kind)
    return signal.lfilter(b, a, x, axis=0)


def _ep(f, dur, vel=1.0):
    """Piano elétrico (FM, timbre de Rhodes): brilho do martelo no ataque e corpo que decai devagar."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    idx = 1.4 * np.exp(-t * 7) + 0.2
    y = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * t))
    y += 0.08 * np.sin(2 * np.pi * f * 7.1 * t) * np.exp(-t * 35)
    return y * np.exp(-t * 0.9) * _env(n, 0.004, 0.12) * vel


def _lofi_kick():
    """Bumbo macio; a saturação dá os harmônicos que o alto-falante do celular toca."""
    n = int(0.32 * SR)
    t = np.arange(n) / SR
    f = 95 * np.exp(-t * 30) + 50
    y = np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)) / np.tanh(2.2)
    click = np.random.default_rng(3).standard_normal(n) * np.exp(-t * 400) * 0.35
    return (y + _butter(click, 6000)) * _env(n, 0.001, 0.03)


def _hat(rng, decay):
    n = int(max(0.08, decay * 5) * SR)
    t = np.arange(n) / SR
    return _butter(rng.standard_normal(n), 7000, "high") * np.exp(-t / decay)


def _clap(rng):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    e = np.exp(-t / 0.09)
    for d in (0.0, 0.011, 0.022):
        e = e + 0.6 * np.exp(-np.clip(t - d, 0, None) / 0.004) * (t >= d)
    return _butter(rng.standard_normal(n), [900, 3500], "band") * e * _env(n, 0.0005, 0.05)


def _lofi(dur, seed=1, bpm=LOFI_BPM):
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    six = beat / 4
    n = int((dur + 2) * SR)
    t = np.arange(n) / SR
    keys, drums = np.zeros((n, 2)), np.zeros((n, 2))
    pad, bass = np.zeros(n), np.zeros(n)

    def put(buf, y, at, pan=0.5):
        i = int(at * SR)
        if i >= n:
            return
        y = y[: n - i]
        if buf.ndim == 1:
            buf[i:i + len(y)] += y
        else:
            buf[i:i + len(y), 0] += y * np.cos(pan * np.pi / 2)
            buf[i:i + len(y), 1] += y * np.sin(pan * np.pi / 2)

    L, t0, k = 8 * beat, 0.0, 0
    while t0 < dur + 1:
        root, voice = LOFI_PROG[k % len(LOFI_PROG)]
        nn = int((L + 0.3) * SR)
        tt = np.arange(nn) / SR
        p = np.zeros(nn)
        for m in voice:                                          # pad contínuo, levemente desafinado
            for det in (-4, 4):
                ff = _note(m) * 2 ** (det / 1200)
                ph0 = rng.uniform(0, 6.28)
                p += sum(np.sin(2 * np.pi * h * ff * tt + h * ph0) / h for h in range(1, 6))   # quase serrote
        put(pad, p * _env(nn, 0.05, 0.3) / (2 * len(voice)), t0)
        b = np.tanh(1.8 * np.sin(2 * np.pi * _note(root) * tt)) / np.tanh(1.8)
        put(bass, b * _env(nn, 0.02, 0.25), t0)
        for s in LOFI_STABS:                                     # acordes do piano, "dedilhados" de leve
            vel = rng.uniform(0.75, 1.0)
            for j, m in enumerate(voice):
                put(keys, _ep(_note(m), 2.2, vel) / len(voice), t0 + s * beat + j * 0.012 + rng.uniform(0, 0.008),
                    pan=0.35 + 0.1 * j)
        t0 += L
        k += 1
    kick = _lofi_kick()
    for q in range(int((dur + 1) / beat) + 1):
        put(drums, kick * 0.65, q * beat)
        if q % 2 == 1:                                           # palma no 2 e no 4
            put(drums, _clap(rng) * 0.35, q * beat + rng.uniform(0, 0.006), pan=0.5)
        for s in range(4):                                       # chimbal; o do contratempo fica aberto
            vel = (0.45, 0.22, 0.75, 0.25)[s] * rng.uniform(0.8, 1.0)
            put(drums, _hat(rng, 0.045 if s == 2 else 0.015) * vel * 0.55, q * beat + s * six + (0.1 * six if s % 2 else 0),
                pan=0.62)
    ph = np.mod(t, beat)                                         # "bombeamento" do bumbo nos acordes e no grave
    duck = 1 - 0.55 * np.exp(-ph / 0.12) * np.clip(ph / 0.008, 0, 1)
    d = (0.004 + 0.0012 * np.sin(2 * np.pi * 0.55 * t) + 0.00008 * np.sin(2 * np.pi * 4.7 * t + 1)) * SR
    src = np.arange(n) - d                                       # fita: oscilação lenta da afinação

    def wow(x):
        return np.interp(src, np.arange(n), x)
    keys = np.stack([wow(c) for c in _butter(keys, 3400).T], 1)
    pad = wow(_butter(pad, 1800))
    mel = (keys * 1.3 + (pad * 0.55 + bass * 0.32)[:, None]) * duck[:, None]   # acordes na frente: o celular não toca o sub
    hiss = _butter(rng.standard_normal(n), [800, 5000], "band") * 0.0015   # vinil: chiado + estalos
    pops = np.zeros(n)
    idx = rng.integers(0, n, int(dur * 7))
    pops[idx] = rng.uniform(-1, 1, len(idx)) * rng.uniform(0.02, 0.08, len(idx))
    vinyl = hiss + _butter(pops, 1200, "high")
    out = mel + _butter(drums, 11000) * 0.8 + vinyl[:, None]
    out = np.tanh(1.2 * _butter(out, 12000)) / 1.2
    out = out / (np.abs(out).max() + 1e-9) * 0.9
    out = out[: int(dur * SR)]
    out[: int(0.25 * SR)] *= np.linspace(0, 1, int(0.25 * SR))[:, None]
    fade = int(min(1.5, dur / 4) * SR)
    out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return out


def _kick():
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    f = 120 * np.exp(-t * 18) + 45
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14)


def _shaker(rng):
    n = int(0.06 * SR)
    x = rng.standard_normal(n)
    x = np.diff(x, prepend=0)
    return x * np.exp(-np.arange(n) / SR * 60) * 0.5


def _lp(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


def sfx(kind, seed=0):
    rng = np.random.default_rng(seed)
    if kind == "softpop":
        n = int(0.09 * SR)
        t = np.arange(n) / SR
        f = 300 + 700 * np.exp(-t * 45)
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 38)
    elif kind == "tap":
        n = int(0.05 * SR)
        t = np.arange(n) / SR
        y = 0.6 * np.sin(2 * np.pi * 1700 * t) * np.exp(-t * 120) + 0.4 * rng.standard_normal(n) * np.exp(-t * 200)
    elif kind == "air":
        n = int(0.5 * SR)
        t = np.arange(n) / SR
        x = _lp(rng.standard_normal(n), 9) - _lp(rng.standard_normal(n), 60) * 0.5
        y = x * np.sin(np.pi * np.clip(t / 0.5, 0, 1)) ** 2 * 0.8
    elif kind == "paper":
        n = int(0.14 * SR)
        x = np.diff(rng.standard_normal(n), prepend=0)
        y = x * (rng.random(n) < 0.35) * np.exp(-np.arange(n) / SR * 25) * 0.6
    elif kind == "chime":
        n = int(1.4 * SR)
        t = np.arange(n) / SR
        f = 1318.5
        y = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * d) for a, r, d in
                [(1, 1, 3.2), (0.45, 2.76, 5), (0.25, 5.4, 8), (0.3, 0.5, 2.5)])
        y *= _env(n, 0.003, 0.2) * 0.5
    elif kind == "cash":                       # dinheiro: "ka" (trava da caixa) + "ching" (sino) + moedas
        n = int(1.1 * SR)
        t = np.arange(n) / SR
        y = np.zeros(n)
        k = int(0.035 * SR)
        y[:k] += (np.diff(rng.standard_normal(k), prepend=0) * 0.5 + np.sin(2 * np.pi * 160 * t[:k])) \
            * np.exp(-t[:k] * 90) * 0.6
        i0 = int(0.05 * SR)
        tb = t[: n - i0]
        bell = sum(a * (np.sin(2 * np.pi * 2637 * r * tb) + np.sin(2 * np.pi * 2650 * r * tb + 1.0)) * np.exp(-tb * d)
                   for a, r, d in [(1, 1, 4.5), (0.5, 2.32, 7), (0.3, 4.25, 11), (0.15, 6.63, 16)])
        y[i0:] += bell * 0.5 * _env(len(tb), 0.002, 0.1)
        for _ in range(7):                     # moedas tilintando logo depois
            tc = rng.uniform(0.09, 0.42)
            ic, m = int(tc * SR), int(0.05 * SR)
            tt = np.arange(m) / SR
            f = rng.uniform(4200, 7800)
            c = (np.sin(2 * np.pi * f * tt) + 0.6 * np.sin(2 * np.pi * f * 1.47 * tt)) \
                * np.exp(-tt * rng.uniform(70, 120)) * rng.uniform(0.15, 0.35) * (1 - tc)
            y[ic:ic + m] += c[: max(0, min(m, n - ic))]
    elif kind == "click":                      # clique de mouse (aperta + solta)
        n = int(0.11 * SR)
        y = np.zeros(n)
        for t0, a in ((0.0, 1.0), (0.075, 0.55)):
            i, m = int(t0 * SR), int(0.012 * SR)
            tt = np.arange(m) / SR
            c = (np.diff(rng.standard_normal(m), prepend=0) * 0.7 + np.sin(2 * np.pi * 3100 * tt)) * np.exp(-tt * 420) * a
            y[i:i + m] += c[: n - i]
    elif kind == "correct":
        y = np.concatenate([_pluck(_note(88), 0.12), _pluck(_note(93), 0.5)])
    elif kind == "wrong":
        n = int(0.4 * SR)
        t = np.arange(n) / SR
        y = 0.5 * np.sign(np.sin(2 * np.pi * (180 - 60 * t) * t)) * np.exp(-t * 6)
        y = _lp(y, 20)
    elif kind == "whoosh":                     # passagem de ar: ruído filtrado que abre e fecha (0,5 s)
        n = int(0.5 * SR)
        t = np.arange(n) / SR
        x = rng.standard_normal(n)
        al = 0.012 + 0.11 * np.sin(np.pi * t / 0.5) ** 2    # corte do filtro ~100 Hz → ~1 kHz → ~100 Hz
        y = np.zeros(n)
        acc = acc2 = 0.0
        for i in range(n):                         # passa-baixa de 2 polos com corte variável
            acc += al[i] * (x[i] - acc)
            acc2 += al[i] * (acc - acc2)
            y[i] = acc2
        y = y - _lp(y, 160)                        # tira o grave abaixo de ~150 Hz
        y *= np.sin(np.pi * np.clip(t / 0.5, 0, 1)) ** 1.5
    elif kind == "pop":                        # "pop" de elemento entrando (mais corpo que o softpop)
        n = int(0.14 * SR)
        t = np.arange(n) / SR
        f = 180 + 900 * np.exp(-t * 38)
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30)
        y[: int(0.004 * SR)] += rng.standard_normal(int(0.004 * SR)) * 0.4
    elif kind == "zap":                        # faísca elétrica curta: estalo + zumbido 120 Hz com harmônicos (~0,3 s)
        n = int(0.32 * SR)
        t = np.arange(n) / SR
        ph = 2 * np.pi * 120 * t
        buzz = sum(np.sign(np.sin(h * ph)) / h for h in (2, 3, 5, 8, 13))           # zumbido de 240 Hz a ~3 kHz (sem o grave)
        buzz = _lp(buzz, 6) * np.interp(t, [0, 0.01, 0.08, 0.32], [0, 1, 0.5, 0])
        crack = np.zeros(n)
        for _ in range(9):                         # estalos irregulares
            i = int(rng.uniform(0, 0.22) * SR)
            m = int(0.006 * SR)
            crack[i:i + m] += rng.standard_normal(m) * rng.uniform(0.6, 1.2)
        crack = _lp(crack, 5) - _lp(crack, 40)     # estalo na faixa ~1–8 kHz (sem chiado agudo)
        y = 1.0 * buzz + crack * 0.9
    elif kind == "switch":                     # interruptor de luz: "tlec" curto e seco
        n = int(0.09 * SR)
        y = np.zeros(n)
        for t0, a, f in ((0.0, 1.0, 2400), (0.018, 0.6, 1300)):
            i, m = int(t0 * SR), int(0.02 * SR)
            tt = np.arange(m) / SR
            nz = rng.standard_normal(m)
            c = ((_lp(nz, 4) - _lp(nz, 20)) * 0.8 + np.sin(2 * np.pi * f * tt)
                 + 0.6 * np.sin(2 * np.pi * 380 * tt)) * np.exp(-tt * 260) * a
            y[i:i + m] += c[: n - i]
    elif kind == "swipe":                      # marcador riscando a palavra (rápido, ~0,2 s)
        n = int(0.2 * SR)
        t = np.arange(n) / SR
        x = rng.standard_normal(n)
        x = _lp(x, 4) - _lp(x, 18)                 # faixa ~2–9 kHz
        y = x * np.interp(t, [0, 0.02, 0.14, 0.2], [0, 1, 0.7, 0])
    elif kind == "scribble":                   # caneta riscando o círculo (~0,35 s)
        n = int(0.38 * SR)
        t = np.arange(n) / SR
        x = rng.standard_normal(n)
        x = _lp(x, 5) - _lp(x, 22)                 # faixa ~2–8 kHz
        strokes = 0.55 + 0.45 * np.sin(2 * np.pi * 7.5 * t) ** 2
        y = x * strokes * np.interp(t, [0, 0.03, 0.3, 0.38], [0, 1, 0.8, 0])
    elif kind == "pling":                      # notificação curtinha (comentário)
        y = np.concatenate([_pluck(_note(88), 0.09, 1.4), _pluck(_note(95), 0.45, 1.4)])
    elif kind == "impact":                     # impacto grave e curto (gancho), com ataque audível no celular
        n = int(0.7 * SR)
        t = np.arange(n) / SR
        f = 60 + 110 * np.exp(-t * 16)
        y = 0.55 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)       # peso (fone)
        y += 1.0 * np.sin(2 * np.pi * np.cumsum(f * 3.1) / SR) * np.exp(-t * 8)   # corpo (celular)
        y += 0.7 * np.sin(2 * np.pi * np.cumsum(f * 5.2) / SR) * np.exp(-t * 12)
        y += (_lp(rng.standard_normal(n), 4) - _lp(rng.standard_normal(n), 20)) * np.exp(-t * 40) * 2.2
    else:
        raise ValueError(kind)
    y = np.asarray(y, dtype=float)
    return y / (np.max(np.abs(y)) + 1e-9)
