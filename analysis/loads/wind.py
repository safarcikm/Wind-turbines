"""Wind inputs for the time-domain simulation (IEC 61400-1/-2 models).

- Turbulent longitudinal wind on a square grid covering the rotor: Kaimal
  spectrum, IEC exponential coherence, synthesised by the Veers method
  (Cholesky per frequency). Lateral and vertical components are neglected
  (concept-level simplification).
- Normal turbulence model (NTM) per IEC 61400-2: sigma1 = I15 (15 + a V) / (a + 1).
- Extreme turbulence model (ETM) per IEC 61400-1 ed. 3 style, with c = 2.
- Extreme operating gust (EOG) and power-law shear.
"""
from __future__ import annotations

import math

import numpy as np

I15, A_SLOPE = 0.20, 2.0           # design basis Class S turbulence
Z_HUB = 18.0
LAMBDA1 = 0.7 * Z_HUB              # turbulence scale parameter (z < 60 m)
L_U = 8.1 * LAMBDA1                # Kaimal integral length (u)
L_C = 8.1 * LAMBDA1                # coherence scale
V_REF = 55.0
V_AVE = 10.0
V_E1 = 0.75 * 1.4 * V_REF          # 1-year 3 s gust (58 m/s)
ALPHA = 0.2                        # shear exponent


def sigma_ntm(V):
    return I15 * (15 + A_SLOPE * V) / (A_SLOPE + 1)


def sigma_etm(V, c=2.0):
    # IEC 61400-1 ed.3 form, using an I_ref equivalent to our I15 (I_ref ~ I15 at 15 m/s)
    I_ref = I15 * (15 + A_SLOPE * 15) / (A_SLOPE + 1) / (0.75 * 15 + 5.6)
    return c * I_ref * (0.072 * (V_AVE / c + 3) * (V / c - 4) + 10)


def turbulent_field(V_hub, sigma, T=600.0, dt=0.05, n_grid=9, width=8.4, seed=0):
    """Return (t, y, z, u[t, iy, iz]) with u = longitudinal wind incl. mean shear."""
    rng = np.random.default_rng(seed)
    n = int(round(T / dt))
    ys = np.linspace(-width / 2, width / 2, n_grid)
    zs = np.linspace(-width / 2, width / 2, n_grid)
    Y, Z = np.meshgrid(ys, zs, indexing="ij")
    pts = np.stack([Y.ravel(), Z.ravel()], 1)
    npts = len(pts)
    d = np.linalg.norm(pts[:, None, :] - pts[None, :, :], axis=-1)
    freqs = np.fft.rfftfreq(n, dt)[1:]
    df = freqs[1] - freqs[0]
    S = 4 * sigma ** 2 * L_U / V_hub / (1 + 6 * freqs * L_U / V_hub) ** (5 / 3)
    spec = np.zeros((len(freqs) + 1, npts), complex)
    for k, f in enumerate(freqs):
        coh = np.exp(-12 * np.sqrt((f * d / V_hub) ** 2 + (0.12 * d / L_C) ** 2))
        Lc = np.linalg.cholesky(coh + 1e-10 * np.eye(npts))
        phases = np.exp(1j * rng.uniform(0, 2 * np.pi, npts))
        amp = math.sqrt(S[k] * df)
        spec[k + 1] = amp * (Lc @ phases)
    u = np.fft.irfft(spec, n=n, axis=0) * n / 2 * 2 / 2
    # normalise to target sigma (finite-record correction)
    u *= sigma / u.std(axis=0).mean()
    shear = ((Z_HUB + Z) / Z_HUB) ** ALPHA
    u = V_hub * shear.ravel()[None, :] + u
    t = np.arange(n) * dt
    return t, ys, zs, u.reshape(n, n_grid, n_grid)


def eog(V_hub, D=7.5, T=10.5, t0=20.0, t_end=60.0, dt=0.01):
    """Extreme operating gust time series (hub height, uniform over rotor)."""
    s1 = sigma_ntm(V_hub)
    V_gust = min(1.35 * (V_E1 - V_hub), 3.3 * s1 / (1 + 0.1 * D / LAMBDA1))
    t = np.arange(0, t_end, dt)
    tau = t - t0
    v = np.full_like(t, V_hub)
    m = (tau >= 0) & (tau <= T)
    v[m] = V_hub - 0.37 * V_gust * np.sin(3 * np.pi * tau[m] / T) * (1 - np.cos(2 * np.pi * tau[m] / T))
    return t, v, V_gust


def uniform_field(t, v, n_grid=9, width=8.4):
    ys = np.linspace(-width / 2, width / 2, n_grid)
    zs = np.linspace(-width / 2, width / 2, n_grid)
    Y, Z = np.meshgrid(ys, zs, indexing="ij")
    shear = ((Z_HUB + Z) / Z_HUB) ** ALPHA
    return t, ys, zs, v[:, None, None] * shear[None]
