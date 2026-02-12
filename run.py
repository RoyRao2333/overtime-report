import sys
from pathlib import Path

from overtime_report.main import app

# Add src to sys.path to ensure modules can be imported
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))


if __name__ == "__main__":
    app()
