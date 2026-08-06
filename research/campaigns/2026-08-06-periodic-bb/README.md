# Continuous local autoresearch: periodic bivariate-bicycle codes

This is the active, local-only campaign selected by the user. The construction
lock is exact:

```text
G = Z_l x Z_m
H_X = [A | B]
H_Z = [B^T | A^T]
```

`A` and `B` may contain arbitrary monomials and may have unequal support
sizes. Lattice dimensions and check weights are unrestricted within the
repository schema (`2*l*m <= 700`, total check weight at most 32). The campaign
does not include open-boundary planar, twisted-torus, generalized-bicycle,
coset, lifted-product, or balanced-product constructions.

## Local-only policy

- Work stays on the local `autoresearch/2026-08-06-local` branch.
- Nothing is written to `codes/`, pushed, submitted, or used to open a PR.
- Structural ledgers, packaged candidates, full validator verdicts, and
  campaign notes live under this directory so a local commit preserves them.
- Every witness search is tied to a candidate that has already passed through
  `submit.make_submission`; every resulting witness is written immediately.
- A find requires both `passed: true` and
  `gates.novelty.board_advancing: true` from `validate_candidate`.
- Finding a code does not stop the campaign.

## Initial lanes

The current board audit at `origin/main@240ed51` identifies two high-rate gaps:

1. weight 6, `145 <= n <= 287`, aiming for `k >= 26`;
2. weight 8, `288 <= n <= 470`, aiming for `k >= 52`.

The generator also gives continuing coverage to weight 4, lower-rate/high-
distance candidates, unequal support sizes, weights above 8, new rectangular
group types, and mutations of reproducible historical BB seeds.

Previously mined regions are down-weighted, not treated as proofs of
exhaustion: 3+3 and selected 4--5 term searches on `12x12`, `15x12`, `30x6`,
and the old random rectangle sweep. Exact translated `A=B` is skipped because
it has a structural weight-2 logical whenever it encodes.

## Reproducible commands

```bash
env UV_CACHE_DIR=.uv-cache uv run python \
  research/campaigns/2026-08-06-periodic-bb/campaign.py census --count 20000

env UV_CACHE_DIR=.uv-cache uv run python \
  research/campaigns/2026-08-06-periodic-bb/campaign.py select --limit 48
```

Witness-producing commands are deliberately separate. `package` creates and
saves the NumPy witness result. `confirm` first saves that result, then runs the
accelerated rung and immediately saves both its raw witness evidence and the
updated candidate. `validate` saves the trusted gate's complete verdict.

## Decision journal

- 2026-08-06: Read `AUTORESEARCH.md`, all fieldnotes, current board activity,
  and the notes for the recent mixed-monomial BB campaign.
- 2026-08-06: User selected periodic rectangular BB exclusively, with no
  restriction on weight, lattice size, support size, or monomial shape.
- 2026-08-06: Fast-forwarded the local branch to `origin/main@240ed51`; the
  seven newly arrived codes were non-BB and did not change these lanes.
- 2026-08-06: Built the optional `gf2_fast` extension locally. Its witnesses
  are accepted only after the Python GF(2) checks and are always persisted.
