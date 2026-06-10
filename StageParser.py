"""
StageParser.py
==============
Parses stagen.out into the per-section blade-surface point clouds that the
Stage / Blade classes consume.

stagen.out layout (repeats once per blade SECTION, hub -> tip, row after row):
    SUCTION SURFACE POINTS FROM LE TO TE.        -> "idx  x  y" lines
    PRESSURE SURFACE POINTS FROM LE TO TE.       -> "idx  x  y" lines
    AXIAL & RADIAL COORDINATES ON THE SS AFTER STACKING
        J , XGRID,RGRID  n  <x>  <r>             -> radial station of the section
The surface points are normalised to unit axial chord (XCHORD ~= 1.0); the
metric axial chord and the blade count are NOT in stagen.out — they come from
stagen.dat via MeagenParser.merge().

Important: stagen.out has NO "STAGE No, ROW No, No. BLADES" header (that string
is not emitted to the file), so rows cannot be delimited by a blade-count line.
Instead, blade rows are detected by the radius RESETTING to the hub between the
last section of one row (tip) and the first section of the next (hub).

Output: list of stage dicts, one per stage:
    {
      'rotor':  { 'suction', 'pressure', 'r_sections', 'span_fractions',
                  'chords', 'pitch_angles', 'n_blades' },
      'stator': { ... same keys ... },
      '_row_order': ['rotor', 'stator'],   # physical order, used by merge()
    }
Placeholders filled by MeagenParser.merge(): chords (normalised 1.0 -> metric),
pitch_angles (0.0 -> stagger), n_blades (0 -> real count).
"""

import re


_SUC   = 'SUCTION SURFACE POINTS FROM LE TO TE'
_PRS   = 'PRESSURE SURFACE POINTS FROM LE TO TE'
_STACK = 'AXIAL & RADIAL COORDINATES ON THE SS AFTER STACKING'
_PRS_END = 'AXIAL,TANGENTIAL AND RADIAL COORDINATES ON THE STREAM'

# Fortran real/int token (incl. E-notation).
_NUM = r'[-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?'


class StageParser:
    """Parser for stagen.out files."""

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @staticmethod
    def parse(filepath, row_order=None, n_sections=None):
        """Parse stagen.out and return a list of stage dicts.

        Parameters
        ----------
        filepath : str
            Path to stagen.out.
        row_order : list[str] or None
            Physical 'rotor'/'stator' label of each blade row in file order,
            e.g. ['rotor', 'stator'] for a compressor stage or
            ['stator', 'rotor'] for a turbine stage. If None, alternating
            rotor/stator starting with rotor is assumed (compressor default).
        n_sections : int or None
            Sections per blade row (e.g. 3 for hub/mid/tip). If None, rows are
            auto-detected by the radius reset between tip and the next hub.

        Returns
        -------
        list[dict]
            One dict per stage, each with 'rotor', 'stator' and '_row_order'.
        """
        with open(filepath, 'r') as fh:
            text = fh.read()

        sections = StageParser._parse_sections(text)
        if not sections:
            raise ValueError(
                "StageParser: no 'SUCTION SURFACE POINTS' blocks found. "
                "Is this a stagen.out file?"
            )

        section_groups = StageParser._group_into_rows(sections, n_sections)
        row_dicts = [StageParser._assemble_row(g) for g in section_groups]

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

        Each: {'suction': [(x,y)...], 'pressure': [(x,y)...], 'r': float|None}.
        """
        suc_positions = [m.start() for m in re.finditer(re.escape(_SUC), text)]
        sections = []
        for i, sp in enumerate(suc_positions):
            end = suc_positions[i + 1] if i + 1 < len(suc_positions) else len(text)
            chunk = text[sp:end]

            prs_rel = chunk.find(_PRS)
            suc_txt = chunk[len(_SUC):prs_rel] if prs_rel != -1 else chunk[len(_SUC):]
            suction = StageParser._parse_xy_block(suc_txt)

            if prs_rel != -1:
                after = chunk[prs_rel + len(_PRS):]
                stop = StageParser._first_index(after, [_PRS_END, _STACK])
                pressure = StageParser._parse_xy_block(after[:stop])
            else:
                pressure = []

            stack_rel = chunk.find(_STACK)
            r = (StageParser._parse_first_rgrid(chunk[stack_rel:])
                 if stack_rel != -1 else None)

            sections.append({'suction': suction, 'pressure': pressure, 'r': r})
        return sections

    @staticmethod
    def _group_into_rows(sections, n_sections):
        """Group consecutive sections into blade rows.

        If n_sections is given, chunk in fixed blocks of that size. Otherwise
        start a new row whenever the radius drops (tip -> next hub).
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

    @staticmethod
    def _assemble_row(secs):
        """Build a blade-row dict from its list of section dicts."""
        suction    = [s['suction'] for s in secs]
        pressure   = [s['pressure'] for s in secs]
        r_sections = StageParser._fill_none([s['r'] for s in secs])

        r_hub, r_tip = r_sections[0], r_sections[-1]
        span = (r_tip - r_hub) if r_tip != r_hub else 1.0
        span_fractions = [(r - r_hub) / span for r in r_sections]

        n = len(secs)
        return {
            'suction':        suction,
            'pressure':       pressure,
            'r_sections':     r_sections,
            'span_fractions': span_fractions,
            'chords':         [1.0] * n,   # normalised; merge() -> metric
            'pitch_angles':   [0.0] * n,   # placeholder; merge() -> stagger
            'n_blades':       0,           # placeholder; merge() -> real count
        }

    @staticmethod
    def _pair_into_stages(row_dicts, row_order):
        """Pair consecutive blade rows into stages, labelled by row_order."""
        stages = []
        for s in range(0, len(row_dicts) - 1, 2):
            lbl0, lbl1 = row_order[s], row_order[s + 1]
            stages.append({
                lbl0:        row_dicts[s],
                lbl1:        row_dicts[s + 1],
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

    base_dir = Path.cwd()

    path = base_dir / "Multall" / "DesignExample" / "stagen.out"

    stages = StageParser.parse(path)
    print(f"Parsed {len(stages)} stage(s)")
    for si, st in enumerate(stages):
        for row in st['_row_order']:
            d = st[row]
            print(f"  Stage {si+1} {row}: {len(d['suction'])} sections, "
                  f"suc_pts/sec={[len(s) for s in d['suction']]}, "
                  f"r={[round(r, 4) for r in d['r_sections']]}, "
                  f"span_frac={[round(f, 3) for f in d['span_fractions']]}")