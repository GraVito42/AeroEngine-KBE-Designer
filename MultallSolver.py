"""
MultallSolver.py
================
External-solver wrapper for the Multall turbomachinery pipeline.

Pure I/O component — no geometry, no thermodynamics. Instantiated as a @Part
of Turbomachine. Single point of contact with the three Fortran executables:

    meangen.in ──[MEANGEN]──> meangen.out + stagen.dat   (1D meanline design)
    stagen.dat ──[STAGEN] ──> stagen.out + stage_new.dat (blade geometry + mesh)
    stage_new.dat ─[MULTALL]─> flow_out + grid_out        (3D Navier-Stokes CFD)

Two fidelity levels:
  - LOW fidelity (meangen + stagen): exposed as @Attribute `stagen_out_path`,
    runs automatically the first time geometry is needed. Cached by ParaPy.
  - HIGH fidelity (multall): gated behind @action `run_cfd`, never auto-fires.

meangen.in is generated completely from scratch by the module-level function
`write_meangen_in()`. No template file is needed or used. The function lives
at module level (not as a class method) so it can be called from the smoke
test without going through ParaPy's __getattr__, which blocks names starting
with '_'.
"""

import os
import re
import subprocess

from parapy.core import Base, Input, Attribute, action


# ---------------------------------------------------------------------------
# Module-level helpers (callable without a class instance)
# ---------------------------------------------------------------------------

def _generate_tail(n_stages, turbo_typ='C', nosect=3,
                   rotor_t_over_c=0.05, rotor_x_tmax=0.40,
                   stator_t_over_c=0.05, stator_x_tmax=0.50):
    """Generate the meangen.in tail section for n_stages stages.

    Row order in the ANSTK block is machine-type dependent:
      Compressor: ROW 1 = rotor,  ROW 2 = stator
      Turbine:    ROW 1 = stator, ROW 2 = rotor

    Covers:
      - Stage 1 ANSANGL (n)
      - For stages 2..n_stages: IFSAME_ALL (y) + FBLOCK (A) + ANSANGL (n)
      - ANSOUT (Y)
      - ANSTK blocks: stage-1 row-1 defines thickness (N + section lines),
        row-2 reuses (Y); all rows in stages 2..n_stages reuse (Y).

    Parameters
    ----------
    n_stages : int
    turbo_typ : str  'C' or 'T'
    nosect : int  number of spanwise blade sections (default 3: hub/mid/tip)
    rotor_t_over_c : float  rotor max t/c ratio
    rotor_x_tmax   : float  rotor axial location of max thickness (fraction of chord)
    stator_t_over_c : float  stator max t/c ratio
    stator_x_tmax   : float  stator axial location of max thickness
    """
    pad  = ' ' * 23
    lpad = ' ' * 4
    lines = []

    # Stage 1 — ANSANGL
    lines.append(f'n{pad} DO YOU WANT TO CHANGE THE ANGLES FOR THIS STAGE ? "Y" or "N"\n')

    # Stages 2..n_stages
    for _ in range(2, n_stages + 1):
        lines.append(f'y{pad} IFSAME_ALL, SET = "Y" TO REPEAT THE LAST STAGE INPUT TYPE '
                     f'AND VELOCITY TRIANGLES, SET = "C" TO CHANGE INPUT TYPE.\n')
        lines.append(f'A{pad} BLOCKAGE FACTORS, FBLOCK_LE, FBLOCK_TE '
                     f'(ERR/END accepts previous stage values)\n')
        lines.append(f'n{pad} DO YOU WANT TO CHANGE THE ANGLES FOR THIS STAGE ? "Y" or "N"\n')

    # ANSOUT
    lines.append(f'Y{pad} IS OUTPUT REQUESTED FOR ALL BLADE ROWS ?\n')

    # ANSTK — row order: compressor = rotor first; turbine = stator first
    if turbo_typ.upper() == 'C':
        row1_label, row2_label = 'ROTOR ', 'STATOR'
        row1_tk, row1_xtk = rotor_t_over_c,  rotor_x_tmax
        row2_tk, row2_xtk = stator_t_over_c, stator_x_tmax
    else:
        row1_label, row2_label = 'STATOR', 'ROTOR '
        row1_tk, row1_xtk = stator_t_over_c, stator_x_tmax
        row2_tk, row2_xtk = rotor_t_over_c,  rotor_x_tmax

    # Stage 1, row 1 — define thickness per section
    lines.append(f'N     {row1_label} No.  1  SET ANSTK = "N" TO DEFINE NEW BLADE SECTIONS\n')
    for sec in range(1, nosect + 1):
        lines.append(f'{lpad}{row1_tk:8.4f}  {row1_xtk:8.4f}'
                     f'         MAX THICKNESS AND ITS LOCATION FOR '
                     f'{row1_label}  1 SECTION No.  {sec}\n')

    # Stage 1, row 2 — define thickness per section (different from row 1)
    lines.append(f'N     {row2_label} No.   1  SET ANSTK = "N" TO DEFINE NEW BLADE SECTIONS\n')
    for sec in range(1, nosect + 1):
        lines.append(f'{lpad}{row2_tk:8.4f}  {row2_xtk:8.4f}'
                     f'         MAX THICKNESS AND ITS LOCATION FOR '
                     f'{row2_label}   1 SECTION No.  {sec}\n')

    # Stages 2..n_stages — both rows reuse stage-1 sections
    for stg in range(2, n_stages + 1):
        lines.append(f'Y     {row1_label} No.  {stg}  SET ANSTK = "Y" TO USE THE SAME  '
                     f'BLADE SECTIONS AS THE LAST STAGE\n')
        lines.append(f'Y     {row2_label} No.   {stg}  SET ANSTK = "Y" TO USE THE SAME  '
                     f'BLADE SECTIONS AS THE LAST STAGE\n')

    return lines


