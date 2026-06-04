# material.py
# ---------------------------------------------------------------------------
from parapy.core import Base, Input, Attribute
from material_database import MATERIAL_DB


class Material(Base):
    """
    KBE material class for EngineComponent.

    Usage (minimal – all props come from the DB):
        mat = Material(material_name="Ti-6Al-4V")

    Usage (override one prop):
        mat = Material(material_name="Ti-6Al-4V", yield_stress=950e6)
    """

    # ------------------------------------------------------------------
    # Required input
    # ------------------------------------------------------------------
    material_name = Input()   # must match a key in MATERIAL_DB

    # ------------------------------------------------------------------
    # Method: DB lookup → dict with all properties for this material
    # Plain method (not @Attribute) because it is the *source* from
    # which the @Input defaults are derived; making it @Attribute would
    # create a circular dependency with the @Input slots below.
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Physical inputs – default derived from DB, fully overridable
    # ------------------------------------------------------------------
    @Input
    def density(self):                      # kg/m³
        return self.get_info_material()["density"]

    @Input
    def yield_stress(self):                 # Pa
        return self.get_info_material()["yield_stress"]

    @Input
    def ultimate_tensile_strength(self):    # Pa
        return self.get_info_material()["ultimate_tensile_strength"]

    @Input
    def fracture_strain(self):              # -
        return self.get_info_material()["fracture_strain"]

    # ------------------------------------------------------------------
    # Display attribute – RGB tuple for CAD visualisation
    # Not overridable by the user; purely derived from the DB entry.
    # ------------------------------------------------------------------
    @Attribute
    def color(self):
        return self.get_info_material()["color"]

    def get_info_material(self):
        if self.material_name not in MATERIAL_DB:
            raise KeyError(
                f"Material '{self.material_name}' not found in MATERIAL_DB. "
                f"Available: {list(MATERIAL_DB.keys())}"
            )
        return MATERIAL_DB[self.material_name]


if __name__ == "__main__":
    mat = Material(material_name="Ti-6Al-4V")
    print(f"Material : {mat.material_name}")
    print(f"Density  : {mat.density} kg/m³")
    print(f"Yield σ  : {mat.yield_stress / 1e6:.1f} MPa")
    print(f"UTS      : {mat.ultimate_tensile_strength / 1e6:.1f} MPa")
    print(f"ε_f      : {mat.fracture_strain}")
    print(f"Color    : {mat.color}")

    # override test
    mat2 = Material(material_name="Ti-6Al-4V", yield_stress=999e6)
    print(f"\nOverride yield_stress: {mat2.yield_stress / 1e6:.1f} MPa (expected 999.0)")