#!/usr/bin/env python3
"""Bounded original -> candidate -> original -> absent test. Root, approved scope only."""
import hashlib,json,os,stat,subprocess,sys,tempfile,fcntl
from pathlib import Path
assert os.getuid()==os.geteuid()==0 and len(sys.argv)==2
assert sys.argv[1] in ('prepare','install','cleanup')
assert os.uname().machine=='aarch64' and 'VERSION_ID=5.2.0.18' in Path('/etc/os-release').read_text()
os.umask(0o077)
B=Path(__file__).absolute().parent
info=B.lstat();assert B.parent==Path('/var/tmp') and B.name.startswith('sailfish-vendor-dev-root.')
assert stat.S_ISDIR(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700 and B.resolve()==B
lockfd=os.open(B/'invocation.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
info=os.fstat(lockfd);assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o600 and info.st_nlink==1
fcntl.flock(lockfd,fcntl.LOCK_EX|fcntl.LOCK_NB)
P='sailfishsecretsdaemon-cryptoplugins-gnupg'
ORIGINAL=B/'original.rpm';CANDIDATE=B/'candidate.rpm'
INPUTS={ORIGINAL:'a0f54b19d184db9afdb2e1e534baac33402157ff983e1c0eef4231ddf59d8af0',CANDIDATE:'572213e9f23db34201b93c44d1f2ce2e2b50e1421e1f38ba75bde42b7522cb76'}
FILES=('/usr/bin/pinentry','/usr/lib64/Sailfish/Crypto/libsailfishcrypto-openpgp.so','/usr/lib64/Sailfish/Crypto/libsailfishcrypto-smime.so')
ENV={'PATH':'/usr/bin:/bin','LC_ALL':'C','LANG':'C'}
for path,digest in INPUTS.items():
 info=path.lstat();assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o600 and info.st_nlink==1
 assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
STATE=B/'package-test.json'
def save(profile):
 with tempfile.NamedTemporaryFile(mode='w',dir=B,delete=False) as f:
  json.dump(profile,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno());name=f.name
 os.replace(name,STATE)
 fd=os.open(B,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
def call(args,timeout=120):
 return subprocess.run(args,env=ENV,capture_output=True,timeout=timeout)
def checked(args):
 r=call(args);assert r.returncode==0,'Command failed; inspect retained public package records';return r.stdout.decode()
def inventory():
 return sorted(checked(['/usr/bin/rpm','-qa','--qf','%{NAME} %{EPOCHNUM}:%{VERSION}-%{RELEASE} %{ARCH}\n']).splitlines())
STOCK=('sailfishsecretsdaemon','libsailfishcrypto','libsailfishcryptopluginapi','libsailfishsecrets','gpgme','libgpg-error','mlite-qt5','gnupg2')
def stock():
 files={};verification={}
 for package in STOCK:
  r=call(['/usr/bin/rpm','-V',package]);assert r.returncode in (0,1)
  verification[package]={'exit':r.returncode,'output':r.stdout.decode(),'diagnostic':r.stderr.decode()}
  for name in checked(['/usr/bin/rpm','-ql',package]).splitlines():
   path=Path(name)
   selected=(path.parent==Path('/usr/lib64') and '.so' in path.name) or (path.parent in (Path('/usr/bin'),Path('/usr/libexec')) and package in ('sailfishsecretsdaemon','gnupg2'))
   if not selected:continue
   info=path.lstat()
   if stat.S_ISREG(info.st_mode):files[name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'uid':info.st_uid,'mode':stat.S_IMODE(info.st_mode)}
   elif stat.S_ISLNK(info.st_mode):files[name]={'symlink':os.readlink(path),'uid':info.st_uid}
 assert files,'Empty bounded stock fingerprint'
 return {'verification':verification,'files':files}
def absent():
 assert call(['/usr/bin/rpm','-q',P]).returncode==1
 assert all(not os.path.lexists(v) for v in FILES)
def quiet():
 # Public process metadata only; do not log unrelated maps or inspect memory.
 for path in Path('/proc').iterdir():
  if not path.name.isdigit():continue
  try:
   exe=os.readlink(path/'exe')
  except FileNotFoundError:continue
  if exe in ('/usr/bin/gpg-agent','/usr/bin/gpg-agent (deleted)'):raise AssertionError('Stock agent present; no package transaction')
  if exe=='/usr/libexec/sailfish-gnupg/bin/gpg-agent':
   try:arguments=(path/'cmdline').read_bytes().split(b'\0')
   except FileNotFoundError:continue
   assert not any(arguments[i:i+2]==[b'--pinentry-program',b'/usr/bin/pinentry'] for i in range(len(arguments)-1)),'Private native agent present; no package transaction'
  if exe in FILES or exe in [v+' (deleted)' for v in FILES]:raise AssertionError('Native helper is active; no package transaction')
  try:maps=(path/'maps').read_text()
  except FileNotFoundError:continue
  assert not any(v in maps for v in FILES),'Plugin/helper mapped in a live process; no package transaction'
def verify(release):
 assert checked(['/usr/bin/rpm','-q','--qf','%{NAME} %{VERSION}-%{RELEASE} %{ARCH}',P])==P+' 0.2.44-'+release+' aarch64'
 r=call(['/usr/bin/rpm','-V',P]);assert r.returncode==0 and not r.stdout
 for value in FILES:
  info=Path(value).lstat();assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o755
if sys.argv[1]=='prepare':
 assert not os.path.lexists(STATE);absent();quiet()
 for path in INPUTS:
  assert set(checked(['/usr/bin/rpm','-qp','--list',str(path)]).splitlines())==set(FILES)
  assert not checked(['/usr/bin/rpm','-qp','--scripts',str(path)]).strip()
 baseline=inventory();stock_before=stock()
 tests=[]
 for path in INPUTS:
  r=call(['/usr/bin/rpm','-ivh','--test',str(path)])
  tests.append({'input':path.name,'exit':r.returncode,'output':r.stdout.decode(),'diagnostic':r.stderr.decode()})
  assert r.returncode==0
 absent();assert inventory()==baseline;assert stock()==stock_before
 profile={'phase':'prepared','baseline':baseline,'stock_before':stock_before,'input_sha256':{v.name:d for v,d in INPUTS.items()},'preflight':tests,'events':[],'uncertain_transaction':False}
 save(profile);print('PASS: both exact RPM preflights; package inventory/file absence unchanged');raise SystemExit(0)
info=STATE.lstat();assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o600 and info.st_nlink==1
profile=json.loads(STATE.read_text());assert profile['input_sha256']=={v.name:d for v,d in INPUTS.items()}
assert not profile['uncertain_transaction'],'Preserve pending transaction for explicit audit; do not retry'
def transaction(args,label):
 quiet()
 if args[1]=='-e':testargs=['/usr/bin/rpm','-e','--test',P]
 else:testargs=args[:2]+['--test']+args[2:]
 test=call(testargs);profile['events'].append({'label':label+'-fresh-test','exit':test.returncode,'output':test.stdout.decode(),'diagnostic':test.stderr.decode()});save(profile)
 assert test.returncode==0,'Fresh exact transaction preflight failed; no mutation'
 profile['uncertain_transaction']=True;profile['pending_transaction']=label;save(profile)
 r=call(args)
 profile['events'].append({'label':label,'exit':r.returncode,'output':r.stdout.decode(),'diagnostic':r.stderr.decode()});save(profile)
 assert r.returncode==0,'Transaction not proven complete; preserve state, no automatic retry'
 profile['uncertain_transaction']=False;profile.pop('pending_transaction',None);save(profile)
def unchanged_except_plugin():
 now=[v for v in inventory() if not v.startswith(P+' ')]
 assert now==profile['baseline'],'Other package metadata changed'
if sys.argv[1]=='install':
 assert profile['phase']=='prepared';absent();assert inventory()==profile['baseline'];assert stock()==profile['stock_before']
 transaction(['/usr/bin/rpm','-ivh',str(ORIGINAL)],'original-install')
 verify('1.14.3.jolla');unchanged_except_plugin();profile['phase']='original-installed';save(profile)
 transaction(['/usr/bin/rpm','-Uvh',str(CANDIDATE)],'candidate-upgrade')
 verify('1.14.3.jolla.compat1');unchanged_except_plugin();profile['phase']='candidate-installed';save(profile)
 print('PASS: original installed, candidate upgraded; other package metadata unchanged. Native UI proof pending.')
else:
 assert profile['phase']=='candidate-installed';verify('1.14.3.jolla.compat1');unchanged_except_plugin()
 transaction(['/usr/bin/rpm','-Uvh','--oldpackage',str(ORIGINAL)],'return-to-original')
 verify('1.14.3.jolla');unchanged_except_plugin();profile['phase']='original-restored';save(profile)
 checked(['/usr/bin/rpm','-e','--test',P])
 transaction(['/usr/bin/rpm','-e',P],'remove-temporary-original')
 absent();assert inventory()==profile['baseline'];assert stock()==profile['stock_before'];profile['stock_after_equal']=True;profile['phase']='cleaned';save(profile)
 print('PASS: original restored, temporary package removed; baseline inventory and three-file absence restored.')
