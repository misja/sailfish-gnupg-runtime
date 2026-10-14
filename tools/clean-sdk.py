#!/usr/bin/env python3
"""Purge this prototype's disposable outputs; keep sources, evidence and RPMs."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path('/home/ubuntu/gnupg-runtime')
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--apply', action='store_true', help='Delete listed temporary files')
args = parser.parse_args()
if Path.cwd() != ROOT or ROOT.is_symlink():
    raise SystemExit('Run only in the approved LXC project directory')
directories = ['build', 'inspect', 'test-results', 'verify-home', 'scripts']
files = ['debugfiles.list', 'debuglinks.list', 'debugsourcefiles.list',
         'debugsources.list', 'documentation.list', 'elfbins.list',
         'rpm/synthetic-upgrade.spec']
paths = [ROOT / name for name in directories + files if (ROOT / name).exists()]
for path in paths:
    if path.is_symlink():
        raise SystemExit(f'Refusing symlink: {path}')
print('\n'.join(str(path.relative_to(ROOT)) for path in paths) or 'Already clean')
if not args.apply:
    raise SystemExit(0)
# Refuse cleanup while an agent references any of our synthetic homes.
processes = subprocess.check_output(['ps', '-eo', 'args'], text=True)
if any(str(ROOT / 'build') + '/' in line and
       any(command in line for command in ['gcc', 'g++', 'gpg-agent', 'configure'])
       for line in processes.splitlines()):
    raise SystemExit('Project build/runtime processes still active; refuse cleanup')
if any('gpg-agent' in line and str(ROOT / 'test-results') in line
       for line in processes.splitlines()):
    raise SystemExit('Stop scoped fixture agents before deleting their homes')
summary = ROOT / 'test-results/runtime-test.json'
if summary.is_file():
    shutil.copy2(summary, ROOT / 'evidence/last-synthetic-run.json')
removed = []
for path in paths:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    removed.append(str(path.relative_to(ROOT)))
(ROOT / 'evidence/cleanup.json').write_text(json.dumps({
    'removed': removed, 'retained': ['sources', 'evidence', 'RPMS', '.sfdk',
                                   'tools', 'runtime', 'rpm', 'sources.lock.json'],
    'scope': 'approved prototype outputs only; no Docker/LXD-wide prune'
}, indent=2) + '\n')
