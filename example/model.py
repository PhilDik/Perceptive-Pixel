"""Noise-free explanatory forward/inverse calculation; not a sensor simulation.

Run: python example/model.py
Requires only Python and the already installed NumPy. Writes example.json and EXAMPLE.md beside this script.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import time

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
POSES_MM = (-20.0, 0.0, 20.0)
TARGET_MM = (20.0, 0.0, 150.0)
TRUE_SCALE = 0.6
PITCH_MM = 10.0
PATCH_AREA_M2 = 1e-6
BASE_SIDE_MM = 0.9 * PITCH_MM
TILT_DEG = 30.0
AZIMUTHS_DEG = (30.0, 150.0, 270.0)
INRADIUS_MM = BASE_SIDE_MM / (2 * math.sqrt(3))
HEIGHT_MM = INRADIUS_MM * math.tan(math.radians(TILT_DEG))
FACET_AREA_MM2 = BASE_SIDE_MM * math.hypot(INRADIUS_MM, HEIGHT_MM) / 2
FACET_AREA_M2 = FACET_AREA_MM2 * 1e-6


def pixel_centers_mm(rows=4, columns=4):
    """Upright pyramids: every odd column shifts vertically by half a pitch."""
    pixels = np.array([
        [PITCH_MM * math.sqrt(3) / 2 * col,
         PITCH_MM * (row + 0.5 * (col % 2)), 0.0]
        for row in range(rows) for col in range(columns)
    ])
    return pixels - pixels.mean(axis=0)


def pyramid_vertices_mm():
    """Three base vertices CCW, followed by the centered apex."""
    angles = np.deg2rad([90.0, 210.0, 330.0])
    radius = BASE_SIDE_MM / math.sqrt(3)
    return np.vstack((np.column_stack((radius * np.cos(angles),
                                      radius * np.sin(angles), np.zeros(3))),
                      [0.0, 0.0, HEIGHT_MM]))


# R0 faces +30 degrees, R1 +150, R2 +270 in the physical xy plane.
FACE_INDICES = ((2, 0, 3), (0, 1, 3), (1, 2, 3))


def geometry():
    pixels = pixel_centers_mm() * 1e-3
    even = np.array([(row + col) % 2 == 0 for row in range(4) for col in range(4)])
    phi = np.deg2rad(AZIMUTHS_DEG)
    tilt = math.radians(TILT_DEG)
    normals = np.column_stack((
        math.sin(tilt) * np.cos(phi),
        math.sin(tilt) * np.sin(phi),
        np.full(3, math.cos(tilt)),
    ))
    acquisitions = []
    channel_info = []
    for pose in POSES_MM:
        moved = pixels + np.array([pose * 1e-3, 0.0, 0.0])
        for slot, emask in (("A", even), ("B", ~even)):
            receiver_ids = np.flatnonzero(~emask)
            acquisitions.append((moved[emask], moved[~emask]))
            for pid in receiver_ids:
                for facet in range(3):
                    channel_info.append({
                        "pose_x_mm": pose, "slot": slot,
                        "pixel_id": int(pid), "pixel_row": int(pid // 4),
                        "pixel_column": int(pid % 4), "facet": facet,
                        "receiver_position_mm": (moved[pid] * 1e3).tolist(),
                    })
    return normals, acquisitions, channel_info


NORMALS, ACQUISITIONS, CHANNEL_INFO = geometry()


def model(targets_mm):
    """Return radiometric coefficients with one unit shared reflectance/gain.

    One arbitrary total source-power unit is split equally among 8 emitters.
    The target normal is fixed at (0,0,-1); array rotations are zero.
    """
    targets = np.atleast_2d(np.asarray(targets_mm, dtype=float)) * 1e-3
    blocks = []
    for emitters, receivers in ACQUISITIONS:
        de = targets[:, None, :] - emitters[None, :, :]
        de2 = np.sum(de * de, axis=2)
        # For a source facing +z and a patch facing -z, both cosines are z/d.
        illumination = np.sum(de[:, :, 2] ** 2 / de2 ** 2, axis=1) / (len(emitters) * np.pi)
        dr = targets[:, None, :] - receivers[None, :, :]
        dr2 = np.sum(dr * dr, axis=2)
        length = np.sqrt(dr2)
        unit = dr / length[:, :, None]
        cosine_facet = np.maximum(np.einsum("mrd,kd->mrk", unit, NORMALS), 0.0)
        cosine_target_exit = dr[:, :, 2] / length
        signal = (illumination[:, None, None] / np.pi * PATCH_AREA_M2 * FACET_AREA_M2
                  * cosine_target_exit[:, :, None] * cosine_facet / dr2[:, :, None])
        blocks.append(signal.reshape(len(targets), -1))
    return np.concatenate(blocks, axis=1)


def main():
    started = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)
    truth = model([TARGET_MM])[0]
    normalization = float(truth.max())
    observed = TRUE_SCALE * truth / normalization
    xs = np.arange(-20.0, 60.0 + 1.0, 1.0)
    zs = np.arange(100.0, 200.0 + 1.0, 1.0)
    xx, zz = np.meshgrid(xs, zs)
    candidates = np.column_stack((xx.ravel(), np.zeros(xx.size), zz.ravel()))
    predictions = model(candidates) / normalization
    fitted_scale = np.maximum((predictions @ observed) / np.einsum("ij,ij->i", predictions, predictions), 0.0)
    residual = predictions * fitted_scale[:, None] - observed[None, :]
    objective = np.einsum("ij,ij->i", residual, residual) / (observed @ observed)
    best_idx = int(np.argmin(objective))
    objectives_2d = objective.reshape(len(zs), len(xs))
    scales_2d = fitted_scale.reshape(len(zs), len(xs))
    at_true_x = int(np.flatnonzero(xs == TARGET_MM[0])[0])
    depth_curve = []
    for zi, z in enumerate(zs):
        xi = int(np.argmin(objectives_2d[zi]))
        depth_curve.append({
            "z_mm": float(z), "fixed_x_mm": TARGET_MM[0],
            "objective_at_fixed_x": float(objectives_2d[zi, at_true_x]),
            "objective_profiled_x": float(objectives_2d[zi, xi]),
            "profiled_x_mm": float(xs[xi]), "profiled_scale": float(scales_2d[zi, xi]),
            "single_monostatic_channel_profiled_objective": 0.0,
            "single_monostatic_channel_scale_over_true": float((z / TARGET_MM[2]) ** 4),
        })

    channels = []
    for metadata, value in zip(CHANNEL_INFO, observed):
        channels.append({**metadata, "normalized_signal": float(value)})
    example_pixel = []
    for pose in POSES_MM:
        selected = [c for c in channels if c["pose_x_mm"] == pose and c["slot"] == "B" and c["pixel_id"] == 5]
        values = np.array([c["normalized_signal"] for c in selected])
        example_pixel.append({
            "pose_x_mm": pose, "slot": "B", "pixel_id": 5,
            "pixel_local_position_mm": pixel_centers_mm()[5].tolist(),
            "signals": values.tolist(), "facet_fractions": (values / values.sum()).tolist(),
        })
    nontruth = np.flatnonzero(np.any(candidates != np.array(TARGET_MM), axis=1))
    second_idx = int(nontruth[np.argmin(objective[nontruth])])
    summary = {
        "kind": "Illustrative, noise-free geometric/radiometric calculation; no measured data",
        "target_mm": list(TARGET_MM), "best_grid_target_mm": candidates[best_idx].tolist(),
        "true_shared_scale": TRUE_SCALE, "best_shared_scale": float(fitted_scale[best_idx]),
        "best_normalized_squared_residual": float(objective[best_idx]),
        "best_other_grid_target_mm": candidates[second_idx].tolist(),
        "best_other_grid_normalized_squared_residual": float(objective[second_idx]),
        "channels": len(CHANNEL_INFO), "grid_candidates": len(candidates),
        "grid_x_mm": [float(xs.min()), float(xs.max()), 1.0],
        "grid_z_mm": [float(zs.min()), float(zs.max()), 1.0],
    }
    data = {
        "summary": summary,
        "parameters": {
            "array_rows": 4, "array_columns": 4, "pitch_mm": PITCH_MM,
            "layout": "vertical column stagger; all base triangles point upward (+y)",
            "odd_column_vertical_shift_mm": PITCH_MM / 2,
            "column_spacing_mm": PITCH_MM * math.sqrt(3) / 2,
            "vertical_pitch_mm": PITCH_MM,
            "pixel_centers_mm": pixel_centers_mm().tolist(),
            "pyramid_base_side_mm": BASE_SIDE_MM,
            "pyramid_height_mm": HEIGHT_MM,
            "pyramid_vertices_local_mm": pyramid_vertices_mm().tolist(),
            "facet_vertex_indices": FACE_INDICES,
            "periodic_base_coverage_fraction": 0.5 * (BASE_SIDE_MM / PITCH_MM) ** 2,
            "horizontal_normal_to_nearest_neighbor_angle_deg": 0.0,
            "minimum_base_clearance_mm": PITCH_MM - math.sqrt(3) * BASE_SIDE_MM / 2,
            "whole_array_translation_x_mm": list(POSES_MM), "whole_array_rotation_deg": [0, 0, 0],
            "facet_tilt_deg": TILT_DEG, "facet_azimuth_deg": list(AZIMUTHS_DEG),
            "facet_normals": NORMALS.tolist(), "facet_area_mm2": FACET_AREA_M2 * 1e6,
            "target_area_mm2": PATCH_AREA_M2 * 1e6, "target_normal": [0, 0, -1],
            "total_source_power_arbitrary_units_per_slot": 1,
            "slot_A_emitters": "(row + column) even; other whole pixels receive on all 3 facets",
            "slot_B_emitters": "(row + column) odd; other whole pixels receive on all 3 facets",
            "pixel_indices": "zero-based row/column; pixel_id = 4*row + column",
            "normalization": "All signals divided by maximum coefficient at true geometry and scale=1",
        },
        "selected_pixel": example_pixel, "depth_curve": depth_curve,
        "channels": channels,
        "limitations": [
            "One static isolated Lambertian patch; y, surface normal and area known.",
            "Candidate geometry and exact forward model generate and fit the same noiseless data.",
            "Known emitter power and channel calibration; one shared unknown reflectance/gain scale.",
            "No unknown per-channel gains, ambient, crosstalk, cover layer, occlusion or motion errors.",
            "Each small emitter, patch and facet is approximated by its center and normal.",
            "All receiver facets are treated as co-located at their pixel center.",
            "No proof of uniqueness outside the chosen grid or for a general scene.",
            "No range, resolution, precision, noise robustness, novelty or hardware feasibility established.",
        ],
    }
    (OUT / "example.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    table = "\n".join(
        f"| {r['pose_x_mm']:+.0f} | " + " | ".join(f"{v:.6f}" for v in r["facet_fractions"]) + " |"
        for r in example_pixel
    )
    depth_table = "\n".join(
        f"| {r['z_mm']:.0f} | {r['profiled_x_mm']:.0f} | {r['objective_profiled_x']:.6g} |"
        for r in depth_curve if r["z_mm"] in (100, 125, 140, 149, 150, 151, 160, 175, 200)
    )
    report = f"""# Reproducible example: one patch, one moving array

