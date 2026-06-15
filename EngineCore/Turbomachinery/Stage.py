"""
Stage.py
========
Parametric turbomachinery stage: full rotor row + full stator row.

Each row contains n_blades blades distributed evenly around the annulus.
The stator is placed downstream of the rotor with an axial gap.

Coordinate system (engine frame):
  X — axial / meridional      <- engine spin axis
  Y — radial
  Z — tangential / circumferential

Instancing strategy (performance refactor):
  Previously: quantify=N independent Blade lofts  -> ~70 lofts/stage.
  Now:        1 master Blade loft (hidden) + N RotatedShape copies
              -> exactly 2 LoftedSolid evaluations per stage.
"""

# Ensure project root is in sys.path when running this file directly
import sys
from pathlib import Path
for parent in Path(__file__).resolve().parents:
    if (parent / "EngineCore").exists() and (parent / "Thermodynamics").exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break

import math

from parapy.core import Input, Attribute, Part
from parapy.geom import GeomBase, RotatedShape, Vector, Point, Compound
from parapy.core import child

from EngineCore.Turbomachinery.Blade import Blade


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
    Set by the parent Turbomachine to stack consecutive stages."""

    n_pts = Input(60)
    """Resampling resolution passed to Blade."""

    preview_deflection = Input(0.0005)
    """Forwarded as mesh_deflection to LoftedSolid. Lower = finer tessellation."""

    show_blades = Input(False)
    """If False, the 3D blade geometries are hidden by default to keep load times fast."""

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _closed_profiles(self, suc_list, prs_list):
        """Merge suction+pressure lists into closed profile loops.

        STAGEN writes both surfaces FROM LE TO TE (x increases 0->1).
        Closed loop: suction LE->TE + pressure reversed (TE->LE),
        with shared LE and TE endpoints deduplicated.
        """
        result = []
        for suc, prs in zip(suc_list, prs_list):
            if suc and suc[0][0] > suc[-1][0]:
                suc = list(reversed(suc))
                prs = list(reversed(prs))
            prs_rev = list(reversed(prs))
            result.append(list(suc) + prs_rev[1:-1])
        return result

    # ------------------------------------------------------------------
    # Derived geometry attributes
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
    def rotor_angle_step_rad(self):
        """Angular spacing between rotor blades [rad] — used by RotatedShape."""
        return 2.0 * math.pi / self.rotor_n_blades

    @Attribute
    def stator_angle_step_rad(self):
        """Angular spacing between stator blades [rad]."""
        return 2.0 * math.pi / self.stator_n_blades

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
        Compressor: rotor upstream. Turbine: stator upstream."""
        return {'compressor': self.rotor_mean_axial_chord,
                'turbine':    self.stator_mean_axial_chord}[self.stage_type]

    @Attribute
    def rotor_axial_offset(self):
        """Absolute X offset of the rotor LE [m].
        Compressor: rotor is first (row-local = 0).
        Turbine:    rotor is second (row-local = stator chord + gap)."""
        return self.stage_axial_offset + {
            'compressor': 0.0,
            'turbine':    self.stator_mean_axial_chord + self.axial_gap,
        }[self.stage_type]

    @Attribute
    def stator_axial_offset(self):
        """Absolute X offset of the stator LE [m].
        Compressor: stator is second (row-local = rotor chord + gap).
        Turbine:    stator is first (row-local = 0)."""
        return self.stage_axial_offset + {
            'compressor': self.rotor_mean_axial_chord + self.axial_gap,
            'turbine':    0.0,
        }[self.stage_type]

    @Attribute
    def rotor_solidity(self):
        """Mean rotor solidity: (n * chord) / (2π * r_mean)."""
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
    # Volume aggregation (rigid rotation is volume-preserving)
    # ------------------------------------------------------------------

    @Attribute
    def rotor_blade_volume(self):
        """Total rotor row volume [m³] = master volume × blade count."""
        return self.rotor_master.body.volume * self.rotor_n_blades

    @Attribute
    def stator_blade_volume(self):
        """Total stator row volume [m³]."""
        return self.stator_master.body.volume * self.stator_n_blades

    # ------------------------------------------------------------------
    # Master blades — ONE LoftedSolid per row, hidden
    # ------------------------------------------------------------------

    @Part
    def rotor_master(self):
        """Master rotor blade at circumferential_angle=0. Hidden.
        Source OCC solid for all rotor_blades RotatedShape copies."""
        return Blade(
            profiles              = self.rotor_profiles_closed,
            span_fractions        = self.rotor_span_fractions,
            chords                = self.rotor_chords,
            pitch_angles          = self.rotor_pitch_angles,
            total_span            = self.rotor_span,
            r_hub                 = self.rotor_r_hub,
            n_pts                 = self.n_pts,
            preview_deflection    = self.preview_deflection,
            circumferential_angle = 0.0,
            axial_offset          = self.rotor_axial_offset,
            color                 = self.rotor_color,
            hidden                = True,
        )

    @Part
    def stator_master(self):
        """Master stator blade at circumferential_angle=0. Hidden."""
        return Blade(
            profiles              = self.stator_profiles_closed,
            span_fractions        = self.stator_span_fractions,
            chords                = self.stator_chords,
            pitch_angles          = self.stator_pitch_angles,
            total_span            = self.stator_span,
            r_hub                 = self.stator_r_hub,
            n_pts                 = self.n_pts,
            preview_deflection    = self.preview_deflection,
            circumferential_angle = 0.0,
            axial_offset          = self.stator_axial_offset,
            color                 = self.stator_color,
            hidden                = True,
        )

    # ------------------------------------------------------------------
    # Full blade rows — pure OCC rigid transforms, no extra BREP work
    # ------------------------------------------------------------------

    @Part
    def rotor_blades(self):
        """Full rotor row: N rotated copies of rotor_master.body as a single Compound."""
        return Compound(
            built_from=[
                self.rotor_master.body.rotated(Vector(1.0, 0.0, 0.0),
                                               idx * self.rotor_angle_step_rad,
                                               Point(0.0, 0.0, 0.0))
                for idx in range(self.rotor_n_blades)
            ] if self.show_blades else [],
            color          = self.rotor_color,
        )

    @Part
    def stator_blades(self):
        """Full stator row: N rotated copies of stator_master.body as a single Compound."""
        return Compound(
            built_from=[
                self.stator_master.body.rotated(Vector(1.0, 0.0, 0.0),
                                                idx * self.stator_angle_step_rad,
                                                Point(0.0, 0.0, 0.0))
                for idx in range(self.stator_n_blades)
            ] if self.show_blades else [],
            color          = self.stator_color,
        )


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    import time
    from parapy.gui import display

    def _profile(n=30):
        suc = [(i / (n-1), 0.06 * math.sin(math.pi * i / (n-1))) for i in range(n)]
        prs = [(i / (n-1), -0.06 * math.sin(math.pi * i / (n-1))) for i in range(n)]
        return suc, prs

    suc, prs = _profile()

    t0 = time.perf_counter()

    stage = Stage(
        # rotor
        rotor_profiles_suc   = [suc, suc, suc],
        rotor_profiles_prs   = [prs, prs, prs],
        rotor_r_sections     = [0.168, 0.234, 0.299],
        rotor_span_fractions = [0.0, 0.5, 1.0],
        rotor_chords         = [0.060, 0.055, 0.045],
        rotor_pitch_angles   = [-58.6, -60.4, -61.5],
        rotor_n_blades       = 12,
        # stator
        stator_profiles_suc   = [suc, suc, suc],
        stator_profiles_prs   = [prs, prs, prs],
        stator_r_sections     = [0.178, 0.234, 0.290],
        stator_span_fractions = [0.0, 0.5, 1.0],
        stator_chords         = [0.060, 0.055, 0.045],
        stator_pitch_angles   = [58.6, 60.4, 61.5],
        stator_n_blades       = 16,
        # layout
        stage_type         = 'compressor',
        axial_gap          = 0.001,
        stage_axial_offset = 0.0,
        n_pts              = 30,
        preview_deflection = 0.001,
        label              = 'smoke_stage',
    )

    t1 = time.perf_counter()
    print(f"[BENCH] Stage instantiation:        {t1 - t0:.3f} s")

    t2 = time.perf_counter()
    vol = stage.rotor_master.body.volume
    t3 = time.perf_counter()
    print(f"[BENCH] Master rotor loft:          {t3 - t2:.3f} s")
    print(f"        rotor master volume:         {vol:.4e} m^3")

    t4 = time.perf_counter()
    _ = stage.rotor_blades.faces
    t5 = time.perf_counter()
    print(f"[BENCH] Compound evaluation:        {t5 - t4:.3f} s")

    print(f"rotor  blades   = {stage.rotor_n_blades}, "
          f"angle step = {stage.rotor_angle_step_deg:.2f} deg")
    print(f"stator blades   = {stage.stator_n_blades}, "
          f"angle step = {stage.stator_angle_step_deg:.2f} deg")
    print(f"rotor  X offset = {stage.rotor_axial_offset*1000:.1f} mm")
    print(f"stator X offset = {stage.stator_axial_offset*1000:.1f} mm")
    print(f"rotor  solidity = {stage.rotor_solidity:.3f}")
    print(f"stator solidity = {stage.stator_solidity:.3f}")
    print(f"rotor  blade volume (total) = {stage.rotor_blade_volume:.4e} m^3")

    display(stage, view='top', autodraw=True)