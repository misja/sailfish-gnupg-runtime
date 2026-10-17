"""Synthetic /proc and socket fixtures; execute the unchanged BusyBox policy.

No GnuPG binary, real key home, existing agent or package operation is used.
The fake metadata tests admission decisions, not kernel race resistance.
"""
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest

POLICY = Path(__file__).resolve().parents[1] / "runtime/runtime-policy.sh"


@unittest.skipUnless(Path("/usr/bin/busybox").is_file(), "BusyBox required")
class AgentPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="synthetic-agent-policy-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.prefix = self.root / "private"
        self.proc = self.root / "proc"
        self.pid = self.proc / "12345"
        self.home = self.root / "home"
        self.home.mkdir(mode=0o700)
        self.pid.mkdir(parents=True)
        (self.prefix / "bin").mkdir(parents=True)
        (self.prefix / "lib").mkdir()
        (self.prefix / "bin/gpg-agent").write_text("inert executable identity fixture")
        (self.pid / "exe").symlink_to(self.prefix / "bin/gpg-agent")
        self.argv = [str(self.prefix / "bin/gpg-agent"), "--homedir",
                     str(self.home), "--no-options", "--daemon"]
        self.write_argv()
        self.mappings = []
        for soname in ("libgcrypt.so.20", "libassuan.so.9", "libgpg-error.so.0", "libnpth.so.0"):
            target = self.prefix / "lib" / (soname + ".fixture")
            target.write_text("inert library identity fixture")
            (self.prefix / "lib" / soname).symlink_to(target.name)
            self.mappings.append(f"1000-2000 r-xp 0000 00:00 {target.stat().st_ino} {target}\n")
        self.write_maps()
        self.socket_path = self.home / "S.gpg-agent"
        self.helper("gpgconf", 'printf "%s\\n" "$GNUPGHOME/S.gpg-agent"')
        self.helper("gpg-connect-agent", "printf 'D 12345\\nOK\\n'")

    def helper(self, name, body):
        path = self.prefix / "bin" / name
        path.write_text("#!/usr/bin/busybox sh\n" + body + "\n")
        path.chmod(0o700)

    def write_argv(self):
        (self.pid / "cmdline").write_bytes(b"\0".join(x.encode() for x in self.argv) + b"\0")

    def write_maps(self):
        (self.pid / "maps").write_text("".join(self.mappings))

    def run_policy(self, function="policy_verify_agent", pid="12345"):
        command = '. "$1"; private_prefix=$2; proc_root=$3; agent_pid=$4; ' + function
        return subprocess.run(["/usr/bin/busybox", "sh", "-c", command, "fixture",
                               str(POLICY), str(self.prefix), str(self.proc), pid],
                              env={"PATH": "/usr/bin:/bin", "LC_ALL": "C",
                                   "SAILFISH_GNUPGHOME": str(self.home)},
                              capture_output=True, text=True, timeout=5)

    def bind_socket(self):
        connection = socket.socket(socket.AF_UNIX)
        self.addCleanup(connection.close)
        connection.bind(str(self.socket_path))
        self.socket_path.chmod(0o700)

    def test_current_private_identity_is_accepted(self):
        self.assertEqual(self.run_policy().returncode, 0)

    def test_replaced_agent_executable_is_rejected(self):
        executable = self.prefix / "bin/gpg-agent"
        executable.rename(executable.with_suffix(".old"))
        executable.write_text("changed payload")
        (self.pid / "exe").unlink()
        (self.pid / "exe").symlink_to(executable.with_suffix(".old"))
        self.assertEqual(self.run_policy().returncode, 78)

    def test_replaced_private_executable_is_accepted(self):
        (self.pid / "exe").unlink()
        (self.pid / "exe").symlink_to(str(self.prefix / "bin/gpg-agent") + " (deleted)")
        self.assertEqual(self.run_policy().returncode, 0)

    def test_unmanaged_launch_options_are_rejected(self):
        self.argv.append("--allow-loopback-pinentry")
        self.write_argv()
        self.assertEqual(self.run_policy().returncode, 78)

    def test_other_home_is_rejected(self):
        self.argv[2] = str(self.root / "other-home")
        self.write_argv()
        self.assertEqual(self.run_policy().returncode, 78)

    def test_stock_crypto_mapping_is_rejected(self):
        self.mappings[0] = self.mappings[0].replace(str(self.prefix / "lib"), "/usr/lib64")
        self.write_maps()
        self.assertEqual(self.run_policy().returncode, 78)

    def test_unlinked_private_mapping_is_accepted(self):
        self.mappings[0] = self.mappings[0].rstrip() + " (deleted)\n"
        self.write_maps()
        self.assertEqual(self.run_policy().returncode, 0)

    def test_replaced_private_library_inode_is_accepted(self):
        library = self.prefix / "lib/libgcrypt.so.20.fixture"
        library.rename(library.with_suffix(".old"))
        library.write_text("changed library payload")
        self.assertEqual(self.run_policy().returncode, 0)

    def test_previous_private_library_filename_is_accepted(self):
        self.mappings[0] = self.mappings[0].replace("libgcrypt.so.20.fixture", "libgcrypt.so.20.previous")
        self.mappings[0] = self.mappings[0].rstrip() + " (deleted)\n"
        self.write_maps()
        self.assertEqual(self.run_policy().returncode, 0)

    def test_nested_library_path_is_rejected(self):
        self.mappings[0] = self.mappings[0].replace("/lib/libgcrypt", "/lib/nested/libgcrypt")
        self.write_maps()
        self.assertEqual(self.run_policy().returncode, 78)

    def test_malformed_deleted_mapping_suffix_is_rejected(self):
        self.mappings[0] = self.mappings[0].rstrip() + " (deleted) extra\n"
        self.write_maps()
        self.assertEqual(self.run_policy().returncode, 78)

    def test_malformed_deleted_executable_suffix_is_rejected(self):
        (self.pid / "exe").unlink()
        (self.pid / "exe").symlink_to(str(self.prefix / "bin/gpg-agent") + " (deleted) extra")
        self.assertEqual(self.run_policy().returncode, 78)

    def test_missing_required_mapping_is_rejected(self):
        self.mappings.pop()
        self.write_maps()
        self.assertEqual(self.run_policy().returncode, 78)

    def test_invalid_pid_is_rejected(self):
        for pid in ("", "0", "../12345", "12345x"):
            with self.subTest(pid=pid):
                self.assertEqual(self.run_policy(pid=pid).returncode, 78)

    def test_absent_socket_reports_unknown_process_state(self):
        self.assertEqual(self.run_policy("policy_agent_status").returncode, 3)

    def test_regular_file_socket_is_rejected(self):
        self.socket_path.write_text("not a socket")
        self.assertEqual(self.run_policy("policy_agent_status").returncode, 78)

    def test_symlink_socket_is_rejected(self):
        self.bind_socket()
        target = self.home / "real-socket"
        self.socket_path.rename(target)
        self.socket_path.symlink_to(target)
        self.assertEqual(self.run_policy("policy_agent_status").returncode, 78)

    def test_socket_permissions_are_enforced(self):
        self.bind_socket()
        self.socket_path.chmod(0o777)
        self.assertEqual(self.run_policy("policy_agent_status").returncode, 78)

    def test_socket_pid_and_current_identity_are_checked_together(self):
        self.bind_socket()
        self.assertEqual(self.run_policy("policy_agent_status").returncode, 0)
        self.helper("gpg-connect-agent", "printf 'OK\\n'")
        self.assertEqual(self.run_policy("policy_agent_status").returncode, 78)


if __name__ == "__main__":
    unittest.main()
