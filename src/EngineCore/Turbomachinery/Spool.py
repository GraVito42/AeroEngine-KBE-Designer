"""
Spool.py
========
Coaxial engine spool — couples a Compressor and a Turbine on a common shaft and
hosts the (low-fidelity -> high-fidelity) power-balance action.

Inheritance:
    Spool(EngineComponent, GeomBase)
  - EngineComponent: thermo-fluid contract, material lookup, volume/weight, position frame.
  - GeomBase: hosts the shaft RevolvedSolid and the two turbomachine children.

Coordinate system (engine frame): X axial, Y radial, Z tangential.
Shaft geometry is revolved about the global X axis.
"""

# Ensure project root is in sys.path when running this file directly
import sys
from pathlib import Path
for parent in Path(__file__).resolve().parents:
    if (parent / "EngineCore").exists() and (parent / "Thermodynamics").exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break

import math
import os

from parapy.core import Input, Attribute, Part, action
from parapy.geom import (GeomBase, Point, FittedCurve, LineSegment,
                         ComposedCurve, RevolvedSolid, BezierCurve)

from EngineCore.Material import Material
from EngineCore.Turbomachinery.Compressor import Compressor
from EngineCore.Turbomachinery.Turbine import Turbine
from Thermodynamics.FlowStation import FlowStation
from EngineCore.Turbomachinery.MultallUtilities.MultallSolver import parse_shaft_power
from concurrent.futures import ThreadPoolExecutor


