"""
Spool2.py
=========
Coaxial engine spool — couples a Compressor and a Turbine on a common shaft and
hosts the (low-fidelity -> high-fidelity) power-balance action.

Supports single spools, primary spools (innermost spools in nested architectures),
and secondary spools (outer spools nested coaxially over previous spools).
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
                         ComposedCurve, RevolvedSolid)

from EngineCore.Material import Material
from EngineCore.Turbomachinery.Compressor import Compressor
from EngineCore.Turbomachinery.Turbine import Turbine
from Thermodynamics.FlowStation import FlowStation
from EngineCore.Turbomachinery.Multall.MultallSolver import parse_shaft_power


class Spool(GeomBase):
    """Compressor + Turbine on one shaft, supporting nested architectures."""

    # ------------------------------------------------------------------
    # Inputs — Sizing, Sparing, and Architecture
    # ------------------------------------------------------------------
    architecture = Input('single')      # 'single', 'primary', or 'secondary'
    gap_radius = Input(None)            # Gap radius for primary/nested spools [m]
    prev_gap_radius = Input(None)       # Previous spool's gap radius (required for secondary) [m]

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
    x_start = Input(0.0)               # Spool start X [m]
    x_start_compressor = Input()       # Compressor LE X [m]
    x_end = Input()                    # Spool end X [m]

    isos_efficiency = Input(0.90)      # Isentropic efficiency
    spool_index = Input(0)             # 0 = HP (innermost), 1 = IP, 2 = LP
    _cfd_runs_counter = Input(0)       # Internal counter to invalidate CFD-based attributes

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
    # Validation and Sanity Checks
    # ------------------------------------------------------------------
    @Attribute
    def validation_warnings(self):
        """Sanity checks for spool nested architecture configurations."""
        w = []
        if self.architecture == 'primary':
            if self.gap_radius is None:
                w.append("Spool2: gap_radius must be specified for primary spool.")
            elif self.gap_radius <= 0:
                w.append("Spool2: gap_radius must be positive.")
        elif self.architecture == 'secondary':
            if self.prev_gap_radius is None:
                w.append("Spool2: prev_gap_radius must be specified for secondary spool.")
            else:
                if self.prev_gap_radius <= 0:
                    w.append("Spool2: prev_gap_radius must be positive.")
                min_hub = min(self.compressor_hub_in, self.compressor_hub_out,
                              self.turbine_hub_in, self.turbine_hub_out)
                if self.prev_gap_radius >= min_hub:
                    w.append(f"Spool2: prev_gap_radius ({self.prev_gap_radius}) must be less than min hub radius ({min_hub}) to ensure positive thickness.")
        return w

    # ------------------------------------------------------------------
    # Shaft Profile Curve Points
    # ------------------------------------------------------------------
    @Attribute
    def nose_cap_points(self):
        """Points defining the ellipsoidal nose cap curve."""
        if self.architecture == 'secondary':
            return []
        x1 = self.x_start
        x2 = self.x_start_compressor
        r_hub = self.compressor_hub_in
        dx = x2 - x1
        if dx <= 0:
            raise ValueError(f"x_start_compressor ({x2}) must be greater than x_start ({x1})")
        pts = []
        for i in range(5):
            t = i / 4.0
            x_val = x1 + t * dx
            r_val = r_hub * math.sqrt(1.0 - (1.0 - t) ** 2)
            pts.append(Point(x_val, r_val, 0.0))
        return pts

    @Attribute
    def tail_cap_points(self):
        """Points defining the ellipsoidal tail cap curve."""
        if self.architecture == 'secondary':
            return []
        x1 = self.turbine_end_x
        x2 = self.x_end
        r_hub = self.turbine_hub_out
        dx = x2 - x1
        if dx <= 0:
            raise ValueError(f"x_end ({x2}) must be greater than turbine_end_x ({x1})")
        pts = []
        for i in range(5):
            t = i / 4.0
            x_val = x1 + t * dx
            r_val = r_hub * math.sqrt(1.0 - t ** 2)
            pts.append(Point(x_val, r_val, 0.0))
        return pts

    # ------------------------------------------------------------------
    # Shaft Geometry Parts
    # ------------------------------------------------------------------
    @Part
    def nose_cap_curve(self):
        """Ellipsoidal nose cap curve."""
        return FittedCurve(
            points=self.nose_cap_points,
            quantify=1 if self.architecture in ('single', 'primary') else 0,
            hidden=True
        )

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
            quantify=0 if (self.architecture == 'primary' or (self.architecture == 'secondary' and self.gap_radius is not None)) else 1,
            hidden=True
        )

    @Part
    def gap_step_in(self):
        """Vertical step from compressor exit hub to gap_radius."""
        return LineSegment(
            start=Point(self.compressor_end_x, self.compressor_hub_out, 0.0),
            end=Point(self.compressor_end_x, self.gap_radius, 0.0),
            quantify=1 if ((self.architecture == 'primary' or (self.architecture == 'secondary' and self.gap_radius is not None))
                           and abs(self.compressor_hub_out - self.gap_radius) > 1e-6) else 0,
            hidden=True
        )

    @Part
    def gap_shaft(self):
        """Horizontal shaft running at gap_radius through the gap."""
        return LineSegment(
            start=Point(self.compressor_end_x, self.gap_radius, 0.0),
            end=Point(self.turbine_start_x, self.gap_radius, 0.0),
            quantify=1 if ((self.architecture == 'primary' or (self.architecture == 'secondary' and self.gap_radius is not None))
                           and abs(self.turbine_start_x - self.compressor_end_x) > 1e-6) else 0,
            hidden=True
        )

    @Part
    def gap_step_out(self):
        """Vertical step from gap_radius to turbine entry hub."""
        return LineSegment(
            start=Point(self.turbine_start_x, self.gap_radius, 0.0),
            end=Point(self.turbine_start_x, self.turbine_hub_in, 0.0),
            quantify=1 if ((self.architecture == 'primary' or (self.architecture == 'secondary' and self.gap_radius is not None))
                           and abs(self.turbine_hub_in - self.gap_radius) > 1e-6) else 0,
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
        """Ellipsoidal tail cap curve."""
        return FittedCurve(
            points=self.tail_cap_points,
            quantify=1 if self.architecture in ('single', 'primary') else 0,
            hidden=True
        )

    @Part
    def axis_closure_segment(self):
        """Closure along the rotational axis (r = 0) from tail tip to nose tip."""
        return LineSegment(
            start=Point(self.x_end, 0.0, 0.0),
            end=Point(self.x_start, 0.0, 0.0),
            quantify=1 if self.architecture in ('single', 'primary') else 0,
            hidden=True
        )

    @Part
    def start_segment(self):
        """LineSegment defining the start/front face of a secondary spool."""
        return LineSegment(
            start=Point(self.x_start, self.prev_gap_radius, 0.0),
            end=Point(self.x_start_compressor, self.compressor_hub_in, 0.0),
            quantify=1 if (self.architecture == 'secondary' and
                           math.sqrt((self.x_start_compressor - self.x_start) ** 2 +
                                     (self.compressor_hub_in - self.prev_gap_radius) ** 2) > 1e-6) else 0,
            hidden=True
        )

    @Part
    def end_segment(self):
        """LineSegment defining the end/back face of a secondary spool."""
        return LineSegment(
            start=Point(self.turbine_end_x, self.turbine_hub_out, 0.0),
            end=Point(self.x_end, self.prev_gap_radius, 0.0),
            quantify=1 if (self.architecture == 'secondary' and
                           math.sqrt((self.x_end - self.turbine_end_x) ** 2 +
                                     (self.turbine_hub_out - self.prev_gap_radius) ** 2) > 1e-6) else 0,
            hidden=True
        )

    @Part
    def inner_closure_segment(self):
        """LineSegment defining the inner hole boundary of a secondary spool."""
        return LineSegment(
            start=Point(self.x_end, self.prev_gap_radius, 0.0),
            end=Point(self.x_start, self.prev_gap_radius, 0.0),
            quantify=1 if (self.architecture == 'secondary' and abs(self.x_end - self.x_start) > 1e-6) else 0,
            hidden=True
        )

    @Attribute
    def shaft_profile_curves(self):
        """List of curves making up the shaft meridian profile."""
        # Check warnings on validation
        warnings = self.validation_warnings
        if warnings:
            raise ValueError(f"Validation failed for Spool2: {warnings}")

        curves = []
        # Front face / nose cap
        if self.architecture in ('single', 'primary'):
            if len(self.nose_cap_curve) > 0:
                curves.append(self.nose_cap_curve[0])
        else: # secondary
            if len(self.start_segment) > 0:
                curves.append(self.start_segment[0])

        # Compressor outer body
        curves.append(self.compressor_body_segment)

        # Gap transition
        if self.architecture == 'primary' or (self.architecture == 'secondary' and self.gap_radius is not None):
            if len(self.gap_step_in) > 0:
                curves.append(self.gap_step_in[0])
            if len(self.gap_shaft) > 0:
                curves.append(self.gap_shaft[0])
            if len(self.gap_step_out) > 0:
                curves.append(self.gap_step_out[0])
        else:
            if len(self.gap_transition_segment) > 0:
                curves.append(self.gap_transition_segment[0])

        # Turbine outer body
        curves.append(self.turbine_body_segment)

        # Rear face / tail cap
        if self.architecture in ('single', 'primary'):
            if len(self.tail_cap_curve) > 0:
                curves.append(self.tail_cap_curve[0])
            if len(self.axis_closure_segment) > 0:
                curves.append(self.axis_closure_segment[0])
        else: # secondary
            if len(self.end_segment) > 0:
                curves.append(self.end_segment[0])
            if len(self.inner_closure_segment) > 0:
                curves.append(self.inner_closure_segment[0])

        return curves

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
            color=self.shaft_material_instance.color
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
        """The compressor turbomachine child."""
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
            enable_cad_chord_capping=True,
        )

    @Part
    def turbine(self):
        """The turbine turbomachine child."""
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
        """Power required by the compressor [W]."""
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
                print(f"Warning: failed to parse compressor shaft power: {e}")

        return self.compressor_inflow.mass_flow * self.compressor_delta_h

    @Attribute
    def power_estimated(self):
        """Power supplied/estimated by the turbine [W]."""
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
                print(f"Warning: failed to parse turbine shaft power: {e}")

        return self.turbine_inflow.mass_flow * self.turbine_delta_h

    @action(label='Run power balance')
    def power_balance(self):
        """Sequential balance action."""
        print("[Power Balance] Running Compressor CFD...")
        self.compressor.multall_analysis()
        self._cfd_runs_counter += 1

        turbine_power_gen = self.turbine_delta_h * self.turbine_inflow.mass_flow
        remaining_power = turbine_power_gen - self.compressor_power
        required_power = self.thrust_power + self.ext_systems_power
        
        print(f"[Power Balance] Turbine Power Gen: {turbine_power_gen:.0f} W")
        print(f"[Power Balance] Compressor CFD Power: {self.compressor_power:.0f} W")
        print(f"[Power Balance] Remaining Power: {remaining_power:.0f} W")
        print(f"[Power Balance] Required Power (Thrust + Ext): {required_power:.0f} W")

        if remaining_power >= required_power:
            print("[Power Balance] Power check passed. Running Turbine CFD...")
            self.turbine.multall_analysis()
            self._cfd_runs_counter += 1
            print("[Power Balance] Power balance complete.")
        else:
            print("UPDATE GEOMETRY")
            raise ValueError("UPDATE GEOMETRY")

    @Attribute
    def total_weight(self):
        """Total weight of the spool: shaft + compressor + turbine [kg]."""
        shaft_weight = self.body.volume * self.shaft_material_instance.density
        return shaft_weight + self.compressor.weight + self.turbine.weight

    def info_next_spool(self):
        """Extract important geometric information from this spool for the next nested spool.
        
        Returns
        -------
        dict
            A dictionary containing design_radius, gap_length, x_compressor_end,
            r_compressor_end, x_turbine_start, and r_turbine_start.
        """
        return {
            'design_radius': self.design_radius,
            'gap_length': self.gap_length,
            'gap_lenght': self.gap_length,  # Support prompt's typo safely
            'x_compressor_end': self.compressor_end_x,
            'r_compressor_end': self.compressor_hub_out,
            'x_turbine_start': self.turbine_start_x,
            'r_turbine_start': self.turbine_hub_in
        }


# ---------------------------------------------------------------------------
# Smoke test — HP (primary) + LP (secondary) nested twin-spool test
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    from parapy.gui import display

    # HP spool (primary) flow conditions
    compressor_inlet_hp = FlowStation(
        station_number=3,
        fluid_type='air',
        p_total=250000.0,
        T_total=400.0,
        mass_flow=25.0,
        Mach=0.45,
    )

    turbine_inlet_hp = FlowStation(
        station_number=4,
        fluid_type='air',
        p_total=1300000.0,
        T_total=1500.0,
        mass_flow=25.5,
        Mach=0.30,
    )

    # LP spool (secondary) flow conditions
    compressor_inlet_lp = FlowStation(
        station_number=1,
        fluid_type='air',
        p_total=101325.0,
        T_total=288.15,
        mass_flow=65.0,
        Mach=0.50,
    )

    turbine_inlet_lp = FlowStation(
        station_number=5,
        fluid_type='air',
        p_total=350000.0,
        T_total=1000.0,
        mass_flow=65.5,
        Mach=0.35,
    )

    print("=== INITIALIZING HP SPOOL (PRIMARY) ===")
    hp_spool = Spool(
        architecture='primary',
        gap_radius=0.12,
        design_radius=0.20,
        compressor_delta_h=150000.0,
        compressor_n_stages=5,
        turbine_n_stages=3,
        shaft_rpm=12000.0,
        compressor_inflow=compressor_inlet_hp,
        turbine_inflow=turbine_inlet_hp,
        gap_length=0.25,
        x_start=0.0,
        x_start_compressor=0.4,
        x_end=1.5,
        isos_efficiency=0.90,
        label='HP_spool',
    )

    print(f"HP shaft volume: {hp_spool.body.volume:.6f} m3")
    print(f"HP total weight: {hp_spool.total_weight:.3f} kg")

    print("\n=== INITIALIZING LP SPOOL (SECONDARY) ===")
    lp_spool = Spool(
        architecture='secondary',
        prev_gap_radius=hp_spool.gap_radius,
        design_radius=0.28,
        compressor_delta_h=80000.0,
        compressor_n_stages=3,
        turbine_n_stages=2,
        shaft_rpm=4500.0,
        compressor_inflow=compressor_inlet_lp,
        turbine_inflow=turbine_inlet_lp,
        gap_length=1.1,
        x_start=0.0,
        x_start_compressor=0.0,
        x_end=2.0,
        isos_efficiency=0.90,
        label='LP_spool',
        spool_index=2, # LP spool drives thrust
    )

    print(f"LP shaft volume: {lp_spool.body.volume:.6f} m3")
    print(f"LP total weight: {lp_spool.total_weight:.3f} kg")

    display((hp_spool, lp_spool), autodraw=True)
