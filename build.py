"""Build script: package NetherIX using PyInstaller."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def build():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "NetherIX",
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--add-data", f"{ROOT / 'config.yaml'};.",
        "--add-data", f"{ROOT / 'assets'};assets",
        "--add-data", f"{ROOT / 'skills'};skills",
        "--hidden-import", "netherix",
        "--hidden-import", "netherix.pet",
        "--hidden-import", "netherix.brain",
        "--hidden-import", "netherix.automation",
        "--hidden-import", "netherix.skills",
        "--hidden-import", "netherix.skills.builtin",
        "--hidden-import", "netherix.ui",
        "--hidden-import", "netherix.voice",
        "--hidden-import", "edge_tts",
        "--hidden-import", "yaml",
        "--hidden-import", "loguru",
        "--hidden-import", "openai",
        "--hidden-import", "pyautogui",
        "--hidden-import", "keyboard",
        str(ROOT / "main.py"),
    ]

    icon_path = ROOT / "assets" / "icons" / "nix.ico"
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])

    print(f"Building NetherIX...")
    print(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode == 0:
        print(f"\nBuild successful! Output in: {ROOT / 'dist' / 'NetherIX'}")
    else:
        print(f"\nBuild failed with code {result.returncode}")
    return result.returncode


if __name__ == "__main__":
    sys.exit(build())
