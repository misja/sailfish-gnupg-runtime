#!/usr/bin/env python3
"""Owned foreground stock agent; synthetic passphrase RPC, not key decryption."""
import hashlib,json,os,re,selectors,signal,subprocess,sys,tempfile,time
from pathlib import Path
assert os.getuid()==100000
stage=Path(__file__).absolute().parent
assert not Path(__file__).is_symlink() and not stage.is_symlink()
assert stage.parent==Path('/var/tmp') and stage.name.startswith('sailfish-upstream-native.')
assert stage.stat().st_uid==100000 and stage.stat().st_mode&0o777==0o700
helper=stage/'pinentry'
assert helper.is_file() and not helper.is_symlink() and helper.stat().st_uid==100000
assert hashlib.sha256(helper.read_bytes()).hexdigest()=='ee5cac67e01080f0e3af693f5030b67e3ad7309d20601b78f936c8816148d416'
assert sys.argv[1] in ['probe','exercise']
assert len(sys.argv) in [2,3]
attempt=sys.argv[2] if len(sys.argv)==3 else ''
assert not attempt or re.fullmatch(r'[a-zA-Z0-9_-]{1,16}',attempt)
tag='legacy-env-'+sys.argv[1]+('-'+attempt if attempt else '')
os.umask(0o077)
# No automatic child reaping: the foreground child PID remains owned until wait.
signal.signal(signal.SIGCHLD,signal.SIG_DFL)
state=stage/(tag+'-state.json')
assert not os.path.lexists(state)
home=Path(tempfile.mkdtemp(prefix='synthetic-legacy-agent-',dir='/var/tmp'))
(home/'.synthetic-fixture').write_text('legacy-agent-protocol-v1\n')
profile={'home':str(home),'unknown_launch':True,'mode':sys.argv[1],'attempt':attempt,'scope':'Foreground stock agent and synthetic RPC only; no keys/Secrets grants'}
def save():
 with tempfile.NamedTemporaryFile(mode='w',prefix='legacy-state-',dir=stage,delete=False) as f:
  json.dump(profile,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno());temporary=f.name
 os.replace(temporary,state)
 fd=os.open(stage,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
save()
env={'PATH':'/usr/bin:/bin','HOME':str(home),'GNUPGHOME':str(home),'LANG':'C','LC_ALL':'C','XDG_RUNTIME_DIR':'/run/user/100000','DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/100000/bus','QT_LOGGING_RULES':'org.sailfishos.secrets.gnupg.pinentry.debug=false'}
argv=['/usr/bin/gpg-agent','--options','/dev/null','--disable-scdaemon','--pinentry-program',str(helper),'--server']
with tempfile.NamedTemporaryFile(prefix='legacy-agent-',suffix='.log',dir=stage) as log:
 proc=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,env=env)
 try:
  path=Path('/proc')/str(proc.pid)
  assert path.stat().st_uid==100000 and os.readlink(path/'exe')=='/usr/bin/gpg-agent'
  actual=(path/'cmdline').read_bytes().split(b'\0')
  child_env=(path/'environ').read_bytes().split(b'\0')
  assert ('GNUPGHOME='+str(home)).encode() in child_env and ('HOME='+str(home)).encode() in child_env
  assert b'--server' in actual and b'/dev/null' in actual and str(helper).encode() in actual
  profile['agent']={'pid':proc.pid,'start':(path/'stat').read_text().split(') ',1)[1].split()[19]}
  profile['unknown_launch']=False;save()
  selector=selectors.DefaultSelector();selector.register(proc.stdout,selectors.EVENT_READ);buffer=bytearray()
  def response(timeout=100):
   end=time.monotonic()+timeout;data=bytearray();statuses=0
   while True:
    while b'\n' in buffer:
     line,_,tail=buffer.partition(b'\n');buffer[:]=tail;line=line.rstrip(b'\r')
     if line.startswith(b'D '):
      from urllib.parse import unquote_to_bytes
      data.extend(unquote_to_bytes(line[2:]));assert len(data)<=1024
     elif line.startswith(b'S '):statuses+=1
     elif line.startswith(b'OK') or line.startswith(b'ERR '):
      error=int(line.split()[1])&65535 if line.startswith(b'ERR ') else 0
      return error,bytes(data),statuses
    remaining=end-time.monotonic();assert remaining>0,'Assuan response timeout'
    assert selector.select(remaining),'Assuan response timeout'
    block=os.read(proc.stdout.fileno(),4096);assert block,'Agent closed without terminal response'
    buffer.extend(block);assert len(buffer)<=65536
  def command(text,label):
   profile['operation']=label;save()
   proc.stdin.write(text.encode()+b'\n');proc.stdin.flush()
   rc,data,statuses=response()
   with (stage/(tag+'-'+label+'.json')).open('x') as f:
    json.dump({'label':label,'error_code':rc,'data_bytes':len(data),'equals_public_fixture':data==b'test-123','status_count':statuses},f);f.flush();os.fsync(f.fileno())
   profile['operation']=None;save()
   return rc,data
  rc,data,_=response(15);assert rc==0 and not data
  if sys.argv[1]=='probe':
   rc,data=command('HELP','help');assert rc==0
  else:
   request='GET_PASSPHRASE --data SYNTHETIC-LEGACY-COMPAT X Synthetic+legacy Synthetic+Jolla+compatibility'
   print('Legacy native dialog: enter test-123',flush=True)
   rc,data=command(request,'cold');assert rc==0 and data==b'test-123'
   rc,data=command(request,'second');assert rc==0 and data==b'test-123'
   rc,data=command('CLEAR_PASSPHRASE SYNTHETIC-LEGACY-COMPAT','clear');assert rc==0 and not data
   print('Legacy native dialog: cancel this request',flush=True)
   rc,data=command(request,'cancel');assert rc==99 and not data
  rc,data=command('BYE','bye');assert rc==0 and not data
  proc.stdin.close();assert proc.wait(timeout=10)==0
  profile['agent_reaped']=True;save()
  print('PASS: legacy '+sys.argv[1]+'; owned foreground agent exited; fixture retained')
 finally:
  if proc.returncode is None:
   # SIGCHLD is default and this child has not been reaped: PID cannot be reused.
   proc.terminate()
   try:proc.wait(timeout=10)
   except subprocess.TimeoutExpired:
    proc.kill();proc.wait(timeout=5)
   profile['agent_reaped']=True;profile['failed_cleanup']=True;save()
  if sys.argv[1]=='probe':
   log.flush();log.seek(0)
   with (stage/(tag+'-stderr.json')).open('x') as diagnostic:
    json.dump({'scope':'No-UI stock probe stderr','stderr':log.read(8192).decode(errors='replace')},diagnostic);diagnostic.flush();os.fsync(diagnostic.fileno())
