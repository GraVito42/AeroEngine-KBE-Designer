# Ensure project root is in sys.path when running this file directly
import sys
from pathlib import Path
for parent in Path(__file__).resolve().parents:
    if (parent / "EngineCore").exists() and (parent / "Thermodynamics").exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break

import numpy as np
from parapy.core import Input, Attribute, Part, child, Base
from scipy.optimize import root_scalar

"""
In this file the FlowStation class is defined in order to classify flow properties at the diverse station of the engine, 
along with AmbientStation class which is a specific type of low station used to define the ambient flow condition following the ISA standard.
"""

class FlowStation(Base):
    """
    Class that collects and define all the flow characteristics
    at a given engine station
    """
    station_number = Input(0)                  # Flow station number - 0 is the ambient (input)

    fluid_type     = Input("air")              # Fluid type used ("air" or "fuel_gas")
    R              = 8.31446                   # Universal gas constant                  [J/mol*K]

    p_total        = Input(1e5)                # Total Pressure at the station           [Pa]
    T_total        = Input(288.15)             # Total Temperature at the station        [K]
    mass_flow      = Input(15)                 # Mass flow rate at the station           [kg/s]
    Mach           = Input(0.5)                # Mach number of the flow at the station  [-]

    @Input
    def area(self):
        """Engine Section area at the station [m^2]"""
        return (self.mass_flow * np.sqrt(self.R * self.T_total)) / (self.p_total * self.Mach * np.sqrt(self.gamma) * (1 + ((self.gamma - 1) / 2) * self.Mach**2)**(-(self.gamma+1)/(2* (self.gamma -1))))

    @Attribute
    def cp(self):
        """Specific heat at constant pressure [J/kg*K]"""
        return 1000 if self.fluid_type == "air" else 1150

    @Attribute
    def gamma(self):
        """Specific heats ratio [-]"""
        return 1.4 if self.fluid_type == "air" else 1.33

    @Attribute
    def r_gas(self):
        """Specific gas constant [J/kg*K]"""
        return 287.05 if self.fluid_type == "air" else 287.15 #  <------------------------- Affinare il dato (287.15)!!!!!!!!

    @Attribute
    def p_static(self):
        """Static pressure [Pa]"""
        return self.p_total / (1 + ((self.gamma -1)/2) * self.Mach**2)**(self.gamma/(self.gamma-1))

    @Attribute
    def t_static(self):
        """Static temperature [K]"""
        return self.T_total / (1 + ((self.gamma - 1) / 2) * self.Mach ** 2)

    @Attribute
    def rho(self):
        """Gas density [kg/m3]"""
        return self.p_static /(self.r_gas * self.t_static)

    @Attribute
    def c(self):
        """Speed of sound [m/s]"""
        return np.sqrt(self.gamma * self.r_gas * self.t_static)

    @Attribute
    def v(self):
        """Gas velocity [m/s]"""
        return self.Mach * self.c

    def isentropic_trans(self, target_type="temperature", target_value=1000000, eta=0.99, Mach_out=0.7):
        """
        Method to compute a new FlowStation object based on the application of an isentropic transformation on the actual
        FlowStation object. It can compute either pressure starting from temperature or viceversa.
        Inputs:
            target_type:   "pressure" or "temperature" - based on what we want to compute;
            target_value:  temperature or pressure value of the next station;
            eta:           isentropic efficiency of the process.
        Outputs:
            target_output: pressure or temperature of the next station;
        """
        target_output = None

        #Add a check for compression/expansion



        if target_type == "pressure":
            T_out = self.T_total
            ratio_T = T_out / self.T_total

            #Distinguish between expansion and compressio
            if ratio_T < 1:
                csi = eta      # Expansion case
            else:
                csi = 1/eta    # Compression case

            #Compute total pressure at the end of the transformation
            p_out = self.p_total * (csi*((T_out/self.T_total)-1)+1)**(self.gamma/(self.gamma-1))

        elif target_type == "temperature":
            p_out = target_value
            ratio_p = p_out / self.p_total

            # Distinguish between expansion and compressio
            if ratio_p < 1:
                csi = eta  # Compression case
            else:
                csi = 1 / eta  # Expansion case

            T_out = self.T_total * (1 + csi * ((p_out/self.p_total)**((self.gamma - 1)/self.gamma)-1))


        FlowOut = FlowStation(
            p_total   = p_out,
            T_total   = T_out,
            mass_flow = self.mass_flow,
            Mach      = Mach_out
        )
        return FlowOut


if __name__ == '__main__':
    # Test 1: Original test
    inlet_flow = FlowStation(
        p_total        = 1500000,
        T_total        = 973,
        mass_flow      = 22.929,
        Mach           = 0.8)

    print("Inlet area:", inlet_flow.area)
    outlet_flow = inlet_flow.isentropic_trans()
    print("Outlet T_total:", outlet_flow.T_total)
    print("Outlet area:", outlet_flow.area)

    # Test 2: New flight_condition_flow static method test (Troposphere, < 11 km)
    # fc_cruise = {
    #     "altitude": 10668.0,
    #     "Mach": 0.78,
    #     "ISA_deviation": 0.0
    # }
    # cruise_flow = FlowStation.flight_condition_flow(fc_cruise, 250.0)
    # print("\nCruise Flow Station (< 11km):")
    # print(f"Altitude: {fc_cruise['altitude']} m, Mach: {fc_cruise['Mach']}")
    # print(f"Ambient Temperature (Static): {cruise_flow.t_static:.2f} K (Expected ~218.81 K)")
    # print(f"Ambient Pressure (Static): {cruise_flow.p_static:.2f} Pa (Expected ~23841 Pa)")
    # print(f"Total Temperature: {cruise_flow.T_total:.2f} K")
    # print(f"Total Pressure: {cruise_flow.p_total:.2f} Pa")
    #
    # Test 3: New flight_condition_flow static method test (Stratosphere, > 11 km)
    # fc_strato = {
    #     "altitude": 15000.0,
    #     "Mach": 0.8,
    #     "ISA_deviation": 5.0  # Warm day deviation
    # }
    # strato_flow = FlowStation.flight_condition_flow(fc_strato, 200.0)
    # print("\nStratosphere Flow Station (> 11km):")
    # print(f"Altitude: {fc_strato['altitude']} m, Mach: {fc_strato['Mach']}, ISA Dev: {fc_strato['ISA_deviation']} K")
    # print(f"Ambient Temperature (Static): {strato_flow.t_static:.2f} K (Expected 216.65 + 5 = 221.65 K)")
    # print(f"Ambient Pressure (Static): {strato_flow.p_static:.2f} Pa")
    # print(f"Total Temperature: {strato_flow.T_total:.2f} K")
    # print(f"Total Pressure: {strato_flow.p_total:.2f} Pa")


