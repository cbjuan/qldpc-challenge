# Exact-distance certification handoff

This directory hands the completed periodic bivariate-bicycle campaign to a
separate 64-core machine. It is an exact-certification campaign, not a new-code
search and not a challenge submission.

## Inputs and trust boundary

- `../FINDINGS.md` is the human-readable ledger.
- `targets.json` lists all 129 canonical candidate/verdict pairs: 128 trusted,
  board-advancing supports plus the `[[40,2,4]]` calibration support.
- Every target carries SHA-256 hashes for transfer/integrity checking.
- `build_targets.py` deterministically rebuilds the manifest and fails if a
  canonical pair is missing, inconsistent, non-passing, or from another family.
- `verify/` is immutable. `verify/certify.py` is the authoritative exact solver.
- Existing witnesses establish upper bounds. Exactness requires proving the
  absence of every lighter logical. A timeout or heuristic agreement is not an
  exact result.

## Recommended queue

Calibrate the environment and parallel runner first on known exact-certified
board fixtures, then on these campaign targets:

1. c60702 `[[630,14,28]]`, balanced `(X,Z)=(28,28)`, 28 logical MILP tasks.
2. c56213 `[[576,12,30]]`, 24 tasks; best campaign board FOM.
3. c58579 `[[686,18,24]]`, balanced, 36 tasks; best `k^2*d/n` for `d>=20`.
4. c60754 `[[576,16,20]]`, balanced, 32 tasks.
5. c50584 `[[630,8,34]]`, 16 tasks.
6. c48487 `[[686,6,36]]`, 12 tasks.
7. c49220 `[[648,4,38]]`, 8 tasks but the hardest cutoff (`d-1=37`).
8. c45113 `[[432,24,12]]`, then c20168 `[[280,20,8]]` and c20283
   `[[330,22,9]]` as high-`k`/lower-cutoff calibrations.

After this priority queue, attempt every board-advancing target in
`targets.json`; structurally distinct supports must remain separate even when
their `(n,k,d)` parameters coincide.

## Using 64 cores safely

The stock certifier is serial within a candidate: it solves one MILP per
logical-basis row and side, approximately `2*k` tasks. A separate runner may
parallelize those tasks without editing `verify/` by importing the pinned
certifier and applying its exact `_exists_lighter` predicate to one logical row
per worker. Aggregate conservatively:

- any feasible task: the submitted side value is not exact;
- all tasks proven infeasible: that side is exact;
- any timeout/unknown and no feasible task: the side remains an upper bound;
- `d_exact` only when both sides close.

Validate any sharded runner against the unmodified serial
`verify/certify.py` on several existing `certs/*.json` examples. Before calling
a campaign target exact, rerun that target through the authoritative serial
certifier and persist its `d_exact: true` output.

Some SciPy/HiGHS builds can write a native diagnostic to file descriptor 1
after Python has emitted the certifier JSON. For a fresh serial-confirmation
stage, `confirm_serial.py --isolate-native-stdout` loads the single,
hash-recorded `serial_stdout_isolation/sitecustomize.py` module in the child
only. It keeps Python's `sys.stdout` on the captured stdout pipe and redirects
later native fd-1 writes to captured stderr. The stock certifier command and
source remain unchanged, parsing remains strict `json.loads`, and both raw
streams are persisted. The wrapper rejects bytecode caches or sibling modules,
records the complete child environment override, and requires a source-hash
activation marker before accepting output. Calibrate this mode on a known exact
case before using it to close a campaign target.

Prevent numerical-library oversubscription (`OMP_NUM_THREADS=1`,
`OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1`) and choose process concurrency
from both the 64-core count and available RAM. Each MILP builds dense matrices;
64 simultaneous processes may be inappropriate on a low-memory host.

## Persistence contract

Write immutable results under `certification/results/`, one directory per
candidate ID. Preserve:

- candidate and certifier SHA-256 hashes;
- git commit, dependency versions, host/core/RAM information;
- per-side/per-logical-row status, runtime, cutoff, seed if applicable, and
  solver output;
- aggregate status (`exact`, `refuted`, or `timeout`);
- the final authoritative serial-certifier JSON for every exact result.

Checkpoint and push result batches only to a personal-fork branch. Never edit
`codes/` or `verify/`, never open a PR, and never push or submit to
`unitaryfoundation/qldpc-challenge`.
