# =============================================================================
# aero_engine_kbe / flow_station.py
# =============================================================================
import math
from parapy.core import Base, Input, Attribute

GAMMA = 1.4
R_AIR = 287.05


class FlowStation(Base):
    """Thermodynamic state at one engine cross-section. No geometry here."""

    mass_flow = Input()          # [kg/s]
    mach      = Input(0.4)       # [-]
    p_total   = Input()          # [Pa]
    t_total   = Input()          # [K]

    @Attribute
    def gamma(self):
        return GAMMA

    @Attribute
    def cp(self):
        return self.gamma * R_AIR / (self.gamma - 1.0)

    @Attribute
    def t_static(self):
        return self.t_total / (1.0 + 0.5 * (self.gamma - 1.0) * self.mach ** 2)

    @Attribute
    def p_static(self):
        return self.p_total * (self.t_static / self.t_total) ** (
            self.gamma / (self.gamma - 1.0))

    @Attribute
    def density(self):
        return self.p_static / (R_AIR * self.t_static)

    @Attribute
    def velocity(self):
        return self.mach * math.sqrt(self.gamma * R_AIR * self.t_static)

    @Attribute
    def area(self):
        """Cross-sectional flow area [m²] from continuity."""
        return self.mass_flow / (self.density * self.velocity)

    @Attribute
    def radius(self):
        """Flow annulus radius [m] assuming circular cross-section."""
        return math.sqrt(self.area / math.pi)