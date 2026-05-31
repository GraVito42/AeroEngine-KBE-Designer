# =============================================================================
# aero_engine_kbe / engine.py
# =============================================================================
import math
import openpyxl
from parapy.core import Base, Input, Attribute, Part
from parapy.geom import (GeomBase, Cylinder, SubtractedSolid,
                          FusedSolid, translate, Position)

from flow_station  import FlowStation
from turbomachine  import Turbomachine
from engine_frame  import EngineFrame, Duct

GAMMA = 1.4
R_AIR = 287.05


# ---------------------------------------------------------------------------
class Combustor(GeomBase):
    """
    Annular combustor chamber.
    Positioned at self.position; hollow cylinder coloured yellow.
    X = axial flow direction.
    """

    outer_radius     = Input()       # [m]
    inner_radius     = Input()       # [m]  ~ compressor tip radius
    length           = Input(0.30)   # [m]
    wall_thickness   = Input(0.008)  # [m]
    material_density = Input(8220.0) # [kg/m³] Inconel 718

    @Attribute
    def volume_wall(self):
        return (math.pi
                * (self.outer_radius**2 - self.inner_radius**2)
                * self.length)

    @Attribute
    def mass(self):
        return self.volume_wall * self.material_density

    # ---- 3-D geometry -------------------------------------------------------
    @Part
    def outer_cyl(self):
        return Cylinder(
            radius=self.outer_radius,
            height=self.length,
            position=self.position,
            color='yellow',
        )

    @Part
    def inner_bore(self):
        return Cylinder(
            radius=self.inner_radius,
            height=self.length,
            position=self.position,
        )

    @Part
    def solid(self):
        """Hollow annular combustor solid."""
        return SubtractedSolid(
            shape_in=self.outer_cyl,
            tool=self.inner_bore,
            color='yellow',
        )


# ---------------------------------------------------------------------------
class Spool(GeomBase):
    """
    Hollow drive shaft.
    Positioned at self.position; extends along X for self.length.
    """

    outer_radius     = Input(0.05)
    inner_radius     = Input(0.03)
    length           = Input()
    material_density = Input(7900.0)

    @Attribute
    def mass(self):
        vol = (math.pi
               * (self.outer_radius**2 - self.inner_radius**2)
               * self.length)
        return vol * self.material_density

    # ---- 3-D geometry -------------------------------------------------------
    @Part
    def outer_shaft(self):
        return Cylinder(
            radius=self.outer_radius,
            height=self.length,
            position=self.position,
            color='darkgrey',
        )

    @Part
    def inner_bore(self):
        return Cylinder(
            radius=self.inner_radius,
            height=self.length,
            position=self.position,
        )

    @Part
    def solid(self):
        return SubtractedSolid(
            shape_in=self.outer_shaft,
            tool=self.inner_bore,
            color='darkgrey',
        )


