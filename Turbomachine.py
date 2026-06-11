"""
Turbomachine.py
===============
Abstract turbomachine (parent of Compressor and Turbine).

Responsibilities (matching the UML):
  1. ELABORATE the data coming from Spool (rpm, mean radius) together with the
     inlet FlowStation (gas state) and the turbomachine design knobs into a
     single `meangen_input` dict — the input for the meanline design.
  2. OWN the MultallSolver as a @Part, which runs:
        - the LOW-fidelity pipeline (meangen + stagen) automatically, because
          the blade geometry is built from its output;
        - the HIGH-fidelity solver (multall) on demand via `multall_analysis`.
  3. PARSE the low-fidelity output (meangen.out + stagen.out) with the existing
     MeagenParser / StageParser, and build one Stage per stage from that data.

Inheritance:
    Turbomachine(EngineComponent, GeomBase)
  - EngineComponent gives the thermo-fluid contract (inflow_conditions,
    pressure_ratio, isos_efficiency, station_in/out, overridable area_in/out).
  - GeomBase gives the position frame used to host and stack the Stage parts.
  Compressor / Turbine subclass this and only set what distinguishes them
  (machine_type, and the design coefficients / presets).

Coordinate system (engine frame): X axial, Y radial, Z tangential.
"""

from pathlib import Path
import os

from parapy.core import Input, Attribute, Part, child, action
from parapy.geom import GeomBase, Compound

from EngineComponent import EngineComponent
from Stage import Stage
from MultallSolver import MultallSolver

from MeagenParser import MeagenParser
from StageParser import StageParser
from plot_blade_profile import plot_blade_profiles


