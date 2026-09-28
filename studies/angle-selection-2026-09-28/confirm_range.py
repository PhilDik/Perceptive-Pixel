"""Additional scene/area challenge prompted by the changed validation ranking.
All scenes and the decision rule are saved before the new fits begin.
"""
from pathlib import Path
import json,time
import select_angle as s
import numpy as np
OUT=Path(__file__).resolve().parent

def main():
    start=time.perf_counter();rng=np.random.default_rng(2809281)
    scenes={}
    for group in ['central','oblique','grazing']:
        for i in range(4):
            if group=='central':
                xy=[[rng.uniform(-24,-10),rng.uniform(-12,0)],[rng.uniform(12,26),rng.uniform(0,14)]]
                z=[rng.uniform(75,125),rng.uniform(130,180)]
            elif group=='oblique':
                xy=[[rng.uniform(45,75),rng.uniform(-20,-5)],[rng.uniform(80,115),rng.uniform(5,20)]]
                z=[rng.uniform(65,95),rng.uniform(100,150)]
            else:
                xy=[[rng.uniform(80,110),rng.uniform(-20,-5)],[rng.uniform(100,130),rng.uniform(5,20)]]
                z=[rng.uniform(25,45),rng.uniform(50,75)]
            scenes[f'{group}_{i}']={'group':group,'xy':xy,'z':z,'rho':[[rng.uniform(.4,.85),rng.uniform(.12,.35),rng.uniform(.08,.23)],
                                                                        [rng.uniform(.08,.25),rng.uniform(.25,.55),rng.uniform(.45,.85)]]}
    angles=[0,15,20,25,30,35,45]
    protocol={'reason':'first selection and validation rankings differed; additional scene and active-area robustness challenge',
      'angles':angles,'eta':1e-6,'trials':48,'scenes':scenes,'area_modes':['fixed_base','fixed_active'],
      'score':'equal weights of 3 scene groups, each4scenes; mean absolute relative depth error across2patches andnoise',
      'candidate_rule':'smallest positive angle within10percent of bestpositive score separately for eacharea mode; retain planarranking',
      'statistics':'exploratory conditional study; scene-stratified bootstrap; no claim of global optimum or universal generalization'}
    (OUT/'range_protocol.json').write_text(json.dumps(protocol,indent=2)+'\n',encoding='utf-8')
    s.LEVELS=[1e-6]
    rows=[]
    for ai,area in enumerate(protocol['area_modes']):
        for ki,a in enumerate(angles):
            panel=s.make_panel(a,area);leak=panel.leakage(panel.exchange(4))*s.SCALE
            for ni,(name,scene) in enumerate(scenes.items()):
                calculated=s.run_scene(panel,scene,np.array(scene['rho']),leak,48,3000000+ai*100000+ki*1000+ni*10,'range_challenge',name,a==0)
                for r in calculated:r['area_mode']=area;r['group']=scene['group']
                rows.extend(calculated)
            print(json.dumps({'area_mode':area,'alpha':a,'elapsed_s':round(time.perf_counter()-start,1)}),flush=True)
            (OUT/'range_progress.json').write_text(json.dumps({'rows':rows}),encoding='utf-8')
    out={'status':'complete','protocol':protocol,'rows':rows,'fit_count':sum(r['trials'] for r in rows),'nonconverged':sum(r['nonconverged'] for r in rows),
         'boundary_fits':sum(r['boundary_fits'] for r in rows),'elapsed_s':time.perf_counter()-start}
    (OUT/'range-results.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k not in ['protocol','rows']}),flush=True)

if __name__=='__main__':main()
