#!/usr/bin/env python3
"""Materialize the pinned cache-free prototype from the upstream fork."""
from pathlib import Path
import subprocess
import sys

tool = Path(__file__).resolve().parents[2] / "tools/materialize-native-pinentry.py"
raise SystemExit(subprocess.call([sys.executable, str(tool), *sys.argv[1:]]))
