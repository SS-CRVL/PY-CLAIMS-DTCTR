from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parent
    python_executable = sys.executable

    print(f"Running tests with: {python_executable}")
    result = subprocess.run(
        [python_executable, "-m", "pytest", "-q", "tests"],
        cwd=project_root,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
