"""
MeangenParser.py
===============
Parses stagen.dat — the MEANGEN -> STAGEN hand-off file — to extract the
per-blade-row, per-section meanline geometry that stagen.out does NOT carry.

Why stagen.dat and not meangen.out:
  MEANGEN writes two things. `meangen.out` is only an ECHO of the input deck
  (gas props, RPM, coefficients, ...) and contains no per-row radii, blade
  counts or metal angles. The verbose design summary that older parsers looked
  for ("FIRST BLADE TIP RADIUS =", "... INLET AND EXIT ANGLES", etc.) is sent
  by MEANGEN to the console (Fortran WRITE(6,*)), so it never reaches a file
  unless stdout is captured. The authoritative, machine-readable geometry is in
  `stagen.dat`, which MEANGEN writes for STAGEN.

What this parser extracts (per blade row, in file order — rotor first for a
compressor stage, stator first for a turbine stage):
  - row_type   : 'rotor' / 'stator'   (from BLADE ROW TYPE = R / S)
  - n_blades   : int                  (NUMBER OF BLADES IN ROW)
  - per section (hub -> tip):
        chords       [m]   axial chord = TE_x - LE_x  (LE/TE COORDINATES line)
        r_sections   [m]   leading-edge radius (3rd value on the LE/TE line)
        pitch_angles [deg] stagger = mean(BETUP, BETDWN)  (XCUP,XCDWN,... line)
        betup/betdwn [deg] raw inlet/exit metal angles (kept for reference)

Also exposes NOWS (number of rows) and N SECTIONS via parse_structure().

merge():
  MeangenParser.merge(stages, meagen_rows) writes n_blades, the metric chords
  and the stagger angles into the Stage dicts produced by StageParser (which
  only knows the normalised profile shapes). Rows are matched by their physical
  row_type, so it works for both compressor (rotor-first) and turbine
  (stator-first) stage layouts.

stagen.dat is fixed free-format; values are the leading tokens of each line and
the trailing text is a comment, so this parser keys on those comment strings.
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


# Matches a Fortran real/int token, including E-notation (e.g. -2.31E-02).
_NUM = r'[-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?'


class MeangenParser:
    """Parser for stagen.dat (MEANGEN output / STAGEN input)."""

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @staticmethod
    def parse(filepath):
        """Parse stagen.dat and return a list of blade-row dicts in file order.

        Parameters
        ----------
        filepath : str
            Path to stagen.dat.

        Returns
        -------
        list[dict]
            One dict per blade row. Keys: 'row_type', 'n_blades', 'chords',
            'r_sections', 'pitch_angles', 'betup', 'betdwn'.
        """
        with open(filepath, 'r') as fh:
            text = fh.read()
        return MeangenParser._extract_rows(text)

    @staticmethod
    def parse_structure(filepath):
        """Return (nows, n_sections) from the 'NOWS, N SECTIONS' line."""
        with open(filepath, 'r') as fh:
            text = fh.read()
        return MeangenParser._extract_structure(text)

    @staticmethod
    def merge(stages, meagen_rows, row_order=None):
        """Enrich StageParser's stage dicts with stagen.dat data.

        For each blade row found in stagen.dat, the matching row in `stages`
        (by physical row_type) gets its n_blades, metric chords and stagger
        (pitch) angles overwritten. r_sections from StageParser (taken from the
        stacked stagen.out geometry) are kept.

        Parameters
        ----------
        stages : list[dict]
            Output of StageParser.parse(); each has 'rotor' and 'stator'.
        meagen_rows : list[dict]
            Output of MeangenParser.parse(), in physical file order.
        row_order : list[str] or None
            Optional explicit order; if None it is taken from the meagen_rows'
            own row_type fields (authoritative).

        Returns
        -------
        list[dict]
            The same `stages` list, mutated in place.
        """
        # Flatten the stage dicts into (stage_index, slot) addresses, in the
        # physical order the rows appear in the machine.
        flat = []
        for st in stages:
            order = st.get('_row_order', ['rotor', 'stator'])
            for slot in order:
                flat.append(st[slot])

        if len(flat) != len(meagen_rows):
            raise ValueError(
                f"MeangenParser.merge: {len(flat)} rows in stages but "
                f"{len(meagen_rows)} rows in stagen.dat — counts must match."
            )

        for row, mrow in zip(flat, meagen_rows):
            # Overwrite the radii from stagen.dat to correct stagen.out's collapsed mid-span radial coordinates
            row['r_sections'] = mrow['r_sections']
            
            # Recalculate span fractions using the correct radii to avoid zero-span collapse
            r_hub, r_tip = row['r_sections'][0], row['r_sections'][-1]
            span = (r_tip - r_hub) if r_tip != r_hub else 1.0
            row['span_fractions'] = [(r - r_hub) / span for r in row['r_sections']]
            
            n_sec = len(row['r_sections'])
            row['n_blades'] = mrow['n_blades']
            # chords / pitch_angles are per section; pad or trim to n_sec.
            row['chords'] = MeangenParser._fit(mrow['chords'], n_sec)
            row['pitch_angles'] = MeangenParser._fit(mrow['pitch_angles'], n_sec)

        return stages

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_structure(text):
        """Read NOWS and N SECTIONS from the header line."""
        m = re.search(rf'({_NUM})\s+({_NUM})\s+NOWS,\s*N\s*SECTIONS', text)
        if not m:
            return (None, None)
        return (int(float(m.group(1))), int(float(m.group(2))))

    @staticmethod
    def _extract_rows(text):
        """Split stagen.dat into blade-row blocks and parse each."""
        row_marker = 'STARTING DATA FOR A NEW BLADE ROW'
        positions = [m.start() for m in re.finditer(re.escape(row_marker), text)]
        if not positions:
            raise ValueError(
                "MeagenParser: no 'STARTING DATA FOR A NEW BLADE ROW' blocks "
                "found. Is this a stagen.dat file?"
            )

        rows = []
        for bi, start in enumerate(positions):
            end = positions[bi + 1] if bi + 1 < len(positions) else len(text)
            rows.append(MeangenParser._parse_row_block(text[start:end]))
        return rows

    @staticmethod
    def _parse_row_block(block):
        """Extract one blade row's data from its text slice."""
        # Row type: R -> rotor, S -> stator.
        tm = re.search(r'BLADE ROW\s+TYPE\s*=\s*([A-Za-z])', block)
        type_letter = tm.group(1).upper() if tm else 'R'
        row_type = 'rotor' if type_letter == 'R' else 'stator'

        # Blade count.
        bm = re.search(rf'({_NUM})\s+NUMBER OF BLADES IN ROW', block)
        n_blades = int(float(bm.group(1))) if bm else 0

        # Per-section metal angles: 4 leading tokens of the XCUP,... line are
        # XCUP, XCDWN, BETUP, BETDWN — we want the 3rd and 4th.
        angle_lines = re.findall(
            rf'({_NUM})\s+({_NUM})\s+({_NUM})\s+({_NUM})\s+'
            r'XCUP,\s*XCDWN,\s*BETUP,\s*BETDWN',
            block
        )
        betup = [float(a[2]) for a in angle_lines]
        betdwn = [float(a[3]) for a in angle_lines]

        # Per-section LE/TE coordinates: LE_x, TE_x, LE_r, TE_r.
        le_te_lines = re.findall(
            rf'({_NUM})\s+({_NUM})\s+({_NUM})\s+({_NUM})\s+'
            r'LEADING AND TRAILING EDGE COORDINATES',
            block
        )
        chords = [float(c[1]) - float(c[0]) for c in le_te_lines]   # TE_x - LE_x
        r_sections = [float(c[2]) for c in le_te_lines]             # LE_r

        # Stagger per section = mean of inlet/exit metal angles.
        # TODO (verify in GUI): sign convention vs Blade.pitch_angles twist.
        pitch_angles = [MeangenParser._stagger(u, d)
                        for u, d in zip(betup, betdwn)]

        return {
            'row_type':     row_type,
            'n_blades':     n_blades,
            'chords':       chords,
            'r_sections':   r_sections,
            'pitch_angles': pitch_angles,
            'betup':        betup,
            'betdwn':       betdwn,
        }

    @staticmethod
    def _stagger(betup_deg, betdwn_deg):
        """Stagger (pitch) angle [deg] = mean of inlet and exit metal angles."""
        return 0.5 * (betup_deg + betdwn_deg)

    @staticmethod
    def _fit(values, n):
        """Pad/trim `values` to length n (repeat last value if too short)."""
        if not values:
            return [0.0] * n
        if len(values) >= n:
            return list(values[:n])
        return list(values) + [values[-1]] * (n - len(values))


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    from pathlib import Path

    path = Path(__file__).resolve().parents[4] / "softwares" / "Multall" / "DesignExample" / "stagen.dat"

    nows, n_sec = MeangenParser.parse_structure(path)
    rows = MeangenParser.parse(path)
    print(f"NOWS={nows}, N_SECTIONS={n_sec}, parsed {len(rows)} blade row(s)")
    for i, r in enumerate(rows):
        print(f"  Row {i+1} [{r['row_type']}]: n_blades={r['n_blades']}, "
              f"chords={[round(c, 4) for c in r['chords']]} m, "
              f"r={[round(x, 4) for x in r['r_sections']]} m, "
              f"stagger={[round(p, 2) for p in r['pitch_angles']]} deg")