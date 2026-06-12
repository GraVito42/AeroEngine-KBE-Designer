"""
Turbine.py
==========
Axial turbine — concrete subclass of Turbomachine.

Adds only what distinguishes a turbine from the generic turbomachine:
  - pins machine_type = 'turbine'  (drives the MEANGEN 'T' flag and the
    stator-first / rotor-second row order in Stage);
  - exposes the UML-mandated knobs: inlet_temperature, loading_factor,
    degree_of_reaction.

Sign / coefficient note:
  Work is EXTRACTED, so the total-temperature drops across the machine and
  delta_H (computed in Turbomachine from |cp * dT0|) is a positive magnitude.
  The loading coefficient psi = |delta_H_stage| / U^2 is therefore already
  positive and is reused as-is.

Coordinate system (engine frame): X axial, Y radial, Z tangential.
"""

from parapy.core import Input, Attribute
from pathlib import Path

from Turbomachine import Turbomachine

PROJECT_ROOT = Path(__file__).resolve().parent



class Turbine(Turbomachine):
    """Axial turbine driven by the inherited Multall pipeline."""

    # ------------------------------------------------------------------
    # Machine-type pin
    # ------------------------------------------------------------------

    machine_type = Input('turbine')
    """Override the base default: a Turbine is always a 'T' machine."""

    # ------------------------------------------------------------------
    # Working directory
    # ------------------------------------------------------------------

    working_directory = Input('Multall/DesignExample/test_run')
    """Root directory for this turbine's CFD run. All Meangen/Stagen/Multall
    files are rooted in a 'turbine' subdirectory below this path (see work_dir),
    so a turbine and a compressor that share the same working_directory never
    collide on disk."""

    @Input
    def work_dir(self):
        """Per-machine Multall working directory: <working_directory>/turbine.

        Overrides the Turbomachine.work_dir default. The 'turbine' subdirectory
        is created here (idempotent) so it exists before MultallSolver writes
        any file into it. Pass work_dir explicitly to bypass working_directory
        entirely.
        """
        base_path = Path(self.working_directory)
        if not base_path.is_absolute():
            base_path = PROJECT_ROOT / base_path
        path = base_path / 'turbine'
        path.mkdir(parents=True, exist_ok=True)
        return str(path.resolve())


    # ------------------------------------------------------------------
    # Turbine-specific design knobs (UML: Turbine)
    # ------------------------------------------------------------------

    @Input
    def inlet_temperature(self):
        """Turbine inlet total temperature TIT [K].

        Adaptive default: the inlet FlowStation total temperature. Exposed as a
        named slot because TIT is the primary turbine sizing/life driver and is
        often pinned directly from the cycle (combustor exit) rather than left
        to propagate. Feeds nothing extra in the base meangen_input (which
        already uses inflow_conditions.T_total as TOIN); kept for the UML
        contract and downstream stress/cooling rules.
        """
        return self.inflow_conditions.T_total

    # ------------------------------------------------------------------
    # Validation (extends Turbomachine.validate)
    # ------------------------------------------------------------------

    def validate(self):
        warnings = super().validate()
        # For a turbine the machine pressure_ratio is an EXPANSION ratio:
        # EngineComponent stores P_out / P_in, which is < 1 for a turbine.
        if self.pressure_ratio >= 1.0:
            warnings.append(
                f"Turbine '{self.label}': pressure_ratio="
                f"{self.pressure_ratio:.3f} should be < 1 for expansion "
                f"(P_out / P_in)."
            )
        # Typical aero-engine turbine reaction is around 0.5; flag extremes.
        if not (0.0 <= self.reaction <= 0.6):
            warnings.append(
                f"Turbine '{self.label}': reaction={self.reaction:.3f} is "
                f"outside the typical 0.0-0.6 band — verify with the Architect."
            )
        return warnings


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    from parapy.gui import display
    from Flow_station import FlowStation

    # Turbine inlet = combustor exit: hot, high pressure.
    inlet = FlowStation(
        station_number=4,
        fluid_type='fuel_gas',
        p_total=1_500_000.0,
        T_total=1600.0,
        mass_flow=22.9,
        Mach=0.4,
    )

    hpt = Turbine(
        inflow_conditions=inlet,
        pressure_ratio=0.25,     # expansion: P_out / P_in < 1
        isos_efficiency=0.90,
        n_stages=2,
        rpm=12000.0,
        design_radius=0.35,
        reaction=0.50,
        label='HPT',
    )

    print(f"machine_type         = {hpt.machine_type} ({hpt.turbo_typ_code})")
    print(f"inlet_temperature [K] = {hpt.inlet_temperature:.1f}")
    print(f"U               [m/s] = {hpt.U:.2f}")
    print(f"V_ax            [m/s] = {hpt.V_ax:.2f}")
    print(f"delta_H        [J/kg] = {hpt.delta_H:.1f}")
    print(f"delta_H_stage  [J/kg] = {hpt.delta_H_stage:.1f}")
    print(f"flow_coeff        [-] = {hpt.flow_coeff:.4f}")
    print(f"loading_factor    [-] = {hpt.loading_coeff:.4f}")
    print(f"degree_of_reaction[-] = {hpt.reaction:.4f}")
    print(f"stages_required       = {hpt.stages_required} (set n_stages = {hpt.n_stages})")

    # Optional: derive reaction from a known stator-exit (rotor-inlet) swirl.
    # alpha1 = 65 deg is a typical HPT value.
    print(f"reaction(alpha1=65)   = {hpt.reaction_from_inlet_swirl(65.0):.4f}  "
          f"(compressor-convention formula — confirm sign for turbine)")

    for w in hpt.validate():
        print("  WARN:", w)

    display(hpt, view='top', autodraw=True)