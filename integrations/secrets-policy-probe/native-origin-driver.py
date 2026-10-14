#!/usr/bin/env python3
"""One exact synthetic GET-UI diagnosis; preserve argv identity and restore bytes."""
import hashlib,json,os,re,shlex,stat,subprocess,sys,tempfile
from pathlib import Path
BASE=Path('/var/tmp/sailfish-secrets-policy-PGG4Hh')
PROBE=BASE/'secrets-policy-probe';BACKUP=BASE/'secrets-policy-probe.before-native';CANDIDATE=BASE/'secrets-auth-origin.native';STATE=BASE/'native-origin-state.json'
ORIGINAL='4bde163e7b9bcd327e614b0f8c20d4a373f0f4d14c1b782c69c14efecde443f8'
DIAGNOSTIC='007fea33e284b1eb1b609d08ca085c6327db510101cde10e8cd4c8ede33cc40b'
TOKEN='65b7ff98df1b410eabe0f2cf';COLLECTION='SPP'+TOKEN+'V'
assert os.getuid()==100000 and os.uname().machine=='aarch64';os.umask(0o077)
def guard(p,mode,directory=False):
 s=p.lstat();assert s.st_uid==100000 and stat.S_IMODE(s.st_mode)==mode
 assert stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode) and s.st_nlink==1
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def syncdir():
 fd=os.open(BASE,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
def save(state):
 with tempfile.NamedTemporaryFile(mode='w',dir=BASE,delete=False) as f:
  json.dump(state,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno());name=f.name
 os.replace(name,STATE);syncdir()
guard(BASE,0o700,True);guard(BASE/'policy-fixture.json',0o600)
profile=json.loads((BASE/'policy-fixture.json').read_text())
assert profile['token']==TOKEN and profile['probe_sha256']==ORIGINAL
assert set(profile['attempts'])=={'keep','verify'}
assert not any(v.get('uncertain_write',False) for v in profile['attempts'].values())
assert profile['attempts']['verify']['created'] and profile['attempts']['verify']['cleanup_required']
assert profile['attempts']['keep']['cleanup_required'] is False
ENV={'PATH':'/usr/bin:/bin','HOME':'/home/defaultuser','LANG':'C','LC_ALL':'C','XDG_RUNTIME_DIR':'/run/user/100000','DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/100000/bus','QT_LOGGING_RULES':'*.debug=false'}
action=sys.argv[1];assert action in ('install','probe','restore')
assert len(sys.argv)==(3 if action=='probe' else 2)
if action=='probe':assert sys.argv[2]=='on-device','Human must invoke from native Terminal'
if action=='install':
 assert not os.path.lexists(STATE) and not os.path.lexists(BACKUP)
 guard(PROBE,0o700);guard(CANDIDATE,0o700);assert sha(PROBE)==ORIGINAL and sha(CANDIDATE)==DIAGNOSTIC
 with BACKUP.open('xb') as f:
  os.chmod(BACKUP,0o700);f.write(PROBE.read_bytes());f.flush();os.fsync(f.fileno())
 assert sha(BACKUP)==ORIGINAL;syncdir()
 state={'collection':COLLECTION,'original':ORIGINAL,'diagnostic':DIAGNOSTIC,'phase':'replacement-intent','probe_attempted':False,'probe_finished':False,'request_launched':False,'no_request_proven':False}
 save(state);os.replace(CANDIDATE,PROBE);syncdir();assert sha(PROBE)==DIAGNOSTIC
 state['phase']='diagnostic-installed';save(state);print('PASS: original backed up; bounded GET-UI diagnostic installed');sys.exit(0)
guard(STATE,0o600);state=json.loads(STATE.read_text())
assert state['collection']==COLLECTION and state['original']==ORIGINAL and state['diagnostic']==DIAGNOSTIC
assert state['phase']=='diagnostic-installed'
guard(PROBE,0o700);guard(BACKUP,0o700);assert sha(PROBE)==DIAGNOSTIC and sha(BACKUP)==ORIGINAL
if action=='restore':
 context_refused=(state.get('no_request_proven') is True and state.get('request_launched') is False and state.get('context',{}).get('context_refused') is True)
 client_refused=(state.get('no_request_proven') is True and state.get('no_request_reason')=='Pinned client refused before constructing Secrets manager' and state.get('request_launched') is True and state.get('result',{}).get('refused_not_unlocked') is True and state.get('result',{}).get('exit')==65)
 assert state['probe_finished'] is True or context_refused or client_refused,'Preserve identity until completed reply or validated no-request refusal'
 with tempfile.NamedTemporaryFile(dir=BASE,delete=False) as f:
  os.chmod(f.name,0o700);f.write(BACKUP.read_bytes());f.flush();os.fsync(f.fileno());name=f.name
 os.replace(name,PROBE);syncdir();assert sha(PROBE)==ORIGINAL
 state['phase']='restored';save(state);print('PASS: original client bytes restored; collection obligation retained');sys.exit(0)
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
assert not state['probe_attempted'],'Do not repeat diagnostic blindly'
# Exclusive attempt reservation also prevents two concurrent native commands.
with (BASE/'native-origin-attempt.json').open('x') as f:
 os.chmod(f.name,0o600);json.dump({'collection':COLLECTION,'diagnostic':DIAGNOSTIC,'intent':'One human native-Terminal GET-UI attempt'},f);f.write('\n');f.flush();os.fsync(f.fileno())
syncdir()
state['probe_attempted']=True;save(state)
facts,valid=native_context();state['context']=facts
if not valid:
 state['no_request_proven']=True;save(state);print('REFUSED: native context not established; no Secrets request');raise SystemExit(64)
state['request_launched']=True;save(state)
try:r=subprocess.run([str(PROBE),'request',TOKEN,'verify'],env=ENV,capture_output=True,timeout=90)
except subprocess.TimeoutExpired:
 state['result']={'client_timeout':True};save(state);raise SystemExit('STOP: preserve client/history after timeout')
assert len(r.stdout)<=8192
try:reply=json.loads(r.stdout)
except ValueError:
 state['result']={'invalid_result':True,'exit':r.returncode};save(state);raise SystemExit('STOP: preserve client/history after invalid result')
assert reply['collection']==COLLECTION and reply['policy']=='verify' and reply['action']=='get-ui'
reply['exit']=r.returncode;state['result']=reply
state['probe_finished']=reply.get('finished') is True and reply.get('result') in (0,2)
if reply.get('refused_not_unlocked') is True and r.returncode==65:
 state['no_request_proven']=True;state['no_request_reason']='Pinned client refused before constructing Secrets manager'
save(state);print(json.dumps(reply))
assert state['probe_finished'] or state.get('no_request_proven') is True,'Preserve client/history until finished result or proven no-request refusal'
