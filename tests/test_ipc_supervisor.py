"""Fast-path IPC regressions; interruption timeout is tested by the observer."""
from pathlib import Path
import subprocess
import tempfile
import unittest

POLICY = Path(__file__).resolve().parents[1] / 'runtime/runtime-policy.sh'


@unittest.skipUnless(Path('/usr/bin/busybox').is_file(), 'BusyBox required')
class IpcSupervisorTests(unittest.TestCase):
    def invoke(self, command, policy=POLICY):
        with tempfile.TemporaryDirectory(prefix='synthetic-ipc-result-') as directory:
            return subprocess.run(['/usr/bin/busybox', 'sh', '-c',
                                   '. "$1"; shift; runtime_timed "$@"', 'fixture',
                                   str(policy), '/usr/bin/busybox', 'sh', '-c', command],
                                  env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C',
                                       'SAILFISH_GNUPGHOME': directory},
                                  capture_output=True, text=True, timeout=5)

    def test_success_preserves_standard_output(self):
        result = self.invoke("printf 'D 12345\\nOK\\n'")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'D 12345\nOK\n')

    def test_failure_preserves_exit_status_and_stderr(self):
        result = self.invoke("printf 'fixture failure\\n' >&2; exit 42")
        self.assertEqual(result.returncode, 42)
        self.assertIn('fixture failure', result.stderr)

    def test_timeout_is_failure_even_if_helper_handles_term_with_success(self):
        with tempfile.TemporaryDirectory(prefix='synthetic-ipc-timeout-') as directory:
            policy = Path(directory) / 'policy.sh'
            source = POLICY.read_text()
            needle = '/usr/bin/busybox sleep 15 &'
            self.assertEqual(source.count(needle), 1)
            policy.write_text(source.replace(needle, '/usr/bin/busybox sleep 0.1 &'))
            result = self.invoke("trap 'exit 0' TERM; while :; do /usr/bin/busybox sleep 0.05; done", policy)
            self.assertEqual(result.returncode, 124, result.stderr)


if __name__ == '__main__':
    unittest.main()
