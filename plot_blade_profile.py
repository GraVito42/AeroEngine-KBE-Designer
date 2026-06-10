"""
plot_blade_profiles.py
======================
Standalone plotting module for blade profiles parsed from stagen.out.
Called from Turbomachine.plot_profiles() (@action).
"""

import os


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


def plot_blade_profiles(stage_data, machine_type='compressor', save_dir=None):
    """Plot rotor and stator blade profiles for every stage.

    Figure A — hub/mid/tip grid:
        One subplot per spanwise section. Rotor in steelblue, stator in firebrick.
        x-axis = axial (flow direction →), y-axis = tangential.

    Figure B — flow-direction view:
        Mid-span rotor and stator placed in axial sequence. Stator LE
        y-aligned with rotor TE. Rotor concave toward positive y (suction up),
        stator concave the other way (typical compressor/turbine stage layout).
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        raise ImportError("matplotlib required: pip install matplotlib")

    for stage_idx, stage in enumerate(stage_data):
        rotor  = stage['rotor']
        stator = stage['stator']
        n_sec  = len(rotor['suction'])
        mid    = _mid_section_idx(n_sec)

        # ------------------------------------------------------------------
        # Figure A — per-section grid
        # ------------------------------------------------------------------
        fig_a, axes = plt.subplots(1, n_sec, figsize=(4 * n_sec, 4), squeeze=False)
        fig_a.suptitle(
            f"{machine_type.capitalize()} — Stage {stage_idx + 1}  "
            f"(rotor: {rotor['n_blades']} blades, "
            f"stator: {stator['n_blades']} blades)",
            fontsize=11,
        )

        for sec_idx in range(n_sec):
            ax = axes[0][sec_idx]
            r  = rotor['r_sections'][sec_idx]

            r_suc, r_prs = _prepare_profile(
                rotor['suction'][sec_idx], rotor['pressure'][sec_idx],
                label=f'stage{stage_idx+1} rotor sec{sec_idx+1}')
            s_suc, s_prs = _prepare_profile(
                stator['suction'][sec_idx], stator['pressure'][sec_idx],
                label=f'stage{stage_idx+1} stator sec{sec_idx+1}')

            _plot_row_profile(ax, r_suc, r_prs, 'steelblue', 'Rotor')
            _plot_row_profile(ax, s_suc, s_prs, 'firebrick', 'Stator')

            ax.set_title(f"Section {sec_idx + 1}  (r = {r:.3f} m)", fontsize=9)
            ax.set_xlabel("x / chord  →  flow", fontsize=8)
            ax.set_ylabel("y / chord", fontsize=8)
            ax.set_aspect('equal')
            ax.grid(True, lw=0.4, alpha=0.5)
            ax.tick_params(labelsize=7)

        handles = [
            mpatches.Patch(color='steelblue', label='Rotor'),
            mpatches.Patch(color='firebrick', label='Stator'),
        ]
        fig_a.legend(handles=handles, loc='lower center', ncol=2,
                     fontsize=9, frameon=False)
        fig_a.tight_layout(rect=[0, 0.05, 1, 1])

        # ------------------------------------------------------------------
        # Figure B — flow-direction view (mid-span)
        # ------------------------------------------------------------------
        fig_b, ax_b = plt.subplots(figsize=(9, 4))
        fig_b.suptitle(
            f"{machine_type.capitalize()} — Stage {stage_idx + 1}  "
            f"mid-span profiles in flow direction",
            fontsize=11,
        )

        r_suc_m, r_prs_m = _prepare_profile(
            rotor['suction'][mid], rotor['pressure'][mid],
            label=f'stage{stage_idx+1} rotor mid')
        s_suc_raw, s_prs_raw = _prepare_profile(
            stator['suction'][mid], stator['pressure'][mid],
            label=f'stage{stage_idx+1} stator mid')
        s_suc_m = [(x, -y) for x, y in s_suc_raw]
        s_prs_m = [(x, -y) for x, y in s_prs_raw]

        # Place rotor at x=0; stator LE starts at rotor_TE + 15% gap.
        # Shift stator y so its LE aligns with rotor TE.
        r_te_x = r_suc_m[-1][0]   # TE is last point after _prepare_profile
        r_te_y = r_suc_m[-1][1]

        gap_x  = r_te_x + 0.15
        s_le_y = s_suc_m[0][1]    # stator LE y before shift
        dy     = r_te_y - s_le_y  # shift so stator LE matches rotor TE y

        _plot_row_profile(ax_b, r_suc_m, r_prs_m, 'steelblue', 'Rotor',
                          x_offset=0.0, y_offset=0.0)
        _plot_row_profile(ax_b, s_suc_m, s_prs_m, 'firebrick', 'Stator',
                          x_offset=gap_x, y_offset=dy)

        # Mark the TE/LE junction
        ax_b.plot(r_te_x, r_te_y, 'k^', ms=6, zorder=5,
                  label=f'Rotor TE / Stator LE  y={r_te_y:.3f}')
        ax_b.axvline(gap_x, color='firebrick', lw=0.5, ls='--', alpha=0.4)

        ax_b.set_xlabel("x / chord  →  flow direction", fontsize=9)
        ax_b.set_ylabel("y / chord", fontsize=9)
        ax_b.set_aspect('equal')
        ax_b.grid(True, lw=0.4, alpha=0.5)
        ax_b.legend(fontsize=8, frameon=False, loc='upper right')
        fig_b.tight_layout()

        # ------------------------------------------------------------------
        # Display or save
        # ------------------------------------------------------------------
        if save_dir is not None:
            os.makedirs(save_dir, exist_ok=True)
            path_a = os.path.join(save_dir, f'stage_{stage_idx+1}_sections.png')
            path_b = os.path.join(save_dir, f'stage_{stage_idx+1}_flow_view.png')
            fig_a.savefig(path_a, dpi=150, bbox_inches='tight')
            fig_b.savefig(path_b, dpi=150, bbox_inches='tight')
            print(f"[plot_blade_profiles] saved {path_a}")
            print(f"[plot_blade_profiles] saved {path_b}")
            plt.close(fig_a)
            plt.close(fig_b)
        else:
            plt.show(block=False)

    if save_dir is None:
        plt.show()


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