#!/usr/bin/env python3
"""Authenticate public runtime sources using the sibling workspace tooling."""
import subprocess
import sys
from pathlib import Path

project = Path(__file__).resolve().parents[1]
tool = project.parent / "sailfish-workspace/tools/fetch-sources.py"
if not tool.is_file():
    raise SystemExit("Clone sailfish-workspace beside this repository; see docs/FORK_WORKFLOW.md")
subprocess.run([sys.executable, str(tool), "--root", str(project.parent),
                "--component", "runtime", *sys.argv[1:]], check=True)
