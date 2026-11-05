"""
მართეოს ლოგოს ანიმაციის ხმოვანი ეფექტები (მუსიკის გარეშე): სვუშები, დარტყმა, „კლიკები“, ბრჭყვიალი.
ყველა ხმა აქვე სინთეზირდება, გარე ფაილები და ლიცენზიები არ სჭირდება.

  python3 tools/logo-sfx.py video/raw-sfx.wav
  # ხმის დონე -18 LUFS-მდე (ტელეფონი / სოციალური ქსელები):
  ffmpeg -i video/raw-sfx.wav -af "acompressor=threshold=-24dB:ratio=2:attack=10:release=200:makeup=2,loudnorm=I=-18:TP=-2:LRA=11" -ar 48000 video/marteo-logo-sfx.wav
  ffmpeg -i video/marteo-logo.mp4 -i video/marteo-logo-sfx.wav -c:v copy -c:a aac -b:a 192k -shortest video/marteo-logo-sound.mp4

დროები ემთხვევა index.html-ის ლოგოს ანიმაციას (--ld:.2s, პირველი სლაიდი).
"""
import sys
import wave
import numpy as np

SR = 48000
DUR = 5.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
L = np.zeros(N)
R = np.zeros(N)


def t_axis(d):
    return np.arange(int(SR * d)) / SR


def svf_bandpass(x, f_start, f_end, q=1.2):
    """Time-varying state-variable band-pass (frequency glides exponentially)."""
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


def place(sig, at, gain=1.0, pan=0.0):
    """Add mono signal at time `at` (s), pan -1..1 (equal power)."""
    i = int(at * SR)
    sig = sig[: max(0, N - i)]
    th = (pan + 1) * np.pi / 4
    L[i:i + len(sig)] += sig * gain * np.cos(th)
    R[i:i + len(sig)] += sig * gain * np.sin(th)


def place_stereo(sl, sr_, at, gain=1.0):
    i = int(at * SR)
    n = min(len(sl), N - i)
    L[i:i + n] += sl[:n] * gain
    R[i:i + n] += sr_[:n] * gain


def whoosh(d, f0, f1, peak=0.75, q=1.4, pan_from=-0.6, pan_to=0.4):
    t = t_axis(d)
    noise = rng.standard_normal(len(t))
    x = svf_bandpass(noise, f0, f1, q)
    env = np.where(t < peak * d, (t / (peak * d)) ** 2.2, np.exp(-(t - peak * d) / (0.09 * d / 0.6)))
    x = x * env
    x /= np.max(np.abs(x)) + 1e-9
    pan = np.linspace(pan_from, pan_to, len(t))
    th = (pan + 1) * np.pi / 4
    return x * np.cos(th), x * np.sin(th)


def airy(d, f0, f1, q=0.7, lp=3000, shape=1.0, pan_from=-0.3, pan_to=0.3):
    """Soft breathy swoosh: wide band-pass noise, low-passed, smooth bell-shaped envelope."""
    t = t_axis(d)
    x = svf_bandpass(rng.standard_normal(len(t)), f0, f1, q)
    x = onepole_lp(x, lp)
    env = np.sin(np.pi * (t / d) ** shape) ** 2
    x = x * env
    x /= np.max(np.abs(x)) + 1e-9
    th = (np.linspace(pan_from, pan_to, len(t)) + 1) * np.pi / 4
    return x * np.cos(th), x * np.sin(th)


def pillow(f=68, d=0.6):
    """Very soft low landing: sine with slow attack, a little breath, no click."""
    t = t_axis(d)
    body = np.sin(2 * np.pi * f * t) * np.minimum(1, t / 0.018) * np.exp(-t / 0.18)
    breath = onepole_lp(rng.standard_normal(len(t)), 260) * np.minimum(1, t / 0.02) * np.exp(-t / 0.08)
    x = body + 0.6 * breath / (np.max(np.abs(breath)) + 1e-9)
    return x / (np.max(np.abs(x)) + 1e-9)


def note(f, d=0.9):
    """Gentle glassy tone (soft attack, round decay)."""
    t = t_axis(d)
    ph = 2 * np.pi * f * t
    x = (np.sin(ph) + 0.12 * np.sin(2 * ph)) * np.minimum(1, t / 0.008) * np.exp(-t / 0.28)
    return x / (np.max(np.abs(x)) + 1e-9)


def glow(d=2.0):
    """Soft sparkle: a few high partials fading in and out slowly."""
    t = t_axis(d)
    x = np.zeros(len(t))
    for k, (f, a) in enumerate([(1046.5, 1.0), (1568, .6), (2093, .4), (2637, .22)]):
        tt = np.clip(t - k * 0.06, 0, None)
        x += a * np.sin(2 * np.pi * f * tt) * np.minimum(1, tt / 0.04) * np.exp(-tt / 0.6) * (tt > 0)
    return x / (np.max(np.abs(x)) + 1e-9)


# 1) tile drifts in: soft swoosh -> pillowy landing (~0.88s)
wl, wr = airy(0.9, 200, 1500, q=0.7, lp=2200, shape=0.8, pan_from=-0.4, pan_to=0.0)
place_stereo(wl, wr, 0.0, 0.7)
place(pillow(), 0.84, 0.6)

# 2) the "M" draws itself: faint breath of air
sl, sr_ = airy(0.95, 1200, 3500, q=0.8, lp=4000, pan_from=-0.25, pan_to=0.25)
place_stereo(sl, sr_, 0.62, 0.18)

# 3) three bars grow: soft rising notes (C - E - G)
for at, f, pan in [(1.45, 523.25, -0.2), (1.6, 659.25, 0.0), (1.75, 783.99, 0.2)]:
    place(note(f), at, 0.2, pan)

# 4) wordmark appears: airy swell + gentle sparkle
rl, rr = airy(0.9, 500, 3000, q=0.7, lp=3500, shape=1.4, pan_from=0.3, pan_to=-0.1)
place_stereo(rl, rr, 1.55, 0.4)
g1 = glow()
place(g1, 2.3, 0.14, -0.25)
place(g1, 2.34, 0.14, 0.25)

# light room reverb (exponential noise tail)
ir_t = t_axis(1.6)
def make_ir():
    h = onepole_lp(rng.standard_normal(len(ir_t)) * np.exp(-ir_t / 0.38), 3500)
    return h / np.sqrt(np.sum(h ** 2))


ir_l, ir_r = make_ir(), make_ir()  # decorrelated tails for stereo width


def conv(x, h):
    n = len(x) + len(h) - 1
    m = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(h, m), m)[:len(x)]


L2 = L + 0.32 * conv(L, ir_l)
R2 = R + 0.32 * conv(R, ir_r)

# match the video fade-out (4.3s -> 5.0s) and normalise to -1 dBFS
fade = np.ones(N)
s0 = int(4.3 * SR)
fade[s0:] = np.cos(np.linspace(0, np.pi / 2, N - s0)) ** 2
L2 *= fade
R2 *= fade
peak = max(np.max(np.abs(L2)), np.max(np.abs(R2)))
g = 10 ** (-1 / 20) / peak
pcm = (np.stack([L2, R2], axis=1) * g * 32767).astype('<i2')

out = sys.argv[1] if len(sys.argv) > 1 else 'video/marteo-logo-sfx.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print('wrote', out)
