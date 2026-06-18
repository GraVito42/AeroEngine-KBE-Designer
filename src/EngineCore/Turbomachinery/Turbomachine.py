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
     MeangenParser / StageParser, and build one Stage per stage from that data.

Inheritance:
    Turbomachine(EngineComponent, GeomBase)
  - EngineComponent gives the thermo-fluid contract (inflow_conditions,
    pressure_ratio, isos_efficiency, station_in/out, overridable area_in/out).
  - GeomBase gives the position frame used to host and stack the Stage parts.
  Compressor / Turbine subclass this and only set what distinguishes them
  (machine_type, and the design coefficients / presets).

Coordinate system (engine frame): X axial, Y radial, Z tangential.
"""

# Ensure project root is in sys.path when running this file directly
import sys
from pathlib import Path
for parent in Path(__file__).resolve().parents:
    if (parent / "EngineCore").exists() and (parent / "Thermodynamics").exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break

from pathlib import Path
import math

from parapy.core import Input, Attribute, Part, child, action
from parapy.geom import GeomBase, Compound

from EngineCore.EngineComponent import EngineComponent
from EngineCore.Turbomachinery.Stage import Stage
from EngineCore.Material import Material
from EngineCore.Turbomachinery.MultallUtilities.MultallSolver import MultallSolver

from EngineCore.Turbomachinery.MultallUtilities.MeangenParser import MeangenParser
from EngineCore.Turbomachinery.MultallUtilities.StageParser import StageParser, validate_stage_data
from EngineCore.Turbomachinery.plot_blade_profile import plot_blade_profiles


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SOFTWARES = PROJECT_ROOT / 'softwares' / 'Multall'


class Turbomachine(EngineComponent, GeomBase):
    """Common base for axial compressors and turbines driven by Multall."""

    # ------------------------------------------------------------------
    # Inputs — coming from Spool / the architecture
    # ------------------------------------------------------------------

    machine_type = Input('compressor')

    show_blades = Input(False)
    """If False, the 3D blade geometries are hidden by default to keep load times fast."""

    show_geometry = Input(True)
    """If False, the turbomachine stages are hidden by default."""
    """'compressor' or 'turbine'. Subclasses (Compressor/Turbine) pin this.
    Drives the 'C'/'T' MEANGEN flag and the rotor/stator row order in Stage."""

    n_stages = Input(3)
    """Number of stages in this machine (Spool sizes this)."""

    rpm = Input(3600)
    """Shaft rotational speed [rev/min], shared across the spool."""

    design_radius = Input()
    """Meanline design-point radius [m] (the mean blade radius)."""

    stator_material_name = Input("Steel-4340")
    """Material name for the stator rows."""

    @Part
    def stator_material(self):
        """Material representation for stator color/density lookup."""
        return Material(material_name=self.stator_material_name)


    # ------------------------------------------------------------------
    # Inputs — PHYSICAL REQUIREMENTS of the machine (primary design knobs)
    # The meanline coefficients below are DERIVED from these. Each has an
    # adaptive default (rule-of-thumb), so the class runs standalone, but
    # they are meant to be pinned from the cycle analysis / Spool.
    # ------------------------------------------------------------------

    @Input
    def U(self):
        """Blade speed at the design (mean) radius [m/s].
        Default: U = omega * r_mean = (rpm * pi/30) * design_radius."""
        return self.rpm * math.pi / 30.0 * self.design_radius

    @Input
    def V_ax(self):
        """Axial (meridional) flow velocity [m/s].
        Default: the inlet absolute velocity, assuming axial inflow (no swirl)."""
        return self.inflow_conditions.v

    @Input
    def delta_H(self):
        """Total specific enthalpy change across the WHOLE machine [J/kg].
        Default (magnitude): cp * |T0_out - T0_in|, driven by pressure_ratio
        and isos_efficiency through EngineComponent.outlet_flow."""
        return self.station_in.cp * abs(
            self.station_out_part.T_total - self.station_in.T_total)

    @Input
    def delta_H_stage(self):
        """Total specific enthalpy change PER STAGE [J/kg].
        Default: even split, delta_H / n_stages. Override for biased loading."""
        return self.delta_H / self.n_stages

    #: [-] Degree of reaction. INDEPENDENT design parameter — it is NOT derivable
    #  from (U, V_ax, delta_H, delta_H_stage) alone; it sets the rotor/stator
    #  enthalpy split and needs a velocity-triangle angle to be computed.
    #  See reaction_from_inlet_swirl() if you have the inlet swirl angle.
    reaction = Input(0.5)

    # ------------------------------------------------------------------
    # DERIVED meanline coefficients (consumed by meangen_input unchanged)
    # Kept as @Input-with-default so they remain individually overridable.
    # ------------------------------------------------------------------

    @Input
    def flow_coeff(self):
        """Flow coefficient  phi = V_ax / U  [-]."""
        return self.V_ax / self.U

    @Input
    def loading_coeff(self):
        """Stage loading coefficient  psi = |delta_H_stage| / U^2  [-]."""
        return abs(self.delta_H_stage) / self.U ** 2

    @Attribute
    def delta_Vtheta(self):
        """Euler tangential-velocity change per stage  dCtheta = delta_H_stage / U  [m/s]."""
        return self.delta_H_stage / self.U

    @Attribute
    def stages_required(self):
        """Minimum stage count implied by the two enthalpy requirements [-].
        Diagnostic only — n_stages stays the primary input (set by Spool)."""
        return math.ceil(abs(self.delta_H) / abs(self.delta_H_stage))

    @Attribute
    def coefficients(self):
        """The three meanline coefficients in one dict (for ReportWriter)."""
        return {"flow_coeff": self.flow_coeff,
                "loading_coeff": self.loading_coeff,
                "reaction": self.reaction}

    def reaction_from_inlet_swirl(self, alpha1_deg):
        """Compute degree of reaction from the inlet absolute swirl angle.

        Axial NORMAL-stage relation (constant V_ax, mean radius):
            Lambda = 1 - psi/2 - phi * tan(alpha1)
        Use this only when alpha1 is known; otherwise `reaction` is a free input.
        """
        return 1.0 - self.loading_coeff / 2.0 \
            - self.flow_coeff * math.tan(math.radians(alpha1_deg))

    blade_axial_chords = Input(None)
    """Axial chords [m] per blade row [rotor, stator].
    If None, estimated from design_radius and blade_AR via blade_axial_chords_estimated.
    Override with an explicit [c_rotor, c_stator] list to bypass the estimate."""

    blade_AR = Input(3.0)
    """Blade aspect ratio (span / chord). Used when blade_axial_chords is None
    to estimate axial chords from design_radius. Typical: 2-4 compressor, 2-3 turbine."""

    inlet_rotor_max_AR = Input(10)
    """Max span/chord aspect ratio for the FIRST-stage rotor's CAD blade.
    Deprecated: use max_aspect_ratio_cap instead."""

    enable_cad_chord_capping = Input(False)
    """If True, scales up the CAD chords of rows that are too slender or too thin
    so that the LoftedSolid is robust and does not degenerate at the tip."""

    @Input
    def max_aspect_ratio_cap(self):
        """Max span/chord aspect ratio for any CAD blade row. By default,
        falls back to `inlet_rotor_max_AR` to preserve compatibility.
        """
        return self.inlet_rotor_max_AR

    min_blade_chord_m = Input(0.020)
    """Minimum mean chord [m] allowed for a CAD blade row. If a row's parsed mean
    chord falls below this, its chords are scaled up to prevent degeneration.
    Default 20 mm ensures at least ~3 mm physical tip thickness, well above
    the FittedCurve tolerance. Set to 0.0 or negative to disable."""

    mid_chord_fraction = Input(0.40)
    """Ratio of axial chord to true chord (cos of stagger angle approximation).
    Typical: 0.35-0.50. Used to convert span/AR -> axial chord."""

    row_gap   = Input(0.25)   # blade-row gap as fraction of axial chord
    stage_gap = Input(0.50)   # inter-stage gap as fraction of axial chord

    frac_twist = Input(1.0)
    """Blade twist option for MEANGEN FRAC_TWIST.
    1.0 = full free-vortex (aero-optimal, twisted blades).
    0.0 = prismatic blade (manufacturing-friendly, no twist).
    Values between 0 and 1 give a controlled-vortex design."""

    rotor_t_over_c  = Input(0.1)
    """Rotor max thickness-to-chord ratio t/c. Typical: 0.04-0.08."""

    stator_t_over_c = Input(0.1)
    """Stator max thickness-to-chord ratio t/c. Typical: 0.04-0.08."""

    rotor_x_tmax  = Input(0.40)
    """Rotor: axial location of max thickness as fraction of axial chord.
    Forward loading (0.35-0.45) matches turbine/compressor rotor aerodynamics."""

    stator_x_tmax = Input(0.50)
    """Stator: axial location of max thickness as fraction of axial chord.
    Mid-chord (0.45-0.55) suits symmetric diffusing stator geometry."""

    gas_constant = Input(287.15)
    """Specific gas constant R [J/(kg.K)].
    Used as fallback if FlowStation does not expose gas_constant directly."""

    # ------------------------------------------------------------------
    # Inputs — geometry / meshing resolution
    # ------------------------------------------------------------------

    n_pts     = Input(60)      # blade profile resampling resolution

    axial_offset = Input(0.0)
    """X position [m] of this machine's first stage LE along the engine axis.
    Set by the parent Spool to place the whole machine on the shaft. Added on
    top of the per-stage cumulative stacking and fed to Stage.stage_axial_offset
    (which drives Blade.axial_offset, since blades are built from absolute
    coordinates and a position frame would not move them)."""

    # ------------------------------------------------------------------
    # Inputs — solver configuration (forwarded to MultallSolver)
    # ------------------------------------------------------------------

    work_dir = Input(str(PROJECT_ROOT / 'design' / 'DesignExample'))
    """Working directory for THIS machine's Multall files. Compressor and
    turbine must use different folders (e.g. .../multall/compressor)."""

    meangen_exe      = Input(str(SOFTWARES / 'executables' / 'meangen-17.4.exe'))
    stagen_exe       = Input(str(SOFTWARES / 'executables' / 'stagen-18.1.exe'))
    multall_exe      = Input(str(SOFTWARES / 'executables' / 'multall-open-20.9.exe'))

    postprocess_results = Input(True)
    """If True, run PostPy after `multall_analysis` to generate the
    ParaView_TecPlotInterpreter_{blades,passages}.dat files. Forwarded to MultallSolver."""

    postpy_max_instances = Input(3)
    """Max number of extra passage/blade instances PostPy generates per row.
    Forwarded to MultallSolver."""

    log_low_fidelity = Input(False)
    log_high_fidelity = Input(False)

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
    def blade_axial_chords_estimated(self):
        """Estimate axial chords from design_radius and blade_AR.

        Geometry chain:
          annulus_height ≈ design_radius * 0.30  (hub-to-tip ~ 70% of r_m, rough)
          chord          = annulus_height / blade_AR
          c_ax           = chord * mid_chord_fraction

        This is a bootstrap estimate — after a first MEANGEN run the real chords
        come from stagen.dat via MeangenParser and override this in Stage.
        The 0.30 factor gives a hub/tip ratio of ~0.70 which is typical for the
        first stage of an HPC. Override blade_axial_chords explicitly if needed.
        """
        h_estimate = self.design_radius * 0.30
        c_ax = (h_estimate / self.blade_AR) * self.mid_chord_fraction
        return [round(c_ax, 4), round(c_ax * 1.10, 4)]   # stator ~10% longer than rotor

    @Attribute
    def effective_axial_chords(self):
        """Active axial chord values passed to MEANGEN.

        Returns blade_axial_chords if the user set it explicitly (not None),
        otherwise falls back to the aspect-ratio-based estimate.
        """
        return self.blade_axial_chords if self.blade_axial_chords is not None \
            else self.blade_axial_chords_estimated

    @Attribute
    def axial_gap(self):
        """Metric gap between the two rows in a Stage [m]."""
        return self.row_gap * self.effective_axial_chords[-1]

    @Attribute
    def deviation_angles(self):
        """Estimated row deviation angles [deg] — simplified Ainley-Mathieson.

        Returns [dev_row1, dev_row2].
        Compressor: row1=rotor, row2=stator.
        Turbine:    row1=stator, row2=rotor.

        Compressor:  delta ≈ 1.0 + 0.5 * psi  (light loading -> small deviation)
        Turbine:     delta ≈ 2.0 + max(0, psi - 1.5)  (high loading -> more underturning)
        Both rows assumed equal at meanline design; acceptable for preliminary design.
        """
        return {
            'compressor': [round(1.0 + 0.5 * self.loading_coeff, 2),
                           round(1.0 + 0.5 * self.loading_coeff, 2)],
            'turbine':    [round(2.0 + max(0.0, self.loading_coeff - 1.5), 2),
                           round(2.0 + max(0.0, self.loading_coeff - 1.5), 2)],
        }[self.machine_type]

    @Attribute
    def incidence_angles(self):
        """Estimated row incidence angles [deg] — design-point near-zero.

        Negative = suction-side incidence (MEANGEN sign convention).
        -1.0 deg is a small suction-side bias that reduces leading-edge
        separation at design point; consistent with Multall tutorial guidance.
        """
        return [-1.0, -1.0]


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
            axial_chords  = self.effective_axial_chords,
            row_gap       = self.row_gap,
            stage_gap     = self.stage_gap,
            eta_guess     = self.isos_efficiency,
            frac_twist    = self.frac_twist,
            deviation     = self.deviation_angles,
            incidence     = self.incidence_angles,
            rotor_t_over_c  = self.rotor_t_over_c,
            stator_t_over_c = self.stator_t_over_c,
            rotor_x_tmax    = self.rotor_x_tmax,
            stator_x_tmax   = self.stator_x_tmax,
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
            postprocess_results=self.postprocess_results,
            postpy_max_instances=self.postpy_max_instances,
            log_low_fidelity=self.log_low_fidelity,
            log_high_fidelity=self.log_high_fidelity,
        )

    @Attribute
    def postpy_output_paths(self):
        """Paths to PostPy's ParaView .dat files for this machine, or None
        if `multall_analysis` has not produced them yet. Pure pass-through
        to MultallSolver.postpy_output_paths."""
        return self.solver.postpy_output_paths

    # ------------------------------------------------------------------
    # 3) PARSING — turn the low-fidelity output into per-stage geometry data
    # ------------------------------------------------------------------

    @Attribute
    def stage_data(self):
        """List of per-stage dicts used to build the Stage parts."""
        out_path = self.solver.stagen_out_path
        dat_path = self.solver.stagen_dat_path
        return self._build_stage_data_from(out_path, dat_path)

    def _build_stage_data(self):
        """Parse the low-fidelity output into per-stage geometry data.

        Plain method (imperative logic allowed). MeangenParser reads stagen.dat
        (authoritative source for row type, blade count, metric chords and
        stagger); StageParser reads suction/pressure profiles from stagen.out;
        merge() fuses them.

        Accessing solver.stagen_out_path is what triggers meangen + stagen,
        so both stagen.dat and stagen.out exist before they are parsed.
        """
        out_path = self.solver.stagen_out_path
        dat_path = self.solver.stagen_dat_path
        return self._build_stage_data_from(out_path, dat_path)

    def _build_stage_data_from(self, out_path, dat_path):
        """Logica di parsing. Riceve i path già risolti da stage_data.
        Non referenzia self.solver qui dentro — il caching è garantito
        dall'@Attribute stage_data che ha già registrato le dipendenze.
        """
        meagen_rows = MeangenParser.parse(dat_path)
        row_order = [r['row_type'] for r in meagen_rows]
        _, n_sections = MeangenParser.parse_structure(dat_path)
        stages = StageParser.parse(out_path, row_order=row_order,
                                   n_sections=n_sections,
                                   machine_type=self.machine_type)
        merged = MeangenParser.merge(stages, meagen_rows)
        validate_stage_data(merged)
        self._cap_blade_rows_aspect_ratio(merged)
        for i, st in enumerate(merged):
            rc = sum(st['rotor']['chords']) / len(st['rotor']['chords'])
            sc = sum(st['stator']['chords']) / len(st['stator']['chords'])
            if self.log_low_fidelity:
                print(f"[stage_data] stage {i}: rotor chord={rc:.4f}m, "
                      f"stator chord={sc:.4f}m, "
                      f"stator_LE_offset={rc + self.axial_gap:.4f}m")
        return merged

    def _cap_blade_rows_aspect_ratio(self, merged):
        """Thicken any blade row that is too slender or too thin to loft.

        If enable_cad_chord_capping is True, we iterate through all stages and
        rows (rotor and stator) and scale up the chords if:
          1. The aspect ratio (span/chord) exceeds max_aspect_ratio_cap.
          2. The mean chord is less than min_blade_chord_m.
        This modifies the displayed CAD blade chords only; CFD calculations are
        unaffected because the solver has already run.
        """
        if not self.enable_cad_chord_capping or not merged:
            return

        for stage_idx, stage in enumerate(merged):
            for row_name in ['rotor', 'stator']:
                row = stage[row_name]
                r = row['r_sections']
                if not r or len(r) < 2:
                    continue
                span = r[-1] - r[0]
                mean_chord = sum(row['chords']) / len(row['chords'])
                if span <= 0.0 or mean_chord <= 0.0:
                    continue

                ar = span / mean_chord
                
                # Check aspect ratio cap
                factor_ar = 1.0
                if ar > self.max_aspect_ratio_cap:
                    factor_ar = ar / self.max_aspect_ratio_cap
                
                # Check minimum chord cap
                factor_chord = 1.0
                if self.min_blade_chord_m > 0.0 and mean_chord < self.min_blade_chord_m:
                    factor_chord = self.min_blade_chord_m / mean_chord

                factor = max(factor_ar, factor_chord)
                if factor > 1.0:
                    row['chords'] = [c * factor for c in row['chords']]
                    if self.log_low_fidelity:
                        print(f"[stage_data] Stage {stage_idx} {row_name} scaled by {factor:.2f}x "
                              f"(AR={ar:.2f} limit={self.max_aspect_ratio_cap:.2f}, "
                              f"mean_chord={mean_chord:.4f} m min={self.min_blade_chord_m:.4f} m, CAD only)")

    def _cap_inlet_rotor_aspect_ratio(self, merged):
        """Deprecated: use _cap_blade_rows_aspect_ratio instead."""
        self._cap_blade_rows_aspect_ratio(merged)

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
            stage_axial_offset    = self.axial_offset + self.stage_axial_starts[child.index],
            rotor_color           = self.material.color,
            stator_color          = self.stator_material.color,
            show_blades           = self.show_blades,
            show_geometry         = self.show_geometry,
        )

    # ------------------------------------------------------------------
    # HIGH-fidelity analysis (orchestration + geometry feedback)
    # ------------------------------------------------------------------

    @action(label='Run Multall CFD analysis')
    def multall_analysis(self):
        """GUI button: run the 3D Multall CFD and refresh the model."""
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
        """Total blade mass [kg] = (rotor_density * rotor_volume) + (stator_density * stator_volume).

        Uses stage-level aggregated volume attributes to avoid querying
        individual transformed shapes.
        """
        rotor_vol = sum(stage.rotor_blade_volume for stage in self.body)
        stator_vol = sum(stage.stator_blade_volume for stage in self.body)
        return (self.material.density * rotor_vol) + (self.stator_material.density * stator_vol)

    @Attribute
    def detailed_features(self):
        """Container for high-fidelity results (filled by multall_analysis).
        Matches the UML 'detailed_features: dict[str, float]'."""
        return {}

    def validate(self):
        warnings = super().validate()
        if self.U <= 0.0:
            warnings.append(f"{self.label}: blade speed U={self.U:.2f} must be > 0.")
        if not (0.0 <= self.reaction <= 1.0):
            warnings.append(
                f"{self.label}: reaction={self.reaction:.3f} outside [0, 1].")
        if self.stages_required != self.n_stages:
            warnings.append(
                f"{self.label}: n_stages={self.n_stages} but delta_H/delta_H_stage "
                f"implies {self.stages_required} stage(s) — check the work split.")
        if self.n_stages > 4:
            warnings.append(
                f"{self.label}: n_stages={self.n_stages} exceeds the MULTALL solver "
                f"maximum limit of 4 stages (8 rows) due to fixed array dimensions "
                f"in the Fortran executable.")
        return warnings


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    from parapy.gui import display
    from Thermodynamics.FlowStation import FlowStation

    inlet = FlowStation(
        station_number=2,
        fluid_type='air',
        p_total=400000.0,  # 4 bar
        T_total=1400.0,  # 1400 K (post-combustore)
        mass_flow=20.0,
        Mach=0.3,
    )

    work = PROJECT_ROOT / 'design' / 'DesignExample' / 'test_run_t'

    turbine = Turbomachine(
        machine_type='turbine',
        inflow_conditions=inlet,
        design_radius=0.30,
        work_dir=str(work),
        label='HPT_smoke',
    )

    print(f"machine        = {turbine.machine_type} ({turbine.turbo_typ_code})")
    print(f"n_stages       = {turbine.n_stages}")
    print(f"U              = {turbine.U:.1f} m/s")
    print(f"flow_coeff     = {turbine.flow_coeff:.4f}  (target 0.50)")
    print(f"loading_coeff  = {turbine.loading_coeff:.4f}  (target 2.00)")
    print(f"reaction       = {turbine.reaction:.3f}")
    print(f"deviation      = {turbine.deviation_angles}")
    print(f"axial_chords   = {turbine.effective_axial_chords}")

    display(turbine, view='top', autodraw=True)