**Status:** a small explanatory calculation added for this revision. Every dimension,
normal and optical parameter below is an analyst-selected assumption. This is not a
fabricated pixel, measurement, validated device simulation or demonstration of sensing performance.

## Defined scene and schedule

A 4 × 4 addressed array uses vertically staggered columns of upright pyramids.
Before subtracting the centroid, c(r,j) = (5√3 j, 10[r + (j mod 2)/2], 0) mm,
for row r and column j from 0 to 3. Consecutive columns are 8.660254 mm apart;
odd columns shift upward by 5 mm. Pitch along each column is 10 mm. All base
triangles point toward +y; none are reversed. The half-pitch offset is an illustrative
choice implementing the author's vertical-stagger requirement, not an optimized value.
The complete array translates to x = −20, 0, +20 mm with no
rotation. One static 1 mm² Lambertian patch is centered at (20, 0, 150) mm; its known
normal is (0, 0, −1), and y is fixed at 0 in reconstruction.

At each pose, slot A uses even-parity whole pixels as emitters and the other eight
whole pixels as receivers. Slot B swaps their roles. Each receiving pixel reads all
three facets separately and simultaneously during illumination. This schedule assumes
independently addressable purpose-built pixels; it does not establish a switchable
semiconductor implementation. No prompt reflection is collected after a frame ends.

