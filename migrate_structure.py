#!/usr/bin/env python3
"""
migrate_structure.py
====================
Automates the directory restructuring and internal reference updates for the KBE project.
"""

import os
import shutil
from pathlib import Path

# Define root of the project (directory where migrate_structure.py is running)
ROOT = Path(__file__).resolve().parent

# Define directories to create
DIRS_TO_CREATE = [
    ROOT / "Thermodynamics",
    ROOT / "EngineCore",
    ROOT / "EngineCore" / "Ducts",
    ROOT / "EngineCore" / "Turbomachinery",
    ROOT / "EngineCore" / "Turbomachinery" / "Multall",
    ROOT / "IO_Management",
    ROOT / "IO_Management" / "work_dir",
    ROOT / "IO_Management" / "work_dir" / "compressor",
    ROOT / "IO_Management" / "work_dir" / "turbine",
]

# Mapping of file moves/renames relative to ROOT
FILE_MIGRATION_MAP = {
    "AeroEngine.py": "Aeroengine.py",
    "AeroEngine2.py": "Aeroengine2.py",
    "Flow_station.py": "Thermodynamics/FlowStation.py",
    "EngineComponent.py": "EngineCore/EngineComponent.py",
    "Combustor.py": "EngineCore/Combustor.py",
    "Duct.py": "EngineCore/Ducts/Duct.py",
    "Inlet.py": "EngineCore/Ducts/Inlet.py",
    "Nozzle.py": "EngineCore/Ducts/Nozzle.py",
    "EngineFrame.py": "EngineCore/Ducts/EngineFrame.py",
    "EngineFrame_Old.py": "EngineCore/Ducts/EngineFrame_Old.py",
    "Turbomachine.py": "EngineCore/Turbomachinery/Turbomachine.py",
    "Turbine.py": "EngineCore/Turbomachinery/Turbine.py",
    "Compressor.py": "EngineCore/Turbomachinery/Compressor.py",
    "Spool.py": "EngineCore/Turbomachinery/Spool.py",
    "Spool2.py": "EngineCore/Turbomachinery/Spool2.py",
    "Stage.py": "EngineCore/Turbomachinery/Stage.py",
    "Blade.py": "EngineCore/Turbomachinery/Blade.py",
    "plot_blade_profile.py": "EngineCore/Turbomachinery/plot_blade_profile.py",
    "Material.py": "EngineCore/Material.py",
    "material_database.py": "EngineCore/material_database.py",
    "aeroengine_materials.csv": "EngineCore/aeroengine_materials.csv",
    "MultallSolver.py": "EngineCore/Turbomachinery/Multall/MultallSolver.py",
    "StageParser.py": "EngineCore/Turbomachinery/Multall/StageParser.py",
    "MeagenParser.py": "EngineCore/Turbomachinery/Multall/MeangenParser.py",
}

# Subdirectories of Multall to move into EngineCore/Turbomachinery/Multall/
MULTALL_SUBDIRS = [
    "DesignExample",
    "Source",
    "executables",
    "scratch_low_fid",
    "smoke_cfd",
    "spool_0",
    "spool_2",
]

def create_structure():
    print("--- Creating directory structure ---")
    for d in DIRS_TO_CREATE:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {d.relative_to(ROOT)}")
        
    # Create empty __init__.py files
    init_files = [
        ROOT / "Thermodynamics" / "__init__.py",
        ROOT / "EngineCore" / "__init__.py",
        ROOT / "EngineCore" / "Ducts" / "__init__.py",
        ROOT / "EngineCore" / "Turbomachinery" / "__init__.py",
        ROOT / "EngineCore" / "Turbomachinery" / "Multall" / "__init__.py",
        ROOT / "IO_Management" / "__init__.py",
    ]
    for init in init_files:
        init.touch(exist_ok=True)
        print(f"Created empty init file: {init.relative_to(ROOT)}")
        
    # Create empty placeholders in IO_Management
    placeholders = [
        ROOT / "IO_Management" / "InputParser.py",
        ROOT / "IO_Management" / "ReportWriter.py",
    ]
    for p in placeholders:
        p.touch(exist_ok=True)
        print(f"Created placeholder file: {p.relative_to(ROOT)}")

