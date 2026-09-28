"""Conditional tilt selection and planar controls, not commercial-device ranking.
Reuses the bounded two-patch inverse problem; no trained network or rotation.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
import importlib.util,json,time,math,hashlib
import numpy as np
OUT=Path(__file__).resolve().parent
SOURCE=OUT.parent/'layout-noise-2026-09-27/depth_benchmark.py'
spec=importlib.util.spec_from_file_location('old_depth',SOURCE)
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
ANGLES=list(range(0,61,5))
LEVELS=[0.,1e-6,1e-4]
TRAIN=d.SCENES
VALIDATION={
 'central_new':{'xy':[[-14.,-6.],[22.,11.]],'z':[93.7,147.3]},
 'oblique_new':{'xy':[[55.,-18.],[88.,13.]],'z':[73.7,126.3]},
 'grazing_new':{'xy':[[84.,-12.],[108.,18.]],'z':[35.7,57.3]},
}
RHO_TRAIN=d.TRUE_RGB
RHO_VALID=np.array([[.60,.22,.13],[.16,.40,.68]])
REFERENCE=d.Panel('triangle',30.,'aligned')
SCALE=float(100000/(3*REFERENCE.forward([[0.,0.,150.]],n=4).sum()))

def make_panel(alpha,area_mode='fixed_base'):
    panel=d.Panel('triangle',float(alpha),'vertical')
    if area_mode=='fixed_active':
        # Shrink the complete pyramid, keeping centers and normalized emitted energy.
        # Then sum(facet areas) equals the planar baseline's active area.
        f=math.sqrt(math.cos(math.radians(alpha)))
        panel.faces*=f;panel.height*=f;panel.side*=f;panel.area*=f*f
        panel.offsets=np.r_[panel.normals[:,2]*panel.height,0.]
        assert np.allclose(panel.area.sum(),d.BASE_AREA)
    return panel

def pooled(a):return a.reshape(-1,3,*a.shape[1:]).sum(axis=1)

def table(panel,scene,n=4):
    xy=np.asarray(scene['xy']);z=np.asarray(scene['z'])
    grids=[panel.forward(np.c_[np.tile(xy[i],(len(d.DEPTH_GRID),1)),d.DEPTH_GRID],n=n)*SCALE for i in range(2)]
    truth=panel.forward(np.c_[xy,z],n=n)*SCALE
    return grids,truth

def fisher(panel,scene,rho,bg,mode='split',n=4,unknown_xy=False):
    pts=np.c_[scene['xy'],scene['z']].astype(float)
    ff=panel.forward(pts,n=n)*SCALE
    if mode=='pooled':ff=pooled(ff)
    mu=ff@rho;rv=48. if mode=='pooled' else 16.
    w=1/np.sqrt(mu+bg[:,None]+rv)
    derivatives=[]
    for patch in range(2):
        for coord in [0,1,2]:
            delta=np.zeros_like(pts);delta[patch,coord]=.05
            derivative=(panel.forward(pts+delta,n=n)-panel.forward(pts-delta,n=n))*SCALE/.1
            if mode=='pooled':derivative=pooled(derivative)
            derivatives.append((derivative@rho*w).ravel())
    jz=np.array([derivatives[2],derivatives[5]]).T
    nuisance=[]
    for p in range(2):
        for c in range(3):
            v=np.zeros_like(mu);v[:,c]=ff[:,p];nuisance.append((v*w).ravel())
    if unknown_xy:nuisance.extend(derivatives[i] for i in [0,1,3,4])
    u,s,_=np.linalg.svd(np.array(nuisance).T,full_matrices=False)
    q=u[:,s>max(s[0]*1e-10,1e-14)]
    projected=jz-q@(q.T@jz)
    _,sv,vh=np.linalg.svd(projected,full_matrices=False)
    rank=int(np.sum(sv>max(sv[0]*1e-10,1e-14)))
    std=None if rank<2 else np.sqrt(np.diag((vh.T/(sv*sv))@vh)).tolist()
    return {'depth_rank':rank,'singular_values_per_mm':sv.tolist(),'local_std_mm':std,'unknown_xy':unknown_xy}

def summarize(fits,scene,rho):
    est=np.array([x['z_mm'] for x in fits]);err=np.abs(est-np.array(scene['z']))
    rel=(err/np.array(scene['z'])).mean(axis=1)
    boundary=np.any((est<=20.05)|(est>=199.95),axis=1)
    return {'mean_relative_depth_error':float(rel.mean()),'median_relative_depth_error':float(np.median(rel)),
      'median_mae_mm':float(np.median(err.mean(axis=1))),'p90_mae_mm':float(np.quantile(err.mean(axis=1),.9)),
      'fraction_any_patch_relative_error_over_25pct':float(np.mean(np.any(err/scene['z']>.25,axis=1))),
      'nonconverged':int(sum(not x['success'] for x in fits)),'boundary_fits':int(boundary.sum()),
      'relative_errors':rel.tolist(),'fits':fits}

def run_scene(panel,scene,rho,leak,ntrials,seed,stage,scene_name,allow_pool=False):
    grids,truth=table(panel,scene)
    mu=truth@rho
    rows=[]
    # Truth is directly integrated; inversion uses interpolated values at off-grid depths.
    interp=d.interpolate(grids,scene['z'])@rho
    for li,eta in enumerate(LEVELS):
        rng=np.random.default_rng(seed+li)
        bg=leak*eta
        fits=[];poolfits=[]
        for _ in range(ntrials):
            obs=rng.poisson(mu+bg[:,None]).astype(float)+rng.normal(0,4.,mu.shape)
            fits.append(d.fit(obs,bg,bg,grids,16.))
            if allow_pool:
                poolfits.append(d.fit(pooled(obs),pooled(bg),pooled(bg),[pooled(g) for g in grids],48.))
        for mode,f in [('split',fits)]+([('pooled',poolfits)] if allow_pool else []):
            row={'stage':stage,'alpha_deg':panel.alpha,'mode':mode,'scene':scene_name,'scene_parameters':scene,
             'rho':rho.tolist(),'eta':eta,'trials':ntrials,'signal_e':float(mu.sum()),'background_e':float(bg.sum()*3),
             'interpolation_signal_relative_l2':float(np.linalg.norm(mu-interp)/np.linalg.norm(mu)),
             **summarize(f,scene,rho)}
            rows.append(row)
    return rows

def main():
    start=time.perf_counter();rows=[];geometries=[];diagnostics=[]
    geometry_cache={}
    protocol={'status':'protocol fixed before simulation','angles_deg':ANGLES,'scenes_selection':TRAIN,'scenes_validation':VALIDATION,
      'primary_eta':1e-6,'other_eta':LEVELS,'selection_trials':32,'validation_trials':128,
      'criterion':'equal weight across 3 near/wide scenes, mean absolute relative depth error over patches and noise trials; select smallest positive tilt within 10% of lowest positive-tilt score',
      'planar_rule':'planar controls reported alongside, never excluded to force a faceted winner',
      'validation_candidates':'selected positive tilt, positive minimum-score tilt, 15,30,45 degrees, and planar0; fixed after selection, before validation',
      'sensor_scope':'ideal common sensitivity, 9mm triangular footprint, 4x4 verticalstagger, knownxy/area/normals, calibrated3bands, +/-20mm translations, no rotations',
      'raw_readouts':'12 per whole receiver pixel/slot/band; 1728 overall; triangle3regions x4 subexposures',
      'planar_pooled':'deterministic sum of the SAME 3 planar observations; read variance48 versus16 per splitregion; not single-read hardware',
      'normalization':'primary fixed base; selected fixed-active-area geometry physically shrunk before photon computation',
      'far_scope':'local information diagnostic only, fixed light budget and mm-sized patches, not included in angle selection',
      'scale':SCALE,'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest()}
    (OUT/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n',encoding='utf-8')
    for ai,alpha in enumerate(ANGLES):
        panel=make_panel(alpha);ex=panel.exchange(4);leak=panel.leakage(ex)*SCALE
        geometry_cache[alpha]=(panel,leak)
        geometries.append({'alpha_deg':alpha,'height_mm':panel.height,'active_area_per_pixel_mm2':float(panel.area.sum()),'leakage_fraction':float(leak.sum()*3/SCALE)})
        for si,(name,scene) in enumerate(TRAIN.items()):
            rows.extend(run_scene(panel,scene,RHO_TRAIN,leak,32,100000+ai*1000+si*10,'selection',name,alpha==0))
        print(json.dumps({'stage':'selection','alpha':alpha,'elapsed_s':round(time.perf_counter()-start,1)}),flush=True)
        (OUT/'progress.json').write_text(json.dumps({'geometry':geometries,'rows':rows}),encoding='utf-8')
    scores=[]
    for alpha,mode in [(0,'pooled')]+[(a,'split') for a in ANGLES]:
        subset=[r for r in rows if r['alpha_deg']==alpha and r['mode']==mode and r['eta']==1e-6]
        scores.append({'alpha_deg':alpha,'mode':mode,'score':float(np.mean([r['mean_relative_depth_error'] for r in subset]))})
    positive=[r for r in scores if r['alpha_deg']>0]
    best=min(positive,key=lambda r:r['score'])
    eligible=[r for r in positive if r['score']<=1.1*best['score']]
    chosen=min(eligible,key=lambda r:r['alpha_deg'])
    candidates=sorted(set([0,15,30,45,best['alpha_deg'],chosen['alpha_deg']]))
    selection={'scores':scores,'best_positive_on_selection':best,'smallest_within_10pct':chosen,'validation_candidates':candidates,
               'warning':'choice conditional on assumed model and eta; not a device optimum'}
    (OUT/'selection_frozen.json').write_text(json.dumps(selection,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'selection_frozen':selection}),flush=True)
    for ai,alpha in enumerate(candidates):
        panel,leak=geometry_cache[alpha]
        for si,(name,scene) in enumerate(VALIDATION.items()):
            rows.extend(run_scene(panel,scene,RHO_VALID,leak,128,900000+ai*1000+si*10,'validation',name,alpha==0))
        print(json.dumps({'stage':'validation','alpha':alpha,'elapsed_s':round(time.perf_counter()-start,1)}),flush=True)
        (OUT/'progress.json').write_text(json.dumps({'geometry':geometries,'rows':rows}),encoding='utf-8')
    for area_mode in ['fixed_base','fixed_active']:
        for alpha in candidates:
            panel=make_panel(alpha,area_mode)
            leak=panel.leakage(panel.exchange(4))*SCALE
            # Direct geometric local derivatives, not a singular pseudo-inverse.
            for name,scene in {**VALIDATION,'far_diagnostic':{'xy':[[-18.,-8.],[18.,8.]],'z':[503.7,907.3]}}.items():
                signal=panel.forward(np.c_[scene['xy'],scene['z']],n=4)*SCALE@RHO_VALID
                for eta in LEVELS:
                    bg=leak*eta
                    for unknown_xy in [False,True]:
                        info=fisher(panel,scene,RHO_VALID,bg,unknown_xy=unknown_xy)
                        diagnostics.append({'area_mode':area_mode,'alpha_deg':alpha,'scene':name,'eta':eta,'signal_e':float(signal.sum()),'background_e':float(bg.sum()*3),**info})
            print(json.dumps({'stage':'area_information','mode':area_mode,'alpha':alpha}),flush=True)
    # Selective quadrature refinement for chosen candidate and planar / 45 controls.
    checks=[]
    for alpha in sorted(set([0,45,chosen['alpha_deg']])):
        panel,leak=geometry_cache[alpha]
        fineleak=panel.leakage(panel.exchange(8))*SCALE
        checks.append({'alpha_deg':alpha,'coupling_refinement_relative_change':float(np.linalg.norm(leak-fineleak)/max(np.linalg.norm(fineleak),1e-30)),
                       'scene_signal_refinement_relative_l2':{name:float(np.linalg.norm(panel.forward(np.c_[scene['xy'],scene['z']],n=4)-panel.forward(np.c_[scene['xy'],scene['z']],n=8))/np.linalg.norm(panel.forward(np.c_[scene['xy'],scene['z']],n=8))) for name,scene in VALIDATION.items()}})
    result={'status':'complete; conditional synthetic angle selection','protocol':protocol,'selection':selection,'geometry':geometries,'rows':rows,'local_information':diagnostics,
            'numerical_checks':checks,'elapsed_seconds':time.perf_counter()-start,'fit_count':sum(r['trials'] for r in rows),
            'nonconverged':sum(r['nonconverged'] for r in rows),'boundary_fits':sum(r['boundary_fits'] for r in rows)}
    (OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['status','fit_count','nonconverged','boundary_fits','elapsed_seconds']}),flush=True)

if __name__=='__main__':main()
