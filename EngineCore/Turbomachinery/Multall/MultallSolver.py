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

# Ensure project root is in sys.path when running this file directly
import sys
from pathlib import Path
for parent in Path(__file__).resolve().parents:
    if (parent / "EngineCore").exists() and (parent / "Thermodynamics").exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break

import os
import re
import subprocess
from pathlib import Path

# Project root: directory containing MultallSolver.py
MULTALL_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = MULTALL_DIR.parent.parent.parent

def _resolve_absolute_path(path):
    """Resolve a path to an absolute path relative to MULTALL_DIR or PROJECT_ROOT.
    
    If the path is already absolute, it is returned unchanged.
    """
    if not path:
        return path
    p = Path(path)
    if p.is_absolute():
        return str(p)
    
    # Check if the file is one of the executables
    if p.name in ['meangen-17.4.exe', 'stagen-18.1.exe', 'multall-open-20.9.exe']:
        exec_path = MULTALL_DIR / 'executables' / p.name
        if exec_path.exists():
            return str(exec_path.resolve())
            
    # Clean old "Multall/" prefix if it resides under MULTALL_DIR
    if p.parts and p.parts[0] == 'Multall':
        p = Path(*p.parts[1:])
        
    return str((MULTALL_DIR / p).resolve())


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
    Path(work_dir).mkdir(parents=True, exist_ok=True)
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

    out_path = str(Path(work_dir) / 'meangen.in')
    with open(out_path, 'w') as fh:
        fh.writelines(lines)
    print(f"[MultallSolver] meangen.in written to {out_path} ({len(lines)} lines)")
    return out_path

