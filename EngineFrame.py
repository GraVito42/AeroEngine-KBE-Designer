# engine_frame.py
"""
EngineFrame — structural engine casing shell + blade-off containment analysis.

Class architecture:
  AeroEngine
  └── EngineFrame          (inherits Duct)
      ├── inlet_duct        Inlet child  — front lip geometry, hidden
      └── nozzle_duct       Nozzle child — rear nozzle geometry, hidden

Inherits from Duct:
  - Single RevolvedSolid body built from self.wall_profile
  - weight and volume from EngineComponent
  - pressure_ratio = 1.0  (frame is structural, no aero pressure loss)
  - Mach_out = nozzle exit Mach (default, overridable by AeroEngine)
  - length = inlet_length + length_casing + nozzle_length
  - x_offset = 0.0  (frame always starts at global origin)

Unified wall_profile (single FittedCurve):
  The profile is a closed meridional loop assembled as follows:
    1. Inlet inner wall:  outlet_inner → highlight  (from inlet_duct.profile_points)
    2. Internal profile:  compressor / combustor / turbine points  (increasing x)
    3. Nozzle inner wall: nozzle inlet inner → nozzle outlet inner
    4. Nozzle outer wall: nozzle outlet outer → nozzle inlet outer
    5. Outer casing:      interpolated points on the straight line
                          (inlet outlet outer → nozzle inlet outer), reversed
    6. Inlet outer wall:  outlet_outer → highlight  (from inlet_duct.profile_points, reversed)
    7. Closure back to start point

All internal x positions in `internal_profile` are relative to the
START OF THE CASING  (absolute x = inlet_length + x_casing_relative).

Blade-off containment (CS-E §25.903(d)):
  E_s = sigma_avg * eps_f * A_inner * t  >=  E_k * SF * (1 + margin_target)
"""

import math

from parapy.core import Input, Attribute, Part, action
from parapy.geom import Point, FittedCurve, XOY, rotate, Polygon, ComposedCurve, BSplineCurve, Polyline

from Flow_station import FlowStation
from Duct         import Duct
from Inlet        import Inlet
from Nozzle       import Nozzle


