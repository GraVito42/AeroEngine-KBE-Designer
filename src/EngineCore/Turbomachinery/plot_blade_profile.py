"""
plot_blade_profiles.py
======================
Standalone plotting module for blade profiles parsed from stagen.out.
Called from Turbomachine.plot_profiles() (@action).

Window layout (3 windows total, regardless of number of stages):
  Fig 1 — mid-span profiles of ALL stages in sequence (max 4 cols per row).
  Fig 2 — tip sections of ALL stages: rotor vs stator side-by-side per stage.
  Fig 3 — hub sections of ALL stages: rotor vs stator side-by-side per stage.
"""

# Ensure project root is in sys.path when running this file directly
import sys
from pathlib import Path
for parent in Path(__file__).resolve().parents:
    if (parent / "EngineCore").exists() and (parent / "Thermodynamics").exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break

from pathlib import Path


# ---------------------------------------------------------------------------
# Internal helpers (unchanged — retrocompatibility guaranteed)
# ---------------------------------------------------------------------------

def _prepare_profile(suc_raw, prs_raw, label=''):
    """Fix orientation so profiles plot with LE on the left (upstream).

    stagen.out writes SUCTION SURFACE POINTS FROM LE TO TE using XUP/YUP
    arrays (stagen-18.1.f). For a compressor the loop is clockwise from LE,
    so the suction x-values increase LE→TE (suc[0].x < suc[-1].x).
    For a turbine the loop runs the other way so x decreases (suc[0].x > suc[-1].x).

    Reverse if written TE→LE. Also ensure suction on positive-y side.
    """
    suc = list(suc_raw)
    prs = list(prs_raw)

    if not suc:
        return suc, prs

    # Diagnostic: print first/last point to confirm direction in the console.
    print(f"[_prepare_profile] {label}  "
          f"suc[0]=({suc[0][0]:.4f},{suc[0][1]:.4f})  "
          f"suc[-1]=({suc[-1][0]:.4f},{suc[-1][1]:.4f})  "
          f"x_first{'>' if suc[0][0]>suc[-1][0] else '<'}x_last → "
          f"{'REVERSE' if suc[0][0]>suc[-1][0] else 'keep'}")

    # Reverse if written TE→LE (first x > last x)
    if suc[0][0] > suc[-1][0]:
        suc = list(reversed(suc))
        prs = list(reversed(prs))

    # Ensure suction on positive-y side
    mean_y = sum(p[1] for p in suc) / len(suc)
    if mean_y < 0:
        suc = [(x, -y) for x, y in suc]
        prs = [(x, -y) for x, y in prs]

    return suc, prs


def _mid_section_idx(n_sections):
    return n_sections // 2


def _plot_row_profile(ax, suc, prs, color, label, x_offset=0.0, y_offset=0.0):
    """Draw one closed blade profile on ax with optional translation."""
    if not suc or not prs:
        return

    def shift(pts):
        return [(x + x_offset, y + y_offset) for x, y in pts]

    suc_s = shift(suc)
    prs_s = shift(prs)

    xs, ys = zip(*suc_s)
    xp, yp = zip(*prs_s)
    ax.plot(xs, ys, color=color, lw=0.8, alpha=0.5)
    ax.plot(xp, yp, color=color, lw=0.8, alpha=0.5)

    prs_rev = list(reversed(prs_s))
    outline = list(suc_s) + prs_rev[1:-1] + [suc_s[0]]
    xo, yo  = zip(*outline)
    ax.plot(xo, yo, color=color, lw=1.6, label=label)

    ax.plot(suc_s[0][0],  suc_s[0][1],  'o', color=color, ms=3)   # LE
    ax.plot(suc_s[-1][0], suc_s[-1][1], 's', color=color, ms=3)   # TE


# ---------------------------------------------------------------------------
# Internal: plot one spanwise section (rotor + stator) on a given axes
# ---------------------------------------------------------------------------

