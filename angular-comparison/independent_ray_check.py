"""Independent triangle-ray reference for compare_layouts.py's convex-slab tracer.

Uses two-sided Moller-Trumbore intersections against all four pyramid faces.
Runs a bounded deterministic check, with extra emphasis on 75--85 degree rays.
No source models or comparison results are modified.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import time

import numpy as np

import compare_layouts as source


ROOT = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def independent_neighbors(design, own, radius):
    """Enumerate using inverse-basis coordinate bounds, independent of SVD bounds."""
    basis = np.asarray(design['basis'], dtype=float)
    inverse = np.linalg.inv(basis)
    coefficient_radii = radius * np.linalg.norm(inverse, axis=0)
    result = []
    for motif in np.asarray(design['motif'], dtype=float):
        coefficient_center = (own - motif) @ inverse
        lower = np.floor(coefficient_center - coefficient_radii).astype(int) - 1
        upper = np.ceil(coefficient_center + coefficient_radii).astype(int) + 1
        for first in range(lower[0], upper[0] + 1):
            for second in range(lower[1], upper[1] + 1):
                xy = np.array([first, second]) @ basis + motif - own
                distance = np.linalg.norm(xy)
                if 1e-8 < distance <= radius + 1e-8:
                    result.append([xy[0], xy[1], 0.0])
    return np.asarray(result)


def point_set(points):
    return {tuple(row) for row in np.round(points, 8)}


def triangles_at_centers(vertices, centers):
    # Closed tetrahedron; no backface culling. Different face order from source.
    indices = np.array([[0, 1, 2], [0, 1, 3], [1, 2, 3], [2, 0, 3]])
    return (vertices[indices][None, :, :, :] + centers[:, None, None, :]).reshape(-1, 3, 3)


def moller_trumbore_blocked(origins, direction, triangles):
    edge_one = triangles[:, 1] - triangles[:, 0]
    edge_two = triangles[:, 2] - triangles[:, 0]
    p_vector = np.cross(np.broadcast_to(direction, edge_two.shape), edge_two)
    determinant = np.einsum('ij,ij->i', edge_one, p_vector)
    nonparallel = np.abs(determinant) > 1e-12
    inverse = np.zeros_like(determinant)
    inverse[nonparallel] = 1.0 / determinant[nonparallel]
    translation = origins[:, None, :] - triangles[None, :, 0, :]
    coordinate_one = np.einsum('ijk,jk->ij', translation, p_vector) * inverse
    q_vector = np.cross(translation, edge_one[None, :, :])
    coordinate_two = np.einsum('ijk,k->ij', q_vector, direction) * inverse
    distance = np.einsum('ijk,jk->ij', q_vector, edge_two) * inverse
    hit = (nonparallel[None, :] & (coordinate_one >= -1e-10)
           & (coordinate_two >= -1e-10) & (coordinate_one + coordinate_two <= 1 + 1e-10)
           & (distance > 1e-9))
    return hit.any(axis=1)


def source_slab_masks(numerators, planes, direction):
    """Expose the source's slab rule per ray, avoiding aggregate-only comparisons."""
    denominator = planes @ direction
    positive = denominator > 1e-11
    negative = denominator < -1e-11
    parallel = np.abs(denominator) <= 1e-11
    shape = numerators.shape[:-1]
    enter = np.max(numerators[..., negative] / denominator[negative], axis=-1) if negative.any() else np.full(shape, -np.inf)
    leave = np.min(numerators[..., positive] / denominator[positive], axis=-1) if positive.any() else np.full(shape, np.inf)
    hit = leave >= np.maximum(enter, 1e-9)
    if parallel.any():
        hit &= np.all(numerators[..., parallel] >= -1e-10, axis=-1)
    return hit.any(axis=-1)


def directions_to_check():
    cases = [(theta, phi) for theta in (0, 30, 60, 75, 77.5, 80, 82.5, 85)
             for phi in range(0, 360, 15)]
    rng = np.random.default_rng(20260926)
    cases.extend(zip(rng.uniform(75, 85, 32).tolist(), rng.uniform(0, 360, 32).tolist()))
    return [(float(theta), float(phi), source.direction(theta, phi)) for theta, phi in cases]


