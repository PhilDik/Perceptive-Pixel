"""Finite-area geometric reception: upright triangles versus square diamonds.

Run: python geometry_benchmark.py
Only NumPy is required. No measured sensor parameters or refractive optics.
API: geometry(shape, tilt_deg); RayModel(shape, tilt_deg, layout, n=16).
The facet-normal tilt is measured from +z. Lengths and areas are mm and mm^2.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import json
import math
from pathlib import Path
import time

import numpy as np


ROOT = Path(__file__).resolve().parent
PITCH = 10.0
SX = math.sqrt(3) * PITCH / 2
CELL_AREA = SX * PITCH
Q = math.sqrt(CELL_AREA)
BASE_AREA = math.sqrt(3) * 9.0**2 / 4
CHEOPS_TILT = math.degrees(math.atan(14 / 11))
TILTS = [30.0, 45.0, CHEOPS_TILT]
THETA = np.array([0.0, 30.0, 45.0, 60.0, 75.0, 80.0, 85.0])
PHI = np.arange(0.0, 360.0, 5.0)
LATTICES = {
    "aligned": [[SX, 0.0], [0.0, PITCH]],
    "aligned_square": [[Q, 0.0], [0.0, Q]],
    "shifted_square": [[Q, Q / 2], [0.0, Q]],
    "vertical": [[SX, PITCH / 2], [0.0, PITCH]],
}
DEFAULT_LAYOUTS = ["aligned_square", "shifted_square", "vertical"]


def geometry(shape, tilt_deg):
    """Return vertices, triangular side faces, outward unit normals, face areas."""
    if shape == "triangle":
        radius = 9.0 / math.sqrt(3)
        azimuths = [90, 210, 330]
        inradius = radius / 2
        indices = [[2, 0, 3], [0, 1, 3], [1, 2, 3]]
        expected_azimuths = [30, 150, 270]
    elif shape == "diamond":
        side = math.sqrt(BASE_AREA)
        radius = side / math.sqrt(2)
        inradius = side / 2
        azimuths = [0, 90, 180, 270]
        indices = [[0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]]
        expected_azimuths = [45, 135, 225, 315]
    else:
        raise ValueError(f"Unknown shape: {shape}")
    angles = np.radians(azimuths)
    height = inradius * math.tan(math.radians(tilt_deg))
    vertices = np.vstack([
        np.column_stack([radius * np.cos(angles), radius * np.sin(angles), np.zeros(len(angles))]),
        [0, 0, height],
    ])
    faces = vertices[np.array(indices)]
    cross = np.cross(faces[:, 1] - faces[:, 0], faces[:, 2] - faces[:, 0])
    lengths = np.linalg.norm(cross, axis=1)
    normals, areas = cross / lengths[:, None], lengths / 2
    measured_azimuths = np.degrees(np.arctan2(normals[:, 1], normals[:, 0])) % 360
    assert np.allclose(measured_azimuths, expected_azimuths, atol=1e-10, rtol=0)
    assert np.allclose(normals[:, 2], math.cos(math.radians(tilt_deg)), atol=1e-12, rtol=0)
    assert abs(np.sum(areas * normals[:, 2]) - BASE_AREA) < 1e-10
    assert np.allclose(np.sum(areas[:, None] * normals[:, :2], axis=0), 0, atol=1e-10, rtol=0)
    assert np.allclose(np.linalg.norm(faces[:, 0] - faces[:, 2], axis=1),
                       np.linalg.norm(faces[:, 1] - faces[:, 2], axis=1), atol=1e-10, rtol=0)
    return vertices, faces, normals, areas


def sample_faces(faces, n):
    """Exactly n^2 equal-area subtriangle centroids on each side face."""
    uv = []
    for i in range(n):
        for j in range(n - i):
            uv.append([(i + 1 / 3) / n, (j + 1 / 3) / n])
            if i + j <= n - 2:
                uv.append([(i + 2 / 3) / n, (j + 2 / 3) / n])
    uv = np.asarray(uv)
    assert len(uv) == n * n
    return (faces[:, 0, None, :] + uv[None, :, :1] * (faces[:, 1] - faces[:, 0])[:, None, :]
            + uv[None, :, 1:] * (faces[:, 2] - faces[:, 0])[:, None, :])


def lattice_centers(layout, radius, include_origin=False):
    basis = np.asarray(LATTICES[layout])
    assert abs(abs(np.linalg.det(basis)) - CELL_AREA) < 1e-10
    limit = math.ceil(radius / np.linalg.svd(basis)[1].min()) + 2
    out = []
    for i in range(-limit, limit + 1):
        for j in range(-limit, limit + 1):
            c = i * basis[0] + j * basis[1]
            if np.linalg.norm(c) <= radius + 1e-9 and (include_origin or (i, j) != (0, 0)):
                out.append([c[0], c[1], 0.0])
    return np.asarray(out)


@lru_cache(maxsize=None)
def minimum_clearance(shape, layout):
    vertices, _, _, _ = geometry(shape, 30)
    polygon = vertices[:-1, :2]
    centers = lattice_centers(layout, 30)
    edges = np.roll(polygon, -1, axis=0) - polygon
    axes = np.column_stack([-edges[:, 1], edges[:, 0]])
    axes /= np.linalg.norm(axes, axis=1)[:, None]
    minimum = math.inf
    for center in centers[:, :2]:
        other = polygon + center
        p, q = polygon @ axes.T, other @ axes.T
        separations = np.maximum(q.min(0) - p.max(0), p.min(0) - q.max(0))
        if separations.max() <= 1e-10:
            raise ValueError(f"Intersecting/touching bases: {shape}, {layout}; neighbor center {center.tolist()} mm")
        for aa, bb in ((polygon, other), (other, polygon)):
            for point in aa:
                for a, b in zip(bb, np.roll(bb, -1, axis=0)):
                    edge = b - a
                    fraction = np.clip((point - a) @ edge / (edge @ edge), 0, 1)
                    minimum = min(minimum, float(np.linalg.norm(point - a - fraction * edge)))
    return minimum


def direction(theta, phi):
    theta, phi = np.radians([theta, phi])
    return np.array([math.sin(theta) * math.cos(phi), math.sin(theta) * math.sin(phi), math.cos(theta)])


class RayModel:
    """Periodic opaque identical convex pyramids with cosine-sensitive side faces."""
    def __init__(self, shape, tilt_deg, layout, n=16, theta_max=85, radius_extra=0):
        self.shape, self.tilt_deg, self.layout, self.n = shape, tilt_deg, layout, n
        self.vertices, self.faces, self.normals, self.areas = geometry(shape, tilt_deg)
        self.height = float(self.vertices[-1, 2])
        self.base_radius = float(np.linalg.norm(self.vertices[0, :2]))
        self.samples = sample_faces(self.faces, n)
        # Before reaching any apex height, a ray has horizontal travel <=h*tan(theta_max).
        self.radius = 2 * self.base_radius + self.height * math.tan(math.radians(theta_max)) + radius_extra
        self.centers = lattice_centers(layout, self.radius)
        self.clearance = minimum_clearance(shape, layout)
        self.planes = np.vstack([self.normals, [0, 0, -1]])
        offsets = np.r_[self.normals[:, 2] * self.height, 0]
        relative = self.samples[:, :, None, :] - self.centers[None, None, :, :]
        self.numerator = offsets - relative @ self.planes.T

    def visibility(self, v, indices=None):
        """Neighbor visibility per sampled face point; own-face cosine is separate."""
        den = self.planes @ v
        plus, minus, parallel = den > 1e-11, den < -1e-11, abs(den) <= 1e-11
        cosine = self.normals @ v
        selected = self.numerator if indices is None else self.numerator[:, indices]
        visible = np.ones(selected.shape[:2], dtype=bool)
        for face in np.flatnonzero(cosine > 1e-12):
            numerator = selected[face]
            t_enter = (np.max(numerator[..., minus] / den[minus], axis=-1)
                       if minus.any() else np.full(numerator.shape[:2], -np.inf))
            t_exit = (np.min(numerator[..., plus] / den[plus], axis=-1)
                      if plus.any() else np.full(numerator.shape[:2], np.inf))
            hit = t_exit >= np.maximum(t_enter, 1e-9)
            if parallel.any():
                hit &= np.all(numerator[..., parallel] >= -1e-10, axis=-1)
            visible[face] = ~np.any(hit, axis=1)
        return visible

    def response(self, v):
        return self.areas * np.maximum(self.normals @ v, 0) * self.visibility(v).mean(axis=1)


def independent_triangle_visibility(model, v, indices):
    """Independent Moller-Trumbore intersections against neighbors' side triangles."""
    origins = model.samples[:, indices].reshape(-1, 3)
    triangles = (model.faces[None, :, :, :] + model.centers[:, None, None, :]).reshape(-1, 3, 3)
    e1, e2 = triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    h = np.cross(np.broadcast_to(v, e2.shape), e2)
    determinant = np.sum(e1 * h, axis=1)
    nonparallel = abs(determinant) > 1e-11
    inv = np.divide(1.0, determinant, out=np.zeros_like(determinant), where=nonparallel)
    s = origins[:, None, :] - triangles[None, :, 0, :]
    u = np.sum(s * h[None, :, :], axis=2) * inv
    q = np.cross(s, e1[None, :, :])
    w = np.sum(q * v, axis=2) * inv
    t = np.sum(q * e2[None, :, :], axis=2) * inv
    hits = nonparallel & (u >= -1e-10) & (w >= -1e-10) & (u + w <= 1 + 1e-10) & (t > 1e-9)
    return (~np.any(hits, axis=1)).reshape(len(model.faces), len(indices))


