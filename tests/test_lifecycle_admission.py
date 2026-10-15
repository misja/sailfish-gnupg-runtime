"""Real flock/process tests in own temporary state; no package or agent access."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from lifecycle_admission import Admission, AdmissionError

MODULE = str(Path(__file__).resolve().parents[1] / 'runtime')
GENERATION = 'a' * 64


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-admission-')
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'state'
        self.gate = Admission(self.path, expected_uid=os.geteuid())
        self.gate.initialize(GENERATION)

    def process(self, code):
        setup = ('import os,sys,time; sys.path.insert(0, sys.argv[1]); '
                 'from lifecycle_admission import Admission; '
                 'gate=Admission(sys.argv[2], expected_uid=os.geteuid()); ')
        process = subprocess.Popen([sys.executable, '-I', '-c', setup + code, MODULE, str(self.path)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, start_new_session=True)
        def cleanup():
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate(timeout=3)
        self.addCleanup(cleanup)
        return process

    def wait_state(self, state):
        deadline = time.monotonic() + 3
        while self.gate.status()['state'] != state:
            self.assertLess(time.monotonic(), deadline, 'State transition did not occur')
            time.sleep(0.01)

    def ready_line(self, process):
        # Bounded read, including failures before the child writes its marker.
        import select
        self.assertTrue(select.select([process.stdout], [], [], 3)[0], 'No fixture readiness marker')
        line = process.stdout.readline().strip()
        self.assertTrue(line, 'Fixture exited before readiness')
        return line

    def test_parallel_operations_share_one_generation(self):
        with self.gate.acquire() as first, self.gate.acquire() as second:
            self.assertEqual(first.generation, GENERATION)
            self.assertEqual(first.generation, second.generation)
            self.assertNotEqual(first.fd, second.fd)

    def test_drain_closes_admission_before_waiting_for_operation(self):
        with self.gate.acquire():
            closer = self.process('print(gate.drain(5), flush=True)')
            self.wait_state('DRAINING')
            with self.assertRaises(AdmissionError):
                self.gate.acquire()
        output, errors = closer.communicate(timeout=3)
        self.assertEqual(closer.returncode, 0, errors)
        self.assertEqual(output.strip(), 'DRAINED')
        self.assertEqual(self.gate.status()['state'], 'DRAINED')
        with self.assertRaises(AdmissionError):
            self.gate.acquire()

    def test_timeout_stays_blocked_after_operation_exits(self):
        with self.gate.acquire():
            self.assertEqual(self.gate.drain(0), 'BLOCKED')
        self.assertEqual(self.gate.status()['state'], 'BLOCKED')
        with self.assertRaises(AdmissionError):
            self.gate.acquire()
        with self.assertRaises(AdmissionError):
            self.gate.drain(0)

    def test_dead_coordinator_does_not_reopen_admission(self):
        with self.gate.acquire():
            closer = self.process('print(gate.drain(30), flush=True)')
            self.wait_state('DRAINING')
            closer.kill()
            closer.wait(timeout=3)
        self.assertEqual(self.gate.status()['state'], 'DRAINING')
        with self.assertRaises(AdmissionError):
            self.gate.acquire()

    def test_inherited_lease_survives_killed_client(self):
        holder = self.process("lease=gate.acquire(); child=lease.spawn([sys.executable, '-I', '-c', 'import time; time.sleep(30)']); print(child.pid, flush=True); time.sleep(30)")
        self.assertGreater(int(self.ready_line(holder)), 0)
        holder.kill()
        holder.wait(timeout=3)
        # The inherited descriptor keeps the operation registered after client death.
        self.assertEqual(self.gate.drain(0), 'BLOCKED')

    def test_live_subprocess_retains_lease_after_parent_closes_copy(self):
        holder = self.process("lease=gate.acquire(); child=lease.spawn([sys.executable, '-I', '-c', 'import time; time.sleep(30)']); lease.close(); print(child.pid, flush=True); time.sleep(30)")
        self.ready_line(holder)
        self.assertEqual(self.gate.drain(0), 'BLOCKED')

    def test_dead_client_without_children_releases_lease(self):
        holder = self.process("lease=gate.acquire(); print('READY', flush=True); time.sleep(30)")
        self.assertEqual(self.ready_line(holder), 'READY')
        holder.kill()
        holder.wait(timeout=3)
        self.assertEqual(self.gate.drain(0), 'DRAINED')

    def test_two_coordinators_cannot_both_own_transition(self):
        with self.gate.acquire():
            closer = self.process('print(gate.drain(5), flush=True)')
            self.wait_state('DRAINING')
            with self.assertRaises(AdmissionError):
                self.gate.drain(0)
        output, errors = closer.communicate(timeout=3)
        self.assertEqual(closer.returncode, 0, errors)
        self.assertEqual(output.strip(), 'DRAINED')

    def test_agent_registration_survives_operation_drain(self):
        operation = self.gate.acquire()
        self.addCleanup(operation.close)
        closer = self.process('print(gate.drain(5), flush=True)')
        self.wait_state('DRAINING')
        registration = self.gate.acquire_agent(operation)
        self.addCleanup(registration.close)
        operation.close()
        output, error = closer.communicate(timeout=3)
        self.assertEqual(closer.returncode, 0, error)
        self.assertEqual(output.strip(), 'DRAINED')
        self.assertTrue(self.gate.agents_registered())
        registration.close()
        self.assertFalse(self.gate.agents_registered())

    def test_stop_requires_exclusive_operation_access(self):
        with self.gate.acquire():
            with self.assertRaises(BlockingIOError):
                self.gate.acquire_stop()
        with self.gate.acquire_stop():
            with self.assertRaises(BlockingIOError):
                self.gate.acquire()
        self.gate.drain(0)
        with self.gate.acquire_stop():
            with self.assertRaises(AdmissionError):
                self.gate.acquire()
        self.assertEqual(self.gate.status()['state'], 'DRAINED')

    def test_closed_or_stop_lease_cannot_register_an_agent(self):
        operation = self.gate.acquire()
        operation.close()
        with self.assertRaises(AdmissionError):
            self.gate.acquire_agent(operation)
        with self.gate.acquire_stop() as stop:
            with self.assertRaises(AdmissionError):
                self.gate.acquire_agent(stop)

    def test_missing_state_never_defaults_to_active(self):
        (self.path / 'state.json').unlink()
        with self.assertRaises(FileNotFoundError):
            self.gate.acquire()

    def test_invalid_and_oversized_state_fail_closed(self):
        for content in ('not-json', '{}', 'null', 'x' * 4097,
                        json.dumps({'state': 'ACTIVE', 'generation': 'unverified'})):
            with self.subTest(content=content[:40]):
                (self.path / 'state.json').write_text(content)
                with self.assertRaises(AdmissionError):
                    self.gate.acquire()

    def test_symlink_state_or_locks_are_rejected(self):
        for name in ('state.json', 'admission.lock', 'operations.lock'):
            with self.subTest(name=name):
                original = self.path / name
                saved = self.path / (name + '.saved')
                original.rename(saved)
                original.symlink_to(saved)
                try:
                    with self.assertRaises((AdmissionError, OSError)):
                        self.gate.acquire()
                finally:
                    original.unlink()
                    saved.rename(original)

    def test_untrusted_directory_and_file_modes_are_rejected(self):
        self.path.chmod(0o777)
        with self.assertRaises(AdmissionError):
            self.gate.acquire()
        self.path.chmod(0o755)
        (self.path / 'operations.lock').chmod(0o666)
        with self.assertRaises(AdmissionError):
            self.gate.acquire()

    def test_unexpected_owner_is_rejected(self):
        gate = Admission(self.path, expected_uid=os.geteuid() + 1)
        with self.assertRaises(AdmissionError):
            gate.acquire()
        with self.assertRaises(AdmissionError):
            gate.drain(0)

    def test_initialization_never_replaces_existing_locks(self):
        before = (self.path / 'admission.lock').stat().st_ino
        with self.assertRaises(FileExistsError):
            self.gate.initialize(GENERATION)
        self.assertEqual((self.path / 'admission.lock').stat().st_ino, before)

    def test_lease_inheritance_cannot_be_disabled_through_api(self):
        with self.gate.acquire() as lease:
            with self.assertRaises(AdmissionError):
                lease.spawn(['/bin/true'], pass_fds=())
        with self.assertRaises(AdmissionError):
            lease.spawn(['/bin/true'])

    def test_bad_deadlines_do_not_close_admission(self):
        for timeout in (-1, 3601, float('nan'), '1'):
            with self.assertRaises(AdmissionError):
                self.gate.drain(timeout)
        self.assertEqual(self.gate.status()['state'], 'ACTIVE')


if __name__ == '__main__':
    unittest.main()
