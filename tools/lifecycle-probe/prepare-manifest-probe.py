#!/usr/bin/env python3
"""Stage the inert manifest-ordering RPM probe; never run builds or install."""
import argparse
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('output', type=Path)
args = parser.parse_args()
output = args.output.absolute()
if output.exists() or output.is_symlink():
    raise SystemExit('Refusing to replace an existing probe directory')
output.mkdir(parents=True)
(output / 'runtime').mkdir()
for name in ('sailfish-gpg', 'sailfish-gpg-agent', 'runtime-policy.sh',
             'gpg-operation', 'agent-operation', 'lifecycle-entry.py',
             'lifecycle_admission.py', 'lifecycle_control.py', 'lifecycle-admin.py'):
    source = root / 'runtime' / name
    if source.is_symlink() or not source.is_file():
        raise SystemExit('Expected regular public runtime input: ' + name)
    shutil.copyfile(source, output / 'runtime' / name)
(output / 'tools').mkdir()
shutil.copyfile(root / 'tools/build-payload-manifest.py', output / 'tools/build-payload-manifest.py')
hook = (root / 'rpm/sailfish-gnupg-private.spec').read_text().split('%global private_prefix')[0]
template = (root / 'tools/lifecycle-probe/manifest-probe.spec.in').read_text()
if template.count('@REAL_HOOK@') != 1:
    raise SystemExit('Missing unique production install-post hook placeholder')
(output / 'probe.spec').write_text(template.replace('@REAL_HOOK@', hook))
shutil.copyfile(root / 'tools/lifecycle-probe/manifest-probe.c', output / 'probe.c')
shutil.copyfile(root / 'tools/lifecycle-probe/inspect-manifest-probe.py', output / 'check-probe.py')
print(output)
