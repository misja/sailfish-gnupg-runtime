"""Exercise the RPM removal body against temporary inert Linux processes."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SLEEP = shutil.which('gnusleep') or shutil.which('sleep')


@unittest.skipUnless(Path('/usr/bin/busybox').exists() and SLEEP, 'BusyBox and sleep required')
class PackageRemovalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-package-removal-')
        self.addCleanup(self.temp.cleanup)
        self.prefix = Path(self.temp.name) / 'private'
        (self.prefix / 'bin').mkdir(parents=True)
        self.script = (ROOT / 'rpm/sailfish-gnupg-runtime.spec').read_text().split('%preun\n', 1)[1].split('\n%files', 1)[0]
        self.script = self.script.replace('%{private_prefix}', str(self.prefix))

    def process(self, name, private=True):
        target = (self.prefix if private else Path(self.temp.name) / 'stock') / 'bin' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SLEEP, target)
        target.chmod(0o755)
        process = subprocess.Popen([str(target), '60'])
        self.addCleanup(self.stop, process)
        # Wait for exec, rather than racing the parent's fork/exec transition.
        for _ in range(1000):
            if Path('/proc', str(process.pid), 'exe').resolve() == target:
                return process, target
        self.fail('Fixture did not execute')

    @staticmethod
    def stop(process):
        if process.poll() is None:
            process.kill()
        process.wait(timeout=3)

    def remove(self, count='0'):
        return subprocess.run(['/usr/bin/busybox', 'sh', '-c', self.script, 'preun', count],
                              capture_output=True, text=True, timeout=5)

    def test_private_agent_signalled_stock_agent_untouched(self):
        agent, _ = self.process('gpg-agent')
        stock, _ = self.process('gpg-agent', private=False)
        self.assertEqual(self.remove().returncode, 0)
        self.assertEqual(agent.wait(timeout=3), -15)
        self.assertIsNone(stock.poll())

    def test_deleted_private_agent_is_signalled(self):
        agent, path = self.process('gpg-agent')
        path.unlink()
        self.assertEqual(self.remove().returncode, 0)
        self.assertEqual(agent.wait(timeout=3), -15)

    def test_busy_refusal_sends_no_signals_even_on_retry(self):
        agent, _ = self.process('gpg-agent')
        client, _ = self.process('gpg')
        for _ in range(3):
            result = self.remove()
            self.assertEqual(result.returncode, 1)
            self.assertIn('Close the application', result.stderr)
            self.assertIsNone(agent.poll())
            self.assertIsNone(client.poll())

    def test_upgrade_does_not_stop_agent(self):
        agent, _ = self.process('gpg-agent')
        self.assertEqual(self.remove('1').returncode, 0)
        self.assertIsNone(agent.poll())
