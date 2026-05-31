"""
Engine Frame – Simplified Geometric KBE Model (v3 – positioning fixed)
=======================================================================

Fixes vs v2:
  1. void_fused: FusedSolid(tool=Sequence) passed GeomBase objects, not solids.
     Fixed with @Attribute iterative chain over .solid geometry objects only.

  2. Positioning: rotate90(self.position, 'x') was stacking rotations across
     the hierarchy (Duct position already translated → child rotate adds on top
     → garbage orientation).
     Fixed: ALL Cylinder/Cone primitives use a fresh rotate90(XOY, 'x') as base,
     then translate by the ABSOLUTE Z position computed from parent inputs.
     GeomBase position-chaining is intentionally NOT used for geometry primitives
     here — it adds complexity without benefit when we control Z explicitly.

  3. FlowStation simplified: it now receives z_start (absolute global Z) directly.
     No more relative-offset confusion across the Duct boundary.

Axis convention (confirmed with Architect TODO still open):
  Z  = engine longitudinal axis (front → rear)
  rotate90(XOY, 'x') turns local-Z cylinder → global-Z alignment.
  # TODO: if everything appears on its side, swap 'x' → 'y'.
"""

from parapy.core import Input, Attribute, Part, child
from parapy.geom import (
    GeomBase,
    Cylinder, Cone, Box,
    FusedSolid, SubtractedSolid,
    translate, rotate90,
    XOY,
)

# Shorthand: base position for a Z-aligned cylinder/cone at global z=0
Z_AXIS_POS = rotate90(XOY, 'x')


def z_pos(z_offset):
    """Return a Position aligned with engine Z-axis, translated to z_offset."""
    return translate(Z_AXIS_POS, 'z', z_offset)


# =============================================================================
# LAYER 1 – Atomic flow-path primitive
# =============================================================================

class FlowStation(GeomBase):
    """
    One internal flow-path cylinder.
    z_start is the ABSOLUTE global Z coordinate of the cylinder's front face.
    """
    radius  = Input(0.30)
    length  = Input(0.50)
    z_start = Input(0.0)   # absolute Z in global frame

    @Part
    def solid(self):
        return Cylinder(
            radius  =self.radius,
            height  =self.length,
            position=z_pos(self.z_start),
        )


# =============================================================================
# LAYER 2 – Duct
# =============================================================================

class Duct(GeomBase):
    """
    Aggregates FlowStation children forming the internal void.
    z_core_start: absolute global Z where the core begins (= frame_length_inlet).
    Station z_offsets are relative to z_core_start and converted to absolute here.
    """

    engine_type  = Input('turbojet')
    core_length  = Input(3.0)
    core_radius  = Input(0.30)
    z_core_start = Input(0.8)   # absolute Z of core front face in global frame

    @Attribute
    def station_definitions(self):
        """
        List of dicts: {radius, length, z_offset}
        z_offset is relative to the core front face.
        Converted to absolute z_start = z_core_start + z_offset in stations @Part.
        """
        L = self.core_length
        R = self.core_radius

        if self.engine_type == 'turbojet':
            return [
                {'radius': R * 0.20, 'length': L,        'z_offset': 0.0       },  # Shaft
                {'radius': R * 0.80, 'length': L * 0.15, 'z_offset': 0.0       },  # Compressor 1
                {'radius': R * 0.75, 'length': L * 0.15, 'z_offset': L * 0.15  },  # Compressor 2
                {'radius': R * 0.60, 'length': L * 0.30, 'z_offset': L * 0.35  },  # Combustor
                {'radius': R * 0.80, 'length': L * 0.15, 'z_offset': L * 0.70  },  # Turbine 1
                {'radius': R * 0.75, 'length': L * 0.15, 'z_offset': L * 0.85  },  # Turbine 2
            ]

        elif self.engine_type == 'turbofan_2spool':
            return [
                {'radius': R * 1.50, 'length': L * 0.15, 'z_offset': -L * 0.15},  # Fan (ahead of core)
                {'radius': R * 0.25, 'length': L,        'z_offset': 0.0       },  # LP Shaft
                {'radius': R * 0.15, 'length': L,        'z_offset': 0.0       },  # HP Shaft
                {'radius': R * 0.80, 'length': L * 0.15, 'z_offset': L * 0.15  },  # HPC 1
                {'radius': R * 0.75, 'length': L * 0.15, 'z_offset': L * 0.30  },  # HPC 2
                {'radius': R * 0.60, 'length': L * 0.20, 'z_offset': L * 0.50  },  # Combustor
                {'radius': R * 0.80, 'length': L * 0.12, 'z_offset': L * 0.70  },  # HPT
                {'radius': R * 0.75, 'length': L * 0.18, 'z_offset': L * 0.82  },  # LPT
            ]

        elif self.engine_type == 'turbofan_3spool':
            return [
                {'radius': R * 1.60, 'length': L * 0.12, 'z_offset': -L * 0.12},  # Fan
                {'radius': R * 0.90, 'length': L * 0.12, 'z_offset': L * 0.12  },  # IPC
                {'radius': R * 0.78, 'length': L * 0.15, 'z_offset': L * 0.24  },  # HPC
                {'radius': R * 0.60, 'length': L * 0.18, 'z_offset': L * 0.44  },  # Combustor
                {'radius': R * 0.78, 'length': L * 0.10, 'z_offset': L * 0.62  },  # HPT
                {'radius': R * 0.88, 'length': L * 0.12, 'z_offset': L * 0.72  },  # IPT
                {'radius': R * 0.75, 'length': L * 0.16, 'z_offset': L * 0.84  },  # LPT
                {'radius': R * 0.10, 'length': L,        'z_offset': 0.0       },  # Triple shaft
            ]

        else:
            raise ValueError(
                f"Unknown engine_type '{self.engine_type}'. "
                "Choose: 'turbojet', 'turbofan_2spool', 'turbofan_3spool'."
            )

    @Part
    def stations(self):
        """
        Quantified FlowStation sequence.
        z_start = absolute global Z = z_core_start + z_offset (core-relative).
        """
        return FlowStation(
            quantify=len(self.station_definitions),
            radius  =self.station_definitions[child.index]['radius'],
            length  =self.station_definitions[child.index]['length'],
            z_start =(self.z_core_start
                      + self.station_definitions[child.index]['z_offset']),
        )

    @Attribute
    def total_void(self):
        """
        Iterative FusedSolid chain over station SOLIDS (not FlowStation objects).
        FusedSolid requires actual geometry (TopoDS solids), not GeomBase wrappers.
        This @Attribute is fine here: it returns the final fused solid object,
        which is then referenced as a tool in Engine.resulting_frame @Part.
        """
        solids = [st.solid for st in self.stations]
        result = solids[0]
        for s in solids[1:]:
            result = FusedSolid(shape_in=result, tool=s)
        return result


