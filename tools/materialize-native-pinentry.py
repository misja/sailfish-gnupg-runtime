#!/usr/bin/env python3
"""Materialize pinned native pinentry sources from the public upstream fork."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

project = Path(__file__).resolve().parents[1]
root = project / "integrations/native-pinentry"
lock = json.loads((root / "sources.json").read_text())
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--checkout", type=Path, default=project.parent / "sailfish-secrets")
parser.add_argument("--variant", choices=("cache-free", "compat"), default="cache-free")
args = parser.parse_args()
checkout = args.checkout.resolve()
if not (checkout / ".git").exists():
    parser.error("Clone the fork beside this repository, or supply --checkout.")

def source(commit, name):
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise SystemExit("Expected a pinned commit ID")
    path = "LICENSE" if name == "LICENSE" else "plugins/gnupgplugin/pinentry/" + name
    return subprocess.check_output(["git", "-C", str(checkout), "show", commit + ":" + path])

def write(directory, name, data):
    if directory.is_symlink() or (directory / name).is_symlink():
        raise SystemExit("Refusing to write through a generated-source symlink")
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_bytes(data)

base = lock["upstream_commit"]
# Verify all source bytes before writing any generated input.
original = {name: source(base, name) for name in lock["files"]}
for name, data in original.items():
    if hashlib.sha256(data).hexdigest() != lock["files"][name]:
        raise SystemExit("Pinned upstream source mismatch: " + name)
variant = lock["fork_variants"][args.variant]
subprocess.run(["git", "-C", str(checkout), "merge-base", "--is-ancestor",
                base, variant["commit"]], check=True)
prepared = {name: source(variant["commit"], name) for name in variant["files"]}
for name, data in prepared.items():
    if hashlib.sha256(data).hexdigest() != variant["files"][name]:
        raise SystemExit("Pinned fork source mismatch: " + name)
for name, data in prepared.items():
    if name.endswith((".cpp", ".h")):
        for include in re.findall(rb'^\s*#include\s+"([^"]+)"', data, re.MULTILINE):
            header = include.decode("ascii")
            if header not in prepared:
                raise SystemExit("Missing quoted local header in source lock: " + header)
for name, data in original.items():
    write(root / "upstream", name, data)
destination = root / ("prepared" if args.variant == "cache-free" else "compat")
for name, data in prepared.items():
    write(destination, name, data)
print("Verified and materialized", args.variant, "at", variant["commit"])
