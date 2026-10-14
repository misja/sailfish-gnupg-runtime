#!/usr/bin/env python3
"""One human-native enrollment of a fresh, approved three-policy synthetic fixture."""
import hashlib,json,os,re,resource,shlex,stat,subprocess,sys,tempfile
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
assert profile['phase']=='prepared' and not profile['attempts'] and profile['probe_sha256']==CLIENT_HASH
assert re.fullmatch('[0-9a-f]{24}',profile['token'])
MARKER=BASE/'native-enroll-attempt.json'
record={'token':profile['token'],'coordinator':COORD_HASH,'client':CLIENT_HASH,'human_launch_attestation':'on-device','coordinator_launched':False}
def syncdir():
 fd=os.open(BASE,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
with MARKER.open('x') as f:
 os.chmod(f.name,0o600);json.dump(record,f);f.write('\n');f.flush();os.fsync(f.fileno())
syncdir()
def save():
 with tempfile.NamedTemporaryFile(mode='w',dir=BASE,delete=False) as f:
  json.dump(record,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno());name=f.name
 os.replace(name,MARKER);syncdir()
ENV={'PATH':'/usr/bin:/bin','HOME':'/home/defaultuser','LANG':'C','LC_ALL':'C','XDG_RUNTIME_DIR':'/run/user/100000','DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/100000/bus','QT_LOGGING_RULES':'*.debug=false'}
def native_context():
 facts={'human_launch_attestation':'on-device','pid_binding_verified':False}
 def call(args):return subprocess.run(['/usr/bin/busctl','--system','--timeout=5']+args,env=ENV,capture_output=True,timeout=10)
 def fields(args):
  r=call(args);assert r.returncode==0 and len(r.stdout)<=1024
  return shlex.split(r.stdout.decode('utf-8'))
 def prop(path,interface,name):return fields(['get-property','org.freedesktop.login1',path,interface,name])
 try:
  assert hashlib.sha256(Path('/usr/share/polkit-1/actions/org.sailfishos.secrets.policy').read_bytes()).hexdigest()=='83fde1e06b55f72ce7ddeccc62a17d72aa67246f276c68cc2b4173a885afd249'
  booster=any(':name=booster:' in line and line.split(':name=booster:',1)[1].strip() not in ('','/') for line in Path('/proc/self/cgroup').read_text().splitlines())
  facts['booster_context']=booster
  assert not booster,'Preserve original command-line OwnerOnly fallback'
  r=call(['call','org.freedesktop.login1','/org/freedesktop/login1','org.freedesktop.login1.Manager','GetSessionByPID','u',str(os.getpid())])
  assert len(r.stdout)<=1024
  own=shlex.split(r.stdout.decode()) if r.returncode==0 else []
  if r.returncode==0:
   assert len(own)==2 and own[0]=='o' and re.fullmatch('/org/freedesktop/login1/session/[A-Za-z0-9_]+',own[1])
   facts['pid_binding_verified']=True
   remote=prop(own[1],'org.freedesktop.login1.Session','Remote')
   active=prop(own[1],'org.freedesktop.login1.Session','Active')
   assert remote==['b','false'] and active==['b','true']
  else:facts['pid_binding_unavailable']=True
  user=fields(['call','org.freedesktop.login1','/org/freedesktop/login1','org.freedesktop.login1.Manager','GetUser','u','100000'])
  assert user==['o','/org/freedesktop/login1/user/_100000']
  display=prop(user[1],'org.freedesktop.login1.User','Display')
  assert len(display)==3 and display[0]=='(so)' and display[1] and re.fullmatch('/org/freedesktop/login1/session/[A-Za-z0-9_]+',display[2])
  interface='org.freedesktop.login1.Session'
  assert prop(display[2],interface,'User')==['(uo)','100000',user[1]]
  assert prop(display[2],interface,'Remote')==['b','false']
  assert prop(display[2],interface,'Active')==['b','true']
  seat=prop(display[2],interface,'Seat');assert len(seat)==3 and seat[0]=='(so)' and seat[1]
  facts['own_display_verified_local_active_seat']=True
  facts['proof_limit']='User display and human invocation do not prove PID/session association'
  return facts,True
 except (AssertionError,ValueError,subprocess.TimeoutExpired):
  facts['context_refused']=True;return facts,False
facts,valid=native_context();record['context']=facts
if not valid:
 record['context_refused']=True;save();raise SystemExit('REFUSED: native context not established; no Secrets writes')
record['coordinator_launched']=True;save()
# Frozen coordinator owns per-request deadlines and unresolved-write bookkeeping.
os.execve('/usr/bin/python3',['/usr/bin/python3','-I',str(COORD),'enroll'],ENV)
