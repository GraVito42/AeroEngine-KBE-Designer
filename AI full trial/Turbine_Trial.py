# turbine_disk.py

import numpy as np
from math import radians, pi, cos, sin
from parapy.core import Input, Attribute, Part, child
from parapy.geom import (
    GeomBase, FittedCurve, ExtrudedSolid, FusedSolid,
    Cylinder, Point, Vector, translate, LoftedSolid
)


# ============================================================
# Profile DIAMOND
# ============================================================

def diamond_profile_global(chord, thickness_ratio, r_start, theta, stagger_deg, n=40):
    t_max = thickness_ratio * chord / 2.0
    s_half = np.linspace(0, chord, n)
    z_half = np.where(
        s_half <= chord / 2.0,
        t_max * (s_half / (chord / 2.0)),
        t_max * (1.0 - (s_half - chord / 2.0) / (chord / 2.0))
    )
    s_upper = s_half;         z_upper = z_half
    s_lower = s_half[::-1];   z_lower = -z_half[::-1]
    s_profile = np.concatenate([s_upper, s_lower[1:]])
    z_profile = np.concatenate([z_upper, z_lower[1:]])
    s_profile = np.append(s_profile, s_profile[0])
    z_profile = np.append(z_profile, z_profile[0])

    sg = radians(stagger_deg)
    cs, ss = cos(sg), sin(sg)
    s_rot = cs * s_profile - ss * z_profile
    z_rot = ss * s_profile + cs * z_profile

    rx, ry = cos(theta), sin(theta)
    tx, ty = -sin(theta), cos(theta)
    ox, oy = r_start * rx, r_start * ry

    pts = [Point(ox + si * tx, oy + si * ty, zi)
           for si, zi in zip(s_rot, z_rot)]
    return pts, Vector(rx, ry, 0.0)

# ============================================================
# Profile AIRFOIL da file .dat
# ============================================================

