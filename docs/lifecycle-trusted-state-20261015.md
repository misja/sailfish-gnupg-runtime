# Trusted state and same-generation recovery — 2026-10-15

Basis: approved PR #12, merged at `0f661fbf3eba9a539138e372c3b908c854e24920`.
Tracking: [runtime #3](https://github.com/misja/sailfish-gnupg-runtime/issues/3).
Candidate release 0.5 adds verified cold initialization and recovery of the same
installed generation. It does not implement a changed-payload package transaction.

## Payload identity and loading

The recipe generates `libexec/payload-generation.json` after the existing RPM
install-post hooks, including stripping/compression/byte compilation. It covers
private file names, types, modes, content hashes, relative symlinks and both
public wrappers. The manifest itself is excluded from its entries; its exact
SHA-256 is the generation stored in the separate root-owned lifecycle state.
The RPM inspector checks this manifest against final CPIO bytes and root file
ownership, as well as the existing binary/source requirements.

Every public invocation opens the stable root-owned `bootstrap.lock` on FD 9
and takes a shared system-flock lock before Python is loaded. The guardian retains
it through the operation; agent watches close that descriptor and retain their
separate agent registration. Recovery requires exclusive bootstrap access before
reopening admission, preventing a cooperating client with already loaded code
from crossing that recovery boundary. `/usr/bin/flock` is an explicit dependency;
the SDK provided util-linux 2.40.2.

Under its operation registration, the guardian verifies the installed manifest
against the trusted state generation, then checks installed names, types, modes,
root ownership, canonical prefix and symlink containment. Unknown names are
rejected before unknown file contents are opened. The verifier reads only the
declared software payload, not user key homes or password stores. Verification
currently hashes the whole declared payload per operation; device performance
has not been measured. The runtime implementation uses Python 3.9+ APIs; the
SDK tests used Python 3.11. Device dependency acceptance remains separate.

These checks bind local content to a root-controlled manifest/state. They are
not package-signature verification or proof of software origin. Package trust
and distribution acceptance remain separate gates.

## Explicit owner administration

The fixed private `lifecycle-admin.py` supports four actions. It requires the
state owner (root in installed code); it exposes no state/prefix/UID override,
force/reset action, package command or user-home discovery.

| Action | Behavior |
| --- | --- |
| `initialize` | Verify the installed manifest, create fresh state as BLOCKED, exclude bootstrap/operation/agent leases, check public process metadata and reverify before ACTIVE. Existing state is never replaced. |
| `close --timeout N` | Close ACTIVE admission before draining. A timeout remains BLOCKED. A later explicit close can settle finished operations into DRAINED while allowing their users to stop remaining managed agents. |
| `recover` | Exclude loaders, operations and agents; check process metadata and the original generation; reopen only the same verified generation. Payload/process failure retains BLOCKED. Busy registrations leave admission closed. |
| `status` | Report state, verified generation and whether agent leases exist. It does not claim process/socket quiescence. |

After a successful close, agent stop remains available through the existing
public wrapper with an explicit private home. Recovery does not kill processes,
scan user homes or remove any user data. The process check reads executable and
mapping metadata, not argv, environment or key contents. A private executable,
private mapping or unavailable metadata blocks recovery; unrelated fixture
metadata is left untouched.

Administrative syntax for a separately approved deployment/test scope is:

```sh
/usr/bin/python3 -I -B /usr/libexec/sailfish-gnupg/libexec/lifecycle-admin.py status
```

The other action names use the same invocation. No such real root-state action
was executed in this slice: tests inject an owner and isolated installation,
state and proc trees. Low-level `Admission.initialize` remains a primitive for
fixtures; the administrative controller explicitly requests initially BLOCKED
state and performs the full checks before activation.

Recovery refuses modified files, a freshly regenerated manifest or another
installed generation. There is no supported way to bless a new payload through
recovery. Checked package transitions, interrupted package transactions, initial
migration from older wrappers, unregistered callers and unrelated root activity
still need their own protocol and evidence. This is not a ready device upgrade.
The bootstrap lock is advisory coordination for supported entry points, not a
security boundary against the same user/root executing private tools directly.

## Executed evidence

- All 77 host tests and 72 selected SDK tests passed. The five source/package
  fixture tests ran on the host. SDK: 3.13.5, SailfishOS-5.1.0.11-aarch64.
- Tests cover cold-init failure, retained lock inodes, cancelled/timed-out drain,
  agent/loader exclusion, changed code/wrapper/manifest, unsafe modes/symlinks,
  unknown-file non-reading and private/unavailable process metadata. A public
  wrapper test deliberately corrupts the temporary Python entry while bootstrap
  is exclusively locked: the wrapper returns busy before Python parses it.
- A small inert AArch64 RPM was compiled with the existing SDK toolchain and
  built with the production install-post hook. A deliberate postprocessing
  mutation was included correctly in the packaged manifest. CPIO inspection
  checked declared hashes/modes and the postprocessed marker. The initial fixture
  incorrectly required a target `gcc` RPM; that declaration was removed because
  the existing SDK supplies the cross compiler outside the target RPM database.
  No dependency was installed and no dependency checks were bypassed.
- [Probe sources and reproduction](../tools/lifecycle-probe/manifest-probe.md)
  regenerate the hook from the actual runtime recipe. The reproduced probe and
  staged SDK input hashes are in the [bounded record](lifecycle-trusted-state-20261015.json).
- Python/shell syntax, local links and whitespace checks passed.

The full GnuPG runtime RPM was not rebuilt here; only the inert probe RPM was
built. No RPM, dependency or target installation, real GnuPG operation, real root
state initialization, device/OBS action or upstream submission occurred. Power
loss, actual root/proc access, device performance and independent security/release
verification are not established by these implementation self-tests. Issue #3
remains In Progress.