class Spool(GeomBase):
    """Compressor + Turbine on one shaft, with a sequential power balance."""

    # ------------------------------------------------------------------
    # Inputs — Sizing, Sparing, and Architecture
    # ------------------------------------------------------------------
    design_radius = Input()            # Meanline radius for meangen [m]
    compressor_delta_h = Input()       # Total specific enthalpy rise [J/kg]
    compressor_n_stages = Input()      # Number of compressor stages
    turbine_n_stages = Input()         # Number of turbine stages
    shaft_rpm = Input()                # Shaft rotational speed [rev/min]

    compressor_inflow = Input()        # FlowStation at compressor inlet
    turbine_inflow = Input()           # FlowStation at turbine inlet

    compressor_reaction_coeff = Input(0.5)  # Compressor reaction coefficient
    turbine_reaction_coeff = Input(0.5)     # Turbine reaction coefficient

    gap_length = Input()               # Inter-machine axial gap [m]
    x_start_compressor = Input()       # Compressor LE X [m]
    # x_start and x_end are now derived @Attributes (see below)

    tip_fraction    = Input(0.3)       # fraction of inlet_length ahead of compressor LE occupied by spool nose
    bottom_fraction = Input(0.3)       # fraction of nozzle_length behind turbine exit occupied by spool tail
    nozzle_length   = Input(0.45)      # nozzle axial length [m], needed to compute x_end
    inlet_length    = Input(0.55)      # inlet duct axial length [m], needed to compute x_start
    spool_sheet_thickness = Input(0.015)   # Shaft shell thickness [m]

    isos_efficiency = Input(0.90)      # Isentropic efficiency
    spool_index = Input(0)             # 0 = HP (innermost), 1 = IP, 2 = LP
    show_compressor = Input(False)     # Defer compressor lofting by default
    show_turbine = Input(False)        # Defer turbine lofting by default

    show_geometry = Input(True)
    """If False, the shaft body and stages are hidden by default."""

    postprocess_results = Input(True)
    """If True, run PostPy after each turbomachine's CFD run. Forwarded to
    Compressor/Turbine -> MultallSolver."""

    postpy_max_instances = Input(2)
    """Max number of extra passage/blade instances PostPy generates per row.
    Forwarded to Compressor/Turbine -> MultallSolver."""

    _cfd_runs_counter = Input(0)       # Internal counter to invalidate CFD-based attributes

    log_low_fidelity = Input(False)
    """If True: show MEANGEN and STAGEN stdout/stderr in the console"""

    log_high_fidelity = Input(False)
    """If True: show MULTALL CFD stdout/stderr in the console"""

    thrust_needed = Input(30000.0)      # Required engine thrust [N]
    ext_systems_power = Input(50000.0)  # Power absorbed by auxiliary systems [W]
    flight_velocity = Input(250.0)      # Flight velocity [m/s]
    loss_margin = Input(0.1)            # Power loss margin percentage (must be positive)

    @Input
    def turbine_delta_h(self):
        """Calculated turbine enthalpy drop [J/kg] based on required power components."""
        if self.loss_margin < 0:
            raise ValueError("loss_margin must be positive")
        return ((self.thrust_power + self.compressor_power + self.ext_systems_power) / self.turbine_inflow.mass_flow) * (1.0 + self.loss_margin)

    shaft_material = Input("Ti-6Al-4V")
    compressor_rotor_material = Input("Ti-6Al-4V")
    compressor_stator_material = Input("Al-2024-T3")
    turbine_rotor_material = Input("Inconel-718")
    turbine_stator_material = Input("Inconel-718")

    # ------------------------------------------------------------------
    # Material representations for color/density lookup
    # ------------------------------------------------------------------
    @Part
    def shaft_material_instance(self):
        """Material representation for shaft color/density lookup."""
        return Material(material_name=self.shaft_material)

    @Part
    def compressor_rotor_material_instance(self):
        """Material representation for compressor rotor color/density lookup."""
        return Material(material_name=self.compressor_rotor_material)

    @Part
    def compressor_stator_material_instance(self):
        """Material representation for compressor stator color/density lookup."""
        return Material(material_name=self.compressor_stator_material)

    @Part
    def turbine_rotor_material_instance(self):
        """Material representation for turbine rotor color/density lookup."""
        return Material(material_name=self.turbine_rotor_material)

    @Part
    def turbine_stator_material_instance(self):
        """Material representation for turbine stator color/density lookup."""
        return Material(material_name=self.turbine_stator_material)

    # ------------------------------------------------------------------
    # Derived Axial Extents
    # ------------------------------------------------------------------
    @Attribute
    def x_start(self):
        """Spool nose start X [m]: compressor LE minus tip_fraction of inlet_length."""
        return self.x_start_compressor - self.tip_fraction * self.inlet_length

    @Attribute
    def x_end(self):
        """Spool end X [m]: turbine exit plus bottom_fraction of nozzle_length."""
        return self.turbine_end_x + self.bottom_fraction * self.nozzle_length

    @Attribute
    def length(self):
        """Length of the spool shaft [m]."""
        return self.x_end - self.x_start

    # ------------------------------------------------------------------
    # Derived Sizing & Radii from Low-Fidelity CFD
    # ------------------------------------------------------------------
    @Attribute
    def compressor_hub_in(self):
        """Inlet hub radius of the compressor [m] derived from stage data."""
        return self.compressor.stage_data[0]['rotor']['r_sections'][0]

    @Attribute
    def compressor_hub_out(self):
        """Outlet hub radius of the compressor [m] derived from stage data."""
        return self.compressor.stage_data[-1]['stator']['r_sections'][0]

    @Attribute
    def turbine_hub_in(self):
        """Inlet hub radius of the turbine [m] derived from stage data."""
        return self.turbine.stage_data[0]['stator']['r_sections'][0]

    @Attribute
    def turbine_hub_out(self):
        """Outlet hub radius of the turbine [m] derived from stage data."""
        return self.turbine.stage_data[-1]['rotor']['r_sections'][0]

    @Attribute
    def compressor_tip_radii(self):
        """Compressor inlet and outlet tip radii [m] (r_tip_in, r_tip_out)."""
        return (
            self.compressor.stage_data[0]['rotor']['r_sections'][-1],
            self.compressor.stage_data[-1]['stator']['r_sections'][-1]
        )

    @Attribute
    def turbine_tip_radii(self):
        """Turbine inlet and outlet tip radii [m] (r_tip_in, r_tip_out)."""
        return (
            self.turbine.stage_data[0]['stator']['r_sections'][-1],
            self.turbine.stage_data[-1]['rotor']['r_sections'][-1]
        )

    @Attribute
    def compressor_tip_r_in(self):
        """Tip radius at compressor inlet [m] — from first Stage rotor r_sections."""
        return self.compressor.body[0].rotor_r_sections[-1]

    @Attribute
    def compressor_tip_r_out(self):
        """Tip radius at compressor outlet [m] — from last Stage stator r_sections."""
        return self.compressor.body[-1].stator_r_sections[-1]

    @Attribute
    def turbine_tip_r_in(self):
        """Tip radius at turbine inlet [m] — from first Stage stator r_sections."""
        return self.turbine.body[0].stator_r_sections[-1]

    @Attribute
    def turbine_tip_r_out(self):
        """Tip radius at turbine outlet [m] — from last Stage rotor r_sections."""
        return self.turbine.body[-1].rotor_r_sections[-1]

    @Attribute
    def compressor_axial_length(self):
        """Total axial length of the compressor [m]."""
        return sum(self.compressor.stage_axial_lengths)

    @Attribute
    def turbine_axial_length(self):
        """Total axial length of the turbine [m]."""
        return sum(self.turbine.stage_axial_lengths)

    # ------------------------------------------------------------------
    # Dynamic Axial Stations
    # ------------------------------------------------------------------
    @Attribute
    def compressor_end_x(self):
        """Compressor exit axial position [m]."""
        return self.x_start_compressor + self.compressor_axial_length

    @Attribute
    def turbine_start_x(self):
        """Turbine inlet axial position [m]."""
        return self.compressor_end_x + self.gap_length

    @Attribute
    def turbine_end_x(self):
        """Turbine exit axial position [m]."""
        return self.turbine_start_x + self.turbine_axial_length

    # ------------------------------------------------------------------
    # Shaft Profile Curve Points
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Shaft Profile Curve Points — parabolic (quadratic Bézier) end caps
    # ------------------------------------------------------------------
    @Attribute
    def nose_cap_control_points(self):
        """Three control points of the convex parabolic nose cap.
        P0 = axis tip at x_start (input-set x).
        P1 = control at hub radius, axially centered -> convex outward bulge,
             finite (conical) tip tangent (no r=0 degeneracy), axial tangent at
             the hub join (smooth transition to the compressor body).
        P2 = first hub point under the compressor first stage.
        Assumes x_start < x_start_compressor (guaranteed by the axial stack)."""
        return [
            Point(self.x_start, 0.0, 0.0),
            Point(0.5 * (self.x_start + self.x_start_compressor),
                  self.compressor_hub_in, 0.0),
            Point(self.x_start_compressor, self.compressor_hub_in, 0.0),
        ]

    @Attribute
    def tail_cap_control_points(self):
        """Three control points of the convex parabolic tail cap (mirror of nose).
        P0 = last hub point under the turbine last stage (turbine_end_x).
        P1 = control at hub radius, axially centered -> convex outward bulge,
             axial tangent at the turbine join, finite tip tangent at x_end.
        P2 = axis tip at x_end (input-set x).
        Assumes turbine_end_x < x_end (guaranteed by the axial stack)."""
        return [
            Point(self.turbine_end_x, self.turbine_hub_out, 0.0),
            Point(0.5 * (self.turbine_end_x + self.x_end),
                  self.turbine_hub_out, 0.0),
            Point(self.x_end, 0.0, 0.0),
        ]

    # ------------------------------------------------------------------
    # Shaft Geometry Parts
    # ------------------------------------------------------------------
    @Part
    def nose_cap_curve(self):
        """Convex parabolic nose cap (quadratic Bézier)."""
        return BezierCurve(control_points=self.nose_cap_control_points, hidden=True)

    @Part
    def compressor_body_segment(self):
        """Linear taper compressor body segment."""
        return LineSegment(
            start=Point(self.x_start_compressor, self.compressor_hub_in, 0.0),
            end=Point(self.compressor_end_x, self.compressor_hub_out, 0.0),
            hidden=True
        )

    @Part
    def gap_transition_segment(self):
        """Straight transition line between compressor exit and turbine inlet."""
        return LineSegment(
            start=Point(self.compressor_end_x, self.compressor_hub_out, 0.0),
            end=Point(self.turbine_start_x, self.turbine_hub_in, 0.0),
            hidden=True
        )

    @Part
    def turbine_body_segment(self):
        """Linear taper turbine body segment."""
        return LineSegment(
            start=Point(self.turbine_start_x, self.turbine_hub_in, 0.0),
            end=Point(self.turbine_end_x, self.turbine_hub_out, 0.0),
            hidden=True
        )

    @Part
    def tail_cap_curve(self):
        """Convex parabolic tail cap (quadratic Bézier)."""
        return BezierCurve(control_points=self.tail_cap_control_points, hidden=True)

    @Part
    def axis_closure_segment(self):
        """Closure along the rotational axis (r = 0) from tail tip to nose tip."""
        return LineSegment(
            start=Point(self.x_end, 0.0, 0.0),
            end=Point(self.x_start, 0.0, 0.0),
            hidden=True
        )

    @Attribute
    def shaft_profile_curves(self):
        """List of curves making up the shaft meridian profile."""
        return [
            self.nose_cap_curve,
            self.compressor_body_segment,
            self.gap_transition_segment,
            self.turbine_body_segment,
            self.tail_cap_curve,
            self.axis_closure_segment
        ]

    @Part
    def shaft_profile(self):
        """The composed meridian profile wire."""
        return ComposedCurve(built_from=self.shaft_profile_curves, hidden=True)

    @Part
    def body(self):
        """The revolved 3D solid shaft revolved about the X-axis."""
        return RevolvedSolid(
            built_from=self.shaft_profile,
            center=Point(0.0, 0.0, 0.0),
            direction=(1.0, 0.0, 0.0),
            angle=2.0 * math.pi,
            color=self.shaft_material_instance.color,
            hidden=not self.show_geometry,
        )

    # ------------------------------------------------------------------
    # Turbomachine Children
    # ------------------------------------------------------------------
    @Attribute
    def compressor_pressure_ratio(self):
        """Derive compressor pressure ratio from compressor_delta_h and inlet conditions."""
        inflow = self.compressor_inflow
        eta = self.isos_efficiency
        temp = 1.0 + (eta * self.compressor_delta_h) / (inflow.cp * inflow.T_total)
        return temp ** (inflow.gamma / (inflow.gamma - 1.0))

    @Attribute
    def turbine_pressure_ratio(self):
        """Derive turbine pressure ratio from turbine_delta_h and inlet conditions."""
        inflow = self.turbine_inflow
        eta = self.isos_efficiency
        temp = 1.0 - self.turbine_delta_h / (eta * inflow.cp * inflow.T_total)
        if temp <= 0:
            raise ValueError(f"Turbine delta_h is too large, resulting in non-physical negative temperatures: temp = {temp}")
        return temp ** (inflow.gamma / (inflow.gamma - 1.0))

    @Input
    def work_dir_base(self):
        """Base directory for this spool's Multall solver runs."""
        return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "Multall", f"spool_{self.spool_index}")

    @Part
    def compressor(self):
        """The compressor turbomachine child.
        Marked hidden=True to defer blade lofting CAD generation until requested.
        """
        return Compressor(
            inflow_conditions=self.compressor_inflow,
            pressure_ratio=self.compressor_pressure_ratio,
            n_stages=self.compressor_n_stages,
            rpm=self.shaft_rpm,
            design_radius=self.design_radius,
            reaction=self.compressor_reaction_coeff,
            material_name=self.compressor_rotor_material,
            stator_material_name=self.compressor_stator_material,
            work_dir=os.path.join(self.work_dir_base, "compressor"),
            axial_offset=self.x_start_compressor,
            label=f"C_{self.label}" if hasattr(self, 'label') else "C",
            enable_cad_chord_capping=False,
            show_blades=self.show_compressor,
            show_geometry=self.show_geometry,
            postprocess_results=self.postprocess_results,
            postpy_max_instances=self.postpy_max_instances,
            log_low_fidelity=self.log_low_fidelity,
            log_high_fidelity=self.log_high_fidelity,
        )

    @Part
    def turbine(self):
        """The turbine turbomachine child.
        Marked hidden=True to defer blade lofting CAD generation until requested.
        """
        return Turbine(
            inflow_conditions=self.turbine_inflow,
            pressure_ratio=self.turbine_pressure_ratio,
            n_stages=self.turbine_n_stages,
            rpm=self.shaft_rpm,
            design_radius=self.design_radius,
            reaction=self.turbine_reaction_coeff,
            material_name=self.turbine_rotor_material,
            stator_material_name=self.turbine_stator_material,
            work_dir=os.path.join(self.work_dir_base, "turbine"),
            axial_offset=self.turbine_start_x,
            label=f"T_{self.label}" if hasattr(self, 'label') else "T",
            enable_cad_chord_capping=True,
            show_blades=self.show_turbine,
            show_geometry=self.show_geometry,
            postprocess_results=self.postprocess_results,
            postpy_max_instances=self.postpy_max_instances,
            log_low_fidelity=self.log_low_fidelity,
            log_high_fidelity=self.log_high_fidelity,
        )

    # ------------------------------------------------------------------
    # Power and Sequential Power Balance
    # ------------------------------------------------------------------
    @Attribute
    def thrust_power(self):
        """Propulsive power required to generate thrust [W]. Only driven by LP spool (index 2)."""
        if self.spool_index == 2:
            return self.thrust_needed * self.flight_velocity
        return 0.0

    @Attribute
    def compressor_power(self):
        """Power required by the compressor [W].
        If Multall CFD has run, it parses the shaft power from the CFD results.
        Otherwise, it falls back to the thermodynamic design power.
        """
        self._cfd_runs_counter  # Register dependency for invalidation
        work_dir = self.compressor.work_dir
        if os.path.exists(os.path.join(work_dir, "global.plt")):
            try:
                return parse_shaft_power(
                    work_dir=work_dir,
                    rpm=self.shaft_rpm,
                    gamma=self.compressor_inflow.gamma,
                    R=self.compressor.effective_gas_constant,
                    mass_flow=self.compressor_inflow.mass_flow,
                    machine_type='compressor'
                )
            except Exception as e:
                print(f"WARNING: failed to parse compressor shaft power: {e}", file=sys.stderr)

        # Fallback to thermodynamic design power
        return self.compressor_inflow.mass_flow * self.compressor_delta_h

    @Attribute
    def power_estimated(self):
        """Power supplied/estimated by the turbine [W].
        If Multall CFD has run for the turbine, it parses the shaft power.
        Otherwise, it falls back to the thermodynamic design power.
        """
        self._cfd_runs_counter  # Register dependency for invalidation
        work_dir = self.turbine.work_dir
        if os.path.exists(os.path.join(work_dir, "global.plt")):
            try:
                return parse_shaft_power(
                    work_dir=work_dir,
                    rpm=self.shaft_rpm,
                    gamma=self.turbine_inflow.gamma,
                    R=self.turbine.effective_gas_constant,
                    mass_flow=self.turbine_inflow.mass_flow,
                    machine_type='turbine'
                )
            except Exception as e:
                print(f"WARNING: failed to parse turbine shaft power: {e}", file=sys.stderr)

        # Fallback to thermodynamic design power
        return self.turbine_inflow.mass_flow * self.turbine_delta_h

    def measure_power_balance(self) -> dict:
        """Runs compressor CFD and turbine CFD IN PARALLEL using
        ThreadPoolExecutor(max_workers=2).
        After both complete, increments self._cfd_runs_counter += 1
        Returns a dict of measured values.
        """
        if self.log_high_fidelity:
            print("[Power Balance] Running Compressor and Turbine CFD in parallel...")
        with ThreadPoolExecutor(max_workers=2) as executor:
            fut_comp = executor.submit(self.compressor.multall_analysis)
            fut_turb = executor.submit(self.turbine.multall_analysis)
            fut_comp.result()
            fut_turb.result()

        self._cfd_runs_counter += 1

        try:
            t_power = parse_shaft_power(
                work_dir=self.turbine.work_dir,
                rpm=self.shaft_rpm,
                gamma=self.turbine_inflow.gamma,
                R=self.turbine.effective_gas_constant,
                mass_flow=self.turbine_inflow.mass_flow,
                machine_type='turbine'
            )
        except Exception:
            t_power = self.turbine_inflow.mass_flow * self.turbine_delta_h

        try:
            c_power = parse_shaft_power(
                work_dir=self.compressor.work_dir,
                rpm=self.shaft_rpm,
                gamma=self.compressor_inflow.gamma,
                R=self.compressor.effective_gas_constant,
                mass_flow=self.compressor_inflow.mass_flow,
                machine_type='compressor'
            )
        except Exception:
            c_power = self.compressor_inflow.mass_flow * self.compressor_delta_h

        return {
            "turbine_power": float(t_power),
            "compressor_power": float(c_power),
            "n_turbine_stages": int(self.turbine_n_stages),
            "mass_flow": float(self.turbine_inflow.mass_flow),
        }

    @Attribute
    def total_weight(self):
        """Total weight of the spool: shaft (thin shell) + compressor + turbine [kg].

        The shaft is modelled as a thin sheet-metal shell rather than a solid:
        mass = wetted area * sheet thickness * density, mirroring the Duct.weight
        convention (area * sheet_thickness * density).
        """
        shaft_weight = (self.body.area
                        * self.spool_sheet_thickness
                        * self.shaft_material_instance.density)
        return shaft_weight + self.compressor.weight + self.turbine.weight

    @Attribute
    def postpy_output_paths(self):
        """PostPy ParaView .dat paths for compressor and turbine, or None
        per machine if not (yet) generated."""
        self._cfd_runs_counter  # register dependency for invalidation
        return {
            'compressor': self.compressor.postpy_output_paths,
            'turbine': self.turbine.postpy_output_paths,
        }


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

    # TIT = 1500 K
    turbine_inlet = FlowStation(
        station_number=4,
        fluid_type='air',
        p_total=1300000.0,   # combustor exit [Pa]
        T_total=1500.0,      # turbine entry temperature [K]
        mass_flow=25.5,      # core flow + fuel [kg/s]
        Mach=0.30,
    )

    hp_spool = Spool(
        design_radius=0.20,
        compressor_delta_h=150000.0,   # [J/kg]
        compressor_n_stages=5,
        turbine_n_stages=3,
        shaft_rpm=12000.0,
        compressor_inflow=compressor_inlet,
        turbine_inflow=turbine_inlet,
        gap_length=0.25,
        x_start_compressor=0.4,
        isos_efficiency=0.90,
        label='HP_spool',
    )

    print("=== SPOOL INITIALIZATION SUCCESS ===")
    print(f"x_start              [m] = {hp_spool.x_start:.4f} (expected: 0.2350)")
    print(f"x_start_compressor   [m] = {hp_spool.x_start_compressor:.4f} (expected: 0.4000)")
    print(f"turbine_end_x        [m] = {hp_spool.turbine_end_x:.4f}")
    print(f"x_end                [m] = {hp_spool.x_end:.4f}")
    print(f"compressor_hub_in    [m] = {hp_spool.compressor_hub_in:.4f}")
    print(f"compressor_hub_out   [m] = {hp_spool.compressor_hub_out:.4f}")
    print(f"turbine_hub_in       [m] = {hp_spool.turbine_hub_in:.4f}")
    print(f"turbine_hub_out      [m] = {hp_spool.turbine_hub_out:.4f}")
    print(f"compressor_axial_len [m] = {hp_spool.compressor_axial_length:.4f}")
    print(f"turbine_axial_len    [m] = {hp_spool.turbine_axial_length:.4f}")
    print(f"shaft_length         [m] = {hp_spool.length:.4f}")
    print(f"shaft volume        [m3] = {hp_spool.body.volume:.6f}")
    print(f"compressor power     [W] = {hp_spool.compressor_power:.2f}")
    print(f"power estimated      [W] = {hp_spool.power_estimated:.2f}")
    print(f"calculated delta_h[J/kg] = {hp_spool.turbine_delta_h:.2f}")
    print(f"shaft weight        [kg] = {hp_spool.body.area * hp_spool.spool_sheet_thickness * hp_spool.shaft_material_instance.density:.3f}")
    print(f"compressor weight   [kg] = {hp_spool.compressor.weight:.3f}")
    print(f"turbine weight      [kg] = {hp_spool.turbine.weight:.3f}")
    print(f"spool total weight  [kg] = {hp_spool.total_weight:.3f}")

    display(hp_spool, autodraw=True)