class EngineFrame(Duct):
    """
    Structural engine frame modelled as a single Duct with a unified wall profile.
    The inlet lip and nozzle geometry drive the front and rear ends respectively.
    The internal wall follows component radii supplied via `internal_profile`.
    """

    # ------------------------------------------------------------------
    # Thermodynamic boundary conditions
    # ------------------------------------------------------------------

    #: FlowStation at station 1 — inlet highlight face
    inlet_inflow: object = Input()

    #: FlowStation at station 6 — nozzle inlet (turbine exit)
    nozzle_inflow: object = Input()

    # ------------------------------------------------------------------
    # Structural / containment inputs
    # ------------------------------------------------------------------

    #: [m]   Sheet-metal wall thickness
    sheet_thickness: float = Input(0.003)

    #: [-]   Blade-off safety factor (CS-E §25.903(d) minimum = 1.5)
    safety_factor: float = Input(1.5)

    #: [-]   Target fractional containment margin (0 = exactly at limit)
    containment_margin_target: float = Input(0.0)

    # ------------------------------------------------------------------
    # Blade-off kinetic inputs
    # ------------------------------------------------------------------

    #: [kg]      Mass of one released blade
    blade_mass: float = Input(1.5)

    #: [m]       Blade tip radius (worst case = casing inner radius)
    blade_tip_radius: float = Input(0.28)

    #: [rad/s]   Rotor angular velocity at blade-off event
    omega: float = Input(1200.0)

    #: [kg·m²]  Blade moment of inertia about rotor axis
    blade_inertia: float = Input(0.02)

    # ------------------------------------------------------------------
    # Inlet duct inputs
    # ------------------------------------------------------------------

    #: str   Lip contour type: 'curved' | 'bellmouth' | 'polygonal'
    inlet_lip_profile: str = Input("curved")

    #: [-]   Total-pressure recovery factor across the inlet
    inlet_pressure_ratio: float = Input(0.98)

    #: [-]   Inlet isentropic efficiency
    inlet_isos_efficiency: float = Input(0.95)

    #: [-]   Design exit Mach number of the inlet
    inlet_Mach_out: float = Input(0.45)

    #: [m]   Axial length of the inlet duct
    inlet_length: float = Input(0.55)

    #: [m]   Wall thickness at the inlet face
    inlet_wall_thickness: float = Input(0.012)

    # ------------------------------------------------------------------
    # Casing inputs
    # ------------------------------------------------------------------

    #: [m]   Axial length of the casing barrel
    length_casing: float = Input(2.0)

    #: [m]   Wall thickness at the casing inlet face
    casing_inlet_wall_thickness: float = Input(0.012)

    #: [m]   Wall thickness at the casing outlet face
    casing_outlet_wall_thickness: float = Input(0.012)

    # ------------------------------------------------------------------
    # Nozzle inputs
    # ------------------------------------------------------------------

    #: [-]   Total-pressure ratio across the nozzle
    nozzle_pressure_ratio: float = Input(0.97)

    #: [-]   Nozzle isentropic efficiency
    nozzle_isos_efficiency: float = Input(0.96)

    #: [-]   Design exit Mach number (> 1.0 for convergent-divergent)
    nozzle_Mach_out: float = Input(1.20)

    #: [m]   Axial length of the nozzle
    nozzle_length: float = Input(0.45)

    #: [m]   Wall thickness at the nozzle exit face
    nozzle_wall_thickness: float = Input(0.012)

    #: [Pa]  Ambient static pressure — reference for thrust coefficient
    p_ambient: float = Input(101325.0)

    # ------------------------------------------------------------------
    # Internal component profile
    # List of (x_casing_relative [m], r [m]) tuples.
    # x is measured from the START OF THE CASING (not from frame origin).
    # Defines inner wall waypoints through compressor, combustor, turbine.
    # Default: representative single-spool turbojet layout.
    # ------------------------------------------------------------------

    internal_profile: list = Input([
        (0.02, 0.080),  # compressor inlet   — large-radius fan/compressor face
        (0.35, 0.075),  # compressor outlet  — radius shrinks through compression
        (0.37, 0.090),  # combustor inlet    — sudden expansion into combustor annulus
        (0.63, 0.090),  # combustor outlet   — constant combustor annulus radius
        (0.65, 0.070),  # turbine inlet      — contraction into turbine
        (0.95, 0.089),  # turbine outlet     — slight expansion, matches nozzle r_inlet_inner
    ])

    # ------------------------------------------------------------------
    # Override Duct @Input slots — wire frame-level values
    # ------------------------------------------------------------------

    @Input
    def inflow_conditions(self):
        """Frame inlet = station 1 flow conditions."""
        return self.inlet_inflow

    @Input
    def pressure_ratio(self):
        """No aero pressure loss across the structural frame."""
        return 1.0

    @Input
    def isos_efficiency(self):
        """Isentropic efficiency = 1 (structural component, no work)."""
        return 1.0

    @Input
    def Mach_out(self):
        """Frame exit Mach = nozzle inflow Mach (default, overridable)."""
        return self.nozzle_inflow.Mach

    @Input
    def station_out(self):
        """Frame outlet is station 7 (nozzle exit)."""
        return 7

    @Input
    def length(self):
        """Total axial length of the frame [m]."""
        return self.inlet_length + self.length_casing + self.nozzle_length

    @Input
    def position(self):
        """Frame base position — X axis aligned with engine axial direction."""
        return rotate(XOY, 'y', 90, deg=True)

    @Input
    def x_offset(self):
        """Frame always starts at global origin."""
        return 0.0

    @Input
    def wall_thickness_inlet(self):
        return self.inlet_wall_thickness

    @Input
    def wall_thickness_outlet(self):
        return self.nozzle_wall_thickness

    # ------------------------------------------------------------------
    # Child ducts — geometry and thermodynamics at the two ends
    # Both are hidden: they supply radii and profile_points only.
    # ------------------------------------------------------------------

    @Part
    def inlet_duct(self):
        """Inlet end-cap — drives front lip geometry and inlet radii."""
        return Inlet(
            x_offset              = 0,
            inflow_conditions     = self.inlet_inflow,
            isos_efficiency       = self.inlet_isos_efficiency,
            Mach_out              = self.inlet_Mach_out,
            station_out           = 2,
            pressure_ratio        = self.inlet_pressure_ratio,
            lip_profile_type      = self.inlet_lip_profile,
            sheet_thickness       = self.sheet_thickness,
            length                = self.inlet_length,
            material_name         = self.material_name,
            wall_thickness_inlet  = self.inlet_wall_thickness,
            wall_thickness_outlet = self.casing_inlet_wall_thickness,
            hidden                = True,
        )

    @Part
    def nozzle_duct(self):
        """Nozzle end-cap — drives rear geometry and nozzle radii."""
        return Nozzle(
            x_offset              = self.inlet_length + self.length_casing,
            inflow_conditions     = self.nozzle_inflow,
            isos_efficiency       = self.nozzle_isos_efficiency,
            Mach_out              = self.nozzle_Mach_out,
            station_out           = 7,
            pressure_ratio        = self.nozzle_pressure_ratio,
            p_ambient             = self.p_ambient,
            length                = self.nozzle_length,
            material_name         = self.material_name,
            wall_thickness_inlet  = self.casing_outlet_wall_thickness,
            wall_thickness_outlet = self.nozzle_wall_thickness,
            hidden                = True,
        )

    # ------------------------------------------------------------------
    # Convenience radius attributes — delegate to child ducts
    # ------------------------------------------------------------------

    @Attribute
    def r_inlet_inner(self):
        """Inner radius at frame inlet = inlet throat radius [m]."""
        return self.inlet_duct.r_inlet_inner

    @Attribute
    def r_inlet_outer(self):
        """Outer radius at frame inlet face [m]."""
        return self.inlet_duct.r_inlet_outer

    @Attribute
    def r_outlet_inner(self):
        """Inner radius at frame outlet = nozzle exit inner radius [m]."""
        return self.nozzle_duct.r_outlet_inner

    @Attribute
    def r_outlet_outer(self):
        """Outer radius at frame outlet = nozzle exit outer radius [m]."""
        return self.nozzle_duct.r_outlet_outer

    # ------------------------------------------------------------------
    # Internal profile — convert to absolute x coordinates
    # ------------------------------------------------------------------

    @Attribute
    def _resolved_internal_profile(self):
        """
        Converts casing-relative x to absolute coordinates and clips any
        points that fall outside [inlet_length, inlet_length + length_casing].
        This prevents internal profile points from breaching the nozzle when
        length_casing is reduced.
        """
        return sorted(
            [
                (self.inlet_length + x, r)
                for x, r in self.internal_profile
                if self.inlet_length + x <= self.inlet_length + self.length_casing
            ],
            key=lambda p: p[0],
        )

    # ------------------------------------------------------------------
    # Outer casing interpolation
    # ------------------------------------------------------------------

    @Attribute
    def _outer_casing_points(self):
        """
        For each internal profile point, compute the corresponding outer
        casing point by linear interpolation on the straight line connecting:
          - inlet duct outlet outer  (x = inlet_length,                r = inlet_duct.r_outlet_outer)
          - nozzle duct inlet outer  (x = inlet_length + length_casing, r = nozzle_duct.r_inlet_outer)
        These points are used in profile_points to give FittedCurve enough
        outer wall waypoints and avoid oscillation.
        """
        return [
        Point(
            x_abs,
            self.inlet_duct.r_outlet_outer
            + (self.nozzle_duct.r_inlet_outer - self.inlet_duct.r_outlet_outer)
            * (x_abs - self.inlet_length)
            / (self.nozzle_duct.profile_points[1].x - self.inlet_length),
            0.0,
        )
        for x_abs, _ in self._resolved_internal_profile
    ]

    # ------------------------------------------------------------------
    # Split inlet profile_points into inner and outer halves
    # The highlight is the point with minimum x in the inlet profile.
    # ------------------------------------------------------------------

    @Attribute
    def _inlet_highlight_idx(self):
        """Index of the highlight point (minimum x) in inlet_duct.profile_points."""
        return min(
            range(len(self.inlet_duct.profile_points)),
            key=lambda i: self.inlet_duct.profile_points[i].x,
        )

    @Attribute
    def _inlet_outlet_outer(self):
        """Point at (inlet_length, r_outlet_outer) — junction with outer casing."""
        return max(
            (p for p in self.inlet_duct.profile_points if abs(p.x - self.inlet_length) < 1e-4),
            key=lambda p: p.y,
        )

    @Attribute
    def _inlet_outlet_outer_idx(self):
        """Index of outlet_outer point in inlet_duct.profile_points."""
        return max(
            (i for i, p in enumerate(self.inlet_duct.profile_points) if abs(p.x - self.inlet_length) < 1e-4),
            key=lambda i: self.inlet_duct.profile_points[i].y,
        )

    @Attribute
    def _inlet_inner(self):
        """
        Inner half of the inlet meridian:
        outlet_inner → highlight  (decreasing x, starts at x=inlet_length).
        """
        return self.inlet_duct.profile_points[: self._inlet_highlight_idx + 1]

    @Attribute
    def _inlet_outer(self):
        """highlight → outlet_outer (from highlight_idx to outlet_outer_idx)."""
        return self.inlet_duct.profile_points[
            self._inlet_highlight_idx: self._inlet_outlet_outer_idx + 1
        ]

    # ------------------------------------------------------------------
    # Unified wall profile points
    # ------------------------------------------------------------------

    @Attribute
    def profile_points(self):
        """
        Closed meridional loop starting and ending at the inlet highlight.
        Traversal: highlight → inner wall (increasing x) → internal pts
        → nozzle inner → nozzle outer → outer casing (decreasing x)
        → inlet outer → highlight.
        """
        return (
                list(reversed(self._inlet_inner))  # highlight → outlet_inner (increasing x)
                + [Point(x, r, 0.0) for x, r in self._resolved_internal_profile]  # internal (increasing x)
                + [self.nozzle_duct.profile_points[0]]  # nozzle inner inlet
                + [self.nozzle_duct.profile_points[-1]
                   if not self.nozzle_duct.is_convergent_divergent
                   else self.nozzle_duct.profile_points[3]]  # nozzle inner outlet
                + [self.nozzle_duct.profile_points[2]]  # nozzle outer outlet
                + [self.nozzle_duct.profile_points[1]]  # nozzle outer inlet
                + list(reversed(self._outer_casing_points))  # outer casing (decreasing x)
                + self._inlet_outer[1:]  # inlet outer (decreasing x to highlight)
        )

    @Attribute
    def _outer_casing_points_reversed(self):
        return list(reversed(self._outer_casing_points))

    @Part
    def _curve_inlet_inner(self):
        """Inlet inner wall: highlight → outlet_inner (increasing x)."""
        return FittedCurve(points=list(reversed(self._inlet_inner)), hidden=True)

    @Part
    def _curve_internal(self):
        """
        Inner wall ending at nozzle inner inlet.
        Nozzle inner geometry (including C-D throat) handled by _curve_outer_casing.
        """
        return BSplineCurve(
            control_points=(
                    [self._inlet_inner[0]]
                    + [Point(x, r, 0.0) for x, r in self._resolved_internal_profile]
                    + [self.nozzle_duct.profile_points[0]]
            ),
            degree=1,
            hidden=True,
        )
    # @Part
    # def _curve_nozzle_inner(self):
    #     return Polygon(
    #         points=[
    #             self.nozzle_duct.profile_points[0],
    #             self.nozzle_duct.profile_points[3]
    #             if not self.nozzle_duct.is_convergent_divergent
    #             else self.nozzle_duct.profile_points[3],
    #         ],
    #         hidden=True,
    #     )
    #
    # @Part
    # def _curve_nozzle_outer(self):
    #     return Polygon(
    #         points=[
    #             self.nozzle_duct.profile_points[3],
    #             self.nozzle_duct.profile_points[2],
    #             self.nozzle_duct.profile_points[1],
    #         ],
    #         hidden=True,
    #     )

    @Part
    def _curve_outer_casing(self):
        """
        Full nozzle box traversal + outer casing.
        For C-D nozzle: includes throat point [4] on the inner wall path.
        """
        return BSplineCurve(
            control_points=(
                    [self.nozzle_duct.profile_points[0]]  # nozzle inner inlet
                    + (
                        [self.nozzle_duct.profile_points[4],  # throat (C-D only)
                         self.nozzle_duct.profile_points[3]]
                        if self.nozzle_duct.is_convergent_divergent
                        else [self.nozzle_duct.profile_points[3]]
                    )
                    + [self.nozzle_duct.profile_points[2]]  # nozzle outer outlet
                    + [self.nozzle_duct.profile_points[1]]  # nozzle outer inlet
                    + self._outer_casing_points_reversed
                    + [self._inlet_outlet_outer]
            ),
            degree=1,
            hidden=True,
        )

    @Part
    def _curve_inlet_outer(self):
        """Inlet outer wall: outlet_outer → highlight."""
        return FittedCurve(
            points=list(reversed(self._inlet_outer)),  # outlet_outer → highlight
            hidden=True,
        )

    @Part(parse=False)
    def wall_profile(self):
        return ComposedCurve(
            built_from=[
                self._curve_inlet_inner,  # highlight        → outlet_inner
                self._curve_internal,  # outlet_inner     → nozzle inner outlet
                self._curve_outer_casing,  # nozzle inner outlet → inlet outlet outer
                self._curve_inlet_outer,  # inlet outlet outer → highlight
            ],
            hidden=True,
        )
    # ------------------------------------------------------------------
    # Blade-off containment analysis
    # ------------------------------------------------------------------

    @Attribute
    def mean_area_inner(self):
        """
        Wetted inner area of the casing barrel [m²].
        Approximated as the lateral area of a cylinder at the mean inner radius.
        """
        return (
            2.0 * math.pi
            * (self.inlet_duct.r_outlet_inner + self.nozzle_duct.r_inlet_inner) / 2.0
            * self.length_casing
        )

    @Attribute
    def kinetic_energy_blade_off(self):
        """
        Total kinetic energy of a released blade [J].
        E_k = 0.5 * m * v_tip^2 + 0.5 * I * omega^2
        """
        return (
            0.5 * self.blade_mass * (self.blade_tip_radius * self.omega) ** 2
            + 0.5 * self.blade_inertia * self.omega ** 2
        )

    @Attribute
    def strain_energy_casing(self):
        """
        Strain energy absorbed by the casing sheet to fracture [J].
        E_s = sigma_avg * eps_f * A_inner * t
        sigma_avg = (yield_stress + ult_strength) / 2  (trapezoidal sigma-eps rule)
        """
        return (
            (self.material.yield_stress + self.material.ultimate_tensile_strength) / 2.0
            * self.material.fracture_strain
            * self.mean_area_inner
            * self.sheet_thickness
        )

    def is_contained(self):
        """True when the casing absorbs the blade-off event with the required margin."""
        return self.strain_energy_casing >= self.kinetic_energy_blade_off * self.safety_factor

    @Attribute
    def containment_margin(self):
        """
        Fractional containment margin [-].
          > 0  →  safe (positive margin)
          <= 0 →  containment failure
        """
        return (
            (self.strain_energy_casing - self.kinetic_energy_blade_off * self.safety_factor)
            / (self.kinetic_energy_blade_off * self.safety_factor)
        )

    @Attribute
    def sheet_thickness_required(self):
        """
        Minimum sheet thickness to achieve containment_margin_target [m].
        Derived by inverting strain_energy_casing >= E_k * SF * (1 + margin_target).
        """
        return (
            self.kinetic_energy_blade_off
            * self.safety_factor
            * (1.0 + self.containment_margin_target)
            / (
                (self.material.yield_stress + self.material.ultimate_tensile_strength) / 2.0
                * self.material.fracture_strain
                * self.mean_area_inner
            )
        )

    @action
    def update_sheet_thickness_for_containment(self):
        """
        GUI action: set sheet_thickness to satisfy containment_margin_target.
        Modify containment_margin_target in the property panel, then click.
        """
        self.sheet_thickness = self.sheet_thickness_required
        return self.sheet_thickness

    # ------------------------------------------------------------------
    # Mass properties
    # ------------------------------------------------------------------

    @Attribute
    def frame_weight(self):
        """Total frame mass [kg] — delegates to Duct.weight (surface * t * rho)."""
        return self.weight

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self):
        warnings = super().validate()

        if self.blade_mass <= 0.0:
            warnings.append(
                f"EngineFrame: blade_mass={self.blade_mass:.3f} kg must be > 0.")
        if self.blade_tip_radius <= 0.0:
            warnings.append(
                f"EngineFrame: blade_tip_radius={self.blade_tip_radius:.4f} m must be > 0.")
        if self.omega <= 0.0:
            warnings.append(
                f"EngineFrame: omega={self.omega:.1f} rad/s must be > 0.")
        if self.safety_factor < 1.5:
            warnings.append(
                f"EngineFrame: safety_factor={self.safety_factor:.2f} "
                f"is below the CS-E minimum of 1.5.")
        if not self.is_contained():
            warnings.append(
                f"EngineFrame: BLADE-OFF CONTAINMENT FAILED — "
                f"margin={self.containment_margin:.3f} "
                f"(E_s={self.strain_energy_casing:.1f} J < "
                f"E_k*SF={self.kinetic_energy_blade_off * self.safety_factor:.1f} J). "
                f"Increase sheet_thickness or switch to a tougher material.")
        if self.sheet_thickness <= 0.0:
            warnings.append(
                f"EngineFrame: sheet_thickness={self.sheet_thickness:.4f} m must be > 0.")
        if self.length_casing <= 0.0:
            warnings.append(
                f"EngineFrame: length_casing={self.length_casing:.3f} m must be > 0.")

        if self._resolved_internal_profile:
            x_start = self.inlet_length
            x_end = self.inlet_length + self.length_casing

            # Check first internal point against inlet outlet outer radius
            r_first = self._resolved_internal_profile[0][1]
            if r_first >= self.inlet_duct.r_outlet_outer:
                warnings.append(
                    f"EngineFrame: internal_profile first point r={r_first:.4f} m "
                    f">= inlet outlet outer r={self.inlet_duct.r_outlet_outer:.4f} m. "
                    f"Inner wall breaches outer casing at inlet junction.")
            if r_first <= 0.0:
                warnings.append(
                    f"EngineFrame: internal_profile first point r={r_first:.4f} m must be > 0.")

            # Check last internal point against nozzle inlet outer radius
            r_last = self._resolved_internal_profile[-1][1]
            if r_last >= self.nozzle_duct.r_inlet_outer:
                warnings.append(
                    f"EngineFrame: internal_profile last point r={r_last:.4f} m "
                    f">= nozzle inlet outer r={self.nozzle_duct.r_inlet_outer:.4f} m. "
                    f"Inner wall breaches outer casing at nozzle junction.")

            # Check every internal point against the linearly interpolated outer casing radius
            for x_abs, r in self._resolved_internal_profile:
                r_outer_at_x = (
                        self.inlet_duct.r_outlet_outer
                        + (self.nozzle_duct.r_inlet_outer - self.inlet_duct.r_outlet_outer)
                        * (x_abs - x_start) / self.length_casing
                )
                if r >= r_outer_at_x:
                    warnings.append(
                        f"EngineFrame: internal_profile point at x={x_abs:.3f} m "
                        f"has r={r:.4f} m >= outer casing r={r_outer_at_x:.4f} m. "
                        f"Inner wall breaches outer casing.")
                if r <= 0.0:
                    warnings.append(
                        f"EngineFrame: internal_profile point at x={x_abs:.3f} m "
                        f"has r={r:.4f} m — must be > 0.")

            # Check internal profile points do not exceed casing length
            x_casing_end = self.inlet_length + self.length_casing
            for x_rel, r in self.internal_profile:
                x_abs = self.inlet_length + x_rel
                if x_abs > x_casing_end:
                    warnings.append(
                        f"EngineFrame: internal_profile point at x_rel={x_rel:.3f} m "
                        f"(x_abs={x_abs:.3f} m) exceeds casing end at x={x_casing_end:.3f} m. "
                        f"Point discarded. Increase length_casing or reduce x_rel.")

        return warnings

    # =============================================================================
    # Smoke-test
    # =============================================================================
