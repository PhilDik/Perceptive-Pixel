"""Independent geometric checks for the illustrated staggered pyramid array.

Run: python example/check_geometry.py
Requires NumPy. Writes example/geometry-check.json only after all checks pass.
This checks ideal geometry, not an optical field of view or a manufactured sensor.
"""
from __future__ import annotations

from itertools import combinations
import json
import math
from pathlib import Path

import numpy as np

from model import (
    BASE_SIDE_MM,
    FACE_INDICES,
    HEIGHT_MM,
    NORMALS,
    PITCH_MM,
    pixel_centers_mm,
    pyramid_vertices_mm,
)


TOL = 1e-9
ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def separated_by_sat(first, second):
    """Separating-axis theorem, using edge normals from both triangles."""
    for polygon in (first, second):
        for index in range(3):
            edge = polygon[(index + 1) % 3] - polygon[index]
            axis = np.array([-edge[1], edge[0]]) / np.linalg.norm(edge)
            left, right = first @ axis, second @ axis
            gap = max(right.min() - left.max(), left.min() - right.max())
            if gap > TOL:
                return True
    return False


def point_segment_distance(point, start, end):
    edge = end - start
    fraction = np.clip(np.dot(point - start, edge) / np.dot(edge, edge), 0.0, 1.0)
    return float(np.linalg.norm(point - (start + fraction * edge)))


def triangle_distance(first, second):
    """Exact boundary distance for two disjoint convex triangles in 2-D."""
    return min(
        point_segment_distance(point, polygon[index], polygon[(index + 1) % 3])
        for points, polygon in ((first, second), (second, first))
        for point in points
        for index in range(3)
    )


def angle_differences_degrees(angles, reference):
    return np.abs((angles - reference + 180.0) % 360.0 - 180.0)


