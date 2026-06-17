"""
Compressor.py
=============
Axial compressor — concrete subclass of Turbomachine.

Adds only what distinguishes a compressor from the generic turbomachine:
  - pins machine_type = 'compressor'  (drives the MEANGEN 'C' flag and the
    rotor-first / stator-second row order in Stage);
  - exposes the UML-mandated knobs: stage_pressure_ratio, polytropic_efficiency;

All meanline coefficients (flow, loading, reaction) and the geometry / Multall
pipeline are inherited unchanged from Turbomachine.

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

import math
from pathlib import Path

from parapy.core import Input, Attribute

from EngineCore.Turbomachinery.Turbomachine import Turbomachine

PROJECT_ROOT = Path(__file__).resolve().parents[3]



class Compressor(Turbomachine):
    """Axial compressor driven by the inherited Multall pipeline."""

    # ------------------------------------------------------------------
    # Machine-type pin
    # ------------------------------------------------------------------

    machine_type = Input('compressor')
    """Override the base default: a Compressor is always a 'C' machine."""

    # ------------------------------------------------------------------
    # Working directory
    # ------------------------------------------------------------------

    working_directory = Input('design/test_run')
    """Root directory for this compressor's CFD run. All Meangen/Stagen/Multall
    files are rooted in a 'compressor' subdirectory below this path (see
    work_dir), so a compressor and a turbine that share the same
    working_directory never collide on disk."""

    @Input
    def work_dir(self):
        """Per-machine Multall working directory: <working_directory>/compressor.

        Overrides the Turbomachine.work_dir default. The 'compressor'
        subdirectory is created here (idempotent) so it exists before
        MultallSolver writes any file into it. Pass work_dir explicitly to
        bypass working_directory entirely.
        """
        base_path = Path(self.working_directory)
        if not base_path.is_absolute():
            base_path = PROJECT_ROOT / base_path
        path = base_path / 'compressor'
        path.mkdir(parents=True, exist_ok=True)
        return str(path.resolve())


    # ------------------------------------------------------------------
    # Compressor-specific design knobs (UML: Compressor)
    # ------------------------------------------------------------------

    @Input
    def stage_pressure_ratio(self):
        """Per-stage total-pressure ratio [-].

        Adaptive default: equal logarithmic split of the overall machine
        pressure_ratio (EngineComponent input) across n_stages, i.e. the
        geometric n-th root. Overridable to bias loading between stages.
        """
        return self.pressure_ratio ** (1.0 / self.n_stages)

    @Input
    def polytropic_efficiency(self):
        """Small-stage (polytropic) efficiency e_poly [-].

        Derived from the overall isentropic pressure ratio and the realised
        total-temperature rise (driven by isos_efficiency in EngineComponent):

            e_poly = [(gamma-1)/gamma * ln(PR)] / ln(T0_out / T0_in)

        This is the exact polytropic-from-isentropic relation for compression;
        it stays > isos_efficiency as expected. Overridable for off-design work.
        """
        return ((self.station_in.gamma - 1.0) / self.station_in.gamma) \
            * math.log(self.pressure_ratio) \
            / math.log(self.station_out_part.T_total / self.station_in.T_total)

    # ------------------------------------------------------------------
    # Validation (extends Turbomachine.validate)
    # ------------------------------------------------------------------

    def validate(self):
        warnings = super().validate()
        if self.pressure_ratio <= 1.0:
            warnings.append(
                f"Compressor '{self.label}': pressure_ratio="
                f"{self.pressure_ratio:.3f} must be > 1 for compression."
            )
        if self.stage_pressure_ratio <= 1.0:
            warnings.append(
                f"Compressor '{self.label}': stage_pressure_ratio="
                f"{self.stage_pressure_ratio:.3f} must be > 1."
            )
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
        p_total=101325.0,
        T_total=288.15,
        mass_flow=20.0,
        Mach=0.5,
    )

    hpc = Compressor(
        inflow_conditions=inlet,
        pressure_ratio=4,
        frac_twist=0.5,
        isos_efficiency=0.88,
        n_stages=5,
        rpm=12000.0,
        design_radius=0.30,
        label='HPC',
    )

    print(f"machine_type         = {hpc.machine_type} ({hpc.turbo_typ_code})")
    print(f"U               [m/s] = {hpc.U:.2f}")
    print(f"V_ax            [m/s] = {hpc.V_ax:.2f}")
    print(f"delta_H        [J/kg] = {hpc.delta_H:.1f}")
    print(f"delta_H_stage  [J/kg] = {hpc.delta_H_stage:.1f}")
    print(f"flow_coeff        [-] = {hpc.flow_coeff:.4f}")
    print(f"loading_coeff     [-] = {hpc.loading_coeff:.4f}")
    print(f"reaction          [-] = {hpc.reaction:.4f}")
    print(f"stage_PR          [-] = {hpc.stage_pressure_ratio:.4f}")
    print(f"e_poly            [-] = {hpc.polytropic_efficiency:.4f}")
    print(f"stages_required       = {hpc.stages_required} (set n_stages = {hpc.n_stages})")

    for w in hpc.validate():
        print("  WARN:", w)

    display(hpc, view='top', autodraw=True)