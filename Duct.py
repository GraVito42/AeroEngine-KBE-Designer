# duct.py
"""
Duct – parametric annular flow-path component.

Axis convention (inherited from EngineComponent):
  EngineComponent.position = rotate(XOY, 'y', 90 deg)
  → local X axis  = global Z = engine axial direction
  → local Y axis  = global Y = radial direction

Profile points in the local XY plane (X=axial, Y=radial):
  P1  (X=0,      Y=r_inlet_inner)   inlet  inner edge
  P2  (X=0,      Y=r_inlet_outer)   inlet  outer edge
  P3  (X=length, Y=r_outlet_outer)  outlet outer edge
  P4  (X=length, Y=r_outlet_inner)  outlet inner edge

Revolution axis = local X (axial), full 360 deg → annular solid.

#   If the duct appears on its side, change direction=(1,0,0) to (0,1,0).
"""

import math
from parapy.core import Input, Attribute, Part
from parapy.geom import (
    GeomBase,
    Point, Polygon, RevolvedSolid, RevolvedSurface, LineSegment,
    XOY,
)

from Flow_station    import FlowStation
from EngineComponent import EngineComponent


class Duct(EngineComponent):
    """
    Generic parametric annular duct.

    Geometry:  trapezoidal wire profile revolved 360 deg around the local
               axial axis (X in the EngineComponent frame).
    Aero:      outlet_flow respects choking — if A_min <= A*, exit is
               capped at Mach 1.0.
    Modular:   `wall_profile` is the designed override point for subclasses.
               `body` is shape-agnostic; volume/weight are inherited from
               EngineComponent automatically.
    """

    # ------------------------------------------------------------------
    # Inputs
    # ------------------------------------------------------------------

    #: [-]      Design Mach number for the duct
    Mach_design: float = Input(0.5)

    #: [m]      Sheet-metal wallt thickness for the surface-based weight model
    sheet_thickness: float = Input(0.003)

    #: -        outlet pressure ratio choked vs unchoked
    choking_losses: float = Input(0.99)

    #: [m]  Axial offset from the global origin — set by parent assembly.
    x_offset: float = Input(0.0)

    # ------------------------------------------------------------------
    # Derived thermodynamic attributes
    # ------------------------------------------------------------------

    @Attribute
    def pressure_drop(self):
        """Absolute total-pressure loss across the duct [Pa]."""
        return (1.0 - self.pressure_ratio) * self.station_in.p_total

    @Input
    def wall_thickness_inlet(self) -> float:
        """Wall thickness at inlet cross-section [m]."""
        return 0.1*self.r_inlet_inner

    @Input
    def wall_thickness_outlet(self) -> float:
        """Wall thickness at outlet cross-section [m]."""
        return 0.1*self.r_outlet_inner

    # ------------------------------------------------------------------
    # Boundary-constraint radii  (settable @Input, default from flow area)
    # Override area_in / area_out from EngineComponent to shift the whole
    # chain; or pin a radius directly for CFD-corrected geometry.
    # ------------------------------------------------------------------

    @Input
    def r_inlet_inner(self) -> float:
        """Inner radius at inlet [m]."""
        return math.sqrt(self.area_in / math.pi)

    @Input
    def r_outlet_inner(self) -> float:
        """Inner radius at outlet [m]."""
        return math.sqrt(self.area_out / math.pi)

    @Attribute
    def r_inlet_outer(self) -> float:
        """Outer radius at inlet [m]. Default: 10% over inner."""
        return self.r_inlet_inner + self.wall_thickness_inlet

    @Attribute
    def r_outlet_outer(self) -> float:
        """Outer radius at outlet [m]. Default: 10% over inner."""
        return self.r_outlet_inner + self.wall_thickness_outlet

    # ------------------------------------------------------------------
    # Aerodynamic logic — geometry-driven choking
    # ------------------------------------------------------------------

    def is_choked(self) -> bool:
        """
        Return True when A_min <= A* (geometry forces sonic flow).

        A*    : critical area to pass mass_flow at Mach 1.0 given inlet
                total conditions (ideal isentropic reference, eta=1.0).
        A_min : min of inlet area and raw outlet area. Raw outlet is
                computed directly from inflow_conditions — NOT through
                station_out_part — to avoid a circular reference.

        Subclass override note (Nozzle):
            Replace this method and compute A_min from the physical
            throat area of the C-D profile instead.
        """

        a_star = self.inflow_conditions.isentropic_trans(
            target_type  = "temperature",
            target_value = self.inflow_conditions.p_total * self.pressure_ratio,
            eta          = 1.0,
            Mach_out     = 1.0,
        ).area

        raw_outlet = self.inflow_conditions.isentropic_trans(
            target_type  = "temperature",
            target_value = self.inflow_conditions.p_total * self.pressure_ratio,
            eta          = self.isos_efficiency,
            Mach_out     = self.Mach_out,
        )
        a_min = min(self.station_in.area, raw_outlet.area)

        return a_min <= a_star

    # ------------------------------------------------------------------
    # Override outlet_flow (EngineComponent @Input)
    # ------------------------------------------------------------------

    @Input
    def outlet_flow(self):
        """
        Conditional outlet station:
          Choked   → exit forced to Mach 1.0.
          Subsonic → standard pressure-ratio path at design Mach_out.
        """
        if self.is_choked():
            #in chocked conditions,
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
    # Geometry — Part 1: wall_profile  (DESIGNED OVERRIDE POINT)
    # ------------------------------------------------------------------

    @Part
    def wall_profile(self):
        """
        Closed trapezoidal wire in the local XY plane.

        Coordinate convention (matches EngineComponent rotated frame):
          X = axial (engine longitudinal)
          Y = radial

        Points:
          P1  (X=0,      Y=r_inlet_inner)
          P2  (X=0,      Y=r_inlet_outer)
          P3  (X=length, Y=r_outlet_outer)
          P4  (X=length, Y=r_outlet_inner)
          Polygon closes P4 → P1 automatically.

        Subclass override contract:
          Return any closed wire whose first point lies on
          (X=0, Y=r_inlet_inner) and last point on
          (X=length, Y=r_outlet_inner) to preserve C0 continuity
          with adjacent components.
        """
        return Polygon(
            points=[
                Point(self.x_offset, self.r_inlet_inner, 0.0),
                Point(self.x_offset, self.r_inlet_outer, 0.0),
                Point(self.x_offset + self.length, self.r_outlet_outer, 0.0),
                Point(self.x_offset + self.length, self.r_outlet_inner, 0.0),
            ],
            hidden=True,
        )

    # ------------------------------------------------------------------
    # Geometry — Part 2: wall_surface  (shape-agnostic, never overridden)
    # It is used to perform a surface-based weight estimation
    # ------------------------------------------------------------------

    @Part
    def outer_meridian(self):
        """
        Single-edge line from inlet-outer to outlet-outer.
        This is the wetted outer wall only — used as the basis curve
        for RevolvedSurface, which requires a single-edge wire.
        """
        return LineSegment(
            start=Point(self.x_offset, self.r_inlet_outer, 0.0),
            end=Point(self.x_offset + self.length, self.r_outlet_outer, 0.0),
            hidden=True,
        )

    @Part
    def wall_surface(self):
        """
        Revolved outer-wall surface for sheet-metal weight estimation.
        Uses outer_meridian (single LineSegment) — avoids MultiEdgedWire error.
        """
        return RevolvedSurface(
            basis_curve=self.outer_meridian,
            center=Point(0.0, 0.0, 0.0),
            direction=(1.0, 0.0, 0.0),
            angle=2 * math.pi,
            hidden=True,
        )
    @Attribute
    def weight(self) -> float:
        """
        Sheet-metal weight: wetted wall area * sheet thickness * density.
        Overrides EngineComponent.weight (which used solid volume * density).
        """
        return self.wall_surface.area * self.sheet_thickness * self.material.density

    # ------------------------------------------------------------------
    # Geometry — Part 3: body  (shape-agnostic, never overridden)
    # ------------------------------------------------------------------

    @Part
    def body(self):
        """
        Annular solid wall — revolve wall_profile 360 deg around
        the local X axis (axial direction in the EngineComponent frame).

        Completely shape-agnostic: reads only self.wall_profile.
        Subclasses inherit volume and weight for free.
        """
        return RevolvedSolid(
            built_from=self.wall_profile,
            center=Point(0.0, 0.0, 0.0),
            direction=(1.0, 0.0, 0.0),
            angle=2 * math.pi,
            color=self.material.color,
        )

    # ----------------------------------------------------------------------------------
    # Geometry - Part4 volume override — total swept envelope, NOT the solid-wall volume
    # Kernel-measured (envelope_solid) so it is exact for any outer shape, unlike an analytic
    # frustum formula. Summed components = EngineFrame.
    # ----------------------------------------------------------------------------------

    @Attribute
    def outer_envelope_points(self):
        """Outer-wall meridian points only, inlet→outlet, for the envelope solid. Duct base: straight outer wall P2→P3. Subclasses (Inlet) override with their curved outer contour."""
        return [
            Point(self.x_offset, self.r_inlet_outer, 0.0),
            Point(self.x_offset + self.length, self.r_outlet_outer, 0.0),
        ]

    @Part
    def envelope_profile(self):
        """Closed wire: outer wall + closure down to the axis (y=0) at both ends. Revolved, this is the full swept envelope of the duct (bore included)."""
        return Polygon(
            points=self.outer_envelope_points + [
                Point(self.x_offset + self.length, 0.0, 0.0),
                Point(self.x_offset, 0.0, 0.0),
            ],
            hidden=True,
        )

    @Part
    def envelope_solid(self):
        """Full envelope solid (outer contour revolved to the axis). Its volume is the total swept ingombro, exact for any outer-wall shape. NOT shown."""
        return RevolvedSolid(
            built_from=self.envelope_profile,
            center=Point(0.0, 0.0, 0.0),
            direction=(1.0, 0.0, 0.0),
            angle=2 * math.pi,
            hidden=True,
        )

    @Attribute
    def volume(self) -> float:
        """Total axisymmetric envelope volume (bore included), measured by the kernel. Overrides EngineComponent.volume so summed component volumes match the EngineFrame envelope."""
        return self.envelope_solid.volume

    # ------------------------------------------------------------------
    # Validation  (extends EngineComponent.validate)
    # ------------------------------------------------------------------

    def validate(self):
        warnings = super().validate()

        if not (0.0 < self.pressure_ratio <= 1.0):
            warnings.append(
                f"Duct '{self.label}': pressure_ratio={self.pressure_ratio:.4f} "
                f"is outside the valid range (0, 1]."
            )

        if self.wall_thickness_inlet <= 0.0:
            warnings.append(
                f"Duct '{self.label}': wall_thickness_inlet={self.wall_thickness_inlet:.4f} "
                f"must be > 0 (r_inlet_outer must exceed r_inlet_inner)."
            )
        if self.wall_thickness_outlet <= 0.0:
            warnings.append(
                f"Duct '{self.label}': wall_thickness_outlet={self.wall_thickness_outlet:.4f} "
                f"must be > 0 (r_outlet_outer must exceed r_outlet_inner)."
            )

        return warnings


