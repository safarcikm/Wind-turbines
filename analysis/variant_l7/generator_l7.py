"""L7 generator: Rev C (doc 23) unchanged, 778 Nm at 167 rpm (doc 38). Copied from generator_m8.py; with
L_STACK = 0.074 every scaling factor below is 1 and only the speed and current change.

Original M8 note follows.

Run:  python3 generator_l7.py   -> results/generator_l7.json

Same drum Ø646, same 40 poles / 45 slots, same N45SH 30x15x12 block, same 28 turns, same
coil wire. Only the stack grows from 74 to 104 mm (5 -> 7 magnet rows).
Why this works: torque per amp and EMF per rpm both scale with stack length:
104/74 = 1.405 vs 991/730 = 1.36 (torque, current -3 %) and 1.405 x 131/178 = 1.034 (EMF, +3.4 %).
Demagnetisation margins (current per turn) and the converter stay as in Rev C. The 2D FEA of doc 23 (sh30.py S1x)
is per unit length, so its results scale exactly; end effects favour the longer stack.
Thermal: doc 06 network (thermal.py) via passive_cooling.py with the M8 losses and speed.
"""
from __future__ import annotations
import io, contextlib, json, math, sys
from pathlib import Path
import common as C

GEN = C.ROOT / "generator"
sys.path.insert(0, str(GEN))
sys.argv = sys.argv[:1]
import checks_rc as CK  # noqa: E402
import thermal as TH  # noqa: E402
import passive_cooling as PC  # noqa: E402

L_C, L_V = 0.074, C.L_STACK
K_L = L_V / L_C
DLmm = (L_V - L_C) * 1e3
RPM_C, RPM_V = 178.0, C.RPM
F_C, F_V = 20 * RPM_C / 60, 20 * RPM_V / 60          # electrical frequency, 20 pole pairs
FEA = CK.FEA


def losses():
    l_end = TH.L_END
    k_i = C.Q_RATED / 730.0 / K_L                         # rated current vs Rev C (0.966)
    k_cu = (L_V + l_end) / (L_C + l_end) * k_i ** 2       # longer turn, slightly lower current
    # core loss: 60 % hysteresis (~f), 40 % eddy (~f^2) at 59 Hz, volume x K_L
    k_fe = K_L * (0.6 * F_V / F_C + 0.4 * (F_V / F_C) ** 2)
    k_rot = K_L * (F_V / F_C) ** 2
    return dict(P_cu_RevC=round(CK.P_CU), P_cu=round(CK.P_CU * k_cu), k_cu=round(k_cu, 3), k_R=round((L_V + l_end) / (L_C + l_end), 3),
                P_fe_RevC=218.0, P_fe=round(218.0 * k_fe), P_rotor=round(40.0 * k_rot), P_stray=70.0,
                l_end_mm=round(l_end * 1e3, 1))


def thermal(L):
    """Run the doc 23 §4a passive cooling study with M8 values."""
    orig_thermal = CK.thermal
    orig_solve = TH.solve_case

    def v5_thermal():
        orig_thermal()
        TH.L, TH.L_DRUM = L_V, 0.194 + (L_V - L_C)
        TH.P_CU_75, TH.P_FE, TH.P_ROTOR, TH.P_STRAY = L["P_cu"], L["P_fe"], L["P_rotor"], L["P_stray"]

    def v5_solve(**kw):
        kw["rpm"] = RPM_V
        kw["h_int_run"] = kw["h_int_run"] * (RPM_V / RPM_C) ** 0.8     # rotor-driven stirring is slower
        if kw.get("V_wind") == 10.5:
            kw["V_wind"] = C.V_RATED
        return orig_solve(**kw)

    CK.thermal = v5_thermal
    TH.solve_case = v5_solve
    PC.HERE = C.HERE
    with contextlib.redirect_stdout(io.StringIO()):
        PC.main()
    src = C.OUT / "passive_cooling.json"
    dst = C.OUT / "generator_l7_cooling.json"
    src.replace(dst)
    CK.thermal, TH.solve_case = orig_thermal, orig_solve
    return json.loads(dst.read_text())


