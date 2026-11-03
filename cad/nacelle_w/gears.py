"""Involute gear outlines for printed functional gears (doc 17).

external(z, m)  closed (x, y) outline of an external spur gear
internal_cutter(z, m)  outline to cut out of a ring to make an internal gear
                       (its 'teeth' are the internal gear's tooth spaces)

Backlash is taken out of the tooth thickness (half on each gear), so two
printed gears at the nominal centre distance run with `backlash` mm play.
"""
import math


def _inv(a):
    return math.tan(a) - a


def _outline(z, m, add, ded, backlash, pa_deg=20.0, n_flank=8, n_arc=3, phase=0.0):
    pa = math.radians(pa_deg)
    rp = m * z / 2
    rb = rp * math.cos(pa)
    ra, rf = rp + add, rp - ded
    psi = math.pi / (2 * z) - backlash / 2 / (2 * rp)     # half tooth angle at the pitch circle

    def half(r):
        r = max(r, rb)
        return psi + _inv(pa) - _inv(math.acos(min(1.0, rb / r)))

    radii = [rf + (ra - rf) * i / n_flank for i in range(n_flank + 1)]
    pts = []
    for k in range(z):
        c = phase + 2 * math.pi * k / z
        # root arc from the previous tooth space centre
        h0 = half(rf)
        a_prev = c - math.pi / z
        for i in range(n_arc):
            a = a_prev + (c - h0 - a_prev) * i / n_arc
            pts.append((rf * math.cos(a), rf * math.sin(a)))
        for r in radii:                      # leading flank, root to tip
            a = c - half(r)
            pts.append((r * math.cos(a), r * math.sin(a)))
        ht = half(ra)
        for i in range(1, n_arc):            # tip arc
            a = c - ht + 2 * ht * i / n_arc
            pts.append((ra * math.cos(a), ra * math.sin(a)))
        for r in reversed(radii):            # trailing flank, tip to root
            a = c + half(r)
            pts.append((r * math.cos(a), r * math.sin(a)))
        a_next = c + math.pi / z
        for i in range(1, n_arc):
            a = c + h0 + (a_next - c - h0) * i / n_arc
            pts.append((rf * math.cos(a), rf * math.sin(a)))
    return pts


def external(z, m, backlash=0.3, phase=0.0):
    return _outline(z, m, add=m, ded=1.25 * m, backlash=backlash, phase=phase)


def internal_cutter(z, m, backlash=0.3, phase=0.0):
    # the cutter's teeth are the internal gear's spaces: widen them by the backlash
    return _outline(z, m, add=1.25 * m, ded=1.0 * m, backlash=-backlash, phase=phase)