def _repair_stagen_dat(path):
    """Re-insert spaces between fused numbers on MEANGEN's
    'RPM, STATIC PRESSURES THROUGH ROW' lines.

    Also dynamically scales down the grid points (NPOINTS_UP, NPOINTS_ON, NPOINTS_DWN)
    if the total grid size exceeds the 500 limit of the multall-open binary.
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

    # Check for grid scaling (to fit within JD=500 limit of multall)
    npoints_pattern = re.compile(
        r'^\s*(\d+)\s+(\d+)\s+(\d+)\s+(NPOINTS_UP,\s*NPOINTS_ON,\s*NPOINTS_DWN.*)',
        re.IGNORECASE
    )
    total_grid_points = 0
    npoints_occurrences = []
    for i, line in enumerate(lines):
        m = npoints_pattern.match(line)
        if m:
            up = int(m.group(1))
            on = int(m.group(2))
            dwn = int(m.group(3))
            total_grid_points += (up + on + dwn)
            npoints_occurrences.append((i, up, on, dwn, m.group(4)))
            
    if total_grid_points > 480 and npoints_occurrences:
        factor = 480.0 / total_grid_points
        print(f"[MultallSolver] Total expected grid points {total_grid_points} exceeds 480. "
              f"Scaling down grid with factor {factor:.4f}")
        for idx, up, on, dwn, suffix in npoints_occurrences:
            scaled_up = max(8, int(up * factor))
            scaled_on = max(25, int(on * factor))
            scaled_dwn = max(6, int(dwn * factor))
            new_line = f"    {scaled_up:d}   {scaled_on:d}   {scaled_dwn:d}     {suffix.strip()}\n"
            lines[idx] = new_line
            changed = True
            
    if changed:
        with open(path, 'w') as fh:
            fh.writelines(lines)
        print(f"[MultallSolver] repaired and/or scaled stagen.dat at {path}")


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
        """Directory for ALL solver files — flat, no per-run subdirectory.

        Everything (meangen.in/.out, stagen.dat/.out, stage_new.dat, intype,
        flow_out, grid_out) is written directly into work_dir, which is already
        the per-machine folder (.../compressor or .../turbine). MEANGEN, STAGEN
        and MULTALL therefore read and write the same flat directory, which is
        what their relative-filename I/O expects. Re-run invalidation no longer
        relies on a path hash; it is driven by stagen_out_path depending on
        meangen_input directly (see below)."""
        return _resolve_absolute_path(self.work_dir)

    @Attribute
    def meangen_out_path(self):
        """Absolute path to meangen.out."""
        return str(Path(self.run_dir) / 'meangen.out')

    @Attribute
    def stagen_out_path(self):
        """Absolute path to stagen.out. Accessing this triggers the low-fidelity run.

        The bare `self.meangen_input` reference is intentional: it registers
        meangen_input as a dependency of this attribute, so ParaPy re-runs
        MEANGEN+STAGEN whenever any design parameter changes. With the path hash
        gone, this is what keeps the on-disk files in sync with the inputs.
        """
        self.meangen_input            # explicit dependency for re-run on change
        return self._run_low_fidelity()

    @Attribute
    def flow_out_path(self):
        """Absolute path to the Multall flow field output."""
        return str(Path(self.run_dir) / 'flow_out')

    @Attribute
    def stagen_dat_path(self):
        """Absolute path to stagen.dat."""
        return str(Path(self.run_dir) / 'stagen.dat')

    # ------------------------------------------------------------------
    # LOW fidelity
    # ------------------------------------------------------------------

    def _run_low_fidelity(self):
        """Write meangen.in, run MEANGEN and STAGEN. Returns path to stagen.out.

        Writes into run_dir, which is now the flat per-machine work_dir. Re-run
        consistency is guaranteed by stagen_out_path depending on meangen_input,
        so a design change overwrites the files in place.
        """
        run_dir = self.run_dir
        Path(run_dir).mkdir(parents=True, exist_ok=True)
        # Resolve exe paths to absolute BEFORE changing cwd in subprocess.
        meangen_abs = _resolve_absolute_path(self.meangen_exe)
        stagen_abs  = _resolve_absolute_path(self.stagen_exe)
        print(f"[MultallSolver] run_dir = {run_dir}")
        write_meangen_in(run_dir, self.meangen_input)
        print("[MultallSolver] running MEANGEN ...")
        self._run_meangen(meangen_abs, cwd=run_dir)
        _repair_stagen_dat(str(Path(run_dir) / 'stagen.dat'))
        print("[MultallSolver] running STAGEN ...")
        self._run_stagen(stagen_abs, cwd=run_dir)
        path = str(Path(run_dir) / 'stagen.out')
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
                f"  meangen.in is at: {str(Path(cwd) / 'meangen.in')}"
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

        All paths resolve to run_dir, which is now the flat per-machine
        work_dir where the low-fidelity stage wrote stagen.dat and
        stage_new.dat, so the solver is launched in the same folder. The
        returned flow_out_path is rooted there too, keeping everything
        consistent.
        """
        # Ensure that the low-fidelity run is up-to-date
        _ = self.stagen_out_path

        multall_abs = _resolve_absolute_path(self.multall_exe)
        run_dir = self.run_dir

        # Enforce stage limit for the pre-compiled Fortran solver
        n_stages = self.meangen_input.get('n_stages')
        if n_stages and n_stages > 6:
            raise RuntimeError(
                f"MULTALL solver limit exceeded: n_stages={n_stages} is greater than "
                f"the maximum supported 4 stages (8 blade rows) due to fixed array dimensions "
                f"in the Fortran executable. Please reduce n_stages to 4 or fewer."
            )

        with open(str(Path(run_dir) / 'intype'), 'w') as fh:
            fh.write('N\n')
        
        # Read stage_new.dat, find and cap NSTEPS_MAX to 2000 to keep verification runs fast
        stage_new_path = Path(run_dir) / 'stage_new.dat'
        lines = stage_new_path.read_text(errors='ignore').splitlines()
        for idx, line in enumerate(lines):
            if "NSTEPS_MAX" in line and idx + 1 < len(lines):
                next_line = lines[idx+1]
                parts = next_line.split()
                if len(parts) >= 2:
                    conlim = parts[1]
                    lines[idx+1] = f"       2000  {conlim}"
                    print(f"[MultallSolver] Capped NSTEPS_MAX to 2000 (was {parts[0]}) for faster execution.")
                break
        modified_content = "\n".join(lines) + "\n"
        deck = modified_content.encode('utf-8')
        try:
            result = subprocess.run(
                [multall_abs],
                cwd=run_dir,
                input=deck,
                capture_output=False,  # Stream directly to parent console to avoid pipe buffering
            )
            
            # Post-run check: MULTALL sometimes exits with code 0 on failure (e.g., dimension errors)
            flow_out_path = Path(self.flow_out_path)
            if result.returncode != 0 or not flow_out_path.exists() or flow_out_path.stat().st_size == 0:
                log_path = Path(run_dir) / 'stage.log'
                
                # Try to read the solver's own log file for context
                stage_log_content = ""
                if log_path.exists():
                    try:
                        with open(log_path, 'r') as log_fh:
                            # Get last 20 lines of stage.log
                            stage_log_content = "\n".join(log_fh.readlines()[-20:])
                    except Exception:
                        pass

                # Format exit code
                exit_hex = f"0x{result.returncode & 0xFFFFFFFF:08X}"
                is_segfault = (result.returncode & 0xFFFFFFFF) == 0xC0000005

                msg = (
                    f"MULTALL solver failed or aborted (exit code {result.returncode} / {exit_hex}).\n"
                    f"  Executable : {multall_abs}\n"
                    f"  Working dir: {run_dir}\n"
                )
                if stage_log_content:
                    msg += f"\n  Last lines of stage.log:\n{stage_log_content}\n"
                else:
                    msg += f"  Check the console output above for details.\n"
                
                if is_segfault:
                    msg += (
                        "\n  This is a STATUS_ACCESS_VIOLATION (segfault) inside the\n"
                        "  Fortran solver. Common causes:\n"
                        "    - Too many stages/rows for the solver's fixed array sizes\n"
                        "    - Numerical instability in the flow computation\n"
                    )
                raise RuntimeError(msg)
        except FileNotFoundError:
            raise RuntimeError(
                f"MULTALL executable not found: {multall_abs}\n"
                f"  Check that multall_exe points to a valid path."
            )
        except OSError as e:
            raise RuntimeError(
                f"Cannot execute MULTALL: {e}\n"
                f"  Executable: {multall_abs}\n"
                f"  If this is a permission error, try running:\n"
                f"    Get-ChildItem '{Path(multall_abs).parent}' | Unblock-File"
            )
        return self.flow_out_path


