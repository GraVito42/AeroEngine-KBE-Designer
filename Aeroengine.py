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
import math
import numpy as np
from scipy.optimize import brentq
for parent in Path(__file__).resolve().parents:
    if (parent / "EngineCore").exists() and (parent / "Thermodynamics").exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break

from parapy.core import Base, Input, Attribute, Part, action
from parapy.geom import GeomBase, rotate, XOY, translate, Position
from concurrent.futures import ThreadPoolExecutor

from EngineCore.Ducts.EngineFrame import EngineFrame
from EngineCore.Combustor import Combustor
from EngineCore.Turbomachinery.Spool import Spool
from EngineCore.Turbomachinery.Compressor import Compressor
from EngineCore.Turbomachinery.Turbine import Turbine
from Thermodynamics.FlowStation import FlowStation
from Thermodynamics.TurbojetSimplified import TurbojetSimplified
from Thermodynamics.FlowCondition import FlowCondition

from IO_Management.InputParser import InputParser
# from IO_Management.ReportWriter import ReportWriter


DEFAULT_FLIGHT_CONDITIONS = {
    "altitude": 10668.0,       # m   — cruise FL350
    "Mach": 0.78,              # -   — cruise Mach
    "ISA_deviation": 0.0,      # K   — standard day
}

DEFAULT_ENGINE_FEATURES = {
    "IPR":  0.99,              # -   — inlet pressure recovery (tipical cruise condition)
    "CPR": 30.0,               # -   — compressor pressure ratio
    "CCPR": 0.96,              # -   — combustor pressure ratio
    "TPR": 0.03,               # -   — turbine pressure ratio
    "NPR": 0.2,                # -   —  nozzle pressure ratio
    "I_eta": 0.99,              # -   — inlet isentropic efficiency
    "C_eta": 0.88,             # -   — compressor isentropic efficiency
    "CC_eta": 0.995,            # -   — combustor isentropic efficiency
    "T_eta": 0.90,             # -   — turbine isentropic efficiency
    "N_eta": 0.98,              # -   —  nozzle isentropic efficiency
    "TIT": 1500.0,             # K   — turbine entry temperature
    "Thrust_required": 35000,  # N   — thrust required
    "LHV": 43.0e6,             # J/kg — Fuel lower heating value
    "gamma_g": 1.33,           # -   — Gas specific-heat ratio
    "cpg": 1150.0,             # J/kg/K — cp combustion gas
    "r_gas": 287.05,           # J/kg/K — Specific gas constant (air)
    "mech_eta": 0.98,          # -      — Shaft mechanical efficiency
    "stage_PR_max": 1.4,       # -      — Axial-compressor per-stage total-pressure ratio ceiling
    "C_work_coeff": 0.4,        # -      — Compressor stage loading coefficient
    "T_work_coeff": 1.5,         # .      — Turbine stage loading coefficient
    "C_reaction_coeff": 0.5,  # -      — Compressor stage reaction coefficient
    "T_reaction_coeff": 0.5  # .      — Turbine stage reaction coefficient
}

DEFAULT_ENGINE_GEOMETRY = {
    "d_max": 1.0,              # m  — Engine maximum diameter == Compressor inlet diameter
    "spool_tip_length": 0.2,   # m  — Spool tip length == Combustor x_offset wrt to the start of the spool
    "spool_length": 1.5,       # m  — Spool length
    "inlet_length": 0.55,      # m  — inlet duct axial length
    "nozzle_length": 0.45,     # m — nozzle axial length
    "casing_wall_thickness": 0.012      # m — casing wall thickness (uniform default)
}

DEFAULT_ENGINE_MATERIALS = {
    "C_rotor": "Ti",
    "C_stator": "Ti",
    "T_rotor": "Ti",
    "T_stator": "Ti",
    "casing": "Ti",
    "combustor": "Ti",
}


