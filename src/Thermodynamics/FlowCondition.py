# ===== FILE: FlowCondition.py =====
import numpy as np
from parapy.core import Base, Input, Attribute

"""
FlowCondition: pure-thermodynamic primitive for a calorically perfect gas.
Holds ONLY total conditions and fluid properties.
NO Mach, NO area, NO mass_flow, NO static quantities (those live in FlowStation).
"""


class FlowCondition(Base):
    """Total thermodynamic state of a calorically perfect gas."""

    fluid_type:str = Input("air")        # "air" or "fuel_gas"
    p_total:float    = Input(1e5)          # Total pressure    [Pa]
    T_total:float    = Input(288.15)       # Total temperature [K]

    R = 8.31446                      # Universal gas constant [J/mol/K]

    @Attribute
    def cp(self):
        """Specific heat at constant pressure [J/kg/K]."""
        return {"air": 1000.0, "fuel_gas": 1150.0}[self.fluid_type]

    @Attribute
    def gamma(self):
        """Specific-heat ratio [-]."""
        return {"air": 1.4, "fuel_gas": 1.33}[self.fluid_type]

    @Attribute
    def r_gas(self):
        """Specific gas constant [J/kg/K]."""
        return {"air": 287.05, "fuel_gas": 287.15}[self.fluid_type]

    def isentropic_trans_th(self, target_type="temperature", target_value=1e6, eta=0.99):
        """Pure thermodynamic isentropic transformation (no Mach / area / mass_flow).
        Returns (p_out, T_out). Uses only self.p_total, self.T_total, self.gamma.
        Plain Python method: assignments and if-blocks are allowed here."""
        if target_type == "temperature":
            # Pressure is the target; temperature is the computed output.
            p_out = target_value
            ratio_p = p_out / self.p_total
            csi = eta if ratio_p < 1.0 else 1.0 / eta
            T_out = self.T_total * (
                1.0 + csi * (ratio_p ** ((self.gamma - 1.0) / self.gamma) - 1.0))
            return p_out, T_out
        elif target_type == "pressure":
            # Temperature is the target; pressure is the computed output.
            T_out = target_value          # BUG FIX: legacy code wrongly used self.T_total here.
            ratio_T = T_out / self.T_total
            csi = eta if ratio_T < 1.0 else 1.0 / eta
            p_out = self.p_total * (csi * (ratio_T - 1.0) + 1.0) ** (
                self.gamma / (self.gamma - 1.0))
            return p_out, T_out
        raise ValueError("target_type must be 'temperature' or 'pressure'")

    @staticmethod
    def flight_condition_flow(flight_condition):
        """
        Computes flow properties at freestream conditions based on flight conditions.
        Uses the International Standard Atmosphere (ISA) model for altitude-dependent pressure and temperature.

        Parameters:
        - flight_condition: dict containing:
            - 'altitude': altitude in meters [m]
            - 'Mach': Mach number [-]
            - 'ISA_deviation' (or 'isa_deviation'): deviation from standard day temperature [K] (default 0.0)

        Returns:
        - FlowStation object
        """
        # Retrieve values with fallback keys
        altitude = flight_condition.get("altitude", flight_condition.get("Altitude", 0.0))
        mach = flight_condition.get("Mach", flight_condition.get("mach", 0.0))
        isa_deviation = flight_condition["ISA_deviation"]

        # Sea-level standard constants
        p0 = 101325.0  # Standard sea-level pressure [Pa]
        T0 = 288.15  # Standard sea-level temperature [K]
        L = 0.0065  # Temperature lapse rate [K/m]
        g = 9.80665  # Gravitational acceleration [m/s^2]
        R = 287.05  # Specific gas constant for air [J/(kg*K)]
        # \\ even if we have self.r_gas, this is independent of self

        # Troposphere vs Lower Stratosphere (tropopause at 11,000 m)
        if altitude <= 11000.0:
            T_static_std = T0 - L * altitude
            p_static = p0 * (T_static_std / T0) ** (g / (L * R))
        else:
            T_tropo = T0 - L * 11000.0  # 216.65 K
            p_tropo = p0 * (T_tropo / T0) ** (g / (L * R))  # ~22632.04 Pa

            T_static_std = T_tropo
            p_static = p_tropo * np.exp(-g * (altitude - 11000.0) / (R * T_tropo))

        # Apply temperature deviation
        T_static = T_static_std + isa_deviation

        # Standard air (gamma = 1.4)
        gamma = 1.4  # same as above, we didn't use self.gamma to keep it independent
        T_total = T_static * (1 + ((gamma - 1) / 2) * mach ** 2)
        p_total = p_static * (1 + ((gamma - 1) / 2) * mach ** 2) ** (gamma / (gamma - 1))

        return FlowCondition(
            p_total=p_total,
            T_total=T_total,
            fluid_type="air",
        )


if __name__ == '__main__':
    fc = FlowCondition(fluid_type="air", p_total=1.0e5, T_total=288.15)
    print("cp, gamma, r_gas :", fc.cp, fc.gamma, fc.r_gas)
    # target_type='temperature' -> we KNOW the pressure target, compute T.
    p_out, T_out = fc.isentropic_trans_th("temperature", 10.0e5, eta=0.90)
    print(f"Compression to 10 bar -> p_out={p_out:.1f} Pa, T_out={T_out:.2f} K")
    # target_type='pressure' -> we KNOW the temperature target, compute p.
    p2, T2 = fc.isentropic_trans_th("pressure", 600.0, eta=0.90)
    print(f"To T=600 K            -> p_out={p2:.1f} Pa, T_out={T2:.2f} K")