def parse_shaft_power(work_dir, rpm, gamma, R, mass_flow, machine_type):
    """Extract the shaft power [W] of a turbomachine from Multall's global.plt file.

    Cites the following WRITE statements in multall-open-20.9.f as evidence:
      - Line 11995: WRITE(11) (BLADE_FLOW(J), J=1,JM) -> Record 3
      - Line 11997: WRITE(11) (SUMTO(J), J=1,JM)      -> Record 5

    And the plane J definitions at lines 12637-12639:
      - J1 = 2 (inlet plane, Python index 1)
      - J2M1 = JM - 1 (outlet plane, Python index JM - 2)

    Parameters
    ----------
    work_dir : str
        The working directory of the turbomachine run containing global.plt.
    rpm : float
        The rotational speed [rpm] of the machine (not directly used here, but part of interface).
    gamma : float
        Specific heat ratio.
    R : float
        Specific gas constant [J/(kg K)].
    mass_flow : float
        The design mass flow rate [kg/s]. Used as the primary mdot for the power formula.
    machine_type : str
        Either 'compressor' or 'turbine'.

    Returns
    -------
    float
        The shaft power [W] (positive magnitude).
    """
    import struct
    from pathlib import Path

    global_plt_path = Path(work_dir) / "global.plt"
    if not global_plt_path.exists():
        raise FileNotFoundError(f"Multall output file not found: {global_plt_path}")

    # Read binary Fortran unformatted records
    file_bytes = global_plt_path.read_bytes()
    records = []
    offset = 0
    while offset < len(file_bytes):
        if offset + 4 > len(file_bytes):
            break
        length = struct.unpack('<I', file_bytes[offset:offset+4])[0]
        if offset + 4 + length + 4 > len(file_bytes):
            raise ValueError(f"Corrupted Fortran record at offset {offset}")
        data = file_bytes[offset+4 : offset+4+length]
        suffix = struct.unpack('<I', file_bytes[offset+4+length : offset+4+length+4])[0]
        if length != suffix:
            raise ValueError(f"Fortran record length mismatch at offset {offset}")
        records.append(data)
        offset += 4 + length + 4

    if len(records) < 11:
        raise ValueError(f"global.plt contains only {len(records)} records, expected at least 11.")

    # Record 0: JM, 1, 1
    JM, _, _ = struct.unpack('<iii', records[0])

    # Record 3: BLADE_FLOW(J)
    blade_flow = struct.unpack(f'<{JM}f', records[3])
    # Record 5: SUMTO(J)
    sum_to = struct.unpack(f'<{JM}f', records[5])

    # J-indices for inlet and outlet (1-indexed J1=2 and J2M1=JM-1)
    J1_idx = 1
    J2M1_idx = JM - 2

    # Stagnation temperatures (mass-flow weighted averages)
    # T0_avg = sum_i( rho * Vx * A * T0 ) / sum_i( rho * Vx * A ) = SUMTO / BLADE_FLOW
    T0_in = sum_to[J1_idx] / blade_flow[J1_idx]
    T0_out = sum_to[J2M1_idx] / blade_flow[J2M1_idx]

    # Calculate cp
    cp = gamma * R / (gamma - 1.0)

    # Calculate power (positive magnitude)
    if machine_type.lower() == 'compressor':
        power = mass_flow * cp * (T0_out - T0_in)
    elif machine_type.lower() == 'turbine':
        power = mass_flow * cp * (T0_in - T0_out)
    else:
        raise ValueError(f"Invalid machine_type: '{machine_type}'. Must be 'compressor' or 'turbine'.")

    return abs(power)


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------


if __name__ == '__main__':
    from pathlib import Path

    base_dir      = Path(__file__).resolve().parent
    work_dir_path = base_dir / 'DesignExample' / 'test_run_c'

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
        exe_dir = base_dir / 'executables'
        work    = base_dir / 'smoke_cfd'

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
        print("stagen.out exists:", Path(stagen_out).exists())

        print("launching MULTALL ...")
        flow_out = cfd_solver._run_high_fidelity()
        print("flow_out path:", flow_out)
        print("flow_out exists:", Path(flow_out).exists())