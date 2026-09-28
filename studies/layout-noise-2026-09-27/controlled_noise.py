"""Isolate the effect of photon contamination, holding scene/operator fixed."""
import json,time
import numpy as np
from depth_benchmark import Panel,SCENES,TRUE_RGB,prepare_tables,interpolate,fit,information,OUT

started=time.perf_counter()
panel=Panel('triangle',45.,'vertical')
reference=Panel('triangle',30.,'aligned')
scale=100000/(3*reference.forward([[0,0,150]],n=4).sum())
scene=SCENES['central']
raw,_=prepare_tables(panel,scene,4)
grids=[g*scale for g in raw]
mu=interpolate(grids,scene['z'])@TRUE_RGB
rows=[];rng=np.random.default_rng(620927)
for ratio in [0.,1.,10.,100.]:
    # Fixed calibration reference, independent of any scene/depth candidate.
    bg=np.full(len(mu),100000*ratio/(3*len(mu)))
    estimates=[]
    for trial in range(256):
        observed=rng.poisson(mu+bg[:,None]).astype(float)+rng.normal(0,np.sqrt(panel.read_variance),mu.shape)
        estimates.append(fit(observed,bg,bg,grids,panel.read_variance))
    error=np.abs(np.array([e['z_mm'] for e in estimates])-scene['z'])
    rows.append({'background_in_reference_units':ratio,'signal_electrons':float(mu.sum()),
                 'background_electrons':float(bg.sum()*3),
                 'median_mean_absolute_depth_error_mm':float(np.median(error.mean(axis=1))),
                 'mean_absolute_depth_error_mm':float(error.mean()),
                 'p90_mean_absolute_depth_error_mm':float(np.quantile(error.mean(axis=1),.9)),
                 'failure_gt10mm_fraction':float(np.mean(error.max(axis=1)>10)),
                 'information':information(grids,scene,bg,panel.read_variance),'estimates':estimates})
    print(json.dumps({k:v for k,v in rows[-1].items() if k not in ['estimates','information']}),flush=True)
# In a fixed linearized model, adding background cannot add information.
std=np.array([r['information']['local_depth_std_mm'] for r in rows])
assert np.all(np.diff(std,axis=0)>=-1e-7)
data={'status':'controlled synthetic ablation; fixed useful signal, no physical suppression claim',
      'configuration':panel.id,'scene':scene,'trials_per_level':256,
      'rows':rows,'runtime_seconds':time.perf_counter()-started}
(OUT/'controlled-results.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
