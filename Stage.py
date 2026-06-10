"""
Stage.py
========
Parametric turbomachinery stage: full rotor row + full stator row.

Each row contains n_blades blades distributed evenly around the annulus.
The stator is placed downstream of the rotor with an axial gap.

Coordinate system (engine frame):
  X — axial / meridional      ← engine spin axis
  Y — radial
  Z — tangential / circumferential

Circumferential blade placement:
  Each blade[i] is rotated by  i * (360 / n_blades) degrees
  around the X axis (engine spin axis).

Axial placement:
  Rotor row  at X = 0 (origin)
  Stator row at X = rotor_axial_chord + axial_gap
"""

import math
from parapy.core import Base, Input, Attribute, Part, child
from parapy.geom import GeomBase

from Blade import Blade


class Stage(GeomBase):
    """
    One turbomachinery stage: rotor blade row + stator blade row.

    Purely constructive — no thermodynamics. Receives pre-parsed geometry
    data from Turbomachine and instantiates both full blade rows.
    """

    # ------------------------------------------------------------------
    # Inputs — rotor
    # ------------------------------------------------------------------

    rotor_profiles_suc   = Input([])
    rotor_profiles_prs   = Input([])
    rotor_r_sections     = Input([])
    rotor_span_fractions = Input([0.0, 0.5, 1.0])
    rotor_chords         = Input([0.05, 0.05, 0.05])
    rotor_pitch_angles   = Input([0.0, 0.0, 0.0])
    rotor_n_blades       = Input(30)
    rotor_color          = Input('yellow')

    # ------------------------------------------------------------------
    # Inputs — stator
    # ------------------------------------------------------------------

    stator_profiles_suc   = Input([])
    stator_profiles_prs   = Input([])
    stator_r_sections     = Input([])
    stator_span_fractions = Input([0.0, 0.5, 1.0])
    stator_chords         = Input([0.05, 0.05, 0.05])
    stator_pitch_angles   = Input([0.0, 0.0, 0.0])
    stator_n_blades       = Input(40)
    stator_color          = Input('orange')

    # ------------------------------------------------------------------
    # Inputs — layout
    # ------------------------------------------------------------------

    stage_type = Input('compressor')
    """Row order:
      'compressor' -> rotor first (upstream), stator second (downstream).
      'turbine'    -> stator first (upstream), rotor second (downstream).
    """

    axial_gap = Input(0.010)
    """Axial clearance between the two blade rows within the stage [m]."""

    stage_axial_offset = Input(0.0)
    """X offset [m] of this whole stage's leading edge along the engine axis.
    Set by the parent Turbomachine to stack consecutive stages. It is added to
    BOTH rotor_axial_offset and stator_axial_offset, because Blade builds its
    geometry from absolute coordinates (via Blade.axial_offset): a parent
    position frame would NOT translate the blades, but this offset does."""

    n_pts = Input(60)
    """Resampling resolution passed to Blade."""

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _closed_profiles(self, suc_list, prs_list):
        """Merge suction+pressure lists into closed profile loops.

        stagen.out: both surfaces run LE→TE.
        Closed loop: suction LE→TE + pressure reversed (TE→LE),
        shared LE/TE endpoints deduplicated.
        """
        result = []
        for suc, prs in zip(suc_list, prs_list):
            prs_rev = list(reversed(prs))
            result.append(list(suc) + prs_rev[1:-1])
        return result

    # ------------------------------------------------------------------
    # Derived scalars
    # ------------------------------------------------------------------

    @Attribute
    def rotor_profiles_closed(self):
        """Closed 2-D loops for the rotor, one per section."""
        return self._closed_profiles(
            self.rotor_profiles_suc, self.rotor_profiles_prs)

    @Attribute
    def stator_profiles_closed(self):
        """Closed 2-D loops for the stator, one per section."""
        return self._closed_profiles(
            self.stator_profiles_suc, self.stator_profiles_prs)

    @Attribute
    def rotor_r_hub(self):
        """Hub radius of the rotor [m]."""
        return self.rotor_r_sections[0]

    @Attribute
    def rotor_span(self):
        """Blade span of the rotor [m]."""
        return self.rotor_r_sections[-1] - self.rotor_r_sections[0]

    @Attribute
    def stator_r_hub(self):
        """Hub radius of the stator [m]."""
        return self.stator_r_sections[0]

    @Attribute
    def stator_span(self):
        """Blade span of the stator [m]."""
        return self.stator_r_sections[-1] - self.stator_r_sections[0]

    @Attribute
    def rotor_angle_step_deg(self):
        """Angular spacing between rotor blades [deg]."""
        return 360.0 / self.rotor_n_blades

    @Attribute
    def stator_angle_step_deg(self):
        """Angular spacing between stator blades [deg]."""
        return 360.0 / self.stator_n_blades

    @Attribute
    def rotor_mean_axial_chord(self):
        """Mean axial chord of the rotor [m]."""
        return sum(self.rotor_chords) / len(self.rotor_chords)

    @Attribute
    def stator_mean_axial_chord(self):
        """Mean axial chord of the stator [m]."""
        return sum(self.stator_chords) / len(self.stator_chords)

    @Attribute
    def upstream_axial_chord(self):
        """Axial chord of the upstream blade row [m].

        Compressor: rotor is upstream.
        Turbine:    stator is upstream.
        """
        return {'compressor': self.rotor_mean_axial_chord,
                'turbine':    self.stator_mean_axial_chord}[self.stage_type]

    @Attribute
    def rotor_axial_offset(self):
        """Absolute X offset of the rotor LE [m], including stage position.

        Compressor: rotor is first (row-local offset = 0).
        Turbine:    rotor is second (row-local offset = stator chord + gap).
        stage_axial_offset stacks this stage behind previous ones.
        """
        row_local = {'compressor': 0.0,
                     'turbine':    self.stator_mean_axial_chord + self.axial_gap
                     }[self.stage_type]
        return self.stage_axial_offset + row_local

    @Attribute
    def stator_axial_offset(self):
        """Absolute X offset of the stator LE [m], including stage position.

        Compressor: stator is second (row-local offset = rotor chord + gap).
        Turbine:    stator is first (row-local offset = 0).
        stage_axial_offset stacks this stage behind previous ones.
        """
        row_local = {'compressor': self.rotor_mean_axial_chord + self.axial_gap,
                     'turbine':    0.0
                     }[self.stage_type]
        return self.stage_axial_offset + row_local

    @Attribute
    def rotor_solidity(self):
        """Mean rotor solidity (n * chord) / (2π * r_mean)."""
        r_mean = 0.5 * (self.rotor_r_sections[0] + self.rotor_r_sections[-1])
        c_mean = sum(self.rotor_chords) / len(self.rotor_chords)
        return (self.rotor_n_blades * c_mean) / (2.0 * math.pi * r_mean)

    @Attribute
    def stator_solidity(self):
        """Mean stator solidity."""
        r_mean = 0.5 * (self.stator_r_sections[0] + self.stator_r_sections[-1])
        c_mean = sum(self.stator_chords) / len(self.stator_chords)
        return (self.stator_n_blades * c_mean) / (2.0 * math.pi * r_mean)

    # ------------------------------------------------------------------
    # Parts
    # ------------------------------------------------------------------

    @Part
    def rotor_blades(self):
        """Full rotor blade row — n_blades equally spaced around annulus."""
        return Blade(
            quantify             = self.rotor_n_blades,
            profiles             = self.rotor_profiles_closed,
            span_fractions       = self.rotor_span_fractions,
            chords               = self.rotor_chords,
            pitch_angles         = self.rotor_pitch_angles,
            total_span           = self.rotor_span,
            r_hub                = self.rotor_r_hub,
            n_pts                = self.n_pts,
            circumferential_angle= child.index * self.rotor_angle_step_deg,
            axial_offset         = self.rotor_axial_offset,
            color                = self.rotor_color,
        )

    @Part
    def stator_blades(self):
        """Full stator blade row, n_blades equally spaced.

        Compressor: stator is downstream of rotor.
        Turbine:    stator is upstream of rotor.
        """
        return Blade(
            quantify             = self.stator_n_blades,
            profiles             = self.stator_profiles_closed,
            span_fractions       = self.stator_span_fractions,
            chords               = self.stator_chords,
            pitch_angles         = self.stator_pitch_angles,
            total_span           = self.stator_span,
            r_hub                = self.stator_r_hub,
            n_pts                = self.n_pts,
            circumferential_angle= child.index * self.stator_angle_step_deg,
            axial_offset         = self.stator_axial_offset,
            color                = self.stator_color,
        )


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    from parapy.gui import display

    def _profile(n=30):
        suc = [(i / (n-1), 0.06 * math.sin(math.pi * i / (n-1))) for i in range(n)]
        prs = [(i / (n-1), -0.06 * math.sin(math.pi * i / (n-1))) for i in range(n)]
        return suc, prs

    suc, prs = _profile()

    stage = Stage(
        # rotor
        rotor_profiles_suc   = [suc, suc, suc],
        rotor_profiles_prs   = [prs, prs, prs],
        rotor_r_sections     = [0.168, 0.234, 0.299],
        rotor_span_fractions = [0.0, 0.5, 1.0],
        rotor_chords         = [0.060, 0.055, 0.045],
        rotor_pitch_angles   = [-58.6, -60.4, -61.5],
        rotor_n_blades       = 25,
        # stator
        stator_profiles_suc   = [suc, suc, suc],
        stator_profiles_prs   = [prs, prs, prs],
        stator_r_sections     = [0.178, 0.234, 0.290],
        stator_span_fractions = [0.0, 0.5, 1.0],
        stator_chords         = [0.060, 0.055, 0.045],
        stator_pitch_angles   = [58.6, 60.4, 61.5],
        stator_n_blades       = 25,
        # layout
        axial_gap          = 0.001,
        stage_axial_offset = 0.0,
        n_pts              = 40,
        label              = 'stage_1',
        stage_type         = 'compressor',
    )

    print(f"rotor  blades   = {stage.rotor_n_blades}, "
          f"angle step = {stage.rotor_angle_step_deg:.2f} deg")
    print(f"stator blades   = {stage.stator_n_blades}, "
          f"angle step = {stage.stator_angle_step_deg:.2f} deg")
    print(f"rotor  X offset = {stage.rotor_axial_offset*1000:.1f} mm")
    print(f"stator X offset = {stage.stator_axial_offset*1000:.1f} mm")
    print(f"rotor  solidity = {stage.rotor_solidity:.3f}")
    print(f"stator solidity = {stage.stator_solidity:.3f}")

    display(stage, view='top', autodraw=True)