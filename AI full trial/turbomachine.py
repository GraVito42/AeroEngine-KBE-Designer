# =============================================================================
# aero_engine_kbe / turbomachine.py
# =============================================================================
import math
from parapy.core import Base, Input, Attribute, Part, child
from parapy.geom import (GeomBase, Cylinder, Cone, SubtractedSolid,
                          FusedSolid, translate, rotate, Position, Point,
                          Vector)

from flow_station import FlowStation


# ---------------------------------------------------------------------------
class Blade(GeomBase):
    """
    Single rotor blade – simplified box geometry.
    X = axial (chord), Z = radial (span), Y = tangential (thickness).
    # TODO: Verify X/Z/Y blade orientation against Positioning Cheatsheet.
    """

    chord      = Input()    # [m]  axial extent
    span       = Input()    # [m]  radial height
    t_c_ratio  = Input(0.08)
    density    = Input(4430.0)   # [kg/m³] Ti-6Al-4V default
    #: Angular position of this blade on the annulus [rad]
    angle      = Input(0.0)
    #: Mean-line radius for radial placement [m]
    r_mean     = Input()

    @Attribute
    def thickness(self):
        return self.chord * self.t_c_ratio

    @Attribute
    def volume_estimate(self):
        return self.chord * self.span * self.thickness

    @Attribute
    def mass_estimate(self):
        return self.volume_estimate * self.density

    # ---- 3-D geometry -------------------------------------------------------
    @Attribute
    def blade_root_position(self):
        """
        Place the blade root at radius r_mean, rotated by self.angle around X.
        # TODO: Verify rotation axis ('x' = axial) with Architect.
        """
        # Start at origin, shift radially outward in Y, then rotate around X
        pos_radial = translate(self.position, 'y', self.r_mean)
        return rotate(pos_radial, 'x', self.angle)

    @Part
    def solid(self):
        """
        Blade solid: thin box (chord × thickness × span).
        Position places it at hub radius, oriented radially outward (Z-up).
        # TODO: Confirm Z = radial-outward convention with Architect.
        """
        from parapy.geom import Box
        return Box(
            width=self.thickness,    # tangential (Y)
            length=self.chord,       # axial      (X)
            height=self.span,        # radial     (Z)
            position=self.blade_root_position,
        )


# ---------------------------------------------------------------------------
class Stage(GeomBase):
    """One aerodynamic stage: annular flow path + quantified rotor blades."""

    inlet_station   = Input()      # FlowStation
    outlet_station  = Input()      # FlowStation
    pressure_ratio  = Input(1.3)
    eta_poly        = Input(0.90)
    r_mean          = Input()      # [m]
    omega           = Input()      # [rad/s]
    n_blades        = Input(30)

    @Attribute
    def r_hub(self):
        """Hub radius from inlet annulus assuming hub-tip ratio 0.5."""
        htr = 0.5
        r_tip = math.sqrt(self.inlet_station.area / (math.pi * (1 - htr**2)))
        return r_tip * htr

    @Attribute
    def r_tip(self):
        return self.r_hub / 0.5

    @Attribute
    def blade_span(self):
        return self.r_tip - self.r_hub

    @Attribute
    def blade_chord(self):
        """Rule-of-thumb: chord ≈ 0.5 × annulus height."""
        return self.blade_span * 0.5

    @Attribute
    def stage_length(self):
        """Axial length: rotor + stator, estimated as 2 × chord."""
        return 2.0 * self.blade_chord

    # ---- 3-D geometry -------------------------------------------------------
    @Part
    def annulus_outer(self):
        """Outer flow-path cylinder."""
        return Cylinder(
            radius=self.r_tip,
            height=self.stage_length,
            position=self.position,
        )

    @Part
    def annulus_inner(self):
        """Inner (hub) cylinder to cut out."""
        return Cylinder(
            radius=self.r_hub,
            height=self.stage_length,
            position=self.position,
        )

    @Part
    def flow_annulus(self):
        """Hollow annular flow passage solid."""
        return SubtractedSolid(
            shape_in=self.annulus_outer,
            tool=self.annulus_inner,
            color='cyan',
        )

    @Part
    def rotor_blades(self):
        """
        Quantified blade parts, evenly spaced angularly around the annulus.
        child.index gives the current blade number.
        """
        return Blade(
            quantify=self.n_blades,
            chord=self.blade_chord,
            span=self.blade_span,
            r_mean=self.r_mean,
            angle=child.index * (2.0 * math.pi / self.n_blades),
            position=self.position,
            color='orange',
        )


