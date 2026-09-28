"""Post-result noiseless diagnostic: distinguish solver/conditioning from noise.

Uses exact matched quadrature deliberately; not an independent reconstruction
validation and not included in matched-budget noisy performance statistics.
"""
from pathlib import Path
import json
import numpy as np
import scene_model as s
ROOT=Path(__file__).resolve().parent

def main():
    main=json.loads((ROOT/'experiment-results.json').read_text());out=[]
    protocol={'reason':'observed failure on close equal-colour patches and variable recovery on separated patches',
      'selected_cases':[[a,sc] for a in [0,15] for sc in ['separated_colours','similar_colours_close']],
      'conditions':'rigid trajectory; no noise; matched n=4 forward/inverse; same6genericstarts; max_nfev1000; eta1e-6',
      'interpretation':'post-result numerical diagnosis only; truth never supplied as initialization; no physical uniqueness conclusion'}
    (ROOT/'diagnostic-protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    for alpha,scene_name in protocol['selected_cases']:
        scene=main['protocol']['scenes'][scene_name];panel=s.make_panel(alpha)
        a=s.Acquisition(panel,s.poses('rigid'),n=4,scale=main['protocol']['scale_e'])
        bg=a.background(panel.exchange(4),1e-6);mu=a.forward(scene['points_mm'])@scene['rho']
        fit=s.fit(a,mu+bg[:,None],bg,s.initializations(3,6,28092863),max_nfev=1000)
        best=fit['best'];metrics=s.matched_errors(best['points_mm'],best['rho'],np.array(scene['points_mm']),np.array(scene['rho']))
        out.append({'alpha_deg':alpha,'scene':scene_name,**metrics,**fit})
        print(json.dumps({'alpha':alpha,'scene':scene_name,'xyz_rmse_mm':metrics['xyz_rmse_mm'],'cost':best['cost'],'converged':best['success']}),flush=True)
    result={'protocol':protocol,'rows':out,'optimizer_runs':24,'optimizer_nonconverged':sum(not sol['success'] for r in out for sol in r['solutions'])}
    (ROOT/'diagnostic-results.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
