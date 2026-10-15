# IPC supervision evidence — 2026-10-15

Historical test record: the admission prototype described by the original PR
and its recorded test counts has since been removed. Only IPC supervision is
retained; these historical counts are not current-suite counts.

Basis: reviewed [contract](lifecycle-contract.md), merged in PR #10 at
`ac206931dba69670490aae112c417d77b7112371`. Tracking: [issue #3](https://github.com/misja/sailfish-gnupg-runtime/issues/3).
The retained change fixes direct IPC supervision. Package coordination remains open.

## Direct IPC supervision

`runtime_timed` now waits for a separate supervisor. That supervisor owns the
IPC helper and watchdog; loss of the calling wrapper does not change the helper's
parent identity. The existing PID/start-time/parent comparisons remain intact.
The supervisor continues until normal completion or the existing 15-second
timeout plus one-second termination grace. Only a temporary test copy shortens
the 15-second interval.

A successful helper preserves stdout and exit status. A watchdog timeout returns
124 even if the helper subsequently reports success. Unexpected watchdog failure
returns 78. The SDK exposed this distinction: emulated helper termination could
appear successful after TERM. The regression now checks a helper deliberately
handling TERM with exit zero.

The inert observer now supports `--require-cleanup`, making surviving IPC a test
failure. In both host and SDK measurements the direct helper was no longer alive
before observer cleanup in all three cases: live wrapper, wrapper TERM, wrapper
KILL. Live-owner timeout returned 124. The old policy failed the same regression.
This does not establish cleanup after the supervisor itself dies, arbitrary
helper descendants, daemon agents or a whole interrupted GnuPG operation.


## Executed verification

- Host: all 39 runtime repository tests passed.
- Existing SDK 3.13.5 / SailfishOS-5.1.0.11-aarch64: 34 selected policy, admission
  and IPC tests passed. Five package/source fixture tests ran on the host only.
- Both environments: live-owner/TERM/KILL inert observer cases passed with
  `--require-cleanup`. The original policy regression returned the expected
  failure on the host only.
- All six staged SDK input file hashes match the review worktree. Exact hashes
  and bounded results are in the [machine-readable record](lifecycle-implementation-20261015.json).
- Shell syntax, local document links and whitespace checks passed.

Commands from the repository root:

```sh
python3 -m unittest discover -s tests -q
python3 tools/test-interrupted-watchdog.py --require-cleanup --output /tmp/lifecycle-result.json
```

SDK tests staged only the six recorded files in a new `build/lifecycle-review`
directory within the existing clean-build checkout. The selected tests used
`TMPDIR=/home/ubuntu/sflc-tmp-20261015`: Scratchbox2's physical `/tmp` path caused
the strict socket-parent check to reject one initial fixture; using a long shared
work path then exceeded the Unix-socket path limit. A short shared fixture path
resolved both without relaxing production checks. The first SDK observer also
failed the live-owner exit-status requirement, leading to the explicit timeout
result and its regression test above. These earlier failures are not counted as
passes.

No cryptographic operation, real user store/home inspection, package rebuild,
installation, device/OBS action or upstream submission occurred. These are
implementation self-tests, not independent security or release verification.
The source changes are prepared for maintainer review; issue #3 remains open.
