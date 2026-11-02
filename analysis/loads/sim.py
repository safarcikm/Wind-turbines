"""Time-domain aeroelastic simulation of the 12 kW turbine (concept-level).

Degrees of freedom: rotor azimuth and speed, first flap mode of each blade,
tower first fore-aft mode, pitch actuator per blade, dynamic inflow per blade
element. Aerodynamics: unsteady BEM (Prandtl tip/hub loss, Buhl correction,
first-order dynamic inflow), with yaw error handled by projecting the wind.
Control: variable-speed torque control (k*omega^2, region 2.5), gain-scheduled
PI pitch control, supervisory overspeed trip and emergency stop, fault
injection (loss of generator torque, pitch runaway, stuck blade), and a
mechanical brake.

This is an in-house tool to replace hand estimates until an OpenFAST/QBlade
model exists. Limitations: no edgewise or torsional blade DOF, no tower
side-side DOF, only the longitudinal turbulence component, rigid drivetrain.
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "rotor"))
from bem import Blade, CLEAN, ROUGH, solve  # noqa: E402

G = 9.81


@dataclass
class Turbine:
    R: float = 3.75
    n_el: int = 16
    m_blade: float = 20.0
    f_flap: float = 6.0            # Hz, first flap natural frequency at standstill (assumption)
    zeta_flap: float = 0.01
    southwell: float = 1.2
    J_rotor: float = 216.0         # kg m2 incl. hub and generator drum
    hub_height: float = 18.0
    m_top: float = 480.0
    m_tower_modal: float = 100.0   # 0.25 x tower mass (assumed 400 kg)
    f_tower: float = 1.8           # Hz (assumption, see doc 08 on frequency placement)
    zeta_tower: float = 0.02
    rho: float = 1.225
    P_aero_rated: float = 13_600.0
    rpm_rated: float = 178.0
    rpm_min: float = 0.0           # minimum operating speed (region 1.5), 0 = none; doc 09 uses 80 rpm
    const_power: bool = False       # above rated: Q = P_ref / omega (doc 11) instead of rated torque + speed term
    storm_control: bool = False     # 25-30 m/s: speed and power reduced on the 60 s nacelle wind (doc 11)
    storm_v: tuple = (25.0, 30.0)
    storm_speed_frac: float = 0.25  # speed reduction at the end of the storm ramp
    storm_power_frac: float = 0.60  # power reduction at the end of the storm ramp
    excl_rpm: tuple | None = None   # speed exclusion zone (rpm_lo, rpm_hi) around a tower resonance (doc 09)
    pitch_err: tuple = (0.0, 0.0, 0.0)   # deg, per-blade pitch misalignment (aerodynamic imbalance)
    rpm_trip: float = 210.0        # overspeed trip (118 %) -> emergency stop; design overspeed 250 rpm (doc 08)
    k_overspeed: float = 400.0     # Nm per rad/s above rated speed
    pitch_min: float = -0.5
    pitch_rate_normal: float = 15.0   # deg/s
    pitch_rate_emergency: float = 30.0
    pitch_tau: float = 0.08
    brake_torque: float = 8_730.0
    brake_delay: float = 1.0       # s after emergency stop trigger
    pitch_wn: float = 3.0          # rad/s, speed-loop natural frequency
    polar = CLEAN

    def __post_init__(self):
        self.blade = Blade(R=self.R, tsr_design=6.5, cl_design=1.0, n=self.n_el)
        b = self.blade
        self.r, self.dr, self.c = b.r, b.dr, b.chord
        self.twist0 = b.twist + b.twist_tip_offset
        # blade mass per length ~ chord^2 (section area), normalised to m_blade
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
        # optimal-mode gain from steady BEM (clean polars)
        best = max((solve(b, 8.0, l * 8.0 / self.R, 0.0, self.rho, CLEAN).cp, l)
                   for l in np.arange(5.0, 9.01, 0.125))
        self.cp_opt, self.tsr_opt = best
        self.k_opt = 0.5 * self.rho * math.pi * self.R ** 5 * self.cp_opt / self.tsr_opt ** 3
        # pitch sensitivity dQ/dtheta at several pitch angles above rated (for gain scheduling)
        self._schedule()

    def _schedule(self):
        b = self.blade
        pts = []
        for V in (11.0, 14.0, 18.0, 24.0):
            # pitch that gives rated power at rated speed
            lo, hi = 0.0, 40.0
            for _ in range(30):
                mid = 0.5 * (lo + hi)
                if solve(b, V, self.omega_rated, mid, self.rho, CLEAN).power > self.P_aero_rated:
                    lo = mid
                else:
                    hi = mid
            th = 0.5 * (lo + hi)
            dq = (solve(b, V, self.omega_rated, th + 0.5, self.rho, CLEAN).torque -
                  solve(b, V, self.omega_rated, th - 0.5, self.rho, CLEAN).torque) / 1.0
            pts.append((th, dq))
        self.sched = np.array(pts)          # (pitch deg, dQ/dtheta Nm/deg)
        th0, dq0 = self.sched[0]
        self.dq0, self.th0 = dq0, th0
        wn, zeta = self.pitch_wn, 0.7
        self.Kp0 = 2 * zeta * wn * self.J_rotor / -dq0      # deg per rad/s
        self.Ki0 = wn ** 2 * self.J_rotor / -dq0

    def gain(self, pitch):
        """Gain-scheduling factor: ratio of pitch sensitivity at rated to that at this pitch."""
        dq = np.interp(pitch, self.sched[:, 0], self.sched[:, 1])
        return float(self.dq0 / dq)


@dataclass
class Scenario:
    name: str
    T: float
    field: tuple                    # (t, ys, zs, u[t, y, z])
    yaw: float = 0.0                # deg, yaw misalignment
    parked: bool = False            # brake on, blades feathered
    park_azimuth: float = 0.0       # deg
    idle: bool = False              # feathered, brake off, free rotation
    events: dict = field(default_factory=dict)
    # events: loss_of_torque_t, estop_t, pitch_runaway_t (blade 0 to min at emergency rate),
    #         stuck_blade (index, frozen at its pitch from start or at stop), stuck_pitch_value
    ice_blade_mass: float = 0.0     # kg of ice on blade 0
    rho: float | None = None
    init_rpm: float | None = None
    init_pitch: float | None = None


def interp_field(field_, t, y, z):
    tt, ys, zs, u = field_
    dt = tt[1] - tt[0]
    k = int(min(max(t / dt, 0), len(tt) - 2))
    w = t / dt - k
    w = min(max(w, 0.0), 1.0)
    uk = u[k] * (1 - w) + u[k + 1] * w
    fy = np.clip((y - ys[0]) / (ys[1] - ys[0]), 0, len(ys) - 1.0001)
    fz = np.clip((z - zs[0]) / (zs[1] - zs[0]), 0, len(zs) - 1.0001)
    iy, iz = fy.astype(int), fz.astype(int)
    wy, wz = fy - iy, fz - iz
    return (uk[iy, iz] * (1 - wy) * (1 - wz) + uk[iy + 1, iz] * wy * (1 - wz) +
            uk[iy, iz + 1] * (1 - wy) * wz + uk[iy + 1, iz + 1] * wy * wz)


def steady_init(tb: Turbine, V):
    """Initial rotor speed and pitch from the steady operating schedule."""
    b = tb.blade
    om = min(tb.tsr_opt * V / tb.R, tb.omega_rated)
    res = solve(b, V, om, 0.0, tb.rho, CLEAN)
    if res.power <= tb.P_aero_rated:
        return om, 0.0
    lo, hi = 0.0, 45.0
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        if solve(b, V, tb.omega_rated, mid, tb.rho, CLEAN).power > tb.P_aero_rated:
            lo = mid
        else:
            hi = mid
    return tb.omega_rated, 0.5 * (lo + hi)


def simulate(tb: Turbine, sc: Scenario, dt=0.01, record_every=2):
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
        om, pitch0 = 0.0, 90.0
    else:
        om, pitch0 = steady_init(tb, V0 * math.cos(yaw))
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
    integ = pitch0 / (tb.Ki0 * tb.gain(pitch0)) if pitch0 > 0 else 0.0
    mode = "parked" if sc.parked else ("idle" if sc.idle else "run")
    t_estop = None
    torque_lost = False
    zone = None
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
                           "Mflap2", "Medge0", "Mres0", "Mtilt", "Myaw", "xt", "Mbase", "Fimb", "Vhub"]}
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
        # ---------------- generator / brake torque
        v_filt += dt / 60.0 * (float(np.mean(u)) - v_filt)
        sf = 0.0
        if tb.storm_control:
            sf = min(max((v_filt - tb.storm_v[0]) / (tb.storm_v[1] - tb.storm_v[0]), 0.0), 1.0)
        om_ref = tb.omega_rated * (1 - tb.storm_speed_frac * sf)
        P_ref = tb.P_aero_rated * (1 - tb.storm_power_frac * sf)
        om_rpm = om * 60 / (2 * math.pi)
        if mode == "run" and not torque_lost:
            om_min = tb.rpm_min * 2 * math.pi / 60
            Qz = None
            if zone is not None:
                # speed exclusion zone: hold the lower edge, then cross quickly in either direction
                if zone == "low" and om >= om_L:
                    Qz = min(Q_L + Ks * (om - om_L), Q_H)
                    if Qz >= Q_H and om > 1.02 * om_L:
                        zone = "up"
                if zone == "up":
                    Qz = 0.25 * Q_L                 # unload the generator so the rotor crosses quickly
                    if om >= om_H:
                        zone, Qz = "high", None
                    elif om < 0.99 * om_L:          # gust died before crossing: fall back
                        zone, Qz = "low", None
                if zone == "high" and om < om_H:
                    Qz = max(Q_H - Ks * (om_H - om), Q_L)
                    if Qz <= Q_L and om < 0.98 * om_H:
                        zone = "down"
                if zone == "down":
                    Qz = 2.0 * Q_H                  # extra torque so the rotor crosses down quickly
                    if om <= om_L:
                        zone, Qz = "low", None
                    elif om > 1.01 * om_H:
                        zone, Qz = "high", None
            if Qz is not None:
                Qg = Qz
            elif om_min > 0 and om < 1.05 * om_min:
                # region 1.5: steep torque ramp holds the rotor at or above the minimum speed
                Qg = tb.k_opt * (1.05 * om_min) ** 2 * max(0.0, (om - om_min) / (0.05 * om_min))
            elif tb.const_power and sf > 0 and om > 0.9 * om_ref:
                Qg = P_ref / max(om, 0.5 * om_ref)
            elif om < 0.95 * tb.omega_rated:
                Qg = tb.k_opt * om ** 2
            elif pitch.mean() < 1.0 and om < tb.omega_rated:
                Q95 = tb.k_opt * (0.95 * tb.omega_rated) ** 2
                Qg = Q95 + (tb.Q_rated - Q95) * (om - 0.95 * tb.omega_rated) / (0.05 * tb.omega_rated)
            elif tb.const_power:
                # above rated (or in storm control): constant power, plus the overspeed term
                Qg = P_ref / max(om, 0.5 * om_ref) + tb.k_overspeed * max(om - 1.05 * om_ref, 0.0)
            else:
                # above rated: rated torque plus a speed-proportional term that helps the pitch
                # loop catch gusts (converter and generator rated for 125 % torque)
                Qg = tb.Q_rated + tb.k_overspeed * max(om - tb.omega_rated, 0.0)
            Qg = min(Qg, 1.25 * tb.Q_rated)
        elif mode == "estop" and not torque_lost:
            # converter brakes with maximum torque (dump load) until the rotor slows down
            Qg = 1.25 * tb.Q_rated if om > 2 else 0.0
        else:
            Qg = 0.0
        Qbrake = 0.0
        if mode == "estop" and t >= t_estop + tb.brake_delay:
            Qbrake = tb.brake_torque * min(1.0, (t - t_estop - tb.brake_delay) / 0.3)
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
            Qnet = Qaero - Qg + Qgrav_ice
            if Qbrake > 0:
                if om > 1e-3:
                    Qnet -= Qbrake
                else:
                    Qnet = 0.0 if abs(Qnet) < Qbrake else Qnet - math.copysign(Qbrake, Qnet)
            om = max(om + dt * Qnet / tb.J_rotor, 0.0)
            psi += dt * om
        # ---------------- pitch control
        if mode == "run":
            err = om - om_ref
            gk = tb.gain(pitch.mean())
            integ += dt * err
            integ = min(max(integ, tb.pitch_min / max(tb.Ki0 * gk, 1e-9)), 90 / max(tb.Ki0 * gk, 1e-9))
            cmd = gk * (tb.Kp0 * err + tb.Ki0 * integ)
            pitch_cmd[:] = min(max(cmd, tb.pitch_min), 90.0)
            rate = tb.pitch_rate_normal
        elif mode in ("estop", "parked", "idle"):
            pitch_cmd[:] = 90.0
            rate = tb.pitch_rate_emergency
        if "pitch_runaway_t" in sc.events and t >= sc.events["pitch_runaway_t"]:
            pitch_cmd[0] = -2.0
        if stuck is not None:
            if "stuck_value" in sc.events:
                pitch_cmd[stuck] = sc.events["stuck_value"]
            elif mode == "estop":
                pitch_cmd[stuck] = pitch[stuck]          # freezes when stop begins
        dp = (pitch_cmd - pitch) / tb.pitch_tau
        dp = np.clip(dp, -rate, rate)
        if "pitch_runaway_t" in sc.events and t >= sc.events["pitch_runaway_t"]:
            dp[0] = max(min((pitch_cmd[0] - pitch[0]) / tb.pitch_tau, tb.pitch_rate_emergency), -tb.pitch_rate_emergency)
        pitch = pitch + dt * dp
        if stuck is not None and "stuck_value" in sc.events:
            pitch[stuck] = sc.events["stuck_value"]
        # ---------------- tower fore-aft
        thrust = float(np.sum(Froot))
        xtd += dt * xtdd
        xt += dt * xtd
        # ---------------- record
        if step % record_every == 0:
            M_rc = Mflap + rh * Froot          # flap moment about rotor centre
            rec["t"].append(t); rec["rpm"].append(om_rpm)
            rec["pitch0"].append(pitch[0]); rec["pitch1"].append(pitch[1])
            rec["P"].append(Qg * om); rec["Qgen"].append(Qg + Qbrake); rec["Qaero"].append(Qaero)
            rec["thrust"].append(thrust)
            rec["Mflap0"].append(Mflap[0]); rec["Mflap1"].append(Mflap[1]); rec["Mflap2"].append(Mflap[2])
            rec["Medge0"].append(Medge_aero[0] + grav_edge[0])
            rec["Mres0"].append(math.hypot(Mflap[0], Medge_aero[0] + grav_edge[0]))
            rec["Mtilt"].append(float(np.sum(M_rc * np.cos(az))))
            rec["Myaw"].append(float(np.sum(M_rc * np.sin(az))))
            rec["xt"].append(xt)
            rec["Mbase"].append(tb.k_tower * xt * tb.hub_height)
            rec["Fimb"].append(Fimb)
            rec["Vhub"].append(float(interp_field(sc.field, t, np.array([0.0]), np.array([0.0]))[0]))
    return {k: np.array(v) for k, v in rec.items()}


# ------------------------------------------------------------ fatigue tools
def rainflow(x):
    """Return (ranges, counts) by the ASTM E1049 four-point method on turning points."""
    x = np.asarray(x, float)
    d = np.diff(x)
    tp = [x[0]]
    for i in range(1, len(x) - 1):
        if d[i - 1] * d[i] < 0:
            tp.append(x[i])
    tp.append(x[-1])
    stack, ranges, counts = [], [], []
    for p in tp:
        stack.append(p)
        while len(stack) >= 3:
            X = abs(stack[-1] - stack[-2]); Y = abs(stack[-2] - stack[-3])
            if X < Y:
                break
            if len(stack) == 3:
                ranges.append(Y); counts.append(0.5); stack.pop(0)
            else:
                ranges.append(Y); counts.append(1.0)
                last = stack.pop(); stack.pop(); stack.pop(); stack.append(last)
    for i in range(len(stack) - 1):
        ranges.append(abs(stack[i + 1] - stack[i])); counts.append(0.5)
    return np.array(ranges), np.array(counts)


def damage_sum(x, m):
    rg, ct = rainflow(x)
    return float(np.sum(ct * rg ** m))
