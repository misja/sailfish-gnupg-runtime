#!/usr/bin/env python3
"""Exact empty synthetic collection recovery; no root or permission changes."""
import hashlib,json,os,stat,subprocess,sys,tempfile
from pathlib import Path
BASE=Path('/var/tmp/sailfish-secrets-policy-5JamYk')
PROBE=BASE/'secrets-policy-probe';BACKUP=BASE/'secrets-policy-probe.original';CANDIDATE=BASE/'secrets-policy-owner-recovery'
ORIGINAL='046f3f87bffc7aef2a6f362b769752783539636cd846229680b4a280dc1af4e2'
RECOVERY='d20c21884eff4ab1df48a56e92692fcef5f7c3dd7ec432138c1831b3cd2351ea'
TOKEN='4245823b8da845a29bef5e45';COLLECTION='SPP'+TOKEN+'K'
STATE=BASE/'owner-recovery-state.json'
assert os.getuid()==100000 and os.uname().machine=='aarch64'
os.umask(0o077)
def guard(p,mode,directory=False):
 s=p.lstat();assert s.st_uid==100000 and stat.S_IMODE(s.st_mode)==mode
 assert stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode) and s.st_nlink==1
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def syncdir():
 fd=os.open(BASE,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
def save(v):
 with tempfile.NamedTemporaryFile(mode='w',dir=BASE,delete=False) as f:
  json.dump(v,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno());name=f.name
 os.replace(name,STATE);syncdir()
guard(BASE,0o700,True);guard(BASE/'policy-fixture.json',0o600)
profile=json.loads((BASE/'policy-fixture.json').read_text())
assert profile['token']==TOKEN and profile['probe_sha256']==ORIGINAL
assert set(profile['attempts'])=={'keep'} and profile['attempts']['keep']['created'] is True
assert profile['attempts']['keep']['uncertain_write'] is False
assert profile['attempts']['keep']['pre_create_absent'] is True
ENV={'PATH':'/usr/bin:/bin','HOME':'/home/defaultuser','LANG':'C','LC_ALL':'C','XDG_RUNTIME_DIR':'/run/user/100000','DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/100000/bus','QT_LOGGING_RULES':'org.sailfishos.secrets*.debug=false'}
action=sys.argv[1];assert action in ('install','get','delete','verify','restore')
if action=='install':
 assert not os.path.lexists(STATE) and not os.path.lexists(BACKUP)
 guard(PROBE,0o700);guard(CANDIDATE,0o700)
 assert sha(PROBE)==ORIGINAL and sha(CANDIDATE)==RECOVERY
 data=PROBE.read_bytes()
 with BACKUP.open('xb') as f:
  os.chmod(BACKUP,0o700);f.write(data);f.flush();os.fsync(f.fileno())
 assert sha(BACKUP)==ORIGINAL;syncdir()
 state={'collection':COLLECTION,'original':ORIGINAL,'recovery':RECOVERY,'phase':'replacement-intent','uncertain_delete':False,'events':[]}
 save(state);os.replace(CANDIDATE,PROBE);syncdir();assert sha(PROBE)==RECOVERY
 state['phase']='recovery-installed';save(state)
 print('PASS: original bytes backed up; exact-argv bounded recovery installed');sys.exit(0)
guard(STATE,0o600);state=json.loads(STATE.read_text())
assert state['collection']==COLLECTION and state['original']==ORIGINAL and state['recovery']==RECOVERY
assert state['phase']=='recovery-installed' and state['uncertain_delete'] is False
guard(PROBE,0o700);guard(BACKUP,0o700);assert sha(PROBE)==RECOVERY and sha(BACKUP)==ORIGINAL
if action=='restore':
 assert state.get('absence_proven') is True
 # Restore exact original bytes; never modify a personal or system binary.
 with tempfile.NamedTemporaryFile(dir=BASE,delete=False) as f:
  os.chmod(f.name,0o700);f.write(BACKUP.read_bytes());f.flush();os.fsync(f.fileno());name=f.name
 os.replace(name,PROBE);syncdir();assert sha(PROBE)==ORIGINAL
 state['phase']='restored-cleaned';save(state);print('PASS: original client restored; exact collection absence recorded');sys.exit(0)
if action=='delete':
 assert not state.get('absence_proven',False),'Do not mutate after proven absence'
 assert state['events'] and state['events'][-1]['action']=='get'
 prior=state['events'][-1]['result'];assert prior.get('finished') is True
 success=(prior.get('result')==0 and prior.get('error')==0 and prior.get('exit')==0 and prior.get('synthetic_bytes_match') is True)
 empty=(prior.get('result')==2 and prior.get('error') in (40,41) and prior.get('exit')==2)
 assert success or empty,'Successful expected synthetic value or exact missing-secret result required'
 state['uncertain_delete']=True;save(state)
mode='delete' if action=='delete' else 'get'
env=dict(ENV);env['SYNTHETIC_OWNER_RECOVERY']=mode
try:r=subprocess.run([str(PROBE),'create',TOKEN,'keep'],env=env,capture_output=True,timeout=90)
except subprocess.TimeoutExpired:
 state['events'].append({'action':action,'result':{'client_timeout':True}});save(state);raise SystemExit('STOP: timeout; preserve recovery and intent')
assert len(r.stdout)<=8192
try:reply=json.loads(r.stdout)
except ValueError:
 state['events'].append({'action':action,'result':{'invalid_result':True,'exit':r.returncode}});save(state);raise SystemExit('STOP: invalid result; preserve recovery and intent')
assert reply['collection']==COLLECTION and reply['policy']=='keep' and reply['action']==mode
reply['exit']=r.returncode
if action=='delete' and reply.get('finished') is True and reply.get('result') in (0,2):state['uncertain_delete']=False
state['events'].append({'action':action,'result':reply})
if action=='verify' and reply.get('finished') is True and reply.get('result')==2 and reply.get('error')==43:state['absence_proven']=True
save(state);print(json.dumps(reply))
if action=='delete':assert r.returncode==0,'Deletion not proven; retain client/history'
if action=='verify':assert state.get('absence_proven') is True,'Exact absence not proven; retain client/history'
