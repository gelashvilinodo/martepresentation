"""
მართეოს სრული პრეზენტაციის ხმოვანი ფონი: ძალიან ჩუმი და ნაზი ეფექტები, მუსიკის გარეშე.
ხმა ჩუმადაა გაკეთებული, რომ ზემოდან ვოისოვერი დაედოს.

  python3 tools/presentation-sfx.py video/raw.wav
  ffmpeg -i video/raw.wav -af "volume=-10dB" -ar 48000 video/marteo-presentation-sfx.wav
  ffmpeg -i video/marteo-presentation.mp4 -i video/marteo-presentation-sfx.wav -c:v copy -c:a aac -b:a 192k -shortest video/marteo-presentation-sound.mp4

დროები ემთხვევა index.html-ის ანიმაციებს (8 სლაიდი x 6 წამი, რიცხვების სლაიდის გარეშე).
"""
import sys
import wave
import numpy as np

SR = 48000
SLIDE = 6.0
N_SLIDES = 8
DUR = SLIDE * N_SLIDES
N = int(SR * DUR)
rng = np.random.default_rng(11)
L = np.zeros(N)
R = np.zeros(N)


def t_axis(d):
    return np.arange(int(SR * d)) / SR


def svf_bandpass(x, f_start, f_end, q=0.7):
    n = len(x)
    f = f_start * (f_end / f_start) ** (np.arange(n) / max(1, n - 1))
    g = 2 * np.sin(np.pi * np.minimum(f, SR / 6) / SR)
    damp = 1.0 / q
    low = band = 0.0
    out = np.empty(n)
    for i in range(n):
        high = x[i] - low - damp * band
        band += g[i] * high
        low += g[i] * band
        out[i] = band
    return out


def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    s = 0.0
    for i in range(len(x)):
        s = (1 - a) * x[i] + a * s
        y[i] = s
    return y


def norm(x):
    return x / (np.max(np.abs(x)) + 1e-9)


