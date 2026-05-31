# combustor.py

from parapy.core import Input, Attribute, Part, child
from parapy.geom import Box, Cylinder, SubtractedSolid, FusedSolid, translate, rotate, VZ
from Flow_station import FlowStation
from EngineComponent import EngineComponent
from math import pi

class Combustor(EngineComponent):
    """
    Combustor component — isobaric heat addition.
    Inherits shared flow logic from EngineComponent.

    Differences from the base class:
        - pressure_ratio is fixed to 1.0 (isobaric process).
        - outlet_flow is passed in directly (TIT-driven), NOT computed
          via isentropic_trans — that @Input is overridden here.
        - Coarse geometry: annular cylinder defined by internal_radius,
          external_radius, and length.
    """

    # ------------------------------------------------------------------
    # Inputs (UML: internal_radius, external_radius, length)
    # ------------------------------------------------------------------

    #: m  — inner radius of the annular combustor casing
    internal_radius: float = Input()

    #: m  — outer radius of the annular combustor casing
    external_radius: float = Input()

    #: m — thickness of the solid walls on both sides of the annulus
    wall_thickness: float = Input(0.05)

    #: m  — axial length of the combustor
    length: float = Input()

    #: kg — density of the material of the combustor
    density: float = Input(8000.0)

    #: -  — combustion efficiency factor
    eta_comb: float = Input(0.99)

    #: J/kg — lower heating value of the fuel
    LHV: float = Input(43.2e6)

    #Geometry details - ribs
    rib_thickness = Input(0.02)
    rib_axial_length = Input(0.05)

    # ------------------------------------------------------------------
    # Override pressure_ratio — isobaric by definition
    # ------------------------------------------------------------------

    pressure_ratio: float = Input(1.0)  # locked to 1.0 for a combustor

    # ------------------------------------------------------------------
    # Override outlet_flow — TIT-driven, passed in from AeroEngine/Spool
    # The base class computes this via isentropic_trans, which is wrong
    # for a combustor. Here we receive the already-computed outlet station.
    # ------------------------------------------------------------------

    #: FlowStation at combustor outlet — must be provided by the caller
    outlet_flow: object = Input()

    # ------------------------------------------------------------------
    # Override station_out_part — rebuild from the overridden outlet_flow
    # ------------------------------------------------------------------

    @Part
    def station_out_part(self):
        """Outlet FlowStation re-parented into this object's tree."""
        return FlowStation(
            station_number = self.station_out,
            fluid_type     = "fuel_gas",        # post-combustion fluid
            p_total        = self.outlet_flow.p_total,
            T_total        = self.outlet_flow.T_total,
            mass_flow      = self.outlet_flow.mass_flow,
            Mach           = self.outlet_flow.Mach,
        )

    # ------------------------------------------------------------------
    # Derived thermodynamic attributes
    # ------------------------------------------------------------------

    @Attribute
    def delta_T_total(self):
        """Total temperature rise across the combustor [K]."""
        return self.station_out_part.T_total - self.station_in.T_total

    @Attribute
    def fuel_air_ratio(self):
        """
        Stoichiometric fuel-to-air ratio estimate [-].
        Uses simplified energy balance:  f = Cp_air * dT / (eta_comb * LHV)
        # TODO: verify LHV and eta_comb values with Architect
        """

        return (self.station_in.cp * self.delta_T_total) / (self.eta_comb * self.LHV)

    # ------------------------------------------------------------------
    # Coarse geometry
    # ------------------------------------------------------------------

    @Attribute
    def inner_bore_radius(self):
        """The hollow bore radius = external_radius - wall_thickness"""
        return self.external_radius - self.wall_thickness

    @Attribute
    def inner_wall_outer_radius(self):
        """Outer radius of the inner wall = internal_radius + wall_thickness"""
        return self.internal_radius + self.wall_thickness

    @Attribute
    def rib_radial_length(self):
        return self.inner_bore_radius - self.inner_wall_outer_radius

    # --- Hidden building blocks: ALL plain Cylinders ---

    @Part
    def _outer_solid(self):
        """Full outer cylinder."""
        return Cylinder(radius=self.external_radius, height=self.length, hidden=True)

    @Part
    def _bore_cylinder(self):
        """Cylinder that carves the main bore (hollow annular gap + inner wall)."""
        return Cylinder(radius=self.inner_bore_radius, height=self.length, hidden=True)

    @Part
    def _inner_wall_solid(self):
        """Cylinder that restores the inner wall material."""
        return Cylinder(radius=self.inner_wall_outer_radius, height=self.length, hidden=True)

    @Part
    def _inner_hollow_cylinder(self):
        """Cylinder that carves the inner bore."""
        return Cylinder(radius=self.internal_radius, height=self.length, hidden=True)

    # --- Assembly ---

    @Part
    def _outer_wall(self):
        """Outer annular wall = outer_solid minus the bore."""
        return SubtractedSolid(
            shape_in=self._outer_solid,
            tool=self._bore_cylinder,
            hidden=True,
        )

    @Part
    def _inner_wall(self):
        """Inner annular wall = inner_wall_solid minus the inner bore."""
        return SubtractedSolid(
            shape_in=self._inner_wall_solid,
            tool=self._inner_hollow_cylinder,
            hidden=True,
        )

    @Part
    def _ribs(self):
        return Box(
            quantify=4,
            width=self.external_radius - self.internal_radius,  # along local X = RADIAL
            length=self.rib_thickness,  # along local Y = circumferential (thin)
            height=self.rib_axial_length,  # along local Z = axial
            position=translate(
                rotate(self.position, 'z', pi / 2 * child.index),
                'x', self.internal_radius,  # radial start at inner bore
                'z', self.length * 0.25,  # axial offset
            ),
            hidden=True,
        )

    @Part
    def body(self):
        return FusedSolid(
            shape_in=self._outer_wall,
            tool=[self._inner_wall,
                  self._ribs[0], self._ribs[1],
                  self._ribs[2], self._ribs[3]],
            color=(181, 166, 66),
        )

    # ------------------------------------------------------------------
    # Validation — extends base class checks
    # ------------------------------------------------------------------

    def validate(self):
        warnings = super().validate()
        if self.internal_radius >= self.external_radius:
            warnings.append(
                f"Combustor: internal_radius ({self.internal_radius}) "
                f"must be smaller than external_radius ({self.external_radius})."
            )
        if self.length <= 0.0:
            warnings.append("Combustor: length must be > 0.")
        return warnings

