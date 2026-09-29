"""Exact direction/fixture arithmetic and reuse of prior coupling totals.

This is a component-level planning calculation. No measured LED receive response
or scene reconstruction is synthesized. Standard library only.
"""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TILT = 30.0  # Illustrative fixture orientation, not an optimized design angle.
AREA_MM2 = 7.5
PACKAGE_W, PACKAGE_H = 5.4, 4.3
TOTAL_RECEIVERS = 24
rows = []
cases = [('triangle_3', 3, [0]), ('triangle_6', 3, [0, 60]),
         ('square_4', 4, [0]), ('square_8', 4, [0, 45])]
for name, facets, rotations in cases:
    base = [30, 150, 270] if facets == 3 else [45, 135, 225, 315]
    azimuths = sorted({(a + r) % 360 for r in rotations for a in base})
    a = math.radians(TILT)
    normals = [[math.sin(a)*math.cos(math.radians(p)),
                math.sin(a)*math.sin(math.radians(p)), math.cos(a)] for p in azimuths]
    assert all(abs(sum(v*v for v in n)-1) < 1e-12 for n in normals)
    cells = TOTAL_RECEIVERS // facets
    assert cells % len(rotations) == 0
    # A regular pyramid side face is a triangle of base b and slant height
    # b/[2*tan(pi/facets)*cos(tilt)]. Fit an axis-aligned rectangular envelope
    # of width W along the base and height H up the face, with its bottom at
    # the base. Width at its upper corners gives b >= W + k*H.
    k = 2 * math.tan(math.pi/facets) * math.cos(a)
    bound = PACKAGE_W + k*PACKAGE_H
    envelope_bound = (PACKAGE_W+2) + k*(PACKAGE_H+2)
    for w,h,b in [(PACKAGE_W,PACKAGE_H,bound),(PACKAGE_W+2,PACKAGE_H+2,envelope_bound)]:
        slant = b/k
        assert abs(b*(1-h/slant)-w) < 1e-10
    rows.append({'case': name, 'facets_per_cell': facets, 'cell_rotations_deg': rotations,
                 'normal_azimuths_deg': azimuths, 'distinct_normals': len(azimuths),
                 'normals_xyz': normals, 'cells_at_24_receivers': cells,
                 'independent_receiver_channels': TOTAL_RECEIVERS,
                 'total_sensitive_area_mm2': TOTAL_RECEIVERS*AREA_MM2,
                 'minimum_base_side_body_only_mm': bound,
                 'minimum_base_side_rectangular_1mm_keepout_mm': envelope_bound})
assert [r['distinct_normals'] for r in rows] == [3,6,4,8]
# Translation of a cell does not change any normal; at zero tilt all normals
# become the same +z direction regardless of their nominal azimuth labels.
zero_tilt_unique = {(0.0,0.0,1.0) for r in rows for p in r['normal_azimuths_deg']}
assert len(zero_tilt_unique) == 1

source = ROOT.parent/'layout-noise-2026-09-27/depth-results.json'
old = json.loads(source.read_text())
selected = [r for r in old['geometry'] if r['shape']=='triangle' and r['tilt_deg']==45.0]
leakage = {r['layout']: r['leakage_fraction_all_bands'] for r in selected}
coupling = {'original_source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'source_model': 'same-orientation whole Lambertian facets, finite 4x4 panel, 45 degrees, checkerboard slots',
            'fractions': leakage,
            'pure_stagger_relative_reduction': 1-leakage['shifted']/leakage['aligned'],
            'author_lattice_relative_reduction': 1-leakage['vertical']/leakage['aligned']}

# Datasheet anchor: 50 uA at 1 mW/cm^2, 950 nm, 5 V reverse bias, 25 C.
# 1 mW/cm^2 = 10 W/m^2; incident power on 7.5 mm^2 = 75 uW.
incident_w = 10 * AREA_MM2 * 1e-6
responsivity = 50e-6 / incident_w
result = {'status':'component planning arithmetic', 'fixture_tilt_deg':TILT,
          'receiver_example':'Vishay BPW34', 'cases':rows,
          'flat_distinct_normals':1,
          'datasheet_anchor':{'wavelength_nm':950,'reverse_bias_V':5,'temperature_C':25,
                              'irradiance_W_m2':10,'incident_power_W':incident_w,
                              'typical_current_A':50e-6,'derived_typical_responsivity_A_W':responsivity},
          'packaging_scope':'body/envelope fits on a side face; lead bending, PCB, 3D collisions, masks and carrier spacing require mechanical design',
          'coupling_from_prior_model':coupling,
          'checks':{'unit_normals':True,'expected_direction_counts':True,'balanced_24_channel_budget':True,
                    'rectangle_fit_equalities':True,'flat_collapse':True}}
(ROOT/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')

# Vector diagram of direction sets, not a layout of overlapping physical cells.
parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="420" viewBox="0 0 1040 420" role="img">',
       '<title>FacetCensus: azimuths of facet normals</title>',
       '<rect width="1040" height="420" fill="#f5f8fa"/>',
       '<text x="30" y="35" font-family="Arial" font-size="22">Azimuths of facet normals — two orientations can add directions</text>']
for idx,row in enumerate(rows):
    cx,cy=140+idx*252,210
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="82" fill="white" stroke="#d0dbe3"/>')
    for p in row['normal_azimuths_deg']:
        a=math.radians(p); x,y=cx+77*math.cos(a),cy-77*math.sin(a)
        color='#246d97' if p in ([30,150,270] if row['facets_per_cell']==3 else [45,135,225,315]) else '#bd6a2d'
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.3f}" y2="{y:.3f}" stroke="{color}" stroke-width="3"/>')
        ux,uy=math.cos(a),-math.sin(a)
        points=f'{x:.3f},{y:.3f} {x-10*ux-4*uy:.3f},{y-10*uy+4*ux:.3f} {x-10*ux+4*uy:.3f},{y-10*uy-4*ux:.3f}'
        parts.append(f'<polygon points="{points}" fill="{color}"/>')
    label=f'{row["facets_per_cell"]} facets / {row["distinct_normals"]} directions'
    rot=' + '.join(str(v)+'°' for v in row['cell_rotations_deg'])
    parts.extend([f'<text x="{cx}" y="99" text-anchor="middle" font-family="Arial" font-size="18">{label}</text>',
                  f'<text x="{cx}" y="322" text-anchor="middle" font-family="Arial" font-size="17">Cell rotations: {rot}</text>'])
parts.extend(['<text x="30" y="373" font-family="Arial" font-size="17">Nonzero tilt; arrows show horizontal projections, not narrow light rays or pixel placement.</text>',
              '<text x="30" y="401" font-family="Arial" font-size="17">Vertical column offset changes positions and coupling; it preserves each cell orientation.</text></svg>'])
(ROOT/'directions.svg').write_text(''.join(parts),encoding='utf-8')
print(json.dumps({'direction_counts':[r['distinct_normals'] for r in rows],
                  'fixture_base_mm':[rows[0]['minimum_base_side_body_only_mm'],rows[2]['minimum_base_side_body_only_mm']],
                  'responsivity_A_W':responsivity,'reused_coupling':coupling},ensure_ascii=False))
