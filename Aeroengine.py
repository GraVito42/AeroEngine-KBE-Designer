# AeroEngine.py
"""
AeroEngine — top-level parametric turbofan engine orchestrator.

Class architecture:
    AeroEngine (GeomBase)
    ├── engine_frame : EngineFrame  — structural casing + inlet + nozzle
    ├── combustor    : Combustor    — annular combustion chamber
    └── spool        : Spool        — shaft + compressor + turbine
        ├── compressor : Compressor
        └── turbine    : Turbine

Position convention:
    Engine spin axis = global X.
    EngineFrame starts at x=0 (global origin).
    Components stack axially via explicit x_offset inputs computed from lengths.

Coordinate frame: rotate(XOY, 'y', 90°) aligns ParaPy Z-up with engine X-axial.
"""

# Ensure project root is in sys.path when running this file directly
import sys
from pathlib import Path
for parent in Path(__file__).resolve().parents:
    if (parent / "EngineCore").exists() and (parent / "Thermodynamics").exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break

from parapy.core import Base, Input, Attribute, Part, action
from parapy.geom import GeomBase, rotate, XOY, translate, Position

from EngineCore.Ducts.EngineFrame import EngineFrame
from EngineCore.Combustor import Combustor
from EngineCore.Turbomachinery.Spool import Spool
from Thermodynamics.FlowStation import FlowStation
from Thermodynamics.TurbojetSimplified import TurbojetSimplified
from Thermodynamics.FlowCondition import FlowCondition

# TODO: InputParser and ReportWriter are future utility classes.
#       Uncomment these imports once the modules exist.
# from IO_Management.InputParser import InputParser
# from IO_Management.ReportWriter import ReportWriter


