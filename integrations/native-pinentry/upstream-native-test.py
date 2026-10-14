#!/usr/bin/env python3
"""Bounded full upstream-series native UI proof; external caching disabled. Synthetic only."""
import hashlib,json,os,subprocess,sys,tempfile,time
from pathlib import Path
BASE=Path(__file__).absolute().parent
assert not Path(__file__).is_symlink()
assert not BASE.is_symlink() and BASE.name.startswith('sailfish-upstream-native.')
assert BASE.parent==Path('/var/tmp') and BASE.stat().st_uid==100000 and BASE.stat().st_mode&0o777==0o700
GPG='/usr/libexec/sailfish-gnupg/bin/gpg'
CONF='/usr/libexec/sailfish-gnupg/bin/gpgconf'
IPC='/usr/libexec/sailfish-gnupg/bin/gpg-connect-agent'
AGENT='/usr/libexec/sailfish-gnupg/bin/gpg-agent'
SECRET=b'test-123'
assert os.getuid()==100000 and os.uname().machine=='aarch64'
assert 'VERSION_ID=5.2.0.18' in Path('/etc/os-release').read_text()
os.umask(0o077)
env={'PATH':'/usr/bin:/bin','HOME':'/home/defaultuser','LANG':'C','LC_ALL':'C','XDG_RUNTIME_DIR':'/run/user/100000','QT_LOGGING_RULES':'org.sailfishos.secrets.gnupg.pinentry.debug=false'}
# SSH callers may lack a desktop session bus; the standard per-user bus is fixed.
env['DBUS_SESSION_BUS_ADDRESS']='unix:path=/run/user/100000/bus'
def run(args,data=None,timeout=140):
 try:
  return subprocess.run(args,input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=timeout)
 except subprocess.TimeoutExpired as error:
  record={'timeout_seconds':timeout,'program':Path(args[0]).name,'stdout_bytes':len(error.stdout or b''),'stderr_bytes':len(error.stderr or b''),'fixture_preserved':True}
  with (BASE/('timeout-'+str(time.time_ns())+'.json')).open('x') as out:
   json.dump(record,out,indent=2);out.write('\n');out.flush();os.fsync(out.fileno())
  raise
def checked(args,data=None):
 r=run(args,data);assert r.returncode==0, 'Synthetic subprocess failed (no personal context)';return r.stdout
