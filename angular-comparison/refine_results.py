"""Check spatial/angular convergence and symmetries; keep raw fine azimuth curves."""
import json
import time
import numpy as np
import compare_layouts as c

started = time.perf_counter()
base = json.loads((c.ROOT/'results-n32.json').read_text(encoding='utf-8'))
coarse = json.loads((c.ROOT/'results-n8.json').read_text(encoding='utf-8'))
out = {'theta_deg': [80, 85], 'phi_deg': list(range(360)), 'results': {}, 'checks': {}}
for key in c.DESIGNS:
    entry = {}
    for n in [32, 64]:
        model = c.RayModel(c.DESIGNS[key], n)
        totals = np.array([[model.response(c.direction(t, p)).sum(-1).mean()/c.BASE_AREA for p in range(360)] for t in out['theta_deg']])
        entry[str(n)] = {'normalized_total': totals.tolist(), 'mean': totals.mean(1).tolist(), 'worst': totals.min(1).tolist(), 'worst_azimuth_deg': totals.argmin(1).tolist()}
    b = np.array(base['results'][key]['total_mm2'])/c.BASE_AREA
    a = np.array(coarse['results'][key]['total_mm2'])/c.BASE_AREA
    entry['n8_to_n32_max_absolute_response_change'] = float(abs(a-b).max())
    a, b = [np.array(entry[str(n)]['normalized_total']) for n in [32, 64]]
    entry['n32_to_n64_max_absolute_response_change'] = float(abs(a-b).max())
    out['results'][key] = entry
    print(key, 'refined', entry['64']['mean'], entry['64']['worst'], flush=True)
    (c.ROOT/'refinement.json').write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

# V+30 is H+0 rotated globally by +30: test the full curves, not just means.
h = np.array(base['results']['horizontal']['total_mm2'])
r = np.array(base['results']['rotated30']['total_mm2'])
rotation_error = float(abs(r-np.roll(h, 6, axis=1)).max())
assert rotation_error < 1e-9
out['checks']['rotation_equivalence_max_error_mm2'] = rotation_error

# Expand neighboring region independently of the original radius bound.
radius_error = 0.
for key in ['vertical', 'square', 'quarter']:
    a = c.RayModel(c.DESIGNS[key], 8)
    b = c.RayModel(c.DESIGNS[key], 8, radius_extra=20)
    for t, p in [(60, 17), (75, 39), (80, 113), (85, 0), (85, 191), (85, 273)]:
        v = c.direction(t, p)
        radius_error = max(radius_error, float(abs(a.response(v)-b.response(v)).max()))
assert radius_error < 1e-10
out['checks']['expanded_neighbor_radius_max_error_mm2'] = radius_error
out['checks']['diffuse_missing_85_90_upper_fraction_of_incident'] = float(np.cos(np.radians(85))**2)
out['elapsed_seconds'] = time.perf_counter()-started
(c.ROOT/'refinement.json').write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
