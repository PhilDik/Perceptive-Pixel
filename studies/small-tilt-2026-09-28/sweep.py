"""Small facet tilts: optical reception, coupling, and illustrative cone limits.
No trained model, device data, or depth reconstruction. Lengths in millimetres.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
import importlib.util, json, math, time, hashlib
import numpy as np
OUT=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(OUT/'mpl-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj)
    return obj

SOURCE=OUT.parent/'layout-noise-2026-09-27'
g=module('angular_geometry',SOURCE/'geometry_benchmark.py')
d=module('depth_geometry',SOURCE/'depth_benchmark.py')
ANGLES=[5.,10.,15.,20.,30.,45.]
POLAR=[0.,15.,30.,45.,60.,75.,85.]
AZIMUTH=np.arange(0.,360.,15.)
DEPTH=np.array([5.,10.,20.,30.,50.,100.,200.])

def reception(panel,points,beta=90.,n=8):
    """Per-region reception kernel for known diffuse patches facing -z.
    A hypothetical hard cone gates cosine sensitivity before integration.
    It does not specify emission, diffraction, or actual device acceptance.
    """
    samples=panel.samples(n)
    shape=(16,3,n*n,len(points))
    start=np.broadcast_to(samples[:,:,:,None,:],shape+(3,)).reshape(-1,3)
    end=np.broadcast_to(points[None,None,None,:,:],shape+(3,)).reshape(-1,3)
    norm=np.broadcast_to(panel.normals[None,:,None,None,:],shape+(3,)).reshape(-1,3)
    owners=np.broadcast_to(np.arange(16)[:,None,None,None],shape).ravel()
    delta=end-start;d2=np.sum(delta**2,axis=1)
    cos=np.einsum('ij,ij->i',delta,norm)/np.sqrt(d2)
    val=np.maximum(cos,0)*np.maximum(delta[:,2]/np.sqrt(d2),0)/d2*1e6
    val[cos<math.cos(math.radians(beta))-1e-12]=0
    active=np.flatnonzero(val>0)
    for ids in np.array_split(active,max(1,math.ceil(len(active)/32768))):
        val[ids]*=panel.visible(start[ids],end[ids],owners[ids])
    return val.reshape(shape).mean(axis=2)

def main():
    started=time.perf_counter();rows=[]
    axis_points=np.c_[np.zeros((len(DEPTH),2)),DEPTH]
    for alpha in ANGLES:
        model=g.RayModel('triangle',alpha,'vertical',n=16)
        curves=[]
        for theta in POLAR:
            vals=np.array([model.response(g.direction(theta,phi)).sum()/g.BASE_AREA for phi in AZIMUTH])
            curves.append({'theta_deg':theta,'min':float(vals.min()),'max':float(vals.max()),'mean':float(vals.mean())})
        assert abs(curves[0]['min']-1)<1e-12
        panel=d.Panel('triangle',alpha,'vertical')
        exchange=panel.exchange(4)
        leak=float(panel.leakage(exchange).sum()*3)
        finite={}
        for beta in [20.,40.,90.]:
            k=reception(panel,axis_points,beta)
            if beta==90: assert np.allclose(k,panel.kernel(axis_points,n=8),rtol=1e-12,atol=1e-12)
            signal=(k*panel.area[None,:,None]*1e-6).sum(axis=(0,1))
            finite[str(int(beta))]={'weighted_reception':signal.tolist(),'zero_response':[bool(v==0) for v in signal]}
        assert not any(finite['90']['zero_response'])
        # Independent analytic channel-spread identity, away from clipping.
        direction=g.direction(10.,23.)
        response=model.areas*np.maximum(model.normals@direction,0)
        cv=float(response.std()/response.mean())
        predicted=math.tan(math.radians(alpha))*math.tan(math.radians(10))/math.sqrt(2)
        assert abs(cv-predicted)<1e-12
        row={'alpha_deg':alpha,'height_mm':panel.height,'facet_area_mm2':float(panel.area.sum()),
             'front_cosine_per_equal_area':math.cos(math.radians(alpha)),
             'front_total_per_equal_base':curves[0]['mean'],
             'angular_contrast_relative_to_45':math.tan(math.radians(alpha)),
             'channel_cv_at_theta10':cv,'direct_checkerboard_leakage_fraction':leak,
             'periodic_reception':curves,'finite_axis_reception':finite}
        if alpha in [15.,45.]:
            fine=panel.exchange(8)
            refined=float(panel.leakage(fine).sum()*3)
            row['refined_leakage_fraction']=refined
            row['leakage_refinement_relative_change']=abs(refined-leak)/refined
        rows.append(row)
        print(json.dumps({k:row[k] for k in ['alpha_deg','height_mm','direct_checkerboard_leakage_fraction']}),flush=True)
    result={'status':'complete; synthetic optical diagnostic, not depth reconstruction',
            'convention':'facet normal tilt from panel normal = side-face tilt from panel plane',
            'layout':'all upright triangular bases; author vertical stagger; side 9 mm',
            'angles_deg':ANGLES,'axis_depths_mm':DEPTH.tolist(),
            'quadrature':{'periodic_samples_per_face':256,'coupling_samples_per_face':16,'selected_coupling_refinement':64,'finite_axis_samples_per_face':64},
            'cone_scope':'20 and 40 degree half-angles are hypothetical hard acceptance cones, not measured optics',
            'finite_axis_scope':'passive receiving response to a small diffuse patch with known -z normal; static finite panel; arbitrary source brightness; not active reconstruction or detection threshold',
            'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [SOURCE/'geometry_benchmark.py',SOURCE/'depth_benchmark.py']},
            'rows':rows,'elapsed_seconds':time.perf_counter()-started}
    (OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    render(rows)
    write_report(rows)
    print('Completed',round(result['elapsed_seconds'],2),'seconds',flush=True)

def render(rows):
    fig,ax=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for r in rows:
        ax[0,0].plot(POLAR,[q['min']*100 for q in r['periodic_reception']],marker='o',label=f"{r['alpha_deg']:g}°")
    ax[0,0].set(xlabel='Incident angle from panel normal (degrees)',ylabel='Worst sampled azimuth, % frontal response',title='Broad cosine reception; same base area')
    ax[0,0].legend(ncol=3,fontsize=8);ax[0,0].grid(alpha=.2)
    a=np.array(ANGLES)
    ax[0,1].plot(a,[r['angular_contrast_relative_to_45'] for r in rows],marker='o')
    ax[0,1].set(xlabel='Facet tilt (degrees)',ylabel='Relative angular channel contrast',title='Less tilt also reduces directional contrast')
    ax[0,1].grid(alpha=.2)
    for alpha,color in [(15.,'#1266a3'),(45.,'#c26423')]:
        r=next(r for r in rows if r['alpha_deg']==alpha)
        broad=np.array(r['finite_axis_reception']['90']['weighted_reception'])
        for beta,style in [('20','-'),('40','--')]:
            v=np.array(r['finite_axis_reception'][beta]['weighted_reception'])/broad
            ax[1,0].plot(DEPTH,v,style,marker='o',color=color,label=f"tilt {alpha:g}°, cone half-angle {beta}°")
    ax[1,0].set(xlabel='Axial patch distance from panel plane (mm)',ylabel='Reception / broad response, same geometry',title='Hypothetical narrow cones: finite 4×4 panel',xscale='log',ylim=(-.03,1.04))
    ax[1,0].legend(fontsize=8);ax[1,0].grid(alpha=.2)
    ax[1,1].plot(a,[r['direct_checkerboard_leakage_fraction']*100 for r in rows],marker='o')
    ax[1,1].set(xlabel='Facet tilt (degrees)',ylabel='Direct emitter-to-receiver energy (%)',title='Specified checkerboard schedule; no cover stack')
    ax[1,1].grid(alpha=.2)
    fig.suptitle('Small-tilt diagnostic — synthetic, not a device specification',fontsize=15)
    for ext in ['png','svg']:fig.savefig(OUT/f'small-tilt.{ext}',dpi=170)
    plt.close(fig)

def write_report(rows):
    r15=next(r for r in rows if r['alpha_deg']==15)
    r45=next(r for r in rows if r['alpha_deg']==45)
    table='\n'.join(f"| {r['alpha_deg']:g}° | {r['height_mm']:.3f} | {100*r['front_cosine_per_equal_area']:.1f}% | {r['angular_contrast_relative_to_45']:.3f} | {100*r['direct_checkerboard_leakage_fraction']:.3f}% |" for r in rows)
    text=f'''# Малый наклон граней и фронтальная чувствительность

28 сентября 2026. Расчёт идеализированной геометрии; не измерение устройства и не восстановление глубины.

## Вывод

15° добавлен как кандидат для дальнейшей проверки. **Прямо перед экраном при 45° в прежней широкой косинусной модели нет полной слепой зоны.** При 15° её также нет. Нормаль грани задаёт максимум чувствительности, а не единственный видимый луч. Узкая оптика может менять этот вывод, но её реальная характеристика пока не задана.

Угол здесь — наклон нормали грани от нормали экрана, численно равный наклону боковой грани к плоскости экрана. Основание — равносторонний треугольник со стороной 9 мм; ориентация и вертикальный сдвиг столбцов сохранены.

## Рассчитанные малые углы

| Наклон | Высота, мм | Фронтальный отклик на равную площадь грани | Угловой контраст относительно 45° | Прямая засветка соседей |
|---|---:|---:|---:|---:|
{table}

Столбец фронтального отклика равен cos(наклон). При **равной площади основания**, как в нашем сравнении пирамид, их разная полная площадь компенсирует этот множитель: суммарный фронтальный приём равен 100% для всех шести вариантов. При равной площади самих граней увеличение 45°→15° составляет около 36,6%. Эти нормировки нельзя смешивать. Это пассивный приём; изменение диаграммы активного излучения — отдельный фактор.

Засветка относится только к прямой связи конечных граней 4×4 панели с выбранным клеточным чередованием целых излучающих/принимающих пикселей. При 15° она равна {100*r15['direct_checkerboard_leakage_fraction']:.3f}% против {100*r45['direct_checkerboard_leakage_fraction']:.3f}% при 45°. Электрические утечки, покрытие, переотражения и их шум не посчитаны. Уточнение 16→64 точек на грань меняет эти два значения относительно уточнённых на {100*r15['leakage_refinement_relative_change']:.2f}% и {100*r45['leakage_refinement_relative_change']:.2f}%. Это не доказательство выигрыша глубины.

![Малые наклоны и область приёма](small-tilt.png)

## Почему уменьшение наклона не является бесплатным улучшением

Пока все три грани видят направление без отсечения и тени, нормированный среднеквадратический разброс каналов равен

```text
CV = tan(alpha) * tan(theta) / sqrt(2)
```

Здесь theta — направление света от нормали экрана. При одинаковом theta переход 45°→15° оставляет примерно 0,268 углового контраста. Это не означает ухудшение глубины ровно в 3,73 раза: глубина также зависит от положения пикселей, движения, освещения и шума. Но различия граней, помогающие различать направления, ослабевают. При строго фронтальном свете три показания равны; производные по малому боковому изменению направления остаются ненулевыми при ненулевом наклоне.

## Когда мёртвая зона действительно появляется

Дополнительный идеальный конус приёма полуугла beta пропускает фронтальное направление отдельной грани, если beta >= alpha. Например, при beta=20° наклон 45° исключает ось в дальней угловой модели, а наклон 15° включает её. Это **условный сценарий**, не характеристика наших диодов.

Для конечной панели расположение каждого приёмника тоже важно. Дополнительно рассчитан малый диффузный участок по общей оси панели на расстояниях 5, 10, 20, 30, 50, 100 и 200 мм. У всех шести наклонов широкий приём даёт ненулевой суммарный сигнал во всех этих точках. График показывает, как гипотетические конусы 20°/40° изменяют приём для 15° и 45°. Это линия проверочных точек, не карта всей трёхмерной зоны; очень близкие поверхности, конечная площадь объекта и порог обнаружения требуют отдельного расчёта.

Полное отсутствие сигнала, сигнал ниже шумового порога и невозможность различить две глубины — разные виды ограничений. Для физической границы рабочей зоны нужны измеренный угловой отклик, спектральная чувствительность, шум, освещение и критерий ошибки глубины. Сейчас таких данных нет.

## Методика и воспроизведение

Периодическая геометрия проверена при 7 полярных углах и 24 азимутах, 256 точек на грань; приведён минимум по этой сетке, не непрерывный глобальный минимум. Фронтальный результат дополнительно проверен точной проекционной формулой. Конечная панель и конусы интегрированы по 64 точкам на грань; вариант без конуса совпадает с прежним ядром до численной точности. Аналитическая формула контраста проверена по трём отдельным каналам. Источники кода и их хеши сохранены в JSON.

Запуск: `python sweep.py`. Требуются NumPy, SciPy и Matplotlib; используются соседние каталоги `../layout-noise-2026-09-27` и `../facet-motion-2026-09-26`. [Исходные результаты](results.json). Новых шумных подгонок глубины, оптимизации угла, обучения и аппаратных опытов здесь нет.

Публикационная формулировка: «Малые наклоны 10–20°, включая 15°, рассматриваются для уменьшения высоты и прямой связи соседей при сохранении фронтального приёма. Выбор требует учёта углового различения и реальной оптики; 15° не объявляется оптимумом». Общий компромисс светосбора и различимости измерений также обсуждается в [OrbCam](https://arxiv.org/html/2306.15953v1); приведённые здесь числа — наш геометрический расчёт, не результаты этой статьи.
'''
    (OUT/'REPORT_RU.md').write_text(text,encoding='utf-8')

if __name__=='__main__':main()
