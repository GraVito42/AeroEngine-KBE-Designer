# report_writer.py
import os
import csv

from parapy.core import Base, Input, Attribute
from parapy.exchange import STEPWriter

# pip install reportlab --break-system-packages
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image as RLImage, KeepTogether
)
from reportlab.lib import colors

from EngineCore.Turbomachinery.plot_blade_profile import plot_blade_profiles


class ReportWriter(Base):
    """
    Output handler for AeroEngine. Instantiated as @Part inside AeroEngine.
    All data received as @Input — no pull from self.parent, no circular deps.
    Plain methods handle all file I/O (side effects must not live in @Attribute).
    """

    # ------------------------------------------------------------------
    # INPUT — output directory
    # ------------------------------------------------------------------

    output_path: str = Input("output")

    # ------------------------------------------------------------------
    # INPUTS — summary @Attributes from AeroEngine (passed directly)
    # ------------------------------------------------------------------

    performance_summary: dict = Input({})
    # Populated by AeroEngine.performance_summary @Attribute.
    # Keys: "Thrust [N]", "TSFC [kg/N/s]", "Exhaust Velocity [m/s]", ...

    geometry_summary: dict = Input({})
    # Populated by AeroEngine.geometry_summary @Attribute.
    # Keys: "Total Length [m]", "Max Diameter [m]", "Total Weight [kg]", ...

    # ------------------------------------------------------------------
    # INPUTS — raw dicts from InputParser (passed through AeroEngine)
    # ------------------------------------------------------------------

    engine_features: dict = Input({})
    engine_geometry: dict = Input({})
    engine_materials: dict = Input({})

    # ------------------------------------------------------------------
    # INPUTS — blade stage data for plots and CSV
    # ------------------------------------------------------------------

    compressor_stage_data: list = Input([])
    # List of stage dicts as produced by StageParser / MeangenParser.merge().
    # [{"rotor": {"suction": [[...]], "pressure": [[...]], "r_sections": [...],
    #             "span_fractions": [...], "chords": [...], "n_blades": int},
    #   "stator": {...},
    #   "_row_order": ["rotor", "stator"]}, ...]
    # Passed from AeroEngine.compressor.stage_data.

    turbine_stage_data: list = Input([])
    # Same structure, from AeroEngine.turbine.stage_data.

    # ------------------------------------------------------------------
    # INPUTS — pre-rendered image paths for appendices C and D
    # ------------------------------------------------------------------

    axial_section_path: str = Input("")
    # PNG of engine longitudinal cross-section, rendered by AeroEngine
    # from EngineFrame geometry before calling export.

    ts_diagram_path: str = Input("")
    # PNG of T-S thermodynamic cycle diagram, rendered by AeroEngine
    # from FlowStation data before calling export.

    # ------------------------------------------------------------------
    # INPUTS — ParaPy @Part references for STEP export
    # ------------------------------------------------------------------

    full_assembly_parts: list = Input([])
    # [engine.spool, engine.engine_frame, engine.combustor]
    # NOTE: ParaPy @Part objects — do not serialize; passed at runtime.

    engine_frame_parts: list = Input([])
    # [engine.engine_frame]

    spool_parts: list = Input([])
    # [engine.spool]

    # ------------------------------------------------------------------
    # HELPER
    # ------------------------------------------------------------------

    def _ensure_output_dir(self, subdir=None):
        path = os.path.join(self.output_path, subdir) if subdir else self.output_path
        os.makedirs(path, exist_ok=True)
        return path

    # ------------------------------------------------------------------
    # STEP EXPORT
    # ------------------------------------------------------------------

    def _get_clean_parts(self, parts):
        clean = []
        for p in parts:
            name = p.__class__.__name__
            if name == "Combustor":
                clean.append(p.body)
            elif name == "EngineFrame":
                clean.append(p.body)
            elif name == "Spool":
                clean.append(p.body)
                if hasattr(p, 'compressor') and hasattr(p.compressor, 'body'):
                    for stage in p.compressor.body:
                        if hasattr(stage, 'rotor_blades') and stage.rotor_blades.built_from:
                            clean.append(stage.rotor_blades)
                        if hasattr(stage, 'stator_blades') and stage.stator_blades.built_from:
                            clean.append(stage.stator_blades)
                if hasattr(p, 'turbine') and hasattr(p.turbine, 'body'):
                    for stage in p.turbine.body:
                        if hasattr(stage, 'rotor_blades') and stage.rotor_blades.built_from:
                            clean.append(stage.rotor_blades)
                        if hasattr(stage, 'stator_blades') and stage.stator_blades.built_from:
                            clean.append(stage.stator_blades)
            else:
                clean.append(p)
        return clean

    def export_stp(self):
        """
        Export three STEP files:
          - full_assembly.step     : spool + engine_frame + combustor
          - engine_frame.step      : frame only (for external CFD)
          - spools_and_blades.step : spool only (for FEM)
        """
        self._ensure_output_dir()

        step_exports = {
            "full_assembly.step":     self.full_assembly_parts,
            "engine_frame.step":      self.engine_frame_parts,
            "spools_and_blades.step": self.spool_parts,
        }

        exported = []
        for filename, parts in step_exports.items():
            if not parts:
                print(f"[ReportWriter] Skipping {filename} — no parts provided.")
                continue
            filepath = os.path.join(self.output_path, filename)
            clean_parts = self._get_clean_parts(parts)
            STEPWriter(clean_parts).write(filepath)
            print(f"[ReportWriter] STEP exported → {filepath}")
            exported.append(filepath)

        return exported

    # ------------------------------------------------------------------
    # CSV EXPORT
    # ------------------------------------------------------------------

    def export_csv(self):
        """
        Export two CSV files with closed mid-span blade profiles (rotor + stator)
        for each stage.
          - compressor_blade_profiles.csv
          - turbine_blade_profiles.csv

        One row per point. Columns:
          stage, row_type, point_idx, x, y

        Profile is closed: suction LE→TE + pressure reversed TE→LE + back to LE.
        Section used: mid-span (section index = n_sections // 2).
        """
        self._ensure_output_dir()
        exported = []

        datasets = {
            "compressor_blade_profiles.csv": self.compressor_stage_data,
            "turbine_blade_profiles.csv":    self.turbine_stage_data,
        }

        for filename, stage_data in datasets.items():
            if not stage_data:
                print(f"[ReportWriter] Skipping {filename} — no stage data provided.")
                continue

            filepath = os.path.join(self.output_path, filename)
            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["stage", "row_type", "point_idx", "x", "y"])

                for stage_idx, stage in enumerate(stage_data):
                    row_order = stage.get("_row_order", ["rotor", "stator"])
                    for row_name in row_order:
                        row = stage.get(row_name)
                        if row is None:
                            continue

                        n_sections = len(row.get("suction", []))
                        if n_sections == 0:
                            continue

                        mid = n_sections // 2
                        suc = row["suction"][mid]   # [(x,y), ...]  LE→TE
                        prs = row["pressure"][mid]  # [(x,y), ...]  LE→TE

                        # Closed outline: suc LE→TE, prs reversed TE→LE, close to LE
                        outline = suc + list(reversed(prs))[1:-1] + [suc[0]]

                        for pt_idx, (x, y) in enumerate(outline):
                            writer.writerow([
                                stage_idx + 1,
                                row_name,
                                pt_idx,
                                f"{x:.8f}",
                                f"{y:.8f}",
                            ])

            print(f"[ReportWriter] CSV exported → {filepath}")
            exported.append(filepath)

        return exported

    # ------------------------------------------------------------------
    # BLADE PROFILE PLOTS
    # ------------------------------------------------------------------

    def _render_blade_plots(self):
        """
        Call plot_blade_profiles() for compressor and turbine, saving PNGs
        to output/blade_plots/{compressor,turbine}/.

        plot_blade_profiles() with save_dir != None saves exactly 3 files:
          all_stages_mid.png, all_stages_tip.png, all_stages_hub.png

        Returns dict: {"compressor": [path1, path2, path3], "turbine": [...]}
        """
        blade_dir = self._ensure_output_dir("blade_plots")
        saved_paths = {}

        for machine_type, stage_data in (
            ("compressor", self.compressor_stage_data),
            ("turbine",    self.turbine_stage_data),
        ):
            if not stage_data:
                print(f"[ReportWriter] No {machine_type} stage data — skipping plots.")
                saved_paths[machine_type] = []
                continue

            sub_dir = os.path.join(blade_dir, machine_type)
            plot_blade_profiles(stage_data, machine_type=machine_type, save_dir=sub_dir)

            saved_paths[machine_type] = [
                os.path.join(sub_dir, "all_stages_mid.png"),
                os.path.join(sub_dir, "all_stages_tip.png"),
                os.path.join(sub_dir, "all_stages_hub.png"),
            ]

        return saved_paths

    # ------------------------------------------------------------------
    # PDF REPORT
    # ------------------------------------------------------------------

    def report_results(self):
        """
        Generate the PDF design report. Renders blade plots internally.

        Structure:
          1. Input Parameters (traceability)
          2. Performance Summary
          3. Geometry Summary
          Appendix A — Compressor Blade Profiles
          Appendix B — Turbine Blade Profiles
          Appendix C — Engine Axial Cross-Section
          Appendix D — Thermodynamic Cycle (T-S Diagram)
        """
        self._ensure_output_dir()

        # Render blade PNGs before building the PDF
        blade_paths = self._render_blade_plots()

        filepath = os.path.join(self.output_path, "aero_engine_report.pdf")

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=2.5 * cm, rightMargin=2.5 * cm,
            topMargin=2.5 * cm,  bottomMargin=2.5 * cm,
        )

        styles  = getSampleStyleSheet()
        s_title = ParagraphStyle("RWTitle", parent=styles["Title"],
                                 fontSize=20, spaceAfter=14)
        s_h1    = ParagraphStyle("RWH1",    parent=styles["Heading1"],
                                 fontSize=14, spaceBefore=18, spaceAfter=8)
        s_h2    = ParagraphStyle("RWH2",    parent=styles["Heading2"],
                                 fontSize=11, spaceBefore=12, spaceAfter=6)
        s_cap   = ParagraphStyle("RWCap",   parent=styles["Normal"],
                                 fontSize=9,  spaceAfter=4,
                                 textColor=colors.grey)

        tbl_style = TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0),  colors.HexColor("#1a3a5c")),
            ("TEXTCOLOR",      (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",       (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",       (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ("GRID",           (0, 0), (-1, -1), 0.4, colors.grey),
            ("LEFTPADDING",    (0, 0), (-1, -1), 7),
            ("RIGHTPADDING",   (0, 0), (-1, -1), 7),
            ("TOPPADDING",     (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",  (0, 0), (-1, -1), 4),
        ])

        def _make_table(data_dict):
            rows = [["Parameter", "Value"]]
            for k, v in data_dict.items():
                rows.append([str(k), f"{v:.5g}" if isinstance(v, float) else str(v)])
            t = Table(rows, colWidths=[9 * cm, 6 * cm])
            t.setStyle(tbl_style)
            return t

        def _insert_image(path, caption, max_w=14 * cm, max_h=10 * cm):
            if path and os.path.isfile(path):
                return [
                    RLImage(path, width=max_w, height=max_h, kind="proportional"),
                    Paragraph(caption, s_cap),
                    Spacer(1, 0.3 * cm),
                ]
            return [
                Paragraph(f"[Image not available: {os.path.basename(path)}]", s_cap),
                Spacer(1, 0.2 * cm),
            ]

        story = []

        # ---- Title ----
        story.append(Paragraph("AeroEngine KBE — Design Report", s_title))
        story.append(Spacer(1, 0.5 * cm))

        # ---- Section 1: Input traceability ----
        story.append(Paragraph("1. Input Parameters", s_h1))
        for label, data in (
                ("1.1 Engine Features", self.engine_features),
                ("1.2 Engine Geometry Inputs", self.engine_geometry),
                ("1.3 Material Selections", self.engine_materials),
        ):
            block = [
                Paragraph(label, s_h2),
                _make_table(data) if data
                else Paragraph("No data provided.", styles["Normal"]),
                Spacer(1, 0.3 * cm),
            ]
            story.append(KeepTogether(block))

        # ---- Section 2: Performance summary ----
        story.append(Paragraph("2. Performance Summary", s_h1))
        story.append(
            _make_table(self.performance_summary) if self.performance_summary
            else Paragraph("No performance data available.", styles["Normal"])
        )

        # ---- Section 3: Geometry summary ----
        story.append(Paragraph("3. Geometry Summary", s_h1))
        story.append(
            _make_table(self.geometry_summary) if self.geometry_summary
            else Paragraph("No geometry data available.", styles["Normal"])
        )

        # ---- Appendix A: Compressor blade profiles ----
        story.append(PageBreak())
        story.append(Paragraph("Appendix A — Compressor Blade Profiles", s_h1))
        for path, caption in zip(
            blade_paths.get("compressor", []),
            ["Figure A.1: Mid-span profiles — all compressor stages.",
             "Figure A.2: Tip sections — all compressor stages.",
             "Figure A.3: Hub sections — all compressor stages."],
        ):
            story += _insert_image(path, caption, max_h=12 * cm)

        # ---- Appendix B: Turbine blade profiles ----
        story.append(PageBreak())
        story.append(Paragraph("Appendix B — Turbine Blade Profiles", s_h1))
        for path, caption in zip(
            blade_paths.get("turbine", []),
            ["Figure B.1: Mid-span profiles — all turbine stages.",
             "Figure B.2: Tip sections — all turbine stages.",
             "Figure B.3: Hub sections — all turbine stages."],
        ):
            story += _insert_image(path, caption, max_h=12 * cm)

        # ---- Appendix C: Axial cross-section ----
        story.append(PageBreak())
        story.append(Paragraph("Appendix C — Engine Axial Cross-Section", s_h1))
        story += _insert_image(
            self.axial_section_path,
            "Figure C.1: Longitudinal cross-section of the engine frame.",
            max_h=13 * cm,
        )

        # ---- Appendix D: T-S diagram ----
        story.append(Paragraph("Appendix D — Thermodynamic Cycle (T-S Diagram)", s_h1))
        story += _insert_image(
            self.ts_diagram_path,
            "Figure D.1: T-S diagram of the thermodynamic cycle.",
            max_h=13 * cm,
        )

        doc.build(story)
        print(f"[ReportWriter] PDF exported → {filepath}")
        return filepath

    # ------------------------------------------------------------------
    # CONVENIENCE
    # ------------------------------------------------------------------

    def export_all(self):
        """Run all exports: STEP + CSV + PDF (blade plots rendered internally)."""
        step_files = self.export_stp()
        csv_files  = self.export_csv()
        pdf_file   = self.report_results()
        return {"step": step_files, "csv": csv_files, "pdf": pdf_file}