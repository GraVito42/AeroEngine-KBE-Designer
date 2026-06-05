# inlet.py
"""
Inlet — parametric engine inlet duct.

Inherits from Duct. Overrides:
  - pressure_ratio  →  derived from ram_recovery_factor
  - wall_profile    →  polygonal | bellmouth | curved (superellipse lip)

Axis convention (from EngineComponent):
  local X = axial (downstream +), local Y = radial (outward +)
  Profile in XY plane, revolved 360° by Duct.body.

Lip-profile parametrisation (lip_profile_type == 'curved'):
  Industry-standard superellipse representation (cf. nacelle/intake
  aerodynamic optimisation literature). The lip is built from two
  superellipse quadrants meeting at the HIGHLIGHT (leading-edge tip):
      ((x - a)/a)^n + ((y - r_hl)/b)^n = 1
    - inner quadrant: highlight → throat tangent  (radially inward)
    - outer quadrant: highlight → cowl tangent    (radially outward)
  Exponent n controls roundness: n=2 → ellipse, n→∞ → square.
"""

import math
from parapy.core import Input, Attribute, Part, DynamicType
from parapy.geom import Point, Polygon, FittedCurve,RevolvedSolid, RevolvedSurface

from Duct import Duct


class Inlet(Duct):
    """
    Engine inlet with selectable parametric lip geometry.

    Physics:
      - Total pressure recovery via ram_recovery_factor (P_out / P_in).
      - No heat addition: T_total_out = T_total_in.
      - Choking logic inherited from Duct.is_choked().
    """

    # ------------------------------------------------------------------
    # Inputs — aerodynamics
    # ------------------------------------------------------------------
    #: str  Lip contour type: 'polygonal' | 'bellmouth' | 'curved'
    lip_profile_type: str = Input("curved")

    #: [-]  Lip roundness: ratio of lip radius to highlight radius (bellmouth).
    lip_radius_ratio: float = Input(0.08)

    # ------------------------------------------------------------------
    # Inputs — superellipse lip ('curved') -
    # all of these inputs can be left hardcoded
    # ------------------------------------------------------------------

    #: [-]  Axial extent of OUTER quadrant, as fraction of duct length.
    a_ext_ratio: float = Input(0.30)

    #: [-]  Axial extent of INNER quadrant, as fraction of duct length.
    a_int_ratio: float = Input(0.45)

    #: [-]  Superellipse exponent, outer surface (2 = ellipse).
    n_ext: float = Input(2.0)

    #: [-]  Superellipse exponent, inner surface (2 = ellipse).
    n_int: float = Input(2.5)

    #: int  Sample points per superellipse quadrant (resolution).
    n_lip_pts: int = Input(30)

    # ------------------------------------------------------------------
    # Derived lip parameters
    # ------------------------------------------------------------------

    @Attribute
    def r_highlight(self) -> float:
        """
        Highlight (leading-edge tip) radius [m].
        Placed midway between throat (r_inlet_inner) and cowl (r_inlet_outer).
        # TODO [Architect]: confirm highlight should sit at the mid-radius,
        #   or expose it as an explicit Input if the design dictates otherwise.
        """
        return 0.5 * (self.r_inlet_inner + self.r_inlet_outer)

    @Attribute
    def lip_radius(self) -> float:
        """Absolute lip radius [m] (bellmouth contour)."""
        return self.lip_radius_ratio * self.r_inlet_inner

    @Attribute
    def b_ext(self) -> float:
        """Radial semi-axis of OUTER quadrant: highlight → cowl [m]."""
        return self.r_inlet_outer - self.r_highlight

    @Attribute
    def b_int(self) -> float:
        """Radial semi-axis of INNER quadrant: highlight → throat [m]."""
        return self.r_highlight - self.r_inlet_inner

    # ------------------------------------------------------------------
    # Superellipse quadrant generators
    # ------------------------------------------------------------------

    def superellipse_quadrant(self, a, b, sign, n):
        """
        Sample one superellipse quadrant from the highlight outward.

        Parametrisation (t in [0, pi/2]), centre at (a, r_highlight):
            x = a * (1 - cos(t)^(2/n))      → t=0: x=0 (highlight)
            y = r_hl + sign * b * sin(t)^(2/n)
        sign = +1 → outer (radially out), sign = -1 → inner (radially in).

        Returns points ordered highlight → tangent point.
        """
        exp = 2.0 / n
        pts = []
        for i in range(self.n_lip_pts + 1):
            t = (math.pi / 2.0) * i / self.n_lip_pts
            x = a * (1.0 - math.cos(t) ** exp)
            y = self.r_highlight + sign * b * (math.sin(t) ** exp)
            pts.append(Point(self.x_offset + x, y, 0.0))
        return pts

    @staticmethod
    def wall_points(p0, p1, n):
        """n+1 evenly spaced Points from p0 to p1 (inclusive)."""
        return [Point(p0.x + (p1.x - p0.x) * i / n,
                      p0.y + (p1.y - p0.y) * i / n, 0.0)
                for i in range(n + 1)]

    @Attribute
    def n_wall(self) -> int:
        """Sample count per diffuser wall — keeps spacing even with the lip."""
        return max(8, self.n_lip_pts // 3)

    @Attribute
    def outer_lip_points(self):
        """OUTER quadrant: highlight → cowl tangent."""
        return self.superellipse_quadrant(
            self.a_ext_ratio * self.length, self.b_ext, +1.0, self.n_ext)

    @Attribute
    def inner_lip_points(self):
        """INNER quadrant: highlight → throat tangent."""
        return self.superellipse_quadrant(
            self.a_int_ratio * self.length, self.b_int, -1.0, self.n_int)

    @Attribute
    def bellmouth_points(self):
        """
           Rounded trumpet mouth: forward-bulging ellipse from outer lip
           (0, r_inlet_outer) around to inner lip (0, r_inlet_inner).
           theta=0 → outer, theta=pi → inner, theta=pi/2 → forwardmost (-lip_depth).
           """
        return [Point(
            self.x_offset -self.lip_radius * math.sin(math.pi * i / (2 * self.n_lip_pts)),
            self.r_highlight + (
                (self.r_inlet_outer - self.r_highlight) if i <= (2 * self.n_lip_pts) // 2
                else (self.r_highlight - self.r_inlet_inner)
            ) * math.cos(math.pi * i / (2 * self.n_lip_pts)),
            0.0) for i in range((2 * self.n_lip_pts) + 1)]

    # ------------------------------------------------------------------
    # Profile point set (open meridian, both ends at outlet plane x=length)
    # ------------------------------------------------------------------

    @Attribute
    def profile_points(self):
        """Closed meridian loop, NO auto-cap across the bore. Each branch starts/ends at the outlet plane (x=length); force_closure adds only the short outlet wall-thickness segment. Front nose is sealed (lip), outlet end stays an open annular face."""
        return {
            "curved": (
                        self.wall_points(Point(self.x_offset + self.length, self.r_outlet_inner, 0.0),
                                         self.inner_lip_points[-1], self.n_wall)[:-1]
                        + list(reversed(self.inner_lip_points))
                        + self.outer_lip_points[1:]
                        + self.wall_points(self.outer_lip_points[-1],
                                           Point(self.x_offset + self.length, self.r_outlet_outer, 0.0),
                                           self.n_wall)[1:]
                        + [Point(self.x_offset + self.length, self.r_outlet_inner, 0.0)]
),
            "bellmouth": (
                        self.wall_points(Point(self.x_offset + self.length, self.r_outlet_inner, 0.0),
                                         self.bellmouth_points[-1], self.n_wall)[:-1]
                        + list(reversed(self.bellmouth_points))
                        + self.wall_points(self.bellmouth_points[0],
                                           Point(self.x_offset + self.length, self.r_outlet_outer, 0.0),
                                           self.n_wall)[1:]
                        + [Point(self.x_offset + self.length, self.r_outlet_inner, 0.0)]  # chiusura esplicita
                    ),
            "polygonal": [
                Point(self.x_offset + self.length, self.r_outlet_inner, 0.0),
                Point(self.x_offset, self.r_inlet_inner, 0.0),
                Point(self.x_offset, self.r_inlet_outer, 0.0),
                Point(self.x_offset + self.length, self.r_outlet_outer, 0.0),
            ],
        }[self.lip_profile_type]

    # ------------------------------------------------------------------
    # wall_profile — single return expression: valid ParaPy.
    # ------------------------------------------------------------------

    @Part(parse=False)
    def wall_profile(self):
        """Closed annular meridian; FittedCurve for smooth lips, Polygon for the sharp trapezoid. Closure handled by RevolvedSolid in body."""
        return Polygon(points=self.profile_points, hidden=True) if self.lip_profile_type == "polygonal" else FittedCurve(points=self.profile_points,hidden=True)

    # @Attribute
    # def wall_profile_cls(self):
    #     """Curve class selected by lip type; smooth lips fitted, sharp lip polygonal."""
    #     return Polygon if self.lip_profile_type == "polygonal" else FittedCurve
    #
    # @Part
    # def wall_profile(self):
    #     """Closed annular meridian; type chosen by wall_profile_cls. Closure handled by RevolvedSolid in body."""
    #     return DynamicType(type=self.wall_profile_cls, points=self.profile_points, hidden=True)

    # -----------------------------------------------------------------
    # Outer profile override for volume estimation
    # -----------------------------------------------------------------
    @Attribute
    def outer_envelope_points(self):
        """Outer contour of the inlet, front nose → cowl → outlet_outer. Curved/bellmouth use the lip's forwardmost point as the front; polygonal falls back to the straight outer wall."""
        return {
            "curved": (self.outer_lip_points + self.wall_points(self.outer_lip_points[-1],
                                                                Point(self.x_offset + self.length, self.r_outlet_outer,
                                                                      0.0), self.n_wall)[1:]),
            "bellmouth": (self.bellmouth_points + self.wall_points(self.bellmouth_points[0],
                                                                   Point(self.x_offset + self.length,
                                                                         self.r_outlet_outer, 0.0), self.n_wall)[1:]),
            "polygonal": [Point(self.x_offset, self.r_inlet_outer, 0.0),
                          Point(self.x_offset + self.length, self.r_outlet_outer, 0.0)],
        }[self.lip_profile_type]

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self):
        warnings = super().validate()

        if not 0.0 < self.pressure_ratio <= 1.0:
            warnings.append(
                f"Inlet '{self.label}': ram_recovery_factor="
                f"{self.pressure_ratio:.3f} must be in (0, 1]."
            )

        if not 0.0 <= self.lip_radius_ratio <= 0.3:
            warnings.append(
                f"Inlet '{self.label}': lip_radius_ratio="
                f"{self.lip_radius_ratio:.3f} outside typical range [0, 0.3]."
            )

        if self.lip_profile_type not in ("polygonal", "bellmouth", "curved"):
            warnings.append(
                f"Inlet '{self.label}': unknown lip_profile_type="
                f"'{self.lip_profile_type}'. Use 'polygonal', 'bellmouth' or 'curved'."
            )

        if self.lip_profile_type == "curved":
            if self.r_inlet_outer <= self.r_inlet_inner:
                warnings.append(
                    f"Inlet '{self.label}': curved lip needs "
                    f"r_inlet_outer > r_inlet_inner (highlight radius derivation)."
                )
            if self.n_ext < 2.0 or self.n_int < 2.0:
                warnings.append(
                    f"Inlet '{self.label}': superellipse exponents < 2 produce "
                    f"a concave (pinched) lip — check n_ext/n_int."
                )

        return warnings