def write_meangen_in(work_dir, meangen_input):
    """Generate meangen.in completely from scratch and write it to work_dir.

    Standalone module-level function so it can be called from outside the
    class (smoke tests, debugging) without triggering ParaPy's __getattr__,
    which blocks attribute names that start with '_'.

    Line order follows meangen-17.4.f exactly. All values come from the
    meangen_input dict; no template file is needed.

    Parameters
    ----------
    work_dir : str
        Target directory. Created if absent.
    meangen_input : dict
        Keys: turbo_typ, rgas, gamma, poin, toin, n_stages, rpm, mass_flow,
        reaction, flow_coeff, loading_coeff, design_radius, axial_chords,
        row_gap, stage_gap, eta_guess, frac_twist, deviation, incidence,
        rotor_t_over_c, stator_t_over_c, rotor_x_tmax, stator_x_tmax.

    Returns
    -------
    str
        Absolute path to the written meangen.in.
    """
    os.makedirs(work_dir, exist_ok=True)
    d   = meangen_input
    n   = int(d['n_stages'])
    axc = d['axial_chords']
    c0  = axc[0] if len(axc) > 0 else 0.040
    c1  = axc[1] if len(axc) > 1 else 0.040

    # deviation and incidence: accept list [row1, row2] or fall back to scalar
    dev = d.get('deviation', [5.0, 5.0])
    inc = d.get('incidence', [0.0, 0.0])
    dev1, dev2 = (dev[0], dev[1]) if isinstance(dev, (list, tuple)) else (dev, dev)
    inc1, inc2 = (inc[0], inc[1]) if isinstance(inc, (list, tuple)) else (inc, inc)

    lines = []
    w = lines.append

    # machine type and flow type
    w(f"{d['turbo_typ']}                        TURBO_TYP,\"C\" FOR A COMPRESSOR,\"T\" FOR A TURBINE\n")
    w(f"AXI                      FLO_TYP FOR AXIAL OR MIXED FLOW MACHINE\n")
    # gas properties
    w(f"   {d['rgas']:.3f}     {d['gamma']:.3f}     GAS PROPERTOES, RGAS, GAMMA\n")
    # inlet conditions
    w(f"   {d['poin']:.4f}   {d['toin']:.3f}     POIN,  TOIN\n")
    # number of stages
    w(f"   {n}                    NUMBER OF STAGES IN THE MACHINE\n")
    # radius choice: M = mid-span
    w(f"M                        CHOICE OF DESIGN POINT RADIUS, HUB, MID or TIP\n")
    # rotation speed
    w(f"   {d['rpm']:.3f}             ROTATION SPEED, RPM\n")
    # mass flow
    w(f"   {d['mass_flow']:.3f}             MASS FLOW RATE, FLOWIN.\n")
    # velocity triangle input type: A = (reaction, phi, psi)
    w(f"A                        INTYPE, TO CHOOSE THE METHOD OF DEFINING THE VELOCITY TRIANGLES\n")
    w(f"  {d['reaction']:.4f}  {d['flow_coeff']:.4f}  {d['loading_coeff']:.4f}    REACTION, FLOW COEFF., LOADING COEFF.\n")
    # radius definition: A = specify directly
    w(f"A                        RADTYPE, TO CHOOSE THE DESIGN POINT RADIUS\n")
    w(f"       {d['design_radius']:.4f}           THE DESIGN POINT RADIUS\n")
    # blade axial chords
    w(f"       {c0:.4f}   {c1:.4f} BLADE AXIAL CHORDS IN METRES.\n")
    # gaps
    w(f"       {d['row_gap']:.4f}       {d['stage_gap']:.3f} ROW GAP  AND STAGE GAP (fractions)\n")
    # blockage factors (safe small defaults)
    w(f"   0.00000   0.02000     BLOCKAGE FACTORS, FBLOCK_LE,  FBLOCK_TE\n")
    # efficiency guess
    w(f"       {d['eta_guess']:.4f}             GUESS OF THE STAGE ISENTROPIC EFFICIENCY\n")
    # deviation and incidence angles (empirical, per row)
    w(f"   {dev1:.3f}   {dev2:.3f}         ESTIMATE OF THE FIRST AND SECOND ROW DEVIATION ANGLES\n")
    w(f"   {inc1:.3f}   {inc2:.3f}         FIRST AND SECOND ROW INCIDENCE ANGLES\n")
    # blade twist: 1.0 = full free-vortex, 0.0 = prismatic
    frac_twist = d.get('frac_twist', 1.0)
    w(f"   {frac_twist:.5f}               BLADE TWIST OPTION, FRAC_TWIST (1 is free vortex, 0 is without twist)\n")
    # blade rotation: N = no per-section rotation
    w(f"n                        BLADE ROTATION OPTION , Y or N\n")
    # QO angles: 90 = straight blade (no sweep/lean)
    w(f"  90.000  90.000         QO ANGLES AT LE  AND TE OF ROW 1\n")
    w(f"  90.000  90.000         QO ANGLES AT LE  AND TE OF ROW 2\n")

    lines.extend(_generate_tail(
        n_stages        = n,
        turbo_typ       = d['turbo_typ'],
        rotor_t_over_c  = d.get('rotor_t_over_c',  0.05),
        rotor_x_tmax    = d.get('rotor_x_tmax',    0.40),
        stator_t_over_c = d.get('stator_t_over_c', 0.05),
        stator_x_tmax   = d.get('stator_x_tmax',   0.50),
    ))

    out_path = os.path.join(work_dir, 'meangen.in')
    with open(out_path, 'w') as fh:
        fh.writelines(lines)
    print(f"[MultallSolver] meangen.in written to {out_path} ({len(lines)} lines)")
    return out_path

