#!/usr/bin/env python3
"""Synthetic-only storage policy coordination. Device writes need scoped approval."""
import hashlib,json,os,re,subprocess,sys,tempfile,uuid
from pathlib import Path
BASE=Path(__file__).resolve().parent
PROBE=BASE/'secrets-policy-probe'
HASH='4bde163e7b9bcd327e614b0f8c20d4a373f0f4d14c1b782c69c14efecde443f8'
POLICIES=('keep','verify','relock')
assert os.getuid()==100000 and os.uname().machine=='aarch64'
assert 'VERSION_ID=5.2.0.18' in Path('/etc/os-release').read_text()
assert BASE.parent==Path('/var/tmp') and BASE.name.startswith('sailfish-secrets-policy-')
for path,mode in ((BASE,0o700),(PROBE,0o700)):
 assert not path.is_symlink() and path.stat().st_uid==100000 and path.stat().st_mode&0o777==mode
assert hashlib.sha256(PROBE.read_bytes()).hexdigest()==HASH
os.umask(0o077)
ENV={'PATH':'/usr/bin:/bin','HOME':'/home/defaultuser','LANG':'C','LC_ALL':'C','XDG_RUNTIME_DIR':'/run/user/100000','DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/100000/bus','QT_LOGGING_RULES':'org.sailfishos.secrets*.debug=false'}
STATE=BASE/'policy-fixture.json'
def save(profile):
 with tempfile.NamedTemporaryFile(mode='w',prefix='.policy-state-',dir=BASE,delete=False) as output:
  json.dump(profile,output,indent=2);output.write('\n');output.flush();os.fsync(output.fileno());name=output.name
 os.replace(name,STATE)
 fd=os.open(BASE,os.O_RDONLY|os.O_DIRECTORY);os.fsync(fd);os.close(fd)
def call(args):
 env=dict(ENV)
 if args==['state']:command=[str(PROBE),'state']
 else:
  assert len(args)==3 and args[0] in ('create','store','get','get-ui','delete')
  env['SYNTHETIC_POLICY_ACTION']=args[0]
  command=[str(PROBE),'request',args[1],args[2]]
 try:r=subprocess.run(command,env=env,capture_output=True,timeout=90)
 except subprocess.TimeoutExpired:return {'client_timeout':True,'exit':124}
 try:
  assert len(r.stdout)<=8192
  reply=json.loads(r.stdout)
  assert isinstance(reply,dict)
 except (AssertionError,ValueError):reply={'client_no_valid_result':True}
 reply['exit']=r.returncode
 return reply
if sys.argv[1]=='init':
 assert not STATE.exists() and not STATE.is_symlink()
 profile={'token':uuid.uuid4().hex[:24],'probe_sha256':HASH,'phase':'prepared','attempts':{},'events':[]}
 save(profile);print('PASS: synthetic policy manifest prepared; no Secrets writes');sys.exit(0)
assert not STATE.is_symlink() and STATE.stat().st_uid==100000 and STATE.stat().st_mode&0o777==0o600
profile=json.loads(STATE.read_text());token=profile['token']
assert re.fullmatch('[0-9a-f]{24}',token) and profile['probe_sha256']==HASH
assert set(profile['attempts']).issubset(POLICIES)
def event(action,policy,tag):
 mutation=action in ('create','store','delete')
 if mutation:
  assert policy in profile['attempts']
  assert not profile['attempts'][policy].get('uncertain_write',False),'Unresolved earlier server-side mutation'
  profile['attempts'][policy]['uncertain_write']=True
  profile['attempts'][policy]['pending_write']=action;save(profile)
 result=call([action,token,policy])
 if 'collection' in result:
  assert result['collection']=='SPP'+token+{'keep':'K','verify':'V','relock':'R'}[policy] and result['action']==action and result['policy']==policy
 if mutation and result.get('finished') is True and result.get('result') in (0,2):
  profile['attempts'][policy]['uncertain_write']=False
  profile['attempts'][policy].pop('pending_write',None)
 profile['events'].append({'tag':tag,'action':action,'policy':policy,'result':result});save(profile)
 print(json.dumps({'tag':tag,'policy':policy,'result':result}),flush=True)
 return result
def missing(result):return result.get('finished') is True and result.get('result')==2 and result.get('error')==43
if sys.argv[1]=='state':
 print(json.dumps(call(['state'])));sys.exit(0)
if sys.argv[1]=='enroll':
 assert profile['phase']=='prepared' and not profile['attempts']
 profile['phase']='enrolling';save(profile)
 for policy in POLICIES:
  absent=event('get',policy,'pre-create-missing')
  assert missing(absent),'Collection absence not proven; preserve manifest, do not create or reuse'
  profile['attempts'][policy]={'pre_create_absent':True,'create_attempted':True,'cleanup_required':True};save(profile)
  result=event('create',policy,'create')
  if result.get('error')==46:
   profile['attempts'][policy]['cleanup_required']=False;save(profile)
   raise SystemExit('Unexpected existing collection: preserve metadata, no reuse/delete')
  assert result.get('exit')==0,'Create not proven; preserve cleanup obligation and do not retry'
  profile['attempts'][policy]['created']=True;save(profile)
  assert event('store',policy,'store').get('exit')==0,'Store not proven; preserve exact cleanup obligation'
 profile['phase']='enrolled';save(profile)
 print('PASS: three exact synthetic collections created/stored')
elif sys.argv[1] in ('unlocked','locked','unlocked-again'):
 assert profile['phase']=='enrolled'
 label=sys.argv[1];state=call(['state']);required=1 if label=='locked' else 0
 assert state.get('device_lock_state')==required,'Required actual DeviceLock state not proven; no reads attempted'
 for policy in POLICIES:event('get',policy,label)
 print('Recorded raw policy outcomes; successful locked access is not treated as protection')
elif sys.argv[1]=='get-ui':
 assert profile['phase']=='enrolled' and len(sys.argv)==3 and sys.argv[2] in POLICIES
 assert call(['state']).get('device_lock_state')==0
 event('get-ui',sys.argv[2],'explicit-system-interaction')
elif sys.argv[1]=='cleanup':
 assert not any(a.get('uncertain_write',False) for a in profile['attempts'].values()),'Uncertain server-side mutation: preserve client/manifest for separately reviewed resolution'
 assert call(['state']).get('device_lock_state')==0,'Unlock phone for bounded collection cleanup'
 for policy,attempt in profile['attempts'].items():
  if not attempt['cleanup_required']:continue
  assert attempt['pre_create_absent'] and attempt['create_attempted']
  absent=event('get',policy,'pre-cleanup-check')
  if not missing(absent):
   assert event('delete',policy,'delete').get('exit')==0,'Delete not proven; retain fixed client identity and manifest'
   assert missing(event('get',policy,'post-delete-missing')),'Collection removal not proven'
  attempt['cleanup_required']=False;save(profile)
 profile['phase']='cleaned';save(profile)
 print('PASS: all authorized attempted synthetic collections proved absent; client/metadata retained for export')
else:raise SystemExit('Unknown action')
