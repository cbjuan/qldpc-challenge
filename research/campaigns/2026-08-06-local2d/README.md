# Cancelled pre-search scaffold: planar qLDPC codes

This direction was cancelled by the user before `census.py` or any witness
search was run. It is retained only as an audit trail for the local branch;
the active campaign is `../2026-08-06-periodic-bb/`.

This directory records the reproducible scripts and decision journal for the
local-only autoresearch campaign started on 2026-08-06.

Constraints:

- Results stay local on branch `autoresearch/2026-08-06-local`.
- No candidate is written to `codes/`, pushed, submitted, or used to open a PR.
- Packaged candidates and validator verdicts are staged under the gitignored
  `research/candidates/2026-08-06-local2d/` directory.
- Every distance/witness search must run through `make_submission` and be
  followed immediately by `save_submission`; saved rungs are never overwritten.
- A find requires both `passed: true` and
  `gates.novelty.board_advancing: true` from the trusted validator.

## Campaign 1 direction

Target: `local-2d-bilayer × weight-8` (with weight-6 candidates also eligible
through nested track membership).

Family: open-boundary planar bivariate-bicycle codes built by
`research/local2d/boundary_engine.py`.

Initial rolling budget: enumerate the valid rectangular geometries around the
proven `[[192,12,8]]` support pair, promote the structurally most promising
non-board geometries through a `2k -> 8k -> 60k` saved witness ladder, then move
to high-slope nearby support pairs. Exhausting this budget starts the next
campaign; it does not end the continuous research goal.

## Decision journal

- Read `research/AUTORESEARCH.md`, `./qldpc recent`, all current fieldnotes,
  `research/local2d/README.md`, and the `[[192,12,8]]` research note first.
- Avoided `search.screen`, `graft_r1*`, and `corner_detector.detect` because
  their current implementations can perform witness searches without
  persisting the witness.
- Fixed `research/kit/submit.py`'s schema path before staging any candidate;
  it previously pointed at the nonexistent `research/schema/` directory.