def load_dat_profile(dat_path):
    """
    Legge un file .dat in formato Selig o Lednicer.
    Restituisce due array numpy: x_c, z_c (coordinate normalizzate, corda=1).
    Filtra automaticamente la riga di intestazione (testo non numerico).
    """
    coords = []
    with open(dat_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            try:
                x, z = float(parts[0]), float(parts[1])
                coords.append((x, z))
            except (ValueError, IndexError):
                continue   # salta righe di intestazione o commenti

    coords = np.array(coords)

    # Rimuove duplicati consecutivi (es. doppio TE o LE)
    diffs = np.diff(coords, axis=0)
    mask = np.any(diffs != 0, axis=1)
    mask = np.append(mask, True)
    coords = coords[mask]

    # Assicura che il profilo sia chiuso (TE == primo punto)
    if not np.allclose(coords[0], coords[-1], atol=1e-6):
        coords = np.vstack([coords, coords[0]])

    return coords[:, 0], coords[:, 1]   # x/c,  z/c


def airfoil_profile_global(dat_path, chord, r_start, theta, stagger_deg):
    """
    Carica le coordinate da file .dat, scala per chord,
    applica stagger e trasforma in coordinate globali per la pala i.

    Il file .dat usa convenzione:
      colonna 0 = x/c  (0=LE, 1=TE)
      colonna 1 = z/c  (spessore, positivo verso upper surface)
    """
    xc, zc = load_dat_profile(dat_path)

    # Scala per la corda
    s_profile = xc * chord   # chordwise
    z_profile = zc * chord   # thickness / axial

    # Applica stagger nel piano (chord, thickness)
    sg = radians(stagger_deg)
    cs, ss = cos(sg), sin(sg)
    s_rot = cs * s_profile - ss * z_profile
    z_rot = ss * s_profile + cs * z_profile

    # Base globale per la pala i-esima
    rx, ry = cos(theta), sin(theta)    # radiale (span)
    tx, ty = -sin(theta), cos(theta)   # tangenziale (corda)
    ox, oy = r_start * rx, r_start * ry

    pts = [Point(ox + si * tx, oy + si * ty, zi)
           for si, zi in zip(s_rot, z_rot)]
    return pts, Vector(rx, ry, 0.0)

def profile_points_at_r(profile_type, dat_path, chord,
                         thickness_ratio, r, theta, stagger_deg,
                         n_pts=40):
    """
    Restituisce la lista di Point per un profilo posizionato
    a raggio r, angolo theta, con la corda specificata.
    Usato per costruire le 3 sezioni del loft.
    """
    if profile_type == "diamond":
        pts, _ = diamond_profile_global(
            chord           = chord,
            thickness_ratio = thickness_ratio,
            r_start         = r,
            theta           = theta,
            stagger_deg     = stagger_deg,
            n               = n_pts,
        )
    else:
        pts, _ = airfoil_profile_global(
            dat_path    = dat_path,
            chord       = chord,
            r_start     = r,
            theta       = theta,
            stagger_deg = stagger_deg,
        )
    return pts

# ============================================================
# Blade
# ============================================================

class Blade(GeomBase):
    pts         = Input([])
    extrude_vec = Input(Vector(1, 0, 0))
    span        = Input(0.10)

    @Part
    def profile_curve(self):
        return FittedCurve(points=self.pts)

    @Part
    def solid(self):
        return ExtrudedSolid(
            island=self.profile_curve,
            direction=self.extrude_vec,
            distance=self.span,
        )

class LoftedBlade(GeomBase):
    """
    Genera una pala 3D tramite loft tra 3 profili:
      - sezione al hub    (r=0,         chord=chord_hub)
      - sezione a metà    (r=span/2,    chord=chord_mid)
      - sezione alla tip  (r=span,      chord=chord_tip)

    Tutti i profili sono già in coordinate globali (nessun position trick).
    """
    # Punti delle 3 sezioni — calcolati esternamente da TurbineDisk
    pts_hub  = Input([])
    pts_mid  = Input([])
    pts_tip  = Input([])

    @Part
    def curve_hub(self):
        return FittedCurve(points=self.pts_hub)

    @Part
    def curve_mid(self):
        return FittedCurve(points=self.pts_mid)

    @Part
    def curve_tip(self):
        return FittedCurve(points=self.pts_tip)

    @Part
    def solid(self):
        return LoftedSolid(
            profiles=[
                self.curve_hub,
                self.curve_mid,
                self.curve_tip,
            ],
        )

# ============================================================
# Hub
# ============================================================

class Hub(GeomBase):
    hub_radius    = Input(0.05)
    hub_thickness = Input(0.02)

    @Part
    def solid(self):
        return Cylinder(
            radius=self.hub_radius,
            height=self.hub_thickness,
            centered=True,
            position=translate(
                self.position,
                Vector(0, 0, -1), -self.hub_thickness / 2.0
            ),
            color="gray",
        )


# ============================================================
# TurbineDisk Master
# ============================================================

class TurbineDisk(GeomBase):

    hub_radius       = Input(0.05)
    hub_thickness    = Input(0.02)
    chord            = Input(0.05)
    thickness_ratio  = Input(0.20)      # usato solo per profile="diamond"
    span             = Input(0.08)
    n_blades         = Input(9)
    stagger_angle    = Input(30.0)
    n_profile_pts    = Input(40)        # usato solo per profile="diamond"
    profile          = Input("diamond") # "diamond" oppure "airfoil"
    airfoil_dat_path = Input("")        # path al file .dat, usato se profile="airfoil"

    loft_profile_hub = Input("diamond")  # profilo alla radice
    loft_profile_mid = Input("diamond")  # profilo a metà span
    loft_profile_tip = Input("diamond")  # profilo alla tip
    loft_chord_hub = Input(0.05)  # corda alla radice
    loft_chord_mid = Input(0.04)  # corda a metà span
    loft_chord_tip = Input(0.025)  # corda alla tip

    @Attribute
    def delta_theta(self):
        return 2.0 * pi / self.n_blades

    @Attribute
    def blade_geometry(self):
        geoms = []
        for i in range(self.n_blades):
            theta = i * self.delta_theta

            if self.profile == "diamond":
                pts, evec = diamond_profile_global(
                    chord=self.chord,
                    thickness_ratio=self.thickness_ratio,
                    r_start=0.0,
                    theta=theta,
                    stagger_deg=self.stagger_angle,
                    n=self.n_profile_pts,
                )
                geoms.append(("extrude", pts, evec))

            elif self.profile == "airfoil":
                if not self.airfoil_dat_path:
                    raise ValueError("airfoil_dat_path deve essere specificato.")
                pts, evec = airfoil_profile_global(
                    dat_path=self.airfoil_dat_path,
                    chord=self.chord,
                    r_start=0.0,
                    theta=theta,
                    stagger_deg=self.stagger_angle,
                )
                geoms.append(("extrude", pts, evec))

            elif self.profile == "loft":
                # Genera i punti delle 3 sezioni al raggio corretto
                def _pts(loft_prof, chord_val, r_val):
                    return profile_points_at_r(
                        profile_type="diamond" if loft_prof == "diamond" else "airfoil",
                        dat_path=loft_prof if loft_prof != "diamond" else "",
                        chord=chord_val,
                        thickness_ratio=self.thickness_ratio,
                        r=r_val,
                        theta=theta,
                        stagger_deg=self.stagger_angle,
                        n_pts=self.n_profile_pts,
                    )

                pts_hub = _pts(self.loft_profile_hub, self.loft_chord_hub, 0.0)
                pts_mid = _pts(self.loft_profile_mid, self.loft_chord_mid, self.span / 2.0)
                pts_tip = _pts(self.loft_profile_tip, self.loft_chord_tip, self.span)
                geoms.append(("loft", pts_hub, pts_mid, pts_tip))

            else:
                raise ValueError(f"profile='{self.profile}' non riconosciuto.")

        return geoms

    @Part
    def hub(self):
        return Hub(
            hub_radius    = self.hub_radius,
            hub_thickness = self.hub_thickness,
            position      = self.position,
        )

    @Part
    def blades_extruded(self):
        """Attivo quando profile='diamond' o 'airfoil'."""
        return Blade(
            quantify=self.n_blades,
            pts=self.blade_geometry[child.index][1],
            extrude_vec=self.blade_geometry[child.index][2],
            span=self.span,
            color="steelblue",
            hidden=self.profile not in ("diamond", "airfoil"),
        )

    @Part
    def blades_lofted(self):
        """Attivo quando profile='loft'."""
        return LoftedBlade(
            quantify=self.n_blades,
            pts_hub=self.blade_geometry[child.index][1],
            pts_mid=self.blade_geometry[child.index][2],
            pts_tip=self.blade_geometry[child.index][3],
            color="steelblue",
            hidden=self.profile != "loft",
        )

    @Attribute
    def fused_disk_shape(self):
        """Seleziona il set di pale corretto in base a profile."""
        if self.profile in ("diamond", "airfoil"):
            blade_solids = [self.blades_extruded[i].solid
                            for i in range(self.n_blades)]
        else:
            blade_solids = [self.blades_lofted[i].solid
                            for i in range(self.n_blades)]

        result = self.hub.solid
        for sol in blade_solids:
            result = FusedSolid(
                shape_in=result,
                tool=sol,
                fuzzy_value=1e-4,
            )
        result = FusedSolid(
            shape_in=result,
            tool=self.hub.solid,
            fuzzy_value=1e-4,
        )
        return result

    @Part(parse=False)
    def fused_disk(self):
        return self.fused_disk_shape


# ============================================================
# Entry point
# ============================================================

if __name__ == '__main__':
    from parapy.gui import display

    # Loft con diamond alla hub, airfoil a mid e tip
    disk = TurbineDisk(
        hub_radius       = 0.03,
        hub_thickness    = 0.01,
        span             = 0.08,
        n_blades         = 9,
        stagger_angle    = 30.0,
        profile          = "loft",
        loft_profile_hub = "diamond",       # rombo alla radice
        loft_profile_mid = r"C:\Users\Vito\Documents\UNI- Corsi\TUDELFT\Q3\KBE\Parapy\Tutorial 5\tutorial_5_exercises\whitcomb.dat",
        loft_profile_tip = r"C:\Users\Vito\Documents\UNI- Corsi\TUDELFT\Q3\KBE\Parapy\Tutorial 5\tutorial_5_exercises\n63112.dat",
        loft_chord_hub   = 0.012,   # corda larga alla radice
        loft_chord_mid   = 0.020,
        loft_chord_tip   = 0.025,   # corda più stretta alla tip
        thickness_ratio  = 0.20,
    )

    display(disk)