class Turbomachine(EngineComponent, GeomBase):
    """Common base for axial compressors and turbines driven by Multall."""

    # ------------------------------------------------------------------
    # Inputs — coming from Spool / the architecture
    # ------------------------------------------------------------------

    machine_type = Input('compressor')
    """'compressor' or 'turbine'. Subclasses (Compressor/Turbine) pin this.
    Drives the 'C'/'T' MEANGEN flag and the rotor/stator row order in Stage."""

    n_stages = Input(3)
    """Number of stages in this machine (Spool sizes this)."""

    rpm = Input(3600)
    """Shaft rotational speed [rev/min], shared across the spool."""

    design_radius = Input()
    """Meanline design-point radius [m] (the mean blade radius)."""

    # ------------------------------------------------------------------
    # Inputs — meanline design knobs (Compressor/Turbine override via presets)
    # ------------------------------------------------------------------

    reaction      = Input(0.5)
    flow_coeff    = Input(0.5)
    loading_coeff = Input(1.0)

    blade_axial_chords = Input([0.03, 0.04])
    """Axial chords [m] passed to MEANGEN (one value per blade row per stage)."""

    row_gap   = Input(0.25)   # blade-row gap as fraction of axial chord
    stage_gap = Input(0.50)   # inter-stage gap as fraction of axial chord
    twist     = Input(0)

    gas_constant = Input(287.15)
    """Specific gas constant R [J/(kg.K)].
    Used as fallback if FlowStation does not expose gas_constant directly."""

    # ------------------------------------------------------------------
    # Inputs — geometry / meshing resolution
    # ------------------------------------------------------------------

    n_pts     = Input(60)      # blade profile resampling resolution

    # ------------------------------------------------------------------
    # Inputs — solver configuration (forwarded to MultallSolver)
    # ------------------------------------------------------------------

    work_dir = Input('Multall/DesignExample')
    """Working directory for THIS machine's Multall files. Compressor and
    turbine must use different folders (e.g. .../multall/compressor)."""

    meangen_exe      = Input('Multall/executables/meangen-17.4.exe')
    stagen_exe       = Input('Multall/executables/stagen-18.1.exe')
    multall_exe      = Input('Multall/executables/multall-open-20.9.exe')

    # ------------------------------------------------------------------
    # Derived scalars
    # ------------------------------------------------------------------

    @Attribute
    def turbo_typ_code(self):
        """MEANGEN machine flag: 'C' for compressor, 'T' for turbine."""
        return {'compressor': 'C', 'turbine': 'T'}[self.machine_type]

    @Attribute
    def effective_gas_constant(self):
        """Gas constant R [J/(kg.K)].

        Reads from FlowStation.gas_constant if the attribute exists; falls back
        to the gas_constant Input so the class still works standalone.
        """
        station = self.inflow_conditions
        if hasattr(station, 'gas_constant'):
            return station.gas_constant
        return self.gas_constant

    @Attribute
    def axial_gap(self):
        """ Metric gap between the two rows in a Stage [m]"""
        return self.row_gap*self.blade_axial_chords[-1]

    # ------------------------------------------------------------------
    # 1) ELABORATION — assemble the meanline-design input for MEANGEN
    # ------------------------------------------------------------------

    @Attribute
    def meangen_input(self):
        """Meanline-design parameters serialised into meangen.in.

        Units: MEANGEN expects POIN in bar. FlowStation.p_total is in Pa,
        so it is scaled by 1e5 here.
        """
        return dict(
            turbo_typ     = self.turbo_typ_code,
            rgas          = self.effective_gas_constant,
            gamma         = self.inflow_conditions.gamma,
            poin          = self.inflow_conditions.p_total / 1e5,   # Pa -> bar
            toin          = self.inflow_conditions.T_total,
            n_stages      = self.n_stages,
            rpm           = self.rpm,
            mass_flow     = self.inflow_conditions.mass_flow,
            reaction      = self.reaction,
            flow_coeff    = self.flow_coeff,
            loading_coeff = self.loading_coeff,
            design_radius = self.design_radius,
            axial_chords  = self.blade_axial_chords,
            row_gap       = self.row_gap,
            stage_gap     = self.stage_gap,
            eta_guess     = self.isos_efficiency,
            twist         = self.twist,
        )

    # ------------------------------------------------------------------
    # 2) SOLVER — MultallSolver as a @Part
    # ------------------------------------------------------------------

    @Part
    def solver(self):
        """The Multall pipeline wrapper. Reading solver.stagen_out_path (done
        in `stage_data`) triggers the low-fidelity meangen+stagen run."""
        return MultallSolver(
            work_dir         = self.work_dir,
            meangen_exe      = self.meangen_exe,
            stagen_exe       = self.stagen_exe,
            multall_exe      = self.multall_exe,
            meangen_input    = self.meangen_input,
        )

    # ------------------------------------------------------------------
    # 3) PARSING — turn the low-fidelity output into per-stage geometry data
    # ------------------------------------------------------------------

    @Attribute
    def stage_data(self):
        """List of per-stage dicts used to build the Stage parts."""
        return self._build_stage_data()

    def _build_stage_data(self):
        """Parse the low-fidelity output into per-stage geometry data.

        Plain method (imperative logic allowed). MeagenParser reads stagen.dat
        (authoritative source for row type, blade count, metric chords and
        stagger); StageParser reads suction/pressure profiles from stagen.out;
        merge() fuses them.

        Accessing solver.stagen_out_path is what triggers meangen + stagen,
        so both stagen.dat and stagen.out exist before they are parsed.
        """
        out_path = self.solver.stagen_out_path   # triggers the low-fidelity run
        dat_path = self.solver.stagen_dat_path
        meagen_rows = MeagenParser.parse(dat_path)
        row_order = [r['row_type'] for r in meagen_rows]
        stages = StageParser.parse(out_path, row_order=row_order, machine_type=self.machine_type)
        merged = MeagenParser.merge(stages, meagen_rows)
        for i, st in enumerate(merged):
            rc = sum(st['rotor']['chords'])  / len(st['rotor']['chords'])
            sc = sum(st['stator']['chords']) / len(st['stator']['chords'])
            print(f"[stage_data] stage {i}: rotor chord={rc:.4f}m, "
                  f"stator chord={sc:.4f}m, "
                  f"stator_LE_offset={rc + self.axial_gap:.4f}m")
        return merged

    # ------------------------------------------------------------------
    # Axial stacking of the stages
    # ------------------------------------------------------------------

    @Attribute
    def stage_axial_lengths(self):
        """Approximate axial length [m] of each stage.

        References self.axial_gap and self.stage_gap directly in the
        @Attribute body so ParaPy registers them as dependencies and
        invalidates this attribute when either gap Input changes.
        """
        axial_gap   = self.axial_gap    # intra-stage row gap [m]
        stage_gap_f = self.stage_gap    # inter-stage gap as fraction of rotor chord
        result = []
        for st in self.stage_data:
            rotor_c  = sum(st['rotor']['chords'])  / len(st['rotor']['chords'])
            stator_c = sum(st['stator']['chords']) / len(st['stator']['chords'])
            result.append(rotor_c + axial_gap + stator_c + stage_gap_f * rotor_c)
        return result

    @Attribute
    def stage_axial_starts(self):
        """X position [m] of each stage's leading edge along the engine axis."""
        return self._cumulative(self.stage_axial_lengths)

    @staticmethod
    def _cumulative(lengths):
        """Running start positions: [0, L0, L0+L1, ...]. Plain method."""
        starts = []
        x      = 0.0
        for length in lengths:
            starts.append(x)
            x += length
        return starts

    # ------------------------------------------------------------------
    # GEOMETRY — one Stage per stage, fed from the parsed data
    # ------------------------------------------------------------------

    @Part
    def body(self):
        """Quantified Stage parts, stacked along X.

        Stacking is fed through Stage.stage_axial_offset (NOT the position
        frame): Blade builds its geometry from absolute coordinates via
        Blade.axial_offset, so a position frame would not translate the blades.
        Each stage's leading edge sits at the cumulative start computed in
        `stage_axial_starts`.
        """
        return Stage(
            quantify              = self.n_stages,
            stage_type            = self.machine_type,
            # --- rotor row (parsed slice for this stage) ---
            rotor_profiles_suc    = self.stage_data[child.index]['rotor']['suction'],
            rotor_profiles_prs    = self.stage_data[child.index]['rotor']['pressure'],
            rotor_r_sections      = self.stage_data[child.index]['rotor']['r_sections'],
            rotor_span_fractions  = self.stage_data[child.index]['rotor']['span_fractions'],
            rotor_chords          = self.stage_data[child.index]['rotor']['chords'],
            rotor_pitch_angles    = self.stage_data[child.index]['rotor']['pitch_angles'],
            rotor_n_blades        = self.stage_data[child.index]['rotor']['n_blades'],
            # --- stator row ---
            stator_profiles_suc   = self.stage_data[child.index]['stator']['suction'],
            stator_profiles_prs   = self.stage_data[child.index]['stator']['pressure'],
            stator_r_sections     = self.stage_data[child.index]['stator']['r_sections'],
            stator_span_fractions = self.stage_data[child.index]['stator']['span_fractions'],
            stator_chords         = self.stage_data[child.index]['stator']['chords'],
            stator_pitch_angles   = self.stage_data[child.index]['stator']['pitch_angles'],
            stator_n_blades       = self.stage_data[child.index]['stator']['n_blades'],
            # --- layout ---
            axial_gap             = self.axial_gap,
            n_pts                 = self.n_pts,
            stage_axial_offset    = self.stage_axial_starts[child.index],
            rotor_color           = self.material.color,
        )

    # ------------------------------------------------------------------
    # HIGH-fidelity analysis (orchestration + geometry feedback)
    # ------------------------------------------------------------------

    @action(label='Run Multall CFD analysis')
    def multall_analysis(self):
        """GUI button: run the 3D Multall CFD and refresh the model.

        TODO #2: parse self.solver.flow_out_path for refined cross-sectional
        areas / efficiencies and override the inherited EngineComponent inputs
        so the geometry updates. Hand refined power balance back to parent Spool.
        """
        self.solver.run_cfd()

    @action(label='Plot blade profiles')
    def plot_profiles(self):
        """GUI button: plot rotor and stator blade profiles for every stage.

        One matplotlib figure per stage, one subplot per spanwise section.
        Rotor in blue, stator in red. Opens an interactive plot window.
        """
        plot_blade_profiles(
            stage_data   = self.stage_data,
            machine_type = self.machine_type,
        )

    # ------------------------------------------------------------------
    # Mass estimate
    # ------------------------------------------------------------------

    @Attribute
    def weight(self):
        """Total blade mass [kg] = sum of all blade volumes * density.

        Blade exposes a `volume` @Attribute (LoftedSolid `body.volume`).
        Disk/shaft mass is not included.
        """
        return self.material.density * sum(
            blade.volume
            for stage in self.body
            for row in (stage.rotor_blades, stage.stator_blades)
            for blade in row
        )

    @Attribute
    def detailed_features(self):
        """Container for high-fidelity results (filled by multall_analysis).
        Matches the UML 'detailed_features: dict[str, float]'."""
        return {}


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    from parapy.gui import display
    from Flow_station import FlowStation

    inlet = FlowStation(
        station_number=2,
        fluid_type='air',
        p_total=101325.0,
        T_total=288.15,
        mass_flow=20.0,
        Mach=0.5,
    )

    work = Path(__file__).resolve().parent / 'Multall' / 'DesignExample' / 'test_run_c'

    compressor = Turbomachine(
        machine_type='turbine',
        inflow_conditions=inlet,
        pressure_ratio=4.0,
        isos_efficiency=0.90,
        n_stages=1,
        stage_gap = 1,
        row_gap = 0.5,
        rpm=1200.0,
        design_radius=0.35,
        work_dir=str(work),
        label='HPC',
    )

    print(f"machine        = {compressor.machine_type} ({compressor.turbo_typ_code})")
    print(f"n_stages       = {compressor.n_stages}")
    print(f"meangen_input  = {compressor.meangen_input}")

    display(compressor, view='top', autodraw=True)