class AeroEngine(GeomBase):
    """
    Top-level parametric aero-engine model.

    Orchestrates the structural frame, combustor, and spool children.
    Computes aggregate weight and preliminary 1-D cycle performance.
    """

    # ==================================================================
    # INPUT SLOTS — engine-level configuration
    # ==================================================================

    @Input
    def input_file(self):
        return ""

    work_dir = Input("")

    @Input
    def design_flight_conditions(self):
        return {**DEFAULT_FLIGHT_CONDITIONS, **self.input_parser.flight_conditions}

    @Input
    def engine_features(self):
        return {**DEFAULT_ENGINE_FEATURES, **self.input_parser.engine_features}

    @Input
    def engine_geometry(self):
        return {**DEFAULT_ENGINE_GEOMETRY, **self.input_parser.engine_geometry}

    @Input
    def engine_materials(self):
        return {**DEFAULT_ENGINE_MATERIALS, **self.input_parser.engine_materials}

    show_compressor = Input(False)
    """If False, the compressor 3D blade geometries are hidden by default to keep load times fast."""

    show_turbine = Input(False)
    """If False, the turbine 3D blade geometries are hidden by default to keep load times fast."""

    # --- Parsed inputs (InputParser) ---

    @Attribute
    def parsed_inputs(self):
        return self.input_parser.raw_data

    @action(label="Configure Inputs")
    def configure(self):
        """Pre-launch: open GUI, validate, write xlsx, update input_file."""
        result = self.input_parser.launch_gui(filepath=self.input_file or None)
        if result is not None:
            self.input_file = result[0]
        return self

    #----------------------------------------------------------------------

    @Input
    def inlet_wall_thickness(self):
        if "inlet_wall_thickness" in self.engine_geometry:
            return self.engine_geometry["inlet_wall_thickness"]
        else:
            return self.engine_geometry["casing_wall_thickness"]

    @Input
    def nozzle_wall_thickness(self):
        if "nozzle_wall_thickness" in self.engine_geometry:
            return self.engine_geometry["nozzle_wall_thickness"]
        else:
            return self.engine_geometry["casing_wall_thickness"]


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
            cpa     = self.flight_condition_flow.cp,                                 #   [J/kg/K]
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

    # ------------------------------------------------------------------
    # Spool primary sizing parameters
    # ------------------------------------------------------------------

    @Attribute
    def compressor_delta_h(self):
        """#: J/kg — compressor total enthalpy rise: cp_a*(Tt3 - Tt2)."""
        return self.simplified_engine.cpa * (
                self.simplified_engine.Tt3 - self.simplified_engine.Tt2)

    @Attribute
    def turbine_delta_h(self):
        """#: J/kg — turbine total enthalpy drop: cp_g*(Tt4 - Tt5)."""
        return self.simplified_engine.cpg * (
                self.simplified_engine.Tt4 - self.simplified_engine.Tt5)

    @Attribute
    def compressor_n_stages(self):
        """#: int — stage count from n = ceil(ln(PR_c) / ln(PR_stage_max))."""
        return max(1, math.ceil(
            math.log(self.simplified_engine.comp_pr) / math.log(self.engine_features["stage_PR_max"])))

    @Attribute
    def turbine_n_stages(self):
        """#: int — turbine stages from equal-shaft loading:
        n_t = ceil(dh_t * n_c * psi_c / (psi_t * dh_c)), dh_t = cp_g*(Tt4 - Tt5)."""
        return max(1, math.ceil(
            self.simplified_engine.cpg * (self.simplified_engine.Tt4 - self.simplified_engine.Tt5)
            * self.compressor_n_stages * self.engine_features["C_work_coeff"]
            / (self.engine_features["T_work_coeff"] * self.compressor_delta_h)))

    @Attribute
    def shaft_rpm(self):
        """#: rev/min — from stage loading U = sqrt(dh_c/(n_c*psi_c)),
        N = 60*U / (2*pi*r_mean)."""
        return 60.0 * math.sqrt(
            self.compressor_delta_h / (self.compressor_n_stages * self.engine_features["C_work_coeff"])) / (
                2.0 * math.pi * self.spool_design_radius)

    @Attribute
    def spool_mech_efficiency(self):
        """[-] — mechanical efficiency for spool"""
        return self.engine_features["mech_eta"]

    @Attribute
    def flight_velocity(self):
        """#: Flight velocity [m/s] for thrust power calc"""
        return self.simplified_engine.station0.v

    # ====================================================================
    # Using the simplified model to build the engine
    # ====================================================================

    def build_engine(self):
        """
        Build the engine flow stations from the simplified inverse-cycle model.

        Annulus area at the compressor inlet is derived from first principles
        via a 1D root-find (continuity + duty coefficients, no assumed Mach).
        Downstream areas come from auxiliary meangen/stagen runs.
        Mach at every station is recovered from continuity via mach_from_area.

        :return: dict with keys
            "Inlet", "Compressor", "Combustor", "Turbine", "Nozzle" -> FlowStation
            "spool_radius" -> float [m]
        """
        import os

        mass_flow = self.simplified_engine.mass_flow
        m_g = self.simplified_engine.m_g

        # Station-2 totals (FlowCondition, no Mach/area)
        pt2 = self.simplified_engine.station2.p_total
        Tt2 = self.simplified_engine.station2.T_total

        # Gas properties from the resolved cycle
        gam = self.simplified_engine.station0.gamma  # air gamma from station0
        cp_a = self.simplified_engine.cpa
        R_a = self.simplified_engine.r_gas

        phi = self.engine_features["C_work_coeff"]  # flow coefficient phi = Vax/U
        d_max = self.engine_geometry["d_max"]
        r_tip = d_max / 2.0

        # ------------------------------------------------------------------
        # Root-find: spool_radius (r_hub) such that
        #   A_geometry(r_hub) == A_continuity(V_ax(r_hub))
        # V_ax depends on r_hub through: r_mean -> U -> V_ax = phi * U
        # rpm is derived inline (same formula as shaft_rpm @Attribute, but
        # computed over r_mean so we stay acyclic w.r.t. build_results).
        # ------------------------------------------------------------------
        def _residual(r_hub):
            r_mean = (r_tip + r_hub) / 2.0
            rpm_loc = (
                    60.0
                    * math.sqrt(
                self.compressor_delta_h
                / (self.compressor_n_stages * self.engine_features["C_work_coeff"])
            )
                    / (2.0 * math.pi * r_mean)
            )
            U_loc = rpm_loc * math.pi / 30.0 * r_mean  # simplifies to sqrt(dH/(n*psi))
            V_ax = phi * U_loc
            T_stat = Tt2 - V_ax ** 2 / (2.0 * cp_a)
            if T_stat <= 0.0:
                return 1e9
            p_stat = pt2 * (T_stat / Tt2) ** (gam / (gam - 1.0))
            rho = p_stat / (R_a * T_stat)
            A_cont = mass_flow / (rho * V_ax)
            A_geom = math.pi * (r_tip ** 2 - r_hub ** 2)
            return A_geom - A_cont

        assert _residual(1e-3) * _residual(r_tip - 1e-3) < 0.0, (
            "build_engine: no root for r_hub in (0, r_tip). "
            "Check d_max, C_work_coeff, or compressor_delta_h."
        )
        spool_radius = brentq(_residual, 1e-3, r_tip - 1e-3, xtol=1e-6)

        A_compressor = math.pi * (r_tip ** 2 - spool_radius ** 2)

        # Inlet: freestream Mach == flight Mach (physical identity)
        inlet = FlowStation(
            station_number=1,
            fluid_type="air",
            p_total=self.flight_condition_flow.p_total,
            T_total=self.flight_condition_flow.T_total,
            mass_flow=mass_flow,
            Mach=self.design_flight_conditions["Mach"],
        )

        compressor = FlowStation.mach_from_area(
            A_compressor, pt2, Tt2, mass_flow, fluid_type="air",
        )

        # RPM consistent with the spool_radius solution
        rpm_local = (
                60.0
                * math.sqrt(self.compressor_delta_h
            / (self.compressor_n_stages * self.engine_features["C_work_coeff"]))
                / (2.0 * math.pi * spool_radius)
        )

        # Auxiliary working directory: self.work_dir + /aux only.
        # Compressor and Turbine append /compressor and /turbine internally.
        aux_work_dir = os.path.join(self.work_dir, "aux_components")

        # ==================================================================
        # TASK 1 — combustor inlet area (station 3) from compressor exit geometry
        # compressor: rotor-first / stator-last (confirmed from Turbomachine.py)
        # r_sections: [0]=hub, [-1]=tip (confirmed from StageParser._assemble_row)
        # ==================================================================
        compressor_aux = Compressor(
            inflow_conditions=compressor,
            station_out=3,
            n_stages=self.compressor_n_stages,
            rpm=rpm_local,
            design_radius=spool_radius,
            delta_H=self.compressor_delta_h,
            pressure_ratio=self.simplified_engine.comp_pr,
            isos_efficiency=self.engine_features["C_eta"],
            working_directory=aux_work_dir,
        )
        comp_stages = compressor_aux.stage_data  # triggers meangen + stagen
        # TODO: verify row/section index convention with Architect
        hub_radius_compressor_exit = comp_stages[-1]["stator"]["r_sections"][0]
        tip_radius_compressor_exit = comp_stages[-1]["stator"]["r_sections"][-1]
        A_combustor = math.pi * (
                tip_radius_compressor_exit ** 2 - hub_radius_compressor_exit ** 2
        )
        combustor = FlowStation.mach_from_area(
            A_combustor,
            self.simplified_engine.station3.p_total,
            self.simplified_engine.station3.T_total,
            mass_flow,
            fluid_type="air",
        )

        # ==================================================================
        # TASK 2 + 3 — turbine inlet (station 4) and nozzle inlet (station 5)
        # turbine: stator-first / rotor-last (confirmed from Turbomachine.py)
        # Preliminary turbine inflow uses A_combustor (best available pre-Fortran area)
        # ==================================================================
        turbine_inflow_prelim = FlowStation.mach_from_area(
            A_combustor,
            self.simplified_engine.station4.p_total,
            self.simplified_engine.station4.T_total,
            m_g,
            fluid_type="fuel_gas",
        )
        turbine_aux = Turbine(
            inflow_conditions=turbine_inflow_prelim,
            station_out=5,
            n_stages=self.turbine_n_stages,
            rpm=rpm_local,
            design_radius=spool_radius,
            delta_H=self.turbine_delta_h,
            pressure_ratio=self.engine_features["TPR"],
            reaction=0.5,
            isos_efficiency=self.engine_features["T_eta"],
            working_directory=aux_work_dir,
        )
        turb_stages = turbine_aux.stage_data  # triggers meangen + stagen

        # TASK 2 — turbine inlet = first stage stator LE
        # TODO: verify row/section index convention with Architect
        hub_radius_turbine_inlet = turb_stages[0]["stator"]["r_sections"][0]
        tip_radius_turbine_inlet = turb_stages[0]["stator"]["r_sections"][-1]
        A_turbine = math.pi * (
                tip_radius_turbine_inlet ** 2 - hub_radius_turbine_inlet ** 2
        )
        turbine = FlowStation.mach_from_area(
            A_turbine,
            self.simplified_engine.station4.p_total,
            self.simplified_engine.station4.T_total,
            m_g,
            fluid_type="fuel_gas",
        )

        # TASK 3 — nozzle inlet = turbine exit = last stage rotor TE
        # Totals from station5 (turbine exit / nozzle inlet, not nozzle throat)
        hub_radius_turbine_exit = turb_stages[-1]["rotor"]["r_sections"][0]
        tip_radius_turbine_exit = turb_stages[-1]["rotor"]["r_sections"][-1]
        A_nozzle = math.pi * (
                tip_radius_turbine_exit ** 2 - hub_radius_turbine_exit ** 2
        )
        nozzle = FlowStation.mach_from_area(
            A_nozzle,
            self.simplified_engine.station5.p_total,
            self.simplified_engine.station5.T_total,
            m_g,
            fluid_type="fuel_gas",
        )

        return {
            "Inlet": inlet,
            "Compressor": compressor,
            "Combustor": combustor,
            "Turbine": turbine,
            "Nozzle": nozzle,
            "spool_radius": spool_radius,
        }

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
    def combustor_inflow(self):
        return self.build_results["Combustor"]

    @Attribute
    def turbine_inflow(self):
        return self.build_results["Turbine"]

    @Attribute
    def nozzle_inflow(self):
        return self.build_results["Nozzle"]

    @Attribute
    def spool_design_radius(self):
        return self.build_results["spool_radius"]

    # ------------------------------------------------------------------
    # Internal profile point for the EngineFrame
    # ------------------------------------------------------------------

    @Attribute
    def internal_profile(self):
        # TODO: read actual (x,r) points from self.spool geometry once Spool is built.
        # x coordinates come from Spool's resolved axial stack (inlet LE, compressor TE,
        # turbine LE, turbine TE).  Tip radii come from stage_data via Spool @Attributes.
        # These trigger meangen+stagen on the real spool (not the aux sizing run).
        return [
            # 1. End of inlet == start of compressor (compressor LE, first rotor tip)
            (self.spool.x_start_compressor,
             self.spool.compressor_tip_radii[0]),

            # 2. End of compressor == start of combustor (compressor TE, last stator tip)
            (self.spool.compressor_end_x,
             self.spool.compressor_tip_radii[1]),

            # 3. End of combustor == start of turbine (turbine LE, first stator tip)
            (self.spool.turbine_start_x,
             max(self.spool.turbine_tip_radii[0], self.spool.compressor_tip_radii[1])),

            # 4. End of turbine == start of nozzle (turbine TE, last rotor tip)
            (self.spool.turbine_end_x,
             self.spool.turbine_tip_radii[1]),
        ]

    # "casing_length": 1.0,  # m — structural casing barrel axial length -> this must be derived AFTER THE DEFINITION OF THE SPOOL and the combustor length above.
    #
    @Input
    def combustor_length(self):
        """Combustor axial length [m].
        Sizing via residence time requires empirical combustion intensity
        parameters not available in the 1D cycle model. Default 0.35 m is
        representative of modern annular combustors at this thrust class.
        Override by adding "combustor_length" to engine_geometry if a better
        estimate is available.
        """
        return self.engine_geometry.get("combustor_length", 0.35)

    @Attribute
    def casing_length(self):
        """Axial length of the structural barrel [m].
        Derived from the real Spool geometry: from the end of the inlet duct
        to the turbine exit, as resolved by meangen/stagen. This is the
        authoritative value — it differs from engine_geometry["spool_length"]
        whenever the Fortran meanline solution adjusts the axial chord distribution.
        """
        return self.spool.turbine_end_x - self.engine_geometry["inlet_length"]

    # --- Aggregate weight ---

    @Attribute
    def total_weight(self):
        """Sum of child component weights [kg].
        engine_frame.weight + combustor.weight + spool.total_weight"""
        # TODO: Verify attribute names match child implementations once all wired
        return self.engine_frame.weight + self.combustor.weight + self.spool.total_weight

    # ==================================================================
    # This were defined on a turbofan engine. Not all of them are useful,
    # must be replaced with more high-fidelity attributes that may call
    # high fidelity analysis
    # ==================================================================
    #
    # @Attribute
    # def exhaust_velocity(self):
    #     """Simplified hot-jet exhaust velocity [m/s].
    #     V_e = sqrt(2 * cp * T_total_turbine_exit * (1 - (p_amb / p_total_exit)^((γ-1)/γ)))
    #     """
    #     return (2.0 * 1005.0 * 900.0 * (
    #         1.0 - (101325.0 / self.thermodynamic_cycle.get(6, 120000.0)) ** 0.2857
    #     )) ** 0.5
    #
    # @Attribute
    # def specific_thrust(self):
    #     """Specific thrust [N·s/kg] = V_exhaust - V_flight."""
    #     return self.exhaust_velocity - self.flight_velocity
    #
    # @Attribute
    # def net_thrust(self):
    #     """Net thrust [N] = core_mass_flow * specific_thrust.
    #     (Bypass contribution omitted in this simplified model.)"""
    #     # TODO: Add bypass stream thrust contribution for turbofan
    #     return self.core_mass_flow * self.specific_thrust
    #
    # @Attribute
    # def fuel_flow_rate(self):
    #     """Fuel flow rate [kg/s] — simplified: f * m_core.
    #     f ≈ cp * (TET - T_compressor_exit) / LHV"""
    #     return self.core_mass_flow * 1005.0 * (
    #         self.engine_features["TET"] - 580.0
    #     ) / 43.2e6
    #
    # @Attribute
    # def sfc(self):
    #     """Specific fuel consumption [kg/(N·s)] = fuel_flow / thrust."""
    #     return self.fuel_flow_rate / max(self.net_thrust, 1.0)
    #
    # @Attribute
    # def eta_thermal(self):
    #     """Thermal efficiency [-] = net_power / heat_input."""
    #     return (self.net_thrust * self.flight_velocity) / max(
    #         self.fuel_flow_rate * 43.2e6, 1.0
    #     )
    #
    # @Attribute
    # def eta_propulsive(self):
    #     """Propulsive efficiency [-] = 2 / (1 + V_e / V_0)."""
    #     return 2.0 / (1.0 + self.exhaust_velocity / max(self.flight_velocity, 1.0))
    #
    # @Attribute
    # def eta_overall(self):
    #     """Overall efficiency [-] = eta_thermal * eta_propulsive."""
    #     return self.eta_thermal * self.eta_propulsive
    #
    # @Attribute
    # def preliminary_performance(self):
    #     """Preliminary 1-D cycle performance summary dict."""
    #     return {
    #         "net_thrust_N": self.net_thrust,
    #         "specific_thrust_Ns_kg": self.specific_thrust,
    #         "SFC_kg_Ns": self.sfc,
    #         "fuel_flow_kg_s": self.fuel_flow_rate,
    #         "exhaust_velocity_m_s": self.exhaust_velocity,
    #         "eta_thermal": self.eta_thermal,
    #         "eta_propulsive": self.eta_propulsive,
    #         "eta_overall": self.eta_overall,
    #         "core_mass_flow_kg_s": self.core_mass_flow,
    #         "bypass_mass_flow_kg_s": self.bypass_mass_flow,
    #     }

    # #: dict[int, float] — station-keyed total pressures [Pa] / temps [K]
    # #:   keys = station numbers (2, 3, 4, 5, 6, …)
    # #:   values = total pressure OR temperature at that station
    # @Attribute
    # def thermodynamic_cycle(self):
    #     return {
    #         2: 101325.0,  # Pa — fan face
    #         3: 810600.0,  # Pa — compressor exit (OPR=8 example)
    #         4: 810600.0,  # Pa — combustor exit  (isobaric)
    #         5: 180000.0,  # Pa — turbine exit
    #         6: 120000.0,  # Pa — nozzle inlet
    #     }

    @Part
    def input_parser(self):
        return InputParser(filepath=self.input_file)

    @Part
    def spool(self):
        """HP spool — shaft + compressor + turbine."""
        return Spool(
            design_radius=self.spool_design_radius,
            compressor_delta_h=self.compressor_delta_h,
            compressor_n_stages=self.compressor_n_stages,
            turbine_n_stages=self.turbine_n_stages,
            shaft_rpm=self.shaft_rpm,
            compressor_inflow=self.compressor_inflow,
            turbine_inflow=self.turbine_inflow,
            compressor_reaction_coeff=self.engine_features["C_reaction_coeff"],
            turbine_reaction_coeff=self.engine_features["T_reaction_coeff"],
            compressor_stator_material = self.engine_materials["C_stator"],
            compressor_rotor_material=self.engine_materials["C_rotor"],
            turbine_stator_material=self.engine_materials["T_stator"],
            turbine_rotor_material=self.engine_materials["T_rotor"],
            gap_length=self.combustor_length,
            x_start=self.engine_geometry["inlet_length"] - self.engine_geometry["spool_tip_length"],
            x_start_compressor=self.engine_geometry["inlet_length"],
            x_end=self.engine_geometry["inlet_length"] + self.engine_geometry["spool_length"] -  self.engine_geometry["spool_tip_length"],
            isos_efficiency=self.spool_mech_efficiency,
            thrust_needed=self.engine_features["Thrust_required"],
            flight_velocity=self.flight_velocity,
            show_compressor=self.show_compressor,
            show_turbine=self.show_turbine,
            label="spool",
        )

    @Part
    def combustor(self):
        """Annular combustion chamber."""
        return Combustor(
            inflow_conditions=self.combustor_inflow,
            outlet_flow=self.turbine_inflow,
            station_out=4,
            Mach_out=self.turbine_inflow.Mach,
            internal_radius= self.spool.compressor_hub_out,
            external_radius=self.spool.compressor_tip_radii[1],
            length=self.combustor_length,
            # TODO: verify combustor length convention with Architect
            #       (currently = spool_length - spool_tip_length, i.e. the gap)
            material_name=self.engine_materials["combustor"],
            eta_comb=self.engine_features["CC_eta"],
            LHV=self.engine_features["LHV"],
            x_offset=self.spool.compressor_end_x,
            label="combustor",
        )

    @Part
    def engine_frame(self):
        """Structural casing + inlet + nozzle."""
        return EngineFrame(
            inlet_inflow=self.inlet_inflow,
            nozzle_inflow=self.nozzle_inflow,
            inlet_length=self.engine_geometry["inlet_length"],
            casing_length=self.casing_length,
            nozzle_length=self.engine_geometry["nozzle_length"],
            inlet_wall_thickness=self.inlet_wall_thickness,
            casing_inlet_wall_thickness=self.engine_geometry["casing_wall_thickness"],
            casing_outlet_wall_thickness=self.engine_geometry["casing_wall_thickness"],
            nozzle_wall_thickness=self.nozzle_wall_thickness,
            internal_profile=self.internal_profile,
            material_name=self.engine_materials["casing"],
            label="engine_frame",
        )

    # ==================================================================
    # @action SLOTS — GUI buttons
    # ==================================================================

    # This methods mut be updated with the current notation
    # +++ there must be a method called:
    # satisfy power_balance that run the spool power balance and, if the power_balance requirement is not met,
    # updates the turbomachinery geometries --> we need to see how

    @action(label='Run CFD')
    def run_cfd(self):
        """Run CFD analysis on compressor and turbine in parallel."""
        print("[AeroEngine] Starting parallel CFD analysis...")
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_comp = executor.submit(self.spool.compressor.multall_analysis)
            future_turb = executor.submit(self.spool.turbine.multall_analysis)

        try:
            future_comp.result()
        except Exception as e:
            print(f"[AeroEngine] Compressor CFD failed: {e}")

        try:
            future_turb.result()
        except Exception as e:
            print(f"[AeroEngine] Turbine CFD failed: {e}")

        self.spool._cfd_runs_counter += 1

        print("=" * 50)
        print("[AeroEngine] CFD RESULTS")
        print("=" * 50)
        comp_power = self.spool.compressor_power
        turb_power = self.spool.power_estimated
        delta_power = turb_power - comp_power
        print(f"Compressor shaft power: {comp_power:.2f} W")
        print(f"Turbine shaft power: {turb_power:.2f} W")
        print(f"Power balance delta: {delta_power:.2f} W")
        print("=" * 50)

    @action(label='Compute weights')
    def compute_weights(self):
        """Evaluate total_weight and log component breakdown."""
        frame_w = self.engine_frame.weight
        combustor_w = self.combustor.weight
        compressor_w = self.spool.compressor.weight
        turbine_w = self.spool.turbine.weight
        spool_total = self.spool.total_weight
        shaft_w = spool_total - compressor_w - turbine_w
        total_w = self.total_weight

        print("=" * 50)
        print(f"{'Component':<20} | {'Weight [kg]':>20}")
        print("-" * 50)
        print(f"{'EngineFrame':<20} | {frame_w:>20.3f}")
        print(f"{'Combustor':<20} | {combustor_w:>20.3f}")
        print(f"{'Compressor':<20} | {compressor_w:>20.3f}")
        print(f"{'Turbine':<20} | {turbine_w:>20.3f}")
        print(f"{'Shaft':<20} | {shaft_w:>20.3f}")
        print("-" * 50)
        print(f"{'TOTAL':<20} | {total_w:>20.3f}")
        print("=" * 50)

    # @action(label='Export report')
    # def export_report(self):
    #     """Instantiate ReportWriter and export the full engine report."""
    #     # TODO: Uncomment once ReportWriter module exists:
    #     # writer = ReportWriter(
    #     #     engine=self,
    #     #     performance=self.preliminary_performance,
    #     #     weight=self.total_weight,
    #     # )
    #     # writer.export()
    #     print("[AeroEngine] export_report: ReportWriter not yet implemented.")
    #     print("[AeroEngine] Preliminary performance summary:")
    #     for key, val in self.preliminary_performance.items():
    #         print(f"  {key}: {val:.4f}")

    @action(label='Show Compressor')
    def show_compressor_action(self):
        """Show/render compressor blades in the 3D canvas."""
        self.show_compressor = True

    @action(label='Show Turbine')
    def show_turbine_action(self):
        """Show/render turbine blades in the 3D canvas."""
        self.show_turbine = True


# ======================================================================
# Smoke test — instantiate with dummy inputs (no real .xlsx needed)
# ======================================================================

if __name__ == '__main__':
    from parapy.gui import display

    engine = AeroEngine(
        work_dir="Multall/DesignExample",
        label="AeroEngine_test",
    )

    display(engine)