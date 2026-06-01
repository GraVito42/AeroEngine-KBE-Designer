# inlet.py
"""
Inlet — parametric engine inlet duct.

Inherits from Duct. Overrides:
  - pressure_ratio  →  derived from ram_recovery_factor
  - wall_profile    →  bell-mouth or straight profile

Axis convention (from EngineComponent):
  local X = axial, local Y = radial
  Profile in XY plane, revolved 360° by Duct.body
"""

import math
from parapy.core import Input, Attribute, Part
from parapy.geom import Point, Polygon, BSplineCurve

from Duct import Duct


class Inlet(Duct):
    """
    Engine inlet with parametric geometry.

    Physics:
      - Total pressure recovery modelled via ram_recovery_factor
        (ratio P_total_out / P_total_freestream). Typical: 0.95-0.99.
      - No heat addition: T_total_out = T_total_in.
      - Choking logic inherited from Duct.is_choked().
    """

    # ------------------------------------------------------------------
    # Inputs — aerodynamics
    # ------------------------------------------------------------------

    #: [-]  Total-pressure recovery factor (P_out / P_in).
    ram_recovery_factor: float = Input(0.98)

    #: str  Highlight contour type: 'straight' | 'bellmouth'
    highlight_profile: str = Input("bellmouth")

    #: [-]  Lip roundness: ratio of lip radius to highlight radius.
    lip_radius_ratio: float = Input(0.08)

    # ------------------------------------------------------------------
    # Override Duct.pressure_ratio
    # ------------------------------------------------------------------

    @Attribute
    def pressure_ratio(self) -> float:
        """
        Total pressure ratio = ram recovery factor.
        Physics: P_out/P_in equals ram recovery by definition for an inlet.
        """
        return self.ram_recovery_factor

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    @Attribute
    def lip_radius(self) -> float:
        """Absolute lip radius [m]."""
        return self.lip_radius_ratio * self.r_inlet_inner

    @Attribute
    def profile_points(self):
        """
        Returns the list of Point objects for wall_profile.
        Bellmouth: BSpline with mid-contraction.
        Straight: simple trapezoid (same as Duct).
        Logic lives here so wall_profile @Part has a clean single return.
        """
        if self.highlight_profile == "bellmouth":
            x_mid = self.length * 0.4
            r_mid_inner = self.r_inlet_inner * 0.92
            r_mid_outer = r_mid_inner + self.wall_thickness_inlet
            return [
                Point(0.0,         self.r_inlet_outer,  0.0),
                Point(x_mid,       r_mid_outer,         0.0),
                Point(self.length, self.r_outlet_outer, 0.0),
                Point(self.length, self.r_outlet_inner, 0.0),
                Point(x_mid,       r_mid_inner,         0.0),
                Point(0.0,         self.r_inlet_inner,  0.0),
            ]
        else:
            return [
                Point(0.0,         self.r_inlet_inner,  0.0),
                Point(0.0,         self.r_inlet_outer,  0.0),
                Point(self.length, self.r_outlet_outer, 0.0),
                Point(self.length, self.r_outlet_inner, 0.0),
            ]

    # ------------------------------------------------------------------
    # Override wall_profile — single return, logic in @Attribute above
    # ------------------------------------------------------------------

    @Part
    def wall_profile(self):
        """
        Closed profile in the local XY plane revolved by Duct.body.
        Bellmouth: BSplineCurve. Straight: Polygon.
        Profile points computed in self.profile_points @Attribute.
        """
        return Polygon(
            points=self.profile_points,
            hidden=True,
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self):
        warnings = super().validate()

        if not 0.0 < self.ram_recovery_factor <= 1.0:
            warnings.append(
                f"Inlet '{self.label}': ram_recovery_factor="
                f"{self.ram_recovery_factor:.3f} must be in (0, 1]."
            )

        if not 0.0 <= self.lip_radius_ratio <= 0.3:
            warnings.append(
                f"Inlet '{self.label}': lip_radius_ratio="
                f"{self.lip_radius_ratio:.3f} outside typical range [0, 0.3]."
            )

        if self.highlight_profile not in ("straight", "bellmouth"):
            warnings.append(
                f"Inlet '{self.label}': unknown highlight_profile="
                f"'{self.highlight_profile}'. Use 'straight' or 'bellmouth'."
            )

        return warnings


# =============================================================================
# Smoke-test
# =============================================================================
if __name__ == "__main__":
    from parapy.gui import display
    from Flow_station import FlowStation

    inlet_flow = FlowStation(
        station_number=1,
        fluid_type="air",
        p_total=101325.0,
        T_total=288.15,
        mass_flow=22.9,
        Mach=0.5,
    )

    inlet = Inlet(
        inflow_conditions   = inlet_flow,
        Mach_out            = 0.45,
        isos_efficiency     = 0.95,
        station_out         = 2,
        ram_recovery_factor = 0.97,
        highlight_profile   = "bellmouth",
        lip_radius_ratio    = 0.08,
        r_inlet_inner       = 0.18,
        r_inlet_outer       = 0.20,
        r_outlet_inner      = 0.16,
        r_outlet_outer      = 0.18,
        length              = 0.35,
    )

    print("=== INLET SMOKE-TEST ===")
    print(f"  ram_recovery_factor : {inlet.ram_recovery_factor}")
    print(f"  pressure_ratio      : {inlet.pressure_ratio:.4f}")
    print(f"  is_choked()         : {inlet.is_choked()}")
    print(f"  lip_radius          : {inlet.lip_radius:.4f} m")
    print(f"  wall_thickness_in   : {inlet.wall_thickness_inlet:.4f} m")
    print(f"  weight              : {inlet.weight:.2f} kg")

    warnings = inlet.validate()
    if warnings:
        for w in warnings: print(f"  ⚠  {w}")
    else:
        print("  validation: all checks passed.")

    display(inlet)