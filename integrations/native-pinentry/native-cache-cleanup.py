#!/usr/bin/env python3
"""Remove only the exact, empty, completed keyless cache fixture."""
import hashlib,json,os,stat,tempfile
from pathlib import Path
assert os.getuid()==os.geteuid()==100000
os.umask(0o077)
STAGE=Path('/var/tmp/sailfish-native-cache.39nxFI')
info=STAGE.lstat();assert stat.S_ISDIR(info.st_mode) and info.st_uid==100000 and stat.S_IMODE(info.st_mode)==0o700 and STAGE.resolve()==STAGE
STATE=STAGE/'cache-attempt.json'
info=STATE.lstat();assert stat.S_ISREG(info.st_mode) and info.st_uid==100000 and stat.S_IMODE(info.st_mode)==0o600 and info.st_nlink==1
def syncdir():
 fd=os.open(STAGE,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
assert hashlib.sha256(STATE.read_bytes()).hexdigest()=='e44affbae69dffbdfcf248ef4c50bcec3e96ec414ae4d0739a1f0d7224c25223'
p=json.loads(STATE.read_text())
fixture=Path('/var/tmp/synthetic-native-cache-mnj7jjr_')
assert p['fixture']==str(fixture) and p['complete'] is True
assert len(p['agents'])==2 and all(a['reaped'] and a['startup_policy_verified'] for a in p['agents'])
assert not any(k in p for k in ('pending_launch','pending_operation','failure_cleanup'))
for a in p['agents']:assert not Path('/proc',str(a['pid'])).exists()
for path in Path('/proc').iterdir():
 if not path.name.isdigit():continue
 try:
  if path.stat().st_uid!=100000:continue
  if not (path/'comm').read_text().strip().startswith('pinentry'):continue
  assert os.readlink(path/'exe')!=str(STAGE/'pinentry')
 except FileNotFoundError:continue
home=fixture/'gnupg';keys=home/'private-keys-v1.d';marker=fixture/'.synthetic-fixture'
for path in (fixture,home,keys):
 info=path.lstat();assert stat.S_ISDIR(info.st_mode) and info.st_uid==100000 and stat.S_IMODE(info.st_mode)==0o700 and path.resolve()==path
assert {v.name for v in fixture.iterdir()}=={'.synthetic-fixture','gnupg'}
assert {v.name for v in home.iterdir()}=={'private-keys-v1.d'} and not list(keys.iterdir())
info=marker.lstat();assert stat.S_ISREG(info.st_mode) and info.st_uid==100000 and info.st_nlink==1 and stat.S_IMODE(info.st_mode)==0o600
assert marker.read_bytes()==b'native-agent-cache-lifecycle-v1\n'
with (STAGE/'cache-cleanup.json').open('x') as f:
 json.dump({'fixture':str(fixture),'intent':'Exact nonrecursive empty fixture removal','removed':False},f);f.flush();os.fsync(f.fileno())
syncdir()
keys.rmdir();home.rmdir();marker.unlink();fixture.rmdir()
assert not os.path.lexists(fixture)
with tempfile.NamedTemporaryFile(mode='w',dir=STAGE,delete=False) as f:
 json.dump({'fixture':str(fixture),'removed':True,'recorded_agents_absent':True,'known_helper_absent':True},f);f.flush();os.fsync(f.fileno())
 name=f.name
os.replace(name,STAGE/'cache-cleanup.json');syncdir()
print('PASS: exact keyless synthetic fixture removed; public stage/evidence retained')
