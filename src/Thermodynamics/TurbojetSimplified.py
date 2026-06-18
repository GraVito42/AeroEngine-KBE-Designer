# ===== FILE: Turbojet_simplified_model.py =====
# Ensure project root is in sys.path when running this file directly
import sys
from pathlib import Path
for parent in Path(__file__).resolve().parents:
    if (parent / "EngineCore").exists() and (parent / "Thermodynamics").exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break

import math
from parapy.core import Base, Input, Attribute, Part
from Thermodynamics import FlowCondition, FlowStation

"""
Simplified single-spool turbojet cycle (ParaPy / KBE) - INVERSE sizing.

Native architecture: target_thrust is an @Input; the required air mass flow is
a derived @Attribute (mass_flow = target_thrust / specific_net_thrust). The
specific net thrust is intensive (mass-flow independent), so this closure is
exact and the dependency graph is strictly acyclic.

Forward evaluation is available as a plain Python method evaluate_forward(mdot),
running the SAME equation set in the forward direction (supplied mass flow ->
thrust). It reads only intensive @Attributes and never the resolved mass_flow,
so it is free of any dependency-graph coupling and safe for trade studies.

Station numbering (SAE ARP755): 0 ambient, 2 compressor inlet, 3 compressor exit,
4 turbine inlet (TIT), 5 turbine exit, 8 nozzle exit. Stations are @Part children
(FlowCondition where Mach/area are irrelevant, FlowStation at 0 and 8).
"""