def place(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    sig = sig[: max(0, N - i)]
    th = (pan + 1) * np.pi / 4
    L[i:i + len(sig)] += sig * gain * np.cos(th)
    R[i:i + len(sig)] += sig * gain * np.sin(th)


def place_st(st, at, gain=1.0):
    sl, sr_ = st
    i = int(at * SR)
    n = min(len(sl), N - i)
    L[i:i + n] += sl[:n] * gain
    R[i:i + n] += sr_[:n] * gain


def airy(d, f0, f1, lp=1800, shape=1.2, pan_from=-0.3, pan_to=0.3):
    """Soft breath of air - no sharp attack."""
    t = t_axis(d)
    x = onepole_lp(svf_bandpass(rng.standard_normal(len(t)), f0, f1, 0.7), lp)
    x = norm(x * np.sin(np.pi * (t / d) ** shape) ** 2)
    th = (np.linspace(pan_from, pan_to, len(t)) + 1) * np.pi / 4
    return x * np.cos(th), x * np.sin(th)


def pillow(f=68, d=0.6):
    t = t_axis(d)
    body = np.sin(2 * np.pi * f * t) * np.minimum(1, t / 0.02) * np.exp(-t / 0.18)
    return norm(body)


def note(f, d=1.0, decay=0.3):
    """Gentle glassy tone with a soft attack."""
    t = t_axis(d)
    ph = 2 * np.pi * f * t
    return norm((np.sin(ph) + 0.1 * np.sin(2 * ph)) * np.minimum(1, t / 0.012) * np.exp(-t / decay))


def glow(d=2.0):
    t = t_axis(d)
    x = np.zeros(len(t))
    for k, (f, a) in enumerate([(1046.5, 1.0), (1568, .6), (2093, .4), (2637, .22)]):
        tt = np.clip(t - k * 0.06, 0, None)
        x += a * np.sin(2 * np.pi * f * tt) * np.minimum(1, tt / 0.04) * np.exp(-tt / 0.6) * (tt > 0)
    return norm(x)


# pentatonic notes (C major pentatonic) keep everything consonant
C5, D5, E5, G5, A5, C6 = 523.25, 587.33, 659.25, 783.99, 880.0, 1046.5
G4, A4 = 392.0, 440.0


def soft_notes(start, times, freqs, gain=0.12, pans=None):
    for k, (dt, f) in enumerate(zip(times, freqs)):
        pan = pans[k] if pans else (k - (len(times) - 1) / 2) * 0.25
        place(note(f), start + dt, gain, pan)


def logo(at):
    """Logo reveal (same timings as the CSS logo animation, --ld = 0)."""
    place_st(airy(1.0, 200, 1100, lp=1500, shape=1.3, pan_from=-0.3, pan_to=0.0), at - 0.2, 0.22)
    place(pillow(), at + 0.64, 0.25)
    soft_notes(at + 1.25, [0, 0.15, 0.3], [C5, E5, G5], 0.14)
    g = glow()
    place(g, at + 2.1, 0.08, -0.25)
    place(g, at + 2.14, 0.08, 0.25)


# slide transitions: one quiet breath of air at every slide change
for k in range(1, N_SLIDES):
    place_st(airy(1.1, 250, 1400, lp=1600, shape=0.9, pan_from=0.35, pan_to=-0.35), k * SLIDE - 0.15, 0.16)

S = lambda i: i * SLIDE  # noqa: E731  slide start time

# 1. intro: logo (--ld .2s)
logo(S(0) + 0.2)

# 2. problem: three pain points, then ? and !
soft_notes(S(1), [1.6, 1.95, 2.3], [A4, G4, A4], 0.07)
place(note(E5, decay=0.4), S(1) + 2.4, 0.07, -0.3)
place(note(D5, decay=0.4), S(1) + 2.7, 0.06, 0.3)

# 3. solution: core logo pops, three benefits burst out
place(pillow(74), S(2) + 0.95, 0.18)
soft_notes(S(2), [1.85, 2.15, 2.45], [C5, E5, G5], 0.11, [-0.4, 0.4, 0.0])

# 4. how it works: three steps
soft_notes(S(3), [1.0, 2.0, 3.0], [C5, D5, E5], 0.11, [-0.4, 0.0, 0.4])

# 5. demo: devices rise, screens scroll
place_st(airy(1.2, 150, 700, lp=1000, shape=0.8), S(4) + 0.4, 0.14)
place(note(G5, decay=0.35), S(4) + 1.2, 0.07, 0.4)

# 6. audience: three cards rise
soft_notes(S(5), [1.0, 1.4, 1.8], [E5, G5, A5], 0.1, [-0.4, 0.0, 0.4])

# 7. contact: five icons pop in
soft_notes(S(6), [1.15 + i * 0.3 for i in range(5)], [C5, D5, E5, G5, A5], 0.07,
           [-0.5, -0.25, 0.0, 0.25, 0.5])

# 8. end: title, QR scan, logo again (--ld 3s)
place(note(C6, decay=0.5), S(7) + 1.25, 0.06)
place_st(airy(1.4, 1500, 4000, lp=3500, shape=1.0, pan_from=-0.2, pan_to=0.2), S(7) + 1.6, 0.06)
logo(S(7) + 3.0)

# light room reverb
ir_t = t_axis(1.8)


def make_ir():
    h = onepole_lp(rng.standard_normal(len(ir_t)) * np.exp(-ir_t / 0.42), 3200)
    return h / np.sqrt(np.sum(h ** 2))


def conv(x, h):
    n = len(x) + len(h) - 1
    m = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(h, m), m)[:len(x)]


L2 = L + 0.35 * conv(L, make_ir())
R2 = R + 0.35 * conv(R, make_ir())

# fade in/out with the video (0.5s in, last 0.7s out)
fade = np.ones(N)
fi = int(0.5 * SR)
fade[:fi] = np.sin(np.linspace(0, np.pi / 2, fi)) ** 2
fo = int((DUR - 0.75) * SR)
fade[fo:] = np.cos(np.linspace(0, np.pi / 2, N - fo)) ** 2
L2 *= fade
R2 *= fade
peak = max(np.max(np.abs(L2)), np.max(np.abs(R2)))
pcm = (np.stack([L2, R2], axis=1) * (10 ** (-6 / 20) / peak) * 32767).astype('<i2')

out = sys.argv[1] if len(sys.argv) > 1 else 'video/raw.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print('wrote', out, f'{DUR:.0f}s')
