# ===== FILE: Flow_station.py =====
# Ensure project root is in sys.path when running this file directly
import sys
from pathlib import Path
for parent in Path(__file__).resolve().parents:
    if (parent / "EngineCore").exists() and (parent / "Thermodynamics").exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break

import numpy as np
from parapy.core import Input, Attribute
from scipy.optimize import brentq
from Thermodynamics import FlowCondition

"""
FlowStation: extends FlowCondition with Mach-dependent quantities
(static state, velocities, area) and the mass-flow-aware isentropic
transformation. Same external interface as the legacy FlowStation:
all attribute/method names are preserved (t_static stays lowercase).
"""


class FlowStation(FlowCondition):
    """Flow state at an engine station (total + static + geometry)."""

    station_number:float = Input(0)        # Station id (0 = ambient)   [-]
    mass_flow:float      = Input(15.0)     # Mass flow rate             [kg/s]
    Mach:float           = Input(0.5)      # Mach number                [-]

    @Input
    def area(self):
        """Section area from the isentropic mass-flow relation [m^2] (overridable)."""
        return (self.mass_flow * np.sqrt(self.r_gas * self.T_total)) / (
            self.p_total * self.Mach * np.sqrt(self.gamma)
            * (1.0 + ((self.gamma - 1.0) / 2.0) * self.Mach ** 2)
            ** (-(self.gamma + 1.0) / (2.0 * (self.gamma - 1.0))))

    @Attribute
    def p_static(self):
        """Static pressure [Pa]."""
        return self.p_total / (
            1.0 + ((self.gamma - 1.0) / 2.0) * self.Mach ** 2) ** (
            self.gamma / (self.gamma - 1.0))

    @Attribute
    def t_static(self):
        """Static temperature [K] (legacy lowercase name kept for compatibility)."""
        return self.T_total / (1.0 + ((self.gamma - 1.0) / 2.0) * self.Mach ** 2)

    @Attribute
    def rho(self):
        """Density [kg/m^3]."""
        return self.p_static / (self.r_gas * self.t_static)

    @Attribute
    def c(self):
        """Speed of sound [m/s]."""
        return np.sqrt(self.gamma * self.r_gas * self.t_static)

    @Attribute
    def v(self):
        """Flow velocity [m/s]."""
        return self.Mach * self.c

    def isentropic_trans(self, target_type="temperature", target_value=1000000,
                         eta=0.99, Mach_out=0.7):
        """Isentropic transformation returning a NEW FlowStation.
        Delegates the pure thermodynamics to FlowCondition.isentropic_trans_th."""
        p_out, T_out = self.isentropic_trans_th(target_type, target_value, eta)
        return FlowStation(
            fluid_type=self.fluid_type,
            p_total=p_out,
            T_total=T_out,
            mass_flow=self.mass_flow,
            Mach=Mach_out,
        )

    @classmethod
    def mach_from_area(cls, area, p_total, T_total, mass_flow,
                       fluid_type="air", regime="subsonic", output="station"):
        """Recover Mach (and optionally a full FlowStation) from a known duct area.

        Inverts the isentropic area-Mach relation numerically via Brent's method.
        Fluid properties are computed inline to avoid instantiating a FlowStation.

        Args:
            area       : known duct cross-sectional area [m^2]
            p_total    : total pressure [Pa]
            T_total    : total temperature [K]
            mass_flow  : mass flow rate [kg/s]
            fluid_type : "air" or "fuel_gas"
            regime     : "subsonic" (default) or "supersonic"
            output     : "station" (default) returns FlowStation,
                         "Mach" returns float
        """
        gamma = {"air": 1.4, "fuel_gas": 1.33}[fluid_type]
        r_gas = {"air": 287.05, "fuel_gas": 287.15}[fluid_type]

        def area_from_mach(M):
            return (mass_flow * np.sqrt(r_gas * T_total)) / (
                    p_total * M * np.sqrt(gamma)
                    * (1.0 + ((gamma - 1.0) / 2.0) * M ** 2)
                    ** (-(gamma + 1.0) / (2.0 * (gamma - 1.0))))

        bracket = {"subsonic": (1e-6, 1.0 - 1e-9),
                   "supersonic": (1.0 + 1e-9, 5.0)}[regime]

        M_solution = brentq(lambda M: area_from_mach(M) - area, *bracket)

        return (FlowStation(fluid_type=fluid_type, p_total=p_total,
                            T_total=T_total, mass_flow=mass_flow, Mach=M_solution, area=area)
                if output == "station" else M_solution)


if __name__ == '__main__':
    inlet = FlowStation(p_total=1.5e6, T_total=973.0, mass_flow=22.929, Mach=0.8)
    print("Inlet area       :", inlet.area)
    print("Inlet p_static   :", inlet.p_static)
    print("Inlet t_static   :", inlet.t_static)
    print("Inlet rho/c/v    :", inlet.rho, inlet.c, inlet.v)
    outlet = inlet.isentropic_trans()
    print("Outlet T_total   :", outlet.T_total)
    print("Outlet p_total   :", outlet.p_total)
    print("Outlet area      :", outlet.area)

    M_ref = 0.6
    area_ref = FlowStation(p_total=1.5e6, T_total=973.0,
                           mass_flow=22.929, Mach=M_ref).area
    M_recover = FlowStation.mach_from_area(area_ref, 1.5e6, 973.0,
                                           22.929, output="Mach")
    assert abs(M_recover - M_ref) < 1e-6, f"Round-trip failed: {M_recover} vs {M_ref}"
    print("mach_from_area round-trip OK — M =", M_recover)

    # Test flight_condition_flow static method test (Troposphere, < 11 km)
    fc_cruise = {
        "altitude": 10668.0,
        "Mach": 0.78,
        "ISA_deviation": 0.0
    }
    cruise_flow = FlowStation.flight_condition_flow(fc_cruise, 250.0)
    print("\nCruise Flow Station (< 11km):")
    print(f"Altitude: {fc_cruise['altitude']} m, Mach: {fc_cruise['Mach']}")
    print(f"Ambient Temperature (Static): {cruise_flow.t_static:.2f} K (Expected ~218.81 K)")
    print(f"Ambient Pressure (Static): {cruise_flow.p_static:.2f} Pa (Expected ~23841 Pa)")
    print(f"Total Temperature: {cruise_flow.T_total:.2f} K")
    print(f"Total Pressure: {cruise_flow.p_total:.2f} Pa")