class TurbojetSimplified(Base):
    """Inverse 1D turbojet sizing model (thrust target -> mass flow)."""

    target_thrust = Input(35000.0)     # Required net thrust               [N]

    # ---- Flight / ambient (station 0) ---------------------------------- #
    M0 = Input(0.78)             # Flight Mach number                [-]
    T0 = Input(216.5)            # Ambient static temperature        [K]
    p0 = Input(22632.0)          # Ambient static pressure           [Pa]

    # ---- Gas / fuel properties (mirror FlowCondition) ------------------ #
    gamma_a = Input(1.40)        # Air specific-heat ratio           [-]
    gamma_g = Input(1.33)        # Gas specific-heat ratio           [-]
    cpa     = Input(1000.0)      # cp air                            [J/kg/K]
    cpg     = Input(1150.0)      # cp combustion gas                 [J/kg/K]
    r_gas   = Input(287.05)      # Specific gas constant (air)       [J/kg/K]
    LHV     = Input(43.0e6)      # Fuel lower heating value          [J/kg]

    # ---- Component design parameters ----------------------------------- #
    inlet_pr   = Input(0.99)     # Inlet total-pressure recovery     [-]
    comp_pr    = Input(10.0)     # Compressor pressure ratio         [-]
    comp_eff   = Input(0.90)     # Compressor isentropic efficiency  [-]
    Tt4        = Input(1600.0)   # Turbine inlet temperature (TIT)   [K]
    comb_eff   = Input(0.995)    # Combustion efficiency             [-]
    comb_pr    = Input(0.96)     # Combustor total-pressure ratio    [-]
    turb_eff   = Input(0.91)     # Turbine isentropic efficiency     [-]
    mech_eff   = Input(0.995)    # Shaft mechanical efficiency       [-]
    nozzle_eff = Input(0.99)     # Nozzle isentropic efficiency      [-]

    # ====================== INTENSIVE: total conditions ================= #
    @Attribute
    def v0(self):
        """Flight velocity [m/s] (intensive; computed directly to keep the graph acyclic)."""
        return self.M0 * math.sqrt(self.gamma_a * self.r_gas * self.T0)

    @Attribute
    def Tt0(self):
        return self.T0 * (1.0 + 0.5 * (self.gamma_a - 1.0) * self.M0 ** 2)

    @Attribute
    def pt0(self):
        return self.p0 * (1.0 + 0.5 * (self.gamma_a - 1.0) * self.M0 ** 2) ** (
            self.gamma_a / (self.gamma_a - 1.0))

    @Attribute
    def Tt2(self):
        return self.Tt0

    @Attribute
    def pt2(self):
        return self.pt0 * self.inlet_pr

    @Attribute
    def pt3(self):
        return self.comp_pr * self.pt2

    @Attribute
    def Tt3(self):
        return (1.0 + (1.0 / self.comp_eff) * (
            (self.pt3 / self.pt2) ** ((self.gamma_a - 1.0) / self.gamma_a) - 1.0)) * self.Tt2

    @Attribute
    def pt4(self):
        return self.pt3 * self.comb_pr

    @Attribute
    def f(self):
        """Fuel-to-air ratio: cpg*(Tt4-Tt3) / (eta_cc * LHV)."""
        return (self.cpg * (self.Tt4 - self.Tt3)) / (self.comb_eff * self.LHV)

    @Attribute
    def Tt5(self):
        # Power balance: turbine_work * mech_eff = compressor_work, per unit air mass.
        return self.Tt4 - (self.cpa * (self.Tt3 - self.Tt2)) / (
            self.mech_eff * (1.0 + self.f) * self.cpg)

    @Attribute
    def pt5(self):
        return (1.0 - (1.0 / self.turb_eff) * (1.0 - self.Tt5 / self.Tt4)) ** (
            self.gamma_g / (self.gamma_g - 1.0)) * self.pt4

    # ====================== INTENSIVE: nozzle =========================== #
    @Attribute
    def p_critical_ratio(self):
        return (1.0 - ((self.gamma_g - 1.0) / (self.gamma_g + 1.0)) / self.nozzle_eff) ** (
            -self.gamma_g / (self.gamma_g - 1.0))

    @Attribute
    def is_nozzle_choked(self):
        return (self.pt5 / self.p0) > self.p_critical_ratio

    @Attribute
    def T8(self):
        return (self.Tt5 * (2.0 / (self.gamma_g + 1.0))) if self.is_nozzle_choked else (
            self.Tt5 * (1.0 - self.nozzle_eff * (
                1.0 - (self.p0 / self.pt5) ** ((self.gamma_g - 1.0) / self.gamma_g))))

    @Attribute
    def p8(self):
        return (self.pt5 / self.p_critical_ratio) if self.is_nozzle_choked else self.p0

    @Attribute
    def v8(self):
        return math.sqrt(self.gamma_g * self.r_gas * self.T8) if self.is_nozzle_choked else (
            math.sqrt(2.0 * self.cpg * (self.Tt5 - self.T8)))

    @Attribute
    def rho8(self):
        return self.p8 / (self.r_gas * self.T8)

    @Attribute
    def M8(self):
        return 1.0 if self.is_nozzle_choked else self.v8 / math.sqrt(
            self.gamma_g * self.r_gas * self.T8)

    @Attribute
    def pt8(self):
        return self.p8 * (1.0 + 0.5 * (self.gamma_g - 1.0) * self.M8 ** 2) ** (
            self.gamma_g / (self.gamma_g - 1.0))

    # ====================== SPECIFIC LAYER (per 1 kg/s air) ============= #
    @Attribute
    def A8_specific(self):
        return (1.0 + self.f) / (self.rho8 * self.v8)

    @Attribute
    def specific_gross_thrust(self):
        return (1.0 + self.f) * self.v8 + self.A8_specific * (self.p8 - self.p0)

    @Attribute
    def specific_net_thrust(self):
        return self.specific_gross_thrust - self.v0

    # ====================== SIZING ROOT (inverse closure) =============== #
    @Attribute
    def mass_flow(self):
        """Intake air mass flow sized to target_thrust [kg/s] (intensive closure -> exact)."""
        return self.target_thrust / self.specific_net_thrust

    # ====================== FORWARD EVALUATION (plain method) =========== #
    def evaluate_forward(self, mass_flow):
        """Forward direction: given an air mass flow [kg/s], return net thrust [N].
        Runs the same extensive equation set as the inverse path but with mass_flow
        SUPPLIED, reading only intensive @Attributes -> no coupling to self.mass_flow,
        no dependency-graph conflict. Useful for verification and trade studies."""
        m_g = mass_flow * (1.0 + self.f)
        A8 = mass_flow * self.A8_specific
        gross_thrust = m_g * self.v8 + A8 * (self.p8 - self.p0)
        ram_drag = mass_flow * self.v0
        return gross_thrust - ram_drag

    # ====================== EXTENSIVE LAYER ============================= #
    @Attribute
    def m_f(self):
        """Fuel mass flow [kg/s] = heat_added * mass_flow / (eta_cc * LHV)."""
        return self.mass_flow * self.f

    @Attribute
    def m_g(self):
        return self.mass_flow * (1.0 + self.f)

    @Attribute
    def A8(self):
        return self.mass_flow * self.A8_specific

    @Attribute
    def gross_thrust(self):
        return self.m_g * self.v8 + self.A8 * (self.p8 - self.p0)

    @Attribute
    def ram_drag(self):
        return self.mass_flow * self.v0

    @Attribute
    def net_thrust(self):
        return self.gross_thrust - self.ram_drag

    # ====================== EXPOSED OUTPUTS ============================= #
    @Attribute
    def thrust(self):
        """Net thrust [N] (== target_thrust by construction)."""
        return self.net_thrust

    @Attribute
    def TSFC(self):
        """Thrust-specific fuel consumption [kg/(N*s)]."""
        return self.m_f / self.net_thrust

    @Attribute
    def v_eff(self):
        """Effective jet velocity [m/s] (SAE/lecture convention):
        v_eff = gross_thrust / m_g, so that F_N = m_g*v_eff - m_0*v0.
        For a perfectly-expanded nozzle v_eff == v8; when the nozzle is choked
        it folds the pressure-thrust term (p8-p0)*A8 back into an equivalent
        velocity, which is the velocity the thermal/propulsive efficiency
        definitions require for energy/momentum consistency with net_thrust."""
        return self.gross_thrust / self.m_g

    @Attribute
    def thermal_efficiency(self):
        """Thermal (cycle) efficiency [-]: jet kinetic-energy rise per unit fuel
        chemical power. Uses v_eff (not v8) so the choked-nozzle pressure thrust
        is accounted for consistently with net_thrust."""
        return (0.5 * (self.m_g * self.v_eff ** 2 - self.mass_flow * self.v0 ** 2)) / (
            self.m_f * self.LHV)

    @Attribute
    def propulsive_efficiency(self):
        """Froude efficiency [-]: thrust power / propulsion (kinetic-energy) power.
        Uses v_eff (not v8); with overall_efficiency this now satisfies
        eta_th * eta_prop = eta_ov exactly, including the choked case."""
        return (self.net_thrust * self.v0) / (
            0.5 * (self.m_g * self.v_eff ** 2 - self.mass_flow * self.v0 ** 2))

    @Attribute
    def overall_efficiency(self):
        return (self.net_thrust * self.v0) / (self.m_f * self.LHV)

    # ====================== STATION PARTS =============================== #
    @Part
    def station0(self):
        return FlowStation(fluid_type="air", station_number=0, p_total=self.pt0,
                           T_total=self.Tt0, mass_flow=self.mass_flow, Mach=self.M0)

    @Part
    def station2(self):
        return FlowCondition(fluid_type="air", p_total=self.pt2, T_total=self.Tt2)

    @Part
    def station3(self):
        return FlowCondition(fluid_type="air", p_total=self.pt3, T_total=self.Tt3)

    @Part
    def station4(self):
        return FlowCondition(fluid_type="fuel_gas", p_total=self.pt4, T_total=self.Tt4)

    @Part
    def station5(self):
        return FlowCondition(fluid_type="fuel_gas", p_total=self.pt5, T_total=self.Tt5)

    @Part
    def station8(self):
        return FlowStation(fluid_type="fuel_gas", station_number=8, p_total=self.pt8,
                           T_total=self.Tt5, mass_flow=self.m_g, Mach=self.M8)


