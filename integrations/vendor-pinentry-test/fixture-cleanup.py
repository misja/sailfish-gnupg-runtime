#!/usr/bin/env python3
"""Remove only a completed keyless installed-helper smoke's empty marked fixture."""
import json,os,stat,tempfile
from pathlib import Path
assert os.getuid()==os.geteuid()==100000
os.umask(0o077)
B=Path(__file__).absolute().parent
info=B.lstat();assert B.parent==Path('/var/tmp') and B.name.startswith('sailfish-native-vendor.')
assert stat.S_ISDIR(info.st_mode) and info.st_uid==100000 and stat.S_IMODE(info.st_mode)==0o700 and B.resolve()==B
S=B/'cache-attempt.json';info=S.lstat();assert stat.S_ISREG(info.st_mode) and info.st_uid==100000 and stat.S_IMODE(info.st_mode)==0o600 and info.st_nlink==1
p=json.loads(S.read_text());assert p['complete'] is True and len(p['agents'])==1
assert not any(k in p for k in ('pending_launch','pending_operation','failure_cleanup'))
a=p['agents'][0];assert a['reaped'] is True and a['startup_policy_verified'] is True
assert not Path('/proc',str(a['pid'])).exists()
assert [(v['label'],v['error'],v['data_bytes'],v['synthetic_bytes_match']) for v in p['events']]==[('initial-cache-miss',58,0,False),('cold-prompt',0,8,True),('warm-noask',0,8,True),('stop',0,0,False)]
fixture=Path(p['fixture']);assert fixture.parent==Path('/var/tmp') and fixture.name.startswith('synthetic-native-cache-')
home=fixture/'gnupg';keys=home/'private-keys-v1.d';marker=fixture/'.synthetic-fixture'
assert p['agent_argv']==['/usr/libexec/sailfish-gnupg/bin/gpg-agent','--homedir',str(home),'--no-options','--disable-scdaemon','--pinentry-program','/usr/bin/pinentry','--no-allow-external-cache','--default-cache-ttl','300','--max-cache-ttl','900','--server']
for path in Path('/proc').iterdir():
 if not path.name.isdigit():continue
 try:
  if path.stat().st_uid==100000 and (path/'comm').read_text().strip().startswith('pinentry'):assert os.readlink(path/'exe')!='/usr/bin/pinentry'
 except FileNotFoundError:continue
for path in (fixture,home,keys):
 info=path.lstat();assert stat.S_ISDIR(info.st_mode) and info.st_uid==100000 and stat.S_IMODE(info.st_mode)==0o700 and path.resolve()==path
assert {v.name for v in fixture.iterdir()}=={'.synthetic-fixture','gnupg'}
assert {v.name for v in home.iterdir()}=={'private-keys-v1.d'} and not list(keys.iterdir())
info=marker.lstat();assert stat.S_ISREG(info.st_mode) and info.st_uid==100000 and stat.S_IMODE(info.st_mode)==0o600 and info.st_nlink==1
assert marker.read_bytes()==b'native-agent-cache-lifecycle-v1\n'
def syncdir():
 fd=os.open(B,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
with (B/'fixture-cleanup.json').open('x') as f:
 json.dump({'fixture':str(fixture),'removed':False,'intent':'Exact nonrecursive empty fixture removal'},f);f.flush();os.fsync(f.fileno())
syncdir();keys.rmdir();home.rmdir();marker.unlink();fixture.rmdir()
assert not os.path.lexists(fixture)
with tempfile.NamedTemporaryFile(mode='w',dir=B,delete=False) as f:
 json.dump({'fixture':str(fixture),'removed':True,'recorded_agent_absent':True,'known_helper_absent':True},f);f.flush();os.fsync(f.fileno());name=f.name
os.replace(name,B/'fixture-cleanup.json');syncdir()
print('PASS: exact empty keyless fixture removed; public stage retained')
