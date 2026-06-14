# material_database.py
# ---------------------------------------------------------------------------
# Primary source:  aeroengine_materials.csv (Gemini Deep Research output)
# Fallback source: hardcoded dictionary MATERIAL_DB_FALLBACK
#
# Expected CSV header row:
#   Material Name, Component Category, Density [kg/m³], Yield Strength [MPa],
#   Ultimate Tensile Strength [MPa], Elongation at Break [%],
#   Max Operating Temperature [°C], Notes
# ---------------------------------------------------------------------------

# Ensure project root is in sys.path when running this file directly
import sys
from pathlib import Path
for parent in Path(__file__).resolve().parents:
    if (parent / "EngineCore").exists() and (parent / "Thermodynamics").exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break

import csv
from pathlib import Path

# ------------------------------------------------------------------
# CAD color map per material family (RGB 0-255, heuristic on name)
# ------------------------------------------------------------------
_COLOR_MAP = {
    "ti":      (179, 179, 230),   # titanium   → light blue
    "inconel": (204, 153,  51),   # Ni alloys  → gold
    "al":      (217, 217, 217),   # aluminium  → light grey
    "steel":   (102, 102, 102),   # steel      → dark grey
    "cfrp":    ( 38,  38,  38),   # composites → near black
    "haynes":  (210, 180, 140),   # Co alloys  → tan
    "mar-m":   (180, 130,  80),   # Mar-M      → bronze
    "waspa":   (200, 160,  60),   # Waspaloy   → dark gold
    "rene":    (190, 150,  70),   # René       → dark gold
    "haste":   (160, 200, 160),   # Hastelloy  → sage green
    "default": (153, 153, 153),
}

# ------------------------------------------------------------------
# Hardcoded fallback (used if CSV is not available)
# ------------------------------------------------------------------
MATERIAL_DB_FALLBACK = {
    "Ti-6Al-4V": {
        "density":                   4430.0,
        "yield_stress":              880e6,
        "ultimate_tensile_strength": 950e6,
        "fracture_strain":           0.14,
        "color":                     (179, 179, 230),
    },
    "Inconel-718": {
        "density":                   8190.0,
        "yield_stress":              1100e6,
        "ultimate_tensile_strength": 1375e6,
        "fracture_strain":           0.12,
        "color":                     (204, 153, 51),
    },
    "Al-2024-T3": {
        "density":                   2780.0,
        "yield_stress":              345e6,
        "ultimate_tensile_strength": 483e6,
        "fracture_strain":           0.18,
        "color":                     (217, 217, 217),
    },
    "Steel-4340": {
        "density":                   7850.0,
        "yield_stress":              470e6,
        "ultimate_tensile_strength": 745e6,
        "fracture_strain":           0.22,
        "color":                     (102, 102, 102),
    },
}

# ------------------------------------------------------------------
# Column mapping: aeroengine_materials.csv header → internal key
# Units are already in kg/m³ and MPa → apply correct scaling below.
# ------------------------------------------------------------------
MATWEB_COLUMN_MAP = {
    "Material Name":                    "name",
    "Density [kg/m³]":                  "density",                    # kg/m³ → kg/m³ (scale=1.0)
    "Yield Strength [MPa]":             "yield_stress",               # MPa   → Pa    (scale=1e6)
    "Ultimate Tensile Strength [MPa]":  "ultimate_tensile_strength",  # MPa   → Pa    (scale=1e6)
    "Elongation at Break [%]":          "fracture_strain",            # %     → -     (/100)
}


def _infer_color(material_name: str) -> tuple:
    name_lower = material_name.lower()
    return next(
        (color for key, color in _COLOR_MAP.items() if key in name_lower),
        _COLOR_MAP["default"]
    )


def _safe_float(value: str, scale: float = 1.0) -> float | None:
    """Parse string to float with unit scaling; returns None if not parseable."""
    try:
        return float(value.strip().replace(",", ".")) * scale
    except (ValueError, AttributeError):
        return None


def load_matweb_csv(csv_path: str) -> dict:
    """
    Read aeroengine_materials.csv and return a dictionary compatible
    with MATERIAL_DB_FALLBACK.

    Rows with missing critical properties are skipped with a warning
    and do not block the rest of the load.
    """
    db = {}

    if not Path(csv_path).is_file():
        print(f"[MaterialDB] CSV not found: {csv_path}. Using fallback.")
        return db

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            name = row.get("Material Name", "").strip()
            if not name:
                continue

            # Units: density already kg/m³, strengths already MPa → Pa
            density = _safe_float(row.get("Density [kg/m³]", ""),                   scale=1.0)
            ys      = _safe_float(row.get("Yield Strength [MPa]", ""),              scale=1e6)
            uts     = _safe_float(row.get("Ultimate Tensile Strength [MPa]", ""),   scale=1e6)
            eps_pct = _safe_float(row.get("Elongation at Break [%]", ""))
            eps_f   = eps_pct / 100.0 if eps_pct is not None else None

            missing = [k for k, v in {
                "density": density, "yield_stress": ys,
                "ultimate_tensile_strength": uts, "fracture_strain": eps_f
            }.items() if v is None]

            if missing:
                print(f"[MaterialDB] Skipping '{name}': missing fields → {missing}")
                continue

            db[name] = {
                "density":                   density,
                "yield_stress":              ys,
                "ultimate_tensile_strength": uts,
                "fracture_strain":           eps_f,
                "color":                     _infer_color(name),
            }

    print(f"[MaterialDB] Loaded {len(db)} materials from {csv_path}.")
    return db


def build_material_db(csv_path: str = None) -> dict:
    if csv_path is None:
        csv_path = str(Path(__file__).resolve().parent / "aeroengine_materials.csv")
    """
    Single entry point for material.py.
    Priority: CSV entries override fallback; fallback fills any gaps.
    """
    csv_db = load_matweb_csv(csv_path)
    return {**MATERIAL_DB_FALLBACK, **csv_db}


# Global dictionary — imported by material.py
MATERIAL_DB = build_material_db()