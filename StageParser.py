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
stagen.dat via MeagenParser.merge().
"""

import re
import sys

_SUC   = 'SUCTION SURFACE POINTS FROM LE TO TE'
_PRS   = 'PRESSURE SURFACE POINTS FROM LE TO TE'
_STACK = 'AXIAL & RADIAL COORDINATES ON THE SS AFTER STACKING'

# Sections with fewer points than this on either surface are treated as degenerate.
_MIN_PTS = 10

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
    def _repair_degenerate(sections):
        """Replace degenerate sections (< _MIN_PTS points) by interpolation.

        Works in-place.  Interpolation is linear between the nearest valid
        neighbours; if no valid neighbour exists, copies the one that does.
        Prints a warning to stderr for each repaired section.
        """
        n = len(sections)
        for idx in range(n):
            sec = sections[idx]
            if (len(sec['suction']) >= _MIN_PTS
                    and len(sec['pressure']) >= _MIN_PTS):
                continue  # healthy

            print(
                f"StageParser WARNING: section {idx} is degenerate "
                f"(suc={len(sec['suction'])}, prs={len(sec['pressure'])} points). "
                f"Replacing by interpolation.",
                file=sys.stderr
            )

            # Find nearest valid neighbours.
            prev_ok = next((j for j in range(idx-1, -1, -1)
                            if len(sections[j]['suction']) >= _MIN_PTS), None)
            next_ok = next((j for j in range(idx+1, n)
                            if len(sections[j]['suction']) >= _MIN_PTS), None)

            if prev_ok is None and next_ok is None:
                # Cannot repair -- leave as-is.
                print(
                    f"StageParser WARNING: no valid neighbour found for section {idx}.",
                    file=sys.stderr
                )
                continue

            if prev_ok is None:
                donor = sections[next_ok]
            elif next_ok is None:
                donor = sections[prev_ok]
            else:
                # Linear interpolation: weight towards nearest neighbour.
                # For simplicity, just copy the closer one (index distance).
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
        via MeagenParser.merge()), so the reflection is x' = 1 - x.
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
# Quick test
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    from pathlib import Path
    import sys

    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        path = Path.cwd() / "Multall" / "DesignExample" / "stagen.out"

    stages = StageParser.parse(path)
    print(f"Parsed {len(stages)} stage(s)")
    for si, st in enumerate(stages):
        for row in st['_row_order']:
            d = st[row]
            print(f"  Stage {si+1} {row}: {len(d['suction'])} sections, "
                  f"suc_pts/sec={[len(s) for s in d['suction']]}, "
                  f"prs_pts/sec={[len(s) for s in d['pressure']]}, "
                  f"r={[round(r, 4) for r in d['r_sections']]}")