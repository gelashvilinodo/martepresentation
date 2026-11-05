"""
მართეოს ლოგოს ანიმაციის ხმოვანი ეფექტები (მუსიკის გარეშე): სვუშები, დარტყმა, „კლიკები“, ბრჭყვიალი.
ყველა ხმა აქვე სინთეზირდება, გარე ფაილები და ლიცენზიები არ სჭირდება.

  python3 tools/logo-sfx.py video/raw-sfx.wav
  # ხმის დონე -16 LUFS-მდე (ტელეფონი / სოციალური ქსელები):
  ffmpeg -i video/raw-sfx.wav -af "acompressor=threshold=-26dB:ratio=3:attack=4:release=150:makeup=4,alimiter=limit=0.85:level=false,loudnorm=I=-16:TP=-1.5:LRA=11" -ar 48000 video/marteo-logo-sfx.wav
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


def impact(f0=95, f1=42, d=0.6):
    t = t_axis(d)
    freq = f1 + (f0 - f1) * np.exp(-t / 0.05)
    body = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t / 0.16)
    click = onepole_lp(rng.standard_normal(len(t)), 2500) * np.exp(-t / 0.012) * 3
    x = body + click
    return x / (np.max(np.abs(x)) + 1e-9)


def blip(f, d=0.35):
    t = t_axis(d)
    pitch = f * (1 + 0.06 * np.exp(-t / 0.01))
    ph = 2 * np.pi * np.cumsum(pitch) / SR
    x = (np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph)) * np.exp(-t / 0.07)
    x *= np.minimum(1, t / 0.002)
    return x / (np.max(np.abs(x)) + 1e-9)


def riser(d, f0, f1):
    t = t_axis(d)
    freq = f0 * (f1 / f0) ** (t / d)
    x = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.sin(np.pi * t / d) ** 2
    return x


def shimmer(d=1.8):
    t = t_axis(d)
    x = np.zeros(len(t))
    for k, (f, a) in enumerate([(2093, 1.0), (2637, .7), (3136, .55), (4186, .35), (5274, .2)]):
        delay = k * 0.035
        tt = np.clip(t - delay, 0, None)
        x += a * np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.45) * (t >= delay) * (1 + 0.15 * np.sin(2 * np.pi * 6 * tt))
    x *= np.minimum(1, t / 0.004)
    return x / (np.max(np.abs(x)) + 1e-9)


# 1) tile flies in: whoosh -> soft impact on the overshoot (~0.88s)
wl, wr = whoosh(0.85, 180, 2400, peak=0.85, q=1.6, pan_from=-0.5, pan_to=0.1)
place_stereo(wl, wr, 0.05, 0.8)
place(impact(), 0.86, 1.0)

# 2) the "M" draws itself: airy pen stroke + quiet riser, small pop when it fills
sl, sr_ = whoosh(0.9, 2500, 6000, peak=0.6, q=2.5, pan_from=-0.3, pan_to=0.3)
place_stereo(sl, sr_, 0.65, 0.16)
place(riser(0.9, 300, 760), 0.65, 0.08)
place(blip(520, 0.25), 1.55, 0.1)

# 3) three bars grow: rising UI ticks
for at, f, pan in [(1.45, 880, -0.25), (1.6, 1175, 0.0), (1.75, 1568, 0.25)]:
    place(blip(f), at, 0.14, pan)

# 4) wordmark appears: reverse swoosh + shimmer
rl, rr = whoosh(0.8, 600, 7000, peak=0.92, q=1.1, pan_from=0.4, pan_to=-0.1)
place_stereo(rl, rr, 1.6, 0.5)
sh = shimmer()
place(sh, 2.38, 0.16, -0.2)
place(sh, 2.40, 0.16, 0.2)

# light room reverb (exponential noise tail)
ir_t = t_axis(1.1)
def make_ir():
    h = onepole_lp(rng.standard_normal(len(ir_t)) * np.exp(-ir_t / 0.25), 5000)
    return h / np.sqrt(np.sum(h ** 2))


ir_l, ir_r = make_ir(), make_ir()  # decorrelated tails for stereo width


def conv(x, h):
    n = len(x) + len(h) - 1
    m = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(h, m), m)[:len(x)]


L2 = L + 0.22 * conv(L, ir_l)
R2 = R + 0.22 * conv(R, ir_r)

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
