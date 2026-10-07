"""Original instrumental for the recruitment video (jobs.html).

Modern pop-trap at 84.66 BPM (feels like 170 with 16th hats), D major, built on the same
beat grid as the video so every hit lands on a visual event:
  b0-b4   intro: filtered chords + pluck arp, riser, hits on "מחפשים" (b2) and "עובדי מכירות" (b3)
  b4      DROP on "תותחים": 808, kick, clap, hats, lead
  b17     impact on the logo, stripped break, snare roll back in
  b20     beat returns for the call to action, b21 impact on the e-mail
  b24     final chord, rings out to the end (b26)
Usage: python3 music.py OUT.wav
"""
import sys
import wave
import numpy as np
from scipy.signal import butter, lfilter, fftconvolve

SR = 44100
P = 0.7086937           # seconds per beat (same grid as jobs.html)
BEATS = 26
L = BEATS * P
N = int(L * SR)
b = lambda i: i * P
STEP = P / 4            # 16th note
rng = np.random.default_rng(7)

def note(name):
    names = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4, "F#": -3, "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}
    n, o = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((names[n] + 12 * (o - 4)) / 12)

def t_(d):
    return np.arange(int(d * SR)) / SR

def place(buf, t0, s, gain=1.0):
    i0 = int(round(t0 * SR))
    if i0 >= len(buf):
        return
    if i0 < 0:
        s = s[-i0:]; i0 = 0
    s = s[: len(buf) - i0]
    if s.ndim == 1:
        buf[i0:i0 + len(s)] += gain * s[:, None]
    else:
        buf[i0:i0 + len(s)] += gain * s

def lp(x, fc, order=2):
    bb, aa = butter(order, min(fc, SR / 2 - 100) / (SR / 2), "low")
    return lfilter(bb, aa, x, axis=0)

def hp(x, fc, order=2):
    bb, aa = butter(order, fc / (SR / 2), "high")
    return lfilter(bb, aa, x, axis=0)

def sweep_lp(x, cut):  # time-varying low-pass, cutoff per 512-sample block
    out = np.zeros_like(x); zi = None; blk = 512
    for i in range(0, len(x), blk):
        c = float(cut[min(i, len(cut) - 1)])
        bb, aa = butter(2, min(c, SR / 2 - 200) / (SR / 2), "low")
        if zi is None:
            zi = np.zeros((2, x.shape[1])) if x.ndim == 2 else np.zeros(2)
        y, zi = lfilter(bb, aa, x[i:i + blk], axis=0, zi=zi)
        out[i:i + blk] = y
    return out

# ---------------- instruments ----------------
def kick(d=.45):
    t = t_(d)
    f = 62 + 120 * np.exp(-t / .03)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t / .11) + .45 * np.exp(-t / .004) * rng.standard_normal(len(t))
    return np.tanh(1.4 * s) * .7

def bass808(freq, d):
    t = t_(d)
    s = np.sin(2 * np.pi * 2 * freq * t) * np.minimum(1, t / .005) * np.exp(-t / max(d * .4, .12))
    return np.tanh(1.4 * s) * .35

def clap():
    t = t_(.35); n = rng.standard_normal(len(t))
    env = sum(np.exp(-np.maximum(0, t - k) / .008) * (t >= k) for k in (0, .011, .022)) / 3 + .5 * np.exp(-np.maximum(0, t - .03) / .09) * (t >= .03)
    s = hp(lp(n * env, 5000), 900)
    return s * .55

def hat(open_=False, vel=1.0):
    d = .18 if open_ else .045
    t = t_(d); n = rng.standard_normal(len(t))
    s = hp(n, 7000) * np.exp(-t / (.06 if open_ else .012))
    return s * .14 * vel

def supersaw(freq, d, voices=5, det=.012):
    t = t_(d); s = np.zeros((len(t), 2))
    for v in range(voices):
        f = freq * (1 + det * (v - (voices - 1) / 2) / ((voices - 1) / 2))
        ph = rng.random()
        saw = 2 * ((f * t + ph) % 1) - 1
        pan = .5 + .45 * (v - (voices - 1) / 2) / ((voices - 1) / 2)
        s[:, 0] += saw * (1 - pan); s[:, 1] += saw * pan
    return s / voices

