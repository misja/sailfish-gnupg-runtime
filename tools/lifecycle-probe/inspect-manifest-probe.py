import hashlib,json,stat,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent
artifacts=list((root/'probe-rpm/RPMS').rglob('sailfish-lifecycle-manifest-probe-1-1.*.rpm'))
assert len(artifacts)==1,artifacts
artifact=artifacts[0]
raw=subprocess.check_output(['rpm2cpio',str(artifact)])
offset=0; entries={}
while True:
 assert raw[offset:offset+6] in (b'070701',b'070702')
 fields=[int(raw[offset+6+i*8:offset+14+i*8],16) for i in range(13)]
 size,namesize=fields[6],fields[11]; offset+=110
 name=raw[offset:offset+namesize-1].decode().removeprefix('./');offset=(offset+namesize+3)&~3
 data=raw[offset:offset+size];offset=(offset+size+3)&~3
 if name=='TRAILER!!!':break
 assert name not in entries
 entries[name]=(fields[1],data)
prefix='usr/libexec/sailfish-gnupg'
manifest_raw=entries[prefix+'/libexec/payload-generation.json'][1]
manifest=json.loads(manifest_raw)
for relative,expected in manifest['entries'].items():
 name='usr/bin/'+relative.split('/')[1] if relative.startswith('@entry/') else prefix+('' if relative=='.' else '/'+relative)
 mode,data=entries[name]
 assert oct(stat.S_IMODE(mode))==expected['mode'],name
 if expected['kind']=='file': assert hashlib.sha256(data).hexdigest()==expected['sha256'],name
 else: assert expected['kind']=='directory' and stat.S_ISDIR(mode),name
assert entries[prefix+'/libexec/postprocess-fixture'][1]==b'after-postprocessing'
elf=entries[prefix+'/bin/probe'][1]
assert elf[:4]==b'\x7fELF'
result={'scope':'Synthetic SDK RPM build and CPIO inspection; no installation or GnuPG execution','artifact':artifact.name,'artifact_sha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),'payload_generation':hashlib.sha256(manifest_raw).hexdigest(),'manifest_entries':len(manifest['entries']),'postprocessing_mutation_covered':True,'elf_sha256':hashlib.sha256(elf).hexdigest()}
(root/'probe-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