# =============================================================================
# Smoke-test
# =============================================================================
if __name__ == "__main__":
    from parapy.gui import display

    inlet = FlowStation(
        station_number = 2,
        fluid_type     = "air",
        p_total        = 101325.0,
        T_total        = 288.15,
        mass_flow      = 22.9,
        Mach           = 0.5,
    )

    # --- CONVERGENT duct: inner radius shrinks toward outlet ----------------
    duct_conv = Duct(
        inflow_conditions=inlet,
        material_name="Al-2024-T3",
        Mach_design=0.5,
        Mach_out=0.45,
        pressure_ratio=0.98,
        isos_efficiency=0.92,
        station_out=3,
        r_inlet_inner=0.15,
        r_outlet_inner=0.08,
    )

    duct_div = Duct(
        inflow_conditions=inlet,
        length = 0.1,
        material_name= "Al-2024-T3",
        Mach_design=0.5,
        Mach_out=0.45,
        pressure_ratio=0.98,
        isos_efficiency=0.92,
        station_out=3,
    )

    for label, duct in [("CONVERGENT", duct_conv), ("DIVERGENT", duct_div)]:
        print("=" * 55)
        print(f"DUCT SMOKE-TEST — {label}")
        print("=" * 55)

        print(f"\n  [INLET]")
        print(f"    p_total  : {duct.station_in.p_total:.2f} Pa")
        print(f"    T_total  : {duct.station_in.T_total:.2f} K")
        print(f"    Mach     : {duct.station_in.Mach:.3f}")
        print(f"    area     : {duct.station_in.area:.5f} m²")

        print(f"\n  [OUTLET]")
        print(f"    p_total  : {duct.station_out_part.p_total:.2f} Pa")
        print(f"    T_total  : {duct.station_out_part.T_total:.2f} K")
        print(f"    Mach     : {duct.station_out_part.Mach:.3f}")
        print(f"    area     : {duct.station_out_part.area:.5f} m²")

        print(f"\n  [GEOMETRY]")
        print(f"    r_inlet_inner  : {duct.r_inlet_inner:.4f} m")
        print(f"    r_inlet_outer  : {duct.r_inlet_outer:.4f} m")
        print(f"    r_outlet_inner : {duct.r_outlet_inner:.4f} m")
        print(f"    r_outlet_outer : {duct.r_outlet_outer:.4f} m")
        print(f"    volume         : {duct.volume:.6f} m³")
        print(f"    weight         : {duct.weight:.2f} kg")

        print(f"\n  [AERO]")
        print(f"    is_choked()    : {duct.is_choked()}")
        print(f"    pressure_drop  : {duct.pressure_drop:.2f} Pa")

        warnings = duct.validate()
        if warnings:
            print(f"\n  [VALIDATION WARNINGS]")
            for w in warnings:
                print(f"    ⚠  {w}")
        else:
            print(f"\n  [VALIDATION] all checks passed.")

        print()

    display(duct_div)