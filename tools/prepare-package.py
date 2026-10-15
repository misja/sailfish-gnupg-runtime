#!/usr/bin/env python3
"""Create a self-contained runtime source archive from tracked public inputs."""
import gzip
import hashlib
import io
import json
import re
import subprocess
import tarfile
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]

def source(relative):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise SystemExit("Unsafe source input path")
    target = root / path
    if root.is_symlink() or any(p.is_symlink() for p in [target, *target.parents] if p != root.parent):
        raise SystemExit("Refusing source input symlink: " + relative)
    if not target.is_file():
        raise SystemExit("Missing source input: " + relative)
    return target

def public_mode(path):
    return 0o755 if path.stat().st_mode & 0o111 else 0o644

def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()

lock = json.loads(source("sources.lock.json").read_text())
verification = json.loads(source("evidence/source-verification.json").read_text())
inputs = {"sources/signature_key.asc", "evidence/source-verification.json"}
for item in lock["sources"]:
    filename = f"{item['name']}-{item['version']}.tar.bz2"
    relative = "sources/" + filename
    if sha(source(relative)) != item["sha256"]:
        raise SystemExit("Locked source digest mismatch: " + filename)
    matches = [v for v in verification if all(v.get(k) == item[k] for k in ("name", "version", "sha256"))]
    if len(matches) != 1 or not matches[0].get("signers") or any(
            signer not in lock["allowed_primary_fingerprints"] for signer in matches[0]["signers"]):
        raise SystemExit("Verification record differs from locked source: " + filename)
    inputs.update((relative, relative + ".sig"))
tracked = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"]).decode().split("\0")
inputs.update(path for path in tracked if path)
version = re.search(r"^Version:\s+(\S+)$", source("rpm/sailfish-gnupg-private.spec").read_text(), re.M)[1]
prefix = "sailfish-gnupg-runtime-" + version
paths = [(relative, source(relative)) for relative in sorted(inputs)]
provenance = {
    "git_base_commit": subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip(),
    "tracked_worktree_differs_from_head": bool(subprocess.run(
        ["git", "-C", str(root), "diff", "--quiet", "HEAD", "--"], check=False).returncode),
    "files": {name: {"sha256": sha(path), "mode": oct(public_mode(path))}
              for name, path in paths},
    "scope": "Tracked project worktree plus exact locked archives and regenerated public verification material",
}
destination = root / "sources" / (prefix + ".tar.gz")
if destination.is_symlink() or destination.parent.is_symlink():
    raise SystemExit("Refusing source archive output symlink")
with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
    temporary = Path(stream.name)
try:
    with temporary.open("wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w|") as archive:
            for relative, path in paths:
                info = tarfile.TarInfo(prefix + "/" + relative)
                info.size = path.stat().st_size
                info.mode = public_mode(path)
                info.mtime = 0
                info.uid = info.gid = 0
                with path.open("rb") as data:
                    archive.addfile(info, data)
            data = (json.dumps(provenance, indent=2, sort_keys=True) + "\n").encode()
            info = tarfile.TarInfo(prefix + "/SOURCE-PROVENANCE.json")
            info.size, info.mode, info.mtime = len(data), 0o644, 0
            info.uid = info.gid = 0
            archive.addfile(info, io.BytesIO(data))
    temporary.chmod(0o644)
    temporary.replace(destination)
finally:
    temporary.unlink(missing_ok=True)
for directory in ("BUILD", "BUILDROOT", "RPMS", "SRPMS", "SPECS"):
    (root / "build/rpmbuild" / directory).mkdir(parents=True, exist_ok=True)
print("Prepared complete source archive", destination.name, sha(destination))
