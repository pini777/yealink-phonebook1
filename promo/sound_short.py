"""Builds the 10s cut audio: song segment from the measured downbeat + UI sounds aligned by their peak."""
import sys, subprocess, numpy as np
SONG, OUT = sys.argv[1], sys.argv[2]
SR, P, T0 = 48000, 0.7086937, 123.61814
L = 14 * P
b = lambda i: i * P
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{T0}", "-t", f"{L}", "-i", SONG, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
mus = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()[: int(L * SR)]
n = np.arange(int(L * SR)) / SR
fade = np.minimum(1, np.minimum(n / .012, (L - n) / .012))[:, None]
mix = mus * 0.82 * fade[: len(mus)]

def env(d, a, r):
    t = np.arange(int(d * SR)) / SR
    return t, np.minimum(1, t / a) * np.exp(-t / r)
def click(f=2400, g=.5):
    t, e = env(.05, .0008, .007); rng = np.random.default_rng(1)
    return g * e * (0.6 * np.sin(2 * np.pi * f * t) + 0.4 * rng.standard_normal(len(t)) * np.exp(-t / .002))
def tone(fs, d=.35, g=.28, r=.12):
    t, e = env(d, .003, r); return g * e * sum(np.sin(2 * np.pi * f * t) for f in fs) / len(fs)
def pop(f=520, g=.35):
    t, e = env(.12, .002, .03); return g * e * np.sin(2 * np.pi * (f + 300 * np.exp(-t / .01)) * t)
def key():
    return click(3200, .22)
def thock():
    return click(1100, .55) + pop(180, .3)[: len(click())]

def siren(d):
    t = np.arange(int(d * SR)) / SR
    f = np.where((t / (P / 2)) % 2 < 1, 960, 770)
    ph = 2 * np.pi * np.cumsum(f) / SR
    e = np.minimum(1, np.minimum(t / .4, (d - t) / .5))
    s = 0.07 * e * (np.sin(ph) + .3 * np.sin(2 * ph))
    s[0] = 0.0001; return s
ev = [(b(0), pop(600, .25)), (b(1), click(2400, .45)), (b(1) + .02, pop(500, .3)), (b(2), pop(560, .25)),
      (b(2) + .1, tone([880], .12, .2, .04)), (b(2) + .45, tone([988], .12, .2, .04)), (b(3), tone([1175, 1760], .3, .25, .1)),
      (b(4), pop(620, .25)), (b(4) + .45, click(1800, .35)), (b(6), click(1600, .4)), (b(6) + .02, pop(600, .3)),
      (b(7), tone([1175, 1760], .3, .25, .1)), (b(8), pop(600, .3)), (b(9), pop(700, .25)), (b(10), tone([1046, 1568, 2093], .5, .25, .18)),
      (b(11), pop(500, .35)), (b(12), tone([1318], .25, .22, .08)), (b(13), click(2400, .45))]
ev += [(b(9) + .08 + i * .07, key()) for i in range(5)]
sr_ = siren(b(2))
mix[:len(sr_)] += sr_[:, None]
sr2 = siren(b(1))
i0 = int(b(13) * SR); mix[i0:i0 + len(sr2)] += sr2[:len(mix) - i0, None]
for t, s in ev:
    pk = int(np.argmax(np.abs(s)))          # align the measured peak to the event time
    i0 = int(round(t * SR)) - pk
    seg = s[max(0, -i0):]; i0 = max(0, i0); seg = seg[: len(mix) - i0]
    mix[i0:i0 + len(seg)] += seg[:, None]
mix /= max(1, np.abs(mix).max() / .97)
import wave
with wave.open(OUT, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype("<i2").tobytes())
print("ok", len(ev), "sounds,", round(L, 4), "s")
