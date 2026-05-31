# =============================================================================
# aero_engine_kbe / engine_frame.py
# =============================================================================
import math
from parapy.core import Base, Input, Attribute, Part
from parapy.geom import (GeomBase, Cylinder, Cone, SubtractedSolid,
                          FusedSolid, translate, Position)

from flow_station import FlowStation

SAFETY_FACTOR = 1.5


# ---------------------------------------------------------------------------
class Duct(GeomBase):
    """
    Axisymmetric duct (inlet or nozzle).
    Built as a frustum (truncated cone) matching inlet/outlet radii.
    X = axial flow direction.
    """

    inlet_station    = Input()
    outlet_station   = Input()
    wall_thickness   = Input(0.005)    # [m]
    material_density = Input(2700.0)   # [kg/m³] aluminium default
    color            = Input('lightblue')

    @Attribute
    def r_inlet_inner(self):
        return self.inlet_station.radius

    @Attribute
    def r_outlet_inner(self):
        return self.outlet_station.radius

    @Attribute
    def axial_length(self):
        """Length ≈ 3 × max inner radius (rule of thumb)."""
        return max(self.r_inlet_inner, self.r_outlet_inner) * 3.0

    @Attribute
    def r_inlet_outer(self):
        return self.r_inlet_inner + self.wall_thickness

    @Attribute
    def r_outlet_outer(self):
        return self.r_outlet_inner + self.wall_thickness

    @Attribute
    def volume_material(self):
        """Frustum wall volume [m³] (outer frustum minus inner frustum)."""
        def frustum_vol(r1, r2, h):
            return math.pi * h / 3.0 * (r1**2 + r1*r2 + r2**2)
        return (frustum_vol(self.r_inlet_outer, self.r_outlet_outer,
                            self.axial_length)
                - frustum_vol(self.r_inlet_inner, self.r_outlet_inner,
                              self.axial_length))

    @Attribute
    def mass(self):
        return self.volume_material * self.material_density

    # ---- 3-D geometry -------------------------------------------------------
    @Part
    def outer_frustum(self):
        """Outer surface cone (Cone with radius1 at inlet end)."""
        return Cone(
            radius1=self.r_inlet_outer,
            radius2=self.r_outlet_outer,
            height=self.axial_length,
            position=self.position,
        )

    @Part
    def inner_frustum(self):
        """Inner bore cone to subtract."""
        return Cone(
            radius1=self.r_inlet_inner,
            radius2=self.r_outlet_inner,
            height=self.axial_length,
            position=self.position,
        )

    @Part
    def solid_wall(self):
        """Hollow frustum duct wall."""
        return SubtractedSolid(
            shape_in=self.outer_frustum,
            tool=self.inner_frustum,
            color=self.color,
        )


# ---------------------------------------------------------------------------
class EngineFrame(GeomBase):
    """
    Outer structural casing + containment analysis.
    Geometry: hollow cylinder at position, length covers the full assembly.
    """

    inner_radius     = Input()
    axial_length     = Input()
    wall_thickness   = Input(0.010)    # [m] – updated by containment logic
    material_density = Input(7900.0)
    youngs_modulus   = Input(200e9)
    yield_stress     = Input(250e6)
    epsilon_1        = Input(0.002)    # smallest failure strain
    blade_mass       = Input(1.5)      # [kg]
    blade_tip_speed  = Input(300.0)    # [m/s]
    blade_omega      = Input(1000.0)   # [rad/s]
    blade_inertia    = Input(0.05)     # [kg·m²]

    @Attribute
    def outer_radius(self):
        return self.inner_radius + self.wall_thickness

    @Attribute
    def casing_volume(self):
        return (math.pi
                * (self.outer_radius**2 - self.inner_radius**2)
                * self.axial_length)

    @Attribute
    def casing_mass(self):
        return self.casing_volume * self.material_density

    @Attribute
    def external_surface_area(self):
        return 2.0 * math.pi * self.outer_radius * self.axial_length

    # ---- Containment --------------------------------------------------------
    @Attribute
    def kinetic_energy_debris(self):
        return (0.5 * self.blade_mass * self.blade_tip_speed**2
                + 0.5 * self.blade_inertia * self.blade_omega**2)

    @Attribute
    def strain_energy_capacity(self):
        """
        Es ≈ (σ_eff² / 2E) × V_casing  (linear-elastic, closed-form).
        # TODO: Non-linear / temperature-dependent variant to verify with Architect.
        """
        sigma_eff = min(self.epsilon_1 * self.youngs_modulus, self.yield_stress)
        return (sigma_eff**2 / (2.0 * self.youngs_modulus)) * self.casing_volume

    @Attribute
    def containment_satisfied(self):
        return self.strain_energy_capacity > (
            self.kinetic_energy_debris * SAFETY_FACTOR)

    @Attribute
    def required_wall_thickness(self):
        """Iterate in 1 mm steps until Es > Ek·SF."""
        sigma_eff   = min(self.epsilon_1 * self.youngs_modulus, self.yield_stress)
        target      = self.kinetic_energy_debris * SAFETY_FACTOR
        t           = self.wall_thickness
        for _ in range(500):
            vol = (math.pi * ((self.inner_radius + t)**2
                              - self.inner_radius**2) * self.axial_length)
            if (sigma_eff**2 / (2.0 * self.youngs_modulus)) * vol >= target:
                return t
            t += 0.001
        print("WARNING: Containment iteration did not converge.")
        return t

    @Attribute
    def safety_margin(self):
        return (self.strain_energy_capacity
                / (self.kinetic_energy_debris * SAFETY_FACTOR) - 1.0)

    # ---- 3-D geometry -------------------------------------------------------
    @Part
    def outer_shell(self):
        return Cylinder(
            radius=self.outer_radius,
            height=self.axial_length,
            position=self.position,
            color='silver',
        )

    @Part
    def inner_bore(self):
        return Cylinder(
            radius=self.inner_radius,
            height=self.axial_length,
            position=self.position,
        )

    @Part
    def casing_solid(self):
        """Hollow annular casing — the main structural solid."""
        return SubtractedSolid(
            shape_in=self.outer_shell,
            tool=self.inner_bore,
            color='silver',
        )