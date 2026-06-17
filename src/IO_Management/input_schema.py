"""
input_schema.py — single source of truth for AeroEngine input definitions.

This schema drives ALL THREE InputParser functions:
    1. xlsx I/O      — which keys live in which section / sheet
    2. tkinter GUI   — labels, units, field types, dropdown choices
    3. validate()    — min/max bounds, suggested range on error

Structure:
    INPUT_SCHEMA[section][key] = {
        "label": str,
        "unit":  str,
        "type":  str,        # "float" | "int" | "choice"
        "default": ...,
        "min":   float,      # inclusive lower bound (None = unbounded)
        "max":   float,      # inclusive upper bound (None = unbounded)
        # "choice" entries carry "choices": None -> filled at runtime
        #          by the GUI from material_database.py / sheet 2
    }

Ranges are first-pass engineering estimates to be replaced after validation sweeps.
"""

INPUT_SCHEMA = {

    # SECTION 0 — design_flight_conditions
    "design_flight_conditions": {
        "altitude":      {"label": "Cruise altitude",           "unit": "m",   "type": "float", "default": 10668.0, "min": 0.0,    "max": 20000.0},
        "Mach":          {"label": "Cruise Mach number",        "unit": "-",   "type": "float", "default": 0.78,    "min": 0.0,    "max": 1.0},
        "ISA_deviation": {"label": "ISA temperature deviation", "unit": "K",   "type": "float", "default": 0.0,     "min": -30.0,  "max": 30.0},
    },

    # SECTION 1 — engine_features
    "engine_features": {
        "IPR":              {"label": "Inlet pressure recovery",        "unit": "-",      "type": "float", "default": 0.99,    "min": 0.85,   "max": 1.0},
        "CPR":              {"label": "Compressor pressure ratio",      "unit": "-",      "type": "float", "default": 30.0,    "min": 1.5,    "max": 60.0},
        "CCPR":             {"label": "Combustor pressure ratio",       "unit": "-",      "type": "float", "default": 0.96,    "min": 0.85,   "max": 1.0},
        "TPR":              {"label": "Turbine pressure ratio",         "unit": "-",      "type": "float", "default": 0.03,    "min": 0.0,    "max": 1.0},   # TODO: verify with Architect
        "NPR":              {"label": "Nozzle pressure ratio",          "unit": "-",      "type": "float", "default": 0.2,     "min": 0.0,    "max": 1.0},   # TODO: verify with Architect
        "I_eta":            {"label": "Inlet isentropic efficiency",    "unit": "-",      "type": "float", "default": 0.99,    "min": 0.90,   "max": 1.0},
        "C_eta":            {"label": "Compressor isentropic eff.",     "unit": "-",      "type": "float", "default": 0.88,    "min": 0.80,   "max": 1.0},
        "CC_eta":           {"label": "Combustion efficiency",          "unit": "-",      "type": "float", "default": 0.995,   "min": 0.90,   "max": 1.0},
        "T_eta":            {"label": "Turbine isentropic eff.",        "unit": "-",      "type": "float", "default": 0.90,    "min": 0.80,   "max": 1.0},
        "N_eta":            {"label": "Nozzle isentropic efficiency",   "unit": "-",      "type": "float", "default": 0.98,    "min": 0.90,   "max": 1.0},
        "TIT":              {"label": "Turbine entry temperature",      "unit": "K",      "type": "float", "default": 1500.0,  "min": 1000.0, "max": 2200.0},
        "Thrust_required":  {"label": "Thrust required",                "unit": "N",      "type": "float", "default": 35000.0, "min": 1000.0, "max": 500000.0},
        "LHV":              {"label": "Fuel lower heating value",       "unit": "J/kg",   "type": "float", "default": 43.0e6,  "min": 40.0e6, "max": 46.0e6},
        "fuel_residence_time": {"label": "Fuel residence time",         "unit": "s",      "type": "float", "default": 0.005,   "min": 0.001,  "max": 0.05},
        "gamma_g":          {"label": "Gas specific-heat ratio",        "unit": "-",      "type": "float", "default": 1.33,    "min": 1.25,   "max": 1.40},
        "cpg":              {"label": "cp combustion gas",              "unit": "J/kg/K", "type": "float", "default": 1150.0,  "min": 1000.0, "max": 1300.0},
        "r_gas":            {"label": "Specific gas constant (air)",    "unit": "J/kg/K", "type": "float", "default": 287.05,  "min": 280.0,  "max": 300.0},
        "mech_eta":         {"label": "Shaft mechanical efficiency",    "unit": "-",      "type": "float", "default": 0.98,    "min": 0.90,   "max": 1.0},
        "stage_PR_max":     {"label": "Max per-stage PR (axial)",       "unit": "-",      "type": "float", "default": 1.4,     "min": 1.1,    "max": 1.7},
        "C_work_coeff":     {"label": "Compressor stage coeff.",        "unit": "-",      "type": "float", "default": 0.4,     "min": 0.2,    "max": 1.2},   # TODO: verify with Architect
        "T_work_coeff":     {"label": "Turbine stage loading",          "unit": "-",      "type": "float", "default": 1.5,     "min": 0.8,    "max": 3.0},   # TODO: verify with Architect
        "C_reaction_coeff": {"label": "Compressor reaction",            "unit": "-",      "type": "float", "default": 0.5,     "min": 0.0,    "max": 1.0},
        "T_reaction_coeff": {"label": "Turbine reaction",               "unit": "-",      "type": "float", "default": 0.5,     "min": 0.0,    "max": 1.0},
    },

    # SECTION 2 — engine_geometry
    "engine_geometry": {
        "d_max":                 {"label": "Engine max diameter",           "unit": "m", "type": "float", "default": 1.0,   "min": 0.3,   "max": 4.0},
        "spool_tip_fraction":     {"label": "Spool nose fraction (inlet)",    "unit": "-", "type": "float", "default": 0.3,   "min": 0.05,  "max": 0.6},
        "spool_bottom_fraction":  {"label": "Spool tail fraction (nozzle)",   "unit": "-", "type": "float", "default": 0.3,   "min": 0.05,  "max": 0.6},
        "inlet_length":          {"label": "Inlet duct length",             "unit": "m", "type": "float", "default": 0.55,  "min": 0.1,   "max": 2.0},
        "nozzle_length":         {"label": "Nozzle length",                 "unit": "m", "type": "float", "default": 0.45,  "min": 0.1,   "max": 2.0},
        "casing_wall_thickness": {"label": "Casing wall thickness",         "unit": "m", "type": "float", "default": 0.012, "min": 0.001, "max": 0.05},
        "lip_radius_ratio":      {"label": "Inlet lip radius ratio",        "unit": "-", "type": "float", "default": 0.06,  "min": 0.0,   "max": 0.3},
        "inlet_wall_thickness":  {"label": "Inlet wall thickness (opt.)",   "unit": "m", "type": "float", "default": 0.012, "min": 0.001, "max": 0.05},
        "nozzle_wall_thickness": {"label": "Nozzle wall thickness (opt.)",  "unit": "m", "type": "float", "default": 0.012, "min": 0.001, "max": 0.05},
        "sheet_thickness":       {"label": "Structural sheet thickness",   "unit": "m", "type": "float", "default": 0.003, "min": 0.0005, "max": 0.020},
        "spool_sheet_thickness": {"label": "Spool sheet thickness", "unit": "m", "type": "float", "default": 0.015, "min": 0.001, "max": 0.05},
        "combustor_length":      {"label": "Combustor length (opt.)",       "unit": "m", "type": "float", "default": 0.35,  "min": 0.1,   "max": 1.5},
        "containment_margin":    {"label": "Containment margin [-]",        "unit": "-", "type": "float", "default": 0.0,   "min": 0.0,   "max": 2.0},
    },

    # SECTION 3 — engine_materials
    "engine_materials": {
        "C_rotor":   {"label": "Compressor rotor material",  "unit": "-", "type": "choice", "default": "Ti",           "choices": None},
        "C_stator":  {"label": "Compressor stator material", "unit": "-", "type": "choice", "default": "Ti",           "choices": None},
        "T_rotor":   {"label": "Turbine rotor material",     "unit": "-", "type": "choice", "default": "Ti",           "choices": None},
        "T_stator":  {"label": "Turbine stator material",    "unit": "-", "type": "choice", "default": "Ti",           "choices": None},
        "shaft":     {"label": "Shaft material",             "unit": "-", "type": "choice", "default": "Ti",           "choices": None},
        "casing":    {"label": "Casing material",            "unit": "-", "type": "choice", "default": "Ti",           "choices": None},
        "combustor": {"label": "Combustor material",         "unit": "-", "type": "choice", "default": "Inconel-718",  "choices": None},
        # TODO: combustor @Part in AeroEngine.py hardcodes material_name="Inconel-718" —
        #       wiring this dict to the part is tracked separately, do not fix here.
    },
}