def _plot_section_on_ax(ax, rotor, stator, sec_idx, stage_idx, machine_type, title_prefix=''):
    """Plot rotor and stator in flow-direction sequence on a single axes.

    Rotor placed at x=0; stator LE starts at rotor_TE + 15% gap.
    Stator y-shifted so its LE aligns with rotor TE y.
    For turbines the row order is swapped (stator upstream).
    """
    r_suc, r_prs = _prepare_profile(
        rotor['suction'][sec_idx], rotor['pressure'][sec_idx],
        label=f'stage{stage_idx+1} rotor sec{sec_idx+1}')
    s_suc_raw, s_prs_raw = _prepare_profile(
        stator['suction'][sec_idx], stator['pressure'][sec_idx],
        label=f'stage{stage_idx+1} stator sec{sec_idx+1}')

    # Stator concave opposite way (matches old Fig B convention)
    s_suc = [(x, -y) for x, y in s_suc_raw]
    s_prs = [(x, -y) for x, y in s_prs_raw]

    # Upstream row TE coordinates for gap + y-alignment of downstream row
    r_te_x = r_suc[-1][0]
    r_te_y = r_suc[-1][1]
    gap_x  = r_te_x + 0.15
    s_le_y = s_suc[0][1]
    dy     = r_te_y - s_le_y

    if machine_type == 'compressor':
        _plot_row_profile(ax, r_suc, r_prs, 'steelblue', 'Rotor',
                          x_offset=0.0, y_offset=0.0)
        _plot_row_profile(ax, s_suc, s_prs, 'firebrick', 'Stator',
                          x_offset=gap_x, y_offset=dy)
    else:
        # Turbine: stator upstream, rotor downstream
        _plot_row_profile(ax, s_suc, s_prs, 'firebrick', 'Stator',
                          x_offset=0.0, y_offset=0.0)
        _plot_row_profile(ax, r_suc, r_prs, 'steelblue', 'Rotor',
                          x_offset=gap_x, y_offset=-dy)

    ax.axvline(gap_x, color='gray', lw=0.5, ls='--', alpha=0.4)

    r = rotor['r_sections'][sec_idx]
    ax.set_title(f"{title_prefix}Stage {stage_idx + 1}  r={r:.3f} m", fontsize=8)
    ax.set_xlabel("x / chord  →  flow", fontsize=7)
    ax.set_ylabel("y / chord", fontsize=7)
    ax.set_aspect('equal')
    ax.grid(True, lw=0.4, alpha=0.5)
    ax.tick_params(labelsize=7)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def plot_blade_profiles(stage_data, machine_type='compressor', save_dir=None):
    """Plot blade profiles for all stages in 3 windows.

    Fig 1 — mid-span profiles, all stages in sequence.
            Up to 4 subplots per row; wraps into additional rows beyond 4 stages.
    Fig 2 — tip sections (sec_idx = -1), rotor vs stator, one subplot per stage.
    Fig 3 — hub sections (sec_idx = 0), rotor vs stator, one subplot per stage.

    Retrocompatibility: signature unchanged from previous version.
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        raise ImportError("matplotlib required: pip install matplotlib")

    n_stages = len(stage_data)
    if n_stages == 0:
        print("[plot_blade_profiles] no stages to plot.")
        return

    NCOLS = min(n_stages, 4)
    NROWS = (n_stages + NCOLS - 1) // NCOLS  # ceiling division

    legend_handles = [
        mpatches.Patch(color='steelblue', label='Rotor'),
        mpatches.Patch(color='firebrick', label='Stator'),
    ]

    # ------------------------------------------------------------------
    # Figure 1 — mid-span of all stages
    # ------------------------------------------------------------------
    fig1, axes1 = plt.subplots(
        NROWS, NCOLS,
        figsize=(4 * NCOLS, 4 * NROWS),
        squeeze=False,
    )
    fig1.suptitle(
        f"{machine_type.capitalize()} — mid-span profiles (all stages)",
        fontsize=12,
    )

    for stage_idx, stage in enumerate(stage_data):
        rotor  = stage['rotor']
        stator = stage['stator']
        n_sec  = len(rotor['suction'])
        mid    = _mid_section_idx(n_sec)

        row = stage_idx // NCOLS
        col = stage_idx % NCOLS
        ax  = axes1[row][col]

        _plot_section_on_ax(ax, rotor, stator, mid, stage_idx, machine_type)

    # Hide any unused subplot cells
    total_cells = NROWS * NCOLS
    for unused in range(n_stages, total_cells):
        row = unused // NCOLS
        col = unused % NCOLS
        axes1[row][col].set_visible(False)

    fig1.legend(handles=legend_handles, loc='lower center', ncol=2,
                fontsize=9, frameon=False)
    fig1.tight_layout(rect=[0, 0.04, 1, 1])

    # ------------------------------------------------------------------
    # Figure 2 — tip sections (last sec_idx) for all stages
    # ------------------------------------------------------------------
    fig2, axes2 = plt.subplots(
        NROWS, NCOLS,
        figsize=(4 * NCOLS, 4 * NROWS),
        squeeze=False,
    )
    fig2.suptitle(
        f"{machine_type.capitalize()} — tip sections (all stages)",
        fontsize=12,
    )

    for stage_idx, stage in enumerate(stage_data):
        rotor  = stage['rotor']
        stator = stage['stator']
        n_sec  = len(rotor['suction'])
        tip    = n_sec - 1

        row = stage_idx // NCOLS
        col = stage_idx % NCOLS
        ax  = axes2[row][col]

        _plot_section_on_ax(ax, rotor, stator, tip, stage_idx, machine_type,
                            title_prefix='Tip — ')

    for unused in range(n_stages, total_cells):
        row = unused // NCOLS
        col = unused % NCOLS
        axes2[row][col].set_visible(False)

    fig2.legend(handles=legend_handles, loc='lower center', ncol=2,
                fontsize=9, frameon=False)
    fig2.tight_layout(rect=[0, 0.04, 1, 1])

    # ------------------------------------------------------------------
    # Figure 3 — hub sections (sec_idx = 0) for all stages
    # ------------------------------------------------------------------
    fig3, axes3 = plt.subplots(
        NROWS, NCOLS,
        figsize=(4 * NCOLS, 4 * NROWS),
        squeeze=False,
    )
    fig3.suptitle(
        f"{machine_type.capitalize()} — hub sections (all stages)",
        fontsize=12,
    )

    for stage_idx, stage in enumerate(stage_data):
        rotor  = stage['rotor']
        stator = stage['stator']
        hub    = 0

        row = stage_idx // NCOLS
        col = stage_idx % NCOLS
        ax  = axes3[row][col]

        _plot_section_on_ax(ax, rotor, stator, hub, stage_idx, machine_type,
                            title_prefix='Hub — ')

    for unused in range(n_stages, total_cells):
        row = unused // NCOLS
        col = unused % NCOLS
        axes3[row][col].set_visible(False)

    fig3.legend(handles=legend_handles, loc='lower center', ncol=2,
                fontsize=9, frameon=False)
    fig3.tight_layout(rect=[0, 0.04, 1, 1])

    # ------------------------------------------------------------------
    # Display or save
    # ------------------------------------------------------------------
    if save_dir is not None:
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        figs = {
            'all_stages_mid.png':  fig1,
            'all_stages_tip.png':  fig2,
            'all_stages_hub.png':  fig3,
        }
        for fname, fig in figs.items():
            path = str(Path(save_dir) / fname)
            fig.savefig(path, dpi=150, bbox_inches='tight')
            print(f"[plot_blade_profiles] saved {path}")
            plt.close(fig)
    else:
        plt.show(block=False)
        plt.show()