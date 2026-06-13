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

import math
import os

from parapy.core import Input, Attribute, Part, action
from parapy.geom import (GeomBase, Point, FittedCurve, LineSegment,
                         ComposedCurve, RevolvedSolid)

from Material import Material
from Compressor import Compressor
from Turbine import Turbine
from Flow_station import FlowStation
from MultallSolver import parse_shaft_power


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

    @Input
    def material_name(self):
        return "Ti-6Al-4V"

    # ------------------------------------------------------------------
    # Material and Geometric Attributes
    # ------------------------------------------------------------------
    @Part
    def material(self):
        """Material representation for color/density lookup."""
        return Material(material_name=self.material_name)

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
    # Shaft Profile Curve Points
    # ------------------------------------------------------------------
    @Attribute
    def nose_cap_points(self):
        """Points defining the ellipsoidal nose cap curve."""
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
        return FittedCurve(points=self.nose_cap_points, hidden=True)

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
        """Ellipsoidal tail cap curve."""
        return FittedCurve(points=self.tail_cap_points, hidden=True)

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
            color=self.material.color
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
            material_name=self.material_name,
            work_dir=os.path.join(self.work_dir_base, "compressor"),
            axial_offset=self.x_start_compressor,
            label=f"C_{self.label}" if hasattr(self, 'label') else "C",
            enable_cad_chord_capping=True,
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
            material_name=self.material_name,
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
                print(f"Warning: failed to parse compressor shaft power: {e}")

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
                print(f"Warning: failed to parse turbine shaft power: {e}")

        # Fallback to thermodynamic design power
        return self.turbine_inflow.mass_flow * self.turbine_delta_h

    @action(label='Run power balance')
    def power_balance(self):
        """Sequential balance: size the compressor work, then verify the turbine
        can supply it before running its high-fidelity CFD."""
        # 1. Run Compressor CFD
        print("[Power Balance] Running Compressor CFD...")
        self.compressor.multall_analysis()

        # Invalidate compressor_power and power_estimated cache
        self._cfd_runs_counter += 1

        # 2. Check the power balance
        turbine_power_gen = self.turbine_delta_h * self.turbine_inflow.mass_flow
        remaining_power = turbine_power_gen - self.compressor_power
        required_power = self.thrust_power + self.ext_systems_power
        
        print(f"[Power Balance] Turbine Power Gen: {turbine_power_gen:.0f} W")
        print(f"[Power Balance] Compressor CFD Power: {self.compressor_power:.0f} W")
        print(f"[Power Balance] Remaining Power: {remaining_power:.0f} W")
        print(f"[Power Balance] Required Power (Thrust + Ext): {required_power:.0f} W")

        if remaining_power >= required_power:
            # 3. Run Turbine CFD
            print("[Power Balance] Power check passed. Running Turbine CFD...")
            self.turbine.multall_analysis()
            
            # Invalidate power_estimated cache with the final results
            self._cfd_runs_counter += 1
            print("[Power Balance] Power balance complete.")
        else:
            print("UPDATE GEOMETRY")
            raise ValueError("UPDATE GEOMETRY")


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
        x_start=0.0,
        x_start_compressor=0.4,
        x_end=1.5,
        isos_efficiency=0.90,
        label='HP_spool',
    )

    print("=== SPOOL INITIALIZATION SUCCESS ===")
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

    display(hp_spool, autodraw=True)