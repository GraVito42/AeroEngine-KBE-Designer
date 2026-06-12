"""
Compressor.py
=============
Axial compressor — concrete subclass of Turbomachine.

Adds only what distinguishes a compressor from the generic turbomachine:
  - pins machine_type = 'compressor'  (drives the MEANGEN 'C' flag and the
    rotor-first / stator-second row order in Stage);
  - exposes the UML-mandated knobs: stage_pressure_ratio, polytropic_efficiency;
  - provides surge_margin().

All meanline coefficients (flow, loading, reaction) and the geometry / Multall
pipeline are inherited unchanged from Turbomachine.

Coordinate system (engine frame): X axial, Y radial, Z tangential.
"""

import math
from pathlib import Path

from parapy.core import Input, Attribute, action

from Turbomachine import Turbomachine

PROJECT_ROOT = Path(__file__).resolve().parent



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

    working_directory = Input('Multall/DesignExample/test_run')
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

    #: [-] Lieblein diffusion-factor loading limit used as the surge/stall
    #  reference. ~0.45 is the conservative design ceiling; ~0.6 is the hard
    #  cascade-stall value (Lieblein 1953). Overridable per design practice.
    diffusion_factor_limit = Input(0.45)

    #: [-] Mean blade-row solidity (chord / pitch) of the design rotor. Typical
    #  axial-compressor range 1.0-1.5. This is the geometric lever the surge
    #  action adapts. # TODO: once a STAGEN run exists, default this from the
    #  parsed blade count and chords instead of a fixed guess.
    design_solidity = Input(1.2)

    #: [-] Target fractional surge margin (0 = exactly at the DF limit), the
    #  surge analogue of EngineFrame.containment_margin_target.
    surge_margin_target = Input(0.0)

    # ------------------------------------------------------------------
    # Surge / stall-loading model  (mean-line Lieblein diffusion factor)
    # ------------------------------------------------------------------

    @Attribute
    def rotor_relative_angles(self):
        """Rotor relative flow angles (beta1, beta2) [rad].

        Compressor normal-stage relations at constant axial velocity:
            tan(beta1) = (2*reaction + psi) / (2*phi)
            tan(beta2) = (2*reaction - psi) / (2*phi)
        with phi = flow_coeff, psi = loading_coeff, reaction = degree of reaction.

        # TODO: COMPRESSOR convention (repeating stage, constant Vx). Confirm the
        #       reaction/station convention with the Architect before relying on
        #       this for off-50%-reaction designs.
        """
        b1 = math.atan((2.0 * self.reaction + self.loading_coeff) / (2.0 * self.flow_coeff))
        b2 = math.atan((2.0 * self.reaction - self.loading_coeff) / (2.0 * self.flow_coeff))
        return (b1, b2)

    @Attribute
    def de_haller(self):
        """de Haller number W2/W1 across the rotor [-]. Stall guideline: >= 0.72.
        W = Vx / cos(beta), so W2/W1 = cos(beta1)/cos(beta2)."""
        b1, b2 = self.rotor_relative_angles
        return math.cos(b1) / math.cos(b2)

    @Attribute
    def diffusion_factor(self):
        """Lieblein diffusion factor of the design rotor [-].

            DF = 1 - W2/W1 + dWtheta / (2 * sigma * W1)
               = 1 - de_haller + psi * cos(beta1) / (2 * sigma * phi)

        using dWtheta = psi*U and W1 = phi*U/cos(beta1). sigma = design_solidity.
        """
        b1, _ = self.rotor_relative_angles
        return (1.0 - self.de_haller
                + self.loading_coeff * math.cos(b1)
                / (2.0 * self.design_solidity * self.flow_coeff))

    @Attribute
    def surge_margin(self):
        """Fractional surge (stall-loading) margin [-].
          > 0  -> loaded below the diffusion limit (margin in hand)
          <= 0 -> at/above the limit (stall/surge risk)

        SM = (DF_limit - DF) / DF_limit, the loading analogue of
        EngineFrame.containment_margin.
        """
        return (self.diffusion_factor_limit - self.diffusion_factor) / self.diffusion_factor_limit

    @Attribute
    def stages_required_for_surge(self):
        """Smallest n_stages whose mean-line diffusion factor meets
        surge_margin_target [-].

        Adding stages lowers the per-stage enthalpy rise delta_H_stage, hence
        the loading coefficient psi = |delta_H_stage| / U^2, which lowers the
        diffusion factor and raises the surge margin. The relation DF(psi) is
        transcendental (psi enters through the relative flow angles too), so it
        is swept over integer n rather than inverted in closed form. n is the
        right lever because it is what propagates: it feeds delta_H_stage ->
        loading_coeff -> meangen_input -> geometry.

        References the drivers directly (delta_H, U, flow_coeff, reaction,
        design_solidity, limits) so ParaPy re-evaluates it whenever they change.
        """
        delta_H = abs(self.delta_H)
        u_sq    = self.U ** 2
        phi     = self.flow_coeff
        lam     = self.reaction
        sigma   = self.design_solidity
        df_lim  = self.diffusion_factor_limit
        target  = self.surge_margin_target
        for n in range(1, 101):
            psi = delta_H / (n * u_sq)
            b1  = math.atan((2.0 * lam + psi) / (2.0 * phi))
            b2  = math.atan((2.0 * lam - psi) / (2.0 * phi))
            de_haller = math.cos(b1) / math.cos(b2)
            df = 1.0 - de_haller + psi * math.cos(b1) / (2.0 * sigma * phi)
            if (df_lim - df) / df_lim >= target:
                return n
        return 100   # cap: target unreachable within a sane stage count

    @action
    def adapt_n_stages_for_surge_margin(self):
        """GUI action: raise n_stages until surge_margin meets surge_margin_target.

        Surge analogue of EngineFrame.update_sheet_thickness_for_containment:
        set the target in the property panel, then click. Unlike the containment
        case (continuous sheet thickness, exact hit), the lever here is the
        integer stage count, so the realised surge_margin meets-or-slightly-
        exceeds the target.

        Crucially, n_stages is the lever that PROPAGATES: assigning it
        invalidates delta_H_stage -> loading_coeff -> meangen_input (and the
        quantified Stage parts), so the blade geometry regenerates. The earlier
        solidity lever did not, because design_solidity feeds only the surge
        model and never enters meangen_input.
        """
        self.n_stages = self.stages_required_for_surge
        return self.n_stages

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
    from Flow_station import FlowStation

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
        frac_twist=0.0,
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
    print(f"de_haller         [-] = {hpc.de_haller:.4f}  (stall guideline >= 0.72)")
    print(f"diffusion_factor  [-] = {hpc.diffusion_factor:.4f}  (limit {hpc.diffusion_factor_limit})")
    print(f"surge_margin      [-] = {hpc.surge_margin:.4f}")
    print(f"stages_for_surge      = {hpc.stages_required_for_surge}  "
          f"(for target {hpc.surge_margin_target})")
    print(f"stages_required       = {hpc.stages_required} (set n_stages = {hpc.n_stages})")

    for w in hpc.validate():
        print("  WARN:", w)

    display(hpc, view='top', autodraw=True)