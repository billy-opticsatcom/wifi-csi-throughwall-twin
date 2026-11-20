"""
demo_csi_ratio_breathing.py

Generic, self-contained demonstration of one question that shaped the study:
why a cheap single-chain WiFi receiver struggles to see breathing, and why the
CSI ratio of two receive chains on the same card helps.

A textbook multipath channel (a few static paths plus one weak reflector that
moves a few millimetres at a breathing rate) is observed by a receiver with
per-packet clock errors (random common phase and timing slope), automatic gain
control, white noise and 8-bit quantisation. Two signals are compared:

  * single chain : per-subcarrier amplitude |H|, gain-normalised per packet
  * two chains   : complex CSI ratio H1 / H2 (the clock errors cancel)

The figure shows how far the breathing peak rises above the in-band median as
the receiver's quantisation level (signal rms in LSB) changes, averaged over
random channels.

All parameters are generic textbook values. They are NOT the geometry,
materials, receiver calibration, thresholds or processing of the study.

Requires: Python 3.9+, numpy, matplotlib.   Run:  python demo_csi_ratio_breathing.py

Copyright (c) 2026 Ikhlas Sabilly. All rights reserved. See LICENSE.
"""
import numpy as np
import matplotlib.pyplot as plt

FC = 2.4e9                      # carrier (Hz)
LAM = 3e8 / FC                  # wavelength (m)
NSC = 52                        # data subcarriers
DF = 312.5e3                    # subcarrier spacing (Hz)
FS = 50.0                       # packet rate (Hz)
T = 40.0                        # observation (s)
F_BR = 0.25                     # breathing rate (Hz)
AMP_BR = 0.005                  # chest displacement (m)
N_STATIC = 6                    # static paths
DYN_REL = 0.04                  # dynamic-path amplitude relative to the strongest static path
SNR_DB = 35.0                   # per-subcarrier SNR before quantisation
BAND = (0.15, 0.6)              # breathing band (Hz)


def channel(rng, t):
    """Two-antenna CFR [packets, 2, NSC] for one random static scene plus a breathing reflector."""
    k = (np.arange(NSC) - NSC / 2) * DF
    tau = rng.uniform(10e-9, 120e-9, N_STATIC)
    a = rng.rayleigh(1.0, N_STATIC) * np.exp(1j * rng.uniform(0, 2 * np.pi, N_STATIC))
    a /= np.abs(a).max()
    ant_phase = rng.uniform(0, 2 * np.pi, (2, N_STATIC))       # static paths arrive differently at each antenna
    H = np.zeros((len(t), 2, NSC), complex)
    for m in range(2):
        H[:, m, :] = (a[None, :] * np.exp(1j * ant_phase[m])[None, :]
                      * np.exp(-2j * np.pi * k[None, :, None] * tau[None, None, :])[0]).sum(-1)[None, :]
    # breathing reflector: round-trip path length changes by 2 x displacement
    tau_d = rng.uniform(15e-9, 60e-9)
    disp = AMP_BR * 0.5 * (1 - np.cos(2 * np.pi * F_BR * t))
    phase_d = -2 * np.pi * (2 * disp) / LAM
    ang = rng.uniform(-np.pi / 3, np.pi / 3)                   # arrival angle -> phase step between antennas
    for m in range(2):
        H[:, m, :] += (DYN_REL * np.exp(1j * (phase_d + m * np.pi * np.sin(ang)))[:, None]
                       * np.exp(-2j * np.pi * k * tau_d)[None, :])
    return H, k


def receiver(rng, H, k, level_lsb):
    """Per-packet clock errors (common to both chains), AGC, noise and int8 quantisation."""
    n = H.shape[0]
    cfo = np.exp(1j * rng.uniform(0, 2 * np.pi, n))[:, None, None]
    sto = np.exp(-2j * np.pi * k[None, None, :] * rng.normal(0, 25e-9, n)[:, None, None])
    Y = H * cfo * sto
    p = np.sqrt(np.mean(np.abs(Y) ** 2, axis=(1, 2), keepdims=True))
    Y = Y / p
    sig = 10 ** (-SNR_DB / 20) / np.sqrt(2)
    Y = Y + sig * (rng.standard_normal(Y.shape) + 1j * rng.standard_normal(Y.shape))
    Y = Y * level_lsb                                            # AGC to a fixed rms level (LSB)
    q = lambda x: np.clip(np.round(x), -128, 127)
    return q(Y.real) + 1j * q(Y.imag)


def peak_over_median_db(x):
    """Breathing-band peak over in-band median of the subcarrier-averaged spectrum, in dB."""
    x = x - x.mean(0)
    P = (np.abs(np.fft.fft(x * np.hanning(len(x))[:, None], axis=0)) ** 2).mean(1)
    f = np.abs(np.fft.fftfreq(len(x), 1 / FS))          # complex signals: fold +f and -f together
    b = (f >= BAND[0]) & (f <= BAND[1])
    return 10 * np.log10(P[b].max() / np.median(P[b]))


def main():
    t = np.arange(0, T, 1 / FS)
    levels = [4, 8, 12, 17, 25, 40, 60, 90]
    trials = 30
    res = {"single chain, amplitude": [], "two chains, CSI ratio": []}
    rng = np.random.default_rng(2026)
    for L in levels:
        a, r = [], []
        for _ in range(trials):
            H, k = channel(rng, t)
            Y = receiver(rng, H, k, L)
            amp = np.abs(Y[:, 0, :])
            amp = amp / np.maximum(np.sqrt(np.mean(amp ** 2, 1, keepdims=True)), 1e-9)
            a.append(peak_over_median_db(amp))
            ratio = Y[:, 0, :] / np.where(np.abs(Y[:, 1, :]) > 0, Y[:, 1, :], 1)
            r.append(peak_over_median_db(ratio))
        res["single chain, amplitude"].append(np.median(a))
        res["two chains, CSI ratio"].append(np.median(r))
        print(f"level {L:3d} LSB: amplitude {np.median(a):5.1f} dB | ratio {np.median(r):5.1f} dB")

    plt.figure(figsize=(7, 4.2))
    for name, v in res.items():
        plt.plot(levels, v, "o-", lw=2, label=name)
    plt.axhline(10, ls="--", c="gray", lw=1, label="illustrative 10 dB margin")
    plt.xscale("log"); plt.xticks(levels, [str(x) for x in levels])
    plt.xlabel("receiver signal level (rms, LSB of an 8-bit ADC)")
    plt.ylabel("breathing peak over in-band median (dB)")
    plt.title("Generic channel: single chain vs CSI ratio of two chains")
    plt.grid(alpha=0.3); plt.legend(); plt.tight_layout()
    plt.savefig("demo_csi_ratio_breathing.png", dpi=160)
    plt.show()


if __name__ == "__main__":
    main()
