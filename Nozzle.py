# nozzle.py
"""
Nozzle — parametric engine exhaust nozzle.

Inherits from Duct. Adds:
  - is_convergent_divergent : C-D geometry flag (bool @Input)
  - thrust_coefficient      : gross thrust / ideal thrust (@Attribute)

Geometry:
  Convergent (default):
    4-point trapezoid, identical to Duct — inner radius decreases toward exit.
  Convergent-Divergent:
    5-point polygon — outer wall straight from inlet to outlet (trapezoid);
    inner wall convergent to throat then divergent to exit.
    Throat inner radius and axial position are settable @Inputs.

Axis convention (from EngineComponent / Duct):
  local X = axial, local Y = radial
  Profile in XY plane, revolved 360° by Duct.body
"""

import math
from parapy.core import Input, Attribute, Part
from parapy.geom import Point, Polygon

from Duct import Duct


class Nozzle(Duct):
    """
    Engine exhaust nozzle with convergent or convergent-divergent geometry.

    Physics:
      - Total-pressure loss modelled via pressure_ratio (inherited from Duct).
        For a nozzle, pressure_ratio < 1.0 (expansion).
      - Convergent nozzle: exit capped at Mach 1.0 when choked
        (inherits Duct.is_choked logic).
      - C-D nozzle: choking determined by physical throat area; supersonic
        exit at user-specified Mach_out (must be > 1.0 for design intent).
      - thrust_coefficient: gross-thrust coefficient relative to ideal
        isentropic expansion to p_ambient.
    """

    # ------------------------------------------------------------------
    # Inputs — nozzle type and ambient reference
    # ------------------------------------------------------------------

    #: bool  True → convergent-divergent geometry and supersonic exit logic.
    is_convergent_divergent: bool = Input(False)

    #: [Pa]  Ambient static pressure — reference for thrust coefficient.
    p_ambient: float = Input(101325.0)

    # ------------------------------------------------------------------
    # C-D throat geometry inputs
    # ------------------------------------------------------------------

    #: [-]  Throat-to-inlet area ratio (A_throat / A_in). Only used when
    #:      is_convergent_divergent=True. Typical: 0.6–0.85.
    throat_area_ratio: float = Input(0.8)

    @Input
    def x_throat(self) -> float:
        """Axial position of throat from nozzle face [m]. Default: 60 % of length."""
        return self.length * 0.6

    @Input
    def r_throat_inner(self) -> float:
        """Inner radius at throat [m]."""
        return math.sqrt(self.area_throat / math.pi)

    # ------------------------------------------------------------------
    # Derived throat attribute
    # ------------------------------------------------------------------

    @Attribute
    def area_throat(self) -> float:
        """Throat flow area [m²] = throat_area_ratio × area_in."""
        return self.area_in * self.throat_area_ratio

    # ------------------------------------------------------------------
    # Override outlet_flow — C-D exit at design Mach_out (may be > 1)
    # ------------------------------------------------------------------

    @Input
    def outlet_flow(self):
        """
        C-D nozzle:  exit always at design Mach_out (set > 1 for supersonic).
        Convergent:  cap at Mach 1.0 if choked (inherits Duct behaviour).
        """
        if self.is_convergent_divergent:
            return self.inflow_conditions.isentropic_trans(
                target_type  = "temperature",
                target_value = self.inflow_conditions.p_total * self.pressure_ratio,
                eta          = self.isos_efficiency,
                Mach_out     = self.Mach_out,
            )
        elif self.is_choked():
            return self.inflow_conditions.isentropic_trans(
                target_type  = "temperature",
                target_value = self.inflow_conditions.p_total * self.pressure_ratio * self.choking_losses,
                eta          = self.isos_efficiency,
                Mach_out     = 1.0,
            )
        else:
            return self.inflow_conditions.isentropic_trans(
                target_type  = "temperature",
                target_value = self.inflow_conditions.p_total * self.pressure_ratio,
                eta          = self.isos_efficiency,
                Mach_out     = self.Mach_out,
            )

    # ------------------------------------------------------------------
    # Thrust coefficient
    # ------------------------------------------------------------------

    def thrust_coefficient_estimation(self):
        """
        Gross-thrust coefficient:  C_Fg = F_gross / F_ideal

          F_gross = ṁ·V_exit + (p_exit_static − p_amb)·A_exit
          F_ideal = ṁ·V_ideal  (isentropic expansion to p_ambient)
          V_ideal = √(2·γ/(γ−1)·R·T₀ᵢₙ·(1−(p_amb/p₀ᵢₙ)^((γ−1)/γ)))

        Returns 0.0 if p_ambient ≥ p_total_in (non-physical).
        Values:
          ≈ 1.0  ideal / perfectly expanded
          > 1.0  underexpanded (p_exit > p_amb)
          < 1.0  overexpanded or viscous losses dominate
        """
        T_total_in  = self.station_in.T_total
        p_total_in  = self.station_in.p_total
        m_dot       = self.inflow_conditions.mass_flow

        V_exit        = self.station_out_part.v
        p_exit_static = self.station_out_part.p_static
        A_exit        = self.station_out_part.area

        F_gross = m_dot * V_exit + (p_exit_static - self.p_ambient) * A_exit

        p_ratio_amb = self.p_ambient / p_total_in
        exp_term = 1.0 - p_ratio_amb ** ((self.station_in.gamma - 1.0) / self.station_in.gamma)
        if exp_term <= 0.0:
            return 0.0
        V_ideal = math.sqrt(2.0 * (self.station_in.gamma / (self.station_in.gamma - 1.0)) * self.station_in.r_gas * T_total_in * exp_term)
        F_ideal = m_dot * V_ideal

        return F_gross / F_ideal if F_ideal > 0.0 else 0.0

    @Attribute
    def thrust_coefficient(self):
        return self.thrust_coefficient_estimation()

    # ------------------------------------------------------------------
    # Geometry — wall_profile (override Duct's designed override point)
    # ------------------------------------------------------------------

    @Attribute
    def profile_points(self):
        """
        Returns profile Point list for wall_profile @Part.
        C-D: 5-point polygon — outer wall straight inlet→outlet (trapezoid),
             inner wall convergent inlet→throat then divergent throat→outlet.
        Convergent: 4-point trapezoid (same as Duct default).
        Logic lives here so wall_profile @Part has a single return.
        """
        if self.is_convergent_divergent:
            return [
                Point(0.0,           self.r_inlet_inner,  0.0),
                Point(0.0,           self.r_inlet_outer,  0.0),
                Point(self.length,   self.r_outlet_outer, 0.0),
                Point(self.length,   self.r_outlet_inner, 0.0),
                Point(self.x_throat, self.r_throat_inner, 0.0),
            ]
        else:
            return [
                Point(0.0,         self.r_inlet_inner,  0.0),
                Point(0.0,         self.r_inlet_outer,  0.0),
                Point(self.length, self.r_outlet_outer, 0.0),
                Point(self.length, self.r_outlet_inner, 0.0),
            ]

    @Part
    def wall_profile(self):
        """
        Closed profile in the local XY plane revolved by Duct.body.
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

        if self.is_convergent_divergent:
            if not 0.0 < self.throat_area_ratio < 1.0:
                warnings.append(
                    f"Nozzle '{self.label}': throat_area_ratio="
                    f"{self.throat_area_ratio:.3f} must be in (0, 1) for C-D geometry."
                )
            if self.Mach_out <= 1.0:
                warnings.append(
                    f"Nozzle '{self.label}': C-D nozzle has Mach_out="
                    f"{self.Mach_out:.2f} — set Mach_out > 1.0 for supersonic operation."
                )
            if self.x_throat >= self.length:
                warnings.append(
                    f"Nozzle '{self.label}': x_throat={self.x_throat:.3f} m must be "
                    f"< length={self.length:.3f} m."
                )

        if not 0.0 < self.p_ambient < self.inflow_conditions.p_total:
            warnings.append(
                f"Nozzle '{self.label}': p_ambient={self.p_ambient:.1f} Pa must be "
                f"between 0 and p_total_in={self.inflow_conditions.p_total:.1f} Pa."
            )

        return warnings


# =============================================================================
# Smoke-test
# =============================================================================
if __name__ == "__main__":
    from parapy.gui import display
    from Flow_station import FlowStation

    turbine_exit = FlowStation(
        station_number = 5,
        fluid_type     = "fuel_gas",
        p_total        = 202650.0,   # 2 × ISA sea-level (low NPR example)
        T_total        = 800.0,
        mass_flow      = 23.5,
        Mach           = 0.35,
    )

    # --- CONVERGENT nozzle --------------------------------------------------
    nozzle_conv = Nozzle(
        inflow_conditions      = turbine_exit,
        is_convergent_divergent = False,
        pressure_ratio         = 0.97,
        isos_efficiency        = 0.96,
        Mach_out               = 0.90,
        station_out            = 7,
        p_ambient              = 101325.0,
        length                 = 0.45,
    )

    # --- CONVERGENT-DIVERGENT nozzle ----------------------------------------
    nozzle_cd = Nozzle(
        inflow_conditions      = turbine_exit,
        is_convergent_divergent = True,
        pressure_ratio         = 0.95,
        isos_efficiency        = 0.95,
        Mach_out               = 1.60,
        station_out            = 7,
        p_ambient              = 101325.0,
        throat_area_ratio      = 0.75,
        length                 = 0.55,
    )

    for label, nozzle in [("CONVERGENT", nozzle_conv), ("C-D", nozzle_cd)]:
        print("=" * 58)
        print(f"NOZZLE SMOKE-TEST — {label}")
        print("=" * 58)

        print(f"\n  [INLET]")
        print(f"    p_total  : {nozzle.station_in.p_total:.2f} Pa")
        print(f"    T_total  : {nozzle.station_in.T_total:.2f} K")
        print(f"    Mach     : {nozzle.station_in.Mach:.3f}")
        print(f"    area     : {nozzle.station_in.area:.5f} m²")

        print(f"\n  [OUTLET]")
        print(f"    p_total  : {nozzle.station_out_part.p_total:.2f} Pa")
        print(f"    T_total  : {nozzle.station_out_part.T_total:.2f} K")
        print(f"    Mach     : {nozzle.station_out_part.Mach:.3f}")
        print(f"    area     : {nozzle.station_out_part.area:.5f} m²")
        print(f"    velocity : {nozzle.station_out_part.v:.2f} m/s")

        print(f"\n  [GEOMETRY]")
        print(f"    r_inlet_inner  : {nozzle.r_inlet_inner:.4f} m")
        print(f"    r_inlet_outer  : {nozzle.r_inlet_outer:.4f} m")
        if nozzle.is_convergent_divergent:
            print(f"    r_throat_inner : {nozzle.r_throat_inner:.4f} m")
            print(f"    area_throat    : {nozzle.area_throat:.5f} m²")
            print(f"    x_throat       : {nozzle.x_throat:.4f} m")
        print(f"    r_outlet_inner : {nozzle.r_outlet_inner:.4f} m")
        print(f"    r_outlet_outer : {nozzle.r_outlet_outer:.4f} m")
        print(f"    volume         : {nozzle.volume:.6f} m³")
        print(f"    weight         : {nozzle.weight:.2f} kg")

        print(f"\n  [AERO]")
        print(f"    is_choked()        : {nozzle.is_choked()}")
        print(f"    pressure_drop      : {nozzle.pressure_drop:.2f} Pa")
        print(f"    thrust_coefficient : {nozzle.thrust_coefficient:.4f}")

        warnings = nozzle.validate()
        if warnings:
            print(f"\n  [VALIDATION WARNINGS]")
            for w in warnings:
                print(f"    ⚠  {w}")
        else:
            print(f"\n  [VALIDATION] all checks passed.")
        print()

    display(nozzle_cd)
