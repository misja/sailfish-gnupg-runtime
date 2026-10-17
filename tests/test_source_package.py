"""Self-contained source-capsule checks using synthetic published-source inputs."""
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]

class SourcePackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sailfish-source-package-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for path in ("tools", "rpm", "runtime", "sources", "evidence"):
            (self.root / path).mkdir()
        shutil.copyfile(PROJECT / "tools/prepare-package.py", self.root / "tools/prepare-package.py")
        (self.root / "rpm/sailfish-gnupg-runtime.spec").write_text("Version: 1.0\n")
        (self.root / "runtime/wrapper").write_text("#!/bin/sh\nexit 0\n")
        (self.root / "runtime/wrapper").chmod(0o755)
        (self.root / ".gitignore").write_text("/sources/\n/evidence/\n/build/\n")
        data = b"synthetic public upstream archive"
        self.archive = self.root / "sources/fixture-1.0.tar.bz2"
        self.archive.write_bytes(data)
        (self.root / "sources/fixture-1.0.tar.bz2.sig").write_text("synthetic detached signature")
        (self.root / "sources/signature_key.asc").write_text("synthetic public key")
        sha = hashlib.sha256(data).hexdigest()
        item = {"name": "fixture", "version": "1.0", "sha256": sha}
        (self.root / "sources.lock.json").write_text(json.dumps(
            {"sources": [item], "allowed_primary_fingerprints": ["A" * 40]}))
        (self.root / "evidence/source-verification.json").write_text(
            json.dumps([dict(item, signers=["A" * 40])]))
        self.git("init", "--initial-branch=main")
        self.git("add", ".")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-m", "Synthetic source fixture")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args],
                                       stderr=subprocess.DEVNULL)

    def prepare(self):
        return subprocess.run([sys.executable, str(self.root / "tools/prepare-package.py")],
                              capture_output=True, text=True)

    def test_complete_capsule_is_stable_and_excludes_untracked_files(self):
        (self.root / "untracked-note.txt").write_text("synthetic untracked note")
        result = self.prepare()
        self.assertEqual(result.returncode, 0, result.stderr)
        archive = self.root / "sources/sailfish-gnupg-runtime-1.0.tar.gz"
        first = archive.read_bytes()
        self.assertEqual(self.prepare().returncode, 0)
        self.assertEqual(first, archive.read_bytes())
        with tarfile.open(archive) as stream:
            names = stream.getnames()
            prefix = "sailfish-gnupg-runtime-1.0/"
            for relative in ("tools/prepare-package.py", "sources.lock.json",
                             "sources/fixture-1.0.tar.bz2", "sources/fixture-1.0.tar.bz2.sig",
                             "sources/signature_key.asc", "evidence/source-verification.json",
                             "SOURCE-PROVENANCE.json"):
                self.assertIn(prefix + relative, names)
            self.assertNotIn(prefix + "untracked-note.txt", names)
            self.assertEqual(stream.getmember(prefix + "runtime/wrapper").mode, 0o755)
            self.assertTrue(all(m.uid == 0 and m.gid == 0 and m.mtime == 0 for m in stream.getmembers()))

    def test_corrupt_archive_is_rejected_before_packaging(self):
        self.archive.write_bytes(b"corrupt synthetic fixture")
        self.assertNotEqual(self.prepare().returncode, 0)
        self.assertFalse((self.root / "sources/sailfish-gnupg-runtime-1.0.tar.gz").exists())

    def test_verification_signer_must_match_the_existing_allowlist(self):
        path = self.root / "evidence/source-verification.json"
        data = json.loads(path.read_text())
        data[0]["signers"] = ["B" * 40]
        path.write_text(json.dumps(data))
        self.assertNotEqual(self.prepare().returncode, 0)

    def test_tracked_symlink_is_rejected_without_reading_target(self):
        (self.root / "linked").symlink_to(self.root / "missing")
        self.git("add", "linked")
        result = self.prepare()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", result.stderr)

if __name__ == "__main__":
    unittest.main()
