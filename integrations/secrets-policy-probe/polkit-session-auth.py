#!/usr/bin/env python3
"""One own-subject auth_self comparison per launch context; no Secrets requests."""
import hashlib,json,os,re,resource,shlex,stat,subprocess,sys,tempfile
from pathlib import Path
assert len(sys.argv)==2 and sys.argv[1] in ('ssh','local')
assert os.getuid()==os.geteuid()==100000 and os.uname().machine=='aarch64'
resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077)
BASE=Path(__file__).resolve().parent
assert BASE.parent==Path('/var/tmp') and BASE.name.startswith('sailfish-local-auth-')
s=BASE.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==100000 and stat.S_IMODE(s.st_mode)==0o700
s=Path(__file__).lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==100000 and stat.S_IMODE(s.st_mode)==0o600 and s.st_nlink==1
policy=Path('/usr/share/polkit-1/actions/org.sailfishos.secrets.policy')
assert hashlib.sha256(policy.read_bytes()).hexdigest()=='83fde1e06b55f72ce7ddeccc62a17d72aa67246f276c68cc2b4173a885afd249'
mode=sys.argv[1];statepath=BASE/('auth-'+mode+'.json');assert not os.path.lexists(statepath)
pid=os.getpid();start=int(Path('/proc/self/stat').read_text().rsplit(') ',1)[1].split()[19])
booster=any(':name=booster:' in l and l.split(':name=booster:',1)[1].strip() not in ('','/') for l in Path('/proc/self/cgroup').read_text().splitlines())
ENV={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C'}
def bus(args,timeout=10):return subprocess.run(['/usr/bin/busctl','--system','--timeout=5']+args,env=ENV,capture_output=True,timeout=timeout)
record={'mode':mode,'subject_is_this_process':True,'booster_context':booster,'interaction_requested':False,'request_finished':False,'attempted':False}
# Atomically reserve this mode before metadata or authentication requests.
fd=os.open(statepath,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as f:
 json.dump(record,f);f.write('\n');f.flush();os.fsync(f.fileno())
fd=os.open(BASE,os.O_RDONLY|os.O_DIRECTORY)
try:os.fsync(fd)
finally:os.close(fd)
try:
 r=bus(['call','org.freedesktop.login1','/org/freedesktop/login1','org.freedesktop.login1.Manager','GetSessionByPID','u',str(pid)])
 assert len(r.stdout)<=1024
 fields=shlex.split(r.stdout.decode()) if r.returncode==0 else []
 if len(fields)==2 and fields[0]=='o' and re.fullmatch('/org/freedesktop/login1/session/[A-Za-z0-9_]+',fields[1]):
  record['own_session_found']=True
  for prop in ('Remote','Active'):
   p=bus(['get-property','org.freedesktop.login1',fields[1],'org.freedesktop.login1.Session',prop])
   if p.returncode==0 and p.stdout.strip() in (b'b true',b'b false'):record['own_session_'+prop.lower()]=p.stdout.strip()==b'b true'
 else:record['own_session_found']=False
except (subprocess.TimeoutExpired,ValueError,AssertionError):record['own_session_metadata_failed']=True
def save():
 with tempfile.NamedTemporaryFile(mode='w',dir=BASE,delete=False) as f:
  json.dump(record,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno());name=f.name
 os.replace(name,statepath)
 fd=os.open(BASE,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
if (mode=='local' and not booster) or (mode=='ssh' and booster):
 record['refused_unexpected_context']=True;save();raise SystemExit(64)
if mode=='local' and not (record.get('own_session_found') is True and record.get('own_session_remote') is False and record.get('own_session_active') is True):
 record['refused_unproven_active_local_session']=True;save();raise SystemExit(64)
record['attempted']=True;record['interaction_requested']=True;save()
command=['/usr/bin/busctl','--system','--timeout=60','call','org.freedesktop.PolicyKit1','/org/freedesktop/PolicyKit1/Authority','org.freedesktop.PolicyKit1.Authority','CheckAuthorization','(sa{sv})sa{ss}us','unix-process','3','pid','u',str(pid),'start-time','t',str(start),'uid','i','100000','org.sailfishos.secrets.authentication','0','1','']
try:r=subprocess.run(command,env=ENV,capture_output=True,timeout=70)
except subprocess.TimeoutExpired:
 record['timeout']=True;save();raise SystemExit('STOP: preserve attempted auth record; do not retry automatically')
record['exit']=r.returncode
if r.returncode!=0:
 record['valid_result']=False;save();print(json.dumps(record));raise SystemExit(1)
assert len(r.stdout)<=8192
try:
 values=shlex.split(r.stdout.decode('utf-8'))
 assert len(values)>=4 and values[0]=='(bba{ss})' and values[1] in ('true','false') and values[2] in ('true','false')
 count=int(values[3]);assert 0<=count<=32 and len(values)==4+2*count
 keys=set(values[4::2]);assert len(keys)==count
except (ValueError,AssertionError):
 record['valid_result']=False;save();print(json.dumps(record));raise SystemExit(1)
record.update({'valid_result':True,'request_finished':True,'authorized':values[1]=='true','challenge':values[2]=='true','details_count':count,'dismissed_key_present':'polkit.dismissed' in keys,'retention_key_present':'polkit.retains_authorization_after_challenge' in keys,'temporary_id_key_present':'polkit.temporary_authorization_id' in keys})
assert int(Path('/proc/self/stat').read_text().rsplit(') ',1)[1].split()[19])==start
save();print(json.dumps(record),flush=True)
