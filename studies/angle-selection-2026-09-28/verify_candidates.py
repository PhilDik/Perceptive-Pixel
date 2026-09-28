"""Selected numerical checks and explicit boundary flags; no hardware validation."""
from pathlib import Path
import json
import numpy as np
import select_angle as s

ROOT=Path(__file__).resolve().parent

def main():
    results=json.loads((ROOT/'range-results.json').read_text())
    flags=[]
    for row in results['rows']:
        for i,f in enumerate(row['fits']):
            z=np.array(f['z_mm'])
            if not f['success'] or np.any((z<=20.05)|(z>=199.95)):
                flags.append({k:row[k] for k in ['area_mode','alpha_deg','mode','scene']} | {'trial_index':i,'fit':f})
    assert len(flags)==results['boundary_fits']+results['nonconverged']
    checks=[]
    for area in ['fixed_base','fixed_active']:
        for alpha in [15,20,25,30]:
            panel=s.make_panel(alpha,area)
            coarse=panel.leakage(panel.exchange(4))*s.SCALE
            fine=panel.leakage(panel.exchange(8))*s.SCALE
            selected=[]
            for name in ['central_0','oblique_0','grazing_0']:
                sc=results['protocol']['scenes'][name];rho=np.array(sc['rho'])
                grids,truth=s.table(panel,sc)
                direct=panel.forward(np.c_[sc['xy'],sc['z']],n=8)*s.SCALE
                fit=s.d.fit(direct@rho+fine[:,None]*1e-6,fine*1e-6,fine*1e-6,grids,16.)
                selected.append({'scene':name,'forward_relative_l2':float(np.linalg.norm(truth-direct)/np.linalg.norm(direct)),
                 'fine_truth_coarse_inverse_noiseless_max_depth_error_mm':float(np.max(np.abs(np.array(fit['z_mm'])-sc['z']))),'success':fit['success']})
            checks.append({'area_mode':area,'alpha_deg':alpha,'coupling_relative_l2':float(np.linalg.norm(coarse-fine)/np.linalg.norm(fine)),
             'coupling_total_relative_difference':float(abs(coarse.sum()-fine.sum())/fine.sum()),'selected_scenes':selected})
    output={'flags':flags,'quadrature':'16 to 64 sample points per facet, selected candidates and 3 of 12 scenes only',
      'checks':checks,'interpretation':'numerical convergence/consistency only; not uncertainty bounds for all configurations or real hardware'}
    (ROOT/'candidate-checks.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'flag_count':len(flags),'max_coupling_relative_l2':max(c['coupling_relative_l2'] for c in checks),
      'max_forward_relative_l2':max(v['forward_relative_l2'] for c in checks for v in c['selected_scenes']),
      'max_noiseless_depth_error_mm':max(v['fine_truth_coarse_inverse_noiseless_max_depth_error_mm'] for c in checks for v in c['selected_scenes'])}))

if __name__=='__main__':main()
