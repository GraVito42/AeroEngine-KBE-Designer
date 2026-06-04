# engine_component.py
"""
Abstract base class EngineComponent.
Both Duct and Turbomachine inherit from this class.
"""
from parapy.core import Base, Input, Attribute, Part
from parapy.geom import GeomBase, Position, XOY, Cylinder, rotate

from Flow_station import FlowStation
from Material import Material


class EngineComponent(GeomBase):
    """
    Abstract base for all engine components (Duct, Turbomachine).

    Receives a fully-constructed FlowStation object as inflow_conditions.
    The outlet FlowStation is derived lazily from it.
    """

    # ------------------------------------------------------------------
    # Inputs
    # ------------------------------------------------------------------

    #: FlowStation object — the inlet thermodynamic state
    inflow_conditions: object = Input()

    #: –   total pressure ratio across the component  (P_out / P_in)
    pressure_ratio: float = Input(1.0)

    #: –   isentropic efficiency  (0 < η ≤ 1)
    isos_efficiency: float = Input(0.90)

    #: –   outlet Mach number (set by subclass geometry rule-of-thumb)
    Mach_out: float = Input(0.5)

    #: int  engine station number at outlet (inlet number lives in inflow_conditions)
    station_out: int = Input()

    #: [m]  length of the component wrt the engine axis
    length: float = Input(0.2)

    #: [m]  radius of the component
    radius: float = Input(0.2)

    #: str  material name
    material_name: str = Input("Steel-4340")

    # ----------------------------------------------------------------------
    # Outlet station - default is computed for an isoentropic transformation
    # ----------------------------------------------------------------------

    @Input
    def outlet_flow(self):
        return self.inflow_conditions.isentropic_trans(
            target_type="temperature",
            target_value=self.inflow_conditions.p_total * self.pressure_ratio,
            eta=self.isos_efficiency,
            Mach_out=self.Mach_out,
        )

    # ------------------------------------------------------------------
    # FlowStation @Part children  (UML "2 (inlet/outlet)" composition)
    # ------------------------------------------------------------------

    @Part
    def station_in(self):
        """
        Inlet FlowStation — re-parented as a @Part child so it appears
        in the GUI tree and ParaPy tracks dependencies through it.
        NOTE: we re-instantiate from the passed object's scalar values
        because ParaPy Parts must be owned by exactly one parent.
        """
        return FlowStation(
            station_number = self.inflow_conditions.station_number,
            fluid_type     = self.inflow_conditions.fluid_type,
            p_total        = self.inflow_conditions.p_total,
            T_total        = self.inflow_conditions.T_total,
            mass_flow      = self.inflow_conditions.mass_flow,
            Mach           = self.inflow_conditions.Mach,
        )

    @Part
    def station_out_part(self):
        """
        Outlet FlowStation — derived lazily via isentropic_trans.
        The chain is:  pressure_ratio + isos_efficiency  →  T_total_out
                       → this Part's inputs  →  area_out, etc.
        """
        return FlowStation(
            station_number = self.station_out,
            fluid_type     = self.inflow_conditions.fluid_type,
            p_total        = self.outlet_flow.p_total,
            T_total        = self.outlet_flow.T_total,
            mass_flow      = self.inflow_conditions.mass_flow,
            Mach           = self.Mach_out,
        )

    # --------------------------------------------------------------------------------------------
    # Material @Part - to model Component's density and strain stresses
    # --------------------------------------------------------------------------------------------

    @Part
    def material(self):
        return Material(
            material_name=self.material_name
        )
    # --------------------------------------------------------------------------------------------
    # Geometric features - @Input so they can be changed from the inputs after high-level analysis
    # --------------------------------------------------------------------------------------------

    @Input
    def area_in(self):
        """Inlet cross-sectional flow area [m²]."""
        return self.station_in.area

    @Input
    def area_out(self):
        """Outlet cross-sectional flow area [m²]."""
        return self.station_out_part.area

    @Input
    def position(self):
        return rotate(XOY, 'y', 90, deg=True)

    @Part
    def body(self):
        return Cylinder(
            position = self.position,
            radius=self.radius,
            height=self.length,
            color=self.material.color,
        )

    @Attribute
    def volume(self):
        return self.body.volume

    @Attribute
    def weight(self):
        return self.volume*self.material.density

    # ------------------------------------------------------------------
    # Attributes (shortcuts into the two stations)
    # ------------------------------------------------------------------

    @Attribute
    def station_summary(self):
        """Inlet + outlet summary dict — fed to ReportWriter."""
        return {
            f"station_{self.station_in.station_number}":  self.station_in.summary,
            f"station_{self.station_out}":                self.station_out_part.summary,
        }

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self):
        """Physical-bounds checks. Returns list of warning strings."""
        warnings = []
        if not (0.0 < self.isos_efficiency <= 1.0):
            warnings.append(
                f"{self.__class__.__name__}: isos_efficiency "
                f"{self.isos_efficiency} outside (0,1]."
            )
        if self.pressure_ratio <= 0.0:
            warnings.append(
                f"{self.__class__.__name__}: pressure_ratio must be > 0."
            )
        if self.inflow_conditions.Mach > 0.9:
            warnings.append(
                f"{self.__class__.__name__}: inlet Mach "
                f"{self.inflow_conditions.Mach} is transonic — verify."
            )
        return warnings

from parapy.gui import display

if __name__ == '__main__':

    # ------------------------------------------------------------------
    # Define inlet FlowStation (compressor inlet, station 2)
    # ------------------------------------------------------------------
    inlet = FlowStation(
        station_number = 2,
        fluid_type     = "air",
        p_total        = 101325.0,
        T_total        = 288.15,
        mass_flow      = 22.9,
        Mach           = 0.5,
    )

    # ------------------------------------------------------------------
    # Instantiate EngineComponent directly (no abstract methods to block it)
    # ------------------------------------------------------------------
    comp = EngineComponent(
        inflow_conditions = inlet,
        pressure_ratio    = 8.0,
        isos_efficiency   = 0.88,
        Mach_out          = 0.4,
        station_out       = 3,
    )

    # ------------------------------------------------------------------
    # Check inlet and outlet stations
    # ------------------------------------------------------------------
    print("=== INLET STATION ===")
    print(f"  p_total  [Pa] : {comp.station_in.p_total:.2f}")
    print(f"  T_total  [K]  : {comp.station_in.T_total:.2f}")
    print(f"  area     [m²] : {comp.station_in.area:.4f}")

    print("\n=== OUTLET STATION ===")
    print(f"  p_total  [Pa] : {comp.station_out_part.p_total:.2f}")
    print(f"  T_total  [K]  : {comp.station_out_part.T_total:.2f}")
    print(f"  area     [m²] : {comp.station_out_part.area:.4f}")

    # ------------------------------------------------------------------
    # Check @Input areas (isentropic default, then CFD override)
    # ------------------------------------------------------------------
    print("\n=== AREAS (isentropic default) ===")
    print(f"  area_in  [m²] : {comp.area_in:.4f}")
    print(f"  area_out [m²] : {comp.area_out:.4f}")

    print("\n=== AREAS (after CFD override) ===")
    comp.area_in  = 0.1234
    comp.area_out = 0.0891
    print(f"  area_in  [m²] : {comp.area_in:.4f}")
    print(f"  area_out [m²] : {comp.area_out:.4f}")

    display(comp)