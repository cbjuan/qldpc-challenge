# Prompt for the fresh 64-core Codex session

Copy the text below into the new session after cloning the personal fork.

---

You are taking over exact-distance certification for a completed local qLDPC
autoresearch campaign. Work autonomously and persist every result.

Repository setup:

1. Verify that `origin` is my personal fork, not
   `github.com/unitaryfoundation/qldpc-challenge`.
2. Fetch `origin` and create branch `certification/periodic-bb-exact-64core`
   from `origin/autoresearch/2026-08-06-local`.
3. Read `AGENTS.md`, `research/AUTORESEARCH.md`,
   `research/campaigns/2026-08-06-periodic-bb/certification/README.md`, and
   `research/campaigns/2026-08-06-periodic-bb/certification/targets.json`
   completely before acting.

Objective: attempt exact X/Z distance certification for all 128
board-advancing periodic bivariate-bicycle supports in `targets.json`, using
the machine's 64 cores efficiently. Start with the priority queue in the
handoff README, but do not stop after the first success or timeout. The
existing distances are witness-backed upper bounds; never describe one as
exact unless the unmodified authoritative `verify/certify.py` returns
`d_exact: true` for it.

Hard constraints:

- Never edit anything under `verify/`.
- Never modify `codes/`, open a PR, or submit/push anything to
  `github.com/unitaryfoundation/qldpc-challenge`.
- Push only the certification result branch to my personal fork.
- Do not resume code discovery or generate new code families.
- Preserve every solver result immediately under
  `research/campaigns/2026-08-06-periodic-bb/certification/results/`; a timeout
  is valuable data and must not be discarded.
- A timeout, RIS/decoder agreement, or absence of a lighter witness is not an
  exact proof.

Execution plan:

1. Rebuild `targets.json` with `build_targets.py` and verify it is unchanged.
2. Record candidate hashes, git commit, `verify/certify.py` hash, Python/SciPy/
   HiGHS versions, CPU topology, and RAM.
3. Install/use SciPy through the repository environment and run the stock
   certifier successfully on several existing exact-certified fixtures.
4. Because the stock solver is serial within a candidate, implement a runner
   outside `verify/` that shards the exact same per-side/per-logical-generator
   cutoff MILPs across processes. Validate its aggregate results against the
   stock serial certifier on known exact examples before campaign use.
5. Avoid oversubscription by forcing numerical libraries to one thread per
   worker. Select up to 64 workers subject to measured RAM usage; keep the
   machine busy while avoiding swapping/OOM.
6. Run a staged timeout schedule. Record every per-task result and duration.
   A candidate is exact only if every required task on both sides is proven
   infeasible. Any unknown keeps it at upper-bound status.
7. For every apparent exact closure, rerun the whole candidate with the
   unmodified serial `verify/certify.py`. Only its persisted `d_exact: true`
   output is the final exact claim.
8. If a lighter logical is found, persist all available solver evidence and
   obtain/save an explicit witness through the repository's persistence-first
   submission path before reporting the refutation.
9. Commit and push immutable result batches frequently. Maintain a summary
   table of exact/refuted/timeout/pending targets, wall time, CPU time, and
   timeout budgets.

Begin with environment/integrity checks and the known-exact calibration suite,
then report the execution configuration and proceed without waiting for my
feedback.

---