# =============================================================================
# LAYER 3 – EngineFrame
# =============================================================================

class EngineFrame(GeomBase):

    length_core        = Input(3.0)
    radius_core        = Input(0.35)
    length_inlet       = Input(0.8)
    radius_inlet_front = Input(0.55)
    length_nozzle      = Input(0.6)
    radius_nozzle_rear = Input(0.25)

    @Attribute
    def z_core_start(self):
        return self.length_inlet

    @Attribute
    def z_nozzle_start(self):
        return self.length_inlet + self.length_core

    @Part
    def inlet_cone(self):
        """
        Truncated cone: large radius at front (z=0), core radius at rear.
        radius1 = base of cone (local z=0 → global Z-front after rotate90).
        radius2 = top of cone  (local z=height → global Z-rear).
        # TODO: verify Cone radius1/radius2 front-vs-rear with Architect.
        """
        return Cone(
            radius1 =self.radius_inlet_front,
            radius2 =self.radius_core,
            height  =self.length_inlet,
            position=z_pos(0.0),
        )

    @Part
    def core_cylinder(self):
        return Cylinder(
            radius  =self.radius_core,
            height  =self.length_core,
            position=z_pos(self.z_core_start),
        )

    @Part
    def nozzle_cone(self):
        """
        Truncated cone: core radius at front, small exit radius at rear.
        # TODO: same Cone orientation caveat as inlet_cone.
        """
        return Cone(
            radius1 =self.radius_core,
            radius2 =self.radius_nozzle_rear,
            height  =self.length_nozzle,
            position=z_pos(self.z_nozzle_start),
        )

    @Part
    def envelope(self):
        return FusedSolid(
            shape_in=FusedSolid(
                shape_in=self.inlet_cone,
                tool    =self.core_cylinder,
            ),
            tool=self.nozzle_cone,
        )


# =============================================================================
# LAYER 4 – Engine (root)
# =============================================================================

class Engine(GeomBase):

    engine_type  = Input('turbojet')
    show_section = Input(True)

    frame_length_core        = Input(3.0)
    frame_radius_core        = Input(0.35)
    frame_length_inlet       = Input(0.8)
    frame_radius_inlet_front = Input(0.55)
    frame_length_nozzle      = Input(0.6)
    frame_radius_nozzle_rear = Input(0.25)

    @Attribute
    def total_length(self):
        return (self.frame_length_inlet
                + self.frame_length_core
                + self.frame_length_nozzle)

    @Attribute
    def sectioning_box_size(self):
        return self.total_length * 10.0

    @Part
    def frame(self):
        return EngineFrame(
            length_core        =self.frame_length_core,
            radius_core        =self.frame_radius_core,
            length_inlet       =self.frame_length_inlet,
            radius_inlet_front =self.frame_radius_inlet_front,
            length_nozzle      =self.frame_length_nozzle,
            radius_nozzle_rear =self.frame_radius_nozzle_rear,
        )

    @Part
    def duct(self):
        """
        Duct receives z_core_start explicitly so its stations compute
        absolute global Z positions without relying on position chaining.
        """
        return Duct(
            engine_type  =self.engine_type,
            core_length  =self.frame_length_core,
            core_radius  =self.frame_radius_core,
            z_core_start =self.frame_length_inlet,
        )

    @Part
    def resulting_frame(self):
        """
        Resulting_Frame = Subtraction(envelope, total_void).
        Uses duct.total_void (@Attribute returning a fused solid geometry object).
        Hidden when show_section=True.
        """
        return SubtractedSolid(
            shape_in=self.frame.envelope,
            tool    =self.duct.total_void,
            hidden  =self.show_section,
            color   ='silver',
        )

    @Part
    def sectioning_box(self):
        """
        Large Box filling the −Y half-space for section-view cut.
        # TODO: flip 'y' sign to expose the opposite half.
        """
        return Box(
            width   =self.sectioning_box_size,
            length  =self.sectioning_box_size,
            height  =self.sectioning_box_size,
            position=translate(
                XOY,
                'x', -self.sectioning_box_size / 2.0,
                'y', -self.sectioning_box_size,
            ),
            hidden=True,
        )

    @Part
    def section_view(self):
        return SubtractedSolid(
            shape_in=self.resulting_frame,
            tool    =self.sectioning_box,
            hidden  =not self.show_section,
            color   ='silver',
        )


# =============================================================================
# Entry point
# =============================================================================

if __name__ == '__main__':
    from parapy.gui import display

    engine = Engine(
        engine_type ='turbojet',
        show_section=True,
        label       ='Engine_Turbojet',
    )

    display(engine)