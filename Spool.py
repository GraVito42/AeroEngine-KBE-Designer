"""
Spool.py
========
Coaxial engine spool — couples a Compressor and a Turbine on a common shaft and
hosts the (low-fidelity -> high-fidelity) power-balance action.

Inheritance:
    Spool(EngineComponent, GeomBase)
  - EngineComponent: thermo-fluid contract + material lookup (self.material),
    volume/weight (from self.body), position frame (X axial, Y radial).
  - GeomBase: hosts the shaft RevolvedSolid and the two turbomachine children.

Coordinate system (engine frame): X axial, Y radial, Z tangential.
Shaft geometry is authored directly in (X_axial, Y_radial) and revolved about
the global X axis, matching the working Duct.body / EngineFrame convention.

Shaft profile:
  - spool_index == 0 (HP, SOLID): RevolvedSolid from a ComposedCurve of
      FittedCurve(outer profile)  ->  LineSegment(closure along the axis r = 0).
  - spool_index  > 0 (IP/LP, HOLLOW): outer + inner walls offset by gap() /
      shaft_thickness, closed by nose/tail caps. See TODO #1-#3 — only the HP
      (solid) path is exercised by the smoke test.
"""

import math
import os

from parapy.core import Input, Attribute, Part, action
from parapy.geom import (GeomBase, Point, FittedCurve, LineSegment,
                         ComposedCurve, RevolvedSolid, translate)

from EngineComponent import EngineComponent
from Compressor import Compressor
from Turbine import Turbine
from Flow_station import FlowStation