def main():
    started = time.perf_counter()
    cases = directions_to_check()
    subdivisions = 4
    results = {}
    differences = []
    maximum_absolute_response_error = 0.0
    facet_sample_rays = 0
    active_ray_masks_compared = 0
    for name, design in source.DESIGNS.items():
        model = source.RayModel(design, subdivisions)
        vertices, faces, normals, areas = source.geometry(design['rotation'])
        expected_phi = np.radians(np.array([30, 150, 270]) + design['rotation'])
        expected_normals = np.column_stack((.5 * np.cos(expected_phi), .5 * np.sin(expected_phi),
                                           np.full(3, math.sqrt(3) / 2)))
        require(np.allclose(normals, expected_normals, atol=1e-12, rtol=0), name + ': normal mismatch')
        require(np.allclose(areas, 13.5, atol=1e-12, rtol=0), name + ': unequal facet areas')
        require(np.allclose(model.samples.mean(axis=1), faces.mean(axis=1), atol=1e-12, rtol=0),
                name + ': equal-area sample centroid mismatch')
        basis = np.asarray(design['basis'])
        motif = np.asarray(design['motif'])
        area_per_pixel = abs(np.linalg.det(basis)) / len(motif)
        require(abs(area_per_pixel - source.CELL_AREA) < 1e-10, name + ': unmatched pixel density')
        origins = model.samples.reshape(-1, 3)
        own_triangles = triangles_at_centers(vertices, np.zeros((1, 3)))
        references = []
        expanded_references = []
        neighbor_counts = []
        expanded_counts = []
        for index, own in enumerate(motif):
            centers = independent_neighbors(design, own, model.radius)
            actual = model.centers[index]
            require(point_set(centers) == point_set(actual), name + ': missing or extra source neighbors')
            require(len(point_set(actual)) == len(actual), name + ': duplicated neighbor centers')
            require(np.all(np.linalg.norm(actual, axis=1) > 1e-8), name + ': own pyramid was not excluded')
            for step in basis:
                periodic_centers = independent_neighbors(design, own + step, model.radius)
                require(point_set(periodic_centers) == point_set(centers), name + ': periodicity failure')
            expanded = independent_neighbors(design, own, model.radius + source.PITCH)
            references.append(triangles_at_centers(vertices, centers))
            expanded_references.append(triangles_at_centers(vertices, expanded))
            neighbor_counts.append(len(centers))
            expanded_counts.append(len(expanded))

        design_error = 0.0
        expanded_changes = 0
        self_intersections = 0
        individual_mask_mismatches = 0
        for theta, phi, ray in cases:
            cosine = np.maximum(normals @ ray, 0)
            self_hit = moller_trumbore_blocked(origins, ray, own_triangles).reshape(3, -1)
            self_intersections += int(self_hit[cosine > 1e-12].sum())
            expected = []
            for motif_index, (original, expanded) in enumerate(zip(references, expanded_references)):
                hit = moller_trumbore_blocked(origins, ray, original).reshape(3, -1)
                expanded_hit = moller_trumbore_blocked(origins, ray, expanded).reshape(3, -1)
                slab_hit = source_slab_masks(model.numerators[motif_index], model.planes, ray)
                individual_mask_mismatches += int(np.count_nonzero(hit[cosine > 1e-12] != slab_hit[cosine > 1e-12]))
                active_ray_masks_compared += int(np.count_nonzero(cosine > 1e-12)) * subdivisions ** 2
                expanded_changes += int(np.count_nonzero(hit[cosine > 1e-12] != expanded_hit[cosine > 1e-12]))
                expected.append(areas * cosine * np.mean(~hit, axis=1))
                facet_sample_rays += len(origins)
            expected = np.array(expected)
            actual = model.response(ray)
            error = float(np.max(np.abs(expected - actual)))
            design_error = max(design_error, error)
            if error > 1e-10:
                differences.append({'design': name, 'theta_deg': theta, 'phi_deg': phi,
                                    'maximum_channel_error_mm2': error,
                                    'triangle_reference_mm2': expected.tolist(), 'slab_source_mm2': actual.tolist()})
        maximum_absolute_response_error = max(maximum_absolute_response_error, design_error)
        require(self_intersections == 0, name + ': outward rays intersect their own pyramid')
        require(expanded_changes == 0, name + ': insufficient neighbor cutoff')
        require(individual_mask_mismatches == 0, name + ': triangle/slab individual ray masks differ')
        results[name] = {
            'pixel_area_mm2': area_per_pixel,
            'facet_areas_mm2': areas.tolist(),
            'normal_analytic_check': 'passed',
            'equal_area_sample_centroid_check': 'passed',
            'periodicity_and_unique_neighbor_check': 'passed',
            'neighbor_counts': neighbor_counts, 'expanded_neighbor_counts': expanded_counts,
            'neighbor_cutoff_expansion_mm': source.PITCH,
            'cutoff_expansion_changed_active_rays': expanded_changes,
            'active_self_intersections': self_intersections,
            'individual_active_ray_mask_mismatches': individual_mask_mismatches,
            'maximum_channel_response_difference_mm2': design_error,
        }
    result = {
        'status': 'passed' if not differences else 'failed',
        'reference_algorithm': 'Two-sided Moller-Trumbore intersections with the four triangular faces of every opaque neighbor',
        'source_algorithm': 'Convex solid intersection by four plane slabs',
        'subdivisions': subdivisions, 'samples_per_face': subdivisions ** 2,
        'directions_per_design': len(cases),
        'angular_coverage': '0, 30, 60, 75, 77.5, 80, 82.5, 85 degrees at 15 degree azimuth spacing, plus 32 seeded off-grid directions at 75--85 degrees',
        'facet_sample_rays_compared': facet_sample_rays,
        'individual_active_ray_masks_compared': active_ray_masks_compared,
        'maximum_channel_response_difference_mm2': maximum_absolute_response_error,
        'designs': results, 'differences': differences,
        'scope': 'Algorithm agreement and geometry consistency for these deterministic cases; not an error bound on angular or face-area integration and not validation of material optics.',
        'elapsed_seconds': round(time.perf_counter() - started, 3),
    }
    output = ROOT / 'independent-ray-check.json'
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('status', 'directions_per_design', 'facet_sample_rays_compared',
                                                'maximum_channel_response_difference_mm2', 'elapsed_seconds')}))
    require(not differences, f'{len(differences)} reference/source mismatches; see {output.name}')


if __name__ == '__main__':
    main()
