"""
StageParser.py
==============
Parses stagen.out into the per-section blade-surface point clouds that the
Stage / Blade classes consume.

stagen.out layout (repeats once per blade SECTION, hub -> tip, row after row):

    SUCTION SURFACE POINTS FROM LE TO TE.
        idx  x  y   -- N_suc points, x increasing LE->TE
    PRESSURE SURFACE POINTS FROM LE TO TE.
        idx  x  y   -- N_prs points, x increasing LE->TE

    AXIAL & RADIAL COORDINATES ON THE SS AFTER STACKING
        J , XGRID,RGRID  n  <x>  <r>  -- radial station

Strategy: read ONLY the two explicit SUCTION / PRESSURE blocks that STAGEN
already prints correctly.  Do NOT reconstruct surfaces from the wrap-around
array using LE/TE indices -- that is error-prone and redundant.

If a section is degenerate (suction or pressure has < MIN_PTS points), it is
replaced by linear interpolation between the nearest valid neighbours.  A
warning is printed to stderr.

Rows are auto-detected by the radius resetting from tip back to hub; or a
fixed n_sections count can be supplied.

Metric chord and blade count are NOT in stagen.out -- they come from
stagen.dat via MeangenParser.merge().
"""

# Ensure project root is in sys.path when running this file directly
import sys
from pathlib import Path
for parent in Path(__file__).resolve().parents:
    if (parent / "EngineCore").exists() and (parent / "Thermodynamics").exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break

import re
import sys

_SUC   = 'SUCTION SURFACE POINTS FROM LE TO TE'
_PRS   = 'PRESSURE SURFACE POINTS FROM LE TO TE'
_STACK = 'AXIAL & RADIAL COORDINATES ON THE SS AFTER STACKING'

# Sections with fewer points than this on either surface are treated as degenerate.
_MIN_PTS = 10

# Normalised-chord overshoot thresholds. STAGEN profiles live in roughly
# x in [0,1], y in [-0.5, 0.5]; anything beyond this is non-physical and
# indicates a corrupted/garbage section.
_MAX_ABS_X = 2.0
_MAX_ABS_Y = 2.0

# Fortran real/int token (incl. E-notation).
_NUM = r'[-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?'