# ---------------------------------------------------------------------------
class Engine(GeomBase):
    """
    Top-level engine assembly.
    Layout along X-axis (axial):
        inlet_duct → compressor → combustor → turbine → exhaust_duct
    All child @Parts are positioned by translating along X relative to
    self.position (engine nose).
    # TODO: Confirm X = axial / Z = vertical convention with Architect.
    """

    # ---- Inputs -------------------------------------------------------------
    input_file        = Input()
    engine_type       = Input('turbojet')
    cruise_mach       = Input(0.85)
    cruise_altitude   = Input(10000.0)

    opr               = Input(20.0)
    tit               = Input(1500.0)
    p_inlet           = Input(101325.0)
    t_inlet           = Input(288.15)
    mass_flow         = Input(50.0)
    mach_inlet        = Input(0.4)

    eta_compressor    = Input(0.88)
    eta_turbine       = Input(0.90)
    omega             = Input(1000.0)    # [rad/s]

    casing_density    = Input(7900.0)
    youngs_modulus    = Input(200e9)
    yield_stress      = Input(250e6)

    # ---- FlowStation @Parts (no geometry, pure thermodynamics) --------------
    @Part
    def station_inlet(self):
        return FlowStation(
            mass_flow=self.mass_flow,
            mach=self.mach_inlet,
            p_total=self.p_inlet,
            t_total=self.t_inlet,
        )

    @Attribute
    def p_compressor_exit(self):
        return self.p_inlet * self.opr

    @Attribute
    def t_compressor_exit(self):
        exp = (GAMMA - 1.0) / GAMMA / self.eta_compressor
        return self.t_inlet * self.opr ** exp

    @Part
    def station_compressor_exit(self):
        return FlowStation(
            mass_flow=self.mass_flow,
            mach=0.3,
            p_total=self.p_compressor_exit,
            t_total=self.t_compressor_exit,
        )

    @Attribute
    def turbine_pressure_ratio(self):
        cp       = GAMMA * R_AIR / (GAMMA - 1.0)
        dh_comp  = cp * (self.t_compressor_exit - self.t_inlet)
        t_t_exit = self.tit - dh_comp / cp
        exp      = GAMMA / ((GAMMA - 1.0) * self.eta_turbine)
        return (self.tit / max(t_t_exit, 600.0)) ** exp

    @Attribute
    def t_turbine_exit(self):
        cp      = GAMMA * R_AIR / (GAMMA - 1.0)
        dh_comp = cp * (self.t_compressor_exit - self.t_inlet)
        return self.tit - dh_comp / cp

    @Part
    def station_turbine_exit(self):
        return FlowStation(
            mass_flow=self.mass_flow,
            mach=0.4,
            p_total=self.p_compressor_exit / self.turbine_pressure_ratio,
            t_total=self.t_turbine_exit,
        )

    # ---- Axial positions (cascade along X) ----------------------------------
    @Attribute
    def x_inlet_duct_start(self):
        return 0.0

    @Attribute
    def x_compressor_start(self):
        return self.x_inlet_duct_start + self.inlet_duct.axial_length

    @Attribute
    def x_combustor_start(self):
        return self.x_compressor_start + self.compressor.axial_length

    @Attribute
    def x_turbine_start(self):
        return self.x_combustor_start + self.combustor.length

    @Attribute
    def x_exhaust_duct_start(self):
        return self.x_turbine_start + self.turbine.axial_length

    @Attribute
    def total_axial_length(self):
        return self.x_exhaust_duct_start + self.exhaust_duct.axial_length

    # ---- Component @Parts with real 3-D geometry ----------------------------
    @Part
    def inlet_duct(self):
        """Converging inlet duct (free-stream → compressor face)."""
        return Duct(
            inlet_station=self.station_inlet,
            outlet_station=self.station_compressor_exit,
            position=translate(self.position, 'x', self.x_inlet_duct_start),
            color='lightblue',
        )

    @Part
    def compressor(self):
        return Turbomachine(
            machine_type='compressor',
            pressure_ratio=self.opr,
            eta_poly=self.eta_compressor,
            inlet_station=self.station_inlet,
            outlet_station=self.station_compressor_exit,
            omega=self.omega,
            material_density=self.casing_density,
            position=translate(self.position, 'x', self.x_compressor_start),
        )

    @Part
    def combustor(self):
        return Combustor(
            outer_radius=self.compressor.casing_radius * 1.05,
            inner_radius=self.compressor.casing_radius * 0.70,
            position=translate(self.position, 'x', self.x_combustor_start),
        )

    @Part
    def turbine(self):
        return Turbomachine(
            machine_type='turbine',
            pressure_ratio=self.turbine_pressure_ratio,
            eta_poly=self.eta_turbine,
            inlet_station=self.station_compressor_exit,
            outlet_station=self.station_turbine_exit,
            omega=self.omega,
            material_density=self.casing_density,
            position=translate(self.position, 'x', self.x_turbine_start),
        )

    @Part
    def exhaust_duct(self):
        """Diverging nozzle duct (turbine exit → atmosphere)."""
        return Duct(
            inlet_station=self.station_turbine_exit,
            outlet_station=self.station_inlet,   # atmosphere approx — replace post-CFD
            position=translate(self.position, 'x', self.x_exhaust_duct_start),
            color='red',
        )

    @Part
    def spool(self):
        return Spool(
            outer_radius=self.compressor.r_mean * 0.5,
            inner_radius=self.compressor.r_mean * 0.3,
            length=(self.compressor.axial_length
                    + self.combustor.length
                    + self.turbine.axial_length),
            position=translate(self.position, 'x', self.x_compressor_start),
        )

    @Part
    def frame(self):
        """Outer structural casing wrapping the full machine."""
        return EngineFrame(
            inner_radius=max(self.compressor.casing_radius,
                             self.turbine.casing_radius) * 1.02,
            axial_length=self.total_axial_length,
            material_density=self.casing_density,
            youngs_modulus=self.youngs_modulus,
            yield_stress=self.yield_stress,
            blade_mass=1.5,
            blade_tip_speed=self.omega * self.turbine.r_mean,
            blade_omega=self.omega,
            blade_inertia=0.05,
            position=self.position,
        )

    # ---- Weight -------------------------------------------------------------
    @Attribute
    def total_mass(self):
        """Geometry-based total mass [kg]."""
        return (self.compressor.casing_solid.volume * self.casing_density
                + self.turbine.casing_solid.volume   * self.casing_density
                + self.combustor.mass
                + self.spool.mass
                + self.frame.casing_mass)