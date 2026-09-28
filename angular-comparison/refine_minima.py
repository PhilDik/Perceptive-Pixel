"""Local refinement near the six lowest separated dips of every 1-degree curve."""
import json
import numpy as np
import compare_layouts as c

ref = json.loads((c.ROOT/'refinement.json').read_text(encoding='utf-8'))
out = {'samples_per_face': 128**2, 'azimuth_step_deg': .25, 'search_half_width_deg': 2, 'note': 'Local refinement of sampled minima; not a proof of continuous global minimum.', 'results': {}}
for key in c.DESIGNS:
    model = c.RayModel(c.DESIGNS[key], 128)
    entry = {}
    for index, t in enumerate([80, 85]):
        curve = np.array(ref['results'][key]['64']['normalized_total'][index])
        seeds = []
        for p in np.argsort(curve):
            if not seeds or min(min(abs(p-q), 360-abs(p-q)) for q in seeds) >= 15:
                seeds.append(int(p))
            if len(seeds) == 6:
                break
        angles = sorted({float(p%360) for seed in seeds for p in np.arange(seed-2, seed+2.01, .25)})
        values = [float(model.response(c.direction(t, p)).sum(-1).mean()/c.BASE_AREA) for p in angles]
        i = int(np.argmin(values))
        entry[str(t)] = {'worst': values[i], 'azimuth_deg': angles[i], 'n64_full_grid_worst': float(curve.min()), 'seed_azimuths': seeds, 'tested_angles': angles, 'tested_values': values}
    out['results'][key] = entry
    (c.ROOT/'minima-refinement.json').write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(key, [(t, v['worst'], v['azimuth_deg']) for t, v in entry.items()], flush=True)