def move_files():
    print("--- Moving and Renaming Files ---")
    for src_name, dst_rel in FILE_MIGRATION_MAP.items():
        src = ROOT / src_name
        dst = ROOT / dst_rel
        if src.exists():
            # Ensure parent destination directory exists
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            # If it is a case-only rename in the same directory, use a temp name first
            if src.parent == dst.parent and src.name.lower() == dst.name.lower() and src.name != dst.name:
                temp_name = src.with_name(src.name + ".temp_rename")
                if temp_name.exists():
                    temp_name.unlink()
                shutil.move(str(src), str(temp_name))
                shutil.move(str(temp_name), str(dst))
            else:
                # If destination already exists and is not the same file, delete it first
                if dst.exists() and dst.resolve() != src.resolve():
                    if dst.is_file():
                        dst.unlink()
                    else:
                        shutil.rmtree(dst)
                shutil.move(str(src), str(dst))
            print(f"Moved: {src_name} -> {dst_rel}")
        else:
            print(f"Skipping (not found): {src_name}")

    # Move Multall subdirectory folders
    multall_src_dir = ROOT / "Multall"
    multall_dst_dir = ROOT / "EngineCore" / "Turbomachinery" / "Multall"
    if multall_src_dir.exists() and multall_src_dir.is_dir():
        print("--- Moving Multall subdirectories ---")
        for sub in MULTALL_SUBDIRS:
            sub_src = multall_src_dir / sub
            sub_dst = multall_dst_dir / sub
            if sub_src.exists() and sub_src.is_dir():
                if sub_dst.exists():
                    shutil.rmtree(sub_dst)
                shutil.move(str(sub_src), str(sub_dst))
                print(f"Moved directory: Multall/{sub} -> EngineCore/Turbomachinery/Multall/{sub}")
        
        # Clean up empty Multall directory if it has no files/folders left
        try:
            # Check if there are any remaining files/folders
            remaining = list(multall_src_dir.iterdir())
            if not remaining:
                multall_src_dir.rmdir()
                print("Removed empty original Multall directory.")
            else:
                print(f"Original Multall directory still contains: {[f.name for f in remaining]}")
        except Exception as e:
            print(f"Error cleaning up original Multall directory: {e}")

