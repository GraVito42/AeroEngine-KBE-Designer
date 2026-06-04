# engine_frame.py
"""
EngineFrame — structural engine casing shell + blade-off containment analysis.

Class architecture position:
  AeroEngine
  └── EngineFrame          ← this class
      ├── Inlet            (inherits Duct → EngineComponent)
      └── Nozzle           (inherits Duct → EngineComponent)

Geometry:
  casing_body  : annular cylindrical shell — rectangular wall profile
                 revolved 360° around the local X (axial) axis.
  inlet_duct   : Inlet child — front end-cap.
  nozzle_duct  : Nozzle child — rear end-cap.

Axis convention (same as EngineComponent):
  position = rotate(XOY, 'y', 90, deg=True)
  local X  = engine axial direction
  local Y  = radial direction
  Profiles live in the local XY plane.

Blade-off containment (CS-E §25.903(d) approach):
  Containment check:  E_s  >  E_k × safety_factor
    E_k = ½ m v²_tip + ½ I ω²      [J] kinetic energy of released blade
    E_s = σ_avg × ε_f × V_casing   [J] strain energy absorbed to fracture
    σ_avg = (yield_strength + ult_strength) / 2  (trapezoidal σ-ε approximation)
"""

import math

from parapy.core  import Input, Attribute, Part
from parapy.geom  import (
    GeomBase,
    Point, Polygon, RevolvedSolid,
    XOY, rotate,
)

from Flow_station import FlowStation
from Inlet        import Inlet
from Nozzle       import Nozzle


