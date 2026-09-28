"""Accumulate registered measurements of one fixed scene; no network training."""
from pathlib import Path
import json
import numpy as np
import scene_model as s
ROOT=Path(__file__).resolve().parent

def main():
    result=json.loads((ROOT/'experiment-results.json').read_text())
    row=next(r for r in result['rows'] if r['alpha_deg']==15 and r['mode']=='rigid' and r['scene']=='separated_colours' and r['trial']==0 and r['stress']=='matched')
    scene=result['protocol']['scenes']['separated_colours'];scale=result['protocol']['scale_e']
    panel=s.make_panel(15);observed=np.array(row['raw_observations_e']);bg=np.array(row['background_per_channel_e'])
    sequence=s.poses('rigid');snapshots=[];previous=None
    for count in [1,3,5]:
        a=s.Acquisition(panel,sequence[:count],n=2,scale=scale,pose_budget=5)
        starts=s.initializations(3,6,28092863)
        if previous is not None:starts[0]=previous
        fitted=s.fit(a,observed[:a.rows],bg[:a.rows],starts)
        best=fitted['best'];previous=np.c_[best['points_mm'],best['rho']].ravel()
        metric=s.matched_errors(best['points_mm'],best['rho'],np.array(scene['points_mm']),np.array(scene['rho']))
        snapshots.append({'poses_accumulated':count,'source_energy_fraction':count/5,'raw_readouts':count*1728,
          'state':{'points_mm':best['points_mm'],'three_band_reflectance':best['rho'],
                   'known_count':3,'known_area_mm2':1,'known_normals_world':[s.NORM.tolist()]*3,
                   'observation_support':'all retained raw observations from the listed registered poses',
                   'uncertainty':'retained multi-start alternatives only; no calibrated posterior or unseen-surface map'},
          'metrics':metric,'fit':fitted})
    out={'scope':'sequential re-fit of accumulated data for three persistent patches; no dynamic association, new-surface discovery or trained model',
      'selection':'first trial of the first listed scene,15degree rigid-motion condition; not selected by reconstruction quality',
      'comparison_warning':'the successive stages use increasing acquired energy/data; this is an update demonstration, not a matched-budget gain claim',
      'snapshots':snapshots,'optimizer_runs':18,'optimizer_nonconverged':sum(not sol['success'] for snap in snapshots for sol in snap['fit']['solutions'])}
    (ROOT/'sequential-results.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps([{'poses':q['poses_accumulated'],'xyz_rmse_mm':q['metrics']['xyz_rmse_mm'],'reflectance_rmse':q['metrics']['reflectance_rmse']} for q in snapshots]))

if __name__=='__main__':main()