helper=BASE/'pinentry'
assert helper.is_file() and not helper.is_symlink() and helper.stat().st_uid==100000
assert hashlib.sha256(helper.read_bytes()).hexdigest()=='ee5cac67e01080f0e3af693f5030b67e3ad7309d20601b78f936c8816148d416'
if sys.argv[1]=='protocol':
 r=run([str(helper)],b'GETINFO version\nSETKEYINFO --clear\nRESET\nBYE\n',20)
 assert r.returncode==0 and b'D 0.0.1' in r.stdout and b'ERR ' not in r.stdout,r.stdout
 (BASE/'protocol.json').write_text(json.dumps({'passed':True,'helper_sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),'checks':['standard noninteractive Assuan exchange','no external-cache permission requested','cleared SETKEYINFO','RESET','clean BYE']},indent=2)+'\n')
 print('PASS: native pinentry protocol (no UI or Secrets storage request)');sys.exit(0)
state=BASE/'fixture.json'
def save_profile(profile):
 if os.path.lexists(state):
  assert not state.is_symlink() and state.stat().st_uid==100000 and state.stat().st_mode&0o777==0o600
 with tempfile.NamedTemporaryFile(mode='w',prefix='fixture-state-',dir=BASE,delete=False) as out:
  temporary=Path(out.name)
  json.dump(profile,out,indent=2);out.write('\n');out.flush();os.fsync(out.fileno())
 os.replace(temporary,state)
 fd=os.open(BASE,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
def record_attempt(label,result):
 record={'exitcode':result.returncode,'plaintext_bytes':len(result.stdout),'statuses':[line for line in result.stderr.decode(errors='replace').splitlines() if line.startswith(('[GNUPG:] FAILURE','[GNUPG:] ERROR','[GNUPG:] DECRYPTION_FAILED','[GNUPG:] PINENTRY_LAUNCHED'))]}
 with (BASE/(label+'-'+str(time.time_ns())+'.json')).open('x') as out:
  json.dump(record,out,indent=2);out.write('\n');out.flush();os.fsync(out.fileno())
def agent_record(home,profile):
 assert not profile.get('unknown_launch',False),'Unknown prior launch; exact audit required before retry'
 assert not os.path.lexists(socket_path(home)),'Existing fixture socket; stop/audit before retry'
 assert not any(original_alive(a) for a in profile.get('agents',[])),'Known fixture agent still alive; stop before retry'
 profile['unknown_launch']=True
 save_profile(profile)
 with tempfile.NamedTemporaryFile(prefix='synthetic-agent-start-',suffix='.log',dir=BASE) as launch_log:
  launched=subprocess.run([AGENT,'--homedir',str(home),'--no-options','--pinentry-program',str(helper),'--no-allow-external-cache','--daemon'],stdout=subprocess.DEVNULL,stderr=launch_log,env=env,timeout=20)
  assert launched.returncode==0,'Synthetic agent launcher failed; preserve unknown state'
 reply=checked([IPC,'--no-history','--homedir',str(home),'--no-autostart','GETINFO pid','/bye']).decode()
 pid=int(next(line[2:] for line in reply.splitlines() if line.startswith('D ')))
 proc=Path('/proc/'+str(pid))
 assert proc.stat().st_uid==100000 and os.readlink(proc/'exe')==AGENT
 argv=(proc/'cmdline').read_bytes().split(b'\0');assert str(home).encode() in argv and str(helper).encode() in argv and b'--no-options' in argv and b'--no-allow-external-cache' in argv
 ident={'pid':pid,'start':(proc/'stat').read_text().split(') ',1)[1].split()[19]}
 if ident not in profile.setdefault('agents',[]):profile['agents'].append(ident)
 profile['unknown_launch']=False
 save_profile(profile)
 return ident
def original_alive(ident):
 try:return Path('/proc/'+str(ident['pid'])+'/stat').read_text().split(') ',1)[1].split()[19]==ident['start']
 except FileNotFoundError:return False
def socket_path(home):
 socket=checked([CONF,'--homedir',str(home),'--list-dirs','agent-socket']).decode().strip()
 parent=Path(socket).parent
 assert parent.parent==Path('/run/user/100000/gnupg') and parent.name.startswith('d.') and Path(socket).name=='S.gpg-agent'
 if parent.exists():assert not parent.is_symlink() and parent.stat().st_uid==100000 and parent.stat().st_mode&0o777==0o700
 return socket
def stop_agent(home,profile):
 assert not profile.get('unknown_launch',False),'Unknown synthetic agent launch; preserve fixture for public process audit'
 socket=socket_path(home)
 checked([CONF,'--homedir',str(home),'--kill','gpg-agent'])
 for _ in range(40):
  if not os.path.lexists(socket) and not any(original_alive(a) for a in profile.get('agents',[])):break
  time.sleep(.25)
 assert not os.path.lexists(socket) and not any(original_alive(a) for a in profile.get('agents',[])),'Known synthetic agent stop not proven'
 return socket
if sys.argv[1]=='prepare':
 assert not os.path.lexists(state)
 fixture=Path(tempfile.mkdtemp(prefix='synthetic-upstream-pinentry-',dir='/var/tmp'))
 (fixture/'.synthetic-fixture').write_text('upstream-pinentry-no-external-cache-v1\n');home=fixture/'gnupg';home.mkdir(mode=0o700)
 profile={'fixture':str(fixture),'helper_sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),'upstream_commit':'adfb0b1','external_cache_allowed':False}
 save_profile(profile)
 env['GNUPGHOME']=str(home)
 agent_record(home,profile)
 def gpgargs():return [GPG,'--no-options','--homedir',str(home),'--no-autostart','--agent-program',AGENT,'--disable-dirmngr']
 checked(gpgargs()+['--batch','--pinentry-mode','loopback','--passphrase-fd','0','--quick-generate-key','Synthetic Native Pinentry <synthetic@example.invalid>','ed25519','sign','1d'],SECRET+b'\n')
 listing=checked(gpgargs()+['--with-colons','--list-keys']).decode();fingerprint=next(line.split(':')[9] for line in listing.splitlines() if line.startswith('fpr:'))
 checked(gpgargs()+['--batch','--pinentry-mode','loopback','--passphrase-fd','0','--quick-add-key',fingerprint,'cv25519','encrypt','1d'],SECRET+b'\n')
 (fixture/'plaintext').write_bytes(b'Synthetic native pinentry plaintext\n')
 checked(gpgargs()+['--batch','--yes','--recipient',fingerprint,'--output',str(fixture/'ciphertext.gpg'),'--encrypt',str(fixture/'plaintext')])
 stop_agent(home,profile)
 print('PASS: protected synthetic fixture prepared; native cold UI pending');sys.exit(0)
assert not state.is_symlink() and state.stat().st_uid==100000 and state.stat().st_mode&0o777==0o600
profile=json.loads(state.read_text());fixture=Path(profile['fixture']);home=fixture/'gnupg'
assert profile['external_cache_allowed'] is False
env['GNUPGHOME']=str(home)
assert fixture.parent==Path('/var/tmp') and fixture.name.startswith('synthetic-upstream-pinentry-')
assert not fixture.is_symlink() and fixture.stat().st_uid==100000 and fixture.stat().st_mode & 0o777==0o700
assert not home.is_symlink() and home.is_dir() and home.stat().st_uid==100000 and home.stat().st_mode&0o777==0o700
assert not (fixture/'.synthetic-fixture').is_symlink() and (fixture/'.synthetic-fixture').stat().st_uid==100000
assert (fixture/'.synthetic-fixture').read_text()=='upstream-pinentry-no-external-cache-v1\n'
assert profile['helper_sha256']==hashlib.sha256(helper.read_bytes()).hexdigest()
args=[GPG,'--no-options','--homedir',str(home),'--no-autostart','--agent-program',AGENT,'--disable-dirmngr','--pinentry-mode','ask','--status-fd','2','--decrypt',str(fixture/'ciphertext.gpg')]
if sys.argv[1]=='decrypt':
 agent_record(home,profile)
 print('Native system dialog: enter test-123',flush=True)
 r=run(args);record_attempt('cold-decrypt',r);assert r.returncode==0 and r.stdout==(fixture/'plaintext').read_bytes(),'Native synthetic decrypt failed'
 r2=run(args);record_attempt('warm-decrypt',r2);assert r2.returncode==0 and r2.stdout==r.stdout,'Warm synthetic decrypt failed'
 (BASE/'decrypt.json').write_text(json.dumps({'passed':True,'checks':['cold native UI decryption exact synthetic bytes','immediate second decryption exact bytes'],'warm_prompt_absence_human_observation_required':True},indent=2)+'\n')
 print('PASS: cold and warm native synthetic decrypt exact bytes')
elif sys.argv[1]=='cancel':
 stop_agent(home,profile)
 agent_record(home,profile)
 print('Native system dialog: cancel this request',flush=True)
 r=run(args);record_attempt('cancel-decrypt',r);assert r.returncode!=0 and not r.stdout,'Cancel did not refuse plaintext'
 (BASE/'cancel.json').write_text(json.dumps({'passed':True,'exit':r.returncode,'plaintext_bytes':len(r.stdout),'failure_status':[line for line in r.stderr.decode(errors='replace').splitlines() if line.startswith('[GNUPG:] FAILURE')],'human_cancel_confirmation_required':True},indent=2)+'\n')
 print('PASS: native operation failed with no plaintext; confirm actual UI cancellation')
elif sys.argv[1]=='stop':
 socket=stop_agent(home,profile)
 print('PASS: recorded synthetic agent stopped; fixture retained')
else:raise SystemExit('Unknown action; fixture cleanup requires separately reviewed root audit')