if __name__ == '__main__':
    engine = TurbojetSimplified(target_thrust=35000.0)
    print(f"target thrust         : {engine.target_thrust / 1e3:.2f} kN")
    print(f"resolved mass_flow    : {engine.mass_flow:.3f} kg/s")
    print(f"net thrust (inverse)  : {engine.thrust / 1e3:.3f} kN")
    print(f"nozzle choked         : {engine.is_nozzle_choked}")
    print(f"v8 (exit static)      : {engine.v8:.2f} m/s")
    print(f"v_eff (effective jet) : {engine.v_eff:.2f} m/s")
    print(f"TSFC                  : {engine.TSFC * 1e6:.2f} mg/(N*s)")
    print(f"thermal efficiency    : {engine.thermal_efficiency:.4f}")
    print(f"propulsive efficiency : {engine.propulsive_efficiency:.4f}")
    print(f"overall efficiency    : {engine.overall_efficiency:.4f}")

    # Consistency check: thermal * propulsive must equal overall (now exact with v_eff).
    eta_product = engine.thermal_efficiency * engine.propulsive_efficiency
    residual = eta_product - engine.overall_efficiency
    print(f"\neta_th * eta_prop     : {eta_product:.6f} "
          f"(vs eta_ov {engine.overall_efficiency:.6f}, residual {residual:+.2e})")
    assert abs(residual) < 1e-6, "eta_th * eta_prop != eta_ov — efficiency definitions inconsistent"

    # Round-trip check: forward evaluation at the resolved mass flow -> target_thrust.
    fwd = engine.evaluate_forward(engine.mass_flow)
    print(f"forward check         : {fwd / 1e3:.3f} kN "
          f"(residual {fwd - engine.target_thrust:+.3e} N)")