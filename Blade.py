"""
Blade.py  — parametric turbomachinery blade solid
==================================================

Inputs
------
profiles        : list[list[tuple]] — N closed 2-D loops (x_norm, y_norm)
                  x_norm in [0,1] (chord), y_norm thickness/chord.
                  LE ~ x=0, TE ~ x=1.  Loop need not close (first≠last OK).
span_fractions  : list[float]  — spanwise station positions in [0,1]
chords          : list[float]  — dimensional chord [m] per station
pitch_angles    : list[float]  — stagger/twist [deg] per station
total_span      : float        — span hub→tip [m]
r_hub           : float        — hub radius [m]
n_pts           : int          — resampling resolution (default 80)

Profile pipeline per station
----------------------------
1. Normalise   → LE at x=0, TE at x=1, y scaled by same chord factor
2. Resample    → n_pts uniform arc-length points (binary search, no drift)
3. Align TE    → index-0 = max-x point
4. Winding     → enforce CCW using signed area; if near-zero (thin profile),
                 force CCW by checking suction side (first non-TE point y > 0)
5. Close       → append pts[0] — FittedCurve needs first==last for a closed wire
6. Scale       → multiply (x,y) by chord [m]
7. Twist       → rotate in X-Z plane about the LE point (x=0 after norm, scaled)
                 LE = (0, 0) before scaling → twist centre = (0, 0) after scaling
                 This is the standard turbomachinery stacking convention.
8. Radial offset → Y = r_hub + span_fraction × total_span

Coordinate system
-----------------
  X — axial / meridional
  Y — radial
  Z — tangential / circumferential
  # TODO: confirm Z-sign with Architect.
"""

import math
from parapy.core import Input, Attribute, Part, child
from parapy.geom import GeomBase, FittedCurve, LoftedSolid, Point