Each emitting pixel is represented by an assumed equivalent +z Lambertian source.
Emission from individual tilted facets and its absolute throughput are not modeled.
All pyramids share one orientation. Each has a 9 mm equilateral base and an apex
1.5 mm above its centroid; its three congruent side faces are isosceles triangles.
Each ideal receiving face has area 13.5 mm². Its outward normal is tilted 30° from +z
at azimuth 30°, 150° or 270°. The base vertices have azimuths 90°, 210°, 330°.
The physical geometry is shared by the figures and this calculation. The radiometric
model approximates all three facets as co-located at the base center (z = 0).
It assumes sufficient optical separation that direct light does
not enter the reported signal. One arbitrary total emission-power unit is divided
equally among eight emitters. All channel gains are fixed and calibrated to unity.
These dimensions illustrate geometry; 10 mm pitch is not a display-density claim.

In the interior, six nearest centers have azimuths 30°, 90°, 150°, 210°, 270°, 330°.
Vertex directions (90°, 210°, 330°) point toward three of them; horizontal normal
projections (30°, 150°, 270°) point toward the other three. The earlier statement that
normal projections pass between nearest neighbors does not apply to this layout.
Base footprints do not overlap: minimum clearance is 10 − 9√3/2 = 2.205771 mm.
In the periodic limit bases cover 40.5% of the carrier plane; the remaining space
is open. An upward ray can clear a neighboring pyramid even when its plan projection
points at that neighbor. Broad useful angular coverage is the design objective;
an optimum and reduced refraction have not been established. Materials, coatings,
finite active areas, supports and other ray directions require separate evaluation.

