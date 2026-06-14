# AeroEngine.py
"""
AeroEngine — top-level parametric turbofan orchestrator.

Class hierarchy (this file builds the root):
    AeroEngine (Base)
    ├── engine_frame : EngineFrame   (structural casing, starts at global x=0)
    ├── combustor    : Combustor     (annular, between compressor and turbine)
    └── spool        : Spool         (hosts Compressor + Turbine internally)

Coordinate system (engine frame): X axial (spin axis), Y radial, Z tangential.
Default orientation: rotate(XOY, 'y', radians(90)) so local Z maps onto global X.
EngineFrame sits at x=0; the spool and combustor stack axially via x_offset inputs.

NOTE ON SCOPE: this is the first wiring pass. The child classes expose richer
(and slightly differently named) signatures than the simplified UML — every
place where the UML/spec name does not match the implemented child input is
flagged with a numbered # TODO for the Architect to confirm.
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
from parapy.geom import rotate, translate, XOY
from math import radians

from EngineCore.Ducts.EngineFrame import EngineFrame
from EngineCore.Combustor import Combustor
from EngineCore.Turbomachinery.Spool import Spool
from Thermodynamics.FlowStation import FlowStation          # data carrier passed as Input to children
# from InputParser import InputParser
# from ReportWriter import ReportWriter


class AeroEngine(Base):
    """Parametric turbofan assembly: frame + combustor + spool."""

    # ------------------------------------------------------------------
    # Inputs
    # ------------------------------------------------------------------
    input_file = Input("")                     # path to .xlsx input file
    engine_architecture = Input("turbofan")    # "turbofan" | "turbojet"

    design_flight_conditions = Input({})       # {altitude, Mach, isa_deviation}
    engine_features = Input({})                # {BPR, OPR, TET, mass_flow, ...}

    # Station-keyed cycle data. UML typed this dict[int, float]; a single float
    # per station is not enough to build a FlowStation, so we accept a per-station
    # sub-dict {p_total, T_total, mass_flow, Mach, fluid_type}.
    # TODO #1: confirm the cycle-dict schema with the Architect (and whether the
    #          1D cycle solver should produce it instead of the xlsx parser).
    thermodynamic_cycle = Input({})

    material_name = Input("Ti-6Al-4V")         # default structural material

    # Axial stacking offsets [m]. Parametric so the layout stays editable.
    # TODO #2: derive these from component lengths (inlet_length, compressor
    #          length, combustor length) once those are exposed for chaining.
    spool_x_offset = Input(0.0)
    combustor_x_offset = Input(0.37)

    # ------------------------------------------------------------------
    # Position convention — engine spin axis = global X
    # ------------------------------------------------------------------
    @Input
    def position(self):
        return rotate(XOY, 'y', radians(90))

    # ------------------------------------------------------------------
    # Parsed inputs (InputParser is a plain utility class, not a ParaPy Part)
    # ------------------------------------------------------------------
    # @Attribute
    # def parsed_inputs(self):
    #     # TODO #3: confirm InputParser constructor/method names. UML shows
    #     #          input_path + decode_inputs(); adjust if the real signature differs.
    #     return InputParser(input_path=self.input_file).decode_inputs()

    # ------------------------------------------------------------------
    # FlowStation set built from the thermodynamic cycle.
    # Single-return dict comprehension keeps the @Attribute body legal.
    # TODO #4: confirm which station number feeds which child (mapping below).
    # ------------------------------------------------------------------
    @Attribute
    def flow_stations(self):
        return {
            n: FlowStation(
                station_number=n,
                fluid_type=s.get('fluid_type', 'air'),
                p_total=s['p_total'],
                T_total=s['T_total'],
                mass_flow=s.get('mass_flow', self.engine_features.get('mass_flow', 20.0)),
                Mach=s.get('Mach', 0.3),
            )
            for n, s in self.thermodynamic_cycle.items()
        }

    # ------------------------------------------------------------------
    # Mass roll-up. Direct self.* refs so ParaPy dependency tracking fires.
    # ------------------------------------------------------------------
    @Attribute
    def total_weight(self):
        return (self.engine_frame.weight
                + self.combustor.weight
                + self.spool.weight)

    # ------------------------------------------------------------------
    # Preliminary 1D performance (no CFD).
    # TODO #5: replace the placeholder formulas with the Architect's 1D cycle
    #          equations. Current values are rough order-of-magnitude only.
    # ------------------------------------------------------------------
    @Attribute
    def preliminary_performance(self):
        return {
            'thrust_N': self.engine_features.get('mass_flow', 0.0)
                        * self.design_flight_conditions.get('Mach', 0.0) * 340.0,  # m_dot * V_flight (a≈340 m/s)
            'sfc': self.engine_features.get('TET', 0.0) * 0.0,                       # TODO: fuel_flow / thrust
            'eta_overall': self.engine_features.get('OPR', 1.0) * 0.0,              # TODO: eta_thermal * eta_prop
        }

    # ------------------------------------------------------------------
    # Children
    # ------------------------------------------------------------------
    @Part
    def engine_frame(self):
        # Frame anchors the assembly at the global origin (its own x_offset=0).
        # TODO #6: internal_profile is left at the Inlet/Nozzle defaults; it
        #          should be driven by the spool/combustor radii for consistency.
        return EngineFrame(
            inlet_inflow=self.flow_stations[1],
            nozzle_inflow=self.flow_stations[6],
            material_name=self.material_name,
            position=self.position,
        )

    @Part
    def combustor(self):
        # internal_radius / external_radius / length: UML inputs — present on the
        # real Combustor. inflow = compressor exit (st.3), outlet = TIT (st.4).
        # TODO #7: pull radii/length from engine_features instead of hard defaults.
        return Combustor(
            inflow_conditions=self.flow_stations[3],
            outlet_flow=self.flow_stations[4],
            station_out=4,
            internal_radius=0.15,
            external_radius=0.30,
            length=0.40,
            material_name=self.material_name,
            position=translate(self.position, 'x', self.combustor_x_offset),
        )

    @Part
    def spool(self):
        # NOTE: the implemented Spool does NOT take shaft_radius/shaft_length/
        # turbine_position/compressor_position (UML names). Those are internal
        # @Attributes; the real inputs are hub/tip radii + two FlowStations.
        # TODO #8: confirm hub/tip radii — left at Spool defaults for now.
        # TODO #9: spool_index drives HP/IP/LP; fixed to 0 (HP) until the
        #          multi-spool architecture is wired from engine_architecture.
        return Spool(
            spool_index=0,
            inflow_conditions=self.flow_stations[3],          # compressor inlet
            turbine_inflow_conditions=self.flow_stations[4],  # combustor exit
            n_stages_compressor=int(self.engine_features.get('n_stages_compressor', 3)),
            n_stages_turbine=int(self.engine_features.get('n_stages_turbine', 1)),
            rpm=self.engine_features.get('rpm', 15000.0),
            material_name=self.material_name,
            position=translate(self.position, 'x', self.spool_x_offset),
        )

    # ------------------------------------------------------------------
    # GUI actions
    # ------------------------------------------------------------------
    @action(label='Run CFD analysis')
    def run_cfd_analysis(self):
        """Run the high-fidelity Multall CFD on both turbomachines."""
        # TODO #10: spec named spool.compressor.solver.run(); the implemented
        #           entry point is Turbomachine.multall_analysis() (which wraps
        #           self.solver.run_cfd()). Spool also offers power_balance().
        self.spool.compressor.multall_analysis()
        self.spool.turbine.multall_analysis()
        # TODO #11: lazy evaluation refreshes dependents automatically. If an
        #           explicit cache flush is ever needed, use the documented
        #           ParaPy invalidation API — do NOT assume self.invalidate().

    @action(label='Compute weights')
    def compute_weights(self):
        """Force evaluation of the mass roll-up and log it."""
        print(f"[AeroEngine] total_weight = {self.total_weight:.3f} kg")

    # @action(label='Export report')
    # def export_report(self):
    #     """Instantiate ReportWriter and emit the results report."""
    #     # TODO #12: confirm ReportWriter method name. UML shows report_results()
    #     #           and export_stp(); the spec said export(). Using report_results().
    #     return ReportWriter(
    #         output_path="aero_engine_report",
    #         performance_results=self.preliminary_performance,
    #         engine_features=self.engine_features,
    #         geometry_summary={'total_weight': self.total_weight},
    #     ).report_results()


# ---------------------------------------------------------------------------
# Smoke test — dummy dict inputs, no real xlsx needed
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    dummy_cycle = {
        1: {'p_total': 101325.0, 'T_total': 288.15, 'mass_flow': 25.0, 'Mach': 0.50, 'fluid_type': 'air'},
        3: {'p_total': 250000.0, 'T_total': 400.0,  'mass_flow': 25.0, 'Mach': 0.45, 'fluid_type': 'air'},
        4: {'p_total': 1300000.0,'T_total': 1500.0, 'mass_flow': 25.5, 'Mach': 0.30, 'fluid_type': 'fuel_gas'},
        6: {'p_total': 180000.0, 'T_total': 900.0,  'mass_flow': 25.5, 'Mach': 0.40, 'fluid_type': 'fuel_gas'},
    }

    engine = AeroEngine(
        engine_architecture='turbofan',
        design_flight_conditions={'altitude': 11000.0, 'Mach': 0.78, 'isa_deviation': 0.0},
        engine_features={'BPR': 5.0, 'OPR': 30.0, 'TET': 1500.0, 'mass_flow': 25.0,
                         'n_stages_compressor': 5, 'n_stages_turbine': 2, 'rpm': 15000.0},
        thermodynamic_cycle=dummy_cycle,
    )

    print(f"architecture  = {engine.engine_architecture}")
    print(f"total_weight  = {engine.total_weight:.3f} kg")
    print(f"performance   = {engine.preliminary_performance}")