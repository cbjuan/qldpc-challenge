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
- 2026-08-06: User prioritized `k^2*d/n` as an additional research metric but
  explicitly rejected `d=2` codes as useful correction-code leaders. Preserve
  such witnesses for the audit trail, but do not promote them to deeper rungs;
  rank useful candidates only once a witnessed `d >= 3` is available.
- 2026-08-07: User shifted allocation toward larger distances. Continue to
  report `k^2*d/n`, but downweight `d=3` in new promotion decisions and favor
  shared factors of order 4--7 plus mutations of the witnessed/known
  `d=9--18` periodic-BB parents. This is a priority change, not a hard distance
  cutoff.
- 2026-08-07: User then set `d >= 8` as the high-distance sweet-spot target.
  Preserve all lower-distance witnesses, but stop promoting them beyond the
  shallow rung. New deep-confirmation budget goes to candidates whose persisted
  witness remains at least 8, centered on proven `d=8,9,14,18` parents.
- 2026-08-07: Candidate 20168, a `10x14` transfer of the local d=9
  support, survived the 400→8k→60k ladder as `[[280,20,8]]` and passed the
  trusted gate as board-advancing. Its witness, verdict, ledger row, and note
  remain local; the search continued without pausing.
- 2026-08-07: Added a deterministic high-distance continuation after the
  hand-picked transfer batch. It exhausts calibrated fixed-short-axis geometry
  grids under `n <= 700`, then continues with support-preserving local
  mutations. `parent_d` is used only as a selection prior; every child must
  obtain and persist its own witness before promotion.
- 2026-08-07: Candidate 20283, the `11x15` continuation of the local d=9
  support, stayed `[[330,22,9]]` through 1M and passed the trusted gate as
  board-advancing. The other eight large candidates in that confirmation batch
  passed but were non-advancing; all verdicts were retained.
- 2026-08-07: The first support-preserving high-distance mutation batch yielded
  four additional trusted board-advancing d=8 codes: `[[448,56,8]]` in weight
  8 and `[[644,46,8]]`, `[[616,44,8]]`, `[[532,38,8]]` in weight 6. Each held
  through 1M; all non-advancing siblings and their witnesses were retained.
- 2026-08-07: Exact `m=15` transfers of the local d=9 support yielded four
  trusted board-advancing codes through 1M: `[[690,46,9]]`, `[[660,44,9]]`,
  `[[600,40,9]]`, and `[[570,38,9]]`. The separate `m=8` transfer reached a
  validated local `[[688,100,8]]` FOM leader but was board-non-advancing.
- 2026-08-07: Auditing the high-d grid exposed that the original reused-Python
  path kept raw fast evidence but did not merge a lighter accelerated 8k
  witness into the next candidate document. The runner now merges every saved
  source-rung fast document before promotion, making distance evidence
  monotone. Pre-fix 60k documents remain audit artifacts only; final 1M runs
  use the corrected carry-forward path.
- 2026-08-07: Hardened witness carry-forward again: promotion and the new
  `consolidate` command now independently check both sides of every persisted
  submission document, including the shallow Python rung, and retain the
  lightest X and Z witnesses in a fresh immutable final document. Only these
  all-rung documents are sent to the trusted gate.
- 2026-08-07: Exact high-rate transfers produced 20 trusted board-advancing
  `d=8--9` candidates. The strongest new point is `[[464,72,8]]` with
  `k^2*d/n=89.38`; the distance-nine branch reaches `[[540,36,9]]`. All
  candidate documents, verdicts, and notes remain local.
- 2026-08-07: The exact high-distance grid and parent-d>=14 mutation batch
  produced 14 trusted board-advancing candidates. The observed sweet spots are
  `[[432,24,12]]`, `[[630,14,20]]`, and `[[576,12,28]]`; the largest witnessed
  distance is 36 at `[[648,4,36]]`. These are upper bounds, not exact-distance
  claims, and literature novelty remains unverified.
- 2026-08-07: Began a reproducibility-preserving second mutation epoch at
  candidate ID 49163. Earlier candidate IDs are unchanged. New proposals draw
  mostly from the gate-passing d=12--36 parents, with a small allocation to the
  best d=8--9 high-rate parents so the search can move toward higher d without
  abandoning useful k.
- 2026-08-07: A read-only geometry audit identified the strongest scaling on
  the July support (`30x7`, `30x9`, `30x11` witnessed at d=26,30,34) and the
  known-288/360 distance-ceiling mutations. Added a finite, immutable exact-
  transfer block at IDs 51163--51174, the untouched post-census cursor; 11 of
  its 12 encoded probes are connected and enter the next shallow queue. The
  earlier proposal stream remains byte-for-byte addressable by candidate ID.
- 2026-08-07: The first validated-parent balance probe, c50641, followed a
  400→8k→60k→1M ladder of 24→20→20→20 and passed the trusted gate as the
  board-advancing `[[576,16,20]]`. Four companion k=12--16 candidates also
  passed but were board-non-advancing. The result remains a witness-backed
  upper bound with literature novelty unverified.
- 2026-08-07: Three early high-distance epoch-2 children also passed as
  board-advancing: `[[600,8,26]]`, `[[540,8,26]]`, and a structurally distinct
  `[[540,8,30]]`. The last descended 38→32→32→30 at 1M, demonstrating why the
  deep rung and all-rung witness merge remain mandatory.
- 2026-08-07: The next epoch-2 high-distance queue keeps the 12 connected
  candidates in `selection-validated-highd-epoch2-002.json`. Seven additional
  distance-ceiling proposals and all three high-k balance probes split into
  two or three equal connected components, so the normal structural selector
  excluded them before witness work; do not bypass that gate merely to inflate
  aggregate `k` with direct sums.
- 2026-08-07: Refreshed the validated-parent mutation pool at the untouched
  cursor 51663 with c48101 `[[660,8,34]]`, c48487 `[[686,6,36]]`, and c48911
  `[[630,8,28]]`. Each parent is a connected, structurally distinct periodic
  BB code that passed the trusted gate; its witnessed distance is only a prior
  for children, which must persist their own witnesses.
- 2026-08-07: Structurally censused refreshed IDs 51663--54662, exactly 40
  proposals for every one of the 15 parent/five-kernel pairs. The 3,000
  proposals yielded 508 new encoders, 476 connected. Froze 18 connected
  `parent_d >= 28` records in `selection-refreshed-highd-epoch3-001.json`
  (at most two per parent, four per geometry, and six per kernel), plus a
  disjoint six-record `parent_d=20--26` useful-k balance queue in
  `selection-refreshed-highd-balance-001.json`. No witness search was run;
  `parent_d` remains a scheduling prior, not a child-distance claim.
- 2026-08-07: Continued the immutable refreshed census through IDs
  54663--57662. The 3,000 proposals yielded 369 new encoders, 345 connected;
  182 connected records had `parent_d >= 28`. Froze 18 in
  `selection-refreshed-highd-epoch4-001.json`, retaining the epoch-3 caps of
  two per parent, four per geometry, and six per kernel. Fourteen have
  `k >= 8`; the four `k=4` records are distance-ceiling probes from
  `d=28--36` parents. A disjoint six-record balance queue in
  `selection-refreshed-highd-balance-epoch4-001.json` keeps `k=8--10`
  children of the validated `d=20--26` parents. No witness search was run;
  parent distance is only a structural scheduling prior.
