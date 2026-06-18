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
import os
import shutil
import importlib.util
import warnings
import logging
from pathlib import Path
import math
import math as _math
import numpy as np
from scipy.optimize import brentq

class InfoWarningFilter(logging.Filter):
    def filter(self, record):
        return record.levelno < logging.ERROR

class DynamicStreamHandler(logging.StreamHandler):
    def __init__(self, stream_name):
        logging.Handler.__init__(self)
        self.stream_name = stream_name

    @property
    def stream(self):
        return getattr(sys, self.stream_name)

_log = logging.getLogger("AeroEngine")
_log.setLevel(logging.INFO)
_log.propagate = False
_log.handlers = []

formatter = logging.Formatter("[%(name)s] %(levelname)s: %(message)s")

handler_out = DynamicStreamHandler("stdout")
handler_out.setLevel(logging.INFO)
handler_out.addFilter(InfoWarningFilter())
handler_out.setFormatter(formatter)

handler_err = DynamicStreamHandler("stderr")
handler_err.setLevel(logging.ERROR)
handler_err.setFormatter(formatter)

_log.addHandler(handler_out)
_log.addHandler(handler_err)

for parent in Path(__file__).resolve().parents:
    if (parent / "EngineCore").exists() and (parent / "Thermodynamics").exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break

from parapy.core import Base, Input, Attribute, Part, action, child
from parapy.geom import GeomBase, rotate, XOY, translate, Position, Compound, TranslatedShape, Vector
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
from IO_Management.ReportWriter import ReportWriter
from EngineCore.Turbomachinery.MultallUtilities.MultallSolver import parse_shaft_power


DEFAULT_FLIGHT_CONDITIONS = {
    "altitude": 10668.0,       # m   — cruise altitude
    "Mach": 0.78,              # -   — cruise Mach
    "ISA_deviation": 0.0,      # K   — standard day (temperature deviation)
}

DEFAULT_ENGINE_FEATURES = {
    "IPR":  0.99,              # -   — inlet pressure recovery (typical cruise condition)
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
    "fuel_residence_time": 0.005, # s — Fuel residence time
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
    "spool_tip_fraction": 0.3, # -  — Fraction of inlet_length ahead of compressor LE
    "spool_bottom_fraction": 0.3, # - — Fraction of nozzle_length behind turbine exit
    "inlet_length": 0.55,      # m  — inlet duct axial length
    "nozzle_length": 0.45,     # m — nozzle axial length
    "casing_wall_thickness": 0.012,     # m — casing wall thickness (uniform default)
    "lip_radius_ratio": 0.06,  # - — inlet lip radius ratio
    "containment_margin": 0.0, # - — target fractional containment margin
    "spool_sheet_thickness": 0.015, # m — spool shaft shell thickness
}