class AeroEngine(GeomBase):
    """
    Top-level parametric aero-engine model.

    Orchestrates the structural frame, combustor, and spool children.
    Computes aggregate weight and preliminary 1-D cycle performance.
    """

    # ==================================================================
    # INPUT SLOTS — engine-level configuration
    # ==================================================================

    #: str — path to the .xlsx input file (consumed by InputParser)
    input_file = Input("")

    # --- This section will be overridden by Input parser call ---------

    #: dict[str, float] — altitude [m], Mach [-], ISA deviation [K]
    design_flight_conditions:dict = Input({
        "altitude": 10668.0,       # m   — cruise FL350
        "Mach": 0.78,              # -   — cruise Mach
        "ISA_deviation": 0.0,      # K   — standard day
    })

    #: dict[str, float] — top-level cycle parameters
    engine_features:dict = Input({
        "IPR": 5.0,                # -   — inlet pressure ratio
        "CPR": 30.0,               # -   — compressor pressure ratio
        "CCPR": 0.98,              # -   — combustor pressure ratio
        "TPR": 0.03,               # -   — turbine pressure ratio
        "NPR": 0.2,                # -   —  nozzle pressure ratio
        "I_eta": 5.0,              # -   — inlet isentropic efficiency
        "C_eta": 30.0,             # -   — compressor isentropic efficiency
        "CC_eta": 0.98,            # -   — combustor isentropic efficiency
        "T_eta": 0.03,             # -   — turbine isentropic efficiency
        "N_eta": 0.2,              # -   —  nozzle isentropic efficiency
        "TIT": 1500.0,             # K   — turbine entry temperature
        "Thrust_required": 35000,  # N   — thrust required
        "LHV": 43.0e6,             # J/kg — Fuel lower heating value
        "gamma_g": 1.33,           # -   — Gas specific-heat ratio
        "cpg": 1150.0,             # J/kg/K — cp combustion gas
        "r_gas": 287.05,           # J/kg/K — Specific gas constant (air)
        "mech_eta": 0.98,          # -      — Shaft mechanical efficiency
    })

    engine_geometry:dict = Input({
        "d_max": 1.0,              # m  — Engine maximum diameter == Compressore inlet diameter
        "inlet_length": 0.55,      # m — inlet duct axial length
        "casing_length": 1.0,      # m — structural casing barrel axial length
        "nozzle_length": 0.45,     # m — nozzle axial length
        "combustor_internal_radius": 0.15,  # m — combustor inner radius
        "combustor_external_radius": 0.30,  # m — combustor outer radius
        "combustor_length": 0.40,          # m — combustor axial length
        "casing_wall_thickness": 0.012      # m — casing wall thickness (uniform default)
    })

    #----------------------------------------------------------------------

    # ====================================================================
    # Flight flow condition
    # ====================================================================

    @Attribute
    def flight_condition_flow(self):
        return FlowCondition.flight_condition_flow(self.design_flight_conditions)

    # ====================================================================
    # Simplified Model calculation
    # ====================================================================

    @Part
    def simplified_engine(self):
        return TurbojetSimplified(
            # ---- Sizing target ------------------------------------------------- #
            target_thrust=      self.engine_features["Thrust_required"],           #   [N]
            # ---- Flight / ambient (station 0) ---------------------------------- #
            M0=                 self.design_flight_conditions["Mach"],             #   [-]
            T0= self.flight_condition_flow.T_total,                                #   [K]
            p0 = self.flight_condition_flow.p_total,                               #   [Pa]

            # ---- Gas / fuel properties (mirror FlowCondition) ------------------ #
            gamma_a = self.flight_condition_flow.gamma,                               #   [Pa]
            gamma_g = self.engine_features["gamma_g"],  # Gas specific-heat ratio           [-]
            cpa     = self.flight_condition_flow.c_p,                                 #   [J/kg/K]
            cpg = self.engine_features["cpg"],                                        #   [J/kg/K]
            r_gas = self.engine_features["r_gas"],                                    #   [J/kg/K]
            LHV = self.engine_features["LHV"],                                        #   [J/kg]

            # ---- Component design parameters ----------------------------------- #
            inlet_pr = self.engine_features["IPR"],  # Inlet total-pressure recovery     [-]
            comp_pr = self.engine_features["CPR"],  # Compressor pressure ratio         [-]
            comp_eff = self.engine_features["C_eta"],  # Compressor isentropic efficiency  [-]
            Tt4 = self.engine_features["TIT"],  # Turbine inlet temperature (TIT)   [K]
            comb_eff = self.engine_features["CC_eta"],  # Combustion efficiency             [-]
            comb_pr = self.engine_features["CCPR"],  # Combustor total-pressure ratio    [-]
            turb_eff = self.engine_features["T_eta"],  # Turbine isentropic efficiency     [-]
            mech_eff = self.engine_features["mech_eta"],  # Shaft mechanical efficiency       [-]
            nozzle_eff = self.engine_features["N_eta"],  # Nozzle isentropic efficiency      [-]
            )

    # ====================================================================
    # Using the simplified model to build the engine
    # ====================================================================

    def build_engine(self):
        """
        Here we use the simplified engine to:
        - obtain the mass_flow
        - using mass_flow and Mach (at the compressor inlet == after the inlet)
          we obtain the Area of the annulus at the entrance of the compressor
        - we can compute all the flow stations Mach and Areas, using
            - all the stations in the simplified_engine
            - isentropic_trans in FlowStation
            - isentropic_trans_th in FlowCondition
            - mach_to_area in FlowStation
            - Combustor (auxiliar @Part)
        - we can compute the spool design radius == (d_max/2)*(1- np.sqrt(1-(4*Area_annulus/pi)))
        :return:
            - dict(
            "Inlet": FlowStation at the Inlet == flight_condition_flow + Area at the inlet mouth
            "Compressor": FlowStation at the Compressor inlet
            "Combustor": FlowStation at the Combustor inlet
            "Turbine": FlowStation at the Turbine inlet
            "Nozzle": FlowStation at the Nozzle inlet
            "spool_radius": spool radius
            )
            - spool radius
        """
        return

    # ------------------------------------------------------------------
    # Flow station inputs (pass-through to children)
    # ------------------------------------------------------------------

    @Attribute
    def build_results(self):
        return self.build_engine()

    #: FlowStation at station 1 — freestream / inlet highlight
    @Attribute
    def inlet_inflow(self):
        return self.build_results["Inlet"]

    @Attribute
    def compressor_inflow(self):
        return self.build_results["Compressor"]

    @Attribute
    def turbine_inflow(self):
        return self.build_results["Turbine"]

    @Attribute
    def nozzle_inflow(self):
        return self.build_results["Nozzle"]

    @Attribute
    def spool_design_radius(self):
        return self.build_results["spool_radius"]

    #: dict[int, float] — station-keyed total pressures [Pa] / temps [K]
    #:   keys = station numbers (2, 3, 4, 5, 6, …)
    #:   values = total pressure OR temperature at that station
    @Attribute
    def thermodynamic_cycle(self):
        return {
        2: 101325.0,               # Pa — fan face
        3: 810600.0,               # Pa — compressor exit (OPR=8 example)
        4: 810600.0,               # Pa — combustor exit  (isobaric)
        5: 180000.0,               # Pa — turbine exit
        6: 120000.0,               # Pa — nozzle inlet
        }

    # ------------------------------------------------------------------
    # This part must be replaced with @Attributes,
    # computing all these values coherently with the other results
    # ------------------------------------------------------------------

    # #: J/kg — compressor total enthalpy rise
    # compressor_delta_h = Input(150000.0)
    #
    # #: int — compressor stage count
    # compressor_n_stages = Input(5)
    #
    # #: int — turbine stage count
    # turbine_n_stages = Input(3)
    #
    # #: rev/min — shaft rotational speed
    # shaft_rpm = Input(12000.0)
    #
    # #: m — inter-machine axial gap on the spool
    # spool_gap_length = Input(0.25)

    @Attribute
    def spool_mech_efficiency(self):
        """[-] — mechanical efficiency for spool"""
        return self.engine_features["mech_eta"]

    # ------------------------------------------------------------------
    # Here the Spool must be built
    # ------------------------------------------------------------------

    # @Part
    # def spool(self):
    #     return Spool()

    # THIS MUST BE DEFINED AFTER THE SPOOL:
    # all its inputs are LITERALLY x and r of all the maximum point of the spool
    # internal_profile = Input([
    #     (0.02, 0.080),
    #     (0.35, 0.075),
    #     (0.37, 0.090),
    #     (0.63, 0.090),
    #     (0.65, 0.070),
    #     (0.95, 0.089),
    # ])



    @Attribute
    def flight_velocity(self):
        """#: Flight velocity [m/s] for thrust power calc"""
        return self.flight_condition_flow.v

    # ==================================================================
    # @Attribute SLOTS
    # ==================================================================

    # --- Parsed inputs (InputParser) ---

    @Attribute
    def parsed_inputs(self):
        """
        Result of InputParser.decode_inputs(self.input_file).
        Returns an empty dict until InputParser is wired up.
        """
        # TODO: Uncomment once InputParser module exists:
        # return InputParser.decode_inputs(self.input_file)
        return {}

    # --- Default flow stations (created from dicts when not passed) ---

    @Attribute
    def _inlet_flow_station(self):
        """FlowStation at station 1 — freestream conditions."""
        # TODO: Derive from parsed_inputs when InputParser is wired
        return self.inlet_flow if self.inlet_flow is not None else FlowStation(
            station_number=1,
            fluid_type="air",
            p_total=101325.0,
            T_total=288.15,
            mass_flow=self.engine_features["mass_flow"],
            Mach=self.design_flight_conditions["Mach"],
        )

    @Attribute
    def _compressor_inlet_flow_station(self):
        """FlowStation at station 2 — compressor face."""
        # TODO: Derive from parsed_inputs / inlet outlet when InputParser is wired
        return self.compressor_inlet_flow if self.compressor_inlet_flow is not None else FlowStation(
            station_number=2,
            fluid_type="air",
            p_total=self.thermodynamic_cycle.get(2, 101325.0),
            T_total=300.0,
            mass_flow=self.engine_features["mass_flow"] / (1.0 + self.engine_features["BPR"]),
            Mach=0.45,
        )

    @Attribute
    def _combustor_inlet_flow_station(self):
        """FlowStation at station 3 — compressor exit / combustor inlet."""
        # TODO: Wire to actual compressor outlet when integration is complete
        return FlowStation(
            station_number=3,
            fluid_type="air",
            p_total=self.thermodynamic_cycle.get(3, 810600.0),
            T_total=580.0,
            mass_flow=self.engine_features["mass_flow"] / (1.0 + self.engine_features["BPR"]),
            Mach=0.3,
        )

    @Attribute
    def _combustor_outlet_flow_station(self):
        """FlowStation at station 4 — combustor exit / turbine inlet (TIT-driven)."""
        return self.turbine_inlet_flow if self.turbine_inlet_flow is not None else FlowStation(
            station_number=4,
            fluid_type="fuel_gas",
            p_total=self.thermodynamic_cycle.get(4, 810600.0),
            T_total=self.engine_features["TET"],
            mass_flow=self.engine_features["mass_flow"] / (1.0 + self.engine_features["BPR"]) * 1.02,
            Mach=0.3,
        )

    @Attribute
    def _nozzle_inlet_flow_station(self):
        """FlowStation at station 6 — turbine exit / nozzle inlet."""
        return self.nozzle_inlet_flow if self.nozzle_inlet_flow is not None else FlowStation(
            station_number=6,
            fluid_type="fuel_gas",
            p_total=self.thermodynamic_cycle.get(6, 120000.0),
            T_total=900.0,
            mass_flow=self.engine_features["mass_flow"] / (1.0 + self.engine_features["BPR"]) * 1.02,
            Mach=0.45,
        )

    # --- Axial stacking offsets ---

    @Attribute
    def combustor_x_offset(self):
        """Axial X position of the combustor leading face [m].
        Placed after the inlet duct plus a fraction of the casing."""
        # TODO: Verify exact placement once component lengths are finalised
        return self.inlet_length + self.casing_length * 0.35

    @Attribute
    def spool_x_start(self):
        """Axial X position where the spool shaft begins [m]."""
        # TODO: Verify against final casing internal layout
        return self.inlet_length + 0.02

    @Attribute
    def spool_x_start_compressor(self):
        """Axial X position of the compressor leading edge [m]."""
        return self.spool_x_start + 0.05

    @Attribute
    def spool_x_end(self):
        """Axial X position where the spool shaft ends [m]."""
        return self.inlet_length + self.casing_length - 0.05

    # --- Aggregate weight ---

    @Attribute
    def total_weight(self):
        """Sum of child component weights [kg].
        engine_frame.weight + combustor.weight + spool.total_weight"""
        # TODO: Verify attribute names match child implementations once all wired
        return self.engine_frame.weight + self.combustor.weight + self.spool.total_weight

    # --- Preliminary 1-D performance ---

    @Attribute
    def core_mass_flow(self):
        """Core mass flow [kg/s] = total / (1 + BPR)."""
        return self.engine_features["mass_flow"] / (1.0 + self.engine_features["BPR"])

    @Attribute
    def bypass_mass_flow(self):
        """Bypass mass flow [kg/s] = total - core."""
        return self.engine_features["mass_flow"] - self.core_mass_flow

    @Attribute
    def exhaust_velocity(self):
        """Simplified hot-jet exhaust velocity [m/s].
        V_e = sqrt(2 * cp * T_total_turbine_exit * (1 - (p_amb / p_total_exit)^((γ-1)/γ)))
        """
        return (2.0 * 1005.0 * 900.0 * (
            1.0 - (101325.0 / self.thermodynamic_cycle.get(6, 120000.0)) ** 0.2857
        )) ** 0.5

    @Attribute
    def specific_thrust(self):
        """Specific thrust [N·s/kg] = V_exhaust - V_flight."""
        return self.exhaust_velocity - self.flight_velocity

    @Attribute
    def net_thrust(self):
        """Net thrust [N] = core_mass_flow * specific_thrust.
        (Bypass contribution omitted in this simplified model.)"""
        # TODO: Add bypass stream thrust contribution for turbofan
        return self.core_mass_flow * self.specific_thrust

    @Attribute
    def fuel_flow_rate(self):
        """Fuel flow rate [kg/s] — simplified: f * m_core.
        f ≈ cp * (TET - T_compressor_exit) / LHV"""
        return self.core_mass_flow * 1005.0 * (
            self.engine_features["TET"] - 580.0
        ) / 43.2e6

    @Attribute
    def sfc(self):
        """Specific fuel consumption [kg/(N·s)] = fuel_flow / thrust."""
        return self.fuel_flow_rate / max(self.net_thrust, 1.0)

    @Attribute
    def eta_thermal(self):
        """Thermal efficiency [-] = net_power / heat_input."""
        return (self.net_thrust * self.flight_velocity) / max(
            self.fuel_flow_rate * 43.2e6, 1.0
        )

    @Attribute
    def eta_propulsive(self):
        """Propulsive efficiency [-] = 2 / (1 + V_e / V_0)."""
        return 2.0 / (1.0 + self.exhaust_velocity / max(self.flight_velocity, 1.0))

    @Attribute
    def eta_overall(self):
        """Overall efficiency [-] = eta_thermal * eta_propulsive."""
        return self.eta_thermal * self.eta_propulsive

    @Attribute
    def preliminary_performance(self):
        """Preliminary 1-D cycle performance summary dict."""
        return {
            "net_thrust_N": self.net_thrust,
            "specific_thrust_Ns_kg": self.specific_thrust,
            "SFC_kg_Ns": self.sfc,
            "fuel_flow_kg_s": self.fuel_flow_rate,
            "exhaust_velocity_m_s": self.exhaust_velocity,
            "eta_thermal": self.eta_thermal,
            "eta_propulsive": self.eta_propulsive,
            "eta_overall": self.eta_overall,
            "core_mass_flow_kg_s": self.core_mass_flow,
            "bypass_mass_flow_kg_s": self.bypass_mass_flow,
        }

    # ==================================================================
    # @Part SLOTS — child components
    # ==================================================================

    @Part
    def engine_frame(self):
        """Structural casing + inlet + nozzle."""
        return EngineFrame(
            inlet_inflow=self._inlet_flow_station,
            nozzle_inflow=self._nozzle_inlet_flow_station,
            inlet_length=self.inlet_length,
            casing_length=self.casing_length,
            nozzle_length=self.nozzle_length,
            casing_inlet_wall_thickness=self.casing_wall_thickness,
            casing_outlet_wall_thickness=self.casing_wall_thickness,
            inlet_wall_thickness=self.casing_wall_thickness,
            nozzle_wall_thickness=self.casing_wall_thickness,
            sheet_thickness=self.sheet_thickness,
            material_name=self.frame_material,
            internal_profile=self.internal_profile,
            label="engine_frame",
        )

    @Part
    def combustor(self):
        """Annular combustion chamber."""
        return Combustor(
            inflow_conditions=self._combustor_inlet_flow_station,
            outlet_flow=self._combustor_outlet_flow_station,
            station_out=4,
            Mach_out=0.2,
            internal_radius=self.combustor_internal_radius,
            external_radius=self.combustor_external_radius,
            length=self.combustor_length,
            material_name=self.combustor_material,
            # TODO: Verify x_offset integration with EngineFrame internal_profile
            label="combustor",
        )

    @Part
    def spool(self):
        """HP spool — shaft + compressor + turbine."""
        return Spool(
            design_radius=self.spool_design_radius,
            compressor_delta_h=self.compressor_delta_h,
            compressor_n_stages=self.compressor_n_stages,
            turbine_n_stages=self.turbine_n_stages,
            shaft_rpm=self.shaft_rpm,
            compressor_inflow=self._compressor_inlet_flow_station,
            turbine_inflow=self._combustor_outlet_flow_station,
            gap_length=self.spool_gap_length,
            x_start=self.spool_x_start,
            x_start_compressor=self.spool_x_start_compressor,
            x_end=self.spool_x_end,
            isos_efficiency=self.spool_isos_efficiency,
            flight_velocity=self.flight_velocity,
            label="spool",
        )

    # ==================================================================
    # @action SLOTS — GUI buttons
    # ==================================================================

    @action(label='Run CFD analysis')
    def run_cfd_analysis(self):
        """Trigger high-fidelity Multall CFD on both compressor and turbine.
        Calls the spool's power_balance action which runs compressor CFD first,
        then turbine CFD if the power check passes."""
        # TODO: Verify spool.compressor.solver.run() path once MultallSolver
        #       is fully integrated into the compressor/turbine children
        print("[AeroEngine] Launching CFD analysis via spool power balance...")
        self.spool.power_balance()
        print("[AeroEngine] CFD analysis complete.")

    @action(label='Compute weights')
    def compute_weights(self):
        """Evaluate total_weight and log component breakdown."""
        print("=" * 50)
        print("[AeroEngine] WEIGHT BREAKDOWN")
        print("=" * 50)
        print(f"  EngineFrame : {self.engine_frame.weight:.3f} kg")
        print(f"  Combustor   : {self.combustor.weight:.3f} kg")
        print(f"  Spool       : {self.spool.total_weight:.3f} kg")
        print(f"  {'─' * 40}")
        print(f"  TOTAL       : {self.total_weight:.3f} kg")
        print("=" * 50)

    @action(label='Export report')
    def export_report(self):
        """Instantiate ReportWriter and export the full engine report."""
        # TODO: Uncomment once ReportWriter module exists:
        # writer = ReportWriter(
        #     engine=self,
        #     performance=self.preliminary_performance,
        #     weight=self.total_weight,
        # )
        # writer.export()
        print("[AeroEngine] export_report: ReportWriter not yet implemented.")
        print("[AeroEngine] Preliminary performance summary:")
        for key, val in self.preliminary_performance.items():
            print(f"  {key}: {val:.4f}")