Elements are treated by their center, area and normal. A 1 mm patch and the
9 mm carrier bases are smaller than the 100–200 mm candidate distances, but the
co-location and finite-area approximation errors are not quantified here. No
near-field wave effect or full finite-area integration is modeled. A cover layer,
occlusion and the physical facet supports are omitted.

## Forward model

For source j, patch t and receiving facet (p,k), let d_e and d_r denote source-to-patch
and patch-to-receiver distance. The receiver direction u points **from receiver to patch**.
Emission, incident, exiting and facet cosines use the facing surface normals:

```text
E_t = Σ_j (P_j / π) · cos_emit,j · cos_inc,j / d_e,j²
s_p,k = ρ · (E_t / π) · A_target · cos_exit,p · A_facet · max(n_k · u_p, 0) / d_r,p²
```

Lengths and areas are converted to SI units inside the calculation. Numerical signals
are then normalized by one common constant; they are not predictions of detector watts,
photocurrents or signal-to-noise ratio. A shared scale ρ = 0.6 generates the observations.
Reconstruction treats the product of reflectance and common gain as unknown and profiles
it as a nonnegative amplitude. No separate per-channel gain is fitted.

## What changes as the array moves

For pixel (row 1, column 1), local position (−4.330127, −2.5, 0) mm, slot B is its receiving
slot. Dividing each facet's signal by the sum of all three removes common illumination,
reflectance and distance factors **within that one pixel and exposure**:

| Whole-array x translation, mm | Facet 0 fraction | Facet 1 fraction | Facet 2 fraction |
|---:|---:|---:|---:|
{table}

The fractions change because the direction from that moving pixel to the fixed patch
changes. They encode angular weighting in this restricted one-patch scene. Arbitrary
scenes mix contributions from many directions, so these ratios do not directly label a
scene point or supply a depth for each display pixel.

## Tiny inverse calculation

The script produces 144 values: 3 array poses × 2 slots × 8 receiving pixels × 3 facets.
It checks {len(candidates):,} candidates: x from −20 to +60 mm, z from 100 to 200 mm,
both in 1 mm steps. For each candidate, f is its full 144-channel prediction for unit
shared scale, and y is the synthetic observation:

```text
a = max(0, dot(f,y) / dot(f,f))
J(x,z) = ||a f(x,z) − y||² / ||y||²
J_depth(z) = min_x J(x,z)
```

The grid minimum is ({candidates[best_idx,0]:.0f}, 0, {candidates[best_idx,2]:.0f}) mm,
with fitted scale {fitted_scale[best_idx]:.12g} and J = {objective[best_idx]:.6g}.
This recovery is expected because the same noiseless model generates and fits the data.
The best other grid candidate is ({candidates[second_idx,0]:.0f}, 0, {candidates[second_idx,2]:.0f}) mm,
with J = {objective[second_idx]:.6g}; a nonzero residual does not establish distinguishability
in a real instrument. The 1 mm grid step is not an achieved spatial resolution.

| Candidate z, mm | Best grid x, mm | J after profiling x and shared amplitude |
|---:|---:|---:|
{depth_table}

As a deliberately underdetermined reference, a **single** coaxial, co-located planar
source/receiver and an on-axis patch provide one intensity s ∝ ρ/z⁴. With unknown shared
amplitude, every positive z fits that one value exactly by choosing amplitude proportional
to z⁴. This explains why one intensity alone is ambiguous; it is not a fair performance
comparison with the 144-channel acquisition or a ranking of facet counts. Angular diversity,
array aperture and registered poses act together in the example; their separate contributions
have not been isolated by a matched-budget experiment.

## Reproduce and inspect

Run from the repository root using Python with NumPy already installed:

```powershell
python example/model.py
```

The script writes [example.json](example.json) with all 144 normalized signals, facet
normals, selected-pixel fractions and 101 depth-objective samples. The corresponding
source is [model.py](model.py).

**Limits:** one isolated, static, known-orientation patch; known y and area; exact pose
and channel calibration; no noise, ambient, crosstalk, occlusion or device optics. The
calculation neither reconstructs a hand nor validates hardware, sensing range, accuracy,
uniqueness for a general scene, novelty, or an advantage over another sensor.
"""
    (OUT / "EXAMPLE.md").write_text(report, encoding="utf-8")
    # Analytic identities are useful implementation checks for this particular model.
    assert len(CHANNEL_INFO) == 144
    assert np.allclose(candidates[best_idx], TARGET_MM)
    assert objective[best_idx] < 1e-24
    assert abs(fitted_scale[best_idx] - TRUE_SCALE) < 1e-12
    assert np.all(observed > 0)
    for row in example_pixel:
        direction = np.array(TARGET_MM) - pixel_centers_mm()[5] - [row["pose_x_mm"], 0, 0]
        # Sum of the three positive cosines is 3*cos(tilt)*u_z.
        horizontal = direction[0] * math.cos(math.pi/6) + direction[1] * math.sin(math.pi/6)
        expected_facet0 = 1 / 3 + horizontal / (3 * math.sqrt(3) * direction[2])
        assert abs(row["facet_fractions"][0] - expected_facet0) < 1e-12
    print(json.dumps({**summary, "wall_seconds": round(time.perf_counter() - started, 3)}, indent=2))


if __name__ == "__main__":
    main()