def drum_stability():
    """Doc 23 shell check with the longer drum (L_sh 0.239 -> 0.269)."""
    import rotor_rc as R
    t = R.YOKE / 1000
    r_m = (323.0 + R.R_SEAT) / 2 / 1000
    g_eff = 2.0 + R.H / 1.05
    ump = 1.9 * (2.0 + 7.5 / 1.05) / g_eff
    b_rms2 = ump * 1e6 * CK.MU0 * (g_eff / 1000) / (math.pi * 0.300 * 0.074)
    k_mag = b_rms2 / (CK.MU0 * g_eff / 1000)
    out = {}
    for L_sh in (0.239, 0.239 + L_V - L_C):
        lam = math.pi * r_m / L_sh
        k = min(210e9 * t / r_m ** 2 * (lam ** 4 / (n * n + lam * lam) ** 2
                                       + t * t / (12 * r_m * r_m * 0.91) * (n * n + lam * lam) ** 2) for n in range(2, 40))
        out[f"L_shell_{L_sh * 1000:.0f}mm"] = round(k / k_mag)
    out["ump_kN_per_mm"] = round(ump * K_L, 2)
    return out


def main():
    L = losses()
    emf100 = FEA["line_emf_100C_V"] * K_L * RPM_V / RPM_C
    emf20 = FEA["line_emf_20C_V"] * K_L * RPM_V / RPM_C
    v_pk = emf20 * (1 + 0.0012 * 50) * C.RPM_MAX / RPM_V * math.sqrt(2)
    rows = C.ROWS
    p_out = C.P_SHAFT - L["P_cu"] - L["P_fe"] - L["P_rotor"] - L["P_stray"] - 60
    p_out_c = C.P_SHAFT - L["P_cu_RevC"] - 218 - 40 - 70 - 60
    cool = thermal(L)
    res = dict(
        geometry=dict(drum_d_mm=646, stack_mm=L_V * 1e3, magnet_rows=rows, rows_length_mm=round(rows * 15 + (rows - 1) * 0.2, 1),
                      blocks=40 * rows, spares=2 * rows, skew_step_deg=round(1.0 / rows, 3),
                      magnet_kg=round(8.2 * rows / 5, 1), turns=28, poles=40, slots=45),
        electrical=dict(torque_rated_Nm=round(C.Q_RATED), current_vs_RevC=round(C.Q_RATED / 730 / K_L, 3), torque_RevC_Nm=730, freq_Hz=round(F_V, 1), freq_RevC_Hz=round(F_C, 1),
                        line_emf_100C_V=round(emf100, 1), line_emf_RevC_100C_V=FEA["line_emf_100C_V"],
                        peak_line_V_m30C_at_design_overspeed=round(v_pk), current="6.5 % higher than Rev C at rated (same generator, 778 Nm instead of 730 Nm)",
                        demag_transient_SC_100C_pct=CK.demag_at(100), note="I_sc = psi/Ld, both scale with stack: unchanged"),
        losses_W=L, efficiency_rated=dict(L7=round(p_out / C.P_SHAFT, 4), RevC=round(p_out_c / C.P_SHAFT, 4)),
        drum_stability_margin=drum_stability(),
        mass_kg=dict(
            # drum shell (about half of the 91.8 kg weldment) and ribs/fins grow with the 30 mm longer drum
            rotor=dict(RevC=161.0, L7=round(161.0 + 0.5 * 91.8 * DLmm / 194 + 8.2 * (K_L - 1) + 12.5 * DLmm / 194 + 1.0, 1)),
            stator=dict(RevC=115.0, L7=round(40.6 * (1 + 0.6 * (K_L - 1)) + 48.0 * K_L + 24.0 * L["k_R"] + 2.2, 1))),
        cooling=dict(configs={k: v["cases"] for k, v in cool["configs"].items()
                              if k in ("B_cover_blades_RevC", "G_blades_inner_fins_outer_ribs", "H_G_with_25mm_ribs")},
                     limit_hotspot_C=130))
    res["mass_kg"]["total"] = dict(RevC=276.0, L7=round(res["mass_kg"]["rotor"]["L7"] + res["mass_kg"]["stator"]["L7"], 1))
    (C.OUT / "generator_l7.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
