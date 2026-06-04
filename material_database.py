# material_database.py
# ---------------------------------------------------------------------------
# Primary source:  CSV exported from MatWeb
#                  https://www.matweb.com → search → export results
# Fallback source: hardcoded dictionary MATERIAL_DB_FALLBACK
#
# Expected CSV header row (MatWeb format):
#   Material Name, Density, Yield Strength, Ultimate Tensile Strength,
#   Elongation at Break, ...
# ---------------------------------------------------------------------------

import csv
import os

# ------------------------------------------------------------------
# Hardcoded fallback (used if CSV is not available)
# ------------------------------------------------------------------
MATERIAL_DB_FALLBACK = {
    "Ti-6Al-4V": {
        "density":                    4430.0,
        "yield_stress":               880e6,
        "ultimate_tensile_strength":  950e6,
        "fracture_strain":            0.14,
        "color":                      (0.7, 0.7, 0.9),
    },
    "Inconel-718": {
        "density":                    8190.0,
        "yield_stress":               1100e6,
        "ultimate_tensile_strength":  1375e6,
        "fracture_strain":            0.12,
        "color":                      (0.8, 0.6, 0.2),
    },
    "Al-2024-T3": {
        "density":                    2780.0,
        "yield_stress":               345e6,
        "ultimate_tensile_strength":  483e6,
        "fracture_strain":            0.18,
        "color":                      (0.85, 0.85, 0.85),
    },
    "Steel-4340": {
        "density":                    7850.0,
        "yield_stress":               470e6,
        "ultimate_tensile_strength":  745e6,
        "fracture_strain":            0.22,
        "color":                      (0.4, 0.4, 0.4),
    },
}

# ------------------------------------------------------------------
# Column mapping: MatWeb CSV header → internal key
# Adapt these names if your CSV uses different headers.
# MatWeb uses mixed units (g/cc, MPa) → converted on import.
# ------------------------------------------------------------------
MATWEB_COLUMN_MAP = {
    "Material Name":             "name",
    "Density":                   "density",                  # g/cc  → kg/m³ (*1000)
    "Yield Strength, Tensile":   "yield_stress",             # MPa   → Pa    (*1e6)
    "Ultimate Tensile Strength": "ultimate_tensile_strength",# MPa   → Pa    (*1e6)
    "Elongation at Break":       "fracture_strain",          # %     → -     (/100)
}

# Default CAD colors per material family (heuristic on name substring)
_COLOR_MAP = {
    "ti":      (0.7,  0.7,  0.9),   # titanium  → light blue
    "inconel": (0.8,  0.6,  0.2),   # Ni alloys → gold
    "al":      (0.85, 0.85, 0.85),  # aluminium → light grey
    "steel":   (0.4,  0.4,  0.4),   # steel     → dark grey
    "cfrp":    (0.15, 0.15, 0.15),  # composites→ near black
    "default": (0.6,  0.6,  0.6),
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
    Read a MatWeb CSV export and return a dictionary compatible
    with MATERIAL_DB_FALLBACK.

    Rows with missing critical properties are skipped with a warning
    and do not block the rest of the load.
    """
    db = {}

    if not os.path.isfile(csv_path):
        print(f"[MaterialDB] CSV not found: {csv_path}. Using fallback.")
        return db

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Extract material name
            name = row.get("Material Name", "").strip()
            if not name:
                continue

            # Convert properties, applying MatWeb unit scaling
            density = _safe_float(row.get("Density", ""),                  scale=1000.0)  # g/cc  → kg/m³
            ys      = _safe_float(row.get("Yield Strength, Tensile", ""),  scale=1e6)     # MPa   → Pa
            uts     = _safe_float(row.get("Ultimate Tensile Strength", ""),scale=1e6)     # MPa   → Pa
            eps_pct = _safe_float(row.get("Elongation at Break", ""))
            eps_f   = eps_pct / 100.0 if eps_pct is not None else None                    # %     → -

            # Skip row if any critical property is missing
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


def build_material_db(csv_path: str = "matweb_export.csv") -> dict:
    """
    Single entry point for material.py.
    Priority: CSV entries override fallback; fallback fills any gaps.
    """
    csv_db = load_matweb_csv(csv_path)
    # Merge: fallback provides base, CSV entries take precedence
    return {**MATERIAL_DB_FALLBACK, **csv_db}


# Global dictionary — imported by material.py
MATERIAL_DB = build_material_db()