def _repair_stagen_dat(path):
    """Re-insert spaces between fused numbers on MEANGEN's
    'RPM, STATIC PRESSURES THROUGH ROW' lines.

    That line uses an F10.2 field. A 7-integer-digit value (e.g. 1346066.62,
    from high-pressure turbine stages) fills the field exactly, leaving no
    separating space, so adjacent values fuse into one token with two decimal
    points that STAGEN's list-directed read rejects ('Bad real number in item
    1'). Every value on the line has 2 decimals, so a fused boundary is always
    '.dd' followed immediately by a digit or '-' -> inserting a space is safe.
    Only this line type is touched (other lines use wider, un-fused formats).
    """
    marker = 'RPM, STATIC PRESSURES THROUGH ROW'
    with open(path, 'r') as fh:
        lines = fh.readlines()
    changed = False
    for i, line in enumerate(lines):
        if marker in line:
            fixed = re.sub(r'(\.\d\d)(?=[\d-])', r'\1 ', line)
            if fixed != line:
                lines[i], changed = fixed, True
    if changed:
        with open(path, 'w') as fh:
            fh.writelines(lines)
        print(f"[MultallSolver] repaired fused numeric fields in {path}")


# ---------------------------------------------------------------------------
# ParaPy class
# ---------------------------------------------------------------------------