def separated_extrema_indices(values, minimize=True, count=2):
    order = np.argsort(values if minimize else -values)
    chosen = []
    for index in order:
        if all(min(abs(PHI[index] - PHI[other]), 360 - abs(PHI[index] - PHI[other])) >= 20 for other in chosen):
            chosen.append(int(index))
            if len(chosen) == count:
                break
    return chosen


def calculate(shape, tilt_deg, layout, n=16, refined_n=32):
    started = time.perf_counter()
    model = RayModel(shape, tilt_deg, layout, n=n)
    refined = RayModel(shape, tilt_deg, layout, n=refined_n)
    channels = np.empty((len(THETA), len(PHI), len(model.faces)))
    isolated = np.empty((len(THETA), len(PHI)))
    for ti, theta in enumerate(THETA):
        for pi, phi in enumerate(PHI):
            v = direction(theta, phi)
            channels[ti, pi] = model.response(v)
            isolated[ti, pi] = np.sum(model.areas * np.maximum(model.normals @ v, 0))
    total = channels.sum(axis=2)
    normalized = total / BASE_AREA
    assert np.allclose(normalized[0], 1, atol=1e-12, rtol=0)
    positive_sector = THETA <= 90 - tilt_deg - 1e-9
    isolated_error = float(np.max(abs(isolated[positive_sector] - BASE_AREA * np.cos(np.radians(THETA[positive_sector]))[:, None])))
    assert isolated_error < 1e-10
    bound_excess = float(np.max(total - CELL_AREA * np.cos(np.radians(THETA))[:, None]))
    # Sampling near sharp shadow boundaries is approximate; retain and report any excess.
    assert bound_excess < .02 * BASE_AREA, "Flux bound exceeded beyond coarse quadrature allowance"
    selected_angles = {}
    maximum_refinement_change = 0.0
    for ti, theta in enumerate(THETA):
        values = normalized[ti]
        chosen = set(separated_extrema_indices(values, True) + separated_extrema_indices(values, False))
        # Flat responses need one convergence check; otherwise refine both extrema neighborhoods.
        if values.max() - values.min() < 1e-12:
            candidates = [0.0]
        else:
            candidates = sorted({float((PHI[index] + offset) % 360) for index in chosen for offset in (-2.5, 0.0, 2.5)})
        refined_values, changes = [], []
        for phi in candidates:
            v = direction(theta, phi)
            fine = float(np.sum(refined.response(v)) / BASE_AREA)
            coarse = float(np.sum(model.response(v)) / BASE_AREA)
            refined_values.append(fine)
            changes.append(abs(fine - coarse))
        maximum_refinement_change = max(maximum_refinement_change, max(changes))
        minimum_index, maximum_index = int(np.argmin(refined_values)), int(np.argmax(refined_values))
        selected_angles[str(int(theta))] = {
            "mean_coarse": float(values.mean()),
            "worst_coarse": float(values.min()),
            "best_coarse": float(values.max()),
            "mean_shadow_loss_coarse": float(np.mean(1 - total[ti] / isolated[ti])),
            "worst_refined_sample": refined_values[minimum_index],
            "worst_refined_phi_deg": candidates[minimum_index],
            "best_refined_sample": refined_values[maximum_index],
            "best_refined_phi_deg": candidates[maximum_index],
            "maximum_coarse_to_refined_difference_at_selected_phis": max(changes),
            "refined_phi_deg": candidates,
            "refined_response": refined_values,
        }

    indices = sorted(set([0, n * n // 4, n * n // 2, n * n - 1]))
    independent_rays = 0
    for theta, phi in [(30, 17), (60, 37), (75, 83), (80, 193), (85, 277), (85, 342)]:
        v = direction(theta, phi)
        active = model.normals @ v > 1e-12
        expected = model.visibility(v, indices=indices)
        independent = independent_triangle_visibility(model, v, indices)
        assert np.array_equal(expected[active], independent[active]), "Independent ray intersection mismatch"
        independent_rays += int(active.sum()) * len(indices)
    expanded = RayModel(shape, tilt_deg, layout, n=4, radius_extra=PITCH)
    base_small = RayModel(shape, tilt_deg, layout, n=4)
    radius_error = max(float(np.max(abs(expanded.response(direction(85, phi)) - base_small.response(direction(85, phi)))))
                       for phi in [7, 47, 107, 197, 257, 317])
    assert radius_error < 1e-10
    summary = {
        "shape": shape, "layout": layout, "tilt_from_vertical_deg": tilt_deg,
        "height_mm": model.height, "side_face_count": len(model.faces),
        "total_side_face_area_mm2": float(model.areas.sum()),
        "base_area_mm2": BASE_AREA, "cell_area_mm2": CELL_AREA,
        "clearance_mm": model.clearance, "neighbors_checked": len(model.centers),
        "ray_neighbor_radius_mm": model.radius,
        "samples_per_face": n * n, "refined_samples_per_face": refined_n * refined_n,
        "maximum_coarse_to_refined_difference_at_selected_phis": maximum_refinement_change,
        "energy_bound_excess_mm2": bound_excess,
        "isolated_projected_area_identity_error_mm2": isolated_error,
        "independent_active_rays_checked": independent_rays,
        "expanded_neighbor_radius_response_difference_mm2": radius_error,
        "selected_angles": selected_angles,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }
    print(json.dumps({key: summary[key] for key in ["shape", "layout", "tilt_from_vertical_deg", "clearance_mm", "maximum_coarse_to_refined_difference_at_selected_phis", "elapsed_seconds"]}), flush=True)
    return {"summary": summary, "channels_mm2": channels.tolist(), "isolated_mm2": isolated.tolist()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--subdivisions", type=int, default=32)
    parser.add_argument("--refined-subdivisions", type=int, default=64)
    parser.add_argument("--shapes", nargs="+", default=["triangle", "diamond"])
    parser.add_argument("--layouts", nargs="+", default=DEFAULT_LAYOUTS)
    parser.add_argument("--tilts", nargs="+", type=float, default=TILTS)
    parser.add_argument("--resume", action="store_true", help="Reuse completed same-resolution configurations from the output JSON")
    args = parser.parse_args()
    started = time.perf_counter()
    output = ROOT / "geometry-results.json"
    previous = json.loads(output.read_text(encoding="utf-8")).get("results", {}) if args.resume and output.exists() else {}
    results = {
        "status": "running", "date": "2026-09-27",
        "model": "Periodic opaque convex pyramids; finite-area cosine-sensitive side faces; collimated illumination; whole-pixel sum of independent channels",
        "parameters": {"base_area_mm2": BASE_AREA, "cell_area_mm2": CELL_AREA, "base_fill_fraction": BASE_AREA / CELL_AREA,
                       "triangle_side_mm": 9.0, "diamond_square_side_mm": math.sqrt(BASE_AREA),
                       "diamond_diagonal_mm": math.sqrt(2 * BASE_AREA),
                       "theta_deg": THETA.tolist(), "phi_deg": PHI.tolist(), "lattice_basis_mm": LATTICES},
        "normalization": "Total effective receiving area divided by common frontal projected area (base area). All facets receive independently; displayed totals sum them.",
        "fairness": "For the same tilt, the shapes have identical base area, total side-face area, frontal projected area, and center density; height, facet count, and channel angular signatures differ.",
        "layout_comparison": "aligned_square and shifted_square have the same two column/row pitches Q and differ only by a vertical column half-shift. The author's vertical lattice has the same cell area but a different aspect ratio (SX by PITCH).",
        "refinement_scope": f"Mean is from {args.subdivisions}^2 samples per face and azimuth step 5 degrees. Extrema are refined at {args.refined_subdivisions}^2 samples per face around two separated coarse minimum and maximum candidates, at local step 2.5 degrees. Reported extrema are sampled estimates, not certified continuous extrema.",
        "limitations": ["Pure ray geometry; no refraction, coatings, diffraction, interreflection, or scattering",
                        "No electronic crosstalk, TX leakage model, noise, calibration, or scene inversion in this file",
                        "Uniformly sensitive ideal surfaces; no support structure or cover sheet",
                        "Directions beyond 85 degrees are not sampled; no universal field-of-view or optimality result",
                        "Three versus four channels is not matched in per-channel electronics cost or noise",
                        "The original aligned rectangular control (SX by PITCH, no shift) is invalid for side-9 triangles because its bases overlap; it is not used for optical ranking"],
        "rejected_controls": [{"shape": "triangle", "layout": "aligned", "lattice_basis_mm": LATTICES["aligned"],
                               "status": "invalid_overlapping_bases", "applies_to_all_tilts": True,
                               "reason": "Horizontal center separation SX=8.660254 mm is smaller than the base width 9 mm; same-orientation bases intersect. Removing the shift at these exact pitches is not a valid manufactured control."}],
        "results": {},
    }
    for shape in args.shapes:
        for tilt in args.tilts:
            for layout in args.layouts:
                key = f"{shape}-{layout}-{tilt:.8f}"
                try:
                    prior = previous.get(key, {})
                    prior_summary = prior.get("summary", {})
                    if (prior_summary.get("samples_per_face") == args.subdivisions**2
                            and prior_summary.get("refined_samples_per_face") == args.refined_subdivisions**2):
                        results["results"][key] = prior
                        print(json.dumps({"key": key, "status": "reused_completed_same_resolution"}), flush=True)
                    else:
                        results["results"][key] = calculate(shape, tilt, layout, args.subdivisions, args.refined_subdivisions)
                except ValueError as error:
                    if "Intersecting/touching bases" not in str(error):
                        raise
                    results["results"][key] = {"status": "invalid_overlapping_bases", "reason": str(error),
                                               "shape": shape, "layout": layout, "tilt_from_vertical_deg": tilt}
                    print(json.dumps({"key": key, **results["results"][key]}), flush=True)
                output.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    results["status"] = "completed"
    results["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    output.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "configurations": len(results["results"]), "elapsed_seconds": results["elapsed_seconds"], "output": str(output)}), flush=True)


if __name__ == "__main__":
    main()
