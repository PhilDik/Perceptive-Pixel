"""Independent quadrature audit; imports depth_benchmark without running main.

Writes only validation-depth.json. No inverse fits or Monte Carlo are repeated.
"""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
from pathlib import Path
import importlib.util
import hashlib
import json
import time
import numpy as np

OUT = Path(__file__).resolve().parent
SOURCE = OUT / 'depth_benchmark.py'
spec = importlib.util.spec_from_file_location('depth_benchmark_audit', SOURCE)
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def rel(a, b):
    return float(np.linalg.norm(a-b) / max(np.linalg.norm(b), 1e-300))


def main():
    started = time.perf_counter()
    result = {
        'status': 'running',
        'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'scope': '4 configurations at 45 degrees; truth-only central/grazing forward; no inverse rerun',
        'geometry_definition': {
            'base_area_mm2': float(model.BASE_AREA),
            'cell_area_mm2': float(model.CELL_AREA),
            'aligned_basis_mm': [float(np.sqrt(model.CELL_AREA))]*2,
            'shifted_definition': 'same square basis as aligned, half vertical step on alternate columns',
            'author_vertical_basis_mm': [float(10*np.sqrt(3)/2), 10.],
            'author_vertical_shift_mm': 5.,
            'warning': 'The former 8.660254 x 10 aligned triangular baseline is not used: its bases overlap.',
        },
        'review': {
            'fatal_code_error_found_by_static_review': False,
            'visible': 'Convex slab intersection is consistent. Ignoring endpoint-owner convex solids is valid only for outward-facing endpoint segments; kernel/exchange enforce positive cosines before visibility.',
            'kernel': 'Finite-facet average includes both cosines, mm^-2 to m^-2 factor, and other-pyramid visibility. Object patches remain point-position patches of fixed 1 mm^2 area and -z normal.',
            'exchange': 'Uses double facet average, receiving area/pi; nonnegative, energy and area-weighted reciprocity assertions retained.',
            'readvariance': '12/k subexposures with 2 electron RMS each -> variance (12/k)*4 per aggregated facet; total 48 electron^2 per receiving pixel per slot/band for both k.',
            'fit': 'Bounds/interpolation/index mapping consistent. Uses data-derived weighted least squares, not exact Poisson-Gaussian likelihood. expected_background argument is unused; raw observed counts still include background for weights.',
            'cautions': [
                'Data-derived weights can bias fits at low signal; this is a stated estimator limit, not quadrature validation.',
                'Information uses a pseudoinverse: near-zero singular values must not be interpreted as finite precision of an unidentifiable depth.',
                'Base footprints and unit-cell area are matched; physical finite-array outer shapes differ within the allocated common envelope.',
                'Only a conditional open-facet optical model is checked; real cover-stack leakage is not measured.',
            ],
        },
        'rows': [],
    }
    def save():
        result['elapsed_s'] = time.perf_counter()-started
        (OUT/'validation-depth.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    save()
    worst = None
    for shape in ['triangle', 'diamond']:
        for layout in ['aligned', 'vertical']:
            panel = model.Panel(shape, 45., layout)
            stamp = time.perf_counter()
            print(json.dumps({'start': panel.id}), flush=True)
            f4 = panel.exchange(n=4)
            f8 = panel.exchange(n=8)
            l4, l8 = panel.leakage(f4), panel.leakage(f8)
            area = np.tile(panel.area, 16)
            row = {
                'id': panel.id,
                'leakage_fraction_all_bands_n4': float(l4.sum()*3),
                'leakage_fraction_all_bands_n8': float(l8.sum()*3),
                'leakage_total_relative_change_n4_vs_n8': float(abs(l4.sum()-l8.sum())/l8.sum()),
                'leakage_vector_relative_l2_n4_vs_n8': rel(l4, l8),
                'exchange_matrix_relative_l2_n4_vs_n8': rel(f4, f8),
                'max_source_fraction_n4': float(f4.sum(axis=1).max()),
                'max_source_fraction_n8': float(f8.sum(axis=1).max()),
                'reciprocity_abs_error_n8_mm2': float(np.max(np.abs(area[:,None]*f8-area[None,:]*f8.T))),
                'read_variance_per_aggregated_channel': panel.read_variance,
                'read_variance_sum_per_pixel': panel.k*panel.read_variance,
                'truth_forward': {},
            }
            assert panel.k*panel.read_variance == 48
            for scene_name in ['central', 'grazing']:
                scene = model.SCENES[scene_name]
                points = np.c_[scene['xy'], scene['z']]
                g4, g8 = panel.forward(points,n=4), panel.forward(points,n=8)
                m4, m8 = g4@model.TRUE_RGB, g8@model.TRUE_RGB
                val = rel(m4,m8)
                row['truth_forward'][scene_name] = {
                    'operator_relative_l2_n4_vs_n8': rel(g4,g8),
                    'rgb_signal_relative_l2_n4_vs_n8': val,
                    'rgb_signal_total_relative_change_n4_vs_n8': float(abs(m4.sum()-m8.sum())/m8.sum()),
                    'per_surface_relative_l2_n4_vs_n8': [rel(g4[:,p],g8[:,p]) for p in range(2)],
                }
                if worst is None or val > worst[0]:
                    worst = (val, shape, layout, scene_name, g8)
            row['elapsed_s'] = time.perf_counter()-stamp
            result['rows'].append(row)
            save()
            print(json.dumps(row), flush=True)
    _, shape, layout, scene_name, g8 = worst
    panel = model.Panel(shape,45.,layout)
    scene = model.SCENES[scene_name]
    g16 = panel.forward(np.c_[scene['xy'],scene['z']],n=16)
    result['worst_forward_n16_check'] = {
        'id': panel.id, 'scene': scene_name,
        'operator_relative_l2_n8_vs_n16': rel(g8,g16),
        'rgb_signal_relative_l2_n8_vs_n16': rel(g8@model.TRUE_RGB,g16@model.TRUE_RGB),
        'per_surface_relative_l2_n8_vs_n16': [rel(g8[:,p],g16[:,p]) for p in range(2)],
    }
    result['status'] = 'complete'
    result['source_unchanged_during_validation'] = result['source_sha256'] == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    save()
    print(json.dumps({'complete': True, 'elapsed_s': result['elapsed_s'], 'worst_forward_n16_check': result['worst_forward_n16_check']}), flush=True)


if __name__ == '__main__':
    main()