class MultallSolver(Base):
    """Wrapper around the meangen / stagen / multall executables."""

    # ------------------------------------------------------------------
    # Inputs
    # ------------------------------------------------------------------

    work_dir = Input()
    """Per-turbomachine working directory."""

    meangen_exe = Input('meangen-17.4.exe')
    stagen_exe  = Input('stagen-18.1.exe')
    multall_exe = Input('multall-open-20.9.exe')

    meangen_template = Input(None)
    """Kept for backwards compatibility only. meangen.in is now generated
    from scratch; this Input is ignored."""

    meangen_input = Input()
    """dict of meanline-design values produced by Turbomachine."""

    # ------------------------------------------------------------------
    # Output-file paths
    # ------------------------------------------------------------------

    @Attribute
    def run_dir(self):
        """Per-run subdirectory: work_dir / <8-char hash of meangen_input>.

        Embedding the hash in the path means ParaPy's attribute cache naturally
        invalidates when any input parameter changes — no manual folder deletion
        required. Each unique set of inputs gets its own folder; old folders are
        kept on disk for inspection but are never reused incorrectly.
        """
        import hashlib, json
        # Sort keys for deterministic serialisation; round floats to 6 sig-figs
        # so tiny floating-point noise does not produce spurious cache misses.
        def _normalise(v):
            if isinstance(v, float):
                return round(v, 6)
            if isinstance(v, list):
                return [_normalise(i) for i in v]
            return v
        normalised = {k: _normalise(v) for k, v in sorted(self.meangen_input.items())}
        digest = hashlib.sha256(
            json.dumps(normalised, sort_keys=True).encode()
        ).hexdigest()[:8]
        return os.path.join(self.work_dir, digest)

    @Attribute
    def meangen_out_path(self):
        """Absolute path to meangen.out."""
        return os.path.join(self.run_dir, 'meangen.out')

    @Attribute
    def stagen_out_path(self):
        """Absolute path to stagen.out. Accessing this triggers the low-fidelity run."""
        return self._run_low_fidelity()

    @Attribute
    def flow_out_path(self):
        """Absolute path to the Multall flow field output."""
        return os.path.join(self.run_dir, 'flow_out')

    @Attribute
    def stagen_dat_path(self):
        """Absolute path to stagen.dat."""
        return os.path.join(self.run_dir, 'stagen.dat')

    # ------------------------------------------------------------------
    # LOW fidelity
    # ------------------------------------------------------------------

    def _run_low_fidelity(self):
        """Write meangen.in, run MEANGEN and STAGEN. Returns path to stagen.out.

        Uses run_dir (work_dir/<hash>) so each unique meangen_input gets its own
        folder. ParaPy's cache of stagen_out_path is therefore always consistent
        with the actual files on disk — no manual folder deletion needed.
        """
        run_dir = self.run_dir
        os.makedirs(run_dir, exist_ok=True)
        # Resolve exe paths to absolute BEFORE changing cwd in subprocess.
        meangen_abs = os.path.abspath(self.meangen_exe)
        stagen_abs  = os.path.abspath(self.stagen_exe)
        print(f"[MultallSolver] run_dir = {run_dir}")
        write_meangen_in(run_dir, self.meangen_input)
        print("[MultallSolver] running MEANGEN ...")
        self._run_meangen(meangen_abs, cwd=run_dir)
        _repair_stagen_dat(os.path.join(run_dir, 'stagen.dat'))  # <-- add
        print("[MultallSolver] running STAGEN ...")
        self._run_stagen(stagen_abs, cwd=run_dir)
        path = os.path.join(run_dir, 'stagen.out')
        print(f"[MultallSolver] low-fidelity run complete -> {path}")
        return path

    def _run_meangen(self, exe_path=None, cwd=None):
        """Launch MEANGEN. Feeds 'F' on stdin to select file input (meangen.in)."""
        cwd = cwd or self.work_dir
        result = subprocess.run(
            [exe_path or self.meangen_exe],
            cwd=cwd,
            input=b'F\n',
            capture_output=False,   # stream output to console for diagnostics
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"MEANGEN failed with exit code {result.returncode}.\n"
                f"  exe: {exe_path or self.meangen_exe}\n"
                f"  cwd: {cwd}\n"
                f"  Check the console output above for MEANGEN's error message.\n"
                f"  meangen.in is at: {os.path.join(cwd, 'meangen.in')}"
            )

    def _run_stagen(self, exe_path=None, cwd=None):
        """Launch STAGEN. Feeds 'Y' to accept stagen.dat; extra '0.1' lines
        cover the factk fallback for very thick blades (unread lines ignored)."""
        cwd = cwd or self.work_dir
        result = subprocess.run(
            [exe_path or self.stagen_exe],
            cwd=cwd,
            input=b'Y\n' + b'0.1\n' * 32,
            capture_output=False,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"STAGEN failed with exit code {result.returncode}.\n"
                f"  exe: {exe_path or self.stagen_exe}\n"
                f"  cwd: {cwd}"
            )

    # ------------------------------------------------------------------
    # HIGH fidelity
    # ------------------------------------------------------------------

    @action(label='Run Multall CFD')
    def run_cfd(self):
        """GUI button: run the full 3D Multall Navier-Stokes solver (~30 min)."""
        return self._run_high_fidelity()

    def _run_high_fidelity(self):
        """Run MULTALL on the deck produced by STAGEN.

        MULTALL reads a format selector from 'intype' (unit 13); must contain
        'N' for the NEW_READIN format that STAGEN writes. Reads the solver deck
        from stdin (stage_new.dat piped in).
        """
        multall_abs = os.path.abspath(self.multall_exe)
        with open(os.path.join(self.work_dir, 'intype'), 'w') as fh:
            fh.write('N\n')
        with open(os.path.join(self.work_dir, 'stage_new.dat'), 'rb') as fh:
            deck = fh.read()
        subprocess.run(
            [multall_abs],
            cwd=self.work_dir,
            input=deck,
            stderr=subprocess.STDOUT,
            check=True,
        )
        return self.flow_out_path


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    from pathlib import Path

    base_dir      = Path(__file__).resolve().parent
    work_dir_path = base_dir / 'Multall' / 'DesignExample' / 'test_run_c'

    # ------------------------------------------------------------------
    # Part 1 — file generation check only (no .exe calls).
    # Calls the standalone function directly — no ParaPy instantiation needed.
    # ------------------------------------------------------------------
    meangen_input_test = dict(
        turbo_typ='C', rgas=287.15, gamma=1.4, poin=1.0, toin=300.0,
        n_stages=2, rpm=12000.0, mass_flow=20.0,
        reaction=0.5, flow_coeff=0.6, loading_coeff=0.4,
        design_radius=0.35, axial_chords=[0.035, 0.045],
        row_gap=0.25, stage_gap=0.5, eta_guess=0.9,
        frac_twist=1.0,
        deviation=[1.2, 1.2],
        incidence=[-1.0, -1.0],
        rotor_t_over_c=0.05,  rotor_x_tmax=0.40,
        stator_t_over_c=0.05, stator_x_tmax=0.50,
    )

    out = write_meangen_in(str(work_dir_path), meangen_input_test)
    print("=== Part 1: generated meangen.in (no .exe) ===")
    with open(out) as f:
        print(f.read())

    # ------------------------------------------------------------------
    # Part 2 — full pipeline against the real executables (opt-in).
    # ------------------------------------------------------------------
    RUN_CFD = True   # set True to run the full pipeline

    if RUN_CFD:
        exe_dir = base_dir / 'Multall' / 'executables'
        work    = base_dir / 'Multall' / 'smoke_cfd'

        cfd_solver = MultallSolver(
            work_dir    = str(work),
            meangen_exe = str(exe_dir / 'meangen-17.4.exe'),
            stagen_exe  = str(exe_dir / 'stagen-18.1.exe'),
            multall_exe = str(exe_dir / 'multall-open-20.9.exe'),
            meangen_input=dict(
                turbo_typ='C', rgas=287.0, gamma=1.4, poin=2.76, toin=340.0,
                n_stages=1, rpm=13177.0, mass_flow=88.23,
                reaction=0.8023, flow_coeff=0.5633, loading_coeff=0.3954,
                design_radius=0.2337, axial_chords=[0.044, 0.0806],
                row_gap=0.25, stage_gap=0.5, eta_guess=0.9351,
            ),
        )

        print("\n=== Part 2: full pipeline ===")
        stagen_out = cfd_solver.stagen_out_path
        print("stagen.out exists:", os.path.exists(stagen_out))

        print("launching MULTALL ...")
        flow_out = cfd_solver._run_high_fidelity()
        print("flow_out path:", flow_out)
        print("flow_out exists:", os.path.exists(flow_out))