# ======================================================================
# Smoke test — instantiate with dummy inputs (no real .xlsx needed)
# ======================================================================
if __name__ == '__main__':

    # ------------------------------------------------------------------
    # Default FlowStations for a representative single-spool turbojet
    # ------------------------------------------------------------------
    station_1 = FlowStation(
        station_number=1,
        fluid_type="air",
        p_total=101325.0,
        T_total=288.15,
        mass_flow=250.0,
        Mach=0.78,
    )

    station_2 = FlowStation(
        station_number=2,
        fluid_type="air",
        p_total=101325.0 * 0.98,
        T_total=300.0,
        mass_flow=250.0 / 6.0,
        Mach=0.45,
    )

    station_3 = FlowStation(
        station_number=3,
        fluid_type="air",
        p_total=810600.0,
        T_total=580.0,
        mass_flow=250.0 / 6.0,
        Mach=0.3,
    )

    station_4 = FlowStation(
        station_number=4,
        fluid_type="fuel_gas",
        p_total=810600.0,
        T_total=1500.0,
        mass_flow=250.0 / 6.0 * 1.02,
        Mach=0.3,
    )

    station_6 = FlowStation(
        station_number=6,
        fluid_type="fuel_gas",
        p_total=120000.0,
        T_total=900.0,
        mass_flow=250.0 / 6.0 * 1.02,
        Mach=0.45,
    )

    # ------------------------------------------------------------------
    # Instantiate AeroEngine
    # ------------------------------------------------------------------
    engine = AeroEngine(
        input_file="",
        engine_architecture="turbofan",
        design_flight_conditions={
            "altitude": 10668.0,
            "Mach": 0.78,
            "ISA_deviation": 0.0,
        },
        engine_features={
            "BPR": 5.0,
            "OPR": 30.0,
            "TET": 1500.0,
            "mass_flow": 250.0,
        },
        thermodynamic_cycle={
            2: 101325.0 * 0.98,
            3: 810600.0,
            4: 810600.0,
            5: 180000.0,
            6: 120000.0,
        },
        inlet_flow=station_1,
        compressor_inlet_flow=station_2,
        turbine_inlet_flow=station_4,
        nozzle_inlet_flow=station_6,
        inlet_length=0.55,
        casing_length=1.0,
        nozzle_length=0.45,
        combustor_internal_radius=0.15,
        combustor_external_radius=0.30,
        combustor_length=0.40,
        spool_design_radius=0.20,
        compressor_delta_h=150000.0,
        compressor_n_stages=5,
        turbine_n_stages=3,
        shaft_rpm=12000.0,
        spool_gap_length=0.25,
        spool_isos_efficiency=0.90,
        flight_velocity=250.0,
        label="AeroEngine_HP",
    )

    # ------------------------------------------------------------------
    # Print results
    # ------------------------------------------------------------------
    print("=" * 60)
    print("AeroEngine SMOKE TEST")
    print("=" * 60)

    print("\n--- PRELIMINARY PERFORMANCE ---")
    for k, v in engine.preliminary_performance.items():
        print(f"  {k:30s}: {v:.4f}")

    print("\n--- TOTAL WEIGHT ---")
    # TODO: total_weight will fail if child .weight attributes
    #       require geometry that isn't fully resolved in this smoke test.
    #       Wrap in try/except for graceful degradation.
    try:
        print(f"  total_weight = {engine.total_weight:.3f} kg")
    except Exception as e:
        print(f"  total_weight could not be computed: {e}")

    print("\n--- COMPONENT CHECK ---")
    print(f"  engine_frame type : {type(engine.engine_frame).__name__}")
    print(f"  combustor type    : {type(engine.combustor).__name__}")
    print(f"  spool type        : {type(engine.spool).__name__}")

    # ------------------------------------------------------------------
    # Launch GUI
    # ------------------------------------------------------------------
    from parapy.gui import display
    display(engine, autodraw=True)