class Spool(EngineComponent, GeomBase):
    """Compressor + Turbine on one shaft, with a sequential power balance."""

    # ------------------------------------------------------------------
    # Inputs — architecture / sizing
    # ------------------------------------------------------------------
    spool_index = Input(0)          # 0 = HP (innermost), 1 = IP, 2 = LP
    rpm         = Input(15000)          # shaft speed [rev/min]

    r_hub_c_in  = Input(0.15)          # compressor hub radii [m]
    r_hub_c_out = Input(0.28)
    r_tip_c_in  = Input(0.35)          # compressor tip radii [m]
    r_tip_c_out = Input(0.35)

    r_hub_t_in  = Input(0.22)          # turbine hub radii [m]
    r_hub_t_out = Input(0.18)
    r_tip_t_in  = Input(0.32)          # turbine tip radii [m]
    r_tip_t_out = Input(0.38)

    n_stages_compressor = Input(3)
    n_stages_turbine    = Input(1)

    design_torque = Input(50000)        # shaft design torque [N.m]

    # ------------------------------------------------------------------
    # Inputs — with defaults
    # ------------------------------------------------------------------
    clearance_epsilon = Input(0.01)   # inter-spool gap fraction
    delta_min         = Input(0.005)  # minimum absolute gap / wall floor [m]
    nose_aspect_ratio = Input(1.5)    # end-cap ellipse semi-major/semi-minor
    loss_margin       = Input(0.15)   # power-balance margin fraction

    inflow_conditions = Input()       # FlowStation at compressor inlet
    turbine_inflow_conditions = Input()
    # FlowStation at turbine inlet — set by COMBUSTOR exit (not compressor exit),
    # since the combustor sits between compressor and turbine.

    inner_spool_profile_norm = Input(None)
    # list[(x_norm, r_norm)] of the adjacent inner spool's outer profile.
    # Used only for hollow shafts (spool_index > 0). See TODO #1.

    @Input
    def material_name(self):
        # Default shaft material; override from the assembly if needed.
        return "Ti-6Al-4V"

    # ------------------------------------------------------------------
    # EngineComponent contract — structural placeholders (shaft carries no flow).
    # Safe defaults so the component is runnable / GUI-safe standalone.
    # ------------------------------------------------------------------
    @Input
    def pressure_ratio(self):
        return 1.0

    @Input
    def isos_efficiency(self):
        return 1.0

    @Input
    def Mach_out(self):
        return self.inflow_conditions.Mach

    @Input
    def length(self):
        return self.shaft_length

    @Input
    def radius(self):
        return self.r_tip_c_in

    # ------------------------------------------------------------------
    # Shaft length & axial stations (normalised x range is 0 .. 4.3)
    # ------------------------------------------------------------------
    @Attribute
    def shaft_length(self):
        return self.r_tip_c_in * 4.3

    @Attribute
    def compressor_x_start(self):
        return self.shaft_length * 0.4 / 4.3   # x_norm = 0.4 (compressor inlet)

    @Attribute
    def turbine_x_start(self):
        return self.shaft_length * 3.1 / 4.3   # x_norm = 3.1 (turbine inlet)

    # ------------------------------------------------------------------
    # Normalised outer profile (x_norm, r_norm); r normalised to r_tip_c_in
    # ------------------------------------------------------------------
    @Attribute
    def k0_outer_norm(self):
        return [
            (0.00, 0.000),
            (0.10, 0.298),
            (0.20, 0.390),
            (0.30, 0.436),
            (0.40, 0.450),   # compressor inlet
            (0.65, 0.505),
            (0.90, 0.565),
            (1.15, 0.624),
            (1.40, 0.680),
            (1.65, 0.740),
            (1.90, 0.850),   # compressor exit
            (2.20, 0.834),   # S-curve inter-machine start
            (2.50, 0.800),
            (2.80, 0.766),
            (3.10, 0.750),   # turbine inlet
            (3.90, 0.650),   # turbine exit
            (4.00, 0.629),   # tail ellipse
            (4.10, 0.563),
            (4.20, 0.430),
            (4.30, 0.000),   # tail tip
        ]

    # ------------------------------------------------------------------
    # Hollow-shaft profile derivation (spool_index > 0) — UNTESTED PATH
    #
    # TODO #1 (Architect): wire `inner_spool_profile_norm` from the adjacent
    #   inner spool's outer profile (assembly-level link). Until then only
    #   spool_index == 0 runs end-to-end.
    # ------------------------------------------------------------------
    @Attribute
    def hollow_outer_r(self):
        # gap(r) = max(delta_min, clearance_epsilon * r), applied INDEPENDENTLY
        # at each x station of the inner spool's outer profile.
        return [r + max(self.delta_min, self.clearance_epsilon * r)
                for _, r in self.inner_spool_profile_norm]

    @Attribute
    def hollow_outer_profile_norm(self):
        return [(x, r_new) for (x, _), r_new
                in zip(self.inner_spool_profile_norm, self.hollow_outer_r)]

    @Attribute
    def outer_profile_norm(self):
        return self.k0_outer_norm if self.spool_index == 0 \
            else self.hollow_outer_profile_norm

    # ------------------------------------------------------------------
    # De-normalised wall points (Point objects in the X_axial/Y_radial plane).
    # x_norm in [0, 4.3] maps to [0, shaft_length]; r_norm scaled by r_tip_c_in
    # (same scale on both axes, so the meridian aspect ratio is preserved and
    # x_norm = 4.3 lands exactly at shaft_length).
    # ------------------------------------------------------------------
    @Attribute
    def outer_profile_points(self):
        return [Point(x / 4.3 * self.shaft_length, r * self.r_tip_c_in, 0.0)
                for x, r in self.outer_profile_norm]

    @Attribute
    def tau_allow(self):
        # TODO #2 (Architect): `allowable_shear_stress` is NOT present in the
        #   current Material / MATERIAL_DB. Either add it to the DB, or derive
        #   it here from yield_stress (von Mises: tau = yield_stress / sqrt(3)).
        return self.material.allowable_shear_stress

    @Attribute
    def shaft_thickness(self):
        # Torsion-sized wall thickness per outer point, floored at delta_min.
        # Empty for the solid HP shaft, so the solid path never touches tau_allow.
        # TODO #3: the term under **0.25 can go negative for large torque / small
        #   r_out (complex result). Clamp once the Architect fixes the sizing law.
        return [] if self.spool_index == 0 else [
            max(self.delta_min,
                r_out - (r_out ** 4
                         - (2.0 * self.design_torque * r_out)
                         / (math.pi * self.tau_allow)) ** 0.25)
            for r_out in self.hollow_outer_r
        ]

    @Attribute
    def inner_profile_points(self):
        # Inner wall = outer wall pulled inward radially by the local thickness.
        return [Point(p.x, p.y - t, 0.0)
                for p, t in zip(self.outer_profile_points, self.shaft_thickness)]

    @Attribute
    def shaft_profile_curves(self):
        # Solid HP : outer profile -> axial closure (r = 0).
        # Hollow   : outer -> tail cap -> inner (reversed) -> nose cap.
        return [self.outer_curve, self.closing_segment] if self.spool_index == 0 \
            else [self.outer_curve, self.tail_cap, self.inner_curve, self.nose_cap]

    # ------------------------------------------------------------------
    # Shaft geometry parts
    # ------------------------------------------------------------------
    @Part
    def outer_curve(self):
        return FittedCurve(points=self.outer_profile_points, hidden=True)

    @Part
    def closing_segment(self):
        # Solid shaft: close along the axis from tail tip back to nose tip.
        return LineSegment(start=self.outer_profile_points[-1],
                           end=self.outer_profile_points[0],
                           hidden=True)

    @Part
    def inner_curve(self):
        # Hollow shafts only — inner wall traversed aft -> forward.
        return FittedCurve(points=list(reversed(self.inner_profile_points)),
                           hidden=True)

    @Part
    def tail_cap(self):
        # Hollow shafts only — radial closure outer-aft -> inner-aft.
        return LineSegment(start=self.outer_profile_points[-1],
                           end=self.inner_profile_points[-1],
                           hidden=True)

    @Part
    def nose_cap(self):
        # Hollow shafts only — radial closure inner-fwd -> outer-fwd.
        return LineSegment(start=self.inner_profile_points[0],
                           end=self.outer_profile_points[0],
                           hidden=True)

    @Part
    def shaft_profile(self):
        return ComposedCurve(built_from=self.shaft_profile_curves, hidden=True)

    @Part
    def body(self):
        # Named `body` so EngineComponent.volume / weight resolve automatically.
        return RevolvedSolid(built_from=self.shaft_profile,
                             center=Point(0.0, 0.0, 0.0),
                             direction=(1.0, 0.0, 0.0),
                             angle=2.0 * math.pi,
                             color=self.material.color)

    # ------------------------------------------------------------------
    # Turbomachine children
    # ------------------------------------------------------------------
    @Attribute
    def compressor_pressure_ratio(self):
        # Rule of thumb until the cycle analysis feeds a real PR.
        return (self.r_tip_c_in / self.r_hub_c_in) ** 2

    @Input
    def work_dir_base(self):
        # Separate work_dir per machine type avoids the stale @Attribute cache /
        # profile-swap bug seen when compressor and turbine share one folder.
        return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "Multall", "spool_{}".format(self.spool_index))

    @Part
    def compressor(self):
        # TODO #4: axial placement via the local frame's 'x'. If Stage builds its
        #   blades from ABSOLUTE coords (known issue), this translate will not
        #   move them — an explicit axial_offset input on Turbomachine/Stage is
        #   then required. Verify the rendering in the GUI.
        return Compressor(
            inflow_conditions=self.inflow_conditions,
            pressure_ratio=self.compressor_pressure_ratio,
            n_stages=self.n_stages_compressor,
            rpm=self.rpm,
            design_radius=(self.r_hub_c_in + self.r_tip_c_in) / 2.0,
            material_name=self.material_name,
            work_dir=os.path.join(self.work_dir_base, "compressor"),
            position=translate(self.position, 'x', self.compressor_x_start),
            label="C{}".format(self.spool_index),
        )

    @Part
    def turbine(self):
        # Turbine inlet state comes from the combustor exit (turbine_inflow_conditions),
        # NOT from the compressor. Expansion -> PR < 1.
        return Turbine(
            inflow_conditions=self.turbine_inflow_conditions,
            pressure_ratio=1.0 / self.compressor.pressure_ratio,
            n_stages=self.n_stages_turbine,
            rpm=self.rpm,
            design_radius=(self.r_hub_t_in + self.r_tip_t_in) / 2.0,
            material_name=self.material_name,
            work_dir=os.path.join(self.work_dir_base, "turbine"),
            position=translate(self.position, 'x', self.turbine_x_start),
            label="T{}".format(self.spool_index),
        )

    # ------------------------------------------------------------------
    # Power balance
    # ------------------------------------------------------------------
    @Attribute
    def power_required(self):
        # TODO #5: stub — replace with self.compressor.power_required [W] once
        #   Turbomachine exposes it.
        return 0.0

    @Attribute
    def power_estimated(self):
        # TODO #5: stub — replace with self.turbine.power_estimated [W] once
        #   Turbomachine exposes it.
        return 0.0

    @action(label='Run power balance')
    def power_balance(self):
        """Sequential balance: size the compressor work, then verify the turbine
        can supply it (with loss_margin) before running its high-fidelity CFD."""
        self.compressor.multall_analysis()
        # Reads the Spool-level stubs for now (see TODO #5); the target form is
        # required = self.compressor.power_required * (1 + self.loss_margin).
        required = self.power_required * (1.0 + self.loss_margin)
        if self.power_estimated >= required:
            self.turbine.multall_analysis()
        else:
            raise ValueError(
                f"Power deficit: turbine estimated {self.power_estimated:.0f} W, "
                f"required {required:.0f} W, "
                f"deficit {required - self.power_estimated:.0f} W"
            )
        # TODO #6: PARALLEL CFD — implement after sequential validation.
        # TODO #7: GEOMETRY UPDATE — needs Architect spec before implementation.


