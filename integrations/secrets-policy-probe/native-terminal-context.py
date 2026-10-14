#!/usr/bin/env python3
"""Own-process metadata only; intended for human launch in native Terminal."""
import json,os,re,resource,shlex,stat,subprocess,sys,tempfile
from pathlib import Path
assert len(sys.argv)==1 and os.getuid()==os.geteuid()==100000
resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077)
BASE=Path(__file__).resolve().parent
assert BASE.parent==Path('/var/tmp') and BASE.name.startswith('sailfish-session-meta-')
s=BASE.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==100000 and stat.S_IMODE(s.st_mode)==0o700
s=Path(__file__).lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==100000 and stat.S_IMODE(s.st_mode)==0o600 and s.st_nlink==1
STATE=BASE/'context.json'
pid=os.getpid();start=Path('/proc/self/stat').read_text().rsplit(') ',1)[1].split()[19]
booster=any(':name=booster:' in l and l.split(':name=booster:',1)[1].strip() not in ('','/') for l in Path('/proc/self/cgroup').read_text().splitlines())
record={'uid':100000,'booster_context':booster,'auth_requested':False,'secrets_requested':False,'metadata_finished':False}
fd=os.open(STATE,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as f:
 json.dump(record,f);f.write('\n');f.flush();os.fsync(f.fileno())
def syncdir():
 fd=os.open(BASE,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
syncdir()
ENV={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C'}
def call(args):return subprocess.run(['/usr/bin/busctl','--system','--timeout=5']+args,env=ENV,capture_output=True,timeout=10)
try:
 r=call(['call','org.freedesktop.login1','/org/freedesktop/login1','org.freedesktop.login1.Manager','GetSessionByPID','u',str(pid)])
 assert len(r.stdout)<=1024
 fields=shlex.split(r.stdout.decode()) if r.returncode==0 else []
 if len(fields)==2 and fields[0]=='o' and re.fullmatch('/org/freedesktop/login1/session/[A-Za-z0-9_]+',fields[1]):
  record['own_session_found']=True
  for prop in ('Remote','Active'):
   p=call(['get-property','org.freedesktop.login1',fields[1],'org.freedesktop.login1.Session',prop])
   if p.returncode==0 and p.stdout.strip() in (b'b true',b'b false'):record['own_session_'+prop.lower()]=p.stdout.strip()==b'b true'
  p=call(['get-property','org.freedesktop.login1',fields[1],'org.freedesktop.login1.Session','Seat'])
  if p.returncode==0 and len(p.stdout)<=1024:
   values=shlex.split(p.stdout.decode())
   if len(values)==3 and values[0]=='(so)':record['own_seat_present']=bool(values[1])
 else:record['own_session_found']=False
 record['metadata_finished']=True
except (subprocess.TimeoutExpired,ValueError,AssertionError):record['metadata_failed']=True
assert Path('/proc/self/stat').read_text().rsplit(') ',1)[1].split()[19]==start
with tempfile.NamedTemporaryFile(mode='w',dir=BASE,delete=False) as f:
 json.dump(record,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno());name=f.name
os.replace(name,STATE);syncdir()
print('RECORDED: own session metadata only; no authentication or Secrets request',flush=True)
