#!/usr/bin/env python3
"""Reproducible, persistence-first periodic BB autoresearch campaign.

Structural commands never call a distance routine. Witness-producing commands
save each result under ``artifacts/`` and never overwrite an earlier rung.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ARTIFACTS = HERE / "artifacts"
STRUCTURAL = ARTIFACTS / "structural.jsonl"
STATE = ARTIFACTS / "state.json"

for path in (ROOT / "research" / "kit", ROOT / "verify"):
    sys.path.insert(0, str(path))

from bb import build_bb  # noqa: E402
from css import commutes, compute_k, in_rowspace, verify_css  # noqa: E402
from submit import make_submission, save_submission  # noqa: E402

try:  # structural census can fall back; confirmation requires the extension.
    import gf2_fast  # type: ignore  # noqa: E402
except ImportError:  # pragma: no cover - exercised only without ``make fast``
    gf2_fast = None


VERSION = "periodic-bb-v1"
MASTER_SEED = 20260806

SEEDS = [
    # Current exact board points.
    {"l": 15, "m": 12,
     "A": [(0, 0), (4, 0), (0, 2), (4, 2)],
     "B": [(0, 0), (8, 0), (0, 4), (2, 4)]},
    {"l": 12, "m": 12,
     "A": [(0, 0), (1, 3), (5, 3)],
     "B": [(0, 0), (3, 1), (3, 5)]},
    {"l": 12, "m": 12,
     "A": [(0, 0), (1, 0), (0, 5), (1, 5)],
     "B": [(0, 0), (0, 1), (5, 0), (5, 1)]},
    {"l": 18, "m": 8,
     "A": [(0, 0), (1, 0), (0, 5), (1, 5)],
     "B": [(0, 0), (0, 1), (5, 0), (5, 1)]},
    # Reproducible witnessed seeds from the July local branch.
    {"l": 15, "m": 7,
     "A": [(8, 2), (2, 4), (10, 6)],
     "B": [(3, 0), (6, 3), (7, 5)]},
    {"l": 10, "m": 12,
     "A": [(2, 5), (7, 4), (8, 6)],
     "B": [(9, 1), (5, 11), (3, 9)]},
]


def stable_seed(*parts: object) -> int:
    raw = "|".join(str(p) for p in (VERSION, MASTER_SEED, *parts)).encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def rng_for(*parts: object) -> np.random.Generator:
    return np.random.default_rng(stable_seed(*parts))


def normalize_support(support: Iterable[tuple[int, int]], l: int, m: int) -> list[tuple[int, int]]:
    parity: set[tuple[int, int]] = set()
    for a, b in support:
        term = (int(a) % l, int(b) % m)
        if term in parity:
            parity.remove(term)
        else:
            parity.add(term)
    return sorted(parity)


def translated_support_key(support: list[tuple[int, int]], l: int, m: int) -> tuple[tuple[int, int], ...]:
    if not support:
        return ()
    return min(
        tuple(sorted(((a - a0) % l, (b - b0) % m) for a, b in support))
        for a0, b0 in support
    )


def canonical_key(spec: dict) -> str:
    l, m = int(spec["l"]), int(spec["m"])
    A = [tuple(x) for x in spec["A"]]
    B = [tuple(x) for x in spec["B"]]
    variants = []
    for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        ca = translated_support_key([((sx * a) % l, (sy * b) % m) for a, b in A], l, m)
        cb = translated_support_key([((sx * a) % l, (sy * b) % m) for a, b in B], l, m)
        variants.extend(((l, m, ca, cb), (l, m, cb, ca)))
        if l == m:
            sa = translated_support_key([(b, a) for a, b in ca], l, m)
            sb = translated_support_key([(b, a) for a, b in cb], l, m)
            variants.extend(((l, m, sa, sb), (l, m, sb, sa)))
    canonical = min(variants)
    return hashlib.sha256(repr(canonical).encode()).hexdigest()[:24]


def is_translated_equal(spec: dict) -> bool:
    l, m = int(spec["l"]), int(spec["m"])
    A = [tuple(x) for x in spec["A"]]
    B = [tuple(x) for x in spec["B"]]
    return translated_support_key(A, l, m) == translated_support_key(B, l, m)


@lru_cache(maxsize=None)
def geometry_pool(ncells_min: int, ncells_max: int) -> tuple[tuple[int, int], ...]:
    return tuple((l, m) for l in range(2, ncells_max + 1)
                 for m in range(l, ncells_max + 1)
                 if ncells_min <= l * m <= ncells_max)


def random_support(rng: np.random.Generator, l: int, m: int, weight: int) -> list[tuple[int, int]]:
    if weight < 1 or weight > l * m:
        raise ValueError(f"invalid support weight {weight} on {l}x{m}")
    population = np.arange(1, l * m, dtype=int)
    chosen = [] if weight == 1 else rng.choice(population, size=weight - 1, replace=False).tolist()
    return [(0, 0)] + [(int(q) // m, int(q) % m) for q in chosen]


def axis_mixed_support(rng: np.random.Generator, l: int, m: int, weight: int) -> list[tuple[int, int]]:
    terms = {(0, 0)}
    pools = [
        [(a, 0) for a in range(1, l)],
        [(0, b) for b in range(1, m)],
        [(a, b) for a in range(1, l) for b in range(1, m)],
    ]
    turn = int(rng.integers(0, 3))
    while len(terms) < weight:
        pool = pools[turn % 3]
        if pool:
            terms.add(pool[int(rng.integers(0, len(pool)))])
        turn += 1
    return sorted(terms)


def poly_product(left: list[tuple[int, int]], right: list[tuple[int, int]],
                 l: int, m: int) -> list[tuple[int, int]]:
    return normalize_support(((a + c, b + d) for a, b in left for c, d in right), l, m)


def factored_support(rng: np.random.Generator, l: int, m: int, weight: int,
                     factor: list[tuple[int, int]]) -> list[tuple[int, int]] | None:
    if weight % len(factor):
        return None
    base_weight = weight // len(factor)
    for _ in range(30):
        base = random_support(rng, l, m, base_weight)
        out = poly_product(factor, base, l, m)
        if len(out) == weight:
            return out
    return None


def mutate_seed(rng: np.random.Generator) -> dict:
    parent_index = int(rng.integers(0, len(SEEDS)))
    parent = copy.deepcopy(SEEDS[parent_index])
    l, m = parent["l"], parent["m"]
    for side in ("A", "B"):
        parent[side] = normalize_support(parent[side], l, m)
    side = "A" if int(rng.integers(0, 2)) == 0 else "B"
    terms = set(parent[side])
    ordered_terms = sorted(terms)
    old = ordered_terms[int(rng.integers(0, len(ordered_terms)))]
    terms.remove(old)
    while True:
        new = (int(rng.integers(0, l)), int(rng.integers(0, m)))
        if new not in terms:
            terms.add(new)
            break
    parent[side] = sorted(terms)
    parent["parent"] = parent_index
    return parent


def profile_for_lane(rng: np.random.Generator, lane: str) -> tuple[int, int]:
    profiles = {
        "w4": [(2, 2), (1, 3), (3, 1)],
        "w6-gap": [(3, 3), (2, 4), (4, 2), (1, 5), (5, 1)],
        "w8-gap": [(4, 4), (3, 5), (5, 3), (2, 6), (6, 2)],
    }
    if lane in profiles:
        options = profiles[lane]
        return options[int(rng.integers(0, len(options)))]
    total = int(rng.integers(4, 17))
    wa = int(rng.integers(1, total))
    return wa, total - wa


def proposal(candidate_id: int) -> dict:
    rng = rng_for("proposal", candidate_id)
    lane_roll = candidate_id % 20
    if lane_roll < 2:
        lane, pool = "w4", geometry_pool(18, 180)
    elif lane_roll < 12:
        lane, pool = "w6-gap", geometry_pool(73, 143)
    elif lane_roll < 18:
        lane, pool = "w8-gap", geometry_pool(144, 235)
    else:
        lane, pool = "breadth", geometry_pool(24, 350)
    l, m = pool[int(rng.integers(0, len(pool)))]
    wa, wb = profile_for_lane(rng, lane)
    kernel = (candidate_id // 20) % 6

    if kernel == 0:
        A, B = random_support(rng, l, m, wa), random_support(rng, l, m, wb)
        kernel_name = "uniform"
    elif kernel == 1:
        A, B = axis_mixed_support(rng, l, m, wa), axis_mixed_support(rng, l, m, wb)
        kernel_name = "axis-mixed"
    elif kernel == 2 and wa == wb:
        A = axis_mixed_support(rng, l, m, wa)
        if l == m:
            B = normalize_support(((b, a) for a, b in A), l, m)
        else:
            B = random_support(rng, l, m, wb)
        if int(rng.integers(0, 3)) == 0:
            idx = int(rng.integers(0, len(B)))
            B[idx] = (int(rng.integers(0, l)), int(rng.integers(0, m)))
            B = normalize_support(B, l, m)
            if len(B) != wb:
                B = random_support(rng, l, m, wb)
        kernel_name = "swap-motif"
    elif kernel == 3 and wa % 2 == 0 and wb % 2 == 0:
        factor = [(0, 0), (int(rng.integers(1, l)), int(rng.integers(0, m)))]
        A = factored_support(rng, l, m, wa, factor)
        B = factored_support(rng, l, m, wb, factor)
        if A is None or B is None:
            A, B = random_support(rng, l, m, wa), random_support(rng, l, m, wb)
            kernel_name = "uniform-factor-fallback"
        else:
            kernel_name = "shared-binomial-factor"
    elif kernel == 4 and wa == 4 and wb == 4:
        a, b = int(rng.integers(1, l)), int(rng.integers(1, m))
        c, d = int(rng.integers(1, l)), int(rng.integers(1, m))
        A = [(0, 0), (a, 0), (0, b), (a, b)]
        B = [(0, 0), (c, 0), (0, d), (c, d)]
        if int(rng.integers(0, 2)):
            B[-1] = (int(rng.integers(0, l)), d)
        B = normalize_support(B, l, m)
        if len(B) != 4:
            B = random_support(rng, l, m, 4)
        kernel_name = "cross-factor"
    elif kernel == 5:
        seeded = mutate_seed(rng)
        l, m, A, B = seeded["l"], seeded["m"], seeded["A"], seeded["B"]
        lane = "seed-mutation"
        kernel_name = "seed-mutation"
    else:
        A, B = random_support(rng, l, m, wa), axis_mixed_support(rng, l, m, wb)
        kernel_name = "hybrid"

    A, B = normalize_support(A, l, m), normalize_support(B, l, m)
    return {
        "family": "bivariate-bicycle",
        "construction": "periodic-rectangular-torus",
        "candidate_id": candidate_id,
        "generator_version": VERSION,
        "proposal_seed": stable_seed("proposal", candidate_id),
        "lane": lane,
        "proposal_kernel": kernel_name,
        "l": l,
        "m": m,
        "A": [list(x) for x in A],
        "B": [list(x) for x in B],
    }


def weight_class(weight: int) -> str:
    if weight <= 4:
        return "weight-4"
    if weight <= 6:
        return "weight-6"
    if weight <= 8:
        return "weight-8"
    return "any-weight"


def automatic_k_threshold(n: int, weight: int) -> int | None:
    if weight <= 4:
        return 4
    if weight <= 6:
        return 14 if n < 144 else 26 if n < 288 else 50
    if weight <= 8:
        if n < 128:
            return None
        if n < 144:
            return 22
        if n < 210:
            return 26
        if n < 288:
            return 28
        if n < 472:
            return 52
        if n < 488:
            return 124
        if n < 568:
            return 128
        if n < 584:
            return 148
        return 152
    if 117 <= n <= 169:
        return 46
    if 170 <= n <= 200:
        return 54
    if 252 <= n <= 491:
        return 132
    return None


def exact_k(HX: np.ndarray, HZ: np.ndarray) -> int:
    if gf2_fast is not None:
        return int(gf2_fast.compute_k(HX, HZ))
    return int(compute_k(HX, HZ))


def component_profile(HX: np.ndarray, HZ: np.ndarray) -> tuple[int, list[int]]:
    """Connected components of the qubit interaction graph.

    A disconnected graph is a direct sum and is logged but kept out of the
    main promotion queue. This is a structural filter, not a distance claim.
    """
    n = int(HX.shape[1])
    parent = list(range(n))
    sizes = [1] * n

    def find(q: int) -> int:
        while parent[q] != q:
            parent[q] = parent[parent[q]]
            q = parent[q]
        return q

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        if sizes[ra] < sizes[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        sizes[ra] += sizes[rb]

    for row in np.vstack([HX, HZ]):
        support = np.flatnonzero(row)
        if len(support) > 1:
            first = int(support[0])
            for q in support[1:]:
                union(first, int(q))
    counts: dict[int, int] = defaultdict(int)
    for q in range(n):
        counts[find(q)] += 1
    profile = sorted(counts.values(), reverse=True)
    return len(profile), profile


def load_records() -> list[dict]:
    if not STRUCTURAL.exists():
        return []
    return [json.loads(line) for line in STRUCTURAL.read_text().splitlines() if line.strip()]


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"generator_version": VERSION, "next_candidate_id": 0,
            "proposals": 0, "encoded": 0, "duplicates": 0, "traps": 0}


def save_state(state: dict) -> None:
    STATE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def command_census(args: argparse.Namespace) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    state = load_state()
    if state.get("generator_version") != VERSION:
        raise RuntimeError("generator version changed; start a new artifact directory")
    seen = {r["canonical_key"] for r in load_records()}
    start = int(state["next_candidate_id"])
    encoded_now = 0
    with STRUCTURAL.open("a") as out:
        for candidate_id in range(start, start + args.count):
            spec = proposal(candidate_id)
            state["proposals"] += 1
            if not spec["A"] or not spec["B"] or len(spec["A"]) + len(spec["B"]) > 32:
                continue
            if is_translated_equal(spec):
                state["traps"] += 1
                continue
            key = canonical_key(spec)
            if key in seen:
                state["duplicates"] += 1
                continue
            HX, HZ = build_bb(spec["l"], spec["m"], spec["A"], spec["B"])
            k = exact_k(HX, HZ)
            if k <= 0:
                continue
            if k % 2:
                raise RuntimeError(f"periodic abelian BB produced odd k for c{candidate_id}")
            n = int(HX.shape[1])
            weight = len(spec["A"]) + len(spec["B"])
            threshold = automatic_k_threshold(n, weight)
            components, component_sizes = component_profile(HX, HZ)
            record = {
                **spec,
                "canonical_key": key,
                "n": n,
                "k": k,
                "weight": weight,
                "weight_class": weight_class(weight),
                "rate": round(k / n, 8),
                "components": components,
                "component_sizes": component_sizes,
                "indecomposable": components == 1,
                "automatic_k_threshold": threshold,
                "automatic_high_rate_gap": threshold is not None and k >= threshold,
            }
            out.write(json.dumps(record, sort_keys=True) + "\n")
            out.flush()
            seen.add(key)
            encoded_now += 1
            state["encoded"] += 1
            if args.verbose:
                print(f"c{candidate_id} [[{n},{k},?]] w={weight} {spec['proposal_kernel']}")
            state["next_candidate_id"] = candidate_id + 1
            if candidate_id % 100 == 0:
                save_state(state)
    state["next_candidate_id"] = start + args.count
    save_state(state)
    print(f"census proposals={args.count} encoded={encoded_now} total_encoded={state['encoded']}")
    print(f"ledger={STRUCTURAL}")


def selection_score(record: dict) -> float:
    if not record.get("indecomposable", True):
        return -1_000_000_000 + record["k"]
    automatic = 1.0 if record["automatic_high_rate_gap"] else 0.0
    target = record["automatic_k_threshold"] or max(2, record["k"])
    threshold_ratio = record["k"] / target
    return 1_000_000 * automatic + 10_000 * threshold_ratio + 1_000 * record["rate"] - record["n"] / 1000


def command_select(args: argparse.Namespace) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    records = load_records()
    if not records:
        raise RuntimeError("run census first")
    buckets: dict[str, list[dict]] = defaultdict(list)
    packaged_ids = {
        int(path.name[1:8])
        for path in (ARTIFACTS / "candidates").glob("c???????-*.json")
        if len(path.name) >= 8 and path.name[1:8].isdigit()
    }
    for record in records:
        if "components" not in record:
            HX, HZ = build_bb(record["l"], record["m"], record["A"], record["B"])
            components, component_sizes = component_profile(HX, HZ)
            record = {**record, "components": components,
                      "component_sizes": component_sizes,
                      "indecomposable": components == 1}
        if not record["indecomposable"] and not args.include_disconnected:
            continue
        if args.only_automatic and not record["automatic_high_rate_gap"]:
            continue
        if args.weight_class and record["weight_class"] not in args.weight_class:
            continue
        if record["proposal_kernel"] in args.exclude_kernel:
            continue
        if min(int(record["l"]), int(record["m"])) < args.min_dimension:
            continue
        if int(record["candidate_id"]) in packaged_ids and not args.include_packaged:
            continue
        buckets[record["weight_class"]].append(record)
    for bucket in buckets.values():
        bucket.sort(key=selection_score, reverse=True)

    chosen: list[dict] = []
    positions = defaultdict(int)
    order = ["weight-6", "weight-8", "weight-4", "any-weight"]
    while len(chosen) < args.limit and any(positions[name] < len(buckets[name]) for name in order):
        for name in order:
            pos = positions[name]
            if pos < len(buckets[name]) and len(chosen) < args.limit:
                chosen.append(buckets[name][pos])
                positions[name] += 1
    payload = {
        "generator_version": VERSION,
        "selection_size": len(chosen),
        "records": chosen,
    }
    path = ARTIFACTS / f"selection-{len(list(ARTIFACTS.glob('selection-*.json'))) + 1:03d}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"wrote {len(chosen)} candidates to {path}")
    for r in chosen:
        print(f"c{r['candidate_id']} [[{r['n']},{r['k']},?]] w={r['weight']} "
              f"auto={r['automatic_high_rate_gap']} {r['proposal_kernel']}")


def load_selection(path: str) -> list[dict]:
    selected = json.loads(Path(path).read_text())["records"]
    if not isinstance(selected, list):
        raise ValueError("selection records must be a list")
    return selected


def selected_records(path: str, candidate_ids: list[int]) -> list[dict]:
    records = load_selection(path)
    if not candidate_ids:
        return records
    wanted = set(candidate_ids)
    found = [record for record in records if int(record["candidate_id"]) in wanted]
    missing = wanted - {int(record["candidate_id"]) for record in found}
    if missing:
        raise ValueError(f"candidate IDs absent from selection: {sorted(missing)}")
    return found


def candidate_stem(record: dict, label: str, seed: int) -> str:
    return (f"c{int(record['candidate_id']):07d}-{record['canonical_key'][:10]}-"
            f"{label}-s{seed}")


def build_record(record: dict) -> tuple[np.ndarray, np.ndarray]:
    HX, HZ = build_bb(record["l"], record["m"], record["A"], record["B"])
    if not verify_css(HX, HZ):
        raise RuntimeError(f"CSS failure rebuilding c{record['candidate_id']}")
    if exact_k(HX, HZ) != record["k"]:
        raise RuntimeError(f"k drift rebuilding c{record['candidate_id']}")
    return HX, HZ


def construction_text(record: dict) -> str:
    return (f"Periodic rectangular-torus bivariate bicycle on Z_{record['l']} x Z_{record['m']}: "
            f"A={record['A']}, B={record['B']}; local continuous campaign candidate "
            f"c{record['candidate_id']} ({record['proposal_kernel']}).")


def saved_submission(record: dict, HX: np.ndarray, HZ: np.ndarray, trials: int,
                     seed: int, label: str) -> tuple[dict, Path]:
    candidate_dir = ARTIFACTS / "candidates"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    stem = candidate_stem(record, label, seed)
    path = candidate_dir / f"{stem}.json"
    if path.exists():
        raise FileExistsError(f"refusing to overwrite saved witness: {path}")
    notes = (f"Local-only continuous autoresearch; not submitted. spec="
             f"{json.dumps({k: record[k] for k in ('candidate_id','canonical_key','l','m','A','B','lane','proposal_kernel')}, sort_keys=True)}; "
             f"Python witness trials={trials}, seed={seed}.")
    doc = make_submission(
        HX, HZ,
        name=f"local periodic BB c{record['candidate_id']}",
        construction=construction_text(record),
        authors=["local-autoresearch"],
        family="bivariate-bicycle",
        references=[],
        notes=notes,
        confidence="upper_bound",
        trials=trials,
        seed=seed,
    )
    doc["name"] = f"[[{doc['n']},{doc['k']},{doc['distance']['d']}]] local periodic BB c{record['candidate_id']}"
    errors = save_submission(doc, str(path))
    if errors or not path.exists():
        raise RuntimeError(f"hard save/schema failure for {path}: {errors}")
    json.loads(path.read_text())
    return doc, path


def command_package(args: argparse.Namespace) -> None:
    for record in selected_records(args.selection, args.candidate_id):
        HX, HZ = build_record(record)
        seed = stable_seed("package", record["candidate_id"], args.trials) % (2**31)
        doc, path = saved_submission(record, HX, HZ, args.trials, seed,
                                     f"python{args.trials}")
        print(f"saved {path.name}: [[{doc['n']},{doc['k']},{doc['distance']['d']}]]")


def validate_fast_witness(HX: np.ndarray, HZ: np.ndarray, side: str,
                          support: list[int], weight: int) -> None:
    n = HX.shape[1]
    vector = np.zeros(n, dtype=np.int8)
    vector[support] = 1
    own, opposite = (HX, HZ) if side == "X" else (HZ, HX)
    if (side not in ("X", "Z") or int(vector.sum()) != weight
            or not commutes(vector, opposite) or in_rowspace(vector, own)):
        raise RuntimeError(f"accelerated witness failed trusted Python checks: {side} w={weight}")


def command_confirm(args: argparse.Namespace) -> None:
    if gf2_fast is None:
        raise RuntimeError("gf2_fast unavailable; run `env UV_CACHE_DIR=.uv-cache make fast`")
    for record in selected_records(args.selection, args.candidate_id):
        HX, HZ = build_record(record)
        seed = stable_seed("confirm", args.rung, record["candidate_id"],
                           args.python_trials, args.fast_trials) % (2**31)
        doc, base_path = saved_submission(record, HX, HZ, args.python_trials, seed,
                                          f"{args.rung}-python{args.python_trials}")
        weight, side, support = gf2_fast.distance_rand_witness(
            HX, HZ, trials=args.fast_trials, seed=seed + 17,
            pair_depth=args.pair_depth, threads=args.threads)
        evidence = {
            "candidate_id": record["candidate_id"],
            "canonical_key": record["canonical_key"],
            "rung": args.rung,
            "trials": args.fast_trials,
            "seed": seed + 17,
            "pair_depth": args.pair_depth,
            "threads": args.threads,
            "weight": int(weight),
            "side": str(side),
            "support": [int(q) for q in support],
        }
        evidence_path = base_path.with_name(base_path.stem + f"-fast{args.fast_trials}.evidence.json")
        if evidence_path.exists():
            raise FileExistsError(f"refusing to overwrite fast evidence: {evidence_path}")
        evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
        validate_fast_witness(HX, HZ, str(side), evidence["support"], int(weight))

        fast_doc = copy.deepcopy(doc)
        side_doc = fast_doc["distance"][str(side)]
        if int(weight) <= int(side_doc["value"]):
            side_doc["value"] = int(weight)
            side_doc["witness"] = evidence["support"]
        fast_doc["distance"]["d"] = min(int(fast_doc["distance"]["X"]["value"]),
                                           int(fast_doc["distance"]["Z"]["value"]))
        fast_doc["name"] = (f"[[{fast_doc['n']},{fast_doc['k']},{fast_doc['distance']['d']}]] "
                            f"local periodic BB c{record['candidate_id']}")
        fast_doc["provenance"]["notes"] += (
            f" Accelerated rung={args.rung}, trials={args.fast_trials}, seed={seed + 17}, "
            f"pair_depth={args.pair_depth}, side={side}, witnessed_weight={weight}; "
            f"raw evidence={evidence_path.name}.")
        fast_path = base_path.with_name(base_path.stem + f"-fast{args.fast_trials}.json")
        if fast_path.exists():
            raise FileExistsError(f"refusing to overwrite saved fast candidate: {fast_path}")
        errors = save_submission(fast_doc, str(fast_path))
        if errors or not fast_path.exists():
            raise RuntimeError(f"hard save/schema failure for {fast_path}: {errors}")
        print(f"saved {fast_path.name}: [[{fast_doc['n']},{fast_doc['k']},{fast_doc['distance']['d']}]]")


def command_validate(args: argparse.Namespace) -> None:
    from validate_candidate import validate_candidate

    paths = sorted(Path().glob(args.glob))
    if not paths:
        raise RuntimeError(f"no candidate files matched {args.glob!r}")
    for path in paths:
        if path.name.endswith(".evidence.json") or path.name.endswith(".verdict.json"):
            continue
        if args.candidate_id:
            path_id = int(path.name[1:8]) if path.name.startswith("c") and path.name[1:8].isdigit() else None
            if path_id not in set(args.candidate_id):
                continue
        verdict_path = path.with_name(path.stem + ".verdict.json")
        if verdict_path.exists():
            if args.skip_existing:
                continue
            raise FileExistsError(f"refusing to overwrite validator verdict: {verdict_path}")
        doc = json.loads(path.read_text())
        seed = stable_seed("validate", path.name) % (2**31)
        verdict = validate_candidate(doc, seed=seed)
        verdict_path.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
        advancing = verdict.get("gates", {}).get("novelty", {}).get("board_advancing", False)
        print(f"{path.name}: passed={verdict['passed']} advancing={advancing} "
              f"labels={verdict['labels']}")


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)

    census = sub.add_parser("census", help="distance-free structural proposals")
    census.add_argument("--count", type=int, required=True)
    census.add_argument("--verbose", action="store_true")
    census.set_defaults(func=command_census)

    select = sub.add_parser("select", help="write a diverse promotion batch")
    select.add_argument("--limit", type=int, default=48)
    select.add_argument("--include-disconnected", action="store_true")
    select.add_argument("--only-automatic", action="store_true")
    select.add_argument("--weight-class", action="append", default=[])
    select.add_argument("--exclude-kernel", action="append", default=[])
    select.add_argument("--min-dimension", type=int, default=2)
    select.add_argument("--include-packaged", action="store_true")
    select.set_defaults(func=command_select)

    package = sub.add_parser("package", help="persist initial Python witnesses")
    package.add_argument("--selection", required=True)
    package.add_argument("--candidate-id", action="append", type=int, default=[])
    package.add_argument("--trials", type=int, default=2000)
    package.set_defaults(func=command_package)

    confirm = sub.add_parser("confirm", help="persist a Python + accelerated rung")
    confirm.add_argument("--selection", required=True)
    confirm.add_argument("--candidate-id", action="append", type=int, default=[])
    confirm.add_argument("--rung", required=True)
    confirm.add_argument("--python-trials", type=int, default=8000)
    confirm.add_argument("--fast-trials", type=int, required=True)
    confirm.add_argument("--pair-depth", type=int, default=16)
    confirm.add_argument("--threads", type=int, default=8)
    confirm.set_defaults(func=command_confirm)

    validate = sub.add_parser("validate", help="save full trusted validator verdicts")
    validate.add_argument("--glob", required=True)
    validate.add_argument("--candidate-id", action="append", type=int, default=[])
    validate.add_argument("--skip-existing", action="store_true")
    validate.set_defaults(func=command_validate)
    return ap


def main() -> None:
    args = parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