def update_file_contents():
    print("--- Updating imports, executable paths, and parser names ---")
    
    # 1. Update Aeroengine.py (and Aeroengine2.py)
    for name in ["Aeroengine.py", "Aeroengine2.py"]:
        path = ROOT / name
        if path.exists():
            content = path.read_text(encoding="utf-8")
            
            # Replace imports
            content = content.replace("from EngineFrame import EngineFrame", "from EngineCore.Ducts.EngineFrame import EngineFrame")
            content = content.replace("from Combustor import Combustor", "from EngineCore.Combustor import Combustor")
            content = content.replace("from Spool import Spool", "from EngineCore.Turbomachinery.Spool import Spool")
            content = content.replace("from Flow_station import FlowStation", "from Thermodynamics.FlowStation import FlowStation")
            
            path.write_text(content, encoding="utf-8")
            print(f"Updated imports in {name}")

    # 2. Update FlowStation.py (system file only, no local imports)
    
    # 3. Update EngineComponent.py
    path = ROOT / "EngineCore" / "EngineComponent.py"
    if path.exists():
        content = path.read_text(encoding="utf-8")
        content = content.replace("from Flow_station import FlowStation", "from Thermodynamics.FlowStation import FlowStation")
        content = content.replace("from Material import Material", "from EngineCore.Material import Material")
        path.write_text(content, encoding="utf-8")
        print("Updated imports in EngineComponent.py")

    # 4. Update Combustor.py
    path = ROOT / "EngineCore" / "Combustor.py"
    if path.exists():
        content = path.read_text(encoding="utf-8")
        content = content.replace("from Flow_station import FlowStation", "from Thermodynamics.FlowStation import FlowStation")
        content = content.replace("from EngineComponent import EngineComponent", "from EngineCore.EngineComponent import EngineComponent")
        path.write_text(content, encoding="utf-8")
        print("Updated imports in Combustor.py")

    # 5. Update Duct.py
    path = ROOT / "EngineCore" / "Ducts" / "Duct.py"
    if path.exists():
        content = path.read_text(encoding="utf-8")
        content = content.replace("from Flow_station    import FlowStation", "from Thermodynamics.FlowStation import FlowStation")
        content = content.replace("from Flow_station import FlowStation", "from Thermodynamics.FlowStation import FlowStation")
        content = content.replace("from EngineComponent import EngineComponent", "from EngineCore.EngineComponent import EngineComponent")
        path.write_text(content, encoding="utf-8")
        print("Updated imports in Duct.py")

    # 6. Update Inlet.py
    path = ROOT / "EngineCore" / "Ducts" / "Inlet.py"
    if path.exists():
        content = path.read_text(encoding="utf-8")
        content = content.replace("from Duct import Duct", "from EngineCore.Ducts.Duct import Duct")
        content = content.replace("from Flow_station import FlowStation", "from Thermodynamics.FlowStation import FlowStation")
        path.write_text(content, encoding="utf-8")
        print("Updated imports in Inlet.py")

    # 7. Update Nozzle.py
    path = ROOT / "EngineCore" / "Ducts" / "Nozzle.py"
    if path.exists():
        content = path.read_text(encoding="utf-8")
        content = content.replace("from Flow_station import FlowStation", "from Thermodynamics.FlowStation import FlowStation")
        content = content.replace("from Duct import Duct", "from EngineCore.Ducts.Duct import Duct")
        path.write_text(content, encoding="utf-8")
        print("Updated imports in Nozzle.py")

    # 8. Update EngineFrame.py (and EngineFrame_Old.py)
    for name in ["EngineFrame.py", "EngineFrame_Old.py"]:
        path = ROOT / "EngineCore" / "Ducts" / name
        if path.exists():
            content = path.read_text(encoding="utf-8")
            content = content.replace("from Flow_station import FlowStation", "from Thermodynamics.FlowStation import FlowStation")
            content = content.replace("from Material import Material", "from EngineCore.Material import Material")
            content = content.replace("from Material     import Material", "from EngineCore.Material import Material")
            content = content.replace("from Duct import Duct", "from EngineCore.Ducts.Duct import Duct")
            content = content.replace("from Duct         import Duct", "from EngineCore.Ducts.Duct import Duct")
            content = content.replace("from Inlet import Inlet", "from EngineCore.Ducts.Inlet import Inlet")
            content = content.replace("from Inlet        import Inlet", "from EngineCore.Ducts.Inlet import Inlet")
            content = content.replace("from Nozzle import Nozzle", "from EngineCore.Ducts.Nozzle import Nozzle")
            content = content.replace("from Nozzle       import Nozzle", "from EngineCore.Ducts.Nozzle import Nozzle")
            path.write_text(content, encoding="utf-8")
            print(f"Updated imports in {name}")

    # 9. Update Turbomachine.py
    path = ROOT / "EngineCore" / "Turbomachinery" / "Turbomachine.py"
    if path.exists():
        content = path.read_text(encoding="utf-8")
        
        # Replace imports
        content = content.replace("from EngineComponent import EngineComponent", "from EngineCore.EngineComponent import EngineComponent")
        content = content.replace("from Stage import Stage", "from EngineCore.Turbomachinery.Stage import Stage")
        content = content.replace("from Material import Material", "from EngineCore.Material import Material")
        content = content.replace("from MultallSolver import MultallSolver", "from EngineCore.Turbomachinery.Multall.MultallSolver import MultallSolver")
        content = content.replace("from MeagenParser import MeagenParser", "from EngineCore.Turbomachinery.Multall.MeangenParser import MeangenParser")
        content = content.replace("from StageParser import StageParser", "from EngineCore.Turbomachinery.Multall.StageParser import StageParser")
        content = content.replace("from plot_blade_profile import plot_blade_profiles", "from EngineCore.Turbomachinery.plot_blade_profile import plot_blade_profiles")
        content = content.replace("from Flow_station import FlowStation", "from Thermodynamics.FlowStation import FlowStation")
        
        # Rename all other occurrences of MeagenParser to MeangenParser
        content = content.replace("MeagenParser", "MeangenParser")
        
        # Update executable default inputs to use dynamic path
        old_exe_block = """    work_dir = Input('Multall/DesignExample')
    \"\"\"Working directory for THIS machine's Multall files. Compressor and
    turbine must use different folders (e.g. .../multall/compressor).\"\"\"

    meangen_exe      = Input('Multall/executables/meangen-17.4.exe')
    stagen_exe       = Input('Multall/executables/stagen-18.1.exe')
    multall_exe      = Input('Multall/executables/multall-open-20.9.exe')"""
        
        new_exe_block = """    _base_dir = Path(__file__).resolve().parent
    work_dir = Input(str(_base_dir / 'Multall' / 'DesignExample'))
    \"\"\"Working directory for THIS machine's Multall files. Compressor and
    turbine must use different folders (e.g. .../multall/compressor).\"\"\"

    meangen_exe      = Input(str(_base_dir / 'Multall' / 'executables' / 'meangen-17.4.exe'))
    stagen_exe       = Input(str(_base_dir / 'Multall' / 'executables' / 'stagen-18.1.exe'))
    multall_exe      = Input(str(_base_dir / 'Multall' / 'executables' / 'multall-open-20.9.exe'))"""
        
        if old_exe_block in content:
            content = content.replace(old_exe_block, new_exe_block)
        else:
            # Fallback if whitespace differs
            content = content.replace("'Multall/DesignExample'", "str(Path(__file__).resolve().parent / 'Multall' / 'DesignExample')")
            content = content.replace("'Multall/executables/meangen-17.4.exe'", "str(Path(__file__).resolve().parent / 'Multall' / 'executables' / 'meangen-17.4.exe')")
            content = content.replace("'Multall/executables/stagen-18.1.exe'", "str(Path(__file__).resolve().parent / 'Multall' / 'executables' / 'stagen-18.1.exe')")
            content = content.replace("'Multall/executables/multall-open-20.9.exe'", "str(Path(__file__).resolve().parent / 'Multall' / 'executables' / 'multall-open-20.9.exe')")

        path.write_text(content, encoding="utf-8")
        print("Updated Turbomachine.py imports & executables paths")

    # 10. Update Turbine.py (and Compressor.py)
    for name in ["Turbine.py", "Compressor.py"]:
        path = ROOT / "EngineCore" / "Turbomachinery" / name
        if path.exists():
            content = path.read_text(encoding="utf-8")
            content = content.replace("from Turbomachine import Turbomachine", "from EngineCore.Turbomachinery.Turbomachine import Turbomachine")
            content = content.replace("from Flow_station import FlowStation", "from Thermodynamics.FlowStation import FlowStation")
            path.write_text(content, encoding="utf-8")
            print(f"Updated imports in {name}")

    # 11. Update Spool.py (and Spool2.py)
    for name in ["Spool.py", "Spool2.py"]:
        path = ROOT / "EngineCore" / "Turbomachinery" / name
        if path.exists():
            content = path.read_text(encoding="utf-8")
            content = content.replace("from Material import Material", "from EngineCore.Material import Material")
            content = content.replace("from Compressor import Compressor", "from EngineCore.Turbomachinery.Compressor import Compressor")
            content = content.replace("from Turbine import Turbine", "from EngineCore.Turbomachinery.Turbine import Turbine")
            content = content.replace("from Flow_station import FlowStation", "from Thermodynamics.FlowStation import FlowStation")
            content = content.replace("from MultallSolver import parse_shaft_power", "from EngineCore.Turbomachinery.Multall.MultallSolver import parse_shaft_power")
            path.write_text(content, encoding="utf-8")
            print(f"Updated imports in {name}")

    # 12. Update Stage.py
    path = ROOT / "EngineCore" / "Turbomachinery" / "Stage.py"
    if path.exists():
        content = path.read_text(encoding="utf-8")
        content = content.replace("from Blade import Blade", "from EngineCore.Turbomachinery.Blade import Blade")
        path.write_text(content, encoding="utf-8")
        print("Updated imports in Stage.py")

    # 13. Update Material.py
    path = ROOT / "EngineCore" / "Material.py"
    if path.exists():
        content = path.read_text(encoding="utf-8")
        content = content.replace("from material_database import MATERIAL_DB", "from EngineCore.material_database import MATERIAL_DB")
        path.write_text(content, encoding="utf-8")
        print("Updated imports in Material.py")

    # 14. Update material_database.py
    path = ROOT / "EngineCore" / "material_database.py"
    if path.exists():
        content = path.read_text(encoding="utf-8")
        
        # Replace default CSV path resolution
        old_fn = 'def build_material_db(csv_path: str = "aeroengine_materials.csv") -> dict:'
        new_fn = """def build_material_db(csv_path: str = None) -> dict:
    if csv_path is None:
        csv_path = str(Path(__file__).resolve().parent / "aeroengine_materials.csv")"""
        
        if old_fn in content:
            content = content.replace(old_fn, new_fn)
        else:
            content = content.replace('"aeroengine_materials.csv"', 'str(Path(__file__).resolve().parent / "aeroengine_materials.csv")')
            
        path.write_text(content, encoding="utf-8")
        print("Updated material_database.py dynamic CSV resolution")

    # 15. Update MultallSolver.py
    path = ROOT / "EngineCore" / "Turbomachinery" / "Multall" / "MultallSolver.py"
    if path.exists():
        content = path.read_text(encoding="utf-8")
        
        # Redefine PROJECT_ROOT and MULTALL_DIR
        old_root_def = "PROJECT_ROOT = Path(__file__).resolve().parent"
        new_root_def = """MULTALL_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = MULTALL_DIR.parent.parent.parent"""
        content = content.replace(old_root_def, new_root_def)
        
        # Redefine _resolve_absolute_path(path)
        old_resolve_fn = """def _resolve_absolute_path(path):
    \"\"\"Resolve a path to an absolute path relative to the PROJECT_ROOT.
    
    If the path is already absolute, it is returned unchanged.
    \"\"\"
    if not path:
        return path
    p = Path(path)
    if p.is_absolute():
        return str(p)
    return str((PROJECT_ROOT / p).resolve())"""
        
        new_resolve_fn = """def _resolve_absolute_path(path):
    \"\"\"Resolve a path to an absolute path relative to MULTALL_DIR or PROJECT_ROOT.
    
    If the path is already absolute, it is returned unchanged.
    \"\"\"
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
        
    return str((MULTALL_DIR / p).resolve())"""
        
        content = content.replace(old_resolve_fn, new_resolve_fn)
        
        # Update smoke test in MultallSolver.py
        content = content.replace("work_dir_path = base_dir / 'Multall' / 'DesignExample' / 'test_run_c'",
                                  "work_dir_path = base_dir / 'DesignExample' / 'test_run_c'")
        content = content.replace("exe_dir = base_dir / 'Multall' / 'executables'",
                                  "exe_dir = base_dir / 'executables'")
        content = content.replace("work    = base_dir / 'Multall' / 'smoke_cfd'",
                                  "work    = base_dir / 'smoke_cfd'")
        
        path.write_text(content, encoding="utf-8")
        print("Updated MultallSolver.py solver dynamic resolution and smoke test paths")

    # 16. Update MeangenParser.py (was MeagenParser.py)
    path = ROOT / "EngineCore" / "Turbomachinery" / "Multall" / "MeangenParser.py"
    if path.exists():
        content = path.read_text(encoding="utf-8")
        
        # Rename class and usages in file
        content = content.replace("class MeagenParser:", "class MeangenParser:")
        content = content.replace("MeagenParser.", "MeangenParser.")
        
        path.write_text(content, encoding="utf-8")
        print("Updated MeangenParser.py class name to MeangenParser")
        
    # 17. Update StageParser.py (comments referring to MeagenParser)
    path = ROOT / "EngineCore" / "Turbomachinery" / "Multall" / "StageParser.py"
    if path.exists():
        content = path.read_text(encoding="utf-8")
        content = content.replace("MeagenParser", "MeangenParser")
        path.write_text(content, encoding="utf-8")
        print("Updated StageParser.py comments")

if __name__ == "__main__":
    create_structure()
    move_files()
    update_file_contents()
    print("\n=== Restructuring Completed Successfully! ===")
