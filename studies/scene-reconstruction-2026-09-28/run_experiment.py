"""Predeclared sparse-scene experiment; no known xyz provided to inversion."""
from pathlib import Path
import argparse,json,time,hashlib
import numpy as np
import scene_model as s
ROOT=Path(__file__).resolve().parent
SCENES={
 'separated_colours':{'points_mm':[[-24.3,-12.8,48.6],[7.2,18.4,77.3],[27.6,-5.1,111.8]],'rho':[[.75,.16,.10],[.12,.68,.21],[.13,.22,.78]]},
 'near_oblique':{'points_mm':[[-30.2,14.6,36.7],[18.1,-20.3,53.9],[33.5,17.4,83.2]],'rho':[[.61,.25,.11],[.18,.73,.30],[.20,.16,.64]]},
 'similar_colours_close':{'points_mm':[[-8.1,-2.9,78.7],[4.7,6.2,84.3],[13.2,-7.5,97.6]],'rho':[[.45,.35,.30],[.45,.35,.30],[.45,.35,.30]]},
}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pilot',action='store_true');args=ap.parse_args()
    start=time.perf_counter();scale=s.calibration()
    protocol={'status':'parameters saved before fits','scope':'3 small diffuse patches, known count/area/world normals; all xyz and all three-band reflectances unknown',
      'scenes':SCENES,'alphas':[0,15],'area':'equal total sensitive area; tilted geometry shrunk by sqrt(cos(alpha)) at fixed center positions',
      'modes':['static','translation','rigid'],'pose_count':5,'patterns':'checker/columns/rows, each complemented: six patterns per pose',
      'total_raw_readouts':8640,'recorded_aggregates':2160,'read_variance_per_aggregate':16,'spectral_bands':3,
      'energy':'one common total source energy divided across 5 poses,6 patterns,3 bands,24 emitting facets; never renormalize useful received light per configuration',
      'poses':{mode:[{'R':R.tolist(),'t_mm':t.tolist()} for R,t in s.poses(mode)] for mode in ['static','translation','rigid']},
      'heldout_poses':[{'R':R.tolist(),'t_mm':t.tolist()} for R,t in s.poses('rigid',True)],
      'heldout_budget':'four new poses, same per-pose energy/readouts; diagnostic only, unused for fitting or start selection',
      'truth_quadrature_n':4,'inverse_quadrature_n':2,'eta_primary':1e-6,'scale_e':scale,
      'trials':3,'starts':6,'max_nfev':220,'search_bounds_xyz_mm':[[-50,-40,25],[50,40,160]],'rho_bounds':[0,1],
      'success_diagnostic':'xyz RMSE <5mm AND reflectance RMSE <0.1; illustrative, not a measured device specification',
      'initialization':'same six generic states for every case; seed28092863; no truth coordinates/colours supplied',
      'noise':'Poisson raw signal+background, Gaussian read std4; observed-count variance weighting; independent noise per case',
      'leakage':'hypothetical transmission, no physical suppression mechanism demonstrated',
      'excluded':'unknown patch count/area/normals, extended textures, mutual scene occlusion, multiple/specular scattering, learned prior, pose estimation, dynamic mapping',
      'shadowing':'panel shadowing omitted in differentiable inversion; separately audit truth configurations and reconstructed points',
      'stress_tests':['separated_colours/15/rigid/eta=1e-4,3trials','separated_colours/15/rigid,0.5mm and0.5deg pose error,3trials'],
      'source_sha256':hashlib.sha256((ROOT/'scene_model.py').read_bytes()).hexdigest()}
    name='pilot' if args.pilot else 'experiment'
    (ROOT/(name+'-protocol.json')).write_text(json.dumps(protocol,indent=2)+'\n')
    starts=s.initializations(3,6,28092863);rows=[];geometry={}
    cases=[(alpha,mode,scene,1e-6,'matched',trial) for alpha in [0,15] for mode in protocol['modes'] for scene in SCENES for trial in range(3)]
    cases += [(15,'rigid','separated_colours',eta,stress,trial) for eta,stress in [(1e-4,'high_leakage'),(1e-6,'pose_error')] for trial in range(3)]
    if args.pilot:cases=[(15,'rigid','separated_colours',1e-6,'matched',0)]
    for ci,(alpha,mode,name_scene,eta,stress,trial) in enumerate(cases):
        if alpha not in geometry:
            panel=s.make_panel(alpha);exchange=panel.exchange(4);geometry[alpha]=(panel,exchange)
        panel,exchange=geometry[alpha];sc=SCENES[name_scene];points=np.array(sc['points_mm']);rho=np.array(sc['rho'])
        sequence=s.poses(mode)
        if stress=='pose_error':
            prng=np.random.default_rng(280928500+trial)
            truth_seq=[(s.rotation(*prng.normal(0,.5,2))@R,t+prng.normal(0,.5,3)) for R,t in sequence]
        else:truth_seq=sequence
        truth=s.Acquisition(panel,truth_seq,n=4,scale=scale);inverse=s.Acquisition(panel,sequence,n=2,scale=scale)
        bg=truth.background(exchange,eta);mu=truth.forward(points)@rho
        noise=np.random.default_rng(28092900+ci)
        obs=noise.poisson(mu+bg[:,None]).astype(float)+noise.normal(0,4,mu.shape)
        fit=s.fit(inverse,obs,bg,starts,max_nfev=220);best=fit['best']
        metric=s.matched_errors(best['points_mm'],best['rho'],points,rho)
        held=s.Acquisition(panel,s.poses('rigid',True),n=4,scale=scale)
        expected=held.forward(points)@rho;predicted=held.forward(best['points_mm'])@best['rho']
        hbg=held.background(exchange,eta)
        metric['heldout_signal_relative_l2']=float(np.linalg.norm(predicted-expected)/np.linalg.norm(expected))
        metric['heldout_standardized_mean_rms']=float(np.sqrt(np.mean((predicted-expected)**2/(expected+hbg[:,None]+16))))
        metric['passes_diagnostic']=metric['xyz_rmse_mm']<5 and metric['reflectance_rmse']<.1
        row={'alpha_deg':alpha,'mode':mode,'scene':name_scene,'eta':eta,'stress':stress,'trial':trial,'seed':28092900+ci,
             'signal_e':float(mu.sum()),'background_e':float(bg.sum()*3),'truth_shadow_fraction':truth.shadow_fraction(points),
             'fitted_shadow_fraction':truth.shadow_fraction(np.array(best['points_mm'])),
             'inverse_truth_mismatch_relative_l2':float(np.linalg.norm(inverse.forward(points)@rho-mu)/np.linalg.norm(mu)),
             **metric,**fit}
        if trial==0 and stress=='matched':
            row['raw_observations_e']=obs.tolist();row['expected_signal_e']=mu.tolist();row['background_per_channel_e']=bg.tolist()
        rows.append(row)
        (ROOT/(name+'-progress.json')).write_text(json.dumps({'rows':rows}),encoding='utf-8')
        print(json.dumps({'case':ci+1,'of':len(cases),'alpha':alpha,'mode':mode,'scene':name_scene,'stress':stress,'trial':trial,
          'xyz_rmse_mm':metric['xyz_rmse_mm'],'rho_rmse':metric['reflectance_rmse'],'best_converged':best['success'],
          'elapsed_s':round(time.perf_counter()-start,1)}),flush=True)
    result={'protocol':protocol,'rows':rows,'cases':len(rows),'optimizer_runs':sum(len(r['solutions']) for r in rows),
      'optimizer_nonconverged':sum(not sol['success'] for r in rows for sol in r['solutions']),
      'best_nonconverged':sum(not r['best']['success'] for r in rows),'best_boundary':sum(r['best']['boundary'] for r in rows),
      'elapsed_seconds':time.perf_counter()-start,'status':'complete; restricted sparse-scene reconstruction, no hardware'}
    (ROOT/(name+'-results.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['protocol','rows']}),flush=True)

if __name__=='__main__':main()