class StageParser:
    """Parser for stagen.out files."""

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    # In StageParser.parse() — add machine_type parameter
    @staticmethod
    def parse(filepath, row_order=None, n_sections=None, machine_type='turbine'):
        """Parse stagen.out and return a list of stage dicts.

        Parameters
        ----------
        ...
        machine_type : str
            'compressor' or 'turbine'. For a compressor the axial x-coordinates
            in stagen.out are mirrored (x' = 1 - x for normalised profiles) so
            that the LE sits at x=0 in the engine flow direction.
        ...
        """
        with open(filepath, 'r') as fh:
            text = fh.read()

        sections = StageParser._parse_sections(text)
        if not sections:
            raise ValueError(
                "StageParser: no 'SUCTION SURFACE POINTS' blocks found. "
                "Is this a stagen.out file?"
            )

        StageParser._repair_degenerate(sections)

        section_groups = StageParser._group_into_rows(sections, n_sections)
        # Pass machine_type down so _assemble_row can apply the x-flip if needed.
        row_dicts = [StageParser._assemble_row(g, machine_type=machine_type)
                     for g in section_groups]

        if row_order is None:
            row_order = ['rotor' if i % 2 == 0 else 'stator'
                         for i in range(len(row_dicts))]
        if len(row_order) != len(row_dicts):
            raise ValueError(
                f"StageParser: row_order has {len(row_order)} entries but "
                f"{len(row_dicts)} blade rows were found."
            )

        return StageParser._pair_into_stages(row_dicts, row_order)

    # ------------------------------------------------------------------
    # Section extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_sections(text):
        """Return a flat list of section dicts in file order.

        Each dict: {'suction': [(x,y)...], 'pressure': [(x,y)...], 'r': float|None}.

        Reads the explicit SUCTION/PRESSURE blocks that STAGEN writes --
        no reconstruction from the wrap-around array.
        """
        suc_positions = [m.start() for m in re.finditer(re.escape(_SUC), text)]
        sections = []
        for i, sp in enumerate(suc_positions):
            end = suc_positions[i + 1] if i + 1 < len(suc_positions) else len(text)
            chunk = text[sp:end]

            # --- Suction surface ---
            prs_rel = chunk.find(_PRS)
            suc_txt = chunk[len(_SUC):prs_rel] if prs_rel != -1 else chunk[len(_SUC):]
            suction = StageParser._parse_xy_block(suc_txt)

            # --- Pressure surface ---
            if prs_rel != -1:
                after_prs = chunk[prs_rel + len(_PRS):]
                # Stop at the next structural marker (STACKING or end of chunk).
                stop = StageParser._first_index(after_prs, [_STACK])
                pressure = StageParser._parse_xy_block(after_prs[:stop])
            else:
                pressure = []

            # --- Radial station ---
            stack_rel = chunk.find(_STACK)
            r = (StageParser._parse_first_rgrid(chunk[stack_rel:])
                 if stack_rel != -1 else None)

            sections.append({'suction': suction, 'pressure': pressure, 'r': r})
        return sections

    @staticmethod
    def _is_overshoot(sec):
        """True if any (x,y) point in either surface exceeds the normalised
        chord bounding box [-2,2]x[-2,2] (profiles nominally live in
        [0,1] x [-0.5,0.5]). Indicates a corrupted/garbage STAGEN section."""
        for surf in ('suction', 'pressure'):
            for x, y in sec.get(surf, []):
                if abs(x) > _MAX_ABS_X or abs(y) > _MAX_ABS_Y:
                    return True
        return False

    @staticmethod
    def _segments_intersect(p1, p2, p3, p4):
        """True if segment p1-p2 crosses segment p3-p4 (2D, proper crossing)."""
        def cross(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

        d1 = cross(p3, p4, p1)
        d2 = cross(p3, p4, p2)
        d3 = cross(p1, p2, p3)
        d4 = cross(p1, p2, p4)

        if ((d1 > 0 > d2) or (d1 < 0 < d2)) and ((d3 > 0 > d4) or (d3 < 0 < d4)):
            return True
        return False

    @staticmethod
    def _is_self_intersecting(sec):
        """Simple segment-pair test: does the suction polyline cross the
        pressure polyline anywhere (excluding shared LE/TE endpoints)?

        O(N*M) brute-force over consecutive-point segments; profile sections
        have only a few dozen points so this is cheap.
        """
        suction = sec.get('suction', [])
        pressure = sec.get('pressure', [])
        if len(suction) < 2 or len(pressure) < 2:
            return False

        suc_segs = list(zip(suction[:-1], suction[1:]))
        prs_segs = list(zip(pressure[:-1], pressure[1:]))

        # Skip the first and last segment of each surface — these meet at the
        # shared LE/TE points and a "touch" there is not a real crossing.
        for i, (a, b) in enumerate(suc_segs):
            if i == 0 or i == len(suc_segs) - 1:
                continue
            for j, (c, d) in enumerate(prs_segs):
                if j == 0 or j == len(prs_segs) - 1:
                    continue
                if StageParser._segments_intersect(a, b, c, d):
                    return True
        return False

    @staticmethod
    def _repair_degenerate(sections):
        """Replace degenerate sections by interpolation/neighbour-copy.

        A section is degenerate if ANY of the following hold:
          - either surface has < _MIN_PTS points (point-count check), or
          - either surface contains a coordinate outside the normalised
            chord bounding box (overshoot check, _is_overshoot), or
          - the suction and pressure polylines cross each other
            (self-intersection check, _is_self_intersecting).

        Works in-place.  Repair is by nearest valid neighbour (copy); if no
        valid neighbour exists, the section is left as-is.  Prints a warning
        to stderr for each repaired section, identifying which check failed.
        """
        n = len(sections)

        def _is_degenerate(sec):
            reasons = []
            if (len(sec['suction']) < _MIN_PTS
                    or len(sec['pressure']) < _MIN_PTS):
                reasons.append(
                    f"point-count (suc={len(sec['suction'])}, "
                    f"prs={len(sec['pressure'])}, min={_MIN_PTS})")
            if StageParser._is_overshoot(sec):
                reasons.append(
                    f"overshoot (|x| or |y| > {_MAX_ABS_X})")
            if StageParser._is_self_intersecting(sec):
                reasons.append("self-intersection (suction/pressure cross)")
            return reasons

        for idx in range(n):
            sec = sections[idx]
            reasons = _is_degenerate(sec)
            if not reasons:
                continue  # healthy

            print(
                f"StageParser WARNING: section {idx} is degenerate -- "
                f"{'; '.join(reasons)}. Replacing by interpolation."
            )

            # Find nearest valid (non-degenerate by ALL checks) neighbours.
            prev_ok = next((j for j in range(idx - 1, -1, -1)
                            if not _is_degenerate(sections[j])), None)
            next_ok = next((j for j in range(idx + 1, n)
                            if not _is_degenerate(sections[j])), None)

            if prev_ok is None and next_ok is None:
                print(
                    f"StageParser WARNING: no valid neighbour found for section {idx}."
                )
                continue

            if prev_ok is None:
                donor = sections[next_ok]
            elif next_ok is None:
                donor = sections[prev_ok]
            else:
                # Copy the closer neighbour (index distance).
                donor = (sections[prev_ok]
                         if (idx - prev_ok) <= (next_ok - idx)
                         else sections[next_ok])

            sections[idx]['suction']  = list(donor['suction'])
            sections[idx]['pressure'] = list(donor['pressure'])
            if sections[idx]['r'] is None:
                sections[idx]['r'] = donor['r']

    @staticmethod
    def _group_into_rows(sections, n_sections):
        """Group consecutive sections into blade rows.

        If n_sections is given, chunk in fixed blocks.  Otherwise start a new
        row whenever the radius drops (tip -> next hub).
        """
        if n_sections:
            return [sections[i:i + n_sections]
                    for i in range(0, len(sections), n_sections)]

        rows, current, prev_r = [], [], None
        for sec in sections:
            r = sec['r']
            if (prev_r is not None and r is not None and r < prev_r - 1e-4):
                rows.append(current)
                current = []
            current.append(sec)
            prev_r = r
        if current:
            rows.append(current)
        return rows

    # In StageParser._assemble_row() — add machine_type parameter and flip logic
    @staticmethod
    def _assemble_row(secs, machine_type='turbine'):
        """Build a blade-row dict from its list of section dicts.

        For a compressor, stagen.out writes x increasing in the direction
        OPPOSITE to the engine flow (TE at low x, LE at high x). Profiles are
        normalised to unit axial chord at this point (metric chords arrive later
        via MeangenParser.merge()), so the reflection is x' = 1 - x.
        For a turbine the orientation is already correct; no flip is applied.
        """
        suction = [s['suction'] for s in secs]
        pressure = [s['pressure'] for s in secs]

        if machine_type == 'compressor':
            # Reflect x about mid-chord: x' = 1 - x (profiles are normalised here).
            suction = [[(1.0 - x, y) for x, y in sec] for sec in suction]
            pressure = [[(1.0 - x, y) for x, y in sec] for sec in pressure]

        r_sections = StageParser._fill_none([s['r'] for s in secs])

        r_hub, r_tip = r_sections[0], r_sections[-1]
        span = (r_tip - r_hub) if r_tip != r_hub else 1.0
        span_fractions = [(r - r_hub) / span for r in r_sections]

        n = len(secs)
        return {
            'suction': suction,
            'pressure': pressure,
            'r_sections': r_sections,
            'span_fractions': span_fractions,
            'chords': [1.0] * n,  # normalised; merge() -> metric
            'pitch_angles': [0.0] * n,  # placeholder; merge() -> stagger
            'n_blades': 0,  # placeholder; merge() -> real count
        }

    @staticmethod
    def _pair_into_stages(row_dicts, row_order):
        """Pair consecutive blade rows into stages, labelled by row_order."""
        stages = []
        for s in range(0, len(row_dicts) - 1, 2):
            lbl0, lbl1 = row_order[s], row_order[s + 1]
            stages.append({
                lbl0:         row_dicts[s],
                lbl1:         row_dicts[s + 1],
                '_row_order': [lbl0, lbl1],
            })
        return stages

    # ------------------------------------------------------------------
    # Low-level parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_xy_block(text):
        """Extract (x, y) pairs from 'idx  x  y' (or 'x  y') numbered lines."""
        pts = []
        for line in text.splitlines():
            parts = line.split()
            try:
                if len(parts) == 3:
                    _, x, y = parts
                elif len(parts) == 2:
                    x, y = parts
                else:
                    continue
                pts.append((float(x), float(y)))
            except ValueError:
                continue
        return pts

    @staticmethod
    def _parse_first_rgrid(text):
        """Return the first RGRID value from a 'J , XGRID,RGRID  n  x  r' block."""
        m = re.search(rf'XGRID,RGRID\s+\d+\s+{_NUM}\s+({_NUM})', text)
        return float(m.group(1)) if m else None

    @staticmethod
    def _first_index(text, markers):
        """Lowest find() index among `markers`, or len(text) if none present."""
        found = [text.find(mk) for mk in markers]
        found = [i for i in found if i != -1]
        return min(found) if found else len(text)

    @staticmethod
    def _fill_none(lst):
        """Replace None radii by linear interpolation from known neighbours."""
        if not lst:
            return lst
        result = list(lst)
        first_val = next((v for v in result if v is not None), 0.18)
        last_val  = next((v for v in reversed(result) if v is not None), 0.30)
        n = len(result)
        for i in range(n):
            if result[i] is None:
                result[i] = first_val + (last_val - first_val) * i / max(n - 1, 1)
        return result


# ---------------------------------------------------------------------------
# Module-level diagnostic — importable, no class instance needed
# ---------------------------------------------------------------------------

def validate_stage_data(stage_data):
    """Diagnostic sanity-check on parsed/merged per-stage geometry dicts.

    Plain module-level function (NOT a StageParser method) so it can be
    imported directly and called from Turbomachine._build_stage_data_from()
    without going through the ParaPy class.

    Checks, per stage and per row ('rotor', 'stator'):
      1. r_sections has >= 2 entries.
      2. hub radius (r_sections[0]) < tip radius (r_sections[-1]).
      3. x-coordinates of each blade surface (suction/pressure) are
         monotonically increasing within every section.
      4. (via StageParser._is_overshoot / _is_self_intersecting) flags any
         section whose profile points fall outside the normalised chord
         bounding box, or whose suction/pressure surfaces cross.

    Degenerate findings are printed with a clear, identifiable message;
    nothing is mutated and nothing raises -- this is read-only diagnostics.

    Parameters
    ----------
    stage_data : list[dict]
        Output of Turbomachine._build_stage_data_from() / MeangenParser.merge().

    Returns
    -------
    bool
        True if no issues were found, False if any check failed.
    """
    ok = True

    for stage_idx, stage in enumerate(stage_data):
        row_order = stage.get('_row_order', ['rotor', 'stator'])
        for row_name in row_order:
            row = stage.get(row_name)
            if row is None:
                print(f"WARNING: [validate_stage_data] stage {stage_idx} '{row_name}': "
                      f"row missing from stage dict.")
                ok = False
                continue

            label = f"stage {stage_idx} {row_name}"
            r_sections = row.get('r_sections', [])

            # 1. r_sections length
            if len(r_sections) < 2:
                print(f"WARNING: [validate_stage_data] {label}: r_sections has "
                      f"{len(r_sections)} entries (need >= 2).")
                ok = False
                continue  # remaining radius checks need >=2 entries

            # 2. hub < tip
            r_hub, r_tip = r_sections[0], r_sections[-1]
            if not (r_hub < r_tip):
                print(f"WARNING: [validate_stage_data] {label}: hub radius "
                      f"({r_hub:.5f} m) is not < tip radius ({r_tip:.5f} m).")
                ok = False

            # 3. x-monotonicity per section, per surface
            for surf_name in ('suction', 'pressure'):
                sections = row.get(surf_name, [])
                for sec_idx, pts in enumerate(sections):
                    xs = [p[0] for p in pts]
                    if any(xs[i + 1] < xs[i] for i in range(len(xs) - 1)):
                        print(f"WARNING: [validate_stage_data] {label} {surf_name} "
                              f"section {sec_idx}: x-coordinates are not "
                              f"monotonically increasing.")
                        ok = False

            # 4. overshoot / self-intersection, per section
            suction = row.get('suction', [])
            pressure = row.get('pressure', [])
            n_sec = max(len(suction), len(pressure))
            for sec_idx in range(n_sec):
                sec = {
                    'suction':  suction[sec_idx]  if sec_idx < len(suction)  else [],
                    'pressure': pressure[sec_idx] if sec_idx < len(pressure) else [],
                }
                if StageParser._is_overshoot(sec):
                    print(f"ERROR: [validate_stage_data] {label} section {sec_idx}: "
                          f"profile point exceeds bounding box "
                          f"(|x| or |y| > {_MAX_ABS_X}) -- likely degenerate "
                          f"STAGEN output.", file=sys.stderr)
                    ok = False
                if StageParser._is_self_intersecting(sec):
                    print(f"ERROR: [validate_stage_data] {label} section {sec_idx}: "
                          f"suction and pressure surfaces appear to cross "
                          f"(self-intersecting profile).", file=sys.stderr)
                    ok = False

    return ok


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    from pathlib import Path
    import sys

    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        path = Path(__file__).resolve().parents[4] / "softwares" / "Multall" / "DesignExample" / "stagen.out"

    stages = StageParser.parse(path)
    print(f"Parsed {len(stages)} stage(s)")
    for si, st in enumerate(stages):
        for row in st['_row_order']:
            d = st[row]
            print(f"  Stage {si+1} {row}: {len(d['suction'])} sections, "
                  f"suc_pts/sec={[len(s) for s in d['suction']]}, "
                  f"prs_pts/sec={[len(s) for s in d['pressure']]}, "
                  f"r={[round(r, 4) for r in d['r_sections']]}")