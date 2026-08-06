#!/usr/bin/env python3
"""Build a distance-free structural census for the first planar campaign."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
for path in (ROOT / "research" / "kit", ROOT / "research" / "local2d"):
    sys.path.insert(0, str(path))

from boundary_engine import build_planar, reduce_weights  # noqa: E402
from css import compute_k, verify_css  # noqa: E402
from planar import grid_coordinates  # noqa: E402


SUPPORTS = {
    "aspect-ratio-192": {
        "S_f": [(0, 0), (0, 1), (2, 0)],
        "S_g": [(0, 1), (1, 0), (2, 1)],
    },
}


def nonempty(H: np.ndarray) -> np.ndarray:
    """Drop empty generators, which the submission schema rejects."""
    return H[np.asarray(H.sum(axis=1)).reshape(-1) > 0]


def max_weight(HX: np.ndarray, HZ: np.ndarray) -> int:
    return max(int(HX.sum(axis=1).max(initial=0)),
               int(HZ.sum(axis=1).max(initial=0)))


def interaction_radius(HX: np.ndarray, HZ: np.ndarray,
                       coordinates: list[list[float]]) -> float:
    def diameter(row: np.ndarray) -> float:
        support = np.flatnonzero(row)
        if len(support) < 2:
            return 0.0
        points = np.asarray([coordinates[int(q)] for q in support], dtype=float)
        delta = points[:, None, :] - points[None, :, :]
        return float(np.sqrt((delta * delta).sum(axis=2)).max())

    return max((diameter(row) for row in np.vstack([HX, HZ])), default=0.0)


def main() -> None:
    rows: list[dict[str, object]] = []
    for support_name, support in SUPPORTS.items():
        Sf, Sg = support["S_f"], support["S_g"]
        # Reflected support extent is four, so both dimensions honor extent+3.
        for Lx in range(7, 15):
            for Ly in range(7, 17):
                HX, HZ, info = build_planar(Lx, Ly, Sf, Sg)
                HX = nonempty(reduce_weights(HX))
                HZ = nonempty(reduce_weights(HZ))
                if not verify_css(HX, HZ):
                    raise RuntimeError(f"CSS failure for {support_name} {Lx}x{Ly}")
                kept = info.get("kept_qubits")
                coords = grid_coordinates(Lx, Ly, kept=kept)
                rows.append({
                    "support": support_name,
                    "S_f": Sf,
                    "S_g": Sg,
                    "Lx": Lx,
                    "Ly": Ly,
                    "n": int(HX.shape[1]),
                    "k": int(compute_k(HX, HZ)),
                    "w": max_weight(HX, HZ),
                    "radius": round(interaction_radius(HX, HZ, coords), 8),
                    "removed_qubits": int(info.get("n_removed_qubits", 0)),
                    "x_rows": int(HX.shape[0]),
                    "z_rows": int(HZ.shape[0]),
                })

    output = Path(__file__).with_name("census.json")
    output.write_text(json.dumps(rows, indent=2) + "\n")
    viable = [r for r in rows if r["k"] == 12 and r["w"] <= 8
              and r["radius"] <= 7.0]
    print(f"wrote {len(rows)} structural builds to {output}")
    print(f"stable-k local candidates: {len(viable)}")
    for row in sorted(viable, key=lambda r: (r["n"], r["w"], r["Lx"], r["Ly"]))[:30]:
        print(row)


if __name__ == "__main__":
    main()