def main():
    centers = pixel_centers_mm()
    vertices = pyramid_vertices_mm()
    require(centers.shape == (16, 3), "Expected the illustrated 4 by 4 array")
    require(vertices.shape == (4, 3), "Expected a triangular-base pyramid")
    require(np.allclose(vertices[:3, 2], 0.0, atol=TOL, rtol=0), "Base is not planar at z=0")
    require(np.allclose(vertices[3, :2], vertices[:3, :2].mean(axis=0), atol=TOL, rtol=0),
            "Apex must be directly above the base centroid")
    require(abs(vertices[3, 2] - HEIGHT_MM) < TOL, "Apex height mismatch")

    base_lengths = np.linalg.norm(np.roll(vertices[:3], -1, axis=0) - vertices[:3], axis=1)
    require(np.allclose(base_lengths, BASE_SIDE_MM, atol=TOL, rtol=0), "Base is not equilateral")
    face_results = []
    measured_normals = []
    for facet, indices in enumerate(FACE_INDICES):
        face = vertices[list(indices)]
        base_length = float(np.linalg.norm(face[1] - face[0]))
        equal_sides = np.linalg.norm(face[:2] - face[2], axis=1)
        require(abs(equal_sides[0] - equal_sides[1]) < TOL, f"Facet {facet} is not isosceles")
        cross = np.cross(face[1] - face[0], face[2] - face[0])
        area = float(np.linalg.norm(cross) / 2)
        normal = cross / np.linalg.norm(cross)
        require(np.dot(normal, face.mean(axis=0) - vertices.mean(axis=0)) > 0,
                f"Facet {facet} normal is not outward")
        require(np.allclose(normal, NORMALS[facet], atol=TOL, rtol=0),
                f"Facet {facet} geometric normal differs from the numerical channel normal")
        tilt = math.degrees(math.atan2(np.linalg.norm(normal[:2]), normal[2]))
        require(abs(tilt - 30.0) < TOL, f"Facet {facet} tilt is not 30 degrees")
        azimuth = math.degrees(math.atan2(normal[1], normal[0])) % 360.0
        measured_normals.append(normal)
        face_results.append({
            "facet": facet, "vertices": list(indices), "base_length_mm": base_length,
            "equal_side_lengths_mm": equal_sides.tolist(), "area_mm2": area,
            "normal_from_cross_product": normal.tolist(),
            "tilt_from_vertical_deg": tilt, "azimuth_deg": azimuth,
        })
    measured_normals = np.array(measured_normals)

    grid = centers.reshape(4, 4, 3)
    vertical_steps = np.diff(grid[:, :, 1], axis=0)
    column_shifts = np.diff(grid[0, :, 1])
    column_spacing = np.diff(grid[0, :, 0])
    require(np.allclose(vertical_steps, PITCH_MM, atol=TOL, rtol=0), "Vertical pitch mismatch")
    require(np.allclose(np.diff(grid[:, :, 0], axis=0), 0.0, atol=TOL, rtol=0),
            "Columns are not vertical")
    require(np.allclose(np.abs(column_shifts), PITCH_MM / 2, atol=TOL, rtol=0),
            "Columns lack a vertical half-pitch shift")
    require(np.allclose(np.diff(grid[:, :, 1], axis=1), column_shifts[None, :], atol=TOL, rtol=0),
            "Vertical column shifts are not uniform across the array")
    require(np.allclose(column_spacing, math.sqrt(3) * PITCH_MM / 2, atol=TOL, rtol=0),
            "Triangular-lattice horizontal column spacing mismatch")
    require(np.allclose(np.diff(grid[:, :, 0], axis=1), column_spacing[None, :], atol=TOL, rtol=0),
            "Horizontal column spacing is not uniform across the array")

    vertex_angles = np.degrees(np.arctan2(vertices[:3, 1], vertices[:3, 0])) % 360.0
    require(np.allclose(vertex_angles, [90, 210, 330], atol=TOL, rtol=0),
            "Base vertices must keep the author-confirmed upright orientation")

    triangles = centers[:, None, :2] + vertices[None, :3, :2]
    pair_results = []
    for first, second in combinations(range(len(triangles)), 2):
        require(separated_by_sat(triangles[first], triangles[second]),
                f"Base footprints {first} and {second} intersect or touch")
        pair_results.append((triangle_distance(triangles[first], triangles[second]), first, second))
    minimum_gap, closest_first, closest_second = min(pair_results)
    require(len(pair_results) == 120, "Not all footprint pairs were checked")
    predicted_gap = PITCH_MM - math.sqrt(3) * BASE_SIDE_MM / 2
    require(abs(minimum_gap - predicted_gap) < TOL,
            "Measured minimum footprint gap differs from pitch minus triangular altitude")

    # Check only pixels with all six nearest neighbors present in this finite array.
    # For this author-confirmed orientation, face-normal projections align with
    # three nearest centers. Vertices align with the other three. Normals do not
    # bisect nearest-neighbor directions in this vertical-column layout.
    neighbor_results = []
    vertex_neighbor_results = []
    interior_ids = []
    for pixel_id, center in enumerate(centers):
        offsets = centers - center
        distances = np.linalg.norm(offsets[:, :2], axis=1)
        nearest = np.flatnonzero(np.isclose(distances, PITCH_MM, atol=TOL, rtol=0))
        if len(nearest) != 6:
            continue
        interior_ids.append(pixel_id)
        directions = offsets[nearest, :2] / distances[nearest, None]
        angles = np.degrees(np.arctan2(directions[:, 1], directions[:, 0])) % 360
        require(np.allclose(np.sort(angles), [30, 90, 150, 210, 270, 330], atol=TOL, rtol=0),
                f"Pixel {pixel_id} nearest neighbors do not have the expected vertical-stagger directions")
        normal_neighbor_ids = []
        for facet, normal in enumerate(measured_normals):
            azimuth = math.degrees(math.atan2(normal[1], normal[0])) % 360
            differences = angle_differences_degrees(angles, azimuth)
            aligned = int(np.argmin(differences))
            require(np.allclose(np.sort(differences), [0, 60, 60, 120, 120, 180], atol=TOL, rtol=0),
                    f"Pixel {pixel_id}, facet {facet} does not align with a nearest-neighbor direction")
            normal_xy = normal[:2] / np.linalg.norm(normal[:2])
            require(np.allclose(directions[aligned], normal_xy, atol=TOL, rtol=0),
                    f"Pixel {pixel_id}, facet {facet} normal does not point toward its aligned neighbor")
            normal_neighbor_ids.append(int(nearest[aligned]))
            neighbor_results.append({
                "pixel_id": pixel_id, "facet": facet, "normal_azimuth_deg": azimuth,
                "aligned_neighbor_id": int(nearest[aligned]),
                "angular_separation_from_aligned_neighbor_deg": float(differences[aligned]),
                "sorted_angular_separations_from_all_six_neighbors_deg": np.sort(differences).tolist(),
            })
        vertex_neighbor_ids = []
        for vertex, azimuth in enumerate(vertex_angles):
            differences = angle_differences_degrees(angles, azimuth)
            aligned = int(np.argmin(differences))
            require(np.allclose(np.sort(differences), [0, 60, 60, 120, 120, 180], atol=TOL, rtol=0),
                    f"Pixel {pixel_id}, vertex {vertex} does not align with a nearest-neighbor direction")
            vertex_direction = vertices[vertex, :2] / np.linalg.norm(vertices[vertex, :2])
            require(np.allclose(directions[aligned], vertex_direction, atol=TOL, rtol=0),
                    f"Pixel {pixel_id}, vertex {vertex} does not point toward its aligned neighbor")
            vertex_neighbor_ids.append(int(nearest[aligned]))
            vertex_neighbor_results.append({
                "pixel_id": pixel_id, "vertex": vertex, "vertex_azimuth_deg": float(azimuth),
                "aligned_neighbor_id": int(nearest[aligned]),
                "angular_separation_from_aligned_neighbor_deg": float(differences[aligned]),
            })
        require(set(normal_neighbor_ids).isdisjoint(vertex_neighbor_ids)
                and set(normal_neighbor_ids + vertex_neighbor_ids) == set(nearest.tolist()),
                f"Pixel {pixel_id} normals and vertices do not align with alternating nearest neighbors")
    require(len(interior_ids) == 4 and len(neighbor_results) == 12,
            "Expected four fully surrounded pixels and twelve direction checks")
    require(len(vertex_neighbor_results) == 12, "Expected twelve vertex-direction checks")

    # A ray starting on a face has z>=0. Before it can reach any other footprint,
    # it must travel at least minimum_gap horizontally. If it already lies above
    # HEIGHT_MM then, it cannot hit any equal-height neighboring pyramid.
    horizontal_per_vertical = np.linalg.norm(measured_normals[:, :2], axis=1) / measured_normals[:, 2]
    require(np.all(measured_normals[:, 2] > 0), "Normal rays must point upward")
    maximum_travel_to_apex_height = float(HEIGHT_MM * horizontal_per_vertical.max())
    require(maximum_travel_to_apex_height < minimum_gap,
            "The sufficient all-normal-rays clearance bound is not satisfied")
    minimum_ray_height_at_gap = float(minimum_gap / horizontal_per_vertical.max())
    base_area = float(abs(np.linalg.det(np.stack((vertices[1, :2] - vertices[0, :2],
                                                vertices[2, :2] - vertices[0, :2])))) / 2)
    lattice_area = float(abs(np.linalg.det(np.stack((centers[1, :2] - centers[0, :2],
                                                   centers[4, :2] - centers[0, :2])))))
    result = {
        "status": "passed",
        "scope": "Independent numerical checks of the finite 4 by 4 ideal geometric array; not an optical or fabrication validation.",
        "length_unit": "mm", "pixel_count": len(centers),
        "pitch_mm": PITCH_MM, "base_side_mm": BASE_SIDE_MM, "height_mm": HEIGHT_MM,
        "faces": face_results,
        "column_vertical_shifts_mm": column_shifts.tolist(),
        "horizontal_column_spacing_mm": column_spacing.tolist(),
        "vertical_pitch_mm": PITCH_MM,
        "base_vertex_azimuths_deg": vertex_angles.tolist(),
        "base_area_mm2": base_area, "lattice_cell_area_mm2": lattice_area,
        "infinite_lattice_base_fill_fraction": base_area / lattice_area,
        "sat_disjoint_base_pairs_checked": len(pair_results),
        "minimum_footprint_gap_mm": minimum_gap,
        "one_closest_footprint_pair": [closest_first, closest_second],
        "pitch_minus_triangular_altitude_mm": predicted_gap,
        "interior_pixel_ids_with_six_nearest_neighbors": interior_ids,
        "neighbor_direction_checks": neighbor_results,
        "vertex_neighbor_direction_checks": vertex_neighbor_results,
        "direction_check_meaning": "Horizontal face-normal projections and vertex directions align with alternating nearest-neighbor centers. The normal projections do not bisect nearest-neighbor directions.",
        "normal_ray_clearance": {
            "sufficient_bound_satisfied": True,
            "maximum_horizontal_travel_before_clearing_apex_height_mm": maximum_travel_to_apex_height,
            "available_minimum_footprint_gap_mm": minimum_gap,
            "minimum_ray_height_after_traversing_gap_from_z_zero_mm": minimum_ray_height_at_gap,
            "vertical_margin_above_other_apices_mm": minimum_ray_height_at_gap - HEIGHT_MM,
            "meaning": "Every straight outward face-normal ray clears all other ideal equal-height pyramids, including rays starting at base edges.",
            "exclusions": ["Arbitrary incidence angles or finite angular acceptance", "Added supports or coverings", "Unequal heights or manufacturing tolerances", "Diffraction, scattering, and optical crosstalk"],
        },
        "optical_claim_limit": "These geometric checks establish neither minimum refraction nor an optimal or improved field of view. Column translation alone does not establish either optical claim.",
    }
    output = Path(__file__).resolve().parent / "geometry-check.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"], "pairs_checked": len(pair_results),
        "minimum_gap_mm": minimum_gap, "isosceles_faces_checked": len(face_results),
        "neighbor_direction_checks": len(neighbor_results),
        "vertex_direction_checks": len(vertex_neighbor_results),
        "normal_ray_horizontal_travel_mm": maximum_travel_to_apex_height,
        "output": "example/geometry-check.json",
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
