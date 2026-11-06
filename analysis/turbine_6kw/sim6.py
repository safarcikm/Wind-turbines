"""Aeroelastic simulator for the 6 kW stall-controlled turbine S6 (doc 31).

The time loop is analysis/loads/sim.py (unsteady BEM, flap modes, tower fore-aft, dynamic inflow)
copied from sim.simulate with three changes:
  * fixed pitch (no pitch DOF or pitch controller); +-0.3 deg shim tolerance as pitch_err (relative to pf)
  * generator: optimum-TSR torque below rated, then a PI speed loop whose set point is lowered by
    an outer power loop (stall speed control, doc 28/30), torque limit 1.5 x rated; torque at the
    limit for 2 s -> normal stop (converter brakes to 30 rpm, then the brake)
  * safety chain (doc 29): trip -> K1 closes on the 3 x 4 ohm resistor and the 1.5 kNm spring brake drops;
    events no_k1 / no_brake disable one of them (each-system-alone cases)
"""
from __future__ import annotations
import math, sys, json
from dataclasses import dataclass
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "loads"))
sys.path.insert(0, str(HERE.parent / "rotor"))
from bem import Blade, CLEAN, ROUGH, solve  # noqa: E402
from sim import Turbine, Scenario, interp_field, rainflow, damage_sum, G  # noqa: E402,F401

REG = json.loads((HERE / "results" / "regulation.json").read_text())


@dataclass
class Turbine6(Turbine):
    R: float = 3.0
    r_hub: float = 0.28
    tsr_design: float = 5.5
    pf: float = -2.0
    m_blade: float = 20.6
    f_flap: float = 15.2
    J_rotor: float = 134.0
    m_top: float = 935.0
    P_aero_rated: float = 6800.0
    rpm_rated: float = 163.6
    rpm_trip: float = 189.0
    storm_control: bool = True
    brake_torque: float = 1500.0
    brake_delay: float = 0.2
    q_max_frac: float = 1.5
    k_set: float = 0.03            # outer loop: set point change per s per unit power error
    tau_p: float = 2.0             # s, filter on the estimated aerodynamic power
    om_frac_min: float = 0.50      # lowest speed set point / rated (stall line at 30 m/s is 0.54)
    wn_s: float = 3.0              # speed loop natural frequency, rad/s
    R_ext: float = 4.0             # braking resistor per phase (doc 29)
    ke: float = 11.52              # V rms per rad/s, magnets 100 C (doc 29)
    L_s: float = 13.95e-3
    R_ph: float = 0.307 * 1.2
    poles: int = 20
    polar = ROUGH

    def __post_init__(self):
        self.blade = Blade(R=self.R, r_hub=self.r_hub, tsr_design=self.tsr_design, cl_design=1.0, n=self.n_el)
        b = self.blade
        self.r, self.dr, self.c = b.r, b.dr, b.chord
        self.twist0 = b.twist + b.twist_tip_offset
        w = self.c ** 2
        self.mu = self.m_blade * w / np.sum(w * self.dr)
        self.phi = ((self.r - b.r_hub) / (self.R - b.r_hub)) ** 2
        self.m_gen = float(np.sum(self.mu * self.phi ** 2 * self.dr))
        self.m_cpl = float(np.sum(self.mu * self.phi * self.dr))
        self.w_flap0 = 2 * math.pi * self.f_flap
        self.k_tower = (self.m_top + self.m_tower_modal) * (2 * math.pi * self.f_tower) ** 2
        self.omega_rated = self.rpm_rated * 2 * math.pi / 60
        self.Q_rated = self.P_aero_rated / self.omega_rated
        self.sigma = 3 * self.c / (2 * math.pi * self.r)
        best = max((solve(b, 8.0, l * 8.0 / self.R, self.pf, self.rho, self.polar).cp, l) for l in np.arange(4.0, 8.01, 0.125))
        self.cp_opt, self.tsr_opt = best
        self.k_opt = 0.5 * self.rho * math.pi * self.R ** 5 * self.cp_opt / self.tsr_opt ** 3
        self.Kp_s = 2 * 0.7 * self.wn_s * self.J_rotor + 60.0     # + margin for the positive stall slope dQ/domega
        self.Ki_s = self.wn_s ** 2 * self.J_rotor
        self.om_set_min = self.om_frac_min * self.omega_rated

    def t_res(self, om):
        if om <= 0:
            return 0.0
        E = self.ke * om
        X = self.poles * om * self.L_s
        Rt = self.R_ext + self.R_ph
        I = E / math.hypot(Rt, X)
        return 3 * I * I * Rt / om


