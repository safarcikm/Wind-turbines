"""M8 generator (doc 35) with other magnet blocks: N42SH 40x20x7.5 and a block-size sweep (doc 36).

Same machine as doc 23 / doc 35: 40 poles / 45 slots, drum Ø646 (shell outer r 323), stator r 299,
gap 2.0, sleeve 0.5, magnet face r 301.5 at the block centre, bond 0.15 mm, stack 104 mm, 131 rpm.
Only the magnet blocks (grade, width across, thickness, length along, pieces across) change.

The 2D FEA (fem.py / magnets.py model, unchanged) is per metre of stack. It is run on the 74 mm
model length and scaled to the 104 mm M8 stack exactly as generator_m8.py does. For each case:

  * line EMF at 100 °C, 28 turns, 131 rpm, 104 mm, with the step skew of its own number of rows
  * rated current: the ampere-turns that give the M8 torque (991 Nm on 104 mm = 705 Nm on 74 mm)
    at 100 °C, q-axis; copper loss = M8 baseline 596 W x (NI / NI_baseline)^2 (same slot fill,
    so independent of the number of turns)
  * torque ripple at rated load and cogging (60 °C), not skewed and step-skewed by rows
  * magnet eddy loss at rated load and 131 rpm (rotor-frame time stepping as magnets.py, then the
    3D piece-length correction for the block length along the stack)
  * demagnetisation margin (worst fully-inside element vs catalogue HcJ) for rated load, steady and
    2 x transient short circuit at 100, 110 and 120 °C; T20 = highest magnet temperature that keeps
    20 % in the transient short circuit

Run:  python3 blocks_m8.py <key> [...]      -> results/blk_<key>.json   (~4 min per case)
      python3 blocks_m8.py all              (4 worker processes)
      python3 blocks_m8.py table            -> results/blocks_summary.json
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
GEN = HERE.parent / "generator"
sys.path.insert(0, str(GEN))
_argv, sys.argv = sys.argv, sys.argv[:1]
from magnets import (Shape, MagGeometry, MagModel, fourier, shift_avg, torsion_factor, RHO_MAG,  # noqa: E402
                     SIGMA_MAG)
sys.argv = _argv

OUT = HERE / "results"
OUT.mkdir(exist_ok=True)

L_FEA = 0.074                    # model length used by the doc 19-23 FEA (results are per metre)
L_M8 = 0.104                     # M8 stack (doc 35)
RPM = 131.0
T_M8 = 991.0                     # Nm rated shaft torque (doc 35)
T_FEA = T_M8 * L_FEA / L_M8      # torque the 74 mm model must give
TURNS = 28
P_CU_M8 = 596.0                  # W, M8 baseline copper loss at rated (doc 35 §4)
GAP_ROWS = 0.2e-3                # gap between rows along the stack
GRADES = {   # catalogue minimum Br [T], HcJ [kA/m] at 20 °C, coefficients [1/K] (as shgrade.py)
    "N42SH": (1.29, 1592e3, -0.0012, -0.0060),
    "N45SH": (1.32, 1592e3, -0.0012, -0.0060),
}
TEMPS = (100.0, 110.0, 120.0)


def C(key, grade, k, b, hm, l, n, note=""):
    return dict(key=key, grade=grade, k=k, b=b / 1e3, hm=hm / 1e3, l=l / 1e3, n=n, note=note)


CASES = {c["key"]: c for c in [
    # reference: doc 35 M8 baseline (Rev C block, 7 rows)
    C("REF", "N45SH", 1, 30, 12, 15, 7, "M8 baseline: N45SH 30x15x12, 1 across x 7 along"),
    # the requested design: N42SH 40x20x7.5 (doc 19 Rev B block), 2 across x 3 along (120.4 mm rows)
    C("A40", "N42SH", 2, 20, 7.5, 40, 3, "N42SH 40x20x7.5, 2 across (20 wide) x 3 along (40 long)"),
    # grade only: the baseline block in N42SH
    C("G30", "N42SH", 1, 30, 12, 15, 7, "N42SH 30x15x12 (grade effect only)"),
    # sweep: one block across the pole, width x thickness (length along is chosen after, see table)
    *[C(f"W{w}_{h}", "N42SH", 1, w, h, 26, 4, f"N42SH {w} wide x {h} thick, 1 across")
      for w in (30, 33, 36) for h in (8, 10, 12)],
    # second round around the best of the first (span 0.66-0.70, 11-12 mm)
    C("W31_12", "N42SH", 1, 31, 12, 26, 4, "N42SH 31 wide x 12 thick, 1 across"),
    C("W33_11", "N42SH", 1, 33, 11, 26, 4, "N42SH 33 wide x 11 thick, 1 across (doc 21 best block)"),
    # two blocks across
    C("D17_10", "N42SH", 2, 17, 10, 26, 4, "N42SH 2 x 17 wide x 10 thick across"),
    C("D20_10", "N42SH", 2, 20, 10, 26, 4, "N42SH 2 x 20 wide x 10 thick across (40x20x10)"),
    C("D17_8", "N42SH", 2, 17, 8, 26, 4, "N42SH 2 x 17 wide x 8 thick across"),
]}


def shape_of(c):
    return Shape(c["key"], c["note"], c["k"], True, hm=c["hm"], b=c["b"], n_ax=c["n"], l_ax=c["l"])


def run(key):
    c = CASES[key]
    br20, hcj20, a_br, b_hcj = GRADES[c["grade"]]
    shape = shape_of(c)
    geo = MagGeometry(br20=br20, br_tc=a_br, hm=c["hm"], d_slot=0.065, L=L_FEA, g=0.0020, sleeve=0.0005)
    geo.r_seat = shape.seat_radius(geo)
    M = MagModel(geo, shape)
    m = M.mesh
    p = geo.poles // 2
    el = 2 * math.pi / p
    per = 2 * math.pi / 360                         # cogging period 1° (LCM 40/45 = 360)
    w_e = p * RPM * 2 * math.pi / 60
    out = dict(c, seat_d_mm=round(2e3 * geo.r_seat, 2), yoke_mm=round(323.0 - 1e3 * geo.r_seat, 2),
               span=round(c["k"] * 2 * math.atan((c["b"]) / 2 / geo.r_m1) / (2 * math.pi / geo.poles), 3))

    # ---- no load, 100 °C, 18 positions over one electrical period
    geo.t_mag = 100.0
    psi = []
    for t in np.arange(18) * el / 18:
        M.solve(t)
        psi.append(M.flux_linkage_per_turn())
    psi = np.array(psi)
    psi1, _ = fourier(psi[:, 0], 1)
    hh = [fourier(psi[:, 0], n)[0] * n for n in (3, 5, 7, 9, 11)]
    deltas = [fourier(psi[:, k], 1)[1] for k in range(3)]
    out["emf_line_100C_28t_unskewed_per_m_V"] = math.sqrt(3) * w_e * psi1 / math.sqrt(2) * TURNS / L_FEA
    out["phase_thd_pct"] = round(100 * math.sqrt(sum(x * x for x in hh)) / psi1, 2)

    # ---- cogging at 60 °C, 12 positions over 1°
    geo.t_mag = 60.0
    cog = []
    for t in np.arange(12) * per / 12:
        M.solve(t)
        cog.append(M.torque())
    out["_cog_FEA_74"] = [float(x) for x in cog]

    def currents(theta, NI, axis, sgn=1.0):
        return [sgn * NI * (-math.sin(p * theta - d) if axis == "q" else math.cos(p * theta - d)) for d in deltas]

    # ---- rated ampere-turns at 100 °C for 705 Nm on the 74 mm model
    geo.t_mag = 100.0
    NI_a = 900.0
    M.solve(0.0, currents(0.0, NI_a, "q"))
    t_a = M.torque()
    sgn = 1.0 if t_a > 0 else -1.0
    t_a = abs(t_a)
    NI_b = NI_a * T_FEA / t_a
    M.solve(0.0, currents(0.0, NI_b, "q", sgn))
    t_b = abs(M.torque())
    NI = NI_b + (T_FEA - t_b) * (NI_b - NI_a) / (t_b - t_a)
    out["NI_rated_peak"] = round(NI, 1)

    # ---- time stepping over one electrical period at rated load: ripple + magnet eddy loss
    n_steps = 60
    dth = el / n_steps
    step_nodes = int(round(dth / (geo.sec_angle / m.nt)))
    assert abs(step_nodes * geo.sec_angle / m.nt - dth) < 1e-12, "step must be a whole number of nodes"
    ring = np.where((m.r >= geo.r_m1 - 1e-9) & (m.r <= geo.r_m2 + 1e-9))[0]
    th_nodes = np.arange(m.nt) * geo.sec_angle / m.nt
    RR, TT = np.meshgrid(m.r[ring], th_nodes, indexing="ij")
    idx, pole, _ = M.inside(RR, TT)
    piece = np.where(idx >= 0, (pole.astype(int) % (geo.poles // geo.sym)) * shape.k + idx, -1)
    dr = np.gradient(m.r)[ring]
    wgt = (RR * dr[:, None] * (geo.sec_angle / m.nt)) * (idx >= 0)
    A_hist, tq = [], []
    for kk in range(n_steps):
        th = kk * dth
        M.solve(th, currents(th, NI, "q", sgn))
        tq.append(M.torque())
        A_hist.append(M.A.reshape(m.nr, m.nt)[ring].copy())
    tq = np.array(tq)
    out["_ripple"] = tq.tolist()
    n_tot = n_steps * geo.poles // geo.sym // 2
    A_hist = np.array(A_hist)
    jj = np.arange(m.nt)
    A_rot = np.empty((n_tot, len(ring), m.nt))
    for kk in range(n_tot):
        A_rot[kk] = A_hist[kk % n_steps][:, (jj + step_nodes * kk) % m.nt]
    omega = RPM * 2 * math.pi / 60
    t_span = geo.sec_angle / omega
    F = np.fft.rfft(A_rot, axis=0)
    freqs = np.fft.rfftfreq(n_tot, d=t_span / n_tot)
    E = -np.fft.irfft(F * (2j * math.pi * freqs)[:, None, None], n=n_tot, axis=0)
    loss = 0.0
    for pc in np.unique(piece[piece >= 0]):
        sel = piece == pc
        w = wgt[sel]
        e = E[:, sel]
        e = e - (e @ w / w.sum())[:, None]
        loss += SIGMA_MAG * np.mean((e ** 2) @ w)
    out["eddy_2d_W_per_m"] = loss * geo.sym

    # ---- demagnetisation
    th_d = deltas[0] / p
    demag = {}
    for T in TEMPS:
        geo.t_mag = T
        hcj = hcj20 * (1 + b_hcj * (T - 20))
        M.solve(th_d)
        psi_pm = M.flux_linkage_per_turn()[0] * TURNS
        for s_d in (1.0, -1.0):
            M.solve(th_d, currents(th_d, NI, "d", s_d))
            psi_d = M.flux_linkage_per_turn()[0] * TURNS
            if abs(psi_d) < abs(psi_pm):
                break
        Ld = abs(psi_pm - psi_d) / (NI / TURNS)
        I_sc = abs(psi_pm) / Ld
        row = dict(HcJ_kA_m=round(hcj / 1e3))
        for name, NIx, ax, sg in (("rated", NI, "q", sgn), ("steady_sc", I_sc * TURNS, "d", s_d),
                                  ("transient_sc", 2 * I_sc * TURNS, "d", s_d)):
            th = th_d if ax == "d" else 0.0
            M.solve(th, currents(th, NIx, ax, sg))
            H, _ = M.magnet_field_along_magnetisation()
            row[name] = round(100 * (1 - abs(float(H.min())) / hcj), 1)
        demag[f"{int(T)}C"] = row
    out["demag_margin_pct"] = demag
    (OUT / f"blk_{key}.json").write_text(json.dumps(out, indent=1))
    print(key, "done", flush=True)


# ------------------------------------------------------------------ evaluation for the M8 machine
LENGTHS = (15, 21, 26, 35, 52)                   # block lengths along the stack: whole rows cover 104-107 mm


def t20(demag):
    tr = [(T, demag[f"{int(T)}C"]["transient_sc"]) for T in TEMPS]
    for (t0, m0), (t1, m1) in zip(tr, tr[1:]):
        if m0 >= 20 > m1:
            return round(t0 + (m0 - 20) * (t1 - t0) / (m0 - m1))
    if tr[-1][1] >= 20:
        return ">120"
    (t0, m0), (t1, m1) = tr[0], tr[1]
    return round(t0 + (m0 - 20) * (t1 - t0) / (m0 - m1))


def evaluate(r, ref, l_mm=None, n=None):
    """M8 figures for result r with blocks l_mm long, n rows along the stack."""
    l_mm = l_mm or r["l"] * 1e3
    n = n or r["n"]
    rows = n * l_mm + (n - 1) * GAP_ROWS * 1e3
    l_in = min(rows, L_M8 * 1e3) / 1e3                   # magnet length facing the stack (overhang: no credit)
    per = 2 * math.pi / 360
    offs = [i / n * per for i in range(n)]
    p = 20
    skf = abs(np.mean([np.exp(1j * p * o) for o in offs]))
    emf28 = r["emf_line_100C_28t_unskewed_per_m_V"] * l_in * skf
    # stack-short magnets need more current: torque ∝ NI x magnet length
    ni = r["NI_rated_peak"] * (L_M8 / l_in) / (skf / ref["_skf"])
    cu = P_CU_M8 * (ni / ref["_ni"]) ** 2
    turns = max(20, round(TURNS * ref["_emf28"] / emf28))
    cog = np.array(r["_cog_FEA_74"]) * l_in / L_FEA
    tq = np.array(r["_ripple"])
    el = 2 * math.pi / p
    rip = float(np.ptp(shift_avg(tq, el, offs)) / tq.mean() * 100)
    eddy = r["eddy_2d_W_per_m"] * l_in * torsion_factor(r["b"], l_mm / 1e3)
    pieces = 40 * r["k"] * n
    mass = pieces * r["b"] * r["hm"] * l_mm / 1e3 * RHO_MAG
    return dict(rows_mm=round(rows, 1), rows=n, l_mm=l_mm, pieces=pieces, spares=2 * r["k"] * n,
                piece_g=round(r["b"] * r["hm"] * l_mm / 1e3 * RHO_MAG * 1e3, 1), magnet_kg=round(mass, 2),
                skew_step_deg=round(1.0 / n, 3), emf_28t_100C_V=round(emf28, 1), turns_for_baseline_V=turns,
                emf_at_turns_V=round(emf28 * turns / TURNS, 1), copper_W=round(cu), copper_vs_M8=round(cu / P_CU_M8, 3),
                cogging_unskewed_Nm=round(float(np.ptp(cog)), 2),
                cogging_skewed_Nm=round(float(np.ptp(shift_avg(cog, per, offs))), 2),
                ripple_skewed_pct=round(rip, 2), eddy_W=round(eddy, 1),
                T20_C=t20(r["demag_margin_pct"]), sc100=r["demag_margin_pct"]["100C"]["transient_sc"],
                sc120=r["demag_margin_pct"]["120C"]["transient_sc"])


def best_length(r, ref):
    """Block length along the stack: whole rows that cover the 104 mm stack (<= 1.5 mm overhang per end).
    Fewest pieces, as long as the magnet eddy loss stays under 10 W and a piece under 60 g."""
    opts = []
    for l in LENGTHS:
        for n in range(2, 9):
            rows = n * l + (n - 1) * 0.2
            if 103.5 <= rows <= 107.0:
                opts.append(evaluate(r, ref, l, n))
    ok = [o for o in opts if o["eddy_W"] <= 10 and o["piece_g"] <= 60] or opts
    return min(ok, key=lambda o: (o["pieces"], o["eddy_W"])), opts


def table():
    res = {k: json.loads((OUT / f"blk_{k}.json").read_text()) for k in CASES if (OUT / f"blk_{k}.json").exists()}
    ref = res["REF"]
    per = 2 * math.pi / 360
    ref["_skf"] = abs(np.mean([np.exp(1j * 20 * i / 7 * per) for i in range(7)]))
    ref["_ni"] = ref["NI_rated_peak"]
    ref["_emf28"] = ref["emf_line_100C_28t_unskewed_per_m_V"] * L_M8 * ref["_skf"]
    rows = []
    for k, r in res.items():
        base = dict(key=k, note=r["note"], grade=r["grade"], k_across=r["k"], width_mm=r["b"] * 1e3,
                    thick_mm=r["hm"] * 1e3, span=r["span"], seat_d_mm=r["seat_d_mm"], yoke_mm=r["yoke_mm"],
                    thd_pct=r["phase_thd_pct"], demag_margin_pct=r["demag_margin_pct"])
        if k in ("REF", "A40", "G30"):
            ev = evaluate(r, ref)
            alts = []
        else:
            ev, alts = best_length(r, ref)
        base.update(ev)
        base["length_options"] = [dict(l_mm=o["l_mm"], rows=o["rows"], pieces=o["pieces"], eddy_W=o["eddy_W"],
                                       piece_g=o["piece_g"], cogging_skewed_Nm=o["cogging_skewed_Nm"]) for o in alts]
        rows.append(base)
    (OUT / "blocks_summary.json").write_text(json.dumps(rows, indent=1))
    print(f"{'key':7s} {'blk':16s} span seat  yoke kg    pcs  E28   N  Cu   cog0 cogS rip  eddy THD  sc100 sc120 T20")
    for r in rows:
        blk = f"{r['width_mm']:.0f}x{r['l_mm']:.0f}x{r['thick_mm']:g}" + (f" x{r['k_across']}" if r["k_across"] > 1 else "")
        print(f"{r['key']:7s} {blk:16s} {r['span']:.2f} {r['seat_d_mm']:.1f} {r['yoke_mm']:4.1f} {r['magnet_kg']:5.2f} "
              f"{r['pieces']:4d} {r['emf_28t_100C_V']:5.1f} {r['turns_for_baseline_V']:2d} {r['copper_W']:4d} "
              f"{r['cogging_unskewed_Nm']:5.2f} {r['cogging_skewed_Nm']:4.2f} {r['ripple_skewed_pct']:4.1f} "
              f"{r['eddy_W']:5.1f} {r['thd_pct']:4.1f} {r['sc100']:5.1f} {r['sc120']:5.1f} {r['T20_C']}")


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    elif sys.argv[1] == "all":
        from multiprocessing import Pool
        todo = [k for k in CASES if not (OUT / f"blk_{k}.json").exists()]
        with Pool(4) as pool:
            pool.map(run, todo, chunksize=1)
    else:
        for k in sys.argv[1:]:
            run(k)