class Blade(GeomBase):

    # ------------------------------------------------------------------
    # Inputs
    # ------------------------------------------------------------------

    profiles       = Input([[], [], []])
    span_fractions = Input([0.0, 0.5, 1.0])
    chords         = Input([0.05, 0.05, 0.05])
    pitch_angles   = Input([0.0, 0.0, 0.0])
    total_span     = Input(0.131)
    r_hub          = Input(0.168)
    n_pts          = Input(80)

    circumferential_angle = Input(0.0)
    """Circumferential angle [deg] of this blade around the engine axis (X).
    Set by Stage for each blade in the row.  Rotates (Y, Z) of each point
    around X: Y' = Y*cos(a) - Z*sin(a),  Z' = Y*sin(a) + Z*cos(a).
    """

    axial_offset = Input(0.0)
    """Axial offset [m] added to X of all points. Used by Stage to place
    the stator downstream of the rotor."""

    # ------------------------------------------------------------------
    # Private helpers — all plain def methods inside the class
    # ------------------------------------------------------------------

    @staticmethod
    def _arc_lengths(pts):
        """Cumulative arc-length for an open 2-D sequence."""
        s = [0.0]
        for k in range(len(pts) - 1):
            s.append(s[-1] + math.hypot(pts[k+1][0]-pts[k][0],
                                        pts[k+1][1]-pts[k][1]))
        return s

    @staticmethod
    def _normalise(pts):
        """Shift LE to x=0, scale so chord = 1.  y divided by same factor."""
        xs = [p[0] for p in pts]
        x_min, x_max = min(xs), max(xs)
        chord = x_max - x_min
        if chord < 1e-12:
            return pts
        return [((p[0]-x_min)/chord, p[1]/chord) for p in pts]

    def _resample(self, pts, n):
        """Resample a closed loop to n uniform arc-length points.

        The loop is closed internally (appends pts[0]) only for arc-length
        computation; the returned list has exactly n points (open, no dup).
        Binary search ensures no drift regardless of original point spacing.
        """
        loop = list(pts)
        if len(loop) > 1 and loop[0] == loop[-1]:
            loop = loop[:-1]
        closed  = loop + [loop[0]]
        lengths = self._arc_lengths(closed)
        total   = lengths[-1]
        if total < 1e-12:
            return [loop[0]] * n
        out = []
        for i in range(n):
            t = total * i / n
            lo, hi = 0, len(lengths) - 2
            while lo < hi - 1:
                mid = (lo + hi) // 2
                if lengths[mid] <= t:
                    lo = mid
                else:
                    hi = mid
            seg   = lengths[lo+1] - lengths[lo]
            alpha = (t - lengths[lo]) / seg if seg > 1e-14 else 0.0
            x = closed[lo][0] + alpha*(closed[lo+1][0]-closed[lo][0])
            y = closed[lo][1] + alpha*(closed[lo+1][1]-closed[lo][1])
            out.append((x, y))
        return out

    @staticmethod
    def _align_te(pts):
        """Rotate loop so index-0 = trailing edge (maximum x)."""
        idx = max(range(len(pts)), key=lambda k: pts[k][0])
        return pts[idx:] + pts[:idx]

    @staticmethod
    def _enforce_ccw(pts):
        """Ensure CCW winding.

        For thin profiles the signed-area test is unreliable (near zero).
        We use a more robust check: after aligning TE to index-0, the first
        non-TE point should be on the suction side (y > 0 for a profile
        with suction on top).  If the second point has y < 0, the loop is
        traversed pressure-first (CW) and must be reversed.

        If the profile is symmetric (y=0 for second point), fall back to
        signed area.
        """
        # Signed-area approach
        n   = len(pts)
        area = 0.5 * sum(pts[k][0]*pts[(k+1)%n][1]
                         - pts[(k+1)%n][0]*pts[k][1]
                         for k in range(n))
        if abs(area) > 1e-8:
            return pts if area >= 0 else list(reversed(pts))
        # Near-zero area (symmetric profile): check y of first non-TE point
        # After _align_te, pts[0] is TE. pts[1] should have y > 0 for CCW.
        if len(pts) > 1 and pts[1][1] < 0:
            return list(reversed(pts))
        return pts

    def _profile_to_3d(self, i):
        """Build the closed 3-D Point list for station i.

        Twist rotates the profile about the LE (x=0, y=0 in normalised
        coords → x=0, z=0 after scaling), which is the standard
        turbomachinery stacking axis.

        After twist the LE stays fixed at (0, r, 0) in ParaPy space;
        the chord and camber rotate around it in the X-Z plane.
        """
        raw = self.profiles[i]
        c = self.chords[i]
        pitch = math.radians(self.pitch_angles[i])
        r = self.r_hub + self.span_fractions[i] * self.total_span

        # 2-D pipeline: normalise → resample → align TE → enforce CCW
        pts2d = self._enforce_ccw(
            self._align_te(
                self._resample(
                    self._normalise(raw),
                    self.n_pts)))

        # Close the loop (FittedCurve needs first == last for a closed wire)
        pts2d_closed = pts2d + [pts2d[0]]

        # Scale, twist about LE (which is at x=0, z=0), then place in annulus.
        cos_p, sin_p = math.cos(pitch), math.sin(pitch)
        # Circumferential placement: rotate (Y=radial, Z=tangential) around X axis.
        ca = math.radians(self.circumferential_angle)
        cos_a, sin_a = math.cos(ca), math.sin(ca)
        x_off = self.axial_offset
        out = []
        for x_n, y_n in pts2d_closed:
            xm = x_n * c  # axial in blade frame (LE = 0)
            zm = y_n * c  # tangential in blade frame (LE = 0)
            # Step 1 — stagger (twist in X-Z plane about LE)
            x3 = xm * cos_p + zm * sin_p
            z3 = -xm * sin_p + zm * cos_p
            # Step 2 — radial offset places hub at r along Y
            y3 = r  # Y = radial distance from engine axis
            # Step 3 — rotate entire blade circumferentially around engine X axis
            # R_x(a): Y' = Y*cos(a) - Z*sin(a),  Z' = Y*sin(a) + Z*cos(a)
            y_rot = y3 * cos_a - z3 * sin_a
            z_rot = y3 * sin_a + z3 * cos_a
            # Step 4 — axial offset (stator downstream of rotor)
            out.append(Point(x3 + x_off, y_rot, z_rot))
        return out

    @staticmethod
    def _flatten_matrix(raw):
        """Flatten body.matrix_of_inertia (tuple of unknown nesting) to 9 floats.

        Row-major: [I00,I01,I02, I10,I11,I12, I20,I21,I22]
        i.e. [Ixx,Ixy,Ixz, Iyx,Iyy,Iyz, Izx,Izy,Izz]
        """
        flat = []
        for item in raw:
            try:
                for v in item:
                    flat.append(float(v))
            except TypeError:
                flat.append(float(item))
        return flat

    # ------------------------------------------------------------------
    # Attributes
    # ------------------------------------------------------------------

    @Attribute
    def n_stations(self):
        """Number of spanwise stations."""
        return len(self.profiles)

    @Attribute
    def span(self):
        """Blade span [m]."""
        return self.total_span

    @Attribute
    def mean_chord(self):
        """Arithmetic mean chord [m]."""
        return sum(self.chords) / len(self.chords)

    @Attribute
    def station_radii(self):
        """Radial position [m] of each station."""
        return [self.r_hub + f*self.total_span for f in self.span_fractions]

    @Attribute
    def validation_warnings(self):
        """Geometry sanity checks — returns list of warning strings."""
        w = []
        if self.n_stations < 2:
            w.append("Blade: need >= 2 profiles to loft.")
        for name, lst in [("chords",         self.chords),
                           ("pitch_angles",   self.pitch_angles),
                           ("span_fractions", self.span_fractions)]:
            if len(lst) != self.n_stations:
                w.append(f"Blade: len({name}) != n_stations.")
        for i, prof in enumerate(self.profiles):
            if len(prof) < 4:
                w.append(f"Blade: profile[{i}] has < 4 points.")
        return w

    @Attribute
    def section_point_lists(self):
        """Closed 3-D Point list per station — feeds section_profiles."""
        return [self._profile_to_3d(i) for i in range(self.n_stations)]

    @Attribute
    def volume(self):
        """Blade volume [m^3]."""
        return self.body.volume

    @Attribute
    def cog(self):
        """Centre of gravity of the blade solid."""
        return self.body.cog

    @Attribute
    def inertia_matrix_flat(self):
        """Flat list of 9 floats [m^5] at unit density.

        Row-major: index 0=Ixx, 4=Iyy, 8=Izz, 1=Ixy, 2=Ixz, 5=Iyz.
        Multiply by density [kg/m^3] to get [kg*m^2].
        """
        return self._flatten_matrix(self.body.matrix_of_inertia)

    @Attribute
    def I_xx(self):
        """MOI about axial X [kg*m^2] — edgewise (index 0)."""
        return self.inertia_matrix_flat[0]

    @Attribute
    def I_yy(self):
        """MOI about radial Y [kg*m^2] — spin axis (index 4)."""
        return self.inertia_matrix_flat[4]

    @Attribute
    def I_zz(self):
        """MOI about tangential Z [kg*m^2] — flapwise (index 8)."""
        return self.inertia_matrix_flat[8]

    @Attribute
    def I_xy(self):
        """Product of inertia I_xy [kg*m^2] (index 1)."""
        return self.inertia_matrix_flat[1]

    @Attribute
    def I_xz(self):
        """Product of inertia I_xz [kg*m^2] (index 2)."""
        return self.inertia_matrix_flat[2]

    @Attribute
    def I_yz(self):
        """Product of inertia I_yz [kg*m^2] (index 5)."""
        return self.inertia_matrix_flat[5]

    # ------------------------------------------------------------------
    # Parts
    # ------------------------------------------------------------------

    @Part
    def section_profiles(self):
        """Quantified closed FittedCurves, one per station (hidden)."""
        return FittedCurve(
            quantify=self.n_stations,
            points=self.section_point_lists[child.index],
            hidden=True,
        )

    @Part
    def body(self):
        """Blade solid — LoftedSolid through all closed station profiles."""
        return LoftedSolid(
            profiles=[self.section_profiles[i] for i in range(self.n_stations)],
            color=self.color,
        )


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    from parapy.gui import display

    hub = [
        (1.0100, 0.00000), (1.0000, 0.00252), (0.9500, 0.01613),
        (0.9000, 0.02896), (0.8000, 0.05247), (0.7000, 0.07328),
        (0.6000, 0.09127), (0.5000, 0.10588), (0.4000, 0.11607),
        (0.3000, 0.12004), (0.2500, 0.11883), (0.2000, 0.11475),
        (0.1500, 0.10691), (0.1000, 0.09365), (0.0750, 0.08400),
        (0.0500, 0.07109), (0.0250, 0.05229), (0.0125, 0.03788),
        (0.0000, 0.00000),
        (0.0125, -0.03788), (0.0250, -0.05229), (0.0500, -0.07109),
        (0.0750, -0.08400), (0.1000, -0.09365), (0.1500, -0.10691),
        (0.2000, -0.11475), (0.2500, -0.11883), (0.3000, -0.12004),
        (0.4000, -0.11607), (0.5000, -0.10588), (0.6000, -0.09127),
        (0.7000, -0.07328), (0.8000, -0.05247), (0.9000, -0.02896),
        (0.9500, -0.01613), (1.0000, -0.00252), (1.0100, 0.00000),
    ]

    tip = [
        (1.000000, 0.000000), (0.949847, -0.005010), (0.899700, -0.009785),
        (0.849572, -0.014642), (0.799563, -0.019578), (0.749635, -0.024853),
        (0.699688, -0.030297), (0.649754, -0.035588), (0.599834, -0.040495),
        (0.549928, -0.044858), (0.500034, -0.048533), (0.450148, -0.051362),
        (0.400269, -0.053193), (0.350390, -0.053850), (0.300507, -0.053287),
        (0.250616, -0.051396), (0.200711, -0.048232), (0.150786, -0.043574),
        (0.100824, -0.036964), (0.075819, -0.032609), (0.050786, -0.027144),
        (0.025694, -0.019716), (0.013089, -0.014304), (0.008015, -0.011318),
        (0.005462, -0.009430), (0.000000, 0.000000),
        (0.004538, 0.009993), (0.006985, 0.012109), (0.011911, 0.015510),
        (0.024306, 0.021825), (0.049214, 0.030750), (0.074181, 0.037473),
        (0.099176, 0.042925), (0.149214, 0.051381), (0.199289, 0.057533),
        (0.249384, 0.061911), (0.299493, 0.064773), (0.349610, 0.066089),
        (0.399731, 0.065981), (0.449852, 0.064504), (0.499966, 0.061833),
        (0.550072, 0.058120), (0.600166, 0.053511), (0.650246, 0.048135),
        (0.700312, 0.042123), (0.750365, 0.035655), (0.800437, 0.028925),
        (0.850428, 0.021856), (0.900300, 0.014689), (0.950153, 0.007463),
        (1.000000, 0.000000),
    ]

    blade = Blade(
        profiles=[hub, hub, tip],
        span_fractions=[0.0, 0.5, 1.0],
        chords=[0.060, 0.055, 0.045],
        pitch_angles=[-58.6, -60.4, -61.5],
        total_span=0.131,
        r_hub=0.168,
        n_pts=60,
        label='test_blade',
        color=( 38,  38,  38)
    )

    for w in blade.validation_warnings:
        print(f"WARNING: {w}")

    print(f"span             = {blade.span:.4f} m")
    print(f"mean_chord       = {blade.mean_chord:.4f} m")
    print(f"station_radii    = {[round(r, 4) for r in blade.station_radii]}")
    print(f"volume           = {blade.volume:.4e} m^3")
    print(f"CoG              = {blade.cog}")
    print(f"inertia flat     = {[f'{v:.3e}' for v in blade.inertia_matrix_flat]}")
    print(f"I_xx (edgewise)  = {blade.I_xx:.4e} kg*m^2")
    print(f"I_yy (spin axis) = {blade.I_yy:.4e} kg*m^2")
    print(f"I_zz (flapwise)  = {blade.I_zz:.4e} kg*m^2")

    display(blade)