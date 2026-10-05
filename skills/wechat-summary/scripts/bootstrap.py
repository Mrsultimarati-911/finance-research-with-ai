"""Create an isolated environment at an explicit destination; no host config edits."""
import argparse
from pathlib import Path
import subprocess
import sys
import venv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", type=Path, required=True)
    parser.add_argument("--lock", action="store_true", help="Use the Windows/Python 3.12 dependency lock")
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        parser.error("Use Python 3.12 or later")
    if args.lock and (sys.platform != "win32" or sys.version_info[:2] != (3, 12)):
        parser.error("This dependency lock is for Windows Python 3.12; omit --lock for other environments")
    destination = args.env.resolve()
    if destination.exists() and any(destination.iterdir()) and not (destination / "pyvenv.cfg").is_file():
        parser.error("Destination contains files and is not a virtual environment")
    venv.EnvBuilder(with_pip=True).create(destination)
    python = destination / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    root = Path(__file__).resolve().parents[1]
    requirements = root / ("requirements-lock-windows-py312.txt" if args.lock else "requirements.txt")
    subprocess.run([str(python), "-m", "pip", "install", "-r", str(requirements)], check=True)
    print(f"MCP command: {python}\nMCP args: {root / 'scripts/wechat_mcp.py'}")


if __name__ == "__main__":
    main()
