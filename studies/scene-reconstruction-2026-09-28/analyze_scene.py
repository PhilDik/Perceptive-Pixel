"""Transparent summaries and figures of the complete sparse-scene experiment."""
from pathlib import Path
import os,json,csv
ROOT=Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'cache-matplotlib'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    result=json.loads((ROOT/'experiment-results.json').read_text())
    sequence=json.loads((ROOT/'sequential-results.json').read_text())
    diagnostic=json.loads((ROOT/'diagnostic-results.json').read_text())
    configurations=[(a,m) for a in [0,15] for m in ['static','translation','rigid']]
    scenes=list(result['protocol']['scenes'])
    summaries=[];scene_summaries=[];flags=[]
    for a,m in configurations:
        rr=[r for r in result['rows'] if r['alpha_deg']==a and r['mode']==m and r['stress']=='matched']
        def stats(rows):
            return {'n':len(rows),'median_xyz_rmse_mm':float(np.median([r['xyz_rmse_mm'] for r in rows])),
              'mean_xyz_rmse_mm':float(np.mean([r['xyz_rmse_mm'] for r in rows])),
              'median_reflectance_rmse':float(np.median([r['reflectance_rmse'] for r in rows])),
              'median_heldout_signal_relative_l2':float(np.median([r['heldout_signal_relative_l2'] for r in rows])),
              'passes':sum(r['passes_diagnostic'] for r in rows),'best_nonconverged':sum(not r['best']['success'] for r in rows),
              'best_boundary':sum(r['best']['boundary'] for r in rows),
              'max_near_cost_alternative_separation_mm':max([v['xyz_distance_from_best_mm'] for r in rows for v in r['near_cost_alternatives']]+[0])}
        summaries.append({'alpha_deg':a,'mode':m,**stats(rr)})
        for sc in scenes:scene_summaries.append({'alpha_deg':a,'mode':m,'scene':sc,**stats([r for r in rr if r['scene']==sc])})
    for ci,r in enumerate(result['rows']):
        for si,solution in enumerate(r['solutions']):
            if not solution['success'] or solution['boundary']:
                flags.append({'case_index':ci,'start_index':si,**{k:r[k] for k in ['alpha_deg','mode','scene','stress','trial']},
                  'success':solution['success'],'boundary':solution['boundary'],'cost':solution['cost']})
    stress=[]
    for name in ['matched','high_leakage','pose_error']:
        rr=[r for r in result['rows'] if r['alpha_deg']==15 and r['mode']=='rigid' and r['scene']=='separated_colours' and r['stress']==name]
        stress.append({'stress':name,**stats(rr)})
    summary={'scope':'descriptive outcomes;3scenes and3noise repetitions; no population-level statistical superiority',
      'configurations':summaries,'by_scene':scene_summaries,'stress':stress,
      'max_truth_shadow_fraction':max(r['truth_shadow_fraction'] for r in result['rows']),
      'max_fitted_shadow_fraction':max(r['fitted_shadow_fraction'] for r in result['rows']),
      'counts':{k:result[k] for k in ['cases','optimizer_runs','optimizer_nonconverged','best_nonconverged','best_boundary']},
      'noiseless_max_xyz_rmse_mm':max(r['xyz_rmse_mm'] for r in diagnostic['rows']),
      'note':'Noiseless matched-model recovery is a numerical diagnostic, not experimental validation or a proof of uniqueness.'}
    (ROOT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (ROOT/'solver-flags.json').write_text(json.dumps(flags,indent=2)+'\n')
    with (ROOT/'metrics.csv').open('w',newline='',encoding='utf-8') as f:
        fields=['alpha_deg','mode','scene','stress','trial','xyz_rmse_mm','depth_rmse_mm','reflectance_rmse','heldout_signal_relative_l2','passes_diagnostic']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in result['rows'])
    labels=['0°\nstatic','0°\nmove','0°\nmove+turn','15°\nstatic','15°\nmove','15°\nmove+turn']
    titles=['Separated colours','Near, oblique patches','Close patches, identical colours']
    fig,axes=plt.subplots(2,3,figsize=(15,7.6))
    for col,sc in enumerate(scenes):
        for row,metric in enumerate(['xyz_rmse_mm','reflectance_rmse']):
            ax=axes[row,col]
            for ci,(a,m) in enumerate(configurations):
                values=[r[metric] for r in result['rows'] if r['alpha_deg']==a and r['mode']==m and r['scene']==sc and r['stress']=='matched']
                colour='#ad6b30' if a==0 else '#14638f'
                ax.plot(np.array([-0.12,0,.12])+ci,values,'o',color=colour,alpha=.75,ms=5)
                ax.plot([ci-.24,ci+.24],[np.median(values)]*2,color=colour,lw=3)
            ax.set_xticks(range(6),labels,fontsize=8);ax.grid(axis='y',alpha=.22)
            ax.set_ylim(bottom=0)
            if row==0:ax.set_title(titles[col])
            if col==0:ax.set_ylabel('Position RMSE (mm)' if row==0 else 'Reflectance RMSE (0–1)')
    fig.suptitle('Unknown xyz and colour: movement helps some scenes, ambiguity remains',fontsize=15)
    fig.text(.5,.014,'Dots: all 3 noise realizations; lines: medians. Same active area, energy and 8,640 raw reads. No trained network.',ha='center',fontsize=10)
    fig.tight_layout(rect=[0,.04,1,.95]);fig.savefig(ROOT/'reconstruction-results.png',dpi=160);fig.savefig(ROOT/'reconstruction-results.svg');plt.close(fig)

    truth=result['protocol']['scenes']['separated_colours'];p=np.array(truth['points_mm']);rho=np.array(truth['rho'])
    fig=plt.figure(figsize=(13,9))
    ax=fig.add_subplot(2,2,1)
    chosen=next(r for r in result['rows'] if r['alpha_deg']==15 and r['mode']=='rigid' and r['scene']=='separated_colours' and r['trial']==0 and r['stress']=='matched')
    raw=np.array(chosen['raw_observations_e'])[:,1].reshape(5,144)
    im=ax.imshow(np.log10(np.maximum(raw,1)),aspect='auto',cmap='magma')
    ax.set_title('Raw mixed measurements: spectral band 2')
    ax.set_xlabel('Receiver region within six source patterns');ax.set_ylabel('Registered pose')
    fig.colorbar(im,ax=ax,label='log10(aggregated electrons)',fraction=.05)
    for i,m in enumerate(['static','translation','rigid']):
        r=next(r for r in result['rows'] if r['alpha_deg']==15 and r['mode']==m and r['scene']=='separated_colours' and r['trial']==0 and r['stress']=='matched')
        est=np.array(r['matched_points_mm']);rgb=np.array(r['matched_rho'])
        ax=fig.add_subplot(2,2,i+2,projection='3d')
        ax.scatter(*p.T,c=rho,s=110,marker='o',edgecolors='black',label='True patches')
        ax.scatter(*est.T,c=rgb,s=90,marker='^',edgecolors='black',label='Estimated')
        for x,y in zip(p,est):ax.plot(*np.stack([x,y]).T,color='#6d7278',ls='--',lw=1)
        ax.set(xlim=(-50,50),ylim=(-40,40),zlim=(25,160),xlabel='x (mm)',ylabel='y (mm)',zlabel='z (mm)')
        ax.set_title(f'{m}: xyz RMSE {r["xyz_rmse_mm"]:.2f} mm')
        ax.view_init(elev=20,azim=-63)
        if i==0:ax.legend(fontsize=8,loc='upper left')
    fig.suptitle('Illustrative example: 15° facets, first listed scene and first noisy trial',fontsize=14)
    fig.text(.5,.013,'All xyz and reflectances estimated. Three patch areas/normals/count are known. Markers enlarged; colours are illustrative.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.04,1,.96]);fig.savefig(ROOT/'reconstruction-example.png',dpi=160);fig.savefig(ROOT/'reconstruction-example.svg');plt.close(fig)

    fig,axes=plt.subplots(1,2,figsize=(11,4.4))
    steps=[x['poses_accumulated'] for x in sequence['snapshots']]
    axes[0].plot(steps,[x['metrics']['xyz_rmse_mm'] for x in sequence['snapshots']],'o-',color='#14638f')
    axes[1].plot(steps,[x['metrics']['reflectance_rmse'] for x in sequence['snapshots']],'o-',color='#ad6b30')
    for ax in axes:ax.set_xlabel('Acquired poses (increasing data and energy)');ax.set_xticks(steps);ax.grid(alpha=.2)
    axes[0].set_ylabel('Position RMSE (mm)');axes[1].set_ylabel('Reflectance RMSE (0–1)')
    fig.suptitle('Persistent sparse state: refit accumulated observations, fixed physical model')
    fig.tight_layout();fig.savefig(ROOT/'sequential-update.png',dpi=160);fig.savefig(ROOT/'sequential-update.svg');plt.close(fig)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