class EngineFrame(GeomBase):
    """
    Structural engine frame: cylindrical casing barrel with inlet and nozzle
    end-caps.  Also performs blade-off containment checks.
    """

    # ------------------------------------------------------------------
    # Thermodynamic inflow conditions — passed down to child ducts
    # ------------------------------------------------------------------

    #: FlowStation at station 1 (inlet highlight face)
    inlet_inflow: object = Input()

    #: FlowStation at station 6 (nozzle inlet = turbine exit)
    nozzle_inflow: object = Input()

    # ------------------------------------------------------------------
    # Main casing barrel geometry
    # ------------------------------------------------------------------

    #: [m]       Total axial length of the casing barrel
    length: float = Input(2.0)

    #: [m]       Outer radius of the cylindrical casing
    r_casing: float = Input(0.35)

    #: [m]       Casing wall thickness
    wall_thickness: float = Input(0.012)

    #: [kg/m³]   Casing material density  (default: Ti-6Al-4V)
    density: float = Input(4430.0)

    # ------------------------------------------------------------------
    # Material properties — blade-off containment
    # ------------------------------------------------------------------

    #: [Pa]   0.2 % proof / yield strength of casing material
    yield_strength: float = Input(880e6)

    #: [Pa]   Ultimate tensile strength
    ult_strength: float = Input(950e6)

    #: [-]    Engineering fracture strain (elongation at fracture)
    fracture_strain: float = Input(0.14)

    #: [-]    Containment safety factor  (typical regulatory requirement ≥ 1.5)
    safety_factor: float = Input(1.5)

    # ------------------------------------------------------------------
    # Blade-off kinetic inputs
    # ------------------------------------------------------------------

    #: [kg]      Mass of one released blade
    blade_mass: float = Input(1.5)

    #: [m]       Blade tip radius (worst-case = casing inner radius)
    blade_tip_radius: float = Input(0.28)

    #: [rad/s]   Rotor angular velocity at blade-off event
    omega: float = Input(1200.0)

    #: [kg·m²]  Blade moment of inertia about rotor spin axis
    blade_inertia: float = Input(0.02)

    # ------------------------------------------------------------------
    # Inlet duct inputs
    # ------------------------------------------------------------------

    #: str   Inlet highlight contour: 'bellmouth' | 'straight'
    inlet_highlight_profile: str = Input("curved")

    #: [-]   Total-pressure recovery factor for the inlet
    inlet_ram_recovery_factor: float = Input(0.98)

    #: [-]   Inlet isentropic efficiency
    inlet_isos_efficiency: float = Input(0.95)

    #: [-]   Inlet exit Mach number
    inlet_Mach_out: float = Input(0.45)

    #: [m]   Axial length of the ducts
    inlet_length: float = Input(0.55)
    nozzle_length: float = Input(0.60)

    @Input
    def inlet_r_inner(self) -> float:
        """Inner radius at the inlet highlight face [m]."""
        return self.r_casing - self.wall_thickness

    @Input
    def inlet_r_outer(self) -> float:
        """Outer radius at the inlet highlight face [m]."""
        return self.r_casing

    @Input
    def inlet_r_outlet_inner(self) -> float:
        """Inner radius at the inlet duct exit (= compressor face) [m]."""
        return self.r_casing - self.wall_thickness

    @Input
    def inlet_r_outlet_outer(self) -> float:
        """Outer radius at the inlet duct exit [m]."""
        return self.r_casing

    # ------------------------------------------------------------------
    # Nozzle duct inputs
    # ------------------------------------------------------------------

    #: bool  True → convergent-divergent nozzle geometry
    nozzle_is_cd: bool = Input(False)

    #: [-]   Total-pressure ratio across the nozzle
    nozzle_pressure_ratio: float = Input(0.97)

    #: [-]   Nozzle isentropic efficiency
    nozzle_isos_efficiency: float = Input(0.96)

    #: [-]   Nozzle exit Mach number (set > 1.0 for C-D supersonic)
    nozzle_Mach_out: float = Input(0.90)

    #: [m]   Axial length of the nozzle duct
    nozzle_length: float = Input(0.45)

    #: [Pa]  Ambient static pressure — reference for thrust coefficient
    nozzle_p_ambient: float = Input(101325.0)

    #: [-]   C-D throat-to-inlet area ratio (only active when nozzle_is_cd=True)
    nozzle_throat_area_ratio: float = Input(0.8)

    @Input
    def nozzle_r_inlet_inner(self) -> float:
        """Nozzle inlet inner radius [m]."""
        return self.r_casing - self.wall_thickness

    @Input
    def nozzle_r_inlet_outer(self) -> float:
        """Nozzle inlet outer radius [m]."""
        return self.r_casing

    @Input
    def nozzle_r_outlet_inner(self) -> float:
        """Nozzle exit inner radius [m]. Default: 15 % convergence from inlet."""
        return (self.r_casing - self.wall_thickness) * 0.85

    @Input
    def nozzle_r_outlet_outer(self) -> float:
        """Nozzle exit outer radius [m]."""
        return self.nozzle_r_outlet_inner + self.wall_thickness

    # ------------------------------------------------------------------
    # Frame position (same convention as EngineComponent)
    # ------------------------------------------------------------------

    @Input
    def position(self):
        return rotate(XOY, 'y', 90, deg=True)

    # ------------------------------------------------------------------
    # Blade-off analysis — attributes
    # ------------------------------------------------------------------

    @Attribute
    def casing_inner_radius(self) -> float:
        """Inner radius of the casing barrel [m]."""
        return self.r_casing - self.wall_thickness

    @Attribute
    def casing_wall_volume(self) -> float:
        """Volume of the annular casing shell [m³]."""
        return math.pi * (self.r_casing**2 - self.casing_inner_radius**2) * self.length

    @Attribute
    def kinetic_energy_blade_off(self) -> float:
        """
        Total kinetic energy of a released blade [J].
        E_k = ½ m v_tip² + ½ I ω²   (translational + rotational contributions)
        """
        v_tip = self.blade_tip_radius * self.omega
        return 0.5 * self.blade_mass * v_tip**2 + 0.5 * self.blade_inertia * self.omega**2

    @Attribute
    def strain_energy_casing(self) -> float:
        """
        Strain energy absorbed by the casing ring to fracture [J].
        E_s = σ_avg × ε_f × V_casing
        σ_avg is the average flow stress (trapezoidal rule on the σ-ε curve).
        """
        sigma_avg = (self.yield_strength + self.ult_strength) / 2.0
        return sigma_avg * self.fracture_strain * self.casing_wall_volume

    def is_contained(self) -> bool:
        """True when the casing can absorb a blade-off event with the required margin."""
        return self.strain_energy_casing > self.kinetic_energy_blade_off * self.safety_factor

    @Attribute
    def containment_margin(self) -> float:
        """
        Fractional containment margin.
          > 0  →  casing contains the blade (positive margin)
          ≤ 0  →  casing fails containment
        """
        required = self.kinetic_energy_blade_off * self.safety_factor
        return (self.strain_energy_casing - required) / required

    # ------------------------------------------------------------------
    # Mass properties
    # ------------------------------------------------------------------

    @Attribute
    def casing_weight(self) -> float:
        """Main casing barrel mass [kg]."""
        return self.casing_wall_volume * self.density

    @Attribute
    def total_weight(self) -> float:
        """Total frame mass: casing barrel + inlet duct + nozzle duct [kg]."""
        return self.casing_weight + self.inlet_duct.weight + self.nozzle_duct.weight

    # ------------------------------------------------------------------
    # Geometry — Part 1: casing wall profile
    # ------------------------------------------------------------------

    @Attribute
    def casing_profile_points(self):
        """
        Rectangular wall profile for the main casing barrel in local XY plane.
        X = axial, Y = radial.
        """
        r_i = self.casing_inner_radius
        r_o = self.r_casing
        return [
            Point(0.0,         r_i, 0.0),
            Point(0.0,         r_o, 0.0),
            Point(self.length, r_o, 0.0),
            Point(self.length, r_i, 0.0),
        ]

    @Part
    def casing_wall_profile(self):
        return Polygon(
            points=self.casing_profile_points,
            hidden=True,
        )

    # ------------------------------------------------------------------
    # Geometry — Part 2: casing body (shape-agnostic, reads casing_wall_profile)
    # ------------------------------------------------------------------

    @Part
    def casing_body(self):
        """Annular cylindrical shell — revolved 360° around local X (axial)."""
        return RevolvedSolid(
            built_from = self.casing_wall_profile,
            center     = Point(0.0, 0.0, 0.0),
            direction  = (1.0, 0.0, 0.0),
            angle      = 2 * math.pi,
            color      = (120, 130, 140),
        )

    # ------------------------------------------------------------------
    # Child ducts — end-caps of the structural frame
    # ------------------------------------------------------------------

    @Part
    def inlet_duct(self):
        """
        Engine inlet — front structural end-cap.
        Positioned at the frame origin (axial X = 0).
        Assembly-level translation is handled by AeroEngine.
        """
        return Inlet(
            inflow_conditions   = self.inlet_inflow,
            isos_efficiency     = self.inlet_isos_efficiency,
            Mach_out            = self.inlet_Mach_out,
            station_out         = 2,
            ram_recovery_factor = self.inlet_ram_recovery_factor,
            highlight_profile   = self.inlet_highlight_profile,
            length              = self.inlet_length,
            density             = self.density,
            r_inlet_inner       = self.inlet_r_inner,
            r_inlet_outer       = self.inlet_r_outer,
            r_outlet_inner      = self.inlet_r_outlet_inner,
            r_outlet_outer      = self.inlet_r_outlet_outer,
        )

    @Part
    def nozzle_duct(self):
        """
        Engine exhaust nozzle — rear structural end-cap.
        Positioned at the frame origin; AeroEngine translates it to X = length.
        """
        return Nozzle(
            inflow_conditions       = self.nozzle_inflow,
            is_convergent_divergent = self.nozzle_is_cd,
            pressure_ratio          = self.nozzle_pressure_ratio,
            isos_efficiency         = self.nozzle_isos_efficiency,
            Mach_out                = self.nozzle_Mach_out,
            station_out             = 7,
            p_ambient               = self.nozzle_p_ambient,
            throat_area_ratio       = self.nozzle_throat_area_ratio,
            length                  = self.nozzle_length,
            density                 = self.density,
            r_inlet_inner           = self.nozzle_r_inlet_inner,
            r_inlet_outer           = self.nozzle_r_inlet_outer,
            r_outlet_inner          = self.nozzle_r_outlet_inner,
            r_outlet_outer          = self.nozzle_r_outlet_outer,
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self):
        warnings = []

        if not (0.0 < self.wall_thickness < self.r_casing):
            warnings.append(
                f"EngineFrame: wall_thickness={self.wall_thickness:.4f} m must be "
                f"in (0, r_casing={self.r_casing:.4f} m)."
            )

        if self.safety_factor < 1.0:
            warnings.append(
                f"EngineFrame: safety_factor={self.safety_factor:.2f} is below 1.0 "
                f"— no structural margin over the blade kinetic energy."
            )

        if self.yield_strength >= self.ult_strength:
            warnings.append(
                f"EngineFrame: yield_strength={self.yield_strength/1e6:.1f} MPa "
                f">= ult_strength={self.ult_strength/1e6:.1f} MPa — check material data."
            )

        if not (0.0 < self.fracture_strain <= 1.0):
            warnings.append(
                f"EngineFrame: fracture_strain={self.fracture_strain:.3f} outside (0, 1]."
            )

        if not self.is_contained():
            warnings.append(
                f"EngineFrame: blade-off NOT contained. "
                f"E_k×SF = {self.kinetic_energy_blade_off * self.safety_factor:.1f} J  "
                f"> E_s = {self.strain_energy_casing:.1f} J. "
                f"Increase wall_thickness or reduce omega / blade_mass."
            )

        warnings += self.inlet_duct.validate()
        warnings += self.nozzle_duct.validate()

        return warnings


