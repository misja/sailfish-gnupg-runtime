#!/usr/bin/env python3
"""One human native-Terminal cleanup of three exact synthetic collections."""
import hashlib,json,os,resource,stat,sys
from pathlib import Path
assert len(sys.argv)==2 and sys.argv[1]=='on-device'
assert os.getuid()==os.geteuid()==100000
resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077)
BASE=Path('/var/tmp/sailfish-secrets-policy-voA1vW')
COORD=BASE/'device-test.py';CLIENT=BASE/'secrets-policy-probe'
COORD_HASH='f4f8e4de3b9b5b30ce74ea4f5918591c04867e2dcefb9edcf4a5d3e46c9d9e28'
CLIENT_HASH='4bde163e7b9bcd327e614b0f8c20d4a373f0f4d14c1b782c69c14efecde443f8'
def guard(path,mode,directory=False):
 info=path.lstat();assert info.st_uid==100000 and stat.S_IMODE(info.st_mode)==mode
 assert stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode) and info.st_nlink==1
guard(BASE,0o700,True);guard(COORD,0o600);guard(CLIENT,0o700);guard(BASE/'policy-fixture.json',0o600)
assert hashlib.sha256(COORD.read_bytes()).hexdigest()==COORD_HASH
assert hashlib.sha256(CLIENT.read_bytes()).hexdigest()==CLIENT_HASH
profile=json.loads((BASE/'policy-fixture.json').read_text())
assert profile['token']=='d37a5b18d506455dba074097' and profile['probe_sha256']==CLIENT_HASH
assert set(profile['attempts'])=={'keep','verify','relock'}
assert not any(v.get('uncertain_write',False) for v in profile['attempts'].values())
assert profile['phase']=='enrolled'
assert all(v['cleanup_required'] is True and v['created'] is True and v['pre_create_absent'] is True for v in profile['attempts'].values())
with (BASE/'native-cleanup-attempt.json').open('x') as output:
 os.chmod(output.name,0o600)
 json.dump({'collections':['SPPd37a5b18d506455dba074097'+suffix for suffix in ('K','V','R')],'coordinator':COORD_HASH,'client':CLIENT_HASH,'human_launch_attestation':'on-device','intent':'One exact cleanup attempt; retain record on failure'},output)
 output.write('\n');output.flush();os.fsync(output.fileno())
fd=os.open(BASE,os.O_RDONLY|os.O_DIRECTORY)
try:os.fsync(fd)
finally:os.close(fd)
# Frozen coordinator bounds requests and preserves unresolved server mutation intent.
ENV={'PATH':'/usr/bin:/bin','HOME':'/home/defaultuser','LANG':'C','LC_ALL':'C','XDG_RUNTIME_DIR':'/run/user/100000','DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/100000/bus','QT_LOGGING_RULES':'*.debug=false'}
os.execve('/usr/bin/python3',['/usr/bin/python3','-I',str(COORD),'cleanup'],ENV)
