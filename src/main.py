import sys
from pathlib import Path

# Ensure project root (src) is in sys.path
for parent in Path(__file__).resolve().parents:
    if (parent / "EngineCore").exists() and (parent / "Thermodynamics").exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break

if __name__ == '__main__':
    from IO_Management.InputParser import InputParser
    print("Launching AeroEngine Designer GUI...")
    parser = InputParser()
    parser.launch_gui()
