#!/usr/bin/env python3
"""Noninteractive authorization metadata for this process only; no credentials."""
import json,os,resource,shlex,subprocess,sys
from pathlib import Path
assert len(sys.argv)==1 and os.getuid()==os.geteuid()==100000
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
pid=os.getpid();start=int(Path('/proc/self/stat').read_text().rsplit(') ',1)[1].split()[19])
ENV={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C'}
for mode in ('source-pid-start','pid-start-uid'):
 subject=['unix-process','2' if mode=='source-pid-start' else '3','pid','u',str(pid),'start-time','t',str(start)]
 if mode=='pid-start-uid':subject+=['uid','i','100000']
 command=['/usr/bin/busctl','--system','--timeout=5','call','org.freedesktop.PolicyKit1','/org/freedesktop/PolicyKit1/Authority','org.freedesktop.PolicyKit1.Authority','CheckAuthorization','(sa{sv})sa{ss}us']+subject+['org.sailfishos.secrets.authentication','0','0','']
 record={'mode':mode,'interaction_requested':False,'subject_is_this_process':True}
 try:r=subprocess.run(command,env=ENV,capture_output=True,timeout=10)
 except subprocess.TimeoutExpired:
  record['timeout']=True;print(json.dumps(record),flush=True);raise SystemExit(1)
 record['exit']=r.returncode
 if r.returncode!=0:
  record['valid_result']=False;print(json.dumps(record),flush=True);continue
 assert len(r.stdout)<=8192
 try:
  values=shlex.split(r.stdout.decode('utf-8'))
  assert len(values)>=4 and values[0]=='(bba{ss})'
  assert values[1] in ('true','false') and values[2] in ('true','false')
  count=int(values[3]);assert 0<=count<=32 and len(values)==4+2*count
  keys=set(values[4::2]);assert len(keys)==count
 except (ValueError,AssertionError):
  record['valid_result']=False;print(json.dumps(record),flush=True);continue
 record.update({'valid_result':True,'authorized':values[1]=='true','challenge':values[2]=='true','details_count':count,'dismissed_key_present':'polkit.dismissed' in keys,'retention_key_present':'polkit.retains_authorization_after_challenge' in keys,'temporary_id_key_present':'polkit.temporary_authorization_id' in keys})
 # Never print detail values, unknown keys, raw responses or error messages.
 print(json.dumps(record),flush=True)
assert int(Path('/proc/self/stat').read_text().rsplit(') ',1)[1].split()[19])==start
