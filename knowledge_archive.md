# Project Knowledge Archive Map

This document serves as a persistent reference guide and behavioral framework for developing, testing, and maintaining the KBE project code using the materials in the `Knowledge/` folder.

---

## 1. Directory Structure of Knowledge Archive

All supplementary documentation files are located under:
* **Root Folder**: `C:\Users\Vito\Documents\UNI- Corsi\TUDELFT\Q3\KBE\Knowledge`

### Files Available:
| Filename | Purpose / Description | Category |
| :--- | :--- | :--- |
| [`00_Project_Knowledge_System.md`](file:///C:/Users/Vito/Documents/UNI-%20Corsi/TUDELFT/Q3/KBE/Knowledge/00_Project_Knowledge_System.md) | High-level map of the knowledge folder and operational boundaries. | Meta Map |
| [`Knowledge_Parapy_Documentation.md`](file:///C:/Users/Vito/Documents/UNI-%20Corsi/TUDELFT/Q3/KBE/Knowledge/Knowledge_Parapy_Documentation.md) | Syntax rules, object-oriented concepts, and GUI layout rules for ParaPy. | Code syntax |
| [`Knowledge_Multall_Documentation.md`](file:///C:/Users/Vito/Documents/UNI-%20Corsi/TUDELFT/Q3/KBE/Knowledge/Knowledge_Multall_Documentation.md) | Theoretical details, input formatting, and output parsing for the Multall suite. | Code syntax |
| [`Knowledge_AeroEngine_Lectures.md`](file:///C:/Users/Vito/Documents/UNI-%20Corsi/TUDELFT/Q3/KBE/Knowledge/Knowledge_AeroEngine_Lectures.md) | Theoretical domain knowledge for aerospace propulsion and gas turbines. | Domain Theory |
| [`Knowledge_KBE_Lectures.md`](file:///C:/Users/Vito/Documents/UNI-%20Corsi/TUDELFT/Q3/KBE/Knowledge/Knowledge_KBE_Lectures.md) | Theoretical domain knowledge for Knowledge-Based Engineering. | Domain Theory |
| `general UML diagram.png` | Visual architecture layout of classes and their associations. | Visuals (Unsupported) |
| `Team23_Ingrosso_Ronchetti.pdf` | Final project report / reference case documentation. | Case Study |

---

## 2. Key Code & Software Guidelines

### A. ParaPy Development Rules
* **Slots & Declarations**:
  * Use `@Input` for parameters that can be overridden or defined at instantiation.
  * Use `@Attribute` for calculations that are done lazily and cached.
  * Use `@Part` for child geometries and components that populate the tree.
* **Boolean & Solid Modeling**:
  * Use `FusedSolid`, `SubtractedSolid`, and `IntersectionSolid` classes from `parapy.geom`.
  * Ensure profile curves are closed before using them in extrusions/revolutions.
* **GUI Layouts**:
  * Leverage `parapy.webgui.layout` (e.g., `Split`) and `parapy.webgui.mui` (e.g., `Divider`) to assemble responsive property panels and viewers.

### B. Multall Suite Integration
* **Input formatting**:
  * Pressure values must be converted from Pascals (Pa) to bar (multiplied by `1e-5`) when setting up `meangen.in`.
  * Ensure proper parameter keys are passed to the solver class via a single `meangen_input` dictionary.
* **Output parsing**:
  * Stage details (rotor/stator parameters, blade counts, chords, section coordinates) are read from `stagen.dat` and `stagen.out` files.
  * Ensure the parser uses exact row type checking to align rows properly.

---

## 3. Visual & Spatial Constraints (CRITICAL)

Because the developer agent cannot directly view images, spatial drawings, or PDF-embedded graphics:
1. **No Guessing Coordinates**: For complex 3D placement, rotations, or vector transformations (e.g., multi-axis stacking), do not guess orientation vectors.
2. **Comment Placeholders**: Insert explicit comments into code indicating parameters that require spatial validation. For example:
   ```python
   # TODO: Verify X/Y/Z vector orientation using the Visual Positioning Cheatsheet PDF
   ```
3. **Architect Consulting**: Prompt the user to ask the "Architect" (Gemini/other multimodal models) to analyze visual files like `general UML diagram.png` or `Positioning Cheatsheet.pdf` to retrieve exact vector alignments or component arrangements.

---

## 4. Operational Protocols
* **Verification**: Prioritize code correctness and clean syntax verification from documentation before generating any class definitions.
* **Scope**: Remain focused on building, debugging, and maintaining code. Do not write long essays on aero-engine theory. Refer theoretical queries back to manual lectures or the user.