# ---------------------------------------------------------------------------
class Turbomachine(GeomBase):
    """
    Compressor or turbine.
    X-axis = axial flow direction.
    Stages are stacked along X using child.previous positioning.
    """

    machine_type     = Input('compressor')   # 'compressor' | 'turbine'
    pressure_ratio   = Input()
    eta_poly         = Input(0.90)
    inlet_station    = Input()
    outlet_station   = Input()
    omega            = Input(1000.0)         # [rad/s]
    psi_target       = Input(0.35)           # loading coefficient
    material_density = Input(7900.0)         # casing [kg/m³]
    wall_thickness   = Input(0.010)          # casing wall [m]

    @Attribute
    def gamma(self):
        return self.inlet_station.gamma

    @Attribute
    def cp(self):
        return self.inlet_station.cp

    @Attribute
    def r_mean(self):
        """Mean-line radius from inlet annulus with hub-tip ratio 0.5."""
        htr = 0.5
        r_tip = math.sqrt(
            self.inlet_station.area / (math.pi * (1 - htr**2)))
        return r_tip * (1 + htr) / 2.0

    @Attribute
    def n_stages(self):
        exponent  = (self.gamma - 1.0) / self.gamma / self.eta_poly
        dh_total  = self.cp * self.inlet_station.t_total * abs(
            self.pressure_ratio ** exponent - 1.0)
        u         = self.omega * self.r_mean
        dh_stage  = self.psi_target * u ** 2
        return max(1, math.ceil(dh_total / dh_stage))

    @Attribute
    def stage_pressure_ratio(self):
        return self.pressure_ratio ** (1.0 / self.n_stages)

    @Attribute
    def casing_radius(self):
        """Outer casing radius = flow tip radius + wall thickness."""
        htr   = 0.5
        r_tip = math.sqrt(
            self.inlet_station.area / (math.pi * (1 - htr**2)))
        return r_tip + self.wall_thickness

    @Attribute
    def axial_length(self):
        """Sum of all stage lengths (lazy — uses Stage.stage_length)."""
        # Each stage contributes 2 × chord ≈ 2 × 0.5 × annulus_height
        ann_h = self.casing_radius - self.wall_thickness - (
            self.casing_radius - self.wall_thickness) * 0.5
        chord = ann_h * 0.5
        return self.n_stages * 2.0 * chord

    # ---- 3-D geometry -------------------------------------------------------
    @Part
    def stages(self):
        """
        Quantified Stage parts, each translated along X by one stage length.
        Uses child.previous positioning pattern.
        """
        return Stage(
            quantify=self.n_stages,
            inlet_station=self.inlet_station,
            outlet_station=self.outlet_station,
            pressure_ratio=self.stage_pressure_ratio,
            eta_poly=self.eta_poly,
            r_mean=self.r_mean,
            omega=self.omega,
            position=(
                self.position if child.index == 0
                else translate(child.previous.position,
                               'x', child.previous.stage_length)
            ),
        )

    @Part
    def casing_outer(self):
        """Full-length outer cylindrical casing."""
        return Cylinder(
            radius=self.casing_radius,
            height=self.axial_length,
            position=self.position,
            color='grey',
        )

    @Part
    def casing_inner_bore(self):
        """Bore to hollow the casing."""
        return Cylinder(
            radius=self.casing_radius - self.wall_thickness,
            height=self.axial_length,
            position=self.position,
        )

    @Part
    def casing_solid(self):
        """Hollow annular casing shell."""
        return SubtractedSolid(
            shape_in=self.casing_outer,
            tool=self.casing_inner_bore,
            color='grey',
        )