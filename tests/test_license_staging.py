"""Exercise the actual RPM license-staging fragment with synthetic files."""
import subprocess
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]

class LicenseStagingTests(unittest.TestCase):
    def test_project_and_component_notices_keep_their_own_directories(self):
        spec = (PROJECT / "rpm/sailfish-gnupg-runtime.spec").read_text()
        start = spec.index("mkdir -p %{buildroot}%{private_prefix}/licenses/project")
        end = spec.index("\nfind %{buildroot}", start)
        fragment = spec[start:end]
        with tempfile.TemporaryDirectory(prefix="sailfish-license-test-") as directory:
            root = Path(directory)
            for file, content in {"LICENSE": "synthetic project license",
                                  "LICENSING.md": "synthetic project grant"}.items():
                (root / file).write_text(content)
            for component, notices in {
                "synthetic-lib-1.0": {"COPYING": "synthetic library copyright",
                                      "COPYING.LESSER": "synthetic library grant",
                                      "AUTHORS": "synthetic library authors"},
                "synthetic-tool-2.0": {"LICENSE.txt": "synthetic tool grant"}
            }.items():
                source = root / "inspect" / component
                source.mkdir(parents=True)
                for file, content in notices.items():
                    (source / file).write_text(content)
            buildroot = root / "stage"
            fragment = fragment.replace("%{buildroot}", str(buildroot))
            fragment = fragment.replace("%{private_prefix}", "/usr/libexec/sailfish-gnupg")
            subprocess.run(["bash", "-euo", "pipefail", "-c", fragment],
                           cwd=root, check=True)
            licenses = buildroot / "usr/libexec/sailfish-gnupg/licenses"
            expected = {
                "project/LICENSE": "synthetic project license",
                "project/LICENSING.md": "synthetic project grant",
                "synthetic-lib-1.0/COPYING": "synthetic library copyright",
                "synthetic-lib-1.0/COPYING.LESSER": "synthetic library grant",
                "synthetic-lib-1.0/AUTHORS": "synthetic library authors",
                "synthetic-tool-2.0/LICENSE.txt": "synthetic tool grant",
            }
            actual = {str(p.relative_to(licenses)): p.read_text()
                      for p in licenses.rglob("*") if p.is_file()}
            self.assertEqual(actual, expected)

if __name__ == "__main__":
    unittest.main()