def steady_init6(tb, V, rho):
    """Initial speed from the doc 28 stall schedule (or the optimum TSR below rated)."""
    V = max(V, 3.0)
    om = min(tb.tsr_opt * V / tb.R, tb.omega_rated)
    if solve(tb.blade, V, om, tb.pf, rho, tb.polar).power <= tb.P_aero_rated:
        return om, tb.pf
    lo, hi = 0.2 * om, om
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        if solve(tb.blade, V, mid, tb.pf, rho, tb.polar).power > tb.P_aero_rated:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi), tb.pf


def simulate6(tb, sc: Scenario, dt=0.01, record_every=2):
    rho = sc.rho or tb.rho
    r, dr, c, mu, phi = tb.r, tb.dr, tb.c, tb.mu, tb.phi
    rh = tb.blade.r_hub
    R = tb.R
    n = len(r)
    nb = 3
    yaw = math.radians(sc.yaw)
    V0 = float(np.mean(sc.field[3][0]))
    # initial state
    if sc.parked or sc.idle:
        om, pitch0 = 0.0, tb.pf
    else:
        om, pitch0 = steady_init6(tb, V0 * math.cos(yaw), rho)
        if sc.init_rpm is not None:
            om = sc.init_rpm * 2 * math.pi / 60
        if sc.init_pitch is not None:
            pitch0 = sc.init_pitch
    psi = math.radians(sc.park_azimuth)
    pitch = np.full(nb, pitch0)
    pitch_cmd = pitch.copy()
    q = np.zeros(nb); qd = np.zeros(nb); qdd = np.zeros(nb)
    xt = 0.0; xtd = 0.0; xtdd = 0.0
    if sc.parked or sc.idle:
        a = np.zeros((nb, n))
    else:
        a0 = solve(tb.blade, V0 * math.cos(yaw), max(om, 0.1), pitch0, rho, tb.polar).a
        a = np.tile(np.clip(a0, -0.2, 0.7), (nb, 1))
    om_set = min(om, tb.omega_rated)
    integ = 0.0
    P_filt = 0.0
    if not (sc.parked or sc.idle) and om > 1.0:
        st = solve(tb.blade, V0 * math.cos(yaw), om, pitch0, rho, tb.polar)
        P_filt = min(st.power, tb.P_aero_rated)
        integ = min(max(st.power / om, 0.0), tb.q_max_frac * tb.Q_rated) / tb.Ki_s
    t_limit = 0.0
    k1_closed = False
    brake_on_t = None
    conv_stop = False
    no_k1 = sc.events.get("no_k1", False)
    no_brake = sc.events.get("no_brake", False)
    mode = "parked" if sc.parked else ("idle" if sc.idle else "run")
    t_estop = None
    torque_lost = False
    zone = None
    Qg_prev = 0.0
    om_prev = om
    v_filt = V0
    if tb.excl_rpm:
        om_L, om_H = (x * 2 * math.pi / 60 for x in tb.excl_rpm)
        Q_L, Q_H = tb.k_opt * om_L ** 2, tb.k_opt * om_H ** 2
        Ks = (Q_H - Q_L) / (0.02 * om_L)
        zone = "high" if om >= om_H else "low"
    mu_b = np.tile(mu, (nb, 1))
    if sc.ice_blade_mass > 0:
        # IEC distribution: linear to R/2 then constant
        mu_i = np.where(r < R / 2, r / (R / 2), 1.0)
        mu_i = mu_i * sc.ice_blade_mass / np.sum(mu_i * dr)
        mu_b[0] = mu + mu_i
    m_gen_b = np.sum(mu_b * phi ** 2 * dr, axis=1)
    m_cpl_b = np.sum(mu_b * phi * dr, axis=1)
    m_bl_tot = float(np.sum(mu_b * dr))
    k_flap0 = m_gen_b * tb.w_flap0 ** 2
    polars = [ROUGH if (sc.ice_blade_mass > 0 and i == 0) else tb.polar for i in range(nb)]
    stuck = sc.events.get("stuck_blade")
    rec = {k: [] for k in ["t", "rpm", "pitch0", "pitch1", "P", "Qgen", "Qaero", "thrust", "Mflap0", "Mflap1",
                           "Mflap2", "Medge0", "Mres0", "Mtilt", "Myaw", "xt", "Mbase", "Fimb", "Vhub", "stopped", "Qres", "Qbrk"]}
    steps = int(round(sc.T / dt))
    for step in range(steps):
        t = step * dt
        # ---------------- events
        ev = sc.events
        if not torque_lost and "loss_of_torque_t" in ev and t >= ev["loss_of_torque_t"]:
            torque_lost = True
            if t_estop is None:
                t_estop = t + ev.get("estop_delay", 0.1)   # converter fault detected quickly
        if "estop_t" in ev and t >= ev["estop_t"] and t_estop is None:
            t_estop = t
        if mode == "run" and om * 60 / (2 * math.pi) > tb.rpm_trip and t_estop is None:
            t_estop = t
        if "normal_stop_t" in ev and t >= ev["normal_stop_t"] and mode == "run":
            conv_stop = True
        if t_estop is not None and t >= t_estop and mode == "run":
            mode = "estop"
        # ---------------- wind at blade elements
        az = psi + np.arange(nb) * 2 * math.pi / 3                # blade 0 up at psi = 0
        ys = np.outer(np.sin(az), r)
        zs = np.outer(np.cos(az), r)
        u = interp_field(sc.field, t, ys.ravel(), zs.ravel()).reshape(nb, n)
        u_n = u * math.cos(yaw)
        u_ip = u * math.sin(yaw)                                    # in-plane wind along +y
        # tangential direction at element (direction of rotation): d/dpsi of (sin, cos) = (cos, -sin)
        v_t_wind = u_ip * np.cos(az)[:, None]
        # ---------------- aerodynamics
        if mode == "parked":
            # Parked: structural velocities are left out of the inflow. The quasi-steady
            # model (no dynamic stall) predicts unbounded stall-induced vibration at some yaw
            # angles, which real blades limit through dynamic stall and torsion; that risk is
            # reported separately (doc 08) and must be checked with a dynamic-stall model.
            vax = u_n * (1 - a)
        else:
            vax = u_n * (1 - a) - xtd - phi[None, :] * qd[:, None]
        vtan = om * r[None, :] - v_t_wind
        W2 = vax ** 2 + vtan ** 2
        ph = np.arctan2(vax, vtan)
        theta = np.radians(tb.twist0[None, :] + pitch[:, None] + np.asarray(tb.pitch_err)[:, None])
        alpha = np.degrees(ph - theta)
        cl = np.empty_like(alpha); cd = np.empty_like(alpha)
        for i in range(nb):
            cl[i], cd[i] = polars[i].coeffs(((alpha[i] + 180) % 360) - 180)
        cl = np.where(tb.blade.is_cylinder[None, :], 0.0, cl)
        cd = np.where(tb.blade.is_cylinder[None, :], 1.0, cd)
        qdyn = 0.5 * rho * W2 * c[None, :]
        fn = qdyn * (cl * np.cos(ph) + cd * np.sin(ph))          # out of plane, per length
        ft = qdyn * (cl * np.sin(ph) - cd * np.cos(ph))          # in plane (driving), per length
        # dynamic inflow update (quasi-steady target from momentum)
        if mode in ("run", "estop") and om > 1.0:
            sphi = np.maximum(np.abs(np.sin(ph)), 1e-3)
            ftip = 1.5 * (R - r) / (r * sphi)
            fhub = 1.5 * (r - rh) / (rh * sphi)
            F = (2 / math.pi) ** 2 * np.arccos(np.exp(-np.clip(ftip, 0, 50))) * np.arccos(np.exp(-np.clip(fhub, 0, 50)))
            F = np.maximum(F, 0.05)
            CT_loc = 3 * c[None, :] * W2 * (cl * np.cos(ph) + cd * np.sin(ph)) / (2 * math.pi * r[None, :] * np.maximum(u_n, 1.0) ** 2)
            CT_loc = np.clip(CT_loc, -0.5, 2.5)
            a_qs = np.where(CT_loc / F <= 0.96,
                            0.5 - 0.5 * np.sqrt(np.clip(1 - CT_loc / F, 0, 1)),
                            0.143 + np.sqrt(np.clip(0.0203 - 0.6427 * (0.889 - CT_loc / F), 0, None)))
            a_qs = np.clip(a_qs, -0.2, 0.7)
            tau = 1.1 * R / max(V0 * (1 - 1.3 * float(np.mean(a))), 2.0)
            a += dt / tau * (a_qs - a)
        else:
            a *= max(0.0, 1 - dt / 0.5)
        # ---------------- blade flap and tower fore-aft dynamics
        # accelerations solved together (implicit inertial coupling), then symplectic Euler;
        # the explicit coupling used in doc 08 became unstable for stiff blades at dt = 0.01 s
        Faero_b = np.sum(fn * phi[None, :] * dr[None, :], axis=1)
        k_flap = k_flap0 + m_gen_b * tb.southwell * om ** 2
        c_flap = 2 * tb.zeta_flap * np.sqrt(k_flap * m_gen_b)
        m_t = tb.m_top + tb.m_tower_modal
        c_t = 2 * tb.zeta_tower * math.sqrt(tb.k_tower * m_t)
        Amat = np.zeros((nb + 1, nb + 1)); rhs = np.zeros(nb + 1)
        Amat[np.arange(nb), np.arange(nb)] = m_gen_b
        Amat[:nb, nb] = m_cpl_b
        Amat[nb, :nb] = m_cpl_b
        Amat[nb, nb] = m_t + m_bl_tot
        rhs[:nb] = Faero_b - c_flap * qd - k_flap * q
        rhs[nb] = float(np.sum(fn * dr[None, :])) - c_t * xtd - tb.k_tower * xt
        sol = np.linalg.solve(Amat, rhs)
        qdd, xtdd = sol[:nb], float(sol[nb])
        qd += dt * qdd
        q += dt * qd
        # root loads
        inert = mu_b * (phi[None, :] * qdd[:, None] + xtdd)
        Mflap = np.sum((fn - inert) * (r - rh)[None, :] * dr[None, :], axis=1)
        Froot = np.sum((fn - inert) * dr[None, :], axis=1)
        grav_edge = np.sum(mu_b * G * (r - rh)[None, :] * dr[None, :], axis=1) * np.sin(az)
        Q_blades = np.sum(ft * r[None, :] * dr[None, :], axis=1)
        Medge_aero = np.sum(ft * (r - rh)[None, :] * dr[None, :], axis=1)
        Qaero = float(np.sum(Q_blades))
        # ---------------- generator / brake torque (stall speed control, doc 28/30)
        v_filt += dt / 60.0 * (float(np.mean(u)) - v_filt)
        sf = 0.0
        if tb.storm_control:
            sf = min(max((v_filt - tb.storm_v[0]) / (tb.storm_v[1] - tb.storm_v[0]), 0.0), 1.0)
        P_ref = tb.P_aero_rated * (1 - tb.storm_power_frac * sf)
        om_rpm = om * 60 / (2 * math.pi)
        Qmax = tb.q_max_frac * tb.Q_rated
        Qg = 0.0
        if mode == "run" and not torque_lost and not conv_stop:
            # outer loop: lower the speed set point while power is above the reference (into stall)
            # aerodynamic power estimate from generator torque and acceleration (what the converter knows)
            P_est = (Qg_prev + tb.J_rotor * (om - om_prev) / dt) * om
            P_filt += dt / tb.tau_p * (P_est - P_filt)
            om_set += dt * tb.k_set * tb.omega_rated * (P_ref - P_filt) / tb.P_aero_rated
            om_set = min(max(om_set, tb.om_set_min), tb.omega_rated)
            # inner loop: PI speed control (torque) on top of the optimum-TSR curve
            err = om - om_set
            Q_pi = tb.Kp_s * err + tb.Ki_s * (integ + dt * err)
            if Q_pi < Qmax or err < 0:          # anti-windup: freeze the integrator at the torque limit
                integ = min(max(integ + dt * err, 0.0), Qmax / tb.Ki_s)
            Q_pi = tb.Kp_s * err + tb.Ki_s * integ
            Qg = min(max(tb.k_opt * om ** 2, Q_pi), Qmax)
            Qz = None
            if zone is not None:
                # speed exclusion zone around the tower 1P resonance (same logic as sim.py)
                if zone == "low" and om >= om_L:
                    Qz = min(Q_L + Ks * (om - om_L), Q_H)
                    if Qz >= Q_H and om > 1.02 * om_L:
                        zone = "up"
                if zone == "up":
                    Qz = 0.25 * Q_L
                    if om >= om_H:
                        zone, Qz = "high", None
                    elif om < 0.99 * om_L:
                        zone, Qz = "low", None
                if zone == "high" and om < om_H:
                    Qz = max(Q_H - Ks * (om_H - om), Q_L)
                    if Qz <= Q_L and om < 0.98 * om_H:
                        zone = "down"
                if zone == "down":
                    Qz = 2.0 * Q_H
                    if om <= om_L:
                        zone, Qz = "low", None
                    elif om > 1.01 * om_H:
                        zone, Qz = "high", None
            if Qz is not None and Qg < Qmax:
                Qg = Qz
            t_limit = t_limit + dt if Qg >= 0.999 * Qmax else 0.0
            if t_limit > 2.0:
                conv_stop = True
        if conv_stop and mode == "run" and not torque_lost:
            # normal stop: converter brakes at the torque limit to 30 rpm, then the brake parks
            Qg = Qmax if om_rpm > 30 else 0.0
            if om_rpm <= 30 and brake_on_t is None:
                brake_on_t = t
        if mode == "estop" or (torque_lost and t_estop is not None and t >= t_estop):
            # safety chain: converter off, K1 closes on the braking resistor, spring brake drops
            mode = "estop"
            Qg = 0.0
            if not no_k1:
                k1_closed = True
            if brake_on_t is None and not no_brake:
                brake_on_t = t_estop + tb.brake_delay
        Qres = tb.t_res(om) if k1_closed else 0.0
        Qbrake = 0.0
        if brake_on_t is not None and t >= brake_on_t:
            Qbrake = tb.brake_torque * min(1.0, (t - brake_on_t) / 0.3)
        Qg_prev = Qg
        om_prev = om
        Qg_tot = Qg + Qres
        Fimb = 0.0
        if sc.ice_blade_mass > 0:
            Fimb = sc.ice_blade_mass * 0.5 * R * 0.75 * om ** 2   # centrifugal imbalance (approx r_cg)
        # rotor dynamics
        if mode == "parked":
            om = 0.0
        else:
            Qgrav_ice = 0.0
            if sc.ice_blade_mass > 0:
                Qgrav_ice = -sc.ice_blade_mass * G * 0.5 * R * 0.75 * math.sin(az[0])
            Qnet = Qaero - Qg_tot + Qgrav_ice
            if Qbrake > 0:
                if om > 1e-3:
                    Qnet -= Qbrake
                else:
                    Qnet = 0.0 if abs(Qnet) < Qbrake else Qnet - math.copysign(Qbrake, Qnet)
            om = max(om + dt * Qnet / tb.J_rotor, 0.0)
            psi += dt * om
        # ---------------- tower fore-aft
        thrust = float(np.sum(Froot))
        xtd += dt * xtdd
        xt += dt * xtd
        # ---------------- record
        if step % record_every == 0:
            M_rc = Mflap + rh * Froot          # flap moment about rotor centre
            rec["t"].append(t); rec["rpm"].append(om_rpm)
            rec["pitch0"].append(pitch[0]); rec["pitch1"].append(pitch[1])
            rec["P"].append(Qg * om); rec["Qgen"].append(Qg_tot + Qbrake); rec["Qaero"].append(Qaero)
            rec["thrust"].append(thrust)
            rec["Mflap0"].append(Mflap[0]); rec["Mflap1"].append(Mflap[1]); rec["Mflap2"].append(Mflap[2])
            rec["Medge0"].append(Medge_aero[0] + grav_edge[0])
            rec["Mres0"].append(math.hypot(Mflap[0], Medge_aero[0] + grav_edge[0]))
            rec["Mtilt"].append(float(np.sum(M_rc * np.cos(az))))
            rec["Myaw"].append(float(np.sum(M_rc * np.sin(az))))
            rec["xt"].append(xt)
            rec["Mbase"].append(tb.k_tower * xt * tb.hub_height)
            rec["Fimb"].append(Fimb)
            rec["stopped"].append(1.0 if (mode == "estop" or conv_stop) else 0.0)
            rec["Qres"].append(Qres); rec["Qbrk"].append(Qbrake)
            rec["Vhub"].append(float(interp_field(sc.field, t, np.array([0.0]), np.array([0.0]))[0]))
    return {k: np.array(v) for k, v in rec.items()}