if __name__ == "__main__":

    station_1 = FlowStation(
        station_number=1, fluid_type="air",
        p_total=101325.0, T_total=288.15, mass_flow=22.9, Mach=0.25,
    )
    station_6 = FlowStation(
        station_number=6, fluid_type="fuel_gas",
        p_total=202650.0, T_total=780.0, mass_flow=23.5, Mach=0.35,
    )

    # ------------------------------------------------------------------
    # Case 1 — baseline: all checks should pass
    # ------------------------------------------------------------------
    frame_ok = EngineFrame(
        inlet_inflow=station_1,
        nozzle_inflow=station_6,
        inlet_length=0.2,
        length_casing=1.0,
        nozzle_length=0.3,
        casing_inlet_wall_thickness=0.012,
        casing_outlet_wall_thickness=0.012,
        inlet_lip_profile="curved",
        inlet_pressure_ratio=0.98,
        inlet_isos_efficiency=0.95,
        inlet_Mach_out=0.45,
        inlet_wall_thickness=0.012,
        nozzle_pressure_ratio=0.97,
        nozzle_isos_efficiency=0.96,
        nozzle_Mach_out=1.20,
        nozzle_wall_thickness=0.012,
        p_ambient=101325.0,
        material_name="Ti-6Al-4V",
        sheet_thickness=0.003,
        safety_factor=1.5,
        blade_mass=1.5,
        blade_tip_radius=0.28,
        omega=1200.0,
        blade_inertia=0.02,
        internal_profile=[
            (0.02, 0.080),
            (0.35, 0.055),
            (0.37, 0.050),
            (0.63, 0.050),
            (0.65, 0.050),
            (0.95, 0.089),
        ],
    )

    print(f"  nozzle Mach_out    : {frame_ok.nozzle_duct.Mach_out:.3f}")
    print(f"  nozzle pressure_ratio: {frame_ok.nozzle_duct.pressure_ratio:.4f}")
    print(f"  nozzle r_outlet_inner: {frame_ok.nozzle_duct.r_outlet_inner:.4f} m")
    print(f"  nozzle is_CD       : {frame_ok.nozzle_duct.is_convergent_divergent}")

    # ------------------------------------------------------------------
    # Case 2 — inner wall breaches outer casing at inlet junction
    # ------------------------------------------------------------------
    frame_breach_inlet = EngineFrame(
        inlet_inflow=station_1,
        nozzle_inflow=station_6,
        inlet_length=0.2,
        length_casing=1.0,
        nozzle_length=0.3,
        casing_inlet_wall_thickness=0.012,
        casing_outlet_wall_thickness=0.012,
        inlet_lip_profile="curved",
        inlet_pressure_ratio=0.98,
        inlet_isos_efficiency=0.95,
        inlet_Mach_out=0.45,
        inlet_wall_thickness=0.012,
        nozzle_pressure_ratio=0.97,
        nozzle_isos_efficiency=0.96,
        nozzle_Mach_out=1.20,
        nozzle_wall_thickness=0.012,
        p_ambient=101325.0,
        material_name="Ti-6Al-4V",
        sheet_thickness=0.003,
        safety_factor=1.5,
        blade_mass=1.5,
        blade_tip_radius=0.28,
        omega=1200.0,
        blade_inertia=0.02,
        internal_profile=[
            (0.02, 0.999),  # r deliberately too large — breaches outer casing
            (0.35, 0.075),
            (0.37, 0.090),
            (0.63, 0.090),
            (0.65, 0.070),
            (0.95, 0.089),
        ],
    )


    # ------------------------------------------------------------------
    # Case 3 — containment failure (sheet too thin)
    # ------------------------------------------------------------------
    frame_no_contain = EngineFrame(
        inlet_inflow=station_1,
        nozzle_inflow=station_6,
        inlet_length=0.2,
        length_casing=1.0,
        nozzle_length=0.3,
        casing_inlet_wall_thickness=0.012,
        casing_outlet_wall_thickness=0.012,
        inlet_lip_profile="curved",
        inlet_pressure_ratio=0.98,
        inlet_isos_efficiency=0.95,
        inlet_Mach_out=0.45,
        inlet_wall_thickness=0.012,
        nozzle_pressure_ratio=0.97,
        nozzle_isos_efficiency=0.96,
        nozzle_Mach_out=1.20,
        nozzle_wall_thickness=0.012,
        p_ambient=101325.0,
        material_name="Ti-6Al-4V",
        sheet_thickness=0.0001,  # deliberately too thin
        safety_factor=1.5,
        blade_mass=1.5,
        blade_tip_radius=0.28,
        omega=1200.0,
        blade_inertia=0.02,
        internal_profile=[
            (0.02, 0.080),
            (0.35, 0.075),
            (0.37, 0.090),
            (0.63, 0.090),
            (0.65, 0.070),
            (0.95, 0.089),
        ],
    )

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------
    cases = [
        ("CASE 1 — baseline (expect: all pass)", frame_ok),
        ("CASE 2 — inlet breach (expect: warning)", frame_breach_inlet),
        ("CASE 3 — containment fail (expect: warning)", frame_no_contain),
    ]

    for label, frame in cases:
        print("=" * 60)
        print(label)
        print("=" * 60)
        print(f"  length        : {frame.length:.3f} m")
        print(f"  r_inlet_inner : {frame.r_inlet_inner:.4f} m")
        print(f"  r_outlet_inner: {frame.r_outlet_inner:.4f} m")
        print(f"  weight        : {frame.frame_weight:.2f} kg")
        print(f"  E_k           : {frame.kinetic_energy_blade_off:.1f} J")
        print(f"  E_s           : {frame.strain_energy_casing:.1f} J")
        print(f"  margin        : {frame.containment_margin:.3f}")
        print(f"  is_contained  : {frame.is_contained()}")
        warns = frame.validate()
        if warns:
            print("  [WARNINGS]")
            for w in warns:
                print(f"    ⚠  {w}")
        else:
            print("  [OK] all checks passed.")
        print()

    import parapy.gui as gui
    gui.display(frame_ok, view='iso', autodraw=True)