# =============================================================================
# Smoke-test
# =============================================================================
if __name__ == "__main__":
    from parapy.gui import display
    from Flow_station import FlowStation

    inlet_flow = FlowStation(
        station_number=1, fluid_type="air",
        p_total=101325.0, T_total=288.15, mass_flow=22.9, Mach=0.5,
    )

    inlet = Inlet(
        inflow_conditions   = inlet_flow,
        Mach_out            = 0.7,
        isos_efficiency     = 0.95,
        station_out         = 2,
        pressure_ratio = 0.97,
        lip_profile_type    = "bellmouth",     # 'polygonal' | 'bellmouth' | 'curved'
        length              = 0.35,
        n_ext               = 2.0,
        n_int               = 2.5,
    )

    print("=== INLET SMOKE-TEST ===")
    print(f"  lip_profile_type    : {inlet.lip_profile_type}")
    print(f"  pressure_ratio      : {inlet.pressure_ratio:.4f}")
    print(f"  is_choked()         : {inlet.is_choked()}")
    print(f"  r_highlight         : {inlet.r_highlight:.4f} m")
    print(f"  b_ext / b_int       : {inlet.b_ext:.4f} / {inlet.b_int:.4f} m")
    print(f"  weight              : {inlet.weight:.2f} kg")

    for w in inlet.validate() or ["validation: all checks passed."]:
        print(f"  {w}")

    pts = inlet.profile_points
    print(f"  meridian first pt   : ({pts[0].x:.3f}, {pts[0].y:.3f})")  # expect (length, r_outlet_outer)
    print(f"  meridian last  pt   : ({pts[-1].x:.3f}, {pts[-1].y:.3f})")  # expect (length, r_outlet_inner)
    print(f"  bore radius (min y) : {min(p.y for p in pts):.3f}")  # expect ~r_inlet_inner / throat

    display(inlet)

