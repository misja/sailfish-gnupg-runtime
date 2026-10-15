"""Owner-injected synthetic installation/proc trees; never real root state."""
import fcntl
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from lifecycle_admission import Admission, AdmissionError
from lifecycle_control import Controller, Payload, ProcessCheck


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-control-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.prefix = self.root / 'private'
        (self.prefix / 'libexec').mkdir(parents=True)
        self.prefix.chmod(0o755)
        (self.prefix / 'libexec').chmod(0o755)
        self.file = self.prefix / 'libexec/inert'
        self.file.write_text('synthetic payload\n')
        self.file.chmod(0o644)
        self.entries = tuple(self.root / name for name in ('sailfish-gpg', 'sailfish-gpg-agent'))
        for entry in self.entries:
            entry.write_text('synthetic public entry\n')
            entry.chmod(0o755)
        self.payload = Payload(self.prefix, entrypoints=self.entries, expected_uid=os.geteuid())
        self.generation = self.payload.build_manifest()
        self.proc = self.root / 'proc'
        self.proc.mkdir()
        self.gate = Admission(self.root / 'state', expected_uid=os.geteuid())
        self.controller = Controller(self.gate, self.payload, ProcessCheck(self.prefix, self.proc))
        self.controller.initialize()

    def closed(self):
        self.assertEqual(self.controller.close(0), 'DRAINED')

    def process(self, *, private=False, mapping=False):
        process = self.proc / '12345'
        process.mkdir()
        (process / 'exe').symlink_to(self.file if private else '/synthetic/unrelated')
        path = str(self.file) if mapping else '/synthetic/unrelated-library'
        (process / 'maps').write_text('1000-2000 r-xp 0 00:00 1 ' + path + '\n')
        return process

    def test_initialize_binds_verified_manifest(self):
        self.assertEqual(self.gate.status(), {'state': 'ACTIVE', 'generation': self.generation})
        self.assertEqual(self.payload.verify(self.generation), self.generation)

    def test_same_payload_manifest_is_stable(self):
        self.assertEqual(self.payload.build_manifest(), self.generation)

    def test_recovery_preserves_generation_and_lock_inodes(self):
        before = {p.name: p.stat().st_ino for p in self.gate.directory.glob('*.lock')}
        self.closed()
        self.assertEqual(self.controller.recover(), self.generation)
        self.assertEqual(self.gate.status()['state'], 'ACTIVE')
        self.assertEqual(before, {p.name: p.stat().st_ino for p in self.gate.directory.glob('*.lock')})

    def test_changed_file_blocks_recovery(self):
        self.closed()
        self.file.write_text('changed synthetic payload\n')
        with self.assertRaises(AdmissionError):
            self.controller.recover()
        self.assertEqual(self.gate.status()['state'], 'BLOCKED')

    def test_regenerated_manifest_cannot_authorize_a_new_generation(self):
        self.closed()
        self.file.write_text('changed synthetic payload\n')
        self.assertNotEqual(self.payload.build_manifest(), self.generation)
        with self.assertRaises(AdmissionError):
            self.controller.recover()
        self.assertEqual(self.gate.status()['generation'], self.generation)
        self.assertEqual(self.gate.status()['state'], 'BLOCKED')

    def test_extra_file_is_not_silently_adopted(self):
        extra = self.prefix / 'libexec/extra'
        extra.write_text('synthetic extra: do not read')
        from unittest.mock import patch
        original = os.open
        def guarded_open(path, *args, **kwargs):
            if Path(path) == extra:
                raise AssertionError('Unknown file contents were opened')
            return original(path, *args, **kwargs)
        with patch('lifecycle_control.os.open', side_effect=guarded_open):
            with self.assertRaises(AdmissionError):
                self.payload.verify(self.generation)

    def test_unsafe_permissions_are_rejected(self):
        self.file.chmod(0o666)
        with self.assertRaises(AdmissionError):
            self.payload.verify(self.generation)

    def test_public_wrapper_is_part_of_the_generation(self):
        self.entries[0].write_text('changed synthetic wrapper')
        with self.assertRaises(AdmissionError):
            self.payload.verify(self.generation)

    def test_manifest_symlink_is_rejected(self):
        manifest = self.prefix / 'libexec/payload-generation.json'
        saved = self.root / 'saved-manifest'
        manifest.rename(saved)
        manifest.symlink_to(saved)
        with self.assertRaises((AdmissionError, OSError)):
            self.payload.verify(self.generation)

    def test_escaping_payload_symlink_is_rejected(self):
        outside = self.root / 'synthetic-outside'
        outside.write_text('outside synthetic input')
        (self.prefix / 'libexec/escape').symlink_to(outside)
        with self.assertRaises(AdmissionError):
            self.payload.verify(self.generation)

    def test_relative_private_symlink_is_verified(self):
        (self.prefix / 'libexec/alias').symlink_to('inert')
        generation = self.payload.build_manifest()
        self.assertEqual(self.payload.verify(generation), generation)

    def test_bootstrap_holder_prevents_recovery(self):
        self.closed()
        fd = os.open(self.gate.directory / 'bootstrap.lock', os.O_RDONLY)
        try:
            fcntl.flock(fd, fcntl.LOCK_SH)
            with self.assertRaises(BlockingIOError):
                self.controller.recover()
        finally:
            os.close(fd)
        self.assertEqual(self.gate.status()['state'], 'DRAINED')

    def test_agent_holder_prevents_reopening_but_stop_remains_possible(self):
        with self.gate.acquire() as operation:
            agent = self.gate.acquire_agent(operation)
        self.addCleanup(agent.close)
        self.closed()
        with self.assertRaises(BlockingIOError):
            self.controller.recover()
        self.assertEqual(self.gate.status()['state'], 'DRAINED')
        with self.gate.acquire_stop():
            pass
        agent.close()
        self.controller.recover()

    def test_timeout_can_be_settled_closed_then_recovered(self):
        with self.gate.acquire():
            self.assertEqual(self.controller.close(0), 'BLOCKED')
        self.assertEqual(self.controller.close(0), 'DRAINED')
        self.controller.recover()
        self.assertEqual(self.gate.status()['state'], 'ACTIVE')

    def test_private_process_metadata_blocks_recovery(self):
        self.closed()
        self.process(private=True)
        with self.assertRaises(AdmissionError):
            self.controller.recover()
        self.assertEqual(self.gate.status()['state'], 'BLOCKED')

    def test_private_mapping_metadata_blocks_recovery(self):
        self.closed()
        self.process(mapping=True)
        with self.assertRaises(AdmissionError):
            self.controller.recover()

    def test_unrelated_process_metadata_is_not_modified(self):
        self.closed()
        process = self.process()
        before = (process / 'maps').read_bytes()
        self.controller.recover()
        self.assertEqual((process / 'maps').read_bytes(), before)
        self.assertEqual(os.readlink(process / 'exe'), '/synthetic/unrelated')

    def test_missing_metadata_for_existing_process_is_uncertainty(self):
        self.closed()
        (self.proc / '12345').mkdir()
        with self.assertRaises(AdmissionError):
            self.controller.recover()
        self.assertEqual(self.gate.status()['state'], 'BLOCKED')

    def test_failed_cold_bootstrap_keeps_blocked_state(self):
        self.process(private=True)
        gate = Admission(self.root / 'cold-state', expected_uid=os.geteuid())
        controller = Controller(gate, self.payload, ProcessCheck(self.prefix, self.proc))
        with self.assertRaises(AdmissionError):
            controller.initialize()
        self.assertEqual(gate.status()['state'], 'BLOCKED')
        with self.assertRaises(FileExistsError):
            controller.initialize()

    def test_foreign_owner_cannot_administer_state(self):
        gate = Admission(self.root / 'foreign-state', expected_uid=os.geteuid() + 1)
        controller = Controller(gate, self.payload, ProcessCheck(self.prefix, self.proc))
        with self.assertRaises(AdmissionError):
            controller.initialize()
        self.assertFalse(gate.directory.exists())


if __name__ == '__main__':
    unittest.main()