# =============================================================================
# Smoke-test
# =============================================================================
if __name__ == "__main__":
    from parapy.gui import display

    station_1 = FlowStation(
        station_number = 1,
        fluid_type     = "air",
        p_total        = 101325.0,
        T_total        = 288.15,
        mass_flow      = 22.9,
        Mach           = 0.25,
    )

    station_6 = FlowStation(
        station_number = 6,
        fluid_type     = "fuel_gas",
        p_total        = 202650.0,
        T_total        = 780.0,
        mass_flow      = 23.5,
        Mach           = 0.35,
    )

    frame = EngineFrame(
        inlet_inflow   = station_1,
        nozzle_inflow  = station_6,
        length         = 2.0,
        r_casing       = 0.35,
        wall_thickness = 0.015,
        # blade-off: moderately loaded fan blade
        blade_mass       = 0.35,
        blade_tip_radius = 0.30,
        omega            = 1100.0,
        blade_inertia    = 0.025,
    )

    print("=" * 60)
    print("ENGINE FRAME SMOKE-TEST")
    print("=" * 60)

    print("\n  [CASING GEOMETRY]")
    print(f"    r_casing          : {frame.r_casing:.4f} m")
    print(f"    casing_inner_r    : {frame.casing_inner_radius:.4f} m")
    print(f"    wall_thickness    : {frame.wall_thickness:.4f} m")
    print(f"    casing_wall_vol   : {frame.casing_wall_volume:.5f} m³")
    print(f"    casing_weight     : {frame.casing_weight:.2f} kg")
    print(f"    total_weight      : {frame.total_weight:.2f} kg")

    print("\n  [BLADE-OFF ANALYSIS]")
    print(f"    omega             : {frame.omega:.1f} rad/s")
    print(f"    v_tip             : {frame.blade_tip_radius * frame.omega:.2f} m/s")
    print(f"    E_k               : {frame.kinetic_energy_blade_off:.1f} J")
    print(f"    E_s               : {frame.strain_energy_casing:.1f} J")
    print(f"    E_k × SF          : {frame.kinetic_energy_blade_off * frame.safety_factor:.1f} J")
    print(f"    containment_margin: {frame.containment_margin:.3f}")
    print(f"    is_contained()    : {frame.is_contained()}")

    print("\n  [INLET DUCT]")
    print(f"    p_total in        : {frame.inlet_duct.station_in.p_total:.2f} Pa")
    print(f"    p_total out       : {frame.inlet_duct.station_out_part.p_total:.2f} Pa")
    print(f"    weight            : {frame.inlet_duct.weight:.2f} kg")
    print(f"    is_choked()       : {frame.inlet_duct.is_choked()}")

    print("\n  [NOZZLE DUCT]")
    print(f"    p_total in        : {frame.nozzle_duct.station_in.p_total:.2f} Pa")
    print(f"    p_total out       : {frame.nozzle_duct.station_out_part.p_total:.2f} Pa")
    print(f"    thrust_coefficient: {frame.nozzle_duct.thrust_coefficient:.4f}")
    print(f"    weight            : {frame.nozzle_duct.weight:.2f} kg")

    warnings = frame.validate()
    if warnings:
        print("\n  [VALIDATION WARNINGS]")
        for w in warnings:
            print(f"    ⚠  {w}")
    else:
        print("\n  [VALIDATION] all checks passed.")

    display(frame)