from parapy.gui import display

if __name__ == '__main__':

    inlet = FlowStation(
        station_number = 3,
        fluid_type     = "air",
        p_total        = 101325.0 * 8.0,   # Pa  — post-compressor
        T_total        = 580.0,             # K   — post-compressor
        mass_flow      = 22.9,
        Mach           = 0.3,
    )

    # Outlet is TIT-driven — built externally and passed in
    outlet = FlowStation(
        station_number = 4,
        fluid_type     = "fuel_gas",
        p_total        = 101325.0 * 8.0,   # Pa  — isobaric
        T_total        = 1600.0,            # K   — TIT
        mass_flow      = 23.3,             # kg/s — slightly higher (fuel added)
        Mach           = 0.2,
    )

    comb = Combustor(
        inflow_conditions = inlet,
        outlet_flow       = outlet,
        station_out       = 4,
        Mach_out          = 0.2,
        internal_radius   = 0.15,
        external_radius   = 0.30,
        length            = 0.40,
    )

    print("=== COMBUSTOR ===")
    print(f"  T_total_in   [K]  : {comb.station_in.T_total:.2f}")
    print(f"  T_total_out  [K]  : {comb.station_out_part.T_total:.2f}")
    print(f"  delta_T      [K]  : {comb.delta_T_total:.2f}")
    print(f"  fuel/air ratio[-] : {comb.fuel_air_ratio:.4f}")
    print(f"  volume       [m³] : {comb.volume}")
    print(f"  weight       [kg] : {comb.weight}")
    print(f"  area_in      [m²] : {comb.area_in:.4f}")
    print(f"  area_out     [m²] : {comb.area_out:.4f}")

    print("\n=== VALIDATION ===")
    print(f"  Warnings: {comb.validate() or 'none'}")

    display(comb)