def chord(freqs, d):
    s = sum(supersaw(f, d) for f in freqs) / len(freqs)
    env = np.minimum(1, t_(d) / .02)[:, None] * np.minimum(1, (d - t_(d)) / .05)[:, None]
    return s * env * .5

def pluck(freq, d=.32):
    t = t_(d)
    sq = np.sign(np.sin(2 * np.pi * freq * t)) * .5 + (2 * ((freq * t) % 1) - 1) * .5
    s = lp(sq * np.exp(-t / .09), 3800)
    return s * .32

def riser(d):
    t = t_(d); u = t / d
    n = rng.standard_normal(len(t))
    out = np.zeros_like(n); blk = 512
    for i in range(0, len(n), blk):
        fc = 400 + 7000 * u[i] ** 2
        bb, aa = butter(2, [fc * .8 / (SR / 2), min(fc * 1.25, SR / 2 - 100) / (SR / 2)], "band")
        out[i:i + blk] = lfilter(bb, aa, n[i:i + blk])
    tone = np.sin(2 * np.pi * np.cumsum(200 + 900 * u ** 2) / SR) * .25
    return (out * 1.6 + tone) * u ** 1.6 * .5

def impact(d=1.8):
    t = t_(d)
    boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-t / .05)) / SR) * np.exp(-t / .5)
    crash = hp(rng.standard_normal(len(t)), 3500) * np.exp(-t / .6) * .35
    return np.tanh(1.2 * boom) * .35 + crash

def snare_roll(t0, t1, buf):
    k = t0
    while k < t1 - 1e-6:
        u = (k - t0) / (t1 - t0)
        place(buf, k, clap()[: int(.12 * SR)], .25 + .6 * u)
        k += STEP if u < .5 else STEP / 2

# ---------------- arrangement ----------------
drums = np.zeros((N + SR * 2, 2)); bass = np.zeros_like(drums); music = np.zeros_like(drums); fx = np.zeros_like(drums)

PROG = {0: ("D", ["D3", "F#3", "A3", "D4"], "D2"), 1: ("D", ["D3", "F#3", "A3", "D4"], "D2"), 2: ("A", ["C#3", "E3", "A3", "C#4"], "A1"),
        3: ("Bm", ["D3", "F#3", "B3", "D4"], "B1"), 4: ("G", ["D3", "G3", "B3", "D4"], "G1"), 5: ("D", ["D3", "F#3", "A3", "D4"], "D2"),
        6: ("D", ["D3", "F#3", "A3", "D4"], "D2")}
ARP = {"D": ["A4", "D5", "F#5", "A5", "F#5", "D5", "E5", "F#5"], "A": ["A4", "C#5", "E5", "A5", "E5", "C#5", "D5", "E5"],
       "Bm": ["B4", "D5", "F#5", "B5", "F#5", "D5", "C#5", "D5"], "G": ["B4", "D5", "G5", "B5", "G5", "D5", "E5", "F#5"]}

# chords: every bar; intro is filtered shut and opens into the drop
pads = np.zeros_like(drums)
for bar in range(7):
    _, notes_, _ = PROG[bar]
    d = 4 * P if bar < 6 else 2 * P + 1.5
    place(pads, b(4 * bar), chord([note(n) for n in notes_], d))
cut = np.full(len(pads), 9000.0)
tt = np.arange(len(pads)) / SR
cut[tt < b(4)] = 1400 + 3000 * (tt[tt < b(4)] / b(4)) ** 2
brk = (tt >= b(17)) & (tt < b(20))
cut[brk] = 1800
pads = sweep_lp(pads, cut)
music += pads * .9

# pluck arpeggio: intro (soft, filtered) and drop (full); silent in the logo break until the roll
for bar in range(6):
    name = PROG[bar][0]
    for k, n in enumerate(ARP[name]):
        tk = b(4 * bar) + k * 2 * STEP
        if b(17) <= tk < b(20) or tk >= b(24):
            continue
        g = .8 if bar == 0 else 1.0
        place(music, tk, np.stack([pluck(note(n))] * 2, 1) * [[.8, 1.0] if k % 2 else [1.0, .8]], g)

