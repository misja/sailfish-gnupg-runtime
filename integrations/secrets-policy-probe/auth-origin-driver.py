#!/usr/bin/env python3
"""One exact synthetic GET-UI diagnosis; preserve argv identity and restore bytes."""
import hashlib,json,os,stat,subprocess,sys,tempfile
from pathlib import Path
BASE=Path('/var/tmp/sailfish-secrets-policy-PGG4Hh')
PROBE=BASE/'secrets-policy-probe';BACKUP=BASE/'secrets-policy-probe.before-auth';CANDIDATE=BASE/'secrets-auth-origin';STATE=BASE/'auth-origin-state.json'
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
if action=='install':
 assert not os.path.lexists(STATE) and not os.path.lexists(BACKUP)
 guard(PROBE,0o700);guard(CANDIDATE,0o700);assert sha(PROBE)==ORIGINAL and sha(CANDIDATE)==DIAGNOSTIC
 with BACKUP.open('xb') as f:
  os.chmod(BACKUP,0o700);f.write(PROBE.read_bytes());f.flush();os.fsync(f.fileno())
 assert sha(BACKUP)==ORIGINAL;syncdir()
 state={'collection':COLLECTION,'original':ORIGINAL,'diagnostic':DIAGNOSTIC,'phase':'replacement-intent','probe_attempted':False,'probe_finished':False}
 save(state);os.replace(CANDIDATE,PROBE);syncdir();assert sha(PROBE)==DIAGNOSTIC
 state['phase']='diagnostic-installed';save(state);print('PASS: original backed up; bounded GET-UI diagnostic installed');sys.exit(0)
guard(STATE,0o600);state=json.loads(STATE.read_text())
assert state['collection']==COLLECTION and state['original']==ORIGINAL and state['diagnostic']==DIAGNOSTIC
assert state['phase']=='diagnostic-installed'
guard(PROBE,0o700);guard(BACKUP,0o700);assert sha(PROBE)==DIAGNOSTIC and sha(BACKUP)==ORIGINAL
if action=='restore':
 assert state['probe_finished'] is True,'Preserve identity until completed reply is recorded'
 with tempfile.NamedTemporaryFile(dir=BASE,delete=False) as f:
  os.chmod(f.name,0o700);f.write(BACKUP.read_bytes());f.flush();os.fsync(f.fileno());name=f.name
 os.replace(name,PROBE);syncdir();assert sha(PROBE)==ORIGINAL
 state['phase']='restored';save(state);print('PASS: original client bytes restored; collection obligation retained');sys.exit(0)
assert not state['probe_attempted'],'Do not repeat diagnostic blindly'
state['probe_attempted']=True;save(state)
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
save(state);print(json.dumps(reply))
assert state['probe_finished'],'Preserve client/history until finished result known'
