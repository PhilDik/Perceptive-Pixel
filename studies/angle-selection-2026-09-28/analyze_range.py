"""Summarize the exploratory challenge; bootstrap scenes and noise, not hardware."""
from pathlib import Path
import json
import os
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parent/'cache-matplotlib'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent

def main():
    data=json.loads((ROOT/'range-results.json').read_text())
    groups=['central','oblique','grazing']
    scenes=list(data['protocol']['scenes'])
    configurations=[(0,'pooled')]+[(a,'split') for a in data['protocol']['angles']]
    result={'bootstrap_draws':2000,'confidence':'descriptive 95% percentile intervals, not adjusted for selection or multiple comparisons',
      'method':'Within each of 3 groups, resample 4 scenes with replacement, shared across configurations. Within each selected scene/configuration, independently resample 48 noise trials. Noise across angles is NOT paired; split/pooled use the same planar acquisitions. All comparisons here are descriptive.',
      'area_modes':{}}
    fig,axes=plt.subplots(1,2,figsize=(12,4.9),sharey=True)
    for ai,area in enumerate(data['protocol']['area_modes']):
        rows=[r for r in data['rows'] if r['area_mode']==area]
        cube=np.array([[next(r['relative_errors'] for r in rows if (r['alpha_deg'],r['mode'],r['scene'])==(a,m,s)) for s in scenes] for a,m in configurations])
        means=cube.mean(axis=(1,2));rng=np.random.default_rng(28092890+ai)
        indices=np.column_stack([rng.choice([i for i,s in enumerate(scenes) if data['protocol']['scenes'][s]['group']==g],(2000,4)) for g in groups])
        samples=[]
        # Keep the exact pairing for the planar split/pooled observations only.
        planar_noise=rng.integers(0,48,(2000,12,48))
        for ci,(a,m) in enumerate(configurations):
            noise=planar_noise if a==0 else rng.integers(0,48,(2000,12,48))
            samples.append(cube[ci][indices[:,:,None],noise].mean(axis=(1,2)))
        boot=np.array(samples)
        positive=[i for i,(a,m) in enumerate(configurations) if a>0]
        best=min(positive,key=lambda i:means[i])
        chosen=min((i for i in positive if means[i]<=means[best]*1.1),key=lambda i:configurations[i][0])
        summaries=[]
        for ci,(a,m) in enumerate(configurations):
            summaries.append({'alpha_deg':a,'mode':m,'score':float(means[ci]),'ci95':np.quantile(boot[ci],[.025,.975]).tolist(),
             'groups':{g:float(cube[ci,[i for i,s in enumerate(scenes) if data['protocol']['scenes'][s]['group']==g]].mean()) for g in groups},
             'delta_vs_planar_pooled':float(means[ci]-means[0]),'delta_vs_planar_pooled_ci95':np.quantile(boot[ci]-boot[0],[.025,.975]).tolist()})
        comparisons=[{'other_alpha_deg':a,'other_mode':m,'chosen_minus_other':float(means[chosen]-means[ci]),
                      'ci95':np.quantile(boot[chosen]-boot[ci],[.025,.975]).tolist()} for ci,(a,m) in enumerate(configurations)]
        result['area_modes'][area]={'best_positive':configurations[best][0],'smallest_within_10pct':configurations[chosen][0],
          'scores':summaries,'chosen_comparisons':comparisons}
        ax=axes[ai];xx=np.arange(len(configurations));interval=np.quantile(boot,[.025,.975],axis=1)*100
        ax.errorbar(xx,means*100,yerr=np.stack([means*100-interval[0],interval[1]-means*100]),fmt='o',capsize=4,color='#155c85')
        for g,c in zip(groups,['#bc6c25','#438755','#8664a9']):
            ax.plot(xx,[r['groups'][g]*100 for r in summaries],'.--',alpha=.75,lw=1,label=g,color=c)
        ax.set_xticks(xx,['0°\nsum','0°\nsplit']+[f'{a}°' for a,m in configurations[2:]])
        ax.set_title('Fixed footprint' if area=='fixed_base' else 'Equal total sensitive area')
        ax.set_xlabel('Facet-normal tilt from panel normal');ax.grid(axis='y',alpha=.2)
    axes[0].set_ylabel('Mean absolute relative depth error (%)')
    axes[1].legend(fontsize=9)
    fig.suptitle('12 new synthetic scenes: near zone and oblique viewing',fontsize=14)
    fig.text(.5,.02,'Dots / bars: aggregate mean / descriptive scene + noise bootstrap 95% interval.  η = 10⁻⁶ assumed leakage transmission.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.055,1,.96])
    fig.savefig(ROOT/'angle-selection.png',dpi=170);fig.savefig(ROOT/'angle-selection.svg');plt.close(fig)
    (ROOT/'range-summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