# opening hit on frame 0 ("משרדינו גדל") and on the brush wipe (b1); light hats keep it moving
place(drums, 0, kick()); place(bass, 0, bass808(note("D2"), 1.2)); place(fx, 0, impact(1.2), .6)
place(drums, b(1), kick(), .8); place(drums, b(1), clap(), .7)
for k in np.arange(0, b(2), 2 * STEP):
    place(drums, k, hat(vel=.55))
# intro hits on the text slams + riser into the drop
for i in (2, 3):
    place(drums, b(i), kick(), 1.0); place(fx, b(i), impact(.6), .35)
snare_roll(b(3), b(4), drums)
place(fx, b(2), riser(2 * P), .9)

# drop groove
KICKS = [0, 7, 10]                 # 16th steps within a bar
def groove(t0, t1):
    k = t0
    while k < t1 - 1e-6:
        step = int(round((k - b(4 * int(k / (4 * P) + 1e-6))) / STEP)) % 16
        bar = int(k / (4 * P) + 1e-6)
        if step in KICKS or (bar % 2 == 1 and step == 14):
            place(drums, k, kick())
            root = note(PROG[bar][2]); nxt = min(t1, k + 6 * STEP)
            place(bass, k, bass808(root, max(.15, nxt - k)))
        if step in (4, 12):
            place(drums, k, clap())
        vel = 1.0 if step % 4 == 0 else .65 if step % 2 == 0 else .45
        if bar % 2 == 1 and step >= 14:   # 32nd roll at the end of every second bar
            place(drums, k, hat(vel=.7)); place(drums, k + STEP / 2, hat(vel=.6))
        else:
            place(drums, k, hat(open_=(step == 6), vel=vel))
        k += STEP

groove(b(4), b(17))
place(fx, b(4), impact(), 1.0)
# logo break: impact, hats only, then roll back in
place(fx, b(17), impact(), .9)
for k in np.arange(b(17), b(19), 2 * STEP):
    place(drums, k, hat(vel=.5))
snare_roll(b(19), b(20), drums)
place(fx, b(18.5), riser(1.5 * P), .7)
# call to action
groove(b(20), b(24))
place(fx, b(20), impact(), .8)
place(fx, b(21), impact(1.2), .6)
# final chord stab on b24 with a last kick + 808
place(drums, b(24), kick()); place(bass, b(24), bass808(note("D2"), 1.4)); place(fx, b(24), impact(1.6), .7)

# sidechain: duck music and bass on every kick
env = np.ones(len(drums))
def duck_at(t0):
    i0 = int(t0 * SR); n = int(.22 * SR)
    seg = 1 - .55 * np.exp(-np.arange(n) / SR / .07)
    env[i0:i0 + n] = np.minimum(env[i0:i0 + n], seg[: max(0, min(n, len(env) - i0))])
for bar in range(7):
    for st in KICKS + [14]:
        tk = b(4 * bar) + st * STEP
        if b(4) <= tk < b(17) or b(20) <= tk < b(24):
            duck_at(tk)
for tk in (0, b(1), b(2), b(3), b(24)):
    duck_at(tk)
music *= env[:, None]

# reverb on music + fx
ir_t = t_(1.4); ir = rng.standard_normal((len(ir_t), 2)) * np.exp(-ir_t / .35)[:, None]
wet = np.stack([fftconvolve(music[:, c] + .5 * fx[:, c], ir[:, c])[: len(music)] for c in range(2)], 1) * .012

mix = drums * .9 + bass * .7 + music * 1.4 + fx * .8 + wet
mix = mix[:N]
mix = hp(mix, 70, 2)
mix = .55 * mix + .45 * hp(mix, 180, 1)
mix = np.tanh(mix * 1.15)
# final fade over the last half second
fade = np.minimum(1, (L - np.arange(N) / SR) / .5)[:, None]
mix *= fade
mix /= np.abs(mix).max() / .95

out = sys.argv[1] if len(sys.argv) > 1 else "music.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print("music", round(L, 3), "s ->", out)