DEFAULT_ENGINE_MATERIALS = {
    "C_rotor": "Ti",
    "C_stator": "Ti",
    "T_rotor": "Ti",
    "T_stator": "Ti",
    "shaft": "Ti",
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

    show_compressor = Input(True)
    """If False, the compressor 3D blade geometries are hidden by default to keep load times fast."""

    show_turbine = Input(True)
    """If False, the turbine 3D blade geometries are hidden by default to keep load times fast."""

    postprocess_cfd_results = Input(True)
    """If True, PostPy generates ParaView .dat files after each CFD run
    (compressor/turbine). Forwarded to Spool -> Compressor/Turbine -> MultallSolver."""

    postpy_max_instances = Input(2)
    """Max number of extra passage/blade instances PostPy generates per row.
    Forwarded to Spool -> Compressor/Turbine -> MultallSolver."""

    log_low_fidelity = Input(False)
    """If True: show MEANGEN and STAGEN stdout/stderr in the console"""

    log_high_fidelity = Input(True)
    """If True: show MULTALL CFD stdout/stderr in the console"""

    engine_offset_y = Input(0.0)
    """metres — lateral offset for side-by-side display"""

    engine_offset_z = Input(0.0)
    """metres — vertical offset"""

    section_angle = Input(270.0)
    """degrees — passed to EngineFrame.section_angle_deg"""

    # --- Parsed inputs (InputParser) ---

    @Attribute
    def parsed_inputs(self):
        return self.input_parser.raw_data

    @action(label="Configure Inputs")
    def configure(self):
        """Pre-launch: open GUI, validate, write xlsx, update input_file and work_dir."""
        result = self.input_parser.launch_gui(filepath=self.input_file or None)
        if result is not None:
            self.input_file = result[0]
            self.work_dir = result[1]
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
            target_thrust =      self.engine_features["Thrust_required"],           #   [N]
            # ---- Flight / ambient (station 0) ---------------------------------- #
            M0 = self.design_flight_conditions["Mach"],             #   [-]
            T0 = self.flight_condition_flow.T_total,                                #   [K]
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

    @Input
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

    @Input
    def position(self):
        return translate(rotate(XOY, 'y', 90, deg=True),
                         'y', self.engine_offset_y,
                         'z', self.engine_offset_z)

    # ====================================================================
    # Using the simplified model to build the engine
    # ====================================================================

    def cross_check_stages(self):
        """Cross-check the stage counts and log warnings/errors as needed."""
        for name, n in [("Compressor", self.compressor_n_stages),
                        ("Turbine",    self.turbine_n_stages)]:
            if n >= 12:
                msg = f"ERROR: {name} n_stages={n} >= 12 — MEANGEN will crash (exit code 3)."
                _log.error(msg)
                raise ValueError(msg)
            elif n >= 8:
                _log.warning(
                    f"[AeroEngine] WARNING: {name} n_stages={n} is between 8 and 12. "
                    f"The model will open but CFD will likely crash above 10 stages.\n"
                    f"  Consider reducing "
                    f"{'CPR or increasing stage_PR_max' if name=='Compressor' else 'TIT or increasing T_work_coeff'} "
                    f"before running CFD."
                )

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
        self.input_parser.validate_on_load()
        self.cross_check_stages()

        _log.info("[AeroEngine] Running TurbojetSimplified...")

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
            U_loc = math.sqrt(
                self.compressor_delta_h
                / (self.compressor_n_stages * self.engine_features["C_work_coeff"])
            )
            V_ax = phi * U_loc

            # Static temperature from isentropic energy equation
            T_stat = Tt2 - V_ax ** 2 / (2.0 * cp_a)
            if T_stat <= 0.0:
                return 1e9

            # Axial Mach number
            M_ax = V_ax / math.sqrt(gam * R_a * T_stat)

            # Geometric annulus area
            A_geom = math.pi * (r_tip ** 2 - r_hub ** 2)

            # Required area from the compressible isentropic mass-flow relation
            # (same formula as FlowStation.area — kept inline to avoid object instantiation)
            A_isen = (mass_flow * math.sqrt(R_a * Tt2)) / (
                    pt2 * M_ax * math.sqrt(gam)
                    * (1.0 + (gam - 1.0) / 2.0 * M_ax ** 2)
                    ** (-(gam + 1.0) / (2.0 * (gam - 1.0)))
            )

            return A_geom - A_isen

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

        _log.info("[AeroEngine] Building aux_compressor...")
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

        turbine_inflow_prelim = FlowStation.mach_from_area(
            A_combustor,
            self.simplified_engine.station4.p_total,
            self.simplified_engine.station4.T_total,
            m_g,
            fluid_type="fuel_gas",
        )
        _log.info("[AeroEngine] Building aux_turbine...")
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

        _log.info("[AeroEngine] Building Spool compressor (MEANGEN→STAGEN→MULTALL)...")
        _log.info("[AeroEngine] Building Spool turbine (MEANGEN→STAGEN→MULTALL)...")
        _log.info("[AeroEngine] Building EngineFrame...")
        _log.info("[AeroEngine] Engine build complete.")

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

    _nozzle_inflow_cfd = Input(None)

    @Attribute
    def nozzle_inflow(self):
        return self._nozzle_inflow_cfd if self._nozzle_inflow_cfd is not None \
               else self.build_results["Nozzle"]

    @Attribute
    def spool_design_radius(self):
        return self.build_results["spool_radius"]

    # ------------------------------------------------------------------
    # Internal profile point for the EngineFrame
    # ------------------------------------------------------------------

    @Attribute
    def internal_profile(self):
        # Read actual (x,r) points from self.spool geometry.
        # x coordinates come from Spool's resolved axial stack (inlet LE, compressor TE,
        # turbine LE, turbine TE). Tip radii come from actual Stage child parts.
        return [
            # 1. End of inlet == start of compressor (compressor LE, first rotor tip)
            (self.spool.x_start_compressor,
             self.spool.compressor_tip_r_in),

            # 2. End of compressor == start of combustor (compressor TE, last stator tip)
            (self.spool.compressor_end_x,
             self.spool.compressor_tip_r_out),

            # 3. End of combustor == start of turbine (turbine LE, first stator tip)
            (self.spool.turbine_start_x,
             max(self.spool.turbine_tip_r_in, self.spool.compressor_tip_r_out)),

            # 4. End of turbine == start of nozzle (turbine TE, last rotor tip)
            (self.spool.turbine_end_x,
             self.spool.turbine_tip_r_out),
        ]

    # "casing_length": 1.0,  # m — structural casing barrel axial length -> this must be derived AFTER THE DEFINITION OF THE SPOOL and the combustor length above.
    #
    @Input
    def combustor_length(self):
        """Combustor axial length [m].
        The combustor considered has a diffuser that is 0.5 m long that forces the
        flow to 20 m/s. Using this value with the residence time, we get the actual length
        of the combustor.
        """
        return self.engine_features["fuel_residence_time"]*20 + 0.5

    @Attribute
    def casing_length(self):
        """Axial length of the structural barrel [m].
        Derived from the real Spool geometry: from the end of the inlet duct
        to the turbine exit, as resolved by meangen/stagen. This is the
        authoritative value — derived dynamically from the physical extent of the turbine exit
        whenever the Fortran meanline solution adjusts the axial chord distribution.
        """
        return self.spool.turbine_end_x - self.engine_geometry["inlet_length"]

    # --- Aggregate weight ---

    @Attribute
    def total_weight(self):
        """Sum of child component weights [kg].
        engine_frame.weight + combustor.weight + spool.total_weight"""
        return self.engine_frame.weight + self.combustor.weight + self.spool.total_weight

    # ==================================================================
    # TWO-TIER PERFORMANCE BLOCK
    # ==================================================================

    # ------------------ TIER 1: LOW-FIDELITY @Attributes --------------

    @Attribute
    def exhaust_velocity_1d(self):
        """Nozzle exit velocity from 1D cycle [m/s].
        Read directly from TurbojetSimplified.station8 — avoids
        duplicating the nozzle expansion formula and guarantees
        consistency with the cycle model."""
        return self.simplified_engine.station8.v

    @Attribute
    def specific_thrust_1d(self):
        """Net specific thrust from 1D cycle [N·s/kg] = V8 - V0.
        V0 = self.simplified_engine.v0
        """
        return self.exhaust_velocity_1d - self.simplified_engine.v0

    @Attribute
    def fuel_mass_flow(self):
        """Fuel mass flow [kg/s]. Source: self.simplified_engine.m_f"""
        return self.simplified_engine.m_f

    @Attribute
    def TSFC(self):
        """Thrust specific fuel consumption [kg/N/s].
        Source: self.simplified_engine.TSFC"""
        return self.simplified_engine.TSFC

    @Attribute
    def thermal_efficiency_1d(self):
        """Thermal efficiency [-].
        Source: self.simplified_engine.thermal_efficiency"""
        return self.simplified_engine.thermal_efficiency

    @Attribute
    def propulsive_efficiency_1d(self):
        """Propulsive efficiency [-].
        Source: self.simplified_engine.propulsive_efficiency"""
        return self.simplified_engine.propulsive_efficiency

    @Attribute
    def overall_efficiency_1d(self):
        """Overall efficiency [-].
        Source: self.simplified_engine.overall_efficiency"""
        return self.simplified_engine.overall_efficiency

    @Attribute
    def net_thrust_1d(self):
        """Net core thrust from 1D cycle [N] = mass_flow * specific_thrust_1d."""
        return self.simplified_engine.mass_flow * self.specific_thrust_1d

    @Attribute
    def thermodynamic_cycle(self):
        """dict[int, dict[str, float]] — station-keyed total pressures [Pa] / temps [K]"""
        return {
            2: {"Pt": self.simplified_engine.station2.p_total,
                "Tt": self.simplified_engine.station2.T_total},
            3: {"Pt": self.simplified_engine.station3.p_total,
                "Tt": self.simplified_engine.station3.T_total},
            4: {"Pt": self.simplified_engine.station4.p_total,
                "Tt": self.simplified_engine.station4.T_total},
            5: {"Pt": self.simplified_engine.station5.p_total,
                "Tt": self.simplified_engine.station5.T_total},
            8: {"Pt": self.simplified_engine.station8.p_total,
                "Tt": self.simplified_engine.station8.T_total,
                "v":  self.simplified_engine.station8.v,
                "Mach": self.simplified_engine.station8.Mach},
        }

    # ------------------ TIER 2: HIGH-FIDELITY plain methods -----------

    def _read_postpy_machine(self, work_dir):
        """Read mass-flow-averaged Pt/Tt from MULTALL output via PostPy.
        
        Returns {'Pt_out': float, 'Tt_out': float} or None on any failure.
        
        Guard conditions (return None immediately if any is true):
          - self.spool._cfd_runs_counter == 0
          - <work_dir>/grid_out does not exist
          - <work_dir>/flow_out does not exist
        
        PostPy import MUST use importlib.util to avoid sys.path pollution
        and sys.modules cache collisions between compressor and turbine runs:
        
          spec = importlib.util.spec_from_file_location(
              f"Components_{unique_tag}",
              os.path.join(work_dir, "Components", "__init__.py"),
              submodule_search_locations=[os.path.join(work_dir, "Components")]
          )
          mod = importlib.util.module_from_spec(spec)
          spec.loader.exec_module(mod)
          PostPyMachine = mod.Turbomachine
        
        Where unique_tag = work_dir.replace(os.sep, '_').replace(':', '')
        to guarantee a unique module name per machine.
        
        Then:
          machine  = PostPyMachine(grid_path, flow_path)
          Pt_out   = machine.rows[-1].passage_original.get_mass_flow_average(
                         'Pt_stn', level=1.0, i_lim=[0,1], k_lim=[0,1])
          Tt_out   = machine.rows[-1].passage_original.get_mass_flow_average(
                         'Tt_stn', level=1.0, i_lim=[0,1], k_lim=[0,1])
        
        Wrap everything after the guard in try/except Exception: return None
        """
        if self.spool._cfd_runs_counter == 0:
            return None
        
        grid_path = os.path.join(work_dir, "grid_out")
        flow_path = os.path.join(work_dir, "flow_out")
        if not os.path.exists(grid_path) or not os.path.exists(flow_path):
            return None
        
        try:
            components_src = str(Path(__file__).resolve().parent.parent / "validation" / "PostPy" / "Components")
            components_dst = os.path.join(work_dir, "Components")
            if not os.path.exists(components_dst) and os.path.exists(components_src):
                shutil.copytree(components_src, components_dst)

            unique_tag = work_dir.replace(os.sep, '_').replace(':', '')
            spec = importlib.util.spec_from_file_location(
                f"Components_{unique_tag}",
                os.path.join(work_dir, "Components", "__init__.py"),
                submodule_search_locations=[os.path.join(work_dir, "Components")]
            )
            mod = importlib.util.module_from_spec(spec)
            sys.modules[f"Components_{unique_tag}"] = mod
            sys.modules["Components"] = mod
            spec.loader.exec_module(mod)
            PostPyMachine = mod.Turbomachine

            machine = PostPyMachine(grid_path, flow_path)
            Pt_out = machine.rows[-1].passage_original.get_mass_flow_average(
                'Pt_stn', level=1.0, i_lim=[0, 1], k_lim=[0, 1])
            Tt_out = machine.rows[-1].passage_original.get_mass_flow_average(
                'Tt_stn', level=1.0, i_lim=[0, 1], k_lim=[0, 1])
            return {'Pt_out': Pt_out, 'Tt_out': Tt_out}
        except Exception:
            return None

    def exhaust_velocity_cfd(self):
        """Exhaust velocity from MULTALL turbine exit [m/s], or None.
        
        Reads turbine PostPy results via _read_postpy_machine.
        Uses same formula as exhaust_velocity_1d but with CFD Pt/Tt:
          Tt5_cfd = result['Tt_out']
          Pt5_cfd = result['Pt_out']
          p0      = self.simplified_engine.station0.p_total
          N_eta, cpg, gamma_g from self.engine_features
        
        Returns None if _read_postpy_machine returns None.
        work_dir = self.spool.turbine.work_dir
        """
        result = self._read_postpy_machine(self.spool.turbine.work_dir)
        if result is None:
            return None
        
        Tt5_cfd = result['Tt_out']
        Pt5_cfd = result['Pt_out']
        p0 = self.simplified_engine.station0.p_total
        N_eta = self.engine_features["N_eta"]
        cpg = self.engine_features["cpg"]
        gamma_g = self.engine_features["gamma_g"]
        
        val = 2 * N_eta * cpg * Tt5_cfd * (1 - (p0 / Pt5_cfd) ** ((gamma_g - 1) / gamma_g))
        return val ** 0.5 if val >= 0 else 0.0

    def specific_thrust_cfd(self):
        """Net specific thrust from CFD [N·s/kg], or None.
        = exhaust_velocity_cfd() - self.simplified_engine.v0
        Returns None if exhaust_velocity_cfd() is None.
        """
        v_cfd = self.exhaust_velocity_cfd()
        if v_cfd is None:
            return None
        return v_cfd - self.simplified_engine.v0

    # ------------------ TIER MERGE: performance_summary & geometry_summary ----

    @Attribute
    def performance_summary(self):
        """Preliminary 1-D cycle and high-fidelity CFD performance summary dict."""
        
        return {
            "Thrust [N]":                self.engine_features["Thrust_required"],
            "TSFC [kg/N/s]":             self.TSFC,
            "Exhaust Velocity [m/s]":    self.exhaust_velocity_cfd() or self.exhaust_velocity_1d,
            "Specific Thrust [N·s/kg]":  self.specific_thrust_cfd() or self.specific_thrust_1d,
            "Thermal Efficiency [-]":    self.thermal_efficiency_1d,
            "Propulsive Efficiency [-]": self.propulsive_efficiency_1d,
            "Overall Efficiency [-]":    self.overall_efficiency_1d,
            "Fuel Flow [kg/s]":          self.fuel_mass_flow,
            "TIT [K]":                   self.engine_features["TIT"],
            "CPR [-]":                   self.engine_features["CPR"],
            "CFD fidelity active":       self.exhaust_velocity_cfd() is not None,
            "Net Thrust [N]":            self.net_thrust_1d,
        }

    @Attribute
    def geometry_summary(self):
        """Summary of physical engine dimensions and component stage count."""
        return {
            "Total Length [m]":    self.engine_frame.length,
            "Max Diameter [m]":    self.engine_geometry["d_max"],
            "Inlet Length [m]":    self.engine_geometry["inlet_length"],
            "Nozzle Length [m]":   self.engine_geometry["nozzle_length"],
            "Frame sheet thickness": self.engine_frame.sheet_thickness,
            "Compressor Stages":   self.compressor_n_stages,
            "Turbine Stages":      self.turbine_n_stages,
            "Shaft RPM":           self.shaft_rpm,
            "Total Weight [kg]":   self.total_weight,
            "Total Volume [m^3]":   self.engine_frame.volume,
        }

    @Attribute
    def blade_kinetics_data(self):
        rotor   = self.spool.turbine.body[0].rotor_master
        density = self.spool.turbine_rotor_material_instance.density
        volume  = rotor.volume
        mass    = volume * density
        r_tip   = self.spool.turbine.body[0].rotor_r_sections[-1]
        omega   = self.spool.shaft_rpm * _math.pi / 30.0
        cog     = rotor.cog
        I_xx_geo = rotor.inertia_matrix_flat[0]
        y_cg    = cog.y
        z_cg    = cog.z
        I_x_cg  = (I_xx_geo - volume * (y_cg**2 + z_cg**2)) * density
        return {
            'blade_mass':       mass,
            'blade_tip_radius': r_tip,
            'omega':            omega,
            'blade_inertia':    abs(I_x_cg),
        }

    @Part
    def input_parser(self):
        return InputParser(
            filepath=self.input_file,
            _on_save_callback=self._invalidate_after_save,
        )

    def _invalidate_after_save(self):
        import threading
        import time

        def _do():
            # Hide blade compounds before invalidation to prevent viewer KeyError
            try:
                self.spool.compressor.hidden = True
                self.spool.turbine.hidden    = True
            except Exception:
                pass
            time.sleep(0.5)
            _path = self.input_file
            self.input_file = ""
            self.input_file = _path
            time.sleep(0.3)
            try:
                self.spool.compressor.hidden = False
                self.spool.turbine.hidden    = False
            except Exception:
                pass

        t = threading.Timer(0.0, _do)
        t.daemon = True
        t.start()

    @Part
    def report_writer(self):
        return ReportWriter(
            output_path=os.path.join(self.work_dir, "output"),
            performance_summary=self.performance_summary,
            geometry_summary=self.geometry_summary,
            engine_features=self.engine_features,
            engine_geometry=self.engine_geometry,
            engine_materials=self.engine_materials,
            compressor_stage_data=self.spool.compressor.stage_data,
            turbine_stage_data=self.spool.turbine.stage_data,
            axial_section_path=self.render_axial_section(),
            ts_diagram_path=self.render_ts_diagram(),
            full_assembly_parts=[self.spool, self.engine_frame, self.combustor],
            engine_frame_parts=[self.engine_frame],
            spool_parts=[self.spool],
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
            compressor_inflow=self.compressor_inflow,
            turbine_inflow=self.turbine_inflow,
            compressor_reaction_coeff=self.engine_features["C_reaction_coeff"],
            turbine_reaction_coeff=self.engine_features["T_reaction_coeff"],
            shaft_material=self.engine_materials["shaft"],
            compressor_stator_material = self.engine_materials["C_stator"],
            compressor_rotor_material=self.engine_materials["C_rotor"],
            turbine_stator_material=self.engine_materials["T_stator"],
            turbine_rotor_material=self.engine_materials["T_rotor"],
            gap_length=self.combustor_length,
            x_start_compressor=self.engine_geometry["inlet_length"],
            tip_fraction=self.engine_geometry.get("spool_tip_fraction", 0.3),
            bottom_fraction=self.engine_geometry.get("spool_bottom_fraction", 0.3),
            inlet_length=self.engine_geometry["inlet_length"],
            nozzle_length=self.engine_geometry["nozzle_length"],
            spool_sheet_thickness=self.engine_geometry.get("spool_sheet_thickness", 0.015),
            isos_efficiency=self.spool_mech_efficiency,
            thrust_needed=self.engine_features["Thrust_required"],
            flight_velocity=self.flight_velocity,
            show_compressor=self.show_compressor,
            show_turbine=self.show_turbine,
            postprocess_results=self.postprocess_cfd_results,
            postpy_max_instances=self.postpy_max_instances,
            work_dir_base=self.work_dir,
            log_low_fidelity=self.log_low_fidelity,
            log_high_fidelity=self.log_high_fidelity,
            show_geometry=False,
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
            material_name=self.engine_materials["combustor"],
            eta_comb=self.engine_features["CC_eta"],
            LHV=self.engine_features["LHV"],
            x_offset=self.spool.compressor_end_x,
            show_geometry=False,
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
            inlet_lip_radius_ratio=self.engine_geometry.get("lip_radius_ratio", 0.06),
            internal_profile=self.internal_profile,
            material_name=self.engine_materials["casing"],
            sheet_thickness=self.engine_geometry.get("sheet_thickness", 0.003),
            containment_margin_target=self.engine_geometry["containment_margin"],
            blade_properties  = self.blade_kinetics_data,
            section_angle_deg = self.section_angle,
            show_geometry=False,
            label="engine_frame",
        )

    @Attribute
    def active_frame_solid(self):
        return self.engine_frame.body_section if self.engine_frame.show_section else self.engine_frame.body

    @Attribute
    def engine_solid_color_pairs(self):
        pairs = [
            (self.active_frame_solid, self.engine_frame.material.color),
            (self.combustor.body,     self.combustor.material.color),
            (self.spool.body,         self.spool.shaft_material_instance.color),
        ]
        if self.show_compressor:
            for stage in self.spool.compressor.body:
                if stage.rotor_blades.built_from:
                    pairs.append((stage.rotor_blades, stage.rotor_color))
                if stage.stator_blades.built_from:
                    pairs.append((stage.stator_blades, stage.stator_color))
        if self.show_turbine:
            for stage in self.spool.turbine.body:
                if stage.rotor_blades.built_from:
                    pairs.append((stage.rotor_blades, stage.rotor_color))
                if stage.stator_blades.built_from:
                    pairs.append((stage.stator_blades, stage.stator_color))
        return pairs

    @Attribute
    def engine_solids(self):
        return [s for (s, _c) in self.engine_solid_color_pairs]

    @Attribute
    def engine_colors(self):
        return [c for (_s, c) in self.engine_solid_color_pairs]

    @Part
    def positioned_engine(self):
        return TranslatedShape(
            quantify=len(self.engine_solids),
            shape_in=self.engine_solids[child.index],
            displacement=Vector(0.0, self.engine_offset_y, self.engine_offset_z),
            color=self.engine_colors[child.index],
        )

    # ==================================================================
    # @action SLOTS — GUI buttons
    # ==================================================================

    @action(label='Adapt for Power Balance')
    def adapt_for_power_balance(self):
        """Perform parallel CFD power measurement, check for balance, and adapt turbine stage count if needed."""
        # STEP 1 — Measure current power balance
        result = self.spool.measure_power_balance()
        surplus = (result["turbine_power"]
                   - result["compressor_power"]
                   - self.spool.thrust_power
                   - self.spool.ext_systems_power)

        # STEP 2 — Check if balanced
        if surplus >= 0:
            print(f"[AdaptPowerBalance] Power check passed. Turbine power: {result['turbine_power']:.0f} W, "
                  f"Compressor power: {result['compressor_power']:.0f} W, Surplus: {surplus:.0f} W.")
        else:
            # STEP 3 — Compute extra stages needed
            power_deficit = -surplus
            power_per_stage = result["turbine_power"] / result["n_turbine_stages"]
            n_extra = math.ceil(power_deficit / power_per_stage)

            if n_extra > 3:
                warnings.warn(
                    f"[AdaptPowerBalance] Power deficit requires {n_extra} extra turbine "
                    f"stages, exceeding the 3-stage limit. Capping at 3."
                )
            n_extra = min(n_extra, 3)

            # STEP 4 — Update turbine geometry and re-run turbine CFD
            self.turbine_n_stages += n_extra
            print(f"[AdaptPowerBalance] Added {n_extra} turbine stage(s). Re-running turbine CFD...")
            self.spool.turbine.multall_analysis()
            self.spool._cfd_runs_counter += 1

            # Read updated turbine exit conditions from PostPy
            turb_exit = self._read_postpy_machine(self.spool.turbine.work_dir)

            if turb_exit is not None:
                self._nozzle_inflow_cfd = FlowStation(
                    station_number=5,
                    fluid_type="fuel_gas",
                    p_total=turb_exit["Pt_out"],
                    T_total=turb_exit["Tt_out"],
                    mass_flow=self.simplified_engine.m_g,
                    Mach=turb_exit.get("Mach_out", self.build_results["Nozzle"].Mach),
                )

        # STEP 5 — Print final report
        final_n_stages = self.turbine_n_stages
        if surplus < 0:
            # Re-read new turbine power
            try:
                final_turbine_power = parse_shaft_power(
                    work_dir=self.spool.turbine.work_dir,
                    rpm=self.shaft_rpm,
                    gamma=self.spool.turbine_inflow.gamma,
                    R=self.spool.turbine.effective_gas_constant,
                    mass_flow=self.spool.turbine_inflow.mass_flow,
                    machine_type='turbine'
                )
            except Exception:
                final_turbine_power = self.spool.turbine_inflow.mass_flow * self.spool.turbine_delta_h
            
            final_compressor_power = result["compressor_power"]
            final_surplus = (final_turbine_power
                             - final_compressor_power
                             - self.spool.thrust_power
                             - self.spool.ext_systems_power)
        else:
            final_turbine_power = result["turbine_power"]
            final_compressor_power = result["compressor_power"]
            final_surplus = surplus

        # Print a formatted table:
        print("\n" + "="*50)
        print("          POWER BALANCE ADAPTATION REPORT          ")
        print("="*50)
        print(f"Turbine Power [W]:          {final_turbine_power:.2f}")
        print(f"Compressor Power [W]:       {final_compressor_power:.2f}")
        print(f"Power Surplus [W]:          {final_surplus:.2f}")
        print(f"Turbine Stages (before->after): {result['n_turbine_stages']} -> {final_n_stages}")
        print(f"CFD Nozzle Inflow Active:   {self._nozzle_inflow_cfd is not None}")
        print("="*50 + "\n")

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

    @Attribute
    def postpy_output_paths(self):
        """PostPy ParaView .dat paths for compressor and turbine, engine-wide.
        Pure pass-through to Spool.postpy_output_paths."""
        return self.spool.postpy_output_paths

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

    @action(label='Update casing for containment')
    def update_containment(self):
        """Re-size the casing sheet thickness to meet the target containment
        margin, delegating to the EngineFrame child."""
        return self.engine_frame.update_sheet_thickness_for_containment()

    def render_axial_section(self):
        """
        Render a 2D axisymmetric cross-section of the engine frame and save as PNG.

        Data source: self.engine_frame.profile_points
          List of ParaPy Point objects. Each has .x (axial [m]) and .y (radial [m]).
          The profile is a CLOSED meridional loop — last point connects back to first.
          Plot the closed polygon directly: xs = [p.x for p in pts], ys = [p.y for p in pts].
          Close the polygon by appending xs[0], ys[0] at the end of both lists.

        Also plot the mirror (negative radii) for visual symmetry:
          ys_mirror = [-y for y in ys]
          Plot ys_mirror with the same xs, same color, no label.

        Axis labels: "Axial position x [m]", "Radius r [m]"
        Title: "Engine Axial Cross-Section"
        Fill: ax.fill_between(xs, ys, ys_mirror, alpha=0.15, color='steelblue')
        Line color: 'steelblue', linewidth=1.5
        Grid: True
        aspect: ax.set_aspect('equal')
        Legend: not required.

        Save path:
            out_dir = os.path.join(self.work_dir, "output")
            os.makedirs(out_dir, exist_ok=True)
            save_path = os.path.join(out_dir, "axial_section.png")
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close(fig)

        Return save_path as string.

        matplotlib must be imported inside this method:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
        """
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import os

        pts = self.engine_frame.profile_points
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        if xs:
            xs.append(xs[0])
            ys.append(ys[0])

        ys_mirror = [-y for y in ys]

        fig, ax = plt.subplots()
        ax.plot(xs, ys, color='steelblue', linewidth=1.5)
        ax.plot(xs, ys_mirror, color='steelblue', linewidth=1.5)
        ax.fill_between(xs, ys, ys_mirror, alpha=0.15, color='steelblue')
        ax.set_xlabel("Axial position x [m]")
        ax.set_ylabel("Radius r [m]")
        ax.set_title("Engine Axial Cross-Section")
        ax.grid(True)
        ax.set_aspect('equal')

        out_dir = os.path.join(self.work_dir, "output")
        os.makedirs(out_dir, exist_ok=True)
        save_path = os.path.join(out_dir, "axial_section.png")
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return save_path

    def render_ts_diagram(self):
        """
        Render the thermodynamic T-S cycle diagram and save as PNG.

        Data source: self.thermodynamic_cycle
          dict keyed by station int: {2, 3, 4, 5, 8}
          Each value is a dict with at least "Pt" [Pa] and "Tt" [K].

        Entropy calculation:
          Use the air/gas properties from self.engine_features:
            cp_a  = self.engine_features["cpg"]   # J/kg/K  (use cpg as representative cp)
            gamma = 1.4                             # standard air
            R     = self.engine_features["r_gas"]  # J/kg/K

          Entropy difference from station 2 (reference s=0):
            s[i] = cp_a * ln(Tt[i] / Tt[2]) - R * ln(Pt[i] / Pt[2])

          So: s_ref = 0.0 at station 2.
          Compute s for stations 2, 3, 4, 5, 8 in order.

        Station labels: {2: "2 (Comp. inlet)", 3: "3 (Comp. exit)",
                         4: "4 (TIT)", 5: "5 (Turb. exit)", 8: "8 (Nozzle exit)"}

        Plot:
          - Connect stations in order: 2 → 3 → 4 → 5 → 8
            ax.plot(s_vals, T_vals, 'o-', color='crimson', linewidth=2)
          - Annotate each point:
            ax.annotate(label, xy=(s, T), xytext=(5, 5), textcoords='offset points', fontsize=8)

        Axis labels: "Specific entropy s [J/kg/K]", "Total temperature T [K]"
        Title: "T-S Thermodynamic Cycle Diagram"
        Grid: True

        Save path:
            out_dir = os.path.join(self.work_dir, "output")
            os.makedirs(out_dir, exist_ok=True)
            save_path = os.path.join(out_dir, "ts_diagram.png")
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close(fig)

        Return save_path as string.

        matplotlib must be imported inside this method:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
        Import math inside this method as well: import math
        """
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import math
        import os

        cycle = self.thermodynamic_cycle
        cp_a = self.engine_features["cpg"]
        R = self.engine_features["r_gas"]

        stations = [2, 3, 4, 5, 8]
        labels = {
            2: "2 (Comp. inlet)",
            3: "3 (Comp. exit)",
            4: "4 (Turbine inlet)",
            5: "5 (Nozzle inlet)",
            8: None
        }

        s_vals = []
        T_vals = []

        Tt2 = cycle[2]["Tt"]
        Pt2 = cycle[2]["Pt"]

        for i in stations:
            Tt_i = cycle[i]["Tt"]
            Pt_i = cycle[i]["Pt"]
            s_i = cp_a * math.log(Tt_i / Tt2) - R * math.log(Pt_i / Pt2)
            s_vals.append(s_i)
            T_vals.append(Tt_i)

        fig, ax = plt.subplots()
        ax.plot(s_vals, T_vals, 'o-', color='crimson', linewidth=2)
        for i, station in enumerate(stations):
            label = labels[station]
            if not label:
                continue
            ax.annotate(label, xy=(s_vals[i], T_vals[i]),
                        xytext=(8, 8), textcoords='offset points', fontsize=8)
        ax.set_xlabel("Specific entropy s [J/kg/K]")
        ax.set_ylabel("Total temperature T [K]")
        ax.set_title("T-S Thermodynamic Cycle Diagram")
        ax.grid(True)

        out_dir = os.path.join(self.work_dir, "output")
        os.makedirs(out_dir, exist_ok=True)
        save_path = os.path.join(out_dir, "ts_diagram.png")
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return save_path

    @action(label='Write Report')
    def write_report(self):
        """Render PNGs and generate the PDF design report via ReportWriter."""
        pdf_path = self.report_writer.report_results()
        print(f"[AeroEngine] PDF report written → {pdf_path}")

    @action(label='Save STEP')
    def save_step(self):
        """Export STEP CAD files (full assembly, frame, spool) via ReportWriter."""
        exported = self.report_writer.export_stp()
        for path in exported:
            print(f"[AeroEngine] STEP exported → {path}")

    @action(label='Save CSV')
    def save_csv(self):
        """Export blade profile CSV files via ReportWriter."""
        exported = self.report_writer.export_csv()
        for path in exported:
            print(f"[AeroEngine] CSV exported → {path}")

    @action(label='Show Compressor')
    def show_compressor_action(self):
        """Show/render compressor blades in the 3D canvas."""
        self.show_compressor = True

    @action(label='Show Turbine')
    def show_turbine_action(self):
        """Show/render turbine blades in the 3D canvas."""
        self.show_turbine = True

    def debug_frame_alignment(self):
        """Prints a comparison table of internal_profile points versus actual stage geometry."""
        c_stages = self.spool.compressor.body
        t_stages = self.spool.turbine.body
        
        actual_radii = [
            c_stages[0].rotor_r_sections[-1],
            c_stages[-1].stator_r_sections[-1],
            t_stages[0].stator_r_sections[-1],
            t_stages[-1].rotor_r_sections[-1]
        ]
        
        profile = self.internal_profile
        
        print("=" * 80)
        print("DEBUG FRAME ALIGNMENT")
        print("=" * 80)
        print(f"{'Point Index':<12} | {'x_profile':<12} | {'r_profile':<12} | {'Actual Stage r':<16} | {'Diff':<12}")
        print("-" * 80)
        for i, (x, r) in enumerate(profile):
            act_r = actual_radii[i]
            diff = r - act_r
            print(f"{i:<12} | {x:<12.5f} | {r:<12.5f} | {act_r:<16.5f} | {diff:<12.5f}")
        print("=" * 80)


# ======================================================================
# Smoke test — instantiate with dummy inputs (no real .xlsx needed)
# ======================================================================

if __name__ == '__main__':
    from parapy.gui import display

    engine = AeroEngine(
        work_dir="design/FullEngine",
        label="AeroEngine_test",
    )

    # engine2=AeroEngine(
    #     work_dir="design/Eg",
    #     label="AeroEngine_test2",
    #     engine_offset_y=0,
    #     engine_offset_z=2.5,
    # )
    #
    # bk  = engine.blade_kinetics_data
    # print(f"blade_mass        = {bk['blade_mass']:.4f} kg")
    # print(f"blade_tip_radius  = {bk['blade_tip_radius']:.4f} m")
    # print(f"omega             = {bk['omega']:.2f} rad/s")
    # print(f"blade_inertia     = {bk['blade_inertia']:.6f} kg*m^2")
    # assert bk['blade_mass'] > 0,        "blade_mass must be positive"
    # assert bk['blade_tip_radius'] > 0,  "blade_tip_radius must be positive"
    # assert bk['omega'] > 0,             "omega must be positive"
    # assert bk['blade_inertia'] > 0,     "blade_inertia must be positive"

    display(engine)