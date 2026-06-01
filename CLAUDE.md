# CLAUDE.md — KBE Turbojet Project (Team 23, TU Delft AE4314)

This file gives you full context on the project architecture, coding conventions,
and domain knowledge. Read it entirely before writing or modifying any code.

---

## Project Overview

A Knowledge Based Engineering (KBE) application built in ParaPy that models a
turbojet engine from 1D thermodynamic input to coarse 3D CAD geometry.

The app bridges the gap between 1D cycle analysis and 3D geometry, supporting
rapid design space exploration during conceptual design. It integrates with the
Multall CFD suite (Meangen → Stagen → Multall) for turbomachinery analysis.

**Input:** `.xlsx` file with thermodynamic cycle parameters, architecture specs,
materials, and operational requirements.

**Output:** STEP files (full assembly, spools+blades, engine frame), PDF/CSV
performance report with T-S diagram and cross-section views.

---

## Class Architecture

```
AeroEngine
├── InputParser          # reads .xlsx, validates inputs
├── ReportWriter         # exports PDF, CSV, STEP
├── EngineFrame          # casing geometry + blade-off analysis
│   ├── Inlet            # inherits Duct → EngineComponent
│   └── Nozzle           # inherits Duct → EngineComponent
├── Combustor            # coarse geometry, no CFD
└── Spool                # coordinates turbomachines, power balance
    ├── Compressor       # inherits Turbomachine → EngineComponent
    │   └── n_stages × Stage
    │       └── 2×n_blades × Blade
    └── Turbine          # inherits Turbomachine → EngineComponent
        └── n_stages × Stage
            └── 2×n_blades × Blade
```

**Abstract classes:**
- `EngineComponent(GeomBase)` — base for all components
- `Turbomachine(EngineComponent)` — base for Compressor and Turbine
- `Duct(EngineComponent)` — base for Inlet and Nozzle

**Utility:**
- `FlowStation(Base)` — thermodynamic state at one engine station

---

## File Structure

```
src/
├── AeroEngine.py
├── EngineComponent.py   # abstract base — DO NOT modify without updating all subclasses
├── Duct.py              # abstract base for Inlet and Nozzle
├── Turbomachine.py      # abstract base for Compressor and Turbine
├── FlowStation.py       # thermodynamic flow state — used everywhere
├── FlowStation.py
├── Inlet.py
├── Nozzle.py
├── Compressor.py
├── Turbine.py
├── Stage.py
├── Blade.py
├── EngineFrame.py
├── Combustor.py
├── Spool.py
├── InputParser.py
└── ReportWriter.py
docs/
├── pdf/                 # Parapy docs, Multall docs, aero engine lectures
└── notes/               # markdown summaries
multall/                 # Multall .dat input and output files (populated later)
```

---

## ParaPy Coding Conventions

These are strict — always follow them exactly.

### 1. Simple inputs (fixed default)
```python
length: float = Input(0.2)
density: float = Input(2800.0)
```

### 2. @Input decorator (default depends on other attributes)
```python
@Input
def n_stages(self):
    return self._estimate_stages()

@Input
def r_inlet_inner(self) -> float:
    return math.sqrt(self.area_in / math.pi)
```

### 3. @Attribute (computed, lazy, cached)
```python
@Attribute
def pressure_drop(self):
    return (1.0 - self.pressure_ratio) * self.station_in.p_total

@Attribute
def weight(self):
    return self.volume * self.density
```

### 4. @Part (geometric children or sub-objects)
```python
@Part
def body(self):
    return RevolvedSolid(
        built_from=self.wall_profile,
        center=Point(0, 0, 0),
        direction=(1, 0, 0),
        angle=2 * math.pi,
    )
```

### 5. Plain methods (no decorator)
```python
def validate(self):
    warnings = super().validate()
    if not 0 < self.isos_efficiency <= 1:
        warnings.append(f"...")
    return warnings

def is_choked(self) -> bool:
    return self.a_min <= self.a_star
```

### CRITICAL ParaPy rules
- `@Part` body must end with a **single `return` statement** — no `if/else` allowed
- Move all conditional logic into an `@Attribute`, then reference it in `@Part`
- Never use `@Part(parse=False)` unless absolutely necessary
- `@Attribute` values are cached — do not use for anything with side effects
- Parts must be owned by exactly one parent — never pass a Part object directly,
  re-instantiate with scalar values (see `station_in` in `EngineComponent`)

---

## FlowStation

The thermodynamic backbone of the project. Used by every component.

```python
FlowStation(
    station_number = 2,       # int, engine station number
    fluid_type     = "air",   # "air" or "fuel_gas"
    p_total        = 101325,  # Pa
    T_total        = 288.15,  # K
    mass_flow      = 22.9,    # kg/s
    Mach           = 0.5,     # -
)
```

Key attributes: `area`, `p_static`, `t_static`, `rho`, `c`, `v`, `gamma`, `cp`, `r_gas`

Key method:
```python
fs.isentropic_trans(
    target_type  = "temperature",  # or "pressure"
    target_value = p_out,          # Pa or K
    eta          = 0.90,           # isentropic efficiency
    Mach_out     = 0.45,           # outlet Mach
) → FlowStation
```

---

## EngineComponent (abstract base)

All components inherit from this. Key inputs and attributes:

| Name | Type | Description |
|------|------|-------------|
| `inflow_conditions` | FlowStation | inlet thermodynamic state |
| `pressure_ratio` | float Input | P_out / P_in |
| `isos_efficiency` | float Input | isentropic efficiency (0,1] |
| `Mach_out` | float Input | outlet Mach number |
| `station_out` | int Input | outlet station number |
| `length` | float Input | axial length [m] |
| `station_in` | @Part FlowStation | inlet station (re-instantiated) |
| `station_out_part` | @Part FlowStation | outlet station (computed) |
| `area_in` | @Input float | inlet flow area [m²] |
| `area_out` | @Input float | outlet flow area [m²] |
| `volume` | @Attribute float | from body.volume |
| `weight` | @Attribute float | volume × density |

`outlet_flow` is an `@Input` that calls `inflow_conditions.isentropic_trans(...)`.
Subclasses override it (e.g. `Duct` adds choking logic).

---

## Duct (abstract, inherits EngineComponent)

Parent of `Inlet` and `Nozzle`.

Additional inputs: `Mach_design`, `pressure_ratio` (overrides EngineComponent),
`r_inlet_inner`, `r_inlet_outer`, `r_outlet_inner`, `r_outlet_outer`

Key attributes: `pressure_drop`, `wall_thickness_inlet`, `wall_thickness_outlet`

Key method: `is_choked() → bool`

Geometry:
- `wall_profile` @Part → closed Polygon in local XY plane (X=axial, Y=radial)
- `body` @Part → RevolvedSolid of wall_profile, 360° around X axis

**Axis convention:** `position = rotate(XOY, 'y', 90, deg=True)`
→ local X = engine axial direction, local Y = radial

Subclasses override `wall_profile` only. `body` is never overridden.

---

## Turbomachine (abstract, inherits EngineComponent)

Parent of `Compressor` and `Turbine`.

| Name | Type | Description |
|------|------|-------------|
| `n_stages` | int Input | number of stages |
| `detailed_features` | dict | Multall output features |
| `build_geometry()` | method | builds 3D blade geometry |
| `weight()` | method | total turbomachine weight |
| `multall_analysis()` | method | runs Meangen→Stagen→Multall pipeline |

Contains `n_stages` instances of `Stage`.

---

## Stage and Blade

**Stage:**
- inputs: `inflow_conditions`, `type` (str), `n_blades` (int)
- methods: `meangen_analysis()`, `weight()`
- contains: `2 × n_blades` Blade instances (stator + rotor)

**Blade:**
- inputs: `type` (list[str]: turbine/compressor, stator/rotor), `chords` (list[float]),
  `radius` (float), `twist` (float), `section_coords` (list[float])
- methods: `weight()`

---

## Multall Integration

The CFD pipeline: **Meangen → Stagen → Multall**

- Input files: `.in` and `.dat` (text format, written by the KBE app)
- Output files: `.out`, `.res`, TecPlot files
- Integration point: `Turbomachine.multall_analysis()` and `Stage.meangen_analysis()`
- Files live in `multall/` directory
- After CFD: geometry updates (n_stages of turbine, cross-sectional areas)

---

## Engine Station Numbering

| Station | Location |
|---------|----------|
| 0 | Ambient (freestream) |
| 1 | Inlet face |
| 2 | Compressor inlet |
| 3 | Compressor outlet |
| 4 | Turbine inlet (= combustor outlet) |
| 5 | Turbine outlet |
| 6 | Nozzle inlet |
| 7 | Nozzle exit |

---

## Physics Rules

- **Brayton cycle:** isentropic compression + isobaric combustion + isentropic expansion
- **Pressure ratio:** key parameter driving compressor and turbine sizing
- **Isentropic efficiency** η: always in (0, 1], distinguishes compression (η = 1/csi) from expansion (η = csi)
- **Choking:** occurs when A_min ≤ A* (critical area at Mach 1.0)
- **Blade-off containment:** E_s > E_k × SF where E_k = ½mv² + ½Iω², E_s = ∫σ(ε,T)dε · V
- **FlowStation.area** computed from isentropic flow relation with mass flow, Mach, p_total, T_total

---

## Validation Pattern

Every class implements `validate()` returning a list of warning strings:

```python
def validate(self):
    warnings = super().validate()      # always call super first
    if not condition:
        warnings.append(f"ClassName '{self.label}': message.")
    return warnings
```

Critical errors (invalid inputs) → raised at startup via `InputParser`
Component warnings → collected by `validate()`, shown in GUI

---

## What Is Already Implemented

- `FlowStation` — complete
- `EngineComponent` — complete
- `Duct` — complete (geometry + choking logic)
- `Inlet` — first version (wall_profile bellmouth/straight)

## What Still Needs to Be Built

- `Nozzle` — similar to Inlet, adds `is_convergent_divergent` and `thrust_coefficient`
- `Turbomachine` — abstract, needs `multall_analysis()` pipeline
- `Compressor` — adds `stage_pressure_ratio`, `polytropic_efficiency`, `surge_margin()`
- `Turbine` — adds `inlet_temperature`, `loading_factor`, `degree_of_reaction`
- `Stage` — blade geometry + meangen interface
- `Blade` — section coordinates + weight
- `EngineFrame` — casing geometry + blade-off analysis
- `Combustor` — coarse geometry
- `Spool` — power balance + coordinates turbomachines
- `AeroEngine` — top-level assembly
- `InputParser` — .xlsx reader + validation
- `ReportWriter` — PDF/CSV/STEP export
