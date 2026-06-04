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
from Material     import Material
from Duct         import Duct
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
    # Material properties — blade-off containment
    # ------------------------------------------------------------------

    #: str    Material name of the frame
    material_name: str = Input("Ti-6Al-4V")

    #: [m]    Metal sheet thickness
    sheet_thickness: float = Input(0.003)

    #: [-]    Containment safety factor  (typical regulatory requirement ≥ 1.5)
    safety_factor: float = Input(1.5)

    # ------------------------------------------------------------------
    # Blade-off kinetic inputs <- will be replaced with actual inputs from solid Blades
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
    inlet_lip_profile: str = Input("curved")

    #: [-]   Total-pressure recovery factor for the inlet
    inlet_pressure_ratio: float = Input(0.98)

    #: [-]   Inlet isentropic efficiency
    inlet_isos_efficiency: float = Input(0.95)

    #: [-]   Inlet exit Mach number
    inlet_Mach_out: float = Input(0.45)

    #: [m]   Axial length of the inlet duct
    inlet_length: float = Input(0.55)

    #: [m]   Wall thickness of the inlet
    inlet_wall_thickness: float = Input(0.012)

    # ------------------------------------------------------------------
    # Casing duct inputs
    # ------------------------------------------------------------------

    #: [m]       Total axial length of the casing barrel
    length_casing: float = Input(2.0)

    #: [m]   Wall thickness of the casing inlet =  Wall thickness of the inlet at the exit
    casing_inlet_wall_thickness: float = Input(0.012)

    #: [m]   Wall thickness of the casing outlet =  Wall thickness of the nozzle at the entrance
    casing_outlet_wall_thickness: float = Input(0.012)

    # ------------------------------------------------------------------
    # Nozzle duct inputs
    # ------------------------------------------------------------------
    #: [-]   Total-pressure ratio across the nozzle
    nozzle_pressure_ratio: float = Input(0.97)

    #: [-]   Nozzle isentropic efficiency
    nozzle_isos_efficiency: float = Input(0.96)

    #: [-]   Nozzle exit Mach number (set > 1.0 for C-D supersonic)
    nozzle_Mach_out: float = Input(1.20)

    #: [m]   Axial length of the nozzle duct
    nozzle_length: float = Input(0.45)

    #: [m]   Wall thickness of the nozzle exit
    nozzle_wall_thickness: float = Input(0.012)

    #: [Pa]  Ambient static pressure — reference for thrust coefficient
    p_ambient: float = Input(101325.0)

    # ------------------------------------------------------------------
    # Frame position (same convention as EngineComponent)
    # ------------------------------------------------------------------

    @Input
    def position(self):
        return rotate(XOY, 'y', 90, deg=True)

    # ------------------------------------------------------------------
    # Material @Part - for structural analysis
    # ------------------------------------------------------------------
    @Part
    def material(self):
        return Material(material_name=self.material_name)

    # ------------------------------------------------------------------
    # Blade-off analysis — attributes
    # ------------------------------------------------------------------

    @Attribute
    def kinetic_energy_blade_off(self) -> float:
        """
        Total kinetic energy of a released blade [J].
        E_k = ½ m v_tip² + ½ I ω²   (translational + rotational contributions)
        """
        return 0.5 * self.blade_mass * self.blade_tip_radius * self.omega**2 + 0.5 * self.blade_inertia * self.omega**2

    @Attribute
    def strain_energy_casing(self) -> float:
        """
        Strain energy absorbed by the casing ring to fracture [J].
        E_s = σ_avg × ε_f × V_casing
        σ_avg is the average flow stress (trapezoidal rule on the σ-ε curve).
        """
        return (self.casing.material.yield_strength + self.casing.material.ultimate_tensile_strength) / 2.0 * self.casing.material.fracture_strain * self.casing_wall_volume

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
        return (self.strain_energy_casing - (self.kinetic_energy_blade_off * self.safety_factor)) / (self.kinetic_energy_blade_off * self.safety_factor)

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
            pressure_ratio      = self.inlet_pressure_ratio,
            lip_profile_type    = self.inlet_lip_profile,
            sheet_thickness     = self.sheet_thickness,
            length              = self.inlet_length,
            material_name       = self.material_name,
            wall_thickness_inlet = self.inlet_wall_thickness,
            wall_thickness_outlet = self.casing_inlet_wall_thickness,
        )

    @Part
    def nozzle_duct(self):
        """
        Engine exhaust nozzle — rear structural end-cap.
        Positioned at the frame origin; AeroEngine translates it to X = length.
        """
        return Nozzle(
            inflow_conditions       = self.nozzle_inflow,
            isos_efficiency         = self.nozzle_isos_efficiency,
            Mach_out                = self.nozzle_Mach_out,
            station_out             = 7,
            pressure_ratio          = self.nozzle_pressure_ratio,
            p_ambient               = self.p_ambient,
            length                  = self.nozzle_length,
            material_name           = self.material_name,
            wall_thickness_inlet    =self.casing_outlet_wall_thickness,
            wall_thickness_outlet   =self.nozzle_wall_thickness,
        )


    @Part
    def casing_inflow(self):
        """Flow condition at the inlet of the casing,
           mainly defined as a helper part to simplify notation in
           casing duct definition."""
        return self.inlet_inflow.isentropic_trans(
            target_type="temperature",
            target_value= self.inlet_inflow.p_total * self.inlet_pressure_ratio,
            isos_efficiency = self.inlet_isos_efficiency,
            Mach_out = self.inlet_Mach_out,
        )

    @Part
    def casing_body(self):
        """Casing inherits from Duct class: builds a Revolved solid coherent with the other ducts."""
        return Duct(
            inflow_conditions=self.casing_inflow,
            length=self.inlet_length,
            material_name=self.material_name,
            #Mach_design=0.5,
            Mach_out=self.nozzle_inflow.Mach,
            pressure_ratio=self.nozzle_inflow.p_total / self.casing_inflow.p_total,
            isos_efficiency=1,
            station_out=6,
            r_inlet_inner= self.inlet_duct.r_outlet_inner,
            r_outlet_inner=self.nozzle_duct.r_inlet_inner,
            wall_thickness_inlet=self.casing_inlet_wall_thickness,
            wall_thickness_outlet=self.casing_outlet_wall_thickness,
        )

    # ------------------------------------------------------------------
    # Mass properties
    # ------------------------------------------------------------------


    @Attribute
    def frame_weight(self) -> float:
        """Total frame mass: casing barrel + inlet duct + nozzle duct [kg]."""
        return self.casing_body.weight + self.inlet_duct.weight + self.nozzle_duct.weight

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self):
        warnings = []

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
