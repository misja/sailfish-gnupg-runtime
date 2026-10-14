#!/usr/bin/env python3
"""Bounded UI-only prototype tests. Synthetic fixtures only; no personal paths."""
import hashlib,json,os,subprocess,sys,tempfile,time
from pathlib import Path
BASE=Path(__file__).resolve().parent
GPG='/usr/libexec/sailfish-gnupg/bin/gpg'
CONF='/usr/libexec/sailfish-gnupg/bin/gpgconf'
IPC='/usr/libexec/sailfish-gnupg/bin/gpg-connect-agent'
AGENT='/usr/libexec/sailfish-gnupg/bin/gpg-agent'
SECRET=b'NOT-A-REAL-SECRET-native-pinentry'
assert os.getuid()==100000 and os.uname().machine=='aarch64'
assert 'VERSION_ID=5.2.0.18' in Path('/etc/os-release').read_text()
os.umask(0o077)
env={'PATH':'/usr/bin:/bin','HOME':'/home/defaultuser','LANG':'C','LC_ALL':'C','XDG_RUNTIME_DIR':'/run/user/100000','QT_LOGGING_RULES':'org.sailfishos.secrets.gnupg.pinentry.debug=false'}
# SSH callers may lack a desktop session bus; the standard per-user bus is fixed.
env['DBUS_SESSION_BUS_ADDRESS']='unix:path=/run/user/100000/bus'
def run(args,data=None,timeout=140):
 return subprocess.run(args,input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=timeout)
def checked(args,data=None):
 r=run(args,data);assert r.returncode==0, 'Synthetic subprocess failed (no personal context)';return r.stdout
helper=BASE/'pinentry'
assert helper.is_file() and not helper.is_symlink()
if sys.argv[1]=='protocol':
 r=run([str(helper)],b'GETINFO version\nOPTION allow-external-password-cache\nSETKEYINFO n/SYNTHETIC-ONLY\nBYE\n',20)
 assert r.returncode==0 and b'D 0.0.1' in r.stdout and b'ERR ' not in r.stdout,r.stdout
 (BASE/'protocol.json').write_text(json.dumps({'passed':True,'helper_sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),'checks':['standard noninteractive Assuan exchange','external cache permission accepted without persistence','synthetic SETKEYINFO','clean BYE']},indent=2)+'\n')
 print('PASS: native pinentry protocol (no UI or Secrets storage request)');sys.exit(0)
state=BASE/'fixture.json'
def agent_record(home,profile):
 profile['unknown_launch']=True
 state.write_text(json.dumps(profile,indent=2)+'\n')
 with tempfile.NamedTemporaryFile(prefix='synthetic-agent-start-',suffix='.log',dir=BASE) as launch_log:
  launched=subprocess.run([AGENT,'--homedir',str(home),'--no-options','--pinentry-program',str(helper),'--daemon'],stdout=subprocess.DEVNULL,stderr=launch_log,env=env,timeout=20)
  assert launched.returncode==0,'Synthetic agent launcher failed; preserve unknown state'
 reply=checked([IPC,'--no-history','--homedir',str(home),'--no-autostart','GETINFO pid','/bye']).decode()
 pid=int(next(line[2:] for line in reply.splitlines() if line.startswith('D ')))
 proc=Path('/proc/'+str(pid))
 assert proc.stat().st_uid==100000 and os.readlink(proc/'exe')==AGENT
 argv=(proc/'cmdline').read_bytes().split(b'\0');assert str(home).encode() in argv and str(helper).encode() in argv and b'--no-options' in argv
 ident={'pid':pid,'start':(proc/'stat').read_text().split(') ',1)[1].split()[19]}
 if ident not in profile.setdefault('agents',[]):profile['agents'].append(ident)
 profile['unknown_launch']=False
 state.write_text(json.dumps(profile,indent=2)+'\n')
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
 assert not state.exists()
 fixture=Path(tempfile.mkdtemp(prefix='synthetic-native-pinentry-',dir='/var/tmp'))
 (fixture/'.synthetic-fixture').write_text('native-pinentry-v1\n');home=fixture/'gnupg';home.mkdir(mode=0o700)
 profile={'fixture':str(fixture),'helper_sha256':hashlib.sha256(helper.read_bytes()).hexdigest()}
 state.write_text(json.dumps(profile,indent=2)+'\n')
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
assert fixture.parent==Path('/var/tmp') and fixture.name.startswith('synthetic-native-pinentry-')
assert not fixture.is_symlink() and fixture.stat().st_uid==100000 and fixture.stat().st_mode & 0o777==0o700
assert not home.is_symlink() and home.is_dir() and home.stat().st_uid==100000 and home.stat().st_mode&0o777==0o700
assert not (fixture/'.synthetic-fixture').is_symlink() and (fixture/'.synthetic-fixture').stat().st_uid==100000
assert (fixture/'.synthetic-fixture').read_text()=='native-pinentry-v1\n'
assert profile['helper_sha256']==hashlib.sha256(helper.read_bytes()).hexdigest()
args=[GPG,'--no-options','--homedir',str(home),'--no-autostart','--agent-program',AGENT,'--disable-dirmngr','--pinentry-mode','ask','--status-fd','2','--decrypt',str(fixture/'ciphertext.gpg')]
if sys.argv[1]=='decrypt':
 agent_record(home,profile)
 print('Native system dialog: enter NOT-A-REAL-SECRET-native-pinentry',flush=True)
 r=run(args);assert r.returncode==0 and r.stdout==(fixture/'plaintext').read_bytes(),'Native synthetic decrypt failed'
 r2=run(args);assert r2.returncode==0 and r2.stdout==r.stdout,'Warm synthetic decrypt failed'
 (BASE/'decrypt.json').write_text(json.dumps({'passed':True,'checks':['cold native UI decryption exact synthetic bytes','immediate second decryption exact bytes'],'warm_prompt_absence_human_observation_required':True},indent=2)+'\n')
 print('PASS: cold and warm native synthetic decrypt exact bytes')
elif sys.argv[1]=='cancel':
 stop_agent(home,profile)
 agent_record(home,profile)
 print('Native system dialog: cancel this request',flush=True)
 r=run(args);assert r.returncode!=0 and not r.stdout,'Cancel did not refuse plaintext'
 (BASE/'cancel.json').write_text(json.dumps({'passed':True,'exit':r.returncode,'plaintext_bytes':len(r.stdout),'failure_status':[line for line in r.stderr.decode(errors='replace').splitlines() if line.startswith('[GNUPG:] FAILURE')],'human_cancel_confirmation_required':True},indent=2)+'\n')
 print('PASS: native operation failed with no plaintext; confirm actual UI cancellation')
elif sys.argv[1]=='cleanup':
 socket=stop_agent(home,profile)
 # Refuse deletion if any helper from this dedicated prototype is still running.
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit():continue
  try:
   if proc.stat().st_uid!=100000:continue
   assert os.readlink(proc/'exe')!=str(helper),'Synthetic pinentry still running'
  except (FileNotFoundError,ProcessLookupError):continue
 import shutil
 shutil.rmtree(fixture)
 parent=Path(socket).parent
 assert parent.parent==Path('/run/user/100000/gnupg') and parent.name.startswith('d.')
 if parent.exists():parent.rmdir()
 state.unlink();print('PASS: exact synthetic fixture and agent/socket cleanup')
else:raise SystemExit('Unknown action')