# ---------------------------------------------------------------------------
# Smoke test — single HP spool (solid shaft)
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    from parapy.gui import display

    compressor_inlet = FlowStation(
        station_number=3,
        fluid_type='air',
        p_total=250000.0,    # post-LPC HP-spool inlet [Pa]
        T_total=400.0,       # [K]
        mass_flow=25.0,      # [kg/s]
        Mach=0.45,
    )

    turbine_inlet = FlowStation(
        station_number=4,
        fluid_type='air',
        p_total=1300000.0,   # combustor exit (HPC exit minus combustor loss) [Pa]
        T_total=1500.0,      # turbine entry temperature [K]
        mass_flow=25.5,      # core flow + fuel [kg/s]
        Mach=0.30,
    )

    hp_spool = Spool(
        spool_index=0,
        inflow_conditions=compressor_inlet,
        turbine_inflow_conditions=turbine_inlet,
        r_tip_c_in=0.35,
        r_hub_c_in=0.15,
        r_hub_c_out=0.28,
        r_tip_c_out=0.34,
        r_hub_t_in=0.22,
        r_hub_t_out=0.18,
        r_tip_t_in=0.32,
        r_tip_t_out=0.38,
        rpm=15000.0,
        design_torque=50000.0,
        n_stages_compressor=5,
        n_stages_turbine=2,
        label='HP_spool',
    )

    print(f"shaft_length        [m] = {hp_spool.shaft_length:.4f}")
    print(f"compressor_x_start  [m] = {hp_spool.compressor_x_start:.4f}")
    print(f"turbine_x_start     [m] = {hp_spool.turbine_x_start:.4f}")
    print(f"compressor PR       [-] = {hp_spool.compressor_pressure_ratio:.3f}")
    print(f"shaft volume       [m3] = {hp_spool.body.volume:.6f}")

